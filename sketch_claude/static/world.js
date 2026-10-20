// The Director's world: the same dome, deck and site as Dome Sketch, from the same model, but in
// its own scene with no modelling tools. It is a stage: the engine sets the build stage, the
// explode, the door and which tags show, and the cast and the set stand in it.

import * as THREE from "three";
import { OrbitControls } from "/static/vendor/OrbitControls.js";

export async function createWorld(canvas, spec = {}) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  const scene = new THREE.Scene();
  const persp = new THREE.PerspectiveCamera(38, 16 / 9, 0.05, 500);
  persp.up.set(0, 0, 1);
  persp.position.set(9, -12, 5);
  const controls = new OrbitControls(persp, canvas);
  controls.enableDamping = true;
  controls.screenSpacePanning = true;
  controls.mouseButtons = { LEFT: THREE.MOUSE.ROTATE, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.PAN };

  const hemi = new THREE.HemisphereLight(0xf4f1ea, 0x8d8576, 1.25);
  hemi.position.set(0, 0, 1);
  const sun = new THREE.DirectionalLight(0xfff6e8, 1.7);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.02;
  Object.assign(sun.shadow.camera, { left: -14, right: 14, top: 14, bottom: -14, near: 0.5, far: 80 });
  const lamp = new THREE.PointLight(0xffd59a, 5, 9, 1.4);
  lamp.position.set(0, -0.05, 1.8);
  scene.add(hemi, sun, sun.target, lamp);
  const sky = document.createElement("canvas"); sky.width = 2; sky.height = 256;
  const g = sky.getContext("2d"), grad = g.createLinearGradient(0, 0, 0, 256);
  grad.addColorStop(0, "#9cc2e6"); grad.addColorStop(0.55, "#dbe7f0"); grad.addColorStop(1, "#f1ede4");
  g.fillStyle = grad; g.fillRect(0, 0, 2, 256);
  scene.background = new THREE.CanvasTexture(sky); scene.background.colorSpace = THREE.SRGBColorSpace;
  // moods: the sky, the sun, the fill and the lamps, for a scene's time and feeling
  const MOODS = {
    day:      { sky: ["#9cc2e6", "#dbe7f0", "#f1ede4"], hemi: 1.25, sun: 1.7, sunCol: 0xfff6e8, lamp: 0, fog: null },
    golden:   { sky: ["#6d7fb0", "#f2b27a", "#f6d7a8"], hemi: 0.95, sun: 2.1, sunCol: 0xffc48a, lamp: 2, fog: null },
    dusk:     { sky: ["#2e3a66", "#a8607a", "#e59a6e"], hemi: 0.65, sun: 0.9, sunCol: 0xff9a6a, lamp: 6, fog: [0x3a3550, 0.02] },
    night:    { sky: ["#05070f", "#141c36", "#283048"], hemi: 0.32, sun: 0.35, sunCol: 0x8fa6ff, lamp: 9, fog: [0x101629, 0.035] },
    overcast: { sky: ["#8e959e", "#b9bec4", "#d6d8d8"], hemi: 1.15, sun: 0.6, sunCol: 0xe8eef2, lamp: 1, fog: [0xb9bec4, 0.015] },
    storm:    { sky: ["#2a2f36", "#4a5058", "#6a6f72"], hemi: 0.6, sun: 0.25, sunCol: 0xc8d4ff, lamp: 4, fog: [0x4a5058, 0.05] },
  };
  function setMood(name = "day") {
    const m = MOODS[name] || MOODS.day;
    const gg = sky.getContext("2d"), gr = gg.createLinearGradient(0, 0, 0, 256);
    gr.addColorStop(0, m.sky[0]); gr.addColorStop(0.55, m.sky[1]); gr.addColorStop(1, m.sky[2]);
    gg.fillStyle = gr; gg.fillRect(0, 0, 2, 256); scene.background.needsUpdate = true;
    hemi.intensity = m.hemi; sun.intensity = m.sun; sun.color.setHex(m.sunCol); lamp.intensity = m.lamp;
    scene.fog = m.fog ? new THREE.FogExp2(m.fog[0], m.fog[1]) : null;
    ctx.mood = name;
  }
  // a wider lawn than the modeller's site disc, for the house, the studio and the hedge
  const lawn = new THREE.Mesh(new THREE.CircleGeometry(60, 64), new THREE.MeshLambertMaterial({ color: "#8fa66b" }));
  lawn.position.z = -0.47; lawn.receiveShadow = true; scene.add(lawn);

  const world = new THREE.Group(); scene.add(world);
  const edgeMat = new THREE.LineBasicMaterial({ color: 0x1d1b18 });
  const edgeSoft = new THREE.LineBasicMaterial({ color: 0x1d1b18, transparent: true, opacity: 0.3 });
  const S = { data: null, spec: null, pieces: new Map(), step: 999, explode: 0, door: 0, tagsOff: new Set(["site"]) };
  const mats = new Map();
  const faceMat = (key) => {
    if (mats.has(key)) return mats.get(key);
    const d = (S.data?.materials || {})[key] || { color: "#cccccc" }, op = d.opacity ?? 1;
    const m = new THREE.MeshLambertMaterial({ color: d.color, transparent: op < 1, opacity: op, side: THREE.DoubleSide,
                                             polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1, depthWrite: op >= 1 });
    if (d.emissive) m.emissive = new THREE.Color(d.color).multiplyScalar(0.9);
    mats.set(key, m); return m;
  };
  const decode = (b64, T) => { const bin = atob(b64), buf = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i); return new T(buf.buffer); };
  function makePieceGroup(p) {
    const v = decode(p.v, Float32Array), t = decode(p.t, Uint32Array), e = decode(p.e, Uint32Array), grp = new THREE.Group();
    grp.userData.piece = p;
    if (t.length) {
      const pos = new Float32Array(t.length * 3);
      for (let i = 0; i < t.length; i++) for (let c = 0; c < 3; c++) pos[i * 3 + c] = v[t[i] * 3 + c];
      const geo = new THREE.BufferGeometry(); geo.setAttribute("position", new THREE.BufferAttribute(pos, 3)); geo.computeVertexNormals();
      const mesh = new THREE.Mesh(geo, faceMat(p.material));
      mesh.castShadow = p.tag !== "site" && p.tag !== "glass"; mesh.receiveShadow = true; grp.add(mesh);
    }
    if (e.length && p.tag !== "site") {
      const lp = new Float32Array(e.length * 3);
      for (let i = 0; i < e.length; i++) for (let c = 0; c < 3; c++) lp[i * 3 + c] = v[e[i] * 3 + c];
      const lg = new THREE.BufferGeometry(); lg.setAttribute("position", new THREE.BufferAttribute(lp, 3));
      grp.add(new THREE.LineSegments(lg, p.tag === "skin" || p.tag === "glass" ? edgeSoft : edgeMat));
    }
    return grp;
  }
  async function api(path, body) {
    const r = await fetch(path, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const j = await r.json(); if (!r.ok) throw new Error(j.error || r.statusText); return j;
  }
  async function load(sp) {
    const data = await api("/api/model", { spec: sp });
    S.data = data; S.spec = data.spec; mats.clear(); world.clear(); S.pieces.clear();
    for (const p of data.pieces) { const grp = makePieceGroup(p); grp.matrixAutoUpdate = false; world.add(grp); S.pieces.set(p.id, grp); }
    apply();
  }
  function apply() {
    const d = S.data.tables.door, hinge = d ? new THREE.Vector3(-d.W / 2, d.y_post, 0) : null;
    const m = new THREE.Matrix4(), a = new THREE.Matrix4(), b = new THREE.Matrix4(), c = new THREE.Matrix4();
    for (const grp of S.pieces.values()) {
      const p = grp.userData.piece;
      grp.visible = !S.tagsOff.has(p.tag) && p.step <= S.step;
      m.makeTranslation(p.explode[0] * S.explode, p.explode[1] * S.explode, p.explode[2] * S.explode);
      if (p.group === "door-leaf" && hinge && S.door) { a.makeTranslation(hinge.x, hinge.y, 0); b.makeRotationZ(-S.door * Math.PI / 180); c.makeTranslation(-hinge.x, -hinge.y, 0); m.multiply(a).multiply(b).multiply(c); }
      grp.matrix.copy(m); grp.matrixWorldNeedsUpdate = true;
    }
  }
  function setView(v = {}) {
    if (v.step !== undefined) S.step = v.step;
    if (v.explode !== undefined) S.explode = v.explode;
    if (v.door !== undefined) S.door = v.door;
    if (v.tagsOff) S.tagsOff = new Set([...v.tagsOff, "site"]);
    apply();
  }
  function placeSun(az = 300, el = 48) {
    const A = az * Math.PI / 180, E = el * Math.PI / 180;
    sun.position.set(Math.cos(A) * Math.cos(E) * 30, Math.sin(A) * Math.cos(E) * 30, Math.sin(E) * 30);
    sun.target.position.set(0, 0, 0);
  }
  placeSun();
  const ctx = {
    THREE, scene, world, renderer, persp, controls, canvas, S, api, decode, makePieceGroup, faceMat: (k) => faceMat(k), edgeMat,
    sun, hemi, lamp, hooks: [], post: [], offline: false, load, setView, placeSun, setMood, mood: "day",
    get camera() { return persp; }, setProjection() {}, toast: (m) => console.log(m),
    renderFrame(dt, now) {
      for (const h of ctx.hooks) h(dt, now);
      if (controls.enabled) controls.update();
      renderer.render(scene, persp);
      for (const h of ctx.post) h(dt, now);
    },
    step(dt, now) { for (const h of ctx.hooks) h(dt, now); },       // a dry run: the world moves, nothing is drawn
    resize(w, h) {
      renderer.setSize(w, h, false);
      persp.aspect = w / Math.max(1, h); persp.updateProjectionMatrix();
    },
  };
  await load(spec);
  return ctx;
}
