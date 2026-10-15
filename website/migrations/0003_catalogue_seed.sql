-- The first catalogue (2026-10-14, the owner's prices). After this, edit rows -- never this file.
--
-- the-40-hour-cabin   digital complete edition, $20 (web/books.config.json)
-- design-session      one-on-one session, $50 (web/books.config.json)
-- triangular-book     the hand-made triangular edition: $50, or $30 with a non-monetary
--                     donation on the honor system (owner, 2026-10-14). A pre-order until
--                     printed: charged now, refundable until it ships.
-- 2-trees             the simplified edition on Amazon, owner's range $10-15; listed at
--                     $12.99 until KDP's printing cost for the final page count is known.

INSERT INTO products (slug, kind, title, subtitle, blurb, file_key, status, ships_note, ship_countries, external_url, sort, created_at, updated_at) VALUES
 ('sample', 'digital', 'The Free Sample', 'The 40 Hour Cabin: Complete Edition',
  'The opening of the complete edition, exactly as built.', 'the-40-hour-cabin-sample.pdf', 'live', NULL, NULL, NULL, 0,
  '2026-10-14T00:00:00Z', '2026-10-14T00:00:00Z'),
 ('the-40-hour-cabin', 'digital', 'The 40 Hour Cabin', 'Complete Edition',
  'The complete edition: the 40-hour frame from standing tree to raised shell, then every way to style it, with the codebase that computed all of it.',
  'the-40-hour-cabin.pdf', 'live', NULL, NULL, NULL, 1, '2026-10-14T00:00:00Z', '2026-10-14T00:00:00Z'),
 ('triangular-book', 'physical', 'The 40 Hour Cabin', 'The triangular edition',
  'Three sides -- build, count, convert -- the shape of every panel in the dome. Printed and bound by hand to fund the build.',
  NULL, 'preorder',
  'A pre-order: it is being made by hand and has no ship date yet. You are charged now and can cancel for a full refund at any time before it ships. US shipping is included.',
  'US', NULL, 2, '2026-10-14T00:00:00Z', '2026-10-14T00:00:00Z'),
 ('design-session', 'service', 'One-on-one design session', 'Your dome, designed with the author',
  'A one-on-one session with the author, designing your dome with the project''s own tools.', NULL, 'live', NULL, NULL, NULL, 3,
  '2026-10-14T00:00:00Z', '2026-10-14T00:00:00Z'),
 ('2-trees', 'amazon', 'The 40 Hour Cabin', '2V Geodesic Dome Wedge Method',
  'The simplified paperback: three trees, one chainsaw, and a geodesic cabin -- the build day by day.', NULL, 'waitlist', NULL, NULL, NULL, 4,
  '2026-10-14T00:00:00Z', '2026-10-14T00:00:00Z');

INSERT INTO prices (product, key, label, amount_cents, currency, honor, honor_prompt, active, sort) VALUES
 ('sample', 'free', 'Free for your email', 0, 'usd', 0, NULL, 1, 0),
 ('the-40-hour-cabin', 'standard', 'Digital edition', 2000, 'usd', 0, NULL, 1, 0),
 ('triangular-book', 'standard', 'The triangular book', 5000, 'usd', 0, NULL, 1, 0),
 ('triangular-book', 'donation', 'With a non-monetary donation', 3000, 'usd', 1,
  'What are you giving to the build? Materials, tools, labour, a skill, land to use, a place to stay -- describe it. This price runs on your word.', 1, 1),
 ('design-session', 'standard', 'One session', 5000, 'usd', 0, NULL, 1, 0),
 ('2-trees', 'amazon', 'Paperback on Amazon', 1299, 'usd', 0, NULL, 1, 0);
