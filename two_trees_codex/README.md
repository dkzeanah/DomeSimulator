# 2 trees: Build your (D)Home — Codex parallel edition

Double-click `Start-2-Trees-Codex.cmd` in the DomeSim folder. It loads the current
existing launcher and adds **2 trees · Book** as the final tab. All of Claude's
current tabs remain available. The book can also run alone with
`python -m two_trees_codex.app` from the repository root.

This implementation only adds `two_trees_codex/`, `launcher_two_trees_codex.py`,
and `Start-2-Trees-Codex.cmd`. It does not edit the existing launcher or any
`two_v_demo/book*` files, Claude's manuscript, or earlier deliverables.

## What is included

- 27 numbered chapters in seven parts, with a substantial initial manuscript.
- 14 daily field-record pages, worked calculations, source notes, and worksheets.
- Writing and private editorial notes, page type/strand/status, search, reordering,
  duplication, autosave, and snapshots of previous revisions.
- Local image library, captions, page placement, and project-derived render plates.
- Radius-first and tree-first sizing, actual member schedules, and the inverse
  physical-stock check through the existing raw-wedge simulator.
- An illustrated HTML reading/printing edition, Markdown export, and portable JSON
  bundles with images embedded. Exports get new names; previous exports remain.
- A live illustrated reader, searchable noun/concept catalog, and chapter-to-scene
  matching with excerpts explaining each suggestion.
- Programmatic snapshots of existing video scenes at a chosen animation moment,
  retaining the source camera, visual objects, icons, equations, and timed callouts.
- A paginated 6 by 9 inch PDF, matching page proofs, and silent MP4 readthroughs
  with adjustable reading time and chapter navigation metadata.

The proposed prose is grounded in the author's existing project notes. Field events
not yet documented remain explicitly open. The saw is named as the author specified,
120 Mark III; specifications, receipt, and real build measurements remain to record.

## Files and saves

`seed.md` contains the initial chapters. `storage.seed_pages()` adds the daily pages
at their place in the outline. On first open these populate `workspace/project.json`.
Subsequent opens preserve the author's saved writing; seeds never replace it.

`workspace/project.json` is authoritative. `workspace/pages/` contains readable
Markdown mirrors of each page. Edit through the desk or import a changed Markdown
file as an alternate; mirrors are regenerated from the saved project. Every save
keeps a timestamped snapshot in `workspace/history/`. Do not delete a save lock while
an editor is saving. After an abnormal process exit, close all book editors before
removing a stale `.save.lock` if one remains.

A second editor changing the same project triggers a conflict. The unsaved editor can
still export a bundle, then reopen and import its pages for reconciliation.

## Merge contract

Public integration entry point:

```python
from two_trees_codex.app import attach_book_tab
book_desk = attach_book_tab(notebook)  # after all other launcher tabs
```

`attach_book_tab` appends one tab and returns its frame. It is idempotent for an
existing BookDesk. It registers a window-close handler that saves pending writing;
if the combined launcher needs its own close handler, call `book_desk.save()` there
before destroying the root instead. The parallel wrapper delays this call until the
existing launcher's main loop, using a temporary in-process adapter. No disk patch
of the shared launcher is involved.

Bundle schema is `two-trees-book/v1`. Pages have stable `id`, `title`, `kind`,
`strand`, `status`, `body`, `notes`, and ordered `figures` asset IDs. `pages` array
order is reading order. Assets have a relative `path`, `caption`, `provenance`, and
embedded `data_base64` in portable exports. Import assigns new page and asset IDs,
preserves `origin_id`, and appends pages. It never silently replaces existing work.
Other Markdown/text manuscripts can be imported as alternate pages and reorganized.

Scene assets also preserve `scene_recipe`, `source_scene`, `source_page_id`,
`source_text_sha256`, and `claim_context`. A recipe records the lesson key, chapter
slug, progress, camera, dimensions, and overlay selection. The source audit includes
code hashes and model settings. Import remaps source page IDs and keeps their
original IDs; these additive fields can be retained when combining implementations.

The ordinary saved JSON stores relative image paths; portable exports embed the
files. To restore an older illustrated snapshot, retain its existing asset folder
and copy it into a separate workspace rather than replacing the active project.

## Geometry conventions

A is long and B is short. The 40-panel hemisphere has 120 wooden members, 65 unique
geometric edges, 55 interior seams and 10 exposed base edges. Every triangle owns
three members. The author's clarified pinwheel detail is end-to-side contact at
each cyclic corner, leaving two distinct members along a shared triangle axis.

Tree-first nominal arithmetic assumes a circular-sector inventory of eight blanks
per section. Gross count does not certify usable section or material. Physical fit
uses actual `physical_stock_length_in`, then adds the separately entered fabrication
allowance. The inverse is derived from two model evaluations and verified against a
third at the resulting radius; it fails explicitly if the closure differs by more
than 0.001 inch. No structural capacity or fastening adequacy is calculated here.

## Validation

`python -m unittest two_trees_codex.test_book -v` checks inventory loss, invalid
inputs, four physical inverse round trips, concurrent-save conflicts, portable image
round trips, additive merges, safe paths, and HTML escaping.

`python -c "from two_trees_codex.test_book import smoke_gui; smoke_gui()"` checks the
real Tk tab, edit/save/reopen, adding and reordering pages, and selection persistence.

`python -m two_trees_codex.render` creates another version of the model plates.
Rendering requires NumPy and Pillow, already used by this project. The core editor
uses Tk and the standard library; image actions use Pillow and calculations use NumPy.

## Artwork

Built-in image generation produced the editorial artwork; prompts and revision
status are preserved in `artwork/prompts.md`. Original drafts are retained there.
Concept artwork is distinct from solver-derived technical plates. The initial
workbench illustration needed a pinwheel correction, requested by the author;
technical explanations use the actual simulator's member meshes.

## Reading, scenes, and publishing

**Read** displays the current chapter or whole manuscript with its latest writing,
attached images and captions. It captures unsaved editor text when opened. Previous
and Next follow the manuscript order. **HTML copy** exports a self-contained browser
edition. Private editorial notes stay out of both reading editions and the PDF.

**Scenes** matches the selected chapter or a typed phrase against the existing
lesson narration, scene titles, visual purposes, authored term definitions and
concept links. Scores are lexical evidence scores, not probabilities. Choose a
result, set its moment from 0 to 100 percent, and use **Render & attach**. A
**3-moment sequence** captures 25, 60 and 85 percent of that same scene. The
whole-book plan stores ranked suggestions; **Render book matches** captures the
top suggestion for each eligible chapter, worked example or plate, sharing renders
where the same scene appears more than once. Empty journals and reference pages
remain manually matchable.

**Catalog** reads the existing project's noun inventory, categories, term definitions,
and concept recipes. It does not modify Claude's lexicon, scripts, painters, or
video engine. Source loading failures and unresolved noun classifications appear
in the exported catalog; an inventory is not a claim that every noun is perfectly
classified or that every word has a dedicated renderable object.

Each capture starts a separate hidden renderer process. `original` preserves the
video presentation; `clean` removes 2D overlays; `math` uses the engine's math
overlay. Snapshots use the authored chapter timeline. A separately narrated video
may have retimed its chapters, so the recipe describes normalized scene progress,
not a promised timestamp in an earlier MP4. All source numerical assumptions stay
with the caption and audit. Changing chapter prose does not silently change the
video model. For example, the source lesson's gas or day-count example is not
automatically a completed-build measurement.

**Publish → Build PDF + proofs** creates a dated publication from the whole book or
current chapter. The PDF has a table of contents, page numbers, chapter bookmarks,
and figures with captions. Proofs show its actual physical pages, including overflow.
The desk marks a saved publication as a snapshot when newer writing exists.
**Export still readthrough** uses those exact proof pages. It produces a silent
H.264 MP4 with whole pages contained in the video frame and chapter markers. The
default dwell is `max(6 seconds, page words / 130 words per minute)`, rounded up to
a video frame. A text transcript and JSON page/chapter timings accompany it. This
is a silent reading edition; no synthesized voice is included.

Media jobs run in the background while writing remains usable. Keep the launcher
open until the export finishes. Exports are new files and never overwrite previous
editions. New stills append to the destination page without replacing its writing.

## Programmatic use

Run from the repository root with the same Python used by the launcher:

```powershell
python -m two_trees_codex.scene_catalog --output-dir two_trees_codex/workspace/catalogs
python -m two_trees_codex.scene_catalog --query "eight wedges from each six foot trunk section"
python -m two_trees_codex.book_visuals
python -m two_trees_codex.book_visuals --render
python -m two_trees_codex.publish
python -m two_trees_codex.publish --page codex-tree-ledger --readthrough
```

`book_visuals --render` makes the plan and PNGs without attaching them; its render
report supports review before programmatic attachment. For an explicit scene:

```python
from pathlib import Path
from two_trees_codex.scene_catalog import build_catalog, get_scene
from two_trees_codex.scene_stills import render_scene_still

catalog = build_catalog()
scene = get_scene('harvest:explode', catalog)
frame = render_scene_still(scene, Path('two_trees_codex/workspace/scene-stills'),
                           progress=0.85, overlay='original')
print(frame['path'], frame['recipe'])
```

`publish --readthrough` creates a full video; without that flag it creates only the
PDF and proofs. Repeat `--page` to export selected source pages in manuscript order.
Use `--words-per-minute`, `--minimum-seconds`, and `--workspace` to control a run.
`--fps 1` is an efficient option for a static page readthrough; the default is 24.
Export manifests are the stable integration contract; local paths can be relocated
along with their publication directory.

The scene renderer requires the existing video runtime's NumPy, pygame and ModernGL
and a working OpenGL driver. `TWO_TREES_SCENE_PYTHON` can select that interpreter.
PDF export needs ReportLab, pypdf, pypdfium2 and Pillow; it automatically tries the
Codex bundled runtime when these are absent from the launcher's Python.
`TWO_TREES_PDF_PYTHON` overrides this selection. Video export reuses the project's
FFmpeg discovery; `TWO_TREES_FFMPEG` can supply an explicit executable.

Headless checks cover catalog evidence, scene request validation, recipe-preserving
merges, source isolation, PDF text/pagination/image placement, and video timing:

```powershell
python -m unittest two_trees_codex.test_book two_trees_codex.test_book_visuals two_trees_codex.test_scene_catalog two_trees_codex.test_scene_stills two_trees_codex.test_publication -v
```
