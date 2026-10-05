# Project Intelligence Observer v1

A passive recorder of how Claude Code understands, navigates, changes, runs,
tests and verifies this repository. It turns every Claude Code session into a
local SQLite dataset: what was asked, what Claude looked at, what it did, what
happened, and how the request ended. That dataset is meant to teach a smaller,
project-specific reasoning system later. It is not general LLM training data.

It never takes part in Claude's work. Its hooks print nothing, exit 0 whatever
happens, approve and deny nothing, and add no context. If the observer breaks,
Claude carries on, and the error goes to `.intelligence/logs/observer.log`.

## Where things are

| Path | What it is | In git? |
|---|---|---|
| `intelligence/` | this package (source) | yes |
| `.claude/hooks/intelligence_observer.py` | the hook entry point | yes |
| `.claude/settings.json` | hook registration (the only thing in it) | yes |
| `.intelligence/intelligence.sqlite3` | the authoritative store | **no** (gitignored) |
| `.intelligence/raw/YYYY-MM-DD.jsonl` | append-only recovery copy of every event | no |
| `.intelligence/logs/observer.log` | the observer's own errors, and slow-hook notes | no |

`.claude/settings.local.json` and its permission allow-list are only ever read,
to seed the vocabulary. Nothing writes to them.

## Hooks

Seven events are registered in `.claude/settings.json`, all running
`py -3.12 "${CLAUDE_PROJECT_DIR}/.claude/hooks/intelligence_observer.py"`
through Git Bash:

| Event | Mode | Records |
|---|---|---|
| SessionStart | sync | the session, its source and model |
| UserPromptSubmit | sync | the request, with git commit, branch and changed files at that moment |
| PreToolUse | **async** | the attempted action |
| PostToolUse | **async** | the result, with the time Claude Code reports |
| PostToolUseFailure | **async** | the failure and its error |
| Stop | sync | Claude's final message, then rebuilds the episode |
| SessionEnd | sync | the end, and any still-open actions marked `orphaned` |

**Why the tool hooks are async.** One hook call costs about 0.35 s, mostly
Python start-up. Run synchronously, that would add about 0.7 s to every tool
call. Async hooks can arrive out of order, so the recorder accepts a result
before its start, and a late result rebuilds its episode.

**Why the shell form, not `"args": [...]`.** The no-shell form needs a real
`.exe`. On this machine `py` is a Windows App Execution Alias (a 0-byte
reparse point). The desktop app launches it, but the `claude` CLI reports
"Executable not found in $PATH". Git Bash resolves it in both.

## The store

**Raw layer** (only ever appended, or updated to record what a later event revealed):

- `sessions`
- `prompts`
- `events`
- `actions`
- `observations`
- `files`

**Derived layer** (rebuildable at any time from the raw layer):

- `episodes`
- `action_vocabulary`
- `procedures`
- `knowledge`
- `knowledge_edges`
- `symbols` (reserved for AST indexing in v2)

**Search:** `text_index` is an FTS5 index of prompts, actions and failures.

### What happens to an event before it is stored

1. **`.env` is never ingested.** Any tool call whose path or command names a
   `.env` file has its response replaced with `<NOT INGESTED: .env content>`.
2. **Secrets are redacted**, recursively:
   - values under keys containing password, passwd, secret, token, api_key,
     apikey, authorization, bearer, credential or private_key;
   - `NAME=value` pairs with those names inside text;
   - `Bearer …` headers;
   - common provider key shapes (`sk-…`, `ghp_…`, `sk_live_…`, `AKIA…`).
3. **Size is capped.** An event payload is capped at 200,000 characters and a
   tool result at 20,000. Each keeps its original length, its SHA-256 and a
   truncation flag.

### Episodes

One user request, as:

- **GOAL**: the prompt.
- **INITIAL STATE**: commit, branch, changed files and permission mode.
- **CONTEXT ACCESSED**: files read, files edited, searches, web pages, commands.
- **ACTION TRAJECTORY**: the ordered actions.
- **OBSERVATIONS**: their results.
- **FINAL RESPONSE**: Claude's last message.
- **OUTCOME**: one of `no_actions`, `in_progress`, `tools_clean`,
  `tools_recovered` or `tools_failed`. It describes only how the tool calls
  ended, never whether the user was satisfied.

### Action vocabulary

A compact set of things the agent knows how to do: `python.syntax_check`,
`render.stills`, `book.check`, `git.commit`, `media.inspect` and so on. The
mapping is deterministic, by ordered rules in `normalize.py`:

- interpreters are recognised (`py`, `python`, `py -3.12`, venv pythons);
- wrappers are peeled off (`timeout N`, `powershell -c "…"`, `$p = …`,
  `FOO=1 cmd`);
- chained commands are split on `; && || |`, but never inside quotes, braces or
  parentheses, and the most significant piece names the action.

Paths are replaced with `<PROJECT_ROOT>`, `<CLAUDE_SCRATCHPAD>`, `<TEMP>` and
`<HOME>`. Numbers, hashes, UUIDs and long literals are generalised, so
variable arguments do not mint new entries.

### Knowledge tiers

| Tier | Name | Produced from | Verification |
|---|---|---|---|
| 0 | OBSERVATION | how often each action ran, succeeded and failed | observed |
| 1 | RELATIONSHIP | which actions touched each edited file, in which episodes | observed |
| 2 | PROCEDURE | sequences that ran fully successfully at least 3 times in at least 2 episodes | observed |
| 3 | EXPERIENCE | each failure in an episode, and what followed until it worked | observed |
| 4 | DEDUCTION | reliability judgements (Wilson 95% bound); **premises kept** and linked | unverified |
| 5 | STRATEGY | procedures that recur in at least 3 sessions | unverified |

Every record carries:

- tier and claim;
- confidence and provenance;
- source event and episode IDs;
- premises (for deductions);
- creation time and verification state.

A deduction is never written as an observation.

## Commands

```bash
py -3.12 -m intelligence.init              # create .intelligence/ and seed the vocabulary
py -3.12 -m intelligence.seed_actions      # re-import vocabulary from the permission list
py -3.12 -m intelligence.analyze_actions   # recount vocabulary, mine procedures, derive knowledge
py -3.12 -m intelligence.build_episode --all

py -3.12 -m intelligence.inspect status
py -3.12 -m intelligence.inspect sessions
py -3.12 -m intelligence.inspect latest
py -3.12 -m intelligence.inspect episode <episode id | prompt id>
py -3.12 -m intelligence.inspect actions
py -3.12 -m intelligence.inspect action python.syntax_check
py -3.12 -m intelligence.inspect failures
py -3.12 -m intelligence.inspect stats
py -3.12 -m intelligence.inspect knowledge [tier]
py -3.12 -m intelligence.inspect search py_compile
```

Set `INTELLIGENCE_DB=<path>` to point every command, and the hook, at a scratch
database.

## Turning it off

Delete the `hooks` block from `.claude/settings.json`, or the file itself.
Nothing else depends on it. To discard the data, delete `.intelligence/`.

## Left for v2

- **Repository indexing:** Python AST definitions, imports, callers and
  callees, entry points and validators, into `symbols`.
- **Joining with the record:** linking that index to the `files` usage history,
  with FTS over identifiers.
- **Better outcome signals:** a test that went from failing to passing, or the
  user's next message as a verdict on the last one.
