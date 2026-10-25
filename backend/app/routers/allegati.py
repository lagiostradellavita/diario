from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..deps import get_session, get_active_user_id as get_user_id

router = APIRouter(prefix="/allegati", tags=["allegati"])

# Gli allegati (foto e PDF) dei vari moduli dell'app. A differenza di /dati, che
# tiene testo JSON, qui il contenuto e' un file, salvato in base64. Per non
# scaricare megabyte a ogni sincronizzazione, l'elenco NON restituisce il
# contenuto: il frontend elenca cosa c'e' sul cloud, confronta con quello che ha
# gia' sul dispositivo, e scarica (o carica) solo i file mancanti.


@router.get("")
def elenco(db: Session = Depends(get_session), uid: str = Depends(get_user_id)):
    """Solo i dati descrittivi di ogni allegato dell'utente, senza il contenuto."""
    righe = db.execute(text(
        "select id, nome, tipo, cat, modulo, size, ts from allegati where user_id = :u"
    ), {"u": uid}).mappings().all()
    return [{"id": r["id"], "nome": r["nome"], "tipo": r["tipo"], "cat": r["cat"],
             "modulo": r["modulo"], "size": r["size"], "ts": r["ts"]} for r in righe]


@router.get("/{aid}")
def leggi(aid: str, db: Session = Depends(get_session), uid: str = Depends(get_user_id)):
    """Un singolo allegato col suo contenuto (base64)."""
    r = db.execute(text(
        "select id, nome, tipo, cat, modulo, size, ts, contenuto from allegati"
        " where user_id = :u and id = :i"
    ), {"u": uid, "i": aid}).mappings().first()
    if not r:
        raise HTTPException(404, "Allegato non trovato")
    return {"id": r["id"], "nome": r["nome"], "tipo": r["tipo"], "cat": r["cat"],
            "modulo": r["modulo"], "size": r["size"], "ts": r["ts"], "b64": r["contenuto"]}


@router.put("/{aid}")
def salva(aid: str, body: dict = Body(...),
          db: Session = Depends(get_session), uid: str = Depends(get_user_id)):
    """Carica (o aggiorna) un allegato. Il corpo contiene i dati descrittivi e
    il file in base64 nel campo 'b64'."""
    if not aid or len(aid) > 200:
        raise HTTPException(400, "Id non valido")
    b64 = body.get("b64") or ""
    if not b64:
        raise HTTPException(400, "Contenuto mancante")
    db.execute(text(
        "insert into allegati (user_id, id, nome, tipo, cat, modulo, size, ts, contenuto, updated_at)"
        " values (:u, :i, :nome, :tipo, :cat, :modulo, :size, :ts, :c, now())"
        " on conflict (user_id, id)"
        " do update set nome = excluded.nome, tipo = excluded.tipo, cat = excluded.cat,"
        " modulo = excluded.modulo, size = excluded.size, ts = excluded.ts,"
        " contenuto = excluded.contenuto, updated_at = now()"
    ), {"u": uid, "i": aid, "nome": body.get("nome"), "tipo": body.get("tipo"),
        "cat": body.get("cat"), "modulo": body.get("modulo"),
        "size": body.get("size"), "ts": body.get("ts"), "c": b64})
    return {"id": aid, "ok": True}


@router.delete("/{aid}", status_code=204)
def elimina(aid: str, db: Session = Depends(get_session), uid: str = Depends(get_user_id)):
    db.execute(text("delete from allegati where user_id = :u and id = :i"),
               {"u": uid, "i": aid})
    return None
