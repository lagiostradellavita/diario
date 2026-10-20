"""Leggo e Conto: accessi delle famiglie e archivio dei giochi

Revision ID: 0004
Revises: 0003

L'app dei giochi per bambini «Leggo e Conto» usa lo stesso servizio del Diario
ma tabelle sue: chi gioca non diventa un utente del Diario, e viceversa.

- giochi_utenti: l'adulto che chiede l'accesso (genitore, insegnante). Nasce
  'in_attesa' e gioca solo dopo l'ok dell'amministratore; 'bloccato' lo chiude
  fuori senza cancellare niente.
- giochi_accessi: un rigo per ogni ingresso, per vedere chi entra e quando.
- giochi_dati: i profili dei bambini e i loro risultati, lo stesso JSON che
  l'app tiene nel browser, cosi' si ritrovano da qualsiasi tablet.

SQL grezzo come le altre. Niente carattere percento, nessun apostrofo dentro
le stringhe SQL.
"""
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        create table if not exists giochi_utenti (
            id             uuid primary key default gen_random_uuid(),
            email          text not null unique,
            nome           text,
            telefono       text,
            messaggio      text,
            password_hash  text not null,
            stato          text not null default 'in_attesa',
            creato_il      timestamptz not null default now(),
            approvato_il   timestamptz,
            ultimo_accesso timestamptz,
            accessi        integer not null default 0
        );
    """)
    op.execute("""
        create table if not exists giochi_accessi (
            id          bigserial primary key,
            utente_id   uuid not null references giochi_utenti(id) on delete cascade,
            quando      timestamptz not null default now(),
            dispositivo text
        );
    """)
    op.execute("create index if not exists giochi_accessi_utente on giochi_accessi (utente_id, quando desc);")
    op.execute("""
        create table if not exists giochi_dati (
            utente_id     uuid primary key references giochi_utenti(id) on delete cascade,
            valore        jsonb not null,
            aggiornato_il timestamptz not null default now()
        );
    """)


def downgrade() -> None:
    op.execute("drop table if exists giochi_dati;")
    op.execute("drop table if exists giochi_accessi;")
    op.execute("drop table if exists giochi_utenti;")
