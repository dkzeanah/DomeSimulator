// What the site owner sees: who signed up, who downloaded what.

import { Router } from 'express';
import { requireAdmin } from '../lib/auth.js';
import { route } from '../lib/http.js';
import { iso } from '../db.js';

const csvCell = (value) => {
  const text = value === null || value === undefined ? '' : String(value);
  // A leading = + - @ makes a spreadsheet run the cell as a formula.
  const safe = /^[=+\-@\t\r]/.test(text) ? `'${text}` : text;
  return /[",\n]/.test(safe) ? `"${safe.replace(/"/g, '""')}"` : safe;
};

export function adminRoutes(db) {
  const router = Router();
  router.use(requireAdmin);

  router.get('/stats', route(async (_req, res) => {
    const count = async (table, where) => {
      let q = db(table);
      if (where) q = q.where(where);
      const [{ n }] = await q.count({ n: '*' });
      return Number(n);
    };
    const byBook = await db('downloads').select('book_slug').count({ n: '*' }).groupBy('book_slug');
    res.json({
      subscribers: await count('subscribers'),
      consenting: await count('subscribers', { marketing_consent: true }),
      users: await count('users'),
      listings: await count('listings'),
      downloads: await count('downloads'),
      downloadsByBook: byBook.map((r) => ({ slug: r.book_slug, count: Number(r.n) })),
      signups: (await db('signups').select('kind', 'book_slug').count({ n: '*' }).groupBy('kind', 'book_slug'))
        .map((r) => ({ kind: r.kind, slug: r.book_slug, count: Number(r.n) })),
      sales: (await db('orders').where({ status: 'paid' }).select('book_slug', 'currency', 'provider')
        .count({ n: '*' }).sum({ cents: 'amount_cents' }).groupBy('book_slug', 'currency', 'provider'))
        .map((r) => ({ slug: r.book_slug, currency: r.currency, test: r.provider === 'test', count: Number(r.n), cents: Number(r.cents) })),
    });
  }));

  router.get('/orders', route(async (req, res) => {
    const limit = Math.min(500, Number(req.query.limit) || 100);
    const rows = await db('orders').orderBy('id', 'desc').limit(limit);
    res.json({
      orders: rows.map((o) => ({
        ref: o.ref,
        book: o.book_slug,
        status: o.status,
        email: o.email || '',
        amountCents: o.amount_cents,
        currency: o.currency,
        test: o.provider === 'test',
        createdAt: iso(o.created_at),
        paidAt: iso(o.paid_at),
      })),
    });
  }));

  // Everyone who asked for one thing -- the Amazon waitlist, say. Asking to
  // be told when the book is out is consent to *that* email, so this list is
  // everyone who asked, whether or not they ticked the general updates box.
  router.get('/signups.csv', route(async (req, res) => {
    const kind = String(req.query.kind || 'waitlist');
    let q = db('signups')
      .join('subscribers', 'subscribers.id', 'signups.subscriber_id')
      .where('signups.kind', kind)
      .whereNull('subscribers.unsubscribed_at')
      .select('subscribers.email', 'subscribers.name', 'signups.book_slug', 'signups.created_at')
      .orderBy('signups.id');
    if (req.query.book) q = q.where('signups.book_slug', String(req.query.book));
    const rows = await q;
    const lines = ['email,name,book,asked_on'];
    for (const r of rows) lines.push([r.email, r.name, r.book_slug, iso(r.created_at)].map(csvCell).join(','));
    res.setHeader('Content-Type', 'text/csv; charset=utf-8');
    res.setHeader('Content-Disposition', `attachment; filename="${kind.replace(/[^a-z]/g, '')}.csv"`);
    res.send(`${lines.join('\n')}\n`);
  }));

  router.get('/subscribers', route(async (req, res) => {
    const limit = Math.min(500, Number(req.query.limit) || 100);
    const offset = Math.max(0, Number(req.query.offset) || 0);
    const rows = await db('subscribers').orderBy('id', 'desc').limit(limit).offset(offset);
    res.json({
      subscribers: rows.map((r) => ({
        id: r.id,
        email: r.email,
        name: r.name || '',
        marketingConsent: Boolean(r.marketing_consent),
        source: r.source || '',
        createdAt: iso(r.created_at),
        unsubscribedAt: iso(r.unsubscribed_at),
      })),
    });
  }));

  // Only people who ticked the box, and have not since unsubscribed: this is
  // the file that goes to a mailing tool, so it must not contain anyone else.
  router.get('/subscribers.csv', route(async (_req, res) => {
    const rows = await db('subscribers').where({ marketing_consent: true }).whereNull('unsubscribed_at').orderBy('id');
    const lines = ['email,name,source,signed_up'];
    for (const r of rows) lines.push([r.email, r.name, r.source, iso(r.created_at)].map(csvCell).join(','));
    res.setHeader('Content-Type', 'text/csv; charset=utf-8');
    res.setHeader('Content-Disposition', 'attachment; filename="subscribers-consenting.csv"');
    res.send(`${lines.join('\n')}\n`);
  }));

  return router;
}
