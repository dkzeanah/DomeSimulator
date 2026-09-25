"""Every check this book has, in one process.

One process matters. Each module's ``--check`` passes on its own, and the
interesting failures are the ones that only appear when the modules share an
interpreter: a figure catalogue that caches a solved model, a number registry
that reads a constant another module has already changed, a book loaded twice
that is not the same book. Running them separately hides exactly the class of
bug that is hardest to find later.

The order is deliberate: the store first, because everything else loads the
book through it; then the numbers, because the figures and the alternatives
quote them; then the pictures; then the layout.

WHAT EACH ONE IS FOR

``store``         the book's three homes agree, and the prose does not
                  describe the other dome in this repository
``numbers``       every high-precision figure and every dollar figure in
                  71,000 words is one this code can produce
``alternatives``  every concept's table of options is in the book, current
``figures``       every shot the solver is asked for builds, is distinct, and
                  the book's own illustration plan is met or explained
``plates``        every film frame names a real chapter of a real film
``paragraphs``    a display formula is still alone on its line
``mathtext``      the LaTeX in the manuscript converts
``outline``       the new book's structure is coherent and its pictures exist
``graphics``      the seam section is a real slice, and the renders are drawn
``network``       the pad adds up for the tenant AND for the host
``systems``       every bill of materials is real, and the seam module's
                  water claim still loses to an inch of rain
``tooling``       every program the last part names exists and does what is
                  claimed of it
``tokens``        every live number in the prose resolves
``assembly``      the book builds, with no unresolved token and no missing
                  picture
``kdp``           the older typeset interior is a file Amazon will accept

``kdp`` is not in the default sweep because it lays out a 400-page book and
that is minutes rather than seconds. ``--full`` includes it.
"""

from __future__ import annotations

import time
import traceback

CHECKS: tuple[tuple[str, str, str], ...] = (
    ("store", "wedge_book.store", "validate_store"),
    ("numbers", "wedge_book.numbers", "validate_numbers"),
    ("outline", "wedge_book.outline", "validate_outline"),
    ("graphics", "wedge_book.graphics", "validate_graphics"),
    ("network", "wedge_book.network", "validate_network"),
    ("systems", "wedge_book.systems", "validate_systems"),
    ("tooling", "wedge_book.tooling", "validate_tooling"),
    ("tokens", "wedge_book.tokens", "validate_tokens"),
    ("assembly", "wedge_book.build", "validate_build"),
    ("alternatives", "wedge_book.alternatives", "validate_alternatives"),
    ("figures", "wedge_book.figures", "validate_figures"),
    ("plates", "wedge_book.plates", "validate_plates"),
    ("paragraphs", "wedge_book.paragraphs", "validate_paragraphs"),
    ("display", "wedge_book.paragraphs", "validate_display_alone"),
    ("mathtext", "wedge_book.mathtext", "validate_mathtext"),
)

SLOW: tuple[tuple[str, str, str], ...] = (
    ("kdp", "wedge_book.kdp", "validate_kdp"),
)


def run(full: bool = False, only: str = "") -> int:
    import importlib

    checks = CHECKS + (SLOW if full else ())
    if only:
        checks = tuple(c for c in checks if c[0] == only)
        if not checks:
            print(f"no check named {only!r}; have "
                  f"{[c[0] for c in CHECKS + SLOW]}")
            return 2
    failures = 0
    started = time.time()
    for name, module_name, function in checks:
        mark = time.time()
        try:
            module = importlib.import_module(module_name)
            getattr(module, function)()
        except Exception as exc:
            failures += 1
            print(f"  FAIL  {name:<14} {time.time() - mark:6.1f}s")
            text = str(exc).strip() or traceback.format_exc(limit=2)
            for line in text.splitlines()[:14]:
                print(f"          {line}")
        else:
            print(f"  ok    {name:<14} {time.time() - mark:6.1f}s")
    total = time.time() - started
    print(f"\n{len(checks) - failures} of {len(checks)} passed "
          f"in {total:.1f}s")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--full", action="store_true",
                        help="also build the PDF and measure it against KDP")
    parser.add_argument("--only", default="", help="run one check")
    args = parser.parse_args(argv)
    return run(full=args.full, only=args.only)


if __name__ == "__main__":
    raise SystemExit(main())
