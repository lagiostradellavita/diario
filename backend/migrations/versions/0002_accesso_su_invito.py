"""accesso su invito con conferma dell'amministratore

Revision ID: 0002
Revises: 0001

Apre l'app a piu' persone, ma solo su invito e con l'ok dell'amministratore.

- utenti.stato: 'attivo' | 'in_attesa' | 'bloccato'. Chi c'e' gia' (compreso
  l'amministratore) diventa 'attivo', cosi' nessuno resta chiuso fuori. I nuovi
  iscritti nascono 'in_attesa' finche' l'amministratore non li approva.
- inviti: la chiave usa-e-getta che apre la registrazione, creata solo
  dall'amministratore. 'codice' unico; 'usato_da'/'usato_il' si riempiono quando
  l'invito viene speso.
- richieste_accesso: chi non ha un invito lascia nome + da chi ha saputo
  dell'app; l'amministratore le vede nel backoffice e decide.

SQL grezzo come la 0001. Niente carattere percento, nessun apostrofo dentro le
stringhe SQL: i valori di stato sono parole semplici.
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Stato dell'utente. default 'attivo' -> i gia' iscritti non si bloccano.
    op.execute("alter table utenti add column if not exists stato text not null default 'attivo';")

    op.execute("""
        create table if not exists inviti (
            id         uuid primary key default gen_random_uuid(),
            codice     text not null unique,
            etichetta  text,
            creato_da  uuid references utenti(id) on delete set null,
            creato_il  timestamptz not null default now(),
            usato_da   uuid references utenti(id) on delete set null,
            usato_il   timestamptz
        );
    """)

    op.execute("""
        create table if not exists richieste_accesso (
            id          uuid primary key default gen_random_uuid(),
            nome        text,
            email       text,
            riferito_da text,
            messaggio   text,
            creato_il   timestamptz not null default now()
        );
    """)


def downgrade() -> None:
    op.execute("drop table if exists richieste_accesso;")
    op.execute("drop table if exists inviti;")
    op.execute("alter table utenti drop column if exists stato;")
