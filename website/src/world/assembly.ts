// The Dome Assembly Line's sums, in the browser. Each product line's dome, element by element,
// and the assumptions come from al_build (scripts/portal_spaces_export.py ->
// /portal/assembly/lines.json); this file is al_build's DomeSpec.sale_price, bhph_monthly(),
// unit_economics(), station_cycle_times(), throughput(), break_even(), product_value() and
// scale_scenarios(), line for line. scripts/test_portal_spaces.mjs checks them against al_build.

export type Assumptions = Record<string, number | string | Record<string, number>>;
export interface Element { stage: string; category: string; label: string; cost: number; labor: number; weight: number; o: [number, number]; t: [number, number]; at: [number, number, number]
  /** Where on the deck a worker carries it (al_build's floor_point), metres from the centre. */
  fp: [number, number] }
export interface MeshHead { file: string; vertices: number; opaque: number; transparent: number; scale: number; palette: number[][] }
export interface Line { key: string; name: string; tagline: string; stages: string[]; radius: number; frequency: number; layout: string; floorArea: number; priceBase: number; pricePerM2: number; elements: Element[]; mesh: MeshHead }
export interface Stage { key: string; title: string; desc: string; colour: number[] }
export interface Lines { assumptions: Assumptions; stages: Stage[]; categoryLabel: Record<string, string>; layouts: string[]; lines: Line[] }

let loaded: Promise<Lines> | null = null;
export const loadLines = () => (loaded ??= fetch("/portal/assembly/lines.json").then((r) => { if (!r.ok) throw new Error(`lines.json: ${r.status}`); return r.json(); }));

const n = (a: Assumptions, k: string) => a[k] as number;

export function salePrice(line: Line, layout: string, a: Assumptions) {
  let p = line.priceBase + line.pricePerM2 * line.floorArea;
  if (line.key === "home") p += ((a.layout_price as Record<string, number>)[layout] ?? 0);
  return p;
}

export function bhphMonthly(price: number, a: Assumptions) {
  const principal = price * (1 - n(a, "bhph_down_fraction"));
  const r = n(a, "bhph_apr") / 12, m = n(a, "bhph_term_months");
  if (r <= 0) return principal / m;
  return (principal * (r * (1 + r) ** m)) / ((1 + r) ** m - 1);
}

const sum = (xs: number[]) => xs.reduce((s, x) => s + x, 0);
export const materialCost = (line: Line) => sum(line.elements.map((e) => e.cost));
export const laborMinutes = (line: Line) => sum(line.elements.map((e) => e.labor));
export const totalWeight = (line: Line) => sum(line.elements.map((e) => e.weight));
const count = (line: Line, stage: string) => line.elements.filter((e) => e.stage === stage).length;

export function unitEconomics(line: Line, layout: string, a: Assumptions, laborHours?: number) {
  const material = materialCost(line);
  const hours = laborHours ?? laborMinutes(line) / 60;
  const labor_cost = hours * n(a, "burdened_wage_per_hour");
  const overhead = hours * n(a, "overhead_per_labor_hour");
  const total_cost = material + labor_cost + overhead;
  const price = salePrice(line, layout, a);
  const margin = price - total_cost;
  return { material, labor_hours: hours, labor_cost, overhead, total_cost, price, margin, margin_pct: price ? (margin / price) * 100 : 0 };
}

export function stationCycleTimes(line: Line, stages: Stage[], a: Assumptions, crew?: number) {
  const c = Math.max(1, crew || n(a, "workers_per_station"));
  return line.stages.map((key) => {
    const els = line.elements.filter((e) => e.stage === key);
    const labor_min = sum(els.map((e) => e.labor));
    return { key, title: stages.find((s) => s.key === key)?.title ?? key, elements: els.length, labor_min, cycle_min: labor_min / c };
  });
}

export function throughput(line: Line, stages: Stage[], a: Assumptions, crew?: number) {
  const rows = stationCycleTimes(line, stages, a, crew);
  const active = rows.filter((r) => r.cycle_min > 0);
  const pool = active.length ? active : rows;
  // Python's max() keeps the first of equals
  const bottleneck = pool.reduce((b, r) => (r.cycle_min > b.cycle_min ? r : b), pool[0]);
  const total_cycle_min = sum(rows.map((r) => r.cycle_min));
  const perDay = n(a, "shift_hours_per_day") * 60;
  const single = total_cycle_min ? perDay / total_cycle_min : 0;
  const pipe = bottleneck.cycle_min ? perDay / bottleneck.cycle_min : 0;
  return { rows, bottleneck, total_cycle_min, single_flow_per_day: single, single_flow_per_year: single * n(a, "work_days_per_year"),
    pipelined_per_day: pipe, pipelined_per_year: pipe * n(a, "work_days_per_year") };
}

export function breakEven(margin: number, a: Assumptions, overhead?: number) {
  const fixed_year = n(a, "fixed_overhead_per_month") * 12;
  let oh = overhead;
  if (oh === undefined) oh = (n(a, "line_capex") / n(a, "capex_amortize_years") + fixed_year) / Math.max(1, n(a, "target_units_per_year"));
  const contribution = Math.max(1, margin + oh);
  return { capex: n(a, "line_capex"), fixed_year, contribution_per_unit: contribution,
    units_to_recover_capex: n(a, "line_capex") / contribution, units_to_cover_annual_fixed: fixed_year / contribution };
}

export function productValue(line: Line, a: Assumptions) {
  const panels = count(line, "solar");
  const solar_kw = (panels * n(a, "solar_watts_per_panel")) / 1000;
  const daily = solar_kw * 4.5 * 1.25;
  return { solar_kw, solar_panels: panels, daily_generation_kwh: daily, net_daily_kwh: daily - n(a, "daily_load_kwh"),
    battery_kwh: n(a, "battery_kwh"), autonomy_days: n(a, "battery_kwh") / Math.max(0.1, n(a, "daily_load_kwh")),
    r_value: 12 + count(line, "insulation") * n(a, "insulation_r_per_element"),
    embodied_carbon_kg: totalWeight(line) * n(a, "carbon_kg_per_kg_material"), osha_target: n(a, "osha_incident_rate_target"), floor_area: line.floorArea };
}

export function scaleScenarios(singlePerYear: number, margin: number, price: number, a: Assumptions) {
  return [1, 3, 6].map((lines) => {
    const units = singlePerYear * lines;
    return { lines, units_per_year: units, revenue: units * price, gross_profit: units * margin, capex: n(a, "line_capex") * lines };
  });
}

// ----------------------------------------------------------------------
// The factory floor (assembly_line.py, the desktop demo)
// ----------------------------------------------------------------------

export interface Phase { kind: string; station: number; dur: number }
export interface Disruption { key: string; label: string; stall?: number; crew?: number; note: string }
export interface Factory { placeAnimPerLaborMin: number; walkSpeed: number; travelSecs: number; phases: Phase[]; disruptions: Disruption[];
  sensitivity: { lumber: string[]; resin: string[]; wage: string[]; levels: number[] } }
/** A production spec on the factory floor: a Line (so every sum above takes it) plus its own make-up. */
export interface Run extends Line { serial: number; model: string; cladding: string; claddingRgb: number[]; accent: number[]; floorR: number; price: number; monthly: number; elementsFile: string }
export interface FactoryLines extends Lines { factory: Factory; runs: Run[] }

const runEls = new Map<string, Promise<Element[]>>();
/** A run's elements live in their own file; fetch them when the run comes up. */
export function loadRun(run: Run): Promise<Run> {
  let p = runEls.get(run.elementsFile);
  if (!p) {
    p = fetch(run.elementsFile).then((r) => { if (!r.ok) throw new Error(`${run.elementsFile}: ${r.status}`); return r.json(); }).then((j) => j.elements as Element[]);
    p.catch(() => runEls.delete(run.elementsFile));
    runEls.set(run.elementsFile, p);
  }
  return p.then((elements) => ({ ...run, elements }));
}

/** assembly_line.build_phases, for a line of this many stations. */
export function phasesFor(f: Factory, stations: number): Phase[] {
  const dur = (kind: string) => f.phases.find((p) => p.kind === kind)?.dur ?? 1;
  const out: Phase[] = [{ kind: "intro", station: -1, dur: dur("intro") }];
  for (let i = 0; i < stations; i++) out.push({ kind: "travel", station: i, dur: f.travelSecs }, { kind: "work", station: i, dur: 0 });
  for (const kind of ["tocrane", "hook", "lift", "carry", "lower", "unhook", "park"]) out.push({ kind, station: -1, dur: dur(kind) });
  return out;
}

/** assembly_line.App._econ_with_sensitivity: lumber moves the frame and floor, resin the fiberglass
 *  and shingles, the wage the labor; the price stays. */
export function econWithSensitivity(line: Line, layout: string, a: Assumptions, f: Factory, s: { lumber: number; resin: number; wage: number }) {
  const base = unitEconomics(line, layout, a);
  let material = 0;
  for (const e of line.elements) material += e.cost * (f.sensitivity.lumber.includes(e.category) ? s.lumber : f.sensitivity.resin.includes(e.category) ? s.resin : 1);
  const labor_cost = base.labor_cost * s.wage;
  const total_cost = material + labor_cost + base.overhead;
  const margin = base.price - total_cost;
  return { ...base, material, labor_cost, total_cost, margin, margin_pct: base.price ? (margin / base.price) * 100 : 0 };
}

/** assembly_line.App._build_days: the unit's labor over the crew over the shift. */
export const buildDays = (line: Line, a: Assumptions, crew: number) => laborMinutes(line) / 60 / Math.max(1, crew) / n(a, "shift_hours_per_day");

/** ProductionRun.final_record: what the yard keeps of a finished unit. */
export interface YardRecord { serial: number; name: string; dtype: string; radius: number; frequency: number; layout: string; cladding: string; rgb: number[];
  floorArea: number; material: number; laborCost: number; overhead: number; totalCost: number; price: number; margin: number; monthly: number;
  laborHours: number; steps: number; distanceM: number; solarKw: number; rValue: number; created: string; seconds: number }
