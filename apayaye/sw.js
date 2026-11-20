/* INTERRUTTORE. Questo service worker non mette piu' niente in cache: al primo
   avvio cancella le vecchie cache, si disattiva (unregister) e ricarica la
   pagina, cosi' il gioco torna a caricarsi sempre fresco dalla rete. Serviva a
   togliere le copie vecchie rimaste bloccate sui telefoni. */
self.addEventListener("install", function(e){ self.skipWaiting(); });
self.addEventListener("activate", function(e){
  e.waitUntil(
    caches.keys().then(function(ks){
      return Promise.all(ks.map(function(k){ return caches.delete(k); }));
    }).then(function(){
      return self.registration.unregister();
    }).then(function(){
      return self.clients.matchAll({ type: "window" });
    }).then(function(cs){
      cs.forEach(function(c){ try{ c.navigate(c.url); }catch(e){} });
    }).catch(function(){})
  );
});
