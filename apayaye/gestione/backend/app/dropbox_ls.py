"""Lettura (sola lettura) di una cartella del progetto su Dropbox.

Serve alla schermata Rendicontazione: mostra i file VERI dentro le cartelle del
progetto Apayaye a chi ha fatto l'accesso, senza scriverne mai i nomi nel codice
pubblico. Usa solo la libreria standard (nessuna dipendenza nuova).

Configurazione (variabili d'ambiente su Render):
  - DROPBOX_REFRESH_TOKEN + DROPBOX_APP_KEY + DROPBOX_APP_SECRET   (consigliato)
  - oppure DROPBOX_TOKEN (token diretto, scade: solo per prove)
  - DROPBOX_PATH_ROOT: id del namespace, se la cartella del progetto e' condivisa
Se niente di tutto questo e' configurato, `disponibile()` torna False e la
schermata continua a mostrare i collegamenti alle cartelle (come prima).
"""
import json
import time
import base64
import urllib.request
import urllib.parse

from .config import settings

_TOKEN = {"val": None, "exp": 0.0}
_TIMEOUT = 20


def disponibile() -> bool:
    return bool(
        settings.dropbox_token
        or (settings.dropbox_refresh_token and settings.dropbox_app_key and settings.dropbox_app_secret)
    )


def _access_token() -> str:
    # Token diretto (prove rapide).
    if settings.dropbox_token:
        return settings.dropbox_token
    # Refresh token: si scambia con un access token a vita breve, tenuto in cache.
    now = time.time()
    if _TOKEN["val"] and _TOKEN["exp"] - 60 > now:
        return _TOKEN["val"]
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": settings.dropbox_refresh_token,
    }).encode()
    auth = base64.b64encode(
        ("%s:%s" % (settings.dropbox_app_key, settings.dropbox_app_secret)).encode()
    ).decode()
    req = urllib.request.Request(
        "https://api.dropbox.com/oauth2/token",
        data=body,
        headers={
            "Authorization": "Basic " + auth,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
        d = json.loads(r.read().decode())
    _TOKEN["val"] = d["access_token"]
    _TOKEN["exp"] = now + int(d.get("expires_in", 14400))
    return _TOKEN["val"]


def _headers(tok: str) -> dict:
    h = {"Authorization": "Bearer " + tok, "Content-Type": "application/json"}
    if settings.dropbox_path_root:
        # Cartella condivisa in uno spazio team: va indicato il namespace radice.
        h["Dropbox-API-Path-Root"] = json.dumps({".tag": "root", "root": settings.dropbox_path_root})
    return h


def _post(url: str, payload: dict, tok: str) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=_headers(tok))
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
        return json.loads(r.read().decode())


def elenca(path: str) -> list:
    """Elenca i figli diretti di una cartella. Torna [{nome, cartella, path}]."""
    if not disponibile():
        raise RuntimeError("Dropbox non configurato")
    tok = _access_token()
    out = []
    url = "https://api.dropboxapi.com/2/files/list_folder"
    payload = {"path": path, "recursive": False, "limit": 200,
               "include_non_downloadable_files": True}
    while True:
        d = _post(url, payload, tok)
        for e in d.get("entries", []):
            out.append({
                "nome": e.get("name", ""),
                "cartella": e.get(".tag") == "folder",
                "path": e.get("path_display") or e.get("path_lower") or "",
            })
        if not d.get("has_more"):
            break
        url = "https://api.dropboxapi.com/2/files/list_folder/continue"
        payload = {"cursor": d["cursor"]}
    return out
