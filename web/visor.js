"use strict";
(() => {
  const panel = document.getElementById("visor3d");
  const canvas = document.getElementById("lienzo-3d");
  const estado = document.getElementById("estado-visor");
  const cerrar = document.getElementById("cerrar-visor");
  const iniciarCalibracion = document.getElementById("iniciar-calibracion");
  const distanciaRef1 = document.getElementById("distancia-ref-1");
  const distanciaRef2 = document.getElementById("distancia-ref-2");
  const estadoCalibracion = document.getElementById("estado-calibracion");
  const iniciarMedicion = document.getElementById("iniciar-medicion");
  const resultadoMedicion = document.getElementById("resultado-medicion");
  const resultadoGeometria = document.getElementById("resultado-geometria");
  const resultadoCalibracion = document.getElementById("resultado-calibracion");
  const descargarMallaMM = document.getElementById("descargar-malla-mm");
  const descargarSTLMM = document.getElementById("descargar-stl-mm");
  const descargarInformeMM = document.getElementById("descargar-informe-mm");
  if (!panel || !canvas) return;
  const ctx = canvas.getContext("2d");
  let vertices = [];
  let verticesOriginales = [];
  let caras = [];
  let carasOriginales = [];
  let ultimoProyectado = [];
  let modoCalibracion = false;
  let puntosCalibracion = [];
  let escalaCalibradaMM = null;
  let modoMedicion = false;
  let puntosMedicion = [];
  let urlsCalibracion = [];
  let rotX = -0.35, rotY = 0.65, zoom = 1;
  let arrastrando = false, px = 0, py = 0;
  let centro = [0, 0, 0], escala = 1;

  function mensaje(texto) { estado.textContent = texto; }
  function ajustarLienzo() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const ancho = Math.max(320, Math.floor(canvas.clientWidth * dpr));
    const alto = Math.max(240, Math.floor(canvas.clientHeight * dpr));
    if (canvas.width !== ancho || canvas.height !== alto) {
      canvas.width = ancho; canvas.height = alto;
    }
  }
  function cargarOBJ(texto) {
    const v = [], f = [];
    for (const linea of texto.split(/\r?\n/)) {
      const p = linea.trim().split(/\s+/);
      if (p[0] === "v" && p.length >= 4) {
        const xyz = p.slice(1, 4).map(Number);
        if (xyz.every(Number.isFinite)) v.push(xyz);
      } else if (p[0] === "f" && p.length >= 4) {
        const ids = p.slice(1).map(x => {
          const n = Number.parseInt(x.split("/")[0], 10);
          return n < 0 ? v.length + n : n - 1;
        });
        if (ids.every(n => Number.isInteger(n) && n >= 0 && n < v.length)) {
          for (let i = 1; i < ids.length - 1; i++) f.push([ids[0], ids[i], ids[i + 1]]);
        }
      }
      if (v.length > 500_000 || f.length > 500_000) {
        throw new Error("La malla supera el límite de visualización del visor.");
      }
    }
    if (v.length < 3 || !f.length) throw new Error("El OBJ no contiene una malla triangular válida.");
    verticesOriginales = v.map(p => p.slice());
    carasOriginales = f.map(face => face.slice());
    puntosCalibracion = [];
    modoCalibracion = false;
    limpiarDescargasCalibracion();
    const min = [Infinity, Infinity, Infinity];
    const max = [-Infinity, -Infinity, -Infinity];
    for (const p of v) for (let k = 0; k < 3; k++) {
      if (p[k] < min[k]) min[k] = p[k];
      if (p[k] > max[k]) max[k] = p[k];
    }
    centro = min.map((x, k) => (x + max[k]) / 2);
    const dimensiones = max.map((x, k) => x - min[k]);
    const radio = Math.max(...dimensiones);
    if (!(radio > 0) || !Number.isFinite(radio)) throw new Error("La malla tiene dimensiones inválidas.");
    escala = 2 / radio;
    if (f.length > 18_000) {
      const paso = Math.ceil(f.length / 18_000);
      caras = f.filter((_, i) => i % paso === 0);
      mensaje("Vista simplificada: " + caras.length.toLocaleString("es-AR") +
        " de " + f.length.toLocaleString("es-AR") + " caras.");
    } else {
      caras = f;
      mensaje(v.length.toLocaleString("es-AR") + " vértices · " +
        f.length.toLocaleString("es-AR") + " caras · caja relativa " +
        dimensiones.map(x => x.toPrecision(4)).join(" × ") +
        " (unidades no verificadas).");
    }
    vertices = v.map(p => p.map((x, k) => (x - centro[k]) * escala));
    rotX = -0.35; rotY = 0.65; zoom = 1;
    dibujar();
  }
  function transformar(p) {
    const cy = Math.cos(rotY), sy = Math.sin(rotY);
    const cx = Math.cos(rotX), sx = Math.sin(rotX);
    const x = p[0] * cy + p[2] * sy;
    const z1 = -p[0] * sy + p[2] * cy;
    const y = p[1] * cx - z1 * sx;
    const z = p[1] * sx + z1 * cx;
    return [x, y, z];
  }
  function dibujar() {
    ajustarLienzo();
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#111827"; ctx.fillRect(0, 0, w, h);
    if (!vertices.length || !caras.length) return;
    const proyectados = vertices.map(p => {
      const q = transformar(p);
      const perspectiva = 3.8 / (3.8 - q[2] * zoom);
      return [w / 2 + q[0] * zoom * perspectiva * w * 0.34,
              h / 2 - q[1] * zoom * perspectiva * h * 0.34, q[2]];
    });
    ultimoProyectado = proyectados;
    const luz = [0.25, 0.65, 0.72];
    const orden = caras.map(face => {
      const a = proyectados[face[0]], b = proyectados[face[1]], c = proyectados[face[2]];
      const ux = b[0] - a[0], uy = b[1] - a[1];
      const vx = c[0] - a[0], vy = c[1] - a[1];
      const nx = uy * (c[2] - a[2]) - (b[2] - a[2]) * vy;
      const ny = (b[2] - a[2]) * vx - ux * (c[2] - a[2]);
      const nz = ux * vy - uy * vx;
      const norma = Math.hypot(nx, ny, nz) || 1;
      const brilho = Math.max(0.18, Math.abs((nx*luz[0] + ny*luz[1] + nz*luz[2]) / norma));
      return {a,b,c,z:(a[2]+b[2]+c[2])/3,brilho};
    }).sort((x,y) => x.z - y.z);
    for (const t of orden) {
      ctx.beginPath(); ctx.moveTo(t.a[0],t.a[1]); ctx.lineTo(t.b[0],t.b[1]);
      ctx.lineTo(t.c[0],t.c[1]); ctx.closePath();
      const tono = Math.round(65 + t.brilho * 145);
      ctx.fillStyle = "rgb(" + tono + "," + Math.min(230,tono+12) + "," + Math.min(255,tono+35) + ")";
      ctx.fill();
      ctx.strokeStyle = "rgba(15,23,42,.35)"; ctx.lineWidth = Math.max(0.5, w/1600); ctx.stroke();
    }
    const puntosMarcados = modoMedicion || puntosMedicion.length ? puntosMedicion : puntosCalibracion;
    puntosMarcados.forEach((indice, posicion) => {
      const punto = proyectados[indice];
      if (!punto) return;
      ctx.beginPath(); ctx.arc(punto[0], punto[1], Math.max(7, w / 100), 0, Math.PI * 2);
      ctx.fillStyle = "#facc15"; ctx.fill();
      ctx.strokeStyle = "#111827"; ctx.lineWidth = Math.max(2, w / 500); ctx.stroke();
      ctx.fillStyle = "#111827"; ctx.font = `bold ${Math.max(12, w / 55)}px sans-serif`;
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(String(posicion + 1), punto[0], punto[1]);
    });
  }
  async function abrir(url) {
    panel.hidden = false;
    mensaje("Cargando malla OBJ…");
    try {
      const r = await fetch(url, {cache:"no-store"});
      if (!r.ok) throw new Error("No se pudo descargar la malla OBJ.");
      cargarOBJ(await r.text());
      panel.scrollIntoView({behavior:"smooth", block:"start"});
    } catch (e) {
      vertices = []; verticesOriginales = []; caras = []; carasOriginales = [];
      ultimoProyectado = []; puntosCalibracion = []; modoCalibracion = false;
      limpiarDescargasCalibracion();
      dibujar(); mensaje(e.message);
    }
  }
  function limpiarDescargasCalibracion() {
    for (const url of urlsCalibracion) URL.revokeObjectURL(url);
    urlsCalibracion = [];
    escalaCalibradaMM = null;
    modoMedicion = false;
    puntosMedicion = [];
    if (iniciarMedicion) iniciarMedicion.disabled = true;
    if (resultadoMedicion) resultadoMedicion.textContent = "La medición se habilita después de calibrar la escala.";
    if (resultadoGeometria) resultadoGeometria.textContent = "Área y volumen se calculan al validar la calibración.";
    if (resultadoCalibracion) resultadoCalibracion.hidden = true;
    if (estadoCalibracion) estadoCalibracion.textContent = "";
  }
  function distancia3D(a, b) {
    return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
  }
  function seleccionarPuntoCalibracion(e) {
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) * canvas.width / rect.width;
    const y = (e.clientY - rect.top) * canvas.height / rect.height;
    let mejor = -1, mejorDistancia = Infinity;
    for (let i = 0; i < ultimoProyectado.length; i++) {
      const punto = ultimoProyectado[i];
      const d = Math.hypot(punto[0] - x, punto[1] - y);
      if (d < mejorDistancia) { mejorDistancia = d; mejor = i; }
    }
    if (mejor < 0 || mejorDistancia > Math.max(24, canvas.width * 0.035)) {
      if (estadoCalibracion) estadoCalibracion.textContent =
        "No se encontró un vértice suficientemente cerca. Acercá el zoom o rotá el modelo.";
      if (resultadoMedicion && modoMedicion) resultadoMedicion.textContent =
        "No se encontró un vértice cerca. Acercá el zoom o rotá el modelo.";
      return;
    }
    if (modoMedicion) {
      if (puntosMedicion.includes(mejor)) {
        if (resultadoMedicion) resultadoMedicion.textContent = "Elegí dos vértices diferentes.";
        return;
      }
      puntosMedicion.push(mejor);
      dibujar();
      if (puntosMedicion.length === 1) {
        if (resultadoMedicion) resultadoMedicion.textContent =
          "Primer punto seleccionado. Elegí el segundo extremo de la distancia.";
        return;
      }
      modoMedicion = false;
      const distancia = distancia3D(
        verticesOriginales[puntosMedicion[0]],
        verticesOriginales[puntosMedicion[1]]
      ) * escalaCalibradaMM;
      if (resultadoMedicion) resultadoMedicion.textContent =
        "Distancia aproximada: " + distancia.toFixed(2) +
        " mm. La precisión depende del escaneo y de la selección de los vértices.";
      return;
    }
    if (puntosCalibracion.includes(mejor)) {
      if (estadoCalibracion) estadoCalibracion.textContent =
        "Elegí un vértice diferente para cada extremo de referencia.";
      return;
    }
    puntosCalibracion.push(mejor);
    dibujar();
    if (puntosCalibracion.length < 4) {
      const instrucciones = [
        "Seleccioná el segundo extremo de la referencia 1.",
        "Seleccioná el primer extremo de la referencia 2.",
        "Seleccioná el segundo extremo de la referencia 2."
      ];
      if (estadoCalibracion) estadoCalibracion.textContent =
        "Punto " + puntosCalibracion.length + " de 4. " + instrucciones[puntosCalibracion.length - 1];
      return;
    }
    modoCalibracion = false;
    calcularCalibracion();
  }
  function calcularCalibracion() {
    const mm1 = Number(distanciaRef1?.value);
    const mm2 = Number(distanciaRef2?.value);
    const [a, b, c, d] = puntosCalibracion.map(i => verticesOriginales[i]);
    const medida1 = distancia3D(a, b);
    const medida2 = distancia3D(c, d);
    if (![mm1, mm2, medida1, medida2].every(Number.isFinite) ||
        mm1 <= 0 || mm2 <= 0 || medida1 <= 1e-12 || medida2 <= 1e-12) {
      if (estadoCalibracion) estadoCalibracion.textContent =
        "Las referencias no son válidas. Reiniciá la selección e ingresá distancias positivas.";
      return;
    }
    const escala1 = mm1 / medida1;
    const escala2 = mm2 / medida2;
    const escala = (escala1 + escala2) / 2;
    const discrepancia = Math.max(Math.abs(escala1 / escala - 1),
                                  Math.abs(escala2 / escala - 1));
    const discrepanciaPct = discrepancia * 100;
    if (discrepancia > 0.05) {
      if (estadoCalibracion) estadoCalibracion.textContent =
        "Calibración rechazada: las dos referencias difieren " +
        discrepanciaPct.toFixed(2) + "% (máximo permitido: 5%). Revisá los extremos y las medidas.";
      puntosCalibracion = [];
      dibujar();
      return;
    }
    escalaCalibradaMM = escala;
    if (iniciarMedicion) iniciarMedicion.disabled = false;
    if (resultadoMedicion) resultadoMedicion.textContent =
      "Escala calibrada. Podés seleccionar dos puntos para medir una distancia aproximada.";
    const mediciones = window.escaneo3D.calcularMedicionesMalla(
      verticesOriginales, carasOriginales, escala
    );
    if (resultadoGeometria) {
      resultadoGeometria.textContent =
        "Área superficial aproximada: " + mediciones.area_superficial_mm2.toFixed(2) +
        " mm². " + (mediciones.volumen_mm3 !== null
          ? "Volumen aproximado: " + mediciones.volumen_mm3.toFixed(2) + " mm³."
          : mediciones.componentes_conectados > 1
            ? "Volumen no calculado: la malla contiene varias componentes desconectadas."
            : "Volumen no calculado: la malla no está cerrada y orientada de forma consistente.") +
        " " + mediciones.advertencia;
    }
    const informe = {
      estado: "escala_global_consistente",
      mediciones_geometricas: mediciones,
      unidad: "mm",
      escala_mm_por_unidad_original: escala,
      referencias: [
        {distancia_real_mm: mm1, distancia_modelo_unidades: medida1, factor: escala1},
        {distancia_real_mm: mm2, distancia_modelo_unidades: medida2, factor: escala2}
      ],
      discrepancia_relativa_entre_referencias_pct: discrepanciaPct,
      tolerancia_relativa_pct: 5,
      advertencia: "La calibración solo fija la escala global. No corrige deriva entre cámaras, deformaciones, errores de selección ni autointersecciones. Verificá con una tercera medida física independiente antes de fabricar piezas."
    };
    const lineas = [
      "# ESCANEO 3D · OBJ calibrado con dos referencias físicas",
      "# Unidad: milímetros; escala global validada por consistencia relativa.",
      ...verticesOriginales.map(p => "v " + p.map(x => (x * escala).toPrecision(12)).join(" ")),
      ...carasOriginales.map(face => "f " + face.map(i => i + 1).join(" "))
    ];
    const blobMalla = new Blob([lineas.join("\n") + "\n"], {type:"text/plain;charset=utf-8"});
    let blobSTL = null, errorSTL = null;
    try { blobSTL = new Blob([window.escaneo3D.crearSTLCalibrado(verticesOriginales, carasOriginales, escala)], {type:"model/stl"}); }
    catch (error) { errorSTL = error.message; }
    informe.stl_exportado = Boolean(blobSTL);
    if (errorSTL) informe.motivo_sin_stl = errorSTL;
    const blobInforme = new Blob([JSON.stringify(informe, null, 2)], {type:"application/json"});
    const urlMalla = URL.createObjectURL(blobMalla);
    const urlInforme = URL.createObjectURL(blobInforme);
    urlsCalibracion.push(urlMalla, urlInforme);
    if (descargarMallaMM) descargarMallaMM.href = urlMalla;
    if (descargarInformeMM) descargarInformeMM.href = urlInforme;
    if (descargarSTLMM) {
      if (blobSTL) {
        const urlSTL = URL.createObjectURL(blobSTL);
        urlsCalibracion.push(urlSTL);
        descargarSTLMM.href = urlSTL;
        descargarSTLMM.hidden = false;
      } else {
        descargarSTLMM.hidden = true;
      }
    }
    if (resultadoCalibracion) resultadoCalibracion.hidden = false;
    if (estadoCalibracion) estadoCalibracion.textContent =
      "Escala global coherente. Discrepancia entre referencias: " +
      discrepanciaPct.toFixed(2) + "%. Se generó OBJ en mm" +
      (blobSTL ? " y STL en mm." : ". No se generó STL: " + errorSTL) +
      " Verificá una tercera dimensión y la integridad de la malla antes de imprimir.";
  }
  iniciarMedicion?.addEventListener("click", () => {
    if (!(escalaCalibradaMM > 0)) {
      if (resultadoMedicion) resultadoMedicion.textContent =
        "Primero calibrá la escala con dos referencias físicas.";
      return;
    }
    puntosMedicion = [];
    modoMedicion = true;
    if (resultadoMedicion) resultadoMedicion.textContent =
      "Modo medición activo. Elegí el primer extremo en el modelo.";
  });
  iniciarCalibracion?.addEventListener("click", () => {
    const mm1 = Number(distanciaRef1?.value);
    const mm2 = Number(distanciaRef2?.value);
    if (!verticesOriginales.length) {
      if (estadoCalibracion) estadoCalibracion.textContent = "Primero abrí una malla OBJ.";
      return;
    }
    if (!(mm1 > 0) || !(mm2 > 0) || !Number.isFinite(mm1) || !Number.isFinite(mm2)) {
      if (estadoCalibracion) estadoCalibracion.textContent = "Ingresá dos distancias reales positivas en milímetros.";
      return;
    }
    limpiarDescargasCalibracion();
    puntosCalibracion = [];
    modoCalibracion = true;
    if (estadoCalibracion) estadoCalibracion.textContent =
      "Modo selección activo. Hacé clic sobre el primer extremo de la referencia 1.";
  });
  canvas.addEventListener("pointerdown", e => {
    if (modoCalibracion || modoMedicion) {
      seleccionarPuntoCalibracion(e);
      return;
    }
    arrastrando = true; px = e.clientX; py = e.clientY;
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener("pointermove", e => {
    if (!arrastrando) return;
    rotY += (e.clientX - px) * 0.008;
    rotX = Math.max(-1.5, Math.min(1.5, rotX + (e.clientY - py) * 0.008));
    px = e.clientX; py = e.clientY; dibujar();
  });
  canvas.addEventListener("pointerup", () => { arrastrando = false; });
  canvas.addEventListener("pointercancel", () => { arrastrando = false; });
  canvas.addEventListener("wheel", e => {
    e.preventDefault(); zoom = Math.max(0.35, Math.min(3.5, zoom * (e.deltaY < 0 ? 1.1 : 0.9))); dibujar();
  }, {passive:false});
  canvas.addEventListener("dblclick", () => { rotX = -0.35; rotY = 0.65; zoom = 1; dibujar(); });
  canvas.addEventListener("keydown", e => {
    const paso = 0.12;
    if (e.key === "ArrowLeft") rotY -= paso;
    else if (e.key === "ArrowRight") rotY += paso;
    else if (e.key === "ArrowUp") rotX = Math.max(-1.5, rotX - paso);
    else if (e.key === "ArrowDown") rotX = Math.min(1.5, rotX + paso);
    else if (e.key === "+" || e.key === "=") zoom = Math.min(3.5, zoom * 1.1);
    else if (e.key === "-") zoom = Math.max(0.35, zoom * 0.9);
    else if (e.key === "Home") { rotX = -0.35; rotY = 0.65; zoom = 1; }
    else return;
    e.preventDefault(); dibujar();
  });
  cerrar.addEventListener("click", () => { panel.hidden = true; });
  window.addEventListener("resize", dibujar);
  window.visorEscaneo3D = {abrir};
})();