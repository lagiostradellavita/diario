import secrets
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from ..deps import get_session, utente_corrente, richiedi
from ..security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

RUOLI = {"admin", "ufficio", "operatore", "genitore"}


class LoginIn(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
def login(dati: LoginIn, db=Depends(get_session)):
    row = db.execute(text(
        "select id, password_hash, ruolo, attivo, deve_cambiare_password "
        "from utenti where lower(email) = :e"
    ), {"e": dati.email.strip().lower()}).mappings().first()
    if not row or not verify_password(dati.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Email o password non corretti")
    if not row["attivo"]:
        raise HTTPException(status_code=403, detail="Accesso sospeso dall'amministratore")
    token = create_access_token(row["id"], row["ruolo"])
    return {"token": token, "ruolo": row["ruolo"],
            "deve_cambiare_password": row["deve_cambiare_password"]}


@router.get("/me")
def me(u: dict = Depends(utente_corrente)):
    return {"id": u["id"], "email": u["email"], "ruolo": u["ruolo"]}


class CambiaPasswordIn(BaseModel):
    attuale: str
    nuova: str


@router.post("/cambia-password")
def cambia_password(dati: CambiaPasswordIn, u: dict = Depends(utente_corrente), db=Depends(get_session)):
    if len(dati.nuova) < 8:
        raise HTTPException(status_code=422, detail="La nuova password deve avere almeno 8 caratteri")
    row = db.execute(text("select password_hash from utenti where id = :i"),
                     {"i": u["id"]}).mappings().first()
    if not row or not verify_password(dati.attuale, row["password_hash"]):
        raise HTTPException(status_code=401, detail="La password attuale non e' corretta")
    db.execute(text("update utenti set password_hash = :h, deve_cambiare_password = false where id = :i"),
               {"h": hash_password(dati.nuova), "i": u["id"]})
    return {"ok": True}


class InvitoIn(BaseModel):
    email: EmailStr
    ruolo: str
    operatore_id: Optional[int] = None
    genitore_id: Optional[int] = None


@router.post("/inviti")
def invita(dati: InvitoIn, u: dict = Depends(richiedi("admin")), db=Depends(get_session)):
    if dati.ruolo not in RUOLI:
        raise HTTPException(status_code=422, detail="Ruolo non valido")
    gia = db.execute(text("select 1 from utenti where lower(email) = :e"),
                     {"e": dati.email.strip().lower()}).first()
    if gia:
        raise HTTPException(status_code=409, detail="Esiste gia' un utente con questa email")
    provvisoria = secrets.token_urlsafe(9)
    db.execute(text(
        "insert into utenti (email, password_hash, ruolo, attivo, deve_cambiare_password, operatore_id, genitore_id) "
        "values (:e, :h, :r, true, true, :op, :ge)"
    ), {"e": dati.email.strip().lower(), "h": hash_password(provvisoria), "r": dati.ruolo,
        "op": dati.operatore_id, "ge": dati.genitore_id})
    return {"ok": True, "email": dati.email, "ruolo": dati.ruolo, "password_provvisoria": provvisoria}


@router.get("/utenti")
def utenti(u: dict = Depends(richiedi("admin")), db=Depends(get_session)):
    righe = db.execute(text(
        "select id, email, ruolo, attivo, operatore_id, genitore_id, creato_il "
        "from utenti order by creato_il desc"
    )).mappings().all()
    return [dict(r) for r in righe]


class StatoIn(BaseModel):
    attivo: bool


@router.post("/utenti/{uid}/attivo")
def cambia_stato(uid: int, dati: StatoIn, u: dict = Depends(richiedi("admin")), db=Depends(get_session)):
    if uid == u["id"] and not dati.attivo:
        raise HTTPException(status_code=400, detail="Non puoi sospendere te stesso")
    r = db.execute(text("update utenti set attivo = :a where id = :i"),
                   {"a": dati.attivo, "i": uid}).rowcount
    if not r:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    return {"ok": True}
