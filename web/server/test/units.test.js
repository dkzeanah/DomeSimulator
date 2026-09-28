import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import { boundingBox, haversineKm } from '../src/lib/geo.js';
import { latestVersion } from '../src/lib/books.js';
import { embedUrl, parseMediaUrl } from '../src/lib/media.js';
import { parseFeed } from '../src/lib/youtube.js';

test('media URLs from every shape the platforms hand out', () => {
  const cases = [
    ['https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42', 'youtube', 'dQw4w9WgXcQ', 'video'],
    ['https://youtu.be/dQw4w9WgXcQ?si=abc', 'youtube', 'dQw4w9WgXcQ', 'video'],
    ['https://youtube.com/shorts/dQw4w9WgXcQ', 'youtube', 'dQw4w9WgXcQ', 'short'],
    ['https://m.youtube.com/watch?v=dQw4w9WgXcQ', 'youtube', 'dQw4w9WgXcQ', 'video'],
    ['https://www.tiktok.com/@shortcircuitr5/video/7312345678901234567?lang=en', 'tiktok', '7312345678901234567', 'short'],
    ['https://www.instagram.com/p/C9abcDEF123/', 'instagram', 'C9abcDEF123', 'post'],
    ['https://www.instagram.com/donovanzeanah/reel/C9abcDEF123/', 'instagram', 'C9abcDEF123', 'reel'],
  ];
  for (const [url, platform, id, kind] of cases) {
    assert.deepEqual(parseMediaUrl(url), { platform, embedId: id, kind }, url);
  }
  for (const bad of ['not a url', 'https://example.com/watch?v=dQw4w9WgXcQ', 'https://youtube.com/watch?v=short', 'https://tiktok.com/@x']) {
    assert.equal(parseMediaUrl(bad), null, bad);
  }
  assert.equal(embedUrl('tiktok', '7312345678901234567'), 'https://www.tiktok.com/embed/v2/7312345678901234567');
});

test('distance: known city pair, and the box always contains the circle', () => {
  // New York to London is about 5,570 km.
  const d = haversineKm(40.7128, -74.006, 51.5074, -0.1278);
  assert.ok(Math.abs(d - 5570) < 15, String(d));
  const box = boundingBox(60, 10, 100);
  for (let bearing = 0; bearing < 360; bearing += 15) {
    // March 99 km out along each bearing: the point must be inside the box.
    const r = 99 / 6371.0088;
    const lat1 = (60 * Math.PI) / 180;
    const b = (bearing * Math.PI) / 180;
    const lat2 = Math.asin(Math.sin(lat1) * Math.cos(r) + Math.cos(lat1) * Math.sin(r) * Math.cos(b));
    const lng2 = (10 * Math.PI) / 180 + Math.atan2(Math.sin(b) * Math.sin(r) * Math.cos(lat1), Math.cos(r) - Math.sin(lat1) * Math.sin(lat2));
    const [la, ln] = [(lat2 * 180) / Math.PI, (lng2 * 180) / Math.PI];
    assert.ok(la >= box.minLat && la <= box.maxLat && ln >= box.minLng && ln <= box.maxLng, `bearing ${bearing}`);
  }
});

test('the newest edition wins, and a gap in versions does not matter', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'domenet-v-'));
  for (const name of ['book.pdf', 'book-v2.pdf', 'book-v7.pdf', 'book-kdp-v9.pdf', 'bookish.pdf']) {
    fs.writeFileSync(path.join(dir, name), 'x');
  }
  assert.equal(latestVersion(dir, 'book.pdf').name, 'book-v7.pdf');
  assert.equal(latestVersion(dir, 'book-kdp.pdf').name, 'book-kdp-v9.pdf');
  assert.equal(latestVersion(dir, 'other.pdf'), null);
});

test('the YouTube feed parser reads ids, titles and shorts', () => {
  const xml = `<feed><entry><yt:videoId>abcdefghijk</yt:videoId><title>Seams &amp; wedges</title>
    <link rel="alternate" href="https://www.youtube.com/shorts/abcdefghijk"/><published>2026-09-20T10:00:00+00:00</published></entry>
    <entry><yt:videoId>bcdefghijkl</yt:videoId><title>The 40 hour cabin</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=bcdefghijkl"/></entry></feed>`;
  const items = parseFeed(xml);
  assert.equal(items.length, 2);
  assert.equal(items[0].title, 'Seams & wedges');
  assert.equal(items[0].short, true);
  assert.equal(items[1].short, false);
});
