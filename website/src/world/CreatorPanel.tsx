// The Dome Creator space's controls. In the control panel's tab: the standard way in -- one of the
// desktop Creator's twelve presets, then the few choices that matter most, and the bill. In
// fullscreen: the whole studio, every page of the desktop Creator's operations suite (Dome,
// Rooms, Panel Lab, File) and more -- the wedge struts split 1/4, 1/8 or 1/16 with their bark in,
// out or alternating, wedge-cut panels split 1/16 to 1/64, a brush to paint panels one by one on
// the dome itself, three cladding layers, a floor plan for rooms, walls, props, wiring and
// plumbing, the bill of materials, and saving designs (including in the desktop Creator's own
// format). Every figure is creator.ts's, which is DomeModel.stats() line for line.

import { useEffect, useMemo, useState } from "react";
import CreatorFloor from "./CreatorFloor";
import { DEFAULTS, T, customExtras, design, fromDesktop, panelTypes, sectionLabel, toDesktop, type Config, type Design } from "./creator";
import { STAGE_RADIUS_FT, drawDesign } from "./creatorView";
import type { ToolProps } from "./tools";
import { Choice, Dial, Head, Row, Select, Stepper, Tabs, download } from "./tools/ui";

const FT = 3.280839895;
const usd = (x: number) => `$${Math.round(x).toLocaleString()}`;
const kg = (x: number) => `${Math.round(x).toLocaleString()} kg`;
const m2 = (x: number) => `${x.toFixed(1)} m² (${Math.round(x * FT * FT).toLocaleString()} ft²)`;
const m = (x: number) => `${x.toFixed(2)} m (${(x * FT).toFixed(1)} ft)`;
const inch = (x: number) => `${(x * 39.3701).toFixed(1)} in`;
const SAVED = "zl.creator.designs.v1";

type Tab = "design" | "frame" | "panels" | "layers" | "floor" | "lab" | "bill" | "file";

function loadSaved(): { name: string; at: string; config: Config }[] {
  try { return JSON.parse(localStorage.getItem(SAVED) || "[]"); } catch { return []; }
}

/** DomeModel.bom_text, for a file the visitor can keep. */
function bomText(d: Design): string {
  const c = d.config, L: string[] = [], add = (s: string) => L.push(s), bar = (t: string) => add(`-- ${t} ${"-".repeat(Math.max(0, 58 - t.length))}`);
  add("=".repeat(62)); add("GEODESIC DOME — BILL OF MATERIALS (Zeanah Lab Dome Creator)"); add("=".repeat(62));
  add(`Frequency:        ${c.frequency}V (flat-base class I)`); add(`Radius:           ${c.radius.toFixed(2)} m`);
  add(`Height:           ${d.height.toFixed(2)} m`); add(`Floor area:       ${d.floorArea.toFixed(1)} m^2`); add(`Surface area:     ${d.surfaceArea.toFixed(1)} m^2`); add("");
  bar("FRAME"); add(`Material:         ${c.frameMaterial}`); add(`Strut profile:    ${c.strutShape}, ${(c.strutWidth * 100).toFixed(1)} cm wide`);
  add(`Frame style:      ${c.frameStyle}`); add(`Struts:           ${d.strutCount} pcs, ${d.strutTotalLen.toFixed(1)} m total`);
  for (const s of d.strutClasses) add(`   ${s.name}: ${String(s.count).padStart(3)} x ${s.length.toFixed(2)} m`);
  if (d.treesRequired) add(`Trees to harvest: ${d.treesRequired} logs (${d.wedgeSplits} wedges each, ${(d.wedgeLogDiameter * 39.3701).toFixed(1)} in across; bark ${(c.wedgeOrientation ?? "Inside").toLowerCase()})`);
  if (d.trunkStockCount) add(`Tree trunks:      ${d.trunkStockCount} x ${(c.trunkStockLength ?? 0).toFixed(2)} m stock`);
  add(d.boltCount ? `Edge bolts:       ${d.boltCount} pcs (hubless joins)` : `Hubs:             ${d.hubCount} pcs (${c.hubStyle})`);
  add(`Frame weight:     ${d.frameWeight.toFixed(1)} kg (+ hubs ${d.hubWeight.toFixed(1)} kg)`);
  add(`Frame cost:       ${usd(d.frameCost)} (+ hubs ${usd(d.hubCost)})`); add("");
  bar("PANELS");
  for (const p of d.panelRows) add(`   ${p.name.padEnd(18)} ${String(p.count).padStart(3)} pcs  ${p.area.toFixed(1).padStart(7)} m^2  ${p.weight.toFixed(1).padStart(8)} kg  ${usd(p.cost)}`);
  if (d.solarWatts > 0) add(`   Solar capacity:  ${(d.solarWatts / 1000).toFixed(2)} kW`);
  for (const r of d.wedgePanelRows) add(`   ${r.name} stock: ${Math.round(r.wedgeFt).toLocaleString()} ft of wedges, ${Math.round(r.logFt).toLocaleString()} ft of ${r.logIn} in log (${Math.round(r.recovery * 100)}% of the log is panel)`);
  add(""); bar("CLADDING LAYERS");
  if (d.layerRows.length) for (const l of d.layerRows) add(`   ${l.name.padEnd(18)} ${l.area.toFixed(1).padStart(7)} m^2  ${l.weight.toFixed(1).padStart(8)} kg  ${usd(l.cost)}`); else add("   (none)");
  add(""); bar("FOUNDATION"); add(`   ${c.foundation.padEnd(18)} ${d.foundationArea.toFixed(1).padStart(7)} m^2  ${d.foundationWeight.toFixed(1).padStart(8)} kg  ${usd(d.foundationCost)}`);
  add(""); bar("WORKSHOP FIT-OUT");
  (c.sections ?? []).forEach((name, i) => { if (name !== "Unassigned") add(`   ${sectionLabel(i).padEnd(14)} ${name}`); });
  if (d.walls.length) add(`   Partitions: ${d.walls.length} walls, ${d.wallArea.toFixed(1)} m^2, ${usd(d.wallCost)}`);
  for (const p of d.propRows) add(`   ${p.name.padEnd(20)} x${p.count}  ${usd(p.cost)}`);
  if (d.wireRuns.length) add(`   Wiring: ${d.wireLen.toFixed(1)} m, ${usd(d.wireCost)}`);
  if (d.pipeRuns.length) add(`   Plumbing: ${d.pexLen.toFixed(1)} m PEX, ${d.drainLen.toFixed(1)} m drain, ${usd(d.plumbingCost)}`);
  add(""); add("=".repeat(62)); add(`STRUCTURE WEIGHT: ${d.structureWeight.toFixed(0)} kg`); add(`TOTAL COST:       ${usd(d.totalCost)}`); add("=".repeat(62));
  return L.join("\n");
}

export default function CreatorPanel({ world, colour, studio }: ToolProps) {
  const [c, setC] = useState<Config>(() => ({ ...DEFAULTS }));
  const [tab, setTab] = useState<Tab>("design");
  const [brush, setBrush] = useState("Glass Window");
  const [explode, setExplode] = useState(0);
  const [hideLayers, setHideLayers] = useState(false);
  const [preset, setPreset] = useState("");
  const [lab, setLab] = useState<{ base: string; qty: Record<string, number> }>({ base: "Plywood", qty: {} });
  const [saved, setSaved] = useState(loadSaved);
  const [msg, setMsg] = useState<string | null>(null);
  const d = useMemo(() => design(c), [c]);
  const set = (patch: Partial<Config>) => setC((x) => ({ ...x, ...patch }));
  const painting = Boolean(studio && tab === "panels");

  useEffect(() => {
    world.current?.setModel(drawDesign(d, { layers: !(painting && hideLayers), explode, fitout: !painting || !hideLayers, paint: painting }));
    // the world's quests hear what the Creator shows (The Twenty Faces asks for a 3V dome)
    window.dispatchEvent(new CustomEvent("dome-creator-design", { detail: { frequency: c.frequency } }));
  }, [d, world, painting, hideLayers, explode]); // eslint-disable-line react-hooks/exhaustive-deps
  // the world is made after this panel mounts; draw again once it exists
  useEffect(() => { const t = window.setTimeout(() => world.current?.setModel(drawDesign(design(c))), 50); return () => window.clearTimeout(t); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // the studio's brush: clicking a panel on the dome (the world's Inspect) paints it
  useEffect(() => {
    const on = (e: Event) => {
      const part = (e as CustomEvent<{ id: string }>).detail;
      if (!studio || !part?.id) return;
      if (part.id.startsWith("panel:") && tab === "panels") {
        const i = Number(part.id.slice(6)), key = d.panelKeys[i];
        setC((x) => ({ ...x, panelOverrides: { ...(x.panelOverrides ?? {}), [key]: brush } }));
      } else if (part.id.startsWith("section:")) setTab("floor");
    };
    window.addEventListener("portal-part", on);
    return () => window.removeEventListener("portal-part", on);
  }, [studio, tab, brush, d.panelKeys]);

  const dials = T.dials as Record<string, { values: number[] }>;
  const hubless = c.frameStyle === "Hubless Doubled";
  const shape = T.strutShapes.find((s) => s.name === c.strutShape);
  const wedge = shape?.kind === "wedge";
  const types = panelTypes(c);
  const applyPreset = (name: string) => {
    const p = T.presets.find((x) => x.name === name);
    if (!p) return;
    setPreset(name);
    setC({ ...DEFAULTS, ...(p.config as Config), customPanels: {} });
  };

  const summary = (
    <div>
      <Head>The dome</Head>
      <Row k="Across, tall" v={`${m(c.radius * 2)}, ${m(d.height)}`} />
      <Row k="Floor" v={m2(d.floorArea)} />
      <Row k="Struts" v={`${d.strutCount} in ${d.strutClasses.length} lengths`} />
      {wedge && <Row k={`Trees, ${d.wedgeSplits} wedges each`} v={`${d.treesRequired} logs, ${inch(d.wedgeLogDiameter)} across`} />}
      <Row k="Weight" v={kg(d.structureWeight)} />
      <div className="flex justify-between gap-2 pt-1 text-sm"><span className="font-semibold">Total</span><span className="num font-bold" style={{ color: colour }}>{usd(d.totalCost)}</span></div>
    </div>
  );

  const frameControls = (
    <div className="grid gap-2">
      <div className="grid grid-cols-2 gap-2">
        <Select label="Frame style" value={c.frameStyle} options={T.frameStyles} onChange={(v) => set({ frameStyle: v })} />
        <Select label="Hub style" value={c.hubStyle} options={T.hubStyles} onChange={(v) => set({ hubStyle: v })} disabled={hubless} />
        <Select label="Strut shape" value={c.strutShape} options={T.strutShapes.map((s) => [s.name, s.kind === "wedge" ? `${s.name} (1/${s.splits} of a log)` : s.name])} onChange={(v) => set({ strutShape: v })} />
        <Select label="Frame material" value={c.frameMaterial} options={T.frameMaterials.map((x) => x.name)} onChange={(v) => set({ frameMaterial: v })} />
      </div>
      {wedge && <Choice label="Which way the bark faces" value={c.wedgeOrientation ?? "Inside"} colour={colour} options={T.wedgeOrientations.map((o) => [o, o === "Alternating" ? `Alternating (${hubless ? "panel by panel" : "strut by strut"})` : o])} onChange={(v) => set({ wedgeOrientation: v })} />}
      <Dial label="Strut width" values={dials["Strut width"].values} value={c.strutWidth} onChange={(v) => set({ strutWidth: v })} show={(v) => `${(v * 100).toFixed(1)} cm (${inch(v)})`} />
    </div>
  );

  // ---------------------------------------------------------------- the tab: presets and the standard choices
  if (!studio) {
    return (
      <div className="grid gap-3">
        <div>
          <p className="text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: colour }}>Dome Creator</p>
          <Select label="Start from a preset" value={preset} options={[["", "Choose one of the twelve..."], ...T.presets.map((p) => p.name)]} onChange={applyPreset} />
        </div>
        <div className="flex gap-1" role="group" aria-label="Frequency">
          {T.frequencies.map((f) => (
            <button key={f} className={`btn-ghost !py-1 !px-2.5 text-sm ${c.frequency === f ? "font-semibold" : "muted"}`}
              style={c.frequency === f ? { borderColor: colour, color: colour } : undefined} onClick={() => set({ frequency: f })}>{f}V</button>
          ))}
        </div>
        <Dial label="Radius" values={dials["Radius"].values} value={c.radius} onChange={(v) => set({ radius: v })} show={(v) => `${v.toFixed(1)} m (${(v * FT).toFixed(1)} ft)`} />
        <div className="grid grid-cols-2 gap-2">
          <Select label="Struts" value={c.strutShape} options={T.strutShapes.map((s) => s.name)} onChange={(v) => set({ strutShape: v })} />
          <Select label="Panels" value={c.panel} options={T.panels.map((x) => x.name)} onChange={(v) => set({ panel: v, panelOverrides: {} })} />
        </div>
        {wedge && <Choice label="Bark faces" value={c.wedgeOrientation ?? "Inside"} colour={colour} options={T.wedgeOrientations.map((o) => [o, o])} onChange={(v) => set({ wedgeOrientation: v })} />}
        {summary}
        <p className="text-[11px] muted leading-snug">Fullscreen opens the whole studio: wedge splits, painting panels one by one, cladding layers, the floor plan, the Panel Lab, the full bill and saving your design.</p>
      </div>
    );
  }

  // ---------------------------------------------------------------- fullscreen: the studio
  const labDef = { base: lab.base, components: Object.fromEntries(Object.entries(lab.qty).filter(([, n]) => n > 0)) };
  const labX = customExtras(labDef);
  return (
    <div className="grid gap-3">
      <div className="flex items-baseline justify-between gap-2">
        <p className="text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: colour }}>Dome Creator studio</p>
        <span className="num text-sm font-bold" style={{ color: colour }}>{usd(d.totalCost)} &middot; {kg(d.structureWeight)}</span>
      </div>
      <Tabs value={tab} onChange={setTab} colour={colour} tabs={[["design", "Design"], ["frame", "Frame"], ["panels", "Panels"], ["layers", "Layers"], ["floor", "Floor plan"], ["lab", "Panel Lab"], ["bill", "Bill"], ["file", "File"]]} />
      {msg && <p className="text-xs panel-2 p-2" role="status">{msg}</p>}

      {tab === "design" && (
        <div className="grid gap-2">
          <Select label="Start from a preset (replaces this design)" value={preset} options={[["", "Choose..."], ...T.presets.map((p) => p.name)]} onChange={applyPreset} />
          <Head>Structure</Head>
          <Choice label="Frequency" value={String(c.frequency)} colour={colour} options={T.frequencies.map((f) => [String(f), `${f}V`])} onChange={(v) => set({ frequency: Number(v), panelOverrides: {} })} />
          <Dial label="Radius" values={dials["Radius"].values} value={c.radius} onChange={(v) => set({ radius: v })} show={(v) => `${v.toFixed(1)} m (${(v * FT).toFixed(1)} ft)`} />
          <Head>Site</Head>
          <div className="grid grid-cols-2 gap-2">
            <Select label="Foundation" value={c.foundation} options={T.foundations.map((x) => x.name)} onChange={(v) => set({ foundation: v })} />
            <Select label="Frame colour" value={c.frameColor ?? "Material"} options={T.frameColors.map((x) => x.name)} onChange={(v) => set({ frameColor: v })} />
          </div>
          <Dial label="Foundation size" values={dials["Foundation size"].values} value={c.foundationScale} onChange={(v) => set({ foundationScale: v })} show={(v) => `${v.toFixed(2)} x radius`} />
          {d.note && <p className="text-xs panel-2 p-2" style={{ borderColor: colour }}>{d.note}</p>}
          {summary}
          <Row k="Drawn on the stage at" v={`1:${((c.radius * FT) / STAGE_RADIUS_FT).toFixed(1)} of the walker's size`} />
        </div>
      )}

      {tab === "frame" && (
        <div className="grid gap-2">
          {frameControls}
          {wedge && (
            <div className="panel-2 p-2 grid gap-0.5">
              <Head>The wedges</Head>
              <Row k="Each strut" v={`1/${d.wedgeSplits} of a log, its bark chord the strut's width`} />
              <Row k="Log it is split from" v={inch(d.wedgeLogDiameter)} />
              <Row k="Logs to harvest" v={`${d.treesRequired} (${d.strutCount} struts, ${d.wedgeSplits} to a log)`} />
              <Row k="Bark" v={c.wedgeOrientation === "Alternating" ? `alternating, ${d.wedgeFlips.filter(Boolean).length} of ${d.wedgeFlips.length} ${hubless ? "panels" : "struts"} out` : (c.wedgeOrientation ?? "Inside").toLowerCase()} />
              <p className="text-[11px] muted mt-1">A finer split of the same width needs a fatter log: the bark chord of a 1/n sector is 2r sin(180/n). Alternating puts an in-wedge beside an out-wedge, the build the raw-wedge solver uses so the sawn faces at a seam cancel; see the 3D Wedge Method for its seam angles.</p>
            </div>
          )}
          {c.strutShape === T.trunkStock.shape && (
            <Dial label="Trunk stock length" values={Array.from({ length: Math.round(T.trunkStock.max / T.trunkStock.step) + 1 }, (_, i) => +(i * T.trunkStock.step).toFixed(4))}
              value={c.trunkStockLength ?? 0} onChange={(v) => set({ trunkStockLength: v })} show={(v) => (v <= 0 ? "off" : `${(v * FT).toFixed(0)} ft`)} />
          )}
          {d.trunkStockCount > 0 && <Row k="Trunks to buy" v={`${d.trunkStockCount}${d.trunkTooShort ? ` -- the longest strut, ${d.trunkLongest.toFixed(2)} m, is longer than the stock` : ""}`} />}
          <Head>Cut list: {d.strutCount} struts, {d.strutClasses.length} lengths</Head>
          <div className="grid grid-cols-3 gap-x-2 text-xs num">
            {d.strutClasses.map((s) => <span key={s.name}><b style={{ color: colour }}>{s.name}</b> {s.count} x {s.length.toFixed(2)} m</span>)}
          </div>
          <Row k="Strut stock" v={`${d.strutTotalLen.toFixed(1)} m`} />
          {hubless ? <Row k="Through-bolts" v={d.boltCount} /> : <Row k="Hubs" v={d.hubCount} />}
          <Row k="Frame" v={`${kg(d.frameWeight)} -- ${usd(d.frameCost)}`} />
          <Row k={hubless ? "Bolts" : "Hubs"} v={`${kg(d.hubWeight)} -- ${usd(d.hubCost)}`} />
        </div>
      )}

      {tab === "panels" && (
        <div className="grid gap-2">
          <div className="grid grid-cols-2 gap-2">
            <Select label="Every panel (resets the painting)" value={c.panel} options={types.map((x) => x.name)} onChange={(v) => set({ panel: v, panelOverrides: {} })} />
            <Select label="Brush: click a panel on the dome" value={brush} options={types.map((x) => x.name)} onChange={setBrush} />
            <Select label="Panel colour" value={c.panelColor ?? "Natural"} options={T.panelColors.map((x) => x.name)} onChange={(v) => set({ panelColor: v })} />
          </div>
          <div className="flex flex-wrap gap-1">
            <button className="btn-ghost !py-1 text-xs" onClick={() => set({ panelOverrides: Object.fromEntries(d.panelKeys.map((k2, i) => [k2, i % 2 ? brush : c.panel])) })}>Brush every other panel</button>
            <button className="btn-ghost !py-1 text-xs" onClick={() => set({ panelOverrides: Object.fromEntries(d.panelKeys.map((k2) => [k2, brush])) })}>Brush them all</button>
            <button className="btn-ghost !py-1 text-xs" onClick={() => set({ panelOverrides: {} })}>Clear the painting</button>
            <label className="text-xs flex items-center gap-1"><input type="checkbox" checked={hideLayers} onChange={(e) => setHideLayers(e.target.checked)} />Hide layers and floor while painting</label>
          </div>
          <p className="text-[11px] muted">Walk round the dome and click a panel to paint it with the brush. {Object.keys(c.panelOverrides ?? {}).length} painted.</p>
          <Head>Panels: {d.panelCount}</Head>
          {d.panelRows.map((p) => <Row key={p.name} k={`${p.name} x${p.count}`} v={`${p.area.toFixed(1)} m², ${kg(p.weight)}, ${usd(p.cost)}`} />)}
          {d.solarWatts > 0 && <Row k="Solar" v={`${Math.round(d.solarWatts).toLocaleString()} W`} />}
          {d.wedgePanelRows.length > 0 && (
            <div className="panel-2 p-2 grid gap-0.5">
              <Head>Wedge-cut panels</Head>
              {d.wedgePanelRows.map((r) => (
                <div key={r.name}>
                  <Row k={`${r.name}: wedges laid`} v={`${Math.round(r.wedgeFt).toLocaleString()} ft`} />
                  <Row k={`${r.name}: log split for them`} v={`${Math.round(r.logFt).toLocaleString()} ft of ${r.logIn} in log`} />
                  <Row k={`${r.name}: log that ends up in the panel`} v={`${Math.round(r.recovery * 100)}% (the rest is ${r.kerfIn} in kerf)`} />
                </div>
              ))}
              <p className="text-[11px] muted mt-1">Wedges side by side, points alternating and nested solid, cut down to the frame's thickness (the Triangle Infill method). A finer split weighs the same -- it is the same slab of wood -- but it takes more, narrower pieces, and more of the log goes to sawdust. Full engagement is a planning assumption, not a measured joint.</p>
            </div>
          )}
        </div>
      )}

      {tab === "layers" && (
        <div className="grid gap-2">
          {[0, 1, 2].map((i) => (
            <Select key={i} label={`Layer ${i + 1}${i === 0 ? " (nearest the panels)" : ""}`} value={(c.layers ?? [])[i] ?? "None"} options={T.layers.map((l) => [l.name, l.name === "None" ? "None" : `${l.name} -- $${l.costPerM2}/m², ${l.areaWeight} kg/m²`])}
              onChange={(v) => { const next = [...(c.layers ?? ["None", "None", "None"])]; next[i] = v; set({ layers: next }); }} />
          ))}
          <Dial label="Pull the layers apart to see the stack" values={[0, 0.02, 0.05, 0.1, 0.2]} value={explode} onChange={setExplode} show={(v) => (v ? `${Math.round(v * 100)} cm` : "together")} />
          {d.layerRows.length ? d.layerRows.map((l) => <Row key={l.name} k={l.name} v={`${l.area.toFixed(1)} m², ${kg(l.weight)}, ${usd(l.cost)}`} />) : <p className="text-xs muted">No cladding: the panels are the weather face.</p>}
          <p className="text-[11px] muted">Each layer covers every panel except the open slots and the windows, as the desktop Creator bills it.</p>
        </div>
      )}

      {tab === "floor" && (
        <div className="grid gap-2">
          <CreatorFloor c={c} d={d} set={set} colour={colour} />
          <Row k="Rooms given" v={`${d.assignedSections} of 10 sections`} />
          <Row k="Partition walls" v={d.walls.length ? `${d.walls.length}, ${d.wallArea.toFixed(1)} m², ${usd(d.wallCost)}` : "none"} />
          <Row k="Props" v={`${d.propCount}, ${kg(d.propWeight)}, ${usd(d.propCost)}${d.propWatts ? `, ${Math.round(d.propWatts).toLocaleString()} W` : ""}`} />
          <Row k="Wiring" v={d.wireRuns.length ? `${d.wireLen.toFixed(1)} m, ${usd(d.wireCost)}` : "none (add a battery bank or charge controller, then outlets)"} />
          <Row k="Plumbing" v={d.pipeRuns.length ? `${d.pexLen.toFixed(1)} m PEX, ${d.drainLen.toFixed(1)} m drain, ${usd(d.plumbingCost)}` : "none"} />
        </div>
      )}

      {tab === "lab" && (
        <div className="grid gap-2">
          <p className="text-xs muted">Compose a panel from a base surface and hardware. The hardware is spread over a nominal {T.panelLab.nominalPanelM2} m² panel, as the desktop Panel Lab does.</p>
          <Select label="Base surface" value={lab.base} options={T.panels.filter((p) => p.name !== "Open").map((p) => p.name)} onChange={(v) => setLab((x) => ({ ...x, base: v }))} />
          <div className="panel-2 p-2">
            {T.panelLab.components.map((comp) => (
              <Stepper key={comp.name} label={comp.name} note={comp.screwsEach ? `(+${comp.screwsEach} screws each)` : undefined} value={lab.qty[comp.name] ?? 0} max={12}
                onChange={(v) => setLab((x) => ({ ...x, qty: { ...x.qty, [comp.name]: v } }))} />
            ))}
          </div>
          <Row k="Per panel" v={`+${usd(labX.cost)}, +${labX.weight.toFixed(1)} kg, ${labX.screws} screws, +${Math.round(labX.minutes)} min`} />
          <button className="btn !py-1.5 text-sm justify-self-start" disabled={!Object.keys(labDef.components).length} onClick={() => {
            const n = Object.keys(c.customPanels ?? {}).length + 1, name = `Custom Mk${n} (${lab.base})`;
            set({ customPanels: { ...(c.customPanels ?? {}), [name]: labDef } });
            setBrush(name); setMsg(`Made ${name}. It is the panel brush now: on the Panels tab, click panels to fit it.`);
          }}>Create the panel</button>
          {Object.entries(c.customPanels ?? {}).map(([name, def]) => (
            <Row key={name} k={name} v={Object.entries(def.components).map(([k2, n]) => `${n} ${k2}`).join(", ")} />
          ))}
          {d.hardwareScrews > 0 && <Row k="Hardware on the dome" v={`${Object.entries(d.hardware).map(([k2, n]) => `${n} ${k2}`).join(", ")}; ${d.hardwareScrews} screws`} />}
        </div>
      )}

      {tab === "bill" && (
        <div className="grid gap-1">
          <Row k="Across / tall / floor" v={`${m(c.radius * 2)} / ${m(d.height)} / ${d.floorArea.toFixed(1)} m²`} />
          <Row k="Surface to close" v={m2(d.surfaceArea)} />
          <Row k="Frame" v={`${kg(d.frameWeight)} -- ${usd(d.frameCost)}`} />
          <Row k={hubless ? "Bolts" : "Hubs"} v={`${kg(d.hubWeight)} -- ${usd(d.hubCost)}`} />
          <Row k="Panels" v={`${kg(d.panelWeight)} -- ${usd(d.panelCost)}`} />
          <Row k="Cladding" v={`${kg(d.layerWeight)} -- ${usd(d.layerCost)}`} />
          <Row k="Foundation" v={d.foundationArea ? `${d.foundationArea.toFixed(1)} m² -- ${usd(d.foundationCost)}` : "none"} />
          <Row k="Walls" v={`${kg(d.wallWeight)} -- ${usd(d.wallCost)}`} />
          <Row k="Props" v={`${kg(d.propWeight)} -- ${usd(d.propCost)}`} />
          <Row k="Wiring and plumbing" v={usd(d.wireCost + d.plumbingCost)} />
          <Row k="Structure" v={kg(d.structureWeight)} />
          <div className="flex justify-between gap-2 pt-1 text-sm"><span className="font-semibold">Total</span><span className="num font-bold" style={{ color: colour }}>{usd(d.totalCost)}</span></div>
          <pre className="text-[10px] leading-tight panel-2 p-2 overflow-x-auto max-h-72">{bomText(d)}</pre>
          <button className="btn-ghost !py-1 text-xs justify-self-start" onClick={() => download("dome_bom.txt", bomText(d), "text/plain")}>Save the bill as a text file</button>
          <p className="text-[11px] muted">Every figure is the desktop Creator's own (DomeModel.stats), checked against it on 240 designs.</p>
        </div>
      )}

      {tab === "file" && (
        <div className="grid gap-2">
          <div className="flex flex-wrap gap-1">
            <button className="btn !py-1 text-xs" onClick={() => {
              const name = window.prompt("A name for this design:", preset || `My dome ${saved.length + 1}`);
              if (!name) return;
              const next = [{ name, at: new Date().toISOString(), config: c }, ...saved.filter((x) => x.name !== name)].slice(0, 30);
              try { localStorage.setItem(SAVED, JSON.stringify(next)); setSaved(next); setMsg(`Saved "${name}" in this browser.`); } catch { setMsg("This browser will not save it; use Download instead."); }
            }}>Save in this browser</button>
            <button className="btn-ghost !py-1 text-xs" onClick={() => download("dome_design.json", JSON.stringify(toDesktop(c), null, 1))}>Download (the desktop Creator's format)</button>
            <label className="btn-ghost !py-1 text-xs cursor-pointer">Open a design file...
              <input type="file" accept=".json,application/json" className="hidden" onChange={async (e) => {
                const f = e.target.files?.[0]; if (!f) return;
                try { setC(fromDesktop(JSON.parse(await f.text()))); setMsg(`Opened ${f.name}.`); } catch { setMsg("That file is not a dome design."); }
              }} /></label>
            <button className="btn-ghost !py-1 text-xs" onClick={() => { setC({ ...DEFAULTS }); setPreset(""); }}>Start again from the defaults</button>
          </div>
          {saved.length > 0 && <Head>Saved in this browser</Head>}
          {saved.map((x) => (
            <div key={x.name} className="flex items-center justify-between gap-2 text-xs border-b py-1" style={{ borderColor: "var(--line)" }}>
              <span><b>{x.name}</b> <span className="muted">{new Date(x.at).toLocaleDateString()}</span></span>
              <span className="flex gap-1">
                <button className="btn-ghost !py-0.5" onClick={() => { setC({ ...DEFAULTS, ...x.config }); setMsg(`Opened "${x.name}".`); }}>Open</button>
                <button className="btn-ghost !py-0.5" onClick={() => { const next = saved.filter((y) => y.name !== x.name); try { localStorage.setItem(SAVED, JSON.stringify(next)); } catch { /* the list still updates */ } setSaved(next); }}>Delete</button>
              </span>
            </div>
          ))}
          <p className="text-[11px] muted">A downloaded design opens in the desktop Creator (dome_creator.py, F9) as well as here.</p>
        </div>
      )}
    </div>
  );
}
