// The 3D Wedge Method space's controls: the raw-wedge simulator's dome, member by member, in every
// build it solves -- its four uniform wedge orientations and its alternating builds, where panels
// point in and out so the sawn faces at a seam cancel -- and the jig that frames one panel, step by
// step. The stage shows the simulator's own solved meshes (wedgeView.ts); every table is its own
// figures (wedge.ts), and the alternating builds' reading -- bands, walks, every seam's pair and
// what a matched seam costs -- is alternating_build.plan's.
//
// In the control panel's tab: pick a build and read what it takes. In fullscreen: the studio --
// the dome raised band by band, every seam, the bands and rings, all eight builds compared at your
// long edge and trunk, a member's cuts, and the jig.

import { useEffect, useMemo, useState } from "react";
import { W, loadMesh, summary, type MeshBuffers, type MeshHead } from "./wedge";
import { JIG_ENLARGE, drawDome, drawJig } from "./wedgeView";
import type { ToolProps } from "./tools";
import { Check, Choice, Dial, Head, Row, Tabs, ftIn } from "./tools/ui";
import type { Part } from "./engine";

const deg = (x: number | null | undefined) => (x === null || x === undefined ? "--" : `${x.toFixed(2)}°`);
const inch = (x: number) => `${x.toFixed(2)} in`;
const D = W.defaults;

type Pattern = (typeof W.patterns)[number];
type Fam = { type: string; count: number; nominal: number; blankMin: number; blankMax: number; buttSetback: number; seams: number; fold: number | null; gap: number | null; keyBase: number | null };
type Sm = { families: Fam[]; members: number; seams: number; joints: number; nodes: number; panels: number; sphereRadius: number; stockIn: number; volumeFt3: number; dryLb: number; greenLb: number; headOffcutIn: number; logsAtSplits: number; matched?: number; extraDeg?: number; pairs?: Record<string, number> };

/** Every build the simulator solves: the four uniform orientations, then the alternating ones. */
const BUILDS: { key: string; label: string; pattern: Pattern | null }[] = [
  ...W.orientations.map((o) => ({ key: o.key, label: o.label, pattern: null })),
  ...W.patterns.map((p) => ({ key: p.key, label: p.label, pattern: p })),
];
const BANDS = Math.max(...W.patterns[0].panels.map((p) => p.band));
const BAND_OF = W.patterns[0].panels.map((p) => p.band);
const sm = (key: string, L: number, d: number) => summary(key, L, d) as unknown as Sm;

type Tab = "dome" | "seams" | "bands" | "compare" | "member" | "jig";

export default function WedgePanel({ world, colour, studio }: ToolProps) {
  const [tab, setTab] = useState<Tab>("dome");
  const [build, setBuild] = useState(D.orientation);
  const [longEdge, setLongEdge] = useState(D.longEdge);
  const [trunk, setTrunk] = useState(D.trunk);
  const [explode, setExplode] = useState(0);
  const [keys, setKeys] = useState(true);
  const [offcuts, setOffcuts] = useState(false);
  const [tint, setTint] = useState(true);
  const [litMatched, setLitMatched] = useState(true);
  const [maxBand, setMaxBand] = useState(BANDS);
  const [family, setFamily] = useState<"A" | "B" | "both">("both");
  const [picked, setPicked] = useState<Record<string, unknown> | null>(null);
  const [seam, setSeam] = useState<string | null>(null);
  const [seamFilter, setSeamFilter] = useState<"all" | "matched" | "A" | "B">("all");
  const [stage, setStage] = useState(0);
  const [buf, setBuf] = useState<{ file: string; b: MeshBuffers } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [drawnAt, setDrawnAt] = useState(1);

  const b = BUILDS.find((x) => x.key === build) ?? BUILDS[0];
  const pattern = b.pattern;
  const head = (W.meshes as Record<string, MeshHead>)[build];
  const jig = studio && tab === "jig";
  const file = jig ? W.jig.file : head.file;
  useEffect(() => {
    let live = true;
    setError(null);
    loadMesh(jig ? W.jig : head).then((x) => live && setBuf({ file, b: x })).catch((e) => live && setError((e as Error).message));
    return () => { live = false; };
  }, [file]); // eslint-disable-line react-hooks/exhaustive-deps

  const hot = useMemo(() => {
    if (seam) return new Set([seam]);
    if (pattern && litMatched) return new Set(pattern.seams.filter((s) => s.pair !== "in/out").map((s) => s.id));
    return new Set<string>();
  }, [seam, pattern, litMatched]);

  useEffect(() => {
    if (!buf || buf.file !== file) return;
    const draw = () => {
      if (!jig) {
        const { group, scale } = drawDome(head, buf.b, {
          explode, keys, offcuts, family: family === "both" ? null : family, picked: (picked?.id as string) ?? null,
          bandOf: BAND_OF, maxBand: studio ? maxBand : BANDS,
          pointsOf: pattern && tint ? pattern.panels.map((p) => p.points as "in" | "out") : undefined, hot,
        });
        world.current?.setModel(group); setDrawnAt(scale);
      } else world.current?.setModel(drawJig(W.jig, buf.b, stage));
    };
    draw();
    const t = window.setTimeout(draw, 50);              // the world is made after this panel mounts
    return () => window.clearTimeout(t);
  }, [buf, file, jig, explode, keys, offcuts, family, picked, stage, maxBand, tint, hot, studio]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const on = (e: Event) => {
      const p = (e as CustomEvent<Part>).detail;
      if (p.id.startsWith("wedge:")) {
        const id = p.id.slice(6);
        setPicked((head.parts.find((x) => x.kind === "member" && x.id === id) as Record<string, unknown>) ?? null);
        if (studio) setTab("member");
      } else if (p.id.startsWith("key:") && studio) { setSeam(p.id.slice(4)); setTab("seams"); }
    };
    window.addEventListener("portal-part", on);
    return () => window.removeEventListener("portal-part", on);
  }, [head, studio]);
  useEffect(() => { setPicked(null); setSeam(null); }, [build]);

  const s = sm(build, longEdge, trunk);
  const orient = W.orientations.find((x) => x.key === build);
  const atReference = longEdge === D.longEdge && trunk === D.trunk;
  const fam = (t: string) => s.families.find((f) => f.type === t)!;

  const buildPicker = (
    <div className="grid gap-1.5">
      <Choice label="One way everywhere: which way each wedge's point faces" value={pattern ? "" : build} colour={colour} onChange={setBuild}
        options={W.orientations.map((x) => [x.key, x.label] as [string, string])} />
      <Choice label="Alternating: panels in and out, so the sawn faces at a seam cancel" value={pattern ? build : ""} colour={colour} onChange={setBuild}
        options={W.patterns.map((x) => [x.key, x.label.replace("Alternating: ", "")] as [string, string])} />
      <p className="text-xs panel-2 p-2" style={{ borderColor: colour }}>
        {pattern ? <>{pattern.blurb}{pattern.ground !== "auto" ? ` (${pattern.ground} panels in on the ground)` : ""}. Where an in-wedge meets an out-wedge the key fills only the fold; <b>{pattern.matched}</b> seams are matched (in/in) and cost <b>+{pattern.extraDeg.toFixed(2)}°</b> in all against in/out.</>
          : <>At a seam: {orient!.reading}. Each stick&rsquo;s butt bears on its neighbour&rsquo;s <b>{orient!.receiver.replace("_", " ").toLowerCase()}</b> face.</>}
      </p>
    </div>
  );

  const takes = (
    <div>
      <Head>What it takes{atReference ? "" : ` (${longEdge} in long edge, ${trunk} in trunk)`}</Head>
      <Row k="Members, one wedge each" v={s.members} />
      <Row k={`Trunk sections, ${W.declared.splits} wedges each`} v={s.logsAtSplits} />
      <Row k="Blank stock" v={`${(s.stockIn / 12).toFixed(1)} ft`} />
      <Row k={pattern ? "Seam keys, A / B (average of in/out and matched)" : "Seam keys, A / B"} v={`${deg(fam("A").gap)} / ${deg(fam("B").gap)}`} />
      <Row k="Wood, dry / green" v={`${Math.round(s.dryLb).toLocaleString()} / ${Math.round(s.greenLb).toLocaleString()} lb`} />
      {s.matched !== undefined && <Row k="Matched seams, extra key angle" v={`${s.matched}, +${(s.extraDeg ?? 0).toFixed(2)}°`} />}
    </div>
  );

  const sizes = (
    <div className="grid gap-2">
      <Dial label="Long edge" values={W.longEdges} value={longEdge} onChange={setLongEdge} show={(v) => `${v} in (${ftIn(v)})`} />
      <Dial label="Trunk" values={W.trunks} value={trunk} onChange={setTrunk} show={(v) => `${v} in across, split ${W.declared.splits} ways`} />
      {!atReference && <p className="text-[11px] muted">The tables follow these dials; the stage shows the simulator&rsquo;s {D.longEdge} in, {D.trunk} in trunk dome.</p>}
    </div>
  );

  // ---------------------------------------------------------------- the tab: pick a build, read what it takes
  if (!studio) {
    return (
      <div className="grid gap-3">
        <p className="text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: colour }}>The raw-wedge method</p>
        {error && <p className="text-xs" style={{ color: "#ff8a7a" }}>Could not load the simulator&rsquo;s mesh: {error}</p>}
        {buildPicker}
        {pattern && <div className="flex flex-wrap gap-3"><Check label="Tint in / out panels" value={tint} onChange={setTint} /><Check label="Light the matched seams" value={litMatched} onChange={setLitMatched} /></div>}
        {takes}
        {sizes}
        <p className="text-[11px] muted leading-snug">Fullscreen opens the studio: raise the dome band by band, read every seam, compare all eight builds, follow the jig. Click a member to read its cuts.</p>
        {picked && <p className="text-xs panel-2 p-2">{String(picked.id)}: {inch(picked.blank as number)} blank, butt {inch(picked.butt as number)} back, bears on {String(picked.buttInto)}.</p>}
      </div>
    );
  }

  // ---------------------------------------------------------------- fullscreen: the studio
  const seams = pattern?.seams ?? [];
  const shownSeams = seams.filter((x) => seamFilter === "all" || (seamFilter === "matched" ? x.pair !== "in/out" : x.type === seamFilter));
  const sel = seam ? seams.find((x) => x.id === seam) ?? null : null;
  const js = W.jigStages[stage];
  return (
    <div className="grid gap-3">
      <div className="flex items-baseline justify-between gap-2">
        <p className="text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: colour }}>Raw-wedge studio</p>
        <span className="text-xs num muted">{b.label}</span>
      </div>
      <Tabs value={tab} onChange={setTab} colour={colour} tabs={[["dome", "Dome"], ["seams", "Seams"], ["bands", "Bands"], ["compare", "Compare"], ["member", "Member"], ["jig", "Jig"]]} />
      {error && <p className="text-xs" style={{ color: "#ff8a7a" }}>Could not load the simulator&rsquo;s mesh: {error}</p>}

      {tab === "dome" && (
        <div className="grid gap-2">
          {buildPicker}
          <Dial label="Raise the dome, band by band" values={Array.from({ length: BANDS + 1 }, (_, i) => i)} value={maxBand} onChange={setMaxBand}
            show={(v) => (v === 0 ? "the deck" : v === BANDS ? "all of it" : `bands 1 to ${v}`)} />
          {pattern && maxBand > 0 && maxBand <= BANDS && <p className="text-[11px] panel-2 p-2">{pattern.bands.find((x) => x.band === maxBand)?.summary}</p>}
          <Dial label="Open the panels out" values={[0, 3, 6, 10, 16, 24]} value={explode} onChange={setExplode} show={(v) => (v ? `${v} in` : "assembled")} />
          <div className="flex flex-wrap gap-3">
            <Check label="Seam keys" value={keys} onChange={setKeys} />
            <Check label="Head stock to flush-cut" value={offcuts} onChange={setOffcuts} />
            {pattern && <Check label="Tint in / out" value={tint} onChange={setTint} />}
            {pattern && <Check label="Light matched seams" value={litMatched} onChange={setLitMatched} />}
          </div>
          <Choice label="Pick out" value={family} colour={colour} onChange={setFamily} options={[["both", "Both lengths"], ["A", "A, long"], ["B", "B, short"]]} />
          <Row k="Panels, nodes, seams, joints" v={`${s.panels}, ${s.nodes}, ${s.seams}, ${s.joints}`} />
          <Row k="Sphere radius" v={`${inch(s.sphereRadius)} (${ftIn(s.sphereRadius)})`} />
          <Row k="Drawn on the stage" v={drawnAt >= 1 ? "full size" : `1:${(1 / drawnAt).toFixed(2)}`} />
          {sizes}
          <table className="w-full text-[11px] num">
            <thead><tr className="muted text-left"><th></th><th>A</th><th>B</th></tr></thead>
            <tbody>
              {([["Members", (f: Fam) => f.count], ["Nominal edge", (f: Fam) => inch(f.nominal)], ["Blank, shortest", (f: Fam) => inch(f.blankMin)],
                ["Blank, longest", (f: Fam) => inch(f.blankMax)], ["Butt setback", (f: Fam) => inch(f.buttSetback)], ["Seams", (f: Fam) => f.seams],
                ["Fold", (f: Fam) => deg(f.fold)], ["Gap for the key", (f: Fam) => deg(f.gap)], ["Key base", (f: Fam) => (f.keyBase === null ? "--" : inch(f.keyBase))]] as [string, (f: Fam) => React.ReactNode][])
                .map(([k, fn]) => <tr key={k}><td className="muted">{k}</td>{s.families.map((f) => <td key={f.type}>{fn(f)}</td>)}</tr>)}
            </tbody>
          </table>
          {takes}
        </div>
      )}

      {tab === "seams" && (
        pattern ? (
          <div className="grid gap-2">
            <Choice value={seamFilter} colour={colour} onChange={setSeamFilter} options={[["all", `All ${seams.length}`], ["matched", `Matched (${pattern.matched})`], ["A", "A seams"], ["B", "B seams"]]} />
            {sel && (
              <div className="panel-2 p-2 text-xs" style={{ borderColor: colour }}>
                <p className="font-semibold">Seam {sel.id} ({sel.type}): panels {sel.a + 1} and {sel.b + 1}, {sel.pair}</p>
                <Row k="The dome's fold here" v={deg(sel.fold)} />
                <Row k="Gap the key fills" v={deg(sel.gap)} />
                <Row k="An in/out seam on this edge would leave" v={deg(sel.alt)} />
                <Row k="Extra, for being matched" v={sel.pair === "in/out" ? "none" : `+${sel.extra.toFixed(2)}°`} />
                <Row k="Key, wide side" v={inch(sel.key)} />
                <Row k="Closed by band" v={sel.band} />
                <button className="underline mt-1" onClick={() => setSeam(null)}>Light all the matched seams again</button>
              </div>
            )}
            <div className="max-h-96 overflow-y-auto">
              <table className="w-full text-[11px] num">
                <thead className="sticky top-0" style={{ background: "var(--panel)" }}><tr className="muted text-left"><th>Seam</th><th>Pair</th><th>Fold</th><th>Gap</th><th>Extra</th><th>Key</th></tr></thead>
                <tbody>
                  {shownSeams.map((x) => (
                    <tr key={x.id} className="cursor-pointer" onClick={() => setSeam(x.id)} style={{ background: seam === x.id ? "rgba(255,179,71,.15)" : x.pair !== "in/out" ? "rgba(255,42,26,.08)" : undefined }}>
                      <td>{x.id} <span className="muted">{x.type}</span></td><td>{x.pair}</td><td>{x.fold.toFixed(2)}°</td><td>{x.gap.toFixed(2)}°</td>
                      <td>{x.pair === "in/out" ? "" : `+${x.extra.toFixed(2)}°`}</td><td>{x.key.toFixed(2)} in</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-[11px] muted">Click a row, or a key on the dome, to light it. Red rows are matched: both panels point the same way, so the key fills the fold and the sawn faces' angle too.</p>
          </div>
        ) : (
          <div className="grid gap-1">
            <p className="text-xs muted">Every seam of a uniform build is the same pair. By edge type:</p>
            {s.families.map((f) => <Row key={f.type} k={`${f.type}: ${f.seams} seams`} v={`fold ${deg(f.fold)}, key fills ${deg(f.gap)}, ${f.keyBase === null ? "--" : inch(f.keyBase)} wide`} />)}
            <p className="text-[11px] muted">Choose an alternating build to read its seams one by one.</p>
          </div>
        )
      )}

      {tab === "bands" && (
        pattern ? (
          <div className="grid gap-2">
            {pattern.bands.map((x) => (
              <button key={x.band} className="text-left panel-2 p-2 text-xs" style={maxBand === x.band ? { borderColor: colour } : undefined} onClick={() => { setMaxBand(x.band); setTab("dome"); }}>
                <b>Band {x.band}</b>: {x.summary.replace(/^band \d+: /, "")}
                <span className="block muted">The walk round it: {x.panels.map((i) => `${i + 1}${pattern.panels[i].points === "in" ? "↓" : "↑"}`).join(" ")}</span>
              </button>
            ))}
            <Head>The rings the panels close round</Head>
            <div className="max-h-56 overflow-y-auto">
              {pattern.rings.map((r) => <Row key={r.vertex} k={`Vertex ${r.vertex} at ${ftIn(r.height_in)}`} v={`${r.panels} panels, ${r.closes ? "alternates all the way round" : "odd: one seam must match"}${r.matched ? `, ${r.matched} matched` : ""}`} />)}
            </div>
            <p className="text-[11px] muted">An odd ring cannot alternate all the way round, so at least one seam there is matched; the pattern decides where. ↓ points in, ↑ points out.</p>
          </div>
        ) : <p className="text-xs muted">The bands matter for the alternating builds: choose one on the Dome tab.</p>
      )}

      {tab === "compare" && (
        <div className="grid gap-2">
          {sizes}
          <table className="w-full text-[11px] num">
            <thead><tr className="muted text-left"><th>Build</th><th>Key A</th><th>Key B</th><th>Matched</th><th>Stock</th><th>Dry</th></tr></thead>
            <tbody>
              {BUILDS.map((x) => {
                const y = sm(x.key, longEdge, trunk), fa = y.families.find((f) => f.type === "A")!, fb = y.families.find((f) => f.type === "B")!;
                return (
                  <tr key={x.key} className="cursor-pointer" onClick={() => { setBuild(x.key); setTab("dome"); }} style={x.key === build ? { color: colour, fontWeight: 600 } : undefined}>
                    <td>{x.label.replace("Alternating: ", "Alt: ")}</td><td>{deg(fa.gap)}</td><td>{deg(fb.gap)}</td>
                    <td>{y.matched === undefined ? "uniform" : `${y.matched}, +${(y.extraDeg ?? 0).toFixed(1)}°`}</td><td>{(y.stockIn / 12).toFixed(0)} ft</td><td>{Math.round(y.dryLb).toLocaleString()} lb</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <p className="text-[11px] muted">The key angle is what the seam key has to fill (the uniform builds use one key everywhere; an alternating build's in/out seams take the fold alone). Click a build to look at it.</p>
        </div>
      )}

      {tab === "member" && (
        picked ? (
          <div className="panel-2 p-2 text-xs" style={{ borderColor: colour }}>
            <p className="font-semibold">{String(picked.id)} <span className="muted">({String(picked.type)} member, panel {Number(picked.face) + 1}{pattern ? `, which points ${pattern.panels[Number(picked.face)].points}` : ""})</span></p>
            <Row k="Nominal edge" v={inch(picked.nominal as number)} />
            <Row k="Blank to cut" v={inch(picked.blank as number)} />
            <Row k="Along its point" v={inch(picked.axis as number)} />
            <Row k="Butt set back from the vertex" v={inch(picked.butt as number)} />
            <Row k="Receiving setback" v={inch(picked.receiving as number)} />
            <Row k="Butt bears on" v={String(picked.buttInto)} />
            <Row k="Receives the butt of" v={String(picked.receives)} />
            <button className="underline mt-1" onClick={() => setPicked(null)}>Put it back</button>
          </div>
        ) : <p className="text-xs muted">Click a member on the dome to read its cuts.</p>
      )}

      {tab === "jig" && (
        <div className="grid gap-2">
          <div className="flex items-center gap-2">
            <button className="btn-ghost !py-1 !px-2 text-sm" disabled={stage === 0} onClick={() => setStage((x) => x - 1)} aria-label="Previous step">&larr;</button>
            <span className="text-xs num muted">step {stage + 1} of {W.jigStages.length}</span>
            <button className="btn-ghost !py-1 !px-2 text-sm" disabled={stage === W.jigStages.length - 1} onClick={() => setStage((x) => x + 1)} aria-label="Next step">&rarr;</button>
          </div>
          <input type="range" min={0} max={W.jigStages.length - 1} value={stage} onChange={(e) => setStage(Number(e.target.value))} aria-label="Jig step" />
          <p className="font-semibold text-sm" style={{ color: colour }}>{js.title}</p>
          <p className="text-xs">{js.see}</p>
          <p className="text-xs"><b>What it enforces:</b> {js.does}</p>
          <p className="text-[11px] muted">Panel {W.jig.panel + 1} of the simulator&rsquo;s dome on its jig, drawn {JIG_ENLARGE} times full size. The same fixture makes all forty.</p>
        </div>
      )}

      <div>
        <Head>What the simulator declares</Head>
        <Row k="Wedges split from each trunk" v={W.declared.splits} />
        <Row k="Head left long, then flush-cut" v={inch(W.declared.headOverfit)} />
        <Row k="Key nose, trimmed flat" v={inch(W.declared.keyNose)} />
        <Row k="Wood, dry / green (estimates)" v={`${W.declared.dryDensity} / ${W.declared.greenDensity} lb/ft³`} />
      </div>
      <p className="text-[11px] muted leading-snug">Every figure and every mesh is the raw-wedge simulator&rsquo;s (<code>geodesic_raw_wedge_dome_dihedral.py</code>, with <code>alternating_build</code> reading its mixed domes), solved on the desktop and carried here unchanged. Have a licensed engineer check any frame before anyone lives in it.</p>
    </div>
  );
}
