"""Leggo e Conto: l'informativa sulla privacy letta e accettata

Revision ID: 0008
Revises: 0007

Chi si iscrive legge l'informativa e la accetta; chi era gia' iscritto, o ha
l'account creato da un acquisto, la accetta al primo ingresso. Si tiene quale
versione e quando: se l'informativa cambia, l'app la ripropone.

- giochi_utenti.privacy_versione: la versione accettata («2026-10»).
- giochi_utenti.privacy_il: quando.

SQL grezzo come le altre. Niente carattere percento, nessun apostrofo dentro
le stringhe SQL.
"""
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("alter table giochi_utenti add column if not exists privacy_versione text;")
    op.execute("alter table giochi_utenti add column if not exists privacy_il timestamptz;")


def downgrade() -> None:
    op.execute("alter table giochi_utenti drop column if exists privacy_il;")
    op.execute("alter table giochi_utenti drop column if exists privacy_versione;")
