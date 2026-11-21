"""Rendicontazione: elenco dei file dentro una cartella del progetto su Dropbox.

Solo lettura e solo per chi ha fatto l'accesso (ufficio/admin): i nomi dei file
(anche dei minori) arrivano dal server al momento, e non stanno mai nel codice
pubblico. Se Dropbox non e' configurato, torna configurato=False e la schermata
mostra i collegamenti alle cartelle come prima.
"""
from base64 import b64decode
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..deps import richiedi
from ..config import settings
from .. import dropbox_ls

router = APIRouter(prefix="/rendicontazione", tags=["rendicontazione"])

SOLO_UFFICIO = richiedi("ufficio", "admin")


def _url(path: str, cartella: bool) -> str:
    base = "https://www.dropbox.com/" + ("home" if cartella else "preview")
    return base + "/" + quote(path.lstrip("/"), safe="/")


@router.get("/documenti")
def documenti(path: str = Query(..., description="Percorso della cartella nel progetto"),
              u: dict = Depends(SOLO_UFFICIO)):
    root = settings.apayaye_root
    # Sicurezza: si puo' leggere SOLO dentro la cartella del progetto Apayaye,
    # e nessun percorso con ".." (niente risalite).
    if ".." in path.split("/"):
        raise HTTPException(status_code=403, detail="Percorso non valido")
    if not (path == root or path.startswith(root + "/")):
        raise HTTPException(status_code=403, detail="Cartella fuori dal progetto")
    if not dropbox_ls.disponibile():
        return {"configurato": False, "file": []}
    try:
        voci = dropbox_ls.elenca(path)
    except Exception as exc:
        return {"configurato": True, "errore": "%s: %s" % (type(exc).__name__, str(exc)[:200]), "file": []}
    # Niente cartelle "Old"; cartelle prima dei file, in ordine di nome.
    voci = [v for v in voci if v["nome"].lower() != "old"]
    voci.sort(key=lambda v: (not v["cartella"], v["nome"].lower()))
    for v in voci:
        v["url"] = _url(v["path"], v["cartella"])
    return {"configurato": True, "file": voci}


class CaricaIn(BaseModel):
    path: str            # cartella di destinazione, DENTRO il progetto Apayaye
    nome_file: str
    contenuto_base64: str


@router.post("/carica")
def carica(dati: CaricaIn, u: dict = Depends(SOLO_UFFICIO)):
    """Carica un nuovo file dentro una cartella del progetto su Dropbox.
    Solo ufficio/admin. Scrive solo dentro la cartella del progetto, niente '..',
    nome file senza barre. Non sovrascrive (add + autorename)."""
    root = settings.apayaye_root
    p = dati.path
    if ".." in p.split("/"):
        raise HTTPException(status_code=403, detail="Percorso non valido")
    if not (p == root or p.startswith(root + "/")):
        raise HTTPException(status_code=403, detail="Cartella fuori dal progetto")
    nf = (dati.nome_file or "").strip()
    if not nf or "/" in nf or "\\" in nf:
        raise HTTPException(status_code=400, detail="Nome file non valido")
    if not dropbox_ls.disponibile():
        raise HTTPException(status_code=400, detail="Dropbox non collegato")
    try:
        raw = b64decode(dati.contenuto_base64.split(",")[-1])
    except Exception:
        raise HTTPException(status_code=400, detail="File non leggibile")
    if not raw:
        raise HTTPException(status_code=400, detail="File vuoto")
    if len(raw) > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File troppo grande (massimo 15 MB)")
    try:
        res = dropbox_ls.carica(p, nf, raw)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Dropbox: %s: %s" % (type(exc).__name__, str(exc)[:200]))
    return {"ok": True, "path": res["path"], "nome": res["nome"], "url": _url(res["path"], False)}
