// Accounts, for members and for the owner. Members: reset a forgotten password, confirm
// their email, see every device signed in and end any of them, download everything the site
// holds about them. The owner: find any account, see its sessions, orders and listings,
// suspend or restore it, sign it out everywhere, make a reset link, delete it -- each act
// written to the audit log.

import { currentSessionHash, normaliseEmail, publicUser, requireAdmin, requireOwner, requireUser, roleFor, startSession } from "./auth";
import { hashPassword, randomToken, sha256Hex } from "./crypto";
import { Ctx, HttpError, User, body, email, honeypot, json, nowIso, text } from "./http";
import { enqueue, site } from "./mail";
import { audit } from "./ops";
import api from "./routes";

const HOUR = 3_600_000;

/** A single-use link for this user. Only its hash is stored. */
async function userToken(ctx: Ctx, userId: number, purpose: "reset" | "verify", hours: number) {
  const token = randomToken();
  await ctx.env.DB.prepare("INSERT INTO user_tokens(token_hash, user_id, purpose, created_at, expires_at) VALUES(?, ?, ?, ?, ?)")
    .bind(await sha256Hex(token), userId, purpose, nowIso(), nowIso(hours * HOUR)).run();
  return token;
}

async function useToken(ctx: Ctx, token: string, purpose: "reset" | "verify") {
  const hash = await sha256Hex(String(token || ""));
  const row = await ctx.env.DB.prepare("SELECT user_id FROM user_tokens WHERE token_hash = ? AND purpose = ? AND used_at IS NULL AND expires_at > ?")
    .bind(hash, purpose, nowIso()).first<{ user_id: number }>();
  if (!row) throw new HttpError(400, "That link has expired or was already used. Ask for a new one.");
  await ctx.env.DB.prepare("UPDATE user_tokens SET used_at = ? WHERE token_hash = ?").bind(nowIso(), hash).run();
  return row.user_id;
}

/** Account mail goes through the same queue as everything else; the address must be on the list
 *  (every account is, from signup) -- with no marketing consent, so only account mail reaches it. */
async function mailUser(ctx: Ctx, u: Pick<User, "email" | "display_name">, subject: string, text: string) {
  let sub = await ctx.env.DB.prepare("SELECT id, email, name, marketing_consent, status FROM subscribers WHERE email = ?").bind(u.email)
    .first<{ id: number; email: string; name: string | null; marketing_consent: number; status: string }>();
  if (!sub) {
    sub = await ctx.env.DB.prepare("INSERT INTO subscribers(email, name, marketing_consent, source, created_at) VALUES(?, ?, 0, 'account', ?) RETURNING id, email, name, marketing_consent, status")
      .bind(u.email, u.display_name, nowIso()).first();
  }
  return enqueue(ctx, { sub: sub!, identity: "owner", kind: "transactional", subject, body: text });
}

async function sendReset(ctx: Ctx, u: User, hours: number) {
  const link = `${site(ctx.env, ctx)}/reset?t=${await userToken(ctx, u.id, "reset", hours)}`;
  const r = await mailUser(ctx, u, "Reset your Zeanah Lab password",
    `Hi {{name}},\n\nSomeone (we hope you) asked to reset the password for this account. Choose a new one here:\n${link}\n\nThe link works once, for ${hours === 1 ? "one hour" : `${hours} hours`}. If you did not ask, ignore this email; your password has not changed.`);
  return { link, queued: Boolean(r.id) };
}

// ---------------------------------------------------------------- passwords and email

api.post("/password/forgot", async (ctx) => {
  const b = await body(ctx);
  honeypot(b);
  const e = email(b);
  const u = await ctx.env.DB.prepare("SELECT * FROM users WHERE email = ?").bind(e).first<User>();
  if (u && u.status !== "suspended") {
    const recent = (await ctx.env.DB.prepare("SELECT COUNT(*) n FROM user_tokens WHERE user_id = ? AND purpose = 'reset' AND created_at >= ?").bind(u.id, nowIso(-HOUR)).first<{ n: number }>())!.n;
    if (recent < 3) await sendReset(ctx, u, 1);
  }
  // the same answer whether or not the address has an account
  return json({ ok: true, note: "If that address has an account, a reset link is on its way. It works for one hour." });
});

api.post("/password/reset", async (ctx) => {
  const b = await body(ctx);
  const userId = await useToken(ctx, String(b.t || ""), "reset");
  const password = text(b, "password", { min: 10, max: 200, required: true })!;
  await ctx.env.DB.prepare("UPDATE users SET password_hash = ?, updated_at = ?, email_verified_at = COALESCE(email_verified_at, ?) WHERE id = ?")
    .bind(await hashPassword(password), nowIso(), nowIso(), userId).run();   // the link reached their inbox: the address is theirs
  await ctx.env.DB.prepare("DELETE FROM sessions WHERE user_id = ?").bind(userId).run();
  const u = (await ctx.env.DB.prepare("SELECT * FROM users WHERE id = ?").bind(userId).first<User>())!;
  if (u.status === "suspended") throw new HttpError(403, "This account is suspended.");
  await startSession(ctx, userId);
  await audit(ctx, "user.password_reset", `user:${userId}`, null, { kind: "user", id: userId, name: u.email });
  return json({ user: publicUser(u) }, 200, ctx);
});

api.post("/me/verify", async (ctx) => {
  const u = requireUser(ctx);
  if (u.email_verified_at) return json({ ok: true, already: true });
  const link = `${site(ctx.env, ctx)}/verify?t=${await userToken(ctx, u.id, "verify", 72)}`;
  const r = await mailUser(ctx, u, "Confirm your email for Zeanah Lab", `Hi {{name}},\n\nConfirm this is your address with one click:\n${link}\n\nThe link works for three days.`);
  return json({ ok: true, queued: Boolean(r.id) });
});

api.post("/verify", async (ctx) => {
  const b = await body(ctx);
  const userId = await useToken(ctx, String(b.t || ""), "verify");
  await ctx.env.DB.prepare("UPDATE users SET email_verified_at = COALESCE(email_verified_at, ?) WHERE id = ?").bind(nowIso(), userId).run();
  return json({ ok: true });
});

// ---------------------------------------------------------------- the member's own sessions and data

const SESSION_COLS = "substr(token_hash, 1, 12) id, created_at, last_seen_at, expires_at, user_agent, country";

api.get("/me/sessions", async (ctx) => {
  const u = requireUser(ctx);
  const here = (await currentSessionHash(ctx))?.slice(0, 12);
  const rows = (await ctx.env.DB.prepare(`SELECT ${SESSION_COLS} FROM sessions WHERE user_id = ? AND expires_at > ? ORDER BY COALESCE(last_seen_at, created_at) DESC`)
    .bind(u.id, nowIso()).all<{ id: string }>()).results;
  return json({ sessions: rows.map((r) => ({ ...r, current: r.id === here })) });
});

api.delete("/me/sessions/:id", async (ctx) => {
  const u = requireUser(ctx);
  const id = String(ctx.params.id);
  if (!/^[0-9a-f]{12}$/.test(id)) throw new HttpError(400, "No such session.");
  await ctx.env.DB.prepare("DELETE FROM sessions WHERE user_id = ? AND substr(token_hash, 1, 12) = ?").bind(u.id, id).run();
  return json({ ok: true });
});

/** Sign out everywhere except here. */
api.post("/me/sessions/others", async (ctx) => {
  const u = requireUser(ctx);
  const here = await currentSessionHash(ctx);
  const r = await ctx.env.DB.prepare("DELETE FROM sessions WHERE user_id = ? AND token_hash != ?").bind(u.id, here || "").run();
  return json({ ok: true, ended: r.meta.changes });
});

const MINE = ["listings", "salvage_logs", "skills", "quests", "quest_requirements", "methods", "method_xp", "assets", "logs", "account_meta", "backers"];

/** Everything the site keeps about this member, as one JSON file. */
api.get("/me/export", async (ctx) => {
  const u = requireUser(ctx);
  const db = ctx.env.DB;
  const out: Record<string, unknown> = {
    exportedAt: nowIso(), site: site(ctx.env, ctx),
    account: { ...publicUser(u), lastSeenAt: u.last_seen_at ?? null, emailVerifiedAt: u.email_verified_at ?? null },
  };
  const sub = await db.prepare("SELECT id, email, name, status, marketing_consent, source, first_source, first_campaign, first_landing, created_at, confirmed_at, unsubscribed_at FROM subscribers WHERE email = ?").bind(u.email).first<{ id: number }>();
  out.list = sub ? { ...sub, tags: (await db.prepare("SELECT tag, created_at FROM subscriber_tags WHERE subscriber_id = ?").bind(sub.id).all()).results } : null;
  out.mailSentToYou = sub ? (await db.prepare("SELECT identity, kind, subject, status, created_at, sent_at FROM outbox WHERE subscriber_id = ? ORDER BY id").bind(sub.id).all()).results : [];
  out.orders = (await db.prepare("SELECT ref, book_slug product, price_key, amount_cents, currency, status, fulfillment, honor_note, ship_name, ship_address, created_at, paid_at FROM orders WHERE user_id = ? OR email = ? ORDER BY id").bind(u.id, u.email).all()).results;
  for (const t of MINE) out[t] = (await db.prepare(`SELECT * FROM ${t} WHERE user_id = ?`).bind(u.id).all()).results;
  out.sessions = (await db.prepare(`SELECT ${SESSION_COLS} FROM sessions WHERE user_id = ?`).bind(u.id).all()).results;
  const res = json(out);
  res.headers.set("Content-Disposition", `attachment; filename="zeanahlab-${u.id}-${nowIso().slice(0, 10)}.json"`);
  return res;
});

// ---------------------------------------------------------------- the owner's controls

api.get("/admin/users", async (ctx) => {
  requireAdmin(ctx);
  const q = `%${(ctx.url.searchParams.get("q") || "").trim().toLowerCase()}%`;
  const status = ctx.url.searchParams.get("status") || "";
  const rows = (await ctx.env.DB.prepare(
    `SELECT u.id, u.email, u.display_name, u.role, u.status, u.created_at, u.last_seen_at, u.email_verified_at, u.public_profile, u.city, u.region, u.country,
       (SELECT COUNT(*) FROM orders o WHERE (o.user_id = u.id OR o.email = u.email) AND o.status = 'paid') orders,
       (SELECT COALESCE(SUM(amount_cents), 0) FROM orders o WHERE (o.user_id = u.id OR o.email = u.email) AND o.status = 'paid') spent_cents,
       (SELECT COUNT(*) FROM listings l WHERE l.user_id = u.id) listings,
       (SELECT COUNT(*) FROM sessions s WHERE s.user_id = u.id AND s.expires_at > ?) sessions,
       (SELECT s.status FROM subscribers s WHERE s.email = u.email) list_status
     FROM users u WHERE (lower(u.email) LIKE ? OR lower(u.display_name) LIKE ?) AND (? = '' OR u.status = ?)
     ORDER BY COALESCE(u.last_seen_at, u.created_at) DESC LIMIT 500`,
  ).bind(nowIso(), q, q, status, status).all()).results;
  const counts = (await ctx.env.DB.prepare("SELECT status, COUNT(*) n FROM users GROUP BY status").all()).results;
  const active7 = (await ctx.env.DB.prepare("SELECT COUNT(*) n FROM users WHERE last_seen_at >= ?").bind(nowIso(-7 * 86_400_000)).first<{ n: number }>())!.n;
  return json({ users: rows, counts, active7 });
});

async function target(ctx: Ctx) {
  const u = await ctx.env.DB.prepare("SELECT * FROM users WHERE id = ?").bind(Number(ctx.params.id)).first<User & { suspended_reason: string | null; admin_note: string | null }>();
  if (!u) throw new HttpError(404, "No such account.");
  return u;
}

/** A manager acts on members; only the owner acts on a manager or the owner's own account. */
function mayActOn(ctx: Ctx, t: User) {
  const me = requireAdmin(ctx);
  const staff = roleFor(ctx.env, t.email, t.role) !== "member";
  if (me.role !== "admin" && staff && t.id !== me.id) throw new HttpError(403, "Only the owner can change a manager's or the owner's account.");
  return me;
}

api.get("/admin/users/:id", async (ctx) => {
  requireAdmin(ctx);
  const u = await target(ctx);
  const db = ctx.env.DB;
  const sub = await db.prepare("SELECT id, status, marketing_consent, first_source, first_campaign, created_at, confirmed_at FROM subscribers WHERE email = ?").bind(u.email).first<{ id: number }>();
  return json({
    user: { ...publicUser(u), role: roleFor(ctx.env, u.email, u.role), status: u.status, suspendedReason: u.suspended_reason, adminNote: u.admin_note, lastSeenAt: u.last_seen_at, emailVerifiedAt: u.email_verified_at, isAdmin: roleFor(ctx.env, u.email) === "admin" },
    list: sub ? { ...sub, tags: (await db.prepare("SELECT tag FROM subscriber_tags WHERE subscriber_id = ?").bind(sub.id).all<{ tag: string }>()).results.map((t) => t.tag) } : null,
    sessions: (await db.prepare(`SELECT ${SESSION_COLS} FROM sessions WHERE user_id = ? AND expires_at > ? ORDER BY COALESCE(last_seen_at, created_at) DESC`).bind(u.id, nowIso()).all()).results,
    orders: (await db.prepare("SELECT ref, book_slug product, amount_cents, status, fulfillment, created_at, paid_at FROM orders WHERE user_id = ? OR email = ? ORDER BY id DESC LIMIT 50").bind(u.id, u.email).all()).results,
    listings: (await db.prepare("SELECT id, kind, title, visible, created_at FROM listings WHERE user_id = ? ORDER BY id DESC").bind(u.id).all()).results,
    logins: (await db.prepare("SELECT ok, ts FROM login_attempts WHERE email = ? ORDER BY id DESC LIMIT 20").bind(u.email).all()).results,
    audit: (await db.prepare("SELECT ts, actor_kind, actor_name, action, detail FROM audit_log WHERE target = ? ORDER BY id DESC LIMIT 50").bind(`user:${u.id}`).all()).results,
  });
});

api.patch("/admin/users/:id", async (ctx) => {
  requireAdmin(ctx);
  const u = await target(ctx);
  const me = mayActOn(ctx, u);
  const b = await body(ctx);
  const changes: Record<string, unknown> = {};
  if ("status" in b) {
    const s = String(b.status);
    if (!["active", "suspended"].includes(s)) throw new HttpError(400, "status is active or suspended.");
    if (s === "suspended" && (u.id === me.id || roleFor(ctx.env, u.email) === "admin")) throw new HttpError(400, "An admin account cannot be suspended here; take it out of ADMIN_EMAILS first.");
    changes.status = s;
    changes.suspended_reason = s === "suspended" ? text(b, "reason", { max: 300 }) : null;
  }
  if ("adminNote" in b) changes.admin_note = text(b, "adminNote", { max: 2000 });
  if ("displayName" in b) changes.display_name = text(b, "displayName", { min: 1, max: 80, required: true });
  if ("emailVerified" in b) changes.email_verified_at = b.emailVerified === true ? (u.email_verified_at || nowIso()) : null;
  if (!Object.keys(changes).length) throw new HttpError(400, "Nothing to change.");
  await ctx.env.DB.prepare(`UPDATE users SET ${Object.keys(changes).map((k) => `${k} = ?`).join(", ")}, updated_at = ? WHERE id = ?`)
    .bind(...Object.values(changes), nowIso(), u.id).run();
  if (changes.status === "suspended") await ctx.env.DB.prepare("DELETE FROM sessions WHERE user_id = ?").bind(u.id).run();
  await audit(ctx, changes.status ? `user.${changes.status === "suspended" ? "suspend" : "restore"}` : "user.edit", `user:${u.id}`,
    { ...changes, admin_note: "admin_note" in changes ? "(changed)" : undefined });
  return json({ ok: true });
});

api.post("/admin/users/:id/signout", async (ctx) => {
  requireAdmin(ctx);
  const u = await target(ctx);
  mayActOn(ctx, u);
  const r = await ctx.env.DB.prepare("DELETE FROM sessions WHERE user_id = ?").bind(u.id).run();
  await audit(ctx, "user.signout_everywhere", `user:${u.id}`, { ended: r.meta.changes });
  return json({ ok: true, ended: r.meta.changes });
});

/** A reset link the owner can hand over personally (until the mail server runs) -- also queued by email. */
api.post("/admin/users/:id/reset-link", async (ctx) => {
  requireAdmin(ctx);
  const u = await target(ctx);
  mayActOn(ctx, u);
  const r = await sendReset(ctx, u, 24);
  await audit(ctx, "user.reset_link", `user:${u.id}`, { queued: r.queued });
  return json({ link: r.link, queued: r.queued, note: "Works once, for 24 hours. Send it only to the account's owner." });
});

api.delete("/admin/users/:id", async (ctx) => {
  const me = requireOwner(ctx);
  const u = await target(ctx);
  const b = await body(ctx);
  if (normaliseEmail(String(b.confirm || "")) !== u.email) throw new HttpError(400, "Type the account's email address to confirm.");
  if (u.id === me.id || roleFor(ctx.env, u.email) === "admin") throw new HttpError(400, "An admin account cannot be deleted here.");
  await ctx.env.DB.prepare("UPDATE subscribers SET unsubscribed_at = COALESCE(unsubscribed_at, ?), marketing_consent = 0 WHERE email = ?").bind(nowIso(), u.email).run();
  await ctx.env.DB.prepare("DELETE FROM users WHERE id = ?").bind(u.id).run();
  await audit(ctx, "user.delete", `user:${u.id}`, { email: u.email });
  return json({ ok: true });
});

/** The owner promotes a member to manager, or a manager back to member. A manager can open every
 *  admin page and do the day's work -- orders, backers, the list, campaigns, automations,
 *  members, approving agents' proposals -- but cannot make managers, make or revoke agent keys,
 *  delete accounts, or change another manager's or the owner's account. */
api.post("/admin/users/:id/role", async (ctx) => {
  requireOwner(ctx);
  const u = await target(ctx);
  const role = String((await body(ctx)).role || "");
  if (!["manager", "member"].includes(role)) throw new HttpError(400, "role is manager or member.");
  if (roleFor(ctx.env, u.email) === "admin") throw new HttpError(400, "The owner's role comes from ADMIN_EMAILS, not from here.");
  if (u.status === "suspended" && role === "manager") throw new HttpError(400, "Restore the account first.");
  await ctx.env.DB.prepare("UPDATE users SET role = ?, updated_at = ? WHERE id = ?").bind(role, nowIso(), u.id).run();
  await audit(ctx, role === "manager" ? "user.promote_manager" : "user.demote_member", `user:${u.id}`, { email: u.email });
  return json({ ok: true, role });
});
