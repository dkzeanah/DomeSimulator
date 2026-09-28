// One Knex instance, pointed at SQLite or Postgres.
//
// The same queries and migrations run on both, which is why nothing in this
// server uses a dialect-only feature: text search is LOWER(...) LIKE, distance
// is computed in JavaScript, and ids are plain auto-increment integers.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import knex from 'knex';
import { config } from './config.js';

const here = path.dirname(fileURLToPath(import.meta.url));
export const MIGRATIONS_DIR = path.join(here, 'migrations');

export function knexConfig({ databaseUrl = config.databaseUrl, sqlitePath = config.sqlitePath } = {}) {
  const migrations = { directory: MIGRATIONS_DIR, loadExtensions: ['.js'] };
  if (databaseUrl) {
    return {
      client: 'pg',
      connection: {
        connectionString: databaseUrl,
        ssl: config.databaseSsl ? { rejectUnauthorized: false } : undefined,
      },
      pool: { min: 0, max: 10 },
      migrations,
    };
  }
  if (sqlitePath !== ':memory:') fs.mkdirSync(path.dirname(sqlitePath), { recursive: true });
  return {
    client: 'better-sqlite3',
    connection: { filename: sqlitePath },
    useNullAsDefault: true,
    migrations,
    pool: {
      // SQLite leaves foreign keys off unless every connection asks.
      afterCreate(conn, done) {
        conn.pragma('foreign_keys = ON');
        conn.pragma('journal_mode = WAL');
        done();
      },
    },
  };
}

export function createDb(options) {
  return knex(knexConfig(options));
}

export async function migrate(db) {
  await db.migrate.latest();
}

export function dialect(db) {
  return db.client.config.client === 'pg' ? 'postgres' : 'sqlite';
}

/**
 * Timestamps come back as Date on Postgres and as text on SQLite, where a
 * column default writes "YYYY-MM-DD HH:MM:SS" (UTC) and this server writes
 * ISO strings. Every timestamp leaves the API as ISO.
 */
export function iso(value) {
  if (value === null || value === undefined || value === '') return null;
  let date;
  if (value instanceof Date) date = value;
  else if (typeof value === 'number') date = new Date(value);
  else {
    const text = String(value);
    date = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(text) ? text : `${text.replace(' ', 'T')}Z`);
  }
  return Number.isNaN(date.getTime()) ? String(value) : date.toISOString();
}

/** What this server writes into a timestamp column: ISO, UTC. */
export function nowIso(offsetMs = 0) {
  return new Date(Date.now() + offsetMs).toISOString();
}
