// copied from sketch_claude/static/app.js by website/scripts/sync_sketch_app.py: edit that file, then re-run
import "/sketch-app/web-shim.js";
// Dome Sketch (sketch-claude): a SketchUp-style modeller for the framed-panel dome.
// The geometry comes from the server (sketch_claude.model): every stick, board and fitting is a
// solid with its own figures. This page draws it the way SketchUp does -- flat faces, inked
// edges, sun shadows -- and adds the tools a builder reaches for: select, orbit, pan, tape
// measure, section plane, scenes, tags, an outliner, entity info and the cut list.

import * as THREE from "three";
import { OrbitControls } from "/sketch-app/vendor/OrbitControls.js";

const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const IN = 0.0254;

// ---------------------------------------------------------------- units
function mm(m) { return `${Math.round(m * 1000).toLocaleString()} mm`; }
function ftin(m) {
  let s = Math.round(m / IN * 16), neg = s < 0; s = Math.abs(s);
  let inch = Math.floor(s / 16), frac = s % 16, ft = Math.floor(inch / 12); inch %= 12;
  let f = "";
  if (frac) { let g = gcd(frac, 16); f = `${inch || ft ? "-" : ""}${frac / g}/${16 / g}`; }
  return (neg ? "-" : "") + (ft ? `${ft}' ` : "") + `${inch || f ? inch || "" : 0}${f}"`;
}
function gcd(a, b) { return b ? gcd(b, a % b) : a; }
function both(m) { return `${mm(m)} (${ftin(m)})`; }
function deg(a, n = 1) { return `${a.toFixed(n)}°`; }

// ---------------------------------------------------------------- renderer
const canvas = $("#gl");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.localClippingEnabled = true;
const scene = new THREE.Scene();
const persp = new THREE.PerspectiveCamera(35, 1, 0.05, 400);
const ortho = new THREE.OrthographicCamera(-5, 5, 5, -5, -200, 400);
let camera = persp;
for (const c of [persp, ortho]) c.up.set(0, 0, 1);
persp.position.set(9, -12, 6);
const controls = new OrbitControls(persp, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.12;
controls.screenSpacePanning = true;

const hemi = new THREE.HemisphereLight(0xf4f1ea, 0x8d8576, 1.25);
hemi.position.set(0, 0, 1);
scene.add(hemi);
const sun = new THREE.DirectionalLight(0xfff6e8, 1.6);
sun.castShadow = true;
sun.shadow.mapSize.set(4096, 4096);
sun.shadow.bias = -0.0004;
sun.shadow.normalBias = 0.02;
const sc = sun.shadow.camera;
sc.left = -9; sc.right = 9; sc.top = 9; sc.bottom = -9; sc.near = 0.5; sc.far = 60;
scene.add(sun, sun.target);
const lamp = new THREE.PointLight(0xffd59a, 5, 9, 1.4);      // the pendant over the room
lamp.position.set(0, -0.05, 1.8);
scene.add(lamp);
const world = new THREE.Group();
scene.add(world);
const overlay = new THREE.Group();          // tape measure lines, section plane
scene.add(overlay);

function skyTexture(top, bottom) {
  const c = document.createElement("canvas"); c.width = 2; c.height = 256;
  const g = c.getContext("2d"), grad = g.createLinearGradient(0, 0, 0, 256);
  grad.addColorStop(0, top); grad.addColorStop(1, bottom);
  g.fillStyle = grad; g.fillRect(0, 0, 2, 256);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
const SKY = { sketch: skyTexture("#c9dbee", "#f4f3ef"), plain: skyTexture("#ffffff", "#f1f0ec") };

// ---------------------------------------------------------------- state
const S = {
  spec: null, data: null, pieces: new Map(), groups: new Map(),
  selected: new Set(), hidden: new Set(), tagsOff: new Set(["site"].filter(() => false)),
  style: "sketch", tool: "select", explode: 0, step: 999, door: 0, sunAz: 215,
  section: { on: false, axis: "z", t: 0.45 }, tape: null, dims: [], defaults: null, scene: "Exterior",
};
const TAGS = [["frame", "Frame"], ["skin", "Skin"], ["glass", "Glazing"], ["base", "Base sections"], ["door", "Door"],
              ["deck", "Deck"], ["furniture", "Furniture"], ["person", "Person"], ["site", "Ground"]];

// ---------------------------------------------------------------- materials
const matCache = new Map();
function faceMat(key, mode) {
  const id = `${key}|${mode}`;
  if (matCache.has(id)) return matCache.get(id);
  const def = S.data.materials[key] || { color: "#cccccc" };
  const opacity = def.opacity ?? 1;
  let color = new THREE.Color(def.color), transparent = opacity < 1, op = opacity, emissive = new THREE.Color(0);
  if (mode === "mono" || mode === "hidden") { color = new THREE.Color(key === "glass" || key === "poly" ? "#d9e6ee" : "#f2f1ee"); }
  if (mode === "xray") { transparent = true; op = Math.min(op, 0.4); }
  if (mode === "sel") { color = new THREE.Color("#6f9ce8"); transparent = false; op = 1; emissive = new THREE.Color("#1d3f8a"); }
  if (def.emissive && mode !== "mono" && mode !== "hidden") emissive = new THREE.Color(def.color).multiplyScalar(0.9);
  const Mat = mode === "hidden" ? THREE.MeshBasicMaterial : THREE.MeshLambertMaterial;
  const m = new Mat({ color, transparent, opacity: op, side: THREE.DoubleSide, polygonOffset: true,
                      polygonOffsetFactor: 1, polygonOffsetUnits: 1, depthWrite: !transparent || mode === "sel" });
  if (m.emissive) m.emissive = emissive;
  matCache.set(id, m);
  return m;
}
const edgeMat = new THREE.LineBasicMaterial({ color: 0x1d1b18 });
const edgeSoft = new THREE.LineBasicMaterial({ color: 0x1d1b18, transparent: true, opacity: 0.35 });
const edgeSel = new THREE.LineBasicMaterial({ color: 0x1846b8 });

// ---------------------------------------------------------------- loading a model
function decode(b64, Type) {
  const bin = atob(b64), buf = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
  return new Type(buf.buffer);
}

async function api(path, body) {
  const r = await fetch(path, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const j = await r.json();
  if (!r.ok) throw new Error(j.error || r.statusText);
  return j;
}

function makePieceGroup(p) {
    const v = decode(p.v, Float32Array), t = decode(p.t, Uint32Array), e = decode(p.e, Uint32Array);
    const g = new THREE.Group();
    g.userData.piece = p;
    if (t.length) {
      const pos = new Float32Array(t.length * 3);
      for (let i = 0; i < t.length; i++) { pos[i * 3] = v[t[i] * 3]; pos[i * 3 + 1] = v[t[i] * 3 + 1]; pos[i * 3 + 2] = v[t[i] * 3 + 2]; }
      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
      geo.computeVertexNormals();
      const mesh = new THREE.Mesh(geo, faceMat(p.material, "base"));
      mesh.castShadow = p.tag !== "site" && p.tag !== "glass";
      mesh.receiveShadow = true;
      mesh.userData.piece = p;
      g.add(mesh); g.userData.mesh = mesh;
    }
    if (e.length && p.tag !== "site") {
      const lp = new Float32Array(e.length * 3);
      for (let i = 0; i < e.length; i++) { lp[i * 3] = v[e[i] * 3]; lp[i * 3 + 1] = v[e[i] * 3 + 1]; lp[i * 3 + 2] = v[e[i] * 3 + 2]; }
      const lg = new THREE.BufferGeometry();
      lg.setAttribute("position", new THREE.BufferAttribute(lp, 3));
      const lines = new THREE.LineSegments(lg, p.tag === "skin" || p.tag === "glass" ? edgeSoft : edgeMat);
      g.add(lines); g.userData.lines = lines;
    }
  return g;
}

let buildToken = 0;
async function load(spec, keepView = false) {
  const token = ++buildToken;
  $("#busy").hidden = false;
  try {
    const data = await api("/api/model", { spec });
    if (token !== buildToken) return;
    S.data = data; S.spec = data.spec;
    matCache.clear();
    world.clear();
    S.pieces.clear(); S.groups.clear(); S.selected.clear();
    S.panelCls = new Map(data.pieces.filter((p) => p.tag === "frame").map((p) => [p.group, p.info.cls]));
    for (const p of data.pieces) {
      const g = makePieceGroup(p);
      g.matrixAutoUpdate = false;
      world.add(g);
      S.pieces.set(p.id, g);
      const cat = category(p);
      if (!S.groups.has(cat)) S.groups.set(cat, []);
      S.groups.get(cat).push(p.id);
    }
    $("#step").max = data.max_step;
    if (S.step > data.max_step) S.step = data.max_step;
    $("#step").value = S.step;
    applyStyle(); applyTransforms(); applyVisibility();
    renderSummary(); renderOutliner(); renderCutlist(); renderInfo();
    if (!keepView) zoomExtents(false);
    placeSun();
  } catch (err) {
    toast(err.message);
  } finally {
    if (token === buildToken) $("#busy").hidden = true;
  }
}

function category(p) {
  if (p.tag === "frame") {
    const c = p.info.cls;
    return c === "partial" ? "Partial panels" : `Panels ${c} (${(S.data.tables.classes.find((k) => k.name === c) || {}).kind || ""})`;
  }
  return { skin: "Skin", glass: "Windows and skylight", base: "Base sections", door: p.group === "door-leaf" ? "Door leaf" : "Door frame",
           deck: "Deck and porch", furniture: "Furniture", person: "Person", site: "Ground" }[p.tag] || p.tag;
}

// ---------------------------------------------------------------- transforms: explode, door swing
function applyTransforms() {
  const d = S.data.tables.door;
  const hinge = d ? new THREE.Vector3(-d.W / 2, d.y_post, 0) : null;
  const rot = new THREE.Matrix4(), tr = new THREE.Matrix4(), back = new THREE.Matrix4(), m = new THREE.Matrix4();
  for (const g of S.pieces.values()) {
    const p = g.userData.piece;
    m.identity();
    if (S.explode) m.makeTranslation(p.explode[0] * S.explode, p.explode[1] * S.explode, p.explode[2] * S.explode);
    if (p.group === "door-leaf" && hinge && S.door) {
      tr.makeTranslation(hinge.x, hinge.y, 0); rot.makeRotationZ(-S.door * Math.PI / 180); back.makeTranslation(-hinge.x, -hinge.y, 0);
      m.multiply(tr).multiply(rot).multiply(back);
    }
    g.matrix.copy(m);
    g.matrixWorldNeedsUpdate = true;
  }
}

// ---------------------------------------------------------------- visibility and style
function applyVisibility() {
  for (const g of S.pieces.values()) {
    const p = g.userData.piece;
    g.visible = !S.tagsOff.has(p.tag) && !S.hidden.has(p.id) && p.step <= S.step;
  }
  $("#step-v").textContent = S.step >= S.data.max_step ? "all" : String(S.step);
}

function applyStyle() {
  const st = S.style;
  for (const g of S.pieces.values()) {
    const p = g.userData.piece, sel = S.selected.has(p.id);
    if (g.userData.mesh) {
      const cls = S.colour && (p.tag === "skin" || p.tag === "glass") ? S.panelCls.get(p.group) : null;
      g.userData.mesh.material = sel ? faceMat(p.material, "sel") : cls ? classMat(cls)
        : faceMat(p.material, st === "shaded" || st === "wire" || st === "sketch" ? "base" : st);
      g.userData.mesh.visible = st !== "wire" || p.tag === "site";
    }
    if (g.userData.lines) {
      g.userData.lines.visible = st !== "shaded";
      g.userData.lines.material = sel ? edgeSel : (p.tag === "skin" || p.tag === "glass") ? edgeSoft : edgeMat;
    }
  }
  scene.background = st === "hidden" || st === "mono" ? SKY.plain : SKY.sketch;
  hemi.intensity = st === "hidden" ? 2.2 : 1.25;
  sun.castShadow = $("#shadows").checked && st !== "hidden" && st !== "xray";
  renderer.shadowMap.needsUpdate = true;
}

// ---------------------------------------------------------------- the sun
function placeSun() {
  const a = S.sunAz * Math.PI / 180, el = 42 * Math.PI / 180, r = 25;
  sun.position.set(Math.cos(a) * Math.cos(el) * r, Math.sin(a) * Math.cos(el) * r, Math.sin(el) * r);
  sun.target.position.set(0, 0, 1);
}

// ---------------------------------------------------------------- cameras and views
function bounds(onlyVisible = true) {
  const box = new THREE.Box3();
  for (const g of S.pieces.values()) {
    const p = g.userData.piece;
    if (p.tag === "site" || (onlyVisible && !g.visible)) continue;
    box.expandByObject(g);
  }
  if (box.isEmpty()) box.set(new THREE.Vector3(-3, -3, 0), new THREE.Vector3(3, 3, 3));
  return box;
}

let anim = null;
function flyTo(pos, target, ms = 550) {
  const p0 = camera.position.clone(), t0 = controls.target.clone(), start = performance.now();
  anim = (now) => {
    const k = Math.min(1, (now - start) / ms), e = k * k * (3 - 2 * k);
    camera.position.lerpVectors(p0, pos, e);
    controls.target.lerpVectors(t0, target, e);
    if (camera === ortho) syncOrtho();
    if (k >= 1) anim = null;
  };
}

function zoomExtents(animate = true, dir = null) {
  const box = bounds(), c = box.getCenter(new THREE.Vector3()), r = box.getSize(new THREE.Vector3()).length() / 2;
  const d = (dir || camera.position.clone().sub(controls.target)).normalize();
  const dist = r / Math.tan((persp.fov * Math.PI / 180) / 2) * 0.82;
  const pos = c.clone().addScaledVector(d, dist);
  if (animate) flyTo(pos, c); else { camera.position.copy(pos); controls.target.copy(c); }
}

function view(name) {
  const dirs = { iso: [0.75, -1, 0.6], top: [0.0001, -0.0001, 1], front: [0, -1, 0.001], back: [0, 1, 0.001],
                 right: [1, 0, 0.001], left: [-1, 0, 0.001] };
  zoomExtents(true, new THREE.Vector3(...dirs[name]));
}

function setProjection(parallel) {
  const pos = camera.position.clone(), tgt = controls.target.clone();
  camera = parallel ? ortho : persp;
  camera.position.copy(pos);
  controls.object = camera;
  controls.target.copy(tgt);
  $("#proj").textContent = parallel ? "Parallel" : "Persp";
  resize();
}

function syncOrtho() {
  const w = canvas.clientWidth, h = canvas.clientHeight || 1;
  const dist = camera.position.distanceTo(controls.target);
  const hh = dist * Math.tan((persp.fov * Math.PI / 180) / 2);
  ortho.top = hh; ortho.bottom = -hh; ortho.left = -hh * w / h; ortho.right = hh * w / h;
  ortho.updateProjectionMatrix();
}

function resize() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  renderer.setSize(w, h, false);
  persp.aspect = w / Math.max(h, 1); persp.updateProjectionMatrix();
  syncOrtho();
}
new ResizeObserver(resize).observe(canvas);

// ---------------------------------------------------------------- scenes
const SCENES = [
  { name: "Exterior", dir: [0.55, -1, 0.32], style: "sketch", off: [], explode: 0, step: 999, door: 60 },
  { name: "Frame", dir: [0.6, -1, 0.42], style: "sketch", off: ["skin", "glass", "furniture"], explode: 0, step: 999, door: 0 },
  { name: "Exploded", dir: [0.55, -1, 0.45], style: "sketch", off: ["skin", "glass", "furniture", "deck", "person"], explode: 110, step: 999, door: 0 },
  { name: "Panel map", dir: [0.0001, -0.0001, 1], style: "mono", off: ["furniture", "person", "deck"], explode: 0, step: 999, door: 0, colour: true },
  { name: "Build: base", dir: [0.6, -1, 0.6], style: "sketch", off: ["skin", "glass", "furniture", "person"], explode: 0, step: 1, door: 0 },
  { name: "Build: halfway", dir: [0.6, -1, 0.5], style: "sketch", off: ["skin", "glass", "furniture", "person"], explode: 0, step: 9, door: 0 },
  { name: "Door", dir: [0.45, -1, 0.15], style: "sketch", off: ["skin", "glass"], explode: 0, step: 999, door: 70, near: true },
  { name: "Floor plan", dir: [0.0001, -0.0001, 1], style: "sketch", off: ["person"], explode: 0, step: 999, door: 0, section: { axis: "z", t: 0.38 } },
  { name: "Inside", inside: true, style: "sketch", off: ["person"], explode: 0, step: 999, door: 40 },
];

function renderScenes() {
  $("#scenes").innerHTML = "";
  SCENES.forEach((sc, i) => {
    const b = document.createElement("button");
    b.textContent = sc.name; b.title = `Scene ${i + 1} (key ${i + 1})`;
    b.onclick = () => goScene(sc);
    b.className = sc.name === S.scene ? "on" : "";
    $("#scenes").append(b);
  });
}

function goScene(sc) {
  S.scene = sc.name;
  renderScenes();
  S.tagsOff = new Set(sc.off);
  S.explode = sc.explode / 100; $("#explode").value = sc.explode;
  S.step = Math.min(sc.step, S.data.max_step); $("#step").value = S.step;
  S.door = sc.door; $("#door").value = sc.door;
  S.style = sc.style; $("#style").value = sc.style;
  S.hidden.clear();
  S.colour = !!sc.colour;
  if (sc.section) { S.section = { on: true, ...sc.section }; } else S.section.on = false;
  syncSection();
  applyStyle(); applyTransforms(); applyVisibility(); renderTags();
  if (sc.inside) {
    const lm = S.data.landmarks;
    flyTo(new THREE.Vector3(0.35, lm.door[1] + 0.55, 1.45), new THREE.Vector3(-0.55, 0.9, 0.9));
    persp.fov = 62; persp.updateProjectionMatrix();
  } else {
    persp.fov = 35; persp.updateProjectionMatrix();
    if (sc.near && S.data.tables.door) {
      const d = S.data.tables.door;
      flyTo(new THREE.Vector3(1.6, d.y_post - 3.6, 1.6), new THREE.Vector3(0, d.y_post, 1.0));
    } else zoomExtents(true, new THREE.Vector3(...sc.dir));
  }
}

const CLASS_COLOURS = ["#e3a64b", "#7fb2d6", "#9cc27a", "#d98b8b", "#b49ad6", "#e0cf6a"];
function classMat(cls) {
  const names = S.data.tables.classes.map((c) => c.name);
  const col = cls === "partial" ? "#c9c3b8" : CLASS_COLOURS[Math.max(0, names.indexOf(cls)) % CLASS_COLOURS.length];
  const id = `class|${col}`;
  if (!matCache.has(id)) matCache.set(id, new THREE.MeshLambertMaterial({ color: col, side: THREE.DoubleSide, polygonOffset: true,
                                                                          polygonOffsetFactor: 1, polygonOffsetUnits: 1 }));
  return matCache.get(id);
}

// ---------------------------------------------------------------- section plane
const clip = new THREE.Plane(new THREE.Vector3(0, 0, -1), 1.2);
function syncSection() {
  $("#sec-wrap").hidden = !S.section.on;
  $$('[data-tool="section"]').forEach((b) => b.classList.toggle("on", S.section.on));
  if (!S.section.on) { renderer.clippingPlanes = []; return; }
  const box = bounds(false), lo = box.min, hi = box.max, t = S.section.t, ax = S.section.axis;
  $("#sec-axis").value = ax; $("#section").value = Math.round(t * 100);
  if (ax === "z") clip.set(new THREE.Vector3(0, 0, -1), lo.z + (hi.z - lo.z) * t);
  if (ax === "y") clip.set(new THREE.Vector3(0, 1, 0), -(lo.y + (hi.y - lo.y) * t));
  if (ax === "x") clip.set(new THREE.Vector3(1, 0, 0), -(lo.x + (hi.x - lo.x) * t));
  renderer.clippingPlanes = [clip];
}

// ---------------------------------------------------------------- picking
const ray = new THREE.Raycaster();
function pick(ev) {
  const r = canvas.getBoundingClientRect();
  const ndc = new THREE.Vector2(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
  ray.setFromCamera(ndc, camera);
  const meshes = [];
  for (const g of S.pieces.values()) if (g.visible && g.userData.mesh && g.userData.mesh.visible && g.userData.piece.tag !== "site") meshes.push(g.userData.mesh);
  const hits = ray.intersectObjects(meshes, false).filter((h) => !S.section.on || clip.distanceToPoint(h.point) >= 0);
  return hits[0] || null;
}

function snapPoint(hit, ev) {
  // the nearest corner of the face that was hit, if it is within 12 px on screen
  const r = canvas.getBoundingClientRect();
  const pos = hit.object.geometry.attributes.position, m = hit.object.matrixWorld;
  let best = null, bestD = 12;
  for (const k of [hit.face.a, hit.face.b, hit.face.c]) {
    const v = new THREE.Vector3().fromBufferAttribute(pos, k).applyMatrix4(m);
    const s = v.clone().project(camera);
    const px = (s.x + 1) / 2 * r.width + r.left, py = (1 - s.y) / 2 * r.height + r.top;
    const d = Math.hypot(px - ev.clientX, py - ev.clientY);
    if (d < bestD) { bestD = d; best = v; }
  }
  return best ? { p: best, snapped: true } : { p: hit.point.clone(), snapped: false };
}

function select(ids, add = false) {
  if (!add) S.selected.clear();
  for (const id of ids) S.selected.add(id);
  applyStyle();
  renderInfo();
  renderOutliner();
}

// ---------------------------------------------------------------- tape measure
let tapeLine = null;
function tapeStart(p) {
  S.tape = p;
  const geo = new THREE.BufferGeometry().setFromPoints([p, p.clone()]);
  tapeLine = new THREE.Line(geo, new THREE.LineDashedMaterial({ color: 0xc45e29, dashSize: 0.05, gapSize: 0.03, depthTest: false }));
  tapeLine.renderOrder = 10;
  overlay.add(tapeLine);
}
function tapeMove(p) {
  if (!S.tape || !tapeLine) return;
  tapeLine.geometry.setFromPoints([S.tape, p]);
  tapeLine.computeLineDistances();
  vcb("Length", both(S.tape.distanceTo(p)));
}
function tapeEnd(p) {
  if (!S.tape) return;
  const a = S.tape, d = a.distanceTo(p);
  tapeLine.geometry.setFromPoints([a, p]); tapeLine.computeLineDistances();
  const label = document.createElement("div");
  label.className = "dimlabel"; label.textContent = both(d);
  $("#labels").append(label);
  S.dims.push({ a, b: p.clone(), line: tapeLine, label });
  tapeLine = null; S.tape = null;
  vcb("Length", both(d));
}
function clearDims() {
  for (const d of S.dims) { overlay.remove(d.line); d.label.remove(); }
  S.dims = [];
  if (tapeLine) { overlay.remove(tapeLine); tapeLine = null; }
  S.tape = null;
}
function placeLabels() {
  const r = canvas.getBoundingClientRect();
  for (const d of S.dims) {
    const m = d.a.clone().add(d.b).multiplyScalar(0.5).project(camera);
    d.label.style.left = `${(m.x + 1) / 2 * r.width}px`;
    d.label.style.top = `${(1 - m.y) / 2 * r.height}px`;
    d.label.style.display = m.z < 1 ? "" : "none";
  }
}

function vcb(label, text) { $("#vcb-label").textContent = label; $("#vcb").textContent = text; }

// ---------------------------------------------------------------- tools
const HINTS = {
  select: "Select: click a piece; double-click selects its whole panel; Shift-click adds. Middle-drag orbits, right-drag pans, wheel zooms.",
  orbit: "Orbit: drag to turn round the model. Wheel zooms.",
  pan: "Pan: drag to slide the view.",
  tape: "Tape measure: click a start point, then an end point. Points snap to corners. Esc clears the measurements.",
  section: "Section plane: drag the Section slider; choose a level, front or side cut.",
};
function setTool(t) {
  if (t === "section") { S.section.on = !S.section.on; syncSection(); return; }
  S.tool = t;
  $$(".tools [data-tool]").forEach((b) => b.classList.toggle("on", b.dataset.tool === t || (b.dataset.tool === "section" && S.section.on)));
  controls.mouseButtons = { LEFT: t === "orbit" ? THREE.MOUSE.ROTATE : t === "pan" ? THREE.MOUSE.PAN : null,
                            MIDDLE: THREE.MOUSE.ROTATE, RIGHT: THREE.MOUSE.PAN };
  canvas.style.cursor = t === "tape" ? "crosshair" : t === "orbit" ? "grab" : t === "pan" ? "move" : "default";
  $("#hint").textContent = HINTS[t];
  if (t !== "tape" && tapeLine) { overlay.remove(tapeLine); tapeLine = null; S.tape = null; }
}

let down = null;
canvas.addEventListener("pointerdown", (ev) => { down = { x: ev.clientX, y: ev.clientY, b: ev.button }; });
canvas.addEventListener("pointerup", (ev) => {
  if (!down || down.b !== 0 || Math.hypot(ev.clientX - down.x, ev.clientY - down.y) > 4) { down = null; return; }
  down = null;
  const hit = pick(ev);
  if (S.tool === "select") {
    if (!hit) { select([]); return; }
    select([hit.object.userData.piece.id], ev.shiftKey);
  } else if (S.tool === "tape" && hit) {
    const { p } = snapPoint(hit, ev);
    if (!S.tape) tapeStart(p); else tapeEnd(p);
  }
});
canvas.addEventListener("dblclick", (ev) => {
  if (S.tool !== "select") return;
  const hit = pick(ev);
  if (!hit) return;
  const grp = hit.object.userData.piece.group;
  const ids = [...S.pieces.values()].map((g) => g.userData.piece).filter((p) => p.group === grp).map((p) => p.id);
  select(ids, ev.shiftKey);
});
canvas.addEventListener("pointermove", (ev) => {
  if (S.tool !== "tape" || !S.tape) return;
  const hit = pick(ev);
  if (hit) tapeMove(snapPoint(hit, ev).p);
});

window.addEventListener("keydown", (ev) => {
  if (ev.target.closest("input, select, textarea")) return;
  const k = ev.key.toLowerCase();
  if (k === " ") { setTool("select"); ev.preventDefault(); }
  else if (k === "o") setTool("orbit");
  else if (k === "h" && !ev.shiftKey) setTool("pan");
  else if (k === "t") setTool("tape");
  else if (k === "p") setTool("section");
  else if (k === "z" && ev.shiftKey) zoomExtents();
  else if (k === "escape") { clearDims(); select([]); }
  else if (k === "delete") hideSelected();
  else if (/^[1-9]$/.test(k) && SCENES[+k - 1]) goScene(SCENES[+k - 1]);
});

// ---------------------------------------------------------------- panels: summary, tags, outliner, info, cut list
function renderSummary() {
  const t = S.data.tables;
  const rows = [["Across the base", both(t.diameter_m)], ["Deck to top", both(t.height_m)], ["Floor", `${t.floor_m2.toFixed(1)} m² (${(t.floor_m2 * 10.7639).toFixed(0)} ft²)`],
    ["Panels", `${t.whole} whole + ${t.partial} partial`], ["Sticks", `${t.stick_count} in ${t.sticks.length} cuts`], ["2x3 studs", t.boards],
    ["Plywood sheets", t.sheets], ["Base sections", `${t.tapered} tapered, ${t.level} level`], ["Rip bevels", `${deg(t.bevel_lo, 2)} to ${deg(t.bevel_hi, 2)}`]];
  if (t.door) rows.push(["Door opening", `${mm(t.door.W)} x ${mm(t.door.H)}`]);
  $("#summary").innerHTML = rows.map(([k, v]) => `<div class="kv"><span>${k}</span><b>${v}</b></div>`).join("") +
    (t.warnings.length ? `<div class="warn">${t.warnings.map(esc).join("<br>")}</div>` : "");
}

function renderTags() {
  $("#tags").innerHTML = "";
  for (const [tag, label] of TAGS) {
    const l = document.createElement("label");
    const c = document.createElement("input");
    c.type = "checkbox"; c.checked = !S.tagsOff.has(tag);
    c.onchange = () => { c.checked ? S.tagsOff.delete(tag) : S.tagsOff.add(tag); applyVisibility(); };
    const n = [...S.pieces.values()].filter((g) => g.userData.piece.tag === tag).length;
    l.append(c, document.createTextNode(` ${label}`));
    const sp = document.createElement("span"); sp.className = "muted"; sp.textContent = ` ${n}`;
    l.append(sp);
    $("#tags").append(l);
  }
}

function renderOutliner() {
  const o = $("#outliner");
  o.innerHTML = "";
  for (const [cat, ids] of S.groups) {
    const d = document.createElement("div");
    d.className = "grp" + (ids.every((id) => S.selected.has(id)) && S.selected.size ? " sel" : "");
    const panels = new Set(ids.map((id) => S.pieces.get(id).userData.piece.group));
    const count = cat.startsWith("Panels") || cat === "Partial panels" ? `${panels.size} panels` : `${ids.length}`;
    d.innerHTML = `<span>${esc(cat)}</span><span class="n">${count}</span>`;
    d.onclick = () => select(ids);
    o.append(d);
  }
}

function renderInfo() {
  const box = $("#info");
  const ids = [...S.selected];
  if (!ids.length) { box.innerHTML = `<p class="muted">Select a piece. Double-click selects its whole panel.</p>`; vcb("Measurements", ""); return; }
  if (ids.length > 1) {
    const ps = ids.map((id) => S.pieces.get(id).userData.piece);
    const names = [...new Set(ps.map((p) => p.name))];
    box.innerHTML = `<h4>${ids.length} pieces</h4><p>${esc(names.slice(0, 6).join(", "))}${names.length > 6 ? " ..." : ""}</p>`;
    const sticks = ps.filter((p) => p.tag === "frame");
    if (sticks.length) {
      const L = sticks.reduce((a, p) => a + p.info.long_m, 0);
      box.innerHTML += `<table><tr><td>Sticks</td><td>${sticks.length}</td></tr><tr><td>Total length</td><td>${both(L)}</td></tr></table>`;
    }
    vcb("Selected", `${ids.length} pieces`);
    return;
  }
  const p = S.pieces.get(ids[0]).userData.piece, f = p.info, rows = [];
  rows.push(["Tag", p.tag], ["Material", (S.data.materials[p.material] || {}).label || p.material]);
  if (p.tag === "frame") {
    rows.push(["Cut-list mark", f.mark || ""], ["Panel", `${f.panel} (class ${f.cls})`], ["Side", `${f.side} (${f.kind})`],
              ["Long point to long point", both(f.long_m)], ["Along the outline", both(f.outline_m)],
              ["Head (compound)", `${deg(f.head_mitre)} mitre, ${deg(f.head_bevel)} bevel`],
              ["Tail", `${deg(f.tail_mitre)} mitre, square`], ["Rip bevel", deg(f.rip_deg, 2)], ["Goes up with", `stage ${p.step}`]);
  } else if (p.tag === "skin" || p.tag === "glass") {
    rows.push(["Panel", f.panel || p.group], ["Class", f.cls || ""], ["Sides", (f.sides_m || []).map(mm).join(", ")],
              ["Area", f.area_m2 ? `${f.area_m2.toFixed(3)} m²` : ""]);
  } else if (p.tag === "base") {
    rows.push(["Section", p.group], ["Shape", f.tapered ? "tapered" : "level"], ["Length", both(f.length_m)],
              ["Low end", mm(f.low_m)], ["High end", mm(f.high_m)], ["End mitres", deg(f.end_mitre)]);
  } else {
    for (const [k, v] of Object.entries(f)) if (typeof v !== "object") rows.push([k.replace(/_m$/, "").replace(/_/g, " "), typeof v === "number" ? (k.endsWith("_m") ? both(v) : v.toFixed(3)) : String(v)]);
  }
  box.innerHTML = `<h4>${esc(p.name)}</h4><table>${rows.map(([k, v]) => `<tr><td>${esc(k)}</td><td>${esc(String(v))}</td></tr>`).join("")}</table>`;
  vcb(p.tag === "frame" ? "Stick" : "Selected", p.tag === "frame" ? both(f.long_m) : p.name);
}

function renderCutlist() {
  const rows = S.data.tables.sticks;
  $("#cutlist").innerHTML = `<table><tr><th>Mark</th><th>Panel</th><th>Qty</th><th>Length</th><th>Head</th><th>Tail</th><th>Rip</th></tr>` +
    rows.map((r) => `<tr data-mark="${r.mark}"><td>${r.mark}</td><td>${r.cls === "partial" ? "P" : r.cls}</td><td>${r.count}</td><td>${mm(r.long_m)}</td>` +
      `<td>${deg(r.head_mitre)}/${deg(r.head_bevel)}</td><td>${deg(r.tail_mitre)}</td><td>${deg(r.rip_deg, 2)}</td></tr>`).join("") + `</table>`;
  $$("#cutlist tr[data-mark]").forEach((tr) => tr.onclick = () => {
    const ids = [...S.pieces.values()].map((g) => g.userData.piece).filter((p) => p.info.mark === tr.dataset.mark).map((p) => p.id);
    S.tagsOff.delete("frame"); applyVisibility(); select(ids);
  });
}

function hideSelected() { for (const id of S.selected) S.hidden.add(id); S.selected.clear(); applyStyle(); applyVisibility(); renderInfo(); }
$("#hide").onclick = hideSelected;
$("#isolate").onclick = () => {
  if (!S.selected.size) return;
  for (const id of S.pieces.keys()) if (!S.selected.has(id)) S.hidden.add(id);
  applyVisibility(); zoomExtents();
};
$("#unhide").onclick = () => { S.hidden.clear(); applyVisibility(); };

function esc(s) { return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]); }
function toast(msg) { $("#hint").textContent = msg; }

// ---------------------------------------------------------------- the dome form
const FIELDS = ["diameter_m", "stick_w_m", "stick_d_m", "riser_m", "windows", "door_w_m", "door_h_m"];
const CHECKS = ["door", "skylight", "stove", "porch", "furnish", "people"];
function fillForm(spec) {
  for (const k of FIELDS) $(`#f-${k}`).value = +(+spec[k]).toFixed(4);
  for (const k of CHECKS) $(`#f-${k}`).checked = !!spec[k];
  $("#f-skin").value = spec.skin;
  $("#f-cut").value = `${spec.frequency}|${spec.cut}`;
}
function readForm() {
  const s = { ...S.spec };
  for (const k of FIELDS) s[k] = parseFloat($(`#f-${k}`).value);
  for (const k of CHECKS) s[k] = $(`#f-${k}`).checked;
  s.skin = $("#f-skin").value;
  const [f, c] = $("#f-cut").value.split("|"); s.frequency = +f; s.cut = c;
  return s;
}
let formTimer = null;
function formChanged() { clearTimeout(formTimer); formTimer = setTimeout(() => load(readForm(), true), 350); }
$("#form").addEventListener("change", formChanged);
$("#preset").onchange = () => {
  const p = S.defaults.presets[$("#preset").value];
  if (!p) return;
  const spec = { ...readForm(), ...p.spec };
  fillForm(spec);
  load(spec);
};

// ---------------------------------------------------------------- jobs
async function startJob(kind) {
  try {
    await api(`/api/${kind}`, { spec: readForm() });
    pollJobs();
  } catch (e) { toast(e.message); }
}
let polling = null;
async function pollJobs() {
  const jobs = await api("/api/jobs");
  $("#jobs").innerHTML = jobs.slice(0, 6).map((j) => {
    const secs = Math.round(((j.ended || Date.now() / 1000) - j.started));
    const link = j.output ? (j.output.endsWith(".pdf") ? `<a href="/api/file?path=${encodeURIComponent(j.output)}" target="_blank">Open the PDF</a>` : `<span class="muted">${esc(j.output)}</span>`) : "";
    return `<div class="job ${j.state}"><span class="st">${j.kind === "plans" ? "Plan set" : "Showcase"}: ${j.state}</span> <span class="muted">${secs}s</span><br>${esc(j.title)}<br>${link}` +
      `<pre>${esc(j.log.split("\n").slice(-4).join("\n"))}</pre></div>`;
  }).join("");
  const running = jobs.some((j) => j.state === "running");
  clearTimeout(polling);
  if (running) polling = setTimeout(pollJobs, 2000);
  else renderOutputs();
}
async function renderOutputs() {
  const outs = await api("/api/outputs");
  $("#outputs").innerHTML = outs.slice(-6).reverse().map((o) => `<div class="out"><b>${esc(o.folder.split("/").pop())}</b>` +
    o.files.filter((f) => /\.(pdf|png)$/i.test(f)).slice(0, 10).map((f) => `<a href="/api/file?path=${encodeURIComponent(f)}" target="_blank">${esc(f.split("/").pop())}</a>`).join("") + `</div>`).join("");
}
$("#plans").onclick = () => startJob("plans");
$("#showcase").onclick = () => startJob("showcase");
$("#snap").onclick = () => {
  renderer.render(scene, camera);
  const a = document.createElement("a");
  a.href = canvas.toDataURL("image/png");
  a.download = `dome-sketch-${S.scene.toLowerCase().replace(/[^a-z0-9]+/g, "-")}.png`;
  a.click();
};

// ---------------------------------------------------------------- toolbar wiring
$$(".tools [data-tool]").forEach((b) => b.onclick = () => setTool(b.dataset.tool));
$("#extents").onclick = () => zoomExtents();
$("#view").onchange = () => { if ($("#view").value) view($("#view").value); $("#view").value = ""; };
$("#proj").onclick = () => setProjection(camera === persp);
$("#style").onchange = () => { S.style = $("#style").value; applyStyle(); };
$("#shadows").onchange = applyStyle;
$("#explode").oninput = () => { S.explode = $("#explode").value / 100; applyTransforms(); };
$("#step").oninput = () => { S.step = +$("#step").value; applyVisibility(); };
$("#door").oninput = () => { S.door = +$("#door").value; applyTransforms(); };
$("#sun").oninput = () => { S.sunAz = +$("#sun").value; placeSun(); };
$("#section").oninput = () => { S.section.t = $("#section").value / 100; syncSection(); };
$("#sec-axis").onchange = () => { S.section.axis = $("#sec-axis").value; syncSection(); };

// ---------------------------------------------------------------- loop
let lastNow = 0;
function renderFrame(dt, now) {
  if (anim) anim(now);
  for (const h of ctx.hooks) h(dt, now);
  if (controls.enabled) controls.update();
  if (camera === ortho) syncOrtho();
  renderer.render(scene, camera);
  for (const h of ctx.post) h(dt, now);
  placeLabels();
}
function frame(now) {
  const dt = Math.min(0.1, lastNow ? (now - lastNow) / 1000 : 0.016);
  lastNow = now;
  if (!ctx.offline) renderFrame(dt, now);      // an offline render drives the frames itself
  requestAnimationFrame(frame);
}

// What the Director (cine.js, cast.js, episode.js) needs from the modeller.
const ctx = {
  THREE, scene, world, renderer, persp, controls, canvas, S, api, decode, faceMat, edgeMat, sun, hemi, lamp, makePieceGroup,
  hooks: [], post: [], offline: false, renderFrame, applyTransforms, applyVisibility, applyStyle, zoomExtents, bounds, goScene, SCENES, setTool,
  get camera() { return camera; }, setProjection, toast, both, mm, deg,
  setView(v) { S.explode = v.explode ?? S.explode; S.step = v.step ?? S.step; S.door = v.door ?? S.door;
               if (v.tagsOff) S.tagsOff = new Set(v.tagsOff); if (v.style) { S.style = v.style; $("#style").value = v.style; }
               $("#explode").value = S.explode * 100; $("#step").value = S.step; $("#door").value = S.door;
               applyStyle(); applyTransforms(); applyVisibility(); renderTags(); },
};
window.domeSketch = ctx;

// ---------------------------------------------------------------- start
(async function start() {
  S.defaults = await api("/api/defaults");
  $("#tag").textContent = S.defaults.tag;
  $("#preset").innerHTML = `<option value="">Choose...</option>` + Object.entries(S.defaults.presets).map(([k, p]) => `<option value="${k}">${esc(p.label)}</option>`).join("");
  $("#f-cut").innerHTML = S.defaults.cuts.map((c) => `<option value="${c.frequency}|${c.cut}">${c.frequency}V ${c.cut}</option>`).join("");
  const urlSpec = new URLSearchParams(location.search).get("spec");
  if (urlSpec) { try { Object.assign(S.defaults.spec, JSON.parse(urlSpec)); } catch { /* the default dome */ } }
  fillForm(S.defaults.spec);
  S.spec = S.defaults.spec;
  setTool("select");
  resize();
  requestAnimationFrame(frame);
  await load(S.defaults.spec);
  renderScenes(); renderTags();
  if (S.data) goScene(SCENES[0]);   // nothing loaded (the server said why): the page stays usable
  pollJobs();

})();
