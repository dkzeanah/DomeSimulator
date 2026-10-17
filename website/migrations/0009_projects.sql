-- The owner's projects and their tasks (2026-10-16): the book, the kids' book, the films,
-- the build, the campaign -- each with tasks on a board (to do, doing, blocked, done), due
-- dates, notes and a link to the deliverable or page the task is about. Staff only; nothing
-- here is public. None are seeded: the owner adds their own on Admin -> Projects.

CREATE TABLE projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'active',      -- active | paused | done
  colour TEXT NOT NULL DEFAULT 'gold',        -- one of the site's palette names, for the board's chips
  sort INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'todo',        -- todo | doing | blocked | done
  due_date TEXT,                              -- YYYY-MM-DD, the owner's own calendar day
  notes TEXT NOT NULL DEFAULT '',
  link TEXT,                                  -- a page on this site, a deliverable's address, or any https:// link
  assignee_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  sort INTEGER NOT NULL DEFAULT 0,
  created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  done_at TEXT
);
CREATE INDEX tasks_project ON tasks(project_id, status);
CREATE INDEX tasks_due ON tasks(status, due_date);
