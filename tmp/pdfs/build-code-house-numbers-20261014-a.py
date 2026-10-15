from pathlib import Path
from xml.sax.saxutils import escape
import hashlib
import json
import math
import sys

ROOT = Path(r'C:\Users\Don\Desktop\DomeSim')
sys.path.insert(0, str(ROOT))
import seed_model as s
import kickstarter as k
from two_v_demo.deliverables import next_version_path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from pypdf import PdfReader, PdfWriter

source_pdf = ROOT / 'deliverables/pitch/domesim-code-house-investor-summary-v2.pdf'
source_md = ROOT / 'deliverables/pitch/domesim-code-house-investor-summary-v2.md'
original_hash = hashlib.sha256(source_pdf.read_bytes()).hexdigest()
overrides = s.load_overrides()
q = s.quote()
c = k.cost_stack()
assert abs(q.price-c.price) < 0.001
assert abs(q.cost_to_build-(q.direct_cost+q.overhead+q.warranty)) < 0.001
assert abs(q.price-q.cost_to_build*(1+s.declared('maker_markup_fraction'))) < 0.001
assert q.fitout.key == 'stem_cell'

money = lambda value: f'${value:,.2f}'
whole = lambda value: f'${value:,.0f}'
percent = lambda value: f'{value*100:.1f}%'
markup = s.declared('maker_markup_fraction')
margin = q.gross_profit/q.price
freight = s.declared('freight_usd')
placement = q.price+q.pad_cost+freight
budget = {line.key:line.usd for line in k.goal_lines()}
funding_groups = [
    ('Production tooling',sum(budget[key] for key in ('cnc_router','cnc_plasma','laser_cutter','strut_tooling','automation'))),
    ('Validation and R&D',sum(budget[key] for key in ('test_platform','instrumentation','hub_rnd','composite_rnd','engineering'))),
    ('Quilts and fulfillment',budget['quilt_seed']+budget['fulfilment']),
]
assert abs(sum(v for _,v in funding_groups)-k.goal()) < 0.001
prototype = q.cost_to_build+q.pad_cost
potential_gap = prototype-budget['test_platform']
reconciled_goal = k.goal()+potential_gap
sensitivity = [(change,q.cost_to_build*(1+change),q.price-q.cost_to_build*(1+change)) for change in (0.0,0.1,0.2)]
productivity_target = 0.20
hours_saved = q.labour_hours*productivity_target
labor_savings = q.labour_cost*productivity_target
loaded_savings = labor_savings*(1+s.declared('shop_overhead_fraction')+s.declared('warranty_reserve_fraction'))

TITLE = 'DomeSim Investor Numbers'
SUBTITLE = 'USD model estimates recomputed October 14 2026'
reference = (f'Reference is the <b>base infrastructure article</b>: customer-supplied trees, soft cap, utility core, window AC and <b>zero quilt insulation</b>. '
             f'Solver geometry: {q.geometry.diameter_ft:.2f} ft across; {q.geometry.floor_decagon_sqft:.0f} sq ft of ten-sided floor; '
             f'{sum(face.count for face in q.geometry.faces)} panels of two shapes and {q.geometry.member_count} members. This is not a finished residential-home price.')
inputs = [
    ['Model input','Declared assumption','Model input','Declared assumption'],
    ['Loaded labor rate',whole(s.declared('labour_usd_per_hour'))+'/hour','Shop overhead',percent(s.declared('shop_overhead_fraction'))+' of direct cost'],
    ['Warranty reserve',percent(s.declared('warranty_reserve_fraction'))+' of direct cost','Maker markup',percent(markup)+' of build cost'],
    ['Regional freight',whole(freight),'Timber acquisition','$0; owner supplies trees'],
]
unit_rows = [
    ['Unit economics','USD'],
    ['Materials and components',money(q.material_cost)],
    [f'Shop/yard labor ({q.labour_hours:.1f} hours)',money(q.labour_cost)],
    ['Direct cost subtotal',money(q.direct_cost)],
    ['Overhead allowance',money(q.overhead)],
    ['Warranty reserve',money(q.warranty)],
    ['Modeled build cost',money(q.cost_to_build)],
    ['Base article list price',money(q.price)],
    ['Price less build cost',money(q.gross_profit)],
    ['Share of selling price',percent(margin)],
]
fund_rows = [['Campaign allocation','USD']]+[[label,whole(value)] for label,value in funding_groups]+[['Declared total',whole(k.goal())]]
formula = (f'<b>Margin math:</b> {money(q.cost_to_build)} x (1 + {percent(markup)}) = {money(q.price)}. '
           f'({money(q.price)} - {money(q.cost_to_build)}) / {money(q.price)} = {percent(margin)}. '
           'This is surplus after modeled overhead and warranty, not after-tax profit or investor return.')
reconciliation = (f'<b>Budget reconciliation:</b> the test dome/pad line is {whole(budget["test_platform"])}; the modeled base build plus pad is {whole(prototype)}. '
                  f'If that line must fund this scope, its gap is {whole(potential_gap)}. Replacing only it gives {whole(reconciled_goal)} before fees and contingency. '
                  'Salary and marketing are not itemized in the declared goal.')
placement_text = (f'<b>Placement scope:</b> buyer dome plus freight {whole(q.price+freight)}; separate host pad {whole(q.pad_cost)}; combined base infrastructure {whole(placement)}. '
                  'Land, tax, complete site development, residential fit-out/insulation, and customer-site setup remain outside this package.')
sense_rows = [['Build-cost scenario','Modeled cost','Price less cost','Share of price']]
for change,cost,spread in sensitivity:
    sense_rows.append(['Baseline' if change == 0 else f'Cost +{change*100:.0f}%',money(cost),money(spread),percent(spread/q.price)])
productivity = (f'<b>Repeatability target:</b> 20% fewer modeled labor hours would save {hours_saved:.1f} hours and {whole(loaded_savings)}/unit including proportional overhead/warranty, '
                'at unchanged rates. This is a scenario, not an achieved improvement. Sale price is held fixed in the sensitivity table.')
validation = ('<b>Before underwriting scale:</b> measure person-hours, site setup, finished occupancy costs, production capacity, demand and working capital. '
              'The 67.3-hour estimate is shop/yard work, not a complete-home schedule. Model validators passed; physical performance and operating break-even still need evidence.')
sources = 'Calculation sources: seed_model.quote(), seed_model.seed_geometry(), kickstarter.cost_stack() and kickstarter.goal_lines(). Material rates and the campaign budget are project allowances, not new supplier quotations.'

page_w,page_h = letter
page_margin = 42
usable_w = page_w-2*page_margin
usable_h = page_h-2*page_margin
black = colors.black
border = colors.HexColor('#D9D9D9')
header_bg = colors.HexColor('#243746')
row_tint = colors.HexColor('#F3F6F8')

chosen = None
for font_size in (9.8,9.6,9.4,9.2):
    styles = {
        'title':ParagraphStyle('NumbersTitle',fontName='Helvetica-Bold',fontSize=19,leading=23,textColor=black),
        'subtitle':ParagraphStyle('NumbersSubtitle',fontName='Helvetica',fontSize=9.5,leading=12,textColor=black),
        'body':ParagraphStyle('NumbersBody',fontName='Helvetica',fontSize=font_size,leading=font_size*1.26,textColor=black),
        'cell':ParagraphStyle('NumbersCell',fontName='Helvetica',fontSize=font_size-0.2,leading=(font_size-0.2)*1.17,textColor=black),
        'header':ParagraphStyle('NumbersHeader',fontName='Helvetica-Bold',fontSize=font_size-0.2,leading=(font_size-0.2)*1.17,textColor=colors.white),
        'source':ParagraphStyle('NumbersSource',fontName='Helvetica',fontSize=8,leading=10,textColor=black),
    }
    def P(text,style='body'):
        return Paragraph(text,styles[style])
    def numeric_table(rows,widths,emphasize=()):
        data=[]
        for idx,row in enumerate(rows):
            data.append([P(escape(str(cell)),'header' if idx==0 else 'cell') for cell in row])
        table=Table(data,colWidths=widths,hAlign='LEFT')
        commands=[('GRID',(0,0),(-1,-1),0.45,border),('BACKGROUND',(0,0),(-1,0),header_bg),
                  ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),4),
                  ('BOTTOMPADDING',(0,0),(-1,-1),4),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6)]
        for idx in range(1,len(rows)):
            if idx % 2 == 0:
                commands.append(('BACKGROUND',(0,idx),(-1,idx),row_tint))
        for idx in emphasize:
            for cell in data[idx]:
                cell.style=ParagraphStyle('Emphasized',parent=styles['cell'],fontName='Helvetica-Bold')
        table.setStyle(TableStyle(commands))
        return table
    left_w=286
    gap=13
    right_w=usable_w-left_w-gap
    left=[numeric_table(unit_rows,[190,left_w-190],emphasize=(6,7,8)),Spacer(1,7),P(formula)]
    right=[numeric_table(fund_rows,[right_w-79,79],emphasize=(4,)),Spacer(1,7),P(reconciliation)]
    columns=Table([[left,'',right]],colWidths=[left_w,gap,right_w])
    columns.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    flow=[P(escape(TITLE),'title'),Spacer(1,3),P(escape(SUBTITLE),'subtitle'),Spacer(1,9),P(reference),Spacer(1,8),
          numeric_table(inputs,[124,usable_w/2-124,120,usable_w/2-120]),Spacer(1,9),columns,Spacer(1,9),
          P(placement_text),Spacer(1,8),numeric_table(sense_rows,[173,112,121,usable_w-406]),Spacer(1,8),
          P(productivity),Spacer(1,7),P(validation),Spacer(1,7),P(sources,'source')]
    height=sum(item.wrap(usable_w,usable_h)[1] for item in flow)
    if height <= usable_h-12:
        chosen=(font_size,height,flow)
        break
if chosen is None:
    raise RuntimeError('Numbers page exceeds one readable page; shorten content before writing.')

font_size,height,flow=chosen
numbers_path=next_version_path(ROOT/'tmp/pdfs/code-house-numbers-20261014-a.pdf')
assert not numbers_path.exists()
SimpleDocTemplate(str(numbers_path),pagesize=letter,leftMargin=page_margin,rightMargin=page_margin,topMargin=page_margin,bottomMargin=page_margin,
                  title=TITLE,author='DomeSim',subject='Computed base-unit economics and declared campaign funding').build(flow)
assert len(PdfReader(str(numbers_path)).pages)==1
out_pdf=next_version_path(ROOT/'deliverables/pitch/domesim-code-house-investor-summary.pdf')
out_md=next_version_path(ROOT/'deliverables/pitch/domesim-code-house-investor-summary.md')
assert not out_pdf.exists() and not out_md.exists()
writer=PdfWriter()
writer.append(str(source_pdf))
writer.append(str(numbers_path))
writer.add_metadata({'/Title':'DomeSim Code House Investor Summary and Numbers','/Author':'DomeSim','/Subject':'Mission, codebase, base-unit economics and development capital'})
with out_pdf.open('xb') as stream:
    writer.write(stream)
reader=PdfReader(str(out_pdf))
assert len(reader.pages)==2
assert reader.pages[0].extract_text()==PdfReader(str(source_pdf)).pages[0].extract_text()
assert hashlib.sha256(source_pdf.read_bytes()).hexdigest()==original_hash
rendered_text=' '.join(reader.pages[1].extract_text().split())
for expected in (money(q.cost_to_build),money(q.price),whole(k.goal()),whole(reconciled_goal),'zero quilt insulation','not a finished residential'):
    assert expected in rendered_text,expected

def md_table(rows):
    return '\n'.join(['| '+' | '.join(rows[0])+' |','| '+' | '.join(['---']*len(rows[0]))+' |']+['| '+' | '.join(row)+' |' for row in rows[1:]])
def plain(text):
    return text.replace('<b>','**').replace('</b>','**')
appendix='\n\n---\n\n# '+TITLE+'\n\n*'+SUBTITLE+'*\n\n'+plain(reference)+'\n\n'+md_table(inputs)+'\n\n'+md_table(unit_rows)+'\n\n'+plain(formula)+'\n\n'+md_table(fund_rows)+'\n\n'+plain(reconciliation)+'\n\n'+plain(placement_text)+'\n\n'+md_table(sense_rows)+'\n\n'+plain(productivity)+'\n\n'+plain(validation)+'\n\n'+sources+'\n'
with out_md.open('x',encoding='utf-8',newline='\n') as stream:
    stream.write(source_md.read_text(encoding='utf-8').rstrip()+appendix)

notes={
    'outputs':{'pdf':str(out_pdf),'editable_text':str(out_md),'numbers_pdf_for_QA':str(numbers_path)},
    'recomputed_date':'2026-10-14','loaded_overrides':overrides,
    'configuration':{'fitout':q.fitout.key,'shell':'soft','frame_stock':q.frame_stock,'quilt_layers':0,'optional_groups':list(s.STANDARD_OPTIONS)},
    'geometry':{'diameter_ft':q.geometry.diameter_ft,'floor_decagon_sqft':q.geometry.floor_decagon_sqft,'panels':sum(face.count for face in q.geometry.faces),'members':q.geometry.member_count},
    'unit':{'materials':q.material_cost,'labor_hours':q.labour_hours,'labor':q.labour_cost,'direct':q.direct_cost,'overhead':q.overhead,'warranty':q.warranty,'built':q.cost_to_build,'price':q.price,'spread':q.gross_profit,'price_margin':margin,'pad':q.pad_cost,'freight':freight,'placement':placement},
    'campaign':{'lines':budget,'grouped':funding_groups,'goal':k.goal(),'modeled_base_prototype':prototype,'potential_gap':potential_gap,'conditional_reconciled_goal':reconciled_goal},
    'sensitivity':[{'change':change,'cost':cost,'spread':spread,'price_margin':spread/q.price} for change,cost,spread in sensitivity],
    'labor_target':{'reduction':productivity_target,'hours_saved':hours_saved,'fully_loaded_cost_saved':loaded_savings},
    'model_constants':{'seed':s.external_constants(),'soft_shell':__import__('soft_shell').EXTERNAL_CONSTANTS},
    'quote_groups':[{'key':g.key,'label':g.label,'side':g.side,'cost':g.cost,'lines':[{'label':line.label,'quantity':line.quantity,'unit':line.unit,'unit_cost':line.unit_cost,'source':line.source,'cost':line.cost} for line in g.lines]} for g in q.groups],
    'font_size':font_size,'flow_height':height,'page_count':len(reader.pages),'original_page_preserved':True,
}
notes_path=next_version_path(ROOT/'tmp/pdfs/code-house-numbers-20261014-a-notes.json')
with notes_path.open('x',encoding='utf-8') as stream:
    json.dump(notes,stream,indent=2)
print(json.dumps({'outputs':notes['outputs'],'page_count':len(reader.pages),'font_size':font_size,'flow_height':round(height,1),'original_page_preserved':True},indent=2))

