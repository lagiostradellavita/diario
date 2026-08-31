from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..deps import get_session, get_user_id
from ..security import hash_password, verify_password, create_access_token

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
    return {"configurato": bool(quanti)}


@router.post("/register", response_model=TokenOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_session)):
    """Primo e unico accesso: crea l'utente. Dopo il primo la porta si chiude
    (e' un'app personale: c'e' una persona sola)."""
    quanti = db.execute(text("select count(*) from utenti")).scalar()
    if quanti:
        raise HTTPException(403, "L'accesso e' gia' stato creato. Entra con la tua password.")
    email = (body.email or "").strip().lower()
    if "@" not in email:
        raise HTTPException(400, "Serve un indirizzo email valido")
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
