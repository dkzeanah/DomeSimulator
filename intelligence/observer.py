"""Record one Claude Code hook event.

:func:`record` is the whole job: redact the event, append it to ``events`` and
to the day's JSONL, then fold it into the relational picture --

    SessionStart        -> sessions
    UserPromptSubmit    -> prompts (+ repository state at that moment)
    PreToolUse          -> actions   (status 'started')
    PostToolUse         -> actions   (status 'success') + observations
    PostToolUseFailure  -> actions   (status 'failure') + observations
    Stop                -> prompts.final_response, then episodes (rebuilt)
    SessionEnd          -> sessions.ended_at; open actions become 'orphaned'

It never raises to its caller in normal use (the hook wraps it anyway), never
prints, and keeps to the standard library so a hook stays fast.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime

from . import normalize as nz
from .database import PROJECT_ROOT, RAW_DIR, connect, now

#: Cap on one stored event payload (the JSONL copy uses the same redacted text).
PAYLOAD_LIMIT = 200_000
#: Cap on a tool result kept in ``observations``.
RESULT_LIMIT = 20_000
#: Cap on a prompt or final response kept inline.
TEXT_LIMIT = 50_000
#: How many dirty paths to keep as a sample of repository state.
DIRTY_SAMPLE = 40
#: Examples kept per vocabulary entry.
EXAMPLE_LIMIT = 12

DOTENV_NOTE = "<NOT INGESTED: .env content>"


# ----------------------------------------------------------------------
# Repository state
# ----------------------------------------------------------------------

def _git(*args: str, timeout: float = 3.0) -> str | None:
    """Run one read-only git command in the project; None on any failure."""
    try:
        result = subprocess.run(["git", *args], cwd=str(PROJECT_ROOT), capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=timeout,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def git_state(with_status: bool) -> dict:
    """Commit, branch and (optionally) the changed/untracked files."""
    state = {"commit": _git("rev-parse", "HEAD"),
             "branch": _git("rev-parse", "--abbrev-ref", "HEAD")}
    if with_status:
        porcelain = _git("status", "--porcelain", "--untracked-files=normal", timeout=6.0)
        lines = [line for line in (porcelain or "").splitlines() if line.strip()]
        state["dirty_count"] = len(lines) if porcelain is not None else None
        state["dirty_sample"] = [line[3:] for line in lines[:DIRTY_SAMPLE]]
    return state


# ----------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------

def _guard_dotenv(event: dict) -> dict:
    """Never keep .env contents: blank the response of any tool call that
    reads or prints a .env file. Returns a shallow-copied event."""
    event = dict(event)
    tool_input = event.get("tool_input") if isinstance(event.get("tool_input"), dict) else {}
    probe = " ".join(str(tool_input.get(k, "")) for k in ("file_path", "command", "path", "pattern"))
    if nz.mentions_dotenv(probe):
        for key in ("tool_response", "tool_result", "output"):
            if key in event:
                event[key] = DOTENV_NOTE
    return event


def _event_duration(ev: dict) -> int | None:
    """Tool execution time the event reports. Claude Code sends ``duration_ms``
    (the docs' example shows ``duration``); accept either."""
    for key in ("duration_ms", "duration"):
        value = ev.get(key)
        if isinstance(value, (int, float)):
            return int(value)
    return None


def _ms_between(start: str | None, end: str) -> int | None:
    """Milliseconds between two ISO timestamps, or None."""
    if not start:
        return None
    try:
        return int((datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds() * 1000)
    except ValueError:
        return None


def _resolve_prompt(conn, event: dict) -> tuple[str | None, str | None]:
    """The prompt this event belongs to: Claude's prompt_id when present,
    else the most recent prompt of the session."""
    if event.get("prompt_id"):
        return str(event["prompt_id"]), "claude"
    session = event.get("session_id")
    if not session:
        return None, None
    row = conn.execute("SELECT prompt_id FROM prompts WHERE session_id = ? "
                       "ORDER BY submitted_at DESC LIMIT 1", (session,)).fetchone()
    return (row["prompt_id"], "resolved") if row else (None, None)


_ARTIFACT = re.compile(r"(?i)(?:saved|wrote|written|created|exported|->)\s+['\"]?"
                       r"([^\s'\"]+\.(?:mp4|png|jpg|pdf|html|srt|json|csv|sqlite3|md))")


def _artifacts(text: str) -> list[str]:
    """Best-effort list of files a command says it produced."""
    return sorted({nz.symbolize(m.group(1)) for m in _ARTIFACT.finditer(text or "")})[:20]


def _touch_files(conn, paths: list[str], how: str, action_id: int, at: str) -> None:
    """Count a read/edit/search against each file."""
    column = {"read": "read_count", "edit": "edit_count", "search": "search_count"}.get(how)
    if not column:
        return
    for path in paths:
        conn.execute("INSERT OR IGNORE INTO files (path, first_seen) VALUES (?, ?)", (path, at))
        conn.execute(f"UPDATE files SET {column} = {column} + 1, last_seen = ?, "
                     f"last_action_id = ? WHERE path = ?", (at, action_id, path))


def _count_vocabulary(conn, name: str, tool_name: str, example: str, success: bool | None) -> None:
    """Keep the vocabulary live: create observed entries, bump counts, keep examples."""
    spec = nz.spec_for(name)
    conn.execute(
        "INSERT OR IGNORE INTO action_vocabulary (name, category, executor, pattern, purpose, "
        "risk, success_signal, examples, source, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (name, spec.category, tool_name.lower(), nz.generalize(example), spec.purpose, spec.risk,
         spec.success_signal, "[]", "observed", now()))
    row = conn.execute("SELECT examples, source FROM action_vocabulary WHERE name = ?",
                       (name,)).fetchone()
    examples = json.loads(row["examples"] or "[]")
    pattern = nz.generalize(example)
    if pattern and pattern not in examples and len(examples) < EXAMPLE_LIMIT:
        examples.append(pattern)
    source = row["source"] or "observed"
    if "observed" not in source:
        source = f"{source}+observed"
    conn.execute(
        "UPDATE action_vocabulary SET examples = ?, source = ?, updated_at = ?, "
        "observation_count = observation_count + 1, "
        "success_count = success_count + ?, failure_count = failure_count + ? WHERE name = ?",
        (json.dumps(examples), source, now(), 1 if success else 0,
         1 if success is False else 0, name))


# ----------------------------------------------------------------------
# Per-event handlers
# ----------------------------------------------------------------------

def _on_session_start(conn, ev: dict, at: str) -> None:
    conn.execute("UPDATE sessions SET source = ?, model = ?, started_at = COALESCE(started_at, ?) "
                 "WHERE session_id = ?",
                 (ev.get("source"), ev.get("model"), at, ev.get("session_id")))


def _on_prompt(conn, ev: dict, at: str, prompt_id: str, git: dict) -> None:
    prompt = nz.cap(ev.get("prompt") or "", TEXT_LIMIT)
    # A placeholder may exist if a tool event outran this one; fill it in.
    conn.execute("DELETE FROM prompts WHERE prompt_id = ? AND synthetic_id = 2 AND prompt_text IS NULL",
                 (prompt_id,))
    conn.execute(
        "INSERT OR IGNORE INTO prompts (prompt_id, session_id, prompt_text, prompt_length, "
        "submitted_at, git_commit, git_branch, git_dirty_count, git_dirty_sample, "
        "permission_mode, synthetic_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (prompt_id, ev.get("session_id"), prompt.text, prompt.length, at, git.get("commit"),
         git.get("branch"), git.get("dirty_count"), json.dumps(git.get("dirty_sample", [])),
         ev.get("permission_mode"), 0 if ev.get("prompt_id") else 1))
    conn.execute("INSERT INTO text_index (kind, ref, body) VALUES ('prompt', ?, ?)",
                 (prompt_id, prompt.text[:5000]))


def _on_pre_tool(conn, ev: dict, at: str, prompt_id: str | None) -> None:
    tool, tool_input = ev.get("tool_name") or "", ev.get("tool_input")
    name = nz.classify_tool(tool, tool_input)
    described = nz.describe_input(tool, tool_input)
    seq = conn.execute("SELECT COUNT(*) FROM actions WHERE prompt_id IS ?", (prompt_id,)).fetchone()[0]
    cur = conn.execute(
        "INSERT OR IGNORE INTO actions (session_id, prompt_id, tool_use_id, tool_name, "
        "normalized_action, generalized, raw_input, status, started_at, agent_id, sequence_no) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (ev.get("session_id"), prompt_id, ev.get("tool_use_id"), tool, name,
         nz.generalize(described), nz.cap(nz.to_text(tool_input), RESULT_LIMIT).text, "started",
         at, ev.get("agent_id"), seq + 1))
    if cur.rowcount:
        paths, how = nz.touched_files(tool, tool_input)
        _touch_files(conn, paths, how, cur.lastrowid, at)
        conn.execute("INSERT INTO text_index (kind, ref, body) VALUES ('action', ?, ?)",
                     (str(cur.lastrowid), f"{name} {nz.symbolize(described)[:2000]}"))


def _on_post_tool(conn, ev: dict, at: str, prompt_id: str | None, failed: bool) -> None:
    tool_use_id = ev.get("tool_use_id")
    row = conn.execute("SELECT * FROM actions WHERE tool_use_id = ?", (tool_use_id,)).fetchone() \
        if tool_use_id else None
    if row is None:                      # observer missed the PreToolUse: open it now
        _on_pre_tool(conn, ev, at, prompt_id)
        row = conn.execute("SELECT * FROM actions WHERE tool_use_id = ?", (tool_use_id,)).fetchone()
        if row is None:
            return
    duration = _event_duration(ev)
    duration_ms = duration if duration is not None else _ms_between(row["started_at"], at)
    response = nz.to_text(ev.get("tool_response"))
    capped = nz.cap(response, RESULT_LIMIT)
    error = ev.get("error")
    # A tool that "succeeds" but reports a non-zero exit in its response is
    # still recorded as success here: the hook said so. Analysis may revisit it.
    status = "failure" if failed else "success"
    conn.execute("UPDATE actions SET status = ?, completed_at = ?, duration_ms = ? "
                 "WHERE action_id = ?", (status, at, duration_ms, row["action_id"]))
    paths, how = nz.touched_files(row["tool_name"], ev.get("tool_input"))
    conn.execute(
        "INSERT INTO observations (action_id, tool_use_id, success, result_text, result_length, "
        "result_sha256, truncated, error, error_code, changed_files, artifacts, observed_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (row["action_id"], tool_use_id, 0 if failed else 1, capped.text, capped.length,
         capped.sha256, int(capped.truncated),
         nz.cap(nz.to_text(error), 4000).text if error else None, ev.get("error_code"),
         json.dumps(paths if how == "edit" else []), json.dumps(_artifacts(response)), at))
    _count_vocabulary(conn, row["normalized_action"], row["tool_name"] or "",
                      nz.describe_input(row["tool_name"] or "", ev.get("tool_input")),
                      success=not failed)
    if failed:
        conn.execute("INSERT INTO text_index (kind, ref, body) VALUES ('failure', ?, ?)",
                     (str(row["action_id"]), f"{row['normalized_action']} {nz.to_text(error)[:2000]}"))
    # Tool hooks run async, so a result can arrive after the request's Stop has
    # already built its episode; rebuild it so the episode is never short.
    stopped = conn.execute("SELECT stopped_at FROM prompts WHERE prompt_id = ?",
                           (row["prompt_id"],)).fetchone()
    if stopped and stopped["stopped_at"]:
        from .build_episode import build
        build(conn, row["prompt_id"])


def _on_stop(conn, ev: dict, at: str, prompt_id: str | None) -> None:
    if not prompt_id:
        return
    final = nz.cap(ev.get("last_assistant_message") or "", TEXT_LIMIT)
    conn.execute("UPDATE prompts SET stopped_at = ?, final_response = ? WHERE prompt_id = ?",
                 (at, final.text or None, prompt_id))
    from .build_episode import build          # imported late: only Stop needs it
    build(conn, prompt_id)


def _on_session_end(conn, ev: dict, at: str) -> None:
    conn.execute("UPDATE sessions SET ended_at = ?, end_reason = ? WHERE session_id = ?",
                 (at, ev.get("reason"), ev.get("session_id")))
    conn.execute("UPDATE actions SET status = 'orphaned' WHERE session_id = ? AND status = 'started'",
                 (ev.get("session_id"),))


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

def record(event: dict, conn=None) -> int:
    """Store one hook event and everything it implies. Returns its event_id."""
    at = now()
    name = event.get("hook_event_name") or "Unknown"
    clean = nz.redact(_guard_dotenv(event))
    payload = json.dumps(clean, ensure_ascii=False, default=str)
    capped = nz.cap(payload, PAYLOAD_LIMIT)

    own = conn is None
    conn = conn or connect()
    try:
        with conn:                                   # one transaction per event
            prompt_id, prompt_source = _resolve_prompt(conn, clean)
            # A new request with no prompt_id from Claude Code gets a minted one;
            # resolving it to the previous prompt would merge two requests.
            if name == "UserPromptSubmit" and prompt_source != "claude":
                n = conn.execute("SELECT COUNT(*) FROM prompts WHERE session_id = ?",
                                 (clean.get("session_id"),)).fetchone()[0]
                prompt_id, prompt_source = f"{clean.get('session_id')}#{n + 1}", "resolved"
            # A request whose UserPromptSubmit was never seen (the observer was
            # installed mid-turn, or that hook failed): keep its actions together
            # under a placeholder prompt, marked synthetic_id = 2 ("joined late").
            if prompt_id and prompt_source == "claude" and name != "UserPromptSubmit":
                conn.execute("INSERT OR IGNORE INTO prompts (prompt_id, session_id, submitted_at, "
                             "permission_mode, synthetic_id) VALUES (?,?,?,?,2)",
                             (prompt_id, clean.get("session_id"), at, clean.get("permission_mode")))
            git = git_state(with_status=(name == "UserPromptSubmit")) \
                if name in ("SessionStart", "UserPromptSubmit", "Stop") else {}
            duration = _event_duration(clean)
            cur = conn.execute(
                "INSERT INTO events (received_at, session_id, prompt_id, prompt_id_source, "
                "hook_event_name, cwd, permission_mode, transcript_path, scratchpad_dir, agent_id, "
                "agent_type, tool_name, tool_use_id, duration_ms, git_commit, git_branch, "
                "payload_json, payload_length, payload_sha256, truncated) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (at, clean.get("session_id"), prompt_id, prompt_source, name, clean.get("cwd"),
                 clean.get("permission_mode"), clean.get("transcript_path"),
                 clean.get("scratchpad_dir"), clean.get("agent_id"), clean.get("agent_type"),
                 clean.get("tool_name"), clean.get("tool_use_id"), duration,
                 git.get("commit"), git.get("branch"), capped.text, capped.length,
                 capped.sha256, int(capped.truncated)))
            event_id = cur.lastrowid

            session = clean.get("session_id")
            if session:
                conn.execute(
                    "INSERT OR IGNORE INTO sessions (session_id, started_at, cwd, transcript_path, "
                    "permission_mode) VALUES (?,?,?,?,?)",
                    (session, at, clean.get("cwd"), clean.get("transcript_path"),
                     clean.get("permission_mode")))
                conn.execute("UPDATE sessions SET last_event_at = ?, event_count = event_count + 1, "
                             "permission_mode = COALESCE(?, permission_mode) WHERE session_id = ?",
                             (at, clean.get("permission_mode"), session))

            if name == "SessionStart":
                _on_session_start(conn, clean, at)
            elif name == "UserPromptSubmit":
                _on_prompt(conn, clean, at, prompt_id, git)
            elif name == "PreToolUse":
                _on_pre_tool(conn, clean, at, prompt_id)
            elif name == "PostToolUse":
                _on_post_tool(conn, clean, at, prompt_id, failed=False)
            elif name == "PostToolUseFailure":
                _on_post_tool(conn, clean, at, prompt_id, failed=True)
            elif name == "Stop":
                _on_stop(conn, clean, at, prompt_id)
            elif name == "SessionEnd":
                _on_session_end(conn, clean, at)
    finally:
        if own:
            conn.close()

    # Recovery copy, outside the transaction: a JSONL failure must not lose the row.
    try:
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        with open(RAW_DIR / f"{at[:10]}.jsonl", "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"event_id": event_id, "received_at": at,
                                     "prompt_id": prompt_id, "event": capped.text},
                                    ensure_ascii=False) + "\n")
    except OSError:
        pass
    return event_id
