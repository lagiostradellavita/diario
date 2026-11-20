"""Somma delle ore erogate ai minori e delle ore degli operatori.

Il numero che va al Ministero (colonna "Sommatoria ore erogate") e' la somma delle
ore di tutte le attivita' a cui il minore ha partecipato. Qui sta la regola, in un
posto solo, cosi' schermata ed export dicono sempre la stessa cifra.

Funzioni pure, senza database.
"""


def ore_per_minore(presenze):
    """presenze: elenco di righe {minore_id, ore}. Ritorna {minore_id: ore_totali}.
    Le ore si sommano; valori mancanti o non numerici valgono 0."""
    tot = {}
    for p in presenze:
        mid = p.get("minore_id")
        if mid is None:
            continue
        tot[mid] = round(tot.get(mid, 0.0) + _num(p.get("ore")), 2)
    return tot


def ore_per_operatore(righe):
    """righe: elenco {operatore_id, ore}. Ritorna {operatore_id: ore_totali}."""
    tot = {}
    for r in righe:
        oid = r.get("operatore_id")
        if oid is None:
            continue
        tot[oid] = round(tot.get(oid, 0.0) + _num(r.get("ore")), 2)
    return tot


def ore_per_attivita(sessioni):
    """sessioni: elenco {attivita_id, ore}. Ritorna {attivita_id: ore_totali}."""
    tot = {}
    for s in sessioni:
        aid = s.get("attivita_id")
        if aid is None:
            continue
        tot[aid] = round(tot.get(aid, 0.0) + _num(s.get("ore")), 2)
    return tot


def _num(v):
    try:
        if v is None or v == "":
            return 0.0
        return float(v)
    except (TypeError, ValueError):
        return 0.0
