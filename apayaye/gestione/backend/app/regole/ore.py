"""Somma delle ore erogate ai minori e delle ore degli operatori. Funzioni pure."""


def ore_per_minore(presenze):
    tot = {}
    for p in presenze:
        mid = p.get("minore_id")
        if mid is None:
            continue
        tot[mid] = round(tot.get(mid, 0.0) + _num(p.get("ore")), 2)
    return tot


def ore_per_operatore(righe):
    tot = {}
    for r in righe:
        oid = r.get("operatore_id")
        if oid is None:
            continue
        tot[oid] = round(tot.get(oid, 0.0) + _num(r.get("ore")), 2)
    return tot


def ore_per_attivita(sessioni):
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
