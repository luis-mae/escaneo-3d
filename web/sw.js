"use strict";
const CACHE = "escaneo3d-shell-v7";
const ARCHIVOS = ["./", "./index.html", "./styles.css", "./app.js", "./visor.js", "./stl_calibrado.js", "./mediciones_malla.js", "./manifest.webmanifest", "./icon.svg", "./privacidad.html", "./ayuda.html"];
self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ARCHIVOS)));
  self.skipWaiting();
});
self.addEventListener("activate", event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key)))));
  self.clients.claim();
});
self.addEventListener("fetch", event => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET" || url.origin !== self.location.origin || url.pathname.includes("/api/")) return;
  event.respondWith(fetch(event.request).then(response => {
    if (response.ok) {
      const copia = response.clone();
      caches.open(CACHE).then(cache => cache.put(event.request, copia));
    }
    return response;
  }).catch(() => caches.match(event.request).then(cached => cached || caches.match("./index.html"))));
});
