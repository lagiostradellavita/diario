"""Anagrafica operatori: dati per la ricevuta (compenso) e la timbratura.
Lettura per chi ha l'accesso ufficio/admin; nessun dato personale finisce nel
codice, sta tutto in archivio. Un operatore si collega poi a un accesso con
POST /auth/utenti/{id}/collega, cosi' puo' entrare e timbrare."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from ..deps import get_session, richiedi

router = APIRouter(prefix="/operatori", tags=["operatori"])

SOLO_UFFICIO = richiedi("ufficio", "admin")

CAMPI = ("cognome, nome, codice_fiscale, voce, email, telefono, "
         "indirizzo, cap, comune, provincia, iban, tipo, ore_settimanali, ritenuta")


@router.get("")
def elenco(u: dict = Depends(SOLO_UFFICIO), db=Depends(get_session)):
    righe = db.execute(text(
        "select o.id, " + CAMPI + ", "
        "(select u.id from utenti u where u.operatore_id = o.id limit 1) as utente_id, "
        "(select u.email from utenti u where u.operatore_id = o.id limit 1) as utente_email "
        "from operatori o order by cognome, nome"
    )).mappings().all()
    return {"operatori": [dict(r) for r in righe]}


class OperatoreIn(BaseModel):
    cognome: str
    nome: str
    codice_fiscale: Optional[str] = None
    voce: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    indirizzo: Optional[str] = None
    cap: Optional[str] = None
    comune: Optional[str] = None
    provincia: Optional[str] = None
    iban: Optional[str] = None
    tipo: Optional[str] = None            # 'autonomo' | 'dipendente'
    ore_settimanali: Optional[float] = None
    ritenuta: Optional[float] = None      # es. 0.20 per il 20%


def _par(d: "OperatoreIn") -> dict:
    return {
        "cognome": d.cognome.strip(), "nome": d.nome.strip(), "cf": d.codice_fiscale,
        "voce": d.voce, "email": d.email, "tel": d.telefono, "ind": d.indirizzo,
        "cap": d.cap, "com": d.comune, "prov": d.provincia, "iban": d.iban,
        "tipo": d.tipo, "ore": d.ore_settimanali, "rit": d.ritenuta,
    }


@router.post("")
def crea(dati: OperatoreIn, u: dict = Depends(SOLO_UFFICIO), db=Depends(get_session)):
    if not dati.cognome.strip() or not dati.nome.strip():
        raise HTTPException(status_code=400, detail="Cognome e nome sono obbligatori")
    i = db.execute(text(
        "insert into operatori (cognome, nome, codice_fiscale, voce, email, telefono, "
        "indirizzo, cap, comune, provincia, iban, tipo, ore_settimanali, ritenuta) "
        "values (:cognome, :nome, :cf, :voce, :email, :tel, :ind, :cap, :com, :prov, "
        ":iban, :tipo, :ore, :rit) returning id"
    ), _par(dati)).scalar()
    return {"id": i}


@router.put("/{oid}")
def modifica(oid: int, dati: OperatoreIn, u: dict = Depends(SOLO_UFFICIO), db=Depends(get_session)):
    p = _par(dati)
    p["i"] = oid
    r = db.execute(text(
        "update operatori set cognome=:cognome, nome=:nome, codice_fiscale=:cf, voce=:voce, "
        "email=:email, telefono=:tel, indirizzo=:ind, cap=:cap, comune=:com, provincia=:prov, "
        "iban=:iban, tipo=:tipo, ore_settimanali=:ore, ritenuta=:rit where id=:i"
    ), p).rowcount
    if not r:
        raise HTTPException(status_code=404, detail="Operatore non trovato")
    return {"ok": True}
