"use strict";
const MAX_FOTOS = 100;
const MAX_BYTES = 20 * 1024 * 1024;
const MAX_TOTAL = 500 * 1024 * 1024;
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
enviar.disabled = true;
preparar.parentElement.appendChild(enviar);
const progreso = document.createElement("p");
progreso.setAttribute("role", "status");
progreso.setAttribute("aria-live", "polite");
enviar.after(progreso);
let temporizador = null;
function detenerConsulta() { if (temporizador) clearInterval(temporizador); temporizador = null; }
function actualizarEnviar() { enviar.disabled = preparar.disabled || !seleccion.length; }
nombre.addEventListener("input", actualizarEnviar);
fotos.addEventListener("change", actualizarEnviar);
zona.addEventListener("drop", () => setTimeout(actualizarEnviar, 0));
limpiar.addEventListener("click", () => { detenerConsulta(); actualizarEnviar(); progreso.textContent = ""; });
enviar.addEventListener("click", async () => {
  const error = validar(seleccion);
  if (error || !nombre.value.trim()) { mostrar(); actualizarEnviar(); return; }
  detenerConsulta();
  enviar.disabled = true;
  const datos = new FormData();
  datos.append("nombre", nombre.value.trim());
  for (const archivo of seleccion) datos.append("fotos", archivo, archivo.name);
  progreso.textContent = "Enviando fotografías al servidor local…";
  try {
    const respuesta = await fetch("/api/proyectos", { method: "POST", body: datos });
    const proyecto = await respuesta.json();
    if (!respuesta.ok) throw new Error(proyecto.detail || "Error al cargar fotos");
    progreso.textContent = "Proyecto " + proyecto.id + " recibido. Esperando COLMAP…";
    const consultar = async () => {
      try {
        const r = await fetch("/api/proyectos/" + encodeURIComponent(proyecto.id));
        if (!r.ok) throw new Error("No se pudo consultar el proyecto");
        const actual = await r.json();
        progreso.textContent = "Estado: " + actual.estado + (actual.error ? " — " + actual.error : "");
        if (actual.estado === "completado") {
          detenerConsulta();
          const enlace = document.createElement("a");
          enlace.href = "/api/proyectos/" + encodeURIComponent(proyecto.id) + "/nube";
          enlace.textContent = "Descargar nube PLY";
          enlace.setAttribute("download", "escaneo3d_nube.ply");
          progreso.append(" · ", enlace);
          enviar.disabled = false;
        } else if (actual.estado === "error") {
          detenerConsulta();
          enviar.disabled = false;
        }
      } catch (e) { detenerConsulta(); progreso.textContent = e.message; enviar.disabled = false; }
    };
    await consultar();
    if (!["completado", "error"].includes(progreso.textContent.replace("Estado: ", "").split(" ")[0])) {
      temporizador = setInterval(consultar, 3000);
    }
  } catch (e) {
    progreso.textContent = "No se pudo iniciar: " + e.message + ". Ejecutá el servidor local.";
    enviar.disabled = false;
  }
});
actualizarEnviar();
