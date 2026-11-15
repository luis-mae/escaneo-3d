"use strict";
// Sesión temporal: el token lo entrega un proveedor de identidad externo.
// Nunca se guarda en localStorage ni IndexedDB; se borra al cerrar la pestaña.
(() => {
  const clave = "escaneo3d_token_sesion";
  const fetchOriginal = window.fetch.bind(window);
  const obtenerToken = () => {
    const token = sessionStorage.getItem(clave) || "";
    if (!token) return "";
    try {
      const cuerpo = token.split(".")[1];
      const claims = JSON.parse(atob(cuerpo.replace(/-/g, "+").replace(/_/g, "/")));
      if (!Number.isInteger(claims.exp) || claims.exp <= Math.floor(Date.now() / 1000)) {
        sessionStorage.removeItem(clave);
        return "";
      }
      return token;
    } catch (_) {
      sessionStorage.removeItem(clave);
      return "";
    }
  };
  window.fetch = (entrada, opciones = {}) => {
    const url = typeof entrada === "string" ? entrada : entrada instanceof URL ? entrada.href : entrada.url;
    const destino = new URL(url, location.href);
    if (destino.origin !== location.origin || !destino.pathname.startsWith("/api/") ||
        destino.pathname === "/api/salud") return fetchOriginal(entrada, opciones);
    const token = obtenerToken();
    if (!token) return fetchOriginal(entrada, opciones);
    const cabeceras = new Headers(entrada instanceof Request ? entrada.headers : undefined);
    new Headers(opciones.headers || {}).forEach((valor, nombre) => cabeceras.set(nombre, valor));
    cabeceras.set("Authorization", "Bearer " + token);
    return fetchOriginal(entrada, {...opciones, headers: cabeceras});
  };
  window.escaneo3dSesion = {
    activa: () => Boolean(obtenerToken()),
    guardar: token => {
      if (!/^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(token) || token.length > 8192)
        throw new Error("Token JWT inválido");
      sessionStorage.setItem(clave, token);
      if (!obtenerToken()) throw new Error("Credencial vencida o mal formada");
    },
    salir: () => sessionStorage.removeItem(clave)
  };
  document.addEventListener("DOMContentLoaded", () => {
    const panel = document.getElementById("acceso-remoto");
    const campo = document.getElementById("token-remoto");
    const estado = document.getElementById("estado-acceso");
    const boton = document.getElementById("guardar-token");
    const salir = document.getElementById("salir-remoto");
    if (!panel) return;
    const refrescar = () => {
      const activa = window.escaneo3dSesion.activa();
      estado.textContent = activa ? "Credencial temporal cargada en esta pestaña." : "Sin credencial de acceso.";
      salir.disabled = !activa;
    };
    boton.addEventListener("click", () => {
      try {
        window.escaneo3dSesion.guardar(campo.value.trim());
        campo.value = "";
        refrescar();
        location.reload();
      } catch (error) { estado.textContent = error.message; }
    });
    salir.addEventListener("click", () => {
      window.escaneo3dSesion.salir();
      campo.value = "";
      location.reload();
    });
    fetchOriginal("/api/salud", {cache:"no-store"}).then(r => r.json()).then(datos => {
      panel.hidden = datos.modo !== "remoto_autenticado";
      refrescar();
    }).catch(() => {});
  });
})();
