// Jaikalki HRMS service worker.
//
// Kept deliberately small: it makes the web app installable in every
// browser that asks for a service worker (e.g. Samsung Internet) and
// shows an offline page instead of the browser's error when there's no
// network. App files are NOT cached here — Flutter's file names carry no
// content hash, so caching them would serve stale code after a deploy;
// the HTTP cache (ETag revalidation, see DEPLOY.md) handles them.
const CACHE = 'jk-offline-v1';
const OFFLINE_URL = 'offline.html';
const OFFLINE_ASSETS = [OFFLINE_URL, 'icons/Icon-192.png'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => cache.addAll(OFFLINE_ASSETS))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)),
      ))
      .then(() => self.clients.claim()),
  );
});

const isOfflineAsset = (url) =>
  OFFLINE_ASSETS.some((a) => new URL(a, self.registration.scope).href === url);

self.addEventListener('fetch', (event) => {
  // The offline page's own files: network first, cached copy offline.
  if (isOfflineAsset(event.request.url)) {
    event.respondWith(
      fetch(event.request).catch(() => caches.match(event.request)),
    );
    return;
  }
  // Only page loads get the offline fallback; everything else (app code,
  // API calls) goes straight to the network as if there were no worker.
  if (event.request.mode !== 'navigate') return;
  event.respondWith(
    // Always revalidate the page with the server (a cheap 304 when
    // unchanged) so being offline reliably shows the offline page rather
    // than a half-loaded copy from the browser cache.
    fetch(event.request, { cache: 'no-cache' }).catch(() =>
      caches.open(CACHE).then((cache) => cache.match(OFFLINE_URL)),
    ),
  );
});
