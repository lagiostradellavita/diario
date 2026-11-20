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
    st.textContent=".extra{margin:12px 0 2px;font-size:.92rem;line-height:1.45;color:#5a4a2a}.extra b{display:block;color:#8a5a2a;margin-bottom:4px}.extra ul{margin:0;padding-left:20px}.extra li{margin:4px 0}";
    document.head.appendChild(st);
    ex=document.createElement("div"); ex.id="sheet-extra"; ex.className="extra";
    var fb=$("sheet-fatto").parentNode;
    fb.parentNode.insertBefore(ex, fb.nextSibling);
  }
  if(l.curiosita && l.curiosita.length){
    ex.innerHTML='<b>Lo sapevi?</b><ul>'+l.curiosita.map(function(c){return '<li>'+c+'</li>';}).join('')+'</ul>';
    ex.style.display="";
  } else { ex.style.display="none"; }
}
function chiudi(){ velo.classList.remove("on"); sheet.classList.remove("on"); corrente = null; if("speechSynthesis" in window) speechSynthesis.cancel(); }
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
function vocePreferita(){
  var vs = (window.speechSynthesis && speechSynthesis.getVoices()) || [];
  var it = vs.filter(function(v){ return /^it/i.test(v.lang || ""); });
  if(!it.length) return null;
  var belle = it.filter(function(v){ return /(siri|alice|federica|luca|enhanced|premium|neural)/i.test(v.name || ""); });
  return belle[0] || it[0];
}
function narrazione(l){
  var c = (l.curiosita && l.curiosita.length) ? (" Lo sapevi? " + l.curiosita.join(" ")) : "";
  return "Ciao! Sono " + l.nome + ", il personaggio di " + l.dove + ". " + l.frase + " " + l.blurb + " " + l.fatto + c;
}
function parla(l){
  if(!("speechSynthesis" in window)){ toast("La voce non è disponibile su questo telefono."); return; }
  try{
    speechSynthesis.cancel();
    var u = new SpeechSynthesisUtterance(narrazione(l));
    u.lang = "it-IT";
    var v = vocePreferita(); if(v) u.voice = v;
    u.rate = (l.voce && l.voce.rate) || 0.98;
    u.pitch = (l.voce && l.voce.pitch) || 1;
    speechSynthesis.speak(u);
  }catch(e){ toast("Non riesco a far partire la voce."); }
}
if("speechSynthesis" in window){ try{ speechSynthesis.getVoices(); speechSynthesis.onvoiceschanged = function(){ speechSynthesis.getVoices(); }; }catch(e){} }
var bAudio = $("b-audio");
if(bAudio){ bAudio.addEventListener("click", function(){ if(corrente) parla(corrente); }); }

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

/* ---------- "sei qui": proietta la posizione sulla mappa illustrata ---------- */
/* Interpolazione pesata sui luoghi (1/distanza^2): se sei SU un luogo, il puntino
   ci cade esatto; tra i luoghi, si posiziona in mezzo in modo naturale. */
function geoAMappa(lat,lng){
  var sx=0, sy=0, sw=0, trovato=false;
  LUOGHI.forEach(function(l){
    var d=distanza(lat,lng,l.coord[0],l.coord[1]);
    var w=1/Math.pow(d<1?1:d,2);
    sx+=w*l.map.x; sy+=w*l.map.y; sw+=w; trovato=true;
  });
  if(!trovato || !sw) return null;
  return { x:Math.max(2,Math.min(98,sx/sw)), y:Math.max(2,Math.min(99,sy/sw)) };
}
var tuEl=null;
function piazzaTu(){
  if(!posizione) return;
  var pt=geoAMappa(posizione.lat, posizione.lng); if(!pt) return;
  if(!tuEl){
    var st=document.createElement("style");
    st.textContent="@keyframes tupulse{0%{transform:translate(-50%,-50%) scale(.5);opacity:.75}70%{transform:translate(-50%,-50%) scale(2.4);opacity:0}100%{opacity:0}}.tu-dot{position:absolute;z-index:6;transform:translate(-50%,-50%);pointer-events:none}.tu-dot .ring{position:absolute;left:0;top:0;width:16px;height:16px;border-radius:50%;background:#1d7ea6;transform:translate(-50%,-50%);animation:tupulse 1.8s ease-out infinite}.tu-dot .core{position:absolute;left:0;top:0;width:14px;height:14px;border-radius:50%;background:#2f9ec4;border:3px solid #fff;transform:translate(-50%,-50%);box-shadow:0 2px 6px rgba(0,0,0,.4)}.tu-dot .lab{position:absolute;left:0;top:11px;transform:translateX(-50%);background:#1d7ea6;color:#fff;font-family:var(--display),system-ui;font-weight:700;font-size:.6rem;padding:1px 7px;border-radius:999px;white-space:nowrap}";
    document.head.appendChild(st);
    tuEl=document.createElement("div"); tuEl.className="tu-dot";
    tuEl.innerHTML='<span class="ring"></span><span class="core"></span><span class="lab">Tu</span>';
    mappa.appendChild(tuEl);
  }
  tuEl.style.left=pt.x+"%"; tuEl.style.top=pt.y+"%"; tuEl.style.display="";
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
