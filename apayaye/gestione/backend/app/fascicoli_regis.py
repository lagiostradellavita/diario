"""Montaggio dei fascicoli ReGiS (funzioni pure).

Una VOCE di spesa del personale (lavoratore autonomo) in un mese ha tre
giustificativi: 1 Bonifico, 2 Ricevuta e Allegato G, 3 F24. Bonifico e F24 sono
file gia' presenti su Dropbox nella cartella "Tutti i bonifici", nominati cosi':

    Apayaye - <Cognome> - <mese> <anno> - <importo>.pdf          (bonifico)
    Apayaye - F24 <Cognome> - <mese> <anno> - <importo>.pdf      (F24)

dove <mese> puo' essere uno o piu' mesi ("gen feb 2026") o la forma "MM-AAAA".
Questo modulo: (a) legge quei nomi, (b) abbina a ogni voce il suo bonifico e il
suo F24, (c) prepara il testo di Ricevuta e Allegato G per il generatore PDF.
Nessuna rete, nessun dato scritto a mano nel codice."""
import re
import unicodedata
from typing import List, Optional

from .pdf_semplice import Riga

MESI = {"gen": 1, "feb": 2, "mar": 3, "apr": 4, "mag": 5, "giu": 6,
        "lug": 7, "ago": 8, "set": 9, "ott": 10, "nov": 11, "dic": 12}
MESI_NOME = {v: k for k, v in MESI.items()}
MESI_LUNGO = ["", "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
              "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]

# Nomi che NON sono persone (distinte cumulative, riepiloghi, fornitori, partner).
_SALTA = ("distinta", "riepilogo", "disposizion", "sepa", "quota parte",
          "national pen", "agriconsulting", "bocs", "come si chiamavano")


def _senza_accenti(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _norm(s: str) -> str:
    return _senza_accenti((s or "").strip().lower())


def importo_it(s: str) -> Optional[float]:
    """'1.264,00' -> 1264.0 ; '€' e spazi ignorati. None se non e' un numero."""
    t = re.sub(r"[^0-9.,-]", "", s or "")
    if not t:
        return None
    t = t.replace(".", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def _parse_mese_anno(token: str):
    """Torna (mesi:[int], anno:int) o None. Accetta 'mag 2026', 'gen feb 2026',
    '03-2026'."""
    token = token.strip().lower()
    m = re.match(r"^(\d{1,2})-(\d{4})$", token)
    if m:
        mm = int(m.group(1))
        if 1 <= mm <= 12:
            return [mm], int(m.group(2))
        return None
    pezzi = token.split()
    mesi, anno = [], None
    for p in pezzi:
        if p in MESI:
            mesi.append(MESI[p])
        elif re.match(r"^\d{4}$", p):
            anno = int(p)
    if mesi and anno:
        return mesi, anno
    return None


def analizza_fonte(nome: str, path: str = "") -> Optional[dict]:
    """Legge il nome di un file di 'Tutti i bonifici'. None se non e' un
    giustificativo di una persona."""
    base = re.sub(r"\.pdf$", "", nome or "", flags=re.I)
    parti = [p.strip() for p in base.split(" - ")]
    if len(parti) < 3 or _norm(parti[0]) != "apayaye":
        return None
    persona_raw = parti[1]
    pl = _norm(persona_raw)
    if any(s in pl for s in _SALTA) or pl in ("f24", ""):
        return None
    if pl.startswith("f24 "):
        tipo, persona = "f24", persona_raw[4:].strip()
    else:
        tipo, persona = "bonifico", persona_raw
    if any(s in _norm(persona) for s in _SALTA) or not persona:
        return None
    mesi, anno, importo = None, None, None
    for p in parti[2:]:
        ma = _parse_mese_anno(p)
        if ma:
            mesi, anno = ma
        else:
            imp = importo_it(p)
            if imp is not None:
                importo = imp
    if not mesi:
        return None
    return {"tipo": tipo, "persona": persona, "mesi": mesi, "anno": anno,
            "importo": importo, "nome": nome, "path": path}


def _persona_combacia(persona: str, cognome: str, nome: str, ambiguo: bool) -> bool:
    """Il cognome deve comparire nel nome del file; se nella cartella ci sono piu'
    persone con lo stesso cognome (ambiguo), serve anche il nome."""
    tok = _norm(persona).split()
    cog = _norm(cognome)
    if not cog or cog not in tok:
        return False
    if ambiguo:
        nn = _norm(nome).split()
        return bool(nn) and nn[0] in tok
    return True


def abbina(voce: dict, fonti: List[dict], tipo: str) -> Optional[dict]:
    """Trova il file (bonifico o F24) della voce: stesso tipo, stesso anno, il
    mese della voce fra i mesi del file, e la persona che combacia. A parita',
    vince l'importo piu' vicino a quello atteso."""
    cognome, nome = voce.get("cognome", ""), voce.get("nome", "")
    mese, anno = voce.get("mese"), voce.get("anno")
    # Il cognome e' ambiguo se piu' persone distinte lo portano nelle fonti.
    cg = _norm(cognome)
    nomi_con_cognome = set()
    for f in fonti:
        tk = _norm(f["persona"]).split()
        if cg and cg in tk:
            nomi_con_cognome.add(" ".join(tk))
    ambiguo = len(nomi_con_cognome) > 1
    cand = [f for f in fonti
            if f["tipo"] == tipo and f["anno"] == anno and mese in f["mesi"]
            and _persona_combacia(f["persona"], cognome, nome, ambiguo)]
    if not cand:
        return None
    atteso = voce.get("netto") if tipo == "bonifico" else voce.get("ritenuta")
    if atteso is not None:
        cand.sort(key=lambda f: abs((f.get("importo") or 0) - atteso))
    return cand[0]


def _eur(n) -> str:
    return ("%0.2f" % (float(n or 0))).replace(".", ",") + " €"


def mese_label(mese: int, anno: int) -> str:
    return "%s %d" % (MESI_NOME.get(mese, str(mese)), anno)


def righe_allegato_g(voce: dict, intest: dict) -> List[Riga]:
    """Timesheet mensile: una riga per timbratura chiusa, con il totale."""
    rr = [Riga("Allegato G – Timesheet mensile", 16, True, 0),
          Riga("Progetto %s – CLP %s · CUP %s" % (intest.get("titolo", "Apayaye"), intest.get("clp", ""), intest.get("cup", "")), 9),
          Riga(intest.get("soggetto", ""), 9, False, 1),
          Riga("Operatore: %s %s%s" % (voce.get("cognome", ""), voce.get("nome", ""),
               ("  ·  C.F. " + voce["codice_fiscale"]) if voce.get("codice_fiscale") else ""), 11, True, 10),
          Riga("Mese: %s" % mese_label(voce["mese"], voce["anno"]), 11, False, 2),
          Riga("Giorno        Entrata   Uscita   Ore    Attività / sede", 10, True, 10)]
    tot = 0.0
    for t in voce.get("righe", []):
        tot += float(t.get("ore") or 0)
        rr.append(Riga("%-12s  %-7s  %-7s  %-5s  %s" % (
            t.get("giorno", ""), t.get("ent", ""), t.get("usc", ""),
            ("%0.2f" % float(t.get("ore") or 0)).replace(".", ","),
            (t.get("incarico", "") + (" / " + t["scuola"] if t.get("scuola") else ""))), 10))
    rr.append(Riga("Totale ore: %s" % ("%0.2f" % tot).replace(".", ","), 11, True, 10))
    rr.append(Riga("Le ore sono calcolate dalle timbrature registrate nell'app.", 9, False, 8))
    rr.append(Riga("Data ____________   Firma dell'operatore ____________________", 10, False, 20))
    return rr


def righe_ricevuta(voce: dict, intest: dict) -> List[Riga]:
    lordo = float(voce.get("lordo") or 0)
    rit = float(voce.get("rit") if voce.get("rit") is not None else 0.20)
    ritimp = lordo * rit
    netto = lordo - ritimp
    bollo = lordo > 77.47
    comm = intest.get("soggetto", "")
    piva = intest.get("committente_piva") or ""
    cf = intest.get("committente_cf") or ""
    rr = [Riga("Ricevuta per prestazione di lavoro autonomo occasionale", 15, True, 0),
          Riga("Progetto %s – CLP %s · CUP %s" % (intest.get("titolo", "Apayaye"), intest.get("clp", ""), intest.get("cup", "")), 9, False, 6),
          Riga("Il/La sottoscritto/a %s %s%s" % (voce.get("cognome", ""), voce.get("nome", ""),
               ("  ·  C.F. " + voce["codice_fiscale"]) if voce.get("codice_fiscale") else ""), 11, True, 10)]
    if voce.get("indirizzo"):
        rr.append(Riga(voce["indirizzo"], 10))
    if voce.get("iban"):
        rr.append(Riga("IBAN %s" % voce["iban"], 10))
    rr.append(Riga("emette ricevuta a favore di %s%s%s" % (
        comm, ("  ·  P. IVA " + piva) if piva else "",
        ("  ·  C.F. " + cf) if cf else ""), 11, False, 10))
    rr.append(Riga("per l'attività svolta nel mese di %s nell'ambito del progetto %s." % (
        mese_label(voce["mese"], voce["anno"]), intest.get("titolo", "Apayaye")), 11, False, 8))
    rr.append(Riga("Compenso lordo:         %s" % _eur(lordo), 11, True, 12))
    rr.append(Riga("Ritenuta d'acconto (%d%%): – %s" % (round(rit * 100), _eur(ritimp)), 11))
    rr.append(Riga("Netto a pagare:          %s" % _eur(netto), 12, True, 2))
    if bollo:
        rr.append(Riga("Marca da bollo da 2,00 € assolta (compenso superiore a 77,47 €).", 10, False, 8))
    rr.append(Riga("Compenso non soggetto a IVA. Prestazione di lavoro autonomo occasionale ai sensi "
                   "dell'art. 2222 c.c. e dell'art. 67, comma 1, lett. l) del TUIR; attività svolta in "
                   "via del tutto occasionale e non abituale.", 9, False, 10))
    rr.append(Riga("Data ____________   Firma ____________________", 10, False, 20))
    return rr


def nome_regis(numero: int, voce: dict, k: int, etichetta: str, importo) -> str:
    """Nome del file nel fascicolo ReGiS, nello stile della cartella:
    'NN - Apayaye - GdV - Cognome Nome - mese anno - k Etichetta - importo.pdf'."""
    nn = "%02d" % numero
    persona = (voce.get("cognome", "") + " " + voce.get("nome", "")).strip()
    mesi = mese_label(voce["mese"], voce["anno"])
    imp = ("%0.2f" % float(importo or 0)).replace(".", ",")
    return "%s - Apayaye - GdV - %s - %s - %d %s - %s.pdf" % (nn, persona, mesi, k, etichetta, imp)
