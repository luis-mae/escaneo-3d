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
  for (const archivo of seleccion) {
    const li = document.createElement("li");
    li.textContent = `${archivo.name} · ${(archivo.size / 1048576).toFixed(2)} MB`;
    lista.appendChild(li);
  }
  if (!seleccion.length) mensaje("Todavía no seleccionaste fotografías.");
  else if (error) mensaje(error, "error");
  else mensaje(`${seleccion.length} fotografías listas para preparar.`, "ok");
  preparar.disabled = Boolean(error) || !nombre.value.trim();
}
function recibir(archivos) {
  seleccion = Array.from(archivos);
  mostrar();
}
fotos.addEventListener("change", () => recibir(fotos.files));
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
enviar.after(progreso);
const acciones = document.createElement("div");
progreso.after(acciones);
const botonMalla = document.createElement("button");
botonMalla.type = "button";
botonMalla.textContent = "Generar malla OBJ experimental";
const botonExportar = document.createElement("button");
botonExportar.type = "button";
botonExportar.textContent = "Preparar OBJ, PLY y STL";
const botonEliminar = document.createElement("button");
botonEliminar.type = "button";
botonEliminar.textContent = "Eliminar proyecto y fotografías";
acciones.append(botonMalla, botonExportar, botonEliminar);
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
  progreso.textContent = "Estado: " + actual.estado +
    " · reconstrucción densa: " + (actual.reconstruccion_densa || "sin dato") +
    (actual.alpha_malla ? " · alpha de malla: " + Number(actual.alpha_malla).toPrecision(4) : "") +
    (actual.error ? " — " + actual.error : "") +
    (actual.error_malla ? " — Malla: " + actual.error_malla : "") +
    (actual.error_exportaciones ? " — Exportación: " + actual.error_exportaciones : "");
  botonMalla.hidden = !listo;
  botonMalla.disabled = ["procesando", "completada"].includes(actual.malla);
  botonExportar.hidden = actual.malla !== "completada";
  botonExportar.disabled = ["procesando", "completadas"].includes(actual.exportaciones);
  botonEliminar.hidden = false;
  botonEliminar.disabled = ["en_cola", "procesando"].includes(actual.estado) ||
    actual.malla === "procesando" || actual.exportaciones === "procesando";
  descargas.replaceChildren();
  const base = "/api/proyectos/" + encodeURIComponent(actual.id);
  if (listo) enlaceDescarga("Descargar nube PLY", base + "/nube");
  if (actual.malla === "completada") {
    enlaceDescarga("Descargar malla OBJ experimental (alpha automático; escala no verificada)", base + "/malla");
  }
  if (actual.exportaciones === "completadas") {
    for (const formato of ["obj", "ply", "stl"]) {
      enlaceDescarga("Descargar " + formato.toUpperCase() + " (sin escala verificada)",
        base + "/exportaciones/" + formato);
    }
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
    const r = await fetch(ruta, {method:"POST"});
    if (!r.ok) {
      const e = await r.json();
      throw new Error(e.detail || "No se pudo iniciar el proceso");
    }
    progreso.textContent = "Procesando " + sufijo + "…";
    comenzarConsulta();
  } catch (e) {
    progreso.textContent = e.message;
    boton.disabled = false;
  }
}
botonMalla.addEventListener("click", () => iniciarAccion("malla"));
botonExportar.addEventListener("click", () => iniciarAccion("exportaciones"));
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
    botonMalla.hidden = botonExportar.hidden = botonEliminar.hidden = true;
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
  try {
    const r = await fetch("/api/proyectos", {cache:"no-store"});
    if (!r.ok) return;
    const datos = await r.json();
    const proyectos = Array.isArray(datos.proyectos) ? datos.proyectos : [];
    if (!proyectos.length) return;
    const ultimo = proyectos[proyectos.length - 1];
    proyectoActual = ultimo.id;
    comenzarConsulta();
  } catch (_) { /* Interfaz utilizable aun sin servidor local. */ }
}
botonMalla.hidden = botonExportar.hidden = botonEliminar.hidden = true;
actualizarEnviar();
recuperarProyectos();
