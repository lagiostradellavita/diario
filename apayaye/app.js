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

/* ---------- percorso tratteggiato sulla mappa ---------- */
(function(){
  var ord = LUOGHI.slice().sort(function(a,b){ return a.num-b.num; });
  var d = ord.map(function(l,i){ return (i?"L":"M")+l.map.x+" "+l.map.y; }).join(" ");
  $("trail").setAttribute("d", d);
})();

/* ---------- marker sulla mappa ---------- */
LUOGHI.forEach(function(l){
  var b = document.createElement("button");
  b.className = "marker"; b.style.left = l.map.x+"%"; b.style.top = l.map.y+"%";
  b.setAttribute("aria-label", l.dove);
  b.innerHTML = '<span class="pin" style="background:'+l.col+'"><span>'+l.emblema+'</span>'+
    '<span class="num">'+l.num+'</span></span>' +
    '<span class="lab">'+l.dove.split("–")[0].split(" di ")[0].trim()+'</span>';
  b.addEventListener("click", function(){ apri(l); });
  l._el = b;
  mappa.appendChild(b);
});

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
    l._el.classList.toggle("catturato", preso);
    l._el.classList.toggle("vicino", !preso && entroRaggio(l));
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
  $("sheet-blurb").textContent = l.blurb;
  $("sheet-fatto").textContent = l.fatto;
  creaEl.innerHTML = artLuogo(l);
  aggiornaScheda();
  velo.classList.add("on"); sheet.classList.add("on");
}
function chiudi(){ velo.classList.remove("on"); sheet.classList.remove("on"); corrente = null; }
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

/* ---------- GPS ---------- */
$("b-gps").addEventListener("click", function(){
  if(!("geolocation" in navigator)){ toast("Questo telefono non dà la posizione."); return; }
  $("gps-txt").textContent = "Cerco la posizione…";
  navigator.geolocation.watchPosition(function(p){
    posizione = { lat:p.coords.latitude, lng:p.coords.longitude, acc:p.coords.accuracy };
    gpsOn = true;
    $("gps").classList.add("on");
    $("gps-txt").textContent = "Posizione attiva (±" + Math.round(posizione.acc) + " m)";
    render(); aggiornaScheda();
  }, function(err){
    $("gps").classList.remove("on");
    $("gps-txt").textContent = err.code === 1 ? "Permesso posizione negato" : "Posizione non disponibile";
  }, { enableHighAccuracy:true, maximumAge:5000, timeout:20000 });
});

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

/* PWA: installa l'app sul telefono (home screen) */
if("serviceWorker" in navigator){
  window.addEventListener("load", function(){
    navigator.serviceWorker.register("sw.js").catch(function(){ /* niente: l'app gira comunque */ });
  });
}
