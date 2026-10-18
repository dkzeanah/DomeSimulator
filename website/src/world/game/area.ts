// One area's game: the teachers, monsters, objects and loot standing in it, what a click or a
// right-click on each of them offers, combat on RuneScape's 0.6-second tick, drops, and quest
// progress. The player lives in the Store; this runs while the area is open.

import { Thing, World, type Pick } from "../engine";
import { idle, logPileMesh, lootMesh, monsterMesh, npcMesh } from "../entities";
import {
  F, MONSTERS, NPCS, OBJECTS, QUESTS, SPAWNS, TALK, itemById, loreById, monsterById, npcById, questById,
  type Choice, type Line, type Monster,
} from "./content";
import type { Store } from "./store";

export const TICK_MS = 600;
const MELEE = 3.3;          // ft: close enough to swing
const LEASH = 22;           // ft from home before a monster gives up
const LOOT_TICKS = 150;     // 90 s on the ground

export interface Option { label: string; target: string; colour?: string; run: () => void }
export interface Dialog { npc: string; name: string; lines: Line[]; at: number; question?: { ask: string; choices: Choice[] }; answered?: string }

interface Mob { key: string; def: Monster; home: [number, number]; roam: number; hp: number; deadUntil: number; cool: number; angry: boolean; nextRoam: number }
interface Loot { key: string; items: { id: string; n: number }[]; until: number }

const rnd = (a: number, b: number) => a + Math.floor(Math.random() * (b - a + 1));

export class AreaGame {
  tick = 0;
  dialog: Dialog | null = null;
  fighting: string | null = null;
  private mobs = new Map<string, Mob>();
  private loot = new Map<string, Loot>();
  private cool = 0;
  private timer: number;
  private splitting = 0;
  private lootSeq = 0;
  private onCreator = (e: Event) => this.creatorSeen((e as CustomEvent).detail);

  constructor(private world: World, readonly area: string, private store: Store, private changed: () => void) {
    for (const n of NPCS.filter((n) => n.area === area)) {
      this.world.addThing({ id: `npc:${n.id}`, kind: "npc", name: n.name }, npcMesh(n.colour, n.hair), n.at[0], n.at[1],
        { facing: Math.atan2(-n.at[0], -n.at[1]) + Math.PI, height: 5.6, animate: idle });
    }
    for (const o of OBJECTS.filter((o) => o.area === area)) {
      this.world.addThing({ id: `obj:${o.id}`, kind: "object", name: o.name }, logPileMesh(), o.at[0], o.at[1], { height: 3 });
    }
    SPAWNS.filter((s) => s.area === area).forEach((s, i) => {
      const def = monsterById(s.monster);
      const key = `mob:${def.id}:${i}`;
      this.mobs.set(key, { key, def, home: s.at, roam: s.roam, hp: def.hp, deadUntil: 0, cool: 0, angry: false, nextRoam: rnd(2, 12) });
      this.spawn(key);
    });
    window.addEventListener("dome-creator-design", this.onCreator);
    this.timer = window.setInterval(() => this.step(), TICK_MS);
    this.markers();
  }

  dispose() {
    window.clearInterval(this.timer);
    window.removeEventListener("dome-creator-design", this.onCreator);
  }

  private spawn(key: string) {
    const m = this.mobs.get(key)!;
    m.hp = m.def.hp; m.angry = false; m.cool = 0;
    this.world.addThing({ id: key, kind: "monster", name: m.def.name, level: m.def.level }, monsterMesh(m.def.shape, m.def.colour, m.def.size),
      m.home[0], m.home[1], { speed: 3.2, height: 3.2 * m.def.size, animate: idle });
  }

  /** The yellow marker floats over a teacher who has something new for you. */
  private markers() {
    for (const n of NPCS.filter((n) => n.area === this.area)) {
      const g = this.world.thingObject(`npc:${n.id}`);
      const mark = g?.getObjectByName("marker");
      if (!mark) continue;
      const q = QUESTS.find((x) => x.teacher === n.id);
      const st = q ? this.store.quest(q.id) : null;
      mark.visible = Boolean(q && st && !st.done && (st.stage === 0 || this.readyToAnswer(q.id)));
    }
  }

  private readyToAnswer(quest: string) {
    const st = this.store.quest(quest);
    return (quest === "twenty" && st.stage === 3) || (quest === "split" && st.stage === 2) || (quest === "water" && st.stage === 2);
  }

  // -------------------------------------------------------------- what a click offers
  options(p: Pick): Option[] {
    const o: Option[] = [];
    const t = p.thing;
    if (t?.kind === "monster") {
      const m = this.mobs.get(t.id);
      if (m) o.push({ label: "Attack", target: `${m.def.name} (level-${m.def.level})`, colour: "#ffe24a", run: () => this.attack(t.id) });
    }
    if (t?.kind === "npc") {
      const n = npcById(t.id.slice(4));
      o.push({ label: "Talk-to", target: n.name, colour: "#ffe24a", run: () => this.talk(n.id) });
    }
    if (t?.kind === "object") o.push({ label: "Split", target: t.name, colour: "#3ad6ff", run: () => this.split(t.id) });
    if (t?.kind === "loot") {
      const l = this.loot.get(t.id);
      for (const it of l?.items ?? []) {
        const item = itemById(it.id)!;
        o.push({ label: "Take", target: `${item.name}${it.n > 1 ? ` (${it.n})` : ""}`, colour: "#ff9a3a", run: () => this.takeLoot(t.id, it.id) });
      }
    }
    if (p.part && !t && !p.gate) {
      const part = p.part;
      o.push({ label: "Inspect", target: part.name, colour: "#3ad6ff", run: () => window.dispatchEvent(new CustomEvent("portal-part", { detail: part })) });
      if (part.examine) o.push({ label: "Examine", target: part.name, colour: "#3ad6ff", run: () => this.store.say(part.examine!) });
    }
    if (p.gate) o.push({ label: "Enter", target: p.gate.name, colour: p.gate.colour, run: () => this.world.walkPoint(p.gate!.at.x, p.gate!.at.y) });
    if (p.ground && !t && !p.gate && !p.part) o.push({ label: "Walk here", target: "", run: () => { this.fighting = null; this.world.walkPoint(p.ground!.x, p.ground!.z); } });
    if (t) o.push({ label: "Examine", target: t.kind === "monster" ? `${t.name} (level-${t.level})` : t.name, colour: "#3ad6ff", run: () => this.examine(t) });
    if (p.gate) o.push({ label: "Examine", target: p.gate.name, colour: "#3ad6ff", run: () => this.store.say(p.gate!.key === "hub" ? "The way back to the hilltop." : `The gateway to ${p.gate!.name}.`) });
    if (p.ground && (t || p.gate || p.part)) o.push({ label: "Walk here", target: "", run: () => { this.fighting = null; this.world.walkPoint(p.ground!.x, p.ground!.z); } });
    o.push({ label: "Cancel", target: "", run: () => undefined });
    return o;
  }

  /** A left click does the first option, as in RuneScape. Walking on open ground is the engine's. */
  click(p: Pick) {
    if (!p.thing && !p.gate && !p.part) { this.fighting = null; return; }
    this.options(p)[0]?.run();
  }

  // -------------------------------------------------------------- examine, talk, split, take
  examine(t: Thing) {
    if (t.kind === "monster") {
      const m = this.mobs.get(t.id)!;
      this.store.say(m.def.examine);
    } else if (t.kind === "npc") this.store.say(npcById(t.id.slice(4)).examine);
    else if (t.kind === "object") this.store.say(OBJECTS.find((o) => `obj:${o.id}` === t.id)!.examine);
    else if (t.kind === "loot") this.store.say("Something dropped here. Take it before it rots.");
    else if (t.kind === "dome") {
      this.store.say(`A 2V geodesic dome: ${F.struts} struts in two lengths (${F.strutsA} long at ${F.longIn} in, ${F.strutsB} short at ${F.shortIn} in), meeting at ${F.nodes} nodes, closing ${F.triangles} triangles. It is the raw-wedge solver's own dome.`);
      const q = this.store.quest("twenty");
      if (q.stage === 1) { this.store.setQuest("twenty", { stage: 2 }); this.store.say("Now go through the Dome Creator gateway and look at a 3V dome.", "quest"); }
    }
  }

  talk(npc: string) {
    this.world.walkNear(`npc:${npc}`, 3.6, () => {
      const n = npcById(npc);
      const q = QUESTS.find((x) => x.teacher === npc);
      const st = q ? this.store.quest(q.id) : { stage: 0 };
      const stage = st.done ? 99 : st.stage;
      const said = TALK[npc](stage);
      this.dialog = { npc, name: n.name, lines: said.lines, at: 0, question: said.question };
      if (q && st.stage === 0 && !st.done) {
        this.store.setQuest(q.id, { stage: 1 });
        this.store.say(`You have started a new quest: ${q.name}.`, "quest");
      }
      this.changed();
    });
  }

  /** Move a dialog on; at the end of the lines, show its question if it has one. */
  next() {
    const d = this.dialog;
    if (!d) return;
    if (d.answered) { this.dialog = null; this.changed(); this.markers(); return; }
    if (d.at < d.lines.length - 1) d.at++;
    else if (!d.question) this.dialog = null;
    else d.at = d.lines.length;          // the question is showing
    this.changed();
  }

  answer(c: Choice) {
    const d = this.dialog;
    if (!d) return;
    d.answered = c.reply;
    const q = QUESTS.find((x) => x.teacher === d.npc);
    if (c.correct && q && this.readyToAnswer(q.id)) this.complete(q.id);
    else if (!c.correct) d.question = undefined;   // ask again next time
    this.changed();
  }

  private complete(id: string) {
    const q = questById(id), s = this.store;
    if (id === "split") s.take("wedge", F.wedgesPerLog);
    s.setQuest(id, { stage: q.steps.length, done: true });
    s.addXp(q.skill, q.xp);
    s.give("coins", q.coins);
    s.give(`lore:${q.lore}`, 1);
    if (!s.s.badges.includes(q.badge)) s.s.badges.push(q.badge);
    s.say(`Congratulations! Quest complete: ${q.name}. You earn the ${q.badge} badge.`, "quest");
    this.markers();
  }

  split(id: string) {
    this.world.walkNear(id, 4, () => {
      this.fighting = null;
      this.splitting = 3;   // three ticks of swinging, then a wedge
      this.store.say("You swing at the log...");
    });
  }

  private takeLoot(key: string, item: string) {
    this.world.walkNear(key, 1.8, () => {
      const l = this.loot.get(key);
      if (!l) return;
      const at = l.items.findIndex((x) => x.id === item);
      if (at < 0) return;
      const it = l.items[at];
      const got = this.store.give(it.id, it.n);
      if (!got) { this.store.say("You don't have enough inventory space."); return; }
      it.n -= got;
      if (it.n <= 0) l.items.splice(at, 1);
      if (!l.items.length) { this.loot.delete(key); this.world.removeThing(key); }
      this.questInventory();
    });
  }

  takeAll() {
    const key = [...this.loot.keys()].sort((a, b) => this.dist(a) - this.dist(b))[0];
    if (!key) { this.store.say("There is nothing here to take."); return; }
    const l = this.loot.get(key)!;
    for (const it of [...l.items]) this.takeLoot(key, it.id);
  }

  private dist(id: string) {
    const a = this.world.thingAt(id), p = this.world.playerAt();
    return a ? Math.hypot(a.x - p.x, a.z - p.z) : Infinity;
  }

  nearest(kind: "monster" | "npc") {
    const ids = kind === "monster" ? [...this.mobs.values()].filter((m) => this.world.hasThing(m.key)).map((m) => m.key)
      : NPCS.filter((n) => n.area === this.area).map((n) => `npc:${n.id}`);
    return ids.sort((a, b) => this.dist(a) - this.dist(b))[0] ?? null;
  }

  creatorSeen(detail: { frequency: number }) {
    const q = this.store.quest("twenty");
    if (detail?.frequency === 3 && q.stage === 2) {
      this.store.setQuest("twenty", { stage: 3 });
      this.store.say(`A 3V dome: ${F.struts3V} struts and ${F.panels3V} panels. Go back to Tutor Tess.`, "quest");
    }
  }

  // -------------------------------------------------------------- combat
  attack(key: string) {
    const m = this.mobs.get(key);
    if (!m || !this.world.hasThing(key)) return;
    this.dialog = null;
    this.fighting = key;
    this.world.walkNear(key, MELEE - 0.4, () => undefined);
    this.changed();
  }

  private roll(att: number, def: number) {
    const a = att, d = def;
    // RuneScape's accuracy: the chance an attack roll beats a defence roll
    const chance = a > d ? 1 - (d + 2) / (2 * (a + 1)) : a / (2 * (d + 1));
    return Math.random() < chance;
  }

  private step() {
    this.tick++;
    const s = this.store, p = this.world.playerAt();
    // splitting the log pile
    if (this.splitting > 0 && --this.splitting === 0) {
      if (s.give("wedge", 1)) {
        s.addXp("splitting", 15);
        this.world.splat("player", "+15 Splitting", "xp");
        if (Math.random() < 0.3) s.give("bark", 1);
        s.say("You split off a wedge.");
        this.questInventory();
        if (s.count("wedge") < F.wedgesPerLog && s.freeSlots() > 0) this.splitting = 3;
      } else s.say("You don't have enough inventory space.");
    }
    // regeneration: a hitpoint every ten ticks
    if (this.tick % 10 === 0 && s.s.hp < s.maxHp()) { s.s.hp++; s.emit(); }
    if (this.cool > 0) this.cool--;

    for (const m of this.mobs.values()) {
      if (!this.world.hasThing(m.key)) {
        if (m.deadUntil && this.tick >= m.deadUntil) { m.deadUntil = 0; this.spawn(m.key); }
        continue;
      }
      const at = this.world.thingAt(m.key)!;
      const d = Math.hypot(at.x - p.x, at.z - p.z);
      if (m.angry) {
        if (Math.hypot(at.x - m.home[0], at.z - m.home[1]) > LEASH || d > LEASH) {
          m.angry = false; m.hp = m.def.hp; this.world.setBar(m.key, null);
          this.world.moveThing(m.key, m.home[0], m.home[1]);
          if (this.fighting === m.key) this.fighting = null;
          continue;
        }
        if (d > MELEE) this.world.moveThing(m.key, p.x + (at.x - p.x) / d * 2.4, p.z + (at.z - p.z) / d * 2.4);
        else if (--m.cool <= 0) {
          m.cool = m.def.speed;
          const hit = this.roll((m.def.level + 8) * 64, (s.level("upkeep") + 8) * 64);
          const dmg = hit ? rnd(0, m.def.maxHit) : 0;
          s.s.hp = Math.max(0, s.s.hp - dmg);
          this.world.splat("player", String(dmg), dmg ? "hit" : "miss");
          this.world.setBar("player", s.s.hp / s.maxHp());
          s.emit();
          if (s.s.hp <= 0) { this.die(); return; }
        }
      } else if (--m.nextRoam <= 0) {
        m.nextRoam = rnd(6, 16);
        const a = Math.random() * Math.PI * 2, r = Math.random() * m.roam;
        this.world.moveThing(m.key, m.home[0] + Math.cos(a) * r, m.home[1] + Math.sin(a) * r);
      }
    }

    // the player's swing
    const f = this.fighting && this.mobs.get(this.fighting);
    if (f && this.world.hasThing(f.key)) {
      const at = this.world.thingAt(f.key)!;
      const d = Math.hypot(at.x - p.x, at.z - p.z);
      if (d > MELEE) this.world.walkNear(f.key, MELEE - 0.4, () => undefined);
      else if (this.cool <= 0) {
        this.cool = 4;
        this.world.face(f.key);
        f.angry = true;
        const power = s.power();
        const hit = this.roll((s.level("upkeep") + 8) * (64 + power * 4), (f.def.level + 8) * 64);
        const maxHit = 1 + Math.floor(s.level("upkeep") / 6) + Math.floor(power / 2);
        const dmg = hit ? Math.min(f.hp, rnd(1, maxHit)) : 0;
        f.hp -= dmg;
        this.world.splat(f.key, String(dmg), dmg ? "hit" : "miss");
        this.world.setBar(f.key, f.hp / f.def.hp);
        if (dmg) { s.addXp("upkeep", dmg * 4); s.addXp("hitpoints", dmg * 1.33); }
        if (f.hp <= 0) this.kill(f);
      }
    } else if (this.fighting) this.fighting = null;

    // loot rots
    for (const [key, l] of this.loot) if (this.tick >= l.until) { this.loot.delete(key); this.world.removeThing(key); }
    if (this.tick % 5 === 0) this.world.setBar("player", s.s.hp < s.maxHp() ? s.s.hp / s.maxHp() : null);
    this.changed();
  }

  private kill(m: Mob) {
    const at = this.world.thingAt(m.key)!;
    this.world.removeThing(m.key);
    m.deadUntil = this.tick + 25;
    m.angry = false;
    this.fighting = null;
    const s = this.store;
    s.s.kills[m.def.id] = (s.s.kills[m.def.id] || 0) + 1;
    // the drop table: every entry rolled on its own
    const items = m.def.drops.filter((d) => Math.random() < d.chance).map((d) => ({ id: d.item, n: rnd(d.qty[0], d.qty[1]) }));
    if (items.length) {
      const key = `loot:${++this.lootSeq}`;
      this.loot.set(key, { key, items, until: this.tick + LOOT_TICKS });
      this.world.addThing({ id: key, kind: "loot", name: "Loot" }, lootMesh(), at.x, at.z, { height: 1.2 });
    }
    s.say(`You defeat the ${m.def.name}.`, "combat");
    const page = items.find((x) => x.id.startsWith("lore:"));
    if (page) s.say(`It drops a lore page: ${loreById(page.id.slice(5))?.title}. Take it and read it.`, "loot");
    const water = s.quest("water");
    if (water.stage === 1 && (m.def.id === "wraith" || m.def.id === "leak")) {
      const k = (water.kills || 0) + 1;
      s.setQuest("water", k >= 3 ? { stage: 2, kills: k } : { stage: 1, kills: k });
      s.say(k >= 3 ? "That is three. Go back to Warden Wren." : `${k} of 3.`, "quest");
    }
    s.emit();
  }

  private die() {
    const s = this.store;
    s.say("Oh dear, you are dead! You wake on the plaza, with everything you carried.", "combat");
    s.s.hp = s.maxHp();
    this.fighting = null;
    for (const m of this.mobs.values()) { m.angry = false; m.hp = m.def.hp; this.world.setBar(m.key, null); }
    this.world.setBar("player", null);
    this.world.teleport(0, this.area === "hub" ? 19 : 21);
    s.emit();
  }

  /** Quests that wait on what you carry. */
  private questInventory() {
    const s = this.store, q = s.quest("split");
    if (q.stage === 1 && s.count("wedge") >= F.wedgesPerLog) {
      s.setQuest("split", { stage: 2 });
      s.say(`That is ${F.wedgesPerLog} wedges. Take them to Splitter Sam.`, "quest");
      this.markers();
    }
  }

  // -------------------------------------------------------------- the bag
  use(slot: number) {
    const s = this.store, x = s.s.inv[slot];
    if (!x) return;
    const item = itemById(x.id)!;
    if (item.heals) {
      if (s.s.hp >= s.maxHp()) { s.say("You are not hungry."); return; }
      s.s.inv[slot] = x.n > 1 ? { id: x.id, n: x.n - 1 } : null;
      const healed = Math.min(item.heals, s.maxHp() - s.s.hp);
      s.s.hp += healed;
      this.world.splat("player", `+${healed}`, "heal");
      s.say(`You eat the ${item.name.toLowerCase()}. It heals some health.`);
      return;
    }
    if (item.lore) { this.read(item.lore); return; }
    s.say(item.examine);
  }

  read(id: string) {
    const s = this.store, l = loreById(id);
    if (!l) return;
    window.dispatchEvent(new CustomEvent("portal-read", { detail: l }));
    if (!s.s.read.includes(id)) {
      s.s.read.push(id);
      s.addXp(l.skill, l.xp);
      this.world.splat("player", `+${l.xp} XP`, "xp");
      s.say(`You learn: ${l.title}.`, "xp");
    }
  }

  eatBest() {
    const s = this.store;
    const slot = s.s.inv.findIndex((x) => x && itemById(x.id)?.heals);
    if (slot < 0) { s.say("You have no food."); return; }
    this.use(slot);
  }

  readNext() {
    const s = this.store;
    const slot = s.s.inv.findIndex((x) => x && itemById(x.id)?.lore && !s.s.read.includes(itemById(x.id)!.lore!));
    if (slot < 0) { s.say("You have no unread lore pages."); return; }
    this.use(slot);
  }

  drop(slot: number) {
    const s = this.store, x = s.s.inv[slot];
    if (!x) return;
    const p = this.world.playerAt();
    s.removeSlot(slot);
    const key = `loot:${++this.lootSeq}`;
    this.loot.set(key, { key, items: [{ ...x }], until: this.tick + LOOT_TICKS });
    this.world.addThing({ id: key, kind: "loot", name: "Loot" }, lootMesh(), p.x + 0.6, p.z + 0.6, { height: 1.2 });
  }
}

export { MONSTERS };
