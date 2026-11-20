"""Importi della rendicontazione Apayaye, dalle ore degli operatori.
E' il numero che va nella app contabilita' (sezione progetti -> APAYAYE).
Funzioni pure. Tariffe: A01 animatore 20, A02 tutor 16 euro/h.
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
    tariffe = tariffe or TARIFFE
    out = {}
    for r in righe:
        voce = r.get("voce")
        eur = round(_num(r.get("ore")) * _num(tariffe.get(voce)), 2)
        out[voce] = round(out.get(voce, 0.0) + eur, 2)
    return out


def costo_diretto(righe, tariffe=None):
    return round(sum(costo_per_voce(righe, tariffe).values()), 2)


def forfait_su(costo, perc=FORFAIT):
    return round(_num(costo) * perc, 2)


def riepilogo(righe, tariffe=None, perc=FORFAIT, costi_vivi=0):
    cd = costo_diretto(righe, tariffe)
    forf = forfait_su(cd, perc)
    return {
        "per_voce": costo_per_voce(righe, tariffe),
        "costo_diretto": cd,
        "forfait": forf,
        "costi_vivi": round(_num(costi_vivi), 2),
        "totale_compensi_e_forfait": round(cd + forf, 2),
    }
