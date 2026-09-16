"""Which words in the scripts are nouns, what they name, and the phrases they form.

No language library is installed in this repository and none is needed: the whole
vocabulary of every film, presentation, outline and note is about six thousand
words, which is small enough to reason about directly. So the tagger here is simple
and fully inspectable, in three layers, each of which a person can read and correct:

1. **Closed classes.** Articles, pronouns, prepositions, conjunctions, auxiliaries,
   number words and the commonest adverbs are listed outright. None of them is ever
   a noun, whatever its neighbours look like.
2. **Context evidence.** Every other word is scored on the company it keeps, across
   every place it occurs. After *the*, *a*, *each*, a number or a possessive -- and
   at the end of such a phrase -- is where English puts nouns. After *to*, a modal or
   a subject pronoun is where it puts verbs. A word is judged on the balance.
3. **Decisions.** :mod:`two_v_demo.lexicon_taxonomy` records what a person decided
   about the words the evidence gets wrong, and gives every noun a category.

The result is deterministic -- the same scripts give the same inventory -- and when a
new script brings in a noun nobody has categorised, :func:`uncategorised` names it
rather than letting it fall silently into a bucket.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache

from .lexicon_corpus import Corpus, Passage, corpus


# ----------------------------------------------------------------------
# Tokens
# ----------------------------------------------------------------------

TOKEN = re.compile(r"""
    (?P<tech>\b\d+(?:\.\d+)?[vV]\b|\b\d+[xX]\d+(?:[xX]\d+)?\b)
  | (?P<num>\d[\d,]*(?:\.\d+)?%?)
  | (?P<word>[A-Za-z]+(?:['’][A-Za-z]+)*(?:-[A-Za-z]+)*)
  | (?P<punct>->|[.,;:!?()\[\]"“”—–=/+*<>|])
""", re.X)

SENTENCE_END = frozenset({".", "!", "?"})


@dataclass(frozen=True)
class Tok:
    text: str
    kind: str
    """``word``, ``num``, ``tech`` (2V, 2x4) or ``punct``."""

    @property
    def low(self) -> str:
        return self.text.lower().replace("’", "'")


def tokenize(text: str) -> list[Tok]:
    return [Tok(match.group(), match.lastgroup) for match in TOKEN.finditer(text)]


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'“(])", text)
    return [part.strip() for part in parts if part.strip()]


# ----------------------------------------------------------------------
# Closed classes: never nouns
# ----------------------------------------------------------------------

def _words(block: str) -> frozenset[str]:
    return frozenset(block.split())


DETERMINERS = _words("""
    the a an this that these those each every either neither another any some no
    all both several such what which whose whatever whichever enough much many few
    fewer fewest more most less least own same other
""")
POSSESSIVES = _words("my your his her its our their one's whose")
SUBJECT_PRONOUNS = _words("i you he she it we they who")
PRONOUNS = _words("""
    me him us them myself yourself himself herself itself ourselves yourselves
    themselves mine yours hers ours theirs someone somebody something anyone anybody
    anything everyone everybody everything noone nobody nothing whoever whomever
    whom thee thou ye oneself
""") | SUBJECT_PRONOUNS
PREPOSITIONS = _words("""
    about above across after against along alongside amid among amongst around as
    at atop before behind below beneath beside besides between beyond by despite
    down during except for from in inside into like minus near nearer nearest next
    of off on onto opposite out outside over past per plus round since than through
    throughout till to toward towards under underneath unlike until unto up upon
    versus via with within without vs
""")
CONJUNCTIONS = _words("""
    and but or nor so yet because although though if unless whether while whilst
    whereas once than that lest till until whenever wherever however therefore thus
    hence otherwise
""")
AUXILIARIES = _words("""
    am is are was were be been being have has had having do does did doing done
    get gets got getting
""")
MODALS = _words("will would shall should can could may might must ought")
NUMBER_WORDS = _words("""
    zero one two three four five six seven eight nine ten eleven twelve thirteen
    fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty
    sixty seventy eighty ninety hundred hundreds thousand thousands million millions
    billion billions dozen dozens first second third fourth fifth sixth seventh
    eighth ninth tenth eleventh twelfth twentieth hundredth thousandth once twice
    thrice ones twos threes fours fives sixes sevens eights nines tens twenties
""")
ADVERBS = _words("""
    not never always often also just only even still already again very too quite
    rather almost nearly well then there here now when where why how instead
    perhaps maybe exactly roughly simply really actually literally probably possibly
    usually sometimes ever anyway anywhere everywhere somewhere nowhere away back
    forward forwards backward backwards together apart ahead aside else soon later
    earlier today tonight yesterday tomorrow meanwhile altogether indeed further
    furthermore moreover likewise also so thus hence overall upward upwards
    downward downwards inward inwards outward outwards sideways yes no okay ok oh
    please thanks thank hello goodbye whereby wherein thereby therein herein
    hereafter thereafter whereupon somehow someday sometime anyhow nonetheless
    nevertheless regardless respectively namely merely barely hardly scarcely
    mostly largely partly fully entirely completely totally absolutely certainly
    clearly obviously basically essentially especially particularly specifically
    generally typically normally naturally directly immediately finally eventually
    initially originally previously currently recently quickly slowly easily
    rarely seldom frequently constantly continually gradually suddenly equally
    slightly greatly highly deeply closely widely truly surely honestly frankly
""")
QUESTION = _words("what which who whom whose when where why how")
CONTRACTION_BASES = _words("""
    it that there here what who where let he she how
""")

CLOSED = (DETERMINERS | POSSESSIVES | PRONOUNS | PREPOSITIONS | CONJUNCTIONS
          | AUXILIARIES | MODALS | NUMBER_WORDS | ADVERBS | QUESTION)

# Words that mark the slot after them as a noun's (or its modifier's).
NOUN_MARKERS = (DETERMINERS | POSSESSIVES | NUMBER_WORDS) - _words("once twice thrice")
# ...and as a verb's.
VERB_MARKERS = SUBJECT_PRONOUNS | MODALS | _words("not n't don't doesn't didn't "
                                                  "won't can't cannot let's")
# After these and before a pause is where a predicate adjective sits.
ADJECTIVE_MARKERS = _words("""
    is are was were be been being seems seem become becomes became very too so
    quite rather fairly more most less least really pretty
""")


# ----------------------------------------------------------------------
# Lemmas
# ----------------------------------------------------------------------

IRREGULAR_PLURALS: dict[str, str] = {
    "feet": "foot", "teeth": "tooth", "men": "man", "women": "woman",
    "children": "child", "people": "person", "mice": "mouse", "geese": "goose",
    "lives": "life", "knives": "knife", "halves": "half", "leaves": "leaf",
    "shelves": "shelf", "wolves": "wolf", "calves": "calf", "loaves": "loaf",
    "thieves": "thief", "wives": "wife", "selves": "self", "elves": "elf",
    "radii": "radius", "vertices": "vertex", "indices": "index",
    "matrices": "matrix", "axes": "axis", "analyses": "analysis",
    "hypotheses": "hypothesis", "criteria": "criterion",
    "phenomena": "phenomenon", "polyhedra": "polyhedron",
    "icosahedra": "icosahedron", "dodecahedra": "dodecahedron",
    "tetrahedra": "tetrahedron", "octahedra": "octahedron", "apices": "apex",
    "lenses": "lens", "buses": "bus", "gases": "gas", "bases": "base",
    "oases": "oasis", "crises": "crisis", "theses": "thesis", "dice": "die",
    "eighths": "eighth", "sixths": "sixth", "fifths": "fifth", "tenths": "tenth",
    "thirds": "third", "quarters": "quarter", "fourths": "fourth",
    "twelfths": "twelfth", "hundredths": "hundredth", "thousandths": "thousandth",
    "rhombi": "rhombus", "focuses": "focus", "campuses": "campus",
    "calories": "calorie", "kilocalories": "kilocalorie", "movies": "movie",
    "cookies": "cookie", "zeroes": "zero", "heroes": "hero", "echoes": "echo",
    "middlemen": "middleman", "goes": "go", "isosceles": "isosceles",
    "descartes": "descartes", "pythagoras": "pythagoras", "chassis": "chassis",
}

# Words ending in s that are not plurals.
INVARIANT = _words("""
    series species gas lens physics mathematics economics analysis basis axis
    chassis news bias canvas atlas focus radius apparatus status surplus bus
    campus virus census bonus corpus genus nexus plexus thesis crisis oasis
    diagnosis emphasis hypothesis synthesis parenthesis ellipsis emphasis
    mechanics dynamics statics kinetics logistics ethics optics acoustics
    aesthetics graphics electronics avionics ergonomics metrics analytics
    tennis chaos cosmos pathos ethos bonus glass grass brass class mass pass
    moss boss loss cross gloss press stress truss dress process access success
    excess address business harness witness fitness thickness darkness
    brightness wellness illness hardness softness sharpness stiffness roughness
    smoothness flatness straightness roundness squareness tightness looseness
    wilderness awareness kindness sickness weakness usefulness goodness
    cleverness plus minus thus us yes this his its was has is less unless across
    always perhaps towards afterwards whereas sometimes gaps various
    serious previous obvious enormous famous generous nervous numerous jealous
    continuous tremendous dangerous curious anxious precious conscious
    ambitious ridiculous anonymous mountainous vigorous rigorous hazardous
    porous ferrous nonferrous
""") - _words("gaps")


def singular(word: str) -> str:
    """The singular of a noun, by rule, with exceptions listed."""
    if word in IRREGULAR_PLURALS:
        return IRREGULAR_PLURALS[word]
    if word in INVARIANT or len(word) <= 3:
        return word
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    # Only a doubled z takes -es (buzzes); sizes and prizes are size and prize.
    if word.endswith(("sses", "shes", "ches", "xes", "zzes")):
        return word[:-2]
    if word.endswith("s") and not word.endswith(("ss", "us", "is", "ics", "ous")):
        return word[:-1]
    return word


def lemma_of(low: str) -> str:
    """A token's dictionary form, for counting purposes.

    Possessives lose their ``'s``; plurals become singular. Verb forms in -ing and
    -ed are deliberately left alone: *felling* and *bucking* are the names of
    processes in this project, not just inflections, and the catalogue wants them.
    """
    if low.endswith("'s") and low[:-2] not in CONTRACTION_BASES:
        low = low[:-2]
    elif low.endswith("s'"):
        low = low[:-1]
    if "'" in low:
        return low
    return singular(low)


# ----------------------------------------------------------------------
# Evidence
# ----------------------------------------------------------------------

@dataclass
class Evidence:
    """What the company a word keeps says about it."""

    total: int = 0
    head: int = 0
    """After a noun marker (with any modifiers between) and before a pause."""
    marked: int = 0
    """Straight after a determiner, possessive or number."""
    plural_after_number: int = 0
    possessive: int = 0
    verb: int = 0
    adjective: int = 0
    capital_mid: int = 0
    """Capitalised where a sentence does not start: a name."""
    lower_mid: int = 0
    all_caps: int = 0

    @property
    def noun_score(self) -> int:
        return 2 * self.head + self.marked + 3 * self.plural_after_number \
            + 3 * self.possessive

    @property
    def other_score(self) -> int:
        return 2 * self.verb + 2 * self.adjective


def _is_boundary(tok: Tok | None) -> bool:
    if tok is None:
        return True
    if tok.kind == "punct":
        return True
    return tok.low in CLOSED and tok.low not in DETERMINERS - _words("that")


def _is_number(tok: Tok | None) -> bool:
    return tok is not None and (tok.kind == "num" or tok.low in NUMBER_WORDS)


@dataclass(frozen=True)
class Occurrence:
    lemma: str
    surface: str
    passage: int
    position: int


class Scan:
    """One pass over the corpus: every content word, its forms and its evidence."""

    def __init__(self, data: Corpus):
        self.data = data
        self.evidence: dict[str, Evidence] = defaultdict(Evidence)
        self.forms: dict[str, Counter] = defaultdict(Counter)
        self.passages: dict[str, set[int]] = defaultdict(set)
        self.works: dict[str, set[str]] = defaultdict(set)
        self.spoken: Counter = Counter()
        self.tokens: list[list[Tok]] = []
        for index, passage in enumerate(data.passages):
            toks = tokenize(passage.text)
            self.tokens.append(toks)
            self._score(index, passage, toks)

    def _score(self, index: int, passage: Passage, toks: list[Tok]) -> None:
        title_case = passage.field == "title"
        works = {f"{place.source}:{place.work}" for place in passage.places}
        for position, tok in enumerate(toks):
            if tok.kind not in ("word", "tech"):
                continue
            low = tok.low
            if low in CLOSED:
                continue
            if "'" in low and not low.endswith(("'s", "s'")):
                continue  # contractions: don't, it'll, I've
            if "-" in low and all(part in NUMBER_WORDS for part in low.split("-")):
                continue  # sixty-five is a number, however it is spelled
            lemma = lemma_of(low) if tok.kind == "word" else low
            if not lemma or lemma in CLOSED:
                continue
            ev = self.evidence[lemma]
            ev.total += 1
            self.forms[lemma][low] += 1
            self.passages[lemma].add(index)
            self.works[lemma].update(works)
            if passage.spoken:
                self.spoken[lemma] += 1

            prev = toks[position - 1] if position > 0 else None
            prev2 = toks[position - 2] if position > 1 else None
            nxt = toks[position + 1] if position + 1 < len(toks) else None

            if low.endswith(("'s", "s'")) and lemma != low:
                ev.possessive += 1
            if tok.kind == "tech":
                ev.marked += 1
                ev.head += 1
                continue

            sentence_start = prev is None or (prev.kind == "punct"
                                              and prev.text in ".!?:\"“(")
            if not title_case and not sentence_start:
                if tok.text.isupper() and len(tok.text) > 1:
                    ev.all_caps += 1
                elif tok.text[0].isupper():
                    ev.capital_mid += 1
                else:
                    ev.lower_mid += 1

            marked = prev is not None and prev.low in NOUN_MARKERS
            # One modifier between the marker and the word still counts: "the raw
            # wedge", "eight sawn faces".
            loosely_marked = (not marked and prev2 is not None
                              and prev2.low in NOUN_MARKERS and prev is not None
                              and prev.kind == "word" and prev.low not in CLOSED)
            if marked:
                ev.marked += 1
            if (marked or loosely_marked) and _is_boundary(nxt):
                ev.head += 1
            if _is_number(prev) and low != lemma and low.endswith("s"):
                ev.plural_after_number += 1

            if prev is not None and prev.low in VERB_MARKERS and not marked:
                if nxt is None or nxt.low in DETERMINERS | POSSESSIVES | PRONOUNS \
                        or _is_number(nxt) or nxt.low in PREPOSITIONS \
                        or nxt.kind == "punct":
                    ev.verb += 1
            elif prev is not None and prev.low == "to" and nxt is not None and (
                    nxt.low in DETERMINERS | POSSESSIVES | PRONOUNS
                    or _is_number(nxt)):
                ev.verb += 1
            if (prev is not None and prev.low in ADJECTIVE_MARKERS
                    and _is_boundary(nxt) and not marked):
                ev.adjective += 1


@lru_cache(maxsize=1)
def scan() -> Scan:
    return Scan(corpus())


# ----------------------------------------------------------------------
# The inventory
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Word:
    """One noun, with the numbers that justify calling it one."""

    lemma: str
    category: str
    count: int
    spoken: int
    passages: int
    works: tuple[str, ...]
    forms: tuple[tuple[str, int], ...]
    decided_by: str
    """``taxonomy`` when a person put it in a category, ``evidence`` otherwise."""
    confidence: float
    proper: bool
    example: str

    @property
    def films(self) -> tuple[str, ...]:
        return tuple(work for work in self.works if work.startswith("film:"))


def _example(data: Corpus, toks: list[list[Tok]], passage_ids: set[int],
             forms: set[str]) -> str:
    """The first spoken sentence using the word, or failing that any sentence."""
    ordered = sorted(passage_ids)
    for want_spoken in (True, False):
        for index in ordered:
            passage = data.passages[index]
            if passage.spoken != want_spoken:
                continue
            for sentence in sentences(passage.text):
                words = {tok.low for tok in tokenize(sentence)}
                if words & forms:
                    return sentence if len(sentence) <= 220 else sentence[:217] + "..."
    return ""


def classify(lemma: str, ev: Evidence) -> tuple[bool, float, bool]:
    """(is a noun, confidence, is a name) from the evidence alone."""
    proper = (ev.capital_mid >= 1 and ev.lower_mid == 0) or \
        (ev.all_caps >= 1 and ev.lower_mid == 0 and ev.capital_mid == 0
         and len(lemma) <= 6)
    if proper:
        return True, 0.9 if ev.capital_mid >= 2 else 0.6, True
    noun = ev.noun_score
    other = ev.other_score
    if noun == 0:
        return False, 0.0, False
    confidence = noun / (noun + other)
    return confidence >= 0.5, confidence, False


def needs_a_person(lemma: str) -> bool:
    """Shapes of word the evidence is least trustworthy about.

    A word ending in -ing, -ed or -ly is far more often a participle or an adverb
    than a noun ("curved", "measured", "evenly"), a one- or two-letter token is
    usually an equation symbol or a unit fragment, and a compound led by a number
    ("six-foot") is an adjective. None of these becomes a noun on evidence alone;
    each needs a person to have put it in a category.
    """
    if len(lemma) <= 2:
        return True
    if lemma.endswith(("ing", "ed", "ly")):
        return True
    head = lemma.split("-", 1)[0]
    return "-" in lemma and (head in NUMBER_WORDS or head in ("half", "quarter"))


@lru_cache(maxsize=1)
def inventory() -> tuple[Word, ...]:
    """Every noun in every script, most frequent first."""
    from .lexicon_taxonomy import NOT_NOUNS, category_of

    result = scan()
    words: list[Word] = []
    for lemma, ev in result.evidence.items():
        category = category_of(lemma)
        if lemma in NOT_NOUNS:
            continue
        if category is None and needs_a_person(lemma):
            continue
        noun, confidence, proper = classify(lemma, ev)
        if category is not None:
            decided = "taxonomy"
            noun = True
            confidence = max(confidence, 1.0)
        else:
            decided = "evidence"
        if not noun:
            continue
        forms = result.forms[lemma]
        words.append(Word(
            lemma=lemma,
            category=category or ("Names" if proper else "Uncategorised"),
            count=ev.total,
            spoken=result.spoken[lemma],
            passages=len(result.passages[lemma]),
            works=tuple(sorted(result.works[lemma])),
            forms=tuple(forms.most_common()),
            decided_by=decided,
            confidence=round(confidence, 3),
            proper=proper,
            example=_example(result.data, result.tokens, result.passages[lemma],
                             set(forms)),
        ))
    words.sort(key=lambda word: (-word.count, word.lemma))
    return tuple(words)


def candidates(minimum: int = 1) -> tuple[tuple[str, Evidence], ...]:
    """Every content word with its evidence, for the person curating the taxonomy."""
    result = scan()
    return tuple(sorted(
        ((lemma, ev) for lemma, ev in result.evidence.items() if ev.total >= minimum),
        key=lambda item: -item[1].total))


def uncategorised(minimum: int = 2) -> tuple[Word, ...]:
    """Nouns the evidence found and nobody has put in a category yet."""
    return tuple(word for word in inventory()
                 if word.decided_by == "evidence" and word.count >= minimum)


# ----------------------------------------------------------------------
# Phrases: the compound nouns ("board foot", "table saw", "pith line")
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Phrase:
    text: str
    head: str
    count: int
    works: tuple[str, ...]
    example: str


@lru_cache(maxsize=1)
def phrases(minimum: int = 3) -> tuple[Phrase, ...]:
    """Runs of nouns and modifiers ending in a noun, counted across the corpus.

    A run is broken by punctuation and by any closed-class word, so "the bark face of
    the wedge" yields "bark face" and not "face of the wedge". Every contiguous two to
    four word stretch of a run that ends in a noun is a candidate; the ones that recur
    are kept.
    """
    nouns = {word.lemma for word in inventory()}
    result = scan()
    data = result.data
    counts: Counter = Counter()
    works: dict[str, set[str]] = defaultdict(set)
    first: dict[str, int] = {}
    for index, toks in enumerate(result.tokens):
        passage = data.passages[index]
        run: list[str] = []

        def flush() -> None:
            for size in (2, 3, 4):
                for start in range(0, len(run) - size + 1):
                    gram = run[start:start + size]
                    if gram[-1] not in nouns:
                        continue
                    text = " ".join(gram)
                    counts[text] += 1
                    works[text].update(f"{p.source}:{p.work}" for p in passage.places)
                    first.setdefault(text, index)
            run.clear()

        for tok in toks:
            if tok.kind == "word" and tok.low not in CLOSED and "'" not in tok.low:
                run.append(lemma_of(tok.low))
            elif tok.kind == "tech":
                run.append(tok.low)
            else:
                flush()
        flush()

    kept = []
    for text, count in counts.items():
        if count < minimum:
            continue
        index = first[text]
        sentence = next((s for s in sentences(data.passages[index].text)
                         if text.split()[-1] in s.lower()), "")
        kept.append(Phrase(text=text, head=text.split()[-1], count=count,
                           works=tuple(sorted(works[text])), example=sentence[:220]))
    kept.sort(key=lambda phrase: (-phrase.count, phrase.text))
    return tuple(kept)


def word_report(limit: int = 60) -> str:
    words = inventory()
    by_category: dict[str, list[Word]] = defaultdict(list)
    for word in words:
        by_category[word.category].append(word)
    lines = [f"{len(words)} nouns across the scripts, in "
             f"{len(by_category)} categories", ""]
    for category in sorted(by_category, key=lambda c: -len(by_category[c])):
        members = by_category[category]
        lines.append(f"{category} ({len(members)})")
        lines.append("  " + ", ".join(f"{w.lemma} {w.count}"
                                      for w in members[:limit]))
        lines.append("")
    return "\n".join(lines)
