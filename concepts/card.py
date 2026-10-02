"""A concept card: what one video taught, as data the dome project can film.

The other model (the one that ingests and transcribes videos) writes one JSON
card per concept. This module loads it, checks it against the project's rules,
and computes its figures. It never trusts a number it cannot trace:

* every number carries a **kind** (measured, claimed, standard, estimate) and a
  **source** -- a claimed number needs the video timestamp it was said at;
* every figure is an **expression** over those numbers (and the dome's own,
  :mod:`concepts.dome_facts`), evaluated here -- so a film states what the
  arithmetic gives, not what somebody typed;
* narration may not contain a typed digit: numbers enter it only as
  ``{name}`` placeholders, filled from the table;
* a card must say what the idea will **not** do (``limits``) -- the house rule
  that the unflattering number goes on screen.

    py -3.12 -m concepts check concepts/cards/<slug>.json
"""

from __future__ import annotations

import ast
import json
import math
import operator
import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "concepts" / "cards"

KINDS = ("measured", "claimed", "standard", "estimate")
STATUSES = ("example", "draft", "ready")
SHAPES = ("box", "cylinder", "sphere", "cone", "arrow", "disc", "flow", "label")
COLOURS = {
    "steel": (0.62, 0.64, 0.68), "copper": (0.80, 0.45, 0.25), "wood": (0.80, 0.58, 0.33),
    "water": (0.42, 0.75, 1.00), "cold": (0.45, 0.80, 1.00), "heat": (1.00, 0.45, 0.25),
    "air": (0.45, 0.92, 0.62), "vapour": (0.85, 0.92, 1.00), "glass": (0.70, 0.85, 0.95),
    "white": (0.92, 0.92, 0.90), "dark": (0.16, 0.17, 0.19), "solar": (0.10, 0.18, 0.40),
    "warn": (1.00, 0.55, 0.45), "ok": (0.45, 0.90, 0.55), "amber": (1.00, 0.74, 0.32),
}
NAME = re.compile(r"^[a-z][a-z0-9_]*$")
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PLACEHOLDER = re.compile(r"\{([a-z][a-z0-9_]*)(:[^}]*)?\}")
ALLOWED_DIGIT_WORDS = re.compile(r"\b(?:[1-9]V|3-D|2-D)\b")


class CardError(ValueError):
    pass


# ----------------------------------------------------------------------
# Safe arithmetic
# ----------------------------------------------------------------------

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg,
        ast.UAdd: operator.pos}
_FUNCS = {"min": min, "max": max, "abs": abs, "round": round, "sqrt": math.sqrt,
          "log10": math.log10, "exp": math.exp, "pi": math.pi}


def evaluate(expr: str, names: dict[str, float]) -> float:
    """Arithmetic over known names -- nothing else can run."""
    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](walk(node.left), walk(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](walk(node.operand))
        if isinstance(node, ast.Name):
            if node.id in names:
                return float(names[node.id])
            if node.id == "pi":
                return math.pi
            raise CardError(f"unknown name {node.id!r} in {expr!r}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in _FUNCS and not node.keywords:
            return float(_FUNCS[node.func.id](*(walk(a) for a in node.args)))
        raise CardError(f"not allowed in a figure: {ast.dump(node)[:60]} in {expr!r}")
    return walk(ast.parse(expr, mode="eval"))


# ----------------------------------------------------------------------
# The card
# ----------------------------------------------------------------------

@dataclass
class Card:
    path: Path
    data: dict
    table: dict[str, float] = field(default_factory=dict)      # every name -> value
    units: dict[str, str] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)
    formats: dict[str, str] = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)

    @property
    def slug(self) -> str:
        return self.data.get("slug", "")

    @property
    def key(self) -> str:
        return "concept_" + self.slug.replace("-", "_")

    @property
    def ready(self) -> bool:
        return self.data.get("status") == "ready" and not self.problems

    def fmt(self, name: str, spec: str = "") -> str:
        value = self.table[name]
        spec = spec or self.formats.get(name, "")
        if not spec:
            spec = ",.0f" if abs(value) >= 100 else (".1f" if abs(value) >= 10 else ".2f")
        return format(value, spec)

    def fill(self, text: str) -> str:
        """Narration with every {name} replaced by its value."""
        return PLACEHOLDER.sub(lambda m: self.fmt(m.group(1), (m.group(2) or ":")[1:]), text)

    def line(self, name: str) -> str:
        unit = self.units.get(name, "")
        label = self.labels.get(name, name.replace("_", " "))
        return f"{label} = {self.fmt(name)}" + (f" {unit}" if unit else "")


def _text_problems(where: str, text: str, names: set[str]) -> list[str]:
    out = []
    for m in PLACEHOLDER.finditer(text):
        if m.group(1) not in names:
            out.append(f"{where}: {{{m.group(1)}}} is not a number or figure on this card")
    bare = ALLOWED_DIGIT_WORDS.sub("", PLACEHOLDER.sub("", text))
    if re.search(r"\d", bare):
        out.append(f"{where}: a typed digit -- numbers must come in as {{name}} placeholders "
                   f"({bare[max(0, re.search(chr(92) + 'd', bare).start() - 20):][:50]!r})")
    return out


def load(path: Path | str, with_dome: bool = True) -> Card:
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CardError(f"cannot read {path}: {exc}") from exc
    card = Card(path, data)
    p = card.problems
    if data.get("schema") != 1:
        p.append("schema must be 1")
    if not SLUG.match(card.slug or ""):
        p.append("slug must be kebab-case, e.g. molecular-sieve-fridge")
    if data.get("status") not in STATUSES:
        p.append(f"status must be one of {', '.join(STATUSES)}")
    for key in ("title", "summary"):
        if not str(data.get(key, "")).strip():
            p.append(f"{key} is required")
    source = data.get("source") or {}
    if not source.get("url") and not source.get("transcript_file"):
        p.append("source needs the video url or the transcript file")

    if with_dome:
        from .dome_facts import dome_facts
        for name, (value, unit, _src) in dome_facts().items():
            card.table[name], card.units[name] = value, unit
            card.labels[name] = name.removeprefix("dome_").replace("_", " ") + " (this dome)"

    for n in data.get("numbers", []):
        name = n.get("name", "")
        if not NAME.match(name):
            p.append(f"number {name!r}: name must be snake_case")
            continue
        if name in card.table:
            p.append(f"number {name!r}: name already used")
        if n.get("kind") not in KINDS:
            p.append(f"number {name}: kind must be one of {', '.join(KINDS)}")
        src = str(n.get("source", ""))
        if not src.strip():
            p.append(f"number {name}: source is required")
        if n.get("kind") == "claimed" and not re.search(r"\d{1,2}:\d{2}", src):
            p.append(f"number {name}: a claimed number needs the video timestamp it was said at")
        value = n.get("value")
        if not isinstance(value, (int, float)):
            p.append(f"number {name}: value is missing (fill it from the transcript)")
            value = float("nan")
        card.table[name] = float(value)
        card.units[name] = str(n.get("unit", ""))
        card.labels[name] = str(n.get("label", name.replace("_", " ")))
        if n.get("format"):
            card.formats[name] = n["format"]

    for f in data.get("figures", []):
        name = f.get("name", "")
        if not NAME.match(name) or name in card.table:
            p.append(f"figure {name!r}: needs a new snake_case name")
            continue
        try:
            card.table[name] = evaluate(str(f.get("expr", "")), card.table)
        except (CardError, ZeroDivisionError, ValueError, SyntaxError) as exc:
            p.append(f"figure {name}: {exc}")
            card.table[name] = float("nan")
        card.units[name] = str(f.get("unit", ""))
        card.labels[name] = str(f.get("label", name.replace("_", " ")))
        if f.get("format"):
            card.formats[name] = f["format"]

    names = set(card.table)
    shape_ids = set()
    for s in data.get("shapes", []):
        if s.get("type") not in SHAPES:
            p.append(f"shape {s.get('id')!r}: type must be one of {', '.join(SHAPES)}")
        colour = s.get("color", "steel")
        if isinstance(colour, str) and colour not in COLOURS:
            p.append(f"shape {s.get('id')!r}: colour {colour!r} unknown ({', '.join(COLOURS)})")
        shape_ids.add(s.get("id"))
    text_places = [("summary", data.get("summary", ""))]
    beats = data.get("beats", [])
    if not beats:
        p.append("beats: at least one is required")
    for i, b in enumerate(beats, start=1):
        for field_ in ("title", "narration"):
            if not str(b.get(field_, "")).strip():
                p.append(f"beat {i}: {field_} is required")
        text_places += [(f"beat {i} title", b.get("title", "")),
                        (f"beat {i} promise", b.get("promise", "")),
                        (f"beat {i} narration", b.get("narration", ""))]
        for sid in b.get("show", []):
            if sid != "all" and sid not in shape_ids:
                p.append(f"beat {i}: shows unknown shape {sid!r}")
        for name in b.get("figures", []):
            if name not in names:
                p.append(f"beat {i}: figure {name!r} is not on this card")
    fit = data.get("dome_fit") or {}
    from .dome_facts import SLOTS
    if fit.get("slot") not in SLOTS:
        p.append(f"dome_fit.slot must be one of {', '.join(SLOTS)}")
    text_places.append(("dome_fit narration", fit.get("narration", "")))
    limits = data.get("limits", [])
    if not limits:
        p.append("limits: say at least one thing this will not do, with its number")
    for i, lim in enumerate(limits, start=1):
        text_places.append((f"limit {i}", lim.get("narration", "")))
    for where, text in text_places:
        p.extend(_text_problems(where, str(text), names))
    if data.get("status") == "ready":
        blob = json.dumps(data)
        if "<" in blob and ">" in blob and re.search(r"<[^<>]{2,60}>", blob):
            p.append("still contains <placeholders> -- fill them before marking ready")
    return card


def all_cards() -> list[Card]:
    return [load(path) for path in sorted(CARDS.glob("*.json"))]
