"""schema iniziale: l'utente e l'archivio dei dati

Revision ID: 0001
Revises:

Due sole tabelle. `utenti` tiene la persona che entra (email + password
hashata). `documenti` e' l'archivio: una riga per ogni «chiave» (un modulo
dell'app) con dentro il suo JSON. E' lo stesso contenuto che oggi sta nel
localStorage del telefono, ma condiviso tra i dispositivi e al sicuro.
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("create extension if not exists pgcrypto;")
    op.execute("""
        create table if not exists utenti (
            id            uuid primary key default gen_random_uuid(),
            email         text not null unique,
            nome          text,
            password_hash text not null,
            created_at    timestamptz not null default now()
        );
    """)
    op.execute("""
        create table if not exists documenti (
            user_id    uuid not null references utenti(id) on delete cascade,
            chiave     text not null,
            valore     jsonb not null,
            updated_at timestamptz not null default now(),
            primary key (user_id, chiave)
        );
    """)


def downgrade() -> None:
    op.execute("drop table if exists documenti;")
    op.execute("drop table if exists utenti;")
