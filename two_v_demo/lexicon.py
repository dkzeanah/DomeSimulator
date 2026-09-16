"""The visual lexicon: every term and idea the films explain, what it means, where it
is taught, and how it is put on screen.

Three layers, each built on the one below it.

1. **The inventory** (:mod:`two_v_demo.lexicon_words`): every noun in every script,
   outline and note, counted and sorted into categories. Nobody writes this; it is
   read off the corpus.
2. **Terms** (:mod:`two_v_demo.lexicon_terms`): the nouns and phrases that carry the
   subject -- *kerf*, *board foot*, *pinwheel joint* -- each defined in plain words
   for someone who has never built anything, tied to the figures that quantify it,
   and to the codified visual object that draws it.
3. **Concepts** (:mod:`two_v_demo.lexicon_concepts`): the ideas the films argue --
   *a split log keeps most of itself*, *the golden ratio is not the strut ratio* --
   each with its claim, a short explanation, the figures it rests on, the caveat it
   owes, where it is already taught, and a *visual recipe*: the objects, callouts
   and existing scenes that show it.

Definitions and claims are written in the book's token language, so a definition
that quotes a figure quotes the function behind it, exactly as a film or the book
would. :func:`validate_lexicon` refuses an unknown token, a visual object or icon
that does not exist, a reference to a chapter that is not there, and a concept that
leans on a term nobody defined.

A term's *rendering* is its visual object if it has one; otherwise it inherits its
category's rendering mode from :mod:`two_v_demo.lexicon_taxonomy` -- a quantity
becomes a figure callout, an abstraction a word on a card. So every noun in every
script has an answer to "how would a film show this?", even before anybody has
drawn it.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache


DOMAINS: dict[str, str] = {
    "geometry": "The shape: spheres, triangles, chords and angles",
    "structure": "Why the shape stands up, and what it asks of its members",
    "wood": "The tree, and what a split trunk gives",
    "method": "Cutting and joining: the saw, the jig, the seam",
    "build": "Doing it: the fortnight, the raising, the shell",
    "economics": "What it costs, what it saves, and who is paid",
    "performance": "Heat, water, air and weather",
    "housing": "The dome as a house: markets, money and objections",
    "rendering": "How the films compute what they show",
    "story": "The montage and the drama",
}

RECIPE_KINDS = ("object", "scene", "callout", "tally", "icon", "type", "diagram")
"""What a visual recipe step can be: a registered visual object, an existing lesson
painter, a figure callout, a checked tally, a pinned icon, a word card, or a
diagram (arrows and dimensions)."""


@dataclass(frozen=True)
class Term:
    """One noun or phrase the subject is built from."""

    key: str
    """The lemma or phrase, singular and lower case, as the tagger reduces it."""
    name: str
    category: str
    """A :mod:`lexicon_taxonomy` category key."""
    define: str
    """Plain words, no jargon unexplained. May quote ``{{tokens}}``."""
    aliases: tuple[str, ...] = ()
    """Other lemma phrases that name the same thing."""
    visual: str = ""
    """A registered visual object key; empty means the category's rendering."""
    icon: str = ""
    """The pictogram a callout about it carries."""
    figures: tuple[str, ...] = ()
    """Token names that quantify it."""
    scene: str = ""
    """An existing painter that already shows it: ``lesson_key:stage``."""
    see: tuple[str, ...] = ()


@dataclass(frozen=True)
class Concept:
    """One idea the films argue, and how to show it."""

    key: str
    name: str
    domain: str
    claim: str
    """One sentence a viewer should leave with."""
    explain: str
    """Two to four plain sentences."""
    terms: tuple[str, ...]
    figures: tuple[str, ...] = ()
    caveat: str = ""
    """What the claim does not cover, or the number that does not help it."""
    taught: tuple[str, ...] = ()
    """Where it is already taught: ``film:why/split``, ``book:2trees/ch12``."""
    recipe: tuple[str, ...] = ()
    """Ordered visual steps, each ``kind:detail`` with a kind from RECIPE_KINDS."""


# ----------------------------------------------------------------------
# Loading the data
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def terms() -> tuple[Term, ...]:
    from .lexicon_terms import TERMS
    return TERMS


@lru_cache(maxsize=1)
def concepts() -> tuple[Concept, ...]:
    from .lexicon_concepts import CONCEPTS
    return CONCEPTS


@lru_cache(maxsize=1)
def term_map() -> dict[str, Term]:
    return {term.key: term for term in terms()}


def resolve(text: str) -> str:
    from .book_tokens import resolve as resolve_tokens
    return resolve_tokens(text, strict=True)


# ----------------------------------------------------------------------
# Counting what the scripts actually say
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def _lemma_streams() -> tuple[tuple[tuple[str, ...], frozenset[str]], ...]:
    """Every passage as a run of lemmas, with the works it appears in."""
    from .lexicon_words import CLOSED, lemma_of, scan

    result = scan()
    streams = []
    for index, toks in enumerate(result.tokens):
        passage = result.data.passages[index]
        works = frozenset(f"{p.source}:{p.work}" for p in passage.places)
        lemmas = []
        for tok in toks:
            if tok.kind == "word":
                low = tok.low
                lemmas.append(low if low in CLOSED else lemma_of(low))
            elif tok.kind == "tech":
                lemmas.append(tok.low)
            else:
                lemmas.append("|")
        streams.append((tuple(lemmas), works))
    return tuple(streams)


@lru_cache(maxsize=1)
def mentions() -> dict[str, tuple[int, frozenset[str]]]:
    """For every term: how often the scripts say it, and in which works."""
    wanted: dict[tuple[str, ...], str] = {}
    for term in terms():
        for phrase in (term.key, *term.aliases):
            wanted[tuple(phrase.split())] = term.key
    longest = max(len(key) for key in wanted) if wanted else 1
    counts: Counter = Counter()
    works: dict[str, set[str]] = defaultdict(set)
    for lemmas, where in _lemma_streams():
        for start in range(len(lemmas)):
            for size in range(1, longest + 1):
                gram = lemmas[start:start + size]
                if len(gram) < size:
                    break
                key = wanted.get(tuple(gram))
                if key is not None:
                    counts[key] += 1
                    works[key].update(where)
    return {term.key: (counts[term.key], frozenset(works[term.key]))
            for term in terms()}


def rendering(term: Term) -> tuple[str, str]:
    """(mode, what draws it): the term's own object, or its category's mode."""
    from .lexicon_taxonomy import categories

    if term.visual:
        return "object", term.visual
    for category in categories():
        if category.key == term.category:
            return category.rendering, category.name
    return "type", "a word on a card"


# ----------------------------------------------------------------------
# Where things are taught
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def places() -> frozenset[str]:
    """Every ``source:work/locator`` the corpus knows, plus chapter-level book refs."""
    from .lexicon_corpus import corpus

    refs: set[str] = set()
    for passage in corpus().passages:
        for place in passage.places:
            refs.add(place.ref())
            if "/" in place.locator:
                refs.add(f"{place.source}:{place.work}/"
                         f"{place.locator.split('/', 1)[0]}")
    return frozenset(refs)


def describe_place(ref: str) -> str:
    """A human name for a reference: the work's title and the spot's heading."""
    from .lexicon_corpus import corpus

    data = corpus()
    source, rest = ref.split(":", 1)
    work, _, locator = rest.partition("/")
    title = data.titles.get((source, work), work)
    for passage in data.passages:
        for place in passage.places:
            if (place.source, place.work) == (source, work) and \
                    place.locator.split("/", 1)[0] == locator.split("/", 1)[0]:
                return f"{title} -- {place.heading}" if place.heading else title
    return title


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

_TOKEN = re.compile(r"\{\{([a-z_]+\.[a-z_0-9]+)\}\}")


def stage_exists(lesson_key: str, stage: str) -> bool:
    """Whether a film can draw a stage: its own painter, or the renderer's own.

    The 2V lessons draw with the renderer's built-in ``scene_*`` methods rather than
    a painter table, so both places count.
    """
    from .lesson_registry import LESSONS

    lesson = LESSONS.get(lesson_key)
    if lesson is None:
        return False
    if stage in lesson.scenes:
        return True
    from .app import MasterclassApp
    return callable(getattr(MasterclassApp, f"scene_{stage}", None))


def validate_lexicon() -> None:
    """Everything that would make the catalogue wrong, refused."""
    from .book_tokens import token_map
    from .icons import ICONS
    from .lesson_registry import LESSONS
    from .lexicon_taxonomy import categories
    from .visual_objects import registry

    known_tokens = token_map()
    category_keys = {category.key for category in categories()}
    objects = registry()
    term_keys = [term.key for term in terms()]
    assert len(set(term_keys)) == len(term_keys), sorted(
        {k for k in term_keys if term_keys.count(k) > 1})
    all_names = set(term_keys)
    for term in terms():
        where = f"term {term.key!r}"
        assert term.category in category_keys, (where, term.category)
        assert term.define.strip() and term.name.strip(), where
        resolve(term.define)
        assert not term.visual or term.visual in objects, (where, term.visual)
        assert not term.icon or term.icon in ICONS, (where, term.icon)
        for figure in term.figures:
            assert figure in known_tokens, (where, figure)
        for other in term.see:
            assert other in all_names, (where, other)
        if term.scene:
            lesson, _, stage = term.scene.partition(":")
            assert stage_exists(lesson, stage), (where, term.scene)
        # A definition may state a figure only through a token.
        bare = _TOKEN.sub("", term.define)
        assert not re.search(r"\d", bare.replace("2V", "").replace("2x4", "")), (
            f"{where} types a figure into its definition: {term.define!r}")

    keys = [concept.key for concept in concepts()]
    assert len(set(keys)) == len(keys), "a concept key repeats"
    known_places = places()
    for concept in concepts():
        where = f"concept {concept.key!r}"
        assert concept.domain in DOMAINS, (where, concept.domain)
        for text in (concept.claim, concept.explain, concept.caveat):
            resolve(text)
            bare = _TOKEN.sub("", text)
            assert not re.search(r"\d", bare.replace("2V", "").replace("2x4", "")), (
                f"{where} types a figure: {text!r}")
        for name in concept.terms:
            assert name in all_names, (where, name)
        for figure in concept.figures:
            assert figure in known_tokens, (where, figure)
        for ref in concept.taught:
            assert ref in known_places, (where, ref)
        for step in concept.recipe:
            kind, _, detail = step.partition(":")
            assert kind in RECIPE_KINDS, (where, step)
            if kind == "object":
                assert detail.split("(", 1)[0] in objects, (where, step)
            elif kind == "scene":
                lesson, _, stage = detail.partition("/")
                assert stage_exists(lesson, stage), (where, step)
            elif kind == "icon":
                assert detail in ICONS, (where, step)
            elif kind in ("callout", "tally"):
                resolve(detail)
        assert concept.recipe, f"{where} has no way to be shown"
        assert concept.taught or concept.domain == "rendering", (
            f"{where} is taught nowhere; say where, or drop it")


# ----------------------------------------------------------------------
# Export
# ----------------------------------------------------------------------

def catalog_data() -> dict:
    """The whole catalogue as plain data: inventory, terms and concepts.

    One structure for every consumer -- the Markdown report, the web page, a studio
    tab -- so none of them re-derives anything.
    """
    from .lexicon_taxonomy import RENDERING_MODES, categories
    from .lexicon_words import inventory
    from .visual_objects import registry

    counted = mentions()
    words = inventory()
    by_category: dict[str, list] = defaultdict(list)
    for word in words:
        by_category[word.category].append(word)
    category_rows = []
    for category in categories():
        members = by_category.get(category.name, [])
        category_rows.append({
            "key": category.key, "name": category.name, "blurb": category.blurb,
            "rendering": category.rendering,
            "rendering_meaning": RENDERING_MODES[category.rendering],
            "count": len(members),
            "words": [{"lemma": w.lemma, "count": w.count, "films": len(w.films),
                       "works": len(w.works), "spoken": w.spoken,
                       "example": w.example} for w in members],
        })
    term_rows = []
    for term in terms():
        mode, drawn_by = rendering(term)
        count, works = counted[term.key]
        term_rows.append({
            "key": term.key, "name": term.name, "category": term.category,
            "define": resolve(term.define), "aliases": list(term.aliases),
            "rendering": mode, "drawn_by": drawn_by, "icon": term.icon,
            "figures": {name: _token_value(name) for name in term.figures},
            "scene": term.scene, "see": list(term.see),
            "mentions": count, "works": sorted(works),
        })
    concept_rows = []
    for concept in concepts():
        concept_rows.append({
            "key": concept.key, "name": concept.name, "domain": concept.domain,
            "domain_name": DOMAINS[concept.domain],
            "claim": resolve(concept.claim), "explain": resolve(concept.explain),
            "caveat": resolve(concept.caveat) if concept.caveat else "",
            "terms": list(concept.terms),
            "figures": {name: _token_value(name) for name in concept.figures},
            "taught": [{"ref": ref, "where": describe_place(ref)}
                       for ref in concept.taught],
            "recipe": [_recipe_row(step) for step in concept.recipe],
        })
    objects = [{"key": obj.key, "label": obj.label, "category": obj.category,
                "blurb": obj.blurb, "source": obj.source,
                "knobs": [{"key": k.key, "label": k.label, "default": k.default,
                           "low": k.low, "high": k.high, "unit": k.unit,
                           "animate": k.animate, "help": k.help}
                          for k in obj.knobs],
                "words": list(obj.words)}
               for obj in registry().values()]
    return {"categories": category_rows, "terms": term_rows,
            "concepts": concept_rows, "objects": objects,
            "totals": {"nouns": len(words), "terms": len(term_rows),
                       "concepts": len(concept_rows), "objects": len(objects)}}


def _token_value(name: str) -> str:
    from .book_tokens import token_map
    token = token_map()[name]
    return f"{token.value()} ({token.describe})"


def _recipe_row(step: str) -> dict:
    kind, _, detail = step.partition(":")
    shown = resolve(detail) if kind in ("callout", "tally") else detail
    return {"kind": kind, "detail": shown}


def catalog_markdown() -> str:
    """The catalogue as one readable document."""
    data = catalog_data()
    totals = data["totals"]
    lines = ["# The visual lexicon", "",
             f"{totals['nouns']} nouns across every script, {totals['terms']} "
             f"defined terms, {totals['concepts']} concepts, "
             f"{totals['objects']} codified visual objects.", ""]
    lines += ["## Concepts", ""]
    for domain, title in DOMAINS.items():
        rows = [c for c in data["concepts"] if c["domain"] == domain]
        if not rows:
            continue
        lines += [f"### {title}", ""]
        for row in rows:
            lines += [f"**{row['name']}** -- {row['claim']}", "", row["explain"], ""]
            if row["caveat"]:
                lines += [f"*Caveat:* {row['caveat']}", ""]
            if row["figures"]:
                lines += ["Figures: " + "; ".join(row["figures"].values()), ""]
            lines += ["Show it: " + " -> ".join(f"{s['kind']} {s['detail']}"
                                                for s in row["recipe"]), ""]
            if row["taught"]:
                lines += ["Taught in: " + "; ".join(t["where"] for t in row["taught"]),
                          ""]
    lines += ["## Terms", ""]
    for row in sorted(data["terms"], key=lambda r: r["name"].lower()):
        lines += [f"**{row['name']}** ({row['category']}, said {row['mentions']} "
                  f"times in {len(row['works'])} works) -- {row['define']} "
                  f"*Drawn as:* {row['rendering']}, {row['drawn_by']}.", ""]
    lines += ["## Every noun, by category", ""]
    for category in data["categories"]:
        lines += [f"### {category['name']} ({category['count']}) -- shown as "
                  f"{category['rendering']}", "",
                  ", ".join(f"{w['lemma']} {w['count']}" for w in category["words"]),
                  ""]
    return "\n".join(lines)
