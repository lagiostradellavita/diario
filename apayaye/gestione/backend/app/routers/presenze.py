"""Presenze e documenti lato OPERATORE.

L'operatore (collegato a un record di `operatori` tramite utenti.operatore_id)
registra le presenze dei minori per una sessione e carica i propri documenti
(foto del foglio firma, Allegato G). Vede e tocca solo cio' che e' suo; gli
amministratori avranno viste d'insieme a parte.
"""
from datetime import date as Date
from base64 import b64decode
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import text

from ..deps import get_session, utente_corrente

router = APIRouter(prefix="/presenze", tags=["presenze"])

TIPI_DOC = {"foglio_firma", "allegato_g", "altro"}
MAX_BYTES = 10 * 1024 * 1024  # 10 MB a file


def _op_id(u: dict) -> int:
    oid = u.get("operatore_id")
    if not oid:
        raise HTTPException(
            status_code=400,
            detail="Il tuo accesso non e' collegato a un operatore. Chiedi all'ufficio di collegarlo.",
        )
    return oid


def _mia_sessione(db, sid: int, oid: int) -> None:
    r = db.execute(
        text("select 1 from operatore_ore where sessione_id=:s and operatore_id=:o"),
        {"s": sid, "o": oid},
    ).first()
    if not r:
        raise HTTPException(status_code=403, detail="Questa sessione non e' tua.")


@router.get("/contesto")
def contesto(u: dict = Depends(utente_corrente), db=Depends(get_session)):
    """Tutto quello che serve alla schermata dell'operatore: chi sei, le attivita'
    disponibili, l'elenco dei minori da spuntare, le tue ultime sessioni."""
    oid = _op_id(u)
    op = db.execute(text("select id, cognome, nome from operatori where id=:i"), {"i": oid}).mappings().first()
    attivita = db.execute(text("select id, nome from attivita where attiva order by nome")).mappings().all()
    minori = db.execute(text(
        "select id, cognome, nome from minori "
        "where stato is distinct from 'Rinunciatario' order by cognome, nome"
    )).mappings().all()
    sess = db.execute(text(
        "select s.id, s.data, s.ore, a.nome as attivita, "
        "(select count(*) from presenze p where p.sessione_id = s.id) as presenti "
        "from sessioni s "
        "join operatore_ore oo on oo.sessione_id = s.id "
        "join attivita a on a.id = s.attivita_id "
        "where oo.operatore_id = :i order by s.data desc, s.id desc limit 30"
    ), {"i": oid}).mappings().all()
    return {
        "operatore": dict(op) if op else None,
        "attivita": [dict(x) for x in attivita],
        "minori": [dict(x) for x in minori],
        "sessioni": [dict(x) for x in sess],
    }


class SessioneIn(BaseModel):
    attivita_id: Optional[int] = None
    attivita_nome: Optional[str] = None   # se non c'e' l'id: si cerca o si crea per nome
    data: Date
    ore: float = 0
    note: Optional[str] = None


@router.post("/sessione")
def crea_sessione(dati: SessioneIn, u: dict = Depends(utente_corrente), db=Depends(get_session)):
    oid = _op_id(u)
    aid = dati.attivita_id
    if aid:
        if not db.execute(text("select 1 from attivita where id=:a"), {"a": aid}).first():
            raise HTTPException(status_code=400, detail="Attivita' non trovata")
    else:
        nome = (dati.attivita_nome or "").strip()
        if not nome:
            raise HTTPException(status_code=400, detail="Scegli o scrivi un'attivita'")
        row = db.execute(text("select id from attivita where lower(nome)=lower(:n)"), {"n": nome}).first()
        aid = row[0] if row else db.execute(text(
            "insert into attivita (nome, attiva) values (:n, true) returning id"
        ), {"n": nome}).scalar()
    sid = db.execute(text(
        "insert into sessioni (attivita_id, data, ore, operatore_id, note) "
        "values (:a, :d, :o, :op, :n) returning id"
    ), {"a": aid, "d": dati.data, "o": dati.ore, "op": oid, "n": dati.note}).scalar()
    db.execute(text(
        "insert into operatore_ore (sessione_id, operatore_id, ore) values (:s, :o, :h) "
        "on conflict (sessione_id, operatore_id) do update set ore = excluded.ore"
    ), {"s": sid, "o": oid, "h": dati.ore})
    return {"id": sid}


@router.get("/sessione/{sid}")
def leggi_sessione(sid: int, u: dict = Depends(utente_corrente), db=Depends(get_session)):
    oid = _op_id(u)
    _mia_sessione(db, sid, oid)
    s = db.execute(text(
        "select s.id, s.data, s.ore, s.attivita_id, a.nome as attivita "
        "from sessioni s join attivita a on a.id = s.attivita_id where s.id = :s"
    ), {"s": sid}).mappings().first()
    pres = db.execute(text("select minore_id, ore from presenze where sessione_id=:s"), {"s": sid}).mappings().all()
    return {"sessione": dict(s) if s else None, "presenze": [dict(x) for x in pres]}


class PresenzaIn(BaseModel):
    minore_id: int
    ore: float = 0


class PresenzeIn(BaseModel):
    presenze: List[PresenzaIn]


@router.post("/sessione/{sid}/presenze")
def salva_presenze(sid: int, dati: PresenzeIn, u: dict = Depends(utente_corrente), db=Depends(get_session)):
    """Chi era presente a questa sessione (sostituisce l'elenco precedente)."""
    oid = _op_id(u)
    _mia_sessione(db, sid, oid)
    db.execute(text("delete from presenze where sessione_id=:s"), {"s": sid})
    n = 0
    for p in dati.presenze:
        db.execute(text(
            "insert into presenze (sessione_id, minore_id, ore) values (:s, :m, :o)"
        ), {"s": sid, "m": p.minore_id, "o": p.ore})
        n += 1
    return {"ok": True, "n": n}


class DocumentoIn(BaseModel):
    tipo: str
    titolo: Optional[str] = None
    periodo: Optional[str] = None
    nome_file: str
    mime: Optional[str] = None
    contenuto_base64: str


@router.post("/documento")
def carica_documento(dati: DocumentoIn, u: dict = Depends(utente_corrente), db=Depends(get_session)):
    """Carica un documento dell'operatore (foglio firma, Allegato G). Il contenuto
    arriva in base64; si salva dentro l'archivio, non su Dropbox."""
    oid = _op_id(u)
    if dati.tipo not in TIPI_DOC:
        raise HTTPException(status_code=400, detail="Tipo di documento non valido")
    try:
        raw = b64decode(dati.contenuto_base64.split(",")[-1])
    except Exception:
        raise HTTPException(status_code=400, detail="File non leggibile")
    if not raw:
        raise HTTPException(status_code=400, detail="File vuoto")
    if len(raw) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="File troppo grande (massimo 10 MB)")
    did = db.execute(text(
        "insert into documenti (tipo, titolo, operatore_id, periodo, nome_file, mime, dimensione, contenuto, caricato_da) "
        "values (:t, :ti, :op, :pe, :nf, :mi, :di, :co, :ca) returning id"
    ), {
        "t": dati.tipo, "ti": dati.titolo or dati.nome_file, "op": oid, "pe": dati.periodo,
        "nf": dati.nome_file, "mi": dati.mime, "di": len(raw), "co": raw, "ca": u["id"],
    }).scalar()
    return {"id": did}


@router.get("/documenti")
def miei_documenti(u: dict = Depends(utente_corrente), db=Depends(get_session)):
    oid = _op_id(u)
    rows = db.execute(text(
        "select id, tipo, titolo, periodo, nome_file, dimensione, caricato_il "
        "from documenti where operatore_id = :o order by caricato_il desc"
    ), {"o": oid}).mappings().all()
    return {"documenti": [dict(x) for x in rows]}


@router.delete("/documento/{did}")
def elimina_documento(did: int, u: dict = Depends(utente_corrente), db=Depends(get_session)):
    oid = _op_id(u)
    r = db.execute(text("select operatore_id from documenti where id=:i"), {"i": did}).mappings().first()
    if not r or r["operatore_id"] != oid:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    db.execute(text("delete from documenti where id=:i"), {"i": did})
    return {"ok": True}


@router.get("/documento/{did}")
def scarica_documento(did: int, u: dict = Depends(utente_corrente), db=Depends(get_session)):
    oid = _op_id(u)
    r = db.execute(text(
        "select nome_file, mime, contenuto, operatore_id from documenti where id=:i"
    ), {"i": did}).mappings().first()
    if not r or r["operatore_id"] != oid:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    return Response(
        content=bytes(r["contenuto"]),
        media_type=r["mime"] or "application/octet-stream",
        headers={"Content-Disposition": 'inline; filename="%s"' % (r["nome_file"] or "documento")},
    )
