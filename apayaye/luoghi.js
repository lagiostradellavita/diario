/* I luoghi delle uscite Apayaye 2026/2027.
   coord: [lat, lng] della posizione reale; raggio in metri entro cui il GPS sblocca.
   Le posizioni marcate "approx:true" sono da rifinire sul posto (l'animatore usa "fissa qui"
   nella versione con account). Il QR funziona comunque, anche al chiuso, senza GPS.
   map: posizione del segnaposto sulla mappa illustrata (viewBox 100 x 120).
   qr: codice contenuto nel QR stampato (vedi stampa.html). */

function creatura(a, b, occhi, emblema){
  // disegno semplice del personaggio: corpo tondo con due colori, occhi, bocca, emblema del luogo
  return '<svg viewBox="0 0 100 100" aria-hidden="true">'
    + '<defs><radialGradient id="rg" cx="35%" cy="30%" r="80%">'
    + '<stop offset="0" stop-color="'+a+'"/><stop offset="1" stop-color="'+b+'"/></radialGradient></defs>'
    + '<ellipse cx="50" cy="92" rx="26" ry="5" fill="rgba(0,0,0,.14)"/>'
    + '<path d="M50 10 C74 10 86 30 86 52 C86 78 70 90 50 90 C30 90 14 78 14 52 C14 30 26 10 50 10 Z" fill="url(#rg)"/>'
    + '<ellipse cx="38" cy="46" rx="9" ry="10" fill="#fff"/><ellipse cx="62" cy="46" rx="9" ry="10" fill="#fff"/>'
    + '<circle cx="'+(38+occhi)+'" cy="48" r="4.2" fill="#241a10"/><circle cx="'+(62+occhi)+'" cy="48" r="4.2" fill="#241a10"/>'
    + '<path d="M42 62 Q50 70 58 62" fill="none" stroke="rgba(0,0,0,.5)" stroke-width="3" stroke-linecap="round"/>'
    + '<circle cx="78" cy="74" r="15" fill="#fff" stroke="rgba(0,0,0,.08)"/>'
    + '<text x="78" y="80" font-size="17" text-anchor="middle">'+emblema+'</text>'
    + '</svg>';
}

var LUOGHI = [
  { id:"carretti", num:1, nome:"Rotella", dove:"Bottega dei carretti di Michele Ducato", quando:"dicembre 2026",
    coord:[38.0945, 13.5290], raggio:250, approx:true, qr:"APAYAYE:carretti:RUOTA7",
    map:{x:33,y:48}, col:"#e4532f", col2:"#f2a33a", emblema:"🎡",
    blurb:"Il maestro Michele Ducato dipinge a mano i carretti siciliani, con cavalieri, battaglie e colori accesi. Vedrai nascere una ruota dipinta.",
    fatto:"Ogni carretto racconta una storia diversa: è un fumetto che cammina su ruote." },
  { id:"guttuso", num:2, nome:"Pennellina", dove:"Museo Guttuso – Villa Cattolica", quando:"febbraio 2027",
    coord:[38.08991, 13.50147], raggio:200, approx:false, qr:"APAYAYE:guttuso:QUADRO2",
    map:{x:60,y:60}, col:"#c2418a", col2:"#f0a33a", emblema:"🎨",
    blurb:"Una villa del Settecento diventata museo. Qui vivono i quadri di Renato Guttuso, il grande pittore nato proprio a Bagheria.",
    fatto:"Nel giardino c'è la sua tomba: una grande scultura azzurra a forma di vela." },
  { id:"orto", num:3, nome:"Germoglio", dove:"Orto botanico di Palermo", quando:"marzo 2027",
    coord:[38.11250, 13.37250], raggio:250, approx:false, qr:"APAYAYE:orto:FOGLIA3",
    map:{x:15,y:55}, col:"#3f9e54", col2:"#8fcf5a", emblema:"🌿",
    blurb:"Un giardino immenso con alberi arrivati da tutto il mondo, alcuni più grandi di una casa.",
    fatto:"Il Ficus magnolioides ha radici come tentacoli che fanno ombra a una piazza intera. Aperto più di 200 anni fa!" },
  { id:"acciuga", num:4, nome:"Acciughina", dove:"Museo dell'Acciuga di Aspra", quando:"marzo 2027",
    coord:[38.0958, 13.5305], raggio:200, approx:true, qr:"APAYAYE:acciuga:PESCE4",
    map:{x:49,y:37}, col:"#4aa0c4", col2:"#cfe3ec", emblema:"🐟",
    blurb:"Nel borgo di pescatori di Aspra si racconta la pesca e come si lavoravano le acciughe, un mestiere di mare.",
    fatto:"Aspra è un paese di pescatori: qui il mare è lavoro, cibo e festa." },
  { id:"grano", num:5, nome:"Granello", dove:"Laboratorio del grano Tumminia", quando:"aprile 2027",
    coord:[38.0500, 13.5200], raggio:400, approx:true, qr:"APAYAYE:grano:SPIGA5",
    map:{x:47,y:74}, col:"#d79a2a", col2:"#f0cf6a", emblema:"🌾",
    blurb:"La Tumminia è un grano antico siciliano. In fattoria didattica si impara a fare il pane, dal chicco alla pagnotta.",
    fatto:"Con la farina di Tumminia si fa il famoso pane nero di Castelvetrano." },
  { id:"mezzojuso", num:6, nome:"Pergamena", dove:"Mezzojuso", quando:"maggio 2027",
    coord:[37.8686, 13.4653], raggio:600, approx:true, qr:"APAYAYE:mezzojuso:LIBRO6",
    map:{x:38,y:100}, col:"#8a5bc0", col2:"#e0a93a", emblema:"📜",
    blurb:"Un paese di montagna con tradizioni arbëreshe (italo-albanesi) e una biblioteca che custodisce pergamene antichissime.",
    fatto:"A Mezzojuso si parla ancora una lingua arrivata dall'Albania più di 500 anni fa." },
  { id:"catalfano", num:7, nome:"Falchetto", dove:"Monte Catalfano", quando:"maggio 2027",
    coord:[38.0875, 13.5560], raggio:500, approx:true, qr:"APAYAYE:catalfano:FALCO7",
    map:{x:75,y:47}, col:"#b07a3e", col2:"#8ec3e0", emblema:"🦅",
    blurb:"Una collina verde sopra Bagheria, con sentieri, profumi di macchia mediterranea e una vista enorme sul mare.",
    fatto:"Dalla cima si vedono le isole e, lì vicino, le antiche rovine della città di Solunto." },
  { id:"barca", num:8, nome:"Ondina", dove:"Giro in barca", quando:"giugno/luglio 2027",
    coord:[38.0988, 13.5325], raggio:500, approx:true, qr:"APAYAYE:barca:ONDA8",
    map:{x:64,y:19}, col:"#2f9ec4", col2:"#bfe7f2", emblema:"🌊",
    blurb:"Si parte dal porticciolo di Aspra per guardare la costa dal mare, dove la terra sembra un'altra cosa.",
    fatto:"Dal mare le grotte e le scogliere si vedono come non le vedi mai da terra." }
];
