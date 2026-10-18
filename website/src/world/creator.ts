// The Dome Creator's sums, in the browser. Every table comes from the desktop tool
// (scripts/creator_export.py -> generated/creator.json); this file does only the arithmetic of
// dome_model.DomeModel.rebuild() and .stats() for a dome without fit-out, line for line, and
// scripts/test_creator.mjs checks it against stats() itself on 160 designs.

import data from "../generated/creator.json";

export type CreatorData = typeof data;
export const T: CreatorData = data;

export interface Config {
  frequency: number; radius: number; frameStyle: string; hubStyle: string; strutShape: string;
  strutWidth: number; frameMaterial: string; panel: string; foundation: string; foundationScale: number;
}

export interface StrutClass { name: string; length: number; count: number }
export interface Design {
  config: Config;
  height: number; floorArea: number; surfaceArea: number;
  struts: [number[], number[]][];          // endpoints, sphere centre at the origin, z up, metres
  panels: number[][][];                   // triangles, same frame
  strutClasses: StrutClass[]; strutCount: number; strutTotalLen: number;
  hubCount: number; boltCount: number; panelCount: number; treesRequired: number;
  frameWeight: number; frameCost: number; hubWeight: number; hubCost: number;
  panelWeight: number; panelCost: number; solarWatts: number;
  foundationArea: number; foundationWeight: number; foundationCost: number;
  structureWeight: number; totalCost: number;
  baseZ: number; note: string | null;
}

export const DEFAULTS: Config = { ...T.defaults };

const byName = <X extends { name: string }>(xs: X[], name: string) => xs.find((x) => x.name === name) ?? xs[0];

/** Python's round(x, 2): to nearest, ties to even, on the decimal that float actually holds. */
function round2(x: number) {
  const s = x * 100;
  const f = Math.floor(s), d = s - f;
  if (Math.abs(d - 0.5) < 1e-9) return (f % 2 === 0 ? f : f + 1) / 100;
  return Math.round(s) / 100;
}

const sub = (a: number[], b: number[]) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const len = (a: number[]) => Math.hypot(a[0], a[1], a[2]);
const scale = (a: number[], k: number) => [a[0] * k, a[1] * k, a[2] * k];
const add = (a: number[], b: number[]) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const triArea = (a: number[], b: number[], c: number[]) => {
  const u = sub(b, a), v = sub(c, a);
  return 0.5 * len([u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]);
};

export function design(c: Config): Design {
  const geo = T.geometry.find((g) => g.frequency === c.frequency) ?? T.geometry[0];
  const r = c.radius;
  const verts = geo.vertices.map((v) => scale(v, r));

  // DomeModel.rebuild: Hubless Doubled is every triangle its own frame, pulled toward its
  // centroid so neighbours run side by side, bolted twice along each shared edge; every other
  // style is a strut per edge with a hub at every node.
  const struts: [number[], number[]][] = [];
  let hubCount = 0, boltCount = 0;
  if (c.frameStyle === "Hubless Doubled") {
    const inset = c.strutWidth * T.hublessInset;
    for (const f of geo.faces) {
      const tri = f.map((i) => verts[i]);
      const cen = scale(add(add(tri[0], tri[1]), tri[2]), 1 / 3);
      const pulled = tri.map((v) => {
        const toC = sub(cen, v), d = len(toC);
        return add(v, scale(toC, Math.min(inset, d * T.hublessInsetCap) / d));
      });
      for (let i = 0; i < 3; i++) struts.push([pulled[i], pulled[(i + 1) % 3]]);
    }
    boltCount = geo.edges.length * 2;
  } else {
    for (const [a, b] of geo.edges) struts.push([verts[a], verts[b]]);
    hubCount = verts.length;
  }
  const panels = geo.faces.map((f) => f.map((i) => verts[i]));

  // DomeModel.stats
  const groups = new Map<number, number>();
  let totalLen = 0;
  for (const [p, q] of struts) {
    const l = len(sub(q, p));
    const key = round2(l);
    groups.set(key, (groups.get(key) || 0) + 1);
    totalLen += l;
  }
  const strutClasses = [...groups.entries()].sort((x, y) => y[0] - x[0])
    .map(([length, count], i) => ({ name: String.fromCharCode(65 + (i % 26)), length, count }));

  const shape = byName(T.strutShapes, c.strutShape);
  const mat = byName(T.frameMaterials, c.frameMaterial);
  const k = T.constants;
  const cs = (shape.section as Record<string, number>)[c.strutWidth.toFixed(4)];
  if (cs === undefined) throw new Error(`no cross section for ${shape.name} at ${c.strutWidth} m`);
  const frameWeight = totalLen * cs * mat.density;
  const frameCost = frameWeight * mat.costPerKg * k.frameCostFactor;

  let hubScale = Math.pow(c.strutWidth / k.hubReferenceWidth, k.hubScalePower);
  let hubCostScale = hubScale;
  if (c.hubStyle === "Metal Brackets") { hubScale *= k.bracketWeightFactor; hubCostScale = hubScale * k.bracketCostFactor; }
  const hubWeight = hubCount * mat.hubWeight * hubScale + boltCount * k.boltWeight;
  const hubCost = hubCount * mat.hubCost * hubCostScale + boltCount * k.boltCost;

  const treesRequired = shape.kind === "wedge" ? Math.ceil(struts.length / k.wedgesPerTree) : 0;

  const pt = byName(T.panels, c.panel);
  let surface = 0;
  for (const t of panels) surface += triArea(t[0], t[1], t[2]);
  const panelWeight = surface * pt.areaWeight, panelCost = surface * pt.costPerM2, solarWatts = surface * pt.wattsPerM2;

  const fd = byName(T.foundations, c.foundation);
  const fr = r * c.foundationScale;
  let fArea = fd.height > 0 ? Math.PI * fr * fr : 0;
  if (fd.name === "Bare Ground") fArea = 0;

  const ring = Math.sqrt(Math.max(0, 1 - geo.baseZ * geo.baseZ));
  const structureWeight = frameWeight + hubWeight + panelWeight;
  const totalCost = frameCost + hubCost + panelCost + fArea * fd.costPerM2;
  return {
    config: c, height: (1 - geo.baseZ) * r, floorArea: Math.PI * (ring * r) ** 2, surfaceArea: surface,
    struts, panels, strutClasses, strutCount: struts.length, strutTotalLen: totalLen,
    hubCount, boltCount, panelCount: panels.length, treesRequired,
    frameWeight, frameCost, hubWeight, hubCost, panelWeight, panelCost, solarWatts,
    foundationArea: fArea, foundationWeight: fArea * fd.weightPerM2, foundationCost: fArea * fd.costPerM2,
    structureWeight, totalCost, baseZ: geo.baseZ,
    note: (T.notes as Record<string, string>)[c.frameStyle] ?? null,
  };
}
