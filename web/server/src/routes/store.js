// The shop: buying the digital book, and the Amazon waitlist.
//
// An order is made before the buyer leaves for Stripe, with a public `ref`
// and a secret key. The key comes back in the buyer's own return link and is
// stored here only as a hash, so that link is the receipt *and* the way back
// to the download -- from any device, account or not. Payment is confirmed
// two ways, whichever arrives first: Stripe's signed webhook, or the return
// page asking Stripe directly. Both end in markPaid(), which is idempotent.

import crypto from 'node:crypto';
import { Router } from 'express';
import { z } from 'zod';
import { config } from '../config.js';
import { iso, nowIso } from '../db.js';
import { normaliseEmail, requireUser } from '../lib/auth.js';
import { loadCatalogue, offerOf, priceOf, resolveBook } from '../lib/books.js';
import { httpError, parse, route } from '../lib/http.js';
import { createCheckoutSession, retrieveCheckoutSession, verifyStripeSignature } from '../lib/payments.js';
import { recordSignup, sendPdf, upsertSubscriber } from './leads.js';

const sha256 = (text) => crypto.createHash('sha256').update(String(text)).digest('hex');

function sameHash(key, hash) {
  if (!key || !hash) return false;
  const a = Buffer.from(sha256(key));
  const b = Buffer.from(hash);
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

/** Which way the shop takes money right now, or null if it is closed. */
export function checkoutMode() {
  if (config.stripeSecretKey) return 'stripe';
  if (config.testCheckout) return 'test';
  return null;
}

/** Mark an order paid, once. Later calls are no-ops. */
export async function markPaid(db, order, { email } = {}) {
  if (order.status === 'paid') return order;
  const buyer = normaliseEmail(email || order.email);
  const subscriberId = buyer
    ? await upsertSubscriber(db, { email: buyer, consent: Boolean(order.marketing_consent), source: order.book_slug })
    : null;
  const changed = await db('orders')
    .where({ id: order.id, status: 'pending' })
    .update({ status: 'paid', paid_at: nowIso(), email: buyer || order.email, subscriber_id: subscriberId });
  // Two confirmations racing: only the one that flipped the row records it.
  if (changed && subscriberId) await recordSignup(db, subscriberId, 'purchase', order.book_slug);
  return db('orders').where({ id: order.id }).first();
}

function publicOrder(order, book, key) {
  const paid = order.status === 'paid';
  const query = key ? `?key=${encodeURIComponent(key)}` : '';
  return {
    ref: order.ref,
    status: order.status,
    amountCents: order.amount_cents,
    currency: order.currency,
    email: order.email || '',
    createdAt: iso(order.created_at),
    paidAt: iso(order.paid_at),
    book: book
      ? { slug: book.slug, title: book.title, subtitle: book.subtitle || '', cover: book.cover || '' }
      : { slug: order.book_slug, title: order.book_slug, subtitle: '', cover: '' },
    downloadUrl: paid ? `/api/orders/${order.ref}/download${query}` : null,
    test: order.provider === 'test',
  };
}

const checkoutSchema = z.object({
  book: z.string().trim().min(1).max(80),
  email: z.email().max(320),
  marketingConsent: z.boolean().optional().default(false),
  website: z.string().max(0, 'leave this empty').optional(),
});

const waitlistSchema = z.object({
  book: z.string().trim().min(1).max(80),
  email: z.email().max(320),
  name: z.string().trim().max(120).optional(),
  marketingConsent: z.boolean().optional().default(false),
  website: z.string().max(0, 'leave this empty').optional(),
});

export function storeRoutes(db) {
  const router = Router();
  const findBook = (slug) => loadCatalogue().find((b) => b.slug === slug);

  /** May this request see the order? Its key, or the account that bought it. */
  async function loadOrder(req) {
    const order = await db('orders').where({ ref: String(req.params.ref) }).first();
    const key = String(req.query.key || req.body?.key || '');
    const owner = req.user && order?.user_id === req.user.id;
    if (!order || (!owner && !sameHash(key, order.key_hash))) {
      throw httpError(404, 'No order matches that link. Check you copied all of it.');
    }
    return { order, key: owner && !key ? '' : key };
  }

  router.get('/shop', (_req, res) => res.json({ mode: checkoutMode() }));

  router.post('/checkout', route(async (req, res) => {
    const body = parse(checkoutSchema, req.body);
    const book = findBook(body.book);
    const price = book && priceOf(book);
    if (!price || !resolveBook(book)) throw httpError(404, 'That book is not for sale right now.');
    const mode = checkoutMode();
    if (!mode) throw httpError(503, 'The shop opens soon. Leave your email on the sample page and you will hear first.');

    const ref = crypto.randomBytes(9).toString('base64url');
    const key = crypto.randomBytes(24).toString('base64url');
    const email = normaliseEmail(body.email);
    const [row] = await db('orders')
      .insert({
        ref,
        key_hash: sha256(key),
        book_slug: book.slug,
        amount_cents: price.cents,
        currency: price.currency,
        email,
        user_id: req.user?.id ?? null,
        provider: mode,
        marketing_consent: body.marketingConsent,
        created_at: nowIso(),
      })
      .returning('id');
    const id = typeof row === 'object' ? row.id : row;
    const order = await db('orders').where({ id }).first();
    const thanks = `/thanks/${ref}?key=${encodeURIComponent(key)}`;

    if (mode === 'test') {
      return res.status(201).json({ url: `/checkout/test/${ref}?key=${encodeURIComponent(key)}`, test: true });
    }
    const session = await createCheckoutSession({
      order,
      book,
      email,
      successUrl: `${config.publicUrl}${thanks}`,
      cancelUrl: `${config.publicUrl}/${book.page || 'book'}?cancelled=1`,
    });
    await db('orders').where({ id }).update({ provider_session: session.id });
    res.status(201).json({ url: session.url, test: false });
  }));

  router.get('/orders/mine', requireUser, route(async (req, res) => {
    const rows = await db('orders').where({ user_id: req.user.id, status: 'paid' }).orderBy('id', 'desc');
    res.json({ orders: rows.map((o) => publicOrder(o, findBook(o.book_slug), '')) });
  }));

  router.get('/orders/:ref', route(async (req, res) => {
    let { order, key } = await loadOrder(req);
    // Back from Stripe before its webhook landed: ask Stripe directly.
    if (order.status === 'pending' && order.provider === 'stripe' && order.provider_session && config.stripeSecretKey) {
      const session = await retrieveCheckoutSession(order.provider_session).catch(() => null);
      if (session?.payment_status === 'paid') {
        order = await markPaid(db, order, { email: session.customer_details?.email });
      }
    }
    res.json({ order: publicOrder(order, findBook(order.book_slug), key) });
  }));

  // The local stand-in for Stripe's page. It cannot run in production, and it
  // only ever pays an order that was made as a test.
  router.post('/orders/:ref/test-pay', route(async (req, res) => {
    if (!config.testCheckout) throw httpError(404, 'Not found.');
    const { order, key } = await loadOrder(req);
    if (order.provider !== 'test') throw httpError(400, 'Only a test order can be paid here.');
    const paid = await markPaid(db, order);
    res.json({ order: publicOrder(paid, findBook(paid.book_slug), key) });
  }));

  router.get('/orders/:ref/download', route(async (req, res) => {
    const { order } = await loadOrder(req);
    if (order.status !== 'paid') throw httpError(402, 'This order has not been paid yet.');
    const book = findBook(order.book_slug);
    const file = book && resolveBook(book);
    if (!file) throw httpError(404, 'The book file is missing. Please get in touch and it will be sent to you.');
    if (req.method === 'GET') {
      await db('downloads').insert({
        subscriber_id: order.subscriber_id,
        user_id: req.user?.id ?? null,
        book_slug: book.slug,
        file_name: file.name,
        created_at: nowIso(),
      });
    }
    sendPdf(req, res, book, file);
  }));

  router.post('/waitlist', route(async (req, res) => {
    const body = parse(waitlistSchema, req.body);
    const book = findBook(body.book);
    if (!book || offerOf(book) !== 'amazon') throw httpError(404, 'No waitlist for that book.');
    const subscriberId = await upsertSubscriber(db, {
      email: body.email,
      name: body.name || null,
      consent: body.marketingConsent,
      source: book.slug,
    });
    const already = await db('signups').where({ subscriber_id: subscriberId, kind: 'waitlist', book_slug: book.slug }).first();
    if (!already) await recordSignup(db, subscriberId, 'waitlist', book.slug);
    res.status(201).json({ ok: true });
  }));

  return router;
}

/**
 * Stripe's webhook. Mounted ahead of the JSON parser because the signature is
 * over the raw bytes; a re-serialised body would never match.
 */
export function stripeWebhook(db) {
  return route(async (req, res) => {
    const raw = Buffer.isBuffer(req.body) ? req.body.toString('utf8') : '';
    if (!verifyStripeSignature(raw, req.headers['stripe-signature'], config.stripeWebhookSecret)) {
      throw httpError(400, 'Bad signature.');
    }
    const event = JSON.parse(raw);
    if (event.type === 'checkout.session.completed' || event.type === 'checkout.session.async_payment_succeeded') {
      const session = event.data?.object || {};
      const ref = session.metadata?.ref || session.client_reference_id;
      const order = ref && (await db('orders').where({ ref }).first());
      if (order && session.payment_status === 'paid') {
        await markPaid(db, order, { email: session.customer_details?.email });
      }
    }
    // Anything else is acknowledged and ignored, so Stripe stops retrying it.
    res.json({ received: true });
  });
}
