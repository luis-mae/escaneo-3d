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
let temporizadorGuardado = null;
let baseDatosSesion = null;
let sesionLista = false;
const estadoSesionLocal = document.getElementById("estado-sesion-local");

function abrirBaseDatosSesion() {
  if (baseDatosSesion) return baseDatosSesion;
  baseDatosSesion = new Promise((resolve, reject) => {
    if (!("indexedDB" in window)) {
      reject(new Error("Este navegador no admite recuperación local de fotografías."));
      return;
    }
    const solicitud = indexedDB.open("escaneo3d-sesiones", 1);
    solicitud.onupgradeneeded = () => {
      const db = solicitud.result;
      if (!db.objectStoreNames.contains("borradores")) {
        db.createObjectStore("borradores", {keyPath:"id"});
      }
    };
    solicitud.onsuccess = () => resolve(solicitud.result);
    solicitud.onerror = () => reject(solicitud.error || new Error("No se pudo abrir el almacenamiento local."));
    solicitud.onblocked = () => reject(new Error("Otra pestaña bloquea el almacenamiento; cerrala y reintentá."));
  }).catch(error => {
    // Permitir reintentar tras bloqueos temporales o cuotas del navegador.
    baseDatosSesion = null;
    throw error;
  });
  return baseDatosSesion;
}

function ejecutarTransaccionSesion(modo, accion) {
  return abrirBaseDatosSesion().then(db => new Promise((resolve, reject) => {
    const tx = db.transaction("borradores", modo);
    const almacen = tx.objectStore("borradores");
    const solicitud = accion(almacen);
    let resultadoSolicitud;
    if (solicitud) {
      solicitud.onsuccess = () => { resultadoSolicitud = solicitud.result; };
      solicitud.onerror = () => reject(solicitud.error);
    }
    tx.oncomplete = () => resolve(resultadoSolicitud);
    tx.onerror = () => reject(tx.error || new Error("Falló el almacenamiento local."));
    tx.onabort = () => reject(tx.error || new Error("Se canceló el almacenamiento local."));
  }));
}

async function guardarSesionLocal() {
  if (!seleccion.length) {
    await eliminarSesionLocal();
    return;
  }
  const total = seleccion.reduce((suma, archivo) => suma + archivo.size, 0);
  if (navigator.storage?.estimate) {
    const [estimacion, anterior] = await Promise.all([
      navigator.storage.estimate(),
      ejecutarTransaccionSesion("readonly", almacen => almacen.get("borrador-principal"))
    ]);
    const bytesAnteriores = Array.isArray(anterior?.archivos)
      ? anterior.archivos.reduce((suma, item) => suma + (item.blob?.size || 0), 0) : 0;
    const usoEstimado = Math.max(0, (estimacion.usage || 0) - bytesAnteriores) + total;
    if (Number.isFinite(estimacion.quota) && usoEstimado > estimacion.quota * 0.95) {
      throw new Error("No hay espacio local suficiente para guardar todas las fotografías.");
    }
  }
  const borrador = {
    id: "borrador-principal",
    nombre: nombre.value,
    denso: Boolean(denso.checked),
    guardado_en: new Date().toISOString(),
    archivos: seleccion.map(archivo => ({
      nombre: archivo.name, tipo: archivo.type,
      ultima_modificacion: archivo.lastModified, blob: archivo
    }))
  };
  await ejecutarTransaccionSesion("readwrite", almacen => almacen.put(borrador));
  if (estadoSesionLocal) estadoSesionLocal.textContent =
    "Sesión recuperable en este dispositivo · " + seleccion.length + " fotografías guardadas localmente.";
}

async function eliminarSesionLocal() {
  try {
    await ejecutarTransaccionSesion("readwrite", almacen => almacen.delete("borrador-principal"));
    if (estadoSesionLocal) estadoSesionLocal.textContent = "Borrador local eliminado.";
  } catch (error) {
    if (estadoSesionLocal) estadoSesionLocal.textContent =
      "No se pudo borrar el borrador local: " + error.message;
  }
}

function programarGuardadoSesion() {
  if (!sesionLista) return;
  if (temporizadorGuardado !== null) clearTimeout(temporizadorGuardado);
  temporizadorGuardado = setTimeout(async () => {
    temporizadorGuardado = null;
    try {
      await guardarSesionLocal();
    } catch (error) {
      if (estadoSesionLocal) estadoSesionLocal.textContent =
        "La sesión no pudo guardarse localmente: " + error.message;
    }
  }, 700);
}

async function restaurarSesionLocal() {
  try {
    const borrador = await ejecutarTransaccionSesion("readonly",
      almacen => almacen.get("borrador-principal"));
    if (!borrador || !Array.isArray(borrador.archivos) || !borrador.archivos.length) {
      sesionLista = true;
      if (seleccion.length || nombre.value.trim()) programarGuardadoSesion();
      return;
    }
    if (seleccion.length || nombre.value.trim()) {
      sesionLista = true;
      programarGuardadoSesion();
      return;
    }
    const archivos = borrador.archivos.map(item =>
      new File([item.blob], item.nombre, {
        type:item.tipo, lastModified:item.ultima_modificacion || Date.now()
      })
    );
    const error = validar(archivos);
    if (error) {
      if (estadoSesionLocal) estadoSesionLocal.textContent =
        "Se encontró un borrador local, pero necesita revisión: " + error;
      sesionLista = true;
      return;
    }
    seleccion = archivos;
    sesionLista = true;
    nombre.value = borrador.nombre || "";
    denso.checked = Boolean(borrador.denso);
    mostrar(false);
    actualizarEnviar();
    if (estadoSesionLocal) estadoSesionLocal.textContent =
      "Sesión recuperada desde este dispositivo · " + seleccion.length + " fotografías.";
  } catch (error) {
    sesionLista = true;
    if (estadoSesionLocal) estadoSesionLocal.textContent =
      "No se pudo recuperar la sesión local: " + error.message;
  }
}

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
const urlsMiniaturas = new Set();
function mostrar(guardar = true) {
  for (const url of urlsMiniaturas) URL.revokeObjectURL(url);
  urlsMiniaturas.clear();
  lista.replaceChildren();
  resultado.hidden = true;
  manifiesto = null;
  const error = seleccion.length ? validar(seleccion) : null;
  seleccion.forEach((archivo, indice) => {
    const li = document.createElement("li");
    li.className = "foto-seleccionada";
    const miniatura = document.createElement("img");
    const urlMiniatura = URL.createObjectURL(archivo);
    urlsMiniaturas.add(urlMiniatura);
    miniatura.src = urlMiniatura;
    miniatura.alt = "Vista previa de " + archivo.name;
    miniatura.loading = "lazy";
    const detalle = document.createElement("span");
    detalle.className = "detalle-foto";
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
    li.append(miniatura, detalle, quitar);
    lista.appendChild(li);
  });
  if (!seleccion.length) mensaje("Todavía no seleccionaste fotografías.");
  else if (error) mensaje(error, "error");
  else mensaje(`${seleccion.length} fotografías listas para preparar.`, "ok");
  preparar.disabled = Boolean(error) || !nombre.value.trim();
  if (guardar) programarGuardadoSesion();
}
function recibir(archivos) {
  seleccion = Array.from(archivos);
  mostrar();
}
function agregarFotos(archivos) {
  const nuevas = Array.from(archivos);
  if (!nuevas.length) return;
  const combinadas = [...seleccion, ...nuevas];
  if (combinadas.length > MAX_FOTOS) {
    mensaje("Se admiten como máximo " + MAX_FOTOS + " fotografías por proyecto.", "error");
    return;
  }
  if (combinadas.reduce((total, archivo) => total + archivo.size, 0) > MAX_TOTAL) {
    mensaje("El proyecto supera el límite de 500 MB.", "error");
    return;
  }
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
denso.addEventListener("change", programarGuardadoSesion);
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
  if (temporizadorGuardado !== null) clearTimeout(temporizadorGuardado);
  temporizadorGuardado = null;
  mostrar(false);
  eliminarSesionLocal();
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
const botonCancelar = document.createElement("button");
botonCancelar.type = "button";
botonCancelar.className = "secundario";
botonCancelar.textContent = "Cancelar reconstrucción";
botonCancelar.hidden = true;
const botonReintentar = document.createElement("button");
botonReintentar.type = "button";
botonReintentar.className = "secundario";
botonReintentar.textContent = "Reintentar reconstrucción";
botonReintentar.hidden = true;
botonReintentar.addEventListener("click", async () => {
  if (!proyectoActual || !window.confirm("¿Reintentar la reconstrucción con las fotografías ya guardadas?")) return;
  botonReintentar.disabled = true;
  try {
    const respuesta = await fetch("/api/proyectos/" + encodeURIComponent(proyectoActual) + "/reintentar", {method:"POST"});
    const cuerpo = await respuesta.json();
    if (!respuesta.ok) throw new Error(cuerpo.detail || "No se pudo reintentar");
    detenerConsulta();
    comenzarConsulta();
  } catch (error) {
    progreso.textContent = error.message;
    botonReintentar.disabled = false;
  }
});
botonCancelar.addEventListener("click", async () => {
  if (!proyectoActual || !window.confirm("¿Cancelar la reconstrucción en curso?")) return;
  botonCancelar.disabled = true;
  try {
    const respuesta = await fetch("/api/proyectos/" + encodeURIComponent(proyectoActual) + "/cancelar",
      {method:"POST"});
    const cuerpo = await respuesta.json();
    if (!respuesta.ok) throw new Error(cuerpo.detail || "No se pudo cancelar");
    progreso.textContent = "Cancelación solicitada. Esperando que COLMAP detenga el proceso…";
  } catch (error) {
    progreso.textContent = error.message;
    botonCancelar.disabled = false;
  }
});
acciones.append(botonMalla, botonVerMalla, botonExportar, botonCancelar, botonReintentar, botonEliminar);
const descargas = document.createElement("div");
acciones.after(descargas);

const solicitudesMallaAutomaticas = new Set();
const fallosInicioMalla = new Set();
const CLAVE_PROYECTO_ACTIVO = "escaneo3d_proyecto_activo";
function recordarProyecto(id) {
  if (/^[a-f0-9]{32}$/.test(id || "")) sessionStorage.setItem(CLAVE_PROYECTO_ACTIVO, id);
  else sessionStorage.removeItem(CLAVE_PROYECTO_ACTIVO);
}
let proyectoActual = null;
let temporizador = null;
let consultando = false;
let generacionConsulta = 0;
let consultaEnCurso = null;
let fallosConsultaConsecutivos = 0;
let proximaConsultaEn = 0;
let enviando = false;

function detenerConsulta() {
  generacionConsulta++;
  if (temporizador !== null) clearInterval(temporizador);
  temporizador = null;
  if (consultaEnCurso) consultaEnCurso.abort();
  consultaEnCurso = null;
  consultando = false;
}
function actualizarEnviar() {
  const consentimiento = document.getElementById("consentir-subida");
  enviar.disabled = enviando || Boolean(validar(seleccion)) ||
    !nombre.value.trim() || !consentimiento?.checked;
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
let mallaDisponibleParaExportar = false;
function pintarProyecto(actual) {
  const mallaAnteriorDisponible = mallaDisponibleParaExportar;
  mallaDisponibleParaExportar = actual.malla === "completada";
  for (const opcion of document.querySelectorAll('input[name="formato-exportacion"]')) {
    if (opcion.value === "nube") continue;
    opcion.disabled = !mallaDisponibleParaExportar;
    if (opcion.disabled) opcion.checked = false;
  }
  if (mallaDisponibleParaExportar && !mallaAnteriorDisponible) {
    const stl = document.querySelector('input[name="formato-exportacion"][value="stl"]');
    if (stl) stl.checked = true;
  }
  if (!mallaDisponibleParaExportar) {
    const nube = document.querySelector('input[name="formato-exportacion"][value="nube"]');
    if (nube) nube.checked = true;
  }
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
  const reparacion = informe.reparacion_conservadora || {};
  const detalleReparacion = Number.isInteger(reparacion.caras_finales)
    ? " · reparación conservadora: " + (reparacion.caras_descartadas || 0) +
      " caras descartadas, " + (reparacion.caras_agregadas || 0) +
      " agregadas, " + (reparacion.aristas_abiertas ?? "?") + " aristas abiertas."
    : "";
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
    actual.estado === "cancelado" ? "Reconstrucción cancelada; la cuota fue liberada." :
    actual.estado === "interrumpido" ? "El trabajo se interrumpió y requiere reanudación." :
    actual.estado;
  progreso.textContent = estadoAmigable + " (" + actual.estado + ")" +
    detalleCaptura +
    " · reconstrucción densa: " + (actual.reconstruccion_densa || "sin dato") +
    (actual.alpha_malla ? " · alpha de malla: " + Number(actual.alpha_malla).toPrecision(4) : "") +
    (actual.error_reconstruccion_densa ? " · error denso: " + actual.error_reconstruccion_densa : "") +
    detalleMalla + detalleReparacion +
    (actual.error ? " — " + actual.error : "") +
    (actual.error_malla ? " — Malla: " + actual.error_malla : "") +
    (actual.error_exportaciones ? " — Exportación: " + actual.error_exportaciones : "");
  // El servidor inicia el mallado al finalizar COLMAP; el navegador solo consulta el estado.
  botonMalla.hidden = !listo;
  botonMalla.disabled = ["procesando", "completada"].includes(actual.malla);
  botonMalla.textContent = actual.malla === "error" || actual.malla === "interrumpido"
    ? "Reintentar generación de malla OBJ" : "Generar malla OBJ experimental";
  botonVerMalla.hidden = actual.estado !== "completado";
  botonVerMalla.textContent = actual.malla === "completada" ? "Ver modelo 3D" : "Ver nube de puntos 3D";
  botonExportar.hidden = !listo;
  botonExportar.disabled = actual.exportaciones === "procesando";
  botonCancelar.hidden = !["en_cola", "procesando"].includes(actual.estado);
  botonCancelar.disabled = Boolean(actual.cancelacion_solicitada);
  botonReintentar.hidden = !["error", "cancelado", "interrumpido"].includes(actual.estado);
  botonReintentar.disabled = false;
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
    enlaceDescarga("Descargar malla OBJ reparada (escala no verificada)", base + "/malla");
    enlaceDescarga("Descargar malla OBJ original sin reparar", base + "/malla/original");
    enlaceDescarga("Descargar informe de calidad de la malla", base + "/malla/informe");
  }
  if (actual.exportaciones === "completadas") {
    const formatos = Array.isArray(actual.exportaciones_formatos)
      ? actual.exportaciones_formatos : ["obj", "ply", "stl"];
    for (const formato of formatos) {
      enlaceDescarga("Guardar archivo " + formato.toUpperCase() +
        (formato === "stl" ? " · impresión 3D" : formato === "obj" ? " · malla editable" : formato === "glb" ? " · visor 3D/web" : formato === "3mf" ? " · fabricación aditiva (unidad asumida mm)" : formato === "nube" ? " · puntos originales" : formato === "ply" ? " · malla PLY" : " · modelo 3D") +
        " (escala no verificada)", base + "/exportaciones/" + formato);
    }
    enlaceDescarga("Descargar informe de exportación (tamaños y SHA-256)",
      base + "/exportaciones/informe");
    if (actual.exportaciones_paquete) {
      enlaceDescarga("Descargar ZIP con los formatos elegidos",
        base + "/exportaciones/paquete");
    }
    if (estadoExportacion) estadoExportacion.textContent =
      "Archivos preparados: " + formatos.map(x => x.toUpperCase()).join(", ");
    if (confirmarExportacion) confirmarExportacion.disabled = false;
  } else if (actual.exportaciones === "error") {
    if (estadoExportacion) estadoExportacion.textContent = actual.error_exportaciones || "No se pudo preparar la exportación.";
    if (confirmarExportacion) confirmarExportacion.disabled = false;
  }
}
async function consultarProyecto() {
  if (!proyectoActual || consultando || document.visibilityState === "hidden" || Date.now() < proximaConsultaEn) return;
  const idConsultado = proyectoActual;
  const generacionActual = generacionConsulta;
  const controlador = new AbortController();
  consultaEnCurso = controlador;
  consultando = true;
  try {
    const r = await fetch("/api/proyectos/" + encodeURIComponent(idConsultado),
      {cache:"no-store", signal:controlador.signal});
    if (!r.ok) throw new Error("No se pudo consultar el estado del proyecto (HTTP " + r.status + ")");
    const actual = await r.json();
    if (actual.id !== idConsultado || idConsultado !== proyectoActual || generacionActual !== generacionConsulta) return;
    fallosConsultaConsecutivos = 0;
    proximaConsultaEn = 0;
    pintarProyecto(actual);
    // Mantener la consulta durante la generación automática de malla.
    // Detenerla solo cuando el proyecto no tenga operaciones pendientes.
    if (["error", "interrumpido", "cancelado"].includes(actual.estado) ||
        (actual.estado === "completado" &&
         (["completada", "error"].includes(actual.malla) ||
          (fallosInicioMalla.has(actual.id) && (!actual.malla || actual.malla === "pendiente"))) &&
         actual.exportaciones !== "procesando")) detenerConsulta();
  } catch (e) {
    if (idConsultado !== proyectoActual || generacionActual !== generacionConsulta || e.name === "AbortError") return;
    fallosConsultaConsecutivos++;
    // El teléfono puede perder la red durante minutos: no abandonar el trabajo
    // ni exigir que el usuario abra nuevamente el proyecto.
    const espera = Math.min(30000, 3000 * Math.pow(2, Math.min(4, fallosConsultaConsecutivos - 1)));
    proximaConsultaEn = Date.now() + espera;
    progreso.textContent = "Sin conexión con el servidor. Reintentando automáticamente en " +
      Math.ceil(espera / 1000) + " segundos (" + fallosConsultaConsecutivos +
      " intentos fallidos). " + e.message;
  } finally {
    if (consultaEnCurso === controlador) {
      consultaEnCurso = null;
      consultando = false;
    }
  }
}
function comenzarConsulta() {
  detenerConsulta();
  fallosConsultaConsecutivos = 0;
  proximaConsultaEn = 0;
  consultarProyecto();
  temporizador = setInterval(consultarProyecto, 3000);
}
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible" && proyectoActual) {
    if (temporizador === null) comenzarConsulta();
    else consultarProyecto();
  }
});
async function iniciarAccion(sufijo, automatico = false) {
  if (!proyectoActual) return;
  const idAccion = proyectoActual;
  const boton = sufijo === "malla" ? botonMalla : botonExportar;
  boton.disabled = true;
  try {
    let ruta = "/api/proyectos/" + encodeURIComponent(idAccion) + "/" + sufijo;
    if (sufijo === "malla" && !automatico && alphaMalla.value.trim()) {
      const valor = Number(alphaMalla.value);
      if (!Number.isFinite(valor) || valor <= 0) {
        throw new Error("Alpha debe ser un número finito mayor que 0.");
      }
      ruta += "?alpha=" + encodeURIComponent(String(valor));
    }
    let opciones = {method:"POST"};
    if (sufijo === "exportaciones") {
      const elegidos = Array.from(document.querySelectorAll('input[name="formato-exportacion"]:checked'))
        .map(x => x.value);
      if (!elegidos.length) throw new Error("Seleccioná al menos un formato disponible.");
      if (!mallaDisponibleParaExportar && elegidos.some(formato => formato !== "nube")) {
        throw new Error("Sin malla OBJ solo podés exportar la nube de puntos PLY.");
      }
      const datos = new FormData();
      elegidos.forEach(formato => datos.append("formatos", formato));
      const crearPaquete = document.getElementById("crear-paquete");
      datos.append("crear_paquete", String(Boolean(crearPaquete?.checked)));
      opciones.body = datos;
      if (confirmarExportacion) confirmarExportacion.disabled = true;
      if (estadoExportacion) estadoExportacion.textContent = "Preparando: " + elegidos.map(x => x.toUpperCase()).join(", ");
    }
    const r = await fetch(ruta, opciones);
    if (!r.ok) {
      const e = await r.json();
      throw new Error(e.detail || "No se pudo iniciar el proceso");
    }
    if (proyectoActual !== idAccion) return;
    progreso.textContent = sufijo === "exportaciones"
      ? "Preparando archivos elegidos…"
      : "Procesando " + sufijo + "…";
    comenzarConsulta();
  } catch (e) {
    if (proyectoActual !== idAccion) return;
    progreso.textContent = e.message;
    if (sufijo === "malla") {
      fallosInicioMalla.add(idAccion);
      botonMalla.textContent = "Reintentar generación de malla OBJ";
      // Mantener la consulta para que la nube y su descarga sigan accesibles
      // aunque el inicio automático de mallado haya fallado.
      if (!automatico) detenerConsulta();
    }
    if (estadoExportacion && sufijo === "exportaciones") estadoExportacion.textContent = e.message;
    boton.disabled = false;
    if (confirmarExportacion) confirmarExportacion.disabled = false;
  }
}
botonMalla.addEventListener("click", () => {
  if (proyectoActual) fallosInicioMalla.delete(proyectoActual);
  iniciarAccion("malla");
});
botonVerMalla.addEventListener("click", () => {
  if (proyectoActual && window.visorEscaneo3D) {
    const base = "/api/proyectos/" + encodeURIComponent(proyectoActual);
    if (botonVerMalla.textContent === "Ver modelo 3D") {
      window.visorEscaneo3D.abrir(base + "/malla");
    } else {
      window.visorEscaneo3D.abrirNube(base + "/nube/vista");
    }
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
document.getElementById("consentir-subida")?.addEventListener("change", actualizarEnviar);
enviar.addEventListener("click", async () => {
  if (enviando || validar(seleccion) || !nombre.value.trim() ||
      !document.getElementById("consentir-subida")?.checked) return;
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
    if (!respuesta.id || !/^[a-f0-9]{32}$/.test(respuesta.id)) throw new Error("El servidor no devolvió un identificador válido");
    proyectoActual = respuesta.id;
    recordarProyecto(proyectoActual);
    if (temporizadorGuardado !== null) clearTimeout(temporizadorGuardado);
    temporizadorGuardado = null;
    // El proyecto ya existe en el servidor: una falla de IndexedDB no debe
    // impedir abrirlo ni provocar una segunda subida accidental.
    seleccion = [];
    fotos.value = "";
    nombre.value = "";
    mostrar(false);
    try {
      await eliminarSesionLocal();
    } catch (error) {
      if (estadoSesionLocal) estadoSesionLocal.textContent =
        "Proyecto enviado; no se pudo limpiar el borrador local: " + error.message;
    }
    actualizarEnviar();
    comenzarConsulta();
    recuperarProyectos();
  } catch (e) {
    progreso.textContent = "Error: " + e.message + ". Revisá la biblioteca antes de reenviar: si el servidor recibió las fotos, el proyecto puede existir.";
    recuperarProyectos();
  } finally {
    enviando = false;
    actualizarEnviar();
  }
});
limpiar.addEventListener("click", actualizarEnviar);
nombre.addEventListener("input", actualizarEnviar);
fotos.addEventListener("change", actualizarEnviar);
zona.addEventListener("drop", () => setTimeout(actualizarEnviar, 0));
restaurarSesionLocal();

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
        recordarProyecto(proyectoActual);
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
      const recordado = sessionStorage.getItem(CLAVE_PROYECTO_ACTIVO);
      const existente = proyectos.find(p => p.id === recordado);
      proyectoActual = existente ? existente.id : proyectos[proyectos.length - 1].id;
      recordarProyecto(proyectoActual);
      comenzarConsulta();
    }
    if (proyectoActual && !proyectos.some(p => p.id === proyectoActual)) {
      proyectoActual = proyectos.length ? proyectos[proyectos.length - 1].id : null;
      recordarProyecto(proyectoActual);
      if (proyectoActual) comenzarConsulta();
      else detenerConsulta();
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
    const servidor = datos.modo === "remoto_autenticado" ? "Servidor remoto" : "Servidor local";
    indicador.textContent = datos.colmap_detectado
      ? servidor + " conectado · COLMAP detectado · " +
        datos.trabajos_en_cola + "/" + datos.limite_trabajos + " trabajos ocupados."
      : servidor + " conectado, pero COLMAP no está instalado o no está en PATH.";
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
