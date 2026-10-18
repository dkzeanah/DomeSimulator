// /portal: the project's tools as places in one 3-D world, and a RuneScape-style game of dome
// know-how laid over it. The hub is a hilltop clearing with the solver's dome in the middle, a
// gateway to each tool round it, teachers on the plaza and the things that destroy buildings
// out past the gateways; /portal/<tool> is that tool's own space and control panel.
// docs/portal-world.md is the plan.

import { Suspense, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api } from "../lib/api";
import { useMeta } from "../lib/meta";
import { useSession } from "../lib/session";
import { World, hubGates, THREE, type Gate, type Pick } from "../world/engine";
import { AreaGame, type HouseTrip } from "../world/game/area";
import { HOUSE_STYLES, houseStyle } from "../world/game/content";
import { buildEstate } from "../world/estates";
import HUD from "../world/game/HUD";
import { Store, clean, hasProgress, loadLocal, type Save } from "../world/game/store";
import { SPACES, spaceByKey, type Space } from "../world/spaces";
import { TOOLS } from "../world/tools";

const HUB_RADIUS = 27;

// One player for the whole visit: the store outlives the page as it moves between areas.
let STORE: Store | null = null;
const store = () => (STORE ??= new Store(loadLocal()));

/** A member's progress lives on their account; a guest's in the browser, kept when they join.
 *  Says when the account's save has come back (a guest's is there from the start). */
let accountLoaded = false;
function useAccountSave(s: Store, signedIn: boolean) {
  const [loaded, setLoaded] = useState(accountLoaded || !signedIn);
  useEffect(() => {
    if (!signedIn) { setLoaded(true); return; }
    let stop = false, timer = 0, lastSent = "";
    api<{ save: Save | null }>("/game/save").then(async (r) => {
      if (stop) return;
      if (r.save) { s.s = clean(r.save); s.emit(); }
      else if (hasProgress(s.s) || s.s.tut) await api("/game/save", { method: "PUT", body: { save: s.s } }).catch(() => undefined);
      lastSent = JSON.stringify(s.s);
    }).catch(() => undefined).finally(() => { if (!stop) { accountLoaded = true; setLoaded(true); } });
    const off = s.subscribe(() => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        const now = JSON.stringify(s.s);
        if (now !== lastSent) { lastSent = now; void api("/game/save", { method: "PUT", body: { save: s.s } }).catch(() => undefined); }
      }, 4000);
    });
    return () => { stop = true; off(); window.clearTimeout(timer); };
  }, [s, signedIn]);
  return loaded;
}

/** Whose house this is and how it is built: one of the grand houses, or a member's. */
interface House { owner: string; style: string; title: string; line: string; yours: boolean }
const GRAND = (n: string) => /^[1-5]$/.test(n);

function useHouse(owner: string | undefined, me: { username: string } | null | undefined, s: Store) {
  const [house, setHouse] = useState<House | null>(null);
  const [missing, setMissing] = useState<string | null>(null);
  const [, bump] = useState(0);
  useEffect(() => s.subscribe(() => bump((n) => n + 1)), [s]);
  const mine = Boolean(owner && me && me.username === owner);
  // your own house follows your save as you change it in build mode
  const myStyle = mine ? houseStyle(s.s.house).key : null;
  useEffect(() => {
    setMissing(null);
    if (!owner) { setHouse(null); return; }
    if (GRAND(owner)) { const h = houseStyle(owner); setHouse({ owner, style: owner, title: h.name, line: `grand house ${owner} of 5`, yours: false }); return; }
    let live = true;
    api<{ username: string; name: string; style: string; yours: boolean }>(`/game/house/${encodeURIComponent(owner)}`)
      .then((r) => {
        if (!live) return;
        const style = r.yours && myStyle ? myStyle : r.style;
        setHouse({ owner: r.username, style, title: style === "starter" ? "Home" : houseStyle(style).name, line: `the house of ${r.name}`, yours: r.yours });
      })
      .catch((e) => live && setMissing((e as Error).message));
    return () => { live = false; };
  }, [owner, myStyle]);
  return { house: owner ? house : null, missing };
}

export default function Portal({ island = false }: { island?: boolean }) {
  const { space: key, owner } = useParams();
  const [params] = useSearchParams();
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
  // the game's side panel (inventory, skills...) shares the right edge with the tool's panel
  const [sideOpen, setSideOpen] = useState(true);
  const s = store();
  const saveLoaded = useAccountSave(s, Boolean(me));
  const { house, missing } = useHouse(owner, me, s);
  // Wedge Island's lesson and scenery load only when you go there
  const [islandMod, setIslandMod] = useState<typeof import("../world/game/island") | null>(null);
  useEffect(() => { if (island && !islandMod) void import("../world/game/island").then((m) => setIslandMod(m)); }, [island]); // eslint-disable-line react-hooks/exhaustive-deps
  // a brand-new player starts on Wedge Island, the way RuneScape starts everyone on Tutorial Island
  const fresh = !s.s.tut?.done && !hasProgress(s.s);
  useEffect(() => {
    if (!key && !owner && !island && saveLoaded && fresh && !(history.state?.usr as { from?: string } | null)?.from) go("/portal/island", { replace: true });
  }, [key, owner, island, saveLoaded, fresh]); // eslint-disable-line react-hooks/exhaustive-deps
  const building = Boolean(house?.yours && params.has("build"));
  useMeta(island ? "Wedge Island -- Portal" : house ? `${house.title} -- Portal` : space ? `${space.name} -- Portal` : "Portal", space ? space.blurb : "A world of dome know-how: walk the hilltop, learn from teachers, fight what destroys buildings, and step through a gateway into each tool.", key ? `/portal/${key}` : "/portal");

  useEffect(() => {
    if (!canvas.current || !labels.current) return;
    if (owner && !house) return;                       // a house waits until we know how it is built
    if (island && !islandMod) return;                   // the island's lesson loads with it
    if (!key && !owner && !island && saveLoaded && fresh && !(history.state?.usr as { from?: string } | null)?.from) return;   // off to the island instead
    setLeaving(null);
    setNear(null);
    setPick(null);
    const from = (history.state?.usr as { from?: string } | null)?.from;
    let gates: Gate[], spawn: { x: number; z: number; facing: number };
    const estate = house ? buildEstate(house.style, house.line) : null;
    const houseSpace: Space | undefined = island && islandMod
      ? { key: "island", name: "Wedge Island", blurb: "from trees to a dome", ports: "", colour: "#e8b45a", sky: islandMod.SKY, ground: islandMod.GROUND, controls: [] }
      : house && estate
        ? { key: "house", name: house.title, blurb: house.line, ports: "", colour: "#b07cff", sky: estate.sky, ground: estate.ground, controls: [] } : undefined;
    if (island) {
      gates = [];
      spawn = { x: islandMod!.AT.spawn[0], z: islandMod!.AT.spawn[1], facing: Math.PI };
    } else if (houseSpace) {
      gates = [];                                      // the way out is the portal by the gate
      spawn = { x: 0, z: 100, facing: Math.PI };
    } else if (space) {
      gates = [{ key: "hub", name: "Back to the hilltop", sub: "the portal hub", colour: "#f4efe6", at: new THREE.Vector2(0, -30), facing: 0 }];   // across the space, behind the stage
      spawn = { x: 0, z: 21, facing: Math.PI };
    } else {
      gates = hubGates(SPACES, HUB_RADIUS).map((g) => ({ ...g, sub: SPACES.find((x) => x.key === g.key)?.blurb.split(":")[0].split(",")[0] }));
      const back = gates.find((g) => g.key === from);
      if (from === "house") {
        spawn = { x: -24, z: 24, facing: Math.atan2(24, -24) };      // beside the house portal
      } else if (back) {
        const dir = back.at.clone().normalize();
        spawn = { x: dir.x * (HUB_RADIUS - 8), z: dir.y * (HUB_RADIUS - 8), facing: Math.atan2(-dir.x, -dir.y) };
      } else {
        spawn = { x: 0, z: 19, facing: Math.PI };            // on the plaza, facing the dome
      }
    }
    const w = new World(canvas.current, {
      kind: houseSpace ? "house" : space ? "space" : "hub", space: houseSpace ?? space, gates, spawn, labels: labels.current, minimap: map.current || undefined,
      clear: [[-30, 30, 9]],
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
    if (estate) w.setEstate(estate.group, estate.obstacles, estate.tick);
    const g = new AreaGame(w, island ? "island" : house ? `house:${house.owner}` : space?.key ?? "hub", s, () => bump((n) => n + 1));
    if (island && islandMod) {
      g.script = islandMod.createIsland(w, s, g, () => bump((n) => n + 1), () => {
        setLeaving("the mainland");
        window.setTimeout(() => go("/portal", { state: { from: "island" } }), 650);
      }).script;
    }
    game.current = g;
    // ?debug: the running world and game, for checking them from the browser's console
    if (new URLSearchParams(window.location.search).has("debug")) (window as unknown as { portal: unknown }).portal = { world: w, game: g, store: s };
    const arrive = island ? "You arrive on Wedge Island." : house ? `Welcome to ${house.title}, ${house.line}.` : space ? `You step into ${space.name}.` : null;
    if (!s.log.length) s.say(arrive ?? "Welcome to the Portal. Talk to Tutor Tess on the plaza to begin.", "game");
    else s.say(arrive ?? "You are back on the hilltop.");
    const home = () => (house ? w.walkPoint(0, 96) : space ? w.walkPoint(0, -30) : w.walkPoint(0, 17));
    window.addEventListener("portal-home", home);
    return () => { window.removeEventListener("portal-home", home); g.dispose(); game.current = null; w.dispose(); world.current = null; };
  }, [key, owner, house?.style, house?.owner, island, islandMod, saveLoaded && fresh]); // eslint-disable-line react-hooks/exhaustive-deps

  // the house portal's trips
  useEffect(() => {
    const trip = (to: string, state?: object) => {
      setLeaving(to.startsWith("/portal/house") ? "the house" : "the hilltop");
      window.setTimeout(() => go(to, { state }), 650);
    };
    const on = async (e: Event) => {
      const t = (e as CustomEvent<HouseTrip>).detail;
      if (t.to === "leave") return trip("/portal", { from: "house" });
      if (t.to === "island") return trip("/portal/island");
      if (t.to === "home" || t.to === "build") {
        if (!me) { s.say("You need an account to own a house. Sign in, then come back to the portal.", "game"); return; }
        return trip(`/portal/house/${me.username}${t.to === "build" ? "?build=1" : ""}`);
      }
      const name = (t.name || "").trim().toLowerCase().replace(/^@/, "");
      if (GRAND(name)) return trip(`/portal/house/${name}`);
      try { await api(`/game/house/${encodeURIComponent(name)}`); trip(`/portal/house/${encodeURIComponent(name)}`); }
      catch { s.say(`Nobody called "${t.name}" has a house. Try a member's username, or 1 to 5 for the grand houses.`, "game"); }
    };
    window.addEventListener("portal-house", on);
    return () => window.removeEventListener("portal-house", on);
  }, [me, go, s]);

  return (
    <div className="relative w-full overflow-hidden select-none" style={{ height: "calc(100dvh - 56px)", background: "#0d1117" }}>
      <canvas ref={canvas} className="absolute inset-0 w-full h-full block touch-none" style={{ cursor: pick?.thing || pick?.gate || pick?.part ? "pointer" : "crosshair" }}
        aria-label={space ? `${space.name}: a 3-D space` : "The portal hub: a 3-D world of the project's tools"} />
      <div ref={labels} className="absolute inset-0 pointer-events-none" aria-hidden />

      {owner && missing && (
        <div className="absolute inset-0 grid place-items-center" style={{ zIndex: 20 }}>
          <div className="panel p-5 max-w-sm text-center">
            <p className="font-semibold">Nobody by that name has a house.</p>
            <p className="text-sm muted mt-1">Try a member&rsquo;s username at the house portal, or 1 to 5 for the grand houses.</p>
            <Link className="btn-ghost inline-block mt-3" to="/portal" state={{ from: "house" }}>Back to the hilltop</Link>
          </div>
        </div>
      )}
      {owner && !house && !missing && <div className="absolute inset-0 grid place-items-center text-[#f4efe6]" style={{ zIndex: 20 }}>Finding the house...</div>}

      {/* build mode: how your house is built */}
      {building && house && (
        <aside className="absolute right-3 top-[118px] sm:top-[156px] panel p-4 text-sm overflow-y-auto w-[min(320px,calc(100%-24px))]"
          style={{ background: "color-mix(in srgb, var(--panel) 92%, transparent)", maxHeight: "calc(100% - 156px - 56px)", zIndex: 4 }}>
          <p className="text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: "#b07cff" }}>Build mode</p>
          <p className="font-semibold mt-1">How your house is built</p>
          <p className="text-xs muted">Visitors who type your name at the house portal see it this way.</p>
          <ul className="mt-2 grid gap-1.5">
            {HOUSE_STYLES.map((h) => {
              const on = houseStyle(s.s.house).key === h.key;
              return (
                <li key={h.key}>
                  <button className={`w-full text-left p-2 rounded border ${on ? "font-semibold" : ""}`} style={{ borderColor: on ? "#b07cff" : "var(--line)" }}
                    onClick={() => { s.s.house = h.key; s.emit(); s.say(`Your house is now ${h.name}.`, "game"); }}>
                    {h.name}<span className="block text-xs muted font-normal">{h.blurb}</span>
                  </button>
                </li>
              );
            })}
          </ul>
          <p className="text-[11px] muted mt-2">Building it piece by piece, room by room, is the next phase (docs/portal-world.md).</p>
          <Link className="btn-ghost !py-1.5 inline-block mt-2" to={`/portal/house/${house.owner}`}>Leave build mode</Link>
        </aside>
      )}

      {/* where you are (on the island the lesson's box stands here instead) */}
      <div className="absolute left-3 top-3 max-w-sm text-[#f4efe6] pointer-events-none" style={{ display: island ? "none" : undefined }}>
        <p className="text-[10px] uppercase tracking-[0.25em] text-[#e8b45a] font-semibold">{house ? (building ? "Your house, build mode" : "A house") : space ? "A tool's space" : "Zeanah Lab"}</p>
        <h1 className="text-xl sm:text-2xl font-bold leading-tight" style={{ textShadow: "0 2px 8px rgba(0,0,0,.6)" }}>{house ? house.title : space ? space.name : "The Portal"}</h1>
        <p className="text-xs mt-0.5 opacity-90 max-sm:hidden" style={{ textShadow: "0 1px 6px rgba(0,0,0,.7)" }}>{house ? `${house.line[0].toUpperCase()}${house.line.slice(1)}. The portal by the gate takes you back.` : space ? space.blurb : "A world of dome know-how. Right-click anything."}</p>
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
          style={{ background: "color-mix(in srgb, var(--panel) 92%, transparent)", maxHeight: sideOpen ? "calc(100% - 156px - 380px)" : "calc(100% - 156px - 56px)", minHeight: 120, zIndex: 4 }}>
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

      <HUD store={s} game={game.current} pick={pick} menuAt={menuAt} onMenuClosed={() => setMenuAt(null)} signedIn={Boolean(me)}
        folded={Boolean((Tool && panel) || building)} onSidePanel={setSideOpen} />

      {/* through the gateway */}
      <div className="absolute inset-0 grid place-items-center pointer-events-none transition-opacity duration-500"
        style={{ opacity: leaving ? 1 : 0, background: "radial-gradient(circle, rgba(255,240,210,.95), rgba(13,17,23,1))", zIndex: 30 }}>
        {leaving && <p className="text-2xl font-semibold text-[#1a1206]">To {leaving}...</p>}
      </div>
    </div>
  );
}
