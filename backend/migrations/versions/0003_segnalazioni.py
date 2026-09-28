"""suggerimenti e segnalazioni degli utenti

Revision ID: 0003
Revises: 0002

Una sola tabella per due cose: le richieste di nuove funzioni e le segnalazioni
di errori che gli utenti mandano dall'app. 'tipo' distingue ('funzione' |
'errore'); 'contesto' tiene, per gli errori, la versione dell'app e il
dispositivo, utili a capire il problema. 'stato' ('nuova' | 'fatta') serve
all'amministratore per spuntare quelle gia' gestite.

SQL grezzo come le altre migrazioni, niente carattere percento.
"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        create table if not exists segnalazioni (
            id        uuid primary key default gen_random_uuid(),
            user_id   uuid references utenti(id) on delete set null,
            tipo      text not null default 'funzione',
            testo     text not null,
            contesto  text,
            stato     text not null default 'nuova',
            creato_il timestamptz not null default now()
        );
    """)


def downgrade() -> None:
    op.execute("drop table if exists segnalazioni;")
