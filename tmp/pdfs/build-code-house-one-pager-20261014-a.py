from pathlib import Path
import json
import sys
from xml.sax.saxutils import escape

ROOT = Path(r'C:\Users\Don\Desktop\DomeSim')
sys.path.insert(0, str(ROOT))
from two_v_demo.deliverables import next_version_path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from pypdf import PdfReader

TITLE = 'DomeSim Code House Investor Summary'
SUBTITLE = 'A humble starting home built around single mothers and veterans'
PARAGRAPHS = [
    '''I am building DomeSim to make a humble, efficient starting home attainable for single mothers, veterans, and people working toward stability. The aim is a practical place to begin: useful shelter, manageable upkeep, and a way to add space or capability as resources grow. I call it a "code-house": a home that applies software development principles to its parts, construction, maintenance, and future upgrades.''',
    '''This purpose is personal. I grew up with a single mother whose housing burden took money and time our family needed. As a Navy veteran and programmer, I want to build something that gives people a firmer starting point. For a mother, that can mean more room in her budget and more time with her children. For a veteran, it can mean an independent home and opportunities to use fabrication and repair skills in a community. Their practical needs should shape the product.''',
    '''The codebase connects design, fabrication planning, production economics, and communication. Shared geometry and costing models generate dimensions, material quantities, cut lists, and cost and labor estimates. Interactive design tools let people inspect panels, layers, utilities, foundations, and whole sites. Fabrication exports turn solved parts into drawings and jig instructions. Assembly-line simulations examine bottlenecks, staffing, throughput, and sensitivity to assumptions. The project also supports illustrated books, narrated lessons, campaign releases, and a website with commerce and community features.''',
    '''The physical design follows the same logic as maintainable software: reuse standardized parts, define connections clearly, separate functions, and change one component without rebuilding everything. Repeated panel designs, reusable jigs, replaceable enclosure layers, and a concentrated utility core are intended to make assembly, repair, and upgrades easier. Standard pad connections support the longer-term vision of owners improving their home and moving it between host sites. In the software, shared specifications, geometric checks, and versioned outputs keep revisions traceable.''',
    '''Process optimization begins by simplifying the core workflow. A deliberately small recurring set of frame and panel fabrication operations gives training, batching, fixtures, and bottleneck improvement a focused target. The goal is to pay for precision and setup once, reuse them across builds, and measure whether each iteration reduces errors, waste, and effort. The proposed business opportunity includes plans, kits, components, utility cores, and compatible upgrades, supported by a proposed network of owners, pad hosts, paid quilters, and veteran builders.''',
    '''The next investment should fund measured prototypes, engineering review, enclosure and moisture testing through the seasons, tooling, and an initial repeatable production run. Working software and early frame experimentation provide a starting point; compliant residential use, full delivered cost, durability, and customer demand still require validation. Success means demonstrating a modest home people can afford to begin with and improve over time, while earning a sustainable business from making that process dependable.''',
]
URL = 'https://github.com/dkzeanah/DomeSimulator'
outdir = ROOT / 'deliverables' / 'pitch'
outdir.mkdir(parents=True, exist_ok=True)
pdf_path = next_version_path(outdir / 'domesim-code-house-investor-summary.pdf')
md_path = next_version_path(outdir / 'domesim-code-house-investor-summary.md')
assert not pdf_path.exists() and not md_path.exists()

page_w, page_h = letter
margin = 46.8
usable_w = page_w - 2 * margin
usable_h = page_h - 2 * margin
chosen = None
for size in (11.0, 10.9, 10.8, 10.7):
    title_style = ParagraphStyle('Title', fontName='Helvetica-Bold', fontSize=19.5, leading=23.5, textColor=colors.black)
    subtitle_style = ParagraphStyle('Subtitle', fontName='Helvetica', fontSize=10, leading=13, textColor=colors.black)
    body_style = ParagraphStyle('Body', fontName='Helvetica', fontSize=size, leading=size*1.31, textColor=colors.black, allowWidows=0, allowOrphans=0)
    source_style = ParagraphStyle('Source', fontName='Helvetica', fontSize=8.3, leading=11, textColor=colors.black)
    flow = [Paragraph(escape(TITLE), title_style), Spacer(1, 4), Paragraph(escape(SUBTITLE), subtitle_style), Spacer(1, 13)]
    for idx, content in enumerate(PARAGRAPHS):
        flow.append(Paragraph(escape(content), body_style))
        flow.append(Spacer(1, 9 if idx < len(PARAGRAPHS)-1 else 12))
    flow.append(Paragraph('Project source and documentation: <link href="'+URL+'">github.com/dkzeanah/DomeSimulator</link>', source_style))
    total_height = sum(item.wrap(usable_w, usable_h)[1] for item in flow)
    if total_height <= usable_h - 12:
        chosen = (size, total_height, flow)
        break
if chosen is None:
    raise RuntimeError('Content does not fit a readable one-page layout; shorten prose before writing outputs.')

size, total_height, flow = chosen
markdown = '# '+TITLE+'\n\n*'+SUBTITLE+'*\n\n'+'\n\n'.join(PARAGRAPHS)+'\n\nProject source and documentation: [DomeSimulator]('+URL+').\n'
with md_path.open('x', encoding='utf-8', newline='\n') as source_file:
    source_file.write(markdown)
doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, rightMargin=margin, leftMargin=margin, topMargin=margin, bottomMargin=margin, title=TITLE, author='DomeSim', subject='Investor summary of the codebase and modular starter housing campaign', creator='DomeSim investor summary')
doc.build(flow)
reader = PdfReader(str(pdf_path))
assert len(reader.pages) == 1, f'Expected one page, got {len(reader.pages)}'
text = reader.pages[0].extract_text()
for term in ('single mothers', 'veterans', 'code-house', 'validation', 'paid quilters'):
    assert term in text, f'Missing required content: {term}'

notes = {
    'outputs': {'pdf':str(pdf_path), 'editable_text':str(md_path)},
    'user_direction':'Single mothers and veterans are the core intended audience and customers; humble, efficient starting infrastructure, modularity, extendability and process optimization.',
    'sources':[
        'CLAUDE.md', 'README.md', 'dome_model.py', 'materials.py', 'mesh_builder.py',
        'geodesic_raw_wedge_dome_dihedral.py', 'dome_forge/designs.py', 'seed_model.py', 'al_build.py', 'assembly_line.py',
        'two_v_demo/wedge_geometry.py', 'two_v_demo/hubless_geometry.py', 'two_v_demo/panel_method.py', 'two_v_demo/dome_costing.py',
        'two_v_demo/franken_economics.py', 'two_v_demo/raw_wedge_bridge.py', 'two_v_demo/book_export.py', 'two_v_demo/release.py', 'two_v_demo/deliverables.py',
        'web/README.md', 'web/export_facts.py', 'web/server/src/routes',
        'books/the-40-hour-cabin/manuscript/03-build-it-so-you-can-change-your-mind.md',
        'books/the-40-hour-cabin/manuscript/05-why-i-built-the-ugly-one.md',
        'books/the-40-hour-cabin/manuscript/22-nine-processes-whatever-size-you-build.md',
        'books/the-40-hour-cabin/manuscript/50-who-this-is-for.md',
        'books/the-40-hour-cabin/manuscript/63-sink-the-money-into-the-part-that-moves.md',
        'books/the-40-hour-cabin/manuscript/71-so-a-mother-could-raise-her-child.md',
        'books/square-on-demand/manuscript/13-built-by-veterans.md', 'kickstarter.py',
    ],
    'claim_boundaries':'Commercial network, physical upgrades/transport and affordable residential delivery are proposed outcomes. Prototype status is described in project memoir, not independently verified. No measured cost/performance, approval, revenue or operating-program claims.',
    'word_count':len(' '.join(PARAGRAPHS).split()),
    'body_font_pt':size,
    'page_count':len(reader.pages),
    'flow_height_pt':round(total_height,2),
}
notes_path = ROOT / 'tmp' / 'pdfs' / 'code-house-one-pager-20261014-a-notes.json'
with notes_path.open('x', encoding='utf-8') as note_file:
    json.dump(notes,note_file,indent=2)
print(json.dumps({key:notes[key] for key in ('outputs','word_count','body_font_pt','page_count','flow_height_pt')},indent=2))
