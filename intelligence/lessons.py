"""Lessons: what the observer's record teaches, in a form an agent can use.

The playbooks (:mod:`intelligence.procedures`) say which kinds of step tend to
follow which. That is the shape of the work, not the work. This module keeps
the parts a learner needs to do the work the way it has actually been done
here:

* **examples** -- every real request the owner made (not the harness's own
  notices), paired with the steps taken, compressed to readable lines -- the
  module run, the file changed, the page checked, the file sent -- and how it
  ended. These are the worked examples an agent is shown when a new request
  resembles an old one (:func:`recall`).
* **recoveries** -- each step that failed, and the step that then worked: the
  project's own record of what to do when a thing breaks.
* **rules** -- the owner's standing rules: the sections of ``CLAUDE.md``, and
  the corrections kept as feedback notes in the assistant's memory. A rule
  stated by the owner outranks any habit inferred from the record.

All of it is derived, deterministic, and written to
``.intelligence/lessons.json``; nothing here writes to the database.

    py -3.12 -m intelligence.lessons            # rebuild lessons.json and print a summary
    py -3.12 -m intelligence.lessons recall "rebuild the sample pdf"
"""

from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

from . import database

ROOT = Path(__file__).resolve().parent.parent
OUT = database.DB_PATH.parent / "lessons.json"
CLAUDE_MD = ROOT / "CLAUDE.md"
#: The assistant's memory for this project, where corrections are kept as feedback notes.
MEMORY_DIR = Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(ROOT)) / "memory"

#: Prompts the harness wrote, not the owner: finished background tasks, linked sessions.
HARNESS = re.compile(r"\s*<(task-notification|side-sessions-event|system-reminder|command-name|local-command)")
#: The harness's resumption line and other non-requests.
NOT_A_REQUEST = re.compile(r"^(the app was quit while you were working|status\??|continue|yes|no|ok)\W*$", re.I)


# ----------------------------------------------------------------------
# Steps, in words
# ----------------------------------------------------------------------

def _raw(action) -> dict:
    try:
        v = json.loads(action["raw_input"] or "{}")
        return v if isinstance(v, dict) else {}
    except json.JSONDecodeError:
        return {}


def _rel(path: str) -> str:
    """A path as the repository names it; anything outside it, by its last part."""
    p = str(path or "").replace("\\", "/")
    root = str(ROOT).replace("\\", "/")
    for prefix in (root, "/c" + root[2:] if root[1:3] == ":/" else root):
        if p.lower().startswith(prefix.lower()):
            return p[len(prefix):].lstrip("/") or "."
    if "/scratchpad/" in p or "/Temp/" in p:
        return "<scratch>/" + p.rsplit("/", 1)[-1]
    return p


def step_text(action) -> str:
    """One action as a line a person could follow."""
    kind = action["normalized_action"] or "tool.other"
    raw = _raw(action)
    cmd = str(raw.get("command") or "")
    if kind in ("filesystem.edit", "filesystem.write") and raw.get("file_path"):
        return f"{'edit' if kind.endswith('edit') else 'write'} {_rel(raw['file_path'])}"
    if kind == "filesystem.read" and raw.get("file_path"):
        return f"read {_rel(raw['file_path'])}"
    m = re.search(r"py(?:thon)?(?:\s+-3\.\d+)?\s+-m\s+([\w.]+)((?:\s+[\w\-=./]+){0,3})", cmd)
    if m and kind.startswith(("python.", "book.", "render.", "intelligence.")):
        return f"run module {m.group(1)}{m.group(2).rstrip()}"
    m = re.search(r"py(?:thon)?(?:\s+-3\.\d+)?\s+([\w./\\-]+\.py)", cmd)
    if m and kind.startswith(("python.", "book.", "render.")):
        return f"run script {_rel(m.group(1))}"
    m = re.search(r"npm (?:--prefix \S+ )?run (\S+)", cmd)
    if m:
        return f"npm run {m.group(1)}"
    m = re.search(r"wrangler ((?:d1|r2|pages) [\w ]+?)(?: --| zeanahlab|$)", cmd)
    if m:
        return f"wrangler {m.group(1).strip()}"
    m = re.search(r"\bgh (pr \w+|run \w+|secret \w+)", cmd)
    if m:
        return f"gh {m.group(1)}"
    if kind.startswith("git."):
        return kind.replace(".", " ")
    if kind == "user.send_file":
        files = raw.get("files") or []
        return "send the owner " + ", ".join(_rel(f) for f in files[:2])
    if kind.startswith("browser."):
        url = raw.get("url") or ""
        return f"{kind.split('.')[1]} the page{(' ' + url) if url else ''}"
    if kind == "python.inline":
        return "python check (inline)"
    if kind == "filesystem.search":
        return f"search for {str(raw.get('pattern') or '')[:40]!r}"
    return kind.replace(".", " ")


#: Steps that change something or prove something. Reading, listing and searching are how
#: the work is found, not the work, and they drown the lesson; they are left out of examples.
QUIET = re.compile(r"^(read |filesystem |search for|python check|tool |mcp call|shell |process |user ask|git status|git diff|git log)")


def signal(steps: list[str]) -> list[str]:
    kept = [s for s in steps if not QUIET.match(s)]
    return kept or steps[:3]


def compress(steps: list[str], limit: int = 14) -> list[str]:
    """Runs of the same line become one line with a count; long trails are cut."""
    out: list[str] = []
    for s in steps:
        if out and out[-1].split(" (x")[0] == s:
            n = int(out[-1].rsplit("(x", 1)[1][:-1]) + 1 if "(x" in out[-1] else 2
            out[-1] = f"{s} (x{n})"
        else:
            out.append(s)
    return out if len(out) <= limit else out[: limit - 1] + [f"... {len(out) - limit + 1} more steps"]


def _request(text: str) -> str:
    """The owner's words, without pasted blocks and attachments."""
    t = re.sub(r"<pasted_content[\s\S]*?</pasted_content[^>]*>", "[pasted]", text or "")
    t = re.sub(r"\[Image[^\]]*\]", "[image]", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).strip()


# ----------------------------------------------------------------------
# The three kinds of lesson
# ----------------------------------------------------------------------

def examples(conn) -> list[dict]:
    rows = conn.execute(
        "SELECT p.prompt_id, p.prompt_text, p.final_response, p.submitted_at, e.outcome, e.action_count, e.failure_count "
        "FROM prompts p LEFT JOIN episodes e ON e.prompt_id = p.prompt_id "
        "WHERE p.prompt_text IS NOT NULL ORDER BY p.submitted_at").fetchall()
    out = []
    for r in rows:
        text = r["prompt_text"] or ""
        if HARNESS.match(text):
            continue
        request = _request(text)
        if len(request) < 12 or NOT_A_REQUEST.match(request):
            continue
        actions = conn.execute("SELECT * FROM actions WHERE prompt_id = ? ORDER BY sequence_no", (r["prompt_id"],)).fetchall()
        if not actions:
            continue
        steps = compress(signal([step_text(a) for a in actions]))
        touched = sorted({_rel(_raw(a).get("file_path", "")) for a in actions
                          if a["normalized_action"] in ("filesystem.edit", "filesystem.write") and _raw(a).get("file_path")})
        out.append({
            "id": r["prompt_id"], "at": r["submitted_at"], "request": request[:600],
            "steps": steps, "files_changed": touched[:20],
            "outcome": r["outcome"] or "unknown", "actions": len(actions),
            "failures": sum(a["status"] == "failure" for a in actions),
            "result": re.sub(r"\s+", " ", (r["final_response"] or "")).strip()[:500],
        })
    return out


def recoveries(conn) -> list[dict]:
    """A failed step and the next step in the same request that worked. The pair is
    the lesson; the same failure seen again is counted, not repeated."""
    seen: dict[tuple, dict] = {}
    fails = conn.execute("SELECT * FROM actions WHERE status = 'failure' ORDER BY action_id").fetchall()
    for f in fails:
        nxt = conn.execute(
            "SELECT * FROM actions WHERE prompt_id = ? AND sequence_no > ? AND status = 'success' "
            "AND normalized_action = ? ORDER BY sequence_no LIMIT 1",
            (f["prompt_id"], f["sequence_no"], f["normalized_action"])).fetchone()
        error = conn.execute("SELECT error FROM observations WHERE action_id = ?", (f["action_id"],)).fetchone() \
            if "observations" in {t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")} else None
        err = re.sub(r"\s+", " ", str(error[0] if error and error[0] else ""))[:240]
        key = (f["normalized_action"], (f["generalized"] or "")[:80])
        item = seen.setdefault(key, {"action": f["normalized_action"], "failed": step_text(f), "error": err,
                                     "fixed_by": step_text(nxt) if nxt else None, "times": 0})
        item["times"] += 1
    return sorted(seen.values(), key=lambda x: (-x["times"], x["action"]))


def _sections(md: str) -> list[tuple[str, str]]:
    parts = re.split(r"^##\s+(.+)$", md, flags=re.M)
    return [(parts[i].strip(), parts[i + 1].strip()) for i in range(1, len(parts) - 1, 2)]


def rules() -> list[dict]:
    out = []
    if CLAUDE_MD.exists():
        for title, body in _sections(CLAUDE_MD.read_text(encoding="utf-8")):
            first = re.split(r"(?<=[.!?])\s", re.sub(r"\s+", " ", re.sub(r"[*`]", "", body)).strip(), maxsplit=2)
            out.append({"source": "CLAUDE.md", "rule": title, "detail": " ".join(first[:2])[:400]})
    if MEMORY_DIR.is_dir():
        for p in sorted(MEMORY_DIR.glob("feedback_*.md")):
            text = p.read_text(encoding="utf-8")
            desc = re.search(r"^description:\s*(.+)$", text, re.M)
            body = text.split("---", 2)[-1].strip()
            out.append({"source": f"memory/{p.name}", "rule": (desc.group(1).strip() if desc else p.stem),
                        "detail": re.sub(r"\s+", " ", body)[:400]})
    return out


def build() -> dict:
    conn = database.connect(init=False)
    try:
        data = {"examples": examples(conn), "recoveries": recoveries(conn), "rules": rules()}
    finally:
        conn.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    return data


def load() -> dict:
    return json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else build()


# ----------------------------------------------------------------------
# Recall: the past requests most like a new one (BM25 over words)
# ----------------------------------------------------------------------

STOP = set("a an and are as at be but by can do for from get have i if in into is it its just me my no not of on "
           "or so that the then there this to up us was we what when where which will with you your our also make "
           "lets let need want should would could".split())


def _words(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP and len(w) > 1]


def recall(query: str, k: int = 3, data: dict | None = None) -> list[dict]:
    data = data or load()
    docs = data.get("examples", [])
    if not docs:
        return []
    # the request counts twice: it is what a new request is most like
    bags = [Counter(_words(d["request"] + " " + d["request"] + " " + " ".join(d["steps"]))) for d in docs]
    n = len(bags)
    avg = sum(sum(b.values()) for b in bags) / n
    df = Counter(w for b in bags for w in b)
    q = _words(query)
    scored = []
    for d, b in zip(docs, bags):
        length = sum(b.values()) or 1
        s = 0.0
        for w in q:
            if w in b:
                idf = math.log(1 + (n - df[w] + 0.5) / (df[w] + 0.5))
                tf = b[w]
                s += idf * tf * 2.2 / (tf + 1.2 * (0.25 + 0.75 * length / avg))
        if s > 0:
            scored.append((s, d))
    scored.sort(key=lambda x: -x[0])
    return [dict(d, score=round(s, 2)) for s, d in scored[:k]]


def as_prompt(examples_: list[dict]) -> str:
    """Worked examples, as a planner reads them."""
    lines = []
    for e in examples_:
        lines.append(f"- Asked: {e['request'][:260]}")
        lines.append(f"  Done: {'; '.join(e['steps'][:10])}")
        if e.get("result"):
            lines.append(f"  Reported: {e['result'][:220]}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["recall"]:
        for e in recall(" ".join(argv[1:]), 5):
            print(f"[{e['score']}] {e['request'][:120]}\n   " + "\n   ".join(e["steps"][:8]))
        return 0
    data = build()
    print(f"wrote {OUT}")
    print(f"  {len(data['examples'])} worked examples, {len(data['recoveries'])} recoveries, {len(data['rules'])} rules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
