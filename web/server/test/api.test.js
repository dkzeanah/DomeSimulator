import assert from 'node:assert/strict';
import { after, before, describe, test } from 'node:test';
import { freshApp, signUp } from './helpers.js';

let ctx;
before(async () => {
  ctx = await freshApp();
});
after(async () => {
  await ctx.db.destroy();
});

describe('accounts', () => {
  test('sign up, see yourself, sign out', async () => {
    const agent = ctx.request();
    const user = await signUp(agent, 'Ada@Example.com');
    assert.equal(user.email, 'ada@example.com', 'emails are stored lower-case');
    assert.equal(user.role, 'member');
    assert.equal(user.passwordHash, undefined);
    assert.equal((await agent.get('/api/auth/me')).body.user.email, 'ada@example.com');
    await agent.post('/api/auth/logout').send({});
    assert.equal((await agent.get('/api/auth/me')).body.user, null);
  });

  test('the same email cannot sign up twice', async () => {
    const res = await ctx.request().post('/api/auth/signup')
      .send({ email: 'ada@example.com', password: 'another long one', displayName: 'Ada' });
    assert.equal(res.status, 409);
  });

  test('a short password is refused with a readable message', async () => {
    const res = await ctx.request().post('/api/auth/signup')
      .send({ email: 'short@example.com', password: 'abc', displayName: 'S' });
    assert.equal(res.status, 400);
    assert.match(res.body.error, /password/);
  });

  test('wrong password and unknown email get the same answer', async () => {
    const a = await ctx.request().post('/api/auth/login').send({ email: 'ada@example.com', password: 'nope nope nope' });
    const b = await ctx.request().post('/api/auth/login').send({ email: 'nobody@example.com', password: 'nope nope nope' });
    assert.equal(a.status, 401);
    assert.equal(b.status, 401);
    assert.equal(a.body.error, b.body.error);
  });

  test('sign in works and ADMIN_EMAILS makes an admin', async () => {
    const agent = ctx.request();
    const user = await signUp(agent, 'boss@example.com');
    assert.equal(user.role, 'admin');
    const again = ctx.request();
    const res = await again.post('/api/auth/login').send({ email: 'BOSS@example.com', password: 'correct horse battery' });
    assert.equal(res.status, 200);
    assert.equal(res.body.user.role, 'admin');
  });

  test('profile edits, and a new password needs the old one', async () => {
    const agent = ctx.request();
    await signUp(agent, 'edit@example.com');
    const ok = await agent.patch('/api/auth/me').send({ city: 'Asheville', bio: 'Splits logs.' });
    assert.equal(ok.body.user.city, 'Asheville');
    const bad = await agent.patch('/api/auth/me').send({ newPassword: 'a brand new password' });
    assert.equal(bad.status, 400);
    const good = await agent.patch('/api/auth/me')
      .send({ currentPassword: 'correct horse battery', newPassword: 'a brand new password' });
    assert.equal(good.status, 200);
    const login = await ctx.request().post('/api/auth/login').send({ email: 'edit@example.com', password: 'a brand new password' });
    assert.equal(login.status, 200);
  });

  test('writes must be JSON (the CSRF guard)', async () => {
    const res = await ctx.request().post('/api/auth/login').type('form').send('email=a@b.c&password=x');
    assert.equal(res.status, 415);
  });
});

describe('the book gate', () => {
  test('the catalogue reports the newest edition and hides disk paths', async () => {
    const { body } = await ctx.request().get('/api/books');
    const book = body.books.find((b) => b.slug === 'test-book');
    assert.equal(book.edition, 3);
    assert.equal(book.available, true);
    assert.equal(JSON.stringify(body).includes('\\'), false, 'no Windows paths leak');
    assert.equal(body.books.find((b) => b.slug === 'missing-book').available, false);
  });

  test('an email buys a download link, and the link serves the newest PDF', async () => {
    const lead = await ctx.request().post('/api/leads')
      .send({ email: 'reader@example.com', book: 'test-book', marketingConsent: true });
    assert.equal(lead.status, 201);
    const pdf = await ctx.request().get(lead.body.downloadUrl).buffer(true).parse((res, cb) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => cb(null, Buffer.concat(chunks)));
    });
    assert.equal(pdf.status, 200);
    assert.equal(pdf.headers['content-type'], 'application/pdf');
    assert.match(pdf.headers['content-disposition'], /test-book-edition-3\.pdf/);
    assert.equal(pdf.body.toString(), '%PDF-1.4 third edition');
    const rows = await ctx.db('downloads').where({ book_slug: 'test-book' });
    assert.equal(rows.length, 1);
  });

  test('a HEAD request (a link preview) is not counted as a download', async () => {
    const lead = await ctx.request().post('/api/leads').send({ email: 'peek@example.com', book: 'test-book' });
    const before = (await ctx.db('downloads')).length;
    const head = await ctx.request().head(lead.body.downloadUrl);
    assert.equal(head.status, 200);
    assert.equal((await ctx.db('downloads')).length, before);
  });

  test('a tampered or missing token is refused', async () => {
    const lead = await ctx.request().post('/api/leads').send({ email: 'x@example.com', book: 'test-book' });
    const tampered = lead.body.downloadUrl.replace(/.$/, (c) => (c === 'A' ? 'B' : 'A'));
    assert.equal((await ctx.request().get(tampered)).status, 403);
    assert.equal((await ctx.request().get('/api/books/test-book/download')).status, 403);
  });

  test('a signed-in member downloads without the gate', async () => {
    const agent = ctx.request();
    await signUp(agent, 'member-dl@example.com');
    assert.equal((await agent.get('/api/books/test-book/download')).status, 200);
  });

  test('the same email twice is one subscriber, and consent only goes up by choice', async () => {
    await ctx.request().post('/api/leads').send({ email: 'twice@example.com', book: 'test-book', marketingConsent: true });
    await ctx.request().post('/api/leads').send({ email: 'TWICE@example.com', book: 'test-book', marketingConsent: false });
    const rows = await ctx.db('subscribers').where({ email: 'twice@example.com' });
    assert.equal(rows.length, 1);
    assert.equal(Boolean(rows[0].marketing_consent), true);
  });

  test('the honeypot field catches bots; an unknown book is a 404', async () => {
    const bot = await ctx.request().post('/api/leads').send({ email: 'bot@example.com', book: 'test-book', website: 'spam.biz' });
    assert.equal(bot.status, 400);
    const none = await ctx.request().post('/api/leads').send({ email: 'y@example.com', book: 'missing-book' });
    assert.equal(none.status, 404);
  });

  test('the admin CSV holds only people who opted in and did not leave', async () => {
    await ctx.request().post('/api/leads').send({ email: 'yes@example.com', book: 'test-book', marketingConsent: true });
    await ctx.request().post('/api/leads').send({ email: 'no@example.com', book: 'test-book' });
    await ctx.request().post('/api/leads').send({ email: 'left@example.com', book: 'test-book', marketingConsent: true });
    await ctx.request().post('/api/unsubscribe').send({ email: 'left@example.com' });
    const admin = ctx.request();
    await admin.post('/api/auth/login').send({ email: 'boss@example.com', password: 'correct horse battery' });
    const csv = await admin.get('/api/admin/subscribers.csv');
    assert.equal(csv.status, 200);
    assert.match(csv.text, /yes@example\.com/);
    assert.doesNotMatch(csv.text, /no@example\.com/);
    assert.doesNotMatch(csv.text, /left@example\.com/);
    assert.equal((await ctx.request().get('/api/admin/subscribers.csv')).status, 401);
  });
});

describe('the dome network', () => {
  let host;
  let owner;
  before(async () => {
    host = ctx.request();
    owner = ctx.request();
    await signUp(host, 'host@example.com');
    await signUp(owner, 'owner@example.com');
    const add = (agent, body) => agent.post('/api/network').send(body);
    // Asheville NC, Knoxville TN (~150 km), Portland OR (~3,500 km).
    assert.equal((await add(host, { kind: 'pad_host', title: 'Serviced pad in the hills', body: 'Water and power at the port.', city: 'Asheville', region: 'NC', lat: 35.5951, lng: -82.5515, contact: 'host@example.com' })).status, 201);
    assert.equal((await add(host, { kind: 'timber', title: 'Standing pine to split', city: 'Knoxville', region: 'TN', lat: 35.9606, lng: -83.9207 })).status, 201);
    assert.equal((await add(owner, { kind: 'quilter', title: 'Quilting layers for hire', city: 'Portland', region: 'OR', lat: 45.5152, lng: -122.6784, contact: 'quilts@example.com' })).status, 201);
  });

  test('text search finds by title, body or place, case-insensitively', async () => {
    const hits = (q) => ctx.request().get('/api/network').query({ q }).then((r) => r.body.results.map((x) => x.title));
    assert.deepEqual(await hits('QUILT'), ['Quilting layers for hire']);
    assert.deepEqual(await hits('power at'), ['Serviced pad in the hills']);
    assert.deepEqual(await hits('knoxville'), ['Standing pine to split']);
    assert.deepEqual(await hits('100%'), [], 'a % in the query is literal, not a wildcard');
  });

  test('kind filter', async () => {
    const res = await ctx.request().get('/api/network').query({ kind: 'pad_host' });
    assert.equal(res.body.total, 1);
    assert.equal(res.body.results[0].kind, 'pad_host');
  });

  test('near me: sorted by distance, and the radius is a real circle', async () => {
    const res = await ctx.request().get('/api/network').query({ lat: 35.6, lng: -82.55, radiusKm: 300 });
    assert.deepEqual(res.body.results.map((x) => x.city), ['Asheville', 'Knoxville']);
    assert.ok(res.body.results[0].distanceKm < 2);
    assert.ok(res.body.results[1].distanceKm > 100 && res.body.results[1].distanceKm < 200);
    const tight = await ctx.request().get('/api/network').query({ lat: 35.6, lng: -82.55, radiusKm: 50 });
    assert.equal(tight.body.total, 1);
  });

  test('strangers see a rounded location and no contact details', async () => {
    const res = await ctx.request().get('/api/network').query({ kind: 'pad_host' });
    const hit = res.body.results[0];
    assert.equal(hit.lat, 35.6);
    assert.equal(hit.lng, -82.55);
    assert.equal(hit.contact, null);
    assert.equal(hit.contactHidden, true);
    const member = await owner.get('/api/network').query({ kind: 'pad_host' });
    assert.equal(member.body.results[0].contact, 'host@example.com');
  });

  test('only the owner (or an admin) can edit or delete a listing', async () => {
    const mine = await host.get('/api/network/mine');
    const id = mine.body.results[0].id;
    assert.equal((await owner.patch(`/api/network/${id}`).send({ title: 'Hijacked' })).status, 403);
    assert.equal((await owner.delete(`/api/network/${id}`)).status, 403);
    const edit = await host.patch(`/api/network/${id}`).send({ title: 'Serviced pad, two acres' });
    assert.equal(edit.body.listing.title, 'Serviced pad, two acres');
  });

  test('a hidden listing drops out of search', async () => {
    const mine = await owner.get('/api/network/mine');
    const id = mine.body.results[0].id;
    await owner.patch(`/api/network/${id}`).send({ visible: false });
    const res = await ctx.request().get('/api/network').query({ q: 'quilt' });
    assert.equal(res.body.total, 0);
    await owner.patch(`/api/network/${id}`).send({ visible: true });
  });

  test('an unknown kind is refused', async () => {
    const res = await host.post('/api/network').send({ kind: 'spaceship', title: 'Nope nope' });
    assert.equal(res.status, 400);
  });

  test('deleting an account takes its listings with it', async () => {
    const agent = ctx.request();
    await signUp(agent, 'leaver@example.com');
    await agent.post('/api/network').send({ kind: 'builder', title: 'Frames built to order' });
    const wrong = await agent.delete('/api/auth/me').send({ password: 'wrong wrong wrong' });
    assert.equal(wrong.status, 400);
    const gone = await agent.delete('/api/auth/me').send({ password: 'correct horse battery' });
    assert.equal(gone.status, 200);
    const res = await ctx.request().get('/api/network').query({ q: 'frames built' });
    assert.equal(res.body.total, 0);
  });
});

describe('links and media', () => {
  let admin;
  before(async () => {
    admin = ctx.request();
    await admin.post('/api/auth/login').send({ email: 'boss@example.com', password: 'correct horse battery' });
  });

  test('only admins add links; the public sees visible ones in order', async () => {
    const member = ctx.request();
    await signUp(member, 'nosy@example.com');
    assert.equal((await member.post('/api/links').send({ label: 'x', url: 'https://x.test' })).status, 403);
    const a = await admin.post('/api/links').send({ label: 'Book', url: 'https://example.com/book', icon: 'book' });
    const b = await admin.post('/api/links').send({ label: 'TikTok', url: 'https://www.tiktok.com/@shortcircuitr5', icon: 'tiktok' });
    assert.equal(a.status, 201);
    await admin.patch(`/api/links/${b.body.link.id}`).send({ visible: false });
    const pub = await ctx.request().get('/api/links');
    assert.deepEqual(pub.body.links.map((l) => l.label), ['Book']);
    const all = await admin.get('/api/links').query({ all: '1' });
    assert.equal(all.body.links.length, 2);
  });

  test('a javascript: link is refused', async () => {
    const res = await admin.post('/api/links').send({ label: 'Evil', url: 'javascript:alert(1)' });
    assert.equal(res.status, 400);
  });

  test('pasting a URL puts it on the wall with an embed address', async () => {
    const yt = await admin.post('/api/media').send({ url: 'https://youtu.be/dQw4w9WgXcQ', title: 'The seam', featured: true });
    assert.equal(yt.status, 201);
    assert.equal(yt.body.media.embedUrl, 'https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ?rel=0');
    const tt = await admin.post('/api/media').send({ url: 'https://www.tiktok.com/@shortcircuitr5/video/7312345678901234567' });
    assert.equal(tt.body.media.platform, 'tiktok');
    const ig = await admin.post('/api/media').send({ url: 'https://www.instagram.com/reel/C9abcDEF123/' });
    assert.equal(ig.body.media.embedUrl, 'https://www.instagram.com/reel/C9abcDEF123/embed');
    assert.equal((await admin.post('/api/media').send({ url: 'https://youtu.be/dQw4w9WgXcQ' })).status, 409);
    assert.equal((await admin.post('/api/media').send({ url: 'https://example.com/video' })).status, 400);
    const wall = await ctx.request().get('/api/media');
    assert.equal(wall.body.media[0].title, 'The seam', 'featured first');
    const onlyTiktok = await ctx.request().get('/api/media').query({ platform: 'tiktok' });
    assert.equal(onlyTiktok.body.media.length, 1);
  });

  test('YouTube latest is empty, not an error, when no channel is set', async () => {
    const res = await ctx.request().get('/api/media/youtube-latest');
    assert.equal(res.status, 200);
    assert.equal(res.body.channelConfigured, false);
  });

  test('the facts endpoint serves the model export', async () => {
    const res = await ctx.request().get('/api/facts');
    assert.equal(res.body.facts.dome.bays, 40);
  });
});
