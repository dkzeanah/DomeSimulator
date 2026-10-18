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
  agent, or the person chatting with it, ask for any part of it;
* the lessons (:mod:`intelligence.lessons`) -- the owner's standing rules,
  every past request worked as an example, and what fixed each failure -- go in
  too: the rules into the system prompt, and, for each new request, the most
  similar past requests as worked examples (:func:`examples_for`, the
  ``recall`` tool).

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


def _lessons() -> dict:
    """The rules, recoveries and worked examples, read where the observer keeps them.

    Never copied into ``kb/learned.json``: that file is in git and the repository is
    public, while the examples are the owner's own requests word for word and the
    rules include the assistant's private memory notes. ``.intelligence/`` is ignored."""
    try:
        from intelligence import lessons
        taught = lessons.load()
    except Exception:  # noqa: BLE001 - the agent works without lessons, just less well
        return {"rules": [], "recoveries": [], "examples": []}
    return {k: taught.get(k, []) for k in ("rules", "recoveries", "examples")}


def sync() -> dict:
    """Re-derive the playbooks and copy the learning into the agent's KB."""
    try:
        from intelligence import lessons, procedures
        procedures.run()
        lessons.build()
    except Exception as exc:  # noqa: BLE001 - a broken observer must not break the agent
        data = collect()
        data["warning"] = f"playbooks not re-derived: {type(exc).__name__}: {exc}"
    else:
        data = collect()
    config.ensure_dirs()
    LEARNED_PATH.write_text(json.dumps(data, indent=1, default=str), encoding="utf-8")
    return data


def load() -> dict:
    data = json.loads(LEARNED_PATH.read_text(encoding="utf-8")) if LEARNED_PATH.exists() else collect()
    return {**data, **_lessons()}


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
    rules = data.get("rules", [])
    if rules:
        lines.append("The owner's standing rules (they outrank any habit above):")
        lines += [f"- {r['rule']}" for r in rules]
    fixes = [r for r in data.get("recoveries", []) if r.get("fixed_by")][:3]
    if fixes:
        lines.append("Seen failing, and what fixed it:")
        lines += [f"- {r['failed']} failed ({r['error'][:70]}); then: {r['fixed_by']}" for r in fixes]
    return "\n".join(lines)


def examples_for(request: str, k: int = 3) -> str:
    """The past requests most like this one, as worked examples for the planner.
    Empty when nothing in the record is close."""
    try:
        from intelligence import lessons
        found = lessons.recall(request, k, {"examples": load().get("examples", [])})
    except Exception:  # noqa: BLE001
        return ""
    found = [e for e in found if e.get("score", 0) >= 3]
    return lessons.as_prompt(found) if found else ""


def query(kind: str = "all") -> dict:
    data = load()
    if not data.get("ok"):
        return {"ok": False, "error": data.get("error", "nothing learned yet")}
    if kind == "all":
        return {"ok": True, "summary": summary(data), "playbooks": [b["name"] for b in data["playbooks"]]}
    if kind == "playbooks":
        from intelligence import procedures
        return {"ok": True, "text": procedures.text(data["playbooks"]), "playbooks": data["playbooks"]}
    if kind in ("top_actions", "failures", "knowledge", "counts", "rules", "recoveries"):
        return {"ok": True, kind: data.get(kind, [])}
    if kind == "examples":
        ex = data.get("examples", [])
        return {"ok": True, "count": len(ex),
                "examples": [{"request": e["request"][:200], "steps": e["steps"][:8]} for e in ex[-20:]]}
    return {"ok": False, "error": f"unknown kind {kind!r}"}
