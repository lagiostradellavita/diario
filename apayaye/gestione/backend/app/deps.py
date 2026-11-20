from typing import Optional
from fastapi import Header, HTTPException, Depends
from sqlalchemy import text
from .db import SessionLocal
from .security import decode_token


def get_session():
    """Una sessione di database per richiesta: commit se va bene, rollback se fallisce, chiusura sempre."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def utente_corrente(authorization: Optional[str] = Header(None), db=Depends(get_session)) -> dict:
    """L'utente dal token 'Bearer'. Senza token valido: 401. Se non e' attivo: 403.
    E' il guardiano di tutte le rotte della gestione: nessuno vede i dati dei minori senza login."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Autenticazione richiesta")
    try:
        payload = decode_token(authorization.split(" ", 1)[1])
    except Exception:
        raise HTTPException(status_code=401, detail="Sessione scaduta: rientra con la password")
    uid = payload.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="Token non valido")
    row = db.execute(text(
        "select id, email, ruolo, attivo, operatore_id, genitore_id from utenti where id = :i"
    ), {"i": uid}).mappings().first()
    if not row:
        raise HTTPException(status_code=401, detail="Utente non trovato")
    if not row["attivo"]:
        raise HTTPException(status_code=403, detail="Accesso sospeso dall'amministratore")
    return dict(row)


def richiedi(*ruoli):
    """Dipendenza che lascia passare solo certi ruoli. Es: Depends(richiedi('ufficio','admin'))."""
    def dep(u: dict = Depends(utente_corrente)) -> dict:
        if u["ruolo"] not in ruoli:
            raise HTTPException(status_code=403, detail="Non hai i permessi per questa operazione")
        return u
    return dep
