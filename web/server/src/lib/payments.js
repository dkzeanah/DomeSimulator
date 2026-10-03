// Stripe Checkout, spoken to directly over its HTTP API.
//
// Three calls are all the shop needs -- create a checkout session, read one
// back, check a webhook's signature -- so there is no SDK: fewer moving parts,
// and the card never touches this server (Stripe's own page takes it).

import crypto from 'node:crypto';
import { config } from '../config.js';

const API = 'https://api.stripe.com/v1';

/** Stripe's form encoding: nested keys as a[b][c]=v. */
export function formEncode(value, prefix = '', out = new URLSearchParams()) {
  if (value === undefined || value === null) return out;
  if (typeof value === 'object') {
    for (const [key, inner] of Object.entries(value)) {
      formEncode(inner, prefix ? `${prefix}[${key}]` : key, out);
    }
  } else {
    out.append(prefix, String(value));
  }
  return out;
}

async function stripe(method, path, body, { secretKey = config.stripeSecretKey, fetchImpl = fetch } = {}) {
  const response = await fetchImpl(`${API}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${secretKey}`,
      ...(body ? { 'Content-Type': 'application/x-www-form-urlencoded' } : {}),
    },
    body: body ? formEncode(body).toString() : undefined,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(`Stripe said: ${data.error?.message || response.status}`);
    error.status = 502;
    throw error;
  }
  return data;
}

export function createCheckoutSession({ order, book, successUrl, cancelUrl, email }, options) {
  return stripe('POST', '/checkout/sessions', {
    mode: 'payment',
    line_items: {
      0: {
        quantity: 1,
        price_data: {
          currency: order.currency,
          unit_amount: order.amount_cents,
          product_data: {
            name: book.subtitle ? `${book.title}${book.subtitle.includes(':') ? ' — ' : ': '}${book.subtitle}` : book.title,
            description: 'Digital edition (PDF). Every future edition included.',
          },
        },
      },
    },
    customer_email: email || undefined,
    client_reference_id: order.ref,
    metadata: { ref: order.ref, book: book.slug },
    success_url: successUrl,
    cancel_url: cancelUrl,
  }, options);
}

export function retrieveCheckoutSession(id, options) {
  return stripe('GET', `/checkout/sessions/${encodeURIComponent(id)}`, undefined, options);
}

/**
 * Check a webhook's Stripe-Signature header: "t=<unix>,v1=<hex>[,v1=...]",
 * where v1 = HMAC-SHA256(secret, "<t>.<raw body>"). A timestamp more than
 * five minutes off is refused, so an old message cannot be replayed.
 */
export function verifyStripeSignature(rawBody, header, secret, { toleranceSec = 300, nowSec = Date.now() / 1000 } = {}) {
  if (!header || !secret) return false;
  const parts = String(header).split(',').map((p) => p.split('='));
  const t = parts.find(([k]) => k === 't')?.[1];
  const signatures = parts.filter(([k]) => k === 'v1').map(([, v]) => v);
  if (!t || !signatures.length || Math.abs(nowSec - Number(t)) > toleranceSec) return false;
  const expected = crypto.createHmac('sha256', secret).update(`${t}.${rawBody}`).digest('hex');
  const b = Buffer.from(expected);
  return signatures.some((sig) => {
    const a = Buffer.from(sig);
    return a.length === b.length && crypto.timingSafeEqual(a, b);
  });
}

/** For tests: a header Stripe would send for this body. */
export function signStripePayload(rawBody, secret, t = Math.floor(Date.now() / 1000)) {
  const v1 = crypto.createHmac('sha256', secret).update(`${t}.${rawBody}`).digest('hex');
  return `t=${t},v1=${v1}`;
}
