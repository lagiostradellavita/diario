"""Vista GENITORE: un genitore collegato a un record di `genitori`
(utenti.genitore_id) vede i propri figli e le loro presenze. Vede solo i minori
collegati a lui, niente altro."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from ..deps import get_session, utente_corrente, richiedi

router = APIRouter(prefix="/genitore", tags=["genitore"])

SOLO_UFFICIO = richiedi("ufficio", "admin")


@router.get("/elenco")
def elenco(u: dict = Depends(SOLO_UFFICIO), db=Depends(get_session)):
    """Elenco dei genitori (per collegarli a un accesso). Solo ufficio/admin."""
    righe = db.execute(text(
        "select id, cognome, nome, email from genitori order by cognome, nome"
    )).mappings().all()
    return {"genitori": [dict(x) for x in righe]}


def _gen_id(u: dict) -> int:
    gid = u.get("genitore_id")
    if not gid:
        raise HTTPException(
            status_code=400,
            detail="Il tuo accesso non e' collegato a un genitore. Chiedi all'ufficio di collegarlo.",
        )
    return gid


def _mio_figlio(db, gid: int, mid: int) -> None:
    r = db.execute(text(
        "select 1 from minore_genitore where genitore_id=:g and minore_id=:m"
    ), {"g": gid, "m": mid}).first()
    if not r:
        raise HTTPException(status_code=403, detail="Questo minore non e' collegato a te.")


@router.get("/figli")
def figli(u: dict = Depends(utente_corrente), db=Depends(get_session)):
    gid = _gen_id(u)
    righe = db.execute(text(
        "select m.id, m.cognome, m.nome, mg.rapporto, "
        "(select coalesce(sum(p.ore),0) from presenze p where p.minore_id = m.id) as ore_totali, "
        "(select count(*) from presenze p where p.minore_id = m.id) as presenze "
        "from minore_genitore mg join minori m on m.id = mg.minore_id "
        "where mg.genitore_id = :g order by m.cognome, m.nome"
    ), {"g": gid}).mappings().all()
    return {"figli": [dict(x) for x in righe]}


@router.get("/figlio/{mid}/presenze")
def presenze_figlio(mid: int, u: dict = Depends(utente_corrente), db=Depends(get_session)):
    gid = _gen_id(u)
    _mio_figlio(db, gid, mid)
    righe = db.execute(text(
        "select s.data, a.nome as attivita, p.ore "
        "from presenze p join sessioni s on s.id = p.sessione_id "
        "join attivita a on a.id = s.attivita_id "
        "where p.minore_id = :m order by s.data desc, s.id desc"
    ), {"m": mid}).mappings().all()
    return {"presenze": [dict(x) for x in righe]}
