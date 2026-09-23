# The Wedge Method - Book Builder

A self-contained Tkinter desktop application for developing **The Wedge Method: A Builder's Guide to Timber Geodesic Domes**.

## What it includes

- The complete canonical 5-part / 20-chapter book outline.
- All 152 planned manuscript subsections from the current book plan.
- A preloaded introduction draft and safety / engineering disclaimer.
- Development notes for every section.
- The original 29-item illustration program retained in code and project data.
- A structured chapter-by-chapter illustration plan so future LLM briefs carry the figure needs relevant to the section being written.
- A full build-out checklist: illustrations, worksheets, research, verification work, reference-build tasks, and final contradiction checking.
- Built-in author/LLM instructions designed to keep future additions consistent with the author's direct builder/technical voice while preventing fabricated build history, dimensions, testing, citations, or engineering claims.
- Automatic preservation/migration of missing canonical sections when an older project file is opened.
- JSON project save/load.
- Reference PDF reader using PyMuPDF.
- One-click extraction of the current reference-PDF page into the selected section's development notes.
- PDF source-list tracking.
- Manuscript PDF export.
- Development-outline PDF export, including notes and AI instructions.
- A machine-readable LLM handoff/import workflow.

## Install on Windows / PowerShell

```powershell
cd C:\path\to\wedge_method_book_app
py -3.12 -m pip install -r .\requirements.txt
py -3.12 .\app.py
```

Tkinter is included with normal Windows Python installations from python.org.

## Project files

Use **File -> Save Project As**. Projects are JSON and default to the extension:

```text
.wedgebook.json
```

The project stores manuscript text, development notes, the canonical outline, structured illustration plan, author/LLM instructions, build-out notes, and source PDF paths.

## Main LLM workflow

The intended drafting loop is now:

1. Click **Write Next Section**.
2. The application scans the book in order and finds the first section whose manuscript body is still empty.
3. That section is automatically selected in the outline.
4. A complete LLM brief is copied to the clipboard. It includes:
   - author/voice rules;
   - exact part/chapter/section;
   - zero-based import path;
   - reference-build context;
   - previous and next section so the LLM does not overlap them;
   - chapter development goal;
   - section-specific requirements;
   - existing draft, if any;
   - relevant chapter illustration requirements;
   - filenames of registered reference PDFs; and
   - a required import envelope.
5. Paste the brief into ChatGPT, Claude, DeepSeek, or another LLM.
6. Copy the complete response returned by the LLM.
7. In the app, click **Upload LLM Response** and then **Paste Clipboard**, or load a `.txt` / `.md` response file.
8. Click **Insert Response Into Book**.
9. The application verifies the target path and section title before inserting anything.
10. Manuscript prose is placed in **Draft Text** and unresolved research/figure/source/verification items are appended to **Development Notes**.
11. Click **Write Next Section** again to continue through the book.

You can still select any existing section and use **Copy Selected Brief** to revise or deliberately work out of sequence.

## LLM response envelope

The copied brief instructs the LLM to return this plain-text format:

```text
<<<WEDGEBOOK_SECTION_V1>>>
SCHEMA=wedgebook.section.v1
TARGET_PATH=0/0/0
CHAPTER_TITLE=1. Why Build a Dome?
TARGET_TITLE=What a geodesic dome is
<<<DRAFT_TEXT>>>
Finished manuscript prose goes here.
<<<DEVELOPMENT_NOTES_APPEND>>>
[FIGURE: any figure still needed]
[SOURCE NEEDED: any technical claim requiring support]
[VERIFY: any dimension or geometry not yet confirmed]
<<<END_WEDGEBOOK_SECTION>>>
```

The importer finds this envelope even if an LLM accidentally adds a small amount of text before or after it. The path and title must match the project before the content is accepted.

## Illustration breadth retained

The application still carries the full original illustration list:

- Complete 2V dome
- Exploded 2V dome
- A-member highlighting
- B-member highlighting
- Two triangle families
- Wedge cross-section
- Conventional rectangular strut versus wedge strut
- Log divided into wedge members
- Dimensional-lumber wedge-cutting layouts
- Inward wedge orientation
- Three-member vertex
- Five-member vertex
- Six-member vertex where applicable
- Dihedral relationship
- Triangle-to-triangle joint
- Base attachment
- First course
- Second course
- Apex assembly
- Door opening
- Reinforced opening
- Removable panel
- Insulated panel
- Utility column
- Floor utility interface
- Apex utility interface
- Gasketed service cap
- Prepared dome pad
- Completed dome cutaway

Those are also mapped into the chapters where they are most likely to be needed. Additional diagrams were added to the structured plan where they make the manual easier to build from, but none of the original figure requirements were removed.

## PDF workflow

Use **Reference PDF** to open a construction paper, source document, drawing package, existing dome reference, or your own PDF. Navigate pages in the right-side PDF Reader panel. **Append Page Text to Notes** copies extractable text from the current page into the selected chapter/section's development notes with the PDF filename and page number.

Scanned PDFs without a text layer will display normally, but this application intentionally does not automatically OCR them.

## Export modes

**Export Manuscript PDF** produces a clean draft containing the disclaimer, introduction, part/chapter/section structure, and written manuscript text.

**Export Development Outline PDF** also includes chapter development notes, section guidance, the book build-out plan, and the author/LLM instructions.

The default page size is 8.5 x 11 inches. The project format also supports `8x10` and `6x9` through `metadata.print_size` in the saved JSON file.

## Technical integrity rule

The LLM workflow deliberately separates manuscript prose from unresolved development work. The AI is instructed not to invent personal build history, dimensions, test results, load ratings, code compliance, citations, engineering approval, or measured prototype results. Missing information belongs in Development Notes until it is actually verified.
