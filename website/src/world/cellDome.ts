// The cell wall on the solver's dome: the reference dome the cell wall is reckoned on
// (two_v_demo.channel_facts.reference_model, exported in cell-wall.json), its skin drawn as the
// stack of layers -- room side inside the frame, weather side outside, thicker than real so the
// stack shows -- each layer a shell of forty cells, every cell with its local loop (one closed run
// round that triangle alone) and the layer's global runs along the seams. A layer the router has
// on glows and its flow moves; the frame's seams can carry the climate controller's air, or show
// their band (where they run, and whether they drain) with the rim ports and the belt's low
// points; the cells can show how many hops each is from the rim. Like two_v_demo.cell_wall_scene,
// where things stand is drawing; every figure is in the panel, from the modules.

import * as THREE from "three";
import { CW, type Layer } from "./climate";
import { MODE_COLOUR, PATHS } from "./cellView";

/** How much thicker than real the layers are drawn on the dome, so the stack can be seen. */
export const DOME_EXAGGERATE = 6;
const DOME_STAGE_FT = 8.2;
export const BAND_COLOUR: Record<string, string> = { lower: "#6fdc9b", belt: "#e8b45a", upper: "#7cc4f0", pentagon: "#ff8a7a", cap: "#d47ac0" };

export interface CellDomeView {
  stack: string[];
  /** Each layer's mode ("off" or missing: idle). */
  modes: Record<string, string>;
  /** Extra room between layers, feet on the stage: pull the stack apart. */
  peel: number;
  /** Draw only this layer (and the frame). */
  only?: string | null;
  /** Seams coloured by their band, with the rim ports and belt low points. */
  bands?: boolean;
  /** One band lit. */
  band?: string | null;
  /** Cells coloured by how many hops they are from the rim (the local net). */
  hops?: boolean;
  /** The climate controller's mode, flowing along the frame's seams. */
  seamMode?: string | null;
  /** Show the cells' local loops and the layers' global runs. */
  loops?: boolean;
}

export function drawCellDome(v: CellDomeView): THREE.Group {
  const g = new THREE.Group();
  const dome = CW.dome;
  const s = DOME_STAGE_FT / (dome.radiusIn / 12) / 12;          // stage feet per inch
  const P = (p: number[]) => new THREE.Vector3(p[0] * s, p[2] * s, -p[1] * s);
  const verts = dome.vertices;
  const layers = v.stack.map((k) => CW.wall.layers.find((l) => l.key === k)).filter(Boolean) as Layer[];
  const core = Math.max(0, layers.findIndex((l) => l.key === "core"));
  const thick = (l: Layer) => Math.max(0.6, (l.thicknessMm / 25.4) * DOME_EXAGGERATE);     // inches on the drawing
  const gap = v.peel / (s * 1);                                                            // the peel, in drawing inches
  // each layer's radius: the core on the frame's own sphere, room-side layers inside it, weather-side outside
  const radius: number[] = layers.map(() => dome.radiusIn);
  let out = dome.radiusIn;
  for (let i = core + 1; i < layers.length; i++) { out += thick(layers[i]) + gap; radius[i] = out; }
  let inn = dome.radiusIn;
  for (let i = core - 1; i >= 0; i--) { inn -= thick(layers[i]) + gap; radius[i] = inn; }
  const onSphere = (p: number[], r: number) => { const n = Math.hypot(p[0], p[1], p[2]) || 1; return p.map((x) => (x * r) / n); };
  const start = performance.now();
  // the dashes move by shifting every point's distance along its line (this three.js has no dash offset)
  const flowing = (line: THREE.Line | THREE.LineSegments, speed: number) => {
    line.computeLineDistances();
    const attr = line.geometry.getAttribute("lineDistance") as THREE.BufferAttribute;
    const base = Float32Array.from(attr.array as Float32Array);
    line.onBeforeRender = () => {
      const t = ((performance.now() - start) / 1000) * speed;
      const a = attr.array as Float32Array;
      for (let i = 0; i < a.length; i++) a[i] = base[i] - t;
      attr.needsUpdate = true;
    };
  };

  layers.forEach((l, li) => {
    if (v.only && l.key !== v.only && l.key !== "core") return;
    const r = radius[li];
    const mode = v.modes[l.key] || "off";
    const on = mode !== "off";
    const col = new THREE.Color(l.colour[0], l.colour[1], l.colour[2]);
    const isCore = l.key === "core";
    const cellMat = new THREE.MeshLambertMaterial({ color: col, transparent: true, side: THREE.DoubleSide, depthWrite: false,
      opacity: isCore ? 0.16 : on ? 0.42 : 0.14, emissive: col, emissiveIntensity: on ? 0.35 : 0 });
    const loopMat = on ? new THREE.LineDashedMaterial({ color: col.clone().lerp(new THREE.Color("#ffffff"), 0.35), dashSize: 1.2, gapSize: 0.8 })
      : new THREE.LineBasicMaterial({ color: col, transparent: true, opacity: 0.5 });
    const loopPts: THREE.Vector3[] = [];
    dome.faces.forEach((f, fi) => {
      const tri = f.v.map((i) => onSphere(verts[i], r));
      const cen = [0, 1, 2].map((k) => (tri[0][k] + tri[1][k] + tri[2][k]) / 3);
      const inset = (p: number[], t: number) => p.map((x, k) => x + (cen[k] - x) * t);
      // the cell: the triangle, a little in from its seams
      const geo = new THREE.BufferGeometry().setFromPoints(tri.map((p) => P(inset(p, 0.04))));
      geo.setIndex([0, 1, 2]); geo.computeVertexNormals();
      let m: THREE.Material = cellMat;
      if (v.hops && isCore) {
        const h = Math.max(0, f.hops);
        m = new THREE.MeshLambertMaterial({ color: new THREE.Color().setHSL(0.33 - h * 0.08, 0.7, 0.5), transparent: true, opacity: 0.75, side: THREE.DoubleSide, depthWrite: false });
      }
      const mesh = new THREE.Mesh(geo, m);
      mesh.userData.part = { id: `cell:${l.key}:${fi}`, name: `${l.label}, cell ${fi + 1}`,
        examine: `Cell ${fi + 1} of ${dome.faces.length} in the ${l.label} layer (${l.side} side), ${f.hops} hops from the rim. ${on ? `Now: ${mode}.` : "Idle."}` };
      g.add(mesh);
      if (v.loops !== false) {
        const loop = tri.map((p) => P(inset(p, 0.16)));
        for (let k = 0; k < 3; k++) loopPts.push(loop[k], loop[(k + 1) % 3]);
      }
    });
    if (loopPts.length) {
      const loops = new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(loopPts), loopMat);
      if (on) flowing(loops, 1.5);
      g.add(loops);
    }
    // the layer's global runs, along the seams between its cells
    if (v.loops !== false && !isCore) {
      const pts: THREE.Vector3[] = [];
      for (const q of dome.seams) pts.push(P(onSphere(verts[q.v[0]], r)), P(onSphere(verts[q.v[1]], r)));
      const gm = on ? new THREE.LineDashedMaterial({ color: col, dashSize: 2, gapSize: 1.2 }) : new THREE.LineBasicMaterial({ color: col, transparent: true, opacity: 0.35 });
      const runs = new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(pts), gm);
      if (on) flowing(runs, 3);
      g.add(runs);
    }
  });

  // the frame's own seams: by band, or carrying the controller's air
  const marked = Boolean(v.bands || v.band);
  for (const q of dome.seams) {
    const lit = v.band ? q.band === v.band : true;
    const colour = marked ? (lit ? BAND_COLOUR[q.band] ?? "#ffffff" : "#3a3a3a") : v.seamMode ? (MODE_COLOUR[v.seamMode] ?? "#888888") : "#c8914e";
    const a = P(verts[q.v[0]]), b = P(verts[q.v[1]]);
    const tube = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, a.distanceTo(b), 5),
      new THREE.MeshLambertMaterial({ color: colour, emissive: new THREE.Color(colour), emissiveIntensity: lit && marked ? 0.4 : 0.1 }));
    tube.position.copy(a.clone().add(b).multiplyScalar(0.5));
    tube.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize());
    const band = CW.climate.bands.find((x) => x.key === q.band);
    tube.userData.part = { id: `seam:${q.id}`, name: `Seam ${q.id} (${q.type}), ${band?.label ?? q.band}`,
      examine: `Seam ${q.id}: a ${q.type} seam in the ${band?.label ?? q.band}, ${band ? `${band.slopeDeg.toFixed(1)}° on average` : ""}${band && !band.drains ? ", dead level: it does not drain" : ""}.` };
    g.add(tube);
    if (v.seamMode && !marked && (PATHS[v.seamMode] || []).length) {
      const air = new THREE.Line(new THREE.BufferGeometry().setFromPoints([a.clone().multiplyScalar(1.01), b.clone().multiplyScalar(1.01)]),
        new THREE.LineDashedMaterial({ color: MODE_COLOUR[v.seamMode], dashSize: 0.4, gapSize: 0.3 }));
      flowing(air, 1.2);
      g.add(air);
    }
  }
  // rim ports and the belt's low points: where the seams drain out, and where the belt gathers
  if (marked) {
    const mark = (i: number, colour: string, label: string) => {
      const m = new THREE.Mesh(new THREE.SphereGeometry(0.28, 10, 8), new THREE.MeshLambertMaterial({ color: colour, emissive: new THREE.Color(colour), emissiveIntensity: 0.5 }));
      m.position.copy(P(verts[i]));
      m.userData.part = { id: `port:${i}`, name: label };
      g.add(m);
    };
    dome.rimPorts.forEach((i) => mark(i, "#3aa0ff", "Rim port: the seams drain out here"));
    dome.lowPoints.forEach((i) => mark(i, "#ffe24a", "Belt low point: where the belt's seams gather"));
  }
  // the tank the water layer fills and floods from, by the rim
  const tank = new THREE.Mesh(new THREE.CylinderGeometry(1.1, 1.1, 2.6, 18), new THREE.MeshLambertMaterial({ color: (v.modes.water || "off") !== "off" ? "#3a8ad0" : "#4a5a6a" }));
  const rim0 = P(verts[dome.rimPorts[0]]);
  tank.position.set(rim0.x * 1.25, 1.3, rim0.z * 1.25);
  tank.userData.part = { id: "tank", name: "The tank", examine: "Rain from the outside channel comes in through the rim to here; the flood goes back out from it." };
  g.add(tank);
  g.position.y = 0.05;
  return g;
}
