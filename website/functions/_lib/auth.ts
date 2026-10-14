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

export async function startSession(ctx: Ctx, userId: number) {
  const token = randomToken();
  await ctx.env.DB.prepare("INSERT INTO sessions(token_hash, user_id, created_at, expires_at) VALUES(?, ?, ?, ?)")
    .bind(await sha256Hex(token), userId, nowIso(), nowIso(SESSION_DAYS * 86_400_000)).run();
  ctx.setCookies.push(cookie(ctx, token, SESSION_DAYS * 86_400));
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
  const row = await ctx.env.DB.prepare(
    "SELECT users.* FROM sessions JOIN users ON users.id = sessions.user_id WHERE sessions.token_hash = ? AND sessions.expires_at > ?",
  ).bind(await sha256Hex(token), nowIso()).first<User>();
  if (!row) return null;
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
    publicProfile: Boolean(u.public_profile), createdAt: u.created_at,
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
