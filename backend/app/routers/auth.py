import json
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


class LoginIn(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: str
    nome: Optional[str] = None


@router.get("/stato")
def stato(db: Session = Depends(get_session)):
    """Dice al frontend se l'accesso e' gia' stato creato: la prima volta mostra
    «Crea accesso», dopo mostra «Entra». Non richiede login."""
    quanti = db.execute(text("select count(*) from utenti")).scalar()
    return {"configurato": bool(quanti), "multiutente": True}


@router.post("/register", response_model=TokenOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_session)):
    """Crea un nuovo utente. Ogni persona ha il proprio account e i propri dati,
    separati da quelli degli altri (l'archivio e' gia' diviso per utente)."""
    email = (body.email or "").strip().lower()
    if "@" not in email:
        raise HTTPException(400, "Serve un indirizzo email valido")
    esiste = db.execute(text("select 1 from utenti where email = :e"), {"e": email}).first()
    if esiste:
        raise HTTPException(409, "Questa email e' gia' registrata. Entra con la tua password.")
    db.execute(text(
        "insert into utenti (email, nome, password_hash) values (:e, :n, :h)"
    ), {"e": email, "n": body.nome, "h": hash_password(body.password)})
    uid = db.execute(text("select id from utenti where email = :e"), {"e": email}).scalar()
    return {"access_token": create_access_token(uid), "email": email, "nome": body.nome}


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_session)):
    email = (body.email or "").strip().lower()
    row = db.execute(text(
        "select id, email, nome, password_hash from utenti where email = :e"
    ), {"e": email}).mappings().first()
    if not row or not row["password_hash"] or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(401, "Email o password non corretti")
    return {"access_token": create_access_token(row["id"]), "email": row["email"], "nome": row["nome"]}


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
    row = db.execute(text("select id, email, nome from utenti where id = :i"),
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
        "select id, email, nome, created_at from utenti order by created_at"
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
        out.append({
            "email": u["email"],
            "nome": u["nome"],
            "iscritto": u["created_at"].isoformat() if u["created_at"] else None,
            "funzioni": funzioni,
            "moduli_con_dati": nmod,
        })
    return {"totale": len(out), "utenti": out}
