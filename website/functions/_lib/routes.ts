// Every /api route. Each block says which page uses it.

import facts from "../../src/generated/facts.json";
import { LifeAccount } from "./account";
import { downloadToken, endSession, normaliseEmail, publicUser, readDownloadToken, requireAdmin, requireUser, roleFor, startSession } from "./auth";
import { checkPassword, hashPassword, randomToken, sameString, sha256Hex } from "./crypto";
import { Ctx, HttpError, Router, User, body, email, honeypot, json, nowIso, num, text } from "./http";
import { checkoutMode, createCheckoutSession, mailReady, retrieveCheckoutSession, sampleLetter, sendMail, verifyStripeSignature } from "./services";

const api = new Router();
export default api;

// ---------------------------------------------------------------- the catalogue (D1)
// Products and prices are rows (migrations/0002, 0003): a price change is a row edit, and
// an order keeps the price it was sold at.

export interface Product {
  slug: string; kind: "digital" | "physical" | "service" | "amazon"; title: string; subtitle: string; blurb: string;
  file_key: string | null; status: string; ships_note: string | null; ship_countries: string | null; external_url: string | null; sort: number;
}
export interface Price { product: string; key: string; label: string; amount_cents: number; currency: string; honor: number; honor_prompt: string | null; active: number; sort: number }

async function product(ctx: Ctx, slug: string) {
  return ctx.env.DB.prepare("SELECT * FROM products WHERE slug = ?").bind(slug).first<Product>();
}
async function price(ctx: Ctx, slug: string, key: string) {
  return ctx.env.DB.prepare("SELECT * FROM prices WHERE product = ? AND key = ? AND active = 1").bind(slug, key).first<Price>();
}
/** The few things a product carries that are not prices: the codebase link, the booking note. */
const extras = (slug: string) => (facts.books as { slug: string; codebaseUrl?: string; bookingNote?: string }[]).find((b) => b.slug === slug);

export async function catalogue(ctx: Ctx) {
  const products = (await ctx.env.DB.prepare("SELECT * FROM products WHERE status != 'hidden' ORDER BY sort").all<Product>()).results;
  const prices = (await ctx.env.DB.prepare("SELECT * FROM prices WHERE active = 1 ORDER BY sort").all<Price>()).results;
  return products.map((p) => ({
    slug: p.slug, kind: p.kind, title: p.title, subtitle: p.subtitle, blurb: p.blurb, status: p.status,
    shipsNote: p.ships_note, shipCountries: (p.ship_countries || "").split(",").filter(Boolean), externalUrl: p.external_url,
    prices: prices.filter((r) => r.product === p.slug).map((r) => ({ key: r.key, label: r.label, amountCents: r.amount_cents, currency: r.currency, honor: Boolean(r.honor), honorPrompt: r.honor_prompt })),
  }));
}
const site = (ctx: Ctx) => (ctx.env.PUBLIC_URL || ctx.url.origin).replace(/\/$/, "");

async function event(ctx: Ctx, kind: string, label: string) {
  await ctx.env.DB.prepare("INSERT INTO events(kind, label, created_at) VALUES(?, ?, ?)").bind(kind, label, nowIso()).run();
}

/** Add or refresh a subscriber. Consent only ever moves by the person's own choice. */
async function upsertSubscriber(ctx: Ctx, o: { email: string; name?: string | null; consent?: boolean; source: string }) {
  const db = ctx.env.DB;
  const e = normaliseEmail(o.email);
  const existing = await db.prepare("SELECT id, name FROM subscribers WHERE email = ?").bind(e).first<{ id: number; name: string | null }>();
  if (existing) {
    if (o.name && !existing.name) await db.prepare("UPDATE subscribers SET name = ? WHERE id = ?").bind(o.name, existing.id).run();
    if (o.consent) await db.prepare("UPDATE subscribers SET marketing_consent = 1, unsubscribed_at = NULL WHERE id = ?").bind(existing.id).run();
    return { id: existing.id, created: false };
  }
  const r = await db.prepare("INSERT INTO subscribers(email, name, marketing_consent, source, created_at) VALUES(?, ?, ?, ?, ?) RETURNING id")
    .bind(e, o.name || null, o.consent ? 1 : 0, o.source, nowIso()).first<{ id: number }>();
  await event(ctx, "subscriber", "Someone joined the list");
  return { id: r!.id, created: true };
}

async function recordSignup(ctx: Ctx, subscriberId: number, kind: string, slug: string) {
  await ctx.env.DB.prepare("INSERT INTO signups(subscriber_id, kind, book_slug, created_at) VALUES(?, ?, ?, ?)").bind(subscriberId, kind, slug, nowIso()).run();
}

// ================================================================ the public numbers
// Home page "the build, live", the plaque wall, the backer page. Counted, never typed.

api.get("/stats", async (ctx) => {
  const db = ctx.env.DB;
  const one = async (sql: string) => ((await db.prepare(sql).first<{ n: number }>())?.n ?? 0);
  const [subscribers, members, sampleDownloads, booksSold, pads, padsHosting, listings, backers, pledged, plaques, salvageHours, salvageCents] = await Promise.all([
    one("SELECT COUNT(*) n FROM subscribers WHERE unsubscribed_at IS NULL"),
    one("SELECT COUNT(*) n FROM users"),
    one("SELECT COUNT(*) n FROM downloads WHERE book_slug = 'sample'"),
    one("SELECT COUNT(*) n FROM orders WHERE status = 'paid' AND book_slug IN ('the-40-hour-cabin', 'triangular-book')"),
    one("SELECT COUNT(*) n FROM listings WHERE visible = 1 AND kind = 'pad_host'"),
    one("SELECT COUNT(*) n FROM listings WHERE visible = 1 AND kind = 'pad_host' AND pad_status = 'hosting'"),
    one("SELECT COUNT(*) n FROM listings WHERE visible = 1"),
    one("SELECT COUNT(*) n FROM backers"),
    one("SELECT COALESCE(SUM(pledge_cents), 0) n FROM backers"),
    one("SELECT COUNT(*) n FROM plaques"),
    one("SELECT COALESCE(SUM(hours), 0) n FROM salvage_logs"),
    one("SELECT COALESCE(SUM(replacement_cents), 0) n FROM salvage_logs"),
  ]);
  const feed = (await db.prepare("SELECT kind, label, created_at FROM events ORDER BY id DESC LIMIT 12").all()).results;
  return json({
    subscribers, members, sampleDownloads, booksSold, pads, padsHosting, listings, backers,
    pledgedCents: pledged, goalUsd: facts.goal.total, plaquesClaimed: plaques, plaqueSlots: facts.plaques.slots,
    salvageHours, salvageCents, feed,
  });
});

api.get("/plaques", async (ctx) => {
  const rows = (await ctx.env.DB.prepare(
    "SELECT plaques.slot, plaques.inscription, plaques.status, plaques.claimed_at, backers.display_name FROM plaques LEFT JOIN backers ON backers.id = plaques.backer_id ORDER BY slot",
  ).all()).results;
  return json({ slots: facts.plaques.slots, plaques: rows });
});

api.get("/backers", async (ctx) => {
  const rows = (await ctx.env.DB.prepare("SELECT display_name, tier, pledge_cents, created_at FROM backers WHERE public = 1 ORDER BY pledge_cents DESC, id").all()).results;
  return json({ backers: rows, kickstarterUrl: facts.site.kickstarterUrl || "" });
});

// ================================================================ the list and the sample
// /sample and every subscribe panel.

api.post("/subscribe", async (ctx) => {
  const b = await body(ctx);
  honeypot(b);
  const e = email(b);
  const source = text(b, "source", { max: 40 }) || "site";
  const s = await upsertSubscriber(ctx, { email: e, name: text(b, "name", { max: 120 }), consent: b.marketingConsent === true, source });
  const kind = source === "backer" || source === "founder" ? source : "list";
  await recordSignup(ctx, s.id, kind, source);
  return json({ ok: true, new: s.created }, 201);
});

api.post("/leads", async (ctx) => {
  const b = await body(ctx);
  honeypot(b);
  const e = email(b);
  const book = await product(ctx, text(b, "book", { max: 80 }) || "sample");
  if (!book || book.kind !== "digital" || !(await price(ctx, book.slug, "free"))) throw new HttpError(404, "That book is not available right now.");
  const s = await upsertSubscriber(ctx, { email: e, name: text(b, "name", { max: 120 }), consent: b.marketingConsent === true, source: book.slug });
  await recordSignup(ctx, s.id, "sample", book.slug);
  const hours = 72;
  const downloadUrl = `/api/books/${encodeURIComponent(book.slug)}/download?token=${await downloadToken(ctx.env, book.slug, s.id, hours)}`;
  const letter = sampleLetter(site(ctx), downloadUrl, hours);
  const emailed = await sendMail(ctx.env, e, letter.subject, letter.html, letter.text);
  return json({ downloadUrl, expiresInHours: hours, emailed }, 201);
});

api.post("/unsubscribe", async (ctx) => {
  const b = await body(ctx);
  await ctx.env.DB.prepare("UPDATE subscribers SET marketing_consent = 0, unsubscribed_at = ? WHERE email = ?").bind(nowIso(), email(b)).run();
  return json({ ok: true }); // the same answer whether or not the address was on the list
});

async function streamBook(ctx: Ctx, book: Product, record: { subscriberId: number | null }) {
  if (!ctx.env.BOOKS) throw new HttpError(503, "The book store is not connected yet.");
  if (!book.file_key) throw new HttpError(404, "There is no file for this.");
  const obj = await ctx.env.BOOKS.get(book.file_key);
  if (!obj) throw new HttpError(404, "That book is not available right now.");
  if (ctx.request.method === "GET") {
    await ctx.env.DB.prepare("INSERT INTO downloads(subscriber_id, user_id, book_slug, created_at) VALUES(?, ?, ?, ?)")
      .bind(record.subscriberId, ctx.user?.id ?? null, book.slug, nowIso()).run();
  }
  return new Response(ctx.request.method === "HEAD" ? null : obj.body, {
    headers: {
      "Content-Type": "application/pdf",
      "Content-Length": String(obj.size),
      "Content-Disposition": `attachment; filename="${book.slug}.pdf"`,
      "Cache-Control": "private, no-store",
    },
  });
}

api.get("/books/:slug/download", async (ctx) => {
  const book = await product(ctx, ctx.params.slug);
  if (!book || book.kind !== "digital") throw new HttpError(404, "No such book.");
  if (!(await price(ctx, book.slug, "free")) && ctx.user?.role !== "admin") throw new HttpError(403, "This book is sold, not given away. Your purchase link downloads it.");
  let subscriberId: number | null = null;
  if (!ctx.user) {
    const t = await readDownloadToken(ctx.env, ctx.url.searchParams.get("token"));
    if (!t || t.slug !== book.slug) throw new HttpError(403, "This download link has expired. Enter your email again for a fresh one.");
    subscriberId = t.subscriberId;
  }
  return streamBook(ctx, book, { subscriberId });
});

// ================================================================ accounts
// /account

api.post("/signup", async (ctx) => {
  const b = await body(ctx);
  honeypot(b);
  const e = email(b);
  const password = text(b, "password", { min: 10, max: 200, required: true })!;
  const name = text(b, "displayName", { min: 1, max: 80, required: true })!;
  const db = ctx.env.DB;
  if (await db.prepare("SELECT id FROM users WHERE email = ?").bind(e).first()) throw new HttpError(409, "That email already has an account. Sign in instead.");
  const r = await db.prepare("INSERT INTO users(email, password_hash, display_name, role, created_at, updated_at) VALUES(?, ?, ?, ?, ?, ?) RETURNING id")
    .bind(e, await hashPassword(password), name, roleFor(ctx.env, e), nowIso(), nowIso()).first<{ id: number }>();
  await upsertSubscriber(ctx, { email: e, name, consent: b.marketingConsent === true, source: "signup" });
  await event(ctx, "member", "A new member joined");  // names stay private unless chosen public
  await startSession(ctx, r!.id);
  return json({ user: publicUser(await db.prepare("SELECT * FROM users WHERE id = ?").bind(r!.id).first<User>()) }, 201, ctx);
});

// Compared against when the email is unknown, so a wrong email takes as long as a wrong password.
const DUMMY = "pbkdf2$100000$c2FsdHNhbHRzYWx0c2FsdA$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA";

api.post("/login", async (ctx) => {
  const b = await body(ctx);
  const e = email(b);
  const password = text(b, "password", { min: 1, max: 200, required: true })!;
  const u = await ctx.env.DB.prepare("SELECT * FROM users WHERE email = ?").bind(e).first<User>();
  const ok = await checkPassword(password, u?.password_hash || DUMMY);
  if (!u || !ok) throw new HttpError(401, "Email or password is not right.");
  await startSession(ctx, u.id);
  return json({ user: publicUser(u) }, 200, ctx);
});

api.post("/logout", async (ctx) => {
  await endSession(ctx);
  return json({ ok: true }, 200, ctx);
});

api.get("/me", async (ctx) => json({ user: publicUser(ctx.user) }));

api.patch("/me", async (ctx) => {
  const u = requireUser(ctx);
  const b = await body(ctx);
  const sets: string[] = [], vals: unknown[] = [];
  for (const [key, col, max] of [["displayName", "display_name", 80], ["bio", "bio", 2000], ["city", "city", 100], ["region", "region", 100], ["country", "country", 100]] as const) {
    if (key in b) { sets.push(`${col} = ?`); vals.push(text(b, key, { max })); }
  }
  if ("publicProfile" in b) { sets.push("public_profile = ?"); vals.push(b.publicProfile === true ? 1 : 0); }
  if (b.newPassword) {
    const cur = text(b, "currentPassword", { max: 200 });
    if (!cur || !(await checkPassword(cur, u.password_hash))) throw new HttpError(400, "Your current password is needed to set a new one.");
    sets.push("password_hash = ?");
    vals.push(await hashPassword(text(b, "newPassword", { min: 10, max: 200, required: true })!));
    await ctx.env.DB.prepare("DELETE FROM sessions WHERE user_id = ?").bind(u.id).run();
    await startSession(ctx, u.id);
  }
  sets.push("updated_at = ?");
  vals.push(nowIso(), u.id);
  await ctx.env.DB.prepare(`UPDATE users SET ${sets.join(", ")} WHERE id = ?`).bind(...vals).run();
  return json({ user: publicUser(await ctx.env.DB.prepare("SELECT * FROM users WHERE id = ?").bind(u.id).first<User>()) }, 200, ctx);
});

api.delete("/me", async (ctx) => {
  const u = requireUser(ctx);
  const b = await body(ctx);
  if (!(await checkPassword(String(b.password || ""), u.password_hash))) throw new HttpError(400, "Password is not right.");
  await ctx.env.DB.prepare("UPDATE subscribers SET unsubscribed_at = ?, marketing_consent = 0 WHERE email = ?").bind(nowIso(), u.email).run();
  await ctx.env.DB.prepare("DELETE FROM users WHERE id = ?").bind(u.id).run();
  await endSession(ctx);
  return json({ ok: true }, 200, ctx);
});

/** The member's standing with the project, as quests: real rows, real fractions. */
api.get("/me/standing", async (ctx) => {
  const u = requireUser(ctx);
  const db = ctx.env.DB;
  const has = async (sql: string, ...a: unknown[]) => Boolean(await db.prepare(sql).bind(...a).first());
  const sub = await db.prepare("SELECT id FROM subscribers WHERE email = ?").bind(u.email).first<{ id: number }>();
  const checks = {
    onTheList: Boolean(sub),
    readTheSample: await has("SELECT 1 FROM downloads WHERE book_slug = 'sample' AND (user_id = ? OR subscriber_id = ?)", u.id, sub?.id ?? -1),
    ownsTheBook: await has("SELECT 1 FROM orders WHERE status = 'paid' AND book_slug = 'the-40-hour-cabin' AND (user_id = ? OR email = ?)", u.id, u.email),
    onTheNetwork: await has("SELECT 1 FROM listings WHERE user_id = ?", u.id),
    backer: await has("SELECT 1 FROM backers WHERE user_id = ?", u.id),
    founder: await has("SELECT 1 FROM plaques JOIN backers ON backers.id = plaques.backer_id WHERE backers.user_id = ?", u.id),
    salvaged: await has("SELECT 1 FROM salvage_logs WHERE user_id = ?", u.id),
  };
  return json({ checks });
});

// ================================================================ the life account
// /account/life -- snowball.py, per member.

const life = (ctx: Ctx) => new LifeAccount(ctx.env.DB, requireUser(ctx).id);

api.get("/life", async (ctx) => {
  const a = life(ctx);
  return json({ review: await a.review(), score: await a.score(), path: await a.path() });
});

api.post("/life/skills", async (ctx) => {
  const b = await body(ctx);
  const name = text(b, "name", { min: 1, max: 60, required: true })!.toLowerCase();
  await life(ctx).addSkill(name, num(b, "level", { min: 1, max: 99 }) ?? 1);
  return json({ ok: true }, 201);
});

api.post("/life/skills/:name/level", async (ctx) => {
  const b = await body(ctx);
  const level = num(b, "level", { min: 1, max: 99, required: true })!;
  await life(ctx).setLevel(ctx.params.name, level);
  return json({ message: `Congratulations! Your ${ctx.params.name} level is now ${level}.` });
});

api.post("/life/skills/:name/xp", async (ctx) => {
  const b = await body(ctx);
  await life(ctx).gainXp(ctx.params.name, num(b, "amount", { min: -1e6, max: 1e6, required: true })!);
  return json({ ok: true });
});

api.post("/life/quests", async (ctx) => {
  const b = await body(ctx);
  const specs = Array.isArray(b.requires) ? b.requires.map(String).filter(Boolean).slice(0, 30) : [];
  const p = await life(ctx).addQuest(text(b, "name", { min: 1, max: 80, required: true })!, text(b, "description", { max: 500 }) || "", specs);
  return json(p, 201);
});

api.post("/life/quests/:name/start", async (ctx) => json(await life(ctx).start(ctx.params.name)));
api.post("/life/quests/:name/complete", async (ctx) => json(await life(ctx).complete(ctx.params.name)));

api.post("/life/methods", async (ctx) => {
  const b = await body(ctx);
  const xp: [string, number][] = [];
  for (const s of Array.isArray(b.xp) ? b.xp.map(String).slice(0, 12) : []) {
    const [skill, rate] = s.split(":");
    if (!skill || !Number.isFinite(Number(rate))) throw new HttpError(400, `bad xp stream '${s}' - use skill:xp_per_hour, e.g. cad:0.2`);
    xp.push([skill.trim().toLowerCase(), Number(rate)]);
  }
  await life(ctx).rate(text(b, "name", { min: 1, max: 60, required: true })!, num(b, "cash", { min: -1e5, max: 1e5, required: true })!,
    num(b, "cost", { min: 0, max: 1e5 }) ?? 0, xp, text(b, "notes", { max: 300 }) || "");
  return json({ ok: true }, 201);
});

api.post("/life/logs", async (ctx) => {
  const b = await body(ctx);
  const r = await life(ctx).log(text(b, "method", { min: 1, max: 60, required: true })!, num(b, "hours", { min: 0.05, max: 24, required: true })!,
    num(b, "cash", { min: -1e6, max: 1e6 }), text(b, "note", { max: 300 }) || "");
  return json(r, 201);
});

api.post("/life/assets", async (ctx) => {
  const b = await body(ctx);
  await life(ctx).addAsset(text(b, "name", { min: 1, max: 60, required: true })!, num(b, "value", { min: 0, max: 1e9 }) ?? 0, text(b, "description", { max: 300 }) || "");
  return json({ ok: true }, 201);
});

api.post("/life/capital", async (ctx) => {
  const b = await body(ctx);
  await life(ctx).setMeta("capital", num(b, "amount", { min: 0, max: 1e9, required: true })!);
  return json({ ok: true });
});

api.post("/life/weight", async (ctx) => {
  const b = await body(ctx);
  await life(ctx).setMeta("xp_weight", num(b, "amount", { min: 0, max: 1e4, required: true })!);
  return json({ ok: true });
});

// ================================================================ the network
// /network: pad hosts and the rest. Contact details only for members; location rounded
// to about a kilometre for everyone else.

export const KINDS = [
  { key: "pad_host", label: "Pad host", blurb: "Land with a serviced pad a dome can stand on -- built or planned." },
  { key: "dome_owner", label: "Dome owner", blurb: "Has a dome, is building one, or wants one and needs somewhere to put it." },
  { key: "recycler", label: "Recycler", blurb: "Reclaims and repurposes materials a build can use." },
  { key: "quilter", label: "Quilter", blurb: "Sews insulating layers from recycled clothing." },
  { key: "builder", label: "Builder", blurb: "Splits, cuts, assembles or installs -- frames, panels, pads, services." },
  { key: "timber", label: "Standing timber", blurb: "Has trees that could become a frame, or a mill that could split them." },
];
const KIND_KEYS = KINDS.map((k) => k.key);

interface ListingRow {
  id: number; user_id: number; kind: string; title: string; body: string | null; city: string | null; region: string | null; country: string | null;
  lat: number | null; lng: number | null; contact: string | null; nightly_rate_cents: number | null; occupancy_pct: number | null;
  season_cost_cents: number | null; season_nights: number | null; hookups: string | null; pad_status: string | null; visible: number;
  display_name: string; created_at: string; updated_at: string;
}

/** A pad's own numbers, worked out the same way for every pad: rate x nights let - running cost. */
export function padNumbers(r: Pick<ListingRow, "nightly_rate_cents" | "occupancy_pct" | "season_cost_cents" | "season_nights">) {
  if (r.nightly_rate_cents == null || r.occupancy_pct == null || r.season_nights == null) return null;
  const nightsLet = Math.round(r.season_nights * (r.occupancy_pct / 100));
  const revenueCents = nightsLet * r.nightly_rate_cents;
  const costCents = r.season_cost_cents ?? 0;
  return { nightsLet, revenueCents, costCents, netCents: revenueCents - costCents, netPerNightCents: nightsLet ? Math.round((revenueCents - costCents) / nightsLet) : null };
}

function toListing(r: ListingRow, viewer: User | null) {
  const own = viewer?.id === r.user_id;
  const round = (v: number | null) => (v == null ? null : Math.round(v * 100) / 100);
  return {
    id: r.id, kind: r.kind, title: r.title, body: r.body || "", city: r.city || "", region: r.region || "", country: r.country || "",
    lat: own ? r.lat : round(r.lat), lng: own ? r.lng : round(r.lng),
    contact: viewer ? r.contact || "" : null, contactHidden: !viewer && Boolean(r.contact),
    pad: r.kind === "pad_host" ? {
      nightlyRateCents: r.nightly_rate_cents, occupancyPct: r.occupancy_pct, seasonCostCents: r.season_cost_cents,
      seasonNights: r.season_nights, hookups: (r.hookups || "").split(",").filter(Boolean), status: r.pad_status || "planned",
      numbers: padNumbers(r),
    } : null,
    owner: { id: r.user_id, displayName: r.display_name }, mine: own, visible: Boolean(r.visible), updatedAt: r.updated_at,
  };
}

api.get("/network/kinds", () => json({ kinds: KINDS }));

api.get("/network", async (ctx) => {
  const q = ctx.url.searchParams;
  const where = ["listings.visible = 1"], args: unknown[] = [];
  const kind = q.get("kind");
  if (kind && KIND_KEYS.includes(kind)) { where.push("listings.kind = ?"); args.push(kind); }
  const term = (q.get("q") || "").trim().toLowerCase().slice(0, 100);
  if (term) {
    where.push("(LOWER(listings.title) LIKE ? OR LOWER(COALESCE(listings.body,'')) LIKE ? OR LOWER(COALESCE(listings.city,'')) LIKE ? OR LOWER(COALESCE(listings.region,'')) LIKE ?)");
    const like = `%${term}%`;
    args.push(like, like, like, like);
  }
  const rows = (await ctx.env.DB.prepare(
    `SELECT listings.*, users.display_name FROM listings JOIN users ON users.id = listings.user_id WHERE ${where.join(" AND ")} ORDER BY listings.updated_at DESC LIMIT 100`,
  ).bind(...args).all<ListingRow>()).results;
  return json({ total: rows.length, results: rows.map((r) => toListing(r, ctx.user)) });
});

api.get("/network/mine", async (ctx) => {
  const u = requireUser(ctx);
  const rows = (await ctx.env.DB.prepare("SELECT listings.*, users.display_name FROM listings JOIN users ON users.id = listings.user_id WHERE user_id = ? ORDER BY updated_at DESC").bind(u.id).all<ListingRow>()).results;
  return json({ results: rows.map((r) => toListing(r, u)) });
});

api.get("/network/:id", async (ctx) => {
  const r = await ctx.env.DB.prepare("SELECT listings.*, users.display_name FROM listings JOIN users ON users.id = listings.user_id WHERE listings.id = ?").bind(Number(ctx.params.id)).first<ListingRow>();
  if (!r || (!r.visible && r.user_id !== ctx.user?.id)) throw new HttpError(404, "No such listing.");
  return json({ listing: toListing(r, ctx.user) });
});

function listingFields(b: Record<string, unknown>, partial: boolean) {
  const f: Record<string, unknown> = {};
  if (!partial || "kind" in b) {
    const k = String(b.kind || "");
    if (!KIND_KEYS.includes(k)) throw new HttpError(400, "kind must be one of the network's kinds.");
    f.kind = k;
  }
  if (!partial || "title" in b) f.title = text(b, "title", { min: 3, max: 120, required: true });
  for (const [k, col, max] of [["body", "body", 4000], ["city", "city", 100], ["region", "region", 100], ["country", "country", 100], ["postalCode", "postal_code", 20], ["contact", "contact", 300]] as const) {
    if (k in b) f[col] = text(b, k, { max });
  }
  for (const [k, col, min, max] of [["lat", "lat", -90, 90], ["lng", "lng", -180, 180], ["occupancyPct", "occupancy_pct", 0, 100], ["seasonNights", "season_nights", 0, 366]] as const) {
    if (k in b) f[col] = num(b, k, { min, max });
  }
  for (const [k, col] of [["nightlyRate", "nightly_rate_cents"], ["seasonCost", "season_cost_cents"]] as const) {
    if (k in b) { const v = num(b, k, { min: 0, max: 1e6 }); f[col] = v == null ? null : Math.round(v * 100); }
  }
  if ("hookups" in b) f.hookups = Array.isArray(b.hookups) ? b.hookups.map(String).filter((h) => ["water", "power", "septic", "internet"].includes(h)).join(",") : null;
  if ("padStatus" in b) {
    const s = String(b.padStatus || "planned");
    if (!["planned", "built", "hosting"].includes(s)) throw new HttpError(400, "padStatus is planned, built or hosting.");
    f.pad_status = s;
  }
  if ("visible" in b) f.visible = b.visible === false ? 0 : 1;
  return f;
}

api.post("/network", async (ctx) => {
  const u = requireUser(ctx);
  const b = await body(ctx);
  const f = listingFields(b, false);
  const n = (await ctx.env.DB.prepare("SELECT COUNT(*) n FROM listings WHERE user_id = ?").bind(u.id).first<{ n: number }>())!.n;
  if (n >= 20) throw new HttpError(400, "Twenty listings is the limit per account.");
  const cols = Object.keys(f);
  const r = await ctx.env.DB.prepare(`INSERT INTO listings(${cols.join(", ")}, user_id, created_at, updated_at) VALUES(${cols.map(() => "?").join(", ")}, ?, ?, ?) RETURNING id`)
    .bind(...Object.values(f), u.id, nowIso(), nowIso()).first<{ id: number }>();
  await event(ctx, f.kind === "pad_host" ? "pad" : "listing", f.kind === "pad_host" ? `A pad joined the network: ${f.title}` : `New on the network: ${f.title}`);
  const row = await ctx.env.DB.prepare("SELECT listings.*, users.display_name FROM listings JOIN users ON users.id = listings.user_id WHERE listings.id = ?").bind(r!.id).first<ListingRow>();
  return json({ listing: toListing(row!, u) }, 201);
});

api.patch("/network/:id", async (ctx) => {
  const u = requireUser(ctx);
  const id = Number(ctx.params.id);
  const row = await ctx.env.DB.prepare("SELECT user_id FROM listings WHERE id = ?").bind(id).first<{ user_id: number }>();
  if (!row) throw new HttpError(404, "No such listing.");
  if (row.user_id !== u.id && u.role !== "admin") throw new HttpError(403, "That listing is not yours.");
  const f = listingFields(await body(ctx), true);
  const cols = Object.keys(f);
  if (cols.length) {
    await ctx.env.DB.prepare(`UPDATE listings SET ${cols.map((c) => `${c} = ?`).join(", ")}, updated_at = ? WHERE id = ?`).bind(...Object.values(f), nowIso(), id).run();
  }
  const saved = await ctx.env.DB.prepare("SELECT listings.*, users.display_name FROM listings JOIN users ON users.id = listings.user_id WHERE listings.id = ?").bind(id).first<ListingRow>();
  return json({ listing: toListing(saved!, u) });
});

api.delete("/network/:id", async (ctx) => {
  const u = requireUser(ctx);
  const id = Number(ctx.params.id);
  const row = await ctx.env.DB.prepare("SELECT user_id FROM listings WHERE id = ?").bind(id).first<{ user_id: number }>();
  if (!row) throw new HttpError(404, "No such listing.");
  if (row.user_id !== u.id && u.role !== "admin") throw new HttpError(403, "That listing is not yours.");
  await ctx.env.DB.prepare("DELETE FROM listings WHERE id = ?").bind(id).run();
  return json({ ok: true });
});

// ================================================================ recyclers
// /recyclers: salvage logged as account work.

api.post("/salvage", async (ctx) => {
  const u = requireUser(ctx);
  const b = await body(ctx);
  const material = text(b, "material", { min: 2, max: 80, required: true })!;
  const replacement = num(b, "replacementValue", { min: 0, max: 1e6, required: true })!;
  const hours = num(b, "hours", { min: 0.05, max: 200, required: true })!;
  await ctx.env.DB.prepare("INSERT INTO salvage_logs(user_id, material, quantity, unit, hours, replacement_cents, note, created_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?)")
    .bind(u.id, material, num(b, "quantity", { min: 0, max: 1e7, required: true }), text(b, "unit", { min: 1, max: 20, required: true }), hours,
      Math.round(replacement * 100), text(b, "note", { max: 300 }), nowIso()).run();
  await event(ctx, "salvage", `A recycler logged ${material}`);
  return json({ savedPerHourCents: Math.round((replacement * 100) / hours) }, 201);
});

api.get("/salvage", async (ctx) => {
  const db = ctx.env.DB;
  const board = (await db.prepare(
    "SELECT users.display_name, SUM(salvage_logs.hours) hours, SUM(salvage_logs.replacement_cents) cents, COUNT(*) loads FROM salvage_logs JOIN users ON users.id = salvage_logs.user_id GROUP BY users.id ORDER BY cents DESC LIMIT 25",
  ).all()).results;
  const mine = ctx.user ? (await db.prepare("SELECT material, quantity, unit, hours, replacement_cents, note, created_at FROM salvage_logs WHERE user_id = ? ORDER BY id DESC LIMIT 50").bind(ctx.user.id).all()).results : [];
  return json({ board, mine });
});

// ================================================================ the shop
// /book and /start: the digital edition, the triangular book (two prices, one on the
// buyer's honor), the design session. Stripe Checkout; a physical product collects an
// address there.

api.get("/catalogue", async (ctx) => json({ products: await catalogue(ctx) }));

api.get("/shop", (ctx) => json({ mode: checkoutMode(ctx.env), mail: mailReady(ctx.env) }));

api.post("/checkout", async (ctx) => {
  const b = await body(ctx);
  honeypot(b);
  const slug = text(b, "product", { max: 80 }) || text(b, "book", { max: 80, required: true })!;
  const prod = await product(ctx, slug);
  const pr = prod ? await price(ctx, prod.slug, text(b, "price", { max: 40 }) || "standard") : null;
  if (!prod || !pr || pr.amount_cents <= 0 || !["digital", "physical", "service"].includes(prod.kind) || !["live", "preorder"].includes(prod.status)) {
    throw new HttpError(404, "That is not for sale right now.");
  }
  let honorNote: string | null = null;
  if (pr.honor) {
    honorNote = text(b, "honorNote", { min: 10, max: 600 });
    if (!honorNote) throw new HttpError(400, "Please describe what you are giving -- this price runs on your word.");
  }
  const mode = checkoutMode(ctx.env);
  if (!mode) throw new HttpError(503, "The shop opens soon. Leave your email on the sample page and you will hear first.");
  const e = email(b);
  const ref = randomToken(9), key = randomToken(24);
  const physical = prod.kind === "physical";
  const r = await ctx.env.DB.prepare(
    "INSERT INTO orders(ref, key_hash, book_slug, amount_cents, currency, email, user_id, provider, marketing_consent, price_key, honor_note, fulfillment, created_at) "
    + "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id",
  ).bind(ref, await sha256Hex(key), prod.slug, pr.amount_cents, pr.currency, e, ctx.user?.id ?? null, mode, b.marketingConsent === true ? 1 : 0,
    pr.key, honorNote, physical ? "waiting" : null, nowIso()).first<{ id: number }>();
  const thanks = `/thanks/${ref}?key=${encodeURIComponent(key)}`;
  if (mode === "test") return json({ url: `/checkout/test/${ref}?key=${encodeURIComponent(key)}`, test: true }, 201);
  const session = await createCheckoutSession(ctx.env, {
    ref, slug: prod.slug, cents: pr.amount_cents, currency: pr.currency, email: e,
    name: `${prod.title}${prod.subtitle ? `: ${prod.subtitle}` : ""}${pr.key !== "standard" ? ` (${pr.label})` : ""}`,
    description: prod.kind === "service" ? "A one-on-one design session."
      : physical ? (prod.ships_note || "A printed book.") : "Digital edition (PDF). Every future edition included.",
    shipTo: physical ? (prod.ship_countries || "US").split(",").map((c) => c.trim()).filter(Boolean) : undefined,
    successUrl: `${site(ctx)}${thanks}`, cancelUrl: `${site(ctx)}/book?cancelled=1`,
  });
  await ctx.env.DB.prepare("UPDATE orders SET provider_session = ? WHERE id = ?").bind(session.id, r!.id).run();
  return json({ url: session.url, test: false }, 201);
});

interface OrderRow {
  id: number; ref: string; key_hash: string; book_slug: string; amount_cents: number; currency: string; email: string | null; user_id: number | null;
  subscriber_id: number | null; status: string; provider: string; provider_session: string | null; marketing_consent: number; created_at: string; paid_at: string | null;
  price_key: string | null; honor_note: string | null; ship_name: string | null; ship_address: string | null; fulfillment: string | null;
}

async function loadOrder(ctx: Ctx) {
  const o = await ctx.env.DB.prepare("SELECT * FROM orders WHERE ref = ?").bind(ctx.params.ref).first<OrderRow>();
  const key = ctx.url.searchParams.get("key") || "";
  const owner = ctx.user && o?.user_id === ctx.user.id;
  if (!o || (!owner && !sameString(await sha256Hex(key), o.key_hash))) throw new HttpError(404, "No order matches that link. Check you copied all of it.");
  return { order: o, key };
}

/** Mark an order paid, once. Later calls change nothing. A physical order keeps its address. */
async function markPaid(ctx: Ctx, o: OrderRow, session?: Record<string, any> | null) {
  if (o.status === "paid") return o;
  const buyer = normaliseEmail(session?.customer_details?.email || o.email || "");
  const sub = buyer ? await upsertSubscriber(ctx, { email: buyer, consent: Boolean(o.marketing_consent), source: o.book_slug }) : null;
  const ship = session?.collected_information?.shipping_details || session?.shipping_details || null;
  const res = await ctx.env.DB.prepare(
    "UPDATE orders SET status = 'paid', paid_at = ?, email = ?, subscriber_id = ?, ship_name = COALESCE(?, ship_name), ship_address = COALESCE(?, ship_address) WHERE id = ? AND status = 'pending'",
  ).bind(nowIso(), buyer || o.email, sub?.id ?? null, ship?.name ?? null, ship?.address ? JSON.stringify(ship.address) : null, o.id).run();
  if (res.meta.changes && sub) {
    await recordSignup(ctx, sub.id, "purchase", o.book_slug);
    const p = await product(ctx, o.book_slug);
    await event(ctx, "sale", p?.kind === "service" ? "A design session was booked"
      : p?.kind === "physical" ? `A ${p.subtitle || p.title} was ordered` : `A copy of ${p?.title || "the book"} was bought`);
  }
  return (await ctx.env.DB.prepare("SELECT * FROM orders WHERE id = ?").bind(o.id).first<OrderRow>())!;
}

async function publicOrder(ctx: Ctx, o: OrderRow, key: string) {
  const p = await product(ctx, o.book_slug);
  const x = extras(o.book_slug);
  const paid = o.status === "paid";
  const digital = p?.kind === "digital";
  return {
    ref: o.ref, status: o.status, amountCents: o.amount_cents, currency: o.currency, email: o.email || "", paidAt: o.paid_at,
    book: { slug: o.book_slug, title: p?.title || o.book_slug, subtitle: p?.subtitle || "", kind: p?.kind || "digital" },
    priceKey: o.price_key, honorNote: o.honor_note, fulfillment: o.fulfillment, shipsNote: p?.kind === "physical" ? p.ships_note : null,
    downloadUrl: paid && digital ? `/api/orders/${o.ref}/download${key ? `?key=${encodeURIComponent(key)}` : ""}` : null,
    codebaseUrl: paid ? x?.codebaseUrl || "" : "",
    bookingNote: paid && p?.kind === "service" ? x?.bookingNote || "" : "",
    test: o.provider === "test",
  };
}

api.get("/orders/:ref", async (ctx) => {
  let { order, key } = await loadOrder(ctx);
  if (order.status === "pending" && order.provider === "stripe" && order.provider_session && ctx.env.STRIPE_SECRET_KEY) {
    const s = await retrieveCheckoutSession(ctx.env, order.provider_session).catch(() => null);
    if (s?.payment_status === "paid") order = await markPaid(ctx, order, s);
  }
  return json({ order: await publicOrder(ctx, order, key) });
});

api.post("/orders/:ref/test-pay", async (ctx) => {
  if (ctx.env.TEST_CHECKOUT !== "1" || ctx.env.STRIPE_SECRET_KEY) throw new HttpError(404, "Not found.");
  const { order, key } = await loadOrder(ctx);
  if (order.provider !== "test") throw new HttpError(400, "Only a test order can be paid here.");
  return json({ order: await publicOrder(ctx, await markPaid(ctx, order), key) });
});

api.get("/orders/:ref/download", async (ctx) => {
  const { order } = await loadOrder(ctx);
  if (order.status !== "paid") throw new HttpError(402, "This order has not been paid yet.");
  const p = await product(ctx, order.book_slug);
  if (!p || p.kind !== "digital") throw new HttpError(404, "There is no file for this order.");
  return streamBook(ctx, p, { subscriberId: order.subscriber_id });
});

api.post("/stripe/webhook", async (ctx) => {
  const raw = await ctx.request.text();
  if (!(await verifyStripeSignature(raw, ctx.request.headers.get("stripe-signature"), ctx.env.STRIPE_WEBHOOK_SECRET))) throw new HttpError(400, "Bad signature.");
  const ev = JSON.parse(raw);
  if (ev.type === "checkout.session.completed" || ev.type === "checkout.session.async_payment_succeeded") {
    const s = ev.data?.object || {};
    const ref = s.metadata?.ref || s.client_reference_id;
    const o = ref ? await ctx.env.DB.prepare("SELECT * FROM orders WHERE ref = ?").bind(ref).first<OrderRow>() : null;
    if (o && s.payment_status === "paid") await markPaid(ctx, o, s);
  }
  return json({ received: true });
});

// ================================================================ admin
// /admin: the list, and recording real backers and founder plaques.

api.get("/admin/subscribers", async (ctx) => {
  requireAdmin(ctx);
  const rows = (await ctx.env.DB.prepare("SELECT email, name, marketing_consent, source, created_at, unsubscribed_at FROM subscribers ORDER BY id DESC").all()).results;
  if (ctx.url.searchParams.get("format") === "csv") {
    const esc = (v: unknown) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    const csv = ["email,name,consent,source,created_at,unsubscribed_at", ...rows.map((r: any) => [r.email, r.name, r.marketing_consent, r.source, r.created_at, r.unsubscribed_at].map(esc).join(","))].join("\n");
    return new Response(csv, { headers: { "Content-Type": "text/csv", "Content-Disposition": 'attachment; filename="subscribers.csv"' } });
  }
  const offers = (await ctx.env.DB.prepare("SELECT kind, book_slug, COUNT(*) n FROM signups GROUP BY kind, book_slug ORDER BY n DESC").all()).results;
  return json({ subscribers: rows, offers });
});

api.post("/admin/backers", async (ctx) => {
  requireAdmin(ctx);
  const b = await body(ctx);
  const tier = text(b, "tier", { max: 40, required: true })!;
  if (!facts.tiers.some((t) => t.key === tier)) throw new HttpError(400, "tier must be one of the campaign's tiers.");
  const userEmail = text(b, "userEmail", { max: 320 });
  const user = userEmail ? await ctx.env.DB.prepare("SELECT id FROM users WHERE email = ?").bind(normaliseEmail(userEmail)).first<{ id: number }>() : null;
  const name = text(b, "displayName", { min: 1, max: 80, required: true })!;
  const r = await ctx.env.DB.prepare("INSERT INTO backers(user_id, display_name, tier, pledge_cents, public, created_at) VALUES(?, ?, ?, ?, ?, ?) RETURNING id")
    .bind(user?.id ?? null, name, tier, Math.round(num(b, "pledge", { min: 0, max: 1e7, required: true })! * 100), b.public === false ? 0 : 1, nowIso()).first<{ id: number }>();
  await event(ctx, "backer", b.public === false ? "A new backer joined the build" : `${name} backed the build`);
  return json({ id: r!.id }, 201);
});

api.post("/admin/plaques", async (ctx) => {
  requireAdmin(ctx);
  const b = await body(ctx);
  const slot = num(b, "slot", { min: 1, max: facts.plaques.slots, required: true })!;
  const backerId = num(b, "backerId", { min: 1, required: true })!;
  if (!(await ctx.env.DB.prepare("SELECT 1 FROM backers WHERE id = ?").bind(backerId).first())) throw new HttpError(404, "No such backer.");
  if (await ctx.env.DB.prepare("SELECT 1 FROM plaques WHERE slot = ?").bind(slot).first()) throw new HttpError(409, `Panel ${slot} is already claimed.`);
  await ctx.env.DB.prepare("INSERT INTO plaques(slot, backer_id, inscription, status, claimed_at) VALUES(?, ?, ?, 'claimed', ?)")
    .bind(slot, backerId, text(b, "inscription", { max: 80 }), nowIso()).run();
  await event(ctx, "plaque", `Founder plaque on panel ${slot} claimed`);
  return json({ ok: true }, 201);
});

api.patch("/admin/prices/:product/:key", async (ctx) => {
  requireAdmin(ctx);
  const b = await body(ctx);
  const sets: string[] = [], vals: unknown[] = [];
  if ("amount" in b) { sets.push("amount_cents = ?"); vals.push(Math.round(num(b, "amount", { min: 0, max: 1e6, required: true })! * 100)); }
  if ("active" in b) { sets.push("active = ?"); vals.push(b.active === false ? 0 : 1); }
  if ("label" in b) { sets.push("label = ?"); vals.push(text(b, "label", { min: 1, max: 80, required: true })); }
  if (!sets.length) throw new HttpError(400, "Nothing to change.");
  const r = await ctx.env.DB.prepare(`UPDATE prices SET ${sets.join(", ")} WHERE product = ? AND key = ?`).bind(...vals, ctx.params.product, ctx.params.key).run();
  if (!r.meta.changes) throw new HttpError(404, "No such price.");
  return json({ products: await catalogue(ctx) });
});

api.patch("/admin/products/:slug", async (ctx) => {
  requireAdmin(ctx);
  const b = await body(ctx);
  const sets: string[] = [], vals: unknown[] = [];
  if ("status" in b) {
    const st = String(b.status);
    if (!["live", "preorder", "waitlist", "hidden"].includes(st)) throw new HttpError(400, "status is live, preorder, waitlist or hidden.");
    sets.push("status = ?"); vals.push(st);
  }
  if ("externalUrl" in b) { sets.push("external_url = ?"); vals.push(text(b, "externalUrl", { max: 500 })); }
  if ("shipsNote" in b) { sets.push("ships_note = ?"); vals.push(text(b, "shipsNote", { max: 600 })); }
  if (!sets.length) throw new HttpError(400, "Nothing to change.");
  sets.push("updated_at = ?"); vals.push(nowIso());
  const r = await ctx.env.DB.prepare(`UPDATE products SET ${sets.join(", ")} WHERE slug = ?`).bind(...vals, ctx.params.slug).run();
  if (!r.meta.changes) throw new HttpError(404, "No such product.");
  return json({ products: await catalogue(ctx) });
});

api.get("/admin/orders", async (ctx) => {
  requireAdmin(ctx);
  const rows = (await ctx.env.DB.prepare(
    "SELECT ref, book_slug, price_key, amount_cents, email, honor_note, ship_name, ship_address, fulfillment, status, paid_at FROM orders WHERE status = 'paid' ORDER BY id DESC LIMIT 200",
  ).all()).results;
  return json({ orders: rows });
});

api.patch("/admin/orders/:ref", async (ctx) => {
  requireAdmin(ctx);
  const b = await body(ctx);
  const f = String(b.fulfillment || "");
  if (!["waiting", "printed", "shipped"].includes(f)) throw new HttpError(400, "fulfillment is waiting, printed or shipped.");
  const r = await ctx.env.DB.prepare("UPDATE orders SET fulfillment = ? WHERE ref = ? AND fulfillment IS NOT NULL").bind(f, ctx.params.ref).run();
  if (!r.meta.changes) throw new HttpError(404, "No physical order with that reference.");
  return json({ ok: true });
});

api.get("/admin/backers", async (ctx) => {
  requireAdmin(ctx);
  return json({ backers: (await ctx.env.DB.prepare("SELECT * FROM backers ORDER BY id DESC").all()).results });
});
