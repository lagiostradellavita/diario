"""Importi della rendicontazione Apayaye, dalle ore degli operatori.

E' il numero che va nella app contabilita' (sezione progetti -> APAYAYE):
- costo diretto = somma, per voce, delle ore x tariffa oraria (A01 animatore, A02 tutor...);
- forfait 40% dei costi indiretti, che matura sui costi diretti (COMPLESSIVO sull'intero piano,
  non per singola attivita': vedi il piano uscite);
- costi vivi (pulmini, biglietti, laboratori, fatture) stanno a parte e rientrano nel forfait.

Funzioni pure, senza database. Le tariffe sono un parametro (oggi A01=20, A02=16 euro/h).
"""

TARIFFE = {"A01": 20.0, "A02": 16.0}
FORFAIT = 0.40


def _num(v):
    try:
        if v is None or v == "":
            return 0.0
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def costo_per_voce(righe, tariffe=None):
    """righe: elenco {voce, ore}. Ritorna {voce: euro} = ore x tariffa della voce.
    Una voce senza tariffa nota vale 0 e si dovrebbe dichiarare a chi chiama."""
    tariffe = tariffe or TARIFFE
    out = {}
    for r in righe:
        voce = r.get("voce")
        eur = round(_num(r.get("ore")) * _num(tariffe.get(voce)), 2)
        out[voce] = round(out.get(voce, 0.0) + eur, 2)
    return out


def costo_diretto(righe, tariffe=None):
    """Totale dei compensi (costo diretto) = somma su tutte le voci."""
    return round(sum(costo_per_voce(righe, tariffe).values()), 2)


def forfait_su(costo, perc=FORFAIT):
    """Forfait dei costi indiretti che matura sul costo diretto."""
    return round(_num(costo) * perc, 2)


def riepilogo(righe, tariffe=None, perc=FORFAIT, costi_vivi=0):
    """Riepilogo pronto per la rendicontazione / contabilita'.
    costi_vivi: pulmini, biglietti, laboratori, fatture (stanno dentro il forfait).
    """
    cd = costo_diretto(righe, tariffe)
    forf = forfait_su(cd, perc)
    return {
        "per_voce": costo_per_voce(righe, tariffe),
        "costo_diretto": cd,
        "forfait": forf,
        "costi_vivi": round(_num(costi_vivi), 2),
        "totale_compensi_e_forfait": round(cd + forf, 2),
    }
