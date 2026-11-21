"""Fascicoli ReGiS: dal lavoro dell'app (ore -> Ricevuta e Allegato G) piu' i
bonifici e gli F24 che stanno su Dropbox, monta i fascicoli numerati e li scrive
nella cartella ReGiS. Solo ufficio/admin. Niente dati di persone nel codice:
tutto viene dall'archivio e da Dropbox al momento."""
from datetime import datetime
from base64 import b64encode

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text

from ..deps import get_session, richiedi
from ..config import settings
from .. import dropbox_ls, fascicoli_regis as FR
from ..pdf_semplice import genera, Riga

router = APIRouter(prefix="/fascicoli-regis", tags=["fascicoli"])

SOLO_UFFICIO = richiedi("ufficio", "admin")


def _fonte_path() -> str:
    return settings.fascicoli_fonte_path or (settings.apayaye_root + "/08 - Rendicontazione/Tutti i bonifici")


def _dest_path() -> str:
    return settings.fascicoli_dest_path or (
        settings.apayaye_root + "/08 - Rendicontazione/09 - Fascicoli per ReGis/00 - Giustificativi per ReGiS 2026")


def _dest_mese_base() -> str:
    return settings.fascicoli_dest_mese_base or (settings.apayaye_root + "/08 - Rendicontazione/2026")


def _cartella_mese(mm: int, anno: int) -> str:
    """Sottocartella per mese, nello stile della cartella 2026: 'MM - Mese AAAA'."""
    nome = FR.MESI_LUNGO[mm].capitalize() if 1 <= mm <= 12 else str(mm)
    return "%s/%02d - %s %d" % (_dest_mese_base(), mm, nome, anno)


def _intest() -> dict:
    return {"titolo": settings.titolo, "clp": settings.clp, "cup": settings.cup,
            "soggetto": settings.soggetto, "committente_piva": settings.committente_piva,
            "committente_cf": settings.committente_cf}


def _voci(db, mese: str) -> list:
    """Le voci del mese (AAAA-MM): un lavoratore autonomo con ore timbrate."""
    try:
        anno, mm = int(mese[:4]), int(mese[5:7])
    except Exception:
        raise HTTPException(status_code=400, detail="Mese non valido (atteso AAAA-MM)")
    ops = db.execute(text(
        "select id, cognome, nome, codice_fiscale, indirizzo, cap, comune, provincia, iban, ritenuta "
        "from operatori where lower(coalesce(tipo,'')) = 'autonomo' order by cognome, nome"
    )).mappings().all()
    voci = []
    for o in ops:
        rr = db.execute(text(
            "select t.entrata, t.uscita, i.descrizione as incarico, i.tariffa, s.nome as scuola, "
            "extract(epoch from (t.uscita - t.entrata))/3600.0 as ore "
            "from timbrature t left join catalogo_incarichi i on i.id=t.incarico_id "
            "left join scuole s on s.id=t.scuola_id "
            "where t.operatore_id=:o and t.uscita is not null and to_char(t.entrata,'YYYY-MM')=:m "
            "order by t.entrata"
        ), {"o": o["id"], "m": mese}).mappings().all()
        if not rr:
            continue
        lordo, ore, righe = 0.0, 0.0, []
        for t in rr:
            h = float(t["ore"] or 0)
            ore += h
            if t["tariffa"] is not None:
                lordo += h * float(t["tariffa"])
            ent = t["entrata"]
            usc = t["uscita"]
            righe.append({
                "giorno": ent.strftime("%d/%m/%Y") if isinstance(ent, datetime) else str(ent)[:10],
                "ent": ent.strftime("%H:%M") if isinstance(ent, datetime) else "",
                "usc": usc.strftime("%H:%M") if isinstance(usc, datetime) else "",
                "ore": round(h, 2), "incarico": t["incarico"] or "", "scuola": t["scuola"] or "",
            })
        if lordo <= 0:
            continue
        rit = float(o["ritenuta"]) if o["ritenuta"] is not None else 0.20
        ritimp = round(lordo * rit, 2)
        indir = " — ".join([x for x in [o["indirizzo"], ((o["cap"] or "") + " " + (o["comune"] or "")).strip(), o["provincia"]] if x and str(x).strip()])
        voci.append({
            "operatore_id": o["id"], "cognome": o["cognome"] or "", "nome": o["nome"] or "",
            "codice_fiscale": o["codice_fiscale"], "indirizzo": indir, "iban": o["iban"],
            "mese": mm, "anno": anno, "ore": round(ore, 2),
            "lordo": round(lordo, 2), "rit": rit, "ritenuta": ritimp, "netto": round(lordo - ritimp, 2),
            "righe": righe,
        })
    return voci


def _fonti():
    """Legge i nomi di 'Tutti i bonifici' e li analizza. [] se Dropbox non c'e'."""
    if not dropbox_ls.disponibile():
        return None
    out = []
    for f in dropbox_ls.elenca(_fonte_path()):
        if f["cartella"]:
            continue
        a = FR.analizza_fonte(f["nome"], f["path"])
        if a:
            out.append(a)
    return out


@router.get("/voci")
def voci(mese: str = Query(...), u: dict = Depends(SOLO_UFFICIO), db=Depends(get_session)):
    """Il prospetto delle voci del mese, con lo stato di bonifico e F24 su Dropbox
    (se Dropbox e' collegato)."""
    vv = _voci(db, mese)
    conf = dropbox_ls.disponibile()
    errore = None
    fonti = None
    if conf:
        try:
            fonti = _fonti()
        except Exception as e:
            errore = "%s: %s" % (type(e).__name__, str(e)[:200])
    out = []
    for i, v in enumerate(vv):
        bon = FR.abbina(v, fonti, "bonifico") if fonti else None
        f24 = FR.abbina(v, fonti, "f24") if fonti else None
        out.append({
            "n": i + 1, "operatore_id": v["operatore_id"], "cognome": v["cognome"], "nome": v["nome"],
            "codice_fiscale": v["codice_fiscale"], "ore": v["ore"], "lordo": v["lordo"],
            "ritenuta": v["ritenuta"], "netto": v["netto"],
            "bonifico": bool(bon), "bonifico_nome": bon["nome"] if bon else None,
            "f24": bool(f24), "f24_nome": f24["nome"] if f24 else None,
        })
    return {"mese": mese, "configurato": conf, "errore": errore,
            "dropbox_fonte": _fonte_path(), "dropbox_dest": _dest_path(),
            "dropbox_dest_mese": _dest_mese_base(), "voci": out}


@router.get("/anteprima")
def anteprima(mese: str = Query(...), operatore_id: int = Query(...),
              u: dict = Depends(SOLO_UFFICIO), db=Depends(get_session)):
    """Il PDF Ricevuta + Allegato G di una voce (per vederlo prima di scrivere)."""
    vv = [v for v in _voci(db, mese) if v["operatore_id"] == operatore_id]
    if not vv:
        raise HTTPException(status_code=404, detail="Nessuna ora per questo operatore nel mese")
    pdf = _pdf_ricevuta_allegato(vv[0])
    from fastapi.responses import Response
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": 'inline; filename="ricevuta_allegatoG.pdf"'})


def _pdf_ricevuta_allegato(v: dict) -> bytes:
    intest = _intest()
    righe = FR.righe_ricevuta(v, intest) + [Riga("", 11, False, 24)] + FR.righe_allegato_g(v, intest)
    return genera(righe)


@router.post("/scrivi")
def scrivi(mese: str = Query(...), u: dict = Depends(SOLO_UFFICIO), db=Depends(get_session)):
    """Monta i fascicoli del mese e li SCRIVE nella cartella ReGiS su Dropbox.
    Per ogni voce: genera 'Ricevuta e Allegato G' (PDF), copia bonifico e F24.
    Richiede Dropbox collegato con permesso di scrittura."""
    if not dropbox_ls.disponibile():
        raise HTTPException(status_code=400, detail="Dropbox non e' collegato: impostalo su Render (vedi COLLEGARE-DROPBOX.md).")
    vv = _voci(db, mese)
    if not vv:
        raise HTTPException(status_code=400, detail="Nessuna voce (lavoratori autonomi con ore) in questo mese")
    try:
        fonti = _fonti()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Non riesco a leggere i bonifici su Dropbox: %s" % str(e)[:200])
    mm, anno = vv[0]["mese"], vv[0]["anno"]
    # Due destinazioni: l'elenco numerato dei Fascicoli ReGiS E la cartella 2026
    # divisa per mesi (richiesta di Gianluca, 'sia dentro 2026 divisa per mesi,
    # sia dentro fascicoli per Regis'). La carica crea da sola le cartelle mancanti.
    dests = [_dest_path(), _cartella_mese(mm, anno)]
    esito = []
    for i, v in enumerate(vv):
        n = i + 1
        riga = {"n": n, "operatore": (v["cognome"] + " " + v["nome"]).strip(), "scritti": [], "mancanti": [], "errore": None}
        try:
            pdf = _pdf_ricevuta_allegato(v)
            bon = FR.abbina(v, fonti, "bonifico")
            f24 = FR.abbina(v, fonti, "f24") if (v["ritenuta"] and v["ritenuta"] > 0) else None
            if not bon:
                riga["mancanti"].append("bonifico")
            if v["ritenuta"] and v["ritenuta"] > 0 and not f24:
                riga["mancanti"].append("F24")
            for dest in dests:
                nome2 = FR.nome_regis(n, v, 2, "Ricevuta e Allegato G", v["lordo"])
                dropbox_ls.carica(dest, nome2, pdf)
                if bon:
                    nome1 = FR.nome_regis(n, v, 1, "Bonifico", bon.get("importo") or v["netto"])
                    dropbox_ls.copia(bon["path"], dest.rstrip("/") + "/" + nome1)
                if f24:
                    nome3 = FR.nome_regis(n, v, 3, "F24", f24.get("importo") or v["ritenuta"])
                    dropbox_ls.copia(f24["path"], dest.rstrip("/") + "/" + nome3)
            # Riepilogo dei pezzi scritti (uguali nelle due cartelle).
            riga["scritti"].append("Ricevuta e Allegato G")
            if bon:
                riga["scritti"].append("Bonifico")
            if f24:
                riga["scritti"].append("F24")
        except Exception as e:
            riga["errore"] = "%s: %s" % (type(e).__name__, str(e)[:200])
        esito.append(riga)
    return {"mese": mese, "dest": dests, "esito": esito}
