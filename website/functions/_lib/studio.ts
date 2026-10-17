// The studio's rules, shared by the shop and sign-up (routes.ts) and the studio's own routes
// (studio_routes.ts): rolling invite codes, promo codes, dome classes. No routes here, so both
// can import it without a cycle.

import classes from "../../src/generated/dome-classes.json";
import { roleFor } from "./auth";
import { hmacHex, randomToken } from "./crypto";
import { Ctx, HttpError, User, nowIso } from "./http";
import { audit, getSetting, setSetting } from "./ops";

export { classes };

// ---------------------------------------------------------------- rolling invite codes
// One live code per access level, worked out from a secret, the level, a salt and the current
// time window -- so nothing needs storing and every code dies on its own. A code is good for
// the window it was shown in and the one after, so a code given just before it rolls still
// works. "Roll now" changes the salt, which kills the level's code at once.

export const LEVELS = [
  { key: "friend", label: "Friend", gives: "Friend prices on every book, without a promo code." },
  { key: "manager", label: "Manager", gives: "Every admin page and the day's work. Cannot make managers, agent keys, or delete accounts." },
] as const;
export type Level = (typeof LEVELS)[number]["key"];

export const ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"; // no 0/O, 1/I

export async function periodHours(ctx: Ctx) {
  const v = Number(await getSetting(ctx, "invite.period_hours"));
  return Number.isFinite(v) && v >= 1 ? v : 72;
}

export async function salt(ctx: Ctx, level: Level) {
  const key = `invite.${level}.salt`;
  let s = await getSetting(ctx, key);
  if (!s) { s = randomToken(12); await setSetting(ctx, key, s); }
  return s;
}

export async function codeFor(ctx: Ctx, level: Level, window: number) {
  if (!ctx.env.SESSION_SECRET) throw new HttpError(500, "The site is not configured yet (SESSION_SECRET is missing).");
  const hex = await hmacHex(ctx.env.SESSION_SECRET, `invite|${level}|${await salt(ctx, level)}|${window}`);
  let out = "";
  for (let i = 0; i < 8; i++) out += ALPHABET[parseInt(hex.slice(i * 2, i * 2 + 2), 16) % ALPHABET.length];
  return `${out.slice(0, 4)}-${out.slice(4)}`;
}

export async function windowNow(ctx: Ctx) {
  const ms = (await periodHours(ctx)) * 3_600_000;
  const w = Math.floor(Date.now() / ms);
  return { w, ms };
}

const cleanCode = (c: string) => String(c || "").toUpperCase().replace(/[^A-Z0-9]/g, "");

/** The level a typed invite code gives, or null. */
export async function levelOfInvite(ctx: Ctx, typed: string): Promise<Level | null> {
  const c = cleanCode(typed);
  if (c.length !== 8) return null;
  const { w } = await windowNow(ctx);
  for (const l of LEVELS) {
    for (const win of [w, w - 1]) if (cleanCode(await codeFor(ctx, l.key, win)) === c) return l.key;
  }
  return null;
}

/** Give an account the level an invite code names. Never lowers anyone, never touches the owner. */
export async function redeemInvite(ctx: Ctx, u: User, typed: string) {
  const level = await levelOfInvite(ctx, typed);
  if (!level) throw new HttpError(400, "That invite code is not right, or it has rolled. Ask for the current one.");
  const now = roleFor(ctx.env, u.email, u.role);
  const rank = { member: 0, friend: 1, manager: 2, admin: 3 } as const;
  if (rank[level] > rank[now]) {
    await ctx.env.DB.prepare("UPDATE users SET role = ?, joined_with = COALESCE(joined_with, ?), updated_at = ? WHERE id = ?").bind(level, `invite:${level}`, nowIso(), u.id).run();
  }
  await audit(ctx, "invite.redeem", `user:${u.id}`, { level, email: u.email }, { kind: "user", id: u.id, name: u.email });
  return level;
}

// ---------------------------------------------------------------- promo codes
// Each code unlocks one gated price of one product: the $20 book for $5, the $5 book for $1.

export interface Promo { code: string; product: string; price_key: string; max_uses: number | null; uses: number; active: number; note: string | null; created_at: string }

/** The promo a buyer typed, if it is live for this product. */
export async function livePromo(ctx: Ctx, product: string, typed: string) {
  const c = String(typed || "").trim().toUpperCase();
  if (!c) return null;
  const p = await ctx.env.DB.prepare("SELECT * FROM promo_codes WHERE code = ? AND product = ? AND active = 1").bind(c, product).first<Promo>();
  if (!p || (p.max_uses != null && p.uses >= p.max_uses)) return null;
  return p;
}

// ---------------------------------------------------------------- dome classes
// A member enters one number -- the longest strut, or the shortest -- and is put in the class of
// every member whose dome has the same longest strut: the same panels fit both.

type DomeClass = (typeof classes.classes)[number];
const BY_LONG = new Map<number, DomeClass>(classes.classes.map((c) => [c.longIn, c]));

/** The class a strut length names: the longest strut to the nearest inch, or the class whose
 *  shortest strut is within half an inch of the one given. */
export function classFor(o: { longIn?: number | null; shortIn?: number | null }): DomeClass | null {
  if (o.longIn != null) return BY_LONG.get(Math.round(o.longIn)) ?? null;
  if (o.shortIn != null) {
    let best: DomeClass | null = null;
    for (const c of classes.classes) if (!best || Math.abs(c.shortIn - o.shortIn) < Math.abs(best.shortIn - o.shortIn)) best = c;
    return best && Math.abs(best.shortIn - o.shortIn) <= 0.5 ? best : null;
  }
  return null;
}
