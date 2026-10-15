-- Controlled access for LLMs and agents. An agent gets an API key the owner made, carrying
-- only the scopes the owner ticked; every call it makes is logged; anything that sends mail,
-- changes a price or touches money is not done but PROPOSED, and waits for the owner to
-- approve it on the admin page.

CREATE TABLE api_keys (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,                         -- what it is for, e.g. "Claude: weekly report"
  prefix TEXT NOT NULL UNIQUE,                -- the first characters, shown in lists and logs
  key_hash TEXT NOT NULL,                     -- SHA-256 of the key; the key itself is shown once
  scopes TEXT NOT NULL,                       -- JSON array, e.g. ["analytics:read","campaigns:draft"]
  rate_per_min INTEGER NOT NULL DEFAULT 30,
  created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT,                            -- NULL = until revoked
  last_used_at TEXT,
  revoked_at TEXT
);

-- Every call an agent makes, allowed or refused.
CREATE TABLE api_calls (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  key_id INTEGER REFERENCES api_keys(id) ON DELETE CASCADE,
  ts TEXT NOT NULL,
  method TEXT NOT NULL,
  path TEXT NOT NULL,
  status INTEGER NOT NULL,
  note TEXT
);
CREATE INDEX api_calls_key ON api_calls(key_id, ts);

-- What an agent proposed and is waiting on the owner: send a campaign, change a price.
CREATE TABLE agent_proposals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  key_id INTEGER REFERENCES api_keys(id) ON DELETE SET NULL,
  action TEXT NOT NULL,                       -- e.g. campaign.queue, price.set
  payload TEXT NOT NULL,                      -- JSON
  reason TEXT,                                -- the agent's own words for why
  status TEXT NOT NULL DEFAULT 'pending',     -- pending | approved | rejected | failed
  result TEXT,
  created_at TEXT NOT NULL,
  decided_at TEXT,
  decided_by INTEGER REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX agent_proposals_status ON agent_proposals(status, created_at);
