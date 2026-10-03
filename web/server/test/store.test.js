import assert from 'node:assert/strict';
import { after, before, describe, test } from 'node:test';
import { freshApp, signUp } from './helpers.js';

const { config } = await import('../src/config.js');
const { signStripePayload, verifyStripeSignature, formEncode } = await import('../src/lib/payments.js');

let ctx;
before(async () => {
  ctx = await freshApp();
});
after(async () => {
  await ctx.db.destroy();
});

const binary = (res, cb) => {
  const chunks = [];
  res.on('data', (c) => chunks.push(c));
  res.on('end', () => cb(null, Buffer.concat(chunks)));
};

/** Start a test checkout and return {ref, key}. */
async function checkout(agent, email = 'buyer@example.com', extra = {}) {
  const res = await agent.post('/api/checkout').send({ book: 'paid-book', email, ...extra });
  assert.equal(res.status, 201, JSON.stringify(res.body));
  assert.equal(res.body.test, true);
  const url = new URL(res.body.url, 'http://x');
  return { ref: url.pathname.split('/').pop(), key: url.searchParams.get('key') };
}

describe('the catalogue as a shop', () => {
  test('offers and prices come from the config; hidden books are not listed', async () => {
    const { body } = await ctx.request().get('/api/books');
    const paid = body.books.find((b) => b.slug === 'paid-book');
    assert.equal(paid.offer, 'paid');
    assert.equal(paid.priceCents, 2000);
    assert.equal(paid.currency, 'usd');
    assert.equal(body.books.find((b) => b.slug === 'kdp-book').offer, 'amazon');
    assert.equal(body.books.find((b) => b.slug === 'test-book').offer, 'free');
    assert.equal(body.books.some((b) => b.slug === 'hidden-book'), false);
  });

  test('a sold book cannot be had for an email, or through the free download route', async () => {
    const lead = await ctx.request().post('/api/leads').send({ email: 'free@example.com', book: 'paid-book' });
    assert.equal(lead.status, 404);
    const member = ctx.request();
    await signUp(member, 'member-paid@example.com');
    assert.equal((await member.get('/api/books/paid-book/download')).status, 403);
    assert.equal((await member.get('/api/books/kdp-book/download')).status, 403);
  });

  test('only a paid book can be checked out', async () => {
    for (const book of ['test-book', 'kdp-book', 'hidden-book', 'nope']) {
      const res = await ctx.request().post('/api/checkout').send({ book, email: 'a@example.com' });
      assert.equal(res.status, 404, book);
    }
  });
});

describe('buying the book (test checkout)', () => {
  test('pending until paid; paid serves the PDF; the key is the receipt', async () => {
    const agent = ctx.request();
    const { ref, key } = await checkout(agent, 'Buyer@Example.com', { marketingConsent: true });

    const pending = await agent.get(`/api/orders/${ref}`).query({ key });
    assert.equal(pending.body.order.status, 'pending');
    assert.equal(pending.body.order.downloadUrl, null);
    assert.equal(pending.body.order.amountCents, 2000, 'the price is the server\'s, not the browser\'s');
    assert.equal((await agent.get(`/api/orders/${ref}/download`).query({ key })).status, 402);

    const paid = await agent.post(`/api/orders/${ref}/test-pay`).send({ key });
    assert.equal(paid.body.order.status, 'paid');
    const pdf = await ctx.request().get(paid.body.order.downloadUrl).buffer(true).parse(binary);
    assert.equal(pdf.status, 200);
    assert.equal(pdf.body.toString(), '%PDF-1.4 the paid one');

    const sub = await ctx.db('subscribers').where({ email: 'buyer@example.com' }).first();
    assert.equal(Boolean(sub.marketing_consent), true);
    const signups = await ctx.db('signups').where({ subscriber_id: sub.id, kind: 'purchase' });
    assert.equal(signups.length, 1);
  });

  test('paying twice records one purchase', async () => {
    const agent = ctx.request();
    const { ref, key } = await checkout(agent, 'twice-buyer@example.com');
    await agent.post(`/api/orders/${ref}/test-pay`).send({ key });
    await agent.post(`/api/orders/${ref}/test-pay`).send({ key });
    const sub = await ctx.db('subscribers').where({ email: 'twice-buyer@example.com' }).first();
    assert.equal((await ctx.db('signups').where({ subscriber_id: sub.id, kind: 'purchase' })).length, 1);
  });

  test('a wrong key sees nothing, and cannot pay or download', async () => {
    const agent = ctx.request();
    const { ref, key } = await checkout(agent, 'guarded@example.com');
    const wrong = key.replace(/.$/, (c) => (c === 'A' ? 'B' : 'A'));
    assert.equal((await ctx.request().get(`/api/orders/${ref}`).query({ key: wrong })).status, 404);
    assert.equal((await ctx.request().get(`/api/orders/${ref}`)).status, 404);
    assert.equal((await ctx.request().post(`/api/orders/${ref}/test-pay`).send({ key: wrong })).status, 404);
    await agent.post(`/api/orders/${ref}/test-pay`).send({ key });
    assert.equal((await ctx.request().get(`/api/orders/${ref}/download`).query({ key: wrong })).status, 404);
  });

  test('a signed-in buyer finds the book in their account without the key', async () => {
    const agent = ctx.request();
    await signUp(agent, 'account-buyer@example.com');
    const { ref, key } = await checkout(agent, 'account-buyer@example.com');
    await agent.post(`/api/orders/${ref}/test-pay`).send({ key });
    const mine = await agent.get('/api/orders/mine');
    assert.equal(mine.body.orders.length, 1);
    const dl = await agent.get(mine.body.orders[0].downloadUrl);
    assert.equal(dl.status, 200);
    const stranger = ctx.request();
    await signUp(stranger, 'stranger@example.com');
    assert.equal((await stranger.get(mine.body.orders[0].downloadUrl)).status, 404);
  });

  test('the test checkout closes the moment a Stripe key is set', async () => {
    const agent = ctx.request();
    const { ref, key } = await checkout(agent, 'closing@example.com');
    config.testCheckout = false;
    try {
      assert.equal((await agent.post(`/api/orders/${ref}/test-pay`).send({ key })).status, 404);
      const shop = await agent.get('/api/shop');
      assert.equal(shop.body.mode, null);
      const closed = await agent.post('/api/checkout').send({ book: 'paid-book', email: 'late@example.com' });
      assert.equal(closed.status, 503);
    } finally {
      config.testCheckout = true;
    }
  });
});

describe('the Stripe webhook', () => {
  const secret = 'whsec_test_only';

  test('the signature check matches Stripe\'s scheme and refuses replays', () => {
    const body = '{"a":1}';
    const header = signStripePayload(body, secret, 1_000_000);
    assert.equal(verifyStripeSignature(body, header, secret, { nowSec: 1_000_100 }), true);
    assert.equal(verifyStripeSignature(body, header, secret, { nowSec: 1_000_400 }), false, 'too old');
    assert.equal(verifyStripeSignature('{"a":2}', header, secret, { nowSec: 1_000_100 }), false, 'altered');
    assert.equal(verifyStripeSignature(body, header, 'whsec_other', { nowSec: 1_000_100 }), false, 'wrong secret');
  });

  test('Stripe\'s form encoding nests keys the way its API reads them', () => {
    const form = formEncode({ line_items: { 0: { price_data: { unit_amount: 2000 } } }, mode: 'payment' }).toString();
    assert.equal(decodeURIComponent(form), 'line_items[0][price_data][unit_amount]=2000&mode=payment');
  });

  test('a signed checkout.session.completed marks the order paid; an unsigned one is refused', async () => {
    const agent = ctx.request();
    const { ref, key } = await checkout(agent, 'hook@example.com');
    const event = JSON.stringify({
      type: 'checkout.session.completed',
      data: { object: { metadata: { ref }, payment_status: 'paid', customer_details: { email: 'hook@example.com' } } },
    });
    config.stripeWebhookSecret = secret;
    try {
      const unsigned = await ctx.request().post('/api/stripe/webhook').set('Content-Type', 'application/json').send(event);
      assert.equal(unsigned.status, 400);
      assert.equal((await agent.get(`/api/orders/${ref}`).query({ key })).body.order.status, 'pending');

      const signed = await ctx.request().post('/api/stripe/webhook')
        .set('Content-Type', 'application/json')
        .set('Stripe-Signature', signStripePayload(event, secret))
        .send(event);
      assert.equal(signed.status, 200);
      assert.equal((await agent.get(`/api/orders/${ref}`).query({ key })).body.order.status, 'paid');
    } finally {
      config.stripeWebhookSecret = '';
    }
  });
});

describe('the Amazon waitlist', () => {
  test('joins once per book, and only for a book sold on Amazon', async () => {
    const join = () => ctx.request().post('/api/waitlist').send({ email: 'wait@example.com', book: 'kdp-book' });
    assert.equal((await join()).status, 201);
    assert.equal((await join()).status, 201);
    const sub = await ctx.db('subscribers').where({ email: 'wait@example.com' }).first();
    assert.equal((await ctx.db('signups').where({ subscriber_id: sub.id, kind: 'waitlist' })).length, 1);
    assert.equal(Boolean(sub.marketing_consent), false, 'the waitlist is not consent to everything');
    const wrong = await ctx.request().post('/api/waitlist').send({ email: 'wait@example.com', book: 'paid-book' });
    assert.equal(wrong.status, 404);
  });

  test('the admin can take the waitlist as a CSV and see sales', async () => {
    const admin = ctx.request();
    await signUp(admin, 'boss@example.com');
    const csv = await admin.get('/api/admin/signups.csv').query({ kind: 'waitlist' });
    assert.equal(csv.status, 200);
    assert.match(csv.text, /wait@example\.com,,kdp-book,/);
    const stats = await admin.get('/api/admin/stats');
    const sale = stats.body.sales.find((s) => s.slug === 'paid-book');
    assert.equal(sale.test, true);
    assert.equal(sale.cents, sale.count * 2000);
    assert.equal((await ctx.request().get('/api/admin/signups.csv')).status, 401);
  });
});
