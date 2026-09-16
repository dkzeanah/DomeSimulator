"""Claims, gaps, and the resolution ledger.

The "easy resolving system": every unknown in a user's brief becomes a
first-class ledger item with a kind, a question, and a status — never a silent
guess.  Items are resolved by a chat command (or an LLM tool call), and
resolved *declared* constants can be emitted as a Python constants module ready
to paste into a facts module.

The provenance vocabulary mirrors the repository's own conventions:
``computed`` (a facts module derives it), ``declared`` (external constant with
name + unit + source), ``estimated`` (allowed, labelled), ``placeholder``
(unknown, shown as a marked card, not faked), ``dropped`` (cut, and the cut is
recorded).

Three things here exist because the first version lost data:

* Writes go through a temp file and :func:`os.replace`, so a crash mid-write
  leaves the previous ledger intact rather than a half-written one.
* A lock file serialises writers, because the whole file is rewritten on every
  change and two writers interleaving lose items.
* :func:`scan_claims` files a whole batch in one write.  Filing one item at a
  time rewrote the entire ledger per sentence, which is quadratic and gave a
  crash a hundred chances to land in the middle of a write.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .config import LEDGER_PATH, ensure_dirs, ticket_lock

KINDS = ("computed", "declared", "estimated", "placeholder", "dropped",
         "review")
STATUSES = ("pending", "resolved", "dropped", "verified")


@dataclass
class LedgerItem:
    id: str
    question: str
    kind: str = "review"
    status: str = "pending"
    proposal: str = ""
    source: str = ""
    answer: str = ""
    note: str = ""
    ask: str = ""
    """What to do about this item, in one line.

    Separate from ``question`` (which holds the claim itself) because the
    first version computed this guidance and then overwrote it with the
    sentence, so the ledger told you *what* was unresolved but never *how* to
    resolve it."""
    created: str = field(default_factory=lambda: _now())

    def to_dict(self) -> dict:
        return {
            "id": self.id, "created": self.created, "question": self.question,
            "kind": self.kind, "status": self.status,
            "proposal": self.proposal, "source": self.source,
            "answer": self.answer, "note": self.note, "ask": self.ask,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LedgerItem":
        return cls(
            id=str(data.get("id", "")), question=str(data.get("question", "")),
            kind=str(data.get("kind", "review")),
            status=str(data.get("status", "pending")),
            proposal=str(data.get("proposal", "")),
            source=str(data.get("source", "")),
            answer=str(data.get("answer", "")),
            note=str(data.get("note", "")),
            ask=str(data.get("ask", "")),
            created=str(data.get("created", _now())),
        )


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_all() -> list[LedgerItem]:
    ensure_dirs()
    if not LEDGER_PATH.is_file():
        return []
    items_out: list[LedgerItem] = []
    for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("id"):
            items_out.append(LedgerItem.from_dict(data))
    return items_out


def _write_all(items_in: list[LedgerItem]) -> None:
    """Replace the ledger atomically.

    Written to a temp file in the same directory and then moved into place:
    ``os.replace`` is atomic on both Windows and POSIX, so a reader either sees
    the old ledger or the new one, never a partial line.
    """
    ensure_dirs()
    payload = "".join(json.dumps(item.to_dict()) + "\n" for item in items_in)
    directory = LEDGER_PATH.parent
    handle, temp_name = tempfile.mkstemp(dir=str(directory), prefix=".ledger-",
                                         suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, LEDGER_PATH)
    except BaseException:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def _next_id(existing: list[LedgerItem]) -> str:
    numbers = [int(item.id.split("-")[-1]) for item in existing
               if item.id.startswith("led-") and item.id.split("-")[-1].isdigit()]
    return f"led-{max(numbers, default=0) + 1:04d}"


def add_item(question: str, kind: str = "review", proposal: str = "",
             source: str = "", note: str = "", ask: str = "") -> LedgerItem:
    """Append a new ledger item and return it."""
    return add_items([{"question": question, "kind": kind,
                       "proposal": proposal, "source": source, "note": note,
                       "ask": ask}])[0]


def add_items(rows: list[dict]) -> list[LedgerItem]:
    """Append several items in a single locked, atomic write."""
    if not rows:
        return []
    with ticket_lock("ledger", wait=60, max_age=120):
        existing = _read_all()
        created: list[LedgerItem] = []
        for row in rows:
            item = LedgerItem(
                id=_next_id(existing + created),
                question=str(row.get("question", "")),
                kind=str(row.get("kind", "review")),
                proposal=str(row.get("proposal", "")),
                source=str(row.get("source", "")),
                note=str(row.get("note", "")),
                ask=str(row.get("ask", "")),
            )
            created.append(item)
        _write_all(existing + created)
    return created


def items(**filters: str) -> list[LedgerItem]:
    """Read ledger items, optionally filtered by kind/status/id."""
    result = _read_all()
    for key, value in filters.items():
        if value:
            result = [i for i in result if getattr(i, key, "") == value]
    return result


def _update(item_id: str, **changes) -> LedgerItem | None:
    with ticket_lock("ledger", wait=60, max_age=120):
        all_items = _read_all()
        for item in all_items:
            if item.id == item_id:
                for key, value in changes.items():
                    if value or key in ("status", "note"):
                        setattr(item, key, value)
                _write_all(all_items)
                return item
    return None


def resolve(item_id: str, answer: str, source: str = "",
            status: str = "resolved") -> LedgerItem | None:
    """Resolve one ledger item — the single command that closes a gap."""
    return _update(item_id, answer=answer, source=source, status=status)


def drop(item_id: str, note: str = "dropped: cannot be sourced") -> LedgerItem | None:
    return _update(item_id, status="dropped", note=note)


def ledger_text(only: str = "") -> str:
    """Human-readable ledger listing."""
    all_items = _read_all()
    if only:
        all_items = [i for i in all_items if i.status == only]
    if not all_items:
        return "ledger is empty"
    width = max(len(i.id) for i in all_items)
    lines: list[str] = []
    for item in all_items:
        lines.append(f"  {item.id:<{width}}  [{item.kind:<11}] "
                     f"{item.status:<9} {item.question}")
        if item.answer:
            lines.append(f"    {item.id} => {item.answer}"
                         + (f"  (source: {item.source})" if item.source else ""))
        elif item.ask and item.status == "pending":
            lines.append(f"    {item.id} -> {item.ask}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Claim scanning: a heuristic first pass that finds gaps in pasted text.
# ---------------------------------------------------------------------------

_SENTENCE = re.compile(r"(?<=[.!?])\s+")
_MONEY = re.compile(r"\$[\d,]+(?:\.\d+)?")
_NUMBER_UNIT = re.compile(
    r"\d+(?:[.,]\d+)?\s*(?:ft|in|ton|cord|board|BF|%|per|kw|sq)",
    re.IGNORECASE)
_SOURCE_WORDS = re.compile(
    r"USDA|Extension|listing|survey|stumpage|average|Q[1-4]\s*\d{4}|\b20\d{2}\b",
    re.IGNORECASE)
_APPROX_WORDS = re.compile(
    r"\babout\b|\broughly\b|\bapproximately\b|~|\bon the order of\b|\baround\b",
    re.IGNORECASE)
_DOME_WORDS = re.compile(
    r"\bdome\b|\btree\b|\bwedge\b|\bcord\b|board feet|\bBF\b|\bmember\b|"
    r"\bframe\b|\bblank\b|\bsplit\b", re.IGNORECASE)

MAX_QUESTION = 140


def classify(sentence: str) -> tuple[str, str]:
    """(kind, what to do about it) for one numeric sentence."""
    sourced = bool(_SOURCE_WORDS.search(sentence))
    approx = bool(_APPROX_WORDS.search(sentence))
    dome = bool(_DOME_WORDS.search(sentence))
    if sourced and approx:
        return "declared", ("cite the exact source and date for this figure "
                            "(it is currently approximate)")
    if sourced:
        return "declared", "name the source and date for this figure"
    if approx:
        return "estimated", ("can a facts module compute this, or must it "
                             "stay an estimate?")
    if dome:
        return "computed", ("derive from a facts module (wedge.tree_yield / "
                            "wedge.build_plan / book.tree_first / "
                            "costing.variants)")
    return "review", "classify: computed, declared, estimated, or placeholder?"


def scan_claims(text: str, quiet: bool = False) -> list[LedgerItem]:
    """Split text into sentences, classify every numeric claim, and file the
    unresolved ones into the ledger.  Returns the new items.

    Re-scanning the same text files nothing new: an identical claim already in
    the ledger is skipped whatever its status, so a resolved item is not
    re-opened by running the scan again.
    """
    seen = {item.question for item in _read_all()}
    rows: list[dict] = []
    for raw_sentence in _SENTENCE.split(text or ""):
        sentence = " ".join(raw_sentence.split())
        if len(sentence) < 12:
            continue
        if not (_MONEY.search(sentence) or _NUMBER_UNIT.search(sentence)):
            continue
        kind, ask = classify(sentence)
        question = (sentence if len(sentence) <= MAX_QUESTION
                    else f"{sentence[:MAX_QUESTION]}…")
        if question in seen:
            continue
        seen.add(question)
        rows.append({"question": question, "kind": kind, "proposal": "",
                     "note": "claim-scan heuristic", "ask": ask})
    new_items = add_items(rows)
    if not quiet:
        print(f"claim scan: {len(new_items)} numeric claim(s) filed in the ledger")
    return new_items


# ---------------------------------------------------------------------------
# Emitting constants
# ---------------------------------------------------------------------------


def constant_name(item: LedgerItem) -> str:
    """A valid Python identifier for a ledger item.

    Shared with :mod:`project_agent.templates` so the constants module and the
    constants injected into a facts module use the same names — they were two
    different schemes, which meant a generated module and an injected block
    disagreed about what the same figure was called.
    """
    question = item.question or ""
    if question.startswith("constant "):
        name = question[len("constant "):].strip()
    else:
        name = item.id.replace("-", "_")
    name = re.sub(r"[^a-z0-9_]", "_", name.lower()).strip("_")
    if not name or name[0].isdigit():
        name = f"led_{item.id[-4:]}"
    return name


def split_value(answer: str) -> tuple[object, str]:
    """('275', 'USD per cord') -> (275.0, 'USD per cord')."""
    text = (answer or "").strip()
    if not text:
        return "", ""
    head, _, tail = text.partition(" ")
    try:
        return float(head.replace(",", "")), tail.strip()
    except ValueError:
        return text, ""


def resolved_constants() -> list[LedgerItem]:
    return [i for i in _read_all()
            if i.kind == "declared" and i.status == "resolved" and i.answer]


def constants_module(out_path: Path, module_name: str = "resolved_constants") -> Path:
    """Emit a Python constants module from resolved declared items — the
    paste-ready bridge between the ledger and a facts module."""
    declared = resolved_constants()
    if not declared:
        raise ValueError("no resolved declared constants to emit")
    lines = [
        f'"""{module_name} — constants resolved through the project agent ledger.',
        "",
        "Every row below is a resolved ledger item: name, value, unit, and the",
        "source it was resolved against.  Generated — edit the ledger, not this",
        "file.",
        '"""',
        "",
        "EXTERNAL_CONSTANTS: tuple[tuple[str, object, str, str], ...] = (",
    ]
    emitted: set[str] = set()
    for item in reversed(declared):          # last resolution wins on a clash
        name = constant_name(item)
        if name in emitted:
            continue
        emitted.add(name)
        value, unit = split_value(item.answer)
        source = item.source or "resolution ledger"
        lines.append(f"    ({name!r}, {value!r}, {unit!r}, {source!r}),")
    lines.append(")")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path
