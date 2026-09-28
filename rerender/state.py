"""Where each re-render stands, shared by every session that works the queue.

``rerender/queue.json`` holds only what people change -- status, who has it,
priority, notes, outputs. The catalogue says what the films *are*; this says
what has been *done*. It is a plain file in the repository so a Claude
session, another model, or a person at the launcher all read and write the
same thing, and git keeps its history.

Two workers must never render the same film, so a worker **claims** an item
before starting. A claim older than :data:`STALE_HOURS` with no update is
considered abandoned and can be taken over.

Originals are protected: a claim records the size and modification time of
every original file, and marking an item done checks they are unchanged.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from .catalogue import ROOT, Item

QUEUE = ROOT / "rerender" / "queue.json"
LOCK = ROOT / "rerender" / ".queue.lock"

STATUSES = ("todo", "claimed", "rendering", "review", "done", "skip")
"""todo -> claimed (someone is on it) -> rendering (the long export is running)
-> review (outputs exist; the user watches them) -> done. ``skip`` means the
user decided this film is not worth re-making."""
PRIORITIES = ("high", "normal", "low")
STALE_HOURS = 12.0


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class _Lock:
    """A lock file, so two processes never write the queue at once."""

    def __enter__(self):
        deadline = time.time() + 20
        while True:
            try:
                self.fd = os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                return self
            except FileExistsError:
                if time.time() - LOCK.stat().st_mtime > 60:   # a crashed writer
                    LOCK.unlink(missing_ok=True)
                    continue
                if time.time() > deadline:
                    raise TimeoutError(f"the queue is locked ({LOCK}); try again")
                time.sleep(0.2)

    def __exit__(self, *exc):
        os.close(self.fd)
        LOCK.unlink(missing_ok=True)


def load() -> dict:
    if not QUEUE.is_file():
        return {"version": 1, "items": {}}
    return json.loads(QUEUE.read_text(encoding="utf-8"))


def _save(data: dict) -> None:
    scratch = QUEUE.with_suffix(".json.tmp")
    scratch.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(scratch, QUEUE)


def entry(data: dict, item: Item) -> dict:
    """An item's state, with defaults for anything never touched."""
    stored = data["items"].get(item.key, {})
    return {"status": "todo", "priority": item.default_priority, "owner": "",
            "updated": "", "outputs": [], "log": [], "originals": {}, **stored}


def _update(item: Item, change) -> dict:
    with _Lock():
        data = load()
        current = entry(data, item)
        change(current)
        current["updated"] = now()
        data["items"][item.key] = current
        _save(data)
        return current


def _snapshot(item: Item) -> dict:
    out = {}
    for rel in item.originals:
        p = ROOT / rel
        if p.is_file():
            st = p.stat()
            out[rel] = [st.st_size, int(st.st_mtime)]
    return out


def is_stale(current: dict) -> bool:
    if current["status"] not in ("claimed", "rendering") or not current["updated"]:
        return False
    then = datetime.fromisoformat(current["updated"])
    return (datetime.now(then.tzinfo) - then).total_seconds() > STALE_HOURS * 3600


def claim(item: Item, by: str, force: bool = False) -> dict:
    def change(c):
        mine = c["owner"] == by
        if c["status"] in ("claimed", "rendering") and not mine and not force and not is_stale(c):
            raise PermissionError(
                f"{item.key} is {c['status']} by {c['owner']} since {c['updated']}; "
                "pick another item, or pass --force if the user says to take it over")
        if c["status"] in ("done", "skip") and not force:
            raise PermissionError(f"{item.key} is already {c['status']}")
        c["status"], c["owner"] = "claimed", by
        c["originals"] = _snapshot(item)
        c["log"].append({"at": now(), "by": by, "text": "claimed"})
    return _update(item, change)


def set_status(item: Item, status: str, by: str, outputs=(), text: str = "") -> dict:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {', '.join(STATUSES)}")

    def change(c):
        if status in ("review", "done"):
            changed = [rel for rel, snap in c.get("originals", {}).items()
                       if _snapshot_one(rel) != snap]
            if changed:
                raise RuntimeError("an original changed while this item was open -- "
                                   "originals must never be modified: " + ", ".join(changed))
            missing = [o for o in outputs if not (ROOT / o).exists()]
            if missing:
                raise FileNotFoundError("outputs not on disk: " + ", ".join(missing))
        c["status"] = status
        if status == "todo":
            c["owner"] = ""
        elif by:
            c["owner"] = by
        for o in outputs:
            if o not in c["outputs"]:
                c["outputs"].append(o)
        c["log"].append({"at": now(), "by": by, "text": f"-> {status}" + (f": {text}" if text else "")})
    return _update(item, change)


def _snapshot_one(rel: str):
    p = ROOT / rel
    if not p.is_file():
        return None
    st = p.stat()
    return [st.st_size, int(st.st_mtime)]


def note(item: Item, by: str, text: str) -> dict:
    return _update(item, lambda c: c["log"].append({"at": now(), "by": by, "text": text}))


def set_priority(item: Item, priority: str) -> dict:
    if priority not in PRIORITIES:
        raise ValueError(f"priority must be one of {', '.join(PRIORITIES)}")
    return _update(item, lambda c: c.__setitem__("priority", priority))


def next_item(items: list[Item]) -> Item | None:
    """The first unclaimed film, highest priority first, in catalogue order."""
    data = load()
    rank = {p: i for i, p in enumerate(PRIORITIES)}
    open_items = [i for i in items if entry(data, i)["status"] == "todo"
                  or is_stale(entry(data, i))]
    open_items.sort(key=lambda i: rank[entry(data, i)["priority"]])
    return open_items[0] if open_items else None
