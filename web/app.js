"use strict";
const MAX_FOTOS = 100;
const MAX_BYTES = 20 * 1024 * 1024;
const MAX_TOTAL = 500 * 1024 * 1024;
const MIN_FOTOS = 3;
const TIPOS = new Set(["image/jpeg", "image/png"]);
const nombre = document.getElementById("nombre");
const fotos = document.getElementById("fotos");
const denso = document.getElementById("denso");
const alphaMalla = document.getElementById("alpha-malla");
const zona = document.getElementById("zona");
const estado = document.getElementById("estado");
const lista = document.getElementById("lista");
const preparar = document.getElementById("preparar");
const limpiar = document.getElementById("limpiar");
const resultado = document.getElementById("resultado");
const resumen = document.getElementById("resumen");
const descargar = document.getElementById("descargar");
let seleccion = [];
let manifiesto = null;

function mensaje(texto, clase = "") {
  estado.textContent = texto;
  estado.className = clase;
}
function validar(archivos) {
  if (archivos.length < MIN_FOTOS || archivos.length > MAX_FOTOS) {
    return `Seleccioná entre ${MIN_FOTOS} y ${MAX_FOTOS} fotografías.`;
  }
  if (archivos.reduce((total, f) => total + f.size, 0) > MAX_TOTAL) return "Máximo 500 MB por proyecto.";
  const nombres = new Set();
  for (const archivo of archivos) {
    if (!["image/jpeg", "image/png"].includes(archivo.type)) return `COLMAP requiere JPG o PNG: ${archivo.name}`;
    if (archivo.size <= 0 || archivo.size > MAX_BYTES) return `Tamaño no admitido: ${archivo.name}`;
    const clave = archivo.name.toLocaleLowerCase();
    if (nombres.has(clave)) return `Hay nombres repetidos: ${archivo.name}`;
    nombres.add(clave);
  }
  return null;
}
function mostrar() {
  lista.replaceChildren();
  resultado.hidden = true;
  manifiesto = null;
  const error = validar(seleccion);
  seleccion.forEach((archivo, indice) => {
    const li = document.createElement("li");
    li.className = "foto-seleccionada";
    const detalle = document.createElement("span");
    detalle.textContent = archivo.name + " · " + (archivo.size / 1048576).toFixed(2) + " MB";
    const quitar = document.createElement("button");
    quitar.type = "button";
    quitar.className = "quitar-foto";
    quitar.textContent = "Quitar";
    quitar.setAttribute("aria-label", "Quitar " + archivo.name);
    quitar.addEventListener("click", () => {
      seleccion.splice(indice, 1);
      mostrar();
      actualizarEnviar();
    });
    li.append(detalle, quitar);
    lista.appendChild(li);
  });
  if (!seleccion.length) mensaje("Todavía no seleccionaste fotografías.");
  else if (error) mensaje(error, "error");
  else mensaje(`${seleccion.length} fotografías listas para preparar.`, "ok");
  preparar.disabled = Boolean(error) || !nombre.value.trim();
}
function recibir(archivos) {
  seleccion = Array.from(archivos);
  mostrar();
}
function agregarFotos(archivos) {
  const nuevas = Array.from(archivos);
  const combinadas = [...seleccion, ...nuevas];
  const nombres = new Set();
  for (const archivo of combinadas) {
    const clave = archivo.name.toLocaleLowerCase();
    if (nombres.has(clave)) {
      mensaje("Hay nombres repetidos. Renombrá una de las fotos antes de continuar.", "error");
      return;
    }
    nombres.add(clave);
  }
  seleccion = combinadas;
  mostrar();
}
fotos.addEventListener("change", () => recibir(fotos.files));
const camara = document.getElementById("camara");
document.getElementById("tomar-foto")?.addEventListener("click", () => camara?.click());
camara?.addEventListener("change", () => {
  if (camara.files?.length) agregarFotos(camara.files);
  camara.value = "";
});
nombre.addEventListener("input", mostrar);
for (const evento of ["dragenter", "dragover"]) {
  zona.addEventListener(evento, (e) => { e.preventDefault(); zona.classList.add("arrastre"); });
}
for (const evento of ["dragleave", "drop"]) {
  zona.addEventListener(evento, (e) => { e.preventDefault(); zona.classList.remove("arrastre"); });
}
zona.addEventListener("drop", (e) => recibir(e.dataTransfer.files));
limpiar.addEventListener("click", () => {
  seleccion = [];
  fotos.value = "";
  nombre.value = "";
  mostrar();
  nombre.focus();
});
preparar.addEventListener("click", () => {
  const error = validar(seleccion);
  if (error || !nombre.value.trim()) { mostrar(); return; }
  manifiesto = {
    version: 1, proyecto: nombre.value.trim(),
    creado_en: new Date().toISOString(),
    estado: "pendiente_de_procesamiento",
    imagenes: seleccion.map(f => ({nombre: f.name, bytes: f.size, tipo: f.type})),
    nota: "Las fotos no están incluidas ni fueron subidas a un servidor."
  };
  resumen.textContent = `${manifiesto.proyecto}: ${seleccion.length} fotos validadas. Procesamiento 3D pendiente.`;
  resultado.hidden = false;
});
descargar.addEventListener("click", () => {
  if (!manifiesto) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(manifiesto, null, 2)], {type:"application/json"}));
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = "proyecto_escaneo3d.json";
  enlace.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
mostrar();


const enviar = document.createElement("button");
enviar.type = "button";
enviar.textContent = "Iniciar reconstrucción 3D";
preparar.parentElement.appendChild(enviar);

const progreso = document.createElement("p");
progreso.setAttribute("role", "status");
progreso.setAttribute("aria-live", "polite");
const barraProgreso = document.createElement("progress");
barraProgreso.className = "progreso-indeterminado";
barraProgreso.max = 100;
barraProgreso.setAttribute("aria-label", "Procesamiento en curso");
barraProgreso.hidden = true;
enviar.after(barraProgreso);
barraProgreso.after(progreso);
const acciones = document.createElement("div");
progreso.after(acciones);
const botonMalla = document.createElement("button");
botonMalla.type = "button";
botonMalla.textContent = "Generar malla OBJ experimental";
const botonVerMalla = document.createElement("button");
botonVerMalla.type = "button";
botonVerMalla.textContent = "Ver modelo 3D";
const botonExportar = document.createElement("button");
botonExportar.type = "button";
botonExportar.textContent = "Guardar o exportar a…";
const botonEliminar = document.createElement("button");
botonEliminar.type = "button";
botonEliminar.textContent = "Eliminar proyecto y fotografías";
acciones.append(botonMalla, botonVerMalla, botonExportar, botonEliminar);
const descargas = document.createElement("div");
acciones.after(descargas);

let proyectoActual = null;
let temporizador = null;
let consultando = false;
let enviando = false;

function detenerConsulta() {
  if (temporizador !== null) clearInterval(temporizador);
  temporizador = null;
}
function actualizarEnviar() {
  enviar.disabled = enviando || Boolean(validar(seleccion)) || !nombre.value.trim();
}
function enlaceDescarga(texto, ruta) {
  const a = document.createElement("a");
  a.href = ruta;
  a.textContent = texto;
  a.download = "";
  const p = document.createElement("p");
  p.append(a);
  descargas.append(p);
}
function pintarProyecto(actual) {
  const listo = actual.estado === "completado";
  const informe = actual.informe_malla || {};
  const detalleMalla = actual.malla === "completada"
    ? " · malla: " + (informe.vertices ?? "?") + " vértices, " +
      (informe.caras ?? "?") + " caras, " +
      (informe.aristas_abiertas ?? "?") + " aristas abiertas, " +
      (informe.aristas_no_manifold ?? "?") + " no-manifold; " +
      (informe.malla_cerrada_por_aristas ? "cerrada por aristas" : "no cerrada por aristas") +
      ". No certifica imprimibilidad."
    : "";
  const captura = actual.calidad_captura || {};
  const detalleCaptura = Number.isInteger(captura.cantidad)
    ? " · fotos: " + captura.cantidad + " · aptas preliminares: " +
      (captura.aptas_preliminares ?? 0) + " · para revisar: " +
      (captura.revisar ?? 0) + " · no decodificables: " +
      (captura.no_decodificables ?? 0)
    : (captura.error ? " · preflight no disponible: " + captura.error : "");
  const trabajando = ["en_cola", "procesando"].includes(actual.estado) ||
    actual.malla === "procesando" || actual.exportaciones === "procesando";
  barraProgreso.hidden = !trabajando;
  const estadoAmigable = actual.estado === "en_cola" ? "En espera para comenzar…" :
    actual.estado === "procesando" ? "Reconstruyendo el objeto en 3D…" :
    actual.estado === "completado" ? "Reconstrucción terminada." :
    actual.estado === "error" ? "No se pudo completar la reconstrucción." :
    actual.estado === "interrumpido" ? "El trabajo se interrumpió y requiere reanudación." :
    actual.estado;
  progreso.textContent = estadoAmigable + " (" + actual.estado + ")" +
    detalleCaptura +
    " · reconstrucción densa: " + (actual.reconstruccion_densa || "sin dato") +
    (actual.alpha_malla ? " · alpha de malla: " + Number(actual.alpha_malla).toPrecision(4) : "") +
    (actual.error_reconstruccion_densa ? " · error denso: " + actual.error_reconstruccion_densa : "") +
    detalleMalla +
    (actual.error ? " — " + actual.error : "") +
    (actual.error_malla ? " — Malla: " + actual.error_malla : "") +
    (actual.error_exportaciones ? " — Exportación: " + actual.error_exportaciones : "");
  botonMalla.hidden = !listo;
  botonMalla.disabled = ["procesando", "completada"].includes(actual.malla);
  botonVerMalla.hidden = actual.malla !== "completada";
  botonExportar.hidden = actual.malla !== "completada";
  botonExportar.disabled = ["procesando", "completadas"].includes(actual.exportaciones);
  botonEliminar.hidden = false;
  botonEliminar.disabled = ["en_cola", "procesando"].includes(actual.estado) ||
    actual.malla === "procesando" || actual.exportaciones === "procesando";
  descargas.replaceChildren();
  const base = "/api/proyectos/" + encodeURIComponent(actual.id);
  enlaceDescarga("Ver informe de calidad de fotografías", base + "/informe-captura");
  if (listo) {
    enlaceDescarga("Descargar nube PLY", base + "/nube");
    if (actual.malla !== "procesando" && actual.exportaciones !== "procesando") {
      enlaceDescarga("Descargar paquete ZIP con todos los resultados", base + "/paquete");
    }
  }
  if (actual.malla === "completada") {
    enlaceDescarga("Descargar malla OBJ experimental (escala no verificada)", base + "/malla");
    enlaceDescarga("Descargar informe de calidad de la malla", base + "/malla/informe");
  }
  if (actual.exportaciones === "completadas") {
    const formatos = Array.isArray(actual.exportaciones_formatos)
      ? actual.exportaciones_formatos : ["obj", "ply", "stl"];
    for (const formato of formatos) {
      enlaceDescarga("Guardar archivo " + formato.toUpperCase() +
        (formato === "stl" ? " · impresión 3D" : formato === "obj" ? " · malla editable" : " · nube/malla") +
        " (escala no verificada)", base + "/exportaciones/" + formato);
    }
    if (estadoExportacion) estadoExportacion.textContent =
      "Archivos preparados: " + formatos.map(x => x.toUpperCase()).join(", ");
    if (confirmarExportacion) confirmarExportacion.disabled = true;
  } else if (actual.exportaciones === "error") {
    if (estadoExportacion) estadoExportacion.textContent = actual.error_exportaciones || "No se pudo preparar la exportación.";
    if (confirmarExportacion) confirmarExportacion.disabled = false;
  }
}
async function consultarProyecto() {
  if (!proyectoActual || consultando) return;
  consultando = true;
  try {
    const r = await fetch("/api/proyectos/" + encodeURIComponent(proyectoActual), {cache:"no-store"});
    if (!r.ok) throw new Error("No se pudo consultar el estado del proyecto");
    const actual = await r.json();
    if (actual.id !== proyectoActual) return;
    pintarProyecto(actual);
    if (["error", "interrumpido"].includes(actual.estado) ||
        (actual.estado === "completado" &&
         actual.exportaciones === "completadas")) detenerConsulta();
  } catch (e) {
    progreso.textContent = e.message;
    detenerConsulta();
  } finally {
    consultando = false;
  }
}
function comenzarConsulta() {
  detenerConsulta();
  consultarProyecto();
  temporizador = setInterval(consultarProyecto, 3000);
}
async function iniciarAccion(sufijo) {
  if (!proyectoActual) return;
  const boton = sufijo === "malla" ? botonMalla : botonExportar;
  boton.disabled = true;
  try {
    let ruta = "/api/proyectos/" + encodeURIComponent(proyectoActual) + "/" + sufijo;
    if (sufijo === "malla" && alphaMalla.value.trim()) {
      const valor = Number(alphaMalla.value);
      if (!Number.isFinite(valor) || valor <= 0 || valor > 1000) {
        throw new Error("Alpha debe ser mayor que 0 y no superar 1000.");
      }
      ruta += "?alpha=" + encodeURIComponent(String(valor));
    }
    let opciones = {method:"POST"};
    if (sufijo === "exportaciones") {
      const elegidos = Array.from(document.querySelectorAll('input[name="formato-exportacion"]:checked'))
        .map(x => x.value);
      if (!elegidos.length) throw new Error("Seleccioná al menos un formato disponible.");
      const datos = new FormData();
      elegidos.forEach(formato => datos.append("formatos", formato));
      opciones.body = datos;
      if (confirmarExportacion) confirmarExportacion.disabled = true;
      if (estadoExportacion) estadoExportacion.textContent = "Preparando: " + elegidos.map(x => x.toUpperCase()).join(", ");
    }
    const r = await fetch(ruta, opciones);
    if (!r.ok) {
      const e = await r.json();
      throw new Error(e.detail || "No se pudo iniciar el proceso");
    }
    progreso.textContent = sufijo === "exportaciones"
      ? "Preparando archivos elegidos…"
      : "Procesando " + sufijo + "…";
    comenzarConsulta();
  } catch (e) {
    progreso.textContent = e.message;
    if (estadoExportacion && sufijo === "exportaciones") estadoExportacion.textContent = e.message;
    boton.disabled = false;
    if (confirmarExportacion) confirmarExportacion.disabled = false;
  }
}
botonMalla.addEventListener("click", () => iniciarAccion("malla"));
botonVerMalla.addEventListener("click", () => {
  if (proyectoActual && window.visorEscaneo3D) {
    window.visorEscaneo3D.abrir("/api/proyectos/" + encodeURIComponent(proyectoActual) + "/malla");
  }
});
const panelExportar = document.getElementById("exportar-panel");
const confirmarExportacion = document.getElementById("confirmar-exportacion");
const cancelarExportacion = document.getElementById("cancelar-exportacion");
const estadoExportacion = document.getElementById("estado-exportacion");
botonExportar.addEventListener("click", () => {
  if (!panelExportar) return iniciarAccion("exportaciones");
  panelExportar.hidden = false;
  panelExportar.scrollIntoView({behavior:"smooth", block:"center"});
});
cancelarExportacion?.addEventListener("click", () => { panelExportar.hidden = true; });
confirmarExportacion?.addEventListener("click", () => iniciarAccion("exportaciones"));
botonEliminar.addEventListener("click", async () => {
  if (!proyectoActual || !window.confirm("¿Eliminar definitivamente las fotos y los modelos del servidor?")) return;
  botonEliminar.disabled = true;
  try {
    const r = await fetch("/api/proyectos/" + encodeURIComponent(proyectoActual), {method:"DELETE"});
    if (!r.ok) {
      const e = await r.json();
      throw new Error(e.detail || "No se pudo eliminar");
    }
    detenerConsulta();
    proyectoActual = null;
    descargas.replaceChildren();
    botonMalla.hidden = botonVerMalla.hidden = botonExportar.hidden = botonEliminar.hidden = true;
    progreso.textContent = "Proyecto y archivos eliminados.";
  } catch (e) {
    progreso.textContent = e.message;
    botonEliminar.disabled = false;
  }
});
enviar.addEventListener("click", async () => {
  if (validar(seleccion) || !nombre.value.trim()) return;
  enviando = true;
  actualizarEnviar();
  const datos = new FormData();
  datos.append("nombre", nombre.value.trim());
  datos.append("solicitar_denso", String(denso.checked));
  for (const archivo of seleccion) datos.append("fotos", archivo, archivo.name);
  progreso.textContent = "Enviando fotografías al servidor local…";
  try {
    const r = await fetch("/api/proyectos", {method:"POST", body:datos});
    const respuesta = await r.json();
    if (!r.ok) throw new Error(respuesta.detail || "No se pudo crear el proyecto");
    proyectoActual = respuesta.id;
    comenzarConsulta();
  } catch (e) {
    progreso.textContent = "Error: " + e.message;
  } finally {
    enviando = false;
    actualizarEnviar();
  }
});
limpiar.addEventListener("click", actualizarEnviar);
nombre.addEventListener("input", actualizarEnviar);
fotos.addEventListener("change", actualizarEnviar);
zona.addEventListener("drop", () => setTimeout(actualizarEnviar, 0));

async function recuperarProyectos() {
  const contenedor = document.getElementById("lista-proyectos");
  try {
    const r = await fetch("/api/proyectos", {cache:"no-store"});
    if (!r.ok) throw new Error("No se pudo recuperar la biblioteca");
    const datos = await r.json();
    const proyectos = Array.isArray(datos.proyectos) ? datos.proyectos : [];
    if (!contenedor) return;
    contenedor.replaceChildren();
    if (!proyectos.length) {
      const vacio = document.createElement("p");
      vacio.textContent = "Todavía no hay proyectos guardados en este servidor.";
      contenedor.append(vacio);
      return;
    }
    proyectos.slice().reverse().forEach(proyecto => {
      const fila = document.createElement("div");
      fila.className = "fila-proyecto";
      const info = document.createElement("div");
      const titulo = document.createElement("strong");
      titulo.textContent = proyecto.nombre || "Proyecto sin nombre";
      const detalle = document.createElement("p");
      detalle.textContent = (proyecto.estado || "sin estado") + " · " +
        (proyecto.fotos || 0) + " fotografías · " +
        (proyecto.creado_en ? new Date(proyecto.creado_en).toLocaleString() : "fecha no disponible");
      info.append(titulo, detalle);
      const controles = document.createElement("div");
      controles.className = "controles-proyecto";
      const abrir = document.createElement("button");
      abrir.type = "button";
      abrir.textContent = "Abrir";
      abrir.addEventListener("click", () => {
        proyectoActual = proyecto.id;
        detenerConsulta();
        comenzarConsulta();
        progreso.scrollIntoView({behavior:"smooth", block:"center"});
      });
      const renombrar = document.createElement("button");
      renombrar.type = "button";
      renombrar.className = "secundario";
      renombrar.textContent = "Renombrar";
      renombrar.addEventListener("click", async () => {
        const nuevo = window.prompt("Nuevo nombre del proyecto:", proyecto.nombre || "");
        if (nuevo === null) return;
        const datosFormulario = new FormData();
        datosFormulario.append("nombre", nuevo);
        try {
          const respuesta = await fetch("/api/proyectos/" + encodeURIComponent(proyecto.id) + "/nombre", {method:"PATCH", body:datosFormulario});
          const resultado = await respuesta.json();
          if (!respuesta.ok) throw new Error(resultado.detail || "No se pudo renombrar");
          recuperarProyectos();
        } catch (error) {
          window.alert(error.message);
        }
      });
      const eliminarDeBiblioteca = document.createElement("button");
      eliminarDeBiblioteca.type = "button";
      eliminarDeBiblioteca.className = "secundario";
      eliminarDeBiblioteca.textContent = "Eliminar";
      eliminarDeBiblioteca.addEventListener("click", async () => {
        if (!window.confirm("¿Eliminar definitivamente «" + (proyecto.nombre || "este proyecto") + "», sus fotografías y todos sus modelos?")) return;
        eliminarDeBiblioteca.disabled = true;
        try {
          const respuesta = await fetch("/api/proyectos/" + encodeURIComponent(proyecto.id), {method:"DELETE"});
          const cuerpo = await respuesta.json();
          if (!respuesta.ok) throw new Error(cuerpo.detail || "No se pudo eliminar");
          if (proyectoActual === proyecto.id) {
            proyectoActual = null;
            detenerConsulta();
            descargas.replaceChildren();
            botonMalla.hidden = botonVerMalla.hidden = botonExportar.hidden = botonEliminar.hidden = true;
            progreso.textContent = "Proyecto eliminado.";
          }
          await recuperarProyectos();
        } catch (error) {
          window.alert(error.message);
          eliminarDeBiblioteca.disabled = false;
        }
      });
      const duplicar = document.createElement("button");
      duplicar.type = "button";
      duplicar.className = "secundario";
      duplicar.textContent = "Duplicar";
      duplicar.addEventListener("click", async () => {
        duplicar.disabled = true;
        try {
          const respuesta = await fetch("/api/proyectos/" + encodeURIComponent(proyecto.id) + "/duplicar",
            {method:"POST"});
          const cuerpo = await respuesta.json();
          if (!respuesta.ok) throw new Error(cuerpo.detail || "No se pudo duplicar");
          await recuperarProyectos();
        } catch (error) {
          window.alert(error.message);
          duplicar.disabled = false;
        }
      });
      controles.append(abrir, renombrar, duplicar, eliminarDeBiblioteca);
      fila.append(info, controles);
      contenedor.append(fila);
    });
    if (!proyectoActual && proyectos.length) {
      proyectoActual = proyectos[proyectos.length - 1].id;
      comenzarConsulta();
    }
  } catch (error) {
    if (contenedor) contenedor.textContent = error.message;
  }
}
botonMalla.hidden = botonExportar.hidden = botonEliminar.hidden = true;
actualizarEnviar();
recuperarProyectos();


async function consultarSalud() {
  const indicador = document.getElementById("salud-servidor");
  if (!indicador) return;
  try {
    const respuesta = await fetch("/api/salud", {cache:"no-store"});
    if (!respuesta.ok) throw new Error("Servidor local no disponible");
    const datos = await respuesta.json();
    indicador.textContent = datos.colmap_detectado
      ? "Servidor local conectado · COLMAP detectado · " +
        datos.trabajos_en_cola + "/" + datos.limite_trabajos + " trabajos ocupados."
      : "Servidor conectado, pero COLMAP no está instalado o no está en PATH.";
    indicador.className = datos.colmap_detectado ? "ayuda estado-servidor ok" : "ayuda estado-servidor error";
  } catch (_) {
    indicador.textContent = "No se pudo verificar el servidor local. Abrí la aplicación desde el servidor ESCANEO 3D.";
    indicador.className = "ayuda estado-servidor error";
  }
}
consultarSalud();
setInterval(consultarSalud, 15000);


if ("serviceWorker" in navigator && location.protocol !== "file:") {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("./sw.js").catch(() => {});
  });
}
