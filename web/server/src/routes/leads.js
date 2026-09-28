// The email gate in front of the book, and the books themselves.

import fs from 'node:fs';
import { Router } from 'express';
import { z } from 'zod';
import { downloadToken, normaliseEmail, readDownloadToken } from '../lib/auth.js';
import { loadCatalogue, publicBooks, resolveBook } from '../lib/books.js';
import { httpError, parse, route } from '../lib/http.js';
import { config } from '../config.js';
import { nowIso } from '../db.js';

/** Add or refresh a subscriber. Consent only ever moves by the person's own choice. */
export async function upsertSubscriber(db, { email, name = null, consent = false, source = 'book' }) {
  email = normaliseEmail(email);
  const existing = await db('subscribers').where({ email }).first();
  if (existing) {
    const update = {};
    if (name && !existing.name) update.name = name;
    if (consent) {
      update.marketing_consent = true;
      update.unsubscribed_at = null;
    }
    if (Object.keys(update).length) await db('subscribers').where({ id: existing.id }).update(update);
    return existing.id;
  }
  const [row] = await db('subscribers')
    .insert({ email, name, marketing_consent: Boolean(consent), source, created_at: nowIso() })
    .returning('id');
  return typeof row === 'object' ? row.id : row;
}

const leadSchema = z.object({
  email: z.email().max(320),
  name: z.string().trim().max(120).optional(),
  book: z.string().trim().min(1).max(80),
  marketingConsent: z.boolean().optional().default(false),
  // A field real people never see. Bots fill it in.
  website: z.string().max(0, 'leave this empty').optional(),
});

export function bookRoutes(db) {
  const router = Router();

  router.get('/books', (_req, res) => res.json({ books: publicBooks() }));

  router.post('/leads', route(async (req, res) => {
    const body = parse(leadSchema, req.body);
    const book = loadCatalogue().find((b) => b.slug === body.book);
    if (!book || !resolveBook(book)) throw httpError(404, 'That book is not available right now.');
    const subscriberId = await upsertSubscriber(db, {
      email: body.email,
      name: body.name || null,
      consent: body.marketingConsent,
      source: 'book',
    });
    const token = downloadToken(book.slug, subscriberId);
    res.status(201).json({
      downloadUrl: `/api/books/${encodeURIComponent(book.slug)}/download?token=${token}`,
      expiresInHours: Math.round(config.downloadTokenMinutes / 60),
    });
  }));

  router.post('/unsubscribe', route(async (req, res) => {
    const body = parse(z.object({ email: z.email() }), req.body);
    await db('subscribers')
      .where({ email: normaliseEmail(body.email) })
      .update({ marketing_consent: false, unsubscribed_at: nowIso() });
    // The same answer whether or not the address was on the list.
    res.json({ ok: true });
  }));

  router.get('/books/:slug/download', route(async (req, res) => {
    const book = loadCatalogue().find((b) => b.slug === req.params.slug);
    if (!book) throw httpError(404, 'No such book.');
    let subscriberId = null;
    if (!req.user) {
      const token = readDownloadToken(req.query.token);
      if (!token || token.slug !== book.slug) {
        throw httpError(403, 'This download link has expired. Enter your email again for a fresh one.');
      }
      subscriberId = token.subscriberId;
    }
    const file = resolveBook(book);
    if (!file) throw httpError(404, 'That book is not available right now.');
    // A HEAD request (link previews, download managers checking the size)
    // is not somebody reading the book.
    if (req.method === 'GET') {
      await db('downloads').insert({
        subscriber_id: subscriberId,
        user_id: req.user?.id ?? null,
        book_slug: book.slug,
        file_name: file.name,
        created_at: nowIso(),
      });
    }
    const niceName = `${book.slug}${file.version > 1 ? `-edition-${file.version}` : ''}.pdf`;
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Length', file.size);
    res.setHeader('Content-Disposition', `attachment; filename="${niceName}"`);
    res.setHeader('Cache-Control', 'private, no-store');
    if (req.method === 'HEAD') return res.end();
    fs.createReadStream(file.path).pipe(res);
  }));

  return router;
}
