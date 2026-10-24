-- Paid tools on the site (2026-10-24): Dome Sketch, build packs, and one queue for tool jobs.
--
-- Dome Sketch (/sketch-app/) opens for anyone whose account holds a paid order whose product
-- grants "domesketch": the $10 product below, or the complete edition of the book. Both also
-- grant "buildpack" credits: a build pack is the full plan set for the buyer's exact design,
-- solved and drawn on the owner's machine (website/scripts/render_packs.py) like a cut list.
-- The owner (admin) has every tool without an order. Change a grant row to change the offer.

INSERT INTO products (slug, kind, title, subtitle, blurb, file_key, status, ships_note, ship_countries, external_url, sort, created_at, updated_at) VALUES
 ('dome-sketch', 'tool', 'Dome Sketch', 'Design your dome in 3-D',
  'Shape a framed-panel geodesic dome in your browser: size, door, windows, skin. Walk round it, cut a section through it, explode it, and get the build pack: plans, cut list, materials, tools, price estimate and every assembly step.',
  NULL, 'live', NULL, NULL, NULL, 6, '2026-10-24T00:00:00Z', '2026-10-24T00:00:00Z');

INSERT INTO prices (product, key, label, amount_cents, currency, honor, honor_prompt, active, sort) VALUES
 ('dome-sketch', 'standard', 'Dome Sketch, one time', 1000, 'usd', 0, NULL, 1, 0);

INSERT INTO tool_grants (product, tool, credits) VALUES
 ('dome-sketch', 'domesketch', 1),
 ('dome-sketch', 'buildpack', 10),
 ('the-40-hour-cabin', 'domesketch', 1),
 ('the-40-hour-cabin', 'buildpack', 10);

CREATE TABLE tool_jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ref TEXT NOT NULL UNIQUE,
  tool TEXT NOT NULL,                             -- 'buildpack'
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  params TEXT NOT NULL,                           -- JSON: the design (sketch_claude.model.Spec)
  status TEXT NOT NULL DEFAULT 'queued',          -- queued | rendering | done | failed
  attempts INTEGER NOT NULL DEFAULT 0,
  error TEXT,
  summary TEXT,
  file_key TEXT,
  size INTEGER,
  downloads INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  claimed_at TEXT,
  done_at TEXT
);
CREATE INDEX tool_jobs_user ON tool_jobs(user_id, tool);
CREATE INDEX tool_jobs_queue ON tool_jobs(tool, status, id);
