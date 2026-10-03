// The book catalogue, and which file on disk is "the book" right now.
//
// Deliverables in this repository are append-only: a new edition is written
// beside the old one as -v2, -v3 ... (see two_v_demo/deliverables.py). So the
// catalogue names a *base* file, and the download is always its highest
// version -- publish a new PDF and the site serves it with no config change.

import fs from 'node:fs';
import path from 'node:path';
import { config } from '../config.js';

export function loadCatalogue(file = config.booksConfig) {
  if (!fs.existsSync(file)) return [];
  const books = JSON.parse(fs.readFileSync(file, 'utf8')).books || [];
  return books.filter((b) => b.slug && b.file);
}

/** "the-wedge-method.pdf" -> the highest of it, -v2, -v3 ... that exists. */
export function latestVersion(dir, fileName) {
  const ext = path.extname(fileName);
  const base = path.basename(fileName, ext).replace(/-v\d+$/, '');
  if (!fs.existsSync(dir)) return null;
  let best = null;
  let bestVersion = -1;
  const pattern = new RegExp(`^${base.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?:-v(\\d+))?${ext.replace('.', '\\.')}$`);
  for (const name of fs.readdirSync(dir)) {
    const match = name.match(pattern);
    if (!match) continue;
    const version = match[1] ? Number(match[1]) : 1;
    if (version > bestVersion) {
      best = name;
      bestVersion = version;
    }
  }
  return best ? { name: best, version: bestVersion, path: path.join(dir, best) } : null;
}

export function resolveBook(book, dir = config.booksDir) {
  const found = latestVersion(dir, book.file);
  if (!found) return null;
  const { size, mtime } = fs.statSync(found.path);
  return { ...found, size, updatedAt: mtime.toISOString() };
}

/**
 * How a book is offered:
 *   free    -- the PDF, for an email (the sample)
 *   paid    -- sold here; priceCents and currency say for how much
 *   amazon  -- sold on Amazon; amazonUrl once it is live, a waitlist until then
 *   none    -- kept in the catalogue, not shown
 */
export const OFFERS = ['free', 'paid', 'amazon', 'none'];
export const offerOf = (book) => (OFFERS.includes(book.offer) ? book.offer : 'free');

/** The shop is open for a book when it is paid, priced, and printed. */
export function priceOf(book) {
  const cents = Number(book.priceCents);
  if (offerOf(book) !== 'paid' || !Number.isInteger(cents) || cents < 50) return null;
  return { cents, currency: String(book.currency || 'usd').toLowerCase() };
}

/** What the API tells the browser about each book: never a disk path. */
export function publicBooks(dir = config.booksDir, file = config.booksConfig) {
  return loadCatalogue(file)
    .filter((book) => offerOf(book) !== 'none')
    .map((book) => {
      const found = resolveBook(book, dir);
      const offer = offerOf(book);
      const price = priceOf(book);
      return {
        slug: book.slug,
        title: book.title,
        subtitle: book.subtitle || '',
        author: book.author || '',
        blurb: book.blurb || '',
        cover: book.cover || '',
        featured: Boolean(book.featured),
        offer,
        page: book.page || '',
        facts: book.facts || '',
        priceCents: price ? price.cents : null,
        currency: price ? price.currency : null,
        amazonUrl: offer === 'amazon' ? book.amazonUrl || '' : '',
        available: Boolean(found),
        edition: found ? found.version : null,
        sizeMb: found ? Math.round((found.size / 1048576) * 10) / 10 : null,
        updatedAt: found ? found.updatedAt : null,
      };
    });
}
