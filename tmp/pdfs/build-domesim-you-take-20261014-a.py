from pathlib import Path
from xml.sax.saxutils import escape
import hashlib
import json
import sys

ROOT=Path(r'C:\Users\Don\Desktop\DomeSim')
sys.path.insert(0,str(ROOT))
from two_v_demo.deliverables import next_version_path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
from pypdf import PdfReader,PdfWriter

TITLE='DomeSim Investor Pitch'
LABEL='you-take by Codex'
PARAGRAPHS=[
'''We are building a modest, livable starting place for veterans, single mothers, craftsmen, college students, and bachelors. The product is basic infrastructure people can own, maintain, and improve as their lives change. A home should leave its owner enough money and time to build a life around it.''',
'''Think of it as a "glorified storage building" developed for living: a simple enclosure with the structure, weather protection, insulation, ventilation, utilities, and usable interior that occupancy requires. Keep the starting specification focused on everyday usefulness. Put effort into dependable essentials and connections that allow future improvements.''',
'''The audiences share a need for an attainable starting point, but their interiors will differ. A veteran may want independence and a practical community. A single mother needs predictable costs, privacy, and appropriate sleeping space for her family. A craftsman needs useful workspace. A student needs a stable base while studying; a bachelor may want a modest home that can adapt when his life changes. A common building platform should accommodate those differences.''',
'''The ownership template is the RV-and-pad arrangement. The occupant owns the building; a host provides prepared ground and service connections. The objective is to keep compatible equipment and improvements through repairs, upgrades, or relocation between qualified sites. Hosts invest in reusable site infrastructure, while owners invest in their own space. The RV comparison explains ownership and connections; the residential configuration still needs its own approval. Relocation is a planned operation, not effortless travel.''',
'''The benefits stack. A stripped-down construct reduces the variety of parts and decisions. Standard parts let a shop repeat fixtures, tasks, and checks. Repetition concentrates training and improvement on a manageable workflow, so each measured reduction in waste or rework can benefit later units. Modular panels and an accessible utility core are designed to support repair and upgrades. A defined pad interface separates site infrastructure from reusable building components. Together, these choices can simplify supply, preserve useful components, and make expansion less disruptive.''',
'''This is the code-house principle: shared specifications, reusable components, clear interfaces, testing, and continual improvement applied to a building. The existing software connects geometry to drawings, quantities, estimates, and instructions. The universal element is a defined family of compatible interfaces. The scale opportunity comes from qualifying that family, then repeating it: local fabricators could reproduce the plans, other makers could supply compatible components, and hosts could add serviced pads. Each participant expands the usefulness of the same system.''',
'''The case for resilience is that the platform has several useful applications to test. Storage buildings, workshops, studios, and residential packages can reuse a common production core while serving different customers. They can be validated in stages, with tooling and knowledge carried forward. Demand, margins, and suitability must be proved for each use. Large scale becomes plausible when the next building repeats a validated process and the next use configures the same platform.''',
'''The investment should establish a qualified residential prototype, measured fabrication and delivered costs, durable enclosure performance, workable host arrangements, and repeatable production. Then expand from demonstrated results. The aim is an enterprise that makes dependable starting space widely available, gives owners a way to improve without starting over, and earns its growth by making the same useful system better.''',
]
source_pdf=ROOT/'deliverables/pitch/domesim-code-house-investor-summary-v3.pdf'
source_md=ROOT/'deliverables/pitch/domesim-code-house-investor-summary-v3.md'
original_hash=hashlib.sha256(source_pdf.read_bytes()).hexdigest()
source_reader=PdfReader(str(source_pdf))
assert len(source_reader.pages)==2

page_w,page_h=letter
margin=43.2
usable_w=page_w-2*margin
usable_h=page_h-2*margin
chosen=None
for font_size in (11.0,10.9,10.8,10.7,10.6,10.5):
    title_style=ParagraphStyle('TakeTitle',fontName='Helvetica-Bold',fontSize=20,leading=24,textColor=colors.black)
    label_style=ParagraphStyle('TakeLabel',fontName='Helvetica',fontSize=10,leading=13,textColor=colors.black)
    body_style=ParagraphStyle('TakeBody',fontName='Helvetica',fontSize=font_size,leading=font_size*1.30,textColor=colors.black,allowWidows=0,allowOrphans=0)
    flow=[Paragraph(escape(TITLE),title_style),Spacer(1,3),Paragraph(escape(LABEL),label_style),Spacer(1,12)]
    for idx,text in enumerate(PARAGRAPHS):
        flow.append(Paragraph(escape(text),body_style))
        if idx<len(PARAGRAPHS)-1:
            flow.append(Spacer(1,8))
    height=sum(item.wrap(usable_w-12,usable_h)[1] for item in flow)
    if height<=usable_h-14:
        chosen=(font_size,height,flow)
        break
if chosen is None:
    raise RuntimeError('Pitch does not fit one readable page; revise before creating a PDF.')
font_size,height,flow=chosen
narrative_pdf=next_version_path(ROOT/'tmp/pdfs/domesim-you-take-narrative-20261014-a.pdf')
SimpleDocTemplate(str(narrative_pdf),pagesize=letter,leftMargin=margin,rightMargin=margin,topMargin=margin,bottomMargin=margin,title=TITLE,author='Codex',subject='you-take on the objective, audience, RV template, cumulative benefits and scale').build(flow)
assert len(PdfReader(str(narrative_pdf)).pages)==1
out_pdf=next_version_path(ROOT/'deliverables/pitch/domesim-you-take-investor-pitch.pdf')
out_md=next_version_path(ROOT/'deliverables/pitch/domesim-you-take-investor-pitch.md')
assert not out_pdf.exists() and not out_md.exists()
writer=PdfWriter()
writer.add_page(PdfReader(str(narrative_pdf)).pages[0])
writer.add_page(source_reader.pages[1])
writer.add_metadata({'/Title':'DomeSim Investor Pitch you-take','/Author':'Codex','/Subject':'Objective, customers, RV ownership template, repeatable modular scale and investor numbers'})
with out_pdf.open('xb') as stream:
    writer.write(stream)
reader=PdfReader(str(out_pdf))
assert len(reader.pages)==2
assert reader.pages[1].extract_text()==source_reader.pages[1].extract_text()
assert hashlib.sha256(source_pdf.read_bytes()).hexdigest()==original_hash
text=' '.join(reader.pages[0].extract_text().split())
for term in ('you-take','veterans','single mothers','craftsmen','college students','bachelors','RV-and-pad','benefits stack','code-house','qualified residential prototype'):
    assert term in text,term

source_markdown=source_md.read_text(encoding='utf-8')
marker='\n\n---\n\n# DomeSim Investor Numbers'
assert marker in source_markdown
numbers_markdown=source_markdown.split(marker,1)[1]
markdown='# '+TITLE+'\n\n*'+LABEL+'*\n\n'+'\n\n'.join(PARAGRAPHS)+marker+numbers_markdown
with out_md.open('x',encoding='utf-8',newline='\n') as stream:
    stream.write(markdown)
notes={
    'outputs':{'pdf':str(out_pdf),'editable_text':str(out_md)},
    'label':LABEL,'word_count':len(' '.join(PARAGRAPHS).split()),'body_font_pt':font_size,'flow_height_pt':height,'page_count':len(reader.pages),
    'prior_numbers_page_preserved':True,
    'user_objective':'Humble livable starting infrastructure for veterans, single mothers, craftsmen, college students and bachelors; RV ownership template; cumulative benefits of stripped-down, repeatable modular design; strong credible scale and resilience case.',
    'sources':[
        'CLAUDE.md','README.md','seed_model.py','park_model.py','docs/dome-park-brief.md',
        'books/the-40-hour-cabin/manuscript/03-build-it-so-you-can-change-your-mind.md',
        'books/the-40-hour-cabin/manuscript/45-why-a-network-beats-a-park.md',
        'books/the-40-hour-cabin/manuscript/48-a-house-that-moves-and-grows.md',
        'books/the-40-hour-cabin/manuscript/50-who-this-is-for.md',
        'books/the-40-hour-cabin/manuscript/63-sink-the-money-into-the-part-that-moves.md',
        'books/the-40-hour-cabin/manuscript/65-fifteen-buildings-from-one-body.md',
        'books/square-on-demand/manuscript/13-built-by-veterans.md',
    ],
    'claim_scope':'The first page is a proposed product and investment thesis. It does not promise success, demonstrated all-in affordability, legal RV status, qualified transport, existing host partners or operating alternative-use markets. Universal refers to a defined compatible product family. Numbers remain the previous independently checked model snapshot.',
}
notes_path=next_version_path(ROOT/'tmp/pdfs/domesim-you-take-20261014-a-notes.json')
with notes_path.open('x',encoding='utf-8') as stream:
    json.dump(notes,stream,indent=2)
print(json.dumps({key:notes[key] for key in ('outputs','word_count','body_font_pt','flow_height_pt','page_count','prior_numbers_page_preserved')},indent=2))
