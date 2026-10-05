"""Seed the action vocabulary from Claude Code's permission allow-list.

``.claude/settings.local.json`` -> ``permissions.allow`` is historical
evidence of what has been run in this project -- not a complete history, and
not a statement of what works. Each entry is classified with the same rules
the observer uses, so ``py -3.12 -m py_compile a.py`` and
``py -3.12 -m py_compile a.py b.py`` both land in ``python.syntax_check``;
the raw strings are kept as examples.

The settings file is only ever READ here. Nothing in it is changed.

    py -3.12 -m intelligence.seed_actions            # import / refresh
    py -3.12 -m intelligence.seed_actions --dry-run  # show the grouping only
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict

from . import normalize as nz
from .database import PROJECT_ROOT, connect, now

SETTINGS = PROJECT_ROOT / ".claude" / "settings.local.json"
_RULE = re.compile(r"^(?P<tool>[A-Za-z_][\w]*)(?:\((?P<arg>.*)\))?$", re.S)


def parse_rule(rule: str) -> tuple[str, str]:
    """'Bash(git add *)' -> ('Bash', 'git add *'); 'WebSearch' -> ('WebSearch', '')."""
    match = _RULE.match(rule.strip())
    if not match:
        return rule.strip(), ""
    arg = (match.group("arg") or "").replace("\\(", "(").replace("\\)", ")")
    return match.group("tool"), arg


def classify_rule(tool: str, arg: str) -> str:
    """The vocabulary name a permission rule is evidence for."""
    if tool in ("Bash", "PowerShell"):
        return nz.classify_command(arg.rstrip("*").strip() or arg)
    if tool == "Read":
        return "filesystem.read"
    return nz.classify_tool(tool, {"command": arg, "url": arg})


def load_rules() -> list[str]:
    """The allow-list, or an empty list if the file is missing or unreadable."""
    try:
        data = json.loads(SETTINGS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return list(data.get("permissions", {}).get("allow", []))


def group_rules(rules: list[str]) -> dict[str, list[tuple[str, str]]]:
    """name -> [(tool, raw rule)] for every allow-list entry."""
    groups: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for rule in rules:
        tool, arg = parse_rule(rule)
        groups[classify_rule(tool, arg)].append((tool, rule))
    return dict(groups)


def seed(conn, rules: list[str] | None = None) -> int:
    """Insert or refresh vocabulary entries from the allow-list.

    Seeding sets descriptions and adds permission examples; it never resets the
    observed counts the observer has accumulated."""
    groups = group_rules(load_rules() if rules is None else rules)
    with conn:
        for name, entries in sorted(groups.items()):
            spec = nz.spec_for(name)
            executors = sorted({tool.lower() for tool, _ in entries})
            examples = [nz.symbolize(raw)[:300] for _tool, raw in entries][:20]
            pattern = nz.generalize(parse_rule(entries[0][1])[1] or entries[0][0])
            row = conn.execute("SELECT examples, source FROM action_vocabulary WHERE name = ?",
                               (name,)).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO action_vocabulary (name, category, executor, pattern, purpose, risk, "
                    "success_signal, examples, source, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (name, spec.category, ",".join(executors), pattern, spec.purpose, spec.risk,
                     spec.success_signal, json.dumps(examples), "permissions", now()))
            else:
                merged = list(dict.fromkeys(json.loads(row["examples"] or "[]") + examples))[:30]
                source = row["source"] or ""
                if "permissions" not in source:
                    source = "permissions+" + source if source else "permissions"
                conn.execute("UPDATE action_vocabulary SET examples = ?, source = ?, "
                             "category = ?, purpose = ?, risk = ?, success_signal = ?, "
                             "updated_at = ? WHERE name = ?",
                             (json.dumps(merged), source, spec.category, spec.purpose, spec.risk,
                              spec.success_signal, now(), name))
    return len(groups)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    rules = load_rules()
    groups = group_rules(rules)
    print(f"{len(rules)} permission rules -> {len(groups)} vocabulary entries")
    for name, entries in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        print(f"  {len(entries):>4}  {name}")
    if not args.dry_run:
        conn = connect()
        try:
            seed(conn, rules)
            total = conn.execute("SELECT COUNT(*) FROM action_vocabulary").fetchone()[0]
            print(f"vocabulary now holds {total} entries")
        finally:
            conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
