// The Dome Creator studio's floor plan: the dome's floor seen from above, its ten sections
// (workshop.section_of: the centre and nine 40-degree wedges) painted with rooms, the partition
// walls creator.ts derived from them, the props standing where they stand, and the wiring and
// plumbing runs to them. Click a section to give it the chosen room; pick a prop and click the
// floor to place it; drag a prop to move it; select one to turn it or take it away.

import { useRef, useState } from "react";
import { T, sectionLabel, sectionOf, type Config, type Design, type Prop } from "./creator";
import { Select } from "./tools/ui";

const css = (c: number[]) => `rgb(${Math.round(c[0] * 255)},${Math.round(c[1] * 255)},${Math.round(c[2] * 255)})`;

export default function CreatorFloor({ c, d, set, colour }: { c: Config; d: Design; set: (patch: Partial<Config>) => void; colour: string }) {
  const [room, setRoom] = useState("Office");
  const [tool, setTool] = useState<"room" | "prop">("room");
  const [prop, setProp] = useState("Worktable");
  const [sel, setSel] = useState<number | null>(null);
  const drag = useRef<number | null>(null);
  const svg = useRef<SVGSVGElement>(null);
  const fr = d.floorRadius, R = 200, k = (R - 6) / fr;       // svg px per metre
  const P = (x: number, y: number) => [R + x * k, R - y * k];  // +y (north) up the page
  const props = c.props ?? [];
  const sections = c.sections ?? Array(10).fill("Unassigned");
  const roomRgb = (name: string) => css(T.fitout.rooms.find((x) => x.name === name)?.rgb ?? [0.55, 0.55, 0.55]);

  const toFloor = (e: React.PointerEvent) => {
    const r = svg.current!.getBoundingClientRect();
    const sx = ((e.clientX - r.left) / r.width) * 2 * R, sy = ((e.clientY - r.top) / r.height) * 2 * R;
    return { x: (sx - R) / k, y: (R - sy) / k };
  };
  const setProps = (next: Prop[]) => set({ props: next });

  const onDown = (e: React.PointerEvent) => {
    const at = toFloor(e);
    const hit = props.findIndex((p) => Math.hypot(p.x - at.x, p.y - at.y) < (T.fitout.props.find((q) => q.name === p.type)?.radius ?? 0.4));
    if (hit >= 0) { setSel(hit); drag.current = hit; (e.target as Element).setPointerCapture?.(e.pointerId); return; }
    const sec = sectionOf(at.x, at.y, fr);
    if (sec < 0) return;
    if (tool === "room") { const next = [...sections]; next[sec] = room; set({ sections: next }); return; }
    setProps([...props, { type: prop, x: +at.x.toFixed(2), y: +at.y.toFixed(2), yaw: 0 }]);
    setSel(props.length);
  };
  const onMove = (e: React.PointerEvent) => {
    if (drag.current === null) return;
    const at = toFloor(e);
    if (Math.hypot(at.x, at.y) > fr) return;
    setProps(props.map((p, i) => (i === drag.current ? { ...p, x: +at.x.toFixed(2), y: +at.y.toFixed(2) } : p)));
  };
  const onUp = () => { drag.current = null; };

  const wedge = (i: number) => {
    const a0 = (i * T.fitout.wedgeDegrees * Math.PI) / 180, a1 = ((i + 1) * T.fitout.wedgeDegrees * Math.PI) / 180;
    const ri = fr * T.fitout.centerFraction;
    const pt = (rr: number, a: number) => P(Math.sin(a) * rr, Math.cos(a) * rr).join(" ");
    return `M ${pt(ri, a0)} L ${pt(fr, a0)} A ${fr * k} ${fr * k} 0 0 1 ${pt(fr, a1)} L ${pt(ri, a1)} A ${ri * k} ${ri * k} 0 0 0 ${pt(ri, a0)} Z`;
  };
  const selected = sel !== null ? props[sel] : null;
  const categories = [...new Set(T.fitout.props.map((q) => q.category))];

  return (
    <div className="grid gap-2">
      <div className="flex gap-1">
        <button className={`btn-ghost !py-1 text-xs ${tool === "room" ? "font-semibold" : "muted"}`} style={tool === "room" ? { borderColor: colour, color: colour } : undefined} onClick={() => setTool("room")}>Paint rooms</button>
        <button className={`btn-ghost !py-1 text-xs ${tool === "prop" ? "font-semibold" : "muted"}`} style={tool === "prop" ? { borderColor: colour, color: colour } : undefined} onClick={() => setTool("prop")}>Place props</button>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {tool === "room"
          ? <Select label="Room to paint" value={room} options={T.fitout.rooms.map((r) => r.name)} onChange={setRoom} />
          : <label className="grid gap-0.5 text-xs"><span className="muted">Prop to place</span>
              <select className="field !py-1 text-sm" value={prop} onChange={(e) => setProp(e.target.value)}>
                {categories.map((cat) => <optgroup key={cat} label={cat}>{T.fitout.props.filter((q) => q.category === cat).map((q) => <option key={q.name} value={q.name}>{q.name} (${q.cost})</option>)}</optgroup>)}
              </select></label>}
        <Select label="Partitions" value={c.partitions ?? "Markings"} options={T.fitout.partitionModes} onChange={(v) => set({ partitions: v })} />
      </div>
      <svg ref={svg} viewBox={`0 0 ${2 * R} ${2 * R}`} className="w-full touch-none select-none rounded" style={{ background: "#1b2230", cursor: tool === "prop" ? "crosshair" : "pointer" }}
        onPointerDown={onDown} onPointerMove={onMove} onPointerUp={onUp} aria-label="The floor plan">
        <circle cx={R} cy={R} r={fr * k} fill="#2a3242" />
        {Array.from({ length: 9 }, (_, i) => <path key={i} d={wedge(i)} fill={roomRgb(sections[i + 1])} fillOpacity={0.55} stroke="#11161f" strokeWidth={1}><title>{sectionLabel(i + 1)}: {sections[i + 1]}</title></path>)}
        <circle cx={R} cy={R} r={fr * T.fitout.centerFraction * k} fill={roomRgb(sections[0])} fillOpacity={0.6} stroke="#11161f"><title>{sectionLabel(0)}: {sections[0]}</title></circle>
        {sections.map((name, i) => {
          if (name === "Unassigned") return null;
          const a = (((i - 0.5) * T.fitout.wedgeDegrees) * Math.PI) / 180, rr = i === 0 ? 0 : fr * (T.fitout.centerFraction + 1) / 2;
          const [x, y] = P(Math.sin(a) * rr, Math.cos(a) * rr);
          return <text key={i} x={x} y={y} fontSize={10} fill="#fff" textAnchor="middle" pointerEvents="none">{name}</text>;
        })}
        {d.walls.map((w) => { const [x1, y1] = P(...w.inner), [x2, y2] = P(...w.outer); return <line key={w.azimuth} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#f0ebe0" strokeWidth={w.height > 1.5 ? 5 : 3} />; })}
        {d.wireRuns.map((r, i) => { const [x1, y1] = P(...r.from), [x2, y2] = P(...r.to); return <line key={`w${i}`} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#ffb020" strokeDasharray="4 3" />; })}
        {d.pipeRuns.map((r, i) => { const [x1, y1] = P(...r.from), [x2, y2] = P(...r.to); return <line key={`p${i}`} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#3aa0ff" strokeDasharray="6 3" />; })}
        {d.pipeRuns.length > 0 && (() => { const [x, y] = P(T.fitout.utility[0], fr * T.fitout.utility[1]); return <rect x={x - 5} y={y - 5} width={10} height={10} fill="#3aa0ff"><title>Utility stub: water in, drain out</title></rect>; })()}
        {props.map((p, i) => {
          const q = T.fitout.props.find((x) => x.name === p.type);
          const [x, y] = P(p.x, p.y), rr = Math.max(4, (q?.radius ?? 0.4) * k * 0.7);
          return <g key={i} transform={`rotate(${p.yaw} ${x} ${y})`}>
            <rect x={x - rr} y={y - rr} width={2 * rr} height={2 * rr} rx={2} fill={q?.role ? "#e0a030" : q && T.fitout.waterFixtures.includes(q.name) ? "#4a9ad0" : "#c8b8a0"}
              stroke={sel === i ? colour : "#000"} strokeWidth={sel === i ? 3 : 1}><title>{p.type}</title></rect>
            <line x1={x} y1={y} x2={x} y2={y - rr} stroke="#000" />
          </g>;
        })}
      </svg>
      <p className="text-[11px] muted">{tool === "room" ? "Click a section to give it the room. Walls rise between neighbours with different rooms." : "Click the floor to place it; drag a prop to move it."} Orange dashes: wiring from the battery bank (or charge controller) to outlets, meters and controllers. Blue: water and drain from the utility stub.</p>
      {selected && (
        <div className="panel-2 p-2 text-xs flex flex-wrap items-center gap-2">
          <b>{selected.type}</b><span className="muted">at {selected.x.toFixed(2)}, {selected.y.toFixed(2)} m, facing {selected.yaw}°</span>
          <button className="btn-ghost !py-0.5" onClick={() => setProps(props.map((p, i) => (i === sel ? { ...p, yaw: (p.yaw + 345) % 360 } : p)))}>&#8634; 15°</button>
          <button className="btn-ghost !py-0.5" onClick={() => setProps(props.map((p, i) => (i === sel ? { ...p, yaw: (p.yaw + 15) % 360 } : p)))}>&#8635; 15°</button>
          <button className="btn-ghost !py-0.5" onClick={() => { setProps(props.filter((_, i) => i !== sel)); setSel(null); }}>Take it away</button>
        </div>
      )}
    </div>
  );
}
