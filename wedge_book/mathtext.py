"""The book's LaTeX, set as type a printer can embed.

Chapters 1 and 2 carry 134 formulas written in LaTeX -- ``$$ ... $$`` for
display and ``\\( ... \\)`` inline. Nothing in the PDF path understood them,
so they would have printed as their own source: a reader would have met
``$$ c = 2R\\sin\\left(\\frac{\\theta}{2}\\right) $$`` in the middle of a
chapter about chord lengths.

This converts them to reportlab's inline markup, using real Unicode for the
symbols and ``<super>``/``<sub>`` for the scripts. It handles exactly the
commands the book uses and raises on anything else, because a formula that
silently loses a term is worse than one that fails the build.

FRACTIONS ARE SET INLINE

``\\frac{a}{b}`` becomes ``(a) / (b)`` rather than a stacked fraction.
Stacking needs a typesetter; parentheses need nothing and are unambiguous.
The parentheses are dropped where the part is a single token, so
``\\frac{D}{2}`` reads ``D / 2`` and not ``(D) / (2)``.
"""

from __future__ import annotations

import re

#: Every command this book actually uses. Anything else is an error rather
#: than a silent passthrough, so a new formula cannot arrive unrendered.
SYMBOLS = {
    "Delta": "\u0394",
    "alpha": "\u03b1",
    "beta": "\u03b2",
    "theta": "\u03b8",
    "circ": "\u00b0",
    "geq": "\u2265",
    "rightarrow": "\u2192",
    "times": "\u00d7",
    "cdot": "\u00b7",
    "pi": "\u03c0",
    "approx": "\u2248",
    "neq": "\u2260",
    "leq": "\u2264",
}

#: Function names, which are set upright rather than italic in real
#: typesetting and are left as plain words here.
FUNCTIONS = ("cos", "sin", "tan", "log", "ln", "max", "min")

KNOWN = set(SYMBOLS) | set(FUNCTIONS) | {"frac", "sqrt", "text", "left",
                                         "right", "mathrm", "operatorname"}

SUPERSCRIPT = re.compile(r"\^(?:\{([^{}]*)\}|(\S))")
SUBSCRIPT = re.compile(r"_(?:\{([^{}]*)\}|(\S))")


class MathError(ValueError):
    """A formula used something this converter does not know."""


def _balanced(text: str, start: int) -> tuple[str, int]:
    """Read a ``{...}`` group beginning at ``start``; return it and the end."""
    # LaTeX allows whitespace between a command and its argument, and the
    # book uses it: "\frac {a}{b}" appears alongside "\frac{a}{b}".
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text) or text[start] != "{":
        raise MathError(f"expected a brace group at {text[start:start + 12]!r}")
    depth = 0
    for index in range(start, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:index], index + 1
    raise MathError(f"unclosed brace in {text!r}")


def _wrap(part: str) -> str:
    """Parenthesise a fraction's half unless it is obviously atomic."""
    part = part.strip()
    if not part:
        return part
    if re.fullmatch(r"[A-Za-z0-9.\u0370-\u03ff]+"
                    r"(?:<su[pb]>[^<]*</su[pb]>)?", part):
        return part
    if part.startswith("(") and part.endswith(")"):
        return part
    return f"({part})"


def convert(latex: str) -> str:
    """One formula, as reportlab inline markup.

    The escaping and the script markup happen once, here, after the
    recursive expansion has finished. Doing them inside ``_expand`` escaped
    the tags a nested ``\\frac`` had already produced, so a fraction with a
    squared term in it printed ``&lt;super&gt;2&lt;/super&gt;``.
    """
    rendered = _expand(latex.strip())

    # Spacing around the relations, which LaTeX supplies and plain text does
    # not: "R=10 ft" wants to be "R = 10 ft".
    #
    # The character class leaves out < and >, and this runs before the
    # scripts are marked up. Including them, and running afterwards, put
    # spaces inside reportlab's own tags -- "<super>2</super>" came out as
    # "< super > 2 < /super >" and printed as literal angle brackets.
    rendered = re.sub(r"\s*([=≥≤≠≈→])\s*",
                      r" \1 ", rendered)
    rendered = rendered.replace("<", "&lt;").replace(">", "&gt;")

    # A degree sign is already a raised glyph, so "90^\circ" is 90° and not
    # 90 with a tiny superscript degree above it.
    rendered = rendered.replace("^°", "°")
    rendered = rendered.replace("^{°}", "°")

    rendered = SUPERSCRIPT.sub(
        lambda m: f"<super>{m.group(1) or m.group(2)}</super>", rendered)
    rendered = SUBSCRIPT.sub(
        lambda m: f"<sub>{m.group(1) or m.group(2)}</sub>", rendered)

    rendered = re.sub(r"\s{2,}", " ", rendered)
    return rendered.strip()


def _expand(latex: str) -> str:
    """Commands to symbols and text, with no escaping and no script markup."""
    text = latex.strip()
    # \left( and \right) are sizing hints with no meaning here.
    text = re.sub(r"\\left\s*", "", text)
    text = re.sub(r"\\right\s*", "", text)

    out: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char != "\\":
            out.append(char)
            index += 1
            continue
        match = re.match(r"\\([a-zA-Z]+)", text[index:])
        if not match:
            # An escaped brace or similar.
            out.append(text[index + 1:index + 2])
            index += 2
            continue
        name = match.group(1)
        index += match.end()
        if name not in KNOWN:
            raise MathError(f"unknown command \\{name} in {latex!r}")
        if name == "frac":
            numerator, index = _balanced(text, index)
            denominator, index = _balanced(text, index)
            out.append(f"{_wrap(_expand(numerator))} / "
                       f"{_wrap(_expand(denominator))}")
        elif name == "sqrt":
            body, index = _balanced(text, index)
            out.append(f"\u221a({_expand(body)})")
        elif name in ("text", "mathrm", "operatorname"):
            body, index = _balanced(text, index)
            out.append(body)
        elif name in FUNCTIONS:
            # LaTeX puts a thin space before a function name and plain text
            # has to put a real one, or "2ab\cos(C)" reads as "2abcos(C)".
            if out and (out[-1][-1:].isalnum() or out[-1][-1:] == ")"):
                out.append(" ")
            out.append(name)
        else:
            out.append(SYMBOLS[name])
    return "".join(out)


DISPLAY = re.compile(r"\$\$(.+?)\$\$", re.S)
INLINE = re.compile(r"\\\((.+?)\\\)", re.S)


def has_math(text: str) -> bool:
    return bool(DISPLAY.search(text) or INLINE.search(text))


def render_inline(text: str) -> str:
    """Replace ``\\( ... \\)`` spans in a line of prose."""
    return INLINE.sub(lambda m: f"<i>{convert(m.group(1))}</i>", text)


def display_blocks(text: str) -> list[str]:
    """Every ``$$ ... $$`` formula in a block, converted."""
    return [convert(m.group(1)) for m in DISPLAY.finditer(text)]


def is_display(block: str) -> bool:
    """A block that is nothing but one display formula."""
    return bool(re.fullmatch(r"\s*\$\$.+?\$\$\s*", block, re.S))


def validate_mathtext(book=None) -> dict:
    """Convert every formula in the book and count them.

    This is the check that matters: not that the converter works on an
    example, but that it works on all 134 of them, so the build cannot
    produce a page with raw LaTeX on it.
    """
    from . import store

    book = book or store.load_json()
    display = inline = 0
    for _part, chapter, section in book.sections:
        text = section.body or ""
        for match in DISPLAY.finditer(text):
            try:
                out = convert(match.group(1))
            except MathError as exc:
                raise AssertionError(
                    f"{chapter.title} / {section.title}: {exc}") from exc
            assert "\\" not in out, (
                f"{chapter.title} / {section.title}: a backslash survived "
                f"conversion: {out!r}")
            assert "$" not in out, out
            display += 1
        for match in INLINE.finditer(text):
            try:
                out = convert(match.group(1))
            except MathError as exc:
                raise AssertionError(
                    f"{chapter.title} / {section.title}: {exc}") from exc
            assert "\\" not in out, out
            inline += 1

    # And a few by hand, so a refactor that quietly stops converting
    # anything still fails.
    assert convert(r"R=\frac{D}{2}") == "R = D / 2"
    assert convert(r"c^2 = a^2 + b^2 - 2ab\cos(C)") == (
        "c<super>2</super> = a<super>2</super> + b<super>2</super> "
        "- 2ab cos(C)")
    assert convert(r"\theta") == "\u03b8"
    # A degree sign is already raised; superscripting it makes it a speck.
    assert convert(r"90^\circ") == "90\u00b0"
    assert convert(r"\sqrt{R^2}") == "\u221a(R<super>2</super>)"
    # A nested fraction must not have its scripts escaped a second time.
    assert convert(r"\frac{a^2}{2b}") == "(a<super>2</super>) / 2b"
    assert convert(r"R=10\text{ ft}") == "R = 10 ft"
    return {"display": display, "inline": inline}


if __name__ == "__main__":
    counts = validate_mathtext()
    print(f"converted {counts['display']} display and {counts['inline']} "
          f"inline formulas with no leftovers")
