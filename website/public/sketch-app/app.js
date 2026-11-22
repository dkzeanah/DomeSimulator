// copied from sketch_claude/static/app.js by website/scripts/sync_sketch_app.py: edit that file, then re-run
import "/sketch-app/web-shim.js";
// Dome Sketch (sketch-claude): a SketchUp-style modeller for every kind of geodesic dome.
// The geometry comes from the server (sketch_claude.kinds): the wedge dome, the zome, framed-panel
// domes and all-steel domes, every stick, wedge and plate a solid with its own figures. This page
// draws it the way SketchUp does -- flat faces, inked edges, sun shadows -- and adds the tools a
// builder reaches for: select, orbit, pan, tape, dimensions, lines, notes, paint, section plane,
// scenes, tags, an outliner, entity info, the visual cut list, the step-by-step build guide and
// renders saved from this very view. Every number goes through units.js.

import * as THREE from "three";
import { OrbitControls } from "/sketch-app/vendor/OrbitControls.js";
import * as U from "/sketch-app/units.js";
import { initTools } from "/sketch-app/tools.js";
import { renderCards, printCards } from "/sketch-app/cutlist.js";
import { initBuild } from "/sketch-app/build.js";
import { initMaterials } from "/sketch-app/materials.js";
import { initDesigns } from "/sketch-app/designs.js";

const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const both = (m) => U.len(m);
const mm = (m) => U.mm(m);
const deg = (a, n = 1) => U.deg(a, n);

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
const lamp = new THREE.PointLight(0xffd59a, 5, 9, 1.4);      // the pendant over a furnished room
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

// Colour themes: the sky, the ink and the light. "Daylight" is the modeller's own look.
const THEMES = {
  sketch:    { sky: ["#c9dbee", "#f4f3ef"], plain: ["#ffffff", "#f1f0ec"], ink: 0x1d1b18, hemi: 1.25, sun: 1.6, lamp: 5 },
  blueprint: { sky: ["#1d4f86", "#12365f"], plain: ["#1d4f86", "#12365f"], ink: 0xe8f1ff, hemi: 1.6, sun: 0.9, lamp: 0, faces: "#3a6ea8", faceOpacity: 0.35 },
  timber:    { sky: ["#efe0c3", "#f8f2e6"], plain: ["#fbf7ef", "#f3ead9"], ink: 0x3b2a1a, hemi: 1.3, sun: 1.7, lamp: 5 },
  steel:     { sky: ["#c7d0d9", "#eef1f4"], plain: ["#f4f6f8", "#e5e9ed"], ink: 0x22272d, hemi: 1.35, sun: 1.5, lamp: 3 },
  present:   { sky: ["#ffffff", "#f3f3f3"], plain: ["#ffffff", "#f6f6f6"], ink: 0x2a2a2a, hemi: 1.45, sun: 1.4, lamp: 3, soft: true },
  night:     { sky: ["#0b1426", "#1d2b44"], plain: ["#0b1426", "#1d2b44"], ink: 0x9fb3d1, hemi: 0.35, sun: 0.15, lamp: 9 },
};
const skyCache = new Map();
function sky(pair) { const k = pair.join(); if (!skyCache.has(k)) skyCache.set(k, skyTexture(...pair)); return skyCache.get(k); }

// ---------------------------------------------------------------- state
const S = {
  spec: null, data: null, pieces: new Map(), groups: new Map(), kind: "panel",
  selected: new Set(), hidden: new Set(), tagsOff: new Set(),
  style: "sketch", theme: "sketch", edges: "strong", skinOpacity: 1, bg: null,
  tool: "select", explode: 0, step: 999, door: 0, sunAz: 215, doorSign: 1,
  section: { on: false, axis: "z", t: 0.45 }, tape: null, dims: [], defaults: null, scene: "Exterior",
  marks: { items: [], paint: {} }, build: { on: false, i: 0, role: null }, markList: [],
};
const PANEL_TAGS = [["frame", "Frame"], ["skin", "Skin"], ["glass", "Glazing"], ["base", "Base sections"], ["door", "Door"],
                    ["deck", "Deck"], ["furniture", "Furniture"], ["person", "Person"], ["site", "Ground"]];
const tags = () => (S.data && S.data.tables.tags) || PANEL_TAGS;
const tagLabel = (t) => (tags().find(([k]) => k === t) || [t, t])[1];
const TRANSLUCENT = new Set(["skin", "glass", "water", "clear"]);

// ---------------------------------------------------------------- materials
const matCache = new Map();
function faceMat(key, mode) {
  const id = `${key}|${mode}|${S.theme}|${S.skinOpacity}`;
  if (matCache.has(id)) return matCache.get(id);
  const def = (S.data && S.data.materials[key]) || { color: "#cccccc" };
  const th = THEMES[S.theme];
  let opacity = def.opacity ?? 1;
  if (opacity < 1 || key === "water" || key === "poly" || key === "glass") opacity *= S.skinOpacity;
  let color = new THREE.Color(def.color), transparent = opacity < 1, op = opacity, emissive = new THREE.Color(0);
  if (mode === "mono" || mode === "hidden") { color = new THREE.Color(key === "glass" || key === "poly" || key === "water" ? "#d9e6ee" : "#f2f1ee"); }
  if (th.faces && mode !== "sel" && mode !== "hi") { color = new THREE.Color(th.faces); transparent = true; op = Math.min(op, th.faceOpacity); }
  if (mode === "xray" || mode === "ghost") { transparent = true; op = Math.min(op, mode === "ghost" ? 0.14 : 0.4); }
  if (mode === "sel") { color = new THREE.Color("#6f9ce8"); transparent = false; op = 1; emissive = new THREE.Color("#1d3f8a"); }
  if (mode === "hi") { emissive = new THREE.Color("#c45e29").multiplyScalar(0.55); transparent = false; op = 1; }
  if (def.emissive && mode !== "mono" && mode !== "hidden") emissive = new THREE.Color(def.color).multiplyScalar(0.9);
  const Mat = mode === "hidden" ? THREE.MeshBasicMaterial : THREE.MeshLambertMaterial;
  const m = new Mat({ color, transparent, opacity: op, side: THREE.DoubleSide, polygonOffset: true,
                      polygonOffsetFactor: 1, polygonOffsetUnits: 1, depthWrite: !transparent || mode === "sel" });
  if (m.emissive) m.emissive = emissive;
  matCache.set(id, m);
  return m;
}
function colorMat(hex) {
  const id = `paint|${hex}`;
  if (!matCache.has(id)) matCache.set(id, new THREE.MeshLambertMaterial({ color: hex, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1 }));
  return matCache.get(id);
}
const edgeMat = new THREE.LineBasicMaterial({ color: 0x1d1b18 });
const edgeSoft = new THREE.LineBasicMaterial({ color: 0x1d1b18, transparent: true, opacity: 0.35 });
const edgeSel = new THREE.LineBasicMaterial({ color: 0x1846b8 });
const edgeGhost = new THREE.LineBasicMaterial({ color: 0x1d1b18, transparent: true, opacity: 0.12 });

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
    mesh.castShadow = p.tag !== "site" && !TRANSLUCENT.has(p.tag);
    mesh.receiveShadow = true;
    mesh.userData.piece = p;
    g.add(mesh); g.userData.mesh = mesh;
    geo.computeBoundingBox();
    g.userData.centre = geo.boundingBox.getCenter(new THREE.Vector3());
  }
  if (e.length && p.tag !== "site") {
    const lp = new Float32Array(e.length * 3);
    for (let i = 0; i < e.length; i++) { lp[i * 3] = v[e[i] * 3]; lp[i * 3 + 1] = v[e[i] * 3 + 1]; lp[i * 3 + 2] = v[e[i] * 3 + 2]; }
    const lg = new THREE.BufferGeometry();
    lg.setAttribute("position", new THREE.BufferAttribute(lp, 3));
    const lines = new THREE.LineSegments(lg, TRANSLUCENT.has(p.tag) ? edgeSoft : edgeMat);
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
    S.data = data; S.spec = data.spec; S.kind = data.tables.kind || data.spec.kind || "panel";
    if (typeof data.preset === "string") $("#preset").value = data.preset;   // online, an open design drawn in place of a locked one
    matCache.clear();
    world.clear();
    S.pieces.clear(); S.groups.clear(); S.selected.clear(); S.hidden.clear();
    S.panelCls = new Map(data.pieces.filter((p) => p.tag === "frame" && p.info.cls).map((p) => [p.group, p.info.cls]));
    S.markList = [...new Set(data.pieces.map((p) => classKey(p)).filter(Boolean))].sort();
    for (const p of data.pieces) {
      const g = makePieceGroup(p);
      g.matrixAutoUpdate = false;
      world.add(g);
      S.pieces.set(p.id, g);
      const cat = category(p);
      if (!S.groups.has(cat)) S.groups.set(cat, []);
      S.groups.get(cat).push(p.id);
    }
    measureDoor();
    $("#step").max = data.max_step;
    if (S.step > data.max_step) S.step = data.max_step;
    $("#step").value = S.step;
    $("#door").max = (data.tables.door && data.tables.door.max) || 95;
    $("#door").closest("label").hidden = !data.tables.door;
    $("#plans").disabled = $("#showcase").disabled = S.kind !== "panel";
    syncKindSelect();
    tools.loadMarks();
    build.reset();
    applyStyle(); applyTransforms(); applyVisibility();
    renderSummary(); renderOutliner(); renderCutlist(); renderInfo(); renderDeclared(); renderTags(); renderScenes();
    materials.render(); designs.render(); renderExports();
    if (!keepView) zoomExtents(false);
    placeSun();
    history.replaceState(null, "", `?spec=${encodeURIComponent(JSON.stringify(S.spec))}`);
  } catch (err) {
    toast(err.message);
  } finally {
    if (token === buildToken) $("#busy").hidden = true;
  }
}

function classKey(p) {
  if (S.kind === "panel" || (S.data && S.data.tables.kind === "panel")) {
    return p.tag === "skin" || p.tag === "glass" ? (S.panelCls && S.panelCls.get(p.group)) || null : null;
  }
  return ["frame", "shell", "key"].includes(p.tag) ? p.info.mark || null : null;
}

function category(p) {
  if (S.kind === "panel" && p.tag === "frame") {
    const c = p.info.cls;
    return c === "partial" ? "Partial panels" : `Panels ${c} (${(S.data.tables.classes.find((k) => k.name === c) || {}).kind || ""})`;
  }
  if (S.kind === "panel") {
    return { skin: "Skin", glass: "Windows and skylight", base: "Base sections", door: p.group === "door-leaf" ? "Door leaf" : "Door frame",
             deck: "Deck and porch", furniture: "Furniture", person: "Person", site: "Ground" }[p.tag] || p.tag;
  }
  const mk = p.info && p.info.mark;
  return mk && ["frame", "shell", "key"].includes(p.tag) ? `${tagLabel(p.tag)} ${mk}` : tagLabel(p.tag);
}

// ---------------------------------------------------------------- transforms: explode, door swing
function measureDoor() {
  // which way round the hinge opens the door outward (the steel domes' door hinges on a slanted edge)
  const d = S.data.tables.door;
  S.doorSign = 1;
  if (!d || !d.hinge_a) return;
  const leaf = [...S.pieces.values()].find((g) => g.userData.piece.group === "door-leaf" && g.userData.centre);
  if (!leaf) return;
  const c = leaf.userData.centre.clone(), m = doorMatrix(10, 1);
  const r0 = Math.hypot(c.x, c.y), c1 = c.clone().applyMatrix4(m);
  S.doorSign = Math.hypot(c1.x, c1.y) > r0 ? 1 : -1;
}
function doorMatrix(angle, sign) {
  const d = S.data.tables.door, a = new THREE.Vector3(...d.hinge_a), b = new THREE.Vector3(...d.hinge_b);
  const axis = b.clone().sub(a).normalize();
  const m = new THREE.Matrix4().makeTranslation(a.x, a.y, a.z);
  m.multiply(new THREE.Matrix4().makeRotationAxis(axis, sign * angle * Math.PI / 180));
  m.multiply(new THREE.Matrix4().makeTranslation(-a.x, -a.y, -a.z));
  return m;
}
function applyTransforms() {
  const d = S.data.tables.door;
  const hinge = d && d.W !== undefined ? new THREE.Vector3(-d.W / 2, d.y_post, 0) : null;
  const rot = new THREE.Matrix4(), tr = new THREE.Matrix4(), back = new THREE.Matrix4(), m = new THREE.Matrix4();
  const swing = d && d.hinge_a && S.door ? doorMatrix(S.door, S.doorSign) : null;
  for (const g of S.pieces.values()) {
    const p = g.userData.piece;
    m.identity();
    if (S.explode) m.makeTranslation(p.explode[0] * S.explode, p.explode[1] * S.explode, p.explode[2] * S.explode);
    if (p.group === "door-leaf" && S.door) {
      if (swing) m.multiply(swing);
      else if (hinge) {
        tr.makeTranslation(hinge.x, hinge.y, 0); rot.makeRotationZ(-S.door * Math.PI / 180); back.makeTranslation(-hinge.x, -hinge.y, 0);
        m.multiply(tr).multiply(rot).multiply(back);
      }
    }
    g.matrix.copy(m);
    g.matrixWorldNeedsUpdate = true;
  }
}

// ---------------------------------------------------------------- visibility and style
function applyVisibility() {
  for (const g of S.pieces.values()) {
    const p = g.userData.piece;
    const role = S.build.on && S.build.role ? S.build.role(p) : null;
    g.visible = !S.tagsOff.has(p.tag) && !S.hidden.has(p.id) && (S.build.on ? role !== "hidden" : p.step <= S.step);
  }
  $("#step-v").textContent = S.step >= S.data.max_step ? "all" : String(S.step);
}

function applyStyle() {
  const st = S.style, th = THEMES[S.theme];
  edgeMat.color.setHex(th.ink); edgeSoft.color.setHex(th.ink); edgeGhost.color.setHex(th.ink);
  edgeSoft.opacity = th.soft ? 0.18 : 0.35;
  for (const g of S.pieces.values()) {
    const p = g.userData.piece, sel = S.selected.has(p.id);
    const role = S.build.on && S.build.role ? S.build.role(p) : null;
    if (g.userData.mesh) {
      const ck = S.colour ? classKey(p) : null;
      const paint = S.marks.paint[p.id];
      let mat;
      if (sel) mat = faceMat(p.material, "sel");
      else if (role === "hi") mat = faceMat(p.material, "hi");
      else if (role === "ghost") mat = faceMat(p.material, "ghost");
      else if (paint) mat = colorMat(paint);
      else if (ck) mat = classMat(ck);
      else mat = faceMat(p.material, st === "shaded" || st === "wire" || st === "sketch" ? "base" : st);
      g.userData.mesh.material = mat;
      g.userData.mesh.visible = st !== "wire" || p.tag === "site";
    }
    if (g.userData.lines) {
      g.userData.lines.visible = st !== "shaded" && S.edges !== "off";
      g.userData.lines.material = sel ? edgeSel : role === "ghost" ? edgeGhost
        : (TRANSLUCENT.has(p.tag) || S.edges === "soft") ? edgeSoft : edgeMat;
    }
  }
  const pair = st === "hidden" || st === "mono" ? th.plain : th.sky;
  scene.background = S.bg ? new THREE.Color(S.bg) : sky(pair);
  hemi.intensity = st === "hidden" ? 2.2 : th.hemi;
  sun.intensity = th.sun;
  lamp.intensity = th.lamp;
  sun.castShadow = $("#shadows").checked && st !== "hidden" && st !== "xray" && !th.faces;
  renderer.shadowMap.needsUpdate = true;
}

// ---------------------------------------------------------------- the sun
function placeSun() {
  const a = S.sunAz * Math.PI / 180, el = 42 * Math.PI / 180;
  const box = bounds(false), c = box.getCenter(new THREE.Vector3()), r = Math.max(6, box.getSize(new THREE.Vector3()).length());
  sun.position.set(c.x + Math.cos(a) * Math.cos(el) * r * 2, c.y + Math.sin(a) * Math.cos(el) * r * 2, Math.sin(el) * r * 2);
  sun.target.position.set(c.x, c.y, c.z);
  const h = Math.max(4, r * 0.75);
  sc.left = -h; sc.right = h; sc.top = h; sc.bottom = -h; sc.far = r * 5; sc.updateProjectionMatrix();
}

// ---------------------------------------------------------------- cameras and views
function bounds(onlyVisible = true, ids = null) {
  const box = new THREE.Box3();
  for (const g of S.pieces.values()) {
    const p = g.userData.piece;
    if (ids ? !ids.has(p.id) : (p.tag === "site" || (onlyVisible && !g.visible))) continue;
    box.expandByObject(g);
  }
  if (box.isEmpty()) box.set(new THREE.Vector3(-3, -3, 0), new THREE.Vector3(3, 3, 3));
  return box;
}

let anim = null;
function flyTo(pos, target, ms = 550) {
  if (!ms) { camera.position.copy(pos); controls.target.copy(target); if (camera === ortho) syncOrtho(); anim = null; return; }
  const p0 = camera.position.clone(), t0 = controls.target.clone(), start = performance.now();
  anim = (now) => {
    const k = Math.min(1, (now - start) / ms), e = k * k * (3 - 2 * k);
    camera.position.lerpVectors(p0, pos, e);
    controls.target.lerpVectors(t0, target, e);
    if (camera === ortho) syncOrtho();
    if (k >= 1) anim = null;
  };
}

function zoomExtents(animate = true, dir = null, ids = null) {
  const box = bounds(true, ids), c = box.getCenter(new THREE.Vector3()), r = Math.max(0.3, box.getSize(new THREE.Vector3()).length() / 2);
  const d = (dir || camera.position.clone().sub(controls.target)).normalize();
  const dist = r / Math.tan((persp.fov * Math.PI / 180) / 2) * 0.82;
  const pos = c.clone().addScaledVector(d, dist);
  flyTo(pos, c, animate ? 550 : 0);
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
const PANEL_SCENES = [
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
const SCENES = [];
function scenesFor() { return (S.data && S.data.tables.scenes) || PANEL_SCENES; }

function renderScenes() {
  SCENES.length = 0; SCENES.push(...scenesFor());
  $("#scenes").innerHTML = "";
  SCENES.forEach((sc, i) => {
    const b = document.createElement("button");
    b.textContent = sc.name; b.title = `Scene ${i + 1} (key ${i + 1})`;
    b.onclick = () => goScene(sc);
    b.className = sc.name === S.scene ? "on" : "";
    $("#scenes").append(b);
  });
}

function goScene(sc, instant = false) {
  if (S.build.on) build.close();
  S.scene = sc.name;
  $$("#scenes button").forEach((b) => b.classList.toggle("on", b.textContent === sc.name));
  S.tagsOff = new Set(sc.off);
  S.explode = sc.explode / 100; $("#explode").value = sc.explode;
  S.step = Math.min(sc.step, S.data.max_step); $("#step").value = S.step;
  S.door = sc.door || 0; $("#door").value = S.door;
  S.style = sc.style; $("#style").value = sc.style;
  S.hidden.clear();
  S.colour = !!sc.colour;
  if (sc.section) { S.section = { on: true, ...sc.section }; } else S.section.on = false;
  syncSection();
  applyStyle(); applyTransforms(); applyVisibility(); renderTags();
  const ms = instant ? 0 : 550;
  if (sc.inside && S.data.landmarks.door) {
    const lm = S.data.landmarks;
    flyTo(new THREE.Vector3(0.35, lm.door[1] + 0.55, 1.45), new THREE.Vector3(-0.55, 0.9, 0.9), ms);
    persp.fov = 62; persp.updateProjectionMatrix();
  } else {
    persp.fov = 35; persp.updateProjectionMatrix();
    if (sc.near && S.data.tables.door && S.data.tables.door.y_post !== undefined) {
      const d = S.data.tables.door;
      flyTo(new THREE.Vector3(1.6, d.y_post - 3.6, 1.6), new THREE.Vector3(0, d.y_post, 1.0), ms);
    } else zoomExtents(!instant, new THREE.Vector3(...(sc.dir || [0.6, -1, 0.4])));
  }
}

const CLASS_COLOURS = ["#e3a64b", "#7fb2d6", "#9cc27a", "#d98b8b", "#b49ad6", "#e0cf6a", "#6fc2b4", "#d6a3c7", "#a9b86a", "#e39a6e", "#8a9fd6", "#c9b48a"];
function classMat(cls) {
  const names = S.kind === "panel" && S.data.tables.classes ? S.data.tables.classes.map((c) => c.name) : S.markList;
  const col = cls === "partial" ? "#c9c3b8" : CLASS_COLOURS[Math.max(0, names.indexOf(cls)) % CLASS_COLOURS.length];
  const id = `class|${col}`;
  if (!matCache.has(id)) matCache.set(id, new THREE.MeshLambertMaterial({ color: col, side: THREE.DoubleSide, polygonOffset: true,
                                                                          polygonOffsetFactor: 1, polygonOffsetUnits: 1 }));
  return matCache.get(id);
}
function classColour(cls) {
  const names = S.kind === "panel" && S.data.tables.classes ? S.data.tables.classes.map((c) => c.name) : S.markList;
  return CLASS_COLOURS[Math.max(0, names.indexOf(cls)) % CLASS_COLOURS.length];
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
function ndcOf(ev) {
  const r = canvas.getBoundingClientRect();
  return new THREE.Vector2(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
}
function pick(ev) {
  ray.setFromCamera(ndcOf(ev), camera);
  const meshes = [];
  for (const g of S.pieces.values()) if (g.visible && g.userData.mesh && g.userData.mesh.visible && g.userData.piece.tag !== "site") meshes.push(g.userData.mesh);
  const hits = ray.intersectObjects(meshes, false).filter((h) => !S.section.on || clip.distanceToPoint(h.point) >= 0);
  return hits[0] || null;
}
function pickGround(ev) {
  // where the pointer meets the ground (z = 0), for drawing off the model
  ray.setFromCamera(ndcOf(ev), camera);
  const p = new THREE.Vector3();
  return ray.ray.intersectPlane(new THREE.Plane(new THREE.Vector3(0, 0, 1), 0), p) ? p : null;
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
function screenOf(p) {
  const r = canvas.getBoundingClientRect(), m = p.clone().project(camera);
  return { x: (m.x + 1) / 2 * r.width, y: (1 - m.y) / 2 * r.height, on: m.z < 1 };
}
function placeLabels() {
  for (const d of S.dims) {
    const s = screenOf(d.a.clone().add(d.b).multiplyScalar(0.5));
    d.label.style.left = `${s.x}px`; d.label.style.top = `${s.y}px`; d.label.style.display = s.on ? "" : "none";
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
  $$("#ftb [data-tool]").forEach((b) => b.classList.toggle("on", b.dataset.tool === t || (b.dataset.tool === "section" && S.section.on)));
  controls.mouseButtons = { LEFT: t === "orbit" ? THREE.MOUSE.ROTATE : t === "pan" ? THREE.MOUSE.PAN : null,
                            MIDDLE: THREE.MOUSE.ROTATE, RIGHT: THREE.MOUSE.PAN };
  canvas.style.cursor = ["tape", "dim", "line", "note"].includes(t) ? "crosshair" : t === "orbit" ? "grab" : t === "pan" ? "move"
    : t === "paint" ? "cell" : t === "erase" ? "not-allowed" : "default";
  $("#hint").textContent = HINTS[t] || tools.hint(t) || "";
  if (t !== "tape" && tapeLine) { overlay.remove(tapeLine); tapeLine = null; S.tape = null; }
  tools.toolChanged(t);
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
  } else tools.click(S.tool, ev, hit);
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
  if (S.tool === "tape" && S.tape) {
    const hit = pick(ev);
    if (hit) tapeMove(snapPoint(hit, ev).p);
    return;
  }
  tools.move(S.tool, ev);
});

window.addEventListener("keydown", (ev) => {
  if (ev.target.closest("input, select, textarea")) return;
  const k = ev.key.toLowerCase();
  if ((ev.ctrlKey || ev.metaKey) && k === "z") { tools.undo(); ev.preventDefault(); return; }
  if ((ev.ctrlKey || ev.metaKey) && k === "y") { tools.redo(); ev.preventDefault(); return; }
  if (S.build.on) {
    if (k === "arrowright" || k === "pagedown") { build.next(); ev.preventDefault(); return; }
    if (k === "arrowleft" || k === "pageup") { build.prev(); ev.preventDefault(); return; }
    if (k === "escape") { build.close(); return; }
  }
  if (k === " ") { setTool("select"); ev.preventDefault(); }
  else if (k === "o") setTool("orbit");
  else if (k === "h" && !ev.shiftKey) setTool("pan");
  else if (k === "t") setTool("tape");
  else if (k === "d") setTool("dim");
  else if (k === "l") setTool("line");
  else if (k === "n") setTool("note");
  else if (k === "k") setTool("paint");
  else if (k === "e") setTool("erase");
  else if (k === "p") setTool("section");
  else if (k === "b") build.toggle();
  else if (k === "z" && ev.shiftKey) zoomExtents();
  else if (k === "escape") { clearDims(); tools.cancel(); select([]); }
  else if (k === "delete") hideSelected();
  else if (/^[1-9]$/.test(k) && SCENES[+k - 1]) goScene(SCENES[+k - 1]);
});

// ---------------------------------------------------------------- panels: summary, tags, outliner, info, cut list
function legacySummary(t) {
  // tables from an older server (the web shim's solved grid) carry no summary rows: make them
  if (t.summary || t.diameter_m === undefined) return t.summary || [];
  const r = [["Across the base", `{m:${t.diameter_m}}`], ["Deck to top", `{m:${t.height_m}}`], ["Floor", `{m2:${t.floor_m2}}`],
             ["Panels", `${t.whole} whole + ${t.partial} partial`], ["Sticks", `${t.stick_count} in ${(t.sticks || []).length} cuts`],
             ["2x3 studs", String(t.boards)], ["Plywood sheets", String(t.sheets)], ["Rip bevels", `{deg:${t.bevel_lo}} to {deg:${t.bevel_hi}}`]];
  if (t.door) r.push(["Door opening", `{m:${t.door.W}} x {m:${t.door.H}}`]);
  return r;
}
function legacyCards(t) {
  if (t.cards || !t.sticks) return t.cards || [];
  return t.sticks.map((r) => ({ mark: r.mark, title: `Stick ${r.mark}`, count: r.count, group: `Rip at ${(+r.rip_deg).toFixed(1)}°`, ids: [], draw: null,
    rows: [["Long point to long point", `{m:${r.long_m}}`], ["Head", `{deg:${r.head_mitre}} mitre, {deg:${r.head_bevel}} bevel`], ["Tail", `{deg:${r.tail_mitre}} mitre`], ["Rip", `{deg:${r.rip_deg}}`]] }));
}
function renderSummary() {
  const t = S.data.tables;
  const rows = legacySummary(t).map(([k, v]) => `<div class="kv"><span>${esc(k)}</span><b>${esc(U.tokens(v))}</b></div>`);
  $("#summary").innerHTML = `<div class="title">${esc(t.title || "")}</div>` + rows.join("") +
    ((t.warnings || []).length ? `<div class="warn">${t.warnings.map((w) => esc(U.tokens(w))).join("<br>")}</div>` : "");
}

function renderTags() {
  $("#tags").innerHTML = "";
  for (const [tag, label] of tags()) {
    const n = [...S.pieces.values()].filter((g) => g.userData.piece.tag === tag).length;
    if (!n) continue;
    const l = document.createElement("label");
    const c = document.createElement("input");
    c.type = "checkbox"; c.checked = !S.tagsOff.has(tag);
    c.onchange = () => { c.checked ? S.tagsOff.delete(tag) : S.tagsOff.add(tag); applyVisibility(); };
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
    const mk = classKey(S.pieces.get(ids[0]).userData.piece);
    const sw = mk && S.kind !== "panel" ? `<span class="sw" style="background:${classColour(mk)}"></span>` : "";
    d.innerHTML = `${sw}<span>${esc(cat)}</span><span class="n">${count}</span>`;
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
    const sticks = ps.filter((p) => p.tag === "frame" && p.info.long_m);
    if (sticks.length) {
      const L = sticks.reduce((a, p) => a + p.info.long_m, 0);
      box.innerHTML += `<table><tr><td>Sticks</td><td>${sticks.length}</td></tr><tr><td>Total length</td><td>${both(L)}</td></tr></table>`;
    }
    const kgs = ps.filter((p) => p.info.mass_kg);
    if (kgs.length) box.innerHTML += `<table><tr><td>Steel</td><td>${U.mass(kgs.reduce((a, p) => a + p.info.mass_kg, 0))}</td></tr></table>`;
    vcb("Selected", `${ids.length} pieces`);
    return;
  }
  const p = S.pieces.get(ids[0]).userData.piece, f = p.info, rows = [];
  rows.push(["Tag", tagLabel(p.tag)], ["Material", (S.data.materials[p.material] || {}).label || p.material]);
  if (S.kind === "panel" && p.tag === "frame") {
    rows.push(["Cut-list mark", f.mark || ""], ["Panel", `${f.panel} (class ${f.cls})`], ["Side", `${f.side} (${f.kind})`],
              ["Long point to long point", both(f.long_m)], ["Along the outline", both(f.outline_m)],
              ["Head (compound)", `${deg(f.head_mitre)} mitre, ${deg(f.head_bevel)} bevel`],
              ["Tail", `${deg(f.tail_mitre)} mitre, square`], ["Rip bevel", deg(f.rip_deg, 2)], ["Goes up with", `stage ${p.step}`]);
  } else if (S.kind === "panel" && (p.tag === "skin" || p.tag === "glass")) {
    rows.push(["Panel", f.panel || p.group], ["Class", f.cls || ""], ["Sides", (f.sides_m || []).map(both).join(", ")],
              ["Area", f.area_m2 ? U.area(f.area_m2) : ""]);
  } else if (S.kind === "panel" && p.tag === "base") {
    rows.push(["Section", p.group], ["Shape", f.tapered ? "tapered" : "level"], ["Length", both(f.length_m)],
              ["Low end", both(f.low_m)], ["High end", both(f.high_m)], ["End mitres", deg(f.end_mitre)]);
  } else {
    for (const [k, v] of Object.entries(f)) if (v !== null && typeof v !== "object" && typeof v !== "boolean") rows.push([U.infoLabel(k), U.infoValue(k, v)]);
    const st = S.data.tables.steps && S.data.tables.steps.findIndex((s) => s.mode === "add" && s.show === p.step);
    if (st >= 0) rows.push(["Build step", `${st + 1}: ${S.data.tables.steps[st].title}`]);
  }
  box.innerHTML = `<h4>${esc(p.name)}</h4><table>${rows.map(([k, v]) => `<tr><td>${esc(k)}</td><td>${esc(String(v))}</td></tr>`).join("")}</table>`;
  vcb(p.tag === "frame" && f.long_m ? "Stick" : "Selected", p.tag === "frame" && f.long_m ? both(f.long_m) : p.name);
}

function renderCutlist() {
  if (!S.data.tables.cards) S.data.tables.cards = legacyCards(S.data.tables);
  renderCards($("#cutlist"), S.data.tables, U, {
    pick: (ids) => { for (const id of ids) { const g = S.pieces.get(id); if (g) S.tagsOff.delete(g.userData.piece.tag); } applyVisibility(); select(ids); },
    colour: (mark) => (S.markList.includes(mark) ? classColour(mark) : null),
  });
}

function renderDeclared() {
  const rows = S.data.tables.declared || [];
  $("#declared").innerHTML = rows.length ? `<table>${rows.map((r) => `<tr><td><b>${esc(r.name)}</b><br><span class="muted">${esc(U.tokens(r.why))}</span></td>` +
    `<td>${esc(U.tokens(r.value))}<br><span class="kind">${esc(r.kind || "")}</span></td></tr>`).join("")}</table>` : `<p class="muted">None.</p>`;
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

// ---------------------------------------------------------------- the dome form: one form per kind of dome
function legacyDefaults(d) {
  // an older server (or the web shim) that knows only the framed-panel dome
  if (d.kinds) return d;
  const form = [{ key: "fc", label: "Geodesic", type: "cut", options: (d.cuts || []).map((c) => [`${c.frequency}|${c.cut}`, `${c.frequency}V ${c.cut}`]) },
    { key: "diameter_m", label: "Diameter", type: "len", min: 2, max: 12, step: 0.05 },
    { key: "skin", label: "Skin", type: "select", options: [["cabin", "Cabin: plywood and shingles"], ["clear", "Greenhouse: clear"], ["none", "None: frame only"]] },
    { key: "windows", label: "Windows", type: "int", min: 0, max: 12, step: 1 },
    ...["door", "skylight", "stove", "porch", "furnish", "people"].map((k) => ({ key: k, label: k.charAt(0).toUpperCase() + k.slice(1), type: "check" }))];
  const presets = Object.entries(d.presets || {}).map(([key, p]) => ({ key, group: "Framed-panel domes", label: p.label, spec: { kind: "panel", ...p.spec } }));
  return { ...d, kinds: { panel: { label: "Framed-panel dome", form } }, presets, default: presets[0] && presets[0].key };
}

function formOf() { return (S.defaults.kinds[S.kind] || S.defaults.kinds.panel || { form: [] }).form; }

function buildForm() {
  const box = $("#fields"); box.innerHTML = "";
  const checks = document.createElement("div"); checks.className = "checks";
  for (const f of formOf()) {
    if (f.type === "check") {
      const l = document.createElement("label");
      l.innerHTML = `<input type="checkbox" data-key="${f.key}"> ${esc(f.label)}`;
      checks.append(l);
      continue;
    }
    const l = document.createElement("label");
    let input;
    if (f.choices && f.type !== "cut" && f.type !== "select") {
      // a solved grid offers these values only (the online copy)
      const fmtc = (v) => (f.type === "len" ? `${U.len(v)}` : String(v));
      input = `<select data-key="${f.key}" data-type="${f.type}" data-choice="1">${f.choices.map((v) => `<option value="${v}">${esc(fmtc(v))}</option>`).join("")}</select>`;
    } else if (f.type === "cut" || f.type === "select") {
      input = `<select data-key="${f.key}" data-type="${f.type}">${f.options.map(([v, t]) => `<option value="${esc(v)}">${esc(t)}</option>`).join("")}</select>`;
    } else if (f.type === "len") {
      input = `<span class="unit"><input type="number" data-key="${f.key}" data-type="len" step="${U.inputStep(f)}" min="${U.toInput(f.min, f)}" max="${U.toInput(f.max, f)}"> <span class="u">${U.inputUnit(f)}</span></span>`;
    } else {
      input = `<input type="number" data-key="${f.key}" data-type="${f.type}" step="${f.step || 1}" min="${f.min ?? ""}" max="${f.max ?? ""}">`;
    }
    l.innerHTML = `${esc(f.label)} ${input}`;
    if (f.fixed) { const el = l.querySelector("[data-key]"); el.disabled = true; l.title = typeof f.fixed === "string" ? f.fixed : "Fixed here"; l.classList.add("fixed"); }
    box.append(l);
  }
  if (checks.children.length) box.append(checks);
}

const fieldOf = (k) => formOf().find((f) => f.key === k);
function fillForm(spec) {
  for (const el of $$("#fields [data-key]")) {
    const k = el.dataset.key, t = el.dataset.type;
    if (el.type === "checkbox") el.checked = !!spec[k];
    else if (el.dataset.choice) { const ch = fieldOf(k).choices; el.value = String(ch.reduce((a, b) => (Math.abs(b - spec[k]) < Math.abs(a - spec[k]) ? b : a), ch[0])); }
    else if (t === "cut") el.value = `${spec.frequency}|${spec.cut}`;
    else if (t === "len") el.value = spec[k] === undefined ? "" : U.toInput(spec[k], fieldOf(k));
    else el.value = spec[k] ?? "";
  }
}
function readForm() {
  const s = { ...S.spec, kind: S.kind };
  for (const el of $$("#fields [data-key]")) {
    const k = el.dataset.key, t = el.dataset.type;
    if (el.disabled) continue;
    if (el.type === "checkbox") s[k] = el.checked;
    else if (el.dataset.choice) s[k] = +el.value;
    else if (t === "cut") { const [f, c] = el.value.split("|"); s.frequency = +f; s.cut = c; }
    else if (t === "len") { const v = U.fromInput(el.value, fieldOf(k)); if (isFinite(v)) s[k] = v; }
    else if (t === "int") s[k] = parseInt(el.value, 10);
    else if (t === "num") s[k] = parseFloat(el.value);
    else s[k] = el.value;
  }
  return s;
}
let formTimer = null;
function formChanged() { clearTimeout(formTimer); formTimer = setTimeout(() => { $("#preset").value = ""; load(readForm(), true); }, 350); }
$("#fields").addEventListener("change", formChanged);

function fillPresets() {
  const groups = new Map();
  for (const p of S.defaults.presets) { if (!groups.has(p.group)) groups.set(p.group, []); groups.get(p.group).push(p); }
  $("#preset").innerHTML = `<option value="">Choose...</option>` + [...groups].map(([g, ps]) =>
    `<optgroup label="${esc(g)}">${ps.map((p) => `<option value="${p.key}">${esc(p.label)}</option>`).join("")}</optgroup>`).join("");
  $("#kind").innerHTML = Object.entries(S.defaults.kinds).map(([k, v]) => `<option value="${k}">${esc(v.label)}</option>`).join("");
}
function syncKindSelect() {
  if ($("#kind").value !== S.kind || !$("#fields").children.length || $("#fields").dataset.kind !== S.kind) {
    $("#kind").value = S.kind; buildForm(); $("#fields").dataset.kind = S.kind;
  }
  fillForm(S.spec);
}
function usePreset(p) {
  if (!p) return;
  S.kind = p.spec.kind || "panel";
  S.spec = { ...p.spec };
  syncKindSelect();
  $("#preset").value = p.key;
  S.scene = "Exterior";
  return load(p.spec).then(() => { if (S.data) goScene(SCENES[0], true); });
}
$("#preset").onchange = () => usePreset(S.defaults.presets.find((p) => p.key === $("#preset").value));
$("#kind").onchange = () => usePreset(S.defaults.presets.find((p) => (p.spec.kind || "panel") === $("#kind").value));

// ---------------------------------------------------------------- units
function renderUnits() {
  $("#units").innerHTML = U.MODES.map(([k, t]) => `<button role="radio" data-u="${k}" aria-checked="${U.get() === k}" class="${U.get() === k ? "on" : ""}">${t}</button>`).join("");
  $$("#units button").forEach((b) => b.onclick = () => U.set(b.dataset.u));
}
U.onChange(() => {
  renderUnits();
  if (!S.data) return;
  buildForm(); fillForm(S.spec);
  renderSummary(); renderInfo(); renderCutlist(); renderDeclared(); build.refresh(); tools.relabel();
  materials.render(); designs.render(); renderExports();
  for (const d of S.dims) d.label.textContent = both(d.a.distanceTo(d.b));
});

// ---------------------------------------------------------------- jobs
async function startJob(kind) {
  try {
    await api(`/api/${kind}`, { spec: readForm() });
    pollJobs();
  } catch (e) { toast(e.message); }
}
let polling = null;
async function pollJobs() {
  let jobs = [];
  try { jobs = await api("/api/jobs"); } catch { return; }
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
  let outs = [];
  try { outs = await api("/api/outputs"); } catch { return; }
  $("#outputs").innerHTML = outs.slice(-8).reverse().map((o) => `<div class="out"><b>${esc(o.folder.split("/").pop())}</b>` +
    o.files.filter((f) => /\.(pdf|png)$/i.test(f)).slice(0, 10).map((f) => `<a href="/api/file?path=${encodeURIComponent(f)}" target="_blank">${esc(f.split("/").pop())}</a>`).join("") + `</div>`).join("");
}
$("#plans").onclick = () => startJob("plans");
$("#showcase").onclick = () => startJob("showcase");
function snapView() {
  renderer.render(scene, camera);
  const a = document.createElement("a");
  a.href = canvas.toDataURL("image/png");
  a.download = `dome-sketch-${S.scene.toLowerCase().replace(/[^a-z0-9]+/g, "-")}.png`;
  a.click();
}
const trial = () => S.defaults && S.defaults.edition === "trial";
$("#printcut").onclick = () => {
  if (trial()) { toast("Printing the cut list is part of the full Dome Sketch."); return; }
  printCards(S.data.tables, U, { colour: (m) => (S.markList.includes(m) ? classColour(m) : null) });
};

// ---------------------------------------------------------------- exports: files to take away
function renderExports() {
  const list = (S.defaults && S.defaults.exports) || [];
  $("#export-menu").innerHTML = list.map(([k, label]) => `<button data-x="${k}" class="pro">${esc(label)}</button>`).join("") +
    `<button data-x="png">This view (PNG)</button>` +
    `<p class="muted small">${trial() ? "Exports come with the full Dome Sketch." : `Lengths in ${U.get() === "m" ? "millimetres" : "inches"} (switch units above). True size; your CAM program adds the kerf.`}</p>`;
  $$("#export-menu [data-x]").forEach((b) => b.onclick = () => { $("#export-menu").hidden = true; b.dataset.x === "png" ? snapView() : exportFile(b.dataset.x); });
}
async function exportFile(format) {
  if (trial()) { toast("Exports come with the full Dome Sketch."); return; }
  toast("Making the file...");
  try {
    if (format === "pack") {
      const r = await api("/api/export-pack", { spec: S.spec });
      toast(`Saved ${r.files.length} files to ${r.folder}.`);
      return;
    }
    const r = await fetch("/api/export", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ spec: S.spec, format, units: U.get(), prices: materials.overrides() }) });
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || r.statusText);
    const name = ((r.headers.get("Content-Disposition") || "").match(/filename="([^"]+)"/) || [])[1] || `dome-sketch-${format}`;
    const url = URL.createObjectURL(await r.blob());
    const a = document.createElement("a"); a.href = url; a.download = name; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
    toast(`Downloaded ${name}.`);
  } catch (e) { toast(e.message); }
}
$("#export-btn").onclick = (ev) => { ev.stopPropagation(); $("#export-menu").hidden = !$("#export-menu").hidden; };
document.addEventListener("click", (ev) => { if (!ev.target.closest(".menu")) $("#export-menu").hidden = true; });

// ---------------------------------------------------------------- toolbar wiring
$$("#ftb [data-tool]").forEach((b) => b.onclick = () => setTool(b.dataset.tool));
$("#extents").onclick = () => zoomExtents();
$("#view").onchange = () => { if ($("#view").value) view($("#view").value); $("#view").value = ""; };
$("#proj").onclick = () => setProjection(camera === persp);
$("#style").onchange = () => { S.style = $("#style").value; applyStyle(); };
$("#theme").onchange = () => { S.theme = $("#theme").value; S.bg = null; matCache.clear(); applyStyle(); };
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

/** One picture of the view as it stands, at a set size, without touching the page's own canvas size. */
function still(width = 1920, height = 1080) {
  const w0 = canvas.clientWidth, h0 = canvas.clientHeight, pr = renderer.getPixelRatio();
  renderer.setPixelRatio(1);
  renderer.setSize(width, height, false);
  persp.aspect = width / height; persp.updateProjectionMatrix();
  if (camera === ortho) { const k = width / height; const hh = ortho.top; ortho.left = -hh * k; ortho.right = hh * k; ortho.updateProjectionMatrix(); }
  controls.update();
  renderer.shadowMap.needsUpdate = true;
  renderer.render(scene, camera);
  const url = canvas.toDataURL("image/png");
  renderer.setPixelRatio(pr);
  renderer.setSize(w0, h0, false);
  persp.aspect = w0 / Math.max(h0, 1); persp.updateProjectionMatrix(); syncOrtho();
  return url;
}

// What the tools, the build guide and the Director need from the modeller.
const ctx = {
  THREE, scene, world, overlay, renderer, persp, controls, canvas, S, U, api, decode, faceMat, edgeMat, sun, hemi, lamp, makePieceGroup,
  hooks: [], post: [], offline: false, renderFrame, applyTransforms, applyVisibility, applyStyle, zoomExtents, bounds, goScene, SCENES, setTool,
  get camera() { return camera; }, setProjection, toast, both, mm, deg, pick, pickGround, snapPoint, screenOf, select, load, still, flyTo,
  esc, renderInfo, renderSummary, classColour, usePreset, renderTags, syncSection, exportFile,
  openSpec(spec) { S.kind = spec.kind || "panel"; S.spec = { ...spec }; $("#preset").value = ""; syncKindSelect(); S.scene = "Exterior";
                   return load(spec).then(() => { if (S.data) goScene(SCENES[0], true); }); },
  setView(v) { S.explode = v.explode ?? S.explode; S.step = v.step ?? S.step; S.door = v.door ?? S.door;
               if (v.tagsOff) S.tagsOff = new Set(v.tagsOff); if (v.style) { S.style = v.style; $("#style").value = v.style; }
               $("#explode").value = S.explode * 100; $("#step").value = S.step; $("#door").value = S.door;
               applyStyle(); applyTransforms(); applyVisibility(); renderTags(); },
};
window.domeSketch = ctx;
const tools = initTools(ctx);
const build = initBuild(ctx);
const materials = initMaterials(ctx);
const designs = initDesigns(ctx);
$("#guide").onclick = () => build.toggle();

// ---------------------------------------------------------------- start
(async function start() {
  renderUnits();
  S.defaults = legacyDefaults(await api("/api/defaults"));
  $("#tag").textContent = S.defaults.tag || "sketch-claude";
  fillPresets();
  let spec = S.defaults.spec;
  const urlSpec = new URLSearchParams(location.search).get("spec");
  if (urlSpec) { try { spec = { ...spec, ...JSON.parse(urlSpec) }; } catch { /* the default dome */ } }
  S.kind = spec.kind || "panel";
  S.spec = spec;
  syncKindSelect();
  const first = S.defaults.presets.find((p) => JSON.stringify(p.spec) === JSON.stringify(spec));
  if (first) $("#preset").value = first.key;
  setTool("select");
  resize();
  requestAnimationFrame(frame);
  await load(spec);
  if (S.data) goScene(SCENES[0], true);   // nothing loaded (the server said why): the page stays usable
  pollJobs();
})();
