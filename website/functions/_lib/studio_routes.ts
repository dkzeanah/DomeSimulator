// The owner's studio: what the home page leads with, the rolling invite codes that give an
// account its access level, the promo codes that unlock friend prices, and the dome classes
// members join by entering their longest strut.

import { normaliseEmail, requireAdmin, requireOwner, requireUser } from "./auth";
import { randomToken } from "./crypto";
import { HttpError, body, json, nowIso, num, text } from "./http";
import { audit, getSetting, setSetting } from "./ops";
import api from "./routes";
import { ALPHABET, LEVELS, type Level, type Promo, classFor, classes, codeFor, livePromo, periodHours, redeemInvite, windowNow } from "./studio";

// ================================================================ the home page's focus
// The book leads for now. Each focus is one module of the site; the studio picks which one the
// home page is built around.

export const FOCI = ["book", "kids", "domes", "network"] as const;

api.get("/site", async (ctx) => {
  const focus = (await getSetting(ctx, "home.focus")) || "book";
  return json({ focus: (FOCI as readonly string[]).includes(focus) ? focus : "book" });
});

api.patch("/admin/site", async (ctx) => {
  requireAdmin(ctx);
  const focus = String((await body(ctx)).focus || "");
  if (!(FOCI as readonly string[]).includes(focus)) throw new HttpError(400, `focus is one of ${FOCI.join(", ")}.`);
  await setSetting(ctx, "home.focus", focus);
  await audit(ctx, "site.focus", "settings:home.focus", { focus });
  return json({ focus });
});

// ================================================================ rolling invite codes (studio.ts)

api.get("/admin/invites", async (ctx) => {
  requireOwner(ctx);
  const { w, ms } = await windowNow(ctx);
  const codes = [];
  for (const l of LEVELS) {
    codes.push({ ...l, code: await codeFor(ctx, l.key, w), shownUntil: new Date((w + 1) * ms).toISOString(), worksUntil: new Date((w + 2) * ms).toISOString() });
  }
  const joined = (await ctx.env.DB.prepare("SELECT SUBSTR(joined_with, 8) level, COUNT(*) n FROM users WHERE joined_with LIKE 'invite:%' GROUP BY joined_with").all()).results;
  return json({ periodHours: await periodHours(ctx), codes, joined });
});

api.post("/admin/invites/:level/roll", async (ctx) => {
  requireOwner(ctx);
  const level = ctx.params.level as Level;
  if (!LEVELS.some((l) => l.key === level)) throw new HttpError(404, "No such level.");
  await setSetting(ctx, `invite.${level}.salt`, randomToken(12));
  await audit(ctx, "invite.roll", `invite:${level}`);
  return json({ ok: true });
});

api.patch("/admin/invites", async (ctx) => {
  requireOwner(ctx);
  const hours = num(await body(ctx), "periodHours", { min: 1, max: 24 * 90, required: true })!;
  await setSetting(ctx, "invite.period_hours", String(Math.round(hours)));
  await audit(ctx, "invite.period", "settings:invite.period_hours", { hours });
  return json({ ok: true });
});

api.post("/me/redeem", async (ctx) => {
  const u = requireUser(ctx);
  const level = await redeemInvite(ctx, u, String((await body(ctx)).code || ""));
  return json({ level });
});

// ================================================================ promo codes (studio.ts)

api.post("/promo/check", async (ctx) => {
  const b = await body(ctx);
  const product = text(b, "product", { max: 80, required: true })!;
  const p = await livePromo(ctx, product, text(b, "code", { max: 40 }) || "");
  if (!p) throw new HttpError(404, "That code is not valid for this book.");
  const pr = await ctx.env.DB.prepare("SELECT * FROM prices WHERE product = ? AND key = ? AND active = 1").bind(product, p.price_key).first<{ key: string; label: string; amount_cents: number; currency: string }>();
  if (!pr) throw new HttpError(404, "That code is not valid for this book.");
  return json({ code: p.code, price: { key: pr.key, label: pr.label, amountCents: pr.amount_cents, currency: pr.currency, honor: false, honorPrompt: null } });
});

api.get("/admin/promos", async (ctx) => {
  requireAdmin(ctx);
  const promos = (await ctx.env.DB.prepare("SELECT * FROM promo_codes ORDER BY created_at DESC").all<Promo>()).results;
  const gated = (await ctx.env.DB.prepare("SELECT product, key, label, amount_cents FROM prices WHERE gated = 1 AND active = 1 ORDER BY product").all()).results;
  return json({ promos, gated });
});

api.post("/admin/promos", async (ctx) => {
  requireAdmin(ctx);
  const b = await body(ctx);
  const product = text(b, "product", { max: 80, required: true })!;
  const key = text(b, "priceKey", { max: 40 }) || "friend";
  if (!(await ctx.env.DB.prepare("SELECT 1 FROM prices WHERE product = ? AND key = ? AND gated = 1").bind(product, key).first())) {
    throw new HttpError(400, "A promo code unlocks a friend (gated) price, and that product has none with that key.");
  }
  const typed = (text(b, "code", { max: 40 }) || "").toUpperCase().replace(/[^A-Z0-9-]/g, "");
  if (typed && typed.length < 4) throw new HttpError(400, "A code needs at least 4 letters or numbers.");
  let code = typed;
  if (!code) for (let i = 0; i < 8; i++) code += ALPHABET[crypto.getRandomValues(new Uint8Array(1))[0] % ALPHABET.length];
  if (await ctx.env.DB.prepare("SELECT 1 FROM promo_codes WHERE code = ?").bind(code).first()) throw new HttpError(409, "That code already exists.");
  const max = num(b, "maxUses", { min: 1, max: 100000 });
  await ctx.env.DB.prepare("INSERT INTO promo_codes(code, product, price_key, max_uses, note, created_at) VALUES(?, ?, ?, ?, ?, ?)")
    .bind(code, product, key, max == null ? null : Math.round(max), text(b, "note", { max: 200 }), nowIso()).run();
  await audit(ctx, "promo.create", `promo:${code}`, { product, key, max });
  return json({ code }, 201);
});

api.patch("/admin/promos/:code", async (ctx) => {
  requireAdmin(ctx);
  const active = (await body(ctx)).active === false ? 0 : 1;
  const r = await ctx.env.DB.prepare("UPDATE promo_codes SET active = ? WHERE code = ?").bind(active, ctx.params.code).run();
  if (!r.meta.changes) throw new HttpError(404, "No such code.");
  await audit(ctx, active ? "promo.on" : "promo.off", `promo:${ctx.params.code}`);
  return json({ ok: true });
});

// ================================================================ dome classes (studio.ts)

api.patch("/me/dome", async (ctx) => {
  const u = requireUser(ctx);
  const b = await body(ctx);
  if (b.clear === true) {
    await ctx.env.DB.prepare("UPDATE users SET dome_long_in = NULL, dome_status = NULL, dome_note = NULL, updated_at = ? WHERE id = ?").bind(nowIso(), u.id).run();
    return json({ dome: null });
  }
  const c = classFor({ longIn: num(b, "longIn", { min: 1, max: 1000 }), shortIn: num(b, "shortIn", { min: 1, max: 1000 }) });
  const range = `${classes.classes[0].longIn} to ${classes.classes[classes.classes.length - 1].longIn} inches`;
  if (!c) throw new HttpError(400, `Give your longest strut (${range}) or your shortest, in inches.`);
  const status = String(b.status || "planning");
  if (!["planning", "building", "built"].includes(status)) throw new HttpError(400, "status is planning, building or built.");
  await ctx.env.DB.prepare("UPDATE users SET dome_long_in = ?, dome_status = ?, dome_note = ?, updated_at = ? WHERE id = ?")
    .bind(c.longIn, status, text(b, "note", { max: 300 }), nowIso(), u.id).run();
  return json({ dome: { longIn: c.longIn, status, note: text(b, "note", { max: 300 }) || "" } });
});

/** How many members are in each class. Counts only -- names are on the class's own page. */
api.get("/domes", async (ctx) => {
  const rows = (await ctx.env.DB.prepare("SELECT dome_long_in longIn, COUNT(*) n, SUM(dome_status = 'built') built FROM users WHERE dome_long_in IS NOT NULL AND status = 'active' GROUP BY dome_long_in ORDER BY dome_long_in").all()).results;
  return json({ classes: rows });
});

/** One class: how many are in it, and the members who chose a public profile. A signed-in
 *  member of the same class also sees how to reach them (their network contact, if listed). */
api.get("/domes/:longIn", async (ctx) => {
  const c = classFor({ longIn: Number(ctx.params.longIn) });
  if (!c) throw new HttpError(404, "No such dome class.");
  const db = ctx.env.DB;
  const count = (await db.prepare("SELECT COUNT(*) n FROM users WHERE dome_long_in = ? AND status = 'active'").bind(c.longIn).first<{ n: number }>())!.n;
  const sameClass = ctx.user?.dome_long_in === c.longIn;
  const members = (await db.prepare(
    `SELECT u.id, u.display_name, u.username, u.city, u.region, u.country, u.dome_status, u.dome_note,
       (SELECT contact FROM listings l WHERE l.user_id = u.id AND l.visible = 1 AND COALESCE(l.contact, '') != '' ORDER BY l.updated_at DESC LIMIT 1) contact
     FROM users u WHERE u.dome_long_in = ? AND u.status = 'active' AND u.public_profile = 1 ORDER BY u.dome_status = 'built' DESC, u.created_at LIMIT 200`,
  ).bind(c.longIn).all<{ id: number; display_name: string; username: string | null; city: string | null; region: string | null; country: string | null; dome_status: string | null; dome_note: string | null; contact: string | null }>()).results;
  return json({
    longIn: c.longIn, count, sameClass,
    members: members.map((m) => ({
      displayName: m.display_name, username: m.username || "", city: m.city || "", region: m.region || "", country: m.country || "",
      status: m.dome_status || "planning", note: m.dome_note || "", contact: sameClass ? m.contact || "" : null, you: m.id === ctx.user?.id,
    })),
  });
});

// ================================================================ the owner's account lookups

/** Find an account by email or username, for the studio's "give a level" box. */
api.get("/admin/find-user", async (ctx) => {
  requireAdmin(ctx);
  const q = String(ctx.url.searchParams.get("q") || "").trim();
  const row = await ctx.env.DB.prepare("SELECT id, email, username, display_name, role FROM users WHERE email = ? OR username = ?").bind(normaliseEmail(q), q.toLowerCase().replace(/^@/, "")).first();
  if (!row) throw new HttpError(404, "No account with that email or username.");
  return json({ user: row });
});
