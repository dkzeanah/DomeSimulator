// The Portal world's interface, laid out the way RuneScape players expect: hover text top
// left, a right-click menu where you click, the chatbox bottom left (dialogue shows there too),
// the action bar along the bottom, and Old School RuneScape's control panel bottom right: a row of
// tabs above and below one box -- combat, skills (every house-building job, by stage), quests, the
// backpack, worn equipment, this portal's own controls, badges; then keys, settings, the world
// map, home and fullscreen. The orbs and the minimap are Portal.tsx's.

import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import type { Pick } from "../engine";
import type { AreaGame, Option } from "./area";
import { useChat } from "./chat";
import { LORE, QUESTS, SKILLS, STAGES, combatLevel, itemById, levelForXp, nextLevelXp, xpForLevel, type Lore, type SkillKey } from "./content";
import { registerKeys, typing, useKeyList } from "./keys";
import { BAR_SIZE, type Store } from "./store";

type Tab = "combat" | "skills" | "quests" | "inv" | "worn" | "tool" | "badges" | "keys" | "settings";
const TOP: { key: Tab; label: string; icon: string; hot: string }[] = [
  { key: "combat", label: "Combat options", icon: "⚔", hot: "F1" },
  { key: "skills", label: "Skills", icon: "\u{1f4ca}", hot: "K" },
  { key: "quests", label: "Quests", icon: "\u{1f4dc}", hot: "J" },
  { key: "inv", label: "Inventory", icon: "\u{1f392}", hot: "I" },
  { key: "worn", label: "Worn equipment", icon: "\u{1f6e1}", hot: "F5" },
  { key: "tool", label: "This portal's controls", icon: "\u{1f6e0}", hot: "F6" },
  { key: "badges", label: "Badges and lore", icon: "\u{1f3c5}", hot: "B" },
];
const FKEYS: Record<string, Tab> = { F1: "combat", F2: "skills", F3: "quests", F4: "inv", F5: "worn", F6: "tool" };

/** A portal's own controls, shown in the control panel's tool tab. The element is moved, not
 *  re-made, so the tool keeps its settings between the tab and fullscreen. */
export interface ToolTab { title: string; icon?: string; colour: string; host: HTMLElement; fullscreen?: () => void }

/** Put a kept element (a tool's panel) inside this box while it is shown. */
export function HostSlot({ host, className }: { host: HTMLElement; className?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.appendChild(host);
    return () => { if (host.parentNode === el) el.removeChild(host); };
  }, [host]);
  return <div ref={ref} className={className} />;
}

const stone = { background: "#3e3529", border: "2px solid #000", color: "#f4efe6" } as const;
const tabBtn = (on: boolean) => ({ background: on ? "#7a3a1a" : "#4a3f30", borderRight: "1px solid #000", color: "#fff" });

export const ACTIONS: Record<string, { label: string; icon: string; hint: string }> = {
  eat: { label: "Eat", icon: "\u{1f95c}", hint: "Eat the first food in your bag" },
  read: { label: "Read", icon: "\u{1f4d6}", hint: "Read your next unread lore page" },
  attack: { label: "Attack", icon: "⚔", hint: "Attack the nearest monster" },
  take: { label: "Take", icon: "\u{1f45c}", hint: "Take everything from the nearest loot" },
  talk: { label: "Talk", icon: "\u{1f4ac}", hint: "Talk to the nearest teacher" },
  home: { label: "Plaza", icon: "⌂", hint: "Walk back to the plaza" },
  keys: { label: "Keys", icon: "⌨", hint: "Show every shortcut" },
};

interface Menu { x: number; y: number; options: Option[] }

export default function HUD({ store, game, pick, menuAt, onMenuClosed, signedIn, tool, onWorldMap, onHome, onSidePanel, hidden }: {
  store: Store; game: AreaGame | null; pick: Pick | null; menuAt: Pick | null; onMenuClosed: () => void; signedIn: boolean;
  /** This area's own controls: a tool's panel, or the house's build mode. */
  tool?: ToolTab | null;
  onWorldMap: () => void;
  onHome: () => void;
  onSidePanel?: (open: boolean) => void;
  /** Fullscreen: the HUD steps aside for the editor. */
  hidden?: boolean;
}) {
  const [, bump] = useState(0);
  useEffect(() => store.subscribe(() => bump((n) => n + 1)), [store]);
  const phone = typeof window !== "undefined" && window.innerWidth < 640;
  const [tab, setTab] = useState<Tab | null>(() => (tool ? "tool" : phone ? null : "inv"));
  // a tool's space opens on its controls; anywhere else the backpack
  useEffect(() => { setTab(tool ? "tool" : phone ? null : "inv"); }, [Boolean(tool), tool?.title]); // eslint-disable-line react-hooks/exhaustive-deps
  const [skill, setSkill] = useState<SkillKey | null>(null);
  useEffect(() => { onSidePanel?.(tab !== null); }, [tab]); // eslint-disable-line react-hooks/exhaustive-deps
  const [menu, setMenu] = useState<Menu | null>(null);
  const [chatTab, setChatTab] = useState<"all" | "game" | "public">("all");
  const [chatOpen, setChatOpen] = useState(() => typeof window === "undefined" || window.innerWidth >= 640);
  const [draft, setDraft] = useState("");
  const [promptText, setPromptText] = useState("");
  const [reading, setReading] = useState<Lore | null>(null);
  const [journal, setJournal] = useState<string | null>(null);
  const input = useRef<HTMLInputElement>(null);
  const chat = useChat(true);
  const s = store.s;

  // the right-click menu, where the click was
  useEffect(() => {
    if (!menuAt || !game) { setMenu(null); return; }
    setMenu({ x: menuAt.x, y: menuAt.y, options: game.options(menuAt) });
  }, [menuAt, game]);
  const close = () => { setMenu(null); onMenuClosed(); };

  // a lore page opens in the reader
  useEffect(() => {
    const f = (e: Event) => setReading((e as CustomEvent).detail as Lore);
    window.addEventListener("portal-read", f);
    return () => window.removeEventListener("portal-read", f);
  }, []);

  const doAction = (key: string | null) => {
    if (!key || !game) return;
    if (key.startsWith("item:")) {
      const slot = s.inv.findIndex((x) => x && x.id === key.slice(5));
      if (slot >= 0) game.use(slot); else store.say("You don't have that any more.");
      return;
    }
    if (key === "eat") game.eatBest();
    else if (key === "read") game.readNext();
    else if (key === "attack") { const m = game.nearest("monster"); if (m) game.attack(m); else store.say("Nothing to fight here."); }
    else if (key === "take") game.takeAll();
    else if (key === "talk") { const n = game.nearest("npc"); if (n) game.talk(n.slice(4)); else store.say("No teacher here."); }
    else if (key === "home") window.dispatchEvent(new CustomEvent("portal-home"));
    else if (key === "spec") game.toggleSpec();
    else if (key === "run") game.toggleRun();
    else if (key === "keys") setTab("keys");
  };

  // keys: the action bar, the tabs, dialogue, chat
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (typing(e)) { if (e.key === "Escape") (e.target as HTMLElement).blur(); return; }
      const d = game?.dialog;
      if (game?.menu) {
        if (/^[1-9]$/.test(e.key)) { game.choose(Number(e.key) - 1); e.preventDefault(); return; }
        if (e.key === "Escape") { game.menu = null; bump((n) => n + 1); return; }
      }
      if (e.key === "Escape") { if (menu) close(); else if (reading) setReading(null); else if (d && game) { game.dialog = null; bump((n) => n + 1); } return; }
      if (d && game) {
        const asking = d.question && d.at >= d.lines.length && !d.answered;
        if (asking && /^[1-9]$/.test(e.key)) { const c = d.question!.choices[Number(e.key) - 1]; if (c) { game.answer(c); e.preventDefault(); } return; }
        if (e.key === " " || e.key === "Enter") { if (!asking) game.next(); e.preventDefault(); return; }
      }
      if (/^[1-8]$/.test(e.key)) { doAction(s.bar[Number(e.key) - 1]); e.preventDefault(); return; }
      if (FKEYS[e.key]) { const t = FKEYS[e.key]; if (t !== "tool" || tool) setTab((x) => (x === t ? null : t)); e.preventDefault(); return; }
      if (e.key.toLowerCase() === "r" && game) { game.toggleRun(); return; }
      const k = e.key.toLowerCase();
      if (k === "i") setTab((t) => (t === "inv" ? null : "inv"));
      else if (k === "k") setTab((t) => (t === "skills" ? null : "skills"));
      else if (k === "j") setTab((t) => (t === "quests" ? null : "quests"));
      else if (k === "b") setTab((t) => (t === "badges" ? null : "badges"));
      else if (e.key === "?" || e.key === "/") { setTab((t) => (t === "keys" ? null : "keys")); e.preventDefault(); }
      else if (e.key === "Enter") { setChatOpen(true); setChatTab("public"); window.setTimeout(() => input.current?.focus(), 0); e.preventDefault(); }
    };
    window.addEventListener("keydown", down);
    return () => window.removeEventListener("keydown", down);
  }); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => registerKeys("Getting around", [
    { keys: "Left click", does: "Walk there, or do the first option on what you click" },
    { keys: "Right click / long press", does: "Every option for what is under the pointer" },
    { keys: "W A S D", does: "Walk" },
    { keys: "Arrow keys, Q, E, or drag", does: "Turn the camera" },
    { keys: "Scroll", does: "Zoom" },
  ]), []);
  useEffect(() => registerKeys("Interface", [
    { keys: "1 - 8", does: "The action bar's slots" },
    { keys: "F1 - F6", does: "Combat, skills, quests, inventory, equipment, this portal's controls" },
    { keys: "I K J B", does: "Inventory, skills, quest journal, badges" },
    { keys: "R", does: "Run on or off" },
    { keys: "Click the minimap", does: "Walk there" },
    { keys: "? or /", does: "This list" },
    { keys: "Enter", does: "Talk in public chat" },
    { keys: "Space", does: "Continue a conversation; 1-3 answers a question" },
    { keys: "Esc", does: "Close a menu, a page or a conversation" },
  ]), []);
  const keyList = useKeyList();

  const hover = useMemo(() => {
    if (!game || !pick || (!pick.thing && !pick.gate && !pick.part)) return null;
    const o = game.options(pick)[0];
    return o && o.label !== "Cancel" ? o : null;
  }, [game, pick]);

  const guide = game?.script?.guide() ?? null;
  const d = game?.dialog;
  const log = store.log;
  const lines = chatTab === "public" ? [] : log.filter((l) => chatTab === "all" || l.kind !== "chat");
  const pub = chatTab === "game" ? [] : chat.messages;
  const panelBox = "color-mix(in srgb, #2b241a 92%, transparent)";

  return (
    <>
      {/* the lesson's instruction box (Wedge Island), where the area's title would be */}
      {guide && (
        <div className="absolute left-3 top-3 w-[min(400px,calc(100%-24px))] p-3 text-[13px] shadow-xl" style={{ background: "#d8cba8", border: "2px solid #3a2e1e", color: "#1a1206", zIndex: 6 }}>
          <div className="flex items-baseline justify-between gap-2">
            <p className="font-bold" style={{ color: "#7a1a10" }}>{guide.title}</p>
            <span className="text-[10px] opacity-70 num">step {guide.step} of {guide.of}</span>
          </div>
          <p className="mt-1 leading-snug">{guide.text}</p>
          <div className="h-1.5 mt-2" style={{ background: "rgba(0,0,0,.15)" }}><div className="h-1.5" style={{ width: `${(guide.step / guide.of) * 100}%`, background: "#7a1a10" }} /></div>
          {game?.script?.skip && guide.step < guide.of && <button className="text-[11px] underline mt-1 opacity-70" onClick={() => game.script!.skip!()}>Skip the tutorial</button>}
        </div>
      )}

      {/* what a click would do */}
      {hover && (
        <div className={`absolute left-3 ${guide ? "top-[170px]" : "top-[104px]"} text-sm font-semibold pointer-events-none`} style={{ textShadow: "0 1px 2px #000", color: "#fff" }}>
          {hover.label} <span style={{ color: hover.colour || "#ffe24a" }}>{hover.target}</span>
          <span className="opacity-70 font-normal"> {pick && game && game.options(pick).length > 2 ? `/ ${game.options(pick).length - 2} more options` : ""}</span>
        </div>
      )}

      {/* the right-click menu */}
      {menu && (
        <div className="fixed inset-0 z-40" onPointerDown={close} onContextMenu={(e) => { e.preventDefault(); close(); }}>
          <div className="absolute min-w-[190px] text-sm shadow-xl" style={{ left: Math.min(menu.x - 10, window.innerWidth - 230), top: Math.min(menu.y - 6, window.innerHeight - 30 - menu.options.length * 24), background: "#5d5447", border: "2px solid #000", color: "#fff" }}
            onPointerDown={(e) => e.stopPropagation()}>
            <div className="px-2 py-0.5 font-semibold" style={{ background: "#000", color: "#5d5447" }}>Choose Option</div>
            {menu.options.map((o, i) => (
              <button key={i} className="block w-full text-left px-2 py-0.5 hover:bg-black/30" onClick={() => { o.run(); close(); }}>
                {o.label} <span style={{ color: o.colour || "#fff" }}>{o.target}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* the chatbox, where conversations happen too */}
      <div className="absolute left-3 bottom-3 w-[min(460px,calc(100%-24px))] text-[13px]" style={{ zIndex: 5, display: hidden && !d && !game?.menu && !game?.prompt ? "none" : undefined }}>
        {game?.prompt ? (
          <form className="p-3 text-center" style={{ background: "#d8cba8", border: "2px solid #3a2e1e", color: "#1a1206", minHeight: 130 }}
            onSubmit={(e) => { e.preventDefault(); game.answerPrompt(promptText); setPromptText(""); }}>
            <p className="font-bold mt-3">{game.prompt.ask}</p>
            <div className="flex justify-center items-baseline gap-0.5 mt-1">
              <input autoFocus className="bg-transparent outline-none text-center font-semibold w-60" style={{ color: "#1a3ab0" }} maxLength={24} value={promptText}
                onChange={(e) => setPromptText(e.target.value)} onKeyDown={(e) => { if (e.key === "Escape") { game.answerPrompt(null); setPromptText(""); } }} aria-label={game.prompt.ask} />
            </div>
            {game.prompt.hint && <p className="text-[11px] mt-2 opacity-70">{game.prompt.hint}. Enter to go, Esc to cancel.</p>}
          </form>
        ) : game?.menu ? (
          <div className="p-3 text-center" style={{ background: "#d8cba8", border: "2px solid #3a2e1e", color: "#1a1206", minHeight: 130 }}>
            <p className="font-bold" style={{ color: "#7a1a10" }}>{game.menu.title}</p>
            <ol className="mt-1 grid gap-0.5">
              {game.menu.options.map((o, i) => (
                <li key={i}><button className="hover:underline" style={{ color: "#1a1206" }} onClick={() => game.choose(i)}>{o.text}</button></li>
              ))}
            </ol>
          </div>
        ) : d ? (
          <div className="p-3" style={{ background: "#d8cba8", border: "2px solid #3a2e1e", color: "#1a1206", minHeight: 130 }}>
            <p className="font-bold" style={{ color: "#7a1a10" }}>{d.name}</p>
            {d.answered ? (
              <>
                <p className="mt-1">{d.answered}</p>
                <button className="mt-2 text-xs underline" onClick={() => game?.next()}>Click here to continue (Space)</button>
              </>
            ) : d.at < d.lines.length ? (
              <>
                <p className="mt-1">{d.lines[d.at].text}</p>
                <button className="mt-2 text-xs underline" onClick={() => game?.next()}>Click here to continue (Space)</button>
              </>
            ) : d.question ? (
              <>
                <p className="mt-1 font-semibold">{d.question.ask}</p>
                <ol className="mt-1 grid gap-0.5">
                  {d.question.choices.map((c, i) => (
                    <li key={i}><button className="text-left hover:underline" onClick={() => game?.answer(c)}><b>{i + 1}.</b> {c.text}</button></li>
                  ))}
                </ol>
              </>
            ) : null}
          </div>
        ) : chatOpen ? (
          <div style={{ background: panelBox, border: "2px solid #000", color: "#f4efe6" }}>
            <div className="flex text-[11px]">
              {(["all", "game", "public"] as const).map((t) => (
                <button key={t} className={`px-3 py-1 ${chatTab === t ? "bg-black/40 font-semibold" : "opacity-70"}`} onClick={() => setChatTab(t)}>{t === "all" ? "All" : t === "game" ? "Game" : "Public"}</button>
              ))}
              <button className="ml-auto px-2 opacity-70" onClick={() => setChatOpen(false)} aria-label="Fold the chat">&#9662;</button>
            </div>
            <div className="h-[118px] overflow-y-auto px-2 py-1 flex flex-col-reverse">
              <div>
                {[...lines.map((l) => ({ at: l.at, el: <p key={`l${l.at}${l.text}`} style={{ color: l.kind === "quest" ? "#ffb03a" : l.kind === "xp" ? "#ffe24a" : l.kind === "loot" ? "#ff9a3a" : l.kind === "combat" ? "#ff8a7a" : "#f4efe6" }}>{l.text}</p> })),
                  ...pub.map((m) => ({ at: Date.parse(m.at), el: <p key={`c${m.id}`}><b style={{ color: m.staff ? "#ffe24a" : "#9ad0ff" }}>{m.name}:</b> {m.text}</p> }))]
                  .sort((a, b) => a.at - b.at).slice(-80).map((x) => x.el)}
                {!lines.length && !pub.length && <p className="opacity-60">Welcome to the Portal. Right-click anything to see what you can do with it.</p>}
              </div>
            </div>
            <form className="flex border-t border-black/50" onSubmit={async (e) => {
              e.preventDefault();
              const t = draft.trim();
              if (!t) return;
              try { await chat.send(t); setDraft(""); } catch (err) { store.say((err as Error).message); }
            }}>
              <input ref={input} className="flex-1 bg-transparent px-2 py-1 outline-none text-[13px] placeholder:text-white/40" maxLength={200} value={draft} onChange={(e) => setDraft(e.target.value)}
                placeholder={signedIn ? "Press Enter to talk in public chat" : "Sign in to talk in public chat"} disabled={!signedIn} />
            </form>
          </div>
        ) : (
          <button className="px-3 py-1 text-xs" style={{ background: panelBox, border: "2px solid #000", color: "#f4efe6" }} onClick={() => setChatOpen(true)}>Chat &#9652;</button>
        )}
      </div>

      {/* the action bar */}
      <div className={`absolute bottom-3 max-[1180px]:bottom-[200px] left-1/2 -translate-x-1/2 ${tab === "tool" ? "max-[1180px]:left-3 max-[1180px]:translate-x-0" : ""} flex items-end gap-2 max-sm:bottom-auto max-sm:top-[190px] max-sm:left-auto max-sm:right-3 max-sm:translate-x-0 max-sm:flex-col`} style={{ zIndex: 6, display: hidden ? "none" : undefined }}>
        <div className="flex gap-1 p-1 max-sm:flex-col" style={{ background: panelBox, border: "2px solid #000" }} role="toolbar" aria-label="Action bar">
          {Array.from({ length: BAR_SIZE }, (_, i) => {
            const k = s.bar[i];
            const a = k ? (k.startsWith("item:") ? (() => { const it = itemById(k.slice(5)); return it ? { label: it.name, icon: it.icon, hint: `Use ${it.name}` } : null; })() : ACTIONS[k]) : null;
            return (
              <button key={i} className="relative w-10 h-10 grid place-items-center text-lg hover:bg-black/30 max-sm:w-9 max-sm:h-9" title={a ? `${i + 1}: ${a.hint}` : `${i + 1}: empty`}
                style={{ background: "#3a3226", border: "1px solid #000", color: "#fff" }} onClick={() => doAction(k)}
                onContextMenu={(e) => { e.preventDefault(); if (k) { s.bar[i] = null; store.emit(); } }}>
                <span>{a?.icon ?? ""}</span>
                <span className="absolute left-0.5 top-0 text-[9px] opacity-80">{i + 1}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* the control panel: tabs above and below one box, Old School RuneScape's */}
      <div className={`absolute right-3 bottom-3 ${tab === "tool" ? "w-[min(400px,calc(100%-24px))]" : "w-[min(252px,calc(100%-24px))]"}`} style={{ zIndex: 5, display: hidden ? "none" : undefined }}>
        <div className="flex" role="tablist" style={{ ...stone, borderBottom: tab ? "none" : undefined }}>
          {TOP.map((t) => {
            const off = t.key === "tool" && !tool;
            return (
              <button key={t.key} role="tab" aria-selected={tab === t.key} disabled={off} title={off ? "No controls in this area" : `${t.key === "tool" && tool ? tool.title : t.label} (${t.hot})`}
                className="flex-1 h-8 grid place-items-center text-base disabled:opacity-30" onClick={() => setTab(tab === t.key ? null : t.key)}
                style={{ ...tabBtn(tab === t.key), ...(t.key === "tool" && tool ? { boxShadow: `inset 0 -3px 0 ${tool.colour}` } : {}) }}>{t.key === "tool" && tool?.icon ? tool.icon : t.icon}</button>
            );
          })}
        </div>
        {tab && (
          <div className={`p-2 overflow-y-auto text-[12px] ${tab === "tool" ? "h-[min(540px,56vh)]" : "h-[min(300px,42vh)]"}`} style={{ ...stone, borderTop: "none", borderBottom: "none" }}>
            {tab === "combat" && (() => {
              const w = store.weapon(), worn = s.worn.weapon ? itemById(s.worn.weapon) : null;
              const names = ["Accurate", "Controlled", "Defensive"], gives = ["Attack XP", "Attack, Strength and Defence XP", "Defence XP"];
              return (
                <div className="grid gap-2">
                  <div className="flex items-center justify-between">
                    <p className="font-bold">{worn ? `${worn.icon} ${worn.name}` : "Unarmed"}</p>
                    <p>Combat Lvl: <b style={{ color: "#ffe24a" }}>{combatLevel((k) => store.level(k))}</b></p>
                  </div>
                  <div className="grid grid-cols-2 gap-1">
                    {w.styles.map((st, i) => (
                      <button key={st} className="p-2 text-left" style={{ background: s.style === i ? "#7a3a1a" : "#2b241a", border: "1px solid #000" }} onClick={() => game?.setStyle(i)}>
                        <b>{st}</b><span className="block opacity-80">{names[i]}</span><span className="block text-[10px] opacity-60">{gives[i]}</span>
                      </button>
                    ))}
                  </div>
                  {w.spec ? (
                    <button className="relative h-7 w-full text-[11px] font-semibold" title={`${w.spec.name}: ${w.spec.blurb} Costs ${w.spec.cost}%.`}
                      style={{ background: "#1a1a1a", border: `1px solid ${game?.specOn ? "#ffe24a" : "#000"}` }} onClick={() => game?.toggleSpec()}>
                      <span className="absolute inset-y-0 left-0" style={{ width: `${s.spec}%`, background: game?.specOn ? "#c8a21a" : "#3a8a2a" }} />
                      <span className="relative">Special attack: {Math.floor(s.spec)}%{game?.specOn ? " (armed)" : ""}</span>
                    </button>
                  ) : <p className="opacity-60">This weapon has no special attack.</p>}
                  {w.spec && <p className="opacity-70">{w.spec.name}: {w.spec.blurb} Costs {w.spec.cost}%; refills 10% every 30 seconds.</p>}
                </div>
              );
            })()}
            {tab === "worn" && (() => {
              const worn = s.worn.weapon ? itemById(s.worn.weapon) : null, w = store.weapon();
              const slot = (label: string, content?: ReactNode, onClick?: () => void, title?: string) => (
                <button key={label} className="w-11 h-11 grid place-items-center text-xl" style={{ background: "#2b241a", border: "1px solid #000", opacity: content ? 1 : 0.45 }}
                  title={title || `${label}: empty`} onClick={onClick} disabled={!onClick}>{content ?? <span className="text-[9px] opacity-70">{label}</span>}</button>
              );
              return (
                <div className="grid gap-3">
                  <div className="grid gap-1 justify-center" style={{ gridTemplateColumns: "repeat(3, 44px)" }}>
                    <span />{slot("Head")}<span />
                    {slot("Cape")}{slot("Neck")}{slot("Ammo")}
                    {slot("Weapon", worn?.icon, worn ? () => game?.unwield() : undefined, worn ? `${worn.name}: click to remove` : undefined)}{slot("Body")}{slot("Shield")}
                    <span />{slot("Legs")}<span />
                    {slot("Hands")}{slot("Feet")}{slot("Ring")}
                  </div>
                  <div style={{ background: "#2b241a", border: "1px solid #000" }} className="p-2">
                    <p className="font-semibold">Equipment bonuses</p>
                    <p>Attack: +{w.attack}</p><p>Strength: +{w.strength}</p>
                    <p>Speed: {w.speed} ticks ({(w.speed * 0.6).toFixed(1)} s)</p>
                  </div>
                  <p className="opacity-60">Right-click a weapon in your bag and Wield it to change weapons.</p>
                </div>
              );
            })()}
            {/* not while fullscreen holds the tool: the slot mounts again after, and takes it back */}
            {tab === "tool" && tool && !hidden && (
              <div className="grid gap-2" style={{ color: "var(--ink)" }}>
                <div className="flex items-center justify-between gap-2 px-1" style={{ color: "#f4efe6" }}>
                  <p className="font-bold" style={{ color: tool.colour }}>{tool.title}</p>
                  {tool.fullscreen && <button className="text-[11px] px-2 py-0.5" style={{ background: "#2b241a", border: "1px solid #000" }} onClick={tool.fullscreen} title="Stand inside it, first person, with these controls beside you">&#x26F6; Fullscreen</button>}
                </div>
                <HostSlot host={tool.host} className="panel p-3 text-sm" />
              </div>
            )}
            {tab === "inv" && (
              <div className="grid grid-cols-4 gap-1">
                {s.inv.map((x, i) => {
                  const it = x && itemById(x.id);
                  return (
                    <button key={i} className="relative h-11 grid place-items-center text-xl hover:bg-black/30" style={{ border: "1px solid rgba(0,0,0,.35)" }}
                      title={it ? `${it.name}${x!.n > 1 ? ` x${x!.n}` : ""}: ${it.examine}` : "Empty"}
                      onClick={() => game?.use(i)}
                      onContextMenu={(e) => {
                        e.preventDefault();
                        if (!it || !game) return;
                        const opts: Option[] = [
                          { label: it.heals ? "Eat" : it.lore ? "Read" : it.weapon ? "Wield" : "Use", target: it.name, colour: "#ff9a3a", run: () => game.use(i) },
                          { label: "Put on action bar", target: it.name, colour: "#ff9a3a", run: () => { const free = s.bar.indexOf(null); if (free < 0) store.say("Your action bar is full. Right-click a slot to empty it."); else { s.bar[free] = `item:${it.id}`; store.emit(); } } },
                          { label: "Examine", target: it.name, colour: "#ff9a3a", run: () => store.say(it.examine) },
                          { label: "Drop", target: it.name, colour: "#ff9a3a", run: () => game.drop(i) },
                          { label: "Cancel", target: "", run: () => undefined },
                        ];
                        setMenu({ x: e.clientX, y: e.clientY, options: opts });
                      }}>
                      {it?.icon}
                      {x && x.n > 1 && <span className="absolute left-0.5 top-0 text-[10px] font-semibold" style={{ color: "#ffe24a" }}>{x.n > 99999 ? `${Math.floor(x.n / 1000)}K` : x.n}</span>}
                    </button>
                  );
                })}
              </div>
            )}
            {tab === "skills" && (() => {
              const lv = (k: SkillKey) => levelForXp(s.xp[k]);
              const open = skill ? SKILLS.find((k) => k.key === skill)! : null;
              if (open) {
                const xp = s.xp[open.key], l = lv(open.key), next = nextLevelXp(l);
                return (
                  <div className="grid gap-1.5">
                    <button className="underline text-[11px] text-left" onClick={() => setSkill(null)}>&larr; All skills</button>
                    <p className="font-bold text-sm">{open.icon} {open.name} <span style={{ color: "#ffe24a" }}>{l}</span></p>
                    <p className="opacity-80">{STAGES.find((x) => x.key === open.stage)!.name}</p>
                    <p>{open.blurb}</p>
                    <p>{xp.toLocaleString()} XP{l < 99 ? `; ${(next - xp).toLocaleString()} to level ${l + 1}` : ""}</p>
                    <p style={{ color: open.trainedBy ? "#3ac83a" : "#ffb03a" }}>{open.trainedBy ? `Trained by: ${open.trainedBy}` : "No way to train it in the world yet: it arrives as the house build mode does."}</p>
                  </div>
                );
              }
              return (
                <div className="grid gap-2">
                  {STAGES.map((st) => {
                    const list = SKILLS.filter((k) => k.stage === st.key);
                    return (
                      <div key={st.key}>
                        <p className="flex justify-between font-semibold text-[11px]" title={st.blurb}>
                          <span style={{ color: "#ffb03a" }}>{st.name}</span><span className="opacity-70">{list.reduce((a, k) => a + lv(k.key), 0)}</span>
                        </p>
                        <div className="grid grid-cols-3 gap-0.5 mt-0.5">
                          {list.map((k) => {
                            const xp = s.xp[k.key], l = lv(k.key), next = nextLevelXp(l);
                            const pct = l >= 99 ? 100 : ((xp - xpForLevel(l)) / (next - xpForLevel(l))) * 100;
                            return (
                              <button key={k.key} className="p-1 text-left" style={{ background: "#2b241a", border: "1px solid #000", opacity: k.trainedBy ? 1 : 0.7 }}
                                title={`${k.name}: ${k.blurb}\n${xp.toLocaleString()} XP${l < 99 ? `, ${(next - xp).toLocaleString()} to level ${l + 1}` : ""}\n${k.trainedBy ? `Trained by: ${k.trainedBy}` : "Not trainable in the world yet."}`}
                                onClick={() => setSkill(k.key)}>
                                <span className="flex justify-between items-baseline gap-1"><span className="truncate">{k.icon}</span><b style={{ color: "#ffe24a" }}>{l}</b></span>
                                <span className="block truncate text-[10px] opacity-80">{k.name}</span>
                                <span className="block h-0.5 mt-0.5 bg-black/50"><span className="block h-full" style={{ width: `${pct}%`, background: "#3ac83a" }} /></span>
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}
                  <p className="text-center">Total level: <b style={{ color: "#ffe24a" }}>{store.total()}</b> &middot; Combat: <b style={{ color: "#ffe24a" }}>{combatLevel(lv)}</b></p>
                  <p className="opacity-60 text-center">Every job a house takes, by the stage it happens in. Dimmed skills cannot be trained yet.</p>
                </div>
              );
            })()}
            {tab === "quests" && (
              journal ? (() => {
                const q = QUESTS.find((x) => x.id === journal)!, st = store.quest(q.id);
                return (
                  <div>
                    <button className="underline text-[11px]" onClick={() => setJournal(null)}>&larr; All quests</button>
                    <p className="font-bold mt-1" style={{ color: "#ffb03a" }}>{q.name}</p>
                    <p className="opacity-80 mt-0.5">{q.blurb}</p>
                    <ol className="mt-2 grid gap-1">
                      {q.steps.map((step, i) => (
                        <li key={i} style={{ opacity: i > st.stage ? 0.45 : 1, textDecoration: st.done || i < st.stage ? "line-through" : "none" }}>{step.task}</li>
                      ))}
                    </ol>
                    {st.done && <p className="mt-2" style={{ color: "#3ac83a" }}>QUEST COMPLETE -- {q.badge} badge</p>}
                    <p className="mt-2 opacity-70">Reward: {q.xp.toLocaleString()} {SKILLS.find((k) => k.key === q.skill)!.name} XP, {q.coins} credits, a lore page.</p>
                  </div>
                );
              })() : (
                <ul className="grid gap-1">
                  <li><button className="hover:underline" style={{ color: s.tut?.done ? "#3ac83a" : s.tut ? "#ffe24a" : "#ff6a5a" }}
                    onClick={() => window.dispatchEvent(new CustomEvent("portal-house", { detail: { to: "island" } }))}>Wedge Island (the tutorial){s.tut?.done ? ": go back" : ""}</button></li>
                  {QUESTS.map((q) => {
                    const st = store.quest(q.id);
                    return <li key={q.id}><button className="hover:underline" style={{ color: st.done ? "#3ac83a" : st.stage > 0 ? "#ffe24a" : "#ff6a5a" }} onClick={() => setJournal(q.id)}>{q.name}</button></li>;
                  })}
                  <li className="opacity-60 mt-2">Red: not started. Yellow: under way. Green: done.</li>
                </ul>
              )
            )}
            {tab === "badges" && (
              <div>
                <p className="font-semibold">Badges ({s.badges.length})</p>
                {s.badges.length ? <ul className="mt-1 grid gap-0.5">{s.badges.map((b) => <li key={b}>&#127941; {b}</li>)}</ul> : <p className="opacity-70 mt-1">Finish a quest to earn your first.</p>}
                <p className="font-semibold mt-3">Lore read ({s.read.length} of {LORE.length})</p>
                <ul className="mt-1 grid gap-0.5">
                  {LORE.map((l) => (
                    <li key={l.id}>{s.read.includes(l.id)
                      ? <button className="hover:underline text-left" onClick={() => setReading(l)}>&#128220; {l.title}</button>
                      : <span className="opacity-40">??? -- dropped by monsters, given by teachers</span>}</li>
                  ))}
                </ul>
                <p className="mt-3 opacity-70">Dome-owner badges and lesson accolades arrive with the network: visiting members' domes and attending their lessons.</p>
              </div>
            )}
            {tab === "keys" && (
              <div className="grid gap-2">
                {pick && game && (pick.thing || pick.gate) && (
                  <div>
                    <p className="font-semibold" style={{ color: "#ffe24a" }}>Under the pointer</p>
                    {game.options(pick).filter((o) => o.label !== "Cancel").map((o, i) => <p key={i}>{i === 0 ? "Left click" : "Right click"}: {o.label} {o.target}</p>)}
                  </div>
                )}
                {keyList.map(([scope, list]) => (
                  <div key={scope}>
                    <p className="font-semibold" style={{ color: "#ffe24a" }}>{scope}</p>
                    {list.map((k) => <p key={k.keys}><b>{k.keys}</b> -- {k.does}</p>)}
                  </div>
                ))}
              </div>
            )}
            {tab === "settings" && (
              <div className="grid gap-2">
                <p className="font-semibold">Settings</p>
                <label className="flex items-center justify-between gap-2"><span>Run (R)</span>
                  <input type="checkbox" checked={s.run} onChange={() => game?.toggleRun()} /></label>
                <label className="flex items-center justify-between gap-2"><span>Auto retaliate</span>
                  <input type="checkbox" checked={game?.autoRetaliate ?? true} onChange={() => { if (game) { game.autoRetaliate = !game.autoRetaliate; bump((n) => n + 1); } }} /></label>
                <p className="opacity-70">Run energy: {Math.floor(s.energy)}%. It drains while you run and comes back while you walk or stand.</p>
              </div>
            )}
          </div>
        )}
        <div className="flex" style={{ ...stone, borderTop: tab ? "none" : undefined }}>
          {[
            { key: "keys", icon: "⌨", label: "Keys and controls (?)", on: tab === "keys", run: () => setTab(tab === "keys" ? null : "keys") },
            { key: "settings", icon: "⚙", label: "Settings", on: tab === "settings", run: () => setTab(tab === "settings" ? null : "settings") },
            { key: "map", icon: "\u{1f5fa}", label: "World map", on: false, run: onWorldMap },
            { key: "home", icon: "\u{1f3e0}", label: "Home: back to the plaza", on: false, run: onHome },
            { key: "full", icon: "⛶", label: tool?.fullscreen ? "Fullscreen: stand inside this portal's model" : "No fullscreen in this area", on: false, run: tool?.fullscreen },
            { key: "chat", icon: "\u{1f4ac}", label: chatOpen ? "Fold the chat" : "Open the chat", on: chatOpen, run: () => setChatOpen(!chatOpen) },
            { key: "hide", icon: "▾", label: "Fold this panel", on: false, run: () => setTab(null) },
          ].map((b) => (
            <button key={b.key} className="flex-1 h-8 grid place-items-center text-base disabled:opacity-30" title={b.label} aria-label={b.label}
              disabled={!b.run} onClick={b.run} style={tabBtn(b.on)}>{b.icon}</button>
          ))}
        </div>
      </div>

      {/* a lore page, open */}
      {reading && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/50 p-4" onClick={() => setReading(null)}>
          <div className="max-w-lg w-full p-6 shadow-2xl" style={{ background: "#f0e2bc", border: "3px solid #5a3a1a", color: "#2a1a0a" }} onClick={(e) => e.stopPropagation()}>
            <p className="text-xs uppercase tracking-widest" style={{ color: "#7a3a1a" }}>Lore -- {SKILLS.find((k) => k.key === reading.skill)!.name}</p>
            <h2 className="text-2xl font-bold mt-1">{reading.title}</h2>
            {reading.text.map((t, i) => <p key={i} className="mt-3 leading-relaxed">{t}</p>)}
            <button className="mt-5 underline" onClick={() => setReading(null)}>Close (Esc)</button>
          </div>
        </div>
      )}
    </>
  );
}
