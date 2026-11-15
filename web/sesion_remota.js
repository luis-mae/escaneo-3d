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
  // Los enlaces <a download> no adjuntan Authorization. En modo remoto,
  // obtener el archivo con fetch autenticado y descargarlo como Blob local.
  document.addEventListener("click", async evento => {
    const enlace = evento.target.closest?.("a[href]");
    if (!enlace || !obtenerToken()) return;
    const destino = new URL(enlace.href, location.href);
    if (destino.origin !== location.origin ||
        !/^\/api\/proyectos\/[a-f0-9]{32}\//.test(destino.pathname)) return;
    evento.preventDefault();
    const anterior = enlace.textContent;
    enlace.textContent = "Descargando…";
    try {
      const respuesta = await window.fetch(destino.href, {cache: "no-store"});
      if (!respuesta.ok) throw new Error("HTTP " + respuesta.status);
      const blob = await respuesta.blob();
      const objeto = URL.createObjectURL(blob);
      const descarga = document.createElement("a");
      descarga.href = objeto;
      const nombreRuta = destino.pathname.split("/").pop() || "escaneo3d";
      const disposicion = respuesta.headers.get("Content-Disposition") || "";
      const nombreCabecera = /filename\*=UTF-8''([^;]+)/i.exec(disposicion);
      descarga.download = nombreCabecera ? decodeURIComponent(nombreCabecera[1]) : nombreRuta;
      document.body.append(descarga);
      descarga.click();
      descarga.remove();
      setTimeout(() => URL.revokeObjectURL(objeto), 60000);
    } catch (error) {
      alert("No se pudo descargar el archivo: " + error.message);
    } finally {
      enlace.textContent = anterior;
    }
  });
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
    const formulario = document.getElementById("formulario-acceso");
    const usuario = document.getElementById("usuario-remoto");
    const claveAcceso = document.getElementById("clave-remota");
    const estado = document.getElementById("estado-acceso");
    const boton = document.getElementById("guardar-token");
    const salir = document.getElementById("salir-remoto");
    if (!panel || !formulario) return;
    const refrescar = () => {
      const activa = window.escaneo3dSesion.activa();
      estado.textContent = activa ? "Sesión activa en esta pestaña." : "Iniciá sesión para usar el servidor remoto.";
      salir.disabled = !activa;
    };
    formulario.addEventListener("submit", async evento => {
      evento.preventDefault();
      boton.disabled = true;
      estado.textContent = "Verificando credenciales…";
      try {
        const respuesta = await fetchOriginal("/api/sesion", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({usuario: usuario.value.trim(), clave: claveAcceso.value}),
          cache: "no-store"
        });
        if (!respuesta.ok) {
          if (respuesta.status === 429) throw new Error("Demasiados intentos. Probá más tarde.");
          throw new Error("No se pudo iniciar sesión (HTTP " + respuesta.status + ")");
        }
        const datos = await respuesta.json();
        window.escaneo3dSesion.guardar(datos.token);
        claveAcceso.value = "";
        location.reload();
      } catch (error) {
        claveAcceso.value = "";
        estado.textContent = error.message;
      } finally { boton.disabled = false; }
    });
    salir.addEventListener("click", () => {
      window.escaneo3dSesion.salir();
      claveAcceso.value = "";
      location.reload();
    });
    fetchOriginal("/api/salud", {cache:"no-store"}).then(r => r.json()).then(datos => {
      panel.hidden = datos.modo !== "remoto_autenticado";
      refrescar();
    }).catch(() => {});
  });
})();
