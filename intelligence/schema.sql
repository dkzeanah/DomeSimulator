-- Project Intelligence Observer v1 -- the authoritative structured store.
--
-- Two layers, kept apart on purpose:
--   RAW      sessions, prompts, events, actions, observations, files
--            (what Claude Code reported; append-only or updated only to
--             record what later events revealed, e.g. a tool's completion)
--   DERIVED  episodes, action_vocabulary, procedures, knowledge,
--            knowledge_edges, symbols
--            (rebuilt by build_episode / analyze_actions / seed_actions;
--             always safe to delete and regenerate from the raw layer)
--
-- Every statement is idempotent so the schema can be applied on every run.

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------
-- RAW LAYER
-- ----------------------------------------------------------------------

-- One Claude Code session (a conversation), from SessionStart to SessionEnd.
CREATE TABLE IF NOT EXISTS sessions (
    session_id       TEXT PRIMARY KEY,
    started_at       TEXT,             -- first event seen (SessionStart, or the
                                       -- first event if the observer arrived late)
    ended_at         TEXT,             -- SessionEnd
    end_reason       TEXT,             -- SessionEnd.reason
    source           TEXT,             -- SessionStart.source: startup|resume|clear|compact|fork
    model            TEXT,             -- SessionStart.model
    cwd              TEXT,
    transcript_path  TEXT,
    permission_mode  TEXT,
    last_event_at    TEXT,
    event_count      INTEGER NOT NULL DEFAULT 0
);

-- One user request. prompt_id is Claude Code's when it supplies one; otherwise
-- a synthetic '<session_id>#<n>' key is minted at UserPromptSubmit.
CREATE TABLE IF NOT EXISTS prompts (
    prompt_id        TEXT PRIMARY KEY,
    session_id       TEXT,
    prompt_text      TEXT,
    prompt_length    INTEGER,
    submitted_at     TEXT,
    stopped_at       TEXT,             -- most recent Stop for this prompt
    final_response   TEXT,             -- Stop.last_assistant_message
    git_commit       TEXT,             -- repository state when the request arrived
    git_branch       TEXT,
    git_dirty_count  INTEGER,
    git_dirty_sample TEXT,             -- JSON list, first N changed/untracked paths
    permission_mode  TEXT,
    synthetic_id     INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS prompts_session ON prompts(session_id, submitted_at);

-- Every hook event, append-only, redacted and size-capped.
CREATE TABLE IF NOT EXISTS events (
    event_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    received_at      TEXT NOT NULL,
    session_id       TEXT,
    prompt_id        TEXT,             -- as supplied, or as resolved by the observer
    prompt_id_source TEXT,             -- 'claude' | 'resolved' | NULL
    hook_event_name  TEXT,
    cwd              TEXT,
    permission_mode  TEXT,
    transcript_path  TEXT,
    scratchpad_dir   TEXT,
    agent_id         TEXT,
    agent_type       TEXT,
    tool_name        TEXT,
    tool_use_id      TEXT,
    duration_ms      INTEGER,
    git_commit       TEXT,
    git_branch       TEXT,
    payload_json     TEXT NOT NULL,    -- the whole redacted event
    payload_length   INTEGER,          -- before truncation
    payload_sha256   TEXT,             -- of the redacted, untruncated payload
    truncated        INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS events_session ON events(session_id, event_id);
CREATE INDEX IF NOT EXISTS events_prompt ON events(prompt_id);
CREATE INDEX IF NOT EXISTS events_tool_use ON events(tool_use_id);

-- One attempted tool call: opened at PreToolUse, closed at PostToolUse(Failure).
CREATE TABLE IF NOT EXISTS actions (
    action_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id        TEXT,
    prompt_id         TEXT,
    tool_use_id       TEXT UNIQUE,
    tool_name         TEXT,
    normalized_action TEXT,            -- vocabulary name, e.g. python.syntax_check
    generalized       TEXT,            -- symbolised pattern, e.g. py -3.12 -m py_compile <PATH>
    raw_input         TEXT,            -- redacted JSON of tool_input
    status            TEXT,            -- started | success | failure | orphaned
    started_at        TEXT,
    completed_at      TEXT,
    duration_ms       INTEGER,
    agent_id          TEXT,
    sequence_no       INTEGER          -- order within the prompt
);
CREATE INDEX IF NOT EXISTS actions_prompt ON actions(prompt_id, sequence_no);
CREATE INDEX IF NOT EXISTS actions_name ON actions(normalized_action);

-- The result of an action.
CREATE TABLE IF NOT EXISTS observations (
    observation_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    action_id        INTEGER REFERENCES actions(action_id),
    tool_use_id      TEXT,
    success          INTEGER,          -- 1 success, 0 failure
    result_text      TEXT,             -- redacted, possibly truncated
    result_length    INTEGER,
    result_sha256    TEXT,
    truncated        INTEGER NOT NULL DEFAULT 0,
    error            TEXT,
    error_code       TEXT,
    changed_files    TEXT,             -- JSON list
    artifacts        TEXT,             -- JSON list of produced files (best effort)
    observed_at      TEXT
);
CREATE INDEX IF NOT EXISTS observations_action ON observations(action_id);

-- Files the agent touched, with how.
CREATE TABLE IF NOT EXISTS files (
    path             TEXT PRIMARY KEY, -- symbolised (<PROJECT_ROOT>/...)
    first_seen       TEXT,
    last_seen        TEXT,
    read_count       INTEGER NOT NULL DEFAULT 0,
    edit_count       INTEGER NOT NULL DEFAULT 0,
    search_count     INTEGER NOT NULL DEFAULT 0,
    last_action_id   INTEGER
);

-- ----------------------------------------------------------------------
-- DERIVED LAYER
-- ----------------------------------------------------------------------

-- One user request and everything Claude did answering it.
CREATE TABLE IF NOT EXISTS episodes (
    episode_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id         TEXT UNIQUE,
    session_id        TEXT,
    goal              TEXT,            -- the user prompt
    initial_state     TEXT,            -- JSON: git commit/branch/dirty, cwd, mode
    context_accessed  TEXT,            -- JSON: files read, searches, fetches
    trajectory        TEXT,            -- JSON: ordered actions
    observations      TEXT,            -- JSON: ordered results
    final_response    TEXT,
    outcome           TEXT,            -- see build_episode.outcome_of
    action_count      INTEGER,
    failure_count     INTEGER,
    started_at        TEXT,
    ended_at          TEXT,
    built_at          TEXT
);

-- The compact vocabulary of things the agent knows how to do.
CREATE TABLE IF NOT EXISTS action_vocabulary (
    name              TEXT PRIMARY KEY,
    category          TEXT,
    executor          TEXT,            -- tool family: bash, powershell, read, ...
    pattern           TEXT,            -- generalized command pattern
    purpose           TEXT,
    risk              TEXT,            -- low | medium | high
    success_signal    TEXT,
    examples          TEXT,            -- JSON list of raw examples (capped)
    observation_count INTEGER NOT NULL DEFAULT 0,
    success_count     INTEGER NOT NULL DEFAULT 0,
    failure_count     INTEGER NOT NULL DEFAULT 0,
    source            TEXT,            -- 'permissions' | 'observed' | 'permissions+observed'
    updated_at        TEXT
);

-- Repeated successful action sequences, stored structurally.
CREATE TABLE IF NOT EXISTS procedures (
    procedure_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT UNIQUE,
    steps               TEXT,          -- JSON list of vocabulary names, in order
    support_count       INTEGER,       -- occurrences
    session_count       INTEGER,       -- distinct sessions it occurred in
    success_rate        REAL,
    example_episode_ids TEXT,          -- JSON list
    created_at          TEXT,
    updated_at          TEXT
);

-- Knowledge with explicit provenance.
--   tier 0 OBSERVATION  directly observed
--   tier 1 RELATIONSHIP deterministic relation between known objects
--   tier 2 PROCEDURE    repeated / demonstrated working sequence
--   tier 3 EXPERIENCE   a historical problem -> action -> outcome
--   tier 4 DEDUCTION    inferred from facts; premises are kept
--   tier 5 STRATEGY     project policy learned from repeated procedures
CREATE TABLE IF NOT EXISTS knowledge (
    knowledge_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    tier               INTEGER NOT NULL CHECK (tier BETWEEN 0 AND 5),
    kind               TEXT,           -- generator that produced it
    subject            TEXT,           -- what it is about (action, file, procedure)
    claim              TEXT NOT NULL,
    confidence         REAL NOT NULL,
    provenance         TEXT NOT NULL,  -- 'observed' | 'derived' | 'deduced' | 'seeded'
    source_event_ids   TEXT,           -- JSON list
    source_episode_ids TEXT,           -- JSON list
    premises           TEXT,           -- JSON list of knowledge_ids (deductions only)
    verification       TEXT NOT NULL,  -- 'observed' | 'unverified' | 'confirmed' | 'refuted'
    created_at         TEXT,
    updated_at         TEXT,
    UNIQUE (tier, kind, subject)
);

CREATE TABLE IF NOT EXISTS knowledge_edges (
    edge_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    src_knowledge_id INTEGER REFERENCES knowledge(knowledge_id),
    dst_knowledge_id INTEGER REFERENCES knowledge(knowledge_id),
    relation         TEXT,             -- 'premise_of' | 'instance_of' | 'corrects'
    UNIQUE (src_knowledge_id, dst_knowledge_id, relation)
);

-- Reserved for repository indexing (v2): AST definitions, imports, callers.
CREATE TABLE IF NOT EXISTS symbols (
    symbol_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    path        TEXT,
    name        TEXT,
    qualname    TEXT,
    kind        TEXT,                  -- module | class | function | import
    line        INTEGER,
    parent      TEXT,
    indexed_at  TEXT
);

-- Exact-identifier search over prompts and commands (no embeddings in v1).
CREATE VIRTUAL TABLE IF NOT EXISTS text_index USING fts5(kind, ref, body);
