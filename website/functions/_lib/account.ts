// The life account: the book's program, snowball.py (Snowball, Appendix A), ported line
// for line to run per member against D1. Same tables, same requirement check, same score
// (TV = Cash + XP*weight - Cost, with Unlocks counted), same critical path (out-degree
// first, then nearest to done), same review (Future Hour Value: $ per logged hour, last 30
// days against the 30 before), same ten stages. The interface is a mirror, not a judge:
// nothing here grades anyone -- it renders what the member recorded.

import { HttpError, nowIso } from "./http";

export const STAGES: [string, string, string][] = [
  ["1. Survival", "Become reliably employed", "reliable employment"],
  ["2. Reserve", "Establish emergency/runway capital", "emergency fund"],
  ["3. Training", "Acquire valuable skills", "core skill"],
  ["4. Questing", "Credentials, portfolio, licenses", "credential or portfolio"],
  ["5. Side income", "Earn independently", "first side income"],
  ["6. Threshold", "Side income becomes meaningful", "side income threshold"],
  ["7. Substitution", "Reduce employment hours", "reduced employment hours"],
  ["8. Independence", "Self-employment covers expenses", "independence"],
  ["9. Infrastructure", "Automation, tools, employees", "infrastructure"],
  ["10. Compounding", "Capital and systems produce leverage", "compounding systems"],
];

const DEFAULT_XP_WEIGHT = 1.0;
const KINDS = ["skill", "quest", "capital", "asset"] as const;
type Kind = (typeof KINDS)[number];
interface Req { kind: Kind; target: string; amount: number }

/** "kind:target:amount" -> requirement, exactly as snowball.py parses it. */
export function parseRequirement(spec: string): Req {
  const parts = spec.split(":");
  let kind: string, target: string, amount = 1;
  if (parts.length === 2) [kind, target] = parts;
  else if (parts.length === 3) {
    [kind, target] = parts;
    amount = Number(parts[2]);
    if (!Number.isFinite(amount)) throw new HttpError(400, `bad requirement (amount must be a number): ${spec}`);
  } else throw new HttpError(400, `bad requirement '${spec}' - use kind:target:amount, e.g. skill:welding:3`);
  kind = kind.trim().toLowerCase();
  if (!(KINDS as readonly string[]).includes(kind)) throw new HttpError(400, `bad requirement kind '${kind}' - use skill, quest, capital, or asset`);
  return { kind: kind as Kind, target: target.trim(), amount };
}

export class LifeAccount {
  constructor(private db: D1Database, private uid: number) {}

  private all<T>(sql: string, ...args: unknown[]) {
    return this.db.prepare(sql).bind(this.uid, ...args).all<T>().then((r) => r.results ?? []);
  }
  private first<T>(sql: string, ...args: unknown[]) {
    return this.db.prepare(sql).bind(this.uid, ...args).first<T>();
  }
  private run(sql: string, ...args: unknown[]) {
    return this.db.prepare(sql).bind(this.uid, ...args).run();
  }

  async meta(key: string, fallback: string | null = null) {
    const r = await this.first<{ value: string }>("SELECT value FROM account_meta WHERE user_id = ? AND key = ?", key);
    return r ? r.value : fallback;
  }
  setMeta(key: string, value: string | number) {
    return this.run("INSERT INTO account_meta(user_id, key, value) VALUES(?, ?, ?) ON CONFLICT(user_id, key) DO UPDATE SET value = excluded.value", key, String(value));
  }

  // ------------------------------------------------------------ the requirement check

  async requirementMet(r: Req): Promise<[boolean, string]> {
    if (r.kind === "skill") {
      const s = await this.first<{ level: number }>("SELECT level FROM skills WHERE user_id = ? AND name = ?", r.target);
      return [Boolean(s && s.level >= r.amount), `${r.target}: ${s ? s.level : 0}/${r.amount}`];
    }
    if (r.kind === "quest") {
      const q = await this.first<{ status: string }>("SELECT status FROM quests WHERE user_id = ? AND name = ?", r.target);
      return [q?.status === "complete", `quest: ${r.target} (${q ? q.status : "undefined"})`];
    }
    if (r.kind === "capital") {
      const have = Number((await this.meta("capital", "0")) || 0);
      return [have >= r.amount, `capital: ${have}/${r.amount}`];
    }
    const a = await this.first("SELECT 1 FROM assets WHERE user_id = ? AND name = ?", r.target);
    return [Boolean(a), `asset: ${r.target} (${a ? "owned" : "missing"})`];
  }

  async questProgress(quest: string) {
    const reqs = await this.all<Req>("SELECT kind, target, amount FROM quest_requirements WHERE user_id = ? AND quest = ?", quest);
    const unmet: string[] = [];
    let met = 0;
    for (const r of reqs) {
      const [ok, label] = await this.requirementMet(r);
      if (ok) met++;
      else unmet.push(label);
    }
    return { met, total: reqs.length, unmet };
  }

  // ------------------------------------------------------------ skills

  async addSkill(name: string, level: number) {
    await this.run("INSERT INTO skills(user_id, name, level, xp) VALUES(?, ?, ?, 0) ON CONFLICT(user_id, name) DO NOTHING", name, level);
  }
  async gainXp(name: string, amount: number) {
    // numbered parameters: ?1 is always the member (bound first by run())
    await this.run("UPDATE skills SET xp = xp + ?2 WHERE user_id = ?1 AND name = ?3", amount, name);
  }
  async setLevel(name: string, level: number) {
    await this.run("UPDATE skills SET level = ?2, xp = 0 WHERE user_id = ?1 AND name = ?3", level, name);
  }

  // ------------------------------------------------------------ quests

  async addQuest(name: string, description: string, specs: string[]) {
    const exists = await this.first("SELECT 1 FROM quests WHERE user_id = ? AND name = ?", name);
    if (exists) throw new HttpError(409, `quest '${name}' already exists.`);
    const reqs = specs.map(parseRequirement);
    await this.run("INSERT INTO quests(user_id, name, description) VALUES(?, ?, ?)", name, description);
    for (const r of reqs) {
      await this.run("INSERT INTO quest_requirements(user_id, quest, kind, target, amount) VALUES(?, ?, ?, ?, ?)", name, r.kind, r.target, r.amount);
    }
    return this.questProgress(name);
  }

  async start(name: string) {
    await this.run("UPDATE quests SET status = 'in_progress' WHERE user_id = ? AND name = ? AND status != 'complete'", name);
    return this.questProgress(name);
  }

  /** Completes a quest only when nothing is missing, and says what it just unlocked. */
  async complete(name: string): Promise<{ completed: boolean; unmet: string[]; unlocked: string[] }> {
    const q = await this.first("SELECT 1 FROM quests WHERE user_id = ? AND name = ?", name);
    if (!q) throw new HttpError(404, `Unknown quest '${name}'.`);
    const { unmet } = await this.questProgress(name);
    if (unmet.length) return { completed: false, unmet, unlocked: [] };
    await this.run("UPDATE quests SET status = 'complete' WHERE user_id = ? AND name = ?", name);
    const unlocked: string[] = [];
    const deps = await this.all<{ quest: string }>("SELECT DISTINCT quest FROM quest_requirements WHERE user_id = ? AND kind = 'quest' AND target = ?", name);
    for (const d of deps) {
      const p = await this.questProgress(d.quest);
      const st = await this.first<{ status: string }>("SELECT status FROM quests WHERE user_id = ? AND name = ?", d.quest);
      if (!p.unmet.length && st && st.status !== "complete") unlocked.push(d.quest);
    }
    return { completed: true, unmet: [], unlocked };
  }

  // ------------------------------------------------------------ methods, logs, assets

  async rate(name: string, cash: number, cost: number, xp: [string, number][], notes: string) {
    await this.run(
      "INSERT INTO methods(user_id, name, cash_per_hour, cost_per_hour, notes) VALUES(?, ?, ?, ?, ?) "
      + "ON CONFLICT(user_id, name) DO UPDATE SET cash_per_hour = excluded.cash_per_hour, cost_per_hour = excluded.cost_per_hour, notes = excluded.notes",
      name, cash, cost, notes);
    await this.run("DELETE FROM method_xp WHERE user_id = ? AND method = ?", name);
    for (const [skill, rate] of xp) await this.run("INSERT INTO method_xp(user_id, method, skill, xp_per_hour) VALUES(?, ?, ?, ?)", name, skill, rate);
  }

  /** Log hours; the forgone cash is the opportunity cost. One change from snowball.py: the
   *  program only printed the XP a log earned; here the trained skills keep it, so the bar
   *  a member watches moves when the hours are logged. */
  async log(method: string, hours: number, cashOverride: number | null, note: string) {
    const m = await this.first<{ cash_per_hour: number }>("SELECT cash_per_hour FROM methods WHERE user_id = ? AND name = ?", method);
    if (!m) throw new HttpError(404, `Unknown method '${method}'. Rate it first.`);
    const cash = cashOverride ?? m.cash_per_hour * hours;
    await this.run("INSERT INTO logs(user_id, ts, method, hours, cash, note) VALUES(?, ?, ?, ?, ?, ?)", nowIso(), method, hours, cash, note);
    const xp = await this.all<{ skill: string; xp_per_hour: number }>("SELECT skill, xp_per_hour FROM method_xp WHERE user_id = ? AND method = ?", method);
    const gained = xp.map((r) => ({ skill: r.skill, xp: r.xp_per_hour * hours }));
    for (const g of gained) await this.run("UPDATE skills SET xp = xp + ?2 WHERE user_id = ?1 AND name = ?3", g.xp, g.skill);
    const best = await this.first<{ name: string; cash_per_hour: number }>(
      "SELECT name, cash_per_hour FROM methods WHERE user_id = ? AND name != ? ORDER BY cash_per_hour DESC LIMIT 1", method);
    return { cash, gained, forgone: best ? { method: best.name, cash: best.cash_per_hour * hours } : null };
  }

  async addAsset(name: string, value: number, description: string) {
    await this.run("INSERT INTO assets(user_id, name, description, value) VALUES(?, ?, ?, ?) ON CONFLICT(user_id, name) DO UPDATE SET description = excluded.description, value = excluded.value", name, description, value);
  }

  // ------------------------------------------------------------ the screens

  async score() {
    const weight = Number((await this.meta("xp_weight", String(DEFAULT_XP_WEIGHT))) || DEFAULT_XP_WEIGHT);
    const methods = await this.all<{ name: string; cash_per_hour: number; cost_per_hour: number }>("SELECT * FROM methods WHERE user_id = ? ORDER BY name");
    const skillReqs = await this.all<{ quest: string; target: string; amount: number }>("SELECT quest, target, amount FROM quest_requirements WHERE user_id = ? AND kind = 'skill'");
    const rows = [];
    for (const m of methods) {
      const xp = await this.all<{ skill: string; xp_per_hour: number }>("SELECT skill, xp_per_hour FROM method_xp WHERE user_id = ? AND method = ?", m.name);
      const xpTotal = xp.reduce((s, r) => s + r.xp_per_hour, 0);
      let unlocks = 0;
      for (const r of skillReqs) {
        const st = await this.first<{ status: string }>("SELECT status FROM quests WHERE user_id = ? AND name = ?", r.quest);
        if (st?.status === "complete") continue;
        const s = await this.first<{ level: number }>("SELECT level FROM skills WHERE user_id = ? AND name = ?", r.target);
        if ((s ? s.level : 0) < r.amount && xp.some((x) => x.skill === r.target)) unlocks++;
      }
      rows.push({ name: m.name, cash: m.cash_per_hour, cost: m.cost_per_hour, xp, xpTotal, unlocks, tv: m.cash_per_hour + xpTotal * weight - m.cost_per_hour });
    }
    rows.sort((a, b) => b.tv - a.tv);
    return { weight, methods: rows };
  }

  async path() {
    const qs = await this.all<{ name: string }>("SELECT name FROM quests WHERE user_id = ? AND status != 'complete' ORDER BY name");
    const out = [];
    for (const q of qs) {
      const p = await this.questProgress(q.name);
      const od = await this.first<{ n: number }>("SELECT COUNT(DISTINCT quest) AS n FROM quest_requirements WHERE user_id = ? AND kind = 'quest' AND target = ?", q.name);
      out.push({ name: q.name, met: p.met, total: p.total, unlocks: od?.n ?? 0 });
    }
    out.sort((a, b) => b.unlocks - a.unlocks || (a.met - a.total) - (b.met - b.total));
    return out;
  }

  async stages() {
    let currentFound = false;
    const out = [];
    for (const [name, goal, quest] of STAGES) {
      const [ok, label] = await this.requirementMet({ kind: "quest", target: quest, amount: 1 });
      const current = !currentFound && !ok;
      if (current) currentFound = true;
      out.push({ name, goal, quest, complete: ok, current, missing: ok ? [] : [label] });
    }
    return out;
  }

  async review() {
    const day = 86_400_000;
    const recent = nowIso(-30 * day), prior = nowIso(-60 * day);
    const a = await this.first<{ h: number | null; c: number | null }>("SELECT SUM(hours) h, SUM(cash) c FROM logs WHERE user_id = ? AND ts >= ?", recent);
    const b = await this.first<{ h: number | null; c: number | null }>("SELECT SUM(hours) h, SUM(cash) c FROM logs WHERE user_id = ? AND ts >= ? AND ts < ?", prior, recent);
    const rate = (r: { h: number | null; c: number | null } | null) => (r && r.h ? (r.c || 0) / r.h : null);
    const now = rate(a), before = rate(b);
    let trend: string | null = null;
    if (now !== null && before !== null) {
      trend = now > before ? "rising - the account is compounding" : now < before ? "falling - check what changed" : "flat - the snowball is not rolling";
    }
    const skills = await this.all("SELECT name, level, xp FROM skills WHERE user_id = ? ORDER BY level DESC, name");
    const quests = [];
    for (const q of await this.all<{ name: string; status: string; description: string }>("SELECT name, status, description FROM quests WHERE user_id = ? ORDER BY name")) {
      quests.push({ ...q, ...(await this.questProgress(q.name)) });
    }
    const assets = await this.all("SELECT name, value, description FROM assets WHERE user_id = ? ORDER BY name");
    const logs = await this.all("SELECT ts, method, hours, cash, note FROM logs WHERE user_id = ? ORDER BY ts DESC LIMIT 20");
    return {
      fhv: { last30: now, prior30: before, trend },
      capital: Number((await this.meta("capital", "0")) || 0),
      skills, quests, assets, logs,
      stages: await this.stages(),
    };
  }
}
