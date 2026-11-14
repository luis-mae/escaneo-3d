"use strict";
const assert = require("node:assert/strict");
global.window = {};
require("../web/stl_calibrado.js");

const vertices = [[0,0,0],[1,0,0],[0,1,0]];
const buffer = window.escaneo3D.crearSTLCalibrado(vertices, [[0,1,2]], 10);
assert.equal(buffer.byteLength, 134);
const vista = new DataView(buffer);
assert.equal(vista.getUint32(80, true), 1);
assert.deepEqual(
  [vista.getFloat32(84, true), vista.getFloat32(88, true), vista.getFloat32(92, true)],
  [0,0,1]
);
assert.deepEqual(
  [vista.getFloat32(96, true), vista.getFloat32(100, true), vista.getFloat32(104, true)],
  [0,0,0]
);
assert.deepEqual(
  [vista.getFloat32(108, true), vista.getFloat32(112, true), vista.getFloat32(116, true)],
  [10,0,0]
);
assert.throws(() => window.escaneo3D.crearSTLCalibrado(vertices, [[0,0,2]], 10), /degenerados/);
assert.throws(() => window.escaneo3D.crearSTLCalibrado(vertices, [[0,1,4]], 10), /Índices/);
assert.throws(() => window.escaneo3D.crearSTLCalibrado(vertices, [[0,1,2]], 0), /inválida/);
console.log("STL calibrado: pruebas OK");
