// The Dome Assembly Line space's control panel: al_build's product lines built on the stage element
// by element, station by station, each element taking its own install labor at the crew you set,
// with the line's unit economics, throughput, break-even and product value worked live (assembly.ts)
// from al_build's own assumptions. The meshes are al_build's own catalog.

import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import {
  bhphMonthly, breakEven, laborMinutes, loadLines, materialCost, productValue, scaleScenarios, throughput, unitEconomics,
  type Assumptions, type Line, type Lines,
} from "./assembly";
import type { ToolProps } from "./tools";
import { Choice, Dial, Head, Row } from "./tools/ui";
import type { Part } from "./engine";

const FT = 3.2808399;
const STAGE_RADIUS_FT = 8.4;
const usd = (x: number) => `$${Math.round(x).toLocaleString()}`;
const SPEEDS = [5, 15, 30, 60, 120, 300];

interface Buffers { pos: Int16Array; col: Uint8Array; alpha: Uint8Array; opaque: Uint16Array; transparent: Uint16Array }
const meshCache = new Map<string, Promise<Buffers>>();
function loadMesh(line: Line): Promise<Buffers> {
  const h = line.mesh;
  let p = meshCache.get(h.file);
  if (!p) {
    p = fetch(h.file).then((r) => { if (!r.ok) throw new Error(`${h.file}: ${r.status}`); return r.arrayBuffer(); }).then((buf) => {
      const V = h.vertices;
      let off = V * 6 + V + V;
      off += off % 2;
      return { pos: new Int16Array(buf, 0, V * 3), col: new Uint8Array(buf, V * 6, V), alpha: new Uint8Array(buf, V * 7, V),
        opaque: new Uint16Array(buf, off, h.opaque), transparent: new Uint16Array(buf, off + h.opaque * 2, h.transparent) };
    });
    p.catch(() => meshCache.delete(h.file));
    meshCache.set(h.file, p);
  }
  return p;
}

/** The catalog's whole mesh, shown up to an element: al_build emits elements in station order, so
 *  everything built so far is a prefix of each index list. */
function drawLine(line: Line, b: Buffers) {
  const h = line.mesh;
  let maxR = 0;
  for (let i = 0; i < h.vertices; i++) maxR = Math.max(maxR, Math.hypot(b.pos[i * 3], b.pos[i * 3 + 1]) * h.scale);
  const fit = Math.min(1, STAGE_RADIUS_FT / (maxR * FT));
  const s = FT * fit;
  const pos = new Float32Array(h.vertices * 3), col = new Float32Array(h.vertices * 3);
  for (let i = 0; i < h.vertices; i++) {
    pos[i * 3] = b.pos[i * 3] * h.scale * s; pos[i * 3 + 1] = b.pos[i * 3 + 2] * h.scale * s; pos[i * 3 + 2] = -b.pos[i * 3 + 1] * h.scale * s;
    const c = h.palette[b.col[i]] || [0.8, 0.6, 0.4];
    col[i * 3] = c[0]; col[i * 3 + 1] = c[1]; col[i * 3 + 2] = c[2];
  }
  const geo = (idx: Uint16Array) => {
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    g.setAttribute("color", new THREE.BufferAttribute(col, 3));
    g.setIndex(new THREE.BufferAttribute(new Uint16Array(idx), 1));
    g.computeVertexNormals();
    return g;
  };
  const group = new THREE.Group();
  const solid = new THREE.Mesh(geo(b.opaque), new THREE.MeshLambertMaterial({ vertexColors: true, flatShading: true, side: THREE.DoubleSide }));
  const glass = new THREE.Mesh(geo(b.transparent), new THREE.MeshLambertMaterial({ vertexColors: true, transparent: true, opacity: 0.45, side: THREE.DoubleSide, depthWrite: false }));
  solid.castShadow = true;
  solid.userData.part = { id: "assembly:dome", name: `the ${line.name.toLowerCase()} on the line` };
  // the carriage the dome rides on, turning slowly so the crew's work faces the walker in turn
  const platter = new THREE.Mesh(new THREE.CylinderGeometry(STAGE_RADIUS_FT * 1.02, STAGE_RADIUS_FT * 1.05, 0.5, 32), new THREE.MeshLambertMaterial({ color: "#3a3a3a" }));
  platter.position.y = -0.25;
  group.add(platter, solid, glass);
  group.onBeforeRender = () => undefined;
  return { group, solid, glass, fit };
}

export default function AssemblyPanel({ world, colour }: ToolProps) {
  const [data, setData] = useState<Lines | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dtype, setDtype] = useState("home");
  const [layout, setLayout] = useState("1-Bedroom");
  const [crew, setCrew] = useState(2);
  const [wage, setWage] = useState<number | null>(null);
  const [speed, setSpeed] = useState(60);
  const [playing, setPlaying] = useState(true);
  const [built, setBuilt] = useState(0);            // elements placed on this unit
  const [units, setUnits] = useState(0);
  const [picked, setPicked] = useState(false);
  const scene = useRef<ReturnType<typeof drawLine> | null>(null);
  const clock = useRef(0);                           // labor-minutes done on the element being placed
  const builtRef = useRef(0);
  builtRef.current = built;

  useEffect(() => { loadLines().then((d) => { setData(d); setCrew(Number(d.assumptions.workers_per_station)); setWage(Number(d.assumptions.burdened_wage_per_hour)); }).catch((e) => setError((e as Error).message)); }, []);
  const line = useMemo(() => data?.lines.find((l) => l.key === dtype && (dtype !== "home" || l.layout === layout)) ?? null, [data, dtype, layout]);
  const a: Assumptions | null = useMemo(() => (data && wage !== null ? { ...data.assumptions, workers_per_station: crew, burdened_wage_per_hour: wage } : null), [data, crew, wage]);
  // elements in station order (al_build's own order within a station)
  const order = useMemo(() => (line ? [...line.stages.flatMap((k) => line.elements.filter((e) => e.stage === k)), ...line.elements.filter((e) => !line.stages.includes(e.stage))] : []), [line]);
  // elements al_build files under a station the line does not have: costed, but on no station
  const stray = useMemo(() => (line ? line.elements.filter((e) => !line.stages.includes(e.stage)) : []), [line]);

  useEffect(() => {
    if (!line) return;
    let live = true;
    setBuilt(0); clock.current = 0;
    loadMesh(line).then((b) => {
      if (!live) return;
      const sc = drawLine(line, b);
      scene.current = sc;
      const put = () => world.current?.setModel(sc.group);
      put(); window.setTimeout(put, 50);
    }).catch((e) => live && setError((e as Error).message));
    return () => { live = false; };
  }, [line, world]);

  // what is on the stage: every element up to the one being placed
  useEffect(() => {
    const sc = scene.current;
    if (!sc || !line) return;
    const done = order.slice(0, built);
    const o = done.reduce((m, e) => Math.max(m, e.o[1]), 0), t = done.reduce((m, e) => Math.max(m, e.t[1]), 0);
    sc.solid.geometry.setDrawRange(0, o);
    sc.glass.geometry.setDrawRange(0, t);
  }, [built, order, line]);

  // the line's clock: each element takes its labor minutes over the crew, at the speed set
  useEffect(() => {
    if (!playing || !order.length) return;
    let last = performance.now();
    const timer = window.setInterval(() => {
      const now = performance.now(), dt = (now - last) / 1000; last = now;
      clock.current += (dt * speed) * Math.max(1, crew);           // labor-minutes this tick
      let k = builtRef.current;
      while (k < order.length && clock.current >= order[k].labor) { clock.current -= order[k].labor; k++; }
      if (k >= order.length) { setUnits((u) => u + 1); clock.current = 0; k = 0; }
      if (k !== builtRef.current) setBuilt(k);
    }, 100);
    return () => window.clearInterval(timer);
  }, [playing, order, speed, crew]);

  useEffect(() => {
    const on = (e: Event) => { if ((e as CustomEvent<Part>).detail.id === "assembly:dome") setPicked(true); };
    window.addEventListener("portal-part", on);
    return () => window.removeEventListener("portal-part", on);
  }, []);

  if (error) return <p className="text-xs" style={{ color: "#ff8a7a" }}>Could not load the line: {error}</p>;
  if (!data || !line || !a) return <p className="text-xs muted">Loading the line...</p>;
  const econ = unitEconomics(line, layout, a);
  const tp = throughput(line, data.stages, a, crew);
  const be = breakEven(econ.margin, a, econ.overhead);
  const pv = productValue(line, a);
  const scale = scaleScenarios(tp.single_flow_per_year, econ.margin, econ.price, a);
  const now = order[Math.min(built, order.length - 1)];
  const st = data.stages.find((s) => s.key === now?.stage);
  const doneEls = order.slice(0, built);
  const spent = doneEls.reduce((s, e) => s + e.cost, 0), hours = doneEls.reduce((s, e) => s + e.labor, 0) / 60;
  const stationIndex = line.stages.indexOf(now?.stage ?? "");
  const types = [...new Set(data.lines.map((l) => l.key))];
  return (
    <div className="grid gap-3">
      <div>
        <p className="text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: colour }}>The assembly line</p>
        <p className="text-xs muted mt-0.5">{line.tagline}: {line.elements.length.toLocaleString()} elements over {line.stages.length} stations, each with its own cost and install time.</p>
      </div>
      <Choice label="Product line" value={dtype} colour={colour} onChange={setDtype} options={types.map((k) => [k, data.lines.find((l) => l.key === k)!.name] as [string, string])} />
      {dtype === "home" && <Choice label="Layout" value={layout} colour={colour} onChange={setLayout} options={data.layouts.map((x) => [x, x] as [string, string])} />}
      <div className="flex items-center gap-2">
        <button className="btn-ghost !py-1 !px-3 text-sm font-semibold" style={{ borderColor: colour, color: colour }} onClick={() => setPlaying((p) => !p)}>{playing ? "Pause" : "Run"}</button>
        <button className="btn-ghost !py-1 !px-2 text-sm" onClick={() => { setPlaying(false); setBuilt((b) => Math.min(order.length, b + 1)); }}>Step</button>
        <button className="btn-ghost !py-1 !px-2 text-sm" onClick={() => { setBuilt(0); clock.current = 0; }}>Start over</button>
        <span className="text-xs muted ml-auto num">{units} built</span>
      </div>
      <Dial label="Line speed" values={SPEEDS} value={speed} onChange={setSpeed} show={(v) => `${v} labor-min a second`} />
      <Dial label="Crew at each station" values={[1, 2, 3, 4, 5, 6]} value={crew} onChange={setCrew} show={(v) => `${v} ${v === 1 ? "worker" : "workers"}`} />
      <Dial label="Burdened wage" values={[20, 25, 30, 35, 40, 46, 50, 55, 60, 70, 80]} value={wage ?? 46} onChange={setWage} show={(v) => `$${v} an hour`} />

      <div className="panel-2 p-2 text-xs" style={{ borderColor: colour }}>
        <p className="text-[10px] uppercase tracking-[0.2em] muted">{stationIndex >= 0 ? `Station ${stationIndex + 1} of ${line.stages.length}` : "On no station"}</p>
        <p className="font-semibold" style={{ color: colour }}>{st?.title}</p>
        <p className="muted">{st?.desc}</p>
        {now && <p className="mt-1">Placing: <b>{now.label}</b>, {usd(now.cost)}, {now.labor.toFixed(1)} labor-min</p>}
        <Row k="This unit so far" v={`${built} of ${order.length} elements, ${usd(spent)}, ${hours.toFixed(1)} h`} />
        {picked && <p className="mt-1 muted">That is {line.name.toLowerCase()} {units + 1} on the carriage: radius {line.radius} m, {line.frequency}V, {line.floorArea.toFixed(1)} m² of floor.</p>}
      </div>

      {stray.length > 0 && (
        <p className="text-[11px] panel-2 p-2" style={{ borderColor: "#ff8a7a" }}>
          A fault in <code>al_build</code>: {stray.length} element{stray.length > 1 ? "s" : ""} ({usd(stray.reduce((x, e) => x + e.cost, 0))}, {stray.reduce((x, e) => x + e.labor, 0).toFixed(0)} labor-min) {stray.length > 1 ? "are" : "is"} filed under &ldquo;{stray[0].stage}&rdquo;, a station this line does not have.
          They are in the unit&rsquo;s cost but on no station, so the station table and the throughput below leave them out, as the desktop line does. They are placed last here.
        </p>
      )}
      <div>
        <Head>Stations, at {crew} a station</Head>
        <table className="w-full text-[11px] num">
          <thead><tr className="muted text-left"><th>#</th><th>Station</th><th>Elements</th><th>Cycle</th></tr></thead>
          <tbody>{tp.rows.map((r, i) => (
            <tr key={r.key} style={i === stationIndex ? { color: colour, fontWeight: 600 } : r.key === tp.bottleneck.key ? { color: "#ff8a7a" } : undefined}>
              <td>{i + 1}</td><td>{r.title}</td><td>{r.elements}</td><td>{r.cycle_min.toFixed(0)} min{r.key === tp.bottleneck.key ? " (bottleneck)" : ""}</td>
            </tr>))}</tbody>
        </table>
      </div>
      <div>
        <Head>One {line.name.toLowerCase()}</Head>
        <Row k="Materials" v={usd(econ.material)} />
        <Row k={`Labor, ${econ.labor_hours.toFixed(0)} h`} v={usd(econ.labor_cost)} />
        <Row k="Overhead, by the labor it takes" v={usd(econ.overhead)} />
        <Row k="Cost" v={usd(econ.total_cost)} />
        <Row k="Price" v={usd(econ.price)} />
        <Row k="Margin" v={`${usd(econ.margin)} (${econ.margin_pct.toFixed(1)}%)`} />
        <Row k={`Buy here, pay here (${(Number(a.bhph_apr) * 100).toFixed(1)}% over ${a.bhph_term_months} months)`} v={`${usd(bhphMonthly(econ.price, a))} a month`} />
      </div>
      <div>
        <Head>The line</Head>
        <Row k="One at a time" v={`${tp.single_flow_per_day.toFixed(2)} a day, ${Math.round(tp.single_flow_per_year)} a year`} />
        <Row k="Every station busy" v={`${tp.pipelined_per_day.toFixed(2)} a day, ${Math.round(tp.pipelined_per_year)} a year`} />
        <Row k="Units to pay back the line" v={Math.ceil(be.units_to_recover_capex).toLocaleString()} />
        <Row k="Units to cover a year's fixed costs" v={Math.ceil(be.units_to_cover_annual_fixed).toLocaleString()} />
        <table className="w-full text-[11px] num mt-1">
          <thead><tr className="muted text-left"><th>Lines</th><th>A year</th><th>Revenue</th><th>Gross profit</th></tr></thead>
          <tbody>{scale.map((x) => <tr key={x.lines}><td>{x.lines}</td><td>{Math.round(x.units_per_year)}</td><td>{usd(x.revenue)}</td><td>{usd(x.gross_profit)}</td></tr>)}</tbody>
        </table>
      </div>
      {pv.solar_panels > 0 && (
        <div>
          <Head>What the owner gets</Head>
          <Row k="Solar" v={`${pv.solar_panels} panels, ${pv.solar_kw.toFixed(1)} kW, ${pv.daily_generation_kwh.toFixed(1)} kWh a day`} />
          <Row k="Against the daily load" v={`${pv.net_daily_kwh >= 0 ? "+" : ""}${pv.net_daily_kwh.toFixed(1)} kWh`} />
          <Row k="Battery" v={`${pv.battery_kwh} kWh, ${pv.autonomy_days.toFixed(1)} days`} />
          <Row k="Wall rating" v={`R-${pv.r_value.toFixed(0)}`} />
          <Row k="Embodied carbon" v={`${Math.round(pv.embodied_carbon_kg).toLocaleString()} kg`} />
        </div>
      )}
      <div>
        <Head>Against {String(a.benchmark_name).toLowerCase()}</Head>
        <Row k="Price" v={`${usd(econ.price)} vs ${usd(Number(a.benchmark_price))}`} />
        <Row k="Materials" v={`${usd(materialCost(line))} vs ${usd(Number(a.benchmark_material_cost))}`} />
        <Row k="Labor" v={`${(laborMinutes(line) / 60).toFixed(0)} h vs ${a.benchmark_labor_hours} h`} />
      </div>
      <details className="text-xs"><summary className="cursor-pointer font-semibold">Every assumption the line rests on</summary>
        <p className="muted mt-1">al_build&rsquo;s editable block: estimates, not measurements. The crew and wage dials above change two of them.</p>
        {Object.entries(data.assumptions).filter(([, v]) => typeof v === "number").map(([k, v]) => <Row key={k} k={k.replace(/_/g, " ")} v={String(k === "workers_per_station" ? crew : k === "burdened_wage_per_hour" ? wage : v)} />)}
      </details>
      <p className="text-[11px] muted leading-snug">
        Every element, cost and minute is <code>al_build</code>&rsquo;s; the sums are re-run here and checked against it. A unit runs through the stations in order; every station busy is the line at full stride.
      </p>
    </div>
  );
}
