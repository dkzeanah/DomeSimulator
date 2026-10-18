// The houses behind the house portal: the starter dome every member begins with, and five grand
// houses, Great Gatsby style, for the portal's defaults 1 to 5. Every dome in them is the solver's
// own 2V dome (generated/dome-mesh.json: its 26 nodes, 65 struts and 40 triangles), scaled up and
// clad; the rest is the estate round it. Feet, y up; the front of every house faces +z, where the
// visitor arrives.

import * as THREE from "three";
import mesh from "../generated/dome-mesh.json";
import type { Obstacle } from "./engine";

export interface Estate { group: THREE.Group; obstacles: Obstacle[]; tick: (t: number, dt: number) => void; sky: [string, string]; ground: string }

// ----------------------------------------------------------------------
// Materials and small parts
// ----------------------------------------------------------------------

const lambert = (c: string) => new THREE.MeshLambertMaterial({ color: c, flatShading: true });
const M = {
  marble: () => new THREE.MeshStandardMaterial({ color: "#f1ece2", roughness: 0.35, metalness: 0.05 }),
  cream: () => lambert("#e9dcc0"),
  white: () => new THREE.MeshStandardMaterial({ color: "#fbfaf6", roughness: 0.5 }),
  gold: () => new THREE.MeshStandardMaterial({ color: "#d4af37", metalness: 0.95, roughness: 0.28, emissive: "#3a2a05", emissiveIntensity: 0.6 }),
  black: () => new THREE.MeshStandardMaterial({ color: "#14141a", metalness: 0.6, roughness: 0.3 }),
  glass: (tint = "#bfe6ff", opacity = 0.32) => new THREE.MeshStandardMaterial({ color: tint, metalness: 0.2, roughness: 0.05, transparent: true, opacity, side: THREE.DoubleSide, depthWrite: false }),
  water: () => new THREE.MeshStandardMaterial({ color: "#2f6fb0", metalness: 0.55, roughness: 0.12, transparent: true, opacity: 0.88 }),
  hedge: () => lambert("#2c5426"),
  path: () => lambert("#d9cdb4"),
  bulb: (c = "#ffe2a0") => new THREE.MeshBasicMaterial({ color: c }),
  glow: (c: string, k = 1.2) => new THREE.MeshStandardMaterial({ color: c, emissive: c, emissiveIntensity: k }),
};

function place(o: THREE.Object3D, x: number, y: number, z: number, ry = 0) { o.position.set(x, y, z); o.rotation.y = ry; return o; }
function shadow<O extends THREE.Object3D>(o: O): O { o.traverse((m) => { if ((m as THREE.Mesh).isMesh) { (m as THREE.Mesh).castShadow = true; (m as THREE.Mesh).receiveShadow = true; } }); return o; }

/** Many copies of one shape, one draw call. */
function instances(geo: THREE.BufferGeometry, mat: THREE.Material, at: THREE.Matrix4[]) {
  const m = new THREE.InstancedMesh(geo, mat, Math.max(1, at.length));
  at.forEach((x, i) => m.setMatrixAt(i, x));
  m.count = at.length;
  m.castShadow = true; m.receiveShadow = true;
  return m;
}
const T = (x: number, y: number, z: number, s = 1, ry = 0) => new THREE.Matrix4().compose(new THREE.Vector3(x, y, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(0, ry, 0)), new THREE.Vector3(s, s, s));

// ----------------------------------------------------------------------
// The solver's dome, made grand
// ----------------------------------------------------------------------

interface DomeLook { frame?: THREE.Material; panel?: THREE.Material | null; strut?: number; drum?: number; drumMat?: THREE.Material; finial?: boolean; lantern?: boolean }

/** The solver's 2V dome at radius R: its struts, its nodes and its 40 triangles, on a drum. */
export function grandDome(R: number, o: DomeLook = {}): THREE.Group {
  const g = new THREE.Group();
  const k = R / mesh.radiusFt;
  const lift = o.drum ?? 0;
  const v = (mesh.vertices as number[][]).map(([x, y, z]) => new THREE.Vector3(x * k, z * k + lift, -y * k));
  const strut = o.strut ?? Math.max(0.25, R * 0.022);
  const frame = o.frame ?? M.white();
  const up = new THREE.Vector3(0, 1, 0);
  const bars = (mesh.edges as [number, number, string, boolean][]).map(([a, b]) => {
    const p = v[a], q = v[b], d = q.clone().sub(p);
    return new THREE.Matrix4().compose(p.clone().add(q).multiplyScalar(0.5), new THREE.Quaternion().setFromUnitVectors(up, d.clone().normalize()), new THREE.Vector3(1, d.length(), 1));
  });
  g.add(instances(new THREE.CylinderGeometry(strut, strut, 1, 6), frame, bars));
  g.add(instances(new THREE.SphereGeometry(strut * 1.7, 8, 6), frame, v.map((p) => T(p.x, p.y, p.z))));
  if (o.panel !== null) {
    const pos: number[] = [];
    for (const f of mesh.faces as [number, number, number, string][]) {
      const tri = [v[f[0]], v[f[1]], v[f[2]]];
      const c = tri[0].clone().add(tri[1]).add(tri[2]).multiplyScalar(1 / 3);
      for (const p of tri) { const q = p.clone().lerp(c, 0.04); pos.push(q.x, q.y, q.z); }
    }
    const pg = new THREE.BufferGeometry();
    pg.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    pg.computeVertexNormals();
    const panels = new THREE.Mesh(pg, o.panel ?? M.cream());
    (panels.material as THREE.Material).side = THREE.DoubleSide;
    panels.scale.setScalar(0.992);
    panels.position.y = lift * 0.008;
    g.add(panels);
  }
  if (lift > 0) {
    const drum = new THREE.Mesh(new THREE.CylinderGeometry(R * 1.0, R * 1.03, lift, 30, 1, true), o.drumMat ?? M.marble());
    drum.position.y = lift / 2;
    (drum.material as THREE.Material).side = THREE.DoubleSide;
    g.add(drum);
    const cornice = new THREE.Mesh(new THREE.TorusGeometry(R * 1.01, R * 0.025, 6, 40), M.gold());
    cornice.rotation.x = Math.PI / 2; cornice.position.y = lift; g.add(cornice);
    // pilasters round the drum
    const pil: THREE.Matrix4[] = [];
    for (let i = 0; i < 20; i++) { const a = (i / 20) * Math.PI * 2; pil.push(T(Math.cos(a) * R * 1.02, lift / 2, Math.sin(a) * R * 1.02, 1, -a)); }
    g.add(instances(new THREE.BoxGeometry(R * 0.05, lift, R * 0.05), M.marble(), pil));
  }
  if (o.finial !== false) {
    const top = R + lift;
    const ball = new THREE.Mesh(new THREE.SphereGeometry(R * 0.06, 16, 12), M.gold()); ball.position.y = top + R * 0.05; g.add(ball);
    const spire = new THREE.Mesh(new THREE.ConeGeometry(R * 0.025, R * 0.3, 8), M.gold()); spire.position.y = top + R * 0.22; g.add(spire);
  }
  if (o.lantern) {
    const lan = new THREE.Mesh(new THREE.CylinderGeometry(R * 0.09, R * 0.09, R * 0.12, 10), M.glow("#ffd27a", 1.6)); lan.position.y = R + lift + R * 0.02; g.add(lan);
  }
  return shadow(g);
}

// ----------------------------------------------------------------------
// The estate's pieces
// ----------------------------------------------------------------------

function columns(points: [number, number][], h: number, r: number, mat = M.marble()) {
  const g = new THREE.Group();
  g.add(instances(new THREE.CylinderGeometry(r * 0.85, r, h, 12), mat, points.map(([x, z]) => T(x, h / 2, z))));
  g.add(instances(new THREE.BoxGeometry(r * 2.6, r * 0.6, r * 2.6), mat, points.flatMap(([x, z]) => [T(x, r * 0.3, z), T(x, h - r * 0.3, z)])));
  return g;
}

function terrace(w: number, d: number, h: number, mat = M.marble(), rail = true) {
  const g = new THREE.Group();
  const slab = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); slab.position.y = h / 2; g.add(slab);
  if (rail) {
    const posts: THREE.Matrix4[] = [];
    for (let x = -w / 2; x <= w / 2 + 0.01; x += 2.2) { posts.push(T(x, h + 1.2, d / 2 - 0.4), T(x, h + 1.2, -d / 2 + 0.4)); }
    for (let z = -d / 2; z <= d / 2 + 0.01; z += 2.2) { posts.push(T(-w / 2 + 0.4, h + 1.2, z), T(w / 2 - 0.4, h + 1.2, z)); }
    g.add(instances(new THREE.CylinderGeometry(0.22, 0.3, 2.4, 6), mat, posts));
    for (const [x, z, sw, sd] of [[0, d / 2 - 0.4, w, 0.5], [0, -d / 2 + 0.4, w, 0.5], [-w / 2 + 0.4, 0, 0.5, d], [w / 2 - 0.4, 0, 0.5, d]] as number[][]) {
      const top = new THREE.Mesh(new THREE.BoxGeometry(sw, 0.35, sd), mat); top.position.set(x, h + 2.5, z); g.add(top);
    }
  }
  return shadow(g);
}

function stairs(w: number, rise: number, steps: number, run = 1.6, mat = M.marble()) {
  const g = new THREE.Group();
  const s = rise / steps;
  for (let i = 0; i < steps; i++) { const b = new THREE.Mesh(new THREE.BoxGeometry(w, s * (i + 1), run), mat); b.position.set(0, (s * (i + 1)) / 2, (steps - i - 0.5) * run); g.add(b); }
  return shadow(g);
}

interface Fountain { group: THREE.Group; tick: (t: number) => void }
function fountain(r: number, tiers = 3): Fountain {
  const g = new THREE.Group();
  const stone = M.marble();
  const basin = new THREE.Mesh(new THREE.CylinderGeometry(r, r * 1.05, 1.6, 32), stone); basin.position.y = 0.8; g.add(basin);
  const water = new THREE.Mesh(new THREE.CylinderGeometry(r * 0.94, r * 0.94, 0.2, 32), M.water()); water.position.y = 1.5; g.add(water);
  let y = 1.6;
  for (let i = 1; i < tiers; i++) {
    const rr = r * (0.55 / i);
    const stem = new THREE.Mesh(new THREE.CylinderGeometry(rr * 0.25, rr * 0.35, 3, 12), stone); stem.position.y = y + 1.5; g.add(stem);
    y += 3;
    const bowl = new THREE.Mesh(new THREE.CylinderGeometry(rr, rr * 0.4, 0.8, 24), stone); bowl.position.y = y + 0.4; g.add(bowl);
    y += 0.8;
  }
  const top = new THREE.Mesh(new THREE.SphereGeometry(0.6, 12, 8), M.gold()); top.position.y = y + 0.6; g.add(top);
  // the spray: drops thrown up and out from the top, falling back into the basin
  const n = 260;
  const geo = new THREE.BufferGeometry();
  const pos = new Float32Array(n * 3), vel = new Float32Array(n * 3), born = new Float32Array(n);
  for (let i = 0; i < n; i++) born[i] = -Math.random() * 2;
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  const drops = new THREE.Points(geo, new THREE.PointsMaterial({ color: "#cfe9ff", size: 0.28, transparent: true, opacity: 0.85 }));
  drops.frustumCulled = false;
  g.add(drops);
  const top0 = y + 1.2;
  const tick = (t: number) => {
    for (let i = 0; i < n; i++) {
      let age = t - born[i];
      if (age > 2 || age < 0) {
        born[i] = t; age = 0;
        const a = Math.random() * Math.PI * 2, out = r * (0.22 + Math.random() * 0.12);
        vel[i * 3] = Math.cos(a) * out; vel[i * 3 + 1] = 9 + Math.random() * 3; vel[i * 3 + 2] = Math.sin(a) * out;
      }
      pos[i * 3] = vel[i * 3] * age; pos[i * 3 + 1] = Math.max(1.5, top0 + vel[i * 3 + 1] * age - 16 * age * age * 0.5); pos[i * 3 + 2] = vel[i * 3 + 2] * age;
    }
    geo.getAttribute("position").needsUpdate = true;
  };
  return { group: shadow(g), tick };
}

function pool(w: number, l: number) {
  const g = new THREE.Group();
  const rim = new THREE.Mesh(new THREE.BoxGeometry(w + 2, 0.5, l + 2), M.marble()); rim.position.y = 0.25; g.add(rim);
  const water = new THREE.Mesh(new THREE.BoxGeometry(w, 0.1, l), M.water()); water.position.y = 0.52; g.add(water);
  return g;
}

/** Lamp posts: a black post, a gold cap, a glowing globe. */
function lamps(points: [number, number][], h = 9) {
  const g = new THREE.Group();
  g.add(instances(new THREE.CylinderGeometry(0.16, 0.26, h, 8), M.black(), points.map(([x, z]) => T(x, h / 2, z))));
  g.add(instances(new THREE.SphereGeometry(0.75, 12, 8), M.bulb(), points.map(([x, z]) => T(x, h + 0.5, z))));
  g.add(instances(new THREE.ConeGeometry(0.7, 0.6, 8), M.gold(), points.map(([x, z]) => T(x, h + 1.4, z))));
  return g;
}

/** Strings of party lights between posts: each a sagging line of bulbs. */
function festoons(runs: [THREE.Vector3, THREE.Vector3][], per = 16, colours = ["#ffe2a0", "#ff9ad0", "#9ad8ff", "#c8ff9a"]) {
  const g = new THREE.Group();
  const byColour: THREE.Matrix4[][] = colours.map(() => []);
  let k = 0;
  for (const [a, b] of runs) for (let i = 0; i <= per; i++) {
    const f = i / per, p = a.clone().lerp(b, f);
    p.y -= Math.sin(f * Math.PI) * a.distanceTo(b) * 0.06;
    byColour[k++ % colours.length].push(T(p.x, p.y, p.z));
  }
  colours.forEach((c, i) => g.add(instances(new THREE.SphereGeometry(0.28, 8, 6), M.bulb(c), byColour[i])));
  return g;
}

function hedges(boxes: [number, number, number, number][], h = 3.2) {
  return instancesBoxes(boxes, h, M.hedge());
}
function instancesBoxes(boxes: [number, number, number, number][], h: number, mat: THREE.Material) {
  const at = boxes.map(([x, z, w, d]) => new THREE.Matrix4().compose(new THREE.Vector3(x, h / 2, z), new THREE.Quaternion(), new THREE.Vector3(w, h, d)));
  return instances(new THREE.BoxGeometry(1, 1, 1), mat, at);
}

function topiaries(points: [number, number][], h = 6) {
  const g = new THREE.Group();
  g.add(instances(new THREE.CylinderGeometry(1.1, 1.3, 1.6, 10), M.marble(), points.map(([x, z]) => T(x, 0.8, z))));
  g.add(instances(new THREE.ConeGeometry(1.6, h, 10), M.hedge(), points.map(([x, z]) => T(x, 1.6 + h / 2, z))));
  return g;
}

function palms(points: [number, number][]) {
  const g = new THREE.Group();
  const trunk = lambert("#8a6a44"), leaf = lambert("#3f7a32");
  for (const [x, z] of points) {
    const p = new THREE.Group();
    const t = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.6, 18, 7), trunk); t.position.y = 9; t.rotation.z = 0.06; p.add(t);
    for (let i = 0; i < 7; i++) {
      const l = new THREE.Mesh(new THREE.ConeGeometry(0.9, 8, 4), leaf);
      const a = (i / 7) * Math.PI * 2;
      l.position.set(Math.cos(a) * 3, 17.4, Math.sin(a) * 3); l.rotation.set(Math.sin(a) * 1.25, 0, -Math.cos(a) * 1.25);
      p.add(l);
    }
    g.add(place(p, x, 0, z));
  }
  return shadow(g);
}

/** A 1920s roadster on the drive. */
function roadster(colour: string) {
  const g = new THREE.Group();
  const paint = new THREE.MeshStandardMaterial({ color: colour, metalness: 0.7, roughness: 0.25 });
  const body = new THREE.Mesh(new THREE.BoxGeometry(5, 1.6, 13), paint); body.position.y = 2.2; g.add(body);
  const hood = new THREE.Mesh(new THREE.BoxGeometry(4.2, 1.3, 5), paint); hood.position.set(0, 3.4, -3.5); g.add(hood);
  const seat = new THREE.Mesh(new THREE.BoxGeometry(4.4, 2, 3), lambert("#5a2a1a")); seat.position.set(0, 3.4, 2.5); g.add(seat);
  const shield = new THREE.Mesh(new THREE.PlaneGeometry(4, 1.6), M.glass("#dff4ff", 0.5)); shield.position.set(0, 4.6, -0.6); shield.rotation.x = -0.3; g.add(shield);
  const grille = new THREE.Mesh(new THREE.BoxGeometry(3.6, 2.4, 0.4), M.gold()); grille.position.set(0, 3.3, -6.3); g.add(grille);
  for (const [x, z] of [[-2.6, -4.2], [2.6, -4.2], [-2.6, 4.2], [2.6, 4.2]]) {
    const w = new THREE.Mesh(new THREE.CylinderGeometry(1.4, 1.4, 0.8, 16), M.black()); w.rotation.z = Math.PI / 2; w.position.set(x, 1.4, z); g.add(w);
    const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.6, 0.6, 0.9, 12), M.gold()); hub.rotation.z = Math.PI / 2; hub.position.set(x, 1.4, z); g.add(hub);
  }
  for (const x of [-1.6, 1.6]) { const l = new THREE.Mesh(new THREE.SphereGeometry(0.45, 10, 8), M.bulb("#fff4c8")); l.position.set(x, 3, -6.6); g.add(l); }
  return shadow(g);
}

function lawnStripes(w: number, l: number, at: [number, number], colourA = "#3f7a34", colourB = "#4a8a3c") {
  const g = new THREE.Group();
  const n = Math.round(w / 8);
  for (let i = 0; i < n; i++) {
    const s = new THREE.Mesh(new THREE.PlaneGeometry(w / n, l), lambert(i % 2 ? colourA : colourB));
    s.rotation.x = -Math.PI / 2; s.position.set(at[0] - w / 2 + (i + 0.5) * (w / n), 0.03, at[1]); s.receiveShadow = true; g.add(s);
  }
  return g;
}

function drive(points: [number, number][], width = 10) {
  const g = new THREE.Group();
  for (let i = 0; i < points.length - 1; i++) {
    const [ax, az] = points[i], [bx, bz] = points[i + 1];
    const len = Math.hypot(bx - ax, bz - az);
    const s = new THREE.Mesh(new THREE.PlaneGeometry(width, len + width * 0.5), M.path());
    s.rotation.x = -Math.PI / 2; s.rotation.z = -Math.atan2(bx - ax, bz - az);
    s.position.set((ax + bx) / 2, 0.04, (az + bz) / 2); s.receiveShadow = true; g.add(s);
  }
  return g;
}

/** A sign at the gate: the house's name, and whose it is. */
export function sign(title: string, sub: string, colour = "#d4af37") {
  const c = document.createElement("canvas"); c.width = 1024; c.height = 384;
  const x = c.getContext("2d")!;
  x.fillStyle = "#14141a"; x.fillRect(0, 0, 1024, 384);
  x.strokeStyle = colour; x.lineWidth = 14; x.strokeRect(20, 20, 984, 344);
  x.fillStyle = colour; x.textAlign = "center";
  x.font = "700 120px Georgia, serif"; x.fillText(title, 512, 190);
  x.font = "italic 52px Georgia, serif"; x.fillStyle = "#f1ece2"; x.fillText(sub, 512, 290);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const g = new THREE.Group();
  const board = new THREE.Mesh(new THREE.PlaneGeometry(12, 4.5), new THREE.MeshBasicMaterial({ map: tex, side: THREE.DoubleSide }));
  board.position.y = 6; g.add(board);
  for (const px of [-6.3, 6.3]) { const p = new THREE.Mesh(new THREE.BoxGeometry(0.6, 8.5, 0.6), M.black()); p.position.set(px, 4.25, 0); g.add(p); }
  return shadow(g);
}

/** Gate piers either side of the drive where the visitor arrives. */
function gatePiers(z: number, half = 14) {
  const g = new THREE.Group();
  for (const x of [-half, half]) {
    const p = new THREE.Mesh(new THREE.BoxGeometry(3, 10, 3), M.marble()); p.position.set(x, 5, z); g.add(p);
    const urn = new THREE.Mesh(new THREE.SphereGeometry(1.4, 12, 8), M.gold()); urn.position.set(x, 11.2, z); g.add(urn);
  }
  return shadow(g);
}

function lights(g: THREE.Group, list: [number, number, number, string, number][]) {
  for (const [x, y, z, c, k] of list) { const l = new THREE.PointLight(c, k, 90, 1.4); l.position.set(x, y, z); g.add(l); }
}

/** Fireworks: bursts of coloured sparks over the house, one after another. */
function fireworks(centre: THREE.Vector3, spread: number) {
  const n = 600;
  const geo = new THREE.BufferGeometry();
  const pos = new Float32Array(n * 3), col = new Float32Array(n * 3);
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
  const pts = new THREE.Points(geo, new THREE.PointsMaterial({ size: 0.9, vertexColors: true, transparent: true, opacity: 0.95, depthWrite: false, blending: THREE.AdditiveBlending }));
  pts.frustumCulled = false;
  const bursts = 4, per = n / bursts;
  const state = Array.from({ length: bursts }, (_, b) => ({ at: new THREE.Vector3(), t0: -b * 0.9, dirs: [] as THREE.Vector3[], c: new THREE.Color() }));
  const palette = ["#ffd27a", "#ff6aa8", "#7ad8ff", "#b6ff7a", "#ffffff"];
  const tick = (t: number) => {
    state.forEach((s, b) => {
      let age = t - s.t0;
      if (age > 3.4 || s.dirs.length === 0) {
        s.t0 = t; age = 0;
        s.at.set(centre.x + (Math.random() - 0.5) * spread, centre.y + Math.random() * 25, centre.z + (Math.random() - 0.5) * spread);
        s.c.set(palette[Math.floor(Math.random() * palette.length)]);
        s.dirs = Array.from({ length: per }, () => new THREE.Vector3().randomDirection().multiplyScalar(14 + Math.random() * 6));
      }
      const fade = Math.max(0, 1 - age / 3.4);
      for (let i = 0; i < per; i++) {
        const k = (b * per + i) * 3, d = s.dirs[i];
        pos[k] = s.at.x + d.x * age; pos[k + 1] = s.at.y + d.y * age - 4 * age * age; pos[k + 2] = s.at.z + d.z * age;
        col[k] = s.c.r * fade; col[k + 1] = s.c.g * fade; col[k + 2] = s.c.b * fade;
      }
    });
    geo.getAttribute("position").needsUpdate = true;
    geo.getAttribute("color").needsUpdate = true;
  };
  return { points: pts, tick };
}

// ----------------------------------------------------------------------
// The houses
// ----------------------------------------------------------------------

function arrival(g: THREE.Group, title: string, owner: string, colour?: string) {
  g.add(gatePiers(92));
  g.add(place(sign(title, owner, colour), 22, 0, 96, -0.35));
}

/** Every member's first house: one 2V dome on its deck, a path, a garden. */
function starter(owner: string): Estate {
  const g = new THREE.Group();
  const deck = new THREE.Mesh(new THREE.CylinderGeometry(12, 12, 1.4, 10), lambert("#8a6440")); deck.position.y = 0.7; g.add(deck);
  const d = grandDome(mesh.radiusFt, { frame: lambert("#c8914e"), panel: lambert("#e2cfa8"), strut: 0.24, finial: false });
  d.position.y = 1.4; g.add(d);
  g.add(drive([[0, 100], [0, 14]], 5));
  const beds: [number, number][] = [];
  for (let i = 0; i < 10; i++) { const a = (i / 10) * Math.PI * 2; beds.push([Math.cos(a) * 17, Math.sin(a) * 17]); }
  g.add(topiaries(beds.filter(([, z]) => z < 10), 3.5));
  const fence: THREE.Matrix4[] = [];
  for (let i = 0; i < 48; i++) { const a = (i / 48) * Math.PI * 2; if (Math.abs(Math.sin(a) - 1) > 0.02 || Math.cos(a) > 0.2 || Math.cos(a) < -0.2) fence.push(T(Math.cos(a) * 30, 1.6, Math.sin(a) * 30, 1, -a)); }
  g.add(instances(new THREE.BoxGeometry(0.4, 3.2, 3.6), lambert("#a07a4a"), fence));
  g.add(place(sign("Home", owner, "#e8b45a"), 12, 0, 40, -0.3));
  return { group: shadow(g), obstacles: [{ x: 0, z: 0, r: 13.5 }], tick: () => undefined, sky: ["#1b2a4a", "#e8a25a"], ground: "#4f6a2a" };
}

/** 1. West Egg: the party house. */
function westEgg(owner: string): Estate {
  const g = new THREE.Group();
  const ticks: ((t: number) => void)[] = [];
  g.add(lawnStripes(200, 120, [0, 40]));
  g.add(drive([[0, 112], [0, 64], [-26, 50], [-26, 30], [26, 30], [26, 50], [0, 64]], 11));
  // the great terrace and the house on it
  const ter = terrace(110, 70, 4); ter.position.set(0, 0, -30); g.add(ter);
  const st = stairs(34, 4, 6); st.position.set(0, 0, 5); g.add(st);
  const main = grandDome(32, { drum: 14, panel: M.cream(), frame: M.gold(), lantern: true }); main.position.set(0, 4, -38); g.add(main);
  for (const side of [-1, 1]) {
    const wing = grandDome(15, { drum: 8, panel: M.cream(), frame: M.gold() }); wing.position.set(side * 44, 4, -26); g.add(wing);
    const link = new THREE.Mesh(new THREE.BoxGeometry(14, 10, 12), M.marble()); link.position.set(side * 30, 9, -30); g.add(shadow(link));
  }
  // a colonnade across the front of the terrace
  const pts: [number, number][] = [];
  for (let x = -48; x <= 48; x += 6) if (Math.abs(x) > 16) pts.push([x, 0]);
  const col = columns(pts, 16, 0.9); col.position.set(0, 4, 2); g.add(col);
  const entab = new THREE.Mesh(new THREE.BoxGeometry(100, 2, 3), M.marble()); entab.position.set(0, 21, 2); g.add(shadow(entab));
  // the fountain, the pool and the lanterns
  const f = fountain(11); f.group.position.set(0, 0, 47); g.add(f.group); ticks.push(f.tick);
  // twin reflecting pools either side of the drive
  for (const x of [-36, 36]) { const p = pool(14, 40); p.position.set(x, 0, 82); g.add(p); }
  g.add(lamps([[-16, 26], [16, 26], [-12, 70], [12, 70], [-12, 88], [12, 88], [-58, 10], [58, 10]]));
  const posts = [[-55, 12], [-20, 30], [20, 30], [55, 12]].map(([x, z]) => new THREE.Vector3(x, 14, z));
  g.add(festoons([[posts[0], posts[1]], [posts[1], posts[2]], [posts[2], posts[3]], [posts[0], new THREE.Vector3(-30, 14, 60)], [posts[3], new THREE.Vector3(30, 14, 60)]], 18));
  g.add(lamps([[-30, 60], [30, 60]], 13));
  g.add(topiaries([[-40, 40], [40, 40], [-40, 60], [40, 60], [-60, 40], [60, 40]]));
  g.add(place(roadster("#f4e04d"), -24, 0, 40, 0.4));
  arrival(g, "West Egg", owner);
  lights(g, [[0, 30, 10, "#ffd9a0", 220], [0, 12, 47, "#bfe4ff", 90], [-45, 20, 0, "#ffc890", 90], [45, 20, 0, "#ffc890", 90]]);
  return { group: g, obstacles: [{ x: 0, z: -30, r: 50 }, { x: -44, z: -26, r: 17 }, { x: 44, z: -26, r: 17 }, { x: 0, z: 47, r: 12 }, { x: -36, z: 70, r: 8 }, { x: -36, z: 94, r: 8 }, { x: 36, z: 70, r: 8 }, { x: 36, z: 94, r: 8 }],
    tick: (t) => ticks.forEach((f2) => f2(t)), sky: ["#0d1438", "#e88a5a"], ground: "#3f6a34" };
}

/** 2. East Egg: white domes, a colonnade, and the green light. */
function eastEgg(owner: string): Estate {
  const g = new THREE.Group();
  // the bay behind the house, and the dock out into it
  const bay = new THREE.Mesh(new THREE.PlaneGeometry(260, 70), M.water()); bay.rotation.x = -Math.PI / 2; bay.position.set(0, 0.06, -96); g.add(bay);
  const dock = new THREE.Mesh(new THREE.BoxGeometry(6, 1, 46), lambert("#8a6440")); dock.position.set(30, 1, -98); g.add(shadow(dock));
  const lightPost = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 8, 8), M.black()); lightPost.position.set(30, 5, -120); g.add(lightPost);
  const green = new THREE.Mesh(new THREE.SphereGeometry(0.9, 16, 12), M.glow("#3aff6a", 2.5)); green.position.set(30, 9.4, -120); g.add(green);
  const greenLight = new THREE.PointLight("#3aff6a", 60, 50, 1.5); greenLight.position.set(30, 10, -120); g.add(greenLight);
  g.add(lawnStripes(220, 110, [0, 20], "#4a8a3c", "#56973f"));
  g.add(drive([[0, 112], [0, 60]], 11));
  // five white domes in a crescent
  const crescent = [[-58, -34, 14], [-30, -46, 18], [0, -50, 24], [30, -46, 18], [58, -34, 14]];
  const obstacles: Obstacle[] = [];
  for (const [x, z, r] of crescent) {
    const d = grandDome(r, { drum: r * 0.45, panel: M.white(), frame: M.white(), drumMat: M.white() }); d.position.set(x, 0, z); g.add(d);
    obstacles.push({ x, z, r: r + 2 });
  }
  // a curved colonnade in front of them, joined by a balustraded walk
  const pts: [number, number][] = [];
  for (let i = 0; i <= 24; i++) { const a = Math.PI * (0.15 + 0.7 * (i / 24)); pts.push([Math.cos(a) * 70, -Math.sin(a) * 70 + 34]); }
  g.add(columns(pts, 15, 0.8, M.white()));
  const walk = terrace(130, 12, 1, M.white()); walk.position.set(0, 0, -16); g.add(walk);
  // the lawn down to the water: topiary, urns, a croquet lawn
  g.add(topiaries([[-24, 10], [24, 10], [-24, 30], [24, 30], [-24, 50], [24, 50]], 7));
  g.add(lamps([[-12, 70], [12, 70], [-12, 96], [12, 96]]));
  const f = fountain(7, 2); f.group.position.set(0, 0, 34); g.add(f.group);
  g.add(place(roadster("#3a4a8a"), 18, 0, 66, -0.5));
  const greenT = (t: number) => { (green.material as THREE.MeshStandardMaterial).emissiveIntensity = 1.6 + Math.sin(t * 2.2) * 1.2; greenLight.intensity = 40 + Math.sin(t * 2.2) * 30; };
  arrival(g, "East Egg", owner, "#7cffa0");
  lights(g, [[0, 30, 0, "#fff2d8", 200], [-50, 20, -10, "#fff2d8", 80], [50, 20, -10, "#fff2d8", 80]]);
  obstacles.push({ x: 0, z: 34, r: 8 });
  return { group: g, obstacles, tick: (t) => { f.tick(t); greenT(t); }, sky: ["#101a3a", "#c87a6a"], ground: "#3f6a34" };
}

/** 3. The Deco Palace: a stepped ziggurat, a gold dome, sunbursts and searchlights. */
function decoPalace(owner: string): Estate {
  const g = new THREE.Group();
  const ticks: ((t: number) => void)[] = [];
  g.add(drive([[0, 112], [0, 40]], 14));
  // the ziggurat: five terraces, each trimmed in gold, a stair up the front
  const tiers = [[96, 10], [78, 9], [60, 8], [44, 7], [30, 6]];
  let y = 0;
  tiers.forEach(([w, h], i) => {
    const tier = new THREE.Mesh(new THREE.BoxGeometry(w, h, w * 0.8), i % 2 ? M.cream() : M.marble()); tier.position.set(0, y + h / 2, -30); g.add(shadow(tier));
    const trim = new THREE.Mesh(new THREE.BoxGeometry(w + 0.6, 0.8, w * 0.8 + 0.6), M.gold()); trim.position.set(0, y + h, -30); g.add(trim);
    y += h;
  });
  // the grand stair runs from the fourth terrace's front down across the lower ones
  const st = stairs(16, tiers.slice(0, 4).reduce((a, [, h]) => a + h, 0), 18, 2.4, M.marble()); st.position.set(0, 0, -30 + 44 * 0.4); g.add(st);
  const crown = grandDome(14, { drum: 6, panel: M.gold(), frame: M.black(), lantern: true }); crown.position.set(0, y, -30); g.add(crown);
  // sunbursts on the front: gold fans of rays
  for (const [x, yy, fz, s] of [[-28, 13, -30 + 78 * 0.4 + 0.3, 1], [28, 13, -30 + 78 * 0.4 + 0.3, 1], [0, 37, -30 + 30 * 0.4 + 0.3, 1.3]] as number[][]) {
    const fan = new THREE.Group();
    for (let i = 0; i < 13; i++) { const a = Math.PI * (i / 12); const ray = new THREE.Mesh(new THREE.BoxGeometry(0.5, 8 * s, 0.3), M.gold()); ray.position.set(Math.cos(a) * 4 * s, Math.sin(a) * 4 * s, 0); ray.rotation.z = a - Math.PI / 2; fan.add(ray); }
    fan.position.set(x, yy, fz); g.add(fan);
  }
  // searchlights sweeping the sky
  const beams: THREE.Mesh[] = [];
  for (const [x, z] of [[-60, -10], [60, -10], [-60, 50], [60, 50]]) {
    const base = new THREE.Mesh(new THREE.CylinderGeometry(1.6, 2, 2.4, 12), M.black()); base.position.set(x, 1.2, z); g.add(base);
    const beam = new THREE.Mesh(new THREE.ConeGeometry(6, 140, 16, 1, true), new THREE.MeshBasicMaterial({ color: "#fff4d0", transparent: true, opacity: 0.26, side: THREE.DoubleSide, depthWrite: false, blending: THREE.AdditiveBlending }));
    beam.geometry.translate(0, -70, 0);
    const pivot = new THREE.Group(); pivot.position.set(x, 2.4, z); pivot.add(beam); beam.rotation.x = Math.PI;
    g.add(pivot); beams.push(pivot as unknown as THREE.Mesh);
  }
  ticks.push((t) => beams.forEach((b, i) => { b.rotation.z = Math.sin(t * 0.4 + i * 1.7) * 0.5; b.rotation.x = Math.cos(t * 0.33 + i) * 0.35; }));
  // a black-and-gold forecourt with a fountain and obelisks
  const court = new THREE.Mesh(new THREE.CircleGeometry(30, 8), M.black()); court.rotation.x = -Math.PI / 2; court.position.set(0, 0.05, 66); g.add(court);
  const f = fountain(9); f.group.position.set(0, 0, 66); g.add(f.group); ticks.push(f.tick);
  for (const [x, z] of [[-24, 48], [24, 48], [-24, 84], [24, 84]]) { const ob = new THREE.Mesh(new THREE.ConeGeometry(1.8, 18, 4), M.gold()); ob.position.set(x, 9, z); g.add(shadow(ob)); }
  g.add(lamps([[-14, 98], [14, 98], [-30, 66], [30, 66]]));
  g.add(place(roadster("#111111"), -16, 0, 96, 0.3));
  arrival(g, "The Deco Palace", owner);
  lights(g, [[0, 50, 10, "#ffe2b0", 260], [0, 14, 66, "#ffd27a", 90]]);
  return { group: g, obstacles: [{ x: 0, z: -30, r: 46 }, { x: 0, z: 22, r: 9.5 }, { x: 0, z: 66, r: 10 }], tick: (t) => ticks.forEach((f2) => f2(t)), sky: ["#0a0a24", "#9a5a7a"], ground: "#34503a" };
}

/** 4. The Conservatory: glass domes over a garden, a hedge maze and a gazebo. */
function conservatory(owner: string): Estate {
  const g = new THREE.Group();
  const ticks: ((t: number) => void)[] = [];
  g.add(drive([[0, 112], [0, 70], [0, 20]], 9));
  const glass = M.glass("#cfefff", 0.28);
  const obstacles: Obstacle[] = [];
  // the palm house: a great glass dome with palms inside, and two lesser glass domes
  for (const [x, z, r, n] of [[0, -40, 30, 6], [-50, -20, 16, 2], [50, -20, 16, 2]] as number[][]) {
    const d = grandDome(r, { drum: r * 0.3, panel: glass, frame: M.white(), drumMat: M.glass("#e8f6ff", 0.4) }); d.position.set(x, 0, z); g.add(d);
    obstacles.push({ x, z, r: r + 1.5 });
    const inside: [number, number][] = [];
    for (let i = 0; i < n; i++) { const a = (i / n) * Math.PI * 2 + 0.3; inside.push([x + Math.cos(a) * r * 0.45, z + Math.sin(a) * r * 0.45]); }
    g.add(palms(inside));
    const glow = new THREE.PointLight("#bfffd8", 50, r * 2.2, 1.5); glow.position.set(x, r * 0.6, z); g.add(glow);
  }
  // the hedge maze in front, and a gazebo dome at its heart
  const boxes: [number, number, number, number][] = [];
  const cx = 0, cz = 40, cells = 7, size = 8;
  for (let i = 0; i <= cells; i++) {
    const o = -cells * size / 2 + i * size;
    for (let j = 0; j < cells; j++) {
      const p = -cells * size / 2 + j * size + size / 2;
      const keepH = (i * 7 + j * 3) % 4 !== 0 && !(j === 3 && (i === 0 || i === cells));
      const keepV = (i * 5 + j * 11) % 3 !== 0 && i > 0 && i < cells;
      if (keepH) boxes.push([cx + p, cz + o, size, 1.4]);
      if (keepV) boxes.push([cx + o, cz + p, 1.4, size]);
    }
  }
  g.add(hedges(boxes.filter(([x, z]) => Math.hypot(x - cx, z - cz) > 9)));
  const gaz = grandDome(6, { drum: 0, panel: null, frame: M.white() }); gaz.position.set(cx, 0.6, cz); g.add(gaz);
  const gazFloor = new THREE.Mesh(new THREE.CylinderGeometry(6.5, 6.5, 0.6, 10), M.marble()); gazFloor.position.set(cx, 0.3, cz); g.add(gazFloor);
  // flower beds and a reflecting pool down the drive
  const beds = [[-20, 80], [20, 80], [-20, 96], [20, 96]];
  for (const [x, z] of beds) {
    const bed = new THREE.Mesh(new THREE.BoxGeometry(14, 1, 10), lambert("#5a3a22")); bed.position.set(x, 0.5, z); g.add(bed);
    const flowers: THREE.Matrix4[] = [];
    for (let i = 0; i < 30; i++) flowers.push(T(x - 6 + (i % 6) * 2.4, 1.3, z - 4 + Math.floor(i / 6) * 2));
    g.add(instances(new THREE.SphereGeometry(0.6, 6, 4), lambert(["#ff7aa8", "#ffd27a", "#c89aff", "#ff8a5a"][(x > 0 ? 1 : 0) + (z > 90 ? 2 : 0)]), flowers));
  }
  for (const x of [-52, 52]) { const p = pool(12, 30); p.position.set(x, 0, 80); g.add(p); }
  g.add(lamps([[-10, 64], [10, 64], [-10, 108], [10, 108]]));
  g.add(palms([[-70, 30], [70, 30], [-80, 70], [80, 70]]));
  arrival(g, "The Conservatory", owner, "#a0ffd0");
  lights(g, [[0, 40, 30, "#fff4e0", 160]]);
  obstacles.push({ x: cx, z: cz, r: 7 }, { x: -52, z: 80, r: 9 }, { x: 52, z: 80, r: 9 });
  return { group: g, obstacles, tick: (t) => ticks.forEach((f2) => f2(t)), sky: ["#16304a", "#e8b07a"], ground: "#3a6a30" };
}

/** 5. The Ballroom: one vast dome lit from inside, a chandelier, a dance floor, fireworks. */
function ballroom(owner: string): Estate {
  const g = new THREE.Group();
  const ticks: ((t: number) => void)[] = [];
  const R = 46;
  const warm = new THREE.MeshStandardMaterial({ color: "#ffe2b0", emissive: "#ffb060", emissiveIntensity: 0.55, transparent: true, opacity: 0.55, side: THREE.DoubleSide, depthWrite: false });
  const dome = grandDome(R, { drum: 16, panel: warm, frame: M.gold(), drumMat: M.marble(), lantern: true }); dome.position.set(0, 0, -36); g.add(dome);
  // the front: a great arched doorway of columns, open to the lawn
  const pts: [number, number][] = [];
  for (let i = -5; i <= 5; i++) { const a = (i / 5) * 0.55; pts.push([Math.sin(a) * (R + 3), -36 + Math.cos(a) * (R + 3)]); }
  g.add(columns(pts, 22, 1.1));
  // inside: a chequered dance floor, a chandelier of light, tables round the edge
  const floor: THREE.Matrix4[] = [], floorB: THREE.Matrix4[] = [];
  for (let i = -8; i < 8; i++) for (let j = -8; j < 8; j++) ((i + j) % 2 ? floor : floorB).push(new THREE.Matrix4().makeTranslation(i * 3 + 1.5, 0.15, -36 + j * 3 + 1.5));
  g.add(instances(new THREE.BoxGeometry(3, 0.3, 3), M.black(), floor));
  g.add(instances(new THREE.BoxGeometry(3, 0.3, 3), M.marble(), floorB));
  const chand = new THREE.Group();
  for (let ring = 0; ring < 4; ring++) {
    const n = 10 + ring * 6, r = 3 + ring * 2.6;
    for (let i = 0; i < n; i++) { const a = (i / n) * Math.PI * 2; const c = new THREE.Mesh(new THREE.OctahedronGeometry(0.45), M.glow("#fff4d8", 2)); c.position.set(Math.cos(a) * r, -ring * 2.2, Math.sin(a) * r); chand.add(c); }
  }
  chand.position.set(0, R * 0.85, -36); g.add(chand);
  const chandLight = new THREE.PointLight("#ffd8a0", 320, 120, 1.3); chandLight.position.set(0, R * 0.7, -36); g.add(chandLight);
  ticks.push((t) => { chand.rotation.y = t * 0.15; });
  const tables: THREE.Matrix4[] = [];
  for (let i = 0; i < 16; i++) { const a = (i / 16) * Math.PI * 2; tables.push(T(Math.cos(a) * 34, 1.6, -36 + Math.sin(a) * 34)); }
  g.add(instances(new THREE.CylinderGeometry(2.4, 2.4, 0.3, 14), M.white(), tables));
  g.add(instances(new THREE.CylinderGeometry(0.3, 0.6, 3, 8), M.gold(), tables.map((m) => m.clone().multiply(new THREE.Matrix4().makeTranslation(0, -1.5, 0)))));
  // a champagne tower: glasses stacked in a pyramid
  const glasses: THREE.Matrix4[] = [];
  for (let lvl = 0; lvl < 5; lvl++) for (let i = 0; i <= lvl; i++) for (let j = 0; j <= lvl; j++) glasses.push(T((i - lvl / 2) * 1.1, 6 - lvl * 1.1, 26 + (j - lvl / 2) * 1.1));
  g.add(instances(new THREE.ConeGeometry(0.5, 1, 10, 1, true), M.glass("#fff2c0", 0.7), glasses));
  const ct = new THREE.Mesh(new THREE.CylinderGeometry(4, 4, 0.8, 16), M.marble()); ct.position.set(0, 0.4, 26); g.add(ct);
  // the lawn: party lights, lamps, cars on the drive, fireworks overhead
  g.add(drive([[0, 112], [0, 40]], 12));
  const poles = [[-40, 20], [40, 20], [-40, 70], [40, 70], [-14, 92]].map(([x, z]) => new THREE.Vector3(x, 16, z));
  g.add(lamps(poles.map((p) => [p.x, p.z] as [number, number]), 15));
  g.add(festoons([[poles[0], poles[1]], [poles[0], poles[2]], [poles[1], poles[3]], [poles[2], poles[3]], [poles[2], poles[4]], [poles[3], poles[4]]], 20));
  g.add(place(roadster("#c8102e"), -18, 0, 72, 0.3), place(roadster("#f4e04d"), 18, 0, 64, -0.5), place(roadster("#e8e8e8"), -16, 0, 50, 0.6));
  const fw = fireworks(new THREE.Vector3(0, 90, -40), 120); g.add(fw.points); ticks.push(fw.tick);
  arrival(g, "The Ballroom", owner);
  lights(g, [[0, 26, 30, "#ffd9a0", 180]]);
  return { group: g, obstacles: [{ x: 0, z: -36, r: R + 4 }, { x: 0, z: 26, r: 5 }], tick: (t) => ticks.forEach((f2) => f2(t)), sky: ["#05081c", "#7a3a6a"], ground: "#2f5a2c" };
}

const BUILDERS: Record<string, (owner: string) => Estate> = { starter, "1": westEgg, "2": eastEgg, "3": decoPalace, "4": conservatory, "5": ballroom };

/** Build a house: its style (a HOUSE_STYLES key) and the line on its gate sign. */
export function buildEstate(style: string, owner: string): Estate {
  return (BUILDERS[style] || starter)(owner);
}
