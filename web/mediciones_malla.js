"use strict";
(() => {
  const raiz = window.escaneo3D = window.escaneo3D || {};

  raiz.calcularMedicionesMalla = function(vertices, caras, escala) {
    if (!Array.isArray(vertices) || !Array.isArray(caras) || !caras.length ||
        !Number.isFinite(escala) || escala <= 0) {
      throw new Error("Geometría o escala inválida para medir.");
    }
    const aristas = new Map();
    let area = 0;
    const volumenPorCara = [];
    let degenerados = 0;
    for (let indiceCara = 0; indiceCara < caras.length; indiceCara++) {
      const cara = caras[indiceCara];
      if (!Array.isArray(cara) || cara.length !== 3 ||
          cara.some(i => !Number.isInteger(i) || i < 0 || i >= vertices.length)) {
        throw new Error("Índices de cara inválidos.");
      }
      const puntos = cara.map(i => {
        const p = vertices[i];
        if (!Array.isArray(p) || p.length !== 3 || p.some(x => !Number.isFinite(x))) {
          throw new Error("Vértice inválido.");
        }
        return p.map(x => x * escala);
      });
      const [a,b,c] = puntos;
      const u = [b[0]-a[0], b[1]-a[1], b[2]-a[2]];
      const v = [c[0]-a[0], c[1]-a[1], c[2]-a[2]];
      const cruz = [
        u[1]*v[2]-u[2]*v[1],
        u[2]*v[0]-u[0]*v[2],
        u[0]*v[1]-u[1]*v[0]
      ];
      const dobleArea = Math.hypot(...cruz);
      if (!(dobleArea > 1e-12)) degenerados++;
      area += dobleArea / 2;
      const volumenCara = (
        a[0] * (b[1]*c[2]-b[2]*c[1]) +
        a[1] * (b[2]*c[0]-b[0]*c[2]) +
        a[2] * (b[0]*c[1]-b[1]*c[0])
      ) / 6;
      volumenPorCara.push(volumenCara);
      for (const [x,y] of [[cara[0],cara[1]],[cara[1],cara[2]],[cara[2],cara[0]]]) {
        const clave = x < y ? x + ":" + y : y + ":" + x;
        const direccion = x < y ? 1 : -1;
        const entrada = aristas.get(clave) || {cantidad:0, sumaDirecciones:0, caras:[]};
        entrada.cantidad++;
        entrada.sumaDirecciones += direccion;
        entrada.caras.push(indiceCara);
        aristas.set(clave, entrada);
      }
    }
    let abiertas = 0, noManifold = 0, orientacionInconsistente = 0;
    for (const entrada of aristas.values()) {
      if (entrada.cantidad === 1) abiertas++;
      else if (entrada.cantidad > 2) noManifold++;
      else if (entrada.cantidad === 2 && entrada.sumaDirecciones !== 0) orientacionInconsistente++;
    }
    const cerradaOrientada = aristas.size > 0 && abiertas === 0 &&
      noManifold === 0 && orientacionInconsistente === 0 && degenerados === 0;
    let volumenTotal = 0;
    if (cerradaOrientada) {
      const adyacencia = Array.from({length: caras.length}, () => []);
      for (const entrada of aristas.values()) {
        if (entrada.cantidad === 2) {
          const [a, b] = entrada.caras;
          adyacencia[a].push(b);
          adyacencia[b].push(a);
        }
      }
      const visitadas = new Set();
      for (let inicio = 0; inicio < caras.length; inicio++) {
        if (visitadas.has(inicio)) continue;
        let sumaComponente = 0;
        const cola = [inicio];
        visitadas.add(inicio);
        while (cola.length) {
          const actual = cola.pop();
          sumaComponente += volumenPorCara[actual];
          for (const vecino of adyacencia[actual]) {
            if (!visitadas.has(vecino)) {
              visitadas.add(vecino);
              cola.push(vecino);
            }
          }
        }
        volumenTotal += Math.abs(sumaComponente);
      }
    }
    return {
      area_superficial_mm2: area,
      volumen_mm3: cerradaOrientada ? volumenTotal : null,
      malla_cerrada_orientada: cerradaOrientada,
      aristas_abiertas: abiertas,
      aristas_no_manifold: noManifold,
      aristas_con_orientacion_inconsistente: orientacionInconsistente,
      triangulos_degenerados: degenerados,
      advertencia: "Medición geométrica sobre la malla; no incluye incertidumbre metrológica ni detecta autointersecciones."
    };
  };
})();
