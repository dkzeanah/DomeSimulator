// The wedge zome, solved in the browser. The zonohedron and the wedge's cross-section come from
// the desktop tool (scripts/portal_tools_export.py -> generated/zome.json); this file is
// wedge_zome.geometry.build(), stick_types(), rows(), blocks(), stock() and
// fabrication.facts(), line for line, and scripts/test_portal_tools.mjs checks it against
// facts() itself.

import data from "../generated/zome.json";

export const Z = data;
export type V3 = [number, number, number];
export type Method = "wedge" | "square";
export interface ZomeConfig { method: Method; log: number; side: number; hand: "ccw" | "cw"; orient: "back" | "point" }
export const ZOME_DEFAULTS: ZomeConfig = { ...(Z.defaults as ZomeConfig) };

const sub = (a: V3, b: V3): V3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const add = (a: V3, b: V3): V3 => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const mul = (a: V3, k: number): V3 => [a[0] * k, a[1] * k, a[2] * k];
const dot = (a: V3, b: V3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a: V3, b: V3): V3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = (a: V3) => Math.hypot(a[0], a[1], a[2]);
const unit = (a: V3): V3 => { const n = norm(a); return n > 1e-12 ? mul(a, 1 / n) : a; };
const clip = (x: number) => Math.max(-1, Math.min(1, x));
const deg = (r: number) => (r * 180) / Math.PI;
const rad = (d: number) => (d * Math.PI) / 180;
const mean = (ps: V3[]): V3 => mul(ps.reduce((s, p) => add(s, p), [0, 0, 0] as V3), 1 / ps.length);
/** Python's round(x, n), for grouping keys. */
const roundTo = (x: number, n: number) => Number(x.toFixed(n));

interface Plane { point: V3; normal: V3 }
const hit = (pl: Plane, origin: V3, d: V3) => dot(pl.normal, sub(pl.point, origin)) / dot(pl.normal, d);

export interface Stick {
  panel: number; side: number; row: number;
  origin: V3; d: V3; v: V3; n: V3;
  section: [number, number][];
  tail: Plane; head: Plane;
  ends: [V3[], V3[]];
  edge: [number, number];
}
const point = (s: Pick<Stick, "origin" | "v" | "n" | "d">, p: [number, number], t: number): V3 =>
  add(add(add(s.origin, mul(s.v, p[0])), mul(s.n, p[1])), mul(s.d, t));
const lengths = (s: Stick) => s.ends[0].map((t, i) => norm(sub(s.ends[1][i], t)));
/** (mitre, bevel) for an end: the stick back-down on the saw table, the edge it runs along on the fence. */
function cut(s: Stick, pl: Plane): [number, number] {
  let p = unit(pl.normal);
  if (dot(p, s.d) < 0) p = mul(p, -1);
  return [deg(Math.atan2(dot(p, s.v), dot(p, s.d))), deg(Math.asin(clip(dot(p, s.n))))];
}

export interface Panel { index: number; row: number; corners: number[]; normal: V3; acute: number; sticks: Stick[] }
export interface Seam { a: number; b: number; panels: [number, number]; rowPair: [number, number]; fold: number; gap: number; gapSide: "inside" | "outside"; length: number }
export interface ZomeModel {
  config: ZomeConfig; vertices: V3[]; panels: Panel[]; seams: Seam[]; rows: number[];
  theta: number; stickW: number; stickH: number; rim: number[]; posts: [number, number][]; postSquare: number;
}

const logRow = (log: number) => {
  const r = Z.logs.find((l) => Math.abs(l.log - log) < 1e-9);
  if (!r) throw new Error(`no wedge table for a ${log} in log`);
  return r;
};

function section(method: Method, log: number, orient: "back" | "point"): [[number, number][], number, number] {
  const w = logRow(log);
  if (method === "wedge") {
    const c = w.chordEff, h = w.rEff * Math.cos(rad(w.theta / 2));
    if (orient === "point") return [[[0, -h], [c, -h], [c / 2, 0]], c, h];
    return [[[0, 0], [c, 0], [c / 2, -h]], c, h];
  }
  const s = w.square;
  return [[[0, 0], [s, 0], [s, s], [0, s]], s, s];
}

const cache = new Map<string, ZomeModel>();

export function build(c: ZomeConfig): ZomeModel {
  const key = JSON.stringify(c);
  const hitCache = cache.get(key);
  if (hitCache) return hitCache;
  const verts = (Z.vertices as V3[]).map((v) => mul(v, c.side));
  const faces = Z.faces as number[][];
  const centre = mean(verts);
  const [sec, w, h] = section(c.method, c.log, c.orient);

  const cz = faces.map((f) => roundTo(f.reduce((s, k) => s + verts[k][2], 0) / f.length, 4));
  const levels = [...new Set(cz)].sort((a, b) => b - a);
  const panels: Panel[] = faces.map((f0, i) => {
    let f = [...f0];
    let pts = f.map((k) => verts[k]);
    let nrm = unit(cross(sub(pts[1], pts[0]), sub(pts[2], pts[0])));
    if (dot(nrm, sub(mean(pts), centre)) < 0) { f = f.reverse(); pts = pts.reverse(); nrm = mul(nrm, -1); }
    const ang = deg(Math.acos(clip(dot(unit(sub(pts[1], pts[0])), unit(sub(pts[3], pts[0]))))));
    return { index: i, row: levels.indexOf(cz[i]) + 1, corners: f, normal: nrm, acute: Math.min(ang, 180 - ang), sticks: [] };
  });

  for (const p of panels) {
    const ids = c.hand === "ccw" ? [...p.corners] : [...p.corners].reverse();
    const pts = ids.map((k) => verts[k]);
    const mid = mean(pts);
    for (let k = 0; k < 4; k++) {
      const a = pts[k], b = pts[(k + 1) % 4], d = unit(sub(b, a));
      let v = unit(cross(p.normal, d));
      if (dot(v, sub(mid, a)) < 0) v = mul(v, -1);
      p.sticks.push({ panel: p.index, side: k, row: p.row, origin: a, d, v, n: p.normal, section: sec,
        tail: null as unknown as Plane, head: null as unknown as Plane, ends: [[], []], edge: [ids[k], ids[(k + 1) % 4]] });
    }
    p.sticks.forEach((s, k) => {
      const nxt = p.sticks[(k + 1) % 4], prv = p.sticks[(k + 3) % 4];
      if (c.method === "wedge") {
        const o = point(nxt, sec[0], 0), a_ = point(nxt, sec[2], 0);
        s.head = { point: o, normal: unit(cross(nxt.d, sub(a_, o))) };
        const i_ = point(prv, sec[1], 0), a2 = point(prv, sec[2], 0);
        s.tail = { point: i_, normal: unit(cross(prv.d, sub(a2, i_))) };
      } else {
        s.head = { point: nxt.origin, normal: nxt.v };
        s.tail = { point: point(prv, sec[1], 0), normal: prv.v };
      }
      const tails: V3[] = [], heads: V3[] = [];
      for (const q of s.section) {
        const base = point(s, q, 0);
        tails.push(add(base, mul(s.d, hit(s.tail, base, s.d))));
        heads.push(add(base, mul(s.d, hit(s.head, base, s.d))));
      }
      s.ends = [tails, heads];
    });
  }

  // the seams: every edge two panels share
  const owners = new Map<string, Panel[]>();
  for (const p of panels) for (let k = 0; k < 4; k++) {
    const a = p.corners[k], b = p.corners[(k + 1) % 4];
    const key2 = `${Math.min(a, b)},${Math.max(a, b)}`;
    owners.set(key2, [...(owners.get(key2) || []), p]);
  }
  const stickOn = (p: Panel, a: number, b: number) => p.sticks.find((s) => (s.edge[0] === a && s.edge[1] === b) || (s.edge[0] === b && s.edge[1] === a))!;
  const faceNormal = (s: Stick) => { const o = point(s, s.section[0], 0), ap = point(s, s.section[2], 0); return unit(cross(s.d, sub(ap, o))); };
  const seams: Seam[] = [];
  for (const [k2, own] of owners) {
    if (own.length !== 2) continue;
    const [a, b] = k2.split(",").map(Number);
    const [pa, pb] = own;
    const fold = deg(Math.acos(clip(dot(pa.normal, pb.normal))));
    let gap = fold, side: "inside" | "outside" = "outside";
    if (c.method === "wedge") {
      gap = deg(Math.acos(clip(Math.abs(dot(faceNormal(stickOn(pa, a, b)), faceNormal(stickOn(pb, a, b)))))));
      side = c.orient === "back" ? "inside" : "outside";
    }
    seams.push({ a, b, panels: [pa.index, pb.index], rowPair: [Math.min(pa.row, pb.row), Math.max(pa.row, pb.row)],
      fold, gap, gapSide: side, length: norm(sub(verts[a], verts[b])) });
  }

  // the rim: the edges only one panel has, round the ring; posts under the corners above the lowest
  const counts = new Map<string, number>();
  for (const f of faces) for (let k = 0; k < 4; k++) {
    const a = f[k], b = f[(k + 1) % 4], key2 = `${Math.min(a, b)},${Math.max(a, b)}`;
    counts.set(key2, (counts.get(key2) || 0) + 1);
  }
  const rimSet = new Set<number>();
  for (const [k2, n] of counts) if (n === 1) for (const i of k2.split(",").map(Number)) rimSet.add(i);
  const rim = [...rimSet].sort((i, j) => Math.atan2(verts[i][1], verts[i][0]) - Math.atan2(verts[j][1], verts[j][0]));
  const low = Math.min(...rim.map((i) => verts[i][2]));
  const posts = rim.filter((i) => verts[i][2] - low > 1e-6).map((i) => [i, verts[i][2] - low] as [number, number]);

  const m: ZomeModel = { config: c, vertices: verts, panels, seams, rows: [...new Set(panels.map((p) => p.row))].sort((x, y) => x - y),
    theta: logRow(c.log).theta, stickW: w, stickH: h, rim, posts, postSquare: logRow(c.log).postSquare };
  cache.set(key, m);
  return m;
}

export const sticks = (m: ZomeModel) => m.panels.flatMap((p) => p.sticks);

export interface StickType { name: string; row: number; count: number; outer: number; lengths: number[]; tail: [number, number]; head: [number, number]; longest: number; members: Stick[] }

export function stickTypes(m: ZomeModel): StickType[] {
  const groups = new Map<string, StickType>();
  for (const s of sticks(m)) {
    const lens = lengths(s), t = cut(s, s.tail), h = cut(s, s.head);
    const key = [s.row, roundTo(lens[0], 2), roundTo(t[0], 1), roundTo(t[1], 1), roundTo(h[0], 1), roundTo(h[1], 1)].join("|");
    let g = groups.get(key);
    if (!g) { g = { name: "", row: s.row, count: 0, outer: lens[0], lengths: lens, tail: t, head: h, longest: Math.max(...lens), members: [] }; groups.set(key, g); }
    g.count++;
    g.members.push(s);
  }
  const out = [...groups.values()].sort((a, b) => a.row - b.row || b.count - a.count);
  const per = new Map<number, number>();
  for (const g of out) { const k = per.get(g.row) || 0; g.name = `R${g.row}${"ABCDEFGHIJKLMNOP"[k]}`; per.set(g.row, k + 1); }
  return out;
}

export function rows(m: ZomeModel) {
  return m.rows.map((r) => {
    const ps = m.panels.filter((p) => p.row === r), ss = m.seams.filter((s) => s.rowPair.includes(r));
    return { row: r, panels: ps.length, acute: ps[0].acute, fold_max: Math.max(...ss.map((s) => s.fold)),
      gap_min: Math.min(...ss.map((s) => s.gap)), gap_max: Math.max(...ss.map((s) => s.gap)) };
  });
}

/** Python's round(): to the nearest whole number, halves to even. */
const pyRound = (x: number) => { const f = Math.floor(x); const d = x - f; return d === 0.5 ? (f % 2 === 0 ? f : f + 1) : Math.round(x); };

/** Square method only: the wedge block each seam's outside V needs, and the log split that makes it. */
export function blocks(m: ZomeModel) {
  const out = new Map<number, { fold: number; count: number; length: number; split_exact: number; split: number; split_error: number }>();
  for (const s of m.seams) {
    const k = roundTo(s.fold, 1);
    let g = out.get(k);
    if (!g) { g = { fold: s.fold, count: 0, length: s.length, split_exact: 360 / s.fold, split: pyRound(360 / s.fold), split_error: 0 }; out.set(k, g); }
    g.count++;
  }
  for (const g of out.values()) g.split_error = 360 / g.split - g.fold;
  return [...out.values()].sort((a, b) => a.fold - b.fold);
}

export function stock(m: ZomeModel) {
  const types = stickTypes(m);
  const n = types.reduce((s, g) => s + g.count, 0);
  const longest = Math.max(...types.map((g) => g.longest));
  const each = Math.floor((Z.section + Z.kerf) / (longest + Z.kerf));
  let wedges = Math.ceil(n / each);
  if (m.config.method === "square") wedges *= 2;           // two wedges paired for every square stick
  return { sticks: n, sticks_per_wedge: each, wedges, sections: Math.ceil(wedges / Z.splits), longest };
}

/** fabrication.facts(): every figure the space shows. */
export function facts(c: ZomeConfig) {
  const m = build(c);
  const other = build({ ...c, method: c.method === "wedge" ? "square" : "wedge", orient: "back" });
  const gaps = m.seams.map((s) => s.gap), folds = m.seams.map((s) => s.fold);
  const p0 = m.panels[0];
  return {
    model: m, method: c.method, panels: m.panels.length, rows: rows(m), types: stickTypes(m), stock: stock(m), other_stock: stock(other),
    seams: m.seams.length, gap_lo: Math.min(...gaps), gap_hi: Math.max(...gaps), fold_lo: Math.min(...folds), fold_hi: Math.max(...folds),
    posts: m.posts.length, post_h: m.posts.length ? Math.max(...m.posts.map((p) => p[1])) : 0, rim_corners: m.rim.length,
    stick_w: m.stickW, stick_h: m.stickH, theta: m.theta, side: norm(sub(m.vertices[p0.corners[1]], m.vertices[p0.corners[0]])),
    height_ft: Math.max(...m.vertices.map((v) => v[2])) / 12, rim_ft: (2 * Math.max(...m.vertices.map((v) => Math.hypot(v[0], v[1])))) / 12,
    blocks: blocks(build({ ...c, method: "square", orient: "back" })), post_square: m.postSquare,
  };
}
