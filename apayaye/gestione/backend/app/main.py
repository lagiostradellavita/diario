from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .config import settings
from .deps import utente_corrente
from .routers import auth, minori, export, rendicontazione, presenze, catalogo, indicatori, operatori, genitore

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


@app.middleware("http")
async def errori_visibili(request: Request, call_next):
    """Se una rotta va in errore, restituisce comunque un 500 CON le intestazioni
    CORS e il tipo+messaggio dell'errore. Senza questo, un errore interno arriva al
    browser senza intestazioni CORS e viene nascosto come 'Server non raggiungibile':
    non si capisce la causa."""
    try:
        return await call_next(request)
    except Exception as exc:
        resp = JSONResponse(
            status_code=500,
            content={"detail": "Errore interno del server: %s: %s" % (type(exc).__name__, str(exc)[:300])},
        )
        origin = request.headers.get("origin")
        if origin and origin in origins:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Credentials"] = "true"
        return resp


app.include_router(auth.router)
app.include_router(minori.router)
app.include_router(export.router)
app.include_router(rendicontazione.router)
app.include_router(presenze.router)
app.include_router(catalogo.router)
app.include_router(indicatori.router)
app.include_router(operatori.router)
app.include_router(genitore.router)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}


@app.get("/progetto", tags=["progetto"])
def progetto_info(u: dict = Depends(utente_corrente)):
    """Intestazione per i documenti (Allegato G, ricevute): soggetto, codici e
    dati del committente. Serve a chi ha fatto l'accesso."""
    return {
        "soggetto": settings.soggetto, "clp": settings.clp, "cup": settings.cup,
        "titolo": settings.titolo,
        "committente_piva": settings.committente_piva,
        "committente_cf": settings.committente_cf,
        "committente_sede": settings.committente_sede,
    }
