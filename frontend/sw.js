// Versión del caché estático; cambiarla fuerza la actualización de recursos.
const CACHE_NAME = 'securebank-v1';
// Recursos mínimos necesarios para abrir la interfaz sin red.
const ASSETS = [
  '/',
  '/static/index.html',
  '/static/css/style.css',
  '/static/js/app.js',
  '/static/manifest.json'
];

self.addEventListener('install', (event) => {
  // Precarga la carcasa de la aplicación al instalar el Service Worker.
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(ASSETS))
  );
});

self.addEventListener('fetch', (event) => {
  // Prioriza caché y consulta la red solo cuando el recurso no está guardado.
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        return response || fetch(event.request);
      })
  );
});

