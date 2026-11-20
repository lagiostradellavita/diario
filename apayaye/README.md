# Esploratori Apayaye

Gioco geografico sui luoghi delle uscite del progetto Apayaye 2026/2027.
App a sé (PWA installabile), separata da Diario Salute e dalla contabilità.

## Com'è fatta (versione 1)
- `index.html` + `app.js` + `luoghi.js`: la mappa illustrata, l'album, la cattura.
- Si sblocca un luogo stando sul posto (**GPS**) o inquadrando il **QR** (`stampa.html`, da stampare e attaccare sul posto).
- `manifest.json` + `sw.js` + `icon.svg`: installabile sul telefono.
- Versione 1: i progressi restano **sul telefono**. Account (animatori/genitori/minori) e salvataggio in rete: passo successivo, con backend FastAPI + Neon.

## I luoghi
Bottega dei carretti di Michele Ducato · Museo Guttuso–Villa Cattolica · Orto botanico di Palermo ·
Museo dell'Acciuga di Aspra · Laboratorio del grano Tumminia · Mezzojuso · Monte Catalfano · Giro in barca.

Alcune coordinate sono approssimative (segnate `approx` in `luoghi.js`): il QR funziona comunque, e nella versione con account l'animatore potrà fissare la posizione esatta stando sul posto.
