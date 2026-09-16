"""Command-line PDF and still-page video publishing for the independent book."""
from copy import deepcopy
import argparse
import json
from pathlib import Path

from .book_visuals import book_fingerprint
from .publication import export_publication, export_readthrough
from .storage import BookStore, DEFAULT_HOME, stamp


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=DEFAULT_HOME)
    parser.add_argument('--page', action='append', help='Source page ID; repeat to select several in manuscript order')
    parser.add_argument('--readthrough', action='store_true', help='Also encode the PDF pages as a silent MP4')
    parser.add_argument('--words-per-minute', type=float, default=130)
    parser.add_argument('--minimum-seconds', type=float, default=6)
    parser.add_argument('--fps', type=int, default=24, help='Frames per second; 1 is efficient for pages with no motion')
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    store = BookStore(args.workspace)
    book = deepcopy(store.book)
    if args.page:
        requested = set(args.page)
        available = {p['id'] for p in book['pages']}
        if requested - available:
            parser.error('Unknown page IDs: ' + ', '.join(sorted(requested - available)))
        book['pages'] = [p for p in book['pages'] if p['id'] in requested]
    publication = export_publication(book, store.home, args.output_dir, print)
    publication['book_sha256'] = book_fingerprint(book)
    publication['book_source_ids'] = [p['id'] for p in book['pages']]
    publication['book_scope'] = 'Selected pages' if args.page else 'Whole book'
    index = store.home/'publication-index'
    index.mkdir(parents=True, exist_ok=True)
    with (index/(stamp()+'.json')).open('x', encoding='utf-8') as stream:
        json.dump(publication, stream, indent=2, ensure_ascii=False)
    print('PDF: ' + publication['pdf'])
    print('Page proofs and manifest: ' + publication['manifest'])
    if args.readthrough:
        result = export_readthrough(publication,
            words_per_minute=args.words_per_minute, minimum_seconds=args.minimum_seconds,
            fps=args.fps, progress_callback=print)
        print('Silent readthrough: ' + result['video'])
        print('Page and chapter timings: ' + result['manifest'])


if __name__ == '__main__':
    main()
