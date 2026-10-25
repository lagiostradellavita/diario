"""allegati: foto e PDF sincronizzati fra dispositivi

Revision ID: 0009
Revises: 0008

Come `documenti`, ma per i file (foto, PDF). A differenza di `documenti`, che
tiene testo JSON, qui il contenuto e' il file in base64 (testo). Una riga per
allegato, con l'id generato dall'app (lo stesso id che sta in IndexedDB sul
telefono). Tabella nuova e indipendente: non tocca nulla di esistente.

SQL grezzo come le altre migrazioni. Niente carattere percento, nessun
apostrofo dentro le stringhe SQL.
"""
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        create table if not exists allegati (
            user_id    uuid not null references utenti(id) on delete cascade,
            id         text not null,
            nome       text,
            tipo       text,
            cat        text,
            modulo     text,
            size       bigint,
            ts         bigint,
            contenuto  text not null,
            updated_at timestamptz not null default now(),
            primary key (user_id, id)
        );
    """)


def downgrade() -> None:
    op.execute("drop table if exists allegati;")
