from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import text
from ..deps import get_session, richiedi
from ..regole import codice_fiscale as cf

router = APIRouter(prefix="/minori", tags=["minori"])

SOLO_UFFICIO = richiedi("ufficio", "admin")


class MinoreIn(BaseModel):
    cognome: str
    nome: str
    codice_fiscale: str
    stato_nascita: Optional[str] = None
    comune_nascita: Optional[str] = None
    provincia: Optional[str] = None
    genere: Optional[str] = None
    data_nascita: Optional[str] = None
    clp: Optional[str] = None
    scuola: Optional[str] = None
    ore_previste: Optional[float] = None
    stato: Optional[str] = None
    modulo_iscrizione: bool = False
    note: Optional[str] = None


@router.get("")
def elenco(u: dict = Depends(SOLO_UFFICIO), db=Depends(get_session)):
    righe = db.execute(text(
        "select id, cognome, nome, codice_fiscale, stato_nascita, comune_nascita, provincia, "
        "genere, data_nascita, clp, scuola, ore_previste, stato, modulo_iscrizione, note "
        "from minori order by cognome, nome"
    )).mappings().all()
    return [dict(r) for r in righe]


@router.post("")
def crea(dati: MinoreIn, u: dict = Depends(SOLO_UFFICIO), db=Depends(get_session)):
    c = cf.controlla(dati.codice_fiscale)
    if not c["ok"]:
        raise HTTPException(status_code=422, detail="; ".join(c["errori"]))
    gia = db.execute(text("select 1 from minori where codice_fiscale = :cf"),
                     {"cf": c["cf"]}).first()
    if gia:
        raise HTTPException(status_code=409, detail="Esiste gia' un minore con questo codice fiscale")
    row = db.execute(text(
        "insert into minori (cognome, nome, codice_fiscale, stato_nascita, comune_nascita, provincia, "
        "genere, data_nascita, clp, scuola, ore_previste, stato, modulo_iscrizione, note) "
        "values (:co, :no, :cf, :sn, :cn, :pr, :ge, :dn, :clp, :sc, :op, :st, :mi, :nt) returning id"
    ), {"co": dati.cognome.strip(), "no": dati.nome.strip(), "cf": c["cf"],
        "sn": dati.stato_nascita, "cn": dati.comune_nascita, "pr": dati.provincia,
        "ge": dati.genere or c["genere"], "dn": c["data_nascita"], "clp": dati.clp,
        "sc": dati.scuola, "op": dati.ore_previste, "st": dati.stato,
        "mi": dati.modulo_iscrizione, "nt": dati.note}).mappings().first()
    return {"id": row["id"], "ok": True}


@router.put("/{mid}")
def modifica(mid: int, dati: MinoreIn, u: dict = Depends(SOLO_UFFICIO), db=Depends(get_session)):
    c = cf.controlla(dati.codice_fiscale)
    if not c["ok"]:
        raise HTTPException(status_code=422, detail="; ".join(c["errori"]))
    altro = db.execute(text("select id from minori where codice_fiscale = :cf and id <> :i"),
                       {"cf": c["cf"], "i": mid}).first()
    if altro:
        raise HTTPException(status_code=409, detail="Un altro minore ha gia' questo codice fiscale")
    r = db.execute(text(
        "update minori set cognome=:co, nome=:no, codice_fiscale=:cf, stato_nascita=:sn, "
        "comune_nascita=:cn, provincia=:pr, genere=:ge, data_nascita=:dn, clp=:clp, scuola=:sc, "
        "ore_previste=:op, stato=:st, modulo_iscrizione=:mi, note=:nt where id=:i"
    ), {"co": dati.cognome.strip(), "no": dati.nome.strip(), "cf": c["cf"],
        "sn": dati.stato_nascita, "cn": dati.comune_nascita, "pr": dati.provincia,
        "ge": dati.genere or c["genere"], "dn": c["data_nascita"], "clp": dati.clp,
        "sc": dati.scuola, "op": dati.ore_previste, "st": dati.stato,
        "mi": dati.modulo_iscrizione, "nt": dati.note, "i": mid}).rowcount
    if not r:
        raise HTTPException(status_code=404, detail="Minore non trovato")
    return {"ok": True}


class ImportIn(BaseModel):
    prova: bool = True
    righe: List[Dict[str, Any]]


@router.post("/importa")
def importa(dati: ImportIn, u: dict = Depends(SOLO_UFFICIO), db=Depends(get_session)):
    """Import dall'Excel dei minori. prova=true mostra, prova=false scrive.
    Legge i codici fiscali gia' presenti in UNA sola interrogazione (niente una query
    per riga: su un database in rete erano centinaia di andate e ritorni, lenti e fragili)."""
    esistenti = {row["codice_fiscale"]: row["id"] for row in db.execute(
        text("select id, codice_fiscale from minori")).mappings().all()}
    creati, aggiornati, scartati = 0, 0, []
    visti = set()
    da_inserire, da_aggiornare = [], []
    for i, r in enumerate(dati.righe, start=1):
        c = cf.controlla(r.get("codice_fiscale"))
        if not c["ok"]:
            scartati.append({"riga": i, "motivo": "; ".join(c["errori"]),
                             "cognome": r.get("cognome"), "nome": r.get("nome")})
            continue
        if c["cf"] in visti:
            scartati.append({"riga": i, "motivo": "codice fiscale duplicato nel file", "cf": c["cf"]})
            continue
        visti.add(c["cf"])
        campi = {"co": (r.get("cognome") or "").strip(), "no": (r.get("nome") or "").strip(),
                 "cf": c["cf"], "sn": r.get("stato_nascita"), "cn": r.get("comune_nascita"),
                 "pr": r.get("provincia"), "ge": r.get("genere") or c["genere"],
                 "dn": c["data_nascita"], "clp": r.get("clp"), "sc": r.get("scuola"),
                 "op": r.get("ore_previste"), "st": r.get("stato"),
                 "mi": bool(r.get("modulo_iscrizione"))}
        if c["cf"] in esistenti:
            campi["i"] = esistenti[c["cf"]]
            da_aggiornare.append(campi)
            aggiornati += 1
        else:
            da_inserire.append(campi)
            creati += 1
    if not dati.prova:
        for campi in da_aggiornare:
            db.execute(text(
                "update minori set cognome=:co, nome=:no, stato_nascita=:sn, comune_nascita=:cn, "
                "provincia=:pr, genere=:ge, data_nascita=:dn, clp=:clp, scuola=:sc, ore_previste=:op, "
                "stato=:st, modulo_iscrizione=:mi where id=:i"), campi)
        if da_inserire:
            db.execute(text(
                "insert into minori (cognome, nome, codice_fiscale, stato_nascita, comune_nascita, "
                "provincia, genere, data_nascita, clp, scuola, ore_previste, stato, modulo_iscrizione) "
                "values (:co, :no, :cf, :sn, :cn, :pr, :ge, :dn, :clp, :sc, :op, :st, :mi)"), da_inserire)
    return {"prova": dati.prova, "creati": creati, "aggiornati": aggiornati,
            "scartati": scartati, "totale_righe": len(dati.righe)}
