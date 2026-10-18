// The Panel Creator space's control panel: the Triangle Infill tool's ways to fill a triangle --
// the owner's wedge pairs and the tool's patterns, filling the frame or covering it -- with one
// panel type up close, every piece numbered with its cuts and saw recipe, or the whole dome
// filled. The pieces are the tool's own solids (infillView.ts); the figures are its own (infill.ts).

import { useEffect, useMemo, useState } from "react";
import { P, loadRows, loadTable, wayByKey, type RowsMesh, type WayTable } from "./infill";
import { CLOSE_ENLARGE, drawDome, drawPanel } from "./infillView";
import type { ToolProps } from "./tools";
import { Choice, Head, Row } from "./tools/ui";
import type { Part } from "./engine";

const FAMILIES: [string, string][] = [["pairs", "Wedge pairs"], ["fill", "Patterns in the frame"], ["cover", "Patterns over it"]];
const familyOf = (w: (typeof P.ways)[number]) => (w.family === "pairs" ? "pairs" : w.mode);
const METRICS: [string, string, (v: number) => string][] = [
  ["pieces", "Pieces", (v) => String(v)], ["solid", "Covered", (v) => `${Math.round(v * 100)}%`],
  ["see_through", "Light through", (v) => `${Math.round(v * 100)}%`], ["longest", "Longest piece", (v) => `${v.toFixed(2)} in`],
  ["shortest", "Shortest piece", (v) => `${v.toFixed(2)} in`], ["linear_in", "Stock", (v) => `${(v / 12).toFixed(1)} ft`],
  ["kg", "Weight", (v) => `${v.toFixed(1)} kg`],
];

export default function PanelCreatorPanel({ world, colour }: ToolProps) {
  const [key, setKey] = useState(P.ways[0].key);
  const [view, setView] = useState<"panel" | "dome">("panel");
  const [kind, setKind] = useState(0);
  const [picked, setPicked] = useState<number | null>(null);
  const [frames, setFrames] = useState<RowsMesh | null>(null);
  const [fill, setFill] = useState<{ key: string; m: RowsMesh; t: WayTable } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const w = wayByKey(key);
  const fam = familyOf(w);

  useEffect(() => { loadRows(P.frames).then(setFrames).catch((e) => setError((e as Error).message)); }, []);
  useEffect(() => {
    let live = true;
    setError(null);
    Promise.all([loadRows(w.mesh), loadTable(w)]).then(([m, t]) => live && setFill({ key: w.key, m, t })).catch((e) => live && setError((e as Error).message));
    return () => { live = false; };
  }, [w]);
  useEffect(() => setPicked(null), [key, kind]);

  const ready = fill && fill.key === key ? fill : null;
  const table = ready?.t.kinds[kind] ?? null;
  useEffect(() => {
    if (!frames) return;
    const draw = () => {
      if (view === "panel") world.current?.setModel(drawPanel(kind, frames, ready?.m ?? null, table, picked));
      else world.current?.setModel(drawDome(frames, ready?.m ?? null, ready?.t ?? null).group);
    };
    draw();
    const t = window.setTimeout(draw, 50);
    return () => window.clearTimeout(t);
  }, [frames, ready, view, kind, picked, table, world]);

  useEffect(() => {
    const on = (e: Event) => { const p = (e as CustomEvent<Part>).detail; if (p.id.startsWith("infill:")) setPicked(Number(p.id.slice(7))); };
    window.addEventListener("portal-part", on);
    return () => window.removeEventListener("portal-part", on);
  }, []);

  const ways = useMemo(() => P.ways.filter((x) => familyOf(x) === fam), [fam]);
  const piece = table?.pieces.find((p) => p.n === picked);
  const recipe = table?.recipes.find((r) => r.number === picked);
  const t = P.types[kind];
  return (
    <div className="grid gap-3">
      <div>
        <p className="text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: colour }}>Triangle infill</p>
        <p className="text-xs muted mt-0.5">Fill the dome&rsquo;s triangles with wedges: every piece cut to the opening&rsquo;s walls and flush with the frame.</p>
      </div>
      {error && <p className="text-xs" style={{ color: "#ff8a7a" }}>Could not load the tool&rsquo;s pieces: {error}</p>}
      <Choice label="Family" value={fam} colour={colour} options={FAMILIES as [string, string][]}
        onChange={(f) => setKey(P.ways.find((x) => familyOf(x) === f)!.key)} />
      <label className="grid gap-0.5 text-xs">
        <span className="muted">Way to fill</span>
        <select className="field !py-1 text-sm" value={key} onChange={(e) => setKey(e.target.value)}>
          {ways.map((x) => <option key={x.key} value={x.key}>{x.title}</option>)}
        </select>
      </label>
      <div className="grid grid-cols-2 gap-2">
        <Choice label="Show" value={view} colour={colour} onChange={setView} options={[["panel", "One triangle"], ["dome", "The whole dome"]]} />
        <Choice label="Panel type" value={String(kind)} colour={colour} onChange={(v) => setKind(Number(v))}
          options={P.types.map((x, i) => [String(i), `${x.name}, ${P.counts[i]} on the dome`] as [string, string])} />
      </div>

      <div>
        <Head>The whole dome, {w.title}</Head>
        <Row k="Pieces" v={w.pieces.toLocaleString()} />
        <Row k="Wedge stock" v={`${Math.round(w.feet).toLocaleString()} ft`} />
        <Row k="Covered" v={`${Math.round(w.solid * 100)}%`} />
        {w.leftSqft > 0 && <Row k="Left open" v={`${w.leftSqft.toFixed(1)} ft²`} />}
        {w.planedOff !== null && <Row k="Planing takes off each pair" v={`${Math.round(w.planedOff * 100)}%`} />}
        <Row k="Panels" v={`${P.dome.panels}: ${P.types.map((x, i) => `${P.counts[i]} ${x.name}`).join(", ")}`} />
      </div>

      {view === "panel" && table && (
        <>
          <div>
            <Head>Panel {t.name}: {table.pieces.length} pieces</Head>
            <Row k="Edges" v={t.edgeLen.map((x) => x.toFixed(1)).join(", ") + " in"} />
            {METRICS.filter(([k]) => typeof table.metrics[k] === "number").map(([k, label, fmt]) => <Row key={k} k={label} v={fmt(table.metrics[k] as number)} />)}
            <Row k="Drawn on the stage" v={`${CLOSE_ENLARGE} times full size`} />
          </div>
          <div>
            <Head>Cut list</Head>
            <p className="text-[11px] muted">Click a piece here or on the stage for its saw setup.</p>
            <div className="max-h-48 overflow-y-auto mt-1">
              <table className="w-full text-[11px] num">
                <thead><tr className="muted text-left"><th>No.</th><th>Piece</th><th>Long</th><th>Short</th></tr></thead>
                <tbody>
                  {table.pieces.map((p) => (
                    <tr key={p.n} className="cursor-pointer" style={p.n === picked ? { color: colour, fontWeight: 600 } : undefined} onClick={() => setPicked(p.n === picked ? null : p.n)}>
                      <td>{p.n}</td><td>{p.name}</td><td>{p.long.toFixed(2)}</td><td>{p.short.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          {piece && (
            <div className="panel-2 p-2 text-xs" style={{ borderColor: colour }}>
              <p className="font-semibold">Piece {piece.n}: {piece.name}</p>
              <p className="mt-1">{piece.cuts}</p>
              {piece.note && <p className="muted mt-1">{piece.note}</p>}
              {recipe && (
                <>
                  <p className="mt-2 font-semibold">{recipe.summary}</p>
                  {recipe.dims.map(([k, v]) => <Row key={k} k={k} v={v} />)}
                  <ol className="list-decimal pl-4 mt-1 space-y-1">{recipe.steps.map((s, i) => <li key={i}><b>{s.title}.</b> {s.text}</li>)}</ol>
                </>
              )}
            </div>
          )}
          {table.prep && (
            <details className="text-xs"><summary className="cursor-pointer font-semibold">{table.prep.name}</summary>
              <p className="mt-1">{table.prep.summary}</p>
              <ol className="list-decimal pl-4 mt-1 space-y-1">{table.prep.steps.map((s, i) => <li key={i}><b>{s.title}.</b> {s.text}</li>)}</ol>
            </details>
          )}
          {table.steps.length > 0 && (
            <details className="text-xs"><summary className="cursor-pointer font-semibold">How to build it</summary>
              <ol className="list-decimal pl-4 mt-1 space-y-1">{table.steps.map((s, i) => <li key={i}>{s}</li>)}</ol>
            </details>
          )}
          {table.fitting.length > 0 && (
            <details className="text-xs"><summary className="cursor-pointer font-semibold">Fit notes</summary>
              <ul className="list-disc pl-4 mt-1 space-y-1">{table.fitting.map((s, i) => <li key={i}>{s}</li>)}</ul>
            </details>
          )}
        </>
      )}
      {!ready && !error && <p className="text-xs muted">Loading the tool&rsquo;s pieces...</p>}
      <p className="text-[11px] muted leading-snug">
        Every piece is the Triangle Infill tool&rsquo;s (<code>infill/</code>), meshed by its own mesher and placed on the dome by <code>two_v_demo.infill_dome</code>.
        The dome: {P.spec.longestIn} in longest member, frame split {P.spec.splits} ways from {P.spec.frameLogIn} in logs, {P.spec.thicknessIn.toFixed(2)} in thick.
      </p>
    </div>
  );
}
