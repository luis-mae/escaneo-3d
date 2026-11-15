"use strict";
const CACHE = "escaneo3d-shell-v12";
const ARCHIVOS = ["./", "./index.html", "./styles.css", "./app.js", "./sesion_remota.js", "./visor.js", "./stl_calibrado.js", "./mediciones_malla.js", "./manifest.webmanifest", "./icon.svg", "./privacidad.html", "./ayuda.html"];
const RUTAS = new Set(ARCHIVOS.map(path => new URL(path, self.registration.scope).pathname));
self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ARCHIVOS)));
  self.skipWaiting();
});
self.addEventListener("activate", event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(key => key.startsWith("escaneo3d-shell-") && key !== CACHE)
      .map(key => caches.delete(key))
  )));
  self.clients.claim();
});
self.addEventListener("fetch", event => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin || url.pathname.startsWith("/api/")) return;
  // No devolver HTML ante fallas de JS/CSS/OBJ: rompe la aplicación y confunde las descargas.
  if (!RUTAS.has(url.pathname)) return;
  event.respondWith((async () => {
    try {
      const respuesta = await fetch(event.request);
      if (respuesta.ok && respuesta.type === "basic") {
        const copia = respuesta.clone();
        event.waitUntil(caches.open(CACHE).then(cache => cache.put(event.request, copia)));
      }
      return respuesta;
    } catch (error) {
      const cache = await caches.open(CACHE);
      const guardado = await cache.match(event.request);
      if (guardado) return guardado;
      if (event.request.mode === "navigate") {
        const inicio = await cache.match("./index.html");
        if (inicio) return inicio;
      }
      throw error;
    }
  })());
});
