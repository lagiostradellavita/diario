"""Validazione del codice fiscale dei minori per il progetto Apayaye (PNRR).

Regole del bando (template ministeriale "Elenco minori destinatari"):
- il CF deve avere 16 caratteri, senza spazi;
- l'eta' ricavata dal CF deve rientrare nella fascia del progetto (11-17 anni);
- non ci devono essere CF doppi o incoerenti.

Funzioni pure, senza database. Non contengono nessun dato di persone reali.
"""
import re
from datetime import date

MESI = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "H": 6,
        "L": 7, "M": 8, "P": 9, "R": 10, "S": 11, "T": 12}

# forma del CF: 6 lettere, 2 cifre, 1 lettera mese, 2 cifre giorno,
# 1 lettera comune, 3 cifre, 1 lettera di controllo
_RE = re.compile(r"^[A-Z]{6}\d{2}[A-EHLMPRST]\d{2}[A-Z]\d{3}[A-Z]$")


def normalizza(cf):
    return re.sub(r"\s+", "", (cf or "")).upper()


def formato_valido(cf):
    """True se il CF ha la forma giusta (16 caratteri, struttura corretta)."""
    return bool(_RE.match(normalizza(cf)))


def dati_dal_cf(cf, anno_riferimento=None):
    """Ricava (data_nascita, genere) dal CF.
    L'anno a due cifre si interpreta nel 2000 (i destinatari sono minori).
    Ritorna None se il CF non e' valido o la data non esiste.
    """
    cf = normalizza(cf)
    if not formato_valido(cf):
        return None
    aa = int(cf[6:8])
    mese = MESI.get(cf[8])
    giorno = int(cf[9:11])
    genere = "F" if giorno > 40 else "M"
    if genere == "F":
        giorno -= 40
    anno = 2000 + aa  # per i minori del progetto l'anno e' sempre 20xx
    try:
        nascita = date(anno, mese, giorno)
    except ValueError:
        return None
    return {"data_nascita": nascita, "genere": genere}


def eta_a(nascita, riferimento):
    """Eta' in anni compiuti alla data di riferimento."""
    r = riferimento
    anni = r.year - nascita.year - ((r.month, r.day) < (nascita.month, nascita.day))
    return anni


def controlla(cf, eta_min=11, eta_max=17, riferimento=None):
    """Controllo completo di un CF per il progetto.
    Ritorna un dizionario: {ok, errori[], data_nascita, genere, eta}.
    """
    riferimento = riferimento or date.today()
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
            "Eta' %d anni: fuori dalla fascia %d-%d prevista dal progetto." % (eta, eta_min, eta_max))
        return out
    out["ok"] = True
    return out


def doppioni(lista_cf):
    """Dato un elenco di CF, ritorna l'insieme dei CF che compaiono piu' di una volta
    (normalizzati). Serve a impedire i duplicati che il bando vieta."""
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
