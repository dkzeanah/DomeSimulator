"""Derive vocabulary statistics, procedures and tiered knowledge.

Reads only the raw layer (actions, observations, episodes) and rewrites the
derived layer, so it is safe to run any number of times.

    tier 0 OBSERVATION   per action: how often it was run, succeeded, failed
    tier 1 RELATIONSHIP  per file: which actions touched it, in which episodes
    tier 2 PROCEDURE     repeated, fully successful action sequences
    tier 3 EXPERIENCE    a failure in an episode, and what followed until it worked
    tier 4 DEDUCTION     reliability judgements, each pointing at its tier-0 premise
    tier 5 STRATEGY      procedures that recur across several sessions

Deductions and strategies are written ``verification = 'unverified'`` with
their premises listed and linked through knowledge_edges. Nothing derived is
ever written at tier 0.

    py -3.12 -m intelligence.analyze_actions
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict

from .build_episode import build_all
from .database import connect, now

#: Shortest and longest action sequence considered for a procedure.
NGRAM_MIN, NGRAM_MAX = 2, 4
#: A sequence must recur this often, in this many episodes, to be a procedure.
MIN_SUPPORT, MIN_EPISODES = 3, 2
#: A procedure seen in this many sessions becomes a strategy.
STRATEGY_SESSIONS = 3
#: Reliability deductions need at least this many observations.
MIN_FOR_DEDUCTION = 5
#: Actions that are pure looking-around; a procedure made only of these is noise.
PASSIVE = {"filesystem.read", "filesystem.search", "filesystem.list", "filesystem.check",
           "tool.load", "shell.echo", "process.wait", "process.inspect"}


def wilson_lower(successes: int, n: int, z: float = 1.96) -> float:
    """Lower bound of the 95% Wilson interval: a success rate that respects n."""
    if n == 0:
        return 0.0
    p = successes / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (centre - margin) / denom)


def upsert_knowledge(conn, tier: int, kind: str, subject: str, claim: str, confidence: float,
                     provenance: str, verification: str, events=(), episodes=(),
                     premises=()) -> int:
    """Insert or refresh one knowledge record keyed by (tier, kind, subject)."""
    at = now()
    row = conn.execute("SELECT knowledge_id FROM knowledge WHERE tier=? AND kind=? AND subject=?",
                       (tier, kind, subject)).fetchone()
    values = (claim, round(confidence, 4), provenance, json.dumps(list(events)[:50]),
              json.dumps(list(episodes)[:50]), json.dumps(list(premises)), verification, at)
    if row:
        conn.execute("UPDATE knowledge SET claim=?, confidence=?, provenance=?, source_event_ids=?, "
                     "source_episode_ids=?, premises=?, verification=?, updated_at=? "
                     "WHERE knowledge_id=?", values + (row["knowledge_id"],))
        kid = row["knowledge_id"]
    else:
        cur = conn.execute("INSERT INTO knowledge (claim, confidence, provenance, source_event_ids, "
                           "source_episode_ids, premises, verification, updated_at, tier, kind, "
                           "subject, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                           values + (tier, kind, subject, at))
        kid = cur.lastrowid
    for premise in premises:
        conn.execute("INSERT OR IGNORE INTO knowledge_edges (src_knowledge_id, dst_knowledge_id, "
                     "relation) VALUES (?,?, 'premise_of')", (premise, kid))
    return kid


def _event_ids_for(conn, tool_use_ids: list[str]) -> list[int]:
    """Event ids that recorded these tool calls (provenance for observations)."""
    if not tool_use_ids:
        return []
    marks = ",".join("?" * len(tool_use_ids[:200]))
    return [r[0] for r in conn.execute(
        f"SELECT event_id FROM events WHERE tool_use_id IN ({marks}) ORDER BY event_id",
        tool_use_ids[:200])]


def recount_vocabulary(conn) -> int:
    """Make vocabulary counts exactly match the actions table."""
    conn.execute("UPDATE action_vocabulary SET observation_count = 0, success_count = 0, "
                 "failure_count = 0")
    rows = conn.execute("SELECT normalized_action AS n, COUNT(*) AS c, "
                        "SUM(status='success') AS s, SUM(status='failure') AS f FROM actions "
                        "WHERE status IN ('success','failure') GROUP BY normalized_action").fetchall()
    for r in rows:
        conn.execute("INSERT OR IGNORE INTO action_vocabulary (name, source, examples, updated_at) "
                     "VALUES (?, 'observed', '[]', ?)", (r["n"], now()))
        conn.execute("UPDATE action_vocabulary SET observation_count=?, success_count=?, "
                     "failure_count=? WHERE name=?", (r["c"], r["s"], r["f"], r["n"]))
    return len(rows)


def tier0_observations(conn) -> dict[str, int]:
    """One observation record per action name. Returns name -> knowledge_id."""
    out = {}
    for r in conn.execute(
            "SELECT normalized_action AS n, COUNT(*) AS c, SUM(status='success') AS s, "
            "SUM(status='failure') AS f, GROUP_CONCAT(tool_use_id) AS ids FROM actions "
            "WHERE status IN ('success','failure') GROUP BY normalized_action"):
        ids = [x for x in (r["ids"] or "").split(",") if x]
        episodes = [e[0] for e in conn.execute(
            "SELECT DISTINCT e.episode_id FROM episodes e JOIN actions a ON a.prompt_id = e.prompt_id "
            "WHERE a.normalized_action = ? LIMIT 50", (r["n"],))]
        out[r["n"]] = upsert_knowledge(
            conn, 0, "action_outcomes", r["n"],
            f"{r['n']} was run {r['c']} times: {r['s']} succeeded, {r['f']} failed.",
            1.0, "observed", "observed", _event_ids_for(conn, ids), episodes)
    return out


def tier1_relationships(conn) -> int:
    """Which actions touched each edited file, and in which episodes."""
    count = 0
    for f in conn.execute("SELECT path, read_count, edit_count FROM files WHERE edit_count > 0"):
        rows = conn.execute(
            "SELECT DISTINCT a.normalized_action, e.episode_id FROM actions a "
            "LEFT JOIN episodes e ON e.prompt_id = a.prompt_id "
            "WHERE a.raw_input LIKE ?", (f"%{f['path'].split('/')[-1]}%",)).fetchall()
        names = sorted({r[0] for r in rows})
        episodes = sorted({r[1] for r in rows if r[1] is not None})
        upsert_knowledge(conn, 1, "file_actions", f["path"],
                         f"{f['path']} was read {f['read_count']} and edited {f['edit_count']} "
                         f"times; actions mentioning it: {', '.join(names) or 'none'}.",
                         1.0, "derived", "observed", (), episodes)
        count += 1
    return count


def _sequences(conn):
    """Per episode: (episode_id, session_id, [(name, status)]) with consecutive
    repeats of the same action collapsed."""
    for e in conn.execute("SELECT episode_id, session_id, trajectory FROM episodes"):
        steps, last = [], None
        for item in json.loads(e["trajectory"] or "[]"):
            if item.get("agent_id"):          # a subagent's calls are its own story
                continue
            key = item["action"]
            if key == last:
                if item["status"] == "failure":
                    steps[-1] = (key, "failure")
                continue
            steps.append((key, item["status"]))
            last = key
        yield e["episode_id"], e["session_id"], steps


def tier2_procedures(conn) -> dict[str, int]:
    """Mine repeated, fully successful sequences. Returns name -> knowledge_id."""
    support, episodes_of, sessions_of = Counter(), defaultdict(set), defaultdict(set)
    for episode_id, session_id, steps in _sequences(conn):
        for n in range(NGRAM_MIN, NGRAM_MAX + 1):
            for i in range(len(steps) - n + 1):
                window = steps[i:i + n]
                if any(status != "success" for _name, status in window):
                    continue
                names = tuple(name for name, _ in window)
                if all(name in PASSIVE for name in names) or len(set(names)) < 2:
                    continue
                support[names] += 1
                episodes_of[names].add(episode_id)
                sessions_of[names].add(session_id)
    out = {}
    at = now()
    for names, count in support.most_common():
        if count < MIN_SUPPORT or len(episodes_of[names]) < MIN_EPISODES:
            continue
        name = "procedure." + "_then_".join(n.split(".")[-1] for n in names)
        examples = sorted(episodes_of[names])[:10]
        conn.execute(
            "INSERT INTO procedures (name, steps, support_count, session_count, success_rate, "
            "example_episode_ids, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?) "
            "ON CONFLICT(name) DO UPDATE SET steps=excluded.steps, support_count=excluded.support_count, "
            "session_count=excluded.session_count, success_rate=excluded.success_rate, "
            "example_episode_ids=excluded.example_episode_ids, updated_at=excluded.updated_at",
            (name, json.dumps(list(names)), count, len(sessions_of[names]), 1.0,
             json.dumps(examples), at, at))
        out[name] = upsert_knowledge(
            conn, 2, "procedure", name,
            f"The sequence {' -> '.join(names)} completed without failure {count} times "
            f"in {len(episodes_of[names])} episodes.",
            min(1.0, count / (count + 2)), "derived", "observed", (), examples)
        out[name + "#sessions"] = len(sessions_of[names])
    return out


def tier3_experiences(conn) -> int:
    """Each failure inside an episode, with what happened until it worked again."""
    count = 0
    for e in conn.execute("SELECT episode_id, prompt_id, trajectory FROM episodes WHERE failure_count > 0"):
        trajectory = json.loads(e["trajectory"] or "[]")
        for i, step in enumerate(trajectory):
            if step["status"] != "failure":
                continue
            fix = next((j for j in range(i + 1, len(trajectory))
                        if trajectory[j]["action"] == step["action"]
                        and trajectory[j]["status"] == "success"), None)
            error = conn.execute("SELECT error, result_text FROM observations WHERE action_id = ?",
                                 (step["action_id"],)).fetchone()
            detail = ((error["error"] or error["result_text"] or "") if error else "")[:200]
            between = [t["action"] for t in trajectory[i + 1:fix]] if fix else []
            claim = (f"{step['action']} failed ({detail.strip() or 'no detail'})"
                     + (f"; it succeeded again after {len(between)} step(s): "
                        f"{', '.join(between) or 'an immediate retry'}." if fix is not None
                        else "; no later success in this episode."))
            events = _event_ids_for(conn, [r[0] for r in conn.execute(
                "SELECT tool_use_id FROM actions WHERE action_id = ?", (step["action_id"],))])
            upsert_knowledge(conn, 3, "failure_recovery", f"action:{step['action_id']}", claim,
                             1.0 if fix is not None else 0.5, "observed", "observed",
                             events, [e["episode_id"]])
            count += 1
    return count


def tier4_deductions(conn, observations: dict[str, int]) -> int:
    """Reliability judgements, each resting on its tier-0 premise."""
    count = 0
    for r in conn.execute("SELECT name, observation_count AS n, success_count AS s, "
                          "failure_count AS f FROM action_vocabulary WHERE observation_count >= ?",
                          (MIN_FOR_DEDUCTION,)):
        premise = observations.get(r["name"])
        if premise is None:
            continue
        low = wilson_lower(r["s"], r["n"])
        if low >= 0.8:
            verdict = f"{r['name']} is reliable here: at least {low:.0%} of runs succeed (95% bound)."
        elif r["f"] / r["n"] >= 0.3:
            verdict = (f"{r['name']} is failure-prone here: {r['f']} of {r['n']} runs failed; "
                       "check inputs before running it.")
            low = r["f"] / r["n"]
        else:
            continue
        upsert_knowledge(conn, 4, "reliability", r["name"], verdict, low, "deduced",
                         "unverified", premises=[premise])
        count += 1
    return count


def tier5_strategies(conn, procedures: dict[str, int]) -> int:
    """Procedures that recur across sessions become standing strategies."""
    count = 0
    for name, kid in procedures.items():
        if name.endswith("#sessions"):
            continue
        sessions = procedures.get(name + "#sessions", 0)
        if sessions < STRATEGY_SESSIONS:
            continue
        steps = json.loads(conn.execute("SELECT steps FROM procedures WHERE name = ?",
                                        (name,)).fetchone()[0])
        upsert_knowledge(conn, 5, "strategy", name,
                         f"When starting with {steps[0]}, this project usually continues "
                         f"{' -> '.join(steps[1:])} (seen in {sessions} sessions).",
                         min(1.0, sessions / (sessions + 2)), "deduced", "unverified",
                         premises=[kid])
        count += 1
    return count


def analyze(conn) -> dict:
    """Run every derivation in order; returns counts."""
    build_all(conn)
    with conn:
        report = {"vocabulary": recount_vocabulary(conn)}
        observations = tier0_observations(conn)
        report["tier0"] = len(observations)
        report["tier1"] = tier1_relationships(conn)
        procedures = tier2_procedures(conn)
        report["tier2"] = sum(1 for k in procedures if not k.endswith("#sessions"))
        report["tier3"] = tier3_experiences(conn)
        report["tier4"] = tier4_deductions(conn, observations)
        report["tier5"] = tier5_strategies(conn, procedures)
    return report


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args(argv)
    conn = connect()
    try:
        for key, value in analyze(conn).items():
            print(f"{key:<11} {value}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
