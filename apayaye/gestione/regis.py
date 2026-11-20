"""Export nel formato ESATTO del template ministeriale "Elenco minori destinatari"
(Presidenza del Consiglio dei Ministri - Struttura di Missione PNRR), per ReGiS.

Costruisce la matrice di righe (aoa) con le intestazioni e l'ordine delle colonne del
template ufficiale. Il browser (o un foglio) la trasforma in .xlsx.

Funzioni pure, senza database e senza dati di persone reali.
"""

# Colonne, nell'ordine esatto del template ufficiale.
COLONNE = [
    "N.",
    "CODICE PROTOCOLLO - CLP",
    "COGNOME",
    "NOME",
    "CODICE FISCALE / ALTRO I.D.",
    "STATO DI NASCITA",
    "COMUNE DI NASCITA",
    "PROVINCIA",
    "GENERE",
    "DATA DI NASCITA",
    "SOMMATORIA DI ORE DI FORMAZIONE EROGATE (al termine del progetto)",
    "SOMMATORIA DI ORE DI FORMAZIONE PREVISTE (al termine del progetto)",
    "NOTE (vedi Legenda)",
]

STATI_AMMESSI = {"Nuovo inserimento", "Concluso", "Rinunciatario"}


def _data_itastr(d):
    """Data in gg/mm/aaaa, come chiede il template. Accetta date o stringa gia' pronta."""
    if d is None or d == "":
        return ""
    if hasattr(d, "strftime"):
        return d.strftime("%d/%m/%Y")
    return str(d)


def riga_minore(n, m, clp):
    """Una riga del template a partire dal dizionario di un minore.
    m: {cognome, nome, codice_fiscale, stato_nascita, comune_nascita, provincia,
        genere, data_nascita, ore_erogate, ore_previste, stato}
    """
    return [
        n,
        clp,
        (m.get("cognome") or "").upper(),
        (m.get("nome") or "").upper(),
        (m.get("codice_fiscale") or "").upper(),
        m.get("stato_nascita") or "",
        m.get("comune_nascita") or "",
        m.get("provincia") or "",
        m.get("genere") or "",
        _data_itastr(m.get("data_nascita")),
        m.get("ore_erogate", ""),
        m.get("ore_previste", ""),
        m.get("stato") or "",
    ]


def matrice(progetto, minori):
    """Costruisce l'intera matrice del foglio, come il template.
    progetto: {soggetto, titolo, cup, clp, data_avvio, destinatari_previsti,
               minori_coinvolti, fascia_eta, fase}
    minori: elenco di dizionari (vedi riga_minore). I rinunciatari restano in elenco
            con NOTE = "Rinunciatario".
    """
    p = progetto
    aoa = []
    aoa.append(["Elenco minori destinatari", "Presidenza del Consiglio dei Ministri"])
    aoa.append(["Struttura di Missione PNRR"])
    aoa.append(["Soggetto Proponente:", p.get("soggetto", ""), "CUP:", p.get("cup", "")])
    aoa.append(["Titolo progetto:", p.get("titolo", ""), "Data di avvio:", _data_itastr(p.get("data_avvio"))])
    aoa.append(["Nr. destinatari previsti da Atto d'obbligo:", p.get("destinatari_previsti", "")])
    aoa.append(["Nr. minori coinvolti:", p.get("minori_coinvolti", "")])
    aoa.append(["Fascia di eta'", p.get("fascia_eta", ""), "Fase progetto", p.get("fase", "")])
    aoa.append([])
    aoa.append(list(COLONNE))
    clp = p.get("clp", "")
    for i, m in enumerate(minori, start=1):
        aoa.append(riga_minore(i, m, clp))
    return aoa


def problemi(minori, eta_min=11, eta_max=17, riferimento=None):
    """Controlla l'elenco prima dell'invio: CF doppi, CF non validi, eta' fuori fascia,
    stato non ammesso. Ritorna un elenco di problemi (stringhe), vuoto se tutto a posto."""
    from codice_fiscale import controlla, doppioni, normalizza
    out = []
    dup = doppioni([m.get("codice_fiscale") for m in minori])
    for n in sorted(dup):
        out.append("Codice fiscale duplicato: %s" % n)
    for i, m in enumerate(minori, start=1):
        c = controlla(m.get("codice_fiscale"), eta_min, eta_max, riferimento)
        if not c["ok"]:
            out.append("Riga %d (%s %s): %s" % (
                i, (m.get("cognome") or "").upper(), (m.get("nome") or "").upper(),
                "; ".join(c["errori"])))
        st = m.get("stato")
        if st and st not in STATI_AMMESSI:
            out.append("Riga %d: stato \"%s\" non ammesso (valori: %s)." % (
                i, st, ", ".join(sorted(STATI_AMMESSI))))
    return out
