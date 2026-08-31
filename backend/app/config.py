from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/diario"
    secret_key: str = "dev-secret-change-me"          # in produzione: variabile d'ambiente su Render
    access_token_ttl_min: int = 60 * 24 * 30          # durata del login: 30 giorni (app personale)
    # Da quale sito il browser puo' chiamare l'API. In produzione e' il frontend
    # su GitHub Pages; in sviluppo aggiungiamo localhost.
    frontend_origin: str = "https://lagiostradellavita.github.io"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("database_url")
    @classmethod
    def _normalize(cls, v: str) -> str:
        # I provider cloud (Neon) danno URL "postgres://" o "postgresql://":
        # SQLAlchemy richiede il driver esplicito "postgresql+psycopg://".
        if v.startswith("postgres://"):
            v = "postgresql+psycopg://" + v[len("postgres://"):]
        elif v.startswith("postgresql://"):
            v = "postgresql+psycopg://" + v[len("postgresql://"):]
        return v


settings = Settings()
