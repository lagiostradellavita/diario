"""Indicatori ReGiS calcolati dai minori: C10 (11-17 che ricevono istruzione/
formazione), C14 (15-17 che ricevono sostegno) e T0158 (nr minori supportati,
cumulato), disaggregati per sesso. La fascia si ricava dalla data di nascita.
Solo ufficio/admin."""
from datetime import date, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text

from ..deps import get_session, richiedi

router = APIRouter(prefix="/indicatori", tags=["indicatori"])

SOLO_UFFICIO = richiedi("ufficio", "admin")


def _eta(dn, rif: date):
    if not dn:
        return None
    try:
        d = dn if isinstance(dn, date) else datetime.strptime(str(dn)[:10], "%Y-%m-%d").date()
    except Exception:
        return None
    return rif.year - d.year - ((rif.month, rif.day) < (d.month, d.day))


def _fascia(eta):
    if eta is None:
        return "senza_data"
    if 11 <= eta <= 14:
        return "11-14"
    if 15 <= eta <= 17:
        return "15-17"
    return "fuori"


@router.get("")
def indicatori(u: dict = Depends(SOLO_UFFICIO), db=Depends(get_session)):
    rif = date.today()
    righe = db.execute(text("select data_nascita, genere, stato from minori")).mappings().all()

    def vuoto():
        return {"M": 0, "F": 0, "altro": 0, "tot": 0}

    per_fascia = {"11-14": vuoto(), "15-17": vuoto(), "fuori": vuoto(), "senza_data": vuoto()}
    tot = vuoto()
    rinunciatari = 0
    for r in righe:
        if (r["stato"] or "") == "Rinunciatario":
            rinunciatari += 1
            continue
        g = r["genere"] if r["genere"] in ("M", "F") else "altro"
        f = _fascia(_eta(r["data_nascita"], rif))
        per_fascia[f][g] += 1
        per_fascia[f]["tot"] += 1
        tot[g] += 1
        tot["tot"] += 1

    c10 = {g: per_fascia["11-14"][g] + per_fascia["15-17"][g] for g in ("M", "F", "altro", "tot")}
    c14 = {g: per_fascia["15-17"][g] for g in ("M", "F", "altro", "tot")}
    return {
        "riferimento": rif.isoformat(),
        "totale_beneficiari": tot["tot"],
        "rinunciatari": rinunciatari,
        "per_genere": tot,
        "per_fascia": per_fascia,
        "C10": c10,                 # minori 11-17 che ricevono istruzione/formazione
        "C14": c14,                 # minori 15-17 che ricevono sostegno
        "T0158": tot["tot"],        # nr minori supportati (cumulato)
        "fuori_fascia": per_fascia["fuori"]["tot"],
        "senza_data": per_fascia["senza_data"]["tot"],
    }
