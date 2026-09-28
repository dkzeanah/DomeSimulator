// Passwords, sessions and the admin check.
//
// Sessions are server-side rows keyed by the SHA-256 of a random token; the
// browser holds the token in an httpOnly, SameSite=Lax cookie. Logging out
// deletes the row, so a stolen cookie stops working the moment its owner
// signs out.

import crypto from 'node:crypto';
import bcrypt from 'bcryptjs';
import { config } from '../config.js';
import { iso, nowIso } from '../db.js';

export const COOKIE = 'sid';
const BCRYPT_COST = 12;

export const hashPassword = (password) => bcrypt.hash(password, BCRYPT_COST);
export const checkPassword = (password, hash) => bcrypt.compare(password, hash);

const sha256 = (text) => crypto.createHash('sha256').update(text).digest('hex');

export function normaliseEmail(email) {
  return String(email || '').trim().toLowerCase();
}

export function roleFor(email) {
  return config.adminEmails.includes(normaliseEmail(email)) ? 'admin' : 'member';
}

function cookieOptions() {
  return {
    httpOnly: true,
    sameSite: 'lax',
    secure: config.production,
    path: '/',
    maxAge: config.sessionDays * 24 * 60 * 60 * 1000,
  };
}

export async function startSession(db, res, userId) {
  const token = crypto.randomBytes(32).toString('base64url');
  await db('sessions').insert({
    token_hash: sha256(token),
    user_id: userId,
    created_at: nowIso(),
    expires_at: nowIso(config.sessionDays * 24 * 60 * 60 * 1000),
  });
  res.cookie(COOKIE, token, cookieOptions());
}

export async function endSession(db, req, res) {
  const token = req.cookies?.[COOKIE];
  if (token) await db('sessions').where({ token_hash: sha256(token) }).delete();
  res.clearCookie(COOKIE, { ...cookieOptions(), maxAge: undefined });
}

/** Public shape of a user. Never includes the password hash. */
export function publicUser(row) {
  if (!row) return null;
  return {
    id: row.id,
    email: row.email,
    displayName: row.display_name,
    role: row.role,
    bio: row.bio || '',
    city: row.city || '',
    region: row.region || '',
    country: row.country || '',
    website: row.website || '',
    createdAt: iso(row.created_at),
  };
}

/** Express middleware: sets req.user when the cookie names a live session. */
export function loadUser(db) {
  return async (req, _res, next) => {
    req.user = null;
    const token = req.cookies?.[COOKIE];
    if (!token) return next();
    try {
      const row = await db('sessions')
        .join('users', 'users.id', 'sessions.user_id')
        .where('sessions.token_hash', sha256(token))
        .andWhere('sessions.expires_at', '>', nowIso())
        .first('users.*');
      if (row) {
        // An address added to ADMIN_EMAILS after sign-up takes effect on the
        // next request, and one removed stops being admin just as quickly.
        const role = roleFor(row.email);
        if (role !== row.role) {
          await db('users').where({ id: row.id }).update({ role });
          row.role = role;
        }
        req.user = row;
      }
      next();
    } catch (error) {
      next(error);
    }
  };
}

export function requireUser(req, res, next) {
  if (!req.user) return res.status(401).json({ error: 'Please sign in first.' });
  next();
}

export function requireAdmin(req, res, next) {
  if (!req.user) return res.status(401).json({ error: 'Please sign in first.' });
  if (req.user.role !== 'admin') return res.status(403).json({ error: 'Admins only.' });
  next();
}

// ----------------------------------------------------------------------
// Download tokens: signed, expiring, no database row needed
// ----------------------------------------------------------------------

function sign(payload) {
  return crypto.createHmac('sha256', config.sessionSecret).update(payload).digest('base64url');
}

export function downloadToken(slug, subscriberId, minutes = config.downloadTokenMinutes) {
  const expires = Date.now() + minutes * 60 * 1000;
  const payload = `${slug}.${subscriberId}.${expires}`;
  return `${Buffer.from(payload).toString('base64url')}.${sign(payload)}`;
}

/** Returns {slug, subscriberId} or null if forged, altered or expired. */
export function readDownloadToken(token) {
  const [encoded, signature] = String(token || '').split('.');
  if (!encoded || !signature) return null;
  const payload = Buffer.from(encoded, 'base64url').toString();
  const expected = sign(payload);
  const a = Buffer.from(signature);
  const b = Buffer.from(expected);
  if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) return null;
  const [slug, subscriberId, expires] = payload.split('.');
  if (!slug || Number(expires) < Date.now()) return null;
  return { slug, subscriberId: Number(subscriberId) };
}
