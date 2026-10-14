"""Every book in the project, in one place: what it is, where its words are, what
builds it, and its newest printed copy in the library.

    py -3.12 -m books.shelf

The books share one method and one set of numbers, and they were written by
different hands at different times, so each keeps its own engine (the Python
package that typesets it). What they share now is this shelf, the ``books/``
folder for their words and pictures, the dated library for their PDFs, and the
composer (``books.composer``) for the books still to come.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Book:
    key: str
    title: str
    words: str
    """Where the writing lives (relative to the project)."""
    engine: str
    """The package that builds it."""
    build: str
    """The command that prints a new numbered copy."""
    output: str
    """The library item its PDF is filed under."""
    by: str
    status: str
    note: str = ""

    def latest(self) -> Path | None:
        import medialib
        return medialib.latest(self.output, ".pdf")


SHELF: tuple[Book, ...] = (
    Book("complete", "The 40 Hour Cabin: Complete Edition", "books/the-40-hour-cabin", "wedge_book",
         "py -3.12 -m wedge_book.print_edition", "the-40-hour-cabin",
         "Claude", "sold on the site with the code",
         "Ten parts; the database (wedge_book.sqlite3) mirrors the Markdown tree."),
    Book("master", "The 40 Hour Cabin: Master Edition", "books/master-edition", "master_book",
         "py -3.12 -m master_book.build", "the-40-hour-cabin-master-edition", "Claude",
         "reader's proof for friends", "Six rungs x twelve threads, both volumes bound in. "
         "Also opens in the composer as a loom."),
    Book("square", "'Square' on Demand", "books/square-on-demand", "square_book",
         "py -3.12 -m square_book.build", "square-on-demand", "Claude", "proof",
         "Building with wedges: pairs into squares, shims, joints."),
    Book("two-trees", "The 40 Hour Cabin: 2V Geodesic Dome Wedge Method (the Amazon paperback)",
         "books/two-trees", "two_v_demo.book", "py -3.12 two_v_demo/book_app.py --headless export",
         "2-trees", "DeepSeek", "on Amazon", "Its manuscript was edited by another agent; see its README."),
    Book("domology", "Domology (three books in one)", "domology", "domology", "py -3.12 -m domology.build",
         "domology-interior", "Claude", "engine and plates done; manuscript in progress"),
    Book("zome-zoomer", "The 40 Hour Cabin: Zome Zoomer (title page)", "wedge_zome", "wedge_zome.cover",
         "py -3.12 -m wedge_zome.cover", "zome-zoomer-title-page", "Claude", "title page only"),
    Book("codex-two-trees", "Two Trees (the Codex workspace)", "two_trees_codex", "two_trees_codex",
         "py -3.12 -m two_trees_codex", "", "Codex", "a separate app with its own workspace"),
)
BY_KEY = {b.key: b for b in SHELF}


def looms() -> list[str]:
    """Books made in the composer (``books/<slug>/loom.json``)."""
    return sorted(p.parent.name for p in (ROOT / "books").glob("*/loom.json"))


def report() -> str:
    lines = []
    for b in SHELF:
        latest = b.latest() if b.output else None
        lines.append(f"{b.title}\n  words   {b.words}\n  engine  {b.engine}  ({b.build})\n"
                     f"  by {b.by}; {b.status}\n  newest  "
                     f"{latest.relative_to(ROOT).as_posix() if latest else '(none in the library)'}")
    made = looms()
    lines.append(f"Composer books: {', '.join(made) if made else 'none yet'} "
                 "(py -3.12 -m books.composer)")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())
