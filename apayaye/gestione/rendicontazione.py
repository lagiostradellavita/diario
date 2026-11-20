"""Cosa serve per la rendicontazione Apayaye: la checklist dei documenti e i rimandi
alla guida ufficiale (ReGiS). E' l'ossatura della schermata "Rendicontazione" dell'app.

⚠️ Elenco di PARTENZA, ricavato dai documenti del progetto. Va rifinito sulle Linee guida
ufficiali del Soggetto Attuatore (file in Dropbox "10 - Regis"). Non e' consulenza: e' una
lista di lavoro che l'ufficio conferma.
"""

# La guida ufficiale (percorsi Dropbox; l'app li apre per l'ufficio, dietro login).
# Niente link con chiave segreta nel codice: si tiene il percorso, non un link pubblico.
GUIDA = [
    {"titolo": "Linee guida rendicontazione (Soggetto Attuatore) 2025",
     "dove": "2023 - Agenzia coesione - Apayaye/10 - Regis/pe_linee_guida_sa_2025.pdf"},
    {"titolo": "Webinar rendicontazione - slide",
     "dove": "2023 - Agenzia coesione - Apayaye/10 - Regis/2025 11 06 - webinar-pe_slide_pdf.pdf"},
    {"titolo": "Indicatori e target (ReGiS)",
     "dove": "2023 - Agenzia coesione - Apayaye/10 - Regis/J54C25000220004__Indicatori_Target_02122025.xlsx"},
]

# Checklist dei documenti della rendicontazione. "importo": True = porta una cifra che va in contabilita'.
CHECKLIST = [
    {"voce": "Elenco minori destinatari (template ministeriale)", "chi": "ufficio",
     "nota": "si esporta dall'app, nel formato esatto per ReGiS"},
    {"voce": "Autocertificazione monte ore (ex art. 17.1)", "chi": "ufficio",
     "nota": "le ore erogate per minore devono coincidere con l'elenco"},
    {"voce": "Allegato G", "chi": "operatore / ufficio"},
    {"voce": "Registri firma dei minori", "chi": "operatore"},
    {"voce": "Registri firma degli operatori", "chi": "operatore"},
    {"voce": "Relazioni delle attivita'", "chi": "operatore"},
    {"voce": "Fatture ricevute / giustificativi di spesa", "chi": "ufficio / operatore", "importo": True},
    {"voce": "Compensi operatori (ore x tariffa)", "chi": "ufficio", "importo": True,
     "nota": "calcolati dall'app (importi.py); costo diretto + forfait 40%"},
    {"voce": "Moduli di iscrizione e consensi (privacy, immagini)", "chi": "ufficio"},
]


def voci_con_importo():
    """Le voci della checklist che portano una cifra verso la contabilita' (progetti -> APAYAYE)."""
    return [c["voce"] for c in CHECKLIST if c.get("importo")]
