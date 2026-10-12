"""What the agent knows about how this project is actually worked.

The Project Intelligence Observer (``intelligence/``) records every tool call a
coding assistant makes in this repository. :mod:`intelligence.procedures`
turns those records into playbooks -- the project's repeated workflows, step
by step, with the commands used, how long each step takes and what failed.
This module hands that learning to the agent:

* :func:`sync` copies it into ``kb/learned.json`` (playbooks, action
  statistics, recurring failures, derived knowledge);
* :func:`summary` is the compact text put into the LLM planner's system
  prompt, so a planner such as DeepSeek plans the way the work is really done;
* the ``learned`` tool (registered in :mod:`project_agent.tools`) lets the
  agent, or the person chatting with it, ask for any part of it.

Reading only: the agent never writes to the observer's database.
"""

from __future__ import annotations

import json

from . import config

LEARNED_PATH = config.KB_DIR / "learned.json"


def _observer():
    """The observer's database, or None when it has never run here."""
    try:
        from intelligence import database
    except ImportError:
        return None
    if not database.DB_PATH.exists():
        return None
    return database.connect(init=False)


def collect() -> dict:
    """Everything worth knowing, read from the observer's store."""
    conn = _observer()
    if conn is None:
        return {"ok": False, "error": "no observer database (.intelligence/) yet"}
    try:
        from intelligence import procedures
        playbooks = procedures.load()
        top = [dict(r) for r in conn.execute(
            "SELECT normalized_action AS action, COUNT(*) AS runs, "
            "SUM(status='failure') AS failures, CAST(AVG(duration_ms) AS INTEGER) AS avg_ms "
            "FROM actions GROUP BY normalized_action ORDER BY runs DESC LIMIT 15")]
        failures = [dict(r) for r in conn.execute(
            "SELECT normalized_action AS action, substr(generalized, 1, 140) AS pattern, COUNT(*) AS times "
            "FROM actions WHERE status='failure' GROUP BY normalized_action, generalized "
            "ORDER BY times DESC LIMIT 10")]
        knowledge = [dict(r) for r in conn.execute(
            "SELECT tier, kind, subject, claim, confidence, verification FROM knowledge "
            "WHERE tier >= 2 ORDER BY tier, confidence DESC LIMIT 30")]
        counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                  for t in ("sessions", "episodes", "actions")}
    finally:
        conn.close()
    return {"ok": True, "counts": counts, "playbooks": playbooks, "top_actions": top,
            "failures": failures, "knowledge": knowledge}


def sync() -> dict:
    """Re-derive the playbooks and copy the learning into the agent's KB."""
    try:
        from intelligence import procedures
        procedures.run()
    except Exception as exc:  # noqa: BLE001 - a broken observer must not break the agent
        data = collect()
        data["warning"] = f"playbooks not re-derived: {type(exc).__name__}: {exc}"
    else:
        data = collect()
    config.ensure_dirs()
    LEARNED_PATH.write_text(json.dumps(data, indent=1, default=str), encoding="utf-8")
    return data


def load() -> dict:
    if LEARNED_PATH.exists():
        return json.loads(LEARNED_PATH.read_text(encoding="utf-8"))
    return collect()


def summary(data: dict | None = None, limit: int = 6) -> str:
    """A few lines for a system prompt: the playbooks and what tends to fail."""
    data = data or load()
    if not data.get("ok"):
        return "(nothing learned yet)"
    lines = [f"Observed: {data['counts']['episodes']} episodes, {data['counts']['actions']} actions."]
    for b in data.get("playbooks", [])[:limit]:
        steps = " -> ".join(s["step"] for s in b["steps"])
        lines.append(f"- playbook '{b['name']}' ({b['status']}, {b['episodes']} episodes): {steps}")
    for f in data.get("failures", [])[:3]:
        lines.append(f"- tends to fail: {f['action']} x{f['times']} ({f['pattern'][:80]})")
    return "\n".join(lines)


def query(kind: str = "all") -> dict:
    data = load()
    if not data.get("ok"):
        return {"ok": False, "error": data.get("error", "nothing learned yet")}
    if kind == "all":
        return {"ok": True, "summary": summary(data), "playbooks": [b["name"] for b in data["playbooks"]]}
    if kind == "playbooks":
        from intelligence import procedures
        return {"ok": True, "text": procedures.text(data["playbooks"]), "playbooks": data["playbooks"]}
    if kind in ("top_actions", "failures", "knowledge", "counts"):
        return {"ok": True, kind: data[kind]}
    return {"ok": False, "error": f"unknown kind {kind!r}"}
