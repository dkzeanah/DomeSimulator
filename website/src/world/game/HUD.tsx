// The Portal world's interface, laid out the way RuneScape players expect: hover text top
// left, a right-click menu where you click, the chatbox bottom left (dialogue shows there too),
// the side panel bottom right (inventory, skills, quests, badges, keys), the hitpoints orb and
// the action bar along the bottom.

import { useEffect, useMemo, useRef, useState } from "react";
import type { Pick } from "../engine";
import type { AreaGame, Option } from "./area";
import { useChat } from "./chat";
import { LORE, QUESTS, SKILLS, itemById, levelForXp, nextLevelXp, xpForLevel, type Lore } from "./content";
import { registerKeys, typing, useKeyList } from "./keys";
import { BAR_SIZE, type Store } from "./store";

type Tab = "inv" | "skills" | "quests" | "badges" | "keys";
const TABS: { key: Tab; label: string; icon: string; hot: string }[] = [
  { key: "inv", label: "Inventory", icon: "\u{1f392}", hot: "I" },
  { key: "skills", label: "Skills", icon: "\u{1f4ca}", hot: "K" },
  { key: "quests", label: "Quests", icon: "\u{1f4dc}", hot: "J" },
  { key: "badges", label: "Badges", icon: "\u{1f3c5}", hot: "B" },
  { key: "keys", label: "Keys", icon: "⌨", hot: "?" },
];

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

export default function HUD({ store, game, pick, menuAt, onMenuClosed, signedIn, folded, onSidePanel }: {
  store: Store; game: AreaGame | null; pick: Pick | null; menuAt: Pick | null; onMenuClosed: () => void; signedIn: boolean;
  /** Start with the side panel folded (a tool's space, where the tool's own panel wants the room). */
  folded?: boolean;
  onSidePanel?: (open: boolean) => void;
}) {
  const [, bump] = useState(0);
  useEffect(() => store.subscribe(() => bump((n) => n + 1)), [store]);
  const [tab, setTab] = useState<Tab | null>(() => (folded || (typeof window !== "undefined" && window.innerWidth < 640) ? null : "inv"));
  useEffect(() => { if (folded) setTab(null); }, [folded]);
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
    { keys: "I K J B", does: "Inventory, skills, quest journal, badges" },
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

  const hp = s.hp, max = store.maxHp();
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
      <div className="absolute left-3 bottom-3 w-[min(460px,calc(100%-24px))] text-[13px]" style={{ zIndex: 5 }}>
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

      {/* hitpoints and the action bar */}
      <div className={`absolute bottom-3 max-[1180px]:bottom-[200px] left-1/2 -translate-x-1/2 ${folded ? "max-[1180px]:left-3 max-[1180px]:translate-x-0" : ""} flex items-end gap-2 max-sm:bottom-auto max-sm:top-[118px] max-sm:left-auto max-sm:right-3 max-sm:translate-x-0 max-sm:flex-col`} style={{ zIndex: 6 }}>
        <div className="w-12 h-12 rounded-full grid place-items-center text-sm font-bold shadow-lg" title="Hitpoints"
          style={{ background: `conic-gradient(#c82a1a ${(hp / max) * 360}deg, #3a1a14 0)`, border: "2px solid #000", color: "#fff", textShadow: "0 1px 1px #000" }}>
          {hp}
        </div>
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

      {/* the side panel */}
      <div className="absolute right-3 bottom-3 w-[min(250px,calc(100%-24px))]" style={{ zIndex: 5 }}>
        {tab && (
          <div className="p-2 mb-1 h-[min(300px,45vh)] overflow-y-auto text-[12px]" style={{ background: panelBox, border: "2px solid #000", color: "#f4efe6" }}>
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
                          { label: it.heals ? "Eat" : it.lore ? "Read" : "Use", target: it.name, colour: "#ff9a3a", run: () => game.use(i) },
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
            {tab === "skills" && (
              <>
                <div className="grid grid-cols-2 gap-1">
                  {SKILLS.map((k) => {
                    const xp = s.xp[k.key], lv = levelForXp(xp), next = nextLevelXp(lv);
                    const pct = lv >= 99 ? 100 : ((xp - xpForLevel(lv)) / (next - xpForLevel(lv))) * 100;
                    return (
                      <div key={k.key} className="p-1 relative" style={{ background: "#3a3226", border: "1px solid #000" }} title={`${k.name}: ${k.blurb}\n${xp.toLocaleString()} XP${lv < 99 ? `, ${(next - xp).toLocaleString()} to level ${lv + 1}` : ""}`}>
                        <div className="flex justify-between"><span>{k.icon} {k.name}</span><b style={{ color: "#ffe24a" }}>{lv}</b></div>
                        <div className="h-1 mt-0.5 bg-black/50"><div className="h-full" style={{ width: `${pct}%`, background: "#3ac83a" }} /></div>
                      </div>
                    );
                  })}
                </div>
                <p className="mt-2 text-center">Total level: <b style={{ color: "#ffe24a" }}>{store.total()}</b></p>
              </>
            )}
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
          </div>
        )}
        <div className="flex gap-1 justify-end" role="tablist">
          {TABS.map((t) => (
            <button key={t.key} role="tab" aria-selected={tab === t.key} title={`${t.label} (${t.hot})`}
              className="w-9 h-8 grid place-items-center text-base" onClick={() => setTab(tab === t.key ? null : t.key)}
              style={{ background: tab === t.key ? "#7a3a1a" : "#3a3226", border: "2px solid #000", color: "#fff" }}>{t.icon}</button>
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
