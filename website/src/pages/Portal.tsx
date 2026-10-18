// /portal: the project's tools as places in one 3-D world. The hub is a hilltop clearing with
// the solver's dome in the middle and a gateway to each tool round it; /portal/<tool> is that
// tool's own space, with its own stage and control panel (the panels are built tool by tool).

import { Suspense, lazy, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMeta } from "../lib/meta";
import { World, hubGates, THREE, type Gate } from "../world/engine";
import { SPACES, spaceByKey } from "../world/spaces";

const CreatorPanel = lazy(() => import("../world/CreatorPanel"));

const HUB_RADIUS = 27;

export default function Portal() {
  const { space: key } = useParams();
  const space = spaceByKey(key);
  const go = useNavigate();
  const canvas = useRef<HTMLCanvasElement>(null);
  const labels = useRef<HTMLDivElement>(null);
  const map = useRef<HTMLCanvasElement>(null);
  const world = useRef<World | null>(null);
  const [near, setNear] = useState<Gate | null>(null);
  const [leaving, setLeaving] = useState<string | null>(null);
  const [help, setHelp] = useState(true);
  const touch = typeof window !== "undefined" && window.matchMedia?.("(pointer: coarse)").matches;
  // a phone has no room for the panel over the world: it folds to a button
  const [panel, setPanel] = useState(() => typeof window === "undefined" || window.innerWidth >= 640);
  useMeta(space ? `${space.name} -- Portal` : "Portal", space ? space.blurb : "Every tool of the dome project as a place: walk the hilltop and step through a gateway.", key ? `/portal/${key}` : "/portal");

  useEffect(() => {
    if (!canvas.current || !labels.current) return;
    setLeaving(null);
    setNear(null);
    const from = (history.state?.usr as { from?: string } | null)?.from;
    let gates: Gate[], spawn: { x: number; z: number; facing: number };
    if (space) {
      gates = [{ key: "hub", name: "Back to the hilltop", sub: "the portal hub", colour: "#f4efe6", at: new THREE.Vector2(0, -30), facing: 0 }];   // across the space, behind the stage
      spawn = { x: 0, z: 21, facing: Math.PI };
    } else {
      gates = hubGates(SPACES, HUB_RADIUS).map((g) => ({ ...g, sub: SPACES.find((s) => s.key === g.key)?.blurb.split(":")[0].split(",")[0] }));
      const back = gates.find((g) => g.key === from);
      if (back) {
        const dir = back.at.clone().normalize();
        spawn = { x: dir.x * (HUB_RADIUS - 8), z: dir.y * (HUB_RADIUS - 8), facing: Math.atan2(-dir.x, -dir.y) };
      } else {
        spawn = { x: 0, z: 19, facing: Math.PI };            // on the plaza, facing the dome
      }
    }
    const w = new World(canvas.current, {
      kind: space ? "space" : "hub", space, gates, spawn, labels: labels.current, minimap: map.current || undefined,
      onNear: setNear,
      onEnter: (g) => {
        setLeaving(g.key === "hub" ? "the hilltop" : g.name);
        window.setTimeout(() => go(g.key === "hub" ? "/portal" : `/portal/${g.key}`, { state: { from: space?.key } }), 650);
      },
    });
    world.current = w;
    return () => { w.dispose(); world.current = null; };
  }, [key]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="relative w-full overflow-hidden select-none" style={{ height: "calc(100dvh - 56px)", background: "#0d1117" }}>
      <canvas ref={canvas} className="absolute inset-0 w-full h-full block touch-none" style={{ cursor: "crosshair" }} aria-label={space ? `${space.name}: a 3-D space` : "The portal hub: a 3-D world of the project's tools"} />
      <div ref={labels} className="absolute inset-0 pointer-events-none" aria-hidden />

      {/* where you are */}
      <div className="absolute left-3 top-3 max-w-sm text-[#f4efe6] pointer-events-none">
        <p className="text-[10px] uppercase tracking-[0.25em] text-[#e8b45a] font-semibold">{space ? "A tool's space" : "Zeanah Lab"}</p>
        <h1 className="text-2xl sm:text-3xl font-bold leading-tight" style={{ textShadow: "0 2px 8px rgba(0,0,0,.6)" }}>{space ? space.name : "The Portal"}</h1>
        <p className="text-sm mt-1 opacity-90" style={{ textShadow: "0 1px 6px rgba(0,0,0,.7)" }}>{space ? space.blurb : "Every tool of the project, as a place. Walk to a gateway and step through."}</p>
      </div>

      {/* the minimap */}
      <canvas ref={map} width={150} height={150} className="absolute right-3 top-3 w-[110px] h-[110px] sm:w-[150px] sm:h-[150px] rounded-full shadow-lg pointer-events-none" aria-hidden />

      {/* the tool's own controls, once it has them */}
      {space && !panel && (
        <button className="absolute right-3 top-[130px] btn-ghost !py-1.5 text-sm" style={{ background: "color-mix(in srgb, var(--panel) 90%, transparent)", borderColor: space.colour }}
          onClick={() => setPanel(true)}>Controls</button>
      )}
      {space && panel && (
        <aside className={`absolute right-3 top-[130px] sm:top-[170px] panel p-4 text-sm overflow-y-auto ${space.key === "dome-creator" ? "w-[min(340px,calc(100%-24px))]" : "w-[min(300px,calc(100%-24px))]"}`}
          style={{ background: "color-mix(in srgb, var(--panel) 92%, transparent)", maxHeight: "calc(100% - 190px)" }}>
          {space.key === "dome-creator" ? (
            <Suspense fallback={<p className="muted text-xs">Loading the Creator...</p>}><CreatorPanel world={world} colour={space.colour} /></Suspense>
          ) : (
            <>
              <p className="text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: space.colour }}>Control panel</p>
              <p className="font-semibold mt-1">Coming to this space</p>
              <ul className="mt-2 space-y-1">
                {space.controls.map((c) => <li key={c} className="flex gap-2"><span aria-hidden style={{ color: space.colour }}>&#9656;</span><span>{c}</span></li>)}
              </ul>
              <p className="text-xs muted mt-3">Ported from <code>{space.ports}</code>.</p>
            </>
          )}
          <div className="flex gap-2 mt-3">
            <Link className="btn-ghost !py-1.5 inline-block" to="/portal" state={{ from: space.key }}>Back to the hilltop</Link>
            <button className="btn-ghost !py-1.5 sm:hidden" onClick={() => setPanel(false)}>Fold</button>
          </div>
        </aside>
      )}

      {/* the nearest gateway */}
      {near && !leaving && (
        <div className="absolute left-1/2 -translate-x-1/2 bottom-24 sm:bottom-20 panel px-4 py-2 text-sm text-center pointer-events-none" style={{ borderColor: near.colour }}>
          <b>{near.name}</b> -- walk into the gateway to {near.key === "hub" ? "go back" : "enter"}
        </div>
      )}

      {/* controls, and the camera buttons for touch */}
      <div className="absolute left-3 bottom-3 flex flex-wrap gap-2 items-end">
        {help && (
          <div className="panel px-3 py-2 text-xs max-w-[min(420px,calc(100vw-24px))]" style={{ background: "color-mix(in srgb, var(--panel) 88%, transparent)" }}>
            {touch
              ? <><b>Tap</b> the ground to walk there, <b>drag</b> to turn the camera, and the buttons to turn and zoom.</>
              : <><b>Click</b> the ground to walk there. <b>WASD</b> to walk, <b>arrow keys</b> or <b>drag</b> to turn the camera, <b>scroll</b> to zoom.</>}
            <button className="underline ml-2" onClick={() => setHelp(false)}>Hide</button>
          </div>
        )}
        <div className="flex gap-1">
          {[["Turn left", "↺", () => world.current?.turn(0.4)], ["Turn right", "↻", () => world.current?.turn(-0.4)],
            ["Zoom in", "+", () => world.current?.zoom(0.8)], ["Zoom out", "−", () => world.current?.zoom(1.25)]].map(([label, glyph, fn]) => (
            <button key={label as string} className="btn-ghost !p-0 w-9 h-9 grid place-items-center text-lg" style={{ background: "color-mix(in srgb, var(--panel) 85%, transparent)" }}
              aria-label={label as string} onClick={fn as () => void}>{glyph as string}</button>
          ))}
        </div>
      </div>

      {/* through the gateway */}
      <div className="absolute inset-0 grid place-items-center pointer-events-none transition-opacity duration-500"
        style={{ opacity: leaving ? 1 : 0, background: "radial-gradient(circle, rgba(255,240,210,.95), rgba(13,17,23,1))" }}>
        {leaving && <p className="text-2xl font-semibold text-[#1a1206]">To {leaving}...</p>}
      </div>
    </div>
  );
}
