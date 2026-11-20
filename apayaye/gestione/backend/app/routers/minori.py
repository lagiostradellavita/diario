from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import text
from ..deps import get_session, richiedi
from ..regole import codice_fiscale as cf

router = APIRouter(prefix="/minori", tags=["minori"])

SOLO_UFFICIO = richiedi("ufficio", "admin")

# Valori ammessi dalla colonna "stato" (vincolo minori_stato_check). Tutto il resto -> NULL.
STATI_MINORE = {"Nuovo inserimento", "Concluso", "Rinunciatario"}

INSERT_MINORE = (
    "insert into minori (cognome, nome, codice_fiscale, stato_nascita, comune_nascita, "
    "provincia, genere, data_nascita, clp, scuola, ore_previste, stato, modulo_iscrizione) "
    "values (:co, :no, :cf, :sn, :cn, :pr, :ge, :dn, :clp, :sc, :op, :st, :mi)"
)
UPDATE_MINORE = (
    "update minori set cognome=:co, nome=:no, stato_nascita=:sn, comune_nascita=:cn, "
    "provincia=:pr, genere=:ge, data_nascita=:dn, clp=:clp, scuola=:sc, ore_previste=:op, "
    "stato=:st, modulo_iscrizione=:mi where id=:i"
)


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
    st = dati.stato if dati.stato in STATI_MINORE else None
    ge = dati.genere if dati.genere in ("M", "F") else c["genere"]
    row = db.execute(text(INSERT_MINORE + " returning id"),
        {"co": dati.cognome.strip(), "no": dati.nome.strip(), "cf": c["cf"],
         "sn": dati.stato_nascita, "cn": dati.comune_nascita, "pr": dati.provincia,
         "ge": ge, "dn": c["data_nascita"], "clp": dati.clp,
         "sc": dati.scuola, "op": dati.ore_previste, "st": st,
         "mi": dati.modulo_iscrizione}).mappings().first()
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
    st = dati.stato if dati.stato in STATI_MINORE else None
    ge = dati.genere if dati.genere in ("M", "F") else c["genere"]
    r = db.execute(text(
        "update minori set cognome=:co, nome=:no, codice_fiscale=:cf, stato_nascita=:sn, "
        "comune_nascita=:cn, provincia=:pr, genere=:ge, data_nascita=:dn, clp=:clp, scuola=:sc, "
        "ore_previste=:op, stato=:st, modulo_iscrizione=:mi, note=:nt where id=:i"
    ), {"co": dati.cognome.strip(), "no": dati.nome.strip(), "cf": c["cf"],
        "sn": dati.stato_nascita, "cn": dati.comune_nascita, "pr": dati.provincia,
        "ge": ge, "dn": c["data_nascita"], "clp": dati.clp,
        "sc": dati.scuola, "op": dati.ore_previste, "st": st,
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
    - Legge i codici fiscali gia' presenti in UNA sola interrogazione.
    - 'stato' fuori dai valori ammessi (o vuoto) -> NULL; 'genere' non M/F -> quello del CF
      (altrimenti il database rifiuta la riga per i vincoli di controllo).
    - In scrittura inserisce in blocco; se una riga da' problemi, le altre entrano lo stesso
      e quella si segnala (niente piu' 'tutto o niente')."""
    esistenti = {row["codice_fiscale"]: row["id"] for row in db.execute(
        text("select id, codice_fiscale from minori")).mappings().all()}
    scartati = []
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
        ge = r.get("genere")
        if ge not in ("M", "F"):
            ge = c["genere"]
        st = r.get("stato")
        if st not in STATI_MINORE:
            st = None
        campi = {"co": (r.get("cognome") or "").strip(), "no": (r.get("nome") or "").strip(),
                 "cf": c["cf"], "sn": r.get("stato_nascita") or None,
                 "cn": r.get("comune_nascita") or None, "pr": r.get("provincia") or None,
                 "ge": ge, "dn": c["data_nascita"], "clp": r.get("clp") or None,
                 "sc": r.get("scuola") or None, "op": r.get("ore_previste"), "st": st,
                 "mi": bool(r.get("modulo_iscrizione"))}
        if c["cf"] in esistenti:
            campi["i"] = esistenti[c["cf"]]
            da_aggiornare.append(campi)
        else:
            da_inserire.append(campi)
    creati, aggiornati = len(da_inserire), len(da_aggiornare)
    if not dati.prova:
        aggiornati = 0
        for campi in da_aggiornare:
            try:
                with db.begin_nested():
                    db.execute(text(UPDATE_MINORE), campi)
                aggiornati += 1
            except Exception as e:
                scartati.append({"riga": "-", "motivo": "non aggiornata (%s)" % type(e).__name__,
                                 "cognome": campi.get("co"), "nome": campi.get("no"), "cf": campi.get("cf")})
        inseriti = 0
        if da_inserire:
            try:
                with db.begin_nested():
                    db.execute(text(INSERT_MINORE), da_inserire)
                inseriti = len(da_inserire)
            except Exception:
                inseriti = 0
                for campi in da_inserire:
                    try:
                        with db.begin_nested():
                            db.execute(text(INSERT_MINORE), campi)
                        inseriti += 1
                    except Exception as e:
                        scartati.append({"riga": "-", "motivo": "non inserita (%s)" % type(e).__name__,
                                         "cognome": campi.get("co"), "nome": campi.get("no"), "cf": campi.get("cf")})
        creati = inseriti
    return {"prova": dati.prova, "creati": creati, "aggiornati": aggiornati,
            "scartati": scartati, "totale_righe": len(dati.righe)}
