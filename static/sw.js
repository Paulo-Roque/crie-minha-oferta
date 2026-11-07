// ComparaOferta PWA - Service Worker V29
const CACHE = 'compara-oferta-v29';
const CORE = ['/', '/static/manifest.json', '/static/icon-192.png', '/static/icon-512.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).then(()=>self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  // Não cacheia API do ML (sempre fresca) nem /api/offer
  if(url.hostname.includes('mercadolibre.com') || url.hostname.includes('mercadolivre.com') || url.pathname.startsWith('/api/') || url.pathname.startsWith('/go/')){
    return;
  }
  e.respondWith(
    fetch(e.request).then(res => {
      const copy = res.clone();
      caches.open(CACHE).then(c=>c.put(e.request, copy));
      return res;
    }).catch(()=>caches.match(e.request).then(m=>m || caches.match('/')))
  );
});
