// /portal: the project's tools as places in one 3-D world, and a RuneScape-style game of dome
// know-how laid over it. The hub is a hilltop clearing with the solver's dome in the middle, a
// gateway to each tool round it, teachers on the plaza and the things that destroy buildings
// out past the gateways; /portal/<tool> is that tool's own space and control panel.
// docs/portal-world.md is the plan.

import { Suspense, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../lib/api";
import { useMeta } from "../lib/meta";
import { useSession } from "../lib/session";
import { World, hubGates, THREE, type Gate, type Pick } from "../world/engine";
import { AreaGame } from "../world/game/area";
import HUD from "../world/game/HUD";
import { Store, clean, hasProgress, loadLocal, type Save } from "../world/game/store";
import { SPACES, spaceByKey } from "../world/spaces";
import { TOOLS } from "../world/tools";

const HUB_RADIUS = 27;

// One player for the whole visit: the store outlives the page as it moves between areas.
let STORE: Store | null = null;
const store = () => (STORE ??= new Store(loadLocal()));

/** A member's progress lives on their account; a guest's in the browser, kept when they join. */
function useAccountSave(s: Store, signedIn: boolean) {
  useEffect(() => {
    if (!signedIn) return;
    let stop = false, timer = 0, lastSent = "";
    api<{ save: Save | null }>("/game/save").then(async (r) => {
      if (stop) return;
      if (r.save) { s.s = clean(r.save); s.emit(); }
      else if (hasProgress(s.s)) await api("/game/save", { method: "PUT", body: { save: s.s } }).catch(() => undefined);
      lastSent = JSON.stringify(s.s);
    }).catch(() => undefined);
    const off = s.subscribe(() => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        const now = JSON.stringify(s.s);
        if (now !== lastSent) { lastSent = now; void api("/game/save", { method: "PUT", body: { save: s.s } }).catch(() => undefined); }
      }, 4000);
    });
    return () => { stop = true; off(); window.clearTimeout(timer); };
  }, [s, signedIn]);
}

export default function Portal() {
  const { space: key } = useParams();
  const space = spaceByKey(key);
  const Tool = space ? TOOLS[space.key] : undefined;
  const go = useNavigate();
  const { me } = useSession();
  const canvas = useRef<HTMLCanvasElement>(null);
  const labels = useRef<HTMLDivElement>(null);
  const map = useRef<HTMLCanvasElement>(null);
  const world = useRef<World | null>(null);
  const game = useRef<AreaGame | null>(null);
  const [, bump] = useState(0);
  const [near, setNear] = useState<Gate | null>(null);
  const [leaving, setLeaving] = useState<string | null>(null);
  const [pick, setPick] = useState<Pick | null>(null);
  const [menuAt, setMenuAt] = useState<Pick | null>(null);
  // a phone has no room for the panel over the world: it folds to a button
  const [panel, setPanel] = useState(() => typeof window === "undefined" || window.innerWidth >= 640);
  const s = store();
  useAccountSave(s, Boolean(me));
  useMeta(space ? `${space.name} -- Portal` : "Portal", space ? space.blurb : "A world of dome know-how: walk the hilltop, learn from teachers, fight what destroys buildings, and step through a gateway into each tool.", key ? `/portal/${key}` : "/portal");

  useEffect(() => {
    if (!canvas.current || !labels.current) return;
    setLeaving(null);
    setNear(null);
    setPick(null);
    const from = (history.state?.usr as { from?: string } | null)?.from;
    let gates: Gate[], spawn: { x: number; z: number; facing: number };
    if (space) {
      gates = [{ key: "hub", name: "Back to the hilltop", sub: "the portal hub", colour: "#f4efe6", at: new THREE.Vector2(0, -30), facing: 0 }];   // across the space, behind the stage
      spawn = { x: 0, z: 21, facing: Math.PI };
    } else {
      gates = hubGates(SPACES, HUB_RADIUS).map((g) => ({ ...g, sub: SPACES.find((x) => x.key === g.key)?.blurb.split(":")[0].split(",")[0] }));
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
      onPick: (p) => game.current?.click(p),
      onContext: (p) => setMenuAt(p),
      onHover: (p) => setPick(p),
    });
    world.current = w;
    const g = new AreaGame(w, space?.key ?? "hub", s, () => bump((n) => n + 1));
    game.current = g;
    // ?debug: the running world and game, for checking them from the browser's console
    if (new URLSearchParams(window.location.search).has("debug")) (window as unknown as { portal: unknown }).portal = { world: w, game: g, store: s };
    if (!s.log.length) s.say(space ? `You step into ${space.name}.` : "Welcome to the Portal. Talk to Tutor Tess on the plaza to begin.", "game");
    else s.say(space ? `You step into ${space.name}.` : "You are back on the hilltop.");
    const home = () => (space ? w.walkPoint(0, -30) : w.walkPoint(0, 17));
    window.addEventListener("portal-home", home);
    return () => { window.removeEventListener("portal-home", home); g.dispose(); game.current = null; w.dispose(); world.current = null; };
  }, [key]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="relative w-full overflow-hidden select-none" style={{ height: "calc(100dvh - 56px)", background: "#0d1117" }}>
      <canvas ref={canvas} className="absolute inset-0 w-full h-full block touch-none" style={{ cursor: pick?.thing || pick?.gate ? "pointer" : "crosshair" }}
        aria-label={space ? `${space.name}: a 3-D space` : "The portal hub: a 3-D world of the project's tools"} />
      <div ref={labels} className="absolute inset-0 pointer-events-none" aria-hidden />

      {/* where you are */}
      <div className="absolute left-3 top-3 max-w-sm text-[#f4efe6] pointer-events-none">
        <p className="text-[10px] uppercase tracking-[0.25em] text-[#e8b45a] font-semibold">{space ? "A tool's space" : "Zeanah Lab"}</p>
        <h1 className="text-xl sm:text-2xl font-bold leading-tight" style={{ textShadow: "0 2px 8px rgba(0,0,0,.6)" }}>{space ? space.name : "The Portal"}</h1>
        <p className="text-xs mt-0.5 opacity-90 max-sm:hidden" style={{ textShadow: "0 1px 6px rgba(0,0,0,.7)" }}>{space ? space.blurb : "A world of dome know-how. Right-click anything."}</p>
      </div>

      {/* the minimap, and the camera buttons beside it */}
      <canvas ref={map} width={150} height={150} className="absolute right-3 top-3 w-[100px] h-[100px] sm:w-[140px] sm:h-[140px] rounded-full shadow-lg pointer-events-none" aria-hidden />
      <div className="absolute top-3 right-[116px] sm:right-[156px] flex flex-col gap-1">
        {[["Turn left", "↺", () => world.current?.turn(0.4)], ["Turn right", "↻", () => world.current?.turn(-0.4)],
          ["Zoom in", "+", () => world.current?.zoom(0.8)], ["Zoom out", "−", () => world.current?.zoom(1.25)]].map(([label, glyph, fn]) => (
          <button key={label as string} className="w-7 h-7 grid place-items-center text-sm rounded" style={{ background: "rgba(43,36,26,.85)", border: "1px solid #000", color: "#fff" }}
            aria-label={label as string} title={label as string} onClick={fn as () => void}>{glyph as string}</button>
        ))}
      </div>

      {/* the tool's own controls */}
      {space && !panel && (
        <button className="absolute right-3 top-[118px] sm:top-[156px] btn-ghost !py-1.5 text-sm" style={{ background: "color-mix(in srgb, var(--panel) 90%, transparent)", borderColor: space.colour }}
          onClick={() => setPanel(true)}>Controls</button>
      )}
      {space && panel && (
        <aside className={`absolute right-3 top-[118px] sm:top-[156px] panel p-4 text-sm overflow-y-auto ${Tool ? "w-[min(340px,calc(100%-24px))]" : "w-[min(300px,calc(100%-24px))]"}`}
          style={{ background: "color-mix(in srgb, var(--panel) 92%, transparent)", maxHeight: "calc(100% - 156px - 380px)", minHeight: 120, zIndex: 4 }}>
          {Tool ? (
            <Suspense fallback={<p className="muted text-xs">Loading the tool...</p>}><Tool world={world} colour={space.colour} /></Suspense>
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
            <button className="btn-ghost !py-1.5" onClick={() => setPanel(false)}>Fold</button>
          </div>
        </aside>
      )}

      {/* the nearest gateway */}
      {near && !leaving && (
        <div className="absolute left-1/2 -translate-x-1/2 bottom-[76px] panel px-4 py-2 text-sm text-center pointer-events-none" style={{ borderColor: near.colour, zIndex: 3 }}>
          <b>{near.name}</b> -- walk into the gateway to {near.key === "hub" ? "go back" : "enter"}
        </div>
      )}

      <HUD store={s} game={game.current} pick={pick} menuAt={menuAt} onMenuClosed={() => setMenuAt(null)} signedIn={Boolean(me)} />

      {/* through the gateway */}
      <div className="absolute inset-0 grid place-items-center pointer-events-none transition-opacity duration-500"
        style={{ opacity: leaving ? 1 : 0, background: "radial-gradient(circle, rgba(255,240,210,.95), rgba(13,17,23,1))", zIndex: 30 }}>
        {leaving && <p className="text-2xl font-semibold text-[#1a1206]">To {leaving}...</p>}
      </div>
    </div>
  );
}
