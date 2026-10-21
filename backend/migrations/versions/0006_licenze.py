"""Leggo e Conto: piani, scadenze e collegamento con Odoo

Revision ID: 0006
Revises: 0005

L'accesso non e' piu' solo approvato o no: ha un piano e, se e' a tempo, una
scadenza.

- piano: 'sociale' (famiglie seguite dalla cooperativa, gratis e senza
  scadenza), 'prova' (30 giorni dalla registrazione), 'base', 'premium'.
- scadenza: fino a quando si gioca; vuota vuol dire senza scadenza. Chi
  supera la scadenza resta 'attivo' ma viene fermato con «abbonamento scaduto»:
  i profili dei bambini non si toccano, e un rinnovo riapre tutto.
- odoo_rif: il numero dell'abbonamento su Odoo che ha dato l'accesso.
- giochi_odoo_eventi: ogni avviso arrivato da Odoo, con com'e' andato. Serve a
  capire cosa e' successo quando una famiglia dice di aver pagato e non entra.

Chi era gia' attivo prima di questa migrazione resta com'era: piano
'sociale', senza scadenza.

SQL grezzo come le altre. Niente carattere percento, nessun apostrofo dentro
le stringhe SQL.
"""
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("alter table giochi_utenti add column if not exists piano text not null default 'sociale';")
    op.execute("alter table giochi_utenti add column if not exists scadenza timestamptz;")
    op.execute("alter table giochi_utenti add column if not exists odoo_rif text;")
    op.execute("""
        create table if not exists giochi_odoo_eventi (
            id          bigserial primary key,
            ricevuto_il timestamptz not null default now(),
            email       text,
            rif         text,
            esito       text not null,
            corpo       jsonb
        );
    """)
    op.execute("create index if not exists giochi_odoo_eventi_quando on giochi_odoo_eventi (ricevuto_il desc);")


def downgrade() -> None:
    op.execute("drop table if exists giochi_odoo_eventi;")
    op.execute("alter table giochi_utenti drop column if exists odoo_rif;")
    op.execute("alter table giochi_utenti drop column if exists scadenza;")
    op.execute("alter table giochi_utenti drop column if exists piano;")
