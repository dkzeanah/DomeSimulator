"""Look at what the observer has collected.

    py -3.12 -m intelligence.inspect status          where the data is, and how much
    py -3.12 -m intelligence.inspect sessions        recent sessions
    py -3.12 -m intelligence.inspect latest          the most recent episode, in full
    py -3.12 -m intelligence.inspect episode <id>    one episode (episode id or prompt id)
    py -3.12 -m intelligence.inspect actions         the action vocabulary with counts
    py -3.12 -m intelligence.inspect action <name>   one vocabulary entry, examples, recent runs
    py -3.12 -m intelligence.inspect failures        recent failed actions
    py -3.12 -m intelligence.inspect stats           counts by table, event and tier
    py -3.12 -m intelligence.inspect knowledge [tier] derived knowledge
    py -3.12 -m intelligence.inspect search <text>   full-text search of prompts, actions, failures

Read-only: nothing here writes to the database.
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap

from .database import DB_PATH, RAW_DIR, connect

TIER_NAMES = {0: "OBSERVATION", 1: "RELATIONSHIP", 2: "PROCEDURE", 3: "EXPERIENCE",
              4: "DEDUCTION", 5: "STRATEGY"}


def _short(text, width: int = 90) -> str:
    """One line, cut to width."""
    text = " ".join(str(text or "").split())
    return text if len(text) <= width else text[: width - 3] + "..."


def _block(text, width: int = 100, indent: str = "    ") -> str:
    """A wrapped, indented paragraph (blank text shows as a dash)."""
    text = str(text or "").strip()
    if not text:
        return indent + "-"
    return "\n".join(textwrap.fill(p, width, initial_indent=indent, subsequent_indent=indent)
                     for p in text.splitlines() if p.strip()) or indent + "-"


def cmd_status(conn, _args) -> None:
    counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ("sessions", "prompts", "events", "actions", "observations", "episodes",
                        "action_vocabulary", "procedures", "knowledge")}
    last = conn.execute("SELECT received_at, hook_event_name FROM events "
                        "ORDER BY event_id DESC LIMIT 1").fetchone()
    print(f"database   {DB_PATH}")
    print(f"raw jsonl  {RAW_DIR}")
    for key, value in counts.items():
        print(f"  {key:<18} {value:>7}")
    if last:
        print(f"last event {last['received_at']}  {last['hook_event_name']}")


def cmd_sessions(conn, args) -> None:
    for s in conn.execute("SELECT * FROM sessions ORDER BY COALESCE(last_event_at, started_at) "
                          "DESC LIMIT ?", (args.limit,)):
        prompts = conn.execute("SELECT COUNT(*) FROM prompts WHERE session_id = ?",
                               (s["session_id"],)).fetchone()[0]
        print(f"{s['session_id']}  started {s['started_at']}  last {s['last_event_at']}  "
              f"events {s['event_count']}  prompts {prompts}  "
              f"{'ended ' + (s['end_reason'] or '') if s['ended_at'] else 'open'}")


def show_episode(conn, episode) -> None:
    """Print one episode in the GOAL ... OUTCOME layout."""
    e = episode
    state = json.loads(e["initial_state"] or "{}")
    context = json.loads(e["context_accessed"] or "{}")
    trajectory = json.loads(e["trajectory"] or "[]")
    observations = {o["action_id"]: o for o in json.loads(e["observations"] or "[]")}
    print(f"EPISODE {e['episode_id']}   prompt {e['prompt_id']}   session {e['session_id']}")
    print(f"  {e['started_at']}  ->  {e['ended_at'] or '(not stopped)'}\n")
    print("GOAL")
    print(_block(e["goal"]))
    print("\nINITIAL STATE")
    print(f"    branch {state.get('branch')}  commit {str(state.get('commit'))[:12]}  "
          f"changed/untracked {state.get('dirty_count')}  mode {state.get('permission_mode')}")
    print("\nCONTEXT ACCESSED")
    for key, values in context.items():
        if values:
            print(f"    {key}: " + ", ".join(_short(v, 60) for v in values[:12])
                  + (f" (+{len(values) - 12})" if len(values) > 12 else ""))
    print("\nACTION TRAJECTORY  /  OBSERVATIONS")
    for step in trajectory:
        mark = {"success": "ok ", "failure": "ERR", "started": "...", "orphaned": "?? "}.get(
            step["status"], step["status"])
        dur = f"{step['duration_ms']} ms" if step.get("duration_ms") is not None else ""
        agent = f" [agent {step['agent_id'][:8]}]" if step.get("agent_id") else ""
        print(f"  {step['seq']:>3}. {mark} {step['action']:<22} {step['tool']:<11} "
              f"{_short(step['input'], 70)}  {dur}{agent}")
        o = observations.get(step["action_id"])
        if o:
            line = o["error"] or o["excerpt"]
            if line:
                print(f"         -> {_short(line, 100)}")
            if o.get("artifacts"):
                print(f"         -> artifacts: {', '.join(o['artifacts'][:4])}")
    print("\nFINAL RESPONSE")
    print(_block(e["final_response"]))
    print(f"\nOUTCOME  {e['outcome']}   ({e['action_count']} actions, {e['failure_count']} failed)")


def cmd_latest(conn, _args) -> None:
    e = conn.execute("SELECT * FROM episodes ORDER BY COALESCE(ended_at, started_at) DESC, "
                     "episode_id DESC LIMIT 1").fetchone()
    if e is None:
        print("no episodes yet")
        return
    show_episode(conn, e)


def cmd_episode(conn, args) -> None:
    key = args.id
    e = conn.execute("SELECT * FROM episodes WHERE prompt_id = ? OR CAST(episode_id AS TEXT) = ?",
                     (key, key)).fetchone()
    if e is None:
        print(f"no episode {key!r}")
        return
    show_episode(conn, e)


def cmd_actions(conn, _args) -> None:
    print(f"{'name':<26} {'risk':<6} {'seen':>5} {'ok':>5} {'fail':>5}  source")
    for v in conn.execute("SELECT * FROM action_vocabulary ORDER BY observation_count DESC, name"):
        print(f"{v['name']:<26} {v['risk'] or '':<6} {v['observation_count']:>5} "
              f"{v['success_count']:>5} {v['failure_count']:>5}  {v['source']}")


def cmd_action(conn, args) -> None:
    v = conn.execute("SELECT * FROM action_vocabulary WHERE name = ?", (args.name,)).fetchone()
    if v is None:
        print(f"no action {args.name!r}")
        return
    for key in ("name", "category", "executor", "pattern", "purpose", "risk", "success_signal",
                "observation_count", "success_count", "failure_count", "source", "updated_at"):
        print(f"{key:<18} {v[key]}")
    print("examples")
    for ex in json.loads(v["examples"] or "[]"):
        print(f"    {_short(ex, 110)}")
    print("recent runs")
    for a in conn.execute("SELECT action_id, status, started_at, duration_ms, generalized FROM actions "
                          "WHERE normalized_action = ? ORDER BY action_id DESC LIMIT 10", (args.name,)):
        print(f"    #{a['action_id']} {a['status']:<8} {a['started_at']} "
              f"{a['duration_ms'] or '':>7}  {_short(a['generalized'], 70)}")


def cmd_failures(conn, args) -> None:
    rows = conn.execute(
        "SELECT a.action_id, a.normalized_action, a.started_at, a.generalized, o.error, "
        "o.result_text FROM actions a LEFT JOIN observations o ON o.action_id = a.action_id "
        "WHERE a.status = 'failure' ORDER BY a.action_id DESC LIMIT ?", (args.limit,)).fetchall()
    if not rows:
        print("no failures recorded")
    for r in rows:
        print(f"#{r['action_id']} {r['started_at']} {r['normalized_action']}")
        print(f"    input  {_short(r['generalized'], 100)}")
        print(f"    error  {_short(r['error'] or r['result_text'], 100)}")


def cmd_stats(conn, _args) -> None:
    print("events by hook")
    for r in conn.execute("SELECT hook_event_name, COUNT(*) c FROM events GROUP BY 1 ORDER BY 2 DESC"):
        print(f"  {r[0]:<20} {r[1]:>7}")
    print("actions by status")
    for r in conn.execute("SELECT status, COUNT(*) FROM actions GROUP BY 1 ORDER BY 2 DESC"):
        print(f"  {r[0]:<20} {r[1]:>7}")
    print("top actions")
    for r in conn.execute("SELECT normalized_action, COUNT(*), CAST(AVG(duration_ms) AS INT) FROM actions "
                          "GROUP BY 1 ORDER BY 2 DESC LIMIT 15"):
        print(f"  {r[0]:<26} {r[1]:>6}   avg {r[2] or 0} ms")
    print("episodes by outcome")
    for r in conn.execute("SELECT outcome, COUNT(*) FROM episodes GROUP BY 1 ORDER BY 2 DESC"):
        print(f"  {r[0]:<20} {r[1]:>7}")
    print("knowledge by tier")
    for r in conn.execute("SELECT tier, COUNT(*) FROM knowledge GROUP BY 1 ORDER BY 1"):
        print(f"  {r[0]} {TIER_NAMES[r[0]]:<14} {r[1]:>7}")


def cmd_knowledge(conn, args) -> None:
    query = "SELECT * FROM knowledge" + (" WHERE tier = ?" if args.tier is not None else "") + \
        " ORDER BY tier, confidence DESC LIMIT ?"
    params = ((args.tier,) if args.tier is not None else ()) + (args.limit,)
    for k in conn.execute(query, params):
        premises = json.loads(k["premises"] or "[]")
        print(f"[{k['tier']} {TIER_NAMES[k['tier']]}] #{k['knowledge_id']} conf {k['confidence']:.2f} "
              f"{k['provenance']}/{k['verification']}"
              + (f"  premises {premises}" if premises else ""))
        print(_block(k["claim"], indent="    "))


def cmd_search(conn, args) -> None:
    text = " ".join(args.text)
    try:
        rows = conn.execute("SELECT kind, ref, snippet(text_index, 2, '[', ']', '...', 12) "
                            "FROM text_index WHERE text_index MATCH ? LIMIT ?",
                            (text, args.limit)).fetchall()
    except Exception:                       # malformed FTS query: fall back to a phrase
        rows = conn.execute("SELECT kind, ref, snippet(text_index, 2, '[', ']', '...', 12) "
                            "FROM text_index WHERE text_index MATCH ? LIMIT ?",
                            ('"' + text.replace('"', '') + '"', args.limit)).fetchall()
    for r in rows:
        print(f"{r[0]:<8} {r[1]:<40} {_short(r[2], 100)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd")
    for name in ("status", "latest", "actions", "stats"):
        sub.add_parser(name)
    for name in ("sessions", "failures"):
        p = sub.add_parser(name)
        p.add_argument("--limit", type=int, default=20)
    p = sub.add_parser("episode")
    p.add_argument("id")
    p = sub.add_parser("action")
    p.add_argument("name")
    p = sub.add_parser("knowledge")
    p.add_argument("tier", nargs="?", type=int)
    p.add_argument("--limit", type=int, default=40)
    p = sub.add_parser("search")
    p.add_argument("text", nargs="+")
    p.add_argument("--limit", type=int, default=20)
    args = parser.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    conn = connect()
    try:
        handler = globals().get(f"cmd_{args.cmd or 'status'}")
        handler(conn, args)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
