"""Validazione del codice fiscale dei minori per il progetto Apayaye (PNRR).
Funzioni pure, senza database. Non contengono nessun dato di persone reali.
"""
import re
from datetime import date

MESI = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "H": 6,
        "L": 7, "M": 8, "P": 9, "R": 10, "S": 11, "T": 12}

_RE = re.compile(r"^[A-Z]{6}\d{2}[A-EHLMPRST]\d{2}[A-Z]\d{3}[A-Z]$")

# Data di avvio del progetto, dalla Dichiarazione di Inizio Attivita' (DIA)
# firmata il 29/07/2025: "le attivita' ... inizieranno in data 22/09/2025".
# La fascia d'eta' 11-17 si valuta a QUESTA data (eta' all'avvio del progetto),
# non alla data odierna: un minore di 17 anni all'avvio resta ammissibile anche
# se nel frattempo ha compiuto 18 anni.
DATA_AVVIO = date(2025, 9, 22)


def normalizza(cf):
    return re.sub(r"\s+", "", (cf or "")).upper()


def formato_valido(cf):
    return bool(_RE.match(normalizza(cf)))


def dati_dal_cf(cf, anno_riferimento=None):
    cf = normalizza(cf)
    if not formato_valido(cf):
        return None
    aa = int(cf[6:8])
    mese = MESI.get(cf[8])
    giorno = int(cf[9:11])
    genere = "F" if giorno > 40 else "M"
    if genere == "F":
        giorno -= 40
    anno = 2000 + aa
    try:
        nascita = date(anno, mese, giorno)
    except ValueError:
        return None
    return {"data_nascita": nascita, "genere": genere}


def eta_a(nascita, riferimento):
    r = riferimento
    return r.year - nascita.year - ((r.month, r.day) < (nascita.month, nascita.day))


def controlla(cf, eta_min=11, eta_max=17, riferimento=None):
    riferimento = riferimento or DATA_AVVIO
    cf = normalizza(cf)
    out = {"cf": cf, "ok": False, "errori": [], "data_nascita": None, "genere": None, "eta": None}
    if len(cf) != 16:
        out["errori"].append("Il codice fiscale deve avere 16 caratteri.")
        return out
    if not formato_valido(cf):
        out["errori"].append("Il codice fiscale non ha la forma corretta.")
        return out
    dati = dati_dal_cf(cf)
    if dati is None:
        out["errori"].append("La data di nascita nel codice fiscale non esiste.")
        return out
    out["data_nascita"] = dati["data_nascita"]
    out["genere"] = dati["genere"]
    eta = eta_a(dati["data_nascita"], riferimento)
    out["eta"] = eta
    if eta < eta_min or eta > eta_max:
        out["errori"].append(
            "Eta' %d anni all'avvio del progetto: fuori dalla fascia %d-%d prevista." % (eta, eta_min, eta_max))
        return out
    out["ok"] = True
    return out


def doppioni(lista_cf):
    visti = {}
    dup = set()
    for cf in lista_cf:
        n = normalizza(cf)
        if not n:
            continue
        visti[n] = visti.get(n, 0) + 1
        if visti[n] > 1:
            dup.add(n)
    return dup
