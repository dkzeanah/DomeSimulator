"""Focused checks for persistence, safe merging, geometry inverses, and editor flow."""
import json
import math
from pathlib import Path
import tempfile
import unittest

from .storage import BookStore, ConflictError, seed_pages, markdown_html
from .calculations import radius_first, tree_first, physical_schedule, fit_physical_stock


class BookChecks(unittest.TestCase):
    def test_outline_and_future_records(self):
        pages = seed_pages()
        self.assertEqual(len([p for p in pages if p['kind'] == 'journal']), 14)
        self.assertEqual(len([p for p in pages if p['kind'] == 'part']), 7)
        self.assertEqual(len(set(p['id'] for p in pages)), len(pages))
        self.assertTrue(all(p['body'].strip() for p in pages))

    def test_save_reopen_and_conflict_preserves_disk(self):
        with tempfile.TemporaryDirectory() as folder:
            first = BookStore(folder)
            second = BookStore(folder)
            first.book['pages'][0]['body'] = 'Author edit that must survive'
            first.save()
            second.book['pages'][0]['body'] = 'Stale competing edit'
            with self.assertRaises(ConflictError):
                second.save()
            self.assertEqual(BookStore(folder).book['pages'][0]['body'], 'Author edit that must survive')
            exported = second.export_bundle()
            self.assertIn('Stale competing edit', exported.read_text(encoding='utf-8'))
            self.assertGreaterEqual(len(list((Path(folder)/'history').glob('*.json'))), 2)

    def test_bundle_appends_and_carries_image(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as folder:
            source = BookStore(Path(folder)/'source')
            png = Path(folder)/'test.png'
            Image.new('RGB', (8, 8), 'green').save(png)
            asset = source.add_asset(png, 'Test caption')
            source.book['pages'][0]['figures'] = [asset]
            bundle = source.export_bundle()
            target = BookStore(Path(folder)/'target')
            ids = [p['id'] for p in target.book['pages']]
            count = target.import_bundle(bundle)
            self.assertEqual(count, len(ids))
            self.assertEqual(ids, [p['id'] for p in target.book['pages'][:len(ids)]])
            new = target.book['pages'][len(ids)]
            self.assertNotIn(new['id'], ids)
            self.assertEqual(new['origin_id'], ids[0])
            self.assertTrue(target.asset_path(target.book['assets'][new['figures'][0]]).is_file())
            self.assertIn('data:image/png;base64', target.export_html().read_text(encoding='utf-8'))
            self.assertNotEqual(target.export_markdown(), target.export_markdown())

    def test_import_path_and_html_safety(self):
        with tempfile.TemporaryDirectory() as folder:
            book = BookStore(folder)
            with self.assertRaises(ValueError):
                book.asset_path({'path': '../outside.png'})
            bad = json.loads(book.export_bundle().read_text(encoding='utf-8'))
            bad['pages'][0]['id'] = '../../outside'
            with self.assertRaises(ValueError):
                book.validate(bad)
        self.assertNotIn('<script>', markdown_html('<script>alert(1)</script>'))
        self.assertNotIn('href="javascript:', markdown_html('[bad](javascript:alert(1))'))

    def test_inventory_losses_and_validation(self):
        result = tree_first()
        self.assertEqual((result['gross_blanks'], result['accepted_blanks'], result['surplus']), (128, 120, 0))
        self.assertGreater(result['minimum_trunk_ft'], 48)
        self.assertEqual(tree_first(rejected_per_tree=5)['surplus'], -2)
        for kwargs in ({'section_ft':float('nan')}, {'sections':2.5}, {'trim_total_in':72}, {'rejected_per_tree':65}):
            with self.assertRaises(ValueError):
                tree_first(**kwargs)
        self.assertAlmostEqual(radius_first(10)['base_polygon_area_sqft'], 293.892626, places=5)

    def test_physical_round_trip_all_orientations(self):
        for orientation in ('point_dome_in', 'point_panel_in', 'point_dome_out', 'point_panel_out'):
            forward = physical_schedule(10, 8, orientation, 3)
            inverse = fit_physical_stock(forward['max_blank_required_in'], 8, orientation, 3)
            self.assertAlmostEqual(inverse['radius_ft'], 10, places=5)
            self.assertEqual((forward['members'], forward['panels'], forward['unique_edges'], forward['seams']), (120,40,65,55))
            self.assertEqual(forward['edge_counts'], {'A':60,'B':60})


def smoke_gui():
    import tkinter as tk
    from tkinter import ttk
    from .app import attach_book_tab
    with tempfile.TemporaryDirectory() as folder:
        root = tk.Tk()
        root.withdraw()
        notebook = ttk.Notebook(root)
        notebook.pack(fill='both', expand=True)
        previous = ttk.Frame(notebook)
        notebook.add(previous, text='Existing tool')
        desk = attach_book_tab(notebook, folder)
        root.update()
        assert notebook.tabs()[-1] == str(desk)
        first = desk.current
        desk.editor.insert('end', '\nSaved author addition')
        root.update()
        assert desk.save()
        desk.add_page()
        desk.title_var.set('New chapter from GUI')
        desk.editor.insert('1.0', 'A real page body')
        root.update()
        assert desk.save()
        desk.move(-1)
        desk.save()
        desk.select_page(first)
        assert 'Saved author addition' in desk.editor.get('1.0','end')
        reopened = BookStore(folder)
        assert any(p['title'] == 'New chapter from GUI' and p['body'] == 'A real page body' for p in reopened.book['pages'])
        desk.close()
    print('GUI smoke passed: last tab, edit/save, new page, reorder, selection and reopen')


if __name__ == '__main__':
    unittest.main()
