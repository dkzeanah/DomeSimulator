// The Triangle Infill tool's pieces on the Panel Creator's stage: one panel type up close, every
// piece its own (pickable) mesh in the frame, or the whole dome with every triangle filled, each
// panel set on its seat. Panel inches (x along the base, y up the triangle, z into the dome from
// the sawn face) and dome inches (z up) in the tool; feet, y up, here.

import * as THREE from "three";
import { P, type KindTable, type RowsMesh } from "./infill";

export const STAGE_RADIUS_FT = 8.4;
/** The close-up triangle is drawn this much bigger than full size, so it reads from the walk. */
export const CLOSE_ENLARGE = 1.5;

type Map3 = (x: number, y: number, z: number) => [number, number, number];

function geometry(m: RowsMesh, ranges: [number, number][], map: Map3): THREE.BufferGeometry {
  let n = 0;
  for (const [, c] of ranges) n += c;
  const pos = new Float32Array(n * 3), col = new Float32Array(n * 3);
  let k = 0;
  for (const [v0, c] of ranges) for (let i = v0; i < v0 + c; i++, k++) {
    const p = map(m.pos[i * 3] * m.scale, m.pos[i * 3 + 1] * m.scale, m.pos[i * 3 + 2] * m.scale);
    pos[k * 3] = p[0]; pos[k * 3 + 1] = p[1]; pos[k * 3 + 2] = p[2];
    const cc = m.palette[m.col[i]] || [0.8, 0.6, 0.4];
    col[k * 3] = cc[0]; col[k * 3 + 1] = cc[1]; col[k * 3 + 2] = cc[2];
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  g.setAttribute("color", new THREE.BufferAttribute(col, 3));
  g.computeVertexNormals();
  return g;
}

const solid = () => new THREE.MeshLambertMaterial({ vertexColors: true, flatShading: true, side: THREE.DoubleSide });

/** One panel type, standing on the stage leaning back toward the walker. */
export function drawPanel(kind: number, frames: RowsMesh, fill: RowsMesh | null, table: KindTable | null, picked: number | null): THREE.Group {
  const g = new THREE.Group();
  const tri = P.types[kind].tri as number[][];
  const cx = (tri[0][0] + tri[1][0] + tri[2][0]) / 3;
  const s = CLOSE_ENLARGE / 12;
  const map: Map3 = (x, y, z) => [(x - cx) * s, y * s, -z * s];
  g.add(new THREE.Mesh(geometry(frames, [P.frames.kinds[kind] as [number, number]], map), solid()));
  if (fill && table) {
    const glow = new THREE.MeshLambertMaterial({ vertexColors: true, flatShading: true, side: THREE.DoubleSide, emissive: new THREE.Color("#ffb347"), emissiveIntensity: 0.55 });
    const mat = solid();
    for (const p of table.pieces) {
      if (!p.v[1]) continue;
      const mesh = new THREE.Mesh(geometry(fill, [p.v], map), p.n === picked ? glow : mat);
      mesh.castShadow = true;
      mesh.userData.part = { id: `infill:${p.n}`, name: `piece ${p.n}`, examine: `Piece ${p.n} (${p.name}): ${p.long.toFixed(2)} in long, ${p.short.toFixed(2)} in short. ${p.cuts}` };
      g.add(mesh);
    }
  }
  // turned to the sun and leaning back toward the walker: the face you see is the panel's inside
  const lean = new THREE.Group();
  lean.rotation.set(0.42, Math.PI, 0);
  lean.add(g);
  lean.position.set(0, 0.3, 1.2);
  return lean;
}

/** The whole dome: every seat's frame and, if given, its fill. */
export function drawDome(frames: RowsMesh, fill: RowsMesh | null, table: { kinds: KindTable[] } | null): { group: THREE.Group; scale: number } {
  const g = new THREE.Group();
  const fit = Math.min(1, STAGE_RADIUS_FT / (P.radiusIn / 12));
  const s = fit / 12;
  // the seats' lowest corner stands on the stage
  let low = Infinity;
  for (const st of P.seats) low = Math.min(low, st.origin[2]);
  const kindRanges = table?.kinds.map((k) => k.pieces.filter((p) => p.v[1]).map((p) => p.v)) ?? [];
  const parts: THREE.BufferGeometry[] = [], fills: THREE.BufferGeometry[] = [];
  for (const st of P.seats) {
    const b = st.basis as number[][], o = st.origin as number[];
    const map: Map3 = (x, y, z) => {
      const X = b[0][0] * x + b[0][1] * y + b[0][2] * z + o[0];
      const Y = b[1][0] * x + b[1][1] * y + b[1][2] * z + o[1];
      const Z = b[2][0] * x + b[2][1] * y + b[2][2] * z + o[2];
      return [X * s, (Z - low) * s, -Y * s];
    };
    parts.push(geometry(frames, [P.frames.kinds[st.kind] as [number, number]], map));
    if (fill && kindRanges[st.kind]?.length) fills.push(geometry(fill, kindRanges[st.kind] as [number, number][], map));
  }
  const merge = (gs: THREE.BufferGeometry[]) => {
    let n = 0;
    for (const x of gs) n += x.getAttribute("position").count;
    const pos = new Float32Array(n * 3), col = new Float32Array(n * 3);
    let k = 0;
    for (const x of gs) { pos.set(x.getAttribute("position").array as Float32Array, k * 3); col.set(x.getAttribute("color").array as Float32Array, k * 3); k += x.getAttribute("position").count; x.dispose(); }
    const m = new THREE.BufferGeometry();
    m.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    m.setAttribute("color", new THREE.BufferAttribute(col, 3));
    m.computeVertexNormals();
    return m;
  };
  const frame = new THREE.Mesh(merge(parts), solid());
  frame.castShadow = true;
  g.add(frame);
  if (fills.length) { const f = new THREE.Mesh(merge(fills), solid()); f.castShadow = true; g.add(f); }
  return { group: g, scale: fit };
}
