from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import auth, dati

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


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}
