const CACHE = 'gnews-v26';
const ASSETS = [
  '/News.html',
  '/manifest.json',
  '/icon.svg',
  '/apple-touch-icon.png',
  '/icon-192.png',
  '/icon-512.png'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS).catch(() => {})));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  // Never cache proxy requests — always fetch live from the local server
  if (e.request.url.includes('/proxy?')) return;
  e.respondWith(
    caches.match(e.request)
      .then(r => r || fetch(e.request).catch(() => caches.match('/News.html')))
  );
});
