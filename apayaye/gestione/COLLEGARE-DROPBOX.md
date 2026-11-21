# Collegare Dropbox all'app Apayaye (su Render)

Serve a tre cose dell'app: **vedere e aggiungere i file** del progetto, le **buste paga** degli operatori, e (più avanti) scrivere i **fascicoli ReGiS** nella cartella su Dropbox.

Lo fai una volta sola, dal pannello di **Render** (dove gira il server dell'app). Non si tocca il codice.

---

## Via più semplice (consigliata): riusa il collegamento che hai già

L'app di **contabilità** è già collegata a Dropbox e sa **scrivere** file (crea i fascicoli). Possiamo usare lo **stesso** collegamento anche per Apayaye: così non devi creare niente di nuovo.

1. Entra su **render.com** → apri il servizio della **contabilità** (il backend).
2. Vai su **Environment** (Ambiente).
3. Copia il **valore** di queste tre variabili (clicca sull'occhietto per vederle):
   - `DROPBOX_REFRESH_TOKEN`
   - `DROPBOX_APP_KEY`
   - `DROPBOX_APP_SECRET`
4. Ora apri il servizio **Apayaye** (`apayaye-api`) → **Environment** → **Add Environment Variable** e incolla le stesse tre (stesso nome, stesso valore).
5. Aggiungi anche:
   - `DROPBOX_PATH_ROOT` = `12830409123`
6. Premi **Save Changes**: Render riavvia il server da solo (1-2 minuti). Fatto.

> Se la contabilità **non** ha queste variabili (usa un token diverso), segui la **Via lunga** qui sotto.

---

## Via lunga: creare il collegamento da zero

Serve solo se non puoi riusare quello della contabilità.

1. Vai su **https://www.dropbox.com/developers/apps** e accedi con l'account della cooperativa.
2. **Create app** → **Scoped access** → **Full Dropbox** → dai un nome (es. `Apayaye`).
3. Scheda **Permissions**: spunta questi tre permessi e premi **Submit**:
   - `files.metadata.read`
   - `files.content.read`
   - `files.content.write`  ← è questo che permette di **aggiungere** file
4. Scheda **Settings**: segnati **App key** e **App secret**.
5. Ottenere il **refresh token** (il "permesso duraturo"):
   - apri nel browser questo indirizzo, mettendo la tua App key al posto di `APPKEY`:
     `https://www.dropbox.com/oauth2/authorize?client_id=APPKEY&token_access_type=offline&response_type=code`
   - autorizza e **copia il codice** che compare.
   - questo codice va scambiato con il refresh token: è un passaggio tecnico, se arrivi qui **mandami App key, App secret e il codice** e te lo ricavo io (il codice dura pochi minuti, quindi fallo quando ci sentiamo).
6. Su Render, servizio **Apayaye** → **Environment**, imposta:
   - `DROPBOX_REFRESH_TOKEN`, `DROPBOX_APP_KEY`, `DROPBOX_APP_SECRET`
   - `DROPBOX_PATH_ROOT` = `12830409123`
7. **Save Changes**.

---

## Altre variabili utili (facoltative), stesso posto

Sempre su Render → **Apayaye** → **Environment**:

| Variabile | A cosa serve | Esempio |
|---|---|---|
| `BUSTE_PAGA_PATH` | cartella Dropbox delle buste paga degli operatori | *(da definire quando le carichi)* |
| `COMMITTENTE_PIVA` | P. IVA della cooperativa, per le ricevute degli autonomi | |
| `COMMITTENTE_CF` | Codice fiscale della cooperativa | |
| `COMMITTENTE_SEDE` | sede legale (per le ricevute) | |

---

## Come capire se ha funzionato

Dopo il riavvio, entra nell'app come **amministratore**:
- in **Rendicontazione** apri una riga: devono comparire i **file veri** delle cartelle (prima si vedevano solo i collegamenti);
- se compaiono, il collegamento **in lettura** funziona. La **scrittura** (aggiungere file, fascicoli) la proviamo insieme sul primo file.

Se qualcosa non torna, scrivimi cosa vedi e lo sistemiamo.
