from fastapi import APIRouter, Depends
from sqlalchemy import text
from ..deps import get_session, richiedi
from ..regole import regis

router = APIRouter(prefix="/export", tags=["export"])

SOLO_UFFICIO = richiedi("ufficio", "admin")


def _progetto(db):
    r = db.execute(text(
        "select soggetto, titolo, cup, clp, data_avvio, destinatari_previsti, fascia_eta, fase "
        "from progetto order by id limit 1")).mappings().first()
    return dict(r) if r else {}


def _minori_con_ore(db):
    ore = dict(db.execute(text(
        "select minore_id, coalesce(sum(ore),0) tot from presenze group by minore_id"
    )).all())
    righe = db.execute(text(
        "select id, cognome, nome, codice_fiscale, stato_nascita, comune_nascita, provincia, "
        "genere, data_nascita, ore_previste, stato from minori order by cognome, nome"
    )).mappings().all()
    out = []
    for m in righe:
        d = dict(m)
        d["ore_erogate"] = float(ore.get(m["id"], 0) or 0)
        out.append(d)
    return out


@router.get("/elenco-minori")
def elenco_minori(u: dict = Depends(SOLO_UFFICIO), db=Depends(get_session)):
    """Dati per il foglio 'Elenco minori destinatari' (formato ReGiS)."""
    prog = _progetto(db)
    minori = _minori_con_ore(db)
    prog["minori_coinvolti"] = len(minori)
    return {
        "colonne": regis.COLONNE,
        "matrice": regis.matrice(prog, minori),
        "problemi": regis.problemi(minori),
    }
