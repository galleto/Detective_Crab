// Versión del caché estático; cambiarla fuerza la actualización de recursos.
const CACHE_NAME = 'detective-crab-v7';

// Recursos mínimos necesarios para abrir la interfaz sin red.
const ASSETS = [
  '/',
  '/index.html',
  '/css/style.css',
  '/js/app.js',
  '/manifest.json',
  '/Detective.png',
  '/icons/icon-192.png',
  '/icons/icon-512.png'
];

self.addEventListener('install', (event) => {
  // Precarga la carcasa de la aplicación al instalar el Service Worker.
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  // Limpia cachés de versiones anteriores para evitar servir archivos viejos.
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(key => key !== CACHE_NAME)
            .map(key => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  // Nunca cachear llamadas a la API: siempre deben ir a la red.
  if (event.request.url.includes('/api/')) {
    return;
  }

  // Para el resto: prioriza caché y consulta la red solo si no está guardado.
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});
