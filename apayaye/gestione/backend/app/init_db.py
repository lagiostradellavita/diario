"""Prepara l'archivio al primo avvio: crea le tabelle (se non ci sono),
mette la riga del progetto e il primo amministratore.
Si lancia da entrypoint.sh prima di avviare l'API. E' idempotente."""
import os
from sqlalchemy import text
from .db import engine, SessionLocal
from .config import settings
from .security import hash_password

SCHEMA = os.path.join(os.path.dirname(__file__), "schema.sql")


def crea_tabelle():
    with open(SCHEMA, "r", encoding="utf-8") as f:
        sql = f.read()
    with engine.begin() as con:
        con.exec_driver_sql(sql)


def semina():
    db = SessionLocal()
    try:
        n = db.execute(text("select count(*) c from progetto")).mappings().first()["c"]
        if not n:
            db.execute(text(
                "insert into progetto (soggetto, titolo, cup, clp, fascia_eta) "
                "values (:s, :t, :cup, :clp, :fe)"
            ), {"s": settings.soggetto, "t": settings.titolo, "cup": settings.cup,
                "clp": settings.clp, "fe": settings.fascia_eta})
        nu = db.execute(text("select count(*) c from utenti")).mappings().first()["c"]
        email = (settings.admin_email or "").strip().lower()
        pwd = settings.admin_password or ""
        if not nu and email and len(pwd) >= 8:
            db.execute(text(
                "insert into utenti (email, password_hash, ruolo, attivo) "
                "values (:e, :h, 'admin', true)"
            ), {"e": email, "h": hash_password(pwd)})
            print("[init] creato amministratore:", email)
        elif not nu:
            print("[init] nessun amministratore: imposta ADMIN_EMAIL e ADMIN_PASSWORD su Render")
        db.commit()
    finally:
        db.close()


def main():
    crea_tabelle()
    semina()
    print("[init] archivio pronto")


if __name__ == "__main__":
    main()
