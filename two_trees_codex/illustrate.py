"""Apply a reviewed illustration plan to the independent Codex manuscript."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import re

from .book_visuals import attach_scene_still
from .placement import prose_paragraph_count
from .storage import BookStore, DEFAULT_HOME, stamp


def coverage_report(book):
    chapters=[p for p in book['pages'] if re.match(r'^\d+\. ',p['title'])]
    return {'sections':len(book['pages']),
            'placed_figures':sum(len(p['figures']) for p in book['pages']),
            'illustrated_chapters':sum(bool(p['figures']) for p in chapters),
            'numbered_chapters':len(chapters),
            'unillustrated_chapters':[p['title'] for p in chapters if not p['figures']],
            'source_families':dict(Counter(book['assets'][key].get('source_family','Earlier book artwork')
                for p in book['pages'] for key in p['figures'])),
            'pages':[{'id':p['id'],'title':p['title'],'figures':len(p['figures'])} for p in book['pages']]}


def apply_illustration_plan(store,plan):
    """Append reviewed source images; repeated plans preserve existing author edits."""
    from PIL import Image
    pages={p['id']:p for p in store.book['pages']}
    entries=plan['illustrations']
    for item in entries:
        if item['page_id'] not in pages:
            raise ValueError('Unknown destination chapter: '+item['page_id'])
        if not item.get('id'):
            raise ValueError('Each illustration needs a stable plan ID.')
        with Image.open(item['result']['path']) as im:
            im.verify()
        anchor=item.get('after_paragraph')
        if anchor is not None and (isinstance(anchor,bool) or not isinstance(anchor,int)
                or not 0<=anchor<=prose_paragraph_count(pages[item['page_id']]['body'])):
            raise ValueError('Invalid paragraph placement for '+item['id'])
    existing={a.get('source_key') for a in store.book['assets'].values()}
    added=[]
    for item in entries:
        if item['id'] in existing:
            continue
        key=attach_scene_still(store,item['page_id'],item['result'],caption=item['caption'])
        asset=store.book['assets'][key]
        asset['source_key']=item['id']
        asset['source_family']=item.get('source_family','Project presentation')
        asset['visual_purpose']=item.get('purpose','')
        if item.get('after_paragraph') is not None:
            asset['book_placement']={'after_paragraph':item['after_paragraph']}
        asset['illustration_plan']=plan.get('id','reviewed-illustrations')
        existing.add(item['id'])
        added.append(key)
    if added:
        store.save()
    return {'added':added,**coverage_report(store.book)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan',type=Path)
    parser.add_argument('--workspace',type=Path,default=DEFAULT_HOME)
    args=parser.parse_args()
    store=BookStore(args.workspace)
    plan=json.loads(args.plan.read_text(encoding='utf-8'))
    result=apply_illustration_plan(store,plan)
    path=store.write_export('illustration-coverage','.json',json.dumps(result,indent=2,ensure_ascii=False))
    print(json.dumps({k:v for k,v in result.items() if k!='pages'},indent=2,ensure_ascii=False))
    print('Coverage report:',path)


if __name__=='__main__':
    main()
