"use strict";
const MAX_FOTOS = 100;
const MAX_BYTES = 20 * 1024 * 1024;
const MIN_FOTOS = 3;
const TIPOS = new Set(["image/jpeg", "image/png", "image/webp"]);
const nombre = document.getElementById("nombre");
const fotos = document.getElementById("fotos");
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
  const nombres = new Set();
  for (const archivo of archivos) {
    if (!TIPOS.has(archivo.type)) return `Formato no admitido: ${archivo.name}`;
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
