from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import settings

# prepare_threshold=None: niente prepared statement lato server, cosi' la
# connessione "pooled" di Neon (PgBouncer) non da' errori del tipo
# "prepared statement _pg3_0 already exists". pool_pre_ping + pool_recycle
# reggono il risveglio del compute Neon e lo spegnimento del servizio Render
# (piano free), riaprendo le connessioni diventate stantie.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"prepare_threshold": None},
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
