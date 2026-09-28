from typing import Optional
from fastapi import Header, HTTPException, Depends
from sqlalchemy import text
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


def get_active_user_id(uid: str = Depends(get_user_id),
                       db=Depends(get_session)) -> str:
    """Come get_user_id, ma lascia passare solo chi ha l'accesso «attivo».

    E' il guardiano delle rotte dei dati: chi e' «in attesa» dell'ok
    dell'amministratore, o e' stato «bloccato», non legge ne' scrive l'archivio.
    Cosi' bloccare qualcuno gli chiude davvero l'app, non solo la schermata."""
    row = db.execute(text("select stato from utenti where id = :i"),
                     {"i": uid}).mappings().first()
    if not row:
        raise HTTPException(status_code=401, detail="Utente non trovato")
    stato = row["stato"] or "attivo"
    if stato == "in_attesa":
        raise HTTPException(status_code=403,
                            detail="Il tuo accesso e' in attesa dell'ok dell'amministratore")
    if stato != "attivo":
        raise HTTPException(status_code=403,
                            detail="Accesso sospeso dall'amministratore")
    return uid
