"use strict";
(() => {
  const panel = document.getElementById("visor3d");
  const canvas = document.getElementById("lienzo-3d");
  const estado = document.getElementById("estado-visor");
  const cerrar = document.getElementById("cerrar-visor");
  if (!panel || !canvas) return;
  const ctx = canvas.getContext("2d");
  let vertices = [];
  let caras = [];
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
    const min = [Infinity, Infinity, Infinity];
    const max = [-Infinity, -Infinity, -Infinity];
    for (const p of v) for (let k = 0; k < 3; k++) {
      if (p[k] < min[k]) min[k] = p[k];
      if (p[k] > max[k]) max[k] = p[k];
    }
    centro = min.map((x, k) => (x + max[k]) / 2);
    const radio = Math.max(max[0]-min[0], max[1]-min[1], max[2]-min[2]);
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
        f.length.toLocaleString("es-AR") + " caras.");
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
      vertices = []; caras = []; dibujar(); mensaje(e.message);
    }
  }
  canvas.addEventListener("pointerdown", e => {
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
  cerrar.addEventListener("click", () => { panel.hidden = true; });
  window.addEventListener("resize", dibujar);
  window.visorEscaneo3D = {abrir};
})();