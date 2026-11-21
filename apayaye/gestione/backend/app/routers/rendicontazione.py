"""Rendicontazione: elenco dei file dentro una cartella del progetto su Dropbox.

Solo lettura e solo per chi ha fatto l'accesso (ufficio/admin): i nomi dei file
(anche dei minori) arrivano dal server al momento, e non stanno mai nel codice
pubblico. Se Dropbox non e' configurato, torna configurato=False e la schermata
mostra i collegamenti alle cartelle come prima.
"""
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query

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
