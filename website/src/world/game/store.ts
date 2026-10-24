// The player, across the whole world: skills, hitpoints, inventory, quests, lore read, badges,
// the action bar and the game log. One store lives for the visit; each area's game (area.ts)
// reads and changes it. Saved in the browser for everyone, and to the account for members.

import { HOUSE_STYLES, ITEMS, LORE, QUESTS, SKILLS, START_ITEMS, START_LEVELS, START_WEAPON, itemById, levelForXp, xpForLevel, type SkillKey, type Weapon } from "./content";

export const INV_SIZE = 28;
export const BAR_SIZE = 8;

export interface Slot { id: string; n: number }
export interface QuestState { stage: number; kills?: number; done?: boolean }
export interface Save {
  v: 1;
  xp: Record<SkillKey, number>;
  hp: number;
  inv: (Slot | null)[];
  quests: Record<string, QuestState>;
  read: string[];
  badges: string[];
  bar: (string | null)[];
  kills: Record<string, number>;
  /** How this member's house is built: a key of HOUSE_STYLES. */
  house?: string;
  /** Wedge Island, the tutorial: the step reached, a count within it, and whether it is done. */
  tut?: { step: number; n: number; done?: boolean };
  /** What is worn, by slot (only the weapon slot holds anything yet). */
  worn: { weapon: string | null };
  /** The combat style: 0, 1 or 2 -- accurate, controlled, defensive (the weapon names them). */
  style: number;
  /** Special attack energy and run energy, 0 to 100; whether running is on. */
  spec: number;
  energy: number;
  run: boolean;
  /** The start every character gets (START_LEVELS and START_WEAPON) has been given: saves from
   *  before it get it once, on load. */
  start: number;
}
export interface LogLine { text: string; kind: "game" | "quest" | "loot" | "combat" | "chat" | "xp"; at: number; who?: string }

export const DEFAULT_BAR = ["eat", "read", "attack", "take", "talk", "home", "keys", null];

/** Which start a save has had: raise it when the start changes, and older saves get the new one. */
const START = 2;

/** The starting levels' XP, with the hitpoints XP that earning them would have given: every
 *  4 combat XP brings 1.33 hitpoints XP (area.ts), as in RuneScape. */
function startXp(): Partial<Record<SkillKey, number>> {
  const out: Partial<Record<SkillKey, number>> = {};
  for (const [k, lv] of Object.entries(START_LEVELS)) out[k as SkillKey] = xpForLevel(lv!);
  const combat = (["attack", "strength", "defence"] as const).reduce((a, k) => a + (out[k] ?? 0), 0);
  out.hitpoints = (out.hitpoints ?? xpForLevel(10)) + Math.round((combat * 1.33) / 4);
  return out;
}

export function fresh(): Save {
  const xp = Object.fromEntries(SKILLS.map((s) => [s.key, 0])) as Record<SkillKey, number>;
  Object.assign(xp, startXp());
  const inv: (Slot | null)[] = Array(INV_SIZE).fill(null);
  START_ITEMS.forEach(([id, n], i) => { inv[i] = { id, n }; });
  return { v: 1, xp, hp: levelForXp(xp.hitpoints), inv, quests: {}, read: [], badges: [], bar: [...DEFAULT_BAR], kills: {},
    worn: { weapon: START_WEAPON }, style: 0, spec: 100, energy: 100, run: false, start: START };
}

/** The XP a brand-new character has: progress is anything beyond it. */
const FRESH_XP = Object.values(fresh().xp).reduce((a, b) => a + b, 0);

/** Bring an old or partial save up to date, dropping anything no longer in the game. */
export function clean(s: Partial<Save> | null | undefined): Save {
  const f = fresh();
  if (!s || s.v !== 1) return f;
  const known = new Set(ITEMS.map((i) => i.id));
  const num = (x: unknown, lo: number, hi: number, d: number) => (typeof x === "number" && isFinite(x) ? Math.min(hi, Math.max(lo, x)) : d);
  const weapon = s.worn?.weapon && itemById(s.worn.weapon)?.weapon ? s.worn.weapon : null;
  const out: Save = {
    v: 1,
    xp: { ...f.xp, ...(s.xp || {}) },
    hp: typeof s.hp === "number" ? s.hp : f.hp,
    inv: Array.from({ length: INV_SIZE }, (_, i) => { const x = s.inv?.[i]; return x && known.has(x.id) && x.n > 0 ? { id: x.id, n: x.n } : null; }),
    quests: Object.fromEntries(Object.entries(s.quests || {}).filter(([k]) => QUESTS.some((q) => q.id === k))),
    read: (s.read || []).filter((r) => LORE.some((l) => l.id === r)),
    badges: [...new Set(s.badges || [])],
    bar: Array.from({ length: BAR_SIZE }, (_, i) => s.bar?.[i] ?? f.bar[i]),
    kills: { ...(s.kills || {}) },
    house: HOUSE_STYLES.some((h) => h.key === s.house) ? s.house : undefined,
    tut: s.tut && typeof s.tut.step === "number" ? { step: s.tut.step, n: Number(s.tut.n) || 0, done: Boolean(s.tut.done) } : undefined,
    worn: { weapon },
    style: num(s.style, 0, 2, 0) | 0,
    spec: num(s.spec, 0, 100, 100),
    energy: num(s.energy, 0, 100, 100),
    run: Boolean(s.run),
    start: num(s.start, 0, START, 0),
  };
  // a character from before the start: the levels and the weapon, once
  if (out.start < START) {
    for (const [k, x] of Object.entries(startXp())) out.xp[k as SkillKey] = Math.max(out.xp[k as SkillKey], x!);
    out.hp = levelForXp(out.xp.hitpoints);
    if (!out.worn.weapon) out.worn.weapon = START_WEAPON;
    if (!out.inv.some((x) => x?.id === "chainsaw")) { const free = out.inv.indexOf(null); if (free >= 0) out.inv[free] = { id: "chainsaw", n: 1 }; }
    out.start = START;
  }
  return out;
}

const LOCAL = "zl.portal.v1";
export function loadLocal(): Save {
  try { return clean(JSON.parse(localStorage.getItem(LOCAL) || "null")); } catch { return fresh(); }
}
export function saveLocal(s: Save) {
  try { localStorage.setItem(LOCAL, JSON.stringify(s)); } catch { /* private mode: the visit keeps it */ }
}

/** Progress worth keeping: anything beyond a fresh start. */
export const hasProgress = (s: Save) =>
  Object.keys(s.quests).length > 0 || s.read.length > 0 || Object.values(s.xp).reduce((a, b) => a + b, 0) > FRESH_XP;

export class Store {
  s: Save;
  log: LogLine[] = [];
  private subs = new Set<() => void>();
  version = 0;

  constructor(save: Save) { this.s = save; }

  subscribe(f: () => void) { this.subs.add(f); return () => { this.subs.delete(f); }; }
  emit() { this.version++; saveLocal(this.s); for (const f of this.subs) f(); }

  say(text: string, kind: LogLine["kind"] = "game", who?: string) {
    this.log = [...this.log.slice(-79), { text, kind, at: Date.now(), who }];
    this.emit();
  }

  level(skill: SkillKey) { return levelForXp(this.s.xp[skill]); }
  maxHp() { return this.level("hitpoints"); }
  total() { return SKILLS.reduce((a, s) => a + this.level(s.key), 0); }

  /** Add XP; says so, and announces a level gained. Returns the XP added. */
  addXp(skill: SkillKey, amount: number) {
    const before = this.level(skill);
    this.s.xp[skill] = Math.min(200_000_000, this.s.xp[skill] + Math.round(amount));
    const after = this.level(skill);
    const name = SKILLS.find((k) => k.key === skill)!.name;
    if (after > before) this.say(`Congratulations, you just advanced a ${name} level. You are now level ${after}.`, "xp");
    this.emit();
    return amount;
  }

  count(id: string) { return this.s.inv.reduce((a, x) => a + (x && x.id === id ? x.n : 0), 0); }
  freeSlots() { return this.s.inv.filter((x) => !x).length; }

  /** Put items in the bag. Stackables share a slot. Returns how many fitted. */
  give(id: string, n = 1): number {
    const item = itemById(id);
    if (!item || n <= 0) return 0;
    if (item.stack) {
      const at = this.s.inv.findIndex((x) => x && x.id === id);
      if (at >= 0) this.s.inv[at]!.n += n;
      else { const free = this.s.inv.indexOf(null); if (free < 0) return 0; this.s.inv[free] = { id, n }; }
      this.emit();
      return n;
    }
    let given = 0;
    for (let i = 0; i < n; i++) {
      const free = this.s.inv.indexOf(null);
      if (free < 0) break;
      this.s.inv[free] = { id, n: 1 }; given++;
    }
    this.emit();
    return given;
  }

  take(id: string, n = 1): boolean {
    if (this.count(id) < n) return false;
    let left = n;
    for (let i = 0; i < this.s.inv.length && left > 0; i++) {
      const x = this.s.inv[i];
      if (!x || x.id !== id) continue;
      const k = Math.min(left, x.n);
      x.n -= k; left -= k;
      if (x.n <= 0) this.s.inv[i] = null;
    }
    this.emit();
    return true;
  }

  removeSlot(i: number) { this.s.inv[i] = null; this.emit(); }

  /** The weapon in hand, or bare fists. */
  weapon(): Weapon {
    return (this.s.worn.weapon && itemById(this.s.worn.weapon)?.weapon) || { look: "whip", attack: 0, strength: 0, speed: 4, styles: ["Punch", "Kick", "Block"] };
  }

  /** Wield a weapon from the bag (what was in hand goes back in the bag), or put it away. */
  wield(slot: number) {
    const x = this.s.inv[slot], item = x && itemById(x.id);
    if (!x || !item?.weapon) return false;
    const was = this.s.worn.weapon;
    this.s.inv[slot] = x.n > 1 ? { id: x.id, n: x.n - 1 } : null;
    this.s.worn.weapon = item.id;
    if (was) this.give(was, 1);
    this.say(`You wield the ${item.name}.`);
    this.emit();
    return true;
  }
  unwield() {
    const was = this.s.worn.weapon;
    if (!was) return;
    if (!this.freeSlots()) { this.say("You don't have enough inventory space."); return; }
    this.s.worn.weapon = null;
    this.give(was, 1);
    this.say(`You put away the ${itemById(was)!.name}.`);
  }

  quest(id: string): QuestState { return this.s.quests[id] || { stage: 0 }; }
  setQuest(id: string, q: QuestState) { this.s.quests[id] = q; this.emit(); }
}
