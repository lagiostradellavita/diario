"""recupero della password con un link via email

Revision ID: 0005
Revises: 0004

Chi ha dimenticato la password chiede un link; il link porta un codice che
vale un'ora e una volta sola. Nel database si salva solo l'impronta del
codice (sha256), mai il codice: chi legge la tabella non puo' usarlo.

'ambito' dice di quale archivio e' l'utente: 'diario' (utenti) o 'giochi'
(giochi_utenti). Niente chiave esterna perche' le tabelle sono due.

SQL grezzo come le altre. Niente carattere percento, nessun apostrofo dentro
le stringhe SQL.
"""
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        create table if not exists recuperi_password (
            id          uuid primary key default gen_random_uuid(),
            ambito      text not null,
            utente_id   uuid not null,
            token_hash  text not null unique,
            creato_il   timestamptz not null default now(),
            scade_il    timestamptz not null,
            usato_il    timestamptz
        );
    """)
    op.execute("create index if not exists recuperi_utente on recuperi_password (ambito, utente_id);")


def downgrade() -> None:
    op.execute("drop table if exists recuperi_password;")
