// The wedge calculator: split a log into wedges, or mill it into lumber, and see what each keeps.
//
// Every figure comes from src/generated/wedge-milling.json, written by `npm run facts` from
// two_v_demo/wedge_geometry.py (split_section: the exact section a wedge keeps after its two
// faces each lose half a kerf; lumber_yield: rows of rough-sawn pieces with a kerf between all).
// This page only picks a row and converts square inches to board feet for the length typed.

import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import data from "../generated/wedge-milling.json";
import { useMeta } from "../lib/meta";

interface Wedge { splits: number; recovery: number; wedgeArea: number; setback: number; chord: number; depth: number; cutLength: number; allowed: boolean }
interface Lumber { size: string; t: number; w: number; count: number; recovery: number; pieces: [number, number][] }
interface Row { diameter: number; kerf: number; wedges: Wedge[]; lumber: Lumber[] }
const D = data as unknown as { splits: number[]; fineMinDiameter: number; kerfs: { in: number; label: string }[]; lumberSizes: string[]; boardFootIn3: number; rows: Row[] };

const DIAMETERS = [...new Set(D.rows.map((r) => r.diameter))];
const pct = (x: number) => `${(x * 100).toFixed(1)}%`;
const frac = (n: number) => `1/${n}`;
const inch = (x: number) => `${x.toFixed(2)} in`;

/** One reference line per distinct share, highest first, naming every size that keeps it. */
function refLines(lumber: Lumber[]) {
  const by = new Map<string, { recovery: number; sizes: string[] }>();
  for (const l of lumber) {
    const k = l.recovery.toFixed(3);
    if (!by.has(k)) by.set(k, { recovery: l.recovery, sizes: [] });
    by.get(k)!.sizes.push(l.size);
  }
  return [...by.values()].sort((a, b) => b.recovery - a.recovery).map((r) => ({ recovery: r.recovery, sizes: r.sizes.join(", ") }));
}

function Chart({ row, pick, onPick }: { row: Row; pick: number; onPick: (n: number) => void }) {
  const [hover, setHover] = useState<Wedge | null>(null);
  const W = 640, H = 300, L = 44, B = 34, T = 14, R = 120;
  const bw = (W - L - R) / row.wedges.length;
  const y = (v: number) => T + (1 - v) * (H - T - B);
  return (
    <div className="relative">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Share of the log kept as wood, by split, against lumber milling">
        <defs>
          <pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <rect width="6" height="6" fill="var(--panel-2)" />
            <line x1="0" y1="0" x2="0" y2="6" stroke="var(--accent)" strokeWidth="2" opacity="0.6" />
          </pattern>
        </defs>
        {[0, 0.25, 0.5, 0.75, 1].map((v) => (
          <g key={v}>
            <line x1={L} x2={W - R} y1={y(v)} y2={y(v)} stroke="var(--line)" strokeWidth="1" />
            <text x={L - 6} y={y(v) + 4} textAnchor="end" fontSize="11" fill="var(--muted)">{v * 100}%</text>
          </g>
        ))}
        {row.wedges.map((w, i) => {
          const x = L + i * bw + 4, h = y(0) - y(w.recovery);
          return (
            <g key={w.splits} onMouseEnter={() => setHover(w)} onMouseLeave={() => setHover(null)} onClick={() => onPick(w.splits)} style={{ cursor: "pointer" }}>
              <rect x={L + i * bw} y={T} width={bw} height={H - T - B} fill="transparent" />
              <path d={`M${x},${y(0)} v${-(h - 4)} q0,-4 4,-4 h${bw - 16} q4,0 4,4 v${h - 4} z`}
                fill={w.allowed ? "var(--accent)" : "url(#hatch)"} opacity={w.splits === pick ? 1 : 0.7}
                stroke={w.splits === pick ? "var(--ink)" : "none"} strokeWidth="1.5" />
              <text x={x + (bw - 8) / 2} y={y(w.recovery) - 6} textAnchor="middle" fontSize="11" fill="var(--ink)">{pct(w.recovery)}</text>
              <text x={x + (bw - 8) / 2} y={H - B + 16} textAnchor="middle" fontSize="12" fill="var(--ink)">{frac(w.splits)}</text>
            </g>
          );
        })}
        {(() => { let below = -99; return refLines(row.lumber).map((r) => {
          // sizes that keep the same share share a line; a label steps down when it would touch the one above
          const yy = y(r.recovery), ly = Math.max(yy + 4, below + 13);
          below = ly;
          return (
            <g key={r.sizes}>
              <line x1={L} x2={W - R} y1={yy} y2={yy} stroke="var(--muted)" strokeWidth="2" strokeDasharray="5 4" />
              <text x={W - R + 6} y={ly} fontSize="11" fill="var(--muted)">{r.sizes} {pct(r.recovery)}</text>
            </g>
          );
        }); })()}
        <text x={L} y={H - 4} fontSize="11" fill="var(--muted)">Split into wedges (bars) against sawn into lumber (dashed lines)</text>
      </svg>
      {hover && (
        <div className="absolute top-2 left-14 panel-2 p-2 text-xs pointer-events-none grid gap-0.5">
          <b>{frac(hover.splits)} -- {hover.splits} wedges</b>
          <span>keeps {pct(hover.recovery)} of the log as wood</span>
          <span>each wedge {inch(hover.chord)} wide at the bark, point {inch(hover.setback)} out from the pith</span>
          {!hover.allowed && <span>finer than the {D.fineMinDiameter} in rule allows for this log</span>}
        </div>
      )}
    </div>
  );
}

function Section({ row, splits, lumber, which }: { row: Row; splits: number; lumber: Lumber; which: "wedge" | "lumber" }) {
  const r = row.diameter / 2, pad = 1, s = 100 / (r + pad);
  const k = row.kerf;
  return (
    <svg viewBox="-100 -100 200 200" className="w-full max-w-[260px] mx-auto" role="img"
      aria-label={which === "wedge" ? `${row.diameter} inch log split into ${splits} wedges` : `${row.diameter} inch log sawn into ${lumber.size}`}>
      <circle r={r * s} fill="var(--panel-2)" stroke="var(--muted)" strokeWidth="1" />
      {which === "wedge"
        ? Array.from({ length: splits / 2 }, (_, i) => {
            const a = (Math.PI * 2 * i) / splits + Math.PI / splits;
            return <line key={i} x1={-Math.cos(a) * r * s} y1={-Math.sin(a) * r * s} x2={Math.cos(a) * r * s} y2={Math.sin(a) * r * s}
              stroke="var(--bg)" strokeWidth={Math.max(k * s, 0.6)} />;
          })
        : lumber.pieces.map(([x, yy], i) => (
            <rect key={i} x={x * s} y={-(yy + lumber.t) * s} width={lumber.w * s} height={lumber.t * s} fill="var(--accent)" opacity="0.85" />
          ))}
      {which === "wedge" && <circle r={r * s} fill="none" stroke="var(--accent)" strokeWidth="2.5" />}
    </svg>
  );
}

export default function WedgeCalculator() {
  useMeta("Wedge calculator", "Split a log into wedges or saw it into lumber: what each keeps, from eighths down to sixty-fourths, at your kerf.", "/calculator");
  const [diameter, setDiameter] = useState(20);
  const [kerf, setKerf] = useState(0.25);
  const [lengthFt, setLengthFt] = useState(12);
  const [splits, setSplits] = useState(8);
  const [size, setSize] = useState(D.lumberSizes[0]);
  const row = useMemo(() => D.rows.find((r) => r.diameter === diameter && r.kerf === kerf)!, [diameter, kerf]);
  const area = Math.PI * (diameter / 2) ** 2;
  const bf = (rec: number) => (area * rec * lengthFt * 12) / D.boardFootIn3;
  const pick = row.wedges.find((w) => w.splits === splits)!;
  const lumber = row.lumber.find((l) => l.size === size)!;
  const bestLumber = row.lumber.reduce((a, b) => (b.recovery > a.recovery ? b : a));
  const eighths = row.wedges.find((w) => w.splits === 8)!;
  return (
    <div className="mx-auto max-w-6xl px-4 py-10 grid gap-8">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">Calculator</p>
        <h1 className="text-4xl sm:text-5xl font-bold mt-1">Wedges or lumber?</h1>
        <p className="mt-2 muted max-w-3xl">
          Split a log radially and every piece keeps its round back: the only wood lost is the saw's kerf. Saw it into
          rectangles and the round outside goes too. But every finer split doubles the cutting, so splitting has its own limit.
          Pick a log and a saw.
        </p>
      </div>

      <div className="panel p-4 grid gap-4 sm:grid-cols-4 items-end">
        <label className="grid gap-1 sm:col-span-2">
          <span className="text-sm font-semibold">Log diameter: {diameter} in</span>
          <input type="range" min={DIAMETERS[0]} max={DIAMETERS[DIAMETERS.length - 1]} step={1} value={diameter}
            onChange={(e) => setDiameter(Number(e.target.value))} />
          <span className="text-xs muted">At the small end of the length you are cutting.</span>
        </label>
        <label className="grid gap-1">
          <span className="text-sm font-semibold">Saw kerf</span>
          <select className="field" value={kerf} onChange={(e) => setKerf(Number(e.target.value))}>
            {D.kerfs.map((k) => <option key={k.in} value={k.in}>{k.in} in ({k.label})</option>)}
          </select>
        </label>
        <label className="grid gap-1">
          <span className="text-sm font-semibold">Length (ft)</span>
          <input className="field" type="number" min={1} max={60} value={lengthFt} onChange={(e) => setLengthFt(Math.max(1, Math.min(60, Number(e.target.value) || 1)))} />
        </label>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="panel p-4"><p className="text-xs muted uppercase tracking-wider">Split into eighths</p>
          <p className="text-3xl font-bold">{pct(eighths.recovery)}</p><p className="text-sm muted">{bf(eighths.recovery).toFixed(0)} board ft of wood in {eighths.splits} wedges</p></div>
        <div className="panel p-4"><p className="text-xs muted uppercase tracking-wider">Best lumber ({bestLumber.size})</p>
          <p className="text-3xl font-bold">{pct(bestLumber.recovery)}</p><p className="text-sm muted">{bf(bestLumber.recovery).toFixed(0)} board ft in {bestLumber.count} pieces</p></div>
        <div className="panel p-4"><p className="text-xs muted uppercase tracking-wider">Eighths keep</p>
          <p className="text-3xl font-bold">{(eighths.recovery / bestLumber.recovery).toFixed(2)}x</p><p className="text-sm muted">the wood the best lumber cut keeps</p></div>
      </div>

      <section className="panel p-4 grid gap-2">
        <h2 className="text-2xl font-semibold">How fine to split</h2>
        <Chart row={row} pick={splits} onPick={setSplits} />
        <p className="text-sm muted">
          Each finer split cuts every wedge in two again, so it adds as much saw cut as all the cuts before it, and the kerf
          eats further into the heart: the wedge's point starts further from the pith. Hatched bars, {frac(32)} and finer on a log under
          {D.fineMinDiameter} in, are what the build's rule does not allow. Click a bar to draw it.
        </p>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="panel p-4 grid gap-2">
          <h3 className="font-semibold">Split into {frac(splits)}: {splits} wedges</h3>
          <Section row={row} splits={splits} lumber={lumber} which="wedge" />
          <p className="text-sm">Each wedge {inch(pick.chord)} wide at the bark, {inch(pick.depth)} deep, its point {inch(pick.setback)} out from the pith. {pct(pick.recovery)} kept; {bf(pick.recovery).toFixed(0)} board ft.</p>
        </div>
        <div className="panel p-4 grid gap-2">
          <h3 className="font-semibold flex flex-wrap gap-2 items-center">Sawn into
            <select className="field !w-auto !py-1" value={size} onChange={(e) => setSize(e.target.value)}>
              {D.lumberSizes.map((s) => <option key={s}>{s}</option>)}
            </select>
          </h3>
          <Section row={row} splits={splits} lumber={lumber} which="lumber" />
          <p className="text-sm">{lumber.count} pieces of rough-sawn {lumber.size}. {pct(lumber.recovery)} kept; {bf(lumber.recovery).toFixed(0)} board ft.</p>
        </div>
      </section>

      <section className="panel p-4 overflow-x-auto">
        <h2 className="text-2xl font-semibold mb-2">Every split, this log, this saw</h2>
        <table className="w-full text-sm">
          <thead><tr className="text-left muted"><th className="py-1">Split</th><th>Wedges</th><th>Width at bark</th><th>Depth</th><th>Point starts</th><th>Wood per wedge</th><th>Kept</th><th>Lost to kerf</th><th>Saw cut per ft</th><th>Board ft</th></tr></thead>
          <tbody>
            {row.wedges.map((w) => (
              <tr key={w.splits} className="border-t" style={{ borderColor: "var(--line)", opacity: w.allowed ? 1 : 0.55 }}>
                <td className="py-1 font-semibold">{frac(w.splits)}{!w.allowed && " *"}</td><td>{w.splits}</td><td>{inch(w.chord)}</td><td>{inch(w.depth)}</td>
                <td>{inch(w.setback)}</td><td>{w.wedgeArea.toFixed(2)} sq in</td><td>{pct(w.recovery)}</td><td>{pct(1 - w.recovery)}</td>
                <td>{((w.cutLength * 12) / 144).toFixed(2)} sq ft</td><td>{bf(w.recovery).toFixed(0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="text-xs muted mt-2">
          * Finer than the build allows on a log under {D.fineMinDiameter} in. "Saw cut per ft" is the face area the saw cuts through per foot of log,
          a measure of the work. Neither way deducts bark, sapwood, checks or taper: compare them with each other, not with a mill's tally.
          Kerfs are typical widths; measure your own. Figures: <Link className="underline" to="/build">the build</Link>, computed by two_v_demo/wedge_geometry.py.
        </p>
      </section>
    </div>
  );
}
