// The Cell Wall & Seams space's stage: a cut through the dome's skin. For the seam's climate, two
// panels meeting at a seam with the channel between them, outside on the left and the room on the
// right, and the air the controller's mode sends moving along its path. For the cell wall, the
// layer stack as slabs (their real thicknesses, exaggerated so they can be seen), each pickable.

import * as THREE from "three";
import { CW, type Layer } from "./climate";

const box = (w: number, h: number, d: number, colour: string, opacity = 1) =>
  new THREE.Mesh(new THREE.BoxGeometry(w, h, d), new THREE.MeshLambertMaterial({ color: colour, transparent: opacity < 1, opacity, flatShading: true }));

/** Where the air goes in each mode: a path of points in the section (x: outside -6 to room +6). */
const PATHS: Record<string, [number, number][]> = {
  INTAKE: [[-7, 1], [-1.2, 1.5], [0, 3], [0, 6], [1.2, 7.5], [7, 7]],
  EXHAUST: [[7, 7], [1.2, 7.5], [0, 6], [0, 3], [-1.2, 1.5], [-7, 1]],
  CONDENSE: [[7, 7], [1.2, 7.5], [0, 6], [0, 2.4], [0, 1.2], [-1.2, 1], [-7, 1]],
  FRAME_LOOP: [[0, 2], [0, 7.5], [0.7, 8], [0.7, 1.5], [0, 2]],
  PURGE: [[-7, 1], [-1.2, 1.5], [0, 3], [0, 7.5], [-1.2, 8.2], [-7, 8.5]],
  DRY_SUPPLY: [[2.5, 1], [2.5, 4], [7, 4.5]],
  CLOSED: [], IDLE: [],
};
const MODE_COLOUR: Record<string, string> = {
  INTAKE: "#6fdc9b", EXHAUST: "#e8b45a", CONDENSE: "#7cc4f0", FRAME_LOOP: "#d47ac0", PURGE: "#f08a5a", DRY_SUPPLY: "#9aa4ff", CLOSED: "#888", IDLE: "#888",
};

function along(path: [number, number][], t: number): [number, number] {
  const seg: number[] = [];
  let total = 0;
  for (let i = 0; i < path.length - 1; i++) { const d = Math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1]); seg.push(d); total += d; }
  let s = (t % 1) * total;
  for (let i = 0; i < seg.length; i++) {
    if (s <= seg[i]) { const f = s / seg[i]; return [path[i][0] + (path[i + 1][0] - path[i][0]) * f, path[i][1] + (path[i + 1][1] - path[i][1]) * f]; }
    s -= seg[i];
  }
  return path[path.length - 1];
}

export function drawSeam(mode: string, rain: boolean): THREE.Group {
  const g = new THREE.Group();
  // two panels leaning in to a seam at x = 0, the channel a V between them
  const wood = "#c8914e";
  for (const side of [-1, 1]) {
    const p = box(5.6, 0.7, 6, wood);
    p.position.set(side * 3.1, 4.6, 0); p.rotation.z = side * -1.25;
    g.add(p);
  }
  const channel = box(0.9, 7.2, 6, "#2a3a44", 0.55);
  channel.position.set(0, 4.6, 0); g.add(channel);
  const sill = box(14, 0.5, 6, "#6a655a"); sill.position.set(0, 0.25, 0); g.add(sill);
  const outside = box(0.1, 9, 6, "#7cc4f0", 0.18); outside.position.set(-7, 4.5, 0); g.add(outside);
  const room = box(0.1, 9, 6, "#e8b45a", 0.18); room.position.set(7, 4.5, 0); g.add(room);
  if (rain) {
    const drops = new THREE.Points(new THREE.BufferGeometry().setFromPoints(Array.from({ length: 120 }, () => new THREE.Vector3(-7 + Math.random() * 6, Math.random() * 10, -3 + Math.random() * 6))),
      new THREE.PointsMaterial({ color: "#9fd4ff", size: 0.12 }));
    drops.onBeforeRender = () => { const a = drops.geometry.getAttribute("position") as THREE.BufferAttribute; for (let i = 0; i < a.count; i++) { let y = a.getY(i) - 0.15; if (y < 0) y = 10; a.setY(i, y); } a.needsUpdate = true; };
    g.add(drops);
  }
  const path = PATHS[mode] || [];
  if (path.length > 1) {
    const n = 60;
    const pts = new THREE.Points(new THREE.BufferGeometry().setFromPoints(Array.from({ length: n }, () => new THREE.Vector3())),
      new THREE.PointsMaterial({ color: MODE_COLOUR[mode], size: 0.32 }));
    const start = performance.now();
    pts.onBeforeRender = () => {
      const a = pts.geometry.getAttribute("position") as THREE.BufferAttribute;
      const t = (performance.now() - start) / 6000;
      for (let i = 0; i < n; i++) { const [x, y] = along(path, t + i / n); a.setXYZ(i, x, y, ((i * 37) % 11) / 11 * 4 - 2); }
      a.needsUpdate = true;
    };
    pts.frustumCulled = false;
    g.add(pts);
  }
  g.userData.part = { id: "seam:section", name: "the seam", examine: "Two panels meeting at a seam: the V between them is the channel the air, water and wire run in." };
  g.scale.setScalar(0.9);
  return g;
}

/** The layer stack, room side on the right, its slabs this many times their real thickness. */
export const WALL_EXAGGERATE = 12;

export function drawWall(stack: string[], modes: Record<string, string>, temps: Record<string, number>): THREE.Group {
  const g = new THREE.Group();
  const layers = stack.map((k) => CW.wall.layers.find((l) => l.key === k)!) as Layer[];
  const ft = (mm: number) => (mm / 304.8) * WALL_EXAGGERATE;
  const total = layers.reduce((s, l) => s + ft(l.thicknessMm), 0);
  let x = total / 2;                                // room side first, at +x
  for (const l of layers) {
    const w = Math.max(0.08, ft(l.thicknessMm));
    const on = (modes[l.key] || "off") !== "off";
    const [r, gg, b] = l.colour;
    const m = box(w, 8, 6, new THREE.Color(r, gg, b).getStyle(), on ? 0.95 : 0.45);
    (m.material as THREE.MeshLambertMaterial).emissive = new THREE.Color(r, gg, b);
    (m.material as THREE.MeshLambertMaterial).emissiveIntensity = on ? 0.35 : 0;
    m.position.set(x - w / 2, 4.2, 0);
    const temp = temps[l.key];
    m.userData.part = { id: `layer:${l.key}`, name: l.label,
      examine: `${l.label} (${l.side} side, ${l.thicknessMm.toFixed(0)} mm): ${l.job}.${temp !== undefined ? ` About ${temp.toFixed(1)} C in a winter night.` : ""}` };
    g.add(m);
    x -= w;
  }
  const sill = box(total + 1, 0.4, 6.4, "#6a655a"); sill.position.set(0, 0.2, 0); g.add(sill);
  g.rotation.y = -0.5;
  return g;
}
