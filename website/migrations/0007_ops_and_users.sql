-- The site's own operations: automations that fire on what happens (a sale, a confirmation,
-- a new pad) or on a clock, the jobs they make, the owner's notices, an audit trail of
-- every change made by a person, an agent or an automation -- and the account controls
-- members and the owner need: suspension, sessions they can see and end, password resets,
-- a brake on password guessing.

-- ---------------------------------------------------------------- accounts

ALTER TABLE users ADD COLUMN status TEXT NOT NULL DEFAULT 'active';   -- active | suspended
ALTER TABLE users ADD COLUMN suspended_reason TEXT;
ALTER TABLE users ADD COLUMN last_seen_at TEXT;
ALTER TABLE users ADD COLUMN email_verified_at TEXT;
ALTER TABLE users ADD COLUMN admin_note TEXT;                          -- the owner's own note; never shown to the member

ALTER TABLE sessions ADD COLUMN last_seen_at TEXT;
ALTER TABLE sessions ADD COLUMN user_agent TEXT;                      -- shortened, so a member can tell their devices apart
ALTER TABLE sessions ADD COLUMN country TEXT;

-- Single-use links: password reset (1 hour) and email verification (3 days). Only the hash is kept.
CREATE TABLE user_tokens (
  token_hash TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  purpose TEXT NOT NULL,                      -- reset | verify
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  used_at TEXT
);
CREATE INDEX user_tokens_user ON user_tokens(user_id, purpose);

-- Every sign-in attempt, kept 30 days: too many misses for one address or one network and
-- the door waits fifteen minutes. The network is kept only as a salted hash.
CREATE TABLE login_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL,
  ip_hash TEXT,
  ok INTEGER NOT NULL,
  ts TEXT NOT NULL
);
CREATE INDEX login_attempts_email ON login_attempts(email, ts);
CREATE INDEX login_attempts_ip ON login_attempts(ip_hash, ts);

-- Who changed what: the owner, an agent key, an automation, or the site itself.
CREATE TABLE audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  actor_kind TEXT NOT NULL,                   -- user | agent | automation | system
  actor_id INTEGER,
  actor_name TEXT,
  action TEXT NOT NULL,                       -- e.g. user.suspend, proposal.approve, automation.edit
  target TEXT,                                -- e.g. user:12, listing:4
  detail TEXT
);
CREATE INDEX audit_log_ts ON audit_log(ts);
CREATE INDEX audit_log_target ON audit_log(target);

-- ---------------------------------------------------------------- operations

-- What happened, as the automations see it.
CREATE TABLE ops_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  type TEXT NOT NULL,                         -- subscriber.created, order.paid, schedule.daily ...
  data TEXT NOT NULL,                         -- JSON
  created_at TEXT NOT NULL
);
CREATE INDEX ops_events_type ON ops_events(type, created_at);

-- When THIS happens (and these fields match), do THESE things -- now or after a delay.
CREATE TABLE automations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT,
  trigger TEXT NOT NULL,                      -- an event type
  conditions TEXT NOT NULL DEFAULT '{}',      -- JSON: field equals value; "field_min" for at least
  actions TEXT NOT NULL,                      -- JSON array of {type, ...}
  delay_minutes INTEGER NOT NULL DEFAULT 0,
  active INTEGER NOT NULL DEFAULT 0,
  runs INTEGER NOT NULL DEFAULT 0,
  last_run_at TEXT,
  created_by TEXT,                            -- seed | owner | agent:<name>
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX automations_trigger ON automations(trigger, active);

-- One firing of one automation. The table is the truth; the clock only finds what is due.
CREATE TABLE jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  automation_id INTEGER REFERENCES automations(id) ON DELETE SET NULL,
  event_id INTEGER REFERENCES ops_events(id) ON DELETE SET NULL,
  label TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued',      -- queued | running | done | failed | cancelled
  attempts INTEGER NOT NULL DEFAULT 0,
  run_at TEXT NOT NULL,
  started_at TEXT,
  finished_at TEXT,
  result TEXT,                                -- JSON: one line per action
  error TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX jobs_due ON jobs(status, run_at);

-- The owner's inbox on the site: sales, proposals waiting, the weekly report, failures.
CREATE TABLE notices (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  level TEXT NOT NULL DEFAULT 'info',         -- info | action | warning
  title TEXT NOT NULL,
  body TEXT,
  link TEXT,
  created_at TEXT NOT NULL,
  read_at TEXT
);
CREATE INDEX notices_unread ON notices(read_at, created_at);

-- Every Workers AI call: what for, which model, how long. The owner can see what it costs.
CREATE TABLE ai_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  purpose TEXT NOT NULL,
  model TEXT NOT NULL,
  input_chars INTEGER NOT NULL,
  output_chars INTEGER NOT NULL DEFAULT 0,
  ms INTEGER NOT NULL,
  ok INTEGER NOT NULL,
  error TEXT,
  created_at TEXT NOT NULL
);

-- Small switches the owner sets on the admin page, and the clock's own bookkeeping.
CREATE TABLE settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

-- ---------------------------------------------------------------- the starting automations
-- Owner-facing and safe: they notify, tag, report and check. None sends marketing mail;
-- the one that drafts an update only drafts it, and starts switched off.

INSERT INTO automations(name, description, trigger, conditions, actions, delay_minutes, active, created_by, created_at, updated_at) VALUES
('Tell me about every sale', 'A notice on the admin page (and to your email once the mail server runs) for each paid order.',
 'order.paid', '{}', '[{"type":"notify","title":"Sold: {{product}}","body":"{{amount}} -- order {{ref}}. Source: {{source}}.","email":true,"level":"info","link":"/admin"}]', 0, 1, 'seed', '2026-10-14T00:00:00Z', '2026-10-14T00:00:00Z'),
('Tag every buyer', 'Adds buyer:<product> to the buyer''s list entry, so updates can go to buyers of one book.',
 'order.paid', '{}', '[{"type":"tag","tag":"buyer:{{product}}"}]', 0, 1, 'seed', '2026-10-14T00:00:00Z', '2026-10-14T00:00:00Z'),
('Agent proposals need you', 'When an agent proposes sending mail or changing a price, you get a notice to approve or reject it.',
 'proposal.created', '{}', '[{"type":"notify","title":"An agent proposes: {{action}}","body":"{{key}}: {{reason}}","email":true,"level":"action","link":"/admin/agents"}]', 0, 1, 'seed', '2026-10-14T00:00:00Z', '2026-10-14T00:00:00Z'),
('Check new network listings', 'Workers AI reads each new listing. If it looks like spam it proposes hiding it; you decide.',
 'listing.created', '{}', '[{"type":"ai_review_listing"}]', 0, 1, 'seed', '2026-10-14T00:00:00Z', '2026-10-14T00:00:00Z'),
('Monday report', 'Every Monday: last week''s visitors, list, sales and mail, counted by the site, with a short reading by Workers AI.',
 'schedule.weekly', '{}', '[{"type":"report","days":7,"email":true}]', 0, 1, 'seed', '2026-10-14T00:00:00Z', '2026-10-14T00:00:00Z'),
('Welcome new members', 'A notice when someone makes an account.',
 'member.joined', '{}', '[{"type":"notify","title":"New member","body":"Someone made an account (source: {{source}}).","level":"info","link":"/admin/users"}]', 0, 1, 'seed', '2026-10-14T00:00:00Z', '2026-10-14T00:00:00Z'),
('Draft a monthly update', 'On the 1st, Workers AI drafts a build update from the month''s numbers. Saved as a DRAFT; nothing is sent.',
 'schedule.monthly', '{}', '[{"type":"ai_draft_campaign","identity":"donovan","brief":"A short, plain monthly build update for people on the list: what happened on the site this month, and one thing to read or watch next."}]', 0, 0, 'seed', '2026-10-14T00:00:00Z', '2026-10-14T00:00:00Z');
