/* I luoghi delle uscite Apayaye 2026/2027.
   coord: [lat, lng] della posizione reale; raggio in metri entro cui il GPS sblocca.
   Le posizioni marcate "approx:true" sono da rifinire sul posto (l'animatore usa "fissa qui"
   nella versione con account). Il QR funziona comunque, anche al chiuso, senza GPS.
   map: posizione del segnaposto sulla mappa illustrata (viewBox 100 x 120).
   qr: codice contenuto nel QR stampato (vedi stampa.html).
   emblema: l'emoji sul segnaposto della mappa. */

/* I disegni dei personaggi: un SVG per ogni luogo, pensato su misura del posto. */
var ART = {
 carretti:'<svg viewBox="0 0 100 100" aria-hidden="true"><ellipse cx="50" cy="93" rx="26" ry="4" fill="rgba(0,0,0,.13)"/><circle cx="50" cy="50" r="40" fill="#e4532f"/><circle cx="50" cy="50" r="40" fill="none" stroke="#b63c1f" stroke-width="3"/><g fill="#ffd56b"><polygon points="50,12 46,20 54,20"/><polygon points="50,88 46,80 54,80"/><polygon points="12,50 20,46 20,54"/><polygon points="88,50 80,46 80,54"/></g><g fill="#2f9ec4"><polygon points="76,24 70,27 74,31"/><polygon points="24,24 30,27 26,31"/><polygon points="76,76 70,73 74,69"/><polygon points="24,76 30,73 26,69"/></g><circle cx="50" cy="50" r="27" fill="#fff"/><g stroke="#e4532f" stroke-width="3" stroke-linecap="round"><line x1="50" y1="25" x2="50" y2="75"/><line x1="25" y1="50" x2="75" y2="50"/><line x1="33" y1="33" x2="67" y2="67"/><line x1="67" y1="33" x2="33" y2="67"/></g><circle cx="50" cy="50" r="18" fill="#f2a33a"/><ellipse cx="43" cy="48" rx="5.5" ry="6.5" fill="#fff"/><ellipse cx="57" cy="48" rx="5.5" ry="6.5" fill="#fff"/><circle cx="44" cy="49" r="2.7" fill="#241a10"/><circle cx="58" cy="49" r="2.7" fill="#241a10"/><path d="M44 58 Q50 63 56 58" fill="none" stroke="#241a10" stroke-width="2.4" stroke-linecap="round"/></svg>',
 guttuso:'<svg viewBox="0 0 100 100" aria-hidden="true"><ellipse cx="50" cy="93" rx="24" ry="4" fill="rgba(0,0,0,.13)"/><circle cx="34" cy="28" r="11" fill="#e4532f"/><circle cx="50" cy="21" r="12" fill="#ffd33a"/><circle cx="66" cy="28" r="11" fill="#2f9ec4"/><circle cx="58" cy="33" r="8" fill="#3f9e54"/><circle cx="42" cy="33" r="7" fill="#8a5bc0"/><path d="M26 54 C26 36 74 36 74 54 C74 74 62 86 50 86 C38 86 26 74 26 54 Z" fill="#c2418a"/><ellipse cx="42" cy="56" rx="7" ry="8" fill="#fff"/><ellipse cx="60" cy="56" rx="7" ry="8" fill="#fff"/><circle cx="43" cy="57" r="3.3" fill="#241a10"/><circle cx="61" cy="57" r="3.3" fill="#241a10"/><circle cx="33" cy="66" r="4" fill="#e78ab8"/><circle cx="69" cy="66" r="4" fill="#e78ab8"/><path d="M44 68 Q51 74 58 68" fill="none" stroke="#241a10" stroke-width="2.5" stroke-linecap="round"/><g transform="rotate(34 82 74)"><rect x="79" y="54" width="6" height="26" rx="3" fill="#8a5a2a"/><rect x="78.5" y="48" width="7" height="8" rx="2" fill="#d8d8d8"/><path d="M79 49 h7 l-1.5 -8 h-4 Z" fill="#e4532f"/></g></svg>',
 orto:'<svg viewBox="0 0 100 100" aria-hidden="true"><ellipse cx="50" cy="93" rx="22" ry="4" fill="rgba(0,0,0,.13)"/><path d="M50 42 C40 24 22 24 20 37 C31 46 46 46 50 42 Z" fill="#8fcf5a"/><path d="M50 42 C60 24 78 24 80 37 C69 46 54 46 50 42 Z" fill="#3f9e54"/><path d="M50 44 V60" stroke="#2f7d3a" stroke-width="3" stroke-linecap="round"/><path d="M30 62 C30 51 70 51 70 62 C70 78 60 87 50 87 C40 87 30 78 30 62 Z" fill="#6fb04a"/><ellipse cx="43" cy="64" rx="6.5" ry="7.5" fill="#fff"/><ellipse cx="57" cy="64" rx="6.5" ry="7.5" fill="#fff"/><circle cx="44" cy="65" r="3.1" fill="#241a10"/><circle cx="58" cy="65" r="3.1" fill="#241a10"/><circle cx="35" cy="72" r="3.5" fill="#f0a86a"/><circle cx="65" cy="72" r="3.5" fill="#f0a86a"/><path d="M44 74 Q50 79 56 74" fill="none" stroke="#241a10" stroke-width="2.4" stroke-linecap="round"/></svg>',
 acciuga:'<svg viewBox="0 0 100 100" aria-hidden="true"><ellipse cx="50" cy="90" rx="24" ry="4" fill="rgba(0,0,0,.12)"/><path d="M68 55 L90 43 L88 67 Z" fill="#2f7fa0"/><path d="M16 55 C28 34 66 34 76 55 C66 76 28 76 16 55 Z" fill="#4aa0c4"/><path d="M26 59 C36 51 58 51 66 59 C58 67 36 67 26 59 Z" fill="#cfe3ec"/><path d="M44 39 L52 29 L58 41 Z" fill="#2f7fa0"/><circle cx="32" cy="52" r="7.5" fill="#fff"/><circle cx="31" cy="52" r="3.4" fill="#241a10"/><path d="M22 61 Q27 65 33 62" fill="none" stroke="#1d5f7a" stroke-width="2.3" stroke-linecap="round"/></svg>',
 grano:'<svg viewBox="0 0 100 100" aria-hidden="true"><ellipse cx="50" cy="93" rx="22" ry="4" fill="rgba(0,0,0,.13)"/><path d="M50 12 V42" stroke="#b9791a" stroke-width="3" stroke-linecap="round"/><g fill="#e8b23a"><ellipse cx="50" cy="13" rx="3.5" ry="6"/><ellipse cx="43" cy="20" rx="3.5" ry="6" transform="rotate(-35 43 20)"/><ellipse cx="57" cy="20" rx="3.5" ry="6" transform="rotate(35 57 20)"/><ellipse cx="42" cy="28" rx="3.5" ry="6" transform="rotate(-35 42 28)"/><ellipse cx="58" cy="28" rx="3.5" ry="6" transform="rotate(35 58 28)"/><ellipse cx="42" cy="36" rx="3.5" ry="6" transform="rotate(-35 42 36)"/><ellipse cx="58" cy="36" rx="3.5" ry="6" transform="rotate(35 58 36)"/></g><path d="M30 60 C30 48 70 48 70 60 C70 77 60 87 50 87 C40 87 30 77 30 60 Z" fill="#d79a2a"/><ellipse cx="43" cy="62" rx="6.5" ry="7.5" fill="#fff"/><ellipse cx="57" cy="62" rx="6.5" ry="7.5" fill="#fff"/><circle cx="44" cy="63" r="3.1" fill="#241a10"/><circle cx="58" cy="63" r="3.1" fill="#241a10"/><path d="M44 72 Q50 77 56 72" fill="none" stroke="#241a10" stroke-width="2.4" stroke-linecap="round"/></svg>',
 mezzojuso:'<svg viewBox="0 0 100 100" aria-hidden="true"><ellipse cx="50" cy="93" rx="22" ry="4" fill="rgba(0,0,0,.13)"/><rect x="29" y="24" width="42" height="54" rx="4" fill="#f6ecd2"/><rect x="22" y="19" width="56" height="13" rx="6.5" fill="#8a5bc0"/><rect x="22" y="70" width="56" height="13" rx="6.5" fill="#8a5bc0"/><rect x="22.5" y="19.5" width="55" height="12" rx="6" fill="none" stroke="#e0a93a" stroke-width="2"/><rect x="22.5" y="70.5" width="55" height="12" rx="6" fill="none" stroke="#e0a93a" stroke-width="2"/><g stroke="#c58f22" stroke-width="2.6" stroke-linecap="round"><line x1="50" y1="33" x2="50" y2="44"/><line x1="44" y1="38" x2="56" y2="38"/></g><ellipse cx="43" cy="55" rx="6" ry="7" fill="#fff"/><ellipse cx="57" cy="55" rx="6" ry="7" fill="#fff"/><circle cx="44" cy="56" r="2.9" fill="#241a10"/><circle cx="58" cy="56" r="2.9" fill="#241a10"/><path d="M44 63 Q50 67 56 63" fill="none" stroke="#241a10" stroke-width="2.3" stroke-linecap="round"/></svg>',
 catalfano:'<svg viewBox="0 0 100 100" aria-hidden="true"><ellipse cx="50" cy="93" rx="22" ry="4" fill="rgba(0,0,0,.13)"/><path d="M26 55 C16 57 15 67 23 71 C27 64 29 58 27 54 Z" fill="#8a5e2c"/><path d="M74 55 C84 57 85 67 77 71 C73 64 71 58 73 54 Z" fill="#8a5e2c"/><path d="M28 56 C28 38 72 38 72 56 C72 76 60 86 50 86 C40 86 28 76 28 56 Z" fill="#b07a3e"/><path d="M38 61 C42 53 58 53 62 61 C60 75 40 75 38 61 Z" fill="#ead2ad"/><path d="M35 39 l9 6 -10 3 Z" fill="#8a5e2c"/><path d="M65 39 l-9 6 10 3 Z" fill="#8a5e2c"/><circle cx="42" cy="51" r="7.5" fill="#fff"/><circle cx="58" cy="51" r="7.5" fill="#fff"/><circle cx="43" cy="52" r="3.4" fill="#241a10"/><circle cx="57" cy="52" r="3.4" fill="#241a10"/><path d="M45 59 L55 59 L50 67 Z" fill="#f0a93a"/></svg>',
 barca:'<svg viewBox="0 0 100 100" aria-hidden="true"><ellipse cx="50" cy="93" rx="22" ry="4" fill="rgba(0,0,0,.12)"/><path d="M24 64 C24 46 40 36 52 42 C60 46 62 55 70 55 C80 55 83 67 77 75 C67 87 33 87 26 77 C22 73 24 68 24 64 Z" fill="#2f9ec4"/><g fill="#eef7fb"><circle cx="43" cy="40" r="8"/><circle cx="56" cy="35" r="9"/><circle cx="67" cy="44" r="7"/></g><path d="M34 66 C40 60 60 60 66 66 C60 78 40 78 34 66 Z" fill="#bfe7f2"/><ellipse cx="43" cy="60" rx="6.5" ry="7.5" fill="#fff"/><ellipse cx="57" cy="60" rx="6.5" ry="7.5" fill="#fff"/><circle cx="44" cy="61" r="3.1" fill="#241a10"/><circle cx="58" cy="61" r="3.1" fill="#241a10"/><path d="M44 70 Q50 75 56 70" fill="none" stroke="#1d5f7a" stroke-width="2.4" stroke-linecap="round"/></svg>'
};
function artLuogo(l){ return ART[l.id] || ""; }

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
