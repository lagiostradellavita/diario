/* I luoghi delle uscite Apayaye 2026/2027.
   coord: [lat, lng]; raggio in metri entro cui il GPS sblocca. "approx:true" = da rifinire sul posto.
   map: posizione sulla mappa illustrata (viewBox 100 x 120). qr: codice del QR stampato.
   emblema: emoji sul segnaposto. frase: la "voce" del personaggio. */

var ART = {
 carretti:'<svg viewBox="0 0 100 100" aria-hidden="true"><ellipse cx="50" cy="93" rx="26" ry="4" fill="rgba(0,0,0,.13)"/><circle cx="50" cy="50" r="40" fill="#e4532f"/><circle cx="50" cy="50" r="40" fill="none" stroke="#b63c1f" stroke-width="3"/><g fill="#ffd56b"><polygon points="50,12 46,20 54,20"/><polygon points="50,88 46,80 54,80"/><polygon points="12,50 20,46 20,54"/><polygon points="88,50 80,46 80,54"/></g><g fill="#2f9ec4"><polygon points="76,24 70,27 74,31"/><polygon points="24,24 30,27 26,31"/><polygon points="76,76 70,73 74,69"/><polygon points="24,76 30,73 26,69"/></g><circle cx="50" cy="50" r="27" fill="#fff"/><g stroke="#e4532f" stroke-width="3" stroke-linecap="round"><line x1="50" y1="25" x2="50" y2="75"/><line x1="25" y1="50" x2="75" y2="50"/><line x1="33" y1="33" x2="67" y2="67"/><line x1="67" y1="33" x2="33" y2="67"/></g><circle cx="50" cy="50" r="18" fill="#f2a33a"/><ellipse cx="43" cy="48" rx="5.5" ry="6.5" fill="#fff"/><ellipse cx="57" cy="48" rx="5.5" ry="6.5" fill="#fff"/><circle cx="44" cy="49" r="2.7" fill="#241a10"/><circle cx="58" cy="49" r="2.7" fill="#241a10"/><path d="M44 58 Q50 63 56 58" fill="none" stroke="#241a10" stroke-width="2.4" stroke-linecap="round"/></svg>',
 guttuso:'<svg viewBox="0 0 100 100" aria-hidden="true"><ellipse cx="50" cy="93" rx="24" ry="4" fill="rgba(0,0,0,.13)"/><circle cx="34" cy="28" r="11" fill="#e4532f"/><circle cx="50" cy="21" r="12" fill="#ffd33a"/><circle cx="66" cy="28" r="11" fill="#2f9ec4"/><circle cx="58" cy="33" r="8" fill="#3f9e54"/><circle cx="42" cy="33" r="7" fill="#8a5bc0"/><path d="M26 54 C26 36 74 36 74 54 C74 74 62 86 50 86 C38 86 26 74 26 54 Z" fill="#c2418a"/><ellipse cx="42" cy="56" rx="7" ry="8" fill="#fff"/><ellipse cx="60" cy="56" rx="7" ry="8" fill="#fff"/><circle cx="43" cy="57" r="3.3" fill="#241a10"/><circle cx="61" cy="57" r="3.3" fill="#241a10"/><circle cx="33" cy="66" r="4" fill="#e78ab8"/><circle cx="69" cy="66" r="4" fill="#e78ab8"/><path d="M44 68 Q51 74 58 68" fill="none" stroke="#241a10" stroke-width="2.5" stroke-linecap="round"/><g transform="rotate(34 82 74)"><rect x="79" y="54" width="6" height="26" rx="3" fill="#8a5a2a"/><rect x="78.5" y="48" width="7" height="8" rx="2" fill="#d8d8d8"/><path d="M79 49 h7 l-1.5 -8 h-4 Z" fill="#e4532f"/></g></svg>',
 orto:'<svg viewBox="0 0 100 100" aria-hidden="true"><ellipse cx="50" cy="93" rx="22" ry="4" fill="rgba(0,0,0,.13)"/><path d="M50 42 C40 24 22 24 20 37 C31 46 46 46 50 42 Z" fill="#8fcf5a"/><path d="M50 42 C60 24 78 24 80 37 C69 46 54 46 50 42 Z" fill="#3f9e54"/><path d="M50 44 V60" stroke="#2f7d3a" stroke-width="3" stroke-linecap="round"/><path d="M30 62 C30 51 70 51 70 62 C70 78 60 87 50 87 C40 87 30 78 30 62 Z" fill="#6fb04a"/><ellipse cx="43" cy="64" rx="6.5" ry="7.5" fill="#fff"/><ellipse cx="57" cy="64" rx="6.5" ry="7.5" fill="#fff"/><circle cx="44" cy="65" r="3.1" fill="#241a10"/><circle cx="58" cy="65" r="3.1" fill="#241a10"/><circle cx="35" cy="72" r="3.5" fill="#f0a86a"/><circle cx="65" cy="72" r="3.5" fill="#f0a86a"/><path d="M44 74 Q50 79 56 74" fill="none" stroke="#241a10" stroke-width="2.4" stroke-linecap="round"/></svg>',
 acciuga:'<svg viewBox="0 0 100 100" aria-hidden="true"><ellipse cx="50" cy="90" rx="24" ry="4" fill="rgba(0,0,0,.12)"/><path d="M68 55 L90 43 L88 67 Z" fill="#2f7fa0"/><path d="M16 55 C28 34 66 34 76 55 C66 76 28 76 16 55 Z" fill="#4aa0c4"/><path d="M26 59 C36 51 58 51 66 59 C58 67 36 67 26 59 Z" fill="#cfe3ec"/><path d="M44 39 L52 29 L58 41 Z" fill="#2f7fa0"/><circle cx="32" cy="52" r="7.5" fill="#fff"/><circle cx="31" cy="52" r="3.4" fill="#241a10"/><path d="M22 61 Q27 65 33 62" fill="none" stroke="#1d5f7a" stroke-width="2.3" stroke-linecap="round"/></svg>',
 grano:'<svg viewBox="0 0 100 100" aria-hidden="true"><ellipse cx="50" cy="93" rx="22" ry="4" fill="rgba(0,0,0,.13)"/><path d="M50 12 V42" stroke="#b9791a" stroke-width="3" stroke-linecap="round"/><g fill="#e8b23a"><ellipse cx="50" cy="13" rx="3.5" ry="6"/><ellipse cx="43" cy="20" rx="3.5" ry="6" transform="rotate(-35 43 20)"/><ellipse cx="57" cy="20" rx="3.5" ry="6" transform="rotate(35 57 20)"/><ellipse cx="42" cy="28" rx="3.5" ry="6" transform="rotate(-35 42 28)"/><ellipse cx="58" cy="28" rx="3.5" ry="6" transform="rotate(35 58 28)"/><ellipse cx="42" cy="36" rx="3.5" ry="6" transform="rotate(-35 42 36)"/><ellipse cx="58" cy="36" rx="3.5" ry="6" transform="rotate(35 58 36)"/></g><path d="M30 60 C30 48 70 48 70 60 C70 77 60 87 50 87 C40 87 30 77 30 60 Z" fill="#d79a2a"/><ellipse cx="43" cy="62" rx="6.5" ry="7.5" fill="#fff"/><ellipse cx="57" cy="62" rx="6.5" ry="7.5" fill="#fff"/><circle cx="44" cy="63" r="3.1" fill="#241a10"/><circle cx="58" cy="63" r="3.1" fill="#241a10"/><path d="M44 72 Q50 77 56 72" fill="none" stroke="#241a10" stroke-width="2.4" stroke-linecap="round"/></svg>',
 mezzojuso:'<svg viewBox="0 0 100 100" aria-hidden="true"><ellipse cx="50" cy="93" rx="22" ry="4" fill="rgba(0,0,0,.13)"/><rect x="29" y="24" width="42" height="54" rx="4" fill="#f6ecd2"/><rect x="22" y="19" width="56" height="13" rx="6.5" fill="#8a5bc0"/><rect x="22" y="70" width="56" height="13" rx="6.5" fill="#8a5bc0"/><rect x="22.5" y="19.5" width="55" height="12" rx="6" fill="none" stroke="#e0a93a" stroke-width="2"/><rect x="22.5" y="70.5" width="55" height="12" rx="6" fill="none" stroke="#e0a93a" stroke-width="2"/><g stroke="#c58f22" stroke-width="2.6" stroke-linecap="round"><line x1="50" y1="33" x2="50" y2="44"/><line x1="44" y1="38" x2="56" y2="38"/></g><ellipse cx="43" cy="55" rx="6" ry="7" fill="#fff"/><ellipse cx="57" cy="55" rx="6" ry="7" fill="#fff"/><circle cx="44" cy="56" r="2.9" fill="#241a10"/><circle cx="58" cy="56" r="2.9" fill="#241a10"/><path d="M44 63 Q50 67 56 63" fill="none" stroke="#241a10" stroke-width="2.3" stroke-linecap="round"/></svg>',
 catalfano:'<svg viewBox="0 0 100 100" aria-hidden="true"><ellipse cx="50" cy="93" rx="22" ry="4" fill="rgba(0,0,0,.13)"/><path d="M26 55 C16 57 15 67 23 71 C27 64 29 58 27 54 Z" fill="#8a5e2c"/><path d="M74 55 C84 57 85 67 77 71 C73 64 71 58 73 54 Z" fill="#8a5e2c"/><path d="M28 56 C28 38 72 38 72 56 C72 76 60 86 50 86 C40 86 28 76 28 56 Z" fill="#b07a3e"/><path d="M38 61 C42 53 58 53 62 61 C60 75 40 75 38 61 Z" fill="#ead2ad"/><path d="M35 39 l9 6 -10 3 Z" fill="#8a5e2c"/><path d="M65 39 l-9 6 10 3 Z" fill="#8a5e2c"/><circle cx="42" cy="51" r="7.5" fill="#fff"/><circle cx="58" cy="51" r="7.5" fill="#fff"/><circle cx="43" cy="52" r="3.4" fill="#241a10"/><circle cx="57" cy="52" r="3.4" fill="#241a10"/><path d="M45 59 L55 59 L50 67 Z" fill="#f0a93a"/></svg>',
 barca:'<svg viewBox="0 0 100 100" aria-hidden="true"><ellipse cx="50" cy="93" rx="22" ry="4" fill="rgba(0,0,0,.12)"/><path d="M24 64 C24 46 40 36 52 42 C60 46 62 55 70 55 C80 55 83 67 77 75 C67 87 33 87 26 77 C22 73 24 68 24 64 Z" fill="#2f9ec4"/><g fill="#eef7fb"><circle cx="43" cy="40" r="8"/><circle cx="56" cy="35" r="9"/><circle cx="67" cy="44" r="7"/></g><path d="M34 66 C40 60 60 60 66 66 C60 78 40 78 34 66 Z" fill="#bfe7f2"/><ellipse cx="43" cy="60" rx="6.5" ry="7.5" fill="#fff"/><ellipse cx="57" cy="60" rx="6.5" ry="7.5" fill="#fff"/><circle cx="44" cy="61" r="3.1" fill="#241a10"/><circle cx="58" cy="61" r="3.1" fill="#241a10"/><path d="M44 70 Q50 75 56 70" fill="none" stroke="#1d5f7a" stroke-width="2.4" stroke-linecap="round"/></svg>',
 palagonia:'<svg viewBox="0 0 100 100" aria-hidden="true"><ellipse cx="50" cy="93" rx="24" ry="4" fill="rgba(0,0,0,.14)"/><path d="M33 30 L27 13 L41 27 Z" fill="#6c4e8a"/><path d="M67 30 L73 13 L59 27 Z" fill="#6c4e8a"/><path d="M26 52 C26 30 74 30 74 52 C74 75 62 87 50 87 C38 87 26 75 26 52 Z" fill="#8e6fb3"/><path d="M30 41 C33 36 44 36 47 41" fill="none" stroke="#6c4e8a" stroke-width="3" stroke-linecap="round"/><circle cx="40" cy="50" r="11" fill="#fff"/><circle cx="62" cy="52" r="7.5" fill="#fff"/><circle cx="41" cy="51" r="4.8" fill="#241a10"/><circle cx="62" cy="53" r="3.3" fill="#241a10"/><circle cx="51" cy="61" r="4.2" fill="#8fcf5a"/><path d="M35 66 Q50 82 65 66 Q58 73 50 73 Q42 73 35 66 Z" fill="#3a2a16"/><polygon points="41,67 46,67 43.5,73" fill="#fff"/><polygon points="55,67 60,67 57.5,73" fill="#fff"/></svg>'
};
function artLuogo(l){ return ART[l.id] || ""; }

var LUOGHI = [
  { id:"carretti", num:1, nome:"Rotella", dove:"Bottega dei carretti di Michele Ducato", quando:"dicembre 2026",
    coord:[38.0945, 13.5290], raggio:250, approx:true, qr:"APAYAYE:carretti:RUOTA7",
    map:{x:33,y:48}, col:"#e4532f", col2:"#f2a33a", emblema:"🎡",
    frase:"Gira, gira: ogni mia ruota racconta una storia!",
    blurb:"Il carretto siciliano è un carro a due ruote, tirato da un cavallo o da un asino. Tra l'Ottocento e il Novecento era il «camion» della Sicilia: portava grano, vino, sale, legna e perfino le persone, e negli anni Venti ne circolavano a migliaia per le strade dell'isola. Non lo costruiva una persona sola: ci lavoravano insieme più artigiani. Il carradore faceva la struttura di legno e le ruote, lo scultore intagliava le sponde, il fabbro batteva il ferro; poi il decoratore riempiva le parti lisce di disegni geometrici e, alla fine, il pittore dipingeva le grandi scene colorate sulle fiancate. Un carretto così non era soltanto un mezzo di lavoro: era un'opera d'arte che camminava.",
    fatto:"Le fiancate raccontano una «storia figurata»: duelli di paladini, cavalieri, re e santi. Si credeva che quelle immagini portassero fortuna e tenessero lontano il malocchio, come un portafortuna gigante montato su ruote.",
    curiosita:[
      "A Palermo i carretti hanno le sponde a forma di trapezio, il fondo giallo e tanti disegni geometrici.",
      "Nella zona di Catania sono diversi: sponde dritte e legno intagliato a rilievo, quasi una scultura.",
      "C'era il «carretto da lavoro», per le merci, e il «carretto da gara», tutto lucido, per le feste e i matrimoni.",
      "Le storie dipinte erano spesso quelle dei paladini di Francia, come nell'Opera dei Pupi.",
      "Le ruote erano la parte più difficile: i mozzi venivano fusi in una lega di rame e stagno.",
      "Oggi i carretti non lavorano più, ma sfilano nelle feste e qualcuno li dipinge perfino sulle Ape a tre ruote."
    ] },
  { id:"guttuso", num:2, nome:"Pennellina", dove:"Museo Guttuso – Villa Cattolica", quando:"febbraio 2027",
    coord:[38.08991, 13.50147], raggio:200, approx:false, qr:"APAYAYE:guttuso:QUADRO2",
    map:{x:60,y:60}, col:"#c2418a", col2:"#f0a33a", emblema:"🎨",
    frase:"Dammi un colore e ti dipingo tutto il mondo!",
    blurb:"Villa Cattolica è una grande villa barocca di Bagheria, costruita fra il 1706 e il 1736 per la famiglia Bonanno, con una curiosa pianta a forma di quadrifoglio. «Barocca» vuol dire ricca di curve, scaloni e decorazioni: era la casa di campagna di una famiglia nobile. Dal 1973 è diventata un museo, perché il pittore Renato Guttuso — nato proprio a Bagheria nel 1911 — regalò alla sua città tante opere. Oggi, salendo le scale, si incontrano i suoi quadri dai colori accesi: contadini al lavoro, mercati pieni di cibo, limoni, tetti e il mare della Sicilia; e accanto ci sono opere di molti altri artisti.",
    fatto:"Guttuso è sepolto nel giardino della villa, dentro una grande arca di pietra scolpita apposta dal suo amico, il famoso scultore Giacomo Manzù: una tomba che è anche un'opera d'arte.",
    curiosita:[
      "Guttuso è uno dei pittori italiani più famosi del Novecento, conosciuto in tutto il mondo.",
      "Il suo quadro più celebre è «La Vucciria», il grande mercato di Palermo traboccante di cibo e di colori.",
      "Amava dipingere la vita vera: la gente che lavora, la frutta, i fichidindia, le battaglie.",
      "La villa è protetta come monumento fin dal 1931, quasi cento anni fa.",
      "Nel museo sono raccolte quasi duecento opere, fra quadri donati e lavori di tanti artisti diversi.",
      "Bagheria è chiamata «la città delle ville»: Villa Cattolica è una delle più grandi."
    ] },
  { id:"orto", num:3, nome:"Germoglio", dove:"Orto botanico di Palermo", quando:"marzo 2027",
    coord:[38.11250, 13.37250], raggio:250, approx:false, qr:"APAYAYE:orto:FOGLIA3",
    map:{x:15,y:55}, col:"#3f9e54", col2:"#8fcf5a", emblema:"🌿",
    frase:"Da piccolo seme divento più alto di una casa!",
    blurb:"L'Orto botanico di Palermo è un giardino scientifico immenso, fondato nel 1789 e aperto nel 1795: più di duecento anni fa. Lo progettarono l'architetto francese Léon Dufourny e il siciliano Giuseppe Venanzio Marvuglia, e col tempo è cresciuto fino a circa dieci ettari, grande come tanti campi di calcio messi uno accanto all'altro. Dentro vivono oltre dodicimila tipi di piante arrivate da tutto il mondo: palme altissime, bambù, cactus e piante grasse enormi, un intero boschetto di palme e tanti alberi di agrumi. Ci sono laghetti con le ninfee, un acquario rotondo pieno di papiri e grandi serre calde per le piante dei paesi tropicali.",
    fatto:"Il re del giardino è un gigantesco Ficus magnolioides, arrivato dall'isola di Norfolk nel 1845: le sue radici scendono dai rami e si allargano a terra come colonne, formando un tetto d'ombra grande come una piazza. È uno degli alberi più grandi d'Europa.",
    curiosita:[
      "È nato come giardino di studio: serviva a conoscere le piante utili e le medicine che se ne ricavano.",
      "L'edificio principale, il Gymnasium, è in stile neoclassico, come un tempietto antico.",
      "L'acquario è una vasca rotonda con papiri e ninfee, le piante che vivono dentro l'acqua.",
      "Le piante sono ordinate in «stanze verdi»: le palme con le palme, i cactus con i cactus.",
      "Ci sono serre calde, come la Serra Maria Carolina, per le piante che amano il caldo tutto l'anno.",
      "Tante piante vivono qui da oltre cento anni: erano già grandi al tempo dei nostri bisnonni."
    ] },
  { id:"acciuga", num:4, nome:"Acciughina", dove:"Museo dell'Acciuga di Aspra", quando:"marzo 2027",
    coord:[38.0958, 13.5305], raggio:200, approx:true, qr:"APAYAYE:acciuga:PESCE4",
    map:{x:49,y:37}, col:"#4aa0c4", col2:"#cfe3ec", emblema:"🐟",
    frase:"Piccola piccola, ma il mare è casa mia!",
    blurb:"Aspra è un piccolo borgo di pescatori affacciato sul mare, una frazione di Bagheria. Qui i fratelli Balistreri hanno preso il vecchio stabilimento della loro famiglia — il posto dove si lavorava il pesce — e l'hanno trasformato in un museo tutto dedicato all'acciuga. Dentro raccontano come si usciva in barca di notte, come si tirava la rete e come si salavano le acciughe nei barili per farle durare: un mestiere antichissimo, conosciuto in Sicilia fin dal Medioevo, che per tanto tempo ha dato da mangiare a tutto il paese. È un museo nato dall'amore dei pescatori per il loro lavoro.",
    fatto:"Dentro si vedono reti, ceste, lampade, modellini di barche e perfino la vera barca usata per pescare: tutto il mondo del mare raccolto in un edificio solo.",
    curiosita:[
      "Le acciughe si conservano sotto sale dentro grossi contenitori e si girano a mano, con tanta pazienza.",
      "L'ingresso al museo è gratuito, e a farti da guida sono gli stessi pescatori della famiglia.",
      "Nel museo è esposto anche lo scheletro di una grande balenottera.",
      "L'acciuga è un pesce piccolissimo, ma è il «pane del mare»: sfama e dà sapore a tanti piatti.",
      "Un tempo ad Aspra quasi tutte le famiglie vivevano di pesca e di sale.",
      "Il museo ha ricevuto un premio grazie ai bei giudizi dei visitatori."
    ] },
  { id:"grano", num:5, nome:"Granello", dove:"Laboratorio del grano Tumminia", quando:"aprile 2027",
    coord:[38.0500, 13.5200], raggio:400, approx:true, qr:"APAYAYE:grano:SPIGA5",
    map:{x:47,y:74}, col:"#d79a2a", col2:"#f0cf6a", emblema:"🌾",
    frase:"Da un chicco nasce il pane… e la merenda!",
    blurb:"La Tumminia (in siciliano «timilia») è un grano duro antico, coltivato in Sicilia fin dai tempi degli antichi Greci, soprattutto nella zona di Trapani. «Grano antico» vuol dire che è rimasto lo stesso di secoli fa: la pianta è alta, con lunghe spighe, e resiste bene al caldo e alla siccità dell'isola. In una fattoria didattica si può seguire tutto il viaggio del grano: il chicco seminato nel campo in autunno, la spiga dorata che matura al sole, la macina di pietra che lo trasforma in farina e, alla fine, le mani che impastano il pane. La sua farina è color nocciola e profuma di mandorle tostate.",
    fatto:"Con la Tumminia si fa un pane scuro e profumato, il famoso «pane nero»: la farina si macina lentamente fra due pietre, e l'impasto ha bisogno di più tempo per lievitare rispetto a quello normale.",
    curiosita:[
      "È un «grano antico»: la pianta è più alta di quelle moderne e non teme il caldo né la siccità.",
      "La sua farina ha molto nutrimento e poco glutine, ed è protetta da Slow Food.",
      "Si macina «a pietra», come una volta, e così la farina conserva tutto il suo profumo.",
      "Dal chicco alla pagnotta passano mesi: si semina in autunno e si miete all'inizio dell'estate.",
      "Il pane di Tumminia resta buono e morbido anche per più giorni.",
      "Impastare a mano è anche un gioco: si sente la farina che pian piano diventa pane."
    ] },
  { id:"mezzojuso", num:6, nome:"Pergamena", dove:"Mezzojuso", quando:"maggio 2027",
    coord:[37.8686, 13.4653], raggio:600, approx:true, qr:"APAYAYE:mezzojuso:LIBRO6",
    map:{x:38,y:100}, col:"#8a5bc0", col2:"#e0a93a", emblema:"📜",
    frase:"Shh… custodisco parole di cinquecento anni fa.",
    blurb:"Mezzojuso è un paese di montagna vicino a Palermo, nato come colonia arbëreshe nel Quattrocento: vi arrivarono famiglie dall'Albania, che portarono la loro lingua, i loro canti e le loro feste. È una cosa rara e preziosa, perché ancora oggi molti abitanti parlano l'arbëresh e seguono il rito greco-bizantino durante la Messa; per questo il paese è chiamato l'«Atene» degli arbëreshe. Nel 1601 qui fu fondato un monastero che divenne un grande centro di cultura, con una biblioteca famosa. Passeggiare per i vicoli di Mezzojuso è come visitare un pezzetto d'Albania rimasto in Sicilia da più di cinquecento anni.",
    fatto:"Il monastero custodisce una biblioteca preziosissima, con antichi codici scritti a mano in greco e libri stampati cinquecento anni fa: veri tesori di carta e di pergamena, da proteggere con cura.",
    curiosita:[
      "A Mezzojuso si parla ancora l'arbëresh, la lingua arrivata dall'Albania secoli fa.",
      "La Messa qui segue il rito greco-bizantino, diverso da quello delle altre chiese italiane.",
      "La festa più famosa è il «Mastro di Campo»: un cavaliere mascherato «assalta» il castello per amore della regina.",
      "Quella pantomima si recita a Carnevale, in piazza, da più di due secoli.",
      "La sua storia ricorda la regina Bianca di Navarra e l'antico castello di Solanto.",
      "I libri un tempo si scrivevano e si copiavano a mano, molto prima che esistessero le stampanti."
    ] },
  { id:"catalfano", num:7, nome:"Falchetto", dove:"Monte Catalfano", quando:"maggio 2027",
    coord:[38.0875, 13.5560], raggio:500, approx:true, qr:"APAYAYE:catalfano:FALCO7",
    map:{x:75,y:47}, col:"#b07a3e", col2:"#8ec3e0", emblema:"🦅",
    frase:"Dalla cima vedo il mare, le isole e anche te!",
    blurb:"Monte Catalfano è una collina verde di circa 370 metri che sovrasta Bagheria e guarda il Golfo di Palermo. È il «polmone verde» della zona: un grande parco di quasi trecento ettari, fatto di roccia calcarea chiara e di macchia mediterranea profumata — rosmarino, timo, mirto, finocchietto — dove volano falchi e tanti altri uccelli. Si cammina lungo i sentieri tra gli odori delle erbe, e dalla cima si apre una vista enorme sul mare, sulle isole e su tutta la città. Ma la sorpresa più grande è sotto i piedi: sul monte ci sono le rovine di un'intera città antica.",
    fatto:"Tra gli alberi si trovano le rovine di Solunto, una città di oltre duemila anni fa: aveva strade dritte a griglia, un teatro affacciato sul mare, una palestra e case ricche con pavimenti a mosaico. Passò sotto Roma nel 254 a.C.",
    curiosita:[
      "Le strade di Solunto erano così in pendenza che in alcuni punti salgono come uno scivolo ripido.",
      "Le case raccoglievano l'acqua della pioggia in cisterne nascoste sotto il pavimento.",
      "La casa più famosa è la «Casa di Leda», con bellissimi mosaici colorati.",
      "All'ingresso c'è un piccolo museo, l'Antiquarium, con gli oggetti ritrovati fra le rovine.",
      "La collina è di roccia calcarea: tantissimo tempo fa era un isolotto in mezzo al mare.",
      "Camminare fra le rovine è come fare un viaggio nel tempo fino agli antichi Greci e Romani."
    ] },
  { id:"barca", num:8, nome:"Ondina", dove:"Giro in barca", quando:"giugno/luglio 2027",
    coord:[38.0988, 13.5325], raggio:500, approx:true, qr:"APAYAYE:barca:ONDA8",
    map:{x:64,y:19}, col:"#2f9ec4", col2:"#bfe7f2", emblema:"🌊",
    frase:"Saliamo? Ti porto dove finisce la terra!",
    blurb:"Dal porticciolo di Aspra si sale in barca per guardare la costa di Bagheria da un punto di vista speciale: il mare. Appena ci si allontana da terra, tutto cambia. Le scogliere, le casette dei pescatori e le grotte si vedono in un modo completamente nuovo, e l'acqua passa dal verde chiaro vicino alla riva all'azzurro profondo al largo. È lo stesso modo in cui, da sempre, i pescatori di Aspra hanno imparato a conoscere il loro mare: osservando il vento, le onde e la linea della costa. Dalla barca si capisce quanto il mare sia importante per chi vive qui.",
    fatto:"Alcune grotte lungo la costa si possono raggiungere soltanto dal mare: da terra, a piedi, non ci si arriva proprio. Sono nascondigli che solo chi va in barca può scoprire.",
    curiosita:[
      "Aspra è un borgo di pescatori: le barche partono dal suo porticciolo ancora oggi.",
      "In barca si impara a leggere il vento, le onde e la rotta da seguire.",
      "Più ci si allontana dalla riva, più l'acqua diventa blu scuro: vuol dire che è profonda.",
      "Spesso i gabbiani seguono la barca, e a volte un pesce salta fuori dall'acqua.",
      "Dal mare si vedono bene il Monte Catalfano e le ville di Bagheria, tutti insieme.",
      "I pescatori conoscono il mare a memoria: sanno dove sono le secche e le grotte senza bisogno di mappe."
    ] },
  { id:"palagonia", num:9, nome:"Mostrino", dove:"Villa Palagonia, la Villa dei Mostri", quando:"gennaio 2027",
    coord:[38.0806, 13.5099], raggio:150, approx:true, qr:"APAYAYE:palagonia:MOSTRO9",
    map:{x:70,y:72}, col:"#8e6fb3", col2:"#8fcf5a", emblema:"🗿",
    frase:"Non avere paura: siamo mostri… ma simpatici!",
    blurb:"Villa Palagonia, a Bagheria, è una villa barocca iniziata nel 1715 e conosciuta da tutti come la «Villa dei Mostri». È famosa in tutta Europa, e deve il suo soprannome alle decine di statue di pietra stranissime che stanno sul muro di cinta: musicisti, dame, cavalieri, animali, draghi, nani e creature mai viste, scolpite nel tenero tufo giallo di Aspra. A volerle, nel Settecento, fu il principe Ferdinando Francesco II Gravina, soprannominato «il Negromante», un uomo bizzarro che amava tutto ciò che era strano e fantastico. Entrando si sale uno scalone a doppia rampa e si arriva a saloni pieni di marmi, vetri colorati e specchi.",
    fatto:"La stanza più magica è il Salone degli Specchi: il soffitto è dipinto con un cielo azzurro e tanti uccelli, e le pareti sono ricoperte di specchi che un tempo deformavano in modo buffo l'immagine di chi entrava, come in una casa degli specchi.",
    curiosita:[
      "Un tempo le statue erano circa duecento; oggi ne restano una sessantina sul muro.",
      "Sono scolpite nel tufo di Aspra, una pietra chiara e tenera, facile da lavorare.",
      "Si racconta che il principe credesse che i «mostri» lo proteggessero dagli spiriti cattivi.",
      "Il grande scrittore tedesco Goethe la visitò nel 1787 e ne scrisse nel suo diario di viaggio.",
      "Si dice che quelle creature abbiano ispirato alcuni mostri di una sua opera famosa, il «Faust».",
      "Ogni statua è diversa dalle altre: è come una galleria di personaggi di pietra, una più buffa dell'altra."
    ] }
];
