// The Cell Wall & Seams space's control panel. The seam's climate: the dome's sensors into the
// controller's three questions (two_v_demo.seam_climate, re-run in climate.ts), its mode and
// reasons, and the air moving that way through the seam on the stage. The cell wall: the layer
// stack (two_v_demo.cell_wall), each layer's mode, the router's interlocks and the winter
// temperature through the wall, as drawn or as the owner first stacked it.

import { useEffect, useMemo, useState } from "react";
import { CW, DEFAULT_STACK, checkScenario, climateConstant, decide, plateSetpoint, profile, type Sensors } from "./climate";
import { WALL_EXAGGERATE, drawSeam, drawWall } from "./cellView";
import type { ToolProps } from "./tools";
import { Check, Choice, Dial, Head, Row } from "./tools/ui";

const range = (a: number, b: number, step: number) => { const out: number[] = []; for (let v = a; v <= b + 1e-9; v += step) out.push(Math.round(v * 1000) / 1000); return out; };
const TEMPS = range(-20, 50, 1), RHS = range(0.05, 1, 0.05), MCS = range(0.06, 0.3, 0.01);
const near = (vs: number[], v: number) => vs.reduce((a, b) => (Math.abs(b - v) < Math.abs(a - v) ? b : a));
const snap = (s: Sensors): Sensors => s;   // weathers set the dials to their exact values; the dials step from there
const pct = (x: number) => `${Math.round(x * 100)}%`;
const c1 = (x: number) => `${x.toFixed(1)} °C`;

export default function CellWallPanel({ world, colour }: ToolProps) {
  const [tab, setTab] = useState<"climate" | "wall">("climate");
  const first = CW.climate.scenarios[0];
  const [weather, setWeather] = useState<string | null>(first.key);
  const [s, setS] = useState<Sensors>(() => snap({ ...first.sensors }));
  const d = useMemo(() => decide(s), [s]);
  const set = <K extends keyof Sensors>(k: K, v: Sensors[K]) => { setWeather(null); setS((x) => ({ ...x, [k]: v })); };

  const [stackName, setStackName] = useState<"drawn" | "owner">("drawn");
  const stack = stackName === "drawn" ? DEFAULT_STACK : [...CW.wall.ownerStack, "core", ...DEFAULT_STACK.filter((k) => !CW.wall.ownerStack.includes(k) && k !== "core")];
  const [tOut, setTOut] = useState(CW.wall.profileInputs.winter_out_c);
  const [situation, setSituation] = useState<string | null>(CW.wall.scenarios[0].key);
  const [modes, setModes] = useState<Record<string, string>>(() => ({ ...(CW.wall.scenarios[0].modes as unknown as Record<string, string>) }));
  const prof = useMemo(() => profile(stack, tOut), [stack.join(), tOut]); // eslint-disable-line react-hooks/exhaustive-deps
  const temps = useMemo(() => Object.fromEntries(prof.map((p) => [p.layer, p.temp_c])), [prof]);
  const broken = useMemo(() => checkScenario(Object.fromEntries(Object.entries(modes).filter(([, m]) => m !== "off")), tOut), [modes, tOut]);

  useEffect(() => {
    const draw = () => world.current?.setModel(tab === "climate" ? drawSeam(d.mode, s.rain) : drawWall(stack, modes, temps));
    draw();
    const t = window.setTimeout(draw, 50);
    return () => window.clearTimeout(t);
  }, [tab, d.mode, s.rain, stack.join(), modes, temps, world]); // eslint-disable-line react-hooks/exhaustive-deps

  const mode = CW.climate.modes.find((m) => m.key === d.mode)!;
  const w = CW.climate.scenarios.find((x) => x.key === weather);
  return (
    <div className="grid gap-3">
      <div>
        <p className="text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: colour }}>The dome&rsquo;s skin</p>
        <Choice value={tab} colour={colour} onChange={setTab} options={[["climate", "The seam's climate"], ["wall", "The cell wall"]]} />
      </div>

      {tab === "climate" ? (
        <>
          <label className="grid gap-0.5 text-xs">
            <span className="muted">A weather (the owner&rsquo;s list)</span>
            <select className="field !py-1 text-sm" value={weather ?? ""} onChange={(e) => { const x = CW.climate.scenarios.find((y) => y.key === e.target.value); if (x) { setWeather(x.key); setS({ ...x.sensors }); } }}>
              {weather === null && <option value="">Your own</option>}
              {CW.climate.scenarios.map((x) => <option key={x.key} value={x.key}>{x.label}</option>)}
            </select>
          </label>
          <div className="panel-2 p-2" style={{ borderColor: colour }}>
            <p className="text-[10px] uppercase tracking-[0.2em] muted">The controller says</p>
            <p className="text-lg font-bold" style={{ color: colour }}>{d.mode.replace("_", " ")}</p>
            <p className="text-xs">{mode.path}: {mode.why}.</p>
            <ol className="list-decimal pl-4 mt-1 text-xs space-y-0.5">{d.reasons.map((r, i) => <li key={i}>{r}</li>)}</ol>
            {w && <p className="text-[11px] mt-1">{w.want.includes(d.mode) ? "✓" : "✗"} The owner&rsquo;s table wants {w.want.join(" or ")}: {w.why}.</p>}
          </div>
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
          <div>
            <Head>Dew points: which air is actually drier</Head>
            <Row k="Inside" v={c1(d.dp_in)} /><Row k="Outside" v={c1(d.dp_out)} /><Row k="In the seam" v={c1(d.dp_seam)} />
            <Row k="Condensing plate held at" v={c1(plateSetpoint(d.dp_in))} />
          </div>
          <div>
            <Head>The owner&rsquo;s weathers, through the controller</Head>
            <table className="w-full text-[11px]">
              <tbody>{CW.climate.scenarios.map((x) => { const m = decide(x.sensors).mode; return (
                <tr key={x.key} className="cursor-pointer" onClick={() => { setWeather(x.key); setS({ ...x.sensors }); }}>
                  <td>{x.label}</td><td className="num">{m}</td><td>{x.want.includes(m) ? "✓" : "✗"}</td>
                </tr>); })}</tbody>
            </table>
          </div>
          <div>
            <Head>The dome&rsquo;s seams, by where they run</Head>
            {CW.climate.bands.map((b) => <Row key={b.key} k={b.label} v={`${b.seams} seams, ${b.slopeDeg.toFixed(1)}°${b.drains ? "" : ", dead level"}`} />)}
            <Row k="Chimney pull, rim to apex, 10 K warmer inside" v={`${CW.climate.stackPa.toFixed(2)} Pa`} />
          </div>
          <p className="text-[11px] muted">Margins the controller uses (assumptions): {climateConstant("dp_margin_k")} K before one air counts as drier; wood kept {climateConstant("wood_margin_k")} K above the dew point; indoor humidity acted on above {pct(climateConstant("rh_high"))}.</p>
        </>
      ) : (
        <>
          <label className="grid gap-0.5 text-xs">
            <span className="muted">A situation</span>
            <select className="field !py-1 text-sm" value={situation ?? ""} onChange={(e) => { const x = CW.wall.scenarios.find((y) => y.key === e.target.value); if (x) { setSituation(x.key); setModes({ ...(x.modes as unknown as Record<string, string>) }); } }}>
              {situation === null && <option value="">Your own</option>}
              {CW.wall.scenarios.map((x) => <option key={x.key} value={x.key}>{x.label}</option>)}
            </select>
          </label>
          <div className="panel-2 p-2 text-xs" style={{ borderColor: broken.length ? "#ff8a7a" : colour }}>
            {broken.length ? <><b>Interlocks broken:</b><ul className="list-disc pl-4">{broken.map((b) => <li key={b}>{b}</li>)}</ul></> : <b>Every interlock holds.</b>}
          </div>
          <div>
            <Head>Every layer, room to weather</Head>
            {stack.map((k) => {
              const l = CW.wall.layers.find((x) => x.key === k)!;
              return (
                <div key={k} className="flex items-center justify-between gap-2 py-0.5 border-b text-xs" style={{ borderColor: "var(--line)" }}>
                  <span className="flex items-center gap-1.5 flex-1 min-w-0"><span className="inline-block w-2.5 h-2.5 rounded-sm shrink-0" style={{ background: `rgb(${l.colour.slice(0, 3).map((c) => Math.round(c * 255)).join(",")})` }} />{l.label}</span>
                  <span className="num muted whitespace-nowrap">{temps[k]?.toFixed(1)} °C</span>
                  {l.modes.length > 1 ? (
                    <select className="field !py-0 !px-1 text-xs w-[6.5rem] shrink-0" value={modes[k] || "off"} onChange={(e) => { setSituation(null); setModes((m) => ({ ...m, [k]: e.target.value })); }}>
                      {l.modes.map((m) => <option key={m} value={m}>{m.replace("_", " ")}</option>)}
                    </select>
                  ) : <span className="muted w-[6.5rem] shrink-0">fixed</span>}
                </div>
              );
            })}
          </div>
          <Choice label="The stack" value={stackName} colour={colour} onChange={setStackName} options={[["drawn", "As the module draws it"], ["owner", "As the owner first stacked it"]]} />
          <Dial label="Outside (the profile and the freeze rule)" values={TEMPS.filter((t) => t <= 15)} value={near(TEMPS, tOut)} onChange={setTOut} show={c1} />
          <div>
            <Head>Why the side of the insulation matters</Head>
            <Row k="Heat a room-side heating layer gives the room" v={pct(CW.wall.heatSplit.room.to_room)} />
            <Row k="The same layer outside the frame, under the board" v={pct(CW.wall.heatSplit.osb.to_room)} />
            <Row k="Wall, room side / core / weather side" v={`${CW.wall.skin.room_mm.toFixed(0)} / ${CW.wall.skin.core_mm.toFixed(0)} / ${CW.wall.skin.weather_mm.toFixed(0)} mm`} />
            <Row k="Valves, one pair per cell" v={CW.wall.complexity.valves_every_cell.toLocaleString()} />
            <Row k="Valves, one pair per band" v={CW.wall.complexity.valves_by_band} />
            <Row k="Drawn on the stage" v={`${WALL_EXAGGERATE} times as thick`} />
          </div>
          <details className="text-xs"><summary className="cursor-pointer font-semibold">Which layer may feed which</summary>
            <ul className="list-disc pl-4 mt-1 space-y-0.5">{CW.wall.routes.map(([a, b, why]) => <li key={a + b}><b>{a} → {b}</b>: {why}</li>)}</ul>
          </details>
        </>
      )}
      <p className="text-[11px] muted leading-snug">
        The controller, the dew points, the wall&rsquo;s temperatures and its interlocks are <code>two_v_demo.seam_climate</code> and <code>two_v_demo.cell_wall</code>, re-run here and checked against them.
        The weathers are typical conditions, not measurements; every judgement is declared in those modules with its reason.
      </p>
    </div>
  );
}
