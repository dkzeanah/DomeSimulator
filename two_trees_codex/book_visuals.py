"""Connect editable book passages to reusable video scenes without editing sources."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from .storage import stamp


def book_fingerprint(book):
    payload = {key: book.get(key) for key in ('title', 'author', 'edition', 'pages', 'assets')}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


def plan_book_scenes(book, catalog=None, limit=3):
    from .scene_catalog import build_catalog, suggest_scenes
    catalog = catalog or build_catalog()
    pages = []
    for page in book['pages']:
        # Empty field logs, metadata and references don't need a stock image on
        # every page. They remain matchable manually from the scene browser.
        eligible = page['kind'] in ('chapter', 'worked', 'plate')
        query = page['title'] + '\n' + page['body']
        matches = suggest_scenes(query, catalog, limit=limit) if eligible else []
        pages.append({'page_id': page['id'], 'title': page['title'], 'eligible': eligible,
                      'text_sha256': hashlib.sha256(query.encode('utf-8')).hexdigest(),
                      'suggestions': matches})
    return {'schema': 'two-trees-scene-plan/v1', 'created': stamp(),
            'book_sha256': book_fingerprint(book), 'pages': pages,
            'note': 'Ranked suggestions based on authored terms and scene purpose. Source-scene values are examples from their own configuration, not inferred field measurements.'}


def save_scene_plan(plan, output_dir):
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / ('scene-plan-' + stamp() + '.json')
    with target.open('x', encoding='utf-8') as stream:
        json.dump(plan, stream, ensure_ascii=False, indent=2)
    return target


def attach_scene_still(store, page_id, result, caption=None, source_text_sha256=None):
    """Append the image and complete reproducible recipe; never replace prose."""
    page = next(p for p in store.book['pages'] if p['id'] == page_id)
    source_caption = caption or result.get('caption') or 'Snapshot of a project video scene.'
    provenance = result.get('provenance', 'Still rendered by the existing video engine.')
    if isinstance(provenance, dict):
        # Early captures used a structured provenance field; keep their complete
        # audit in source_scene while giving the printed caption readable text.
        provenance = (f"Rendered from {provenance.get('source_lesson_title', 'the project video')} "
                      "using the existing scene painter and authored camera. Source-model example.")
    provenance = str(provenance)
    key = store.add_asset(result['path'], source_caption, provenance)
    asset = store.book['assets'][key]
    asset['scene_recipe'] = deepcopy(result.get('recipe', {}))
    asset['source_scene'] = deepcopy({k:v for k,v in result.items() if k not in ('path', 'caption', 'provenance')})
    if isinstance(result.get('provenance'), dict):
        legacy_key = 'legacy_provenance' if 'render_metadata' in asset['source_scene'] else 'render_metadata'
        asset['source_scene'][legacy_key] = deepcopy(result['provenance'])
    asset['source_page_id'] = page_id
    current_text_sha256 = hashlib.sha256((page['title']+'\n'+page['body']).encode('utf-8')).hexdigest()
    # A render can finish after its chapter has been edited. Keep the actual
    # matched passage fingerprint and record that divergence without replacing
    # the user's newer writing or misattributing it to the earlier scene choice.
    asset['source_text_sha256'] = source_text_sha256 or current_text_sha256
    asset['attachment_text_sha256'] = current_text_sha256
    asset['source_text_changed'] = bool(source_text_sha256 and source_text_sha256 != current_text_sha256)
    asset['claim_context'] = 'Source video example. Its model values must be reconciled with the book configuration before being described as build measurements.'
    page['figures'].append(key)
    return key


def render_book_plan(plan, output_dir, progress_callback=None):
    """Render the highest-ranked eligible suggestion per page, reusing recipes.

    Results are not attached until the GUI's main thread receives them. Failures
    are explicit per page, so one unsupported historical scene doesn't discard
    an otherwise useful collection.
    """
    from .scene_stills import render_scene_still
    jobs = [p for p in plan['pages'] if p['eligible'] and p['suggestions']]
    completed, failures, cache = [], [], {}
    for i, page in enumerate(jobs, 1):
        scene = page['suggestions'][0]['scene']
        cache_key = scene['id']
        if progress_callback:
            progress_callback(f"Scene {i}/{len(jobs)}: {page['title']}")
        try:
            if cache_key not in cache:
                cache[cache_key] = render_scene_still(scene, Path(output_dir), overlay='original')
            completed.append({'page_id': page['page_id'], 'result': cache[cache_key],
                              'matching': page['suggestions'][0],
                              'source_text_sha256': page.get('text_sha256')})
        except Exception as exc:
            failures.append({'page_id': page['page_id'], 'scene_id': scene['id'], 'error': str(exc)})
    report = {'schema':'two-trees-scene-render-report/v1','created':stamp(),
              'book_sha256':plan.get('book_sha256'),
              'completed':completed,'failures':failures,'unique_renders':len(cache)}
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / ('book-render-report-' + stamp() + '.json')
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    report['manifest'] = str(path)
    return report


def main():
    import argparse
    from .storage import BookStore, DEFAULT_HOME
    parser = argparse.ArgumentParser(description='Codex book scene plan and programmatic still rendering')
    parser.add_argument('--workspace', type=Path, default=DEFAULT_HOME)
    parser.add_argument('--render', action='store_true', help='Render top matched scenes; does not change manuscript')
    args = parser.parse_args()
    store = BookStore(args.workspace)
    plan = plan_book_scenes(store.book)
    print(save_scene_plan(plan, store.home/'scene-plans'))
    if args.render:
        print(render_book_plan(plan, store.home/'scene-stills', print)['manifest'])


if __name__ == '__main__':
    main()
