// The catalogue and the model's figures, shared by every book page.
//
// Every number a sales page shows comes from /api/facts (written by
// web/export_facts.py from the books' own token resolvers) or /api/books
// (the catalogue and the newest PDF on disk). Nothing here is typed in.

import { useEffect, useState } from 'react';
import { api } from './api.js';

export function useBooks() {
  const [books, setBooks] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => {
    api('/books').then((d) => setBooks(d.books)).catch((e) => setError(e.message));
  }, []);
  return { books, error };
}

export function useFacts() {
  const [facts, setFacts] = useState(null);
  useEffect(() => {
    api('/facts').then((d) => setFacts(d.facts)).catch(() => setFacts({}));
  }, []);
  return facts;
}

/** The book offered a given way: 'free', 'paid' or 'amazon'. */
export const offered = (books, offer) => books?.find((b) => b.offer === offer) || null;

/** 2000, 'usd' -> "$20"; cents shown only when there are any. */
export function price(cents, currency = 'usd') {
  if (cents === null || cents === undefined) return '';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency.toUpperCase(),
    minimumFractionDigits: cents % 100 ? 2 : 0,
  }).format(cents / 100);
}

/** Chapters in a list of parts. */
export const chapterCount = (parts) => (parts || []).reduce((n, p) => n + p.chapters.length, 0);

/** "Title: Subtitle", or "Title — Subtitle" when the subtitle has its own colon. */
export function fullTitle(title, subtitle) {
  if (!subtitle) return title || '';
  return `${title}${subtitle.includes(':') ? ' — ' : ': '}${subtitle}`;
}
