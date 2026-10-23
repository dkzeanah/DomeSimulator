-- The Wedge Builder: cut lists made for a buyer's own dome (2026-10-23).
--
-- A buyer with a paid order types a size and a log; the request is queued here; the owner's
-- machine (website/scripts/render_cutlists.py, an agent key with scope cutlists:render) solves
-- it with the project's wedge_builder package and uploads the PDF to R2; the buyer downloads it
-- from their receipt link. The site never runs the solver: it only gates, queues and serves.
--
-- What a purchase entitles is rows in tool_grants, not code: the Wedge Builder itself gives
-- `credits` cut lists per order; the complete edition of the book gives one. Change a row to
-- change the offer. A failed render does not use a credit.
--
-- The Wedge Builder product starts HIDDEN at a placeholder price: the owner sets the price and
-- puts it live (Admin, or `UPDATE products SET status='live' WHERE slug='wedge-builder'`).

CREATE TABLE tool_grants (
  product TEXT NOT NULL,            -- products.slug
  tool TEXT NOT NULL,               -- 'cutlist'
  credits INTEGER NOT NULL,         -- per paid order
  PRIMARY KEY (product, tool)
);

CREATE TABLE cutlists (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ref TEXT NOT NULL UNIQUE,                       -- public, in the download link
  order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  params TEXT NOT NULL,                           -- the request as JSON (wedge_builder.design.Request)
  status TEXT NOT NULL DEFAULT 'queued',          -- queued | rendering | done | failed
  attempts INTEGER NOT NULL DEFAULT 0,
  error TEXT,                                     -- a reason the buyer can read, when failed
  design TEXT,                                    -- the design id the solver printed on the PDF
  summary TEXT,                                   -- JSON: headline numbers from the render
  file_key TEXT,                                  -- R2 key of the PDF
  size INTEGER,
  downloads INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  claimed_at TEXT,
  done_at TEXT
);
CREATE INDEX cutlists_order ON cutlists(order_id);
CREATE INDEX cutlists_queue ON cutlists(status, id);

INSERT INTO products (slug, kind, title, subtitle, blurb, file_key, status, ships_note, ship_countries, external_url, sort, created_at, updated_at) VALUES
 ('wedge-builder', 'tool', 'The Wedge Builder', 'Your dome''s cut list',
  'Type your dome''s size and your logs. Get back the saw setups, every cut family, which round of which log each wedge comes from, the jigs and the seams, solved for your dome by the same solver as the book.',
  NULL, 'hidden', NULL, NULL, NULL, 5, '2026-10-23T00:00:00Z', '2026-10-23T00:00:00Z');

INSERT INTO prices (product, key, label, amount_cents, currency, honor, honor_prompt, active, sort) VALUES
 ('wedge-builder', 'standard', 'The Wedge Builder', 7900, 'usd', 0, NULL, 1, 0);

INSERT INTO tool_grants (product, tool, credits) VALUES
 ('wedge-builder', 'cutlist', 25),
 ('the-40-hour-cabin', 'cutlist', 1);
