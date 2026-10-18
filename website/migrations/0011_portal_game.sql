-- The Portal world's game (2026-10-18; docs/portal-world.md): each member's progress, and the
-- public chat. A guest's progress lives in their browser until they make an account.

CREATE TABLE game_saves (
  user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  data TEXT NOT NULL,                       -- JSON: skills, hitpoints, inventory, quests, lore, badges, bar
  total_level INTEGER NOT NULL DEFAULT 0,   -- for a high-scores page later
  updated_at TEXT NOT NULL
);

-- Members write, everyone reads. Staff can remove a message (removed_by is kept).
CREATE TABLE game_chat (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  name TEXT NOT NULL,
  text TEXT NOT NULL,
  area TEXT NOT NULL DEFAULT 'public',
  created_at TEXT NOT NULL,
  removed_by INTEGER REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX game_chat_recent ON game_chat(area, id);
