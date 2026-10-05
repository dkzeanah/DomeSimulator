"""Reconstruct one user request as an episode.

    GOAL              the user prompt
    INITIAL STATE     commit, branch, changed files, mode, cwd -- when the request arrived
    CONTEXT ACCESSED  files read, searches, fetches, commands run
    ACTION TRAJECTORY the ordered tool calls, normalised
    OBSERVATIONS      the ordered results
    FINAL RESPONSE    Claude's last message
    OUTCOME           what the tool record alone can say (see outcome_of)

Episodes are DERIVED: rebuilt from the raw tables at every Stop, and by
``py -3.12 -m intelligence.build_episode --all`` whenever the rules change.

    py -3.12 -m intelligence.build_episode <prompt_id>
    py -3.12 -m intelligence.build_episode --all
"""

from __future__ import annotations

import argparse
import json

from . import normalize as nz
from .database import connect, now

#: Characters of each result kept inside the episode's observation list.
OBS_EXCERPT = 600


def outcome_of(actions: list, stopped: bool) -> str:
    """What can be said about the outcome from tool results alone.

    This is deliberately narrow: it says nothing about whether the user was
    satisfied, only how the tool calls ended.

        no_actions       answered without any tool call
        in_progress      calls still open and no Stop yet
        tools_clean      every call succeeded
        tools_recovered  something failed, and the last call succeeded
        tools_failed     the last call failed
    """
    if not actions:
        return "no_actions"
    if not stopped and any(a["status"] == "started" for a in actions):
        return "in_progress"
    failures = [a for a in actions if a["status"] == "failure"]
    if not failures:
        return "tools_clean"
    finished = [a for a in actions if a["status"] in ("success", "failure")]
    if finished and finished[-1]["status"] == "success":
        return "tools_recovered"
    return "tools_failed"


def build(conn, prompt_id: str) -> int | None:
    """(Re)build the episode for one prompt; returns its episode_id."""
    prompt = conn.execute("SELECT * FROM prompts WHERE prompt_id = ?", (prompt_id,)).fetchone()
    if prompt is None:
        return None
    actions = conn.execute("SELECT * FROM actions WHERE prompt_id = ? ORDER BY action_id",
                           (prompt_id,)).fetchall()
    obs_by_action = {}
    for row in conn.execute(
            "SELECT o.* FROM observations o JOIN actions a ON a.action_id = o.action_id "
            "WHERE a.prompt_id = ? ORDER BY o.observation_id", (prompt_id,)):
        obs_by_action.setdefault(row["action_id"], row)

    state = {"commit": prompt["git_commit"], "branch": prompt["git_branch"],
             "dirty_count": prompt["git_dirty_count"],
             "dirty_sample": json.loads(prompt["git_dirty_sample"] or "[]"),
             "permission_mode": prompt["permission_mode"]}
    session = conn.execute("SELECT cwd FROM sessions WHERE session_id = ?",
                           (prompt["session_id"],)).fetchone()
    if session:
        state["cwd"] = nz.symbolize(session["cwd"] or "")

    context = {"files_read": [], "files_edited": [], "searches": [], "web": [], "commands": []}
    trajectory, observations = [], []
    for a in actions:
        raw = {}
        try:
            raw = json.loads(a["raw_input"] or "{}")
        except (TypeError, ValueError):
            pass
        paths, how = nz.touched_files(a["tool_name"] or "", raw)
        if how == "read":
            context["files_read"] += paths
        elif how == "edit":
            context["files_edited"] += paths
        elif how == "search":
            context["searches"].append(nz.symbolize(str(raw.get("pattern", ""))))
        elif a["normalized_action"] in ("web.search", "web.fetch"):
            context["web"].append(str(raw.get("url") or raw.get("query") or ""))
        elif a["tool_name"] in ("Bash", "PowerShell"):
            context["commands"].append(a["generalized"])
        trajectory.append({"seq": a["sequence_no"], "action_id": a["action_id"],
                           "tool": a["tool_name"], "action": a["normalized_action"],
                           "input": a["generalized"], "status": a["status"],
                           "duration_ms": a["duration_ms"], "agent_id": a["agent_id"]})
        o = obs_by_action.get(a["action_id"])
        if o is not None:
            observations.append({"action_id": a["action_id"], "success": bool(o["success"]),
                                 "excerpt": (o["result_text"] or "")[:OBS_EXCERPT],
                                 "length": o["result_length"], "error": o["error"],
                                 "artifacts": json.loads(o["artifacts"] or "[]"),
                                 "changed_files": json.loads(o["changed_files"] or "[]")})
    for key in context:                       # de-duplicate, keep first-seen order
        context[key] = list(dict.fromkeys(x for x in context[key] if x))

    outcome = outcome_of(actions, stopped=bool(prompt["stopped_at"]))
    failures = sum(1 for a in actions if a["status"] == "failure")
    values = (prompt["session_id"], prompt["prompt_text"], json.dumps(state),
              json.dumps(context), json.dumps(trajectory), json.dumps(observations),
              prompt["final_response"], outcome, len(actions), failures,
              prompt["submitted_at"], prompt["stopped_at"], now())
    existing = conn.execute("SELECT episode_id FROM episodes WHERE prompt_id = ?",
                            (prompt_id,)).fetchone()
    if existing:
        conn.execute("UPDATE episodes SET session_id=?, goal=?, initial_state=?, context_accessed=?, "
                     "trajectory=?, observations=?, final_response=?, outcome=?, action_count=?, "
                     "failure_count=?, started_at=?, ended_at=?, built_at=? WHERE prompt_id=?",
                     values + (prompt_id,))
        return existing["episode_id"]
    cur = conn.execute("INSERT INTO episodes (session_id, goal, initial_state, context_accessed, "
                       "trajectory, observations, final_response, outcome, action_count, "
                       "failure_count, started_at, ended_at, built_at, prompt_id) "
                       "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values + (prompt_id,))
    return cur.lastrowid


def build_all(conn) -> int:
    """Rebuild every episode; returns how many."""
    ids = [r["prompt_id"] for r in conn.execute("SELECT prompt_id FROM prompts")]
    with conn:
        for prompt_id in ids:
            build(conn, prompt_id)
    return len(ids)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("prompt_id", nargs="?")
    parser.add_argument("--all", action="store_true", help="rebuild every episode")
    args = parser.parse_args(argv)
    conn = connect()
    try:
        if args.all or not args.prompt_id:
            print(f"rebuilt {build_all(conn)} episodes")
        else:
            with conn:
                print(f"episode {build(conn, args.prompt_id)}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
