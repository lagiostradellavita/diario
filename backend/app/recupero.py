"""Il link «password dimenticata», per il Diario e per Leggo e Conto.

Il codice nel link vale un'ora e si usa una volta sola. Nel database finisce
solo la sua impronta sha256: il codice vero esiste soltanto nell'email.
Chiedere un altro link annulla quelli vecchi ancora aperti.
"""
import hashlib
import os
import secrets
from sqlalchemy import text

DIARIO_URL = os.getenv("DIARIO_URL") or "https://lagiostradellavita.github.io/diario/"
DURATA_MINUTI = 60


def _impronta(codice: str) -> str:
    return hashlib.sha256(codice.encode()).hexdigest()


def crea(db, ambito: str, utente_id, minuti: int = DURATA_MINUTI) -> str:
    db.execute(text(
        "update recuperi_password set usato_il = now()"
        " where ambito = :a and utente_id = :u and usato_il is null"
    ), {"a": ambito, "u": utente_id})
    codice = secrets.token_urlsafe(24)
    db.execute(text(
        "insert into recuperi_password (ambito, utente_id, token_hash, scade_il)"
        " values (:a, :u, :h, now() + make_interval(mins => :m))"
    ), {"a": ambito, "u": utente_id, "h": _impronta(codice), "m": minuti})
    return codice


def usa(db, ambito: str, codice: str):
    """L'utente del codice, se il codice e' buono; lo segna come usato."""
    row = db.execute(text(
        "update recuperi_password set usato_il = now()"
        " where token_hash = :h and ambito = :a and usato_il is null and scade_il > now()"
        " returning utente_id"
    ), {"h": _impronta(codice or ""), "a": ambito}).first()
    return row[0] if row else None


def testo_email(nome, link: str, app: str) -> str:
    return (f"Ciao {nome or ''},\n\nqualcuno ha chiesto di cambiare la password di {app} con questa email.\n"
            f"Per sceglierne una nuova apri questo link entro un'ora:\n\n{link}\n\n"
            "Se non sei stato tu, ignora questo messaggio: la password resta quella di prima.\n")
