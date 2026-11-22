/* Service worker del gioco: "prima la rete" (network-first) per i file del gioco,
   cosi' il telefono mostra SEMPRE l'ultima versione e non resta sulla cache vecchia.
   Le mappe (OpenStreetMap) e le librerie da CDN sono di altri siti: non le tocca,
   le gestisce il browser. Se si e' offline, usa l'ultima copia salvata. */
var VER = "apayaye-gioco-v1";

self.addEventListener("install", function(e){ self.skipWaiting(); });

self.addEventListener("activate", function(e){
  e.waitUntil((async function(){
    var keys = await caches.keys();
    await Promise.all(keys.map(function(k){ return k === VER ? null : caches.delete(k); }));
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", function(e){
  var req = e.request;
  if (req.method !== "GET") return;
  var url;
  try { url = new URL(req.url); } catch(err){ return; }
  if (url.origin !== self.location.origin) return;   // solo i file di questo sito
  e.respondWith((async function(){
    try {
      var fresh = await fetch(req, { cache: "no-store" });   // sempre dalla rete
      try { var c = await caches.open(VER); c.put(req, fresh.clone()); } catch(err){}
      return fresh;
    } catch (err) {
      var cached = await caches.match(req);                  // offline: ultima copia
      if (cached) return cached;
      throw err;
    }
  })());
});
