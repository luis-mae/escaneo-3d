"use strict";
(() => {
  const raiz = window.escaneo3D = window.escaneo3D || {};

  raiz.crearSTLCalibrado = function(vertices, caras, escala) {
    if (!Array.isArray(vertices) || !Array.isArray(caras) || !caras.length ||
        !Number.isFinite(escala) || escala <= 0) {
      throw new Error("Geometría o escala inválida para STL.");
    }
    if (caras.length > 0xffffffff) throw new Error("Cantidad de triángulos no admitida para STL.");
    const buffer = new ArrayBuffer(84 + caras.length * 50);
    const vista = new DataView(buffer);
    const encabezado = "ESCANEO 3D - CALIBRATED MM";
    for (let i = 0; i < Math.min(80, encabezado.length); i++) {
      vista.setUint8(i, encabezado.charCodeAt(i));
    }
    vista.setUint32(80, caras.length, true);
    let offset = 84;
    for (const cara of caras) {
      if (!Array.isArray(cara) || cara.length !== 3 ||
          cara.some(indice => !Number.isInteger(indice) || indice < 0 || indice >= vertices.length)) {
        throw new Error("Índices de triángulo inválidos para STL.");
      }
      const puntos = cara.map(indice => {
        const p = vertices[indice];
        if (!Array.isArray(p) || p.length !== 3 || p.some(x => !Number.isFinite(x))) {
          throw new Error("Vértice inválido para STL.");
        }
        return p.map(valor => valor * escala);
      });
      const [a, b, c] = puntos;
      const u = [b[0]-a[0], b[1]-a[1], b[2]-a[2]];
      const v = [c[0]-a[0], c[1]-a[1], c[2]-a[2]];
      const normal = [
        u[1]*v[2]-u[2]*v[1],
        u[2]*v[0]-u[0]*v[2],
        u[0]*v[1]-u[1]*v[0]
      ];
      const magnitud = Math.hypot(...normal);
      if (!(magnitud > 1e-12) || !Number.isFinite(magnitud)) {
        throw new Error("La malla contiene triángulos degenerados; no se generó STL.");
      }
      const valores = [...normal.map(x => x/magnitud), ...a, ...b, ...c];
      if (valores.some(x => !Number.isFinite(Math.fround(x)))) {
        throw new Error("Las coordenadas exceden el rango numérico STL.");
      }
      for (const valor of valores) {
        vista.setFloat32(offset, valor, true);
        offset += 4;
      }
      vista.setUint16(offset, 0, true);
      offset += 2;
    }
    return buffer;
  };
})();
