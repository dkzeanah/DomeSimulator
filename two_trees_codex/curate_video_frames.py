"""Reproduce the visually reviewed September 12 Codex book film selection."""
from copy import deepcopy
import json
from pathlib import Path

from .storage import stamp
from .video_frames import contact_sheet


def main():
    home = Path(__file__).parent / 'workspace/expanded-art'
    batches = {
        'v1': ('video-20260912T064904694107Z-7c62b29a', [1,3,5,6,7,8,10,11,13,15,16,17,18,19,20,22,25,27,28]),
        'v2': ('video-20260912T103813587203Z-f337b60b', [1,2,3,5,7,8,9,10,11,12,13,14,15,16,17,18]),
        'v3': ('video-20260912T104021619767Z-b5225371', [1,2,3]),
    }
    corrections = {
        'video-v1-03': ('Forty complete triangular frames form a shell', 'Show the completed shell with an independent three-member frame for every panel'),
        'video-v1-06': ('The seam network through the whole shell', 'Follow the connected channels created by neighboring independent panel members'),
        'video-v1-13': ('Dome World: a timber workshop configuration', 'Show a building program generated from the Dome World model catalog'),
        'video-v1-16': ('Dome World: a treehouse dome configuration', 'Show a raised dome model as an example of a different building program'),
        'video-v1-20': ('The source model accounts for work by motion', 'Compare fastening, carrying, lifting, positioning, and recovery in the assembly-line model'),
        'video-v2-01': ('One eighth of the trunk, used as a member', 'Show the sawn faces, bark back, and pith point of an individual wedge'),
        'video-v2-02': ('A pinwheel frame: each butt meets the side of the next member', 'Show three independently made struts in the butt-to-side triangle assembly'),
        'video-v2-09': ('Deriving the two unit-radius chord factors', 'Show the completed geometry calculation; the source presentation uses its own reference member dimensions'),
        'video-v2-10': ('The reference shell is organized into rings and a crown', 'Show course heights and the relationship between the horizontal rings and the shell'),
        'video-v2-16': ('The same panel compared across different trunk diameters', 'Show which dimensions change with source timber and which geometric angles remain fixed'),
    }
    results = []
    for batch, (folder, indices) in batches.items():
        source_manifest = home / folder / 'manifest.json'
        data = json.loads(source_manifest.read_text(encoding='utf-8'))
        for index in indices:
            result = deepcopy(data['results'][index-1])
            result['id'] = f'video-{batch}-{index:02d}'
            result['source_index'] = index
            result['source_batch'] = batch
            result['source_manifest'] = str(source_manifest.resolve())
            if result['id'] in corrections:
                result['caption'], result['purpose'] = corrections[result['id']]
                result['recipe']['purpose'] = result['purpose']
            result['review'] = {'status': 'visually_selected', 'method': 'Full-frame contact sheet inspection',
                                'note': 'Preserve the source scene as an illustration. Small interface text is supporting context, not a substitute for the book explanation.'}
            results.append(result)
    destination = home / ('video-curated-' + stamp())
    destination.mkdir(parents=True, exist_ok=False)
    sheets = [contact_sheet(results[start:start+9], destination / f'contact-sheet-{start//9+1:02d}.jpg')
              for start in range(0, len(results), 9)]
    manifest = {'schema': 'two-trees-curated-video-illustrations/v1', 'created': stamp(),
                'count': len(results), 'results': results, 'contact_sheets': sheets,
                'source_read_only': True, 'reviewed_source_count': 51,
                'selection_note': '38 distinct shots retained after replacing partial builds, early math overlays, and weak catalog views. Figures remain original full frames with no reconstruction or invented detail.',
                'limitations': ['The existing source films contain values from their own scenario configurations.',
                                'The older Eight Cuts film uses a different tree inventory from the current 64-blanks-per-tree book plan.',
                                'No dedicated completed-film visual explaining green-wood drying or shrinkage was identified; do not present the diameter comparison as a shrinkage simulation.'],
                'manifest': str((destination / 'manifest.json').resolve())}
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(manifest['manifest'])
    for item in results:
        print(item['id'] + ' | ' + item['caption'] + ' | chapters ' + str(item['suggested_chapters']))


if __name__ == '__main__':
    main()
