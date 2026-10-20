import json
import os
import secrets
from typing import Any, Optional
from fastapi import APIRouter, BackgroundTasks, Body, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..deps import get_session
from ..security import hash_password, verify_password, create_access_token, decode_token
from .auth import get_admin
from ..config import settings
from .. import posta

# «Leggo e Conto», i giochi per bambini. Stesso servizio del Diario, ma utenti
# e dati separati: un token dei giochi porta scope 'giochi' e non apre il
# Diario (lo rifiuta get_user_id), un token del Diario non apre i giochi.
# Il backoffice invece usa l'accesso dell'amministratore del Diario.
router = APIRouter(prefix="/giochi", tags=["giochi"])

SCOPE = "giochi"
MAX_DATI = 4_000_000   # i profili con le foto rimpicciolite stanno ben sotto
BACKOFFICE = os.getenv("GIOCHI_BACKOFFICE_URL") or "https://lagiostradellavita.github.io/diario/numeri/admin.html"
APP_URL = os.getenv("GIOCHI_APP_URL") or "https://lagiostradellavita.github.io/diario/numeri/"


def get_giochi_uid(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Autenticazione richiesta")
    try:
        payload = decode_token(authorization.split(" ", 1)[1])
    except Exception:
        raise HTTPException(401, "Sessione scaduta: rientra con la password")
    if payload.get("scope") != SCOPE or not payload.get("sub"):
        raise HTTPException(401, "Token non valido")
    return payload["sub"]


def get_giochi_attivo(uid: str = Depends(get_giochi_uid), db: Session = Depends(get_session)) -> str:
    """Lascia passare solo chi l'amministratore ha approvato. Bloccare
    qualcuno gli chiude davvero l'archivio, non solo la schermata."""
    stato = db.execute(text("select stato from giochi_utenti where id = :i"), {"i": uid}).scalar()
    if stato is None:
        raise HTTPException(401, "Utente non trovato")
    if stato == "in_attesa":
        raise HTTPException(403, "Il tuo accesso e' in attesa dell'approvazione")
    if stato != "attivo":
        raise HTTPException(403, "Accesso sospeso")
    return uid


class RegistratiIn(BaseModel):
    email: str
    password: str = Field(min_length=8)
    nome: str = Field(min_length=2)
    telefono: Optional[str] = None
    messaggio: Optional[str] = None


class EntraIn(BaseModel):
    email: str
    password: str
    dispositivo: Optional[str] = None


def _risposta(uid, email, nome, stato):
    return {"access_token": create_access_token(uid, scope=SCOPE), "email": email,
            "nome": nome, "stato": stato}


@router.post("/registrati", status_code=201)
def registrati(body: RegistratiIn, avvisi: BackgroundTasks, db: Session = Depends(get_session)):
    """Chiunque puo' chiedere l'accesso, ma nasce «in_attesa»: gioca solo
    dopo che l'amministratore lo approva dal backoffice."""
    email = (body.email or "").strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(400, "Serve un indirizzo email valido")
    if db.execute(text("select 1 from giochi_utenti where email = :e"), {"e": email}).first():
        raise HTTPException(409, "Questa email e' gia' registrata: entra con la tua password")
    uid = db.execute(text(
        "insert into giochi_utenti (email, nome, telefono, messaggio, password_hash)"
        " values (:e, :n, :t, :m, :h) returning id"
    ), {"e": email, "n": body.nome.strip()[:100], "t": (body.telefono or "").strip()[:40] or None,
        "m": (body.messaggio or "").strip()[:1000] or None, "h": hash_password(body.password)}).scalar()
    db.commit()   # confermo prima di rispondere: la schermata rilegge subito lo stato
    # avviso all'amministratore, dopo la risposta: la famiglia non aspetta la posta
    avvisi.add_task(posta.manda, settings.admin_email, "Leggo e Conto: nuova richiesta d'accesso da " + body.nome.strip(),
                    "E' arrivata una nuova richiesta d'accesso a Leggo e Conto.\n\n"
                    f"Nome: {body.nome.strip()}\nEmail: {email}\nTelefono: {body.telefono or '-'}\n"
                    f"Per chi: {body.messaggio or '-'}\n\nPer approvarla o rifiutarla apri il backoffice:\n{BACKOFFICE}\n")
    return _risposta(uid, email, body.nome.strip(), "in_attesa")


@router.post("/entra")
def entra(body: EntraIn, db: Session = Depends(get_session)):
    email = (body.email or "").strip().lower()
    row = db.execute(text(
        "select id, email, nome, password_hash, stato from giochi_utenti where email = :e"
    ), {"e": email}).mappings().first()
    if not row or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(401, "Email o password non corretti")
    if row["stato"] == "bloccato":
        raise HTTPException(403, "Accesso sospeso: chiedi all'amministratore")
    if row["stato"] == "attivo":
        # si contano solo gli ingressi veri, non i tentativi di chi aspetta
        db.execute(text("insert into giochi_accessi (utente_id, dispositivo) values (:u, :d)"),
                   {"u": row["id"], "d": (body.dispositivo or "")[:200] or None})
        db.execute(text("update giochi_utenti set ultimo_accesso = now(), accessi = accessi + 1 where id = :u"),
                   {"u": row["id"]})
        db.commit()
    return _risposta(row["id"], row["email"], row["nome"], row["stato"])


@router.get("/io")
def io(uid: str = Depends(get_giochi_uid), db: Session = Depends(get_session)):
    row = db.execute(text("select email, nome, stato from giochi_utenti where id = :i"),
                     {"i": uid}).mappings().first()
    if not row:
        raise HTTPException(401, "Utente non trovato")
    return dict(row)


class PasswordIn(BaseModel):
    attuale: str
    nuova: str = Field(min_length=8)


@router.post("/cambia-password")
def cambia_password(body: PasswordIn, uid: str = Depends(get_giochi_uid), db: Session = Depends(get_session)):
    h = db.execute(text("select password_hash from giochi_utenti where id = :i"), {"i": uid}).scalar()
    if not h or not verify_password(body.attuale, h):
        raise HTTPException(400, "La password attuale non e' corretta")
    db.execute(text("update giochi_utenti set password_hash = :h where id = :i"),
               {"h": hash_password(body.nuova), "i": uid})
    db.commit()
    return {"ok": True}


@router.get("/dati")
def leggi_dati(uid: str = Depends(get_giochi_attivo), db: Session = Depends(get_session)):
    """I profili dei bambini e i loro risultati; null la prima volta."""
    return {"valore": db.execute(text("select valore from giochi_dati where utente_id = :u"), {"u": uid}).scalar()}


@router.put("/dati")
def salva_dati(valore: Any = Body(...), uid: str = Depends(get_giochi_attivo), db: Session = Depends(get_session)):
    raw = json.dumps(valore)
    if len(raw) > MAX_DATI:
        raise HTTPException(413, "Troppi dati: usa foto piu' piccole")
    db.execute(text(
        "insert into giochi_dati (utente_id, valore, aggiornato_il) values (:u, cast(:v as jsonb), now())"
        " on conflict (utente_id) do update set valore = excluded.valore, aggiornato_il = now()"
    ), {"u": uid, "v": raw})
    db.commit()
    return {"ok": True}


# --- Backoffice: solo l'amministratore del Diario ---------------------------

def _riassunto_bambini(valore) -> list:
    """Nome, classe e premi di ogni bambino, senza foto: e' quello che serve
    al backoffice per riconoscere le famiglie."""
    out = []
    try:
        for p in (valore or {}).get("profiles", []):
            info, d = p.get("info") or {}, p.get("data") or {}
            out.append({"nome": " ".join(x for x in [info.get("nome"), info.get("cognome")] if x) or "Senza nome",
                        "eta": info.get("eta") or None, "classe": info.get("classe") or None,
                        "partite": d.get("rounds") or 0, "stelline": d.get("stelline") or 0})
    except Exception:
        pass
    return out


@router.get("/admin/posta")
def stato_posta(_admin: str = Depends(get_admin)):
    """Dice al backoffice se gli avvisi via email possono partire."""
    return {"configurata": posta.configurata(), "destinatario": settings.admin_email}


@router.get("/admin/utenti")
def admin_utenti(db: Session = Depends(get_session), _admin: str = Depends(get_admin)):
    righe = db.execute(text(
        "select u.id, u.email, u.nome, u.telefono, u.messaggio, u.stato, u.creato_il, u.approvato_il,"
        " u.ultimo_accesso, u.accessi, d.valore"
        " from giochi_utenti u left join giochi_dati d on d.utente_id = u.id"
        " order by (u.stato = 'in_attesa') desc, u.creato_il desc"
    )).mappings().all()
    iso = lambda t: t.isoformat() if t else None
    return {"utenti": [{
        "id": str(r["id"]), "email": r["email"], "nome": r["nome"], "telefono": r["telefono"],
        "messaggio": r["messaggio"], "stato": r["stato"], "iscritto": iso(r["creato_il"]),
        "approvato": iso(r["approvato_il"]), "ultimo_accesso": iso(r["ultimo_accesso"]),
        "accessi": r["accessi"], "bambini": _riassunto_bambini(r["valore"]),
    } for r in righe]}


def _cambia_stato(db, uid, stato):
    n = db.execute(text(
        "update giochi_utenti set stato = :s,"
        " approvato_il = case when :s = 'attivo' then coalesce(approvato_il, now()) else approvato_il end"
        " where id = :i"
    ), {"s": stato, "i": uid}).rowcount
    if not n:
        raise HTTPException(404, "Utente non trovato")
    db.commit()
    return {"ok": True}


@router.post("/admin/utenti/{uid}/approva")
def approva(uid: str, avvisi: BackgroundTasks, db: Session = Depends(get_session), _admin: str = Depends(get_admin)):
    """Approva chi e' in attesa, o riattiva chi era bloccato. La famiglia
    riceve un'email, se la posta e' configurata."""
    row = db.execute(text("select email, nome, stato from giochi_utenti where id = :i"), {"i": uid}).mappings().first()
    out = _cambia_stato(db, uid, "attivo")
    if row and row["stato"] != "attivo":
        avvisi.add_task(posta.manda, row["email"], "Leggo e Conto: il tuo accesso e' attivo",
                        f"Ciao {row['nome'] or ''},\n\nil tuo accesso a Leggo e Conto e' stato approvato. "
                        f"Entra con la tua email e la tua password da qui:\n{APP_URL}\n\nBuon divertimento!\n")
    return out


@router.post("/admin/utenti/{uid}/blocca")
def blocca(uid: str, db: Session = Depends(get_session), _admin: str = Depends(get_admin)):
    """Chiude l'accesso: i dati restano, si puo' riattivare."""
    return _cambia_stato(db, uid, "bloccato")


@router.post("/admin/utenti/{uid}/password-provvisoria")
def password_provvisoria(uid: str, db: Session = Depends(get_session), _admin: str = Depends(get_admin)):
    """Per chi ha dimenticato la password: l'amministratore gliela comunica a voce."""
    nuova = secrets.token_urlsafe(6)
    n = db.execute(text("update giochi_utenti set password_hash = :h where id = :i"),
                   {"h": hash_password(nuova), "i": uid}).rowcount
    if not n:
        raise HTTPException(404, "Utente non trovato")
    db.commit()
    return {"password": nuova}


@router.delete("/admin/utenti/{uid}", status_code=204)
def elimina(uid: str, db: Session = Depends(get_session), _admin: str = Depends(get_admin)):
    """Cancella l'accesso con i profili dei bambini e i loro risultati."""
    db.execute(text("delete from giochi_utenti where id = :i"), {"i": uid})
    db.commit()
    return None


@router.get("/admin/accessi")
def accessi(limite: int = 200, db: Session = Depends(get_session), _admin: str = Depends(get_admin)):
    righe = db.execute(text(
        "select a.quando, a.dispositivo, u.nome, u.email from giochi_accessi a"
        " join giochi_utenti u on u.id = a.utente_id order by a.quando desc limit :l"
    ), {"l": max(1, min(limite, 1000))}).mappings().all()
    return {"accessi": [{"quando": r["quando"].isoformat(), "dispositivo": r["dispositivo"],
                         "nome": r["nome"], "email": r["email"]} for r in righe]}
