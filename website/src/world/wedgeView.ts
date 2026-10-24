// The raw-wedge simulator's meshes on the 3D Wedge Method space's stage: the solved dome, member
// by member (with its seam keys and the head stock the jig flush-cuts away), or one panel's jig
// at one step of its walk-through. Inches, z up, in the simulator; feet, y up, here. For an
// alternating build the members can be tinted by which way their panel points, the dome raised
// band by band, and the matched seams (in/in or out/out, where the faces do not cancel) lit.

import * as THREE from "three";
import type { JigHead, MeshBuffers, MeshHead } from "./wedge";

export const STAGE_RADIUS_FT = 8.4;

type PartHead = { v: number[]; i: number[] };

function partGeometry(buf: MeshBuffers, scale: number, palette: number[][], p: PartHead, s: number, origin: THREE.Vector3) {
  const [v0, vn] = p.v, [i0, inn] = p.i;
  const pos = new Float32Array(vn * 3), col = new Float32Array(vn * 3);
  for (let k = 0; k < vn; k++) {
    const x = buf.pos[(v0 + k) * 3] * scale, y = buf.pos[(v0 + k) * 3 + 1] * scale, z = buf.pos[(v0 + k) * 3 + 2] * scale;
    pos[k * 3] = (x - origin.x) * s; pos[k * 3 + 1] = (z - origin.z) * s; pos[k * 3 + 2] = -(y - origin.y) * s;
    const c = palette[buf.col[v0 + k]] || [0.8, 0.6, 0.4];
    col[k * 3] = c[0]; col[k * 3 + 1] = c[1]; col[k * 3 + 2] = c[2];
  }
  const idx = new Uint16Array(inn);
  for (let k = 0; k < inn; k++) idx[k] = buf.idx[i0 + k] - v0;
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  g.setAttribute("color", new THREE.BufferAttribute(col, 3));
  g.setIndex(new THREE.BufferAttribute(idx, 1));
  g.computeVertexNormals();
  return g;
}

function bounds(buf: MeshBuffers, scale: number, parts: PartHead[]) {
  const lo = new THREE.Vector3(Infinity, Infinity, Infinity), hi = new THREE.Vector3(-Infinity, -Infinity, -Infinity);
  for (const p of parts) for (let k = p.v[0]; k < p.v[0] + p.v[1]; k++) {
    const v = new THREE.Vector3(buf.pos[k * 3] * scale, buf.pos[k * 3 + 1] * scale, buf.pos[k * 3 + 2] * scale);
    lo.min(v); hi.max(v);
  }
  return { lo, hi };
}

export interface DomeView {
  explode: number; keys: boolean; offcuts: boolean; family: "A" | "B" | null; picked: string | null;
  /** Each panel's band (1 the ground ring), and the highest band to draw: the dome going up. */
  bandOf?: number[]; maxBand?: number;
  /** Tint each member by which way its panel points. */
  pointsOf?: ("in" | "out")[];
  /** Seam keys to light up (the matched seams, or one picked seam). */
  hot?: Set<string>;
}

export function drawDome(head: MeshHead, buf: MeshBuffers, view: DomeView): { group: THREE.Group; scale: number } {
  const g = new THREE.Group();
  const members = head.parts.filter((p) => p.kind === "member");
  const { lo, hi } = bounds(buf, head.scale, members);
  const radiusFt = Math.max(hi.x - lo.x, hi.y - lo.y) / 24;
  const fit = Math.min(1, STAGE_RADIUS_FT / radiusFt);
  const s = fit / 12;
  const origin = new THREE.Vector3((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z);
  const normals = head.faceNormals;
  const mats = new Map<string, THREE.Material>();
  const EMISSIVE: Record<string, string> = { glow: "#ffb347", in: "#4a2a00", out: "#002a4a", hot: "#ff2a1a" };
  const mat = (kind: "solid" | "dim" | "glow" | "ghost" | "in" | "out" | "hot") => {
    if (!mats.has(kind)) mats.set(kind, new THREE.MeshLambertMaterial({
      vertexColors: true, flatShading: true, side: THREE.DoubleSide,
      transparent: kind === "dim" || kind === "ghost", opacity: kind === "dim" ? 0.18 : kind === "ghost" ? 0.55 : 1, depthWrite: kind !== "dim" && kind !== "ghost",
      emissive: new THREE.Color(EMISSIVE[kind] ?? "#000000"), emissiveIntensity: EMISSIVE[kind] ? 0.6 : 0,
    }));
    return mats.get(kind)!;
  };
  const shown = (faces: number[]) => !view.bandOf || view.maxBand === undefined || faces.every((f) => (view.bandOf![f] ?? 0) <= view.maxBand!);
  const shift = (faces: number[]) => {
    const n = new THREE.Vector3();
    for (const f of faces) n.add(new THREE.Vector3(normals[f][0], normals[f][2], -normals[f][1]));
    return n.multiplyScalar((view.explode * s) / faces.length);
  };
  for (const p of head.parts) {
    if (p.kind === "key" && !view.keys) continue;
    if (p.kind === "offcut" && !view.offcuts) continue;
    if (!p.v[1]) continue;
    const faces = "faces" in p && Array.isArray(p.faces) ? (p.faces as number[]) : [(p as { face: number }).face];
    if (!shown(faces)) continue;
    const geo = partGeometry(buf, head.scale, head.palette, p, s, origin);
    let m: THREE.Material;
    if (p.kind === "member") {
      const fam = (p as { type?: string }).type;
      m = p.id === view.picked ? mat("glow") : view.family && fam !== view.family ? mat("dim")
        : view.pointsOf ? mat(view.pointsOf[faces[0]] === "out" ? "out" : "in") : mat("solid");
    } else m = p.kind === "offcut" ? mat("ghost") : p.kind === "key" && view.hot?.has(p.id as string) ? mat("hot") : view.family || view.hot?.size ? mat("dim") : mat("solid");
    const mesh = new THREE.Mesh(geo, m);
    mesh.position.copy(shift(faces));
    mesh.castShadow = p.kind === "member";
    const q = p as Record<string, unknown>;
    if (p.kind === "member") mesh.userData.part = {
      id: `wedge:${p.id}`, name: `${q.type} member ${p.id}`,
      examine: `${p.id}, a ${q.type} member: ${(q.nominal as number).toFixed(2)} in nominal edge, cut from a ${(q.blank as number).toFixed(2)} in blank. Its butt sits ${(q.butt as number).toFixed(2)} in back from the vertex and bears on ${q.buttInto}; ${q.receives} butts into it.`,
    };
    else if (p.kind === "key") mesh.userData.part = {
      id: `key:${p.id}`, name: `seam key ${p.id}`,
      examine: `Seam ${p.id} (${q.type}): the panels fold ${(q.fold as number).toFixed(2)}°, the raw wedge faces leave ${(q.gap as number).toFixed(2)}° for the key, ${(q.keyBase as number).toFixed(2)} in across at its base.`,
    };
    g.add(mesh);
  }
  g.position.y = 0.05;
  return { group: g, scale: fit };
}

/** How much bigger than full size the jig is drawn: a 6 ft panel on its bench is small from the walk. */
export const JIG_ENLARGE = 2;

/** One panel's jig at one stage, enlarged, centred on the stage. */
export function drawJig(head: JigHead, buf: MeshBuffers, stage: number): THREE.Group {
  const g = new THREE.Group();
  const all = head.parts as (PartHead & { stage: number; kind: string })[];
  // centre on the whole walk-through, so the bench stays put as the steps go by
  const { lo, hi } = bounds(buf, head.scale, all.filter((p) => p.v[1]));
  const s = JIG_ENLARGE / 12;
  const origin = new THREE.Vector3((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z);
  const lift = 1.4;                                   // a low bench, so the camera sees the sheet
  const names: Record<string, string> = { jig_fixture: "the jig", jig_wood: "a stick", jig_hangoff: "butt stock to cut off", jig_head_overfit: "head stock to flush-cut" };
  for (const p of all) {
    if (p.stage !== stage || !p.v[1]) continue;
    const ghost = p.kind === "jig_hangoff" || p.kind === "jig_head_overfit";
    const mesh = new THREE.Mesh(partGeometry(buf, head.scale, head.palette, p, s, origin),
      new THREE.MeshLambertMaterial({ vertexColors: true, flatShading: true, side: THREE.DoubleSide, transparent: ghost, opacity: ghost ? 0.75 : 1 }));
    mesh.castShadow = true;
    mesh.userData.part = { id: `jig:${p.kind}`, name: names[p.kind] || p.kind };
    g.add(mesh);
  }
  const lines = head.lines[stage] as number[][];
  if (lines?.length) {
    const pos: number[] = [], col: number[] = [];
    for (const r of lines) { pos.push((r[0] - origin.x) * s, (r[2] - origin.z) * s + 0.01, -(r[1] - origin.y) * s); col.push(r[3], r[4], r[5]); }
    const lg = new THREE.BufferGeometry();
    lg.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    lg.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
    g.add(new THREE.LineSegments(lg, new THREE.LineBasicMaterial({ vertexColors: true })));
  }
  // the sawhorses the sheet sits on
  const horse = new THREE.MeshLambertMaterial({ color: "#7a5a3a", flatShading: true });
  const span = Math.max(hi.x - lo.x, hi.y - lo.y) * s;
  for (const x of [-span * 0.32, span * 0.32]) {
    const h = new THREE.Mesh(new THREE.BoxGeometry(0.3, lift, span * 0.7), horse);
    h.position.set(x, -lift / 2, 0); g.add(h);
  }
  g.position.y = lift;
  return g;
}
