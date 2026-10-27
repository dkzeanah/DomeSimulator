// The Dome Assembly Line space's controls: the desktop demo (assembly_line.py) on al_build's own
// figures. The floor (assemblyFloor.ts) runs the line -- the carriage station to station, the crew
// walking every element from the stockpile and taking its install time, disruptions, the gantry
// crane, the turntable, the yard -- and every sum is al_build's (assembly.ts, checked against it).
//
// In the control panel's tab: the line running, the unit on it and what it has cost so far. In
// fullscreen: the studio -- the line with its disruptions and the next unit, and the desktop's
// panels: P&L (with its cost sensitivity), flow and bottleneck, BOM, the benchmark, the product's
// value, scale, the yard's ledger, and every assumption, editable.

import { useEffect, useMemo, useRef, useState } from "react";
import {
  bhphMonthly, breakEven, buildDays, econWithSensitivity, laborMinutes, loadLines, loadRun, materialCost, productValue, salePrice, scaleScenarios,
  throughput, totalWeight, unitEconomics, type Assumptions, type FactoryLines, type Line, type Run, type YardRecord,
} from "./assembly";
import { FactoryFloor, SCALE_FT_PER_M, loadBuffers, type FloorState } from "./assemblyFloor";
import type { ToolProps } from "./tools";
import { Dial, Head, Row, Select, Tabs } from "./tools/ui";

const usd = (x: number) => `$${Math.round(x).toLocaleString()}`;
const SPEEDS = [0.5, 1, 2, 4, 8, 16, 32];
const YARD = "zl.assembly.yard.v1";
const loadYard = (): YardRecord[] => { try { return JSON.parse(localStorage.getItem(YARD) || "[]"); } catch { return []; } };
const saveYard = (y: YardRecord[]) => { try { localStorage.setItem(YARD, JSON.stringify(y.slice(-200))); } catch { /* the yard lasts the visit */ } };

type Tab = "line" | "pnl" | "flow" | "bom" | "vs" | "value" | "scale" | "yard" | "assume";

/** One of the fixed product-line catalogs as a unit the floor can build. */
function lineAsRun(line: Line, serial: number, a: Assumptions): Run {
  return { ...line, serial, model: `${line.name} ${line.key === "home" ? line.layout : ""}`.trim(), cladding: "Slate Scale", claddingRgb: [0.16, 0.34, 0.38],
    accent: [0.85, 0.65, 0.1], floorR: Math.sqrt(line.floorArea / Math.PI), price: salePrice(line, line.layout, a), monthly: bhphMonthly(salePrice(line, line.layout, a), a), elementsFile: "" };
}

export default function AssemblyPanel({ world, colour, studio }: ToolProps) {
  const [data, setData] = useState<FactoryLines | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("line");
  const [crew, setCrew] = useState(2);
  const [wage, setWage] = useState<number | null>(null);
  const [over, setOver] = useState<Record<string, number>>({});
  const [speed, setSpeed] = useState(4);
  const [playing, setPlaying] = useState(true);
  const [next, setNext] = useState("random");
  const [sens, setSens] = useState({ lumber: 1, resin: 1, wage: 1 });
  const [yard, setYard] = useState<YardRecord[]>(loadYard);
  const [snap, setSnap] = useState<FloorState | null>(null);
  const [picked, setPicked] = useState<{ id: string; name: string; examine?: string } | null>(null);
  const floor = useRef<FactoryFloor | null>(null);
  const live = useRef({ playing, speed });
  live.current = { playing, speed };
  const runIndex = useRef(0);
  // every unit put on the line takes the next serial, finished or not (as the desktop line counts them)
  const serialRef = useRef(loadYard().at(-1)?.serial ?? 0);

  useEffect(() => { loadLines().then((d) => { const f = d as FactoryLines; setData(f); setCrew(Number(f.assumptions.workers_per_station)); setWage(Number(f.assumptions.burdened_wage_per_hour)); }).catch((e) => setError((e as Error).message)); }, []);
  const a: Assumptions | null = useMemo(() => (data && wage !== null ? { ...data.assumptions, ...over, workers_per_station: crew, burdened_wage_per_hour: wage } : null), [data, crew, wage, over]);
  const aRef = useRef(a); aRef.current = a;
  const nextRef = useRef(next); nextRef.current = next;
  const yardRef = useRef(yard); yardRef.current = yard;

  /** The next unit onto the line: the desktop's random run (the exported draws in turn), or a chosen line. */
  const startNext = async () => {
    const f = floor.current, d = data, aa = aRef.current;
    if (!f || !d || !aa) return;
    const serial = ++serialRef.current;
    let run: Run;
    if (nextRef.current === "random") { const r = d.runs[runIndex.current % d.runs.length]; runIndex.current++; run = { ...(await loadRun(r)), serial }; }
    else { const [key, layout] = nextRef.current.split("|"); const line = d.lines.find((l) => l.key === key && (key !== "home" || l.layout === layout))!; run = lineAsRun(line, serial, aa); }
    try { f.start(run, await loadBuffers(run), Number(aa.workers_per_station)); } catch (e) { setError((e as Error).message); }
  };

  // the floor, made once the line's data is here
  useEffect(() => {
    if (!data || floor.current) return;
    const f = new FactoryFloor(data.factory, data.stages);
    floor.current = f;
    f.setYard(yardRef.current);
    f.onFinish = (partial) => {
      const aa = aRef.current!, run = f.state.run!;
      const econ = unitEconomics(run, run.layout, aa, partial.laborHours), pv = productValue(run, aa);
      const rec: YardRecord = { ...partial, serial: run.serial, created: new Date().toLocaleString(), laborCost: econ.labor_cost, overhead: econ.overhead, totalCost: econ.total_cost,
        price: econ.price, margin: econ.margin, steps: Math.round(partial.distanceM / Number(aa.worker_stride_m)), solarKw: pv.solar_kw, rValue: pv.r_value };
      const nextYard = [...yardRef.current, rec];
      setYard(nextYard); saveYard(nextYard); f.setYard(nextYard);
      window.setTimeout(() => { void startNext(); }, 1200);
    };
    const put = () => world.current?.setModel(f.group);
    put(); window.setTimeout(put, 60);
    void startNext();
    let last = performance.now(), raf = 0, lastSnap = 0;
    const loop = (now: number) => {
      const dt = Math.min(0.1, (now - last) / 1000); last = now;
      f.update(live.current.playing ? dt * live.current.speed : 0, now / 1000);
      if (now - lastSnap > 250) { lastSnap = now; setSnap({ ...f.state, placed: { ...f.state.placed } }); }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => { cancelAnimationFrame(raf); floor.current = null; };
  }, [data]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { floor.current?.setCrew(crew); }, [crew]);
  useEffect(() => {
    const on = (e: Event) => { const p = (e as CustomEvent<{ id: string; name: string; examine?: string }>).detail; if (p?.id && /^(unit|station|yard|turntable|carriage)/.test(p.id)) setPicked(p); };
    window.addEventListener("portal-part", on);
    return () => window.removeEventListener("portal-part", on);
  }, []);

  if (error) return <p className="text-xs" style={{ color: "#ff8a7a" }}>Could not load the line: {error}</p>;
  if (!data || !a || !snap?.run) return <p className="text-xs muted">Loading the line...</p>;
  const run = snap.run;
  const econ = unitEconomics(run, run.layout, a);
  const sensed = econWithSensitivity(run, run.layout, a, data.factory, sens);
  const tp = throughput(run, data.stages, a, crew);
  const be = breakEven(econ.margin, a, econ.overhead);
  const pv = productValue(run, a);
  const scale = scaleScenarios(tp.single_flow_per_year, econ.margin, econ.price, a);
  const ph = snap.phase;
  const station = ph && ph.station >= 0 ? ph.station : -1;
  const st = station >= 0 ? data.stages.find((x) => x.key === run.stages[station]) : null;
  const total = run.elements.length;
  const laborCost = (snap.laborMin / 60) * Number(a.burdened_wage_per_hour);
  const soFar = snap.material + laborCost + (snap.elementsDone ? econ.overhead : 0);
  const steps = Math.round(snap.distanceM / Number(a.worker_stride_m));
  const stray = run.elements.filter((e) => !run.stages.includes(e.stage));
  const nextOptions: [string, string][] = [["random", "Random, as the desktop line runs"], ...data.lines.map((l) => [`${l.key}|${l.layout}`, `${l.name}${l.key === "home" ? `, ${l.layout}` : ""}`] as [string, string])];
  const phaseWord: Record<string, string> = { intro: "rolling onto the line", travel: "moving to the station", work: "being built", tocrane: "rolling to the crane", hook: "hooked by its apex", lift: "lifted", carry: "carried in", lower: "lowered onto the turntable", unhook: "unhooked", park: "on the turntable" };

  const controls = (
    <div className="grid gap-2">
      <div className="flex items-center gap-2">
        <button className="btn-ghost !py-1 !px-3 text-sm font-semibold" style={{ borderColor: colour, color: colour }} onClick={() => setPlaying((p) => !p)}>{playing ? "Pause" : "Run"}</button>
        <button className="btn-ghost !py-1 !px-2 text-sm" onClick={() => { setPlaying(false); floor.current?.stepElement(); }}>Step</button>
        <button className="btn-ghost !py-1 !px-2 text-sm" onClick={() => void startNext()}>Next unit</button>
        <span className="text-xs muted ml-auto num">{yard.length} in the yard</span>
      </div>
      <Dial label="Line speed" values={SPEEDS} value={speed} onChange={setSpeed} show={(v) => `${v}x`} />
      <Dial label="Crew at each station" values={[1, 2, 3, 4, 5, 6]} value={crew} onChange={setCrew} show={(v) => `${v} ${v === 1 ? "worker" : "workers"}`} />
    </div>
  );
  const unitCard = (
    <div className="panel-2 p-2 text-xs" style={{ borderColor: snap.stall ? "#ff8a7a" : colour }}>
      <p className="text-[10px] uppercase tracking-[0.2em] muted">#{run.serial} {run.model}: {ph ? phaseWord[ph.kind] ?? ph.kind : ""}</p>
      <p className="font-semibold" style={{ color: colour }}>{st ? `Station ${station + 1} of ${run.stages.length}: ${st.title}` : run.name}</p>
      {st && <p className="muted">{st.desc}</p>}
      {snap.stall > 0 && <p style={{ color: "#ff8a7a" }}>Stalled: {snap.stallReason} ({snap.stall.toFixed(1)} s)</p>}
      {snap.last && <p className="mt-1">Last placed: <b>{snap.last.label}</b>, {usd(snap.last.cost)}, {snap.last.labor.toFixed(1)} labor-min</p>}
      <Row k="Elements" v={`${snap.elementsDone} of ${total}`} />
      <Row k="Spent so far (material, labor, overhead)" v={usd(soFar)} />
      <Row k="Labor, steps walked" v={`${(snap.laborMin / 60).toFixed(1)} h, ${steps.toLocaleString()} steps (${Math.round(snap.distanceM)} m)`} />
      <Row k="The unit" v={`${run.radius} m, ${run.frequency}V, ${run.floorArea.toFixed(1)} m² of floor, ${run.cladding}`} />
      <Row k="Price, margin" v={`${usd(econ.price)}, ${usd(econ.margin)} (${econ.margin_pct.toFixed(1)}%)`} />
    </div>
  );

  // ---------------------------------------------------------------- the tab: the line, running
  if (!studio) {
    return (
      <div className="grid gap-3">
        <p className="text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: colour }}>The assembly line</p>
        {controls}
        {unitCard}
        {picked && <p className="text-xs panel-2 p-2"><b>{picked.name}</b>{picked.examine ? `: ${picked.examine}` : ""}</p>}
        <div>
          <Head>The line, at {crew} a station</Head>
          <Row k="One at a time" v={`${tp.single_flow_per_day.toFixed(2)} a day, ${Math.round(tp.single_flow_per_year)} a year`} />
          <Row k="Every station busy" v={`${tp.pipelined_per_day.toFixed(2)} a day, ${Math.round(tp.pipelined_per_year)} a year`} />
          <Row k="Bottleneck" v={`${tp.bottleneck.title}, ${tp.bottleneck.cycle_min.toFixed(0)} min`} />
        </div>
        <p className="text-[11px] muted leading-snug">Fullscreen opens the studio: disruptions and the next unit, the P&amp;L with cost sensitivity, flow, BOM, benchmark, value, scale, the yard&rsquo;s ledger and every assumption. The units are drawn at {SCALE_FT_PER_M} ft to the metre.</p>
      </div>
    );
  }

  // ---------------------------------------------------------------- fullscreen: the studio
  const cats = new Map<string, { n: number; cost: number; labor: number; weight: number }>();
  for (const e of run.elements) { const c = cats.get(e.category) ?? { n: 0, cost: 0, labor: 0, weight: 0 }; c.n++; c.cost += e.cost; c.labor += e.labor; c.weight += e.weight; cats.set(e.category, c); }
  const yardTotals = yard.reduce((t, r) => ({ price: t.price + r.price, cost: t.cost + r.totalCost, margin: t.margin + r.margin, hours: t.hours + r.laborHours, steps: t.steps + r.steps }), { price: 0, cost: 0, margin: 0, hours: 0, steps: 0 });
  const level = (k: "lumber" | "resin" | "wage") => (
    <Select label={k === "lumber" ? "Lumber prices" : k === "resin" ? "Resin prices" : "Wages"} value={String(sens[k])}
      options={data.factory.sensitivity.levels.map((v) => [String(v), v === 1 ? "as declared" : `${v > 1 ? "+" : ""}${Math.round((v - 1) * 100)}%`])} onChange={(v) => setSens((x) => ({ ...x, [k]: Number(v) }))} />
  );
  return (
    <div className="grid gap-3">
      <div className="flex items-baseline justify-between gap-2">
        <p className="text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: colour }}>Assembly line studio</p>
        <span className="text-xs num muted">{yard.length} built</span>
      </div>
      <Tabs value={tab} onChange={setTab} colour={colour} tabs={[["line", "Line"], ["pnl", "P&L"], ["flow", "Flow"], ["bom", "BOM"], ["vs", "VS"], ["value", "Value"], ["scale", "Scale"], ["yard", "Yard"], ["assume", "Assumptions"]]} />
      {picked && <p className="text-xs panel-2 p-2"><b>{picked.name}</b>{picked.examine ? `: ${picked.examine}` : ""}</p>}

      {tab === "line" && (
        <div className="grid gap-2">
          {controls}
          {unitCard}
          <Select label="The next unit onto the line" value={next} options={nextOptions} onChange={setNext} />
          <Head>Disruptions</Head>
          <div className="flex flex-wrap gap-1">
            {data.factory.disruptions.map((x) => <button key={x.key} className="btn-ghost !py-1 text-xs" title={x.note} onClick={() => floor.current?.inject(x.key)}>{x.label}</button>)}
          </div>
          <Head>The log</Head>
          <div className="text-[11px] num grid gap-0.5">{snap.log.slice().reverse().map((l, i) => <p key={i} className={l.startsWith("!") ? "" : "muted"} style={l.startsWith("!") ? { color: "#ff8a7a" } : undefined}>{l}</p>)}</div>
          {stray.length > 0 && <p className="text-[11px] panel-2 p-2" style={{ borderColor: "#ff8a7a" }}>A fault in <code>al_build</code>: {stray.length} element{stray.length > 1 ? "s are" : " is"} filed under &ldquo;{stray[0].stage}&rdquo;, a station this line does not have: in the unit&rsquo;s cost, on no station.</p>}
        </div>
      )}

      {tab === "pnl" && (
        <div className="grid gap-1">
          <div className="grid grid-cols-3 gap-2">{level("lumber")}{level("resin")}{level("wage")}</div>
          <Row k="Materials" v={usd(sensed.material)} />
          <Row k={`Labor, ${sensed.labor_hours.toFixed(0)} h`} v={usd(sensed.labor_cost)} />
          <Row k="Overhead, by the labor it takes" v={usd(sensed.overhead)} />
          <Row k="Cost" v={usd(sensed.total_cost)} />
          <Row k="Price" v={usd(sensed.price)} />
          <Row k="Margin" v={`${usd(sensed.margin)} (${sensed.margin_pct.toFixed(1)}%)`} />
          <Row k={`Buy here, pay here (${(Number(a.bhph_apr) * 100).toFixed(1)}% over ${a.bhph_term_months} months)`} v={`${usd(bhphMonthly(econ.price, a))} a month`} />
          <Dial label="Burdened wage" values={[20, 25, 30, 35, 40, 46, 50, 55, 60, 70, 80]} value={wage ?? 46} onChange={setWage} show={(v) => `$${v} an hour`} />
          <p className="text-[11px] muted">The sensitivity is the desktop demo&rsquo;s: lumber moves the frame, floor and hubs; resin the fiberglass, shingles and wrap; wages the labor. The price does not move.</p>
        </div>
      )}

      {tab === "flow" && (
        <div className="grid gap-2">
          <table className="w-full text-[11px] num">
            <thead><tr className="muted text-left"><th>#</th><th>Station</th><th>Done</th><th>Cycle</th></tr></thead>
            <tbody>{tp.rows.map((r, i) => {
              const done = snap.placed[r.key] ?? 0, of = snap.totals[r.key] ?? r.elements;
              return (
                <tr key={r.key} style={i === station ? { color: colour, fontWeight: 600 } : r.key === tp.bottleneck.key ? { color: "#ff8a7a" } : undefined}>
                  <td>{i + 1}</td><td>{r.title}</td>
                  <td><span className="inline-block h-1.5 align-middle mr-1" style={{ width: 40, background: "rgba(255,255,255,.1)" }}><span className="block h-full" style={{ width: `${of ? (done / of) * 100 : 0}%`, background: colour }} /></span>{done}/{of}</td>
                  <td>{r.cycle_min.toFixed(0)} min{r.key === tp.bottleneck.key ? " (bottleneck)" : ""}</td>
                </tr>
              );
            })}</tbody>
          </table>
          <Row k="One unit through every station" v={`${tp.total_cycle_min.toFixed(0)} min`} />
          <Row k="One at a time" v={`${tp.single_flow_per_day.toFixed(2)} a day, ${Math.round(tp.single_flow_per_year)} a year`} />
          <Row k="Every station busy" v={`${tp.pipelined_per_day.toFixed(2)} a day, ${Math.round(tp.pipelined_per_year)} a year`} />
        </div>
      )}

      {tab === "bom" && (
        <div className="grid gap-1">
          <table className="w-full text-[11px] num">
            <thead><tr className="muted text-left"><th>What</th><th>Pieces</th><th>Material</th><th>Labor</th><th>Weight</th></tr></thead>
            <tbody>{[...cats.entries()].sort((x, y) => y[1].cost - x[1].cost).map(([k, c]) => (
              <tr key={k}><td>{data.categoryLabel[k] ?? k}</td><td>{c.n}</td><td>{usd(c.cost)}</td><td>{(c.labor / 60).toFixed(1)} h</td><td>{Math.round(c.weight).toLocaleString()} kg</td></tr>
            ))}</tbody>
          </table>
          <Row k="All of it" v={`${total} pieces, ${usd(materialCost(run))}, ${(laborMinutes(run) / 60).toFixed(0)} h, ${Math.round(totalWeight(run)).toLocaleString()} kg`} />
        </div>
      )}

      {tab === "vs" && (
        <div className="grid gap-1">
          <Head>{run.model} against {String(a.benchmark_name).toLowerCase()}</Head>
          <Row k="Price" v={`${usd(econ.price)} vs ${usd(Number(a.benchmark_price))}`} />
          <Row k="Materials" v={`${usd(materialCost(run))} vs ${usd(Number(a.benchmark_material_cost))}`} />
          <Row k="Labor" v={`${(laborMinutes(run) / 60).toFixed(0)} h vs ${a.benchmark_labor_hours} h`} />
          <Row k="Build time" v={`${buildDays(run, a, crew).toFixed(1)} days vs ${a.benchmark_build_days} days`} />
          <p className="text-[11px] muted">The benchmark is al_build&rsquo;s declared figures for a conventional manufactured home; the dome&rsquo;s build days are its labor over the crew over the shift, as the desktop demo works them.</p>
        </div>
      )}

      {tab === "value" && (
        <div className="grid gap-1">
          <Row k="Floor" v={`${pv.floor_area.toFixed(1)} m²`} />
          <Row k="Solar" v={pv.solar_panels ? `${pv.solar_panels} panels, ${pv.solar_kw.toFixed(1)} kW, ${pv.daily_generation_kwh.toFixed(1)} kWh a day` : "none on this line"} />
          {pv.solar_panels > 0 && <Row k="Against the daily load" v={`${pv.net_daily_kwh >= 0 ? "+" : ""}${pv.net_daily_kwh.toFixed(1)} kWh`} />}
          <Row k="Battery" v={`${pv.battery_kwh} kWh, ${pv.autonomy_days.toFixed(1)} days`} />
          <Row k="Wall rating" v={`R-${pv.r_value.toFixed(0)}`} />
          <Row k="Embodied carbon" v={`${Math.round(pv.embodied_carbon_kg).toLocaleString()} kg`} />
          <Row k="Safety target (OSHA incidents)" v={String(pv.osha_target)} />
        </div>
      )}

      {tab === "scale" && (
        <div className="grid gap-1">
          <table className="w-full text-[11px] num">
            <thead><tr className="muted text-left"><th>Lines</th><th>A year</th><th>Revenue</th><th>Gross profit</th><th>Capex</th></tr></thead>
            <tbody>{scale.map((x) => <tr key={x.lines}><td>{x.lines}</td><td>{Math.round(x.units_per_year)}</td><td>{usd(x.revenue)}</td><td>{usd(x.gross_profit)}</td><td>{usd(x.capex)}</td></tr>)}</tbody>
          </table>
          <Row k="Units to pay back the line" v={Math.ceil(be.units_to_recover_capex).toLocaleString()} />
          <Row k="Units to cover a year's fixed costs" v={Math.ceil(be.units_to_cover_annual_fixed).toLocaleString()} />
          <Row k="Contribution per unit" v={usd(be.contribution_per_unit)} />
        </div>
      )}

      {tab === "yard" && (
        <div className="grid gap-2">
          <Row k="Units built" v={yard.length} />
          <Row k="Sold at, cost, margin" v={`${usd(yardTotals.price)}, ${usd(yardTotals.cost)}, ${usd(yardTotals.margin)}`} />
          <Row k="Labor, steps walked" v={`${yardTotals.hours.toFixed(0)} h, ${yardTotals.steps.toLocaleString()} steps`} />
          <div className="max-h-80 overflow-y-auto">
            <table className="w-full text-[11px] num">
              <thead className="sticky top-0" style={{ background: "var(--panel)" }}><tr className="muted text-left"><th>#</th><th>Unit</th><th>Price</th><th>Margin</th><th>Labor</th></tr></thead>
              <tbody>{yard.slice().reverse().map((r) => <tr key={r.serial}><td>{r.serial}</td><td>{r.name} <span className="muted">{r.dtype}</span></td><td>{usd(r.price)}</td><td>{usd(r.margin)}</td><td>{r.laborHours.toFixed(0)} h</td></tr>)}</tbody>
            </table>
          </div>
          <button className="btn-ghost !py-1 text-xs justify-self-start" onClick={() => { if (window.confirm("Clear the yard? The units built so far are forgotten.")) { setYard([]); saveYard([]); floor.current?.setYard([]); serialRef.current = 0; } }}>Clear the yard</button>
          <p className="text-[11px] muted">The yard is kept in this browser, as the desktop line keeps its own in a file.</p>
        </div>
      )}

      {tab === "assume" && (
        <div className="grid gap-1">
          <p className="text-[11px] muted">al_build&rsquo;s editable block: estimates, not measurements. Change one and every figure here follows.</p>
          {Object.entries(data.assumptions).filter(([, v]) => typeof v === "number").map(([k, v]) => (
            <label key={k} className="flex items-center justify-between gap-2 text-xs border-b py-0.5" style={{ borderColor: "var(--line)" }}>
              <span className="muted">{k.replace(/_/g, " ")}</span>
              <input type="number" className="field !py-0 !px-1 w-28 text-right num" step="any"
                value={k === "workers_per_station" ? crew : k === "burdened_wage_per_hour" ? (wage ?? Number(v)) : (over[k] ?? Number(v))}
                onChange={(e) => { const x = Number(e.target.value); if (!Number.isFinite(x)) return; if (k === "workers_per_station") setCrew(Math.max(1, Math.min(6, Math.round(x)))); else if (k === "burdened_wage_per_hour") setWage(x); else setOver((o) => ({ ...o, [k]: x })); }} />
            </label>
          ))}
          <button className="btn-ghost !py-1 text-xs justify-self-start mt-1" onClick={() => { setOver({}); setCrew(Number(data.assumptions.workers_per_station)); setWage(Number(data.assumptions.burdened_wage_per_hour)); }}>Back to al_build&rsquo;s figures</button>
        </div>
      )}
      <p className="text-[11px] muted leading-snug">Every element, cost and minute is <code>al_build</code>&rsquo;s, the floor&rsquo;s pacing and disruptions <code>assembly_line.py</code>&rsquo;s; the sums are re-run here and checked against them.</p>
    </div>
  );
}
