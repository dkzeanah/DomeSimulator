"""Concept cards from the command line.

    py -3.12 -m concepts check [CARD ...]    check cards (all of concepts/cards/ if none given)
    py -3.12 -m concepts facts               the dome numbers a card may use, with values
    py -3.12 -m concepts pack                the handoff zip for the ingesting model
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

from .card import CARDS, ROOT, load


def cmd_check(paths) -> int:
    paths = [Path(p) for p in paths] or sorted(CARDS.glob("*.json"))
    bad = 0
    for path in paths:
        card = load(path)
        state = card.data.get("status")
        if card.problems:
            bad += 1
            print(f"{path.name}: {len(card.problems)} problem(s) [{state}]")
            for problem in card.problems:
                print(f"  - {problem}")
        else:
            films = "films as" if state in ("ready", "example") else "checked; films once ready, as"
            print(f"{path.name}: ok [{state}] -- {films} {card.key}")
    return 1 if bad else 0


def facts_json() -> dict:
    from .dome_facts import SLOTS, dome_facts

    return {"facts": {name: {"value": round(value, 4), "unit": unit, "from": src}
                      for name, (value, unit, src) in dome_facts().items()},
            "slots": {slot: text for slot, (text, _files) in SLOTS.items()}}


def cmd_pack() -> Path:
    """Everything the ingesting model needs, in one zip, under a new name."""
    from two_v_demo.deliverables import next_version_path

    out = next_version_path(ROOT / "deliverables" / "handoff" / "concept-intake-pack.zip")
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(ROOT / "concepts" / "README.md", "README.md")
        z.writestr("dome_facts.json", json.dumps(facts_json(), indent=2))
        z.write(CARDS / "example-molecular-sieve-fridge.json", "example-molecular-sieve-fridge.json")
        z.write(ROOT / "concepts" / "card.py", "reference/card.py")
        graph = ROOT / "research" / "knowledge-graph.json"
        if graph.is_file():
            z.write(graph, "reference/knowledge-graph.json")
        z.write(ROOT / "CLAUDE.md", "reference/CLAUDE.md")
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="concepts", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check"); p.add_argument("cards", nargs="*")
    sub.add_parser("facts"); sub.add_parser("pack")
    args = parser.parse_args(argv)
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if args.cmd == "check":
        return cmd_check(args.cards)
    if args.cmd == "facts":
        for name, f in facts_json()["facts"].items():
            print(f"{name:<24} {f['value']:>12,.2f} {f['unit']:<7} {f['from']}")
        return 0
    if args.cmd == "pack":
        print(cmd_pack())
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
