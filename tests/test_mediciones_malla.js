"use strict";
const assert = require("node:assert/strict");
global.window = {};
require("../web/mediciones_malla.js");

const vertices = [[0,0,0],[1,0,0],[0,1,0],[0,0,1]];
const tetra = [[0,2,1],[0,1,3],[0,3,2],[1,2,3]];
const medicion = window.escaneo3D.calcularMedicionesMalla(vertices, tetra, 10);
assert.equal(medicion.malla_cerrada_orientada, true);
assert.equal(medicion.aristas_abiertas, 0);
assert.ok(Math.abs(medicion.volumen_mm3 - 1000/6) < 1e-6);
assert.ok(Math.abs(medicion.area_superficial_mm2 - (150 + 50*Math.sqrt(3))) < 1e-6);

const verticesDobles = vertices.concat(vertices.map(p => [p[0]+3,p[1],p[2]]));
const tetraInvertido = tetra.map(cara => cara.slice().reverse().map(i => i + 4));
const dosComponentes = window.escaneo3D.calcularMedicionesMalla(
  verticesDobles, tetra.concat(tetraInvertido), 10
);
assert.equal(dosComponentes.volumen_mm3, null);
assert.equal(dosComponentes.componentes_conectados, 2);

const abierta = window.escaneo3D.calcularMedicionesMalla(vertices, [[0,1,2]], 10);
assert.equal(abierta.malla_cerrada_orientada, false);
assert.equal(abierta.volumen_mm3, null);
assert.equal(abierta.aristas_abiertas, 3);

assert.throws(
  () => window.escaneo3D.calcularMedicionesMalla(vertices, [[0,1,8]], 10),
  /Índices/
);
assert.throws(
  () => window.escaneo3D.calcularMedicionesMalla(vertices, [[0,1,2]], 1e308),
  /fuera de rango/
);

console.log("Mediciones geométricas: pruebas OK");
