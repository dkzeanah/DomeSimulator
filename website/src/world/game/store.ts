// The player, across the whole world: skills, hitpoints, inventory, quests, lore read, badges,
// the action bar and the game log. One store lives for the visit; each area's game (area.ts)
// reads and changes it. Saved in the browser for everyone, and to the account for members.

import { HOUSE_STYLES, ITEMS, LORE, QUESTS, SKILLS, START_ITEMS, itemById, levelForXp, xpForLevel, type SkillKey } from "./content";

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
}
export interface LogLine { text: string; kind: "game" | "quest" | "loot" | "combat" | "chat" | "xp"; at: number; who?: string }

export const DEFAULT_BAR = ["eat", "read", "attack", "take", "talk", "home", "keys", null];

export function fresh(): Save {
  const xp = Object.fromEntries(SKILLS.map((s) => [s.key, 0])) as Record<SkillKey, number>;
  xp.hitpoints = xpForLevel(10);   // RuneScape starts everyone at level 10 hitpoints
  const inv: (Slot | null)[] = Array(INV_SIZE).fill(null);
  START_ITEMS.forEach(([id, n], i) => { inv[i] = { id, n }; });
  return { v: 1, xp, hp: 10, inv, quests: {}, read: [], badges: [], bar: [...DEFAULT_BAR], kills: {} };
}

/** Bring an old or partial save up to date, dropping anything no longer in the game. */
export function clean(s: Partial<Save> | null | undefined): Save {
  const f = fresh();
  if (!s || s.v !== 1) return f;
  const known = new Set(ITEMS.map((i) => i.id));
  return {
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
  };
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
  Object.keys(s.quests).length > 0 || s.read.length > 0 || Object.values(s.xp).reduce((a, b) => a + b, 0) > xpForLevel(10);

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

  /** The best tool in the bag for fighting: its power. */
  power() {
    return this.s.inv.reduce((best, x) => Math.max(best, (x && itemById(x.id)?.power) || 0), 0);
  }

  quest(id: string): QuestState { return this.s.quests[id] || { stage: 0 }; }
  setQuest(id: string, q: QuestState) { this.s.quests[id] = q; this.emit(); }
}
