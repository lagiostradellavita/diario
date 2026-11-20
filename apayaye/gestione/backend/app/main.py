from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}
