// Wedge Island's scenery: the sea round it, the beach, the paths between the stations, the pines
// to fell, the splitting block, the saw bench, the simulator's own jig on its bench, and the dome
// site where the simulator's own dome goes up panel by panel, keyed and sheathed. What each
// station shows follows the lesson (game/island.ts). Feet, y up.

import * as THREE from "three";
import mesh from "../generated/dome-mesh.json";
import { sign } from "./estates";
import { W, loadMesh, type MeshHead } from "./wedge";
import { drawDome, drawJig } from "./wedgeView";
import type { Obstacle } from "./engine";

export const SKY: [string, string] = ["#2a5a8a", "#f0c890"];
export const GROUND = "#5a7a34";

export const AT = {
  spawn: [0, 74] as [number, number],
  gale: [7, 64] as [number, number],
  finn: [-44, 34] as [number, number],
  trees: [[-60, 24], [-70, 38], [-56, 46], [-74, 18]] as [number, number][],
  sage: [-38, -10] as [number, number],
  block: [-48, -20] as [number, number],
  sol: [-2, -38] as [number, number],
  saw: [-12, -48] as [number, number],
  jo: [22, -32] as [number, number],
  jig: [36, -48] as [number, number],
  bo: [30, 22] as [number, number],
  site: [52, 10] as [number, number],
  galeEnd: [12, 40] as [number, number],
  exit: [20, 50] as [number, number],
};

const lambert = (c: string) => new THREE.MeshLambertMaterial({ color: c, flatShading: true });
const shadowed = <O extends THREE.Object3D>(o: O) => { o.traverse((m) => { if ((m as THREE.Mesh).isMesh) { (m as THREE.Mesh).castShadow = true; (m as THREE.Mesh).receiveShadow = true; } }); return o; };

/** A pine you can fell: its trunk and tiers stand on a pivot at its foot. */
export function pineMesh() {
  const g = new THREE.Group();
  const tree = new THREE.Group();
  tree.name = "standing";
  const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.7, 26, 8), lambert("#6a4a2e")); trunk.position.y = 13; tree.add(trunk);
  for (let i = 0; i < 4; i++) { const c = new THREE.Mesh(new THREE.ConeGeometry(5 - i * 1, 7, 8), lambert("#2c5a2a")); c.position.y = 12 + i * 4.2; tree.add(c); }
  g.add(tree);
  const stump = new THREE.Mesh(new THREE.CylinderGeometry(0.75, 0.85, 1, 10), lambert("#8a6a44")); stump.position.y = 0.5; stump.name = "stump"; stump.visible = false; g.add(stump);
  // bucked: the trunk on the ground in sections
  const logs = new THREE.Group(); logs.name = "bucked"; logs.visible = false;
  for (let i = 0; i < 4; i++) { const l = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.6, 5.6, 10), lambert(i % 2 ? "#7a5a3a" : "#6a4a2e")); l.rotation.z = Math.PI / 2; l.position.set(2 + i * 6.2, 0.6, 0); logs.add(l); }
  g.add(logs);
  return shadowed(g);
}

/** Felling: the standing tree tips over by f (0 standing, 1 on the ground). */
export function fell(g: THREE.Object3D, f: number) {
  const t = g.getObjectByName("standing");
  if (t) t.rotation.z = -Math.min(1, f) * (Math.PI / 2 - 0.05);
  const s = g.getObjectByName("stump");
  if (s) s.visible = f > 0;
}
export function buck(g: THREE.Object3D) {
  const t = g.getObjectByName("standing"), b = g.getObjectByName("bucked");
  if (t) t.visible = false;
  if (b) b.visible = true;
}

export interface IslandScene {
  group: THREE.Group; obstacles: Obstacle[]; tick: (t: number, dt: number) => void; sky: [string, string]; ground: string;
  /** The section on the block, split this many times (0 whole, 3 eighths); -1 for none. */
  setSplit(k: number): void;
  /** Struts on the rack by the saw. */
  setStruts(a: number, b: number): void;
  /** The jig at one of its stages. */
  setJig(stage: number): void;
  /** The dome: panels raised, seams keyed, triangles sheathed. */
  setDome(panels: number, keys: number, skin: number): void;
  ready: Promise<void>;
  counts: { panels: number; keys: number };
}

export function buildIsland(): IslandScene {
  const g = new THREE.Group();
  // the sea, and the beach where the land meets it
  const sea = new THREE.Mesh(new THREE.CircleGeometry(900, 64), new THREE.MeshStandardMaterial({ color: "#2a6a9a", metalness: 0.3, roughness: 0.25 }));
  sea.rotation.x = -Math.PI / 2; sea.position.y = -1.2; g.add(sea);
  const beach = new THREE.Mesh(new THREE.RingGeometry(112, 134, 64), lambert("#d9c89a")); beach.rotation.x = -Math.PI / 2; beach.position.y = 0.03; g.add(beach);
  // the path round the stations, in the order the lesson walks it
  const route: [number, number][] = [AT.spawn, AT.gale, [-20, 50], AT.finn, [-46, 10], AT.sage, [-28, -36], AT.sol, [10, -42], AT.jo, [40, -14], AT.bo, AT.galeEnd, AT.exit];
  for (let i = 0; i < route.length - 1; i++) {
    const [ax, az] = route[i], [bx, bz] = route[i + 1], len = Math.hypot(bx - ax, bz - az);
    const p = new THREE.Mesh(new THREE.PlaneGeometry(4.5, len + 4.5), lambert("#a88c62"));
    p.rotation.x = -Math.PI / 2; p.rotation.z = -Math.atan2(bx - ax, bz - az); p.position.set((ax + bx) / 2, 0.04, (az + bz) / 2); p.receiveShadow = true; g.add(p);
  }
  // a stand of pines behind the felling trees
  const back: [number, number][] = [[-82, 30], [-86, 48], [-78, 58], [-90, 12], [-66, 60], [-94, 34], [-84, 0]];
  for (const [x, z] of back) { const t = pineMesh(); t.position.set(x, 0, z); t.scale.setScalar(0.9 + ((x * 7 + z) % 5) * 0.05); g.add(t); }
  // signs at each station
  const signs: [string, string, [number, number]][] = [
    ["Wedge Island", "from trees to a dome", [-8, 80]], ["The Forest", "fell and buck", [-36, 44]], ["The Block", "split eight ways", [-32, -22]],
    ["The Saw", "two lengths", [6, -50]], ["The Jig", "one triangle", [20, -50]], ["The Site", "raise, key, sheathe", [34, 34]],
  ];
  for (const [title, sub, [x, z]] of signs) { const s = sign(title, sub); s.scale.setScalar(0.55); s.position.set(x, 0, z); s.rotation.y = Math.atan2(-x, -z) + Math.PI; g.add(s); }

  // the splitting block and the section on it
  const block = new THREE.Group();
  const stump = new THREE.Mesh(new THREE.CylinderGeometry(1.6, 1.8, 2.2, 12), lambert("#8a6a44")); stump.position.y = 1.1; block.add(stump);
  const section = new THREE.Group(); section.position.y = 2.2; block.add(section);
  const sectors: THREE.Mesh[] = [];
  const wood = lambert("#d9b07a"), bark = lambert("#5a3a22");
  for (let i = 0; i < 8; i++) {
    const m = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 6, 3, 1, false, (i / 8) * Math.PI * 2, Math.PI / 4), [bark, wood, wood]);
    m.rotation.z = Math.PI / 2; m.position.y = 0.55; section.add(m); sectors.push(m);
  }
  block.position.set(AT.block[0], 0, AT.block[1]); g.add(shadowed(block));

  // the saw bench and its rack
  const saw = new THREE.Group();
  const table = new THREE.Mesh(new THREE.BoxGeometry(10, 0.4, 2.6), lambert("#8a6440")); table.position.y = 3; saw.add(table);
  for (const x of [-4.5, 4.5]) for (const z of [-1, 1]) { const leg = new THREE.Mesh(new THREE.BoxGeometry(0.3, 3, 0.3), lambert("#5a4430")); leg.position.set(x, 1.5, z); saw.add(leg); }
  const blade = new THREE.Mesh(new THREE.CylinderGeometry(0.9, 0.9, 0.1, 24), new THREE.MeshStandardMaterial({ color: "#c8ccd2", metalness: 0.9, roughness: 0.3 }));
  blade.rotation.x = Math.PI / 2; blade.position.set(0, 4, 0); saw.add(blade);
  const arm = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.4, 2.4), lambert("#c84a2a")); arm.position.set(0, 4.8, 0); saw.add(arm);
  const rack = new THREE.Group(); rack.position.set(0, 0, 3.4); saw.add(rack);
  saw.position.set(AT.saw[0], 0, AT.saw[1]); g.add(shadowed(saw));

  // the jig's bench and the dome site
  const jigSpot = new THREE.Group(); jigSpot.position.set(AT.jig[0], 0, AT.jig[1]); jigSpot.rotation.y = -0.6; g.add(jigSpot);
  const site = new THREE.Group(); site.position.set(AT.site[0], 0, AT.site[1]); g.add(site);
  const deck = new THREE.Mesh(new THREE.CylinderGeometry(mesh.radiusFt * 1.12, mesh.radiusFt * 1.12, 1.2, 10), lambert("#8a6440")); deck.position.y = 0.6; site.add(shadowed(deck));
  const domeAt = new THREE.Group(); domeAt.position.y = 1.2; site.add(domeAt);
  const skin = new THREE.Group(); domeAt.add(skin);
  // the sheathing: the solver's 40 triangles, just outside the frame
  const v = (mesh.vertices as number[][]).map(([x, y, z]) => new THREE.Vector3(x, z, -y).multiplyScalar(1.035));
  const order = (mesh.faces as [number, number, number, string][]).map((f, i) => ({ f, i, h: (v[f[0]].y + v[f[1]].y + v[f[2]].y) / 3 })).sort((a, b) => a.h - b.h);
  const skins = order.map(({ f }) => {
    const geo = new THREE.BufferGeometry().setFromPoints([v[f[0]], v[f[1]], v[f[2]]]);
    geo.computeVertexNormals();
    const m = new THREE.Mesh(geo, new THREE.MeshLambertMaterial({ color: "#c9a26c", side: THREE.DoubleSide, flatShading: true }));
    m.visible = false; skin.add(m); return m;
  });
  const faceRank = new Map<number, number>(order.map((o, k) => [o.i, k]));

  // what is loaded from the simulator: its dome and its jig
  let domeParts: { mesh: THREE.Object3D; rank: number; key: boolean; k: number }[] = [];
  let jig: { head: typeof W.jig; buf: Awaited<ReturnType<typeof loadMesh>> } | null = null;
  const head = (W.meshes as Record<string, MeshHead>).point_dome_in;
  const counts = { panels: mesh.faces.length, keys: head.parts.filter((p) => p.kind === "key").length };
  let want = { split: -1, a: 0, b: 0, jig: 0, panels: 0, keys: 0, skin: 0 };

  const ready = Promise.all([loadMesh(head), loadMesh(W.jig)]).then(([db, jb]) => {
    const { group, scale } = drawDome(head, db, { explode: 0, keys: true, offcuts: false, family: null, picked: null });
    group.scale.setScalar(1 / scale);                 // the island's dome is full size
    group.position.y = -0.05;
    domeAt.add(group);
    const faceOf = new Map(head.parts.map((p) => [p.id, p]));
    group.traverse((o) => {
      const part = o.userData.part as { id: string } | undefined;
      if (!part) return;
      const [kind, id] = [part.id.split(":")[0], part.id.slice(part.id.indexOf(":") + 1)];
      const p = faceOf.get(id) as { face?: number; faces?: number[] } | undefined;
      if (!p) return;
      const rank = kind === "wedge" ? faceRank.get(p.face ?? 0) ?? 0 : Math.max(...(p.faces ?? [0]).map((f) => faceRank.get(f) ?? 0));
      delete o.userData.part;                         // on the island the dome is the site's, not a picker's
      domeParts.push({ mesh: o, rank, key: kind === "key", k: 0 });
    });
    domeParts = domeParts.sort((x, y) => x.rank - y.rank);
    domeParts.filter((p) => p.key).forEach((p, i) => { p.k = i; });     // keys go in from the bottom up
    jig = { head: W.jig, buf: jb };
    api.setDome(want.panels, want.keys, want.skin);
    api.setJig(want.jig);
  });

  const api: IslandScene = {
    group: g, sky: SKY, ground: GROUND, ready, counts,
    obstacles: [{ x: AT.site[0], z: AT.site[1], r: mesh.radiusFt * 1.12 + 1.5 }, { x: AT.jig[0], z: AT.jig[1], r: 8 }, { x: AT.saw[0], z: AT.saw[1], r: 5 }, { x: AT.block[0], z: AT.block[1], r: 2.4 }],
    tick: (t) => { blade.rotation.y = t * 10; },
    setSplit(k) {
      want.split = k;
      section.visible = k >= 0;
      const groups = 2 ** Math.max(0, k);
      sectors.forEach((m, i) => {
        const gi = Math.floor(i / (8 / groups)), a = ((gi + 0.5) / groups) * Math.PI * 2;
        const gap = k > 0 ? 0.35 * k : 0;
        // the sector's own direction across the log's end, opened out from the centre
        m.position.set(0, 0.55 + Math.sin(a) * gap, Math.cos(a) * gap);
      });
    },
    setStruts(a, b) {
      want.a = a; want.b = b;
      rack.clear();
      for (let i = 0; i < a + b; i++) {
        const len = i < a ? 6 : 5.3;
        const s = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.35, len, 3), lambert(i < a ? "#d9a868" : "#c8914e"));
        s.rotation.z = Math.PI / 2; s.position.set(0, 0.5 + i * 0.75, 0); rack.add(s);
      }
    },
    setJig(stage) {
      want.jig = stage;
      if (!jig) return;
      jigSpot.clear();
      const j = drawJig(jig.head, jig.buf, stage);
      j.scale.setScalar(0.75);
      j.traverse((o) => delete o.userData.part);
      jigSpot.add(j);
    },
    setDome(panels, keys, skinN) {
      want = { ...want, panels, keys, skin: skinN };
      for (const p of domeParts) p.mesh.visible = p.key ? p.k < keys : p.rank < panels;
      skins.forEach((m, k) => { m.visible = k < skinN; });
    },
  };
  api.setSplit(-1);
  return api;
}
