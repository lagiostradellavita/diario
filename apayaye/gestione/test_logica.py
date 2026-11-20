"""Prove della logica di compliance, su dati INVENTATI (nessun minore reale)."""
from datetime import date
import codice_fiscale as cf
import ore
import regis

RIF = date(2026, 11, 20)  # data di riferimento per l'eta'
errori = []


def ok(cond, msg):
    if not cond:
        errori.append(msg)


# ---- codice fiscale: CF inventati ----
c = cf.controlla("RSSMRA12A01H501Z", riferimento=RIF)
ok(c["ok"], "CF valido in fascia respinto: %s" % c["errori"])
ok(c["genere"] == "M", "genere sbagliato")
ok(c["data_nascita"] == date(2012, 1, 1), "data sbagliata: %s" % c["data_nascita"])
ok(c["eta"] == 14, "eta sbagliata: %s" % c["eta"])

c = cf.controlla("VRDLRA10A41H501Z", riferimento=RIF)
ok(c["ok"], "CF femmina valido respinto")
ok(c["genere"] == "F", "genere femmina non riconosciuto")

c = cf.controlla("BNCGNN05A01H501Z", riferimento=RIF)
ok(not c["ok"] and c["eta"] == 21, "CF fuori fascia (troppo grande) non respinto")

c = cf.controlla("VRDLCU17A01H501Z", riferimento=RIF)
ok(not c["ok"] and c["eta"] == 9, "CF fuori fascia (troppo piccolo) non respinto")

c = cf.controlla("RSSMRA12B30H501Z", riferimento=RIF)
ok(not c["ok"], "data inesistente non segnalata")

c = cf.controlla("ABC123", riferimento=RIF)
ok(not c["ok"], "formato errato non segnalato")
c = cf.controlla("RSSMRA12A01H5010", riferimento=RIF)
ok(not c["ok"], "formato errato (controllo) non segnalato")

dup = cf.doppioni(["RSSMRA12A01H501Z", "rssmra12a01h501z", "VRDLRA10A41H501Z"])
ok(dup == {"RSSMRA12A01H501Z"}, "doppioni non rilevati: %s" % dup)

# ---- ore ----
presenze = [
    {"minore_id": 1, "ore": 2}, {"minore_id": 1, "ore": 1.5},
    {"minore_id": 2, "ore": 3}, {"minore_id": 2, "ore": None}, {"minore_id": 2, "ore": ""},
]
tot = ore.ore_per_minore(presenze)
ok(tot == {1: 3.5, 2: 3.0}, "somma ore minori sbagliata: %s" % tot)

opore = ore.ore_per_operatore([{"operatore_id": 9, "ore": 3}, {"operatore_id": 9, "ore": 3}])
ok(opore == {9: 6.0}, "somma ore operatori sbagliata: %s" % opore)

# ---- regis: matrice + controlli ----
progetto = {"soggetto": "La Giostra della Vita", "titolo": "Apayaye",
            "cup": "J54C25000220004", "clp": "2024-PE4-00024",
            "data_avvio": date(2025, 9, 22), "destinatari_previsti": 140,
            "minori_coinvolti": 2, "fascia_eta": "11-17 anni", "fase": "Intermedio"}
minori = [
    {"cognome": "rossi", "nome": "mario", "codice_fiscale": "RSSMRA12A01H501Z",
     "stato_nascita": "ITALIA", "comune_nascita": "PALERMO", "provincia": "PA",
     "genere": "M", "data_nascita": date(2012, 1, 1), "ore_erogate": 10,
     "ore_previste": 20, "stato": "Nuovo inserimento"},
    {"cognome": "verdi", "nome": "lara", "codice_fiscale": "VRDLRA10A41H501Z",
     "stato_nascita": "ITALIA", "comune_nascita": "PALERMO", "provincia": "PA",
     "genere": "F", "data_nascita": date(2010, 1, 1), "ore_erogate": 12,
     "ore_previste": 20, "stato": "Concluso"},
]
m = regis.matrice(progetto, minori)
intest = m[8]
ok(intest[0] == "N." and intest[4] == "CODICE FISCALE / ALTRO I.D." and intest[12] == "NOTE (vedi Legenda)",
   "intestazioni template sbagliate: %s" % intest)
riga1 = m[9]
ok(riga1[1] == "2024-PE4-00024" and riga1[2] == "ROSSI" and riga1[9] == "01/01/2012",
   "riga minore sbagliata: %s" % riga1)

ok(regis.problemi(minori, riferimento=RIF) == [], "elenco pulito segnalato come problematico")
minori2 = minori + [
    {"cognome": "rossi", "nome": "mario", "codice_fiscale": "RSSMRA12A01H501Z", "stato": "Nuovo inserimento"},
    {"cognome": "neri", "nome": "ugo", "codice_fiscale": "BNCGNN05A01H501Z", "stato": "Nuovo inserimento"},
]
probs = regis.problemi(minori2, riferimento=RIF)
ok(any("duplicato" in x.lower() for x in probs), "doppione non segnalato nell'export")
ok(any("fascia" in x.lower() for x in probs), "fuori fascia non segnalato nell'export")

if errori:
    print("ROSSO:", len(errori), "prove fallite")
    for e in errori:
        print("  -", e)
    raise SystemExit(1)
print("VERDE: tutte le prove passate")
