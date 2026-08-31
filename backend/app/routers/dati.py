import json
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..deps import get_session, get_user_id

router = APIRouter(prefix="/dati", tags=["dati"])

# L'archivio del Diario e' un semplice deposito «chiave -> valore» per utente:
# ogni modulo dell'app (storia clinica, parametri, fumo, ...) e' una chiave, e
# il suo contenuto e' il JSON che oggi sta nel localStorage del telefono. Cosi'
# il backend non deve conoscere la forma di ogni modulo, e nuovi moduli non
# richiedono nuove tabelle.


@router.get("")
def leggi_tutto(db: Session = Depends(get_session), uid: str = Depends(get_user_id)):
    """Tutto l'archivio dell'utente: {chiave: valore, ...}. Il frontend lo
    carica una volta al login e lo tiene in memoria."""
    righe = db.execute(text(
        "select chiave, valore from documenti where user_id = :u"
    ), {"u": uid}).mappings().all()
    return {r["chiave"]: r["valore"] for r in righe}


@router.put("/{chiave}")
def salva(chiave: str, valore: Any = Body(...),
          db: Session = Depends(get_session), uid: str = Depends(get_user_id)):
    """Salva o aggiorna un pezzo dell'archivio (es. la chiave 'salute-storia'
    con dentro tutta la storia clinica). Il corpo della richiesta e' il JSON
    del modulo."""
    if not chiave or len(chiave) > 200:
        raise HTTPException(400, "Chiave non valida")
    db.execute(text(
        "insert into documenti (user_id, chiave, valore, updated_at)"
        " values (:u, :k, cast(:v as jsonb), now())"
        " on conflict (user_id, chiave)"
        " do update set valore = excluded.valore, updated_at = now()"
    ), {"u": uid, "k": chiave, "v": json.dumps(valore)})
    return {"chiave": chiave, "ok": True}


@router.delete("/{chiave}", status_code=204)
def elimina(chiave: str, db: Session = Depends(get_session), uid: str = Depends(get_user_id)):
    db.execute(text("delete from documenti where user_id = :u and chiave = :k"),
               {"u": uid, "k": chiave})
    return None
