"""Catalogo del progetto: incarichi (ruoli retribuiti con tariffa) e scuole.
E' il riferimento per timbrature, Allegato G e ricevute. Lettura per chi ha
l'accesso; modifica solo ufficio/admin. Nessun dato personale."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from ..deps import get_session, utente_corrente, richiedi

router = APIRouter(prefix="/catalogo", tags=["catalogo"])

SOLO_UFFICIO = richiedi("ufficio", "admin")


@router.get("")
def leggi(u: dict = Depends(utente_corrente), db=Depends(get_session)):
    inc = db.execute(text(
        "select id, codice, descrizione, ruolo, tariffa, fascia, macro, partner, ore_monte, attivo "
        "from catalogo_incarichi order by partner, codice nulls last, descrizione"
    )).mappings().all()
    sc = db.execute(text(
        "select id, nome, comune, grado, email, pec, attiva from scuole order by grado, comune, nome"
    )).mappings().all()
    return {"incarichi": [dict(x) for x in inc], "scuole": [dict(x) for x in sc]}


# ---------- incarichi ----------
class IncaricoIn(BaseModel):
    codice: Optional[str] = None
    descrizione: str
    ruolo: Optional[str] = None
    tariffa: Optional[float] = None
    fascia: Optional[str] = None
    macro: Optional[str] = None
    partner: Optional[str] = None
    ore_monte: Optional[float] = None
    attivo: bool = True


@router.post("/incarichi")
def crea_incarico(dati: IncaricoIn, u: dict = Depends(SOLO_UFFICIO), db=Depends(get_session)):
    if not (dati.descrizione or "").strip():
        raise HTTPException(status_code=400, detail="La descrizione e' obbligatoria")
    i = db.execute(text(
        "insert into catalogo_incarichi (codice, descrizione, ruolo, tariffa, fascia, macro, partner, ore_monte, attivo) "
        "values (:c, :d, :r, :t, :f, :m, :p, :o, :a) returning id"
    ), {"c": dati.codice, "d": dati.descrizione.strip(), "r": dati.ruolo, "t": dati.tariffa,
        "f": dati.fascia, "m": dati.macro, "p": dati.partner, "o": dati.ore_monte, "a": dati.attivo}).scalar()
    return {"id": i}


@router.put("/incarichi/{iid}")
def modifica_incarico(iid: int, dati: IncaricoIn, u: dict = Depends(SOLO_UFFICIO), db=Depends(get_session)):
    r = db.execute(text(
        "update catalogo_incarichi set codice=:c, descrizione=:d, ruolo=:r, tariffa=:t, fascia=:f, "
        "macro=:m, partner=:p, ore_monte=:o, attivo=:a where id=:i"
    ), {"c": dati.codice, "d": dati.descrizione.strip(), "r": dati.ruolo, "t": dati.tariffa,
        "f": dati.fascia, "m": dati.macro, "p": dati.partner, "o": dati.ore_monte, "a": dati.attivo, "i": iid})
    if r.rowcount == 0:
        raise HTTPException(status_code=404, detail="Incarico non trovato")
    return {"ok": True}


@router.delete("/incarichi/{iid}")
def elimina_incarico(iid: int, u: dict = Depends(SOLO_UFFICIO), db=Depends(get_session)):
    db.execute(text("delete from catalogo_incarichi where id=:i"), {"i": iid})
    return {"ok": True}


# ---------- scuole ----------
class ScuolaIn(BaseModel):
    nome: str
    comune: Optional[str] = None
    grado: Optional[str] = None
    email: Optional[str] = None
    pec: Optional[str] = None
    attiva: bool = True


@router.post("/scuole")
def crea_scuola(dati: ScuolaIn, u: dict = Depends(SOLO_UFFICIO), db=Depends(get_session)):
    if not (dati.nome or "").strip():
        raise HTTPException(status_code=400, detail="Il nome e' obbligatorio")
    i = db.execute(text(
        "insert into scuole (nome, comune, grado, email, pec, attiva) values (:n, :co, :g, :e, :p, :a) returning id"
    ), {"n": dati.nome.strip(), "co": dati.comune, "g": dati.grado, "e": dati.email, "p": dati.pec, "a": dati.attiva}).scalar()
    return {"id": i}


@router.put("/scuole/{sid}")
def modifica_scuola(sid: int, dati: ScuolaIn, u: dict = Depends(SOLO_UFFICIO), db=Depends(get_session)):
    r = db.execute(text(
        "update scuole set nome=:n, comune=:co, grado=:g, email=:e, pec=:p, attiva=:a where id=:i"
    ), {"n": dati.nome.strip(), "co": dati.comune, "g": dati.grado, "e": dati.email, "p": dati.pec, "a": dati.attiva, "i": sid})
    if r.rowcount == 0:
        raise HTTPException(status_code=404, detail="Scuola non trovata")
    return {"ok": True}


@router.delete("/scuole/{sid}")
def elimina_scuola(sid: int, u: dict = Depends(SOLO_UFFICIO), db=Depends(get_session)):
    db.execute(text("delete from scuole where id=:i"), {"i": sid})
    return {"ok": True}
