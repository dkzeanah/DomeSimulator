"""Build *The Wedge Method*: one HTML file, one PDF, from the manuscript.

Both come from :func:`two_v_demo.book_export.book_html`, which is the same
function that builds *2 Trees*, handed this book's outline, its manuscript
folder, its pictures and its numbers. One source behind the screen and the
page, so the thing you read and the thing you send somebody cannot be
different books.

Neither export ever overwrites: a rebuild writes ``-v2`` beside the last one.
"""

from __future__ import annotations

from pathlib import Path

from two_v_demo import book_export

from . import outline, tokens


def html(strict: bool = True) -> book_export.BuildReport:
    return book_export.export_html(
        root=outline.MANUSCRIPT_DIR, out_dir=outline.EXPORT_DIR,
        book=outline.BOOK, strict=strict, stem=outline.STEM,
        figure_dir=outline.FIGURE_DIR, tokens=tokens.resolve)


def pdf(strict: bool = True,
        backend: str = "auto") -> book_export.BuildReport:
    return book_export.export_pdf(
        root=outline.MANUSCRIPT_DIR, out_dir=outline.EXPORT_DIR,
        book=outline.BOOK, strict=strict, backend=backend,
        stem=outline.STEM, figure_dir=outline.FIGURE_DIR,
        tokens=tokens.resolve)


def document(strict: bool = True) -> tuple[str, book_export.BuildReport]:
    return book_export.book_html(
        root=outline.MANUSCRIPT_DIR, book=outline.BOOK,
        embed_images=False, strict=strict,
        figure_dir=outline.FIGURE_DIR, tokens=tokens.resolve)


def written() -> tuple[int, int]:
    """How many chapters have prose in them, out of how many."""
    from two_v_demo import book_manuscript as manuscript

    started = sum(
        1 for chapter in outline.BOOK.chapters
        if manuscript.read_chapter(chapter, outline.MANUSCRIPT_DIR).is_started)
    return started, len(outline.BOOK.chapters)


def validate_build() -> None:
    """The book assembles, resolves every token, and finds every picture."""
    text, report = document(strict=True)
    assert "{{" not in text, "an unresolved token reached the reader"
    assert outline.TITLE in text
    assert report.figures_found >= 1, report

    # A picture named in a written chapter has to be on disk. The engine
    # drops a missing one silently, which is right for a reader and wrong
    # for a build.
    assert not report.figures_missing, (
        f"{len(report.figures_missing)} figures are referenced and not "
        f"rendered: {list(report.figures_missing)[:8]}")

    started, total = written()
    assert started >= 1, "no chapter has any prose in it"
    # Whatever is written has to be readable prose, not the scaffold.
    assert "not written yet" not in text or started < total


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pdf", action="store_true")
    parser.add_argument("--html", action="store_true")
    parser.add_argument("--backend", default="auto")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    outline.validate_outline()
    tokens.validate_tokens()
    validate_build()
    started, total = written()
    print(f"{outline.TITLE}: {started} of {total} chapters written")
    if args.check:
        print("build ok")
        return 0

    if args.html or not args.pdf:
        report = html()
        print(f"  html  {report.path}  "
              f"({report.figures_found} figures)")
    if args.pdf:
        report = pdf(backend=args.backend)
        print(f"  pdf   {report.path}  via {report.backend}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
