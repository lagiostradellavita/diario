"""Presenze e documenti lato OPERATORE.

L'operatore (collegato a un record di `operatori` tramite utenti.operatore_id)
registra le presenze dei minori per una sessione e carica i propri documenti
(foto del foglio firma, Allegato G). Vede e tocca solo cio' che e' suo; gli
amministratori avranno viste d'insieme a parte.
"""
from datetime import date as Date
from base64 import b64decode
from typing import Optional, List
import urllib.parse

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import text

from ..deps import get_session, utente_corrente
from ..config import settings
from .. import dropbox_ls

router = APIRouter(prefix="/presenze", tags=["presenze"])

TIPI_DOC = {"foglio_firma", "allegato_g", "altro"}
MAX_BYTES = 10 * 1024 * 1024  # 10 MB a file


def _op_id(u: dict) -> int:
    oid = u.get("operatore_id")
    if not oid:
        raise HTTPException(
            status_code=400,
            detail="Il tuo accesso non e' collegato a un operatore. Chiedi all'ufficio di collegarlo.",
        )
    return oid


def _mia_sessione(db, sid: int, oid: int) -> None:
    r = db.execute(
        text("select 1 from operatore_ore where sessione_id=:s and operatore_id=:o"),
        {"s": sid, "o": oid},
    ).first()
    if not r:
        raise HTTPException(status_code=403, detail="Questa sessione non e' tua.")


@router.get("/contesto")
def contesto(u: dict = Depends(utente_corrente), db=Depends(get_session)):
    """Tutto quello che serve alla schermata dell'operatore: chi sei, le attivita'
    disponibili, l'elenco dei minori da spuntare, le tue ultime sessioni."""
    oid = _op_id(u)
    op = db.execute(text(
        "select id, cognome, nome, codice_fiscale, indirizzo, cap, comune, provincia, "
        "iban, tipo, ritenuta from operatori where id=:i"
    ), {"i": oid}).mappings().first()
    attivita = db.execute(text("select id, nome from attivita where attiva order by nome")).mappings().all()
    minori = db.execute(text(
        "select id, cognome, nome from minori "
        "where stato is distinct from 'Rinunciatario' order by cognome, nome"
    )).mappings().all()
    sess = db.execute(text(
        "select s.id, s.data, s.ore, a.nome as attivita, "
        "(select count(*) from presenze p where p.sessione_id = s.id) as presenti "
        "from sessioni s "
        "join operatore_ore oo on oo.sessione_id = s.id "
        "join attivita a on a.id = s.attivita_id "
        "where oo.operatore_id = :i order by s.data desc, s.id desc limit 30"
    ), {"i": oid}).mappings().all()
    incarichi = db.execute(text(
        "select id, codice, descrizione, ruolo, tariffa from catalogo_incarichi "
        "where attivo order by descrizione"
    )).mappings().all()
    scuole = db.execute(text(
        "select id, nome, comune from scuole where attiva order by nome"
    )).mappings().all()
    aperta = db.execute(text(
        "select t.id, t.incarico_id, t.scuola_id, t.entrata, "
        "i.descrizione as incarico, s.nome as scuola "
        "from timbrature t "
        "left join catalogo_incarichi i on i.id = t.incarico_id "
        "left join scuole s on s.id = t.scuola_id "
        "where t.operatore_id = :i and t.uscita is null order by t.entrata desc limit 1"
    ), {"i": oid}).mappings().first()
    return {
        "operatore": dict(op) if op else None,
        "attivita": [dict(x) for x in attivita],
        "minori": [dict(x) for x in minori],
        "sessioni": [dict(x) for x in sess],
        "incarichi": [dict(x) for x in incarichi],
        "scuole": [dict(x) for x in scuole],
        "timbratura_aperta": dict(aperta) if aperta else None,
    }


# ---------- timbratura entrata/uscita ----------
class EntraIn(BaseModel):
    incarico_id: Optional[int] = None
    scuola_id: Optional[int] = None
    note: Optional[str] = None


@router.post("/timbra/entra")
def timbra_entra(dati: EntraIn, u: dict = Depends(utente_corrente), db=Depends(get_session)):
    """Apre un turno. L'indice unico parziale impedisce due turni aperti insieme."""
    oid = _op_id(u)
    gia = db.execute(text(
        "select id from timbrature where operatore_id=:o and uscita is null"
    ), {"o": oid}).first()
    if gia:
        raise HTTPException(status_code=409, detail="Hai gia' un turno aperto: timbra prima l'uscita.")
    if dati.incarico_id and not db.execute(
            text("select 1 from catalogo_incarichi where id=:i"), {"i": dati.incarico_id}).first():
        raise HTTPException(status_code=400, detail="Incarico non trovato")
    if dati.scuola_id and not db.execute(
            text("select 1 from scuole where id=:i"), {"i": dati.scuola_id}).first():
        raise HTTPException(status_code=400, detail="Scuola non trovata")
    tid = db.execute(text(
        "insert into timbrature (operatore_id, incarico_id, scuola_id, entrata, note) "
        "values (:o, :i, :s, now(), :n) returning id"
    ), {"o": oid, "i": dati.incarico_id, "s": dati.scuola_id, "n": dati.note}).scalar()
    return {"id": tid}


class EsciIn(BaseModel):
    note: Optional[str] = None


@router.post("/timbra/esci")
def timbra_esci(dati: EsciIn, u: dict = Depends(utente_corrente), db=Depends(get_session)):
    """Chiude il turno aperto DI CHI CHIEDE (operatore dal token), non quello che
    arriva dal telefono."""
    oid = _op_id(u)
    r = db.execute(text(
        "select id from timbrature where operatore_id=:o and uscita is null "
        "order by entrata desc limit 1"
    ), {"o": oid}).first()
    if not r:
        raise HTTPException(status_code=409, detail="Non hai un turno aperto.")
    db.execute(text(
        "update timbrature set uscita = now(), note = coalesce(:n, note) where id = :t"
    ), {"n": dati.note, "t": r[0]})
    return {"ok": True}


@router.get("/timbrature")
def mie_timbrature(u: dict = Depends(utente_corrente), db=Depends(get_session)):
    """Le timbrature dell'operatore, piu' recenti prima, con le ore gia' calcolate
    (vuote finche' il turno e' aperto)."""
    oid = _op_id(u)
    rows = db.execute(text(
        "select t.id, t.entrata, t.uscita, t.incarico_id, t.scuola_id, t.note, "
        "i.descrizione as incarico, i.tariffa, s.nome as scuola, "
        "round(extract(epoch from (t.uscita - t.entrata))/3600.0, 2) as ore "
        "from timbrature t "
        "left join catalogo_incarichi i on i.id = t.incarico_id "
        "left join scuole s on s.id = t.scuola_id "
        "where t.operatore_id = :o order by t.entrata desc limit 200"
    ), {"o": oid}).mappings().all()
    return {"timbrature": [dict(x) for x in rows]}


class SessioneIn(BaseModel):
    attivita_id: Optional[int] = None
    attivita_nome: Optional[str] = None   # se non c'e' l'id: si cerca o si crea per nome
    data: Date
    ore: float = 0
    note: Optional[str] = None


@router.post("/sessione")
def crea_sessione(dati: SessioneIn, u: dict = Depends(utente_corrente), db=Depends(get_session)):
    oid = _op_id(u)
    aid = dati.attivita_id
    if aid:
        if not db.execute(text("select 1 from attivita where id=:a"), {"a": aid}).first():
            raise HTTPException(status_code=400, detail="Attivita' non trovata")
    else:
        nome = (dati.attivita_nome or "").strip()
        if not nome:
            raise HTTPException(status_code=400, detail="Scegli o scrivi un'attivita'")
        row = db.execute(text("select id from attivita where lower(nome)=lower(:n)"), {"n": nome}).first()
        aid = row[0] if row else db.execute(text(
            "insert into attivita (nome, attiva) values (:n, true) returning id"
        ), {"n": nome}).scalar()
    sid = db.execute(text(
        "insert into sessioni (attivita_id, data, ore, operatore_id, note) "
        "values (:a, :d, :o, :op, :n) returning id"
    ), {"a": aid, "d": dati.data, "o": dati.ore, "op": oid, "n": dati.note}).scalar()
    db.execute(text(
        "insert into operatore_ore (sessione_id, operatore_id, ore) values (:s, :o, :h) "
        "on conflict (sessione_id, operatore_id) do update set ore = excluded.ore"
    ), {"s": sid, "o": oid, "h": dati.ore})
    return {"id": sid}


@router.get("/sessione/{sid}")
def leggi_sessione(sid: int, u: dict = Depends(utente_corrente), db=Depends(get_session)):
    oid = _op_id(u)
    _mia_sessione(db, sid, oid)
    s = db.execute(text(
        "select s.id, s.data, s.ore, s.attivita_id, a.nome as attivita "
        "from sessioni s join attivita a on a.id = s.attivita_id where s.id = :s"
    ), {"s": sid}).mappings().first()
    pres = db.execute(text("select minore_id, ore from presenze where sessione_id=:s"), {"s": sid}).mappings().all()
    return {"sessione": dict(s) if s else None, "presenze": [dict(x) for x in pres]}


class PresenzaIn(BaseModel):
    minore_id: int
    ore: float = 0


class PresenzeIn(BaseModel):
    presenze: List[PresenzaIn]


@router.post("/sessione/{sid}/presenze")
def salva_presenze(sid: int, dati: PresenzeIn, u: dict = Depends(utente_corrente), db=Depends(get_session)):
    """Chi era presente a questa sessione (sostituisce l'elenco precedente)."""
    oid = _op_id(u)
    _mia_sessione(db, sid, oid)
    db.execute(text("delete from presenze where sessione_id=:s"), {"s": sid})
    n = 0
    for p in dati.presenze:
        db.execute(text(
            "insert into presenze (sessione_id, minore_id, ore) values (:s, :m, :o)"
        ), {"s": sid, "m": p.minore_id, "o": p.ore})
        n += 1
    return {"ok": True, "n": n}


class DocumentoIn(BaseModel):
    tipo: str
    titolo: Optional[str] = None
    periodo: Optional[str] = None
    nome_file: str
    mime: Optional[str] = None
    contenuto_base64: str


@router.post("/documento")
def carica_documento(dati: DocumentoIn, u: dict = Depends(utente_corrente), db=Depends(get_session)):
    """Carica un documento dell'operatore (foglio firma, Allegato G). Il contenuto
    arriva in base64; si salva dentro l'archivio, non su Dropbox."""
    oid = _op_id(u)
    if dati.tipo not in TIPI_DOC:
        raise HTTPException(status_code=400, detail="Tipo di documento non valido")
    try:
        raw = b64decode(dati.contenuto_base64.split(",")[-1])
    except Exception:
        raise HTTPException(status_code=400, detail="File non leggibile")
    if not raw:
        raise HTTPException(status_code=400, detail="File vuoto")
    if len(raw) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="File troppo grande (massimo 10 MB)")
    did = db.execute(text(
        "insert into documenti (tipo, titolo, operatore_id, periodo, nome_file, mime, dimensione, contenuto, caricato_da) "
        "values (:t, :ti, :op, :pe, :nf, :mi, :di, :co, :ca) returning id"
    ), {
        "t": dati.tipo, "ti": dati.titolo or dati.nome_file, "op": oid, "pe": dati.periodo,
        "nf": dati.nome_file, "mi": dati.mime, "di": len(raw), "co": raw, "ca": u["id"],
    }).scalar()
    return {"id": did}


@router.get("/buste-paga")
def buste_paga(u: dict = Depends(utente_corrente), db=Depends(get_session)):
    """Le buste paga dell'operatore, prese dalla cartella Dropbox del progetto.
    Finche' la cartella non e' configurata (o e' vuota) non c'e' nulla: le buste
    arriveranno da ott-nov 2026. Abbina solo i file che nominano QUESTO operatore
    (codice fiscale, oppure cognome E nome insieme), cosi' non si vedono quelle
    degli altri."""
    oid = _op_id(u)
    op = db.execute(text(
        "select cognome, nome, codice_fiscale from operatori where id=:i"
    ), {"i": oid}).mappings().first() or {}
    if not dropbox_ls.disponibile() or not settings.buste_paga_path:
        return {"configurato": False, "buste": []}
    try:
        files = dropbox_ls.elenca(settings.buste_paga_path, recursivo=True)
    except Exception as e:  # Dropbox non deve far cadere la schermata
        return {"configurato": True, "errore": str(e)[:200], "buste": []}
    cf = (op.get("codice_fiscale") or "").strip().lower()
    cog = (op.get("cognome") or "").strip().lower()
    nom = (op.get("nome") or "").strip().lower()
    out = []
    for f in files:
        if f.get("cartella"):
            continue
        n = (f.get("nome") or "").lower()
        if (cf and cf in n) or (cog and nom and cog in n and nom in n):
            p = f.get("path") or ""
            out.append({"nome": f.get("nome"), "path": p,
                        "url": "https://www.dropbox.com/home" + urllib.parse.quote(p, safe="/")})
    out.sort(key=lambda x: (x.get("nome") or ""), reverse=True)
    return {"configurato": True, "buste": out}


@router.get("/documenti")
def miei_documenti(u: dict = Depends(utente_corrente), db=Depends(get_session)):
    oid = _op_id(u)
    rows = db.execute(text(
        "select id, tipo, titolo, periodo, nome_file, dimensione, caricato_il "
        "from documenti where operatore_id = :o order by caricato_il desc"
    ), {"o": oid}).mappings().all()
    return {"documenti": [dict(x) for x in rows]}


@router.delete("/documento/{did}")
def elimina_documento(did: int, u: dict = Depends(utente_corrente), db=Depends(get_session)):
    oid = _op_id(u)
    r = db.execute(text("select operatore_id from documenti where id=:i"), {"i": did}).mappings().first()
    if not r or r["operatore_id"] != oid:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    db.execute(text("delete from documenti where id=:i"), {"i": did})
    return {"ok": True}


@router.get("/documento/{did}")
def scarica_documento(did: int, u: dict = Depends(utente_corrente), db=Depends(get_session)):
    oid = _op_id(u)
    r = db.execute(text(
        "select nome_file, mime, contenuto, operatore_id from documenti where id=:i"
    ), {"i": did}).mappings().first()
    if not r or r["operatore_id"] != oid:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    return Response(
        content=bytes(r["contenuto"]),
        media_type=r["mime"] or "application/octet-stream",
        headers={"Content-Disposition": 'inline; filename="%s"' % (r["nome_file"] or "documento")},
    )
