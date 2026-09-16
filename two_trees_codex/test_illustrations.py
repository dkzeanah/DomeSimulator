"""Illustrations remain beside their prose through publishing and later merges."""
import json
from pathlib import Path
import tempfile
import unittest

from .illustrate import apply_illustration_plan
from .storage import BookStore


class IllustrationChecks(unittest.TestCase):
    def test_position_survives_html_markdown_and_portable_merge(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            store=BookStore(Path(tmp)/'book')
            page=store.book['pages'][0]
            page['body']='FIRST PARAGRAPH.\n\nSECOND PARAGRAPH.\n'
            page['figures']=[]
            image=Path(tmp)/'scene.png'
            Image.new('RGB',(30,20),'green').save(image)
            plan={'illustrations':[{'id':'sample-frame','page_id':page['id'],
                'result':{'path':str(image),'recipe':{'timestamp_seconds':12.5}},
                'caption':'THE INSERTED FIGURE','after_paragraph':1}]}
            apply_illustration_plan(store,plan)
            for path in (store.export_html([page]),store.export_markdown()):
                content=path.read_text(encoding='utf-8')
                self.assertLess(content.index('FIRST PARAGRAPH.'),content.index('THE INSERTED FIGURE'))
                self.assertLess(content.index('THE INSERTED FIGURE'),content.index('SECOND PARAGRAPH.'))
            target=BookStore(Path(tmp)/'merged')
            first=len(target.book['pages'])
            target.import_bundle(store.export_bundle())
            asset=target.book['assets'][target.book['pages'][first]['figures'][0]]
            self.assertEqual(asset['book_placement'],{'after_paragraph':1})
            self.assertEqual(asset['scene_recipe']['timestamp_seconds'],12.5)
            store.book['assets'][page['figures'][0]]['caption']='Author revised caption'
            again=apply_illustration_plan(store,plan)
            self.assertEqual(again['added'],[])
            self.assertEqual(store.book['assets'][page['figures'][0]]['caption'],'Author revised caption')

    def test_plan_rejects_unknown_chapter_before_adding_any_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=BookStore(tmp)
            before=json.dumps(store.book,sort_keys=True)
            with self.assertRaisesRegex(ValueError,'Unknown destination'):
                apply_illustration_plan(store,{'illustrations':[{'id':'x','page_id':'missing'}]})
            self.assertEqual(before,json.dumps(store.book,sort_keys=True))


if __name__=='__main__':
    unittest.main()
