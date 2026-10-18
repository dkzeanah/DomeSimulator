// The wedge zome drawn on its space's stage: every stick as the solid zome.ts solved (its
// cross-section carried from the tail cut plane to the head cut plane), the rim posts under the
// high corners, and the outside skin if asked for. Inches, z up, in the tool; feet, y up, here.

import * as THREE from "three";
import type { StickType, V3, ZomeModel } from "./zome";

const ROW_WOOD = ["#d9a868", "#c8914e", "#b57a3c", "#a0672f", "#8c5a2a", "#7a4e26"];
export const STAGE_RADIUS_FT = 8.4;

export interface ZomeView { explode: number; skin: boolean; posts: boolean; selected: string | null }

export function fitScale(m: ZomeModel) {
  const rimFt = Math.max(...m.vertices.map((v) => Math.hypot(v[0], v[1]))) / 12;
  return Math.min(1, STAGE_RADIUS_FT / rimFt);
}

export function drawZome(m: ZomeModel, types: StickType[], view: ZomeView): THREE.Group {
  const g = new THREE.Group();
  const s = fitScale(m) / 12;
  const at = (p: V3) => new THREE.Vector3(p[0] * s, p[2] * s, -p[1] * s);
  const typeOf = new Map<object, StickType>();
  for (const t of types) for (const st of t.members) typeOf.set(st, t);

  const mats = new Map<string, THREE.Material>();
  const mat = (colour: string, glow: boolean, dim: boolean) => {
    const k = `${colour}|${glow}|${dim}`;
    if (!mats.has(k)) mats.set(k, new THREE.MeshLambertMaterial({ color: colour, flatShading: true, emissive: glow ? new THREE.Color("#ffb347") : new THREE.Color(0), emissiveIntensity: glow ? 0.55 : 0, transparent: dim, opacity: dim ? 0.28 : 1, depthWrite: !dim, side: THREE.DoubleSide }));
    return mats.get(k)!;
  };

  for (const p of m.panels) {
    const off: V3 = [p.normal[0] * view.explode, p.normal[1] * view.explode, p.normal[2] * view.explode];
    const shift = (q: V3): V3 => [q[0] + off[0], q[1] + off[1], q[2] + off[2]];
    for (const st of p.sticks) {
      const [tails, heads] = st.ends;
      const n = tails.length;
      const pos: number[] = [];
      const tri = (a: V3, b: V3, c: V3) => { for (const q of [a, b, c]) { const v = at(shift(q)); pos.push(v.x, v.y, v.z); } };
      for (let i = 1; i < n - 1; i++) { tri(tails[0], tails[i + 1], tails[i]); tri(heads[0], heads[i], heads[i + 1]); }
      for (let i = 0; i < n; i++) { const j = (i + 1) % n; tri(tails[i], tails[j], heads[j]); tri(tails[i], heads[j], heads[i]); }
      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
      geo.computeVertexNormals();
      const t = typeOf.get(st);
      const chosen = view.selected !== null && t?.name === view.selected;
      const mesh = new THREE.Mesh(geo, mat(ROW_WOOD[(st.row - 1) % ROW_WOOD.length], chosen, view.selected !== null && !chosen));
      mesh.castShadow = true;
      if (t) mesh.userData.part = {
        id: `zome:${t.name}`, name: `stick ${t.name}`,
        examine: `Stick ${t.name}, row ${t.row}: ${t.count} like it, ${t.outer.toFixed(2)} in along the outside edge. Tail: mitre ${Math.abs(t.tail[0]).toFixed(1)}°, bevel ${Math.abs(t.tail[1]).toFixed(1)}°. Head: mitre ${Math.abs(t.head[0]).toFixed(1)}°, bevel ${Math.abs(t.head[1]).toFixed(1)}°.`,
      };
      g.add(mesh);
    }
    if (view.skin) {
      const c = p.corners.map((k) => m.vertices[k]);
      const lift = 0.25;
      const out = c.map((q) => shift([q[0] + p.normal[0] * lift, q[1] + p.normal[1] * lift, q[2] + p.normal[2] * lift]));
      const pos: number[] = [];
      for (const q of [out[0], out[1], out[2], out[0], out[2], out[3]]) { const v = at(q); pos.push(v.x, v.y, v.z); }
      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
      geo.computeVertexNormals();
      g.add(new THREE.Mesh(geo, new THREE.MeshLambertMaterial({ color: "#e8f0f2", transparent: true, opacity: 0.42, side: THREE.DoubleSide, depthWrite: false })));
    }
  }

  if (view.posts && m.posts.length) {
    const low = Math.min(...m.rim.map((i) => m.vertices[i][2]));
    const side = m.postSquare * s;
    const post = new THREE.MeshLambertMaterial({ color: "#6a4a2e", flatShading: true });
    for (const [i, h] of m.posts) {
      const v = m.vertices[i];
      const b = new THREE.Mesh(new THREE.BoxGeometry(side, h * s, side), post);
      const c = at([v[0], v[1], low + h / 2]);
      b.position.copy(c);
      b.userData.part = { id: `post:${i}`, name: "rim post", examine: `A rim post ${h.toFixed(1)} in tall under a high corner of the rim: two quarters back to back, ${m.postSquare.toFixed(2)} in square.` };
      g.add(b);
    }
  }
  // stand the rim's lowest corners on the stage
  const lowest = Math.min(...m.rim.map((i) => m.vertices[i][2]));
  g.position.y = -lowest * s + 0.05;
  return g;
}
