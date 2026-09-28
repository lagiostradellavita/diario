import json
import secrets
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..deps import get_session, get_user_id
from ..security import hash_password, verify_password, create_access_token
from ..config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterIn(BaseModel):
    email: str
    password: str = Field(min_length=8)
    nome: Optional[str] = None
    codice: Optional[str] = None      # il codice dell'invito ricevuto dall'amministratore


class LoginIn(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: str
    nome: Optional[str] = None
    stato: Optional[str] = None       # 'attivo' | 'in_attesa' | 'bloccato'


@router.get("/stato")
def stato(db: Session = Depends(get_session)):
    """Dice al frontend se l'accesso e' gia' stato creato: la prima volta mostra
    «Crea accesso», dopo mostra «Entra». Non richiede login."""
    quanti = db.execute(text("select count(*) from utenti")).scalar()
    return {"configurato": bool(quanti), "multiutente": True}


@router.post("/register", response_model=TokenOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_session)):
    """Crea un nuovo utente, ma solo su invito dell'amministratore.

    Chi usa un invito valido nasce «in_attesa»: potra' usare l'app solo dopo
    l'ok dell'amministratore. Il primissimo utente in assoluto (archivio vuoto)
    e' un'eccezione: nasce «attivo», per poter creare il primo amministratore.
    L'archivio e' gia' diviso per utente, quindi i dati di ognuno restano suoi."""
    email = (body.email or "").strip().lower()
    if "@" not in email:
        raise HTTPException(400, "Serve un indirizzo email valido")
    esiste = db.execute(text("select 1 from utenti where email = :e"), {"e": email}).first()
    if esiste:
        raise HTTPException(409, "Questa email e' gia' registrata. Entra con la tua password.")

    quanti = db.execute(text("select count(*) from utenti")).scalar()
    invito = None
    if quanti == 0:
        # Archivio vuoto: primo accesso in assoluto, nasce amministratore attivo.
        stato = "attivo"
    else:
        codice = (body.codice or "").strip()
        if not codice:
            raise HTTPException(403, "Per registrarti serve un invito dell'amministratore")
        invito = db.execute(text(
            "select id, usato_da from inviti where codice = :c"
        ), {"c": codice}).mappings().first()
        if not invito:
            raise HTTPException(403, "Questo invito non risulta inviato dall'amministratore")
        if invito["usato_da"]:
            raise HTTPException(403, "Questo invito e' gia' stato usato")
        stato = "in_attesa"

    db.execute(text(
        "insert into utenti (email, nome, password_hash, stato) values (:e, :n, :h, :s)"
    ), {"e": email, "n": body.nome, "h": hash_password(body.password), "s": stato})
    uid = db.execute(text("select id from utenti where email = :e"), {"e": email}).scalar()

    if invito is not None:
        db.execute(text(
            "update inviti set usato_da = :u, usato_il = now() where id = :i"
        ), {"u": uid, "i": invito["id"]})

    db.commit()   # confermo prima di rispondere: la schermata rilegge subito lo stato
    return {"access_token": create_access_token(uid), "email": email,
            "nome": body.nome, "stato": stato}


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_session)):
    email = (body.email or "").strip().lower()
    row = db.execute(text(
        "select id, email, nome, password_hash, stato from utenti where email = :e"
    ), {"e": email}).mappings().first()
    if not row or not row["password_hash"] or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(401, "Email o password non corretti")
    stato = row["stato"] or "attivo"
    if stato == "bloccato":
        raise HTTPException(403, "Accesso sospeso dall'amministratore")
    # «in_attesa» entra lo stesso: vede la schermata «in attesa», ma i dati
    # restano chiusi (li protegge get_active_user_id sulle rotte /dati).
    return {"access_token": create_access_token(row["id"]), "email": row["email"],
            "nome": row["nome"], "stato": stato}


class PasswordIn(BaseModel):
    attuale: str
    nuova: str = Field(min_length=8)


@router.post("/cambia-password")
def cambia_password(body: PasswordIn, db: Session = Depends(get_session),
                    uid: str = Depends(get_user_id)):
    u = db.execute(text("select id, password_hash from utenti where id = :i"),
                   {"i": uid}).mappings().first()
    if not u:
        raise HTTPException(404, "Utente non trovato")
    if not verify_password(body.attuale, u["password_hash"]):
        raise HTTPException(400, "La password attuale non e' corretta")
    if body.nuova == body.attuale:
        raise HTTPException(400, "La password nuova deve essere diversa da quella di prima")
    db.execute(text("update utenti set password_hash = :h where id = :i"),
               {"h": hash_password(body.nuova), "i": uid})
    return {"ok": True}


@router.get("/me")
def me(db: Session = Depends(get_session), uid: str = Depends(get_user_id)):
    row = db.execute(text("select id, email, nome, stato from utenti where id = :i"),
                     {"i": uid}).mappings().first()
    if not row:
        raise HTTPException(404, "Utente non trovato")
    return dict(row)


def get_admin(db: Session = Depends(get_session), uid: str = Depends(get_user_id)) -> str:
    """Lascia passare solo l'amministratore (l'email in ADMIN_EMAIL)."""
    row = db.execute(text("select email from utenti where id = :i"), {"i": uid}).mappings().first()
    if not row or (row["email"] or "").strip().lower() != settings.admin_email.strip().lower():
        raise HTTPException(403, "Riservato all'amministratore")
    return uid


@router.get("/admin/utenti")
def admin_utenti(db: Session = Depends(get_session), _admin: str = Depends(get_admin)):
    """Solo per l'amministratore: elenco degli iscritti e delle funzioni che
    ognuno usa. NON restituisce i contenuti (i dati di salute) di nessuno."""
    utenti = db.execute(text(
        "select id, email, nome, stato, created_at from utenti order by created_at"
    )).mappings().all()
    out = []
    for u in utenti:
        raw = db.execute(text(
            "select valore from documenti where user_id = :u and chiave = 'salute-funzioni-attive'"
        ), {"u": u["id"]}).scalar()
        try:
            funzioni = raw if isinstance(raw, (list, dict)) else (json.loads(raw) if raw else None)
        except Exception:
            funzioni = None
        nmod = db.execute(text(
            "select count(*) from documenti where user_id = :u"
        ), {"u": u["id"]}).scalar()
        inv = db.execute(text(
            "select etichetta, codice from inviti where usato_da = :u"
        ), {"u": u["id"]}).mappings().first()
        out.append({
            "id": str(u["id"]),
            "email": u["email"],
            "nome": u["nome"],
            "stato": u["stato"] or "attivo",
            "iscritto": u["created_at"].isoformat() if u["created_at"] else None,
            "invito": (inv["etichetta"] or inv["codice"]) if inv else None,
            "funzioni": funzioni,
            "moduli_con_dati": nmod,
        })
    return {"totale": len(out), "utenti": out}


# --- Inviti -----------------------------------------------------------------

class InvitoIn(BaseModel):
    etichetta: Optional[str] = None


@router.post("/admin/inviti", status_code=201)
def crea_invito(body: InvitoIn, db: Session = Depends(get_session),
                admin_uid: str = Depends(get_admin)):
    """Genera un invito usa-e-getta. Solo l'amministratore. Il codice va nel
    link che l'amministratore manda alla persona (.../?invito=CODICE)."""
    codice = secrets.token_urlsafe(9)
    db.execute(text(
        "insert into inviti (codice, etichetta, creato_da) values (:c, :e, :a)"
    ), {"c": codice, "e": (body.etichetta or None), "a": admin_uid})
    db.commit()
    return {"codice": codice, "etichetta": body.etichetta}


@router.get("/admin/inviti")
def lista_inviti(db: Session = Depends(get_session), _admin: str = Depends(get_admin)):
    righe = db.execute(text(
        "select i.codice, i.etichetta, i.creato_il, i.usato_il,"
        " u.email as usato_email, u.nome as usato_nome"
        " from inviti i left join utenti u on u.id = i.usato_da"
        " order by i.creato_il desc"
    )).mappings().all()
    out = [{
        "codice": r["codice"],
        "etichetta": r["etichetta"],
        "creato_il": r["creato_il"].isoformat() if r["creato_il"] else None,
        "usato": bool(r["usato_il"]),
        "usato_il": r["usato_il"].isoformat() if r["usato_il"] else None,
        "usato_da": r["usato_nome"] or r["usato_email"],
    } for r in righe]
    return {"inviti": out}


@router.delete("/admin/inviti/{codice}", status_code=204)
def revoca_invito(codice: str, db: Session = Depends(get_session),
                  _admin: str = Depends(get_admin)):
    """Cancella un invito non ancora usato. Quelli gia' spesi restano, per
    tenere memoria di chi e' entrato con cosa."""
    db.execute(text("delete from inviti where codice = :c and usato_da is null"),
               {"c": codice})
    db.commit()
    return None


# --- Stato degli utenti (approva / blocca) ----------------------------------

@router.post("/admin/utenti/{user_id}/attiva")
def attiva_utente(user_id: str, db: Session = Depends(get_session),
                  _admin: str = Depends(get_admin)):
    """Approva un utente «in attesa» o riattiva uno «bloccato»: diventa attivo."""
    db.execute(text("update utenti set stato = 'attivo' where id = :i"), {"i": user_id})
    db.commit()
    return {"ok": True}


@router.post("/admin/utenti/{user_id}/blocca")
def blocca_utente(user_id: str, db: Session = Depends(get_session),
                  admin_uid: str = Depends(get_admin)):
    """Sospende un accesso: l'utente non entra piu', ma i suoi dati restano.
    Due paletti: non ci si blocca da soli, e non si blocca l'amministratore."""
    if str(user_id) == str(admin_uid):
        raise HTTPException(400, "Non puoi bloccare te stesso")
    row = db.execute(text("select email from utenti where id = :i"),
                     {"i": user_id}).mappings().first()
    if not row:
        raise HTTPException(404, "Utente non trovato")
    if (row["email"] or "").strip().lower() == settings.admin_email.strip().lower():
        raise HTTPException(400, "Non puoi bloccare l'amministratore")
    db.execute(text("update utenti set stato = 'bloccato' where id = :i"), {"i": user_id})
    db.commit()
    return {"ok": True}


# --- Richieste di accesso (chi non ha un invito) ----------------------------

class RichiestaIn(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    riferito_da: Optional[str] = None
    messaggio: Optional[str] = None


@router.post("/richiesta", status_code=201)
def crea_richiesta(body: RichiestaIn, db: Session = Depends(get_session)):
    """Rotta pubblica: chi apre l'app senza un invito valido lascia il proprio
    nome e da chi ha saputo dell'app. La richiesta arriva nel backoffice, dove
    l'amministratore decide se creare un invito."""
    nome = (body.nome or "").strip()
    email = (body.email or "").strip()
    if not nome and not email:
        raise HTTPException(400, "Scrivi almeno il tuo nome")
    db.execute(text(
        "insert into richieste_accesso (nome, email, riferito_da, messaggio)"
        " values (:n, :e, :r, :m)"
    ), {"n": nome or None, "e": email or None,
        "r": (body.riferito_da or None), "m": (body.messaggio or None)})
    db.commit()
    return {"ok": True}


@router.get("/admin/richieste")
def lista_richieste(db: Session = Depends(get_session), _admin: str = Depends(get_admin)):
    righe = db.execute(text(
        "select id, nome, email, riferito_da, messaggio, creato_il"
        " from richieste_accesso order by creato_il desc"
    )).mappings().all()
    return {"richieste": [{
        "id": str(r["id"]),
        "nome": r["nome"],
        "email": r["email"],
        "riferito_da": r["riferito_da"],
        "messaggio": r["messaggio"],
        "creato_il": r["creato_il"].isoformat() if r["creato_il"] else None,
    } for r in righe]}


@router.delete("/admin/richieste/{rid}", status_code=204)
def elimina_richiesta(rid: str, db: Session = Depends(get_session),
                      _admin: str = Depends(get_admin)):
    db.execute(text("delete from richieste_accesso where id = :i"), {"i": rid})
    db.commit()
    return None
