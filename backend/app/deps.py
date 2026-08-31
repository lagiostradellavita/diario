from typing import Optional
from fastapi import Header, HTTPException
from .db import SessionLocal
from .security import decode_token


def get_session():
    """Una sessione di database per richiesta: commit se tutto va bene,
    rollback se qualcosa fallisce, e chiusura sempre."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_user_id(authorization: Optional[str] = Header(None)) -> str:
    """Ricava l'utente dal token 'Bearer'. Senza un token valido, 401.

    E' il guardiano di tutte le rotte dei dati: nessuno legge o scrive
    l'archivio del Diario senza aver fatto il login."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Autenticazione richiesta")
    try:
        payload = decode_token(authorization.split(" ", 1)[1])
    except Exception:
        raise HTTPException(status_code=401, detail="Sessione scaduta: rientra con la password")
    uid = payload.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="Token non valido")
    return uid
