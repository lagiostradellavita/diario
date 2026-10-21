"""Leggo e Conto: i dispositivi di ogni account, contro la condivisione

Revision ID: 0007
Revises: 0006

Un abbonamento vale per una famiglia, non per chiunque conosca la password.
Ogni telefono, tablet o computer che entra viene riconosciuto da un codice che
l'app crea la prima volta e tiene per se'. Oltre il limite del piano un
dispositivo nuovo entra solo se se ne scollega uno.

- giochi_dispositivi: i dispositivi di ogni account, con un nome leggibile
  («iPhone · Safari») e l'ultimo uso.
- giochi_utenti.tentativi_oltre: quante volte qualcuno ha provato a entrare
  da un dispositivo in piu'. Il backoffice segnala chi ne accumula.

SQL grezzo come le altre. Niente carattere percento, nessun apostrofo dentro
le stringhe SQL.
"""
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        create table if not exists giochi_dispositivi (
            id          uuid primary key default gen_random_uuid(),
            utente_id   uuid not null references giochi_utenti(id) on delete cascade,
            codice      text not null,
            nome        text,
            creato_il   timestamptz not null default now(),
            ultimo_uso  timestamptz not null default now(),
            unique (utente_id, codice)
        );
    """)
    op.execute("alter table giochi_utenti add column if not exists tentativi_oltre integer not null default 0;")


def downgrade() -> None:
    op.execute("alter table giochi_utenti drop column if exists tentativi_oltre;")
    op.execute("drop table if exists giochi_dispositivi;")
