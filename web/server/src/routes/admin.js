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
    });
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
