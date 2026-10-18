// The 3D Wedge Method space's control panel: the raw-wedge simulator's dome in each of its four
// wedge orientations, member by member, and the jig that frames one panel, step by step. The
// stage shows the simulator's own solved meshes (wedgeView.ts); the tables are its own figures
// (wedge.ts). Click a member on the stage to read its cuts.

import { useEffect, useState } from "react";
import { W, loadMesh, summary, type MeshBuffers, type MeshHead } from "./wedge";
import { JIG_ENLARGE, drawDome, drawJig } from "./wedgeView";
import type { ToolProps } from "./tools";
import { Check, Choice, Dial, Head, Row, ftIn } from "./tools/ui";
import type { Part } from "./engine";

const deg = (x: number | null) => (x === null ? "--" : `${x.toFixed(2)}°`);
const inch = (x: number) => `${x.toFixed(2)} in`;
const D = W.defaults;

type Mode = "dome" | "jig";

export default function WedgePanel({ world, colour }: ToolProps) {
  const [mode, setMode] = useState<Mode>("dome");
  const [orientation, setOrientation] = useState(D.orientation);
  const [longEdge, setLongEdge] = useState(D.longEdge);
  const [trunk, setTrunk] = useState(D.trunk);
  const [explode, setExplode] = useState(0);
  const [keys, setKeys] = useState(true);
  const [offcuts, setOffcuts] = useState(false);
  const [family, setFamily] = useState<"A" | "B" | "both">("both");
  const [picked, setPicked] = useState<Record<string, unknown> | null>(null);
  const [stage, setStage] = useState(0);
  const [buf, setBuf] = useState<{ file: string; b: MeshBuffers } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [drawnAt, setDrawnAt] = useState(1);

  const head = (W.meshes as Record<string, MeshHead>)[orientation];
  const file = mode === "dome" ? head.file : W.jig.file;
  useEffect(() => {
    let live = true;
    setError(null);
    loadMesh(mode === "dome" ? head : W.jig).then((b) => live && setBuf({ file, b })).catch((e) => live && setError((e as Error).message));
    return () => { live = false; };
  }, [file]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!buf || buf.file !== file) return;
    const draw = () => {
      if (mode === "dome") {
        const { group, scale } = drawDome(head, buf.b, { explode, keys, offcuts, family: family === "both" ? null : family, picked: (picked?.id as string) ?? null });
        world.current?.setModel(group); setDrawnAt(scale);
      } else world.current?.setModel(drawJig(W.jig, buf.b, stage));
    };
    draw();
    const t = window.setTimeout(draw, 50);              // the world is made after this panel mounts
    return () => window.clearTimeout(t);
  }, [buf, file, mode, explode, keys, offcuts, family, picked, stage]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const on = (e: Event) => {
      const p = (e as CustomEvent<Part>).detail;
      if (!p.id.startsWith("wedge:")) return;
      const id = p.id.slice(6);
      setPicked((head.parts.find((x) => x.kind === "member" && x.id === id) as Record<string, unknown>) ?? null);
    };
    window.addEventListener("portal-part", on);
    return () => window.removeEventListener("portal-part", on);
  }, [head]);
  useEffect(() => setPicked(null), [orientation]);

  const sm = summary(orientation, longEdge, trunk);
  const o = W.orientations.find((x) => x.key === orientation)!;
  const atReference = longEdge === D.longEdge && trunk === D.trunk;
  const js = W.jigStages[stage];
  return (
    <div className="grid gap-3">
      <div>
        <p className="text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: colour }}>The raw-wedge method</p>
        <Choice value={mode} colour={colour} onChange={setMode} options={[["dome", "The dome"], ["jig", "The jig, step by step"]]} />
      </div>
      {error && <p className="text-xs" style={{ color: "#ff8a7a" }}>Could not load the simulator&rsquo;s mesh: {error}</p>}
      {!buf && !error && <p className="text-xs muted">Loading the simulator&rsquo;s solved dome...</p>}

      {mode === "dome" ? (
        <>
          <Choice label="Which way the wedge's point faces" value={orientation} colour={colour} onChange={setOrientation}
            options={W.orientations.map((x) => [x.key, x.label] as [string, string])} />
          <p className="text-xs panel-2 p-2" style={{ borderColor: colour }}>
            At a seam: {o.reading}. Each stick&rsquo;s butt bears on its neighbour&rsquo;s <b>{o.receiver.replace("_", " ").toLowerCase()}</b> face.
          </p>
          <Dial label="Open the panels out" values={[0, 3, 6, 10, 16, 24]} value={explode} onChange={setExplode} show={(v) => (v ? `${v} in` : "assembled")} />
          <div className="flex flex-wrap gap-3">
            <Check label="Seam keys" value={keys} onChange={setKeys} />
            <Check label="Head stock to flush-cut" value={offcuts} onChange={setOffcuts} />
          </div>
          <Choice label="Pick out" value={family} colour={colour} onChange={setFamily} options={[["both", "Both lengths"], ["A", "A, long"], ["B", "B, short"]]} />

          {picked && (
            <div className="panel-2 p-2 text-xs" style={{ borderColor: colour }}>
              <p className="font-semibold">{String(picked.id)} <span className="muted">({String(picked.type)} member, panel {Number(picked.face) + 1})</span></p>
              <Row k="Nominal edge" v={inch(picked.nominal as number)} />
              <Row k="Blank to cut" v={inch(picked.blank as number)} />
              <Row k="Along its point" v={inch(picked.axis as number)} />
              <Row k="Butt set back from the vertex" v={inch(picked.butt as number)} />
              <Row k="Butt bears on" v={String(picked.buttInto)} />
              <Row k="Receives the butt of" v={String(picked.receives)} />
              <button className="underline mt-1" onClick={() => setPicked(null)}>Put it back</button>
            </div>
          )}

          <div className="grid gap-2 pt-1 border-t" style={{ borderColor: "var(--line)" }}>
            <p className="text-[11px] muted">The tables follow these dials; the stage shows the simulator&rsquo;s {D.longEdge} in, {D.trunk} in trunk dome{atReference ? "" : " (move them back to see it match)"}.</p>
            <Dial label="Long edge" values={W.longEdges} value={longEdge} onChange={setLongEdge} show={(v) => `${v} in (${ftIn(v)})`} />
            <Dial label="Trunk" values={W.trunks} value={trunk} onChange={setTrunk} show={(v) => `${v} in across, split ${W.declared.splits} ways`} />
          </div>

          <div>
            <Head>The dome</Head>
            <Row k="Panels, nodes, seams" v={`${sm.panels}, ${sm.nodes}, ${sm.seams}`} />
            <Row k="Members (each owned by one panel)" v={sm.members} />
            <Row k="Pinwheel joints" v={sm.joints} />
            <Row k="Sphere radius" v={`${inch(sm.sphereRadius)} (${ftIn(sm.sphereRadius)})`} />
            <Row k="Drawn on the stage" v={drawnAt >= 1 ? "full size" : `1:${(1 / drawnAt).toFixed(2)}`} />
          </div>
          <div>
            <Head>The two lengths</Head>
            <table className="w-full text-[11px] num">
              <thead><tr className="muted text-left"><th></th><th>A</th><th>B</th></tr></thead>
              <tbody>
                {([["Members", (f: (typeof sm.families)[0]) => f.count], ["Nominal edge", (f) => inch(f.nominal)],
                  ["Blank, shortest", (f) => inch(f.blankMin)], ["Blank, longest", (f) => inch(f.blankMax)],
                  ["Butt setback", (f) => inch(f.buttSetback)], ["Seams", (f) => f.seams], ["Fold", (f) => deg(f.fold)],
                  ["Raw gap for the key", (f) => deg(f.gap)], ["Key base", (f) => (f.keyBase === null ? "--" : inch(f.keyBase))]] as [string, (f: (typeof sm.families)[0]) => React.ReactNode][])
                  .map(([k, fn]) => <tr key={k}><td className="muted">{k}</td>{sm.families.map((f) => <td key={f.type}>{fn(f)}</td>)}</tr>)}
              </tbody>
            </table>
          </div>
          <div>
            <Head>What it takes</Head>
            <Row k="Blank stock" v={`${(sm.stockIn / 12).toFixed(1)} ft`} />
            <Row k="Wedges, one member each" v={sm.members} />
            <Row k={`Trunk sections, ${W.declared.splits} wedges each`} v={sm.logsAtSplits} />
            <Row k="Wood" v={`${sm.volumeFt3.toFixed(1)} ft³`} />
            <Row k="Weight, dry / green" v={`${Math.round(sm.dryLb).toLocaleString()} / ${Math.round(sm.greenLb).toLocaleString()} lb`} />
            <Row k="Head stock flush-cut away" v={`${(sm.headOffcutIn / 12).toFixed(0)} ft`} />
          </div>
        </>
      ) : (
        <>
          <div className="flex items-center gap-2">
            <button className="btn-ghost !py-1 !px-2 text-sm" disabled={stage === 0} onClick={() => setStage((x) => x - 1)} aria-label="Previous step">&larr;</button>
            <span className="text-xs num muted">step {stage + 1} of {W.jigStages.length}</span>
            <button className="btn-ghost !py-1 !px-2 text-sm" disabled={stage === W.jigStages.length - 1} onClick={() => setStage((x) => x + 1)} aria-label="Next step">&rarr;</button>
          </div>
          <input type="range" min={0} max={W.jigStages.length - 1} value={stage} onChange={(e) => setStage(Number(e.target.value))} aria-label="Jig step" />
          <div>
            <p className="font-semibold text-sm" style={{ color: colour }}>{js.title}</p>
            <p className="text-xs mt-1">{js.see}</p>
            <p className="text-xs mt-1"><b>What it enforces:</b> {js.does}</p>
          </div>
          <p className="text-[11px] muted">Panel {W.jig.panel + 1} of the simulator&rsquo;s dome on its jig, drawn {JIG_ENLARGE} times full size. The same fixture makes all forty.</p>
        </>
      )}

      <div>
        <Head>What the simulator declares</Head>
        <Row k="Wedges split from each trunk" v={W.declared.splits} />
        <Row k="Head left long, then flush-cut" v={inch(W.declared.headOverfit)} />
        <Row k="Key nose, trimmed flat" v={inch(W.declared.keyNose)} />
        <Row k="Wood, dry / green (estimates)" v={`${W.declared.dryDensity} / ${W.declared.greenDensity} lb/ft³`} />
      </div>
      <p className="text-[11px] muted leading-snug">
        Every figure and every mesh here is the raw-wedge simulator&rsquo;s (<code>geodesic_raw_wedge_dome_dihedral.py</code>), solved on the desktop and carried here unchanged.
        Have a licensed engineer check any frame before anyone lives in it.
      </p>
    </div>
  );
}
