/* Service worker del gioco. "Stale-while-revalidate": apre subito dalla cache
   (va anche con poca rete), ma in sottofondo riscarica sempre la versione nuova
   e aggiorna la cache, cosi' alla riapertura dopo si vede l'ultima. Alzare CACHE
   forza invece un aggiornamento immediato su tutti i telefoni. */
var CACHE = "apayaye-v5";
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
      var fresco = fetch(req).then(function(res){
        if(res && res.status === 200 && res.type === "basic"){
          var copia = res.clone();
          caches.open(CACHE).then(function(c){ c.put(req, copia); });
        }
        return res;
      }).catch(function(){ return hit || caches.match("index.html"); });
      return hit || fresco;
    })
  );
});
