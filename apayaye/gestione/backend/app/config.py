from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/apayaye"
    secret_key: str = "dev-secret-change-me"          # su Render: variabile d'ambiente
    access_token_ttl_min: int = 60 * 12               # 12 ore (dati di minori: sessione corta)
    frontend_origin: str = "https://lagiostradellavita.github.io"
    # Primo amministratore, creato al primo avvio se l'archivio e' vuoto (poi si toglie).
    admin_email: str = ""
    admin_password: str = ""
    # Dati del progetto (per l'export ReGiS).
    clp: str = "2024-PE4-00024"
    cup: str = "J54C25000220004"
    soggetto: str = "La Giostra della Vita Societa' Cooperativa Sociale a r.l."
    titolo: str = "Apayaye"
    fascia_eta: str = "11-17 anni"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("database_url")
    @classmethod
    def _normalize(cls, v: str) -> str:
        # Neon da' URL "postgres://" o "postgresql://"; SQLAlchemy vuole "postgresql+psycopg://".
        if v.startswith("postgres://"):
            v = "postgresql+psycopg://" + v[len("postgres://"):]
        elif v.startswith("postgresql://"):
            v = "postgresql+psycopg://" + v[len("postgresql://"):]
        return v


settings = Settings()
