// @ts-nocheck
// Storytime: a bedtime story told in a 3-D world, on a tablet, out loud.
//
// The world is built the way the Episode Director builds its stages (sketch_claude/static): a sky
// that changes with the mood, a lawn, the solver's own 2V wedge dome (the Portal's mesh, from
// geodesic_raw_wedge_dome_dihedral.py) with every member revealable ring by ring, the cast's
// articulated characters, and the Director's camera moves. Each page of the story is a scene: a
// place, the people in it, what they do, and a slow camera move timed to the page's narration.
// The narration is pre-recorded (scripts/export_storytime.py) with word timings for read-along.

import * as THREE from "three";
import { Character } from "./cast";
import { makeShots, fovForLens, EASE } from "./shots";
import wedgeData from "../generated/wedge-method.json";

const V = (x, y, z) => new THREE.Vector3(x, y, z);
const IN = 0.0254;

// ------------------------------------------------------------------ the people
export const PEOPLE = {
  pip:    { name: "Pip", height: 1.15, skin: "#dca27a", shirt: "#d6463a", shirt2: "#b53a30", pants: "#3f4f78", hair: "#4d2410", hairStyle: "long", skirt: "#d6463a", bucketHat: "#2f7a4b", belly: 0.9 },
  boy:    { name: "the boy", height: 1.15, skin: "#9e6c4c", shirt: "#4277c7", shirt2: "#2f5a9e", pants: "#4d4d5a", hair: "#1d140e", hairStyle: "buzz", belly: 0.92 },
  n1:     { name: "a neighbour", height: 1.72, skin: "#e3b391", shirt: "#9b4d8c", shirt2: "#7a3a6e", pants: "#3a3d4c", hair: "#6b4a2e", hairStyle: "short", belly: 1.05 },
  n2:     { name: "a neighbour", height: 1.12, skin: "#80573e", shirt: "#d9692f", shirt2: "#b5552a", pants: "#2e5157", hair: "#1d140e", hairStyle: "curly", belly: 0.9 },
  n3:     { name: "a neighbour", height: 1.7, skin: "#c79470", shirt: "#62a05a", shirt2: "#4a8044", pants: "#5b4630", hair: "#2a1a12", hairStyle: "bun", belly: 1.0 },
  n4:     { name: "a neighbour", height: 1.1, skin: "#ad805c", shirt: "#e9e5da", shirt2: "#c9c4b8", pants: "#33337a", hair: "#4a2e1c", hairStyle: "ponytail", belly: 0.88 },
  mama:   { name: "Mama", height: 1.62, skin: "#c99572", shirt: "#7fa9c9", shirt2: "#5f89a9", pants: "#3a3f52", hair: "#1d140e", hairStyle: "long", belly: 0.92 },
  annika: { name: "Annika", height: 1.12, skin: "#c99572", shirt: "#f2c94c", shirt2: "#d9ae36", pants: "#5a6b8f", hair: "#1d140e", hairStyle: "long", belly: 0.88 },
  arama:  { name: "Arama", height: 0.98, skin: "#c99572", shirt: "#7cc7a8", shirt2: "#5fae8e", pants: "#5a6b8f", hair: "#1d140e", hairStyle: "curly", belly: 0.88 },
  dada:   { name: "Dada", height: 1.82, skin: "#e0ac86", shirt: "#26324f", shirt2: "#1b243a", pants: "#3a3f52", hair: "#4a3020", hairStyle: "short", beard: "#17120e", beardStyle: "scruff", sailorCap: true, belly: 1.0 },
};

// ------------------------------------------------------------------ moods: sky, sun, fill, fog
const MOODS = {
  day:    { sky: ["#8fbde8", "#d6e8f2", "#f3efe2"], hemi: 1.2, sun: 1.7, sunCol: 0xfff3dd, fog: [0xd6e8f2, 0.012], sunAt: [-0.5, -0.7, 0.75] },
  golden: { sky: ["#6f7db4", "#f0ad78", "#f8dcab"], hemi: 0.95, sun: 2.0, sunCol: 0xffc48a, fog: [0xf0c49a, 0.016], sunAt: [-0.85, -0.4, 0.3] },
  dusk:   { sky: ["#2d3766", "#a65f7c", "#e89a6c"], hemi: 0.6, sun: 0.9, sunCol: 0xff9f74, fog: [0x6a5070, 0.02], sunAt: [-0.9, 0.2, 0.12] },
  night:  { sky: ["#040712", "#0f1834", "#25304d"], hemi: 0.35, sun: 0.5, sunCol: 0x9fb2ff, fog: [0x0f1834, 0.022], sunAt: [0.4, 0.6, 0.7] },
  dream:  { sky: ["#8e7fc9", "#f2b8c9", "#fde8d0"], hemi: 1.3, sun: 1.2, sunCol: 0xffe2f0, fog: [0xf2c8d8, 0.02], sunAt: [-0.5, -0.6, 0.6] },
  blossom:{ sky: ["#9fc5ea", "#f6d6e4", "#fbeee6"], hemi: 1.25, sun: 1.5, sunCol: 0xfff0f4, fog: [0xf6dbe6, 0.03], sunAt: [-0.4, -0.7, 0.7] },
  lamp:   { sky: ["#05070f", "#0d1328", "#1a2038"], hemi: 0.25, sun: 0.0, sunCol: 0x9fb2ff, fog: null, sunAt: [0.4, 0.6, 0.7] },
};

export class Storyworld {
  constructor(canvas) {
    this.canvas = canvas;
    // tablets: a capped pixel ratio and a modest shadow map keep it smooth and cool
    const r = this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: "high-performance" });
    r.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
    r.shadowMap.enabled = true; r.shadowMap.type = THREE.PCFSoftShadowMap;
    r.outputColorSpace = THREE.SRGBColorSpace;
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(40, 1, 0.05, 900);
    this.camera.up.set(0, 0, 1);
    this.hemi = new THREE.HemisphereLight(0xf4f1ea, 0x6f6658, 1.2); this.hemi.position.set(0, 0, 1);
    this.sun = new THREE.DirectionalLight(0xfff3dd, 1.7); this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(1024, 1024); this.sun.shadow.bias = -0.0005; this.sun.shadow.normalBias = 0.03;
    Object.assign(this.sun.shadow.camera, { left: -16, right: 16, top: 16, bottom: -16, near: 1, far: 120 });
    this.fill = new THREE.DirectionalLight(0xfff1e0, 0.55);
    this.scene.add(this.hemi, this.sun, this.sun.target, this.fill, this.fill.target);
    this.skyCanvas = document.createElement("canvas"); this.skyCanvas.width = 2; this.skyCanvas.height = 256;
    this.skyTex = new THREE.CanvasTexture(this.skyCanvas); this.skyTex.colorSpace = THREE.SRGBColorSpace;
    this.scene.background = this.skyTex;
    this.shots = makeShots(THREE);
    this.hooks = [];
    this.cast = {};
    this.time = 0;
    this.stars = this.makeStars();
    this.places = {};
    this.temp = [];
    this.tick = null;
  }

  // -------------------------------------------------------------- the sky and the light
  mood(name, focus = V(0, 0, 0)) {
    const m = MOODS[name] || MOODS.day;
    const g = this.skyCanvas.getContext("2d"), gr = g.createLinearGradient(0, 0, 0, 256);
    gr.addColorStop(0, m.sky[0]); gr.addColorStop(0.55, m.sky[1]); gr.addColorStop(1, m.sky[2]);
    g.fillStyle = gr; g.fillRect(0, 0, 2, 256); this.skyTex.needsUpdate = true;
    this.hemi.intensity = m.hemi; this.sun.intensity = m.sun; this.sun.color.setHex(m.sunCol);
    this.sun.position.copy(focus).add(V(...m.sunAt).multiplyScalar(40)); this.sun.target.position.copy(focus);
    this.scene.fog = m.fog ? new THREE.FogExp2(m.fog[0], m.fog[1]) : null;
    this.stars.visible = name === "night" || name === "lamp";
    this.stars.position.copy(focus); this.stars.updateMatrixWorld(true);
    this.moodName = name;
  }

  makeStars() {
    const n = 900, pos = new Float32Array(n * 3), sizes = [];
    let seed = 7; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    for (let i = 0; i < n; i++) {
      const a = rnd() * Math.PI * 2, e = 0.12 + rnd() * 1.35, R = 180;
      pos.set([Math.cos(a) * Math.cos(e) * R, Math.sin(a) * Math.cos(e) * R, Math.sin(e) * R], i * 3);
    }
    const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    const pts = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xfff6dc, size: 1.4, sizeAttenuation: false, fog: false }));
    const grp = new THREE.Group(); grp.add(pts);
    // the moon, and Dada's star: the brightest one, that blinks hello
    const moon = new THREE.Mesh(new THREE.SphereGeometry(6, 24, 16), new THREE.MeshBasicMaterial({ color: 0xfaf2d4, fog: false }));
    moon.position.set(110, 90, 75); grp.add(moon);
    const star = this.dadaStar = new THREE.Sprite(new THREE.SpriteMaterial({ map: starTexture(), color: 0xfff1c0, fog: false, depthWrite: false, transparent: true }));
    star.position.set(-40, 120, 95); star.scale.set(16, 16, 1); grp.add(star);
    grp.visible = false;
    this.scene.add(grp);
    this.hooks.push((dt) => { const s = 14 + 4 * Math.sin(this.time * 2.2) + 2 * Math.sin(this.time * 5.1); star.scale.set(s, s, 1); });
    return grp;
  }

  // -------------------------------------------------------------- materials and simple shapes
  mat(c, opts = {}) { return new THREE.MeshLambertMaterial({ color: c, flatShading: true, ...opts }); }
  box(parent, x, y, z, sx, sy, sz, c, opts) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), this.mat(c, opts)); m.position.set(x, y, z);
    m.castShadow = true; m.receiveShadow = true; parent.add(m); return m;
  }
  cyl(parent, a, b, r, c, seg = 18, r1) {
    const A = V(...a), B = V(...b), d = B.clone().sub(A), L = d.length();
    const m = new THREE.Mesh(new THREE.CylinderGeometry(r1 ?? r, r, L, seg), this.mat(c));
    m.position.copy(A).add(B).multiplyScalar(0.5);
    m.quaternion.setFromUnitVectors(V(0, 1, 0), d.normalize());
    m.castShadow = true; m.receiveShadow = true; parent.add(m); return m;
  }
  ball(parent, x, y, z, r, c, opts) { const m = new THREE.Mesh(new THREE.SphereGeometry(r, 14, 10), this.mat(c, opts)); m.position.set(x, y, z); m.castShadow = true; parent.add(m); return m; }
  label(text, { w = 2, h = 1, bg = null, fg = "#fff", font = "bold 120px Georgia", lines = null } = {}) {
    const c = document.createElement("canvas"); c.width = 1024; c.height = Math.round(1024 * h / w);
    const g = c.getContext("2d");
    if (bg) { g.fillStyle = bg; g.fillRect(0, 0, c.width, c.height); }
    g.fillStyle = fg; g.textAlign = "center"; g.textBaseline = "middle"; g.font = font;
    const L = lines || [text];
    L.forEach((t, i) => g.fillText(t, c.width / 2, c.height * (i + 0.5) / L.length));
    const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
    return new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: tex, transparent: !bg }));
  }

  // -------------------------------------------------------------- the solver's wedge dome
  async loadDome() {
    const head = wedgeData.meshes.point_dome_out;
    const buf = await fetch(head.file).then((r) => r.arrayBuffer());
    const Vn = head.vertices, off = Vn * 6 + Vn + (Vn % 2);
    const pos = new Int16Array(buf, 0, Vn * 3), idx = new Uint16Array(buf, off, head.indices);
    const members = head.parts.filter((p) => p.kind === "member" || p.kind === "key");
    // centre on the members' footprint, ground on their lowest point; inches to metres
    let lo = V(Infinity, Infinity, Infinity), hi = V(-Infinity, -Infinity, -Infinity);
    for (const p of members) for (let k = p.v[0]; k < p.v[0] + p.v[1]; k++) { const q = V(pos[k * 3], pos[k * 3 + 1], pos[k * 3 + 2]).multiplyScalar(head.scale); lo.min(q); hi.max(q); }
    const o = V((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z);
    this.domeRadius = Math.max(hi.x - lo.x, hi.y - lo.y) / 2 * IN;
    this.domeHeight = (hi.z - lo.z) * IN;
    // every member and key in one geometry, sorted bottom to top, so a dome draws in one call and
    // "built so far" is just how many of its triangles are drawn
    const woods = ["#d8b07a", "#cfa46c", "#e0b986", "#c9995f"].map((c) => new THREE.Color(c)), keyCol = new THREE.Color("#8a6440");
    const parts = members.map((p) => {
      let cz = 0; for (let k = p.v[0]; k < p.v[0] + p.v[1]; k++) cz += pos[k * 3 + 2];
      return { p, z: cz / p.v[1] };
    }).sort((a, b) => a.z - b.z);
    const nv = parts.reduce((n, q) => n + q.p.v[1], 0), ni = parts.reduce((n, q) => n + q.p.i[1], 0);
    const P = new Float32Array(nv * 3), C = new Float32Array(nv * 3), I = new Uint32Array(ni);
    this.domeSteps = [];
    let vo = 0, io = 0;
    for (const { p } of parts) {
      const [v0, vn] = p.v, [i0, inn] = p.i, col = p.kind === "key" ? keyCol : woods[(p.face || 0) % woods.length];
      for (let k = 0; k < vn; k++) {
        for (let c = 0; c < 3; c++) P[(vo + k) * 3 + c] = (pos[(v0 + k) * 3 + c] * head.scale - o.getComponent(c)) * IN;
        C.set([col.r, col.g, col.b], (vo + k) * 3);
      }
      for (let k = 0; k < inn; k++) I[io + k] = idx[i0 + k] - v0 + vo;
      vo += vn; io += inn; this.domeSteps.push(io);
    }
    const g = this.domeGeo = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(P, 3)); g.setAttribute("color", new THREE.BufferAttribute(C, 3));
    g.setIndex(new THREE.BufferAttribute(I, 1)); g.computeVertexNormals();
  }

  /** A dome: the whole frame, or (own: true) one whose build can be shown part way, bottom up. */
  makeDome(opts = {}) {
    const geo = opts.own ? this.domeGeo.clone() : this.domeGeo;
    const mat = opts.ghost
      ? new THREE.MeshLambertMaterial({ vertexColors: true, flatShading: true, transparent: true, opacity: 0.5, emissive: new THREE.Color("#ffd7a0"), emissiveIntensity: 0.4, depthWrite: false })
      : new THREE.MeshLambertMaterial({ vertexColors: true, flatShading: true });
    const m = new THREE.Mesh(geo, mat); m.castShadow = !opts.ghost; m.receiveShadow = true;
    m.userData.build = (f) => {
      const n = this.domeSteps.length, k = Math.floor(n * Math.max(0, Math.min(1, f)));
      geo.setDrawRange(0, k >= n ? Infinity : k > 0 ? this.domeSteps[k - 1] : 0);
    };
    return m;
  }

  // -------------------------------------------------------------- the places
  build() {
    const S = this.scene;
    const hill = this.places.hill = new THREE.Group(); S.add(hill);
    const lawn = new THREE.Mesh(new THREE.CircleGeometry(70, 64), this.mat("#8fb066"));
    lawn.receiveShadow = true; hill.add(lawn);
    this.dome = this.makeDome({ own: true }); hill.add(this.dome);
    this.domeWest = this.makeDome(); this.domeWest.position.set(-9.5, 4.5, 0); hill.add(this.domeWest);
    this.domeEast = this.makeDome(); this.domeEast.position.set(9.5, 3.5, 0); hill.add(this.domeEast);
    this.dreamDome = this.makeDome({ ghost: true }); hill.add(this.dreamDome);
    this.glow = [0, 1, 2].map(() => { const l = new THREE.PointLight(0xffc88a, 0, 10, 1.5); hill.add(l); return l; });
    this.glow[0].position.set(0, 0, 1.3); this.glow[1].position.set(-9.5, 4.5, 1.3); this.glow[2].position.set(9.5, 3.5, 1.3);
    this.town = this.makeTown(); hill.add(this.town);
    this.lumber = this.makeLumber(); hill.add(this.lumber);
    // the fallen pine, the stump and the tools
    const log = this.log = new THREE.Group(); log.position.set(-6.4, 3.2, 0.38); hill.add(log);
    this.cyl(log, [-2.1, 0, 0], [2.1, 0, 0], 0.38, "#7a5236", 20);
    for (const x of [-2.11, 2.11]) { const e = new THREE.Mesh(new THREE.CircleGeometry(0.36, 20), this.mat("#e7c894")); e.position.set(x, 0, 0); e.rotation.y = Math.PI / 2; log.add(e); }
    this.wedgesSplit = this.makeWedges(); this.wedgesSplit.position.copy(log.position); hill.add(this.wedgesSplit);
    const stump = this.stump = new THREE.Group(); stump.position.set(-4.3, -3.4, 0); hill.add(stump);
    this.cyl(stump, [0, 0, 0], [0, 0, 0.5], 0.45, "#6e4b31", 18);
    const top = new THREE.Mesh(new THREE.CircleGeometry(0.44, 18), this.mat("#e2c08c")); top.position.z = 0.501; stump.add(top);
    this.box(stump, 0.15, -0.1, 0.53, 0.6, 0.06, 0.06, "#f0c22c");              // level
    this.cyl(stump, [-0.2, 0.18, 0.5], [-0.2, 0.18, 0.56], 0.07, "#f0b81c");   // tape
    this.box(stump, 0.1, 0.25, 0.55, 0.12, 0.09, 0.1, "#3a6fd1");             // chalk line
    this.box(stump, -0.6, -0.5, 0.11, 0.34, 0.2, 0.22, "#d0372c");            // lunch box
    this.box(stump, -0.6, -0.5, 0.235, 0.16, 0.03, 0.03, "#333");
    this.box(stump, 0.55, -0.55, 0.03, 0.7, 0.1, 0.02, "#b9bcc0");            // the saw blade
    this.box(stump, 0.15, -0.55, 0.05, 0.16, 0.1, 0.06, "#c8432f");          // its handle
    // the stack of wedges, and the chalkboard
    const stack = this.stack = new THREE.Group(); stack.position.set(4.6, 2.4, 0); hill.add(stack);
    for (let row = 0; row < 3; row++) for (let k = 0; k < 6 - row; k++) {
      const w = this.wedgeStick(1.6); w.position.set(-0.6 + k * 0.24 + row * 0.12, 0, 0.09 + row * 0.17); w.rotation.z = Math.PI / 2; stack.add(w);
    }
    const board = this.board = new THREE.Group(); board.position.set(3.0, 4.6, 0); hill.add(board);
    this.cyl(board, [0, 0.07, 0], [0, 0.07, 0.85], 0.04, "#5b3b22", 8);
    this.box(board, 0, 0, 1.3, 1.6, 0.06, 1.0, "#1f3a2c");
    this.panel = this.makeLoosePanel(); this.panel.position.set(-0.8, -6.6, 0.02); hill.add(this.panel);
    // the intro's places, each far from the hill and from each other
    this.places.night = this.makeNightHill(V(0, -320, 0));
    this.places.sea = this.makeSea(V(320, 0, 0));
    this.places.blossoms = this.makeBlossoms(V(-320, 0, 0));
    this.places.bench = this.makeBench(V(0, 320, 0));
  }

  wedgeStick(L) {
    // a wedge, as split from the log: a long triangular prism
    const s = new THREE.Shape(); s.moveTo(-0.1, 0); s.lineTo(0.1, 0); s.lineTo(0, 0.17); s.lineTo(-0.1, 0);
    const g = new THREE.ExtrudeGeometry(s, { depth: L, bevelEnabled: false }); g.translate(0, 0, -L / 2); g.rotateY(Math.PI / 2);
    const m = new THREE.Mesh(g, this.mat("#d8b07a")); m.castShadow = true; return m;
  }

  makeWedges() {
    // the log split into eight, like slices of pie; each piece drifts out from the middle
    const g = new THREE.Group(); g.visible = false; g.userData.pieces = [];
    for (let k = 0; k < 8; k++) {
      const a0 = (k / 8) * Math.PI * 2, a1 = ((k + 1) / 8) * Math.PI * 2, s = new THREE.Shape();
      s.moveTo(0, 0); s.lineTo(Math.cos(a0) * 0.38, Math.sin(a0) * 0.38); s.absarc(0, 0, 0.38, a0, a1, false); s.lineTo(0, 0);
      const geo = new THREE.ExtrudeGeometry(s, { depth: 4.2, bevelEnabled: false, curveSegments: 4 }); geo.translate(0, 0, -2.1); geo.rotateY(Math.PI / 2);
      const m = new THREE.Mesh(geo, [this.mat("#e7c894"), this.mat(k % 2 ? "#7a5236" : "#6e4b31")]); m.castShadow = true;
      m.userData.dir = V(0, Math.cos((a0 + a1) / 2), Math.sin((a0 + a1) / 2));
      g.add(m); g.userData.pieces.push(m);
    }
    g.userData.split = (f) => g.userData.pieces.forEach((m) => m.position.copy(m.userData.dir).multiplyScalar(0.8 * f).add(V(0, 0, 0.35 * f * Math.max(0, m.userData.dir.z))));
    return g;
  }

  makeLoosePanel() {
    const g = new THREE.Group(), s = 1.7;
    for (const [a, b] of [[[-s / 2, 0], [s / 2, -0.1]], [[s / 2, -0.1], [0.05, s * 0.8]], [[0.05, s * 0.8], [-s / 2, 0]]]) {
      const w = this.wedgeStick(Math.hypot(b[0] - a[0], b[1] - a[1]));
      w.position.set((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 0.06); w.rotation.z = Math.atan2(b[1] - a[1], b[0] - a[0]); g.add(w);
    }
    return g;
  }

  makeTown(seed = 3) {
    const g = new THREE.Group();
    let s = seed * 7919; const rnd = () => ((s = (s * 16807) % 2147483647) / 2147483647);
    const greys = ["#9e9ea3", "#b3ab9a", "#8c9199", "#bbb7ad", "#9a8f84"];
    for (let k = 0; k < 70; k++) {
      const a = rnd() * Math.PI * 2, r = 11 + rnd() * 16, x = Math.cos(a) * r, y = Math.sin(a) * r;
      const w = 1.4 + rnd() * 1.2, d = 1.4 + rnd() * 1.2, floors = 1 + Math.floor(rnd() * 3);
      let z = 0;
      for (let f = 0; f < floors; f++) {
        const h = 1.3 + rnd() * 0.8, sc = 1 - 0.08 * f;
        this.box(g, x, y, z + h / 2, w * sc, d * sc, h, greys[Math.floor(rnd() * greys.length)]);
        for (const wx of [-0.25, 0.25]) this.box(g, x + wx * w, y - (d * sc) / 2 - 0.01, z + h * 0.55, 0.32, 0.03, 0.42, "#4c5566");
        z += h;
      }
    }
    return g;
  }

  makeLumber() {
    const g = new THREE.Group(); g.position.set(6.5, -7.5, 0);
    for (let row = 0; row < 3; row++) for (let col = 0; col < 2; col++) {
      const x0 = col * 1.8, y0 = row * 1.3;
      for (let l = 0; l < 6; l++) this.box(g, x0, y0, 0.12 + l * 0.16, 1.4, 0.95, 0.14, "#dcb781");
      const wrap = this.box(g, x0, y0, 0.55, 1.46, 1.0, 1.02, "#d4e2ea", { transparent: true, opacity: 0.5 }); wrap.castShadow = false;
      this.box(g, x0 - 0.5, y0 - 0.51, 0.75, 0.16, 0.02, 0.22, "#d0372c");
    }
    return g;
  }

  makeNightHill(at) {
    const g = new THREE.Group(); g.position.copy(at); this.scene.add(g);
    const lawn = new THREE.Mesh(new THREE.CircleGeometry(60, 48), this.mat("#2f4a33")); lawn.receiveShadow = true; g.add(lawn);
    const blanket = this.box(g, 0, 0, 0.02, 2.4, 1.8, 0.04, "#7d5aa8");
    this.box(g, 0, 0, 0.045, 2.2, 0.1, 0.01, "#f2d36b");
    this.box(g, 4, 6, 1.0, 0.25, 0.25, 2.0, "#5a4a3a");                       // a little fence post, a lamp
    const lamp = this.ball(g, 4, 6, 2.1, 0.14, "#ffd59a", { emissive: new THREE.Color("#ffb060"), emissiveIntensity: 1 });
    const l = new THREE.PointLight(0xffc88a, 4, 10, 1.5); l.position.set(4, 6, 2.0); g.add(l);
    for (let k = 0; k < 6; k++) this.ball(g, -6 + k * 2.4, 9 + (k % 2), 0.8, 1.0 + (k % 3) * 0.3, "#3e5b34");
    return g;
  }

  makeSea(at) {
    const g = new THREE.Group(); g.position.copy(at); this.scene.add(g);
    const geo = new THREE.PlaneGeometry(260, 260, 80, 80);
    const sea = new THREE.Mesh(geo, new THREE.MeshLambertMaterial({ color: "#244a7a", flatShading: true })); sea.position.z = 0.0; g.add(sea);
    const base = geo.attributes.position.array.slice();
    this.hooks.push(() => {
      if (!g.visible) return;
      const p = geo.attributes.position.array, t = this.time;
      for (let i = 0; i < p.length; i += 3) p[i + 2] = base[i + 2] + Math.sin(base[i] * 0.18 + t * 1.3) * 0.25 + Math.cos(base[i + 1] * 0.23 + t * 0.9) * 0.2;
      geo.attributes.position.needsUpdate = true; geo.computeVertexNormals();
    });
    // the ship: a hull, a cabin, a mast and a sail, rocking on the swell
    const ship = this.ship = new THREE.Group(); g.add(ship);
    this.box(ship, 0, 0, 0.5, 7, 2.2, 1.2, "#7a2f2a");
    this.box(ship, 0, 0, 1.15, 7.2, 2.3, 0.12, "#e8dcc2");
    this.box(ship, -1.2, 0, 1.8, 2.2, 1.6, 1.2, "#e8dcc2");
    for (const [x, n] of [[-1.7, 3], [-1.2, 3], [-0.7, 3]]) this.ball(ship, x, -0.81, 1.9, 0.12, "#ffd98a", { emissive: new THREE.Color("#ffb85a"), emissiveIntensity: 1 });
    this.cyl(ship, [1.4, 0, 1.2], [1.4, 0, 7.5], 0.1, "#5a3a22", 8);
    const sail = new THREE.Mesh(new THREE.PlaneGeometry(3, 4.6), this.mat("#f4efe2", { side: THREE.DoubleSide })); sail.position.set(1.4, 0.05, 4.6); sail.rotation.x = Math.PI / 2; ship.add(sail);
    const light = new THREE.PointLight(0xffc88a, 4, 12, 1.5); light.position.set(-1.2, -1.2, 2); ship.add(light);
    this.sailor = new Character(THREE, "dada-sailor", PEOPLE.dada, ship); this.sailor.place(2.6, 0.2, 90); this.sailor.root.position.z = 1.21; this.sailor.ground = () => 1.21;
    this.hooks.push((dt) => { if (!g.visible) return; const t = this.time; ship.rotation.x = Math.sin(t * 0.9) * 0.06; ship.rotation.y = Math.sin(t * 0.7) * 0.03; ship.position.z = Math.sin(t * 1.1) * 0.15; this.sailor.update(dt); });
    // a lighthouse on a rock, its beam turning
    const lh = new THREE.Group(); lh.position.set(-26, 34, 0); g.add(lh);
    this.ball(lh, 0, 0, 0, 4, "#4a4a4a");
    this.cyl(lh, [0, 0, 2], [0, 0, 12], 1.2, "#f2f0ea", 16, 0.9);
    this.cyl(lh, [0, 0, 6], [0, 0, 7.5], 1.06, "#c8432f", 16);
    this.ball(lh, 0, 0, 12.6, 0.8, "#ffe9a8", { emissive: new THREE.Color("#ffd46a"), emissiveIntensity: 1 });
    const beam = new THREE.Mesh(new THREE.ConeGeometry(4, 60, 20, 1, true), new THREE.MeshBasicMaterial({ color: 0xfff1b8, transparent: true, opacity: 0.12, depthWrite: false, side: THREE.DoubleSide }));
    beam.geometry.translate(0, -30, 0); beam.rotation.z = Math.PI / 2; const pivot = new THREE.Group(); pivot.position.set(0, 0, 12.6); pivot.add(beam); lh.add(pivot);
    this.hooks.push(() => { pivot.rotation.z = this.time * 0.6; });
    // the glowing letter, a story on its way across the ocean
    const letter = this.letter = new THREE.Group(); g.add(letter); letter.visible = false;
    this.box(letter, 0, 0, 0, 0.9, 0.04, 0.6, "#fff4d6", { emissive: new THREE.Color("#ffe2a0"), emissiveIntensity: 0.8 });
    const ll = new THREE.PointLight(0xffe2a0, 5, 8, 1.4); letter.add(ll);
    return g;
  }

  makeBlossoms(at) {
    const g = new THREE.Group(); g.position.copy(at); this.scene.add(g);
    const ground = new THREE.Mesh(new THREE.CircleGeometry(40, 40), this.mat("#9fbf7a")); ground.position.z = 0.01; g.add(ground);
    this.box(g, 0, 0, 0.02, 2.0, 40, 0.02, "#d9c9a8");                         // a path
    const pinks = ["#f6b8cf", "#f2a3c0", "#fbd0dd", "#ee98b6"];
    for (const [x, y, s] of [[-3.6, 2, 1.1], [3.4, 4.5, 1.25], [-4, 9, 1.0], [3.8, 11, 1.15], [-3.4, -4, 1.0], [3.2, -2.4, 0.95], [-6, 16, 1.2], [5.5, 18, 1.1]]) {
      this.cyl(g, [x, y, 0], [x, y, 2.4 * s], 0.18 * s, "#5d3d2b", 8);
      this.cyl(g, [x, y, 1.8 * s], [x + 0.8 * s, y, 2.8 * s], 0.08 * s, "#5d3d2b", 6);
      for (let k = 0; k < 9; k++) this.ball(g, x + Math.cos(k * 1.7) * 1.1 * s, y + Math.sin(k * 2.3) * 1.1 * s, 2.8 * s + Math.sin(k * 3.1) * 0.5, (0.7 + (k % 3) * 0.15) * s, pinks[k % 4]);
    }
    // a stone lantern
    this.box(g, 1.6, 0.6, 0.4, 0.4, 0.4, 0.8, "#a8a49c"); this.box(g, 1.6, 0.6, 1.0, 0.7, 0.7, 0.12, "#a8a49c"); this.ball(g, 1.6, 0.6, 0.9, 0.14, "#ffd59a", { emissive: new THREE.Color("#ffb060"), emissiveIntensity: 0.8 });
    // falling petals
    const n = 260, pos = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) pos.set([(Math.random() - 0.5) * 16, (Math.random() - 0.3) * 26, Math.random() * 5], i * 3);
    const pg = new THREE.BufferGeometry(); pg.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    const petals = new THREE.Points(pg, new THREE.PointsMaterial({ color: 0xf9c4d6, size: 0.09 })); g.add(petals);
    this.hooks.push((dt) => {
      if (!g.visible) return;
      for (let i = 0; i < n; i++) { pos[i * 3 + 2] -= dt * 0.35; pos[i * 3] += Math.sin(this.time + i) * dt * 0.2; if (pos[i * 3 + 2] < 0) pos[i * 3 + 2] = 5; }
      pg.attributes.position.needsUpdate = true;
    });
    return g;
  }

  makeBench(at) {
    // far away, at night: a workbench under a lamp, tools, a little dome he is building
    const g = new THREE.Group(); g.position.copy(at); this.scene.add(g);
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(12, 12), this.mat("#5a4636")); g.add(floor);
    this.box(g, 0, 3, 1.6, 8, 0.15, 3.2, "#3b3a46");                          // the wall
    const win = this.box(g, -1.4, 2.92, 2.1, 1.6, 0.04, 1.1, "#18264a", { emissive: new THREE.Color("#1a2a58"), emissiveIntensity: 0.6 });
    for (let k = 0; k < 14; k++) this.ball(g, -2.1 + (k * 0.37) % 1.4, 2.88, 1.65 + ((k * 0.53) % 0.9), 0.015, "#fff6d0", { emissive: new THREE.Color("#fff6d0"), emissiveIntensity: 1 });
    this.box(g, 0.6, 2.2, 0.85, 2.6, 0.9, 0.08, "#8a6440");                  // the bench top
    for (const [x, y] of [[-0.6, 1.85], [1.8, 1.85], [-0.6, 2.55], [1.8, 2.55]]) this.box(g, x, y, 0.42, 0.08, 0.08, 0.84, "#5a3a22");
    const lampHead = this.ball(g, 1.5, 2.3, 1.75, 0.13, "#ffd59a", { emissive: new THREE.Color("#ffb060"), emissiveIntensity: 1 });
    this.cyl(g, [1.5, 2.4, 0.89], [1.5, 2.35, 1.7], 0.02, "#333", 6);
    const lamp = new THREE.PointLight(0xffc88a, 9, 7, 1.4); lamp.position.set(1.5, 2.2, 1.7); g.add(lamp);
    const model = this.makeDome(); model.scale.setScalar(0.07); model.position.set(0.55, 2.2, 0.89); g.add(model);
    for (let k = 0; k < 4; k++) this.box(g, -0.3 + k * 0.12, 2.0 + (k % 2) * 0.05, 0.9 + k * 0.004, 0.42, 0.3, 0.004, "#efe6d2");
    this.box(g, 1.1, 2.5, 0.95, 0.4, 0.2, 0.16, "#c8432f");                    // a toolbox
    this.benchDada = new Character(THREE, "dada-bench", PEOPLE.dada, g); this.benchDada.place(0.6, 1.25, 0); this.benchDada.ground = () => 0;
    this.hooks.push((dt) => { if (g.visible) this.benchDada.update(dt); });
    return g;
  }

  // -------------------------------------------------------------- characters on the hill
  person(id, def, parent = this.places.hill) {
    if (!this.cast[id]) { const c = new Character(THREE, id, def, parent); c.ground = () => 0; this.cast[id] = c; }
    const c = this.cast[id]; c.root.visible = true; return c;
  }
  hideCast() { for (const c of Object.values(this.cast)) { c.root.visible = false; c.walk = null; c.do("idle"); } }

  // -------------------------------------------------------------- frames
  resize(w, h) {
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / Math.max(1, h);
    this.camera.updateProjectionMatrix();
  }
  step(dt) {
    this.time += dt;
    for (const h of this.hooks) h(dt);
    for (const c of Object.values(this.cast)) if (c.root.visible) c.update(dt, this.time);
    if (this.shot && this.tick) this.tick(this.time - this.shot.t0);
    if (this.shot) {
      const s = this.shot, t = Math.min(1, (this.time - s.t0) / s.dur), v = s.at(t);
      this.camera.position.copy(v.pos); this.camera.up.set(0, 0, 1); this.camera.lookAt(v.target);
      if (v.roll) this.camera.rotateZ(v.roll);
      // portrait tablets see more sky: widen the lens so the frame keeps its subject
      const portrait = this.camera.aspect < 1 ? 1 / this.camera.aspect : 1;
      const fov = (v.fov || 40);
      this.camera.fov = Math.min(80, 2 * Math.atan(Math.tan(fov * Math.PI / 360) * Math.min(1.9, portrait)) * 180 / Math.PI);
      this.camera.updateProjectionMatrix();
    }
    const d = new THREE.Vector3(); this.camera.getWorldDirection(d);
    this.fill.position.copy(this.camera.position).add(V(0, 0, 2)); this.fill.target.position.copy(this.camera.position).addScaledVector(d, 6);
    this.renderer.render(this.scene, this.camera);
  }
  play(shot, dur) { this.shot = { ...shot, dur, t0: this.time }; }

  /** Where a 3-D point lands on screen, in CSS pixels (for the lettering drawn over the picture). */
  project(p) {
    const v = p.clone().project(this.camera), r = this.canvas.getBoundingClientRect();
    return { x: (v.x + 1) / 2 * r.width, y: (1 - v.y) / 2 * r.height, visible: v.z < 1 };
  }
}

function starTexture() {
  const c = document.createElement("canvas"); c.width = c.height = 128;
  const g = c.getContext("2d"), gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, "rgba(255,255,240,1)"); gr.addColorStop(0.18, "rgba(255,240,190,0.9)"); gr.addColorStop(1, "rgba(255,220,150,0)");
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
  g.strokeStyle = "rgba(255,245,210,0.8)"; g.lineWidth = 3;
  g.beginPath(); g.moveTo(64, 4); g.lineTo(64, 124); g.moveTo(4, 64); g.lineTo(124, 64); g.stroke();
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

export { V, fovForLens, EASE };
