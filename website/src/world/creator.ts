// The Dome Creator's sums, in the browser. Every table comes from the desktop tool
// (scripts/creator_export.py -> generated/creator.json); this file does only the arithmetic of
// dome_model.DomeModel.rebuild() and .stats(), line for line -- the frame, hubs and bolts, every
// panel with its own type (the Panel Lab's custom panels too), the cladding layers, the
// foundation, the workshop fit-out (rooms, partitions, props, wiring, plumbing), trunk stock and
// the wedges -- and scripts/test_creator.mjs checks it against stats() itself on 240 designs.

import data from "../generated/creator.json";

export type CreatorData = typeof data;
export const T: CreatorData = data;

export interface Prop { type: string; x: number; y: number; yaw: number }
export interface CustomPanel { base: string; components: Record<string, number> }
export interface Config {
  frequency: number; radius: number; frameStyle: string; hubStyle: string; strutShape: string;
  strutWidth: number; frameMaterial: string; panel: string; foundation: string; foundationScale: number;
  /** materials.WEDGE_ORIENTATIONS: which way a wedge strut's bark faces. */
  wedgeOrientation?: string;
  /** Three cladding layers over the panels ("None" for an empty slot). */
  layers?: string[];
  /** Panel key (DomeModel's, from the face's centre on the unit sphere) -> panel type. */
  panelOverrides?: Record<string, string>;
  /** Ten floor sections: the centre, then nine 40-degree wedges. */
  sections?: string[];
  partitions?: string;
  props?: Prop[];
  trunkStockLength?: number; trunkCircumference?: number;
  frameColor?: string; panelColor?: string; recess?: number;
  /** The Panel Lab's panels: a base surface plus hardware. */
  customPanels?: Record<string, CustomPanel>;
}

export interface StrutClass { name: string; length: number; count: number }
export interface PanelRow { name: string; count: number; area: number; weight: number; cost: number }
export interface LayerRow { name: string; area: number; weight: number; cost: number }
export interface WallSegment { inner: [number, number]; outer: [number, number]; length: number; height: number; azimuth: number }
export interface Run { from: [number, number]; to: [number, number]; length: number; what: string }
export interface WedgePanelRow { name: string; splits: number; area: number; wedgeFt: number; logFt: number; recovery: number; logIn: number; kerfIn: number; allowed: boolean }
export interface Design {
  config: Config;
  height: number; floorArea: number; floorRadius: number; surfaceArea: number;
  struts: [number[], number[]][];          // endpoints, sphere centre at the origin, z up, metres
  /** For each strut, the panel it frames (Hubless Doubled) or its own index: the alternating build's unit. */
  strutPiece: number[];
  panels: number[][][];                   // triangles, same frame
  panelKeys: string[]; panelTypes: string[];
  strutClasses: StrutClass[]; strutCount: number; strutTotalLen: number;
  hubCount: number; boltCount: number; panelCount: number; treesRequired: number;
  wedgeSplits: number; wedgeLogDiameter: number; wedgeFlips: boolean[];
  trunkStockCount: number; trunkTooShort: boolean; trunkLongest: number;
  frameWeight: number; frameCost: number; hubWeight: number; hubCost: number;
  panelRows: PanelRow[]; panelWeight: number; panelCost: number; solarWatts: number;
  layerRows: LayerRow[]; layerWeight: number; layerCost: number;
  foundationArea: number; foundationWeight: number; foundationCost: number;
  walls: WallSegment[]; wallArea: number; wallWeight: number; wallCost: number;
  propRows: { name: string; count: number; weight: number; cost: number; watts: number }[];
  propCount: number; propWeight: number; propCost: number; propWatts: number;
  wireRuns: Run[]; wireLen: number; wireCost: number;
  pipeRuns: Run[]; pexLen: number; drainLen: number; plumbingCost: number;
  assignedSections: number; hardware: Record<string, number>; hardwareScrews: number;
  wedgePanelRows: WedgePanelRow[];
  structureWeight: number; totalCost: number;
  baseZ: number; note: string | null;
}

export const DEFAULTS: Config = {
  ...T.defaults, wedgeOrientation: "Inside", layers: ["None", "None", "None"], panelOverrides: {},
  sections: Array(10).fill("Unassigned"), partitions: "Markings", props: [], trunkStockLength: 0, trunkCircumference: 0,
  frameColor: "Material", panelColor: "Natural", recess: 0.5, customPanels: {},
};

const byName = <X extends { name: string }>(xs: X[], name: string) => xs.find((x) => x.name === name) ?? xs[0];
type Panel = (typeof T.panels)[number];
const FIT = T.fitout;

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

/** materials.custom_panel_extras: (cost, weight, screws, minutes) a panel's hardware adds. */
export function customExtras(def: CustomPanel) {
  let cost = 0, weight = 0, minutes = 0, screws = 0;
  for (const [name, qty] of Object.entries(def.components || {})) {
    const comp = T.panelLab.components.find((c) => c.name === name);
    if (!comp || qty <= 0) continue;
    cost += comp.cost * qty; weight += comp.weight * qty; minutes += comp.minutes * qty; screws += comp.screwsEach * qty;
  }
  cost += screws * T.panelLab.screwCost;
  return { cost, weight, screws, minutes };
}

/** Every panel type this design can use: the Creator's, then its Panel Lab panels
 *  (materials.register_custom_panel: the base's figures plus the hardware over a nominal panel). */
export function panelTypes(c: Config): Panel[] {
  const out: Panel[] = [...T.panels];
  for (const [name, def] of Object.entries(c.customPanels || {}).sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))) {
    let base = T.panels.find((p) => p.name === def.base);
    if (!base || base.name === "Open") base = T.panels.find((p) => p.name === "Plywood")!;
    const x = customExtras(def), n = T.panelLab.nominalPanelM2;
    out.push({ ...base, name, areaWeight: base.areaWeight + x.weight / n, costPerM2: base.costPerM2 + x.cost / n });
  }
  return out;
}

/** materials.StrutShape.wedge_radius: a wedge's log radius when its bark chord spans the width. */
export const wedgeRadius = (splits: number, width: number) => width / (2 * Math.sin(Math.PI / splits));

/** DomeConfig.wedge_flips: which pieces curve outward -- none, all, or every other one. */
export function wedgeFlips(orientation: string | undefined, count: number) {
  return Array.from({ length: count }, (_, i) => (orientation === "Alternating" ? i % 2 === 1 : orientation === "Outside"));
}

/** workshop.section_of: 0 the centre, 1-9 the wedges, -1 outside the floor. */
export function sectionOf(x: number, y: number, floorRadius: number) {
  const d = Math.hypot(x, y);
  if (d > floorRadius * 1.02) return -1;
  if (d < floorRadius * FIT.centerFraction) return 0;
  const az = ((Math.atan2(x, y) * 180) / Math.PI + 360) % 360;
  return 1 + (Math.floor(az / FIT.wedgeDegrees) % 9);
}
export const sectionLabel = (i: number) => (i === 0 ? "S1 · Center" : `S${i + 1} · ${(i - 1) * 40}-${(i - 1) * 40 + 40}°`);

export function design(c: Config): Design {
  const geo = T.geometry.find((g) => g.frequency === c.frequency) ?? T.geometry[0];
  const r = c.radius;
  const verts = geo.vertices.map((v) => scale(v, r));

  // DomeModel.rebuild: Hubless Doubled is every triangle its own frame, pulled toward its
  // centroid so neighbours run side by side, bolted twice along each shared edge; every other
  // style is a strut per edge with a hub at every node.
  const struts: [number[], number[]][] = [];
  const strutPiece: number[] = [];
  let hubCount = 0, boltCount = 0;
  const hubless = c.frameStyle === "Hubless Doubled";
  if (hubless) {
    const inset = c.strutWidth * T.hublessInset;
    geo.faces.forEach((f, fi) => {
      const tri = f.map((i) => verts[i]);
      const cen = scale(add(add(tri[0], tri[1]), tri[2]), 1 / 3);
      const pulled = tri.map((v) => {
        const toC = sub(cen, v), d = len(toC);
        return add(v, scale(toC, Math.min(inset, d * T.hublessInsetCap) / d));
      });
      for (let i = 0; i < 3; i++) { struts.push([pulled[i], pulled[(i + 1) % 3]]); strutPiece.push(fi); }
    });
    boltCount = geo.edges.length * 2;
  } else {
    geo.edges.forEach(([a, b], i) => { struts.push([verts[a], verts[b]]); strutPiece.push(i); });
    hubCount = verts.length;
  }
  const panels = geo.faces.map((f) => f.map((i) => verts[i]));

  // DomeModel.stats: struts grouped into length classes (A, B, C, ...)
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

  // wedges are harvested `splits` to a log
  const wedge = shape.kind === "wedge";
  const treesRequired = wedge ? Math.ceil(struts.length / shape.splits) : 0;
  const wedgeLogDiameter = wedge ? 2 * wedgeRadius(shape.splits, c.strutWidth) : 0;
  const pieces = hubless ? geo.faces.length : struts.length;
  const flips = wedgeFlips(c.wedgeOrientation, pieces);
  const longest = Math.max(0, ...groups.keys());
  const stockLen = c.trunkStockLength || 0;
  const trunkStock = stockLen > 0 && shape.name === T.trunkStock.shape;
  const trunkStockCount = trunkStock ? Math.ceil((totalLen * T.trunkStock.waste) / stockLen) : 0;

  // panels, each its own type, grouped by type
  const types = panelTypes(c);
  const typeOf = (name: string) => types.find((p) => p.name === name);
  const defaultType = typeOf(c.panel) ?? typeOf("Plywood")!;
  const rows = new Map<string, PanelRow>();
  let panelWeight = 0, panelCost = 0, solarWatts = 0, surface = 0, covered = 0;
  const panelTypesUsed: string[] = [];
  panels.forEach((t, i) => {
    const pt = typeOf(c.panelOverrides?.[geo.panelKeys[i]] ?? "") ?? defaultType;
    const a = triArea(t[0], t[1], t[2]);
    panelTypesUsed.push(pt.name);
    const row = rows.get(pt.name) ?? { name: pt.name, count: 0, area: 0, weight: 0, cost: 0 };
    row.count++; row.area += a; row.weight += a * pt.areaWeight; row.cost += a * pt.costPerM2;
    rows.set(pt.name, row);
    panelWeight += a * pt.areaWeight; panelCost += a * pt.costPerM2; solarWatts += a * pt.wattsPerM2;
    surface += a;
    if (pt.name !== "Open" && !pt.isWindow) covered += a;
  });
  const panelRows = [...rows.values()].sort((x, y) => (x.name < y.name ? -1 : 1));

  const wedgePanelRows: WedgePanelRow[] = [];
  for (const row of panelRows) {
    const wp = T.wedgePanels.find((w) => w.name === row.name);
    if (wp) wedgePanelRows.push({ name: row.name, splits: wp.splits, area: row.area, wedgeFt: row.area * wp.wedge_ft_per_m2,
      logFt: row.area * wp.log_ft_per_m2, recovery: wp.recovery, logIn: wp.log_in, kerfIn: wp.kerf_in, allowed: wp.allowed });
  }

  // cladding layers cover every panel but the open slots and windows
  const layerRows: LayerRow[] = [];
  let layerWeight = 0, layerCost = 0;
  for (const name of c.layers ?? []) {
    const l = T.layers.find((x) => x.name === name);
    if (!l || l.name === "None") continue;
    const row = { name: l.name, area: covered, weight: covered * l.areaWeight, cost: covered * l.costPerM2 };
    layerRows.push(row); layerWeight += row.weight; layerCost += row.cost;
  }

  const fd = byName(T.foundations, c.foundation);
  const fr = r * c.foundationScale;
  let fArea = fd.height > 0 ? Math.PI * fr * fr : 0;
  if (fd.name === "Bare Ground") fArea = 0;

  const ring = Math.sqrt(Math.max(0, 1 - geo.baseZ * geo.baseZ));
  const floorRadius = r * ring;

  // workshop.partition_segments: a wall between neighbouring wedges whose rooms differ
  const sections = c.sections ?? Array(10).fill("Unassigned");
  const walls: WallSegment[] = [];
  const h = (FIT.partitionHeights as Record<string, number>)[c.partitions ?? "Markings"];
  if (h !== undefined) {
    const inner = floorRadius * FIT.centerFraction + FIT.doorway, outer = floorRadius - FIT.wallRimGap;
    if (outer - inner >= FIT.wallMin) {
      for (let k2 = 0; k2 < 9; k2++) {
        if (sections[1 + ((k2 + 8) % 9)] === sections[1 + k2]) continue;
        const az = k2 * FIT.wedgeDegrees, a = (az * Math.PI) / 180;
        const dir = [Math.sin(a), Math.cos(a)];
        walls.push({ inner: [dir[0] * inner, dir[1] * inner], outer: [dir[0] * outer, dir[1] * outer], length: outer - inner, height: h, azimuth: az });
      }
    }
  }
  const wallArea = walls.reduce((s2, w) => s2 + w.length * w.height, 0);

  // props, and the wiring and plumbing they need
  const props = (c.props ?? []).filter((p) => FIT.props.some((q) => q.name === p.type));
  const propRowMap = new Map<string, { name: string; count: number; weight: number; cost: number; watts: number }>();
  let propWeight = 0, propCost = 0, propWatts = 0;
  for (const p of props) {
    const q = FIT.props.find((x) => x.name === p.type)!;
    const row = propRowMap.get(q.name) ?? { name: q.name, count: 0, weight: 0, cost: 0, watts: 0 };
    row.count++; row.weight += q.weight; row.cost += q.cost; row.watts += q.watts;
    propRowMap.set(q.name, row);
    propWeight += q.weight; propCost += q.cost; propWatts += q.watts;
  }
  const role = (p: Prop) => FIT.props.find((x) => x.name === p.type)?.role ?? "";
  const source = props.find((p) => role(p) === "battery") ?? props.find((p) => role(p) === "controller") ?? null;
  const wireRuns: Run[] = [];
  if (source) {
    for (const p of props) {
      if (p === source || !["outlet", "meter", "controller"].includes(role(p))) continue;
      wireRuns.push({ from: [source.x, source.y], to: [p.x, p.y], length: Math.hypot(p.x - source.x, p.y - source.y) * FIT.wireSlack, what: p.type });
    }
  }
  const util: [number, number] = [FIT.utility[0], floorRadius * FIT.utility[1]];
  const pipeRuns: Run[] = props.filter((p) => FIT.waterFixtures.includes(p.type))
    .map((p) => ({ from: util, to: [p.x, p.y], length: Math.hypot(p.x - util[0], p.y - util[1]) * FIT.pipeSlack, what: p.type }));
  const wireLen = wireRuns.reduce((s2, x) => s2 + x.length, 0);
  const pipeLen = pipeRuns.reduce((s2, x) => s2 + x.length, 0);
  const pexLen = pipeLen * 2, drainLen = pipeLen;
  const wireCost = wireLen * FIT.wireCostPerM;
  const plumbingCost = pexLen * FIT.pexCostPerM + drainLen * FIT.drainCostPerM + pipeRuns.length * FIT.fixtureRoughCost;

  // the Panel Lab's hardware, totalled over every panel that uses a custom type
  const hardware: Record<string, number> = {};
  let hardwareScrews = 0;
  for (const name of panelTypesUsed) {
    const def = c.customPanels?.[name];
    if (!def) continue;
    for (const [comp, qty] of Object.entries(def.components)) {
      const x = T.panelLab.components.find((cc) => cc.name === comp);
      if (!x || qty <= 0) continue;
      hardware[comp] = (hardware[comp] || 0) + qty; hardwareScrews += x.screwsEach * qty;
    }
  }

  const wallWeight = wallArea * FIT.wallWeightPerM2, wallCost = wallArea * FIT.wallCostPerM2;
  const structureWeight = frameWeight + hubWeight + panelWeight + layerWeight + propWeight + wallWeight;
  const totalCost = frameCost + hubCost + panelCost + layerCost + fArea * fd.costPerM2 + propCost + wallCost + wireCost + plumbingCost;
  return {
    config: c, height: (1 - geo.baseZ) * r, floorArea: Math.PI * floorRadius ** 2, floorRadius, surfaceArea: surface,
    struts, strutPiece, panels, panelKeys: geo.panelKeys, panelTypes: panelTypesUsed,
    strutClasses, strutCount: struts.length, strutTotalLen: totalLen,
    hubCount, boltCount, panelCount: panels.length, treesRequired,
    wedgeSplits: wedge ? shape.splits : 0, wedgeLogDiameter, wedgeFlips: flips,
    trunkStockCount, trunkTooShort: trunkStock && longest > stockLen, trunkLongest: longest,
    frameWeight, frameCost, hubWeight, hubCost, panelRows, panelWeight, panelCost, solarWatts,
    layerRows, layerWeight, layerCost,
    foundationArea: fArea, foundationWeight: fArea * fd.weightPerM2, foundationCost: fArea * fd.costPerM2,
    walls, wallArea, wallWeight, wallCost,
    propRows: [...propRowMap.values()], propCount: props.length, propWeight, propCost, propWatts,
    wireRuns, wireLen, wireCost, pipeRuns, pexLen, drainLen, plumbingCost,
    assignedSections: sections.filter((s2) => s2 !== "Unassigned").length, hardware, hardwareScrews,
    wedgePanelRows, structureWeight, totalCost, baseZ: geo.baseZ,
    note: (T.notes as Record<string, string>)[c.frameStyle] ?? null,
  };
}

/** The design as the desktop Creator saves it (DomeConfig.to_dict), so it loads there (F9). */
export function toDesktop(c: Config) {
  return {
    frequency: c.frequency, radius: c.radius, strut_shape: c.strutShape, strut_width: c.strutWidth, frame_material: c.frameMaterial,
    frame_color: c.frameColor ?? "Material", trunk_stock_length: c.trunkStockLength ?? 0, trunk_circumference: c.trunkCircumference ?? 0,
    default_panel: c.panel, panel_color: c.panelColor ?? "Natural", recess_pct: c.recess ?? 0.5, layers: c.layers ?? ["None", "None", "None"],
    foundation: c.foundation, foundation_scale: c.foundationScale, panel_overrides: c.panelOverrides ?? {}, sections: c.sections ?? Array(10).fill("Unassigned"),
    partitions: c.partitions ?? "Markings", props: (c.props ?? []).map((p) => ({ ...p, on: true })), inventory: [],
    frame_style: c.frameStyle, hub_style: c.hubStyle, wedge_flip: c.wedgeOrientation === "Outside", wedge_orientation: c.wedgeOrientation ?? "Inside",
    custom_panels: c.customPanels ?? {},
  };
}

/** A design saved by the desktop Creator (or by this page), back into a Config. */
export function fromDesktop(d: Record<string, unknown>): Config {
  const s = (k: string, fallback: unknown) => (d[k] ?? fallback) as never;
  const has = <X extends { name: string }>(xs: X[], v: unknown) => xs.some((x) => x.name === v);
  return {
    ...DEFAULTS,
    frequency: T.frequencies.includes(Number(d.frequency)) ? Number(d.frequency) : DEFAULTS.frequency,
    radius: Number(d.radius) || DEFAULTS.radius,
    frameStyle: T.frameStyles.includes(String(d.frame_style)) ? String(d.frame_style) : DEFAULTS.frameStyle,
    hubStyle: T.hubStyles.includes(String(d.hub_style)) ? String(d.hub_style) : DEFAULTS.hubStyle,
    strutShape: has(T.strutShapes, d.strut_shape) ? String(d.strut_shape) : DEFAULTS.strutShape,
    strutWidth: T.dials["Strut width"].values.reduce((a, b) => (Math.abs(b - Number(d.strut_width)) < Math.abs(a - Number(d.strut_width)) ? b : a)),
    frameMaterial: has(T.frameMaterials, d.frame_material) ? String(d.frame_material) : DEFAULTS.frameMaterial,
    panel: String(s("default_panel", DEFAULTS.panel)), foundation: has(T.foundations, d.foundation) ? String(d.foundation) : DEFAULTS.foundation,
    foundationScale: Number(d.foundation_scale) || DEFAULTS.foundationScale,
    wedgeOrientation: T.wedgeOrientations.includes(String(d.wedge_orientation)) ? String(d.wedge_orientation) : d.wedge_flip ? "Outside" : "Inside",
    layers: ((d.layers as string[]) ?? []).concat(["None", "None", "None"]).slice(0, 3).map((n) => (has(T.layers, n) ? n : "None")),
    panelOverrides: { ...((d.panel_overrides as Record<string, string>) ?? {}) },
    sections: ((d.sections as string[]) ?? []).concat(Array(10).fill("Unassigned")).slice(0, 10).map((n) => (has(FIT.rooms, n) ? n : "Unassigned")),
    partitions: FIT.partitionModes.includes(String(d.partitions)) ? String(d.partitions) : "Markings",
    props: ((d.props as Prop[]) ?? []).filter((p) => has(FIT.props, p.type)).map((p) => ({ type: p.type, x: Number(p.x) || 0, y: Number(p.y) || 0, yaw: Number(p.yaw) || 0 })),
    trunkStockLength: Number(d.trunk_stock_length) || 0, trunkCircumference: Number(d.trunk_circumference) || 0,
    frameColor: String(s("frame_color", "Material")), panelColor: String(s("panel_color", "Natural")), recess: Number(d.recess_pct) || 0.5,
    customPanels: { ...((d.custom_panels as Record<string, CustomPanel>) ?? {}) },
  };
}
