"""Prepara l'archivio al primo avvio: crea le tabelle (se non ci sono),
aggiorna lo schema (colonne nuove), mette la riga del progetto e il primo
amministratore. Si lancia da entrypoint.sh prima di avviare l'API. E' idempotente."""
import os
from sqlalchemy import text
from .db import engine, SessionLocal
from .config import settings
from .security import hash_password

SCHEMA = os.path.join(os.path.dirname(__file__), "schema.sql")

# Aggiornamenti di schema idempotenti: su un archivio gia' creato le "create table
# if not exists" non aggiungono le colonne nuove, quindi le aggiungiamo qui.
MIGRAZIONI = [
    "alter table minori add column if not exists scheda_link text",
    "alter table minori add column if not exists doc_modulo boolean not null default false",
    "alter table minori add column if not exists doc_identita_genitore boolean not null default false",
    "alter table minori add column if not exists doc_consenso_privacy boolean not null default false",
    "alter table minori add column if not exists doc_consenso_immagini boolean not null default false",
    "alter table minori add column if not exists doc_note text",
    "alter table minori add column if not exists scuola_id integer",
    "alter table operatori add column if not exists indirizzo text",
    "alter table operatori add column if not exists cap text",
    "alter table operatori add column if not exists comune text",
    "alter table operatori add column if not exists provincia text",
    "alter table operatori add column if not exists iban text",
    "alter table operatori add column if not exists tipo text",
    "alter table operatori add column if not exists ore_settimanali numeric(5,2)",
    "alter table operatori add column if not exists ritenuta numeric(5,4)",
]


def crea_tabelle():
    with open(SCHEMA, "r", encoding="utf-8") as f:
        sql = f.read()
    with engine.begin() as con:
        con.exec_driver_sql(sql)


def migra():
    with engine.begin() as con:
        for passo in MIGRAZIONI:
            con.exec_driver_sql(passo)


INCARICHI_SEED = [
    {"c": "A01", "d": "Animatore attivita' extrascolastica di socializzazione", "r": "Animatore", "t": 20, "f": None, "m": "19283", "p": "GdV", "o": 60},
    {"c": "A02", "d": "Tutor attivita' extrascolastica di socializzazione", "r": "Tutor", "t": 16, "f": None, "m": "19283", "p": "GdV", "o": 60},
    {"c": "S01", "d": "Esperto supporto scolastico minori con BES (11-14)", "r": "Esperto", "t": 20, "f": "11-14", "m": "19283", "p": "GdV", "o": 550},
    {"c": "S02", "d": "Tutor supporto scolastico minori con BES (11-14)", "r": "Tutor", "t": 16, "f": "11-14", "m": "19283", "p": "GdV", "o": 550},
    {"c": "S03", "d": "Esperto supporto apprendimento (15-17)", "r": "Esperto", "t": 20, "f": "15-17", "m": "19283", "p": "GdV", "o": 550},
    {"c": "S04", "d": "Tutor supporto apprendimento (15-17)", "r": "Tutor", "t": 16, "f": "15-17", "m": "19283", "p": "GdV", "o": 550},
    {"c": "V01", "d": "Esperto analisi e valutazione minori con BES", "r": "Esperto", "t": 40, "f": None, "m": "19258", "p": "GdV", "o": 160},
    {"c": "F01", "d": "Formatore corso BES - integrazione e inclusione", "r": "Formatore", "t": 30, "f": None, "m": "19254", "p": "GdV", "o": 40},
    {"c": "F02", "d": "Formatore corso ABA", "r": "Formatore", "t": 50, "f": None, "m": "19254", "p": "GdV", "o": 80},
    {"c": "TC", "d": "Tutor del corso (BES / ABA)", "r": "Tutor", "t": 16, "f": None, "m": "19254", "p": "GdV", "o": None},
    {"c": None, "d": "Laboratorio Percorsi di potenziamento - Esperto", "r": "Esperto", "t": 30, "f": None, "m": "19283", "p": "Bocs", "o": None},
    {"c": None, "d": "Laboratorio Percorsi di potenziamento - Tutor", "r": "Tutor", "t": 16, "f": None, "m": "19283", "p": "Bocs", "o": None},
]

SCUOLE_SEED = [
    {"n": "ICS Ignazio Buttitta", "co": "Bagheria", "g": "I"},
    {"n": "ICS Tommaso Aiello", "co": "Bagheria", "g": "I"},
    {"n": "ICS Falcone-Borsellino (Aspra)", "co": "Bagheria", "g": "I"},
    {"n": "ICS Carducci-Gramsci", "co": "Bagheria", "g": "I"},
    {"n": "ICS Giuseppe Bagnera", "co": "Bagheria", "g": "I"},
    {"n": "ICS Scianna", "co": "Bagheria", "g": "I"},
    {"n": "ICS Karol Wojtyla", "co": "Santa Flavia", "g": "I"},
    {"n": "ICS Rosario Livatino", "co": "Ficarazzi", "g": "I"},
    {"n": "Liceo Ginnasio F. Scaduto (Classico/Linguistico)", "co": "Bagheria", "g": "II"},
    {"n": "Liceo Scientifico G.P. D'Alessandro", "co": "Bagheria", "g": "II"},
    {"n": "Liceo Artistico Renato Guttuso", "co": "Bagheria", "g": "II"},
    {"n": "I.P.S.A.S.R. Salvo D'Acquisto", "co": "Bagheria", "g": "II"},
    {"n": "I.T.E.T. Don Luigi Sturzo", "co": "Bagheria", "g": "II"},
]


ATTIVITA_MINORI_SEED = [
    "Supporto scolastico minori con BES (11-14)",
    "Supporto apprendimento (15-17)",
    "Attivita' extrascolastica di socializzazione",
    "Valutazione e profilazione BES",
    "Laboratorio: dietro i social",
    "Laboratorio: scacchi",
    "Laboratorio: teatro sociale",
    "Laboratorio: cinema e narrazioni",
    "Laboratorio: grafica",
    "Laboratorio: video e montaggio",
    "Laboratorio: coprogettazione",
    "Laboratorio: affettivita'",
    "Laboratorio: matematica e logica",
]


def semina_attivita():
    db = SessionLocal()
    try:
        for nome in ATTIVITA_MINORI_SEED:
            db.execute(text(
                "insert into attivita (nome, tipo, attiva) "
                "select :n, 'minori', true where not exists (select 1 from attivita where lower(nome)=lower(:n))"
            ), {"n": nome})
        db.commit()
    finally:
        db.close()


def semina_catalogo():
    db = SessionLocal()
    try:
        n = db.execute(text("select count(*) c from catalogo_incarichi")).mappings().first()["c"]
        if not n:
            for r in INCARICHI_SEED:
                db.execute(text(
                    "insert into catalogo_incarichi (codice, descrizione, ruolo, tariffa, fascia, macro, partner, ore_monte) "
                    "values (:c, :d, :r, :t, :f, :m, :p, :o)"), r)
            print("[init] catalogo incarichi seminato:", len(INCARICHI_SEED))
        ns = db.execute(text("select count(*) c from scuole")).mappings().first()["c"]
        if not ns:
            for r in SCUOLE_SEED:
                db.execute(text("insert into scuole (nome, comune, grado) values (:n, :co, :g)"), r)
            print("[init] scuole seminate:", len(SCUOLE_SEED))
        db.commit()
    finally:
        db.close()


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
    migra()
    semina()
    semina_catalogo()
    semina_attivita()
    print("[init] archivio pronto")


if __name__ == "__main__":
    main()
