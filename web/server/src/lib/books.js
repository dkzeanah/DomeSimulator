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

/** What the API tells the browser about each book: never a disk path. */
export function publicBooks(dir = config.booksDir, file = config.booksConfig) {
  return loadCatalogue(file).map((book) => {
    const found = resolveBook(book, dir);
    return {
      slug: book.slug,
      title: book.title,
      subtitle: book.subtitle || '',
      blurb: book.blurb || '',
      cover: book.cover || '',
      featured: Boolean(book.featured),
      available: Boolean(found),
      edition: found ? found.version : null,
      sizeMb: found ? Math.round((found.size / 1048576) * 10) / 10 : null,
      updatedAt: found ? found.updatedAt : null,
    };
  });
}
