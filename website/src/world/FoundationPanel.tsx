// The Foundation & Pads space's control panel. The pentagon foundation as world3d.structures builds
// it -- five half trunks mitred into a pentagon, the five-point star inside, the piers, the deck --
// laid out the way it is built, starting from the stakes and string on the ground; and the
// platform a seed dome stands on, priced board by board by pad_deck five ways, built up on the
// stage one line of the receipt at a time.

import { useEffect, useMemo, useState } from "react";
import * as THREE from "three";
import data from "../generated/foundation.json";
import type { ToolProps } from "./tools";
import { Choice, Dial, Head, Row } from "./tools/ui";
import type { Part } from "./engine";

const F = data;
const usd = (x: number) => `$${Math.round(x).toLocaleString()}`;
const ftIn = (inches: number) => { const t = Math.round(inches * 10) / 10, ft = Math.floor(t / 12); return `${ft} ft ${(t - ft * 12).toFixed(1)} in`; };
const STAGE_RADIUS_FT = 8.6;
type Piece = (typeof F.pieces)[number];

interface Rows { pos: Int16Array; col: Uint8Array }
let rows: Promise<Rows> | null = null;
const loadRows = () => (rows ??= fetch(F.mesh.file).then((r) => { if (!r.ok) throw new Error(`${F.mesh.file}: ${r.status}`); return r.arrayBuffer(); })
  .then((buf) => ({ pos: new Int16Array(buf, 0, F.mesh.vertices * 3), col: new Uint8Array(buf, F.mesh.vertices * 6, F.mesh.vertices) })));

const STEPS = [
  { key: "jig", title: "Stakes and string", says: "Before a log moves: a stake at every corner and at every crossing of the star, and string between them. The layout is the jig." },
  { key: "frame", title: "The pentagon", says: "Five half trunks on edge, round backs out, mitred at the corners." },
  { key: "star", title: "The star inside it", says: "Ten long pieces and five short ones: one 20 ft log yields one of each." },
  { key: "deck", title: "The deck over it", says: "The floor across the pentagon's top, where the dome stands." },
];
const stepOf = (p: Piece) => {
  if (p.layer === "jig") return 0;
  if (p.layer === "deck") return 3;
  const group = String((p.meta as { group?: string }).group || "");
  return group.startsWith("Frame") || group.startsWith("Pier") ? 1 : 2;   // the pentagon on its piers, then the star
};

function drawFoundation(r: Rows, step: number, picked: string | null) {
  const g = new THREE.Group();
  const s = 1 / 12, fit = Math.min(1, STAGE_RADIUS_FT / (F.facts.diagonal_in / 12 / 1.9));
  const jig = F.jigAt;
  const solid = new THREE.MeshLambertMaterial({ vertexColors: true, flatShading: true, side: THREE.DoubleSide });
  const glow = new THREE.MeshLambertMaterial({ vertexColors: true, flatShading: true, side: THREE.DoubleSide, emissive: new THREE.Color("#ffb347"), emissiveIntensity: 0.6 });
  for (const p of F.pieces) {
    const k = stepOf(p);
    if (k > step || (k === 0 && step > 1)) continue;          // the string comes up once the logs are down
    const [v0, n] = p.v;
    const back = k === 0 ? jig : [0, 0, 0];                    // the jig is laid out beside the foundation in the 3-D world
    const pos = new Float32Array(n * 3), col = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) {
      const j = v0 + i;
      const x = r.pos[j * 3] * F.mesh.scale - back[0], y = r.pos[j * 3 + 1] * F.mesh.scale - back[1], z = r.pos[j * 3 + 2] * F.mesh.scale - back[2];
      pos[i * 3] = x * s * fit; pos[i * 3 + 1] = z * s * fit; pos[i * 3 + 2] = -y * s * fit;
      const c = F.mesh.palette[r.col[j]] || [0.7, 0.5, 0.3];
      col[i * 3] = c[0]; col[i * 3 + 1] = c[1]; col[i * 3 + 2] = c[2];
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
    geo.computeVertexNormals();
    const m = new THREE.Mesh(geo, p.id === picked ? glow : solid);
    m.castShadow = true;
    const meta = p.meta as { centreline_in?: number; cut_in?: number | null };
    m.userData.part = { id: `found:${p.id}`, name: p.name,
      examine: meta.centreline_in ? `${p.name}: ${meta.centreline_in.toFixed(2)} in on its centreline${meta.cut_in ? `, cut to ${meta.cut_in.toFixed(2)} in` : ""}.` : `${p.name}.` };
    g.add(m);
  }
  return g;
}

/** The platform for a seed dome, one construction, built up to a line of its receipt. */
function drawPad(kind: string, acrossFt: number, upto: number, labels: string[]) {
  const g = new THREE.Group();
  const fit = Math.min(1, STAGE_RADIUS_FT / (acrossFt / 2));
  const R = (acrossFt / 2) * fit;
  const has = (prefix: string) => labels.slice(0, upto).some((l) => l.startsWith(prefix));
  const mat = (c: string, extra: Partial<THREE.MeshStandardMaterialParameters> = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.85, flatShading: true, ...extra });
  const deca = (r: number, h: number, m: THREE.Material, y: number) => { const d = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, 10), m); d.rotation.y = Math.PI / 10; d.position.y = y + h / 2; d.castShadow = d.receiveShadow = true; g.add(d); return d; };
  let top = 0;
  if (has("compacted gravel")) { deca(R * 1.04, 0.35, mat("#9a958a"), 0); top = 0.35; }
  if (kind === "slab" && (has("concrete,") || has("forming, placing"))) { deca(R, 0.6, mat("#b8b4aa"), top); top += 0.6; }
  if (kind === "ring" && (has("concrete ring") || has("forming and placing the ring"))) {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(R * 0.9, 0.45, 6, 10), mat("#b8b4aa")); ring.rotation.x = Math.PI / 2; ring.position.y = top + 0.45; g.add(ring);
  }
  if (kind.startsWith("blocks") || kind === "ring") {
    const lift = kind === "ring" ? 0.9 : 1.6;
    if (has("precast piers") || kind === "ring") {
      const pier = mat("#a8a49a");
      if (kind !== "ring") for (let x = -R * 0.75; x <= R * 0.76; x += R * 0.375) for (let z = -R * 0.75; z <= R * 0.76; z += R * 0.375) {
        if (Math.hypot(x, z) > R * 0.92) continue;
        const b = new THREE.Mesh(new THREE.BoxGeometry(0.8, lift, 0.8), pier); b.position.set(x, top + lift / 2, z); b.castShadow = true; g.add(b);
      }
    }
    const wood = mat("#b5834e"), board = mat("#c8a070");
    const level = top + lift;
    if (has("beams")) for (let x = -R * 0.75; x <= R * 0.76; x += R * 0.375) { const len = 2 * Math.sqrt(Math.max(0, R * R - x * x)) * 0.92; const b = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.75, len), wood); b.position.set(x, level + 0.37, 0); b.castShadow = true; g.add(b); }
    if (has("joists")) for (let z = -R * 0.9; z <= R * 0.91; z += 1.33 * fit) { const len = 2 * Math.sqrt(Math.max(0, R * R - z * z)) * 0.95; const j = new THREE.Mesh(new THREE.BoxGeometry(len, 0.5, 0.15), wood); j.position.set(0, level + 1, z); g.add(j); }
    if (has("deck boards")) {
      const epoxy = kind === "blocks_epoxy" && (has("epoxy") || has("sealer"));
      deca(R, 0.12, epoxy ? mat("#d8c8a8", { roughness: 0.15, metalness: 0.1 }) : board, level + 1.25);
      if (!epoxy) for (let x = -R; x <= R; x += 0.5 * fit) { const len = 2 * Math.sqrt(Math.max(0, R * R - x * x)); if (len < 0.2) continue; const line = new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.02, len * 0.96), mat("#7a5a3a")); line.position.set(x, level + 1.38, 0); g.add(line); }
    }
  }
  g.userData.part = { id: "pad", name: "the pad" };
  return g;
}

export default function FoundationPanel({ world, colour }: ToolProps) {
  const [mode, setMode] = useState<"foundation" | "pad">("foundation");
  const [step, setStep] = useState(3);
  const [picked, setPicked] = useState<string | null>(null);
  const [kind, setKind] = useState("blocks");
  const [across, setAcross] = useState(F.pad.across);
  const [upto, setUpto] = useState(99);
  const [r, setR] = useState<Rows | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { loadRows().then(setR).catch((e) => setError((e as Error).message)); }, []);

  const deck = useMemo(() => (F.pad.decks as Record<string, { across: number; key: string; label: string; cost: number; area: number; perSqft: number; boards: number; walkable: boolean; note: string; lines: { label: string; quantity: number; unit: string; unitCost: number; cost: number; source: string }[] }[]>)[kind].find((d) => Math.abs(d.across - across) < 1e-6)!, [kind, across]);
  const seq = (F.pad.sequence as Record<string, { number: number; label: string; detail: string; cumulative: number }[]>)[kind];
  const atReference = Math.abs(across - F.pad.across) < 1e-6;
  const stepsShown = atReference ? seq : deck.lines.map((l, i) => ({ number: i + 1, label: l.label, detail: `${l.quantity.toLocaleString(undefined, { maximumFractionDigits: 0 })} ${l.unit} at $${l.unitCost.toFixed(2)}`, cumulative: deck.lines.slice(0, i + 1).reduce((s, x) => s + x.cost, 0) }));
  const n = Math.min(upto, stepsShown.length);

  useEffect(() => {
    const draw = () => {
      if (mode === "foundation") { if (r) world.current?.setModel(drawFoundation(r, step, picked)); }
      else world.current?.setModel(drawPad(kind, across, n, stepsShown.map((x) => x.label)));
    };
    draw();
    const t = window.setTimeout(draw, 50);
    return () => window.clearTimeout(t);
  }, [mode, r, step, picked, kind, across, n, world]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const on = (e: Event) => { const p = (e as CustomEvent<Part>).detail; if (p.id.startsWith("found:")) setPicked(p.id.slice(6)); };
    window.addEventListener("portal-part", on);
    return () => window.removeEventListener("portal-part", on);
  }, []);

  const f = F.facts;
  const piece = F.pieces.find((p) => p.id === picked);
  const order = [...F.pad.kinds].map((k) => (F.pad.decks as Record<string, { across: number; cost: number; label: string }[]>)[k].find((d) => Math.abs(d.across - across) < 1e-6)!).sort((x, y) => x.cost - y.cost);
  return (
    <div className="grid gap-3">
      <div>
        <p className="text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: colour }}>What the dome stands on</p>
        <Choice value={mode} colour={colour} onChange={setMode} options={[["foundation", "The pentagon foundation"], ["pad", "The pad, priced"]]} />
      </div>
      {error && <p className="text-xs" style={{ color: "#ff8a7a" }}>Could not load the foundation: {error}</p>}
      {mode === "foundation" ? (
        <>
          <div className="flex items-center gap-2">
            <button className="btn-ghost !py-1 !px-2 text-sm" disabled={step === 0} onClick={() => setStep((x) => x - 1)} aria-label="Previous step">&larr;</button>
            <span className="text-xs muted num">step {step + 1} of {STEPS.length}</span>
            <button className="btn-ghost !py-1 !px-2 text-sm" disabled={step === STEPS.length - 1} onClick={() => setStep((x) => x + 1)} aria-label="Next step">&rarr;</button>
          </div>
          <div>
            <p className="font-semibold text-sm" style={{ color: colour }}>{STEPS[step].title}</p>
            <p className="text-xs mt-1">{STEPS[step].says}</p>
          </div>
          {piece && (
            <div className="panel-2 p-2 text-xs" style={{ borderColor: colour }}>
              <p className="font-semibold">{piece.name}</p>
              {"centreline_in" in piece.meta && <Row k="On its centreline" v={ftIn(Number(piece.meta.centreline_in))} />}
              {"cut_in" in piece.meta && piece.meta.cut_in && <Row k="Cut to" v={ftIn(Number(piece.meta.cut_in))} />}
              <button className="underline mt-1" onClick={() => setPicked(null)}>Put it back</button>
            </div>
          )}
          <div>
            <Head>The pentagon and its star</Head>
            <Row k="Side" v={ftIn(f.side_in)} />
            <Row k="Corner to far corner (side x phi)" v={`${ftIn(f.diagonal_in)} (phi ${f.phi.toFixed(4)})`} />
            <Row k="Star: long pieces" v={`${f.long_count} on a ${ftIn(f.long_centre_in)} line, cut ${ftIn(f.long_cut_in)}`} />
            <Row k="Star: short pieces" v={`${f.short_count} on a ${ftIn(f.short_centre_in)} line, cut ${ftIn(f.short_cut_in)}`} />
            <Row k="Left from each log" v={ftIn(f.spare_in)} />
            <Row k="Frame logs" v={f.frame_count} />
            <Row k="Corners, star points" v={`${f.interior_deg}°, ${f.star_point_deg}°`} />
            <Row k="Top of the foundation" v={ftIn(f.top_in)} />
          </div>
          <p className="text-[11px] muted">Click a log on the stage to read its cut.</p>
        </>
      ) : (
        <>
          <Choice label="Built as" value={kind} colour={colour} onChange={(k) => { setKind(k); setUpto(99); }}
            options={F.pad.kinds.map((k) => [k, (F.pad.decks as Record<string, { label: string }[]>)[k][0].label] as [string, string])} />
          <Dial label="Across" values={F.pad.sizes} value={across} onChange={(v) => { setAcross(v); setUpto(99); }} show={(v) => `${v.toFixed(1)} ft${Math.abs(v - F.pad.across) < 1e-6 ? " (a seed dome)" : ""}`} />
          <div className="panel-2 p-2" style={{ borderColor: colour }}>
            <p className="text-lg font-bold" style={{ color: colour }}>{usd(deck.cost)}</p>
            <p className="text-xs">{deck.area.toFixed(0)} ft², {usd(deck.perSqft)} a square foot{deck.boards ? `, ${deck.boards} boards to order` : ""}. {deck.walkable ? "" : "Not a floor."}</p>
            <p className="text-[11px] muted mt-1">{deck.note}</p>
          </div>
          <Dial label="Built up to" values={stepsShown.map((x) => x.number)} value={Math.min(n, stepsShown.length)} onChange={setUpto} show={(v) => `${v} of ${stepsShown.length}: ${usd(stepsShown[v - 1]?.cumulative ?? 0)}`} />
          <div>
            <Head>The receipt, in the order it is built</Head>
            <ol className="text-[11px] space-y-0.5">
              {stepsShown.map((x) => <li key={x.number} style={x.number <= n ? undefined : { opacity: 0.45 }}><b>{x.number}.</b> {x.label}: {x.detail} <span className="muted num">({usd(x.cumulative)})</span></li>)}
            </ol>
          </div>
          <div>
            <Head>Every way, at {across.toFixed(1)} ft</Head>
            {order.map((d) => <Row key={d.label} k={d.label} v={usd(d.cost)} />)}
          </div>
          <p className="text-[11px] muted">Every board is priced off one measured shelf price: a 2x6x12 at {usd(F.pad.board.usd)} (${F.pad.board.perFoot.toFixed(2)} a foot).</p>
        </>
      )}
      <p className="text-[11px] muted leading-snug">
        The foundation&rsquo;s pieces are <code>world3d.structures</code>&rsquo;s, from <code>infill.base</code>; the pad&rsquo;s receipt is <code>pad_deck</code>&rsquo;s takeoff. Have an engineer check any foundation for the ground it sits on.
      </p>
    </div>
  );
}
