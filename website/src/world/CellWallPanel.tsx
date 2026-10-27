// The Cell Wall & Seams space's controls. The cell wall (two_v_demo.cell_wall): the dome's skin as a
// stack of layers, each with its own network -- a local loop round every triangle, global runs
// along the seams -- run alone, both ways, or plugged into each other by the router, whose
// interlocks keep them from fighting. The seam's climate (two_v_demo.seam_climate): the dome's
// sensors into the controller's three questions, its mode and reasons, and where on the dome each
// seam runs. Both drawn on the solver's own dome (cellDome.ts) or in section (cellView.ts).
//
// In the control panel's tab: a situation for the wall and a weather for the seams, and what they
// do. In fullscreen: the studio -- the dome's layers peeled apart, the router with every layer's
// mode, the climate controller with every sensor, the wall in section with its temperatures, every
// function's own computed check, and the network the cells make.

import { useEffect, useMemo, useState } from "react";
import { CW, DEFAULT_STACK, checkScenario, climateConstant, decide, plateSetpoint, profile, type Sensors } from "./climate";
import { WALL_EXAGGERATE, drawSeam, drawWall } from "./cellView";
import { BAND_COLOUR, DOME_EXAGGERATE, drawCellDome } from "./cellDome";
import type { ToolProps } from "./tools";
import { Check, Choice, Dial, Head, Row, Tabs } from "./tools/ui";

const range = (a: number, b: number, step: number) => { const out: number[] = []; for (let v = a; v <= b + 1e-9; v += step) out.push(Math.round(v * 1000) / 1000); return out; };
const TEMPS = range(-20, 50, 1), RHS = range(0.05, 1, 0.05), MCS = range(0.06, 0.3, 0.01);
const near = (vs: number[], v: number) => vs.reduce((a, b) => (Math.abs(b - v) < Math.abs(a - v) ? b : a));
const pct = (x: number) => `${Math.round(x * 100)}%`;
const c1 = (x: number) => `${x.toFixed(1)} °C`;
const rgb = (c: number[]) => `rgb(${c.slice(0, 3).map((x) => Math.round(x * 255)).join(",")})`;
const CHECK = (k: string) => CW.wall.checks.find((c) => c.key === k)!.figures as Record<string, unknown>;

/** A check's figure, read by its name: the module's own suffixes say the unit. */
const UNITS: [RegExp, string][] = [[/(^|_)usd$/, "$"], [/(^|_)pct$/, "%"], [/(^|_)m3$/, " m³"], [/(^|_)m2$/, " m²"], [/(^|_)kg$/, " kg"], [/(^|_)l$/, " L"], [/(^|_)l_day$/, " L/day"], [/(^|_)gal$/, " gal"],
  [/(^|_)gal_day$/, " gal/day"], [/(^|_)gal_year$/, " gal/yr"], [/(^|_)kw$/, " kW"], [/(^|_)w$/, " W"], [/(^|_)kn$/, " kN"], [/(^|_)kpa$/, " kPa"], [/(^|_)tonnes$/, " t"], [/(^|_)m_s$/, " m/s"], [/(^|_)mm_s$/, " mm/s"],
  [/(^|_)m$/, " m"], [/(^|_)ft$/, " ft"], [/(^|_)in2$/, " in²"], [/(^|_)in$/, " in"], [/(^|_)mm$/, " mm"], [/(^|_)min$/, " min"], [/(^|_)s$/, " s"], [/(^|_)h$/, " h"], [/^hours/, " h"], [/(^|_)k$/, " K"], [/(^|_)c$/, " °C"],
  [/(^|_)ghz$/, " GHz"], [/(^|_)mhz$/, " MHz"], [/(^|_)db/, " dB"], [/gpm/, " gal/min"], [/^usd$/, "$"], [/^m3$/, " m³"], [/^bdft$/, " board ft"]];
function figure(key: string, v: unknown): string | null {
  if (typeof v !== "number") return typeof v === "string" ? v : null;
  const unit = UNITS.find(([re]) => re.test(key))?.[1] ?? "";
  const n = Math.abs(v) >= 100 ? Math.round(v).toLocaleString() : Math.abs(v) >= 10 ? v.toFixed(1) : v.toFixed(Number.isInteger(v) ? 0 : 2);
  return unit === "$" ? `$${n}` : `${n}${unit}`;
}
const words = (k: string) => k.replace(/_/g, " ").replace(/\b(usd|pct|m3|m2|kg|l|gal|kw|w|kn|kpa|m s|mm s|in2|mm|min|ghz|mhz|db)\b/g, "").replace(/\s+/g, " ").trim();

type Tab = "dome" | "router" | "climate" | "wall" | "checks" | "network";

export default function CellWallPanel({ world, colour, studio }: ToolProps) {
  const [tab, setTab] = useState<Tab>("dome");
  const first = CW.climate.scenarios[0];
  const [weather, setWeather] = useState<string | null>(first.key);
  const [s, setS] = useState<Sensors>(() => ({ ...first.sensors }));
  const d = useMemo(() => decide(s), [s]);
  const set = <K extends keyof Sensors>(k: K, v: Sensors[K]) => { setWeather(null); setS((x) => ({ ...x, [k]: v })); };

  const [stackName, setStackName] = useState<"drawn" | "owner">("drawn");
  const stack = stackName === "drawn" ? DEFAULT_STACK : [...CW.wall.ownerStack, "core", ...DEFAULT_STACK.filter((k) => !CW.wall.ownerStack.includes(k) && k !== "core")];
  const [tOut, setTOut] = useState(CW.wall.profileInputs.winter_out_c);
  const [situation, setSituation] = useState<string | null>(CW.wall.scenarios[0].key);
  const [modes, setModes] = useState<Record<string, string>>(() => ({ ...(CW.wall.scenarios[0].modes as unknown as Record<string, string>) }));
  const [peel, setPeel] = useState(0.35);
  const [only, setOnly] = useState<string | null>(null);
  const [band, setBand] = useState<string | null>(null);
  const [hops, setHops] = useState(false);
  const [loops, setLoops] = useState(true);
  const [picked, setPicked] = useState<{ id: string; name: string; examine?: string } | null>(null);
  const prof = useMemo(() => profile(stack, tOut), [stack.join(), tOut]); // eslint-disable-line react-hooks/exhaustive-deps
  const temps = useMemo(() => Object.fromEntries(prof.map((p) => [p.layer, p.temp_c])), [prof]);
  const broken = useMemo(() => checkScenario(Object.fromEntries(Object.entries(modes).filter(([, m]) => m !== "off")), tOut), [modes, tOut]);

  // what the stage shows: the dome (most of the time), the wall in section, or the seam in section
  const view = !studio ? "dome" : tab === "wall" ? "wall" : "dome";
  useEffect(() => {
    const draw = () => world.current?.setModel(view === "wall" ? drawWall(stack, modes, temps)
      : drawCellDome({ stack, modes, peel, only: studio && tab === "dome" ? only : null, bands: studio && tab === "climate", band: studio && tab === "climate" ? band : null,
          hops: studio && tab === "network" && hops, seamMode: (studio && tab === "climate") || !studio ? d.mode : null, loops }));
    draw();
    const t = window.setTimeout(draw, 50);
    return () => window.clearTimeout(t);
  }, [view, tab, d.mode, stack.join(), modes, temps, peel, only, band, hops, loops, studio, world]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const on = (e: Event) => {
      const p = (e as CustomEvent<{ id: string; name: string; examine?: string }>).detail;
      if (!p?.id) return;
      if (p.id.startsWith("cell:") || p.id.startsWith("seam:") || p.id.startsWith("port:") || p.id === "tank" || p.id.startsWith("layer:")) setPicked(p);
      if (studio && p.id.startsWith("cell:")) setOnly(p.id.split(":")[1]);
    };
    window.addEventListener("portal-part", on);
    return () => window.removeEventListener("portal-part", on);
  }, [studio]);

  const mode = CW.climate.modes.find((m) => m.key === d.mode)!;
  const w = CW.climate.scenarios.find((x) => x.key === weather);
  const pickSituation = (key: string) => { const x = CW.wall.scenarios.find((y) => y.key === key); if (x) { setSituation(x.key); setModes({ ...(x.modes as unknown as Record<string, string>) }); } };
  const pickWeather = (key: string) => { const x = CW.climate.scenarios.find((y) => y.key === key); if (x) { setWeather(x.key); setS({ ...x.sensors }); } };
  const activeLayers = Object.entries(modes).filter(([, m]) => m !== "off");

  const situationPicker = (
    <label className="grid gap-0.5 text-xs">
      <span className="muted">The wall: a situation</span>
      <select className="field !py-1 text-sm" value={situation ?? ""} onChange={(e) => pickSituation(e.target.value)}>
        {situation === null && <option value="">Your own</option>}
        {CW.wall.scenarios.map((x) => <option key={x.key} value={x.key}>{x.label}</option>)}
      </select>
    </label>
  );
  const weatherPicker = (
    <label className="grid gap-0.5 text-xs">
      <span className="muted">The seams: a weather (the owner&rsquo;s list)</span>
      <select className="field !py-1 text-sm" value={weather ?? ""} onChange={(e) => pickWeather(e.target.value)}>
        {weather === null && <option value="">Your own</option>}
        {CW.climate.scenarios.map((x) => <option key={x.key} value={x.key}>{x.label}</option>)}
      </select>
    </label>
  );
  const interlocks = (
    <div className="panel-2 p-2 text-xs" style={{ borderColor: broken.length ? "#ff8a7a" : colour }}>
      {broken.length ? <><b>Interlocks broken:</b><ul className="list-disc pl-4">{broken.map((b) => <li key={b}>{b}</li>)}</ul></> : <b>Every interlock holds.</b>}
    </div>
  );
  const controller = (
    <div className="panel-2 p-2" style={{ borderColor: colour }}>
      <p className="text-[10px] uppercase tracking-[0.2em] muted">The seam controller says</p>
      <p className="text-lg font-bold" style={{ color: colour }}>{d.mode.replace("_", " ")}</p>
      <p className="text-xs">{mode.path}: {mode.why}.</p>
      <ol className="list-decimal pl-4 mt-1 text-xs space-y-0.5">{d.reasons.map((r, i) => <li key={i}>{r}</li>)}</ol>
      {w && <p className="text-[11px] mt-1">{w.want.includes(d.mode) ? "✓" : "✗"} The owner&rsquo;s table wants {w.want.join(" or ")}: {w.why}.</p>}
    </div>
  );
  const pickedNote = picked && <p className="text-xs panel-2 p-2"><b>{picked.name}</b>{picked.examine ? `: ${picked.examine}` : ""}</p>;

  // ---------------------------------------------------------------- the tab: a situation, a weather, what they do
  if (!studio) {
    const rain = CHECK("rain"), fire = CHECK("fire"), heat = CHECK("heating"), foam = CHECK("foam");
    return (
      <div className="grid gap-3">
        <p className="text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: colour }}>The dome&rsquo;s skin</p>
        {situationPicker}
        <p className="text-xs">On now: {activeLayers.length ? activeLayers.map(([k, m]) => `${CW.wall.layers.find((l) => l.key === k)?.label} (${m})`).join(", ") : "nothing"}.</p>
        {interlocks}
        {weatherPicker}
        {controller}
        {pickedNote}
        <div>
          <Head>What the wall does</Head>
          <Row k="Rain to the tank" v={`${figure("gal_day", rain.gal_day)} (${figure("gal_year", rain.gal_year)})`} />
          <Row k="The sprinkler empties the tank in" v={figure("tank_min", fire.tank_min)} />
          <Row k="Heating it can give, against the loss" v={`${figure("capacity_w", heat.capacity_w)} vs ${figure("loss_w", heat.loss_w)}`} />
          <Row k="Foam to fill the cavity" v={`${figure("m3", foam.m3)}, ${foam.kits} kits, ${figure("usd", foam.usd)}`} />
          <Row k="Layers, cells, seams" v={`${CW.wall.layers.length}, ${CW.wall.networks.triangles} each, ${CW.wall.networks.seams}`} />
        </div>
        <p className="text-[11px] muted leading-snug">Fullscreen opens the studio: peel the layers apart on the dome, set every layer&rsquo;s mode, drive the seam controller sensor by sensor, read the wall in section and every function&rsquo;s own check.</p>
      </div>
    );
  }

  // ---------------------------------------------------------------- fullscreen: the studio
  return (
    <div className="grid gap-3">
      <p className="text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: colour }}>Cell wall studio</p>
      <Tabs value={tab} onChange={setTab} colour={colour} tabs={[["dome", "Dome"], ["router", "Router"], ["climate", "Climate"], ["wall", "Wall"], ["checks", "Checks"], ["network", "Network"]]} />
      {pickedNote}

      {tab === "dome" && (
        <div className="grid gap-2">
          {situationPicker}
          {interlocks}
          <Dial label="Pull the layers apart" values={[0, 0.15, 0.35, 0.6, 1, 1.6]} value={peel} onChange={setPeel} show={(v) => (v ? `${v} ft between layers` : "as built")} />
          <div className="flex flex-wrap gap-3">
            <Check label="Local loops and global runs" value={loops} onChange={setLoops} />
          </div>
          <Head>The layers, room to weather (click one to see it alone)</Head>
          <div className="grid gap-0.5">
            <button className={`text-left text-xs px-1 ${only === null ? "font-semibold" : "muted"}`} onClick={() => setOnly(null)}>All of them</button>
            {stack.map((k) => {
              const l = CW.wall.layers.find((x) => x.key === k)!, m = modes[k] || "off";
              return (
                <button key={k} className="flex items-center justify-between gap-2 text-xs px-1 py-0.5 rounded text-left" style={only === k ? { background: "rgba(255,255,255,.08)", color: colour } : undefined} onClick={() => setOnly(only === k ? null : k)}>
                  <span className="flex items-center gap-1.5"><span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ background: rgb(l.colour) }} />{l.label} <span className="muted">({l.side})</span></span>
                  <span className="num" style={{ color: m !== "off" ? colour : undefined }}>{m}</span>
                </button>
              );
            })}
          </div>
          {only && (() => {
            const l = CW.wall.layers.find((x) => x.key === only)!;
            const checks = CW.wall.checks.filter((c) => c.layer === only);
            return (
              <div className="panel-2 p-2 text-xs">
                <p className="font-semibold">{l.label}</p>
                <p>{l.job}</p>
                <Row k="Medium" v={l.medium} /><Row k="Thickness" v={`${l.thicknessMm.toFixed(0)} mm`} /><Row k="Its modes" v={l.modes.join(", ")} />
                {l.construction.length > 0 && <p className="mt-1 muted">Built: {l.construction.join("; ")}</p>}
                {checks.map((c) => <p key={c.key} className="mt-1"><b>{c.title}:</b> {Object.entries(c.figures).filter(([, v]) => typeof v === "number").slice(0, 4).map(([k, v]) => `${words(k)} ${figure(k, v)}`).join(", ")}</p>)}
              </div>
            );
          })()}
          <p className="text-[11px] muted">Drawn {DOME_EXAGGERATE} times as thick as real on the solver&rsquo;s reference dome. A glowing layer is on: its local loops and global runs carry their flow.</p>
        </div>
      )}

      {tab === "router" && (
        <div className="grid gap-2">
          {situationPicker}
          {interlocks}
          <Head>Every layer, room to weather</Head>
          {stack.map((k) => {
            const l = CW.wall.layers.find((x) => x.key === k)!;
            return (
              <div key={k} className="flex items-center justify-between gap-2 py-0.5 border-b text-xs" style={{ borderColor: "var(--line)" }}>
                <span className="flex items-center gap-1.5 flex-1 min-w-0"><span className="inline-block w-2.5 h-2.5 rounded-sm shrink-0" style={{ background: rgb(l.colour) }} />{l.label}</span>
                <span className="num muted whitespace-nowrap">{temps[k]?.toFixed(1)} °C</span>
                {l.modes.length > 1 ? (
                  <select className="field !py-0 !px-1 text-xs w-[7rem] shrink-0" value={modes[k] || "off"} onChange={(e) => { setSituation(null); setModes((m) => ({ ...m, [k]: e.target.value })); }}>
                    {l.modes.map((m) => <option key={m} value={m}>{m.replace("_", " ")}</option>)}
                  </select>
                ) : <span className="muted w-[7rem] shrink-0">fixed</span>}
              </div>
            );
          })}
          <Head>Which layer may feed which</Head>
          <ul className="text-xs list-disc pl-4 space-y-0.5">{CW.wall.routes.map(([a, b, why]) => <li key={a + b}><b>{a} → {b}</b>: {why}</li>)}</ul>
          <Head>The eight situations</Head>
          <table className="w-full text-[11px]"><tbody>
            {CW.wall.scenarios.map((x) => { const bad = checkScenario(Object.fromEntries(Object.entries(x.modes as unknown as Record<string, string>).filter(([, m]) => m !== "off")), tOut); return (
              <tr key={x.key} className="cursor-pointer" onClick={() => pickSituation(x.key)} style={x.key === situation ? { color: colour } : undefined}>
                <td>{x.label}</td><td className="num muted">{Object.keys(x.modes).length} layers on</td><td>{bad.length ? `✗ ${bad.length}` : "✓"}</td>
              </tr>); })}
          </tbody></table>
        </div>
      )}

      {tab === "climate" && (
        <div className="grid gap-2">
          {weatherPicker}
          {controller}
          <div className="grid grid-cols-2 gap-x-3 gap-y-2">
            <Dial label="Inside" values={TEMPS} value={near(TEMPS, s.t_in)} onChange={(v) => set("t_in", v)} show={c1} />
            <Dial label="Inside humidity" values={RHS} value={near(RHS, s.rh_in)} onChange={(v) => set("rh_in", v)} show={pct} />
            <Dial label="Outside" values={TEMPS} value={near(TEMPS, s.t_out)} onChange={(v) => set("t_out", v)} show={c1} />
            <Dial label="Outside humidity" values={RHS} value={near(RHS, s.rh_out)} onChange={(v) => set("rh_out", v)} show={pct} />
            <Dial label="In the seam" values={TEMPS} value={near(TEMPS, s.t_seam)} onChange={(v) => set("t_seam", v)} show={c1} />
            <Dial label="Seam humidity" values={RHS} value={near(RHS, s.rh_seam)} onChange={(v) => set("rh_seam", v)} show={pct} />
          </div>
          <Dial label="Wood moisture (the meter)" values={MCS} value={near(MCS, s.wood_mc)} onChange={(v) => set("wood_mc", v)} show={pct} />
          <div className="flex flex-wrap gap-3">
            <Check label="Raining" value={s.rain} onChange={(v) => set("rain", v)} />
            <Check label="Harvest the water" value={s.harvest} onChange={(v) => set("harvest", v)} />
            <Check label="Cooling on" value={s.cooling} onChange={(v) => set("cooling", v)} />
          </div>
          <Head>Dew points: which air is actually drier</Head>
          <Row k="Inside" v={c1(d.dp_in)} /><Row k="Outside" v={c1(d.dp_out)} /><Row k="In the seam" v={c1(d.dp_seam)} />
          <Row k="Condensing plate held at" v={c1(plateSetpoint(d.dp_in))} />
          <Head>The dome&rsquo;s seams, by where they run (click one to light it)</Head>
          {CW.climate.bands.map((b) => (
            <button key={b.key} className="flex justify-between gap-2 text-xs py-0.5 border-b text-left" style={{ borderColor: "var(--line)", color: band === b.key ? colour : undefined }} onClick={() => setBand(band === b.key ? null : b.key)}>
              <span><span className="inline-block w-2.5 h-2.5 rounded-sm mr-1.5" style={{ background: BAND_COLOUR[b.key] }} />{b.label}</span>
              <span className="num">{b.seams} seams, {b.slopeDeg.toFixed(1)}°{b.drains ? "" : ", dead level"}</span>
            </button>
          ))}
          <Row k="Rim ports (blue), belt low points (yellow)" v={`${CW.climate.rimPorts}, ${CW.climate.beltLowPoints}`} />
          <Row k="Chimney pull, rim to apex, 10 K warmer inside" v={`${CW.climate.stackPa.toFixed(2)} Pa`} />
          <Head>The owner&rsquo;s weathers, through the controller</Head>
          <table className="w-full text-[11px]"><tbody>{CW.climate.scenarios.map((x) => { const m = decide(x.sensors).mode; return (
            <tr key={x.key} className="cursor-pointer" onClick={() => pickWeather(x.key)} style={x.key === weather ? { color: colour } : undefined}>
              <td>{x.label}</td><td className="num">{m}</td><td>{x.want.includes(m) ? "✓" : "✗"}</td>
            </tr>); })}</tbody></table>
          <p className="text-[11px] muted">Margins the controller uses (assumptions): {climateConstant("dp_margin_k")} K before one air counts as drier; wood kept {climateConstant("wood_margin_k")} K above the dew point; indoor humidity acted on above {pct(climateConstant("rh_high"))}.</p>
        </div>
      )}

      {tab === "wall" && (
        <div className="grid gap-2">
          <Choice label="The stack" value={stackName} colour={colour} onChange={setStackName} options={[["drawn", "As the module draws it"], ["owner", "As the owner first stacked it"]]} />
          <Dial label="Outside (the profile and the freeze rule)" values={TEMPS.filter((t) => t <= 15)} value={near(TEMPS, tOut)} onChange={setTOut} show={c1} />
          <Head>Through the wall, room to weather</Head>
          {prof.map((p) => <Row key={p.layer} k={CW.wall.layers.find((l) => l.key === p.layer)?.label ?? p.layer} v={`${p.temp_c.toFixed(1)} °C, RSI ${p.rsi.toFixed(2)}`} />)}
          <Head>Why the side of the insulation matters</Head>
          <Row k="Heat a room-side heating layer gives the room" v={pct(CW.wall.heatSplit.room.to_room)} />
          <Row k="The same layer outside the frame, under the board" v={pct(CW.wall.heatSplit.osb.to_room)} />
          <Row k="Wall, room side / core / weather side" v={`${CW.wall.skin.room_mm.toFixed(0)} / ${CW.wall.skin.core_mm.toFixed(0)} / ${CW.wall.skin.weather_mm.toFixed(0)} mm`} />
          <Row k="Drawn on the stage" v={`${WALL_EXAGGERATE} times as thick`} />
          <p className="text-[11px] muted">The stage shows the wall in section here; the other tabs show it on the dome.</p>
        </div>
      )}

      {tab === "checks" && (
        <div className="grid gap-2">
          <p className="text-[11px] muted">Every function the wall serves, checked by its own function in two_v_demo.cell_wall. Estimates and assumptions are declared there with their reasons.</p>
          {CW.wall.checks.map((c) => {
            const l = CW.wall.layers.find((x) => x.key === c.layer);
            const rows = Object.entries(c.figures).filter(([, v]) => typeof v === "number" || typeof v === "string");
            return (
              <details key={c.key} className="panel-2 p-2 text-xs" open={c.layer === only}>
                <summary className="cursor-pointer font-semibold">{l && <span className="inline-block w-2.5 h-2.5 rounded-sm mr-1.5" style={{ background: rgb(l.colour) }} />}{c.title}{l ? ` (${l.label})` : ""}</summary>
                {rows.map(([k, v]) => <Row key={k} k={words(k)} v={figure(k, v)} />)}
              </details>
            );
          })}
        </div>
      )}

      {tab === "network" && (() => {
        const ln = CHECK("local_net"), bus = CHECK("bus"), cx = CW.wall.complexity as Record<string, unknown>;
        return (
          <div className="grid gap-2">
            <Check label="Colour the cells by hops from the rim" value={hops} onChange={setHops} />
            <Head>The local net: cell to cell</Head>
            <Row k="Cells, ports, jumpers" v={`${ln.triangles}, ${ln.ports}, ${ln.jumpers}`} />
            <Row k="Rim ports, loops, single points of failure" v={`${ln.rim_ports}, ${ln.loops}, ${ln.single_points}`} />
            <Row k="Farthest cell from the rim, across the dome" v={`${ln.max_hops_from_rim} hops, ${ln.diameter_hops} hops`} />
            <Head>The CAN bus</Head>
            <Row k="Nodes, address bits" v={`${bus.nodes}, ${bus.bits}`} />
            <Row k="Trunk" v={figure("trunk_m", bus.trunk_m)} />
            <Row k="Spare length at 500 k / 125 k" v={`${figure("x_m", bus.spare_500k_m)} / ${figure("x_m", bus.spare_125k_m)}`} />
            <Head>What it costs in valves and joints</Head>
            {Object.entries(cx).filter(([, v]) => typeof v === "number").map(([k, v]) => <Row key={k} k={words(k)} v={(v as number).toLocaleString()} />)}
          </div>
        );
      })()}

      <p className="text-[11px] muted leading-snug">The controller, the dew points, the wall&rsquo;s temperatures and its interlocks are <code>two_v_demo.seam_climate</code> and <code>two_v_demo.cell_wall</code>, re-run here and checked against them; every other figure is theirs, carried unchanged. The weathers are typical conditions, not measurements.</p>
    </div>
  );
}
