# Apayaye — Gestione (minori, iscrizioni, attività, ore)

La parte **privata** dell'app Apayaye: anagrafica dei minori destinatari, iscrizioni e
consensi dei genitori, attività con le ore, ed **export nel formato del Ministero** (ReGiS).

È **una sola app** con il gioco, ma la gestione sta **dietro il login** e per **ruolo**:
il gioco resta pubblico, i dati dei minori no. Il gioco pubblico non tocca mai questo archivio.

## Ruoli
- **ufficio / admin** — tutto: anagrafica, iscrizioni, attività, ore, export.
- **operatore** (animatore/tutor) — segna presenze e ore delle **sue** attività; vede i suoi minori.
- **genitore** — sola lettura del **proprio** figlio (attività e ore).

## Cosa chiede il Ministero (template «Elenco minori destinatari», per ReGiS)
Per ogni minore: Cognome · Nome · **Codice fiscale** · Stato di nascita · Comune di nascita ·
Provincia · Genere · Data di nascita · CLP (2024-PE4-00024) · **Ore erogate** · **Ore previste** ·
Stato (Nuovo inserimento / Concluso / Rinunciatario).
Regole dure: età dal CF **11-17**, niente CF doppi o incoerenti (pena il taglio del 10% a saldo).
⚠️ Il template del Ministero **non chiede i dati dei genitori**: quelli servono per iscrizione e
consensi e restano alla cooperativa.

## Le ore
Si segnano le presenze e le ore di ogni **sessione** di attività (minori presenti + ore degli
operatori). L'app **somma da sola** le ore erogate per minore → è il numero che va a ReGiS.
La regola sta in `ore.py` (un posto solo), così schermata ed export dicono la stessa cifra.

## I file di questa cartella (fondamenta, già provate)
- `codice_fiscale.py` — valida il CF, ricava data/genere/età, controlla la fascia 11-17, trova i doppioni.
- `ore.py` — somma le ore erogate per minore e per operatore.
- `regis.py` — costruisce la matrice del template ministeriale **ed** elenca i problemi prima dell'invio.
- `schema.sql` — il modello dati (minori, genitori, attività, sessioni, presenze, ore).
- `test_logica.py` — le prove su dati **inventati** (nessun minore reale). Esito: tutte verdi.

⚠️ **Mai dati reali di minori** in questi file, nei test, nei controlli o nella memoria.

## Cosa manca (prossimi passi)
1. **Backend FastAPI** (come diario/contabilità): auth su invito con i 4 ruoli, rotte per
   anagrafica/iscrizioni/attività/ore, rotta di export; migrazioni alembic dallo `schema.sql`.
2. **Schermate** dentro l'app: login, elenco minori + scheda, iscrizione con consensi, attività e
   presenze (operatore), vista genitore.
3. **Deploy**: un servizio Render nuovo (`apayaye-api`) + un database **Neon in UE**.

## Impianto da fare una volta
- Creare il database **Neon** (regione UE) e incollare la stringa in `DATABASE_URL` su Render.
- Creare il servizio Render del backend Apayaye.
- Primo utente **admin** su invito; poi da lì si invitano ufficio, operatori, genitori.
- Dati di minori: conservare informativa privacy e registro dei trattamenti (il titolare è la cooperativa).
