const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const listeners = {};
const panel = {hidden: true, scrollIntoView() {}};
const estado = {textContent: ""};
const cerrar = {addEventListener(name, fn) { this[name] = fn; }};
const calls = {fill: 0, stroke: 0};
const ctx = {
  clearRect() {}, fillRect() {}, beginPath() {}, moveTo() {}, lineTo() {},
  closePath() {}, fill() { calls.fill++; }, stroke() { calls.stroke++; }
};
const canvas = {
  width: 900, height: 600, clientWidth: 900, clientHeight: 600,
  getContext() { return ctx; },
  addEventListener(name, fn) { listeners[name] = fn; },
  setPointerCapture() {}
};
global.document = {
  getElementById(id) {
    return {"visor3d": panel, "lienzo-3d": canvas,
      "estado-visor": estado, "cerrar-visor": cerrar}[id] || null;
  }
};
global.window = {devicePixelRatio: 1, addEventListener() {}};
global.fetch = async () => ({
  ok: true,
  text: async () => [
    "v 0 0 0", "v 1 0 0", "v 0 1 0", "v 0 0 1",
    "f 1 3 2", "f 1 2 4", "f 1 4 3", "f 2 3 4"
  ].join("\n")
});

const fuente = fs.readFileSync("web/visor.js", "utf8");
vm.runInThisContext(fuente, {filename: "web/visor.js"});

(async () => {
  await window.visorEscaneo3D.abrir("/malla");
  assert.equal(panel.hidden, false);
  assert.match(estado.textContent, /4 vértices/);
  assert.match(estado.textContent, /4 caras/);
  assert.ok(calls.fill > 0);
  assert.ok(calls.stroke > 0);

  listeners.pointerdown({clientX: 10, clientY: 10, pointerId: 1});
  listeners.pointermove({clientX: 30, clientY: 25});
  listeners.pointerup();
  listeners.wheel({preventDefault() {}, deltaY: -100});
  listeners.dblclick();
  const antesTeclado = calls.fill;
  listeners.keydown({key: "ArrowRight", preventDefault() {}});
  listeners.keydown({key: "+", preventDefault() {}});
  listeners.keydown({key: "Home", preventDefault() {}});
  assert.ok(calls.fill > antesTeclado);
  global.fetch = async () => ({
    ok: true,
    text: async () => ["v 0 0 0", "v 1 0 0", "v 1 1 0", "v 0 1 0", "f -4 -3 -2 -1"].join("\n")
  });
  await window.visorEscaneo3D.abrir("/quad.obj");
  assert.match(estado.textContent, /2 caras/);
  cerrar.click();
  assert.equal(panel.hidden, true);

  global.fetch = async () => ({ok: true, text: async () => "v 0 0 0\nv 1 0 0"});
  await window.visorEscaneo3D.abrir("/obj-invalido");
  assert.match(estado.textContent, /no contiene una malla triangular válida/);
  console.log("Visor 3D: pruebas OK");
})().catch(error => { console.error(error); process.exitCode = 1; });
