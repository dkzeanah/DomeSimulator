// The 3D Zome space's control panel: the wedge zome tool's choices (the method, the log, the
// panel side, the pinwheel's hand, the wedge's way round), its cut schedule and its stock, solved
// as you change them (zome.ts) and drawn on the stage (zomeView.ts). Click a stick on the stage,
// or a row of the schedule, to pick out every stick of that type.

import { useEffect, useMemo, useState } from "react";
import { ZOME_DEFAULTS, Z, facts, type ZomeConfig } from "./zome";
import { drawZome, fitScale } from "./zomeView";
import type { ToolProps } from "./tools";
import { Check, Choice, Dial, Head, Row } from "./tools/ui";
import type { Part } from "./engine";

const deg = (x: number) => `${x.toFixed(1)}°`;
const lr = (x: number) => `${Math.abs(x).toFixed(1)}° ${x < 0 ? "L" : "R"}`;
// the tool's dial, in whole inches, and the Complete Edition's own panel side among them
const SIDES = (() => { const s = Z.side, out = [ZOME_DEFAULTS.side]; for (let v = s.low; v <= s.high + 1e-9; v += s.step) out.push(v); return out.sort((a, b) => a - b); })();
const LOGS = Z.logs.map((l) => l.log);

export default function ZomePanel({ world, colour }: ToolProps) {
  const [c, setC] = useState<ZomeConfig>(() => ({ ...ZOME_DEFAULTS }));
  const [explode, setExplode] = useState(0);
  const [skin, setSkin] = useState(false);
  const [posts, setPosts] = useState(true);
  const [selected, setSelected] = useState<string | null>(null);
  const f = useMemo(() => facts(c), [c]);
  const set = <K extends keyof ZomeConfig>(k: K, v: ZomeConfig[K]) => { setSelected(null); setC((x) => ({ ...x, [k]: v })); };

  useEffect(() => { world.current?.setModel(drawZome(f.model, f.types, { explode, skin, posts, selected })); }, [f, explode, skin, posts, selected, world]);
  useEffect(() => { const t = window.setTimeout(() => world.current?.setModel(drawZome(f.model, f.types, { explode, skin, posts, selected })), 50); return () => window.clearTimeout(t); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  // "Inspect" on a stick in the world picks out its type here
  useEffect(() => {
    const on = (e: Event) => { const p = (e as CustomEvent<Part>).detail; if (p.id.startsWith("zome:")) setSelected(p.id.slice(5)); };
    window.addEventListener("portal-part", on);
    return () => window.removeEventListener("portal-part", on);
  }, []);

  const wedge = c.method === "wedge";
  const scale = fitScale(f.model);
  const sel = f.types.find((t) => t.name === selected);
  return (
    <div className="grid gap-3">
      <div>
        <p className="text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: colour }}>The wedge zome</p>
        <p className="text-xs muted mt-0.5">A nine-sided zome of rhombus panels, each four sticks in a pinwheel, framed flat on a jig.</p>
      </div>
      <Choice label="Sticks" value={c.method} colour={colour} onChange={(v) => set("method", v)}
        options={[["wedge", "Wedges, back out"], ["square", "Square, from pairs"]]} />
      <Dial label="Log" values={LOGS} value={c.log} onChange={(v) => set("log", v)} show={(v) => `${v.toFixed(1)} in, split ${Z.splits} ways`} />
      <Dial label="Panel side" values={SIDES} value={c.side} onChange={(v) => set("side", v)} show={(v) => `${Number.isInteger(v) ? v.toFixed(0) : v.toFixed(2)} in${Math.abs(v - ZOME_DEFAULTS.side) < 1e-9 ? " (the book's)" : ""}`} />
      <div className="grid grid-cols-2 gap-2">
        <Choice label="Pinwheel" value={c.hand} colour={colour} onChange={(v) => set("hand", v)} options={[["ccw", "Anticlockwise"], ["cw", "Clockwise"]]} />
        {wedge && <Choice label="Wedge's way round" value={c.orient} colour={colour} onChange={(v) => set("orient", v)} options={[["back", "Back out"], ["point", "Point out"]]} />}
      </div>
      {wedge && c.orient === "point" && (
        <p className="text-xs panel-2 p-2" style={{ borderColor: colour }}>Point out is shown so you can see why the method lays the back out: the seams now open on the <b>outside</b>, where the weather is.</p>
      )}
      <Dial label="Open the panels out" values={[0, 2, 4, 6, 9, 12, 18, 24]} value={explode} onChange={setExplode} show={(v) => (v ? `${v} in` : "assembled")} />
      <div className="flex gap-3"><Check label="Skin" value={skin} onChange={setSkin} /><Check label="Rim posts" value={posts} onChange={setPosts} /></div>

      <div>
        <Head>The zome</Head>
        <Row k="Panels" v={`${f.panels} in ${f.rows.length} rows`} />
        <Row k="Across the rim" v={`${f.rim_ft.toFixed(1)} ft`} />
        <Row k="Tall" v={`${f.height_ft.toFixed(1)} ft`} />
        <Row k="Panel side" v={`${f.side.toFixed(2)} in`} />
        <Row k="Seams" v={f.seams} />
        <Row k="Folds" v={`${deg(f.fold_lo)} to ${deg(f.fold_hi)}`} />
        <Row k={wedge && c.orient === "back" ? "Inside V (a channel)" : "Outside V"} v={`${deg(f.gap_lo)} to ${deg(f.gap_hi)}`} />
        <Row k="Stick" v={`${f.stick_w.toFixed(2)} x ${f.stick_h.toFixed(2)} in`} />
        <Row k="Drawn on the stage" v={scale >= 1 ? "full size" : `1:${(1 / scale).toFixed(1)}`} />
      </div>
      {wedge && c.orient === "back" && (
        <p className="text-xs muted leading-snug">
          A wedge&rsquo;s sides lean {deg(f.theta / 2)} from square, so the backs close tight on every outside seam and the inside opens a V of the
          wedge&rsquo;s {deg(f.theta)} point less the fold. Nothing needs a block.
        </p>
      )}

      <div>
        <Head>Cut schedule: {f.types.length} stick types{sel ? `, ${sel.name} picked out` : ""}</Head>
        <p className="text-[11px] muted">Back down on the saw table, the edge it runs along on the fence. Click a row, or a stick on the stage.</p>
        <table className="w-full text-[11px] num mt-1">
          <thead><tr className="muted text-left"><th>Stick</th><th>Row</th><th>No.</th><th>Outside</th><th>Tail</th><th>Head</th></tr></thead>
          <tbody>
            {f.types.map((t) => (
              <tr key={t.name} className="cursor-pointer" style={t.name === selected ? { color: colour, fontWeight: 600 } : undefined}
                onClick={() => setSelected(t.name === selected ? null : t.name)}>
                <td>{t.name}</td><td>{t.row}</td><td>{t.count}</td><td>{t.outer.toFixed(2)}</td>
                <td>{lr(t.tail[0])}, {deg(Math.abs(t.tail[1]))}</td><td>{lr(t.head[0])}, {deg(Math.abs(t.head[1]))}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {sel && <p className="text-[11px] mt-1">Each {sel.name}: edges {sel.lengths.map((x) => x.toFixed(2)).join(", ")} in; longest {sel.longest.toFixed(2)} in.</p>}
      </div>

      <div>
        <Head>The rows</Head>
        <table className="w-full text-[11px] num">
          <thead><tr className="muted text-left"><th>Row</th><th>Panels</th><th>Sharp corner</th><th>Largest fold</th><th>V</th></tr></thead>
          <tbody>{f.rows.map((r) => <tr key={r.row}><td>{r.row}</td><td>{r.panels}</td><td>{deg(r.acute)}</td><td>{deg(r.fold_max)}</td><td>{deg(r.gap_min)}–{deg(r.gap_max)}</td></tr>)}</tbody>
        </table>
      </div>

      <div>
        <Head>What it takes</Head>
        <table className="w-full text-[11px] num">
          <thead><tr className="muted text-left"><th></th><th>This method</th><th>The other</th></tr></thead>
          <tbody>
            <tr><td className="muted">Sticks</td><td>{f.stock.sticks}</td><td>{f.other_stock.sticks}</td></tr>
            <tr><td className="muted">Sticks from one wedge</td><td>{f.stock.sticks_per_wedge}</td><td>{f.other_stock.sticks_per_wedge}</td></tr>
            <tr><td className="muted">Wedges, {Z.section} in long</td><td>{f.stock.wedges}</td><td>{f.other_stock.wedges}</td></tr>
            <tr><td className="muted">Log sections, {Z.splits} ways</td><td>{f.stock.sections}</td><td>{f.other_stock.sections}</td></tr>
          </tbody>
        </table>
        <Row k="Rim" v={`${f.rim_corners} corners, ${f.posts} on posts up to ${f.post_h.toFixed(1)} in`} />
        <Row k="Post" v={`${f.post_square.toFixed(2)} in square, two quarters back to back`} />
      </div>

      {!wedge && (
        <div>
          <Head>Wedge blocks for the outside V</Head>
          <p className="text-[11px] muted">A block&rsquo;s point is 360° over the ways its log is split, so each fold wants a log split 360/fold ways.</p>
          <table className="w-full text-[11px] num">
            <thead><tr className="muted text-left"><th>Fold</th><th>Seams</th><th>Exactly</th><th>Split</th><th>Off by</th></tr></thead>
            <tbody>{f.blocks.map((b) => <tr key={b.fold}><td>{deg(b.fold)}</td><td>{b.count}</td><td>{b.split_exact.toFixed(1)}</td><td>{b.split} ways</td><td>{b.split_error >= 0 ? "+" : ""}{b.split_error.toFixed(1)}°</td></tr>)}</tbody>
          </table>
        </div>
      )}

      <div>
        <Head>What the tool declares</Head>
        {Z.declared.map((d) => <Row key={d.key} k={d.why} v={`${d.value} ${d.unit} (${d.kind})`} />)}
        <Row k="Saw kerf (measured)" v={`${Z.kerf} in`} />
      </div>
      <p className="text-[11px] muted leading-snug">
        Every figure is the desktop wedge zome tool&rsquo;s (<code>wedge_zome.fabrication.facts</code>), solved from its planes here and checked against it on 60 zomes.
        This is a method, not a rated structure: have a licensed engineer check it for wind and snow before anyone lives in it.
      </p>
      <button className="text-xs underline justify-self-start" onClick={() => { setSelected(null); setExplode(0); setC({ ...ZOME_DEFAULTS }); }}>Back to the tool&rsquo;s defaults</button>
    </div>
  );
}
