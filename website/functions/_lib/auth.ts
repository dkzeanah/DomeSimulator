// Sessions, the admin check, and signed download links. Ported from web/server/src/lib/
// auth.js: a session cookie holds a random token, the database keeps only its SHA-256, and
// signing out deletes the row -- so a stolen cookie dies the moment its owner signs out.

import { hmac, randomToken, sameString, sha256Hex } from "./crypto";
import { Ctx, Env, HttpError, User, nowIso } from "./http";

export const COOKIE = "zl_sid";
const SESSION_DAYS = 30;

export function normaliseEmail(e: string) {
  return String(e || "").trim().toLowerCase();
}

export function roleFor(env: Env, email: string): "admin" | "member" {
  const admins = String(env.ADMIN_EMAILS || "").split(",").map(normaliseEmail).filter(Boolean);
  return admins.includes(normaliseEmail(email)) ? "admin" : "member";
}

function cookie(ctx: Ctx, value: string, maxAgeSec: number) {
  const secure = ctx.url.protocol === "https:" ? "; Secure" : "";
  return `${COOKIE}=${value}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${maxAgeSec}${secure}`;
}

function readCookie(request: Request, name: string): string | null {
  const raw = request.headers.get("Cookie") || "";
  for (const part of raw.split(";")) {
    const [k, ...v] = part.trim().split("=");
    if (k === name) return v.join("=");
  }
  return null;
}

/** "Chrome on Windows" -- enough for a member to tell their own devices apart, no more. */
export function deviceName(ua: string | null) {
  const u = ua || "";
  const browser = /Edg\//.test(u) ? "Edge" : /Firefox\//.test(u) ? "Firefox" : /Chrome\//.test(u) ? "Chrome" : /Safari\//.test(u) ? "Safari" : "A browser";
  const os = /iPhone|iPad/.test(u) ? "iPhone/iPad" : /Android/.test(u) ? "Android" : /Windows/.test(u) ? "Windows" : /Mac OS X/.test(u) ? "Mac" : /Linux/.test(u) ? "Linux" : "an unknown system";
  return `${browser} on ${os}`;
}

export async function startSession(ctx: Ctx, userId: number) {
  const token = randomToken();
  const country = (ctx.request as Request & { cf?: { country?: string } }).cf?.country ?? null;
  await ctx.env.DB.prepare("INSERT INTO sessions(token_hash, user_id, created_at, expires_at, last_seen_at, user_agent, country) VALUES(?, ?, ?, ?, ?, ?, ?)")
    .bind(await sha256Hex(token), userId, nowIso(), nowIso(SESSION_DAYS * 86_400_000), nowIso(), deviceName(ctx.request.headers.get("User-Agent")), country).run();
  await ctx.env.DB.prepare("UPDATE users SET last_seen_at = ? WHERE id = ?").bind(nowIso(), userId).run();
  ctx.setCookies.push(cookie(ctx, token, SESSION_DAYS * 86_400));
}

/** The hash of this request's session token, which names the session in lists. */
export async function currentSessionHash(ctx: Ctx) {
  const token = readCookie(ctx.request, COOKIE);
  return token ? sha256Hex(token) : null;
}

// ---------------------------------------------------------------- the brake on guessing

const WINDOW_MS = 15 * 60_000;

async function ipHash(ctx: Ctx) {
  const ip = ctx.request.headers.get("CF-Connecting-IP");
  return ip ? (await sha256Hex(`${ctx.env.SESSION_SECRET || ""}|${ip}`)).slice(0, 32) : null;
}

/** Eight misses for one address, or thirty from one network, in fifteen minutes: wait. */
export async function loginGate(ctx: Ctx, email: string) {
  const since = nowIso(-WINDOW_MS);
  const ip = await ipHash(ctx);
  const byEmail = (await ctx.env.DB.prepare("SELECT COUNT(*) n FROM login_attempts WHERE email = ? AND ok = 0 AND ts >= ?").bind(email, since).first<{ n: number }>())!.n;
  const byIp = ip ? (await ctx.env.DB.prepare("SELECT COUNT(*) n FROM login_attempts WHERE ip_hash = ? AND ok = 0 AND ts >= ?").bind(ip, since).first<{ n: number }>())!.n : 0;
  if (byEmail >= 8 || byIp >= 30) throw new HttpError(429, "Too many tries. Wait fifteen minutes, or reset your password.");
}

export async function recordLogin(ctx: Ctx, email: string, ok: boolean) {
  await ctx.env.DB.prepare("INSERT INTO login_attempts(email, ip_hash, ok, ts) VALUES(?, ?, ?, ?)").bind(email, await ipHash(ctx), ok ? 1 : 0, nowIso()).run();
}

export async function endSession(ctx: Ctx) {
  const token = readCookie(ctx.request, COOKIE);
  if (token) await ctx.env.DB.prepare("DELETE FROM sessions WHERE token_hash = ?").bind(await sha256Hex(token)).run();
  ctx.setCookies.push(cookie(ctx, "", 0));
}

/** The signed-in user, if the cookie names a live session. Keeps role in step with ADMIN_EMAILS. */
export async function loadUser(ctx: Ctx): Promise<User | null> {
  const token = readCookie(ctx.request, COOKIE);
  if (!token) return null;
  const hash = await sha256Hex(token);
  const row = await ctx.env.DB.prepare(
    "SELECT users.*, sessions.last_seen_at session_seen FROM sessions JOIN users ON users.id = sessions.user_id WHERE sessions.token_hash = ? AND sessions.expires_at > ?",
  ).bind(hash, nowIso()).first<User & { session_seen: string | null }>();
  if (!row || row.status === "suspended") return null;
  // last seen, written at most every ten minutes rather than on every request
  if (!row.session_seen || Date.parse(row.session_seen) < Date.now() - 10 * 60_000) {
    await ctx.env.DB.batch([
      ctx.env.DB.prepare("UPDATE sessions SET last_seen_at = ? WHERE token_hash = ?").bind(nowIso(), hash),
      ctx.env.DB.prepare("UPDATE users SET last_seen_at = ? WHERE id = ?").bind(nowIso(), row.id),
    ]);
  }
  const role = roleFor(ctx.env, row.email);
  if (role !== row.role) {
    await ctx.env.DB.prepare("UPDATE users SET role = ? WHERE id = ?").bind(role, row.id).run();
    row.role = role;
  }
  return row;
}

export function requireUser(ctx: Ctx): User {
  if (!ctx.user) throw new HttpError(401, "Please sign in first.");
  return ctx.user;
}

export function requireAdmin(ctx: Ctx): User {
  const u = requireUser(ctx);
  if (u.role !== "admin") throw new HttpError(403, "Admins only.");
  return u;
}

/** Public shape of a user. Never the password hash. */
export function publicUser(u: User | null) {
  if (!u) return null;
  return {
    id: u.id, email: u.email, displayName: u.display_name, role: u.role,
    bio: u.bio || "", city: u.city || "", region: u.region || "", country: u.country || "",
    publicProfile: Boolean(u.public_profile), createdAt: u.created_at, emailVerified: Boolean(u.email_verified_at),
  };
}

// ---------------------------------------------------------------- download links
// Signed and expiring, so the email gate needs no database row per link.

function secret(env: Env): string {
  if (!env.SESSION_SECRET || env.SESSION_SECRET.length < 32) {
    throw new HttpError(500, "The site is not configured yet (SESSION_SECRET is missing).");
  }
  return env.SESSION_SECRET;
}

export async function downloadToken(env: Env, slug: string, subscriberId: number, hours = 72): Promise<string> {
  const payload = `${slug}.${subscriberId}.${Date.now() + hours * 3_600_000}`;
  return `${btoa(payload).replace(/=+$/, "")}.${await hmac(secret(env), payload)}`;
}

export async function readDownloadToken(env: Env, token: string | null): Promise<{ slug: string; subscriberId: number } | null> {
  const [encoded, signature] = String(token || "").split(".");
  if (!encoded || !signature) return null;
  let payload: string;
  try {
    payload = atob(encoded);
  } catch {
    return null;
  }
  if (!sameString(signature, await hmac(secret(env), payload))) return null;
  const [slug, subscriberId, expires] = payload.split(".");
  if (!slug || Number(expires) < Date.now()) return null;
  return { slug, subscriberId: Number(subscriberId) };
}
