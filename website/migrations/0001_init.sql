-- zeanahlab.com, the whole schema. Later changes go in new numbered files; never edit
-- this one once it has run anywhere.
--
-- Three groups:
--   * the list and the shop, ported from web/ (subscribers, signups, users, sessions,
--     downloads, orders, listings);
--   * the dome community (pad numbers, backers, plaques, salvage, the public event feed);
--   * every member's own life account -- the tables of the book's program, snowball.py
--     (skills, quests, quest_requirements, methods, method_xp, assets, logs), one set per
--     member, so people own their numbers.

-- ---------------------------------------------------------------- the list

CREATE TABLE subscribers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  name TEXT,
  marketing_consent INTEGER NOT NULL DEFAULT 0,
  source TEXT,                                   -- which form: sample, signup, backer, ...
  created_at TEXT NOT NULL,
  unsubscribed_at TEXT
);

-- One row per thing somebody asked for, so the admin page can say which offer pulls.
CREATE TABLE signups (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  subscriber_id INTEGER NOT NULL REFERENCES subscribers(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,                            -- sample | waitlist | purchase | backer | founder
  book_slug TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX signups_kind ON signups(kind, book_slug);

-- ---------------------------------------------------------------- accounts

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,                   -- pbkdf2-sha256$iterations$salt$hash
  display_name TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'member',           -- member | admin (from ADMIN_EMAILS)
  bio TEXT,
  city TEXT,
  region TEXT,
  country TEXT,
  public_profile INTEGER NOT NULL DEFAULT 0,     -- may visitors inspect this account?
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

-- The cookie holds a random token; only its hash is kept, so a copy of the database
-- cannot be used to sign in as anyone.
CREATE TABLE sessions (
  token_hash TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL
);
CREATE INDEX sessions_user ON sessions(user_id);

CREATE TABLE downloads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  subscriber_id INTEGER REFERENCES subscribers(id) ON DELETE SET NULL,
  user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  book_slug TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX downloads_book ON downloads(book_slug);

-- ---------------------------------------------------------------- the shop

CREATE TABLE orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ref TEXT NOT NULL UNIQUE,                      -- public
  key_hash TEXT NOT NULL,                        -- the buyer's link key, hashed
  book_slug TEXT NOT NULL,
  amount_cents INTEGER NOT NULL,
  currency TEXT NOT NULL,
  email TEXT,
  user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  subscriber_id INTEGER REFERENCES subscribers(id) ON DELETE SET NULL,
  status TEXT NOT NULL DEFAULT 'pending',        -- pending | paid | refunded
  provider TEXT NOT NULL,                        -- stripe | test
  provider_session TEXT,
  marketing_consent INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  paid_at TEXT
);
CREATE INDEX orders_status ON orders(status);
CREATE INDEX orders_user ON orders(user_id);

-- ---------------------------------------------------------------- the network

-- Pad hosts, dome owners, quilters, builders, recyclers, standing timber. A pad host's
-- listing carries its own numbers ("with reasoning"): what a night costs a guest, how
-- often it is let, what a season costs to run, and what it has. All host-reported, and
-- shown as host-reported.
CREATE TABLE listings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT,
  city TEXT,
  region TEXT,
  country TEXT,
  postal_code TEXT,
  lat REAL,
  lng REAL,
  contact TEXT,
  -- pad numbers (pad_host only)
  nightly_rate_cents INTEGER,
  occupancy_pct REAL,                            -- share of nights let, 0-100
  season_cost_cents INTEGER,                     -- running cost per season
  season_nights INTEGER,                         -- nights in the host's season
  hookups TEXT,                                  -- comma list: water,power,septic,internet
  pad_status TEXT,                               -- planned | built | hosting
  visible INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX listings_kind ON listings(kind);
CREATE INDEX listings_geo ON listings(lat, lng);
CREATE INDEX listings_user ON listings(user_id);

-- ---------------------------------------------------------------- backers and founders

-- A backer is recorded when they really back (by the admin, from the campaign's own
-- records) -- the site never takes a pledge itself. Tier keys are kickstarter.tiers().
CREATE TABLE backers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  display_name TEXT NOT NULL,                    -- as they want to be shown
  tier TEXT NOT NULL,
  pledge_cents INTEGER NOT NULL,
  public INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL
);

-- One triangular plaque per dome panel. A slot is claimed by a founder and is then a
-- public, permanent credential that is also a piece of the building.
CREATE TABLE plaques (
  slot INTEGER PRIMARY KEY,                      -- 1..panel count of the dome
  backer_id INTEGER REFERENCES backers(id) ON DELETE SET NULL,
  inscription TEXT,
  status TEXT NOT NULL DEFAULT 'claimed',        -- claimed | cut | mounted
  claimed_at TEXT NOT NULL
);

-- ---------------------------------------------------------------- recyclers

-- Salvage as account work: what an hour reclaimed, and what buying it new would have cost.
CREATE TABLE salvage_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  material TEXT NOT NULL,
  quantity REAL NOT NULL,
  unit TEXT NOT NULL,
  hours REAL NOT NULL,
  replacement_cents INTEGER NOT NULL,            -- what the same material costs new
  note TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX salvage_user ON salvage_logs(user_id);

-- ---------------------------------------------------------------- the public feed

-- Every real event that moves a public number: a subscriber, a member, a pad, a backer,
-- a plaque. The home page's "the build, live" panel reads this; nothing is invented.
CREATE TABLE events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL,
  label TEXT NOT NULL,
  created_at TEXT NOT NULL
);

-- ---------------------------------------------------------------- the life account
-- snowball.py's tables, per member. Same names, same meaning; user_id added.

CREATE TABLE skills (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  level INTEGER NOT NULL DEFAULT 1,
  xp REAL NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, name)
);

CREATE TABLE quests (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'not_started',    -- not_started | in_progress | complete
  description TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (user_id, name)
);

CREATE TABLE quest_requirements (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  quest TEXT NOT NULL,
  kind TEXT NOT NULL,                            -- skill | quest | capital | asset
  target TEXT NOT NULL,
  amount REAL NOT NULL DEFAULT 1
);
CREATE INDEX quest_req_user ON quest_requirements(user_id, quest);

CREATE TABLE methods (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  cash_per_hour REAL NOT NULL DEFAULT 0,
  cost_per_hour REAL NOT NULL DEFAULT 0,
  notes TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (user_id, name)
);

CREATE TABLE method_xp (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  method TEXT NOT NULL,
  skill TEXT NOT NULL,
  xp_per_hour REAL NOT NULL DEFAULT 0
);
CREATE INDEX method_xp_user ON method_xp(user_id, method);

CREATE TABLE assets (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  value REAL NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, name)
);

CREATE TABLE logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  ts TEXT NOT NULL,
  method TEXT NOT NULL,
  hours REAL NOT NULL,
  cash REAL NOT NULL DEFAULT 0,
  note TEXT NOT NULL DEFAULT ''
);
CREATE INDEX logs_user ON logs(user_id, ts);

-- working capital and the XP weight, per member (snowball.py's meta table)
CREATE TABLE account_meta (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  PRIMARY KEY (user_id, key)
);
