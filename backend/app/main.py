from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import auth, dati, giochi

app = FastAPI(title="Diario Salute API", version="0.1.0")

# Da quali siti il browser puo' chiamare l'API. In produzione e' il frontend su
# GitHub Pages (FRONTEND_ORIGIN); localhost serve solo per le prove in locale.
origins = [
    settings.frontend_origin,
    "http://localhost:8792",
    "http://127.0.0.1:8792",
    "http://localhost:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dati.router)
app.include_router(giochi.router)


@app.on_event("startup")
def password_amministratore_da_render():
    """Se l'amministratore non riesce piu' a entrare e la posta non e'
    configurata: su Render si scrive ADMIN_NUOVA_PASSWORD, il servizio riparte
    e quella diventa la sua password. Poi la variabile va tolta."""
    import os
    from sqlalchemy import text
    from .db import SessionLocal
    from .security import hash_password
    nuova = os.getenv("ADMIN_NUOVA_PASSWORD") or ""
    if len(nuova) < 8:
        return
    db = SessionLocal()
    try:
        n = db.execute(text("update utenti set password_hash = :h where lower(email) = :e"),
                       {"h": hash_password(nuova), "e": settings.admin_email.strip().lower()}).rowcount
        db.commit()
        print("[avvio] password dell'amministratore aggiornata da ADMIN_NUOVA_PASSWORD" if n
              else "[avvio] ADMIN_NUOVA_PASSWORD: amministratore non trovato")
    except Exception as e:                      # noqa: BLE001
        print("[avvio] ADMIN_NUOVA_PASSWORD non applicata:", e)
    finally:
        db.close()


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}
