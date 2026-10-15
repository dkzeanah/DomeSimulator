-- The list, the mail queue, and first-party analytics. No third party anywhere: the site
-- decides what to send and to whom and keeps every record; the owner's own mail program
-- (on a rented server) collects the queue, signs and delivers each message, and reports
-- back. Analytics are counted here, on the site, from the site's own requests.

-- ---------------------------------------------------------------- the list

-- A subscriber's place in the list's life: unconfirmed -> confirmed (double opt-in), or out
-- (unsubscribed / bounced / complained). Marketing goes only to confirmed + consenting +
-- not suppressed. First touch records where they came from, for acquisition reports.
ALTER TABLE subscribers ADD COLUMN status TEXT NOT NULL DEFAULT 'unconfirmed';
ALTER TABLE subscribers ADD COLUMN confirmed_at TEXT;
ALTER TABLE subscribers ADD COLUMN visitor_id TEXT;
ALTER TABLE subscribers ADD COLUMN first_source TEXT;
ALTER TABLE subscribers ADD COLUMN first_medium TEXT;
ALTER TABLE subscribers ADD COLUMN first_campaign TEXT;
ALTER TABLE subscribers ADD COLUMN first_referrer TEXT;
ALTER TABLE subscribers ADD COLUMN first_landing TEXT;
CREATE INDEX subscribers_status ON subscribers(status);

CREATE TABLE subscriber_tags (
  subscriber_id INTEGER NOT NULL REFERENCES subscribers(id) ON DELETE CASCADE,
  tag TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY (subscriber_id, tag)
);

-- Addresses that must never be mailed again, whatever the list says.
CREATE TABLE suppressions (
  email TEXT PRIMARY KEY,
  reason TEXT NOT NULL,                       -- unsubscribed | bounced | complained | manual
  created_at TEXT NOT NULL
);

-- Who a message is from. Each identity is its own voice, with its own counts. archive_bcc:
-- a copy of every message goes there (the owner's Gmail), so nothing exists in one place only.
CREATE TABLE identities (
  key TEXT PRIMARY KEY,
  from_name TEXT NOT NULL,
  from_email TEXT NOT NULL,
  reply_to TEXT,
  archive_bcc TEXT,
  purpose TEXT NOT NULL
);

-- ---------------------------------------------------------------- what is sent

CREATE TABLE campaigns (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  identity TEXT NOT NULL REFERENCES identities(key),
  subject TEXT NOT NULL,
  body TEXT NOT NULL,                         -- plain text with {{tokens}}; html is made from it
  segment TEXT NOT NULL DEFAULT '{}',         -- JSON: {"tags":[...],"source":"..."}
  status TEXT NOT NULL DEFAULT 'draft',       -- draft | queued
  queued_count INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  queued_at TEXT
);

-- Automations: a trigger (a kind of signup) starts a run of timed steps.
CREATE TABLE sequences (
  key TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  trigger TEXT NOT NULL,                      -- sample | signup | purchase | backer
  active INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE sequence_steps (
  sequence TEXT NOT NULL REFERENCES sequences(key) ON DELETE CASCADE,
  step INTEGER NOT NULL,
  delay_hours REAL NOT NULL,                  -- after enrolment
  identity TEXT NOT NULL REFERENCES identities(key),
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  PRIMARY KEY (sequence, step)
);

CREATE TABLE enrollments (
  subscriber_id INTEGER NOT NULL REFERENCES subscribers(id) ON DELETE CASCADE,
  sequence TEXT NOT NULL REFERENCES sequences(key) ON DELETE CASCADE,
  enrolled_at TEXT NOT NULL,
  next_step INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'active',      -- active | done | stopped
  PRIMARY KEY (subscriber_id, sequence)
);

-- Every message, from queued to delivered. The mail program leases a batch (status
-- sending, lease_until), delivers it, and reports sent / failed / bounced.
CREATE TABLE outbox (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  subscriber_id INTEGER REFERENCES subscribers(id) ON DELETE SET NULL,
  to_email TEXT NOT NULL,
  identity TEXT NOT NULL REFERENCES identities(key),
  kind TEXT NOT NULL,                         -- confirm | transactional | campaign | sequence
  campaign_id INTEGER REFERENCES campaigns(id) ON DELETE SET NULL,
  sequence TEXT,
  step INTEGER,
  subject TEXT NOT NULL,
  html TEXT NOT NULL,
  text TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued',      -- queued | sending | sent | failed | bounced | cancelled
  attempts INTEGER NOT NULL DEFAULT 0,
  lease_until TEXT,
  message_id TEXT,
  error TEXT,
  created_at TEXT NOT NULL,
  sent_at TEXT
);
CREATE INDEX outbox_status ON outbox(status, created_at);
CREATE INDEX outbox_campaign ON outbox(campaign_id);

-- What happened to a message after it left: opened, clicked, bounced, complained,
-- unsubscribed. Opens are a lower bound (many readers block images); clicks are counted
-- by a redirect on this domain.
CREATE TABLE email_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  outbox_id INTEGER REFERENCES outbox(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,
  detail TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX email_events_outbox ON email_events(outbox_id, kind);

-- ---------------------------------------------------------------- analytics

-- One row per page view. visitor_id / session_id are random first-party ids (no name, no
-- email, no cross-site anything); a browser sending Global Privacy Control or Do Not Track
-- is counted without them.
CREATE TABLE visits (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  visitor_id TEXT,
  session_id TEXT,
  path TEXT NOT NULL,
  referrer_host TEXT,
  utm_source TEXT,
  utm_medium TEXT,
  utm_campaign TEXT,
  utm_content TEXT,
  country TEXT,
  device TEXT                                 -- mobile | tablet | desktop
);
CREATE INDEX visits_ts ON visits(ts);
CREATE INDEX visits_visitor ON visits(visitor_id, ts);

-- The steps that matter, recorded by the server when they happen, tied to the visitor so
-- every sale and signup can be traced to the source that brought it.
CREATE TABLE conversions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  visitor_id TEXT,
  kind TEXT NOT NULL,                         -- subscribe | sample | signup | checkout | purchase | listing | backer
  ref TEXT,
  value_cents INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX conversions_ts ON conversions(ts, kind);
CREATE INDEX conversions_visitor ON conversions(visitor_id);

-- which visitor started each order, so a sale is credited to the source that brought it
ALTER TABLE orders ADD COLUMN visitor_id TEXT;
