// Só arquivos públicos da interface entram no cache. Respostas da API nunca são armazenadas.
const CACHE='alberio-interface-v3';
const ASSETS=['/','/static/styles.css','/static/icons-and-card.css','/static/boletim.css','/static/app.js','/static/api.js','/static/forms.js','/static/icons.js','/static/boletim.js'];
self.addEventListener('install',event=>{
  event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(ASSETS)));
});
self.addEventListener('activate',event=>{
  event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key.startsWith('alberio-interface-')&&key!==CACHE).map(key=>caches.delete(key)))).then(()=>self.clients.claim()));
});
self.addEventListener('fetch',event=>{
  const url=new URL(event.request.url);
  if(event.request.method!=='GET' || url.origin!==self.location.origin || !ASSETS.includes(url.pathname))return;
  event.respondWith(fetch(event.request).then(response=>{
    if(response.ok){const clone=response.clone();caches.open(CACHE).then(cache=>cache.put(event.request,clone));}
    return response;
  }).catch(()=>caches.match(event.request)));
});
