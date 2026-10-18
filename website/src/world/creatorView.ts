// The Dome Creator's design, drawn on the space's stage: its struts, nodes and panels exactly as
// creator.ts computed them, scaled to stand on the pedestal (the Creator works in metres; the
// world in feet), with the panels tinted by type.

import * as THREE from "three";
import type { Design } from "./creator";

const FRAME: Record<string, string> = {
  "Galvanized Steel": "#a9b0b8", "Structural Steel": "#6f767e", "Rebar Steel": "#7a5a44", Aluminum: "#cfd4da",
  "Timber (SPF)": "#c8914e", "Whole Tree Trunk": "#6a4a2e", "PVC Pipe": "#eeeeea", Bamboo: "#c9b26a",
};
const PANEL: Record<string, [string, number]> = {
  Open: ["#000000", 0], Plywood: ["#c9a26c", 0.92], "Glass Window": ["#9fd4ff", 0.28], "Acrylic Window": ["#bfe4ff", 0.3],
  "Polycarb Twinwall": ["#e8f2f6", 0.45], "Plastic Sheeting": ["#f2f6f8", 0.35], "Insulated SIP": ["#e0d2b0", 0.95],
  "Shingle Panel": ["#5a4a44", 0.95], "Metal Panel": ["#9aa2aa", 0.95], "Solar Panel": ["#1e2c5a", 0.95], Canvas: ["#efe6d0", 0.85],
  "Hex Composite": ["#8a8f7a", 0.9], "Hex Mirror": ["#dfe8ee", 0.8], "Square Mirror": ["#dfe8ee", 0.8],
  "Concrete Form Panel": ["#a8a49a", 0.95], "Precast Concrete": ["#9a968c", 0.95],
};

/** Fit the dome to a stage this many feet in radius. */
export const STAGE_RADIUS_FT = 8.2;

export function drawDesign(d: Design): THREE.Group {
  const g = new THREE.Group();
  const r = d.config.radius;
  const s = STAGE_RADIUS_FT / r;
  const lift = -d.baseZ * r;                     // the Creator's base plane sits on the stage
  const at = (p: number[]) => new THREE.Vector3(p[0] * s, (p[2] + lift) * s, -p[1] * s);

  const strutR = Math.max(0.05, Math.min(0.32, d.config.strutWidth * s * 0.6));
  const strutMat = new THREE.MeshLambertMaterial({ color: FRAME[d.config.frameMaterial] || "#c8914e", flatShading: true });
  const geo = new THREE.CylinderGeometry(strutR, strutR, 1, 5);
  const bars = new THREE.InstancedMesh(geo, strutMat, d.struts.length);
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), up = new THREE.Vector3(0, 1, 0);
  d.struts.forEach(([p0, p1], i) => {
    const a = at(p0), b = at(p1), dir = b.clone().sub(a);
    q.setFromUnitVectors(up, dir.clone().normalize());
    m.compose(a.clone().add(b).multiplyScalar(0.5), q, new THREE.Vector3(1, dir.length(), 1));
    bars.setMatrixAt(i, m);
  });
  bars.castShadow = true;
  g.add(bars);

  if (d.hubCount) {
    const nodes = new THREE.InstancedMesh(new THREE.SphereGeometry(strutR * 1.9, 8, 6),
      new THREE.MeshLambertMaterial({ color: d.config.hubStyle === "Metal Brackets" ? "#8a9098" : "#3a3a3a" }), d.hubCount);
    const seen = new Map<string, THREE.Vector3>();
    for (const [p0, p1] of d.struts) for (const p of [p0, p1]) seen.set(p.map((x) => x.toFixed(4)).join(","), at(p));
    [...seen.values()].slice(0, d.hubCount).forEach((v, i) => { m.makeTranslation(v.x, v.y, v.z); nodes.setMatrixAt(i, m); });
    g.add(nodes);
  }

  const [colour, opacity] = PANEL[d.config.panel] || ["#c9a26c", 0.9];
  if (opacity > 0) {
    const pos: number[] = [];
    for (const t of d.panels) for (const p of t) { const v = at(p); pos.push(v.x, v.y, v.z); }
    const pg = new THREE.BufferGeometry();
    pg.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    pg.computeVertexNormals();
    const pm = new THREE.Mesh(pg, new THREE.MeshLambertMaterial({ color: colour, transparent: opacity < 0.9, opacity, side: THREE.DoubleSide, flatShading: true, depthWrite: opacity >= 0.9 }));
    pm.scale.setScalar(0.995);                    // just inside the struts
    g.add(pm);
  }
  return g;
}
