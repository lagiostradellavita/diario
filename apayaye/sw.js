/* Service worker minimo: mette in cache il "guscio" dell'app cosi' si apre
   anche con poca rete. Alza CACHE a ogni modifica per servire i file nuovi. */
var CACHE = "apayaye-v3";
var GUSCIO = [
  ".", "index.html", "app.js", "luoghi.js", "manifest.json", "icon.svg"
];

self.addEventListener("install", function(e){
  e.waitUntil(caches.open(CACHE).then(function(c){ return c.addAll(GUSCIO); }).then(function(){ return self.skipWaiting(); }));
});
self.addEventListener("activate", function(e){
  e.waitUntil(caches.keys().then(function(ks){
    return Promise.all(ks.map(function(k){ if(k !== CACHE) return caches.delete(k); }));
  }).then(function(){ return self.clients.claim(); }));
});
self.addEventListener("fetch", function(e){
  var req = e.request;
  if(req.method !== "GET") return;
  var url = new URL(req.url);
  if(url.origin !== self.location.origin) return; // lascia passare font e librerie
  e.respondWith(
    caches.match(req).then(function(hit){
      return hit || fetch(req).then(function(res){
        var copia = res.clone();
        caches.open(CACHE).then(function(c){ c.put(req, copia); });
        return res;
      }).catch(function(){ return caches.match("index.html"); });
    })
  );
});
