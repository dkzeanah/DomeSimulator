-- The owner's studio (2026-10-16): sign in by username as well as email, access levels given
-- by rolling invite codes, friend prices unlocked by promo codes, the children's book, and
-- each member's own dome -- one number, the longest strut, which puts them in a dome class.

-- ---------------------------------------------------------------- accounts

-- Optional, unique, lower-case. The owner's (OWNER_USERNAME in wrangler.toml) is reserved for
-- the address in ADMIN_EMAILS and is set on the owner's first sign-in after this runs.
ALTER TABLE users ADD COLUMN username TEXT;
CREATE UNIQUE INDEX users_username ON users(username) WHERE username IS NOT NULL;

-- Roles are now: member (default), friend (sees friend prices), manager (runs the admin pages),
-- admin (the owner, from ADMIN_EMAILS). Friend and manager come from an invite code at sign-up
-- or from the owner's members page. The code a member joined with is kept, never the code itself
-- -- only the level it gave.
ALTER TABLE users ADD COLUMN joined_with TEXT;              -- e.g. invite:friend

-- The member's own dome. A 2V wedge dome is fixed by its longest strut; members whose domes
-- share it take the same panels. The figures are computed from it (src/generated/dome-classes.json).
ALTER TABLE users ADD COLUMN dome_long_in INTEGER;          -- the class: longest strut, whole inches
ALTER TABLE users ADD COLUMN dome_status TEXT;              -- planning | building | built
ALTER TABLE users ADD COLUMN dome_note TEXT;
CREATE INDEX users_dome ON users(dome_long_in);

-- ---------------------------------------------------------------- friend prices and promo codes

-- A gated price is never listed. It is unlocked by a promo code for its product, or shown to
-- members whose role is friend.
ALTER TABLE prices ADD COLUMN gated INTEGER NOT NULL DEFAULT 0;

-- Codes the owner hands out. Each unlocks one gated price of one product. Made and switched off
-- on the admin studio page; none are seeded here, because this file is public.
CREATE TABLE promo_codes (
  code TEXT PRIMARY KEY,                     -- upper case
  product TEXT NOT NULL REFERENCES products(slug) ON DELETE CASCADE,
  price_key TEXT NOT NULL,
  max_uses INTEGER,                          -- NULL = no limit
  uses INTEGER NOT NULL DEFAULT 0,           -- paid orders only
  active INTEGER NOT NULL DEFAULT 1,
  note TEXT,                                 -- who it was for
  created_at TEXT NOT NULL
);

ALTER TABLE orders ADD COLUMN promo_code TEXT;

-- ---------------------------------------------------------------- the children's book

-- My Own Home, My Own Dome: a rhyming picture book of the build, $5 (owner, 2026-10-16).
-- A pre-order until the illustrated PDF is uploaded to R2; then set it live on the studio page.
INSERT INTO products (slug, kind, title, subtitle, blurb, file_key, status, ships_note, ship_countries, external_url, sort, created_at, updated_at) VALUES
 ('my-own-home-my-own-dome', 'digital', 'My Own Home, My Own Dome', 'A rhyming picture book',
  'One log, one saw, and one stubborn kid: the dome build told in rhyme, for reading aloud.',
  'my-own-home-my-own-dome.pdf', 'preorder',
  'Being illustrated now. You are charged today, and the book appears on this order page the day it is finished. Write to owner@zeanahlab.com for a full refund any time before then.',
  NULL, NULL, 5, '2026-10-16T00:00:00Z', '2026-10-16T00:00:00Z');

INSERT INTO prices (product, key, label, amount_cents, currency, honor, honor_prompt, active, sort, gated) VALUES
 ('my-own-home-my-own-dome', 'standard', 'Digital picture book', 500, 'usd', 0, NULL, 1, 0, 0),
 ('my-own-home-my-own-dome', 'friend', 'Friend price', 100, 'usd', 0, NULL, 1, 1, 1),
 ('the-40-hour-cabin', 'friend', 'Friend price', 500, 'usd', 0, NULL, 1, 1, 1);

-- What the home page leads with. The book for now; the studio page switches it.
INSERT INTO settings(key, value, updated_at) VALUES ('home.focus', 'book', '2026-10-16T00:00:00Z')
  ON CONFLICT(key) DO NOTHING;
