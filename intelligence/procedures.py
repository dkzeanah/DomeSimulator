"""Playbooks: the project's repeated workflows, named and written down.

``analyze_actions`` mines short n-grams of raw actions ("read, then edit"),
which is true and useless. This module works one level up. Every action is
labelled with what it means *in this project* -- edit a lesson, run a
selftest, render stills, look at them, render the film, watch the render,
verify the video, commit -- and each episode becomes its ordered list of
those milestones. Episodes whose milestones share an ordered spine are
grouped into a playbook, which records:

* the steps, in order;
* the commands actually used at each step (redacted, as recorded);
* how long each step takes, median;
* what failed along the way and what was done next;
* how many episodes and sessions it came from, and how they ended.

A playbook seen once is kept as *observed*; seen in two or more episodes it is
*recurring*. Results go to the ``procedures`` table (names ``playbook.*``),
to tier-2 knowledge, and in full to ``.intelligence/playbooks.json``, which the
dashboard and the project agent read.

    py -3.12 -m intelligence.procedures
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from statistics import median

from .analyze_actions import analyze, upsert_knowledge
from .database import DATA_DIR, connect, now

PLAYBOOKS_PATH = DATA_DIR / "playbooks.json"

#: Episodes with fewer real actions than this are chatter, not workflows.
MIN_ACTIONS = 2
#: Steps that only look around; they do not make a milestone.
LOOKING = {"understand"}

NOTIFICATION = re.compile(r"^\s*<task-notification>")


# ----------------------------------------------------------------------
# What an action means here
# ----------------------------------------------------------------------

def _path_of(raw: dict) -> str:
    for key in ("file_path", "path", "notebook_path"):
        if isinstance(raw.get(key), str):
            return raw[key].replace("\\", "/")
    return ""


def area_of(path: str) -> str:
    """Which part of the project a file belongs to."""
    p = path.lower()
    name = p.rsplit("/", 1)[-1]
    if "/.claude/projects/" in p and "/memory/" in p:
        return "memory"
    if "/scratchpad/" in p or "/temp/" in p:
        return "scratch"
    if p.endswith((".png", ".jpg", ".jpeg")):
        return "image"
    if "/two_v_demo/lesson_" in p:
        return "lesson"
    if name in ("lesson_registry.py", "deliverables.py", "render_presets.py", "release.py") or \
            p.endswith("wedge_book/ledger.py"):
        return "registration"
    if "/two_v_demo/" in p and ("scene" in name or "solids" in name or "render_kit" in name
                                or "cabin_world" in name):
        return "scene"
    if "/two_v_demo/" in p:
        return "model"
    if "/wedge_book/" in p or "/books/the-40-hour-cabin/" in p or "/book/" in p or "/books/" in p:
        return "book"
    if "/intelligence/" in p or "/.claude/" in p or "/project_agent/" in p:
        return "tooling"
    if "/web/" in p:
        return "web"
    if name.endswith(".md"):
        return "docs"
    return "code"


def label_of(action: str, tool: str, raw: dict, generalized: str) -> str:
    """One action as a project milestone, e.g. ``edit:lesson`` or ``render:stills``."""
    command = " ".join(str(raw.get(k, "")) for k in ("command", "prompt", "description")).lower()
    if action in ("filesystem.edit", "filesystem.write"):
        return f"edit:{area_of(_path_of(raw))}"
    if action == "filesystem.read" and tool == "Read":
        area = area_of(_path_of(raw))
        return "review:stills" if area == "image" else "understand"
    if "rerender render" in command or "export_video" in command:
        return "render:film"
    if action == "render.stills" or "rerender stills" in command or "render_shots" in command:
        return "render:stills"
    if "ffprobe" in command or "ffmpeg" in command:
        return "verify:video"
    if action == "book.check" or "wedge_book.check" in command:
        return "verify:book"
    if action == "python.selftest" or "validate_" in command or "selftest" in command:
        return "verify:selftest"
    if action == "process.wait" or tool == "Monitor":
        return "render:watch"
    if action == "process.start":
        return "render:launch"
    if action.startswith("git."):
        return {"git.commit": "ship:commit", "git.push": "ship:push"}.get(action, "ship:git")
    if action in ("python.syntax_check",):
        return "verify:compile"
    if action.startswith("python."):
        module = re.search(r"-m\s+([a-z_][\w.]*)", command)
        return f"run:{module.group(1)}" if module else "run:python"
    if action.startswith(("filesystem.", "tool.", "process.")) or action in ("shell.echo",):
        return "understand"
    return f"run:{action}"


# ----------------------------------------------------------------------
# Episodes as milestone lists
# ----------------------------------------------------------------------

def _episode_rows(conn):
    episodes = {e["prompt_id"]: dict(e) for e in conn.execute(
        "SELECT episode_id, prompt_id, session_id, goal, outcome, action_count, failure_count "
        "FROM episodes")}
    steps = defaultdict(list)
    for a in conn.execute(
            "SELECT prompt_id, normalized_action, tool_name, raw_input, generalized, status, "
            "duration_ms, agent_id FROM actions ORDER BY prompt_id, sequence_no, action_id"):
        if a["agent_id"]:
            continue
        try:
            raw = json.loads(a["raw_input"] or "{}")
        except json.JSONDecodeError:
            raw = {}
        if not isinstance(raw, dict):
            raw = {}
        steps[a["prompt_id"]].append({
            "label": label_of(a["normalized_action"] or "", a["tool_name"] or "", raw, a["generalized"] or ""),
            "status": a["status"], "ms": a["duration_ms"],
            "command": (raw.get("command") or _path_of(raw) or a["generalized"] or "")[:200],
        })
    for pid, e in episodes.items():
        e["steps"] = steps.get(pid, [])
        e["kind"] = "notification" if NOTIFICATION.match(e.get("goal") or "") else "task"
        yield e


def milestones(steps: list[dict]) -> list[str]:
    """The ordered milestones of an episode: consecutive repeats collapsed,
    looking-around dropped, scratch edits dropped."""
    out: list[str] = []
    for s in steps:
        label = s["label"]
        if label in LOOKING or label == "edit:scratch":
            continue
        if out and out[-1] == label:
            continue
        out.append(label)
    return out


def _spine(ms: list[str]) -> tuple:
    """First occurrence order of each milestone: the shape of the workflow."""
    seen, out = set(), []
    for m in ms:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return tuple(out)


def _lcs(a: tuple, b: tuple) -> tuple:
    """Longest common ordered subsequence: what two workflows share."""
    table = [[()] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) - 1, -1, -1):
        for j in range(len(b) - 1, -1, -1):
            if a[i] == b[j]:
                table[i][j] = (a[i],) + table[i + 1][j + 1]
            else:
                table[i][j] = max(table[i + 1][j], table[i][j + 1], key=len)
    return table[0][0]


def _consensus(spines: list[tuple]) -> tuple:
    """The steps at least half the episodes took, in the order they usually
    come (mean relative position). Intersecting every episode loses too much:
    two films are rarely made in exactly the same order."""
    need = (len(spines) + 1) // 2
    count, where = Counter(), defaultdict(list)
    for sp in spines:
        for i, step in enumerate(sp):
            count[step] += 1
            where[step].append(i / max(1, len(sp) - 1))
    keep = [s for s in count if count[s] >= need]
    return tuple(sorted(keep, key=lambda s: sum(where[s]) / len(where[s])))


# ----------------------------------------------------------------------
# Naming
# ----------------------------------------------------------------------

def name_for(spine: tuple, goals: list[str]) -> str:
    s = set(spine)
    if "render:film" in s or "render:launch" in s or ("render:watch" in s and "verify:video" in s):
        if "edit:lesson" in s:
            return "make and release a film"
        return "watch a render and check the cut"
    if "render:stills" in s and "edit:lesson" in s:
        return "author a film and check its stills"
    if "render:stills" in s:
        return "render stills and look at them"
    if "edit:lesson" in s or "edit:scene" in s:
        return "change a film and prove it"
    if "edit:book" in s or "verify:book" in s:
        return "change the book and check it"
    if "ship:commit" in s or "ship:push" in s:
        return "commit and push"
    if "edit:tooling" in s:
        return "change the tooling"
    if "edit:memory" in s and len(s) <= 2:
        return "write memory"
    if "edit:model" in s:
        return "change a model and validate it"
    words = " ".join(goals).lower().split()[:4]
    return " ".join(words) or "workflow"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


# ----------------------------------------------------------------------
# Extraction
# ----------------------------------------------------------------------

def extract(conn) -> list[dict]:
    """Group episodes into playbooks and describe each one."""
    episodes = [e for e in _episode_rows(conn) if len(e["steps"]) >= MIN_ACTIONS]
    for e in episodes:
        e["milestones"] = milestones(e["steps"])
        e["spine"] = _spine(e["milestones"])
    episodes = [e for e in episodes if len(e["spine"]) >= 2]

    # Group by name first (episodes with the same kind of work), then take the
    # ordered spine they all share as the playbook's steps.
    groups: dict[str, list[dict]] = defaultdict(list)
    for e in episodes:
        groups[name_for(e["spine"], [e.get("goal") or ""])].append(e)

    books = []
    for name, members in groups.items():
        spine = _consensus([e["spine"] for e in members])
        steps = []
        for label in spine:
            ms = [s["ms"] for e in members for s in e["steps"] if s["label"] == label and s["ms"]]
            cmds = Counter(s["command"] for e in members for s in e["steps"]
                           if s["label"] == label and s["command"])
            runs = sum(1 for e in members for s in e["steps"] if s["label"] == label)
            fails = sum(1 for e in members for s in e["steps"]
                        if s["label"] == label and s["status"] == "failure")
            steps.append({"step": label, "runs": runs, "failures": fails,
                          "median_s": round(median(ms) / 1000, 1) if ms else None,
                          "examples": [c for c, _n in cmds.most_common(2)]})
        recoveries = []
        for e in members:
            seq = e["steps"]
            for i, s in enumerate(seq):
                if s["status"] != "failure":
                    continue
                nxt = next((t for t in seq[i + 1:] if t["status"] == "success"
                            and t["label"] not in LOOKING), None)
                recoveries.append({"failed": s["label"], "command": s["command"][:140],
                                   "then": nxt["label"] if nxt else None,
                                   "episode": e["episode_id"]})
        clean = sum(1 for e in members if e["outcome"] in ("tools_clean", "tools_recovered"))
        sessions = len({e["session_id"] for e in members})
        books.append({
            "name": name, "id": "playbook." + _slug(name),
            "status": "recurring" if len(members) >= 2 else "observed",
            "steps": steps, "episodes": len(members), "sessions": sessions,
            "success_rate": round(clean / len(members), 2),
            "recoveries": recoveries[:12],
            "example_episodes": [e["episode_id"] for e in members][:10],
            "goals": [(e.get("goal") or "")[:140] for e in members if e["kind"] == "task"][:5],
            "trigger": "background-task notification" if all(e["kind"] == "notification" for e in members)
            else "owner request",
        })
    books.sort(key=lambda b: (-b["episodes"], b["name"]))
    return books


def save(conn, books: list[dict]) -> None:
    at = now()
    with conn:
        conn.execute("DELETE FROM procedures WHERE name LIKE 'playbook.%'")
        for b in books:
            conn.execute(
                "INSERT INTO procedures (name, steps, support_count, session_count, success_rate, "
                "example_episode_ids, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
                (b["id"], json.dumps([s["step"] for s in b["steps"]]), b["episodes"], b["sessions"],
                 b["success_rate"], json.dumps(b["example_episodes"]), at, at))
            upsert_knowledge(
                conn, 2, "playbook", b["id"],
                f"'{b['name']}' ({b['status']}, {b['episodes']} episodes): "
                + " -> ".join(s["step"] for s in b["steps"]),
                min(1.0, b["episodes"] / (b["episodes"] + 2)), "derived", "observed", (),
                b["example_episodes"])
    PLAYBOOKS_PATH.write_text(json.dumps({"generated": at, "playbooks": books}, indent=1),
                              encoding="utf-8")


def run(conn=None) -> list[dict]:
    """Re-derive everything, then the playbooks; returns them."""
    own = conn is None
    conn = conn or connect()
    try:
        analyze(conn)
        books = extract(conn)
        save(conn, books)
        return books
    finally:
        if own:
            conn.close()


def load() -> list[dict]:
    if not PLAYBOOKS_PATH.exists():
        return []
    return json.loads(PLAYBOOKS_PATH.read_text(encoding="utf-8")).get("playbooks", [])


def text(books: list[dict]) -> str:
    lines = []
    for b in books:
        lines.append(f"{b['name']}  [{b['status']}, {b['episodes']} episodes, "
                     f"{b['sessions']} sessions, success {b['success_rate']:.0%}]")
        for s in b["steps"]:
            t = f" ~{s['median_s']}s" if s["median_s"] else ""
            f = f"  ({s['failures']} failed)" if s["failures"] else ""
            lines.append(f"   {s['step']:<20} x{s['runs']}{t}{f}")
        for r in b["recoveries"][:3]:
            lines.append(f"   ! {r['failed']} failed -> then {r['then']}")
    return "\n".join(lines)


def validate() -> None:
    assert label_of("filesystem.edit", "Edit", {"file_path": "C:/x/two_v_demo/lesson_a.py"}, "") == "edit:lesson"
    assert label_of("filesystem.read", "Read", {"file_path": "C:/x/out.png"}, "") == "review:stills"
    assert label_of("python.inline", "Bash", {"command": "py -3.12 -m rerender stills k"}, "") == "render:stills"
    assert label_of("git.commit", "Bash", {"command": "git commit"}, "") == "ship:commit"
    assert milestones([{"label": "understand"}, {"label": "edit:lesson"}, {"label": "edit:lesson"},
                       {"label": "verify:selftest"}]) == ["edit:lesson", "verify:selftest"]
    assert _lcs(("a", "b", "c", "d"), ("a", "c", "d")) == ("a", "c", "d")
    assert _consensus([("a", "b", "c"), ("a", "c", "d")]) == ("a", "b", "c", "d")


def main() -> int:
    validate()
    books = run()
    print(text(books) or "no playbooks yet")
    print(f"\n{len(books)} playbooks -> {PLAYBOOKS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
