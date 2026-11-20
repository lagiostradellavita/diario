from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import auth, minori, export

app = FastAPI(title="Apayaye Gestione API", version="0.1.0")

# Da quali siti il browser puo' chiamare l'API (il frontend su GitHub Pages; localhost per le prove).
origins = [
    settings.frontend_origin,
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(minori.router)
app.include_router(export.router)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}
