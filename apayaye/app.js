"use strict";
/* Esploratori Apayaye — logica dell'app (versione 1: funziona da sola, salva sul telefono). */

var KEY = "apayaye.catturati.v1";
var catturati = {};
try { catturati = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch(e){ catturati = {}; }
function salva(){ try { localStorage.setItem(KEY, JSON.stringify(catturati)); } catch(e){} }

var testMode = false;
var posizione = null;     // {lat, lng, acc}
var gpsOn = false;
var corrente = null;      // luogo aperto nella scheda

var $ = function(id){ return document.getElementById(id); };
var mappa = $("mappa"), slotsEl = $("slots"), contaEl = $("conta");

/* ---------- distanza ---------- */
function distanza(a, b, c, d){
  var R = 6371000, r = Math.PI/180;
  var dLat = (c-a)*r, dLng = (d-b)*r;
  var s = Math.sin(dLat/2)*Math.sin(dLat/2) +
          Math.cos(a*r)*Math.cos(c*r)*Math.sin(dLng/2)*Math.sin(dLng/2);
  return 2*R*Math.asin(Math.min(1, Math.sqrt(s)));
}
function metriDa(l){
  if(!posizione) return null;
  return distanza(posizione.lat, posizione.lng, l.coord[0], l.coord[1]);
}
function testoDistanza(m){
  if(m == null) return "";
  if(m < 1000) return Math.round(m) + " m";
  return (m/1000).toFixed(1).replace(".", ",") + " km";
}

/* ---------- mappa stradale (Leaflet + OpenStreetMap, senza chiave) ---------- */
var map = L.map("mappa", { zoomControl:true, attributionControl:true });
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom:19, minZoom:9, attribution:"\u00a9 OpenStreetMap"
}).addTo(map);

/* percorso che unisce i luoghi in ordine */
(function(){
  var ord = LUOGHI.slice().sort(function(a,b){ return a.num-b.num; });
  L.polyline(ord.map(function(l){ return l.coord; }),
    { color:"#2a2118", opacity:.3, weight:3, dashArray:"5 9", lineCap:"round" }).addTo(map);
})();

/* un pin colorato e numerato per ogni luogo */
function pinIcon(l){
  var lab = l.dove.split("\u2013")[0].split(" di ")[0].trim();
  return L.divIcon({ className:"pinwrap",
    html:'<span class="pin" style="background:'+l.col+'"><span>'+l.emblema+'</span><span class="num">'+l.num+'</span></span><span class="lab">'+lab+'</span>',
    iconSize:[130,86], iconAnchor:[65,60] });
}
LUOGHI.forEach(function(l){
  l._marker = L.marker(l.coord, { icon:pinIcon(l), title:l.dove }).addTo(map);
  l._marker.on("click", function(){ apri(l); });
});

/* inquadra tutti i luoghi, poi assesta le dimensioni */
try{ map.fitBounds(L.latLngBounds(LUOGHI.map(function(l){ return l.coord; })).pad(0.15)); }catch(e){}
setTimeout(function(){ try{ map.invalidateSize(); }catch(e){} }, 300);

/* ---------- album ---------- */
var slotEls = {};
LUOGHI.forEach(function(l){
  var s = document.createElement("div");
  s.className = "slot"; slotsEl.appendChild(s); slotEls[l.id] = s;
});

function entroRaggio(l){
  var m = metriDa(l);
  return m != null && m <= l.raggio;
}
function sbloccabile(l){ return testMode || entroRaggio(l); }

function render(){
  var n = 0;
  LUOGHI.forEach(function(l){
    var preso = !!catturati[l.id];
    if(preso) n++;
    var mel = l._marker && l._marker.getElement && l._marker.getElement();
    if(mel){ mel.classList.toggle("catturato", preso); mel.classList.toggle("vicino", !preso && entroRaggio(l)); }
    var s = slotEls[l.id];
    if(preso){
      s.classList.add("filled");
      s.innerHTML = artLuogo(l);
    } else { s.classList.remove("filled"); s.innerHTML = ""; }
  });
  contaEl.textContent = n + " / " + LUOGHI.length;
}

/* ---------- scheda luogo ---------- */
var velo = $("velo"), sheet = $("sheet"), creaEl = $("crea"), cta = $("cta"), ctaScan = $("cta-scan");

function apri(l){
  corrente = l;
  $("sheet-nome").textContent = l.nome;
  $("sheet-dove").textContent = l.dove;
  $("sheet-quando").textContent = "Uscita · " + l.quando;
  $("sheet-voce").textContent = "« " + l.frase + " »";
  $("sheet-blurb").textContent = l.blurb;
  $("sheet-fatto").textContent = l.fatto;
  mostraCuriosita(l);
  creaEl.innerHTML = artLuogo(l);
  aggiornaScheda();
  velo.classList.add("on"); sheet.classList.add("on");
}
function mostraCuriosita(l){
  var ex = $("sheet-extra");
  if(!ex){
    var st=document.createElement("style");
    st.textContent=".extra{margin:12px 0 2px;font-size:.92rem;line-height:1.45;color:#5a4a2a}.extra>div{margin-bottom:12px}.extra b{display:block;color:#8a5a2a;margin-bottom:4px}.extra .storia p{margin:0}.extra ul{margin:0;padding-left:20px}.extra li{margin:4px 0}";
    document.head.appendChild(st);
    ex=document.createElement("div"); ex.id="sheet-extra"; ex.className="extra";
    var fb=$("sheet-fatto").parentNode;
    fb.parentNode.insertBefore(ex, fb.nextSibling);
  }
  var html="";
  if(l.storia){ html += '<div class="storia"><b>\uD83D\uDCD6 La sua storia</b><p>'+l.storia+'</p></div>'; }
  if(l.curiosita && l.curiosita.length){ html += '<div class="cur"><b>Lo sapevi?</b><ul>'+l.curiosita.map(function(c){return '<li>'+c+'</li>';}).join('')+'</ul></div>'; }
  ex.innerHTML = html;
  ex.style.display = html ? "" : "none";
}
function chiudi(){ velo.classList.remove("on"); sheet.classList.remove("on"); corrente = null; if("speechSynthesis" in window) speechSynthesis.cancel(); segnaAudio(false); }
velo.addEventListener("click", chiudi);

function aggiornaScheda(){
  if(!corrente) return;
  var l = corrente, distEl = $("sheet-dist");
  var preso = !!catturati[l.id];
  if(preso){ distEl.innerHTML = ""; }
  else if(posizione){
    var m = metriDa(l);
    if(m <= l.raggio) distEl.innerHTML = '<span class="vicino">✅ Sei arrivato! Puoi catturarlo.</span>';
    else distEl.innerHTML = '<span class="lontano">Sei a '+testoDistanza(m)+' dal luogo'+(l.approx?' (posizione da confermare)':'')+'</span>';
  } else {
    distEl.innerHTML = '<span class="lontano">Attiva la posizione, oppure inquadra il QR sul posto.</span>';
  }
  if(preso){
    cta.textContent = "Già nel tuo album ✓"; cta.className = "cta ok"; cta.disabled = true;
    ctaScan.style.display = "none";
  } else if(sbloccabile(l)){
    cta.textContent = testMode ? "Catturalo! (prova)" : "Catturalo!"; cta.className = "cta"; cta.disabled = false;
    ctaScan.style.display = "";
  } else {
    cta.textContent = "🔒 Avvicinati per catturarlo"; cta.className = "cta bloccato"; cta.disabled = true;
    ctaScan.style.display = "";
  }
}

cta.addEventListener("click", function(){
  if(corrente && sbloccabile(corrente)) cattura(corrente, testMode ? "prova" : "gps");
});
ctaScan.addEventListener("click", function(){ apriScanner(); });

/* ---------- voce del personaggio (parla la descrizione) ---------- */
function voceSalvata(){ try{ return localStorage.getItem("apayaye.voce") || ""; }catch(e){ return ""; } }
function rateSalvato(){ try{ var r = parseFloat(localStorage.getItem("apayaye.rate")); return (isFinite(r) && r > 0) ? r : 0.98; }catch(e){ return 0.98; } }
function vocePreferita(){
  var vs = (window.speechSynthesis && speechSynthesis.getVoices()) || [];
  var it = vs.filter(function(v){ return /^it/i.test(v.lang || ""); });
  if(!it.length) return null;
  var scelta = voceSalvata();
  if(scelta){ var m = it.filter(function(v){ return v.name === scelta; }); if(m.length) return m[0]; }
  // Punteggio: piu' alto = voce piu' naturale. Le "compact" di iPhone suonano meccaniche.
  function punti(v){
    var n = (v.name || "").toLowerCase(), p = 0;
    if(/siri/.test(n)) p += 6;
    if(/(enhanced|premium|neural|migliorat|eloquen)/.test(n)) p += 5;
    if(/(alice|federica|luca|emma|giovanni)/.test(n)) p += 2;
    if(/compact/.test(n)) p -= 5;
    if(v.localService === false) p += 1;   // voci di rete, spesso migliori
    return p;
  }
  it.sort(function(a, b){ return punti(b) - punti(a); });
  return it[0];
}
/* pronuncia: come la voce DEVE leggere certi nomi (a schermo restano come sono).
   L'accento (ò ì à...) dice alla voce dove battere la sillaba. */
var PRON = {
  "Palagonia": "Palagònia"
};
function applicaPron(t){
  Object.keys(PRON).forEach(function(k){
    try{ t = t.replace(new RegExp("\\b" + k + "\\b", "gi"), PRON[k]); }catch(e){}
  });
  return t;
}
function narrazione(l){
  var st = l.storia ? (" " + l.storia) : "";
  var c = (l.curiosita && l.curiosita.length) ? (" Lo sapevi? " + l.curiosita.join(" ")) : "";
  return "Ciao! Sono " + l.nome + ", il personaggio di " + l.dove + ". " + l.frase + " " + l.blurb + st + " " + l.fatto + c;
}
function segnaAudio(on){ var b=$("b-audio"); if(b) b.textContent = on ? "⏸ Ferma" : "🔊 Ascolta"; }
function parla(l){
  if(!("speechSynthesis" in window)){ toast("La voce non è disponibile su questo telefono."); return; }
  // Secondo tocco: ferma la lettura (pulsante che fa anche da stop).
  if(speechSynthesis.speaking || speechSynthesis.pending){ speechSynthesis.cancel(); segnaAudio(false); return; }
  try{
    speechSynthesis.cancel();
    var u = new SpeechSynthesisUtterance(applicaPron(narrazione(l)));
    u.lang = "it-IT";
    var v = vocePreferita(); if(v) u.voice = v;
    u.rate = rateSalvato();
    u.pitch = (l.voce && l.voce.pitch) || 1;
    u.onstart = function(){ segnaAudio(true); };
    u.onend = function(){ segnaAudio(false); };
    u.onerror = function(){ segnaAudio(false); };
    speechSynthesis.speak(u);
    // iPhone a volte parte "in pausa": lo si sblocca subito.
    try{ speechSynthesis.resume(); }catch(e){}
  }catch(e){ toast("Non riesco a far partire la voce."); segnaAudio(false); }
}
function popolaVoci(){
  var sel = $("sel-voce"); if(!sel) return;
  var vs = (window.speechSynthesis && speechSynthesis.getVoices()) || [];
  var it = vs.filter(function(v){ return /^it/i.test(v.lang || ""); });
  var scelta = voceSalvata();
  sel.innerHTML = '<option value="">Automatica (la migliore)</option>' + it.map(function(v){
    var nome = (v.name || "").replace(/</g,"").replace(/>/g,"");
    return '<option value="'+nome.replace(/"/g,"&quot;")+'"'+(v.name===scelta?' selected':'')+'>'+nome+'</option>';
  }).join("");
}
if("speechSynthesis" in window){ try{ speechSynthesis.getVoices(); speechSynthesis.onvoiceschanged = function(){ speechSynthesis.getVoices(); popolaVoci(); }; }catch(e){} }
var bAudio = $("b-audio");
if(bAudio){ bAudio.addEventListener("click", function(){ if(corrente) parla(corrente); }); }
/* pannello: scegli la voce e la velocità (restano salvate) */
(function(){
  var ing = $("b-voce-opz"), pan = $("voce-opz"), sel = $("sel-voce"), velBox = $("vel");
  if(ing && pan){ ing.addEventListener("click", function(){ pan.classList.toggle("on"); popolaVoci(); }); }
  function anteprima(){ if(!corrente) return; try{ speechSynthesis.cancel(); }catch(e){} setTimeout(function(){ parla(corrente); }, 70); }
  if(sel){ sel.addEventListener("change", function(){ try{ localStorage.setItem("apayaye.voce", sel.value); }catch(e){} anteprima(); }); }
  if(velBox){
    function segna(){ var r = rateSalvato(); Array.prototype.forEach.call(velBox.querySelectorAll("button"), function(b){ b.classList.toggle("on", Math.abs(parseFloat(b.getAttribute("data-r")) - r) < 0.02); }); }
    Array.prototype.forEach.call(velBox.querySelectorAll("button"), function(b){
      b.addEventListener("click", function(){ try{ localStorage.setItem("apayaye.rate", b.getAttribute("data-r")); }catch(e){} segna(); anteprima(); });
    });
    segna();
  }
  popolaVoci();
})();

/* ---------- cattura ---------- */
function cattura(l, metodo){
  if(catturati[l.id]) return;
  catturati[l.id] = { il: Date.now(), come: metodo };
  salva(); render();
  if(corrente === l){ aggiornaScheda(); creaEl.classList.remove("pop"); void creaEl.offsetWidth; creaEl.classList.add("pop"); }
  confetti(l);
  toast("Hai catturato " + l.nome + "! 🎉");
  var n = Object.keys(catturati).length;
  if(n >= LUOGHI.length){
    setTimeout(function(){ toast("🏆 Album completo! Sei un vero Esploratore Apayaye!"); confetti(l); }, 1400);
  }
}

/* ---------- "sei qui": posizione reale sulla mappa ---------- */
var tuMarker=null, tuCircle=null;
function piazzaTu(){
  if(!posizione || typeof map === "undefined" || !map) return;
  var ll=[posizione.lat, posizione.lng];
  var rag=Math.max(12, Math.min(posizione.acc||40, 140));
  if(!tuMarker){
    tuMarker = L.marker(ll, { interactive:false, zIndexOffset:1000,
      icon:L.divIcon({ className:"tu-ico", iconSize:[16,16], iconAnchor:[8,8],
        html:'<span class="ring"></span><span class="core"></span><span class="lab">Tu</span>' }) }).addTo(map);
    tuCircle = L.circle(ll, { radius:rag, color:"#1d7ea6", weight:1, opacity:.5, fillColor:"#2f9ec4", fillOpacity:.12 }).addTo(map);
  } else {
    tuMarker.setLatLng(ll); tuCircle.setLatLng(ll).setRadius(rag);
  }
}

/* ---------- GPS ---------- */
function avviaGps(){
  if(!("geolocation" in navigator)){ toast("Questo telefono non dà la posizione."); return; }
  $("gps-txt").textContent = "Cerco la posizione…";
  navigator.geolocation.watchPosition(function(p){
    posizione = { lat:p.coords.latitude, lng:p.coords.longitude, acc:p.coords.accuracy };
    gpsOn = true;
    $("gps").classList.add("on");
    $("gps-txt").textContent = "Posizione attiva (±" + Math.round(posizione.acc) + " m)";
    render(); aggiornaScheda(); piazzaTu();
  }, function(err){
    $("gps").classList.remove("on");
    $("gps-txt").textContent = err.code === 1 ? "Permesso posizione negato" : "Posizione non disponibile";
  }, { enableHighAccuracy:true, maximumAge:5000, timeout:20000 });
}
$("b-gps").addEventListener("click", avviaGps);

/* ---------- modalità prova ---------- */
$("b-test").addEventListener("click", function(){
  testMode = !testMode;
  this.textContent = "🧪 Modalità prova: " + (testMode ? "on" : "off");
  this.setAttribute("aria-pressed", testMode ? "true" : "false");
  toast(testMode ? "Modalità prova: puoi catturare da qui." : "Modalità prova spenta.");
  render(); aggiornaScheda();
});

/* ---------- scanner QR ---------- */
var scannerEl = $("scanner"), video = $("video"), scanMsg = $("scan-msg");
var stream = null, rafId = null, canvasScan = document.createElement("canvas"), ctxScan = canvasScan.getContext("2d", { willReadFrequently:true });

function apriScanner(){
  if(typeof jsQR !== "function"){ toast("Lettore QR non disponibile."); return; }
  if(!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia){ toast("La fotocamera non è disponibile qui."); return; }
  scannerEl.classList.add("on"); scanMsg.textContent = "Punta la fotocamera sul codice…";
  navigator.mediaDevices.getUserMedia({ video:{ facingMode:"environment" }, audio:false })
    .then(function(s){
      stream = s; video.srcObject = s; video.setAttribute("playsinline", true);
      return video.play();
    })
    .then(function(){ rafId = requestAnimationFrame(loopScan); })
    .catch(function(err){
      scanMsg.textContent = err && err.name === "NotAllowedError" ? "Permesso fotocamera negato." : "Non riesco ad aprire la fotocamera.";
    });
}
function chiudiScanner(){
  scannerEl.classList.remove("on");
  if(rafId){ cancelAnimationFrame(rafId); rafId = null; }
  if(stream){ stream.getTracks().forEach(function(t){ t.stop(); }); stream = null; }
  video.srcObject = null;
}
$("scan-x").addEventListener("click", chiudiScanner);

function loopScan(){
  if(video.readyState === video.HAVE_ENOUGH_DATA){
    var w = video.videoWidth, h = video.videoHeight;
    if(w && h){
      canvasScan.width = w; canvasScan.height = h;
      ctxScan.drawImage(video, 0, 0, w, h);
      var img = ctxScan.getImageData(0, 0, w, h);
      var code = jsQR(img.data, w, h, { inversionAttempts:"dontInvert" });
      if(code && code.data){ gestisciQR(code.data); return; }
    }
  }
  rafId = requestAnimationFrame(loopScan);
}
function gestisciQR(testo){
  var parti = String(testo).split(":"); // APAYAYE : id : codice
  if(parti[0] !== "APAYAYE" || parti.length < 2){
    scanMsg.textContent = "Questo non è un QR del gioco."; rafId = requestAnimationFrame(loopScan); return;
  }
  var l = null;
  for(var i=0;i<LUOGHI.length;i++){ if(LUOGHI[i].id === parti[1] && LUOGHI[i].qr === testo){ l = LUOGHI[i]; break; } }
  if(!l){
    scanMsg.textContent = "Codice non riconosciuto."; rafId = requestAnimationFrame(loopScan); return;
  }
  chiudiScanner();
  if(catturati[l.id]){ apri(l); toast(l.nome + " è già nel tuo album."); return; }
  cattura(l, "qr"); apri(l);
}
$("b-scan").addEventListener("click", apriScanner);

/* ---------- confetti + toast ---------- */
function confetti(l){
  if(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  var box = document.createElement("div"); box.className = "conf";
  var cols = [l.col, l.col2, "#e8a83a", "#d2603a", "#3e8f3f", "#fff"];
  for(var i=0;i<30;i++){
    var p = document.createElement("i");
    p.style.left = (Math.random()*100)+"%";
    p.style.background = cols[i % cols.length];
    p.style.animationDuration = (1.1 + Math.random()*0.9)+"s";
    p.style.animationDelay = (Math.random()*0.2)+"s";
    p.style.transform = "translateY(-10px) rotate("+(Math.random()*180)+"deg)";
    box.appendChild(p);
  }
  document.body.appendChild(box);
  setTimeout(function(){ box.remove(); }, 2200);
}
var toastTimer = null;
function toast(msg){
  var t = $("toast"); t.textContent = msg; t.classList.add("on");
  if(toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(function(){ t.classList.remove("on"); }, 2600);
}

/* ---------- reset ---------- */
$("reset").addEventListener("click", function(){
  catturati = {}; salva(); render(); aggiornaScheda();
  toast("Album svuotato.");
});

/* ---------- avvio ---------- */
render();
/* Attiva la posizione da sola: se il permesso è già dato, il puntino "Tu" compare subito. */
try{ avviaGps(); }catch(e){}

/* Niente cache del gioco: si carica sempre la versione fresca. Se un vecchio
   service worker era rimasto (e teneva bloccata una copia), lo togliamo. */
if("serviceWorker" in navigator){
  try{
    navigator.serviceWorker.getRegistrations().then(function(rs){
      rs.forEach(function(r){ r.unregister(); });
    }).catch(function(){});
  }catch(e){}
}

/* ---------- versione e aggiornamento ---------- */
var APP_VERSION = "3.0";
(function(){
  try{ var v=$("ver"); if(v) v.textContent = "v"+APP_VERSION; }catch(e){}
  function ricarica(){
    // paracadute anti-anello: non ricaricare due volte entro 30 secondi
    try{ var k="apayaye.ricaricato", last=+(sessionStorage.getItem(k)||0);
      if(Date.now()-last < 30000) return;
      sessionStorage.setItem(k, String(Date.now()));
    }catch(e){}
    location.replace(location.pathname + "?r=" + Date.now());
  }
  var b=$("aggiorna");
  if(b){ b.addEventListener("click", ricarica); }   // aggiornamento a mano
  function controlla(){
    try{
      fetch("app.js?c="+Date.now(), { cache:"no-store" }).then(function(r){ return r.text(); }).then(function(t){
        var m = t.match(/APP_VERSION\s*=\s*"([^"]+)"/);
        if(m && m[1] !== APP_VERSION){
          var bb=$("aggiorna");
          if(bb){ bb.textContent = "\u21bb Aggiorna a v"+m[1]; bb.className = "aggbtn nuovo"; }
          ricarica();                                 // aggiornamento automatico
        }
      }).catch(function(){});
    }catch(e){}
  }
  controlla(); setInterval(controlla, 120000);
  document.addEventListener("visibilitychange", function(){ if(!document.hidden) controlla(); });
})();
