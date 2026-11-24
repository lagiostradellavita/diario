import hmac
import json
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from fastapi import APIRouter, BackgroundTasks, Body, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..deps import get_session
from ..security import hash_password, verify_password, create_access_token, decode_token
from .auth import get_admin
from ..config import settings
from .. import odoo, posta, recupero

log = logging.getLogger(__name__)

# «Leggo e Conto», i giochi per bambini. Stesso servizio del Diario, ma utenti
# e dati separati: un token dei giochi porta scope 'giochi' e non apre il
# Diario (lo rifiuta get_user_id), un token del Diario non apre i giochi.
# Il backoffice invece usa l'accesso dell'amministratore del Diario.
router = APIRouter(prefix="/giochi", tags=["giochi"])

SCOPE = "giochi"
MAX_DATI = 4_000_000   # i profili con le foto rimpicciolite stanno ben sotto
BACKOFFICE = os.getenv("GIOCHI_BACKOFFICE_URL") or "https://lagiostradellavita.github.io/diario/numeri/admin.html"
APP_URL = os.getenv("GIOCHI_APP_URL") or "https://lagiostradellavita.github.io/diario/numeri/"
# dove si compra l'abbonamento: la pagina del negozio su Odoo. Vuota, l'app non mostra il pulsante
NEGOZIO_URL = os.getenv("GIOCHI_NEGOZIO_URL") or ""
PROVA_GIORNI = 30
PIANI = ("sociale", "prova", "base", "premium")
# contro la condivisione: quanti dispositivi e quanti bambini per account, secondo il piano
DISPOSITIVI = {"sociale": 5, "prova": 3, "base": 3, "premium": 3}
BAMBINI = {"sociale": None, "prova": 2, "base": 2, "premium": 4}
SOSPETTO = 3   # da quanti tentativi oltre il limite il backoffice segnala l'account
# la versione dell'informativa sulla privacy (numeri/privacy.html): se cambia,
# l'app la ripropone a tutti al prossimo ingresso
PRIVACY_VERSIONE = "2026-10"


def _ora():
    return datetime.now(timezone.utc)


def _stato_vero(stato, scadenza) -> str:
    """Lo stato che conta: un accesso attivo ma oltre la scadenza e' 'scaduto'."""
    if stato == "attivo" and scadenza is not None and scadenza < _ora():
        return "scaduto"
    return stato


def _da_odoo(db, uid, email) -> bool:
    """Chiede a Odoo se quest'email ha un abbonamento in corso e, se si', lo applica.
    Copre gli avvisi persi: il server gratuito di Render dorme e Odoo non riprova."""
    if not odoo.configurato():
        return False
    try:
        a = odoo.per_email(email)
    except Exception as e:   # Odoo irraggiungibile: si resta come si era, non si blocca nessuno
        log.warning("Odoo non risponde per %s: %s", email, e)
        return False
    if not a:
        return False
    db.execute(text(
        "update giochi_utenti set stato = 'attivo', piano = :p, scadenza = :s, odoo_rif = :r,"
        " approvato_il = coalesce(approvato_il, now()) where id = :i and stato <> 'bloccato'"
    ), {"p": a["piano"], "s": a["scadenza"], "r": a["rif"], "i": uid})
    db.commit()
    return True


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


def _dispositivo_ok(db, uid, codice):
    """Il dispositivo e' ancora collegato a quest'account? Se e' stato scollegato
    deve rientrare (e ricadere nel limite). Le app vecchie, senza codice, passano."""
    if not codice:
        return
    n = db.execute(text("update giochi_dispositivi set ultimo_uso = now() where utente_id = :u and codice = :c"),
                   {"u": uid, "c": codice[:80]}).rowcount
    db.commit()
    if not n:
        raise HTTPException(401, "Questo dispositivo è stato scollegato: rientra con la password")


def get_giochi_attivo(uid: str = Depends(get_giochi_uid), db: Session = Depends(get_session),
                      x_dispositivo: Optional[str] = Header(None)) -> str:
    """Lascia passare solo chi ha un accesso attivo e non scaduto. Bloccare
    qualcuno gli chiude davvero l'archivio, non solo la schermata."""
    row = db.execute(text("select stato, scadenza from giochi_utenti where id = :i"), {"i": uid}).first()
    if row is None:
        raise HTTPException(401, "Utente non trovato")
    stato = _stato_vero(*row)
    if stato == "scaduto":
        raise HTTPException(403, "Abbonamento scaduto: rinnova sul sito per continuare")
    if stato == "in_attesa":
        raise HTTPException(403, "Il tuo accesso e' in attesa dell'approvazione")
    if stato != "attivo":
        raise HTTPException(403, "Accesso sospeso")
    _dispositivo_ok(db, uid, x_dispositivo)
    return uid


class RegistratiIn(BaseModel):
    email: str
    password: str = Field(min_length=8)
    nome: str = Field(min_length=2)
    telefono: Optional[str] = None
    messaggio: Optional[str] = None
    codice: Optional[str] = None
    nome_dispositivo: Optional[str] = None
    privacy: Optional[str] = None          # la versione dell'informativa letta e accettata


class EntraIn(BaseModel):
    email: str
    password: str
    dispositivo: Optional[str] = None      # descrizione del browser, per il registro degli accessi
    codice: Optional[str] = None           # il codice del dispositivo, creato dall'app
    nome_dispositivo: Optional[str] = None # «iPhone · Safari»
    scollega: Optional[str] = None         # per entrare da qui, scollega questo dispositivo


def _limite_disp(piano):
    return DISPOSITIVI.get(piano or "", 3)


def _elenco_disp(db, uid):
    righe = db.execute(text(
        "select id, nome, ultimo_uso from giochi_dispositivi where utente_id = :u order by ultimo_uso desc"
    ), {"u": uid}).mappings().all()
    return [{"id": str(r["id"]), "nome": r["nome"] or "Dispositivo", "ultimo_uso": r["ultimo_uso"].isoformat()} for r in righe]


def _registra_disp(db, uid, piano, codice, nome, scollega=None):
    """Collega il dispositivo all'account; oltre il limite risponde 409 con l'elenco,
    cosi' l'app puo' chiedere quale scollegare."""
    if not codice:
        return
    codice, nome = codice[:80], (nome or "Dispositivo")[:80]
    if scollega:
        db.execute(text("delete from giochi_dispositivi where utente_id = :u and id::text = :i"), {"u": uid, "i": scollega})
    gia = db.execute(text("select 1 from giochi_dispositivi where utente_id = :u and codice = :c"), {"u": uid, "c": codice}).first()
    if not gia:
        n = db.execute(text("select count(*) from giochi_dispositivi where utente_id = :u"), {"u": uid}).scalar()
        if n >= _limite_disp(piano):
            db.execute(text("update giochi_utenti set tentativi_oltre = tentativi_oltre + 1 where id = :u"), {"u": uid})
            db.commit()
            raise HTTPException(409, {"codice": "troppi_dispositivi", "limite": _limite_disp(piano),
                                      "messaggio": f"Questo account è già collegato a {n} dispositivi, il massimo del piano. "
                                                   "Per entrare da qui scollegane uno.",
                                      "dispositivi": _elenco_disp(db, uid)})
    db.execute(text(
        "insert into giochi_dispositivi (utente_id, codice, nome) values (:u, :c, :n)"
        " on conflict (utente_id, codice) do update set nome = excluded.nome, ultimo_uso = now()"
    ), {"u": uid, "c": codice, "n": nome})
    db.commit()


def _risposta(uid, email, nome, stato, piano=None, scadenza=None):
    return {"access_token": create_access_token(uid, scope=SCOPE), "email": email, "nome": nome,
            "stato": stato, "piano": piano, "scadenza": scadenza.isoformat() if scadenza else None}


@router.post("/registrati", status_code=201)
def registrati(body: RegistratiIn, avvisi: BackgroundTasks, db: Session = Depends(get_session)):
    """Chiunque si registra gioca subito: 30 giorni di prova, senza carta e
    senza approvazione. Se l'email ha gia' un abbonamento su Odoo vale quello."""
    email = (body.email or "").strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(400, "Serve un indirizzo email valido")
    if body.privacy != PRIVACY_VERSIONE:
        raise HTTPException(400, "Per iscriversi bisogna leggere e accettare l'informativa sulla privacy")
    if db.execute(text("select 1 from giochi_utenti where email = :e"), {"e": email}).first():
        raise HTTPException(409, "Questa email e' gia' registrata: entra con la tua password")
    fine_prova = _ora() + timedelta(days=PROVA_GIORNI)
    uid = db.execute(text(
        "insert into giochi_utenti (email, nome, telefono, messaggio, password_hash, stato, piano, scadenza, approvato_il,"
        " privacy_versione, privacy_il)"
        " values (:e, :n, :t, :m, :h, 'attivo', 'prova', :s, now(), :pv, now()) returning id"
    ), {"pv": PRIVACY_VERSIONE, "e": email, "n": body.nome.strip()[:100], "t": (body.telefono or "").strip()[:40] or None,
        "m": (body.messaggio or "").strip()[:1000] or None, "h": hash_password(body.password), "s": fine_prova}).scalar()
    db.commit()   # confermo prima di rispondere: la schermata rilegge subito lo stato
    _da_odoo(db, uid, email)
    row = db.execute(text("select piano, scadenza from giochi_utenti where id = :i"), {"i": uid}).mappings().first()
    _registra_disp(db, uid, row["piano"], body.codice, body.nome_dispositivo)
    # avviso all'amministratore, dopo la risposta: la famiglia non aspetta la posta
    avvisi.add_task(posta.manda, settings.admin_email, "Leggo e Conto: nuova iscrizione di " + body.nome.strip(),
                    f"Una nuova famiglia si e' iscritta a Leggo e Conto (piano: {row['piano']}).\n\n"
                    f"Nome: {body.nome.strip()}\nEmail: {email}\nTelefono: {body.telefono or '-'}\n"
                    f"Per chi: {body.messaggio or '-'}\n\nSe e' una famiglia seguita dalla cooperativa, rendila «sociale»"
                    f" dal backoffice: gioca gratis senza scadenza.\n{BACKOFFICE}\n")
    # e il benvenuto alla famiglia: e' la prova che l'iscrizione e' andata, e ricorda dove si entra
    fino = f" fino al {row['scadenza'].strftime('%d/%m/%Y')}" if row["scadenza"] else ""
    avvisi.add_task(posta.manda, email, "Benvenuti in Leggo e Conto",
                    f"Ciao {body.nome.strip()},\n\nla tua iscrizione a Leggo e Conto e' fatta: puoi giocare subito"
                    f"{fino}.\n\nPer entrare, da telefono, tablet o computer:\n{APP_URL}\n"
                    f"con questa email ({email}) e la password che hai scelto.\n\n"
                    "Se dimentichi la password, nella pagina d'accesso tocca «Password dimenticata?».\n\n"
                    "Buon divertimento!\nLa Giostra della Vita\n")
    return _risposta(uid, email, body.nome.strip(), "attivo", row["piano"], row["scadenza"])


@router.post("/entra")
def entra(body: EntraIn, db: Session = Depends(get_session)):
    email = (body.email or "").strip().lower()
    sel = "select id, email, nome, password_hash, stato, piano, scadenza from giochi_utenti where email = :e"
    row = db.execute(text(sel), {"e": email}).mappings().first()
    if not row or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(401, "Email o password non corretti")
    if row["stato"] == "bloccato":
        raise HTTPException(403, "Accesso sospeso: chiedi all'amministratore")
    if _stato_vero(row["stato"], row["scadenza"]) != "attivo" and _da_odoo(db, row["id"], email):
        row = db.execute(text(sel), {"e": email}).mappings().first()   # ha rinnovato: l'avviso di Odoo era andato perso
    stato = _stato_vero(row["stato"], row["scadenza"])
    if stato == "attivo":
        _registra_disp(db, row["id"], row["piano"], body.codice, body.nome_dispositivo, body.scollega)
        # si contano solo gli ingressi veri, non i tentativi di chi aspetta
        db.execute(text("insert into giochi_accessi (utente_id, dispositivo) values (:u, :d)"),
                   {"u": row["id"], "d": (body.dispositivo or "")[:200] or None})
        db.execute(text("update giochi_utenti set ultimo_accesso = now(), accessi = accessi + 1 where id = :u"),
                   {"u": row["id"]})
        db.commit()
    return _risposta(row["id"], row["email"], row["nome"], stato, row["piano"], row["scadenza"])


class RecuperoIn(BaseModel):
    email: str


class ConfermaIn(BaseModel):
    codice: str
    nuova: str = Field(min_length=8)


class RicordaIn(BaseModel):
    nome: str
    telefono: str


@router.post("/recupero")
def chiedi_recupero(body: RecuperoIn, avvisi: BackgroundTasks, db: Session = Depends(get_session)):
    """Password dimenticata: link via email. Stessa risposta che l'email esista o no."""
    email = (body.email or "").strip().lower()
    row = db.execute(text("select id, nome from giochi_utenti where email = :e"), {"e": email}).mappings().first()
    if row and posta.configurata():
        codice = recupero.crea(db, "giochi", row["id"])
        db.commit()
        avvisi.add_task(posta.manda, email, "Leggo e Conto: nuova password",
                        recupero.testo_email(row["nome"], f"{APP_URL}?recupero={codice}", "Leggo e Conto"))
    return {"ok": True, "posta": posta.configurata()}


@router.post("/recupero/conferma")
def conferma_recupero(body: ConfermaIn, db: Session = Depends(get_session)):
    uid = recupero.usa(db, "giochi", body.codice)
    if not uid:
        raise HTTPException(400, "Il link non vale piu': chiedine un altro")
    db.execute(text("update giochi_utenti set password_hash = :h where id = :i"),
               {"h": hash_password(body.nuova), "i": uid})
    email = db.execute(text("select email from giochi_utenti where id = :i"), {"i": uid}).scalar()
    db.commit()
    return {"ok": True, "email": email}


def _maschera(email: str) -> str:
    """ma***@gm***.com: abbastanza per riconoscerla, non per copiarla."""
    loc, _, dom = email.partition("@")
    nome_dom, _, tld = dom.rpartition(".")
    return f"{loc[:2]}***@{nome_dom[:2]}***.{tld}"


@router.post("/ricorda-email")
def ricorda_email(body: RicordaIn, db: Session = Depends(get_session)):
    """Email dimenticata: con nome e telefono scritti nella richiesta mostra
    l'email nascosta a meta'. Servono tutti e due, e devono indicare una
    persona sola."""
    cifre = "".join(c for c in (body.telefono or "") if c.isdigit())
    nome = " ".join((body.nome or "").lower().split())
    if len(cifre) < 6 or len(nome) < 2:
        raise HTTPException(400, "Scrivi nome e cognome e il numero di telefono")
    righe = db.execute(text("select email, nome, telefono from giochi_utenti where telefono is not null")).mappings().all()
    trovate = [r["email"] for r in righe
               if " ".join((r["nome"] or "").lower().split()) == nome
               and "".join(c for c in r["telefono"] if c.isdigit()).endswith(cifre[-9:])]
    return {"email": _maschera(trovate[0]) if len(trovate) == 1 else None}


@router.get("/io")
def io(uid: str = Depends(get_giochi_uid), db: Session = Depends(get_session)):
    sel = "select email, nome, stato, piano, scadenza, privacy_versione, privacy_il from giochi_utenti where id = :i"
    row = db.execute(text(sel), {"i": uid}).mappings().first()
    if not row:
        raise HTTPException(401, "Utente non trovato")
    if _stato_vero(row["stato"], row["scadenza"]) == "scaduto" and _da_odoo(db, uid, row["email"]):
        row = db.execute(text(sel), {"i": uid}).mappings().first()
    return {"email": row["email"], "nome": row["nome"], "stato": _stato_vero(row["stato"], row["scadenza"]),
            "piano": row["piano"], "scadenza": row["scadenza"].isoformat() if row["scadenza"] else None,
            "negozio": NEGOZIO_URL, "max_bambini": BAMBINI.get(row["piano"]), "max_dispositivi": _limite_disp(row["piano"]),
            "privacy": row["privacy_versione"], "privacy_il": row["privacy_il"].isoformat() if row["privacy_il"] else None,
            "privacy_corrente": PRIVACY_VERSIONE}


class PrivacyIn(BaseModel):
    versione: str


@router.post("/privacy")
def accetta_privacy(body: PrivacyIn, uid: str = Depends(get_giochi_uid), db: Session = Depends(get_session)):
    """Chi era iscritto prima dell'informativa, o ha l'account da un acquisto,
    la accetta al primo ingresso. Si tiene la versione e il momento."""
    if body.versione != PRIVACY_VERSIONE:
        raise HTTPException(400, "L'informativa e' cambiata: ricarica la pagina e rileggila")
    db.execute(text("update giochi_utenti set privacy_versione = :v, privacy_il = now() where id = :i"),
               {"v": PRIVACY_VERSIONE, "i": uid})
    db.commit()
    return {"ok": True, "privacy": PRIVACY_VERSIONE}


@router.get("/miei-dati")
def miei_dati(uid: str = Depends(get_giochi_uid), db: Session = Depends(get_session)):
    """Tutto quello che l'archivio tiene di questo account, in un file solo:
    il diritto di accesso e di portabilita' dell'informativa."""
    u = db.execute(text(
        "select email, nome, telefono, messaggio, stato, piano, scadenza, creato_il, ultimo_accesso, accessi,"
        " privacy_versione, privacy_il from giochi_utenti where id = :i"), {"i": uid}).mappings().first()
    if not u:
        raise HTTPException(401, "Utente non trovato")
    dati = db.execute(text("select valore from giochi_dati where utente_id = :i"), {"i": uid}).scalar()
    iso = lambda t: t.isoformat() if t else None
    return {"account": {k: (iso(v) if hasattr(v, "isoformat") else v) for k, v in u.items()},
            "dispositivi": _elenco_disp(db, uid), "bambini_e_risultati": dati}


class CancellaIn(BaseModel):
    email: str
    password: str


@router.post("/cancella-account")
def cancella_account(body: CancellaIn, avvisi: BackgroundTasks, db: Session = Depends(get_session)):
    """Il diritto alla cancellazione: account, bambini, risultati, dispositivi.
    Chiede email e password invece del token, cosi' funziona anche ad
    abbonamento scaduto. Gli acquisti restano su Odoo per gli obblighi fiscali."""
    email = (body.email or "").strip().lower()
    row = db.execute(text("select id, nome, password_hash from giochi_utenti where email = :e"), {"e": email}).mappings().first()
    if not row or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(400, "Email o password non corrette")
    db.execute(text("delete from recuperi_password where ambito = 'giochi' and utente_id = :i"), {"i": row["id"]})
    db.execute(text("delete from giochi_utenti where id = :i"), {"i": row["id"]})
    db.commit()
    avvisi.add_task(posta.manda, settings.admin_email, "Leggo e Conto: account cancellato",
                    f"{row['nome']} ({email}) ha cancellato il proprio account dall'app, con i profili dei bambini"
                    " e i loro risultati.\nSe ha un abbonamento attivo su Odoo, va disdetto da li'.\n")
    return {"ok": True}


@router.get("/dispositivi")
def miei_dispositivi(uid: str = Depends(get_giochi_uid), db: Session = Depends(get_session),
                     x_dispositivo: Optional[str] = Header(None)):
    questo = db.execute(text("select id::text from giochi_dispositivi where utente_id = :u and codice = :c"),
                        {"u": uid, "c": (x_dispositivo or "")[:80]}).scalar()
    return {"dispositivi": [dict(d, questo=d["id"] == questo) for d in _elenco_disp(db, uid)]}


@router.delete("/dispositivi/{did}", status_code=204)
def scollega(did: str, uid: str = Depends(get_giochi_uid), db: Session = Depends(get_session)):
    """Toglie un dispositivo dall'account: alla prossima richiesta dovra' rientrare."""
    db.execute(text("delete from giochi_dispositivi where utente_id = :u and id::text = :i"), {"u": uid, "i": did})
    db.commit()
    return None


@router.get("/info")
def info():
    """Quello che serve alla pagina di download, senza accesso."""
    return {"negozio": NEGOZIO_URL, "prova_giorni": PROVA_GIORNI, "app": APP_URL}


# --- Odoo: gli abbonamenti pagati aprono l'accesso ---------------------------

def _evento(db, email, rif, esito, corpo):
    db.execute(text("insert into giochi_odoo_eventi (email, rif, esito, corpo) values (:e, :r, :x, cast(:c as jsonb))"),
               {"e": email, "r": rif, "x": esito, "c": json.dumps(corpo, default=str)[:20000]})
    db.commit()


def _applica(db, a, avvisi) -> str:
    """Apre, rinnova o chiude l'accesso di un'email secondo il suo abbonamento.
    Chi non c'e' ancora viene creato e riceve un link per scegliere la password."""
    email = (a.get("email") or "").strip().lower()
    if "@" not in email:
        return "senza email: niente da fare"
    row = db.execute(text("select id, nome, stato, piano from giochi_utenti where email = :e"), {"e": email}).mappings().first()
    if not a["attivo"]:
        if not row or row["piano"] == "sociale":
            return "abbonamento non in corso: nessun accesso da chiudere"
        if row["piano"] in ("base", "premium"):
            db.execute(text("update giochi_utenti set scadenza = least(coalesce(scadenza, now()), now()) where id = :i"), {"i": row["id"]})
            db.commit()
            return "abbonamento chiuso: accesso fermato"
        return "abbonamento non in corso"
    if row:
        if row["stato"] == "bloccato":
            return "abbonamento in corso ma accesso bloccato dal backoffice: non riaperto"
        db.execute(text(
            "update giochi_utenti set stato = 'attivo', piano = :p, scadenza = :s, odoo_rif = :r,"
            " approvato_il = coalesce(approvato_il, now()) where id = :i"
        ), {"p": a["piano"], "s": a["scadenza"], "r": a["rif"], "i": row["id"]})
        db.commit()
        return f"rinnovato: {a['piano']} fino al {a['scadenza'].date() if a['scadenza'] else 'senza scadenza'}"
    nome = (a.get("nome") or "").strip()[:100] or None
    uid = db.execute(text(
        "insert into giochi_utenti (email, nome, password_hash, stato, piano, scadenza, odoo_rif, approvato_il, messaggio)"
        " values (:e, :n, :h, 'attivo', :p, :s, :r, now(), 'acquisto dal sito') returning id"
    ), {"e": email, "n": nome, "h": hash_password(secrets.token_urlsafe(24)), "p": a["piano"], "s": a["scadenza"], "r": a["rif"]}).scalar()
    codice = recupero.crea(db, "giochi", uid, minuti=7 * 24 * 60)
    db.commit()
    link = f"{APP_URL}?recupero={codice}"
    if not posta.configurata():
        return "nuovo accesso creato, ma la posta non e' configurata: dai tu la password dal backoffice"
    avvisi.add_task(posta.manda, email, "Leggo e Conto: il tuo accesso e' pronto",
                    f"Ciao {nome or ''},\n\ngrazie per aver scelto Leggo e Conto! Il tuo abbonamento e' attivo.\n\n"
                    f"Per cominciare scegli la tua password da questo link (vale 7 giorni):\n{link}\n\n"
                    "Poi entra con questa email e la password che hai scelto. Sul telefono o sul tablet puoi"
                    " aggiungere l'app alla schermata Home: la trovi pronta come le altre app.\n\nBuon divertimento!\n")
    return "nuovo accesso creato, email con il link mandata"


def _dal_corpo(corpo: dict):
    """Un avviso scritto a mano (o da un'azione automatica di Odoo) nella forma semplice:
    {"email", "nome", "piano", "scadenza": "AAAA-MM-GG", "attivo": true|false, "rif"}."""
    scad = corpo.get("scadenza")
    try:
        scad = datetime.strptime(str(scad)[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1) if scad else None
    except ValueError:
        scad = None
    piano = str(corpo.get("piano") or "")
    piano = piano if piano in ("base", "premium") else odoo.piano_da_nomi([piano])
    return {"email": corpo.get("email"), "nome": corpo.get("nome"), "piano": piano, "scadenza": scad,
            "attivo": corpo.get("attivo", True) not in (False, "false", 0, "0"), "rif": str(corpo.get("rif") or "")[:60] or None}


@router.post("/odoo/abbonamento")
def avviso_odoo(avvisi: BackgroundTasks, chiave: str = "", corpo: Any = Body(None), db: Session = Depends(get_session)):
    """Odoo avvisa che un abbonamento e' cambiato (pagato, rinnovato, chiuso).

    L'indirizzo da incollare in Odoo porta la chiave segreta GIOCHI_ODOO_CHIAVE:
    .../giochi/odoo/abbonamento?chiave=... Se Odoo e' configurato (odoo.py),
    dall'avviso si prende solo il numero dell'ordine e il resto si rilegge da
    Odoo: anche chi conoscesse la chiave non potrebbe regalarsi un abbonamento."""
    giusta = os.getenv("GIOCHI_ODOO_CHIAVE") or ""
    if not giusta or not hmac.compare_digest(chiave.encode(), giusta.encode()):
        raise HTTPException(403, "Chiave non valida")
    corpo = corpo if isinstance(corpo, dict) else {}
    try:
        if odoo.configurato() and corpo.get("_id"):
            a = odoo.per_ordine(corpo["_id"])
            if not a:
                _evento(db, None, str(corpo.get("_id")), "non e' un abbonamento: ignorato", corpo)
                return {"ok": True, "esito": "ignorato"}
        elif corpo.get("email"):
            a = _dal_corpo(corpo)
        else:
            _evento(db, None, str(corpo.get("_id") or ""), "manca l'email e Odoo non e' configurato per rileggere l'ordine", corpo)
            return {"ok": False, "esito": "manca l'email"}
        esito = _applica(db, a, avvisi)
    except Exception as e:
        db.rollback()
        log.exception("avviso Odoo non applicato")
        _evento(db, None, str(corpo.get("_id") or ""), f"errore: {e}"[:300], corpo)
        raise HTTPException(500, "Avviso non applicato: riprova")
    _evento(db, a.get("email"), a.get("rif"), esito, corpo)
    return {"ok": True, "esito": esito}


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
    piano = db.execute(text("select piano from giochi_utenti where id = :i"), {"i": uid}).scalar()
    massimo = BAMBINI.get(piano)
    if massimo is not None:
        quanti = lambda v: len((v or {}).get("profiles") or []) if isinstance(v, dict) else 0
        prima = quanti(db.execute(text("select valore from giochi_dati where utente_id = :u"), {"u": uid}).scalar())
        if quanti(valore) > massimo and quanti(valore) > prima:
            raise HTTPException(403, f"Il piano permette fino a {massimo} bambini")
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
    return {"configurata": posta.configurata(), "destinatario": settings.admin_email,
            "via": "Brevo" if posta._brevo() else ("SMTP" if posta.configurata() else None)}


@router.post("/admin/posta/prova")
def prova_posta(_admin: str = Depends(get_admin)):
    """Manda subito un'email di prova all'amministratore e dice se e' partita:
    e' l'unico modo di sapere, da fuori, che la posta funziona davvero."""
    if not posta.configurata():
        return {"ok": False, "messaggio": "La posta non e' configurata su Render."}
    ok = posta.manda(settings.admin_email, "Leggo e Conto: email di prova",
                     "Se leggi questa email, la posta di Leggo e Conto funziona: le famiglie ricevono"
                     " il benvenuto, il link per la password e quello dopo l'acquisto.\n")
    return {"ok": ok, "destinatario": settings.admin_email,
            "messaggio": "Partita: controlla la casella (anche nella posta indesiderata)." if ok else
            "Non e' partita. Se usi l'SMTP sul piano gratuito di Render, e' bloccato: serve Brevo o un piano a pagamento. "
            "Il motivo esatto e' nei Logs del servizio su Render."}


def _pulizia(db):
    """I tempi di conservazione promessi dall'informativa (numeri/privacy.html):
    registro degli accessi 12 mesi; account fermi da 24 mesi, con l'abbonamento
    finito da altrettanto, cancellati con bambini e risultati; i messaggi di
    Odoo 24 mesi. Gira ogni volta che si apre il backoffice."""
    db.execute(text("delete from giochi_accessi where quando < now() - interval '12 months'"))
    db.execute(text("delete from giochi_odoo_eventi where ricevuto_il < now() - interval '24 months'"))
    db.execute(text("delete from recuperi_password where ambito = 'giochi' and scade_il < now() - interval '30 days'"))
    db.execute(text(
        "delete from giochi_utenti where coalesce(piano, '') <> 'sociale'"
        " and scadenza is not null and scadenza < now() - interval '24 months'"
        " and coalesce(ultimo_accesso, creato_il) < now() - interval '24 months'"))
    db.commit()


@router.get("/admin/utenti")
def admin_utenti(db: Session = Depends(get_session), _admin: str = Depends(get_admin)):
    _pulizia(db)
    righe = db.execute(text(
        "select u.id, u.email, u.nome, u.telefono, u.messaggio, u.stato, u.creato_il, u.approvato_il,"
        " u.ultimo_accesso, u.accessi, u.piano, u.scadenza, u.odoo_rif, u.tentativi_oltre, u.privacy_il, d.valore,"
        " (select count(*) from giochi_dispositivi x where x.utente_id = u.id) as n_disp"
        " from giochi_utenti u left join giochi_dati d on d.utente_id = u.id"
        " order by (u.stato = 'in_attesa') desc, u.creato_il desc"
    )).mappings().all()
    iso = lambda t: t.isoformat() if t else None
    return {"utenti": [{
        "id": str(r["id"]), "email": r["email"], "nome": r["nome"], "telefono": r["telefono"],
        "messaggio": r["messaggio"], "stato": r["stato"], "iscritto": iso(r["creato_il"]),
        "approvato": iso(r["approvato_il"]), "ultimo_accesso": iso(r["ultimo_accesso"]),
        "accessi": r["accessi"], "bambini": _riassunto_bambini(r["valore"]),
        "piano": r["piano"], "scadenza": iso(r["scadenza"]), "odoo": r["odoo_rif"],
        "scaduto": _stato_vero(r["stato"], r["scadenza"]) == "scaduto",
        "dispositivi": r["n_disp"], "max_dispositivi": _limite_disp(r["piano"]), "tentativi_oltre": r["tentativi_oltre"],
        "sospetto": r["tentativi_oltre"] >= SOSPETTO, "privacy_il": iso(r["privacy_il"]),
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


class PianoIn(BaseModel):
    piano: str
    giorni: Optional[int] = None   # per prova, base e premium: da oggi; vuoto = senza scadenza


@router.post("/admin/utenti/{uid}/piano")
def cambia_piano(uid: str, body: PianoIn, db: Session = Depends(get_session), _admin: str = Depends(get_admin)):
    """Sociale: gratis e senza scadenza (famiglie seguite dalla cooperativa).
    Gli altri piani si danno a mano per un certo numero di giorni."""
    if body.piano not in PIANI:
        raise HTTPException(400, "Piano sconosciuto")
    scad = None if body.piano == "sociale" or not body.giorni else _ora() + timedelta(days=max(1, min(body.giorni, 3660)))
    n = db.execute(text(
        "update giochi_utenti set piano = :p, scadenza = :s, stato = case when stato = 'in_attesa' then 'attivo' else stato end,"
        " approvato_il = coalesce(approvato_il, now()) where id = :i"
    ), {"p": body.piano, "s": scad, "i": uid}).rowcount
    if not n:
        raise HTTPException(404, "Utente non trovato")
    db.commit()
    return {"ok": True, "scadenza": scad.isoformat() if scad else None}


@router.get("/admin/utenti/{uid}/dispositivi")
def admin_dispositivi(uid: str, db: Session = Depends(get_session), _admin: str = Depends(get_admin)):
    return {"dispositivi": _elenco_disp(db, uid)}


@router.post("/admin/utenti/{uid}/scollega-tutti")
def admin_scollega(uid: str, db: Session = Depends(get_session), _admin: str = Depends(get_admin)):
    """Scollega tutti i dispositivi e azzera i tentativi: la famiglia rientra con la password."""
    db.execute(text("delete from giochi_dispositivi where utente_id = :u"), {"u": uid})
    db.execute(text("update giochi_utenti set tentativi_oltre = 0 where id = :u"), {"u": uid})
    db.commit()
    return {"ok": True}


@router.get("/admin/odoo")
def admin_odoo(db: Session = Depends(get_session), _admin: str = Depends(get_admin)):
    """Com'e' messo il collegamento con Odoo e gli ultimi avvisi arrivati."""
    righe = db.execute(text(
        "select ricevuto_il, email, rif, esito from giochi_odoo_eventi order by ricevuto_il desc limit 100"
    )).mappings().all()
    return {"lettura": odoo.configurato(), "chiave": bool(os.getenv("GIOCHI_ODOO_CHIAVE")),
            "negozio": NEGOZIO_URL, "posta": posta.configurata(),
            "eventi": [{"quando": r["ricevuto_il"].isoformat(), "email": r["email"], "rif": r["rif"], "esito": r["esito"]} for r in righe]}


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
