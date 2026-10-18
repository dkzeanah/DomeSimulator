// The Dome Creator space's control panel: the desktop tool's own choices and dials, and its bill
// of materials, recomputed as you change them (creator.ts) and drawn on the stage (creatorView.ts).

import { useEffect, useMemo, useState } from "react";
import { DEFAULTS, T, design, type Config } from "./creator";
import { STAGE_RADIUS_FT, drawDesign } from "./creatorView";
import type { ToolProps } from "./tools";

const FT = 3.280839895;
const usd = (x: number) => `$${Math.round(x).toLocaleString()}`;
const kg = (x: number) => `${Math.round(x).toLocaleString()} kg`;
const m2 = (x: number) => `${x.toFixed(1)} m² (${Math.round(x * FT * FT).toLocaleString()} ft²)`;
const m = (x: number) => `${x.toFixed(2)} m (${(x * FT).toFixed(1)} ft)`;

function Select({ label, value, options, onChange, disabled }: { label: string; value: string; options: string[]; onChange: (v: string) => void; disabled?: boolean }) {
  return (
    <label className="grid gap-0.5 text-xs">
      <span className="muted">{label}</span>
      <select className="field !py-1 text-sm" value={value} disabled={disabled} onChange={(e) => onChange(e.target.value)}>
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </label>
  );
}

function Dial({ label, values, value, onChange, show }: { label: string; values: number[]; value: number; onChange: (v: number) => void; show: (v: number) => string }) {
  const i = Math.max(0, values.findIndex((v) => Math.abs(v - value) < 1e-9));
  return (
    <label className="grid gap-0.5 text-xs">
      <span className="flex justify-between"><span className="muted">{label}</span><span className="num font-semibold">{show(values[i])}</span></span>
      <input type="range" min={0} max={values.length - 1} step={1} value={i} onChange={(e) => onChange(values[Number(e.target.value)])} />
    </label>
  );
}

function Row({ k, v }: { k: string; v: React.ReactNode }) {
  return <div className="flex justify-between gap-2 py-0.5 border-b text-xs" style={{ borderColor: "var(--line)" }}><span className="muted">{k}</span><span className="num font-semibold text-right">{v}</span></div>;
}

export default function CreatorPanel({ world, colour }: ToolProps) {
  const [c, setC] = useState<Config>(() => ({ ...DEFAULTS }));
  const d = useMemo(() => design(c), [c]);
  const set = <K extends keyof Config>(k: K, v: Config[K]) => setC((x) => ({ ...x, [k]: v }));
  useEffect(() => { world.current?.setModel(drawDesign(d)); }, [d, world]);
  // the world is made after this panel mounts; draw again once it exists
  useEffect(() => { const t = window.setTimeout(() => world.current?.setModel(drawDesign(design(c))), 50); return () => window.clearTimeout(t); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  const dials = T.dials as Record<string, { values: number[] }>;
  const hubless = c.frameStyle === "Hubless Doubled";
  const wedge = T.strutShapes.find((s) => s.name === c.strutShape)?.kind === "wedge";
  return (
    <div className="grid gap-3">
      <div>
        <p className="text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: colour }}>Dome Creator</p>
        <div className="flex gap-1 mt-1" role="group" aria-label="Frequency">
          {T.frequencies.map((f) => (
            <button key={f} className={`btn-ghost !py-1 !px-2.5 text-sm ${c.frequency === f ? "font-semibold" : "muted"}`}
              style={c.frequency === f ? { borderColor: colour, color: colour } : undefined} onClick={() => set("frequency", f)}>{f}V</button>
          ))}
        </div>
      </div>
      <Dial label="Radius" values={dials["Radius"].values} value={c.radius} onChange={(v) => set("radius", v)} show={(v) => `${v.toFixed(1)} m (${(v * FT).toFixed(1)} ft)`} />
      <div className="grid grid-cols-2 gap-2">
        <Select label="Frame style" value={c.frameStyle} options={T.frameStyles} onChange={(v) => set("frameStyle", v)} />
        <Select label="Hub style" value={c.hubStyle} options={T.hubStyles} onChange={(v) => set("hubStyle", v)} disabled={hubless} />
        <Select label="Strut shape" value={c.strutShape} options={T.strutShapes.map((s) => s.name)} onChange={(v) => set("strutShape", v)} />
        <Select label="Frame material" value={c.frameMaterial} options={T.frameMaterials.map((x) => x.name)} onChange={(v) => set("frameMaterial", v)} />
        <Select label="Panels" value={c.panel} options={T.panels.map((x) => x.name)} onChange={(v) => set("panel", v)} />
        <Select label="Foundation" value={c.foundation} options={T.foundations.map((x) => x.name)} onChange={(v) => set("foundation", v)} />
      </div>
      <Dial label="Strut width" values={dials["Strut width"].values} value={c.strutWidth} onChange={(v) => set("strutWidth", v)} show={(v) => `${(v * 100).toFixed(1)} cm`} />
      <Dial label="Foundation size" values={dials["Foundation size"].values} value={c.foundationScale} onChange={(v) => set("foundationScale", v)} show={(v) => `${v.toFixed(2)} x radius`} />
      {d.note && <p className="text-xs panel-2 p-2" style={{ borderColor: colour }}>{d.note}</p>}

      <div>
        <p className="text-xs font-semibold mt-1">The dome</p>
        <Row k="Across" v={m(c.radius * 2)} />
        <Row k="Tall" v={m(d.height)} />
        <Row k="Floor" v={m2(d.floorArea)} />
        <Row k="Surface to close" v={m2(d.surfaceArea)} />
        <Row k="Drawn on the stage at" v={`1:${((c.radius * FT) / STAGE_RADIUS_FT).toFixed(1)} of the walker's size`} />
      </div>
      <div>
        <p className="text-xs font-semibold">Cut list: {d.strutCount} struts, {d.strutClasses.length} lengths</p>
        <div className="grid grid-cols-3 gap-x-2 text-xs num mt-0.5">
          {d.strutClasses.map((s) => <span key={s.name}><b style={{ color: colour }}>{s.name}</b> {s.count} x {s.length.toFixed(2)} m</span>)}
        </div>
        <Row k="Strut stock" v={`${d.strutTotalLen.toFixed(1)} m`} />
        {hubless ? <Row k="Through-bolts" v={d.boltCount} /> : <Row k="Hubs" v={d.hubCount} />}
        <Row k="Panels" v={`${d.panelCount} x ${c.panel}`} />
        {wedge && <Row k="Trees, four wedges each" v={d.treesRequired} />}
        {d.solarWatts > 0 && <Row k="Solar" v={`${Math.round(d.solarWatts).toLocaleString()} W`} />}
      </div>
      <div>
        <p className="text-xs font-semibold">Weight and cost</p>
        <Row k="Frame" v={`${kg(d.frameWeight)} -- ${usd(d.frameCost)}`} />
        <Row k={hubless ? "Bolts" : "Hubs"} v={`${kg(d.hubWeight)} -- ${usd(d.hubCost)}`} />
        <Row k="Panels" v={`${kg(d.panelWeight)} -- ${usd(d.panelCost)}`} />
        <Row k="Foundation" v={d.foundationArea ? `${d.foundationArea.toFixed(1)} m² -- ${usd(d.foundationCost)}` : "none"} />
        <Row k="Structure" v={kg(d.structureWeight)} />
        <div className="flex justify-between gap-2 pt-1 text-sm"><span className="font-semibold">Total</span><span className="num font-bold" style={{ color: colour }}>{usd(d.totalCost)}</span></div>
      </div>
      <p className="text-[11px] muted leading-snug">
        Every figure is the desktop Dome Creator&rsquo;s (<code>dome_model.DomeModel.stats</code>), from its own tables, and checked against it on 160 designs.
        A bare dome: cladding layers, rooms, wiring and plumbing are not in this space yet.
      </p>
      <button className="text-xs underline justify-self-start" onClick={() => setC({ ...DEFAULTS })}>Back to the Creator&rsquo;s defaults</button>
    </div>
  );
}
