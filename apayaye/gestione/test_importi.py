"""Prove degli importi, contro i numeri VERI del piano uscite 2026/2027.
(Un giro completo di 8 uscite: 56 ore animatore + 49 ore tutor.)"""
import importi

errori = []
def ok(c, m):
    if not c: errori.append(m)

cpv = importi.costo_per_voce([{"voce": "A01", "ore": 56}, {"voce": "A02", "ore": 49}])
ok(cpv == {"A01": 1120.0, "A02": 784.0}, "costo per voce sbagliato: %s" % cpv)

cd = importi.costo_diretto([{"voce": "A01", "ore": 56}, {"voce": "A02", "ore": 49}])
ok(cd == 1904.0, "costo diretto sbagliato: %s (atteso 1904.0)" % cd)

ok(importi.forfait_su(1904.0) == 761.60, "forfait sbagliato: %s" % importi.forfait_su(1904.0))

r = importi.riepilogo([{"voce": "A01", "ore": 56}, {"voce": "A02", "ore": 49}], costi_vivi=1224.80)
ok(r["costo_diretto"] == 1904.0 and r["forfait"] == 761.60 and r["totale_compensi_e_forfait"] == 2665.60,
   "riepilogo sbagliato: %s" % r)

ok(importi.costo_diretto([{"voce": "SCONOSCIUTA", "ore": 10}]) == 0.0, "voce ignota non azzerata")
ok(importi.costo_diretto([{"voce": "A01", "ore": None}]) == 0.0, "ore mancanti non azzerate")

if errori:
    print("ROSSO:", len(errori))
    for e in errori: print("  -", e)
    raise SystemExit(1)
print("VERDE: importi corretti (1.904,00 + 761,60 = 2.665,60, come il piano uscite)")
