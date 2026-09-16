"""Integration guarantees for scene illustration metadata and book media UI."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from .book_visuals import attach_scene_still, book_fingerprint, plan_book_scenes, render_book_plan
from .storage import BookStore


class VisualBookChecks(unittest.TestCase):
    def test_legacy_structured_audit_survives_portable_merge(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as folder:
            source=BookStore(Path(folder)/'source')
            image=Path(folder)/'legacy.png'
            Image.new('RGB',(24,16),'green').save(image)
            audit={'source_lesson_title':'Two Trees, All at Once',
                   'source_files_sha256':{'lesson.py':'preserve-this-hash'},
                   'resolved_camera':{'eye':[1,2,3],'target':[0,0,0]}}
            result={'path':str(image),'caption':'An earlier scene still','provenance':audit}
            page_id=source.book['pages'][0]['id']
            key=attach_scene_still(source,page_id,result)
            self.assertIsInstance(source.book['assets'][key]['provenance'],str)
            target=BookStore(Path(folder)/'target')
            old_count=len(target.book['pages'])
            target.import_bundle(source.export_bundle())
            imported_page=target.book['pages'][old_count]
            asset=target.book['assets'][imported_page['figures'][0]]
            self.assertEqual(asset['source_scene']['render_metadata'],audit)
            self.assertEqual(result['provenance'],audit)

    def test_async_render_keeps_matched_text_hash_after_edit(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as folder:
            source=BookStore(Path(folder)/'source')
            image=Path(folder)/'frame.png'
            Image.new('RGB',(24,16),'green').save(image)
            page=source.book['pages'][0]
            planned_hash=hashlib.sha256((page['title']+'\n'+page['body']).encode('utf-8')).hexdigest()
            page['body']+='\nNew prose written while the image rendered.'
            current_hash=hashlib.sha256((page['title']+'\n'+page['body']).encode('utf-8')).hexdigest()
            key=attach_scene_still(source,page['id'],{'path':str(image)},source_text_sha256=planned_hash)
            asset=source.book['assets'][key]
            self.assertEqual(asset['source_text_sha256'],planned_hash)
            self.assertEqual(asset['attachment_text_sha256'],current_hash)
            self.assertTrue(asset['source_text_changed'])
            self.assertIn('New prose written',page['body'])

    def test_cached_scene_keeps_each_planned_passage_hash(self):
        scene={'id':'harvest:tree','lesson_key':'harvest','chapter_slug':'tree'}
        plan={'book_sha256':'original-book-snapshot','pages':[
            {'page_id':key,'title':key,'eligible':True,'text_sha256':digest,
             'suggestions':[{'scene':scene,'score':2}]} for key,digest in [('one','first-hash'),('two','second-hash')]
        ]}
        with tempfile.TemporaryDirectory() as folder, \
                patch('two_trees_codex.scene_stills.render_scene_still',return_value={'path':'fixture.png'}) as render:
            report=render_book_plan(plan,folder)
            self.assertEqual(render.call_count,1)
            self.assertEqual([item['source_text_sha256'] for item in report['completed']],['first-hash','second-hash'])
            self.assertEqual(report['book_sha256'],'original-book-snapshot')
            saved=json.loads(Path(report['manifest']).read_text(encoding='utf-8'))
            self.assertEqual(saved['completed'][1]['source_text_sha256'],'second-hash')

    def test_scene_recipe_survives_portable_merge(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as folder:
            source=BookStore(Path(folder)/'source')
            image=Path(folder)/'frame.png'
            Image.new('RGB',(24,16),'green').save(image)
            page_id=source.book['pages'][0]['id']
            result={'path':str(image),'caption':'Felled trunk example','provenance':'Source lesson model',
                    'recipe':{'lesson_key':'harvest','chapter_slug':'fell','progress':.6,'overlay':'original'}}
            key=attach_scene_still(source,page_id,result)
            target=BookStore(Path(folder)/'target')
            old_count=len(target.book['pages'])
            target.import_bundle(source.export_bundle())
            new_page=target.book['pages'][old_count]
            asset=target.book['assets'][new_page['figures'][0]]
            self.assertEqual(asset['scene_recipe'],result['recipe'])
            self.assertEqual(asset['source_page_id'],new_page['id'])
            self.assertEqual(asset['origin_page_id'],page_id)
            self.assertEqual(source.book['assets'][key]['claim_context'],asset['claim_context'])

    def test_fingerprint_ignores_save_timestamp_but_tracks_prose(self):
        with tempfile.TemporaryDirectory() as folder:
            book=BookStore(folder).book
            before=book_fingerprint(book)
            book['updated']='new save timestamp'
            self.assertEqual(before,book_fingerprint(book))
            book['pages'][0]['body']+=' New fact.'
            self.assertNotEqual(before,book_fingerprint(book))


def smoke_media_gui():
    import tkinter as tk
    from tkinter import ttk
    from .app import attach_book_tab
    with tempfile.TemporaryDirectory() as folder:
        root=tk.Tk(); root.withdraw()
        tabs=ttk.Notebook(root); tabs.pack(fill='both',expand=True)
        desk=attach_book_tab(tabs,folder)
        root.update()
        desk.editor.insert('end','\nThe new reader must show this unsaved sentence.')
        root.update()
        desk.tabs.select(desk.media.reader)
        root.update()
        assert 'unsaved sentence' in desk.media.read_text.get('1.0','end')
        current=desk.current
        desk.media.change_chapter(1)
        assert desk.current != current
        assert desk.title_var.get() in desk.media.read_text.get('1.0','end')
        desk.tabs.select(desk.media.scenes)
        scene={'id':'fixture:tree','lesson_key':'fixture','chapter_slug':'tree','stage':'tree','title':'A standing pine','summary':'Pine trunk and harvest','progress':.8}
        catalog={'scenes':[scene],'terms':[{'name':'pine','category':'wood','definition':'A source tree.'}],'concepts':[]}
        desk.media.accept_result('match',{'catalog':catalog,'matches':[{'scene':scene,'score':3,'matched_terms':['pine'],'reasons':['Source scene depicts pine trunk.']}],'page_id':desk.current})
        root.update()
        assert desk.media.selected_match()['scene']['id']=='fixture:tree'
        assert abs(desk.media.moment.get()-80)<.01
        searched_page=desk.current
        desk.media.change_chapter(1)
        assert not desk.media.matches
        desk.media.accept_result('match',{'catalog':catalog,'matches':[{'scene':scene,'score':3}],
                                         'page_id':searched_page})
        assert not desk.media.matches
        desk.capture()
        desk.media.publication={'book_scope':'Whole book','book_sha256':book_fingerprint(desk.store.book)}
        assert desk.media.publication_is_current()
        desk.editor.insert('end','\nA change after PDF export.')
        assert not desk.media.publication_is_current()
        desk.close()
    print('Media GUI passed: live prose, navigation, scene selection, stale search rejection and publication change detection')


if __name__=='__main__':
    unittest.main()
