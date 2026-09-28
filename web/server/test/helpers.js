// A fresh app and database for each test file.
//
// SQLite in memory by default. `npm run test:pg` sets TEST_DATABASE_URL and
// the same tests run against a real Postgres.

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const books = fs.mkdtempSync(path.join(os.tmpdir(), 'domenet-books-'));
// Three editions of one book, to prove the newest is the one served.
fs.writeFileSync(path.join(books, 'test-book.pdf'), '%PDF-1.4 first');
fs.writeFileSync(path.join(books, 'test-book-v2.pdf'), '%PDF-1.4 second');
fs.writeFileSync(path.join(books, 'test-book-v3.pdf'), '%PDF-1.4 third edition');
fs.writeFileSync(path.join(books, 'books.json'), JSON.stringify({
  books: [
    { slug: 'test-book', title: 'Test Book', file: 'test-book.pdf', featured: true },
    { slug: 'missing-book', title: 'Not Printed Yet', file: 'nope.pdf' },
  ],
}));

process.env.DATABASE_URL = process.env.TEST_DATABASE_URL || '';
process.env.SQLITE_PATH = ':memory:';
process.env.BOOKS_DIR = books;
process.env.BOOKS_CONFIG = path.join(books, 'books.json');
process.env.ADMIN_EMAILS = 'boss@example.com';
process.env.SESSION_SECRET = 'test-secret-test-secret-test-secret';
process.env.YOUTUBE_CHANNEL_ID = '';

const { createDb, migrate } = await import('../src/db.js');
const { createApp } = await import('../src/app.js');
const supertest = (await import('supertest')).default;

export async function freshApp() {
  const db = createDb();
  if (process.env.TEST_DATABASE_URL) {
    // Postgres is shared between files: start each one from nothing.
    await db.migrate.rollback(undefined, true);
  }
  await migrate(db);
  const app = createApp(db, { rateLimits: false });
  return { db, app, request: () => supertest.agent(app) };
}

export async function signUp(agent, email, extra = {}) {
  const res = await agent
    .post('/api/auth/signup')
    .send({ email, password: 'correct horse battery', displayName: email.split('@')[0], ...extra });
  if (res.status !== 201) throw new Error(`signup failed: ${res.status} ${JSON.stringify(res.body)}`);
  return res.body.user;
}
