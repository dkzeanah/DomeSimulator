// Everything the server reads from the environment, in one place.
//
// Local use needs no settings at all: SQLite in server/data/, books from the
// repository's deliverables/book folder, a throwaway session secret. Production
// refuses to start without a real SESSION_SECRET.

import crypto from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import dotenv from 'dotenv';

const here = path.dirname(fileURLToPath(import.meta.url));
export const SERVER_ROOT = path.resolve(here, '..');
export const WEB_ROOT = path.resolve(SERVER_ROOT, '..');
export const REPO_ROOT = path.resolve(WEB_ROOT, '..');

dotenv.config({ path: path.join(WEB_ROOT, '.env'), quiet: true });

const env = process.env;
const production = env.NODE_ENV === 'production';

function sessionSecret() {
  if (env.SESSION_SECRET) return env.SESSION_SECRET;
  if (production) {
    throw new Error('SESSION_SECRET must be set in production (see .env.example).');
  }
  // A fresh secret each start: fine locally, and it means a dev server never
  // shares a signing key with anything.
  return crypto.randomBytes(32).toString('hex');
}

export const config = {
  production,
  port: Number(env.PORT || 8787),
  publicUrl: (env.PUBLIC_URL || 'http://localhost:5173').replace(/\/$/, ''),
  databaseUrl: env.DATABASE_URL || '',
  databaseSsl: env.DATABASE_SSL === 'true',
  sqlitePath: env.SQLITE_PATH || path.join(SERVER_ROOT, 'data', 'domenet.sqlite3'),
  sessionSecret: sessionSecret(),
  sessionDays: 30,
  adminEmails: (env.ADMIN_EMAILS || '')
    .split(',')
    .map((e) => e.trim().toLowerCase())
    .filter(Boolean),
  booksDir: env.BOOKS_DIR || path.join(REPO_ROOT, 'deliverables', 'book'),
  booksConfig: env.BOOKS_CONFIG || path.join(WEB_ROOT, 'books.config.json'),
  siteConfig: path.join(WEB_ROOT, 'site.config.json'),
  youtubeChannelId: env.YOUTUBE_CHANNEL_ID || '',
  clientDist: path.join(WEB_ROOT, 'client', 'dist'),
  // How long a download link from the email gate stays valid.
  downloadTokenMinutes: 60 * 24,
  // Selling the book. With no Stripe key the shop is closed in production,
  // and locally it runs a test checkout where no card is asked for and no
  // money moves -- so the whole path can be tried before Stripe is set up.
  stripeSecretKey: env.STRIPE_SECRET_KEY || '',
  stripeWebhookSecret: env.STRIPE_WEBHOOK_SECRET || '',
  testCheckout: !production && !env.STRIPE_SECRET_KEY,
};
