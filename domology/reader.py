"""The live reading version of Domology: every page in a browser, answerable.

The pages are the paginator's own SVG -- the drawing the PDF prints -- so what
you read here is what the printer gets. Hover a live number and the page says
what computed it; switch on *Live numbers* and every computed figure on every
page lights up; search finds words across the whole book.
"""

from __future__ import annotations

import html
import json

from . import config as C
from .pages import svg_page


def reader_html(layout, href, tokens: dict, chapters: dict | None = None,
                title: str = C.TITLE) -> str:
    leaves = []
    for page in layout.pages:
        side = "recto" if page.recto else "verso"
        leaves.append(f'<section class="leaf {side}" id="page-{page.index}" '
                      f'data-index="{page.index}" data-folio="{html.escape(str(page.folio))}">'
                      f'{svg_page(page, href, interactive=True)}</section>')
    toc = [{"kind": line.kind, "label": line.label, "title": line.title,
            "folio": line.folio, "page": line.page} for line in layout.toc]
    data = json.dumps({"toc": toc, "tokens": tokens, "pages": len(layout.pages),
                       "title": title, "subtitle": C.SUBTITLE},
                      ensure_ascii=False).replace("</", "<\\/")
    return (TEMPLATE.replace("%%TITLE%%", html.escape(title))
            .replace("%%LEAVES%%", "".join(leaves))
            .replace("%%DATA%%", data))


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%%TITLE%% Reader</title>
<style>
:root{--ground:#15171a;--panel:#1d2024;--line:#2c3036;--ink:#ebe7de;--muted:#9aa1a8;
--amber:#d99532;--cyan:#46aed0;--w:430px}
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:var(--ground);color:var(--ink);
font:14px/1.45 "Segoe UI",system-ui,sans-serif}
header{position:fixed;inset:0 0 auto 0;height:52px;display:flex;align-items:center;gap:14px;
padding:0 16px;background:rgba(21,23,26,.94);border-bottom:1px solid var(--line);z-index:5;
backdrop-filter:blur(6px)}
.brand{font:22px/1 "Palatino Linotype","Book Antiqua",Palatino,serif;letter-spacing:.01em}
.brand small{display:block;font:600 9px/1.6 "Segoe UI",sans-serif;letter-spacing:.14em;
color:var(--amber);text-transform:uppercase}
.where{color:var(--muted);font-size:12.5px;flex:1;min-width:0;white-space:nowrap;overflow:hidden;
text-overflow:ellipsis}
.where b{color:var(--ink);font-weight:600}
button,.ctl{background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:6px;
padding:6px 10px;font:inherit;font-size:12.5px;cursor:pointer}
button:hover{border-color:#495059}
button:focus-visible,input:focus-visible{outline:2px solid var(--cyan);outline-offset:1px}
button[aria-pressed=true]{border-color:var(--amber);color:var(--amber)}
input[type=search]{background:var(--panel);color:var(--ink);border:1px solid var(--line);
border-radius:6px;padding:6px 10px;width:180px;font:inherit;font-size:12.5px}
input[type=range]{width:110px;accent-color:var(--amber)}
nav{position:fixed;top:52px;bottom:0;left:0;width:290px;overflow:auto;padding:14px 10px 40px;
background:var(--panel);border-right:1px solid var(--line);transition:transform .2s;z-index:4}
body.hide-toc nav{transform:translateX(-100%)}
nav a{display:grid;grid-template-columns:28px 1fr auto;gap:6px;padding:5px 8px;border-radius:5px;
color:var(--ink);text-decoration:none;font-size:12.8px}
nav a:hover{background:#262a2f}
nav a .n{color:var(--cyan);font-weight:600}
nav a .f{color:var(--muted);font-variant-numeric:tabular-nums}
nav .book{margin:16px 8px 4px;font-size:10px;letter-spacing:.14em;text-transform:uppercase;
color:var(--amber);font-weight:700}
nav .book span{display:block;font:17px/1.25 "Palatino Linotype",Palatino,serif;letter-spacing:0;
text-transform:none;color:var(--ink);font-weight:400;margin-top:2px}
main{padding:76px 24px 120px 314px;transition:padding .2s}
body.hide-toc main{padding-left:24px}
.book-pages{display:grid;grid-template-columns:repeat(2,var(--w));justify-content:center;
row-gap:28px}
.book-pages .leaf:first-child{grid-column:2}
body.single .book-pages{grid-template-columns:var(--w)}
body.single .book-pages .leaf:first-child{grid-column:1}
.leaf{width:var(--w);content-visibility:auto;contain-intrinsic-size:var(--w) calc(var(--w)*1.2615)}
.leaf svg{display:block;width:100%;height:auto;background:#fff;
box-shadow:0 1px 2px rgba(0,0,0,.5),0 10px 28px rgba(0,0,0,.35)}
.leaf.verso svg{border-radius:2px 0 0 2px}.leaf.recto svg{border-radius:0 2px 2px 0}
.tok{cursor:help}
body.live .tok{fill:#b8751a;font-weight:700}
body.live .tok:hover{fill:#17779a}
#tip{position:fixed;max-width:340px;padding:10px 12px;background:#0f1113;border:1px solid #3a4047;
border-radius:8px;box-shadow:0 8px 30px rgba(0,0,0,.5);font-size:12.5px;pointer-events:none;
opacity:0;transition:opacity .12s;z-index:9}
#tip.on{opacity:1}
#tip code{color:var(--amber);font:600 12px Consolas,monospace}
#tip .v{font:20px/1.2 "Palatino Linotype",Palatino,serif;margin:4px 0}
#tip .s{color:var(--muted);font-size:11.5px;margin-top:6px}
#results{position:fixed;top:56px;right:16px;width:330px;max-height:60vh;overflow:auto;
background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:6px;z-index:6}
#results[hidden]{display:none}
#results a{display:block;padding:6px 8px;border-radius:5px;color:var(--ink);text-decoration:none;
font-size:12.5px}
#results a:hover{background:#262a2f}
#results a b{color:var(--amber);font-weight:600;margin-right:6px}
.hl{outline:3px solid var(--amber);outline-offset:4px;border-radius:2px}
@media (max-width:980px){nav{transform:translateX(-100%)}body.show-toc nav{transform:none}
main{padding-left:16px!important;padding-right:16px}.book-pages{grid-template-columns:min(var(--w),92vw)!important}
.book-pages .leaf:first-child{grid-column:1}.leaf{width:min(var(--w),92vw)}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style></head>
<body>
<header>
<button id="tocBtn" aria-label="Show or hide the contents">&#9776;</button>
<div class="brand">%%TITLE%%<small>Three books in one</small></div>
<div class="where" id="where"></div>
<input type="search" id="q" placeholder="Search the book" aria-label="Search the book">
<button id="liveBtn" aria-pressed="false" title="Light up every computed figure">Live numbers</button>
<button id="spreadBtn" aria-pressed="true" title="Two pages side by side">Spreads</button>
<input type="range" id="zoom" min="300" max="820" value="430" aria-label="Page size">
</header>
<nav id="toc" aria-label="Contents"></nav>
<main><div class="book-pages" id="pages">%%LEAVES%%</div></main>
<div id="tip" role="tooltip"></div>
<div id="results" hidden></div>
<script id="data" type="application/json">%%DATA%%</script>
<script>
(function(){
const D=JSON.parse(document.getElementById('data').textContent);
const body=document.body, leaves=[...document.querySelectorAll('.leaf')];
const store={get(k){try{return localStorage.getItem(k)}catch(e){return null}},
 set(k,v){try{localStorage.setItem(k,v)}catch(e){}}};
// contents
const nav=document.getElementById('toc');
let html='';
for(const line of D.toc){
  if(line.kind==='book'){html+=`<div class="book">${line.label}<span>${esc(line.title)}</span></div>`;continue}
  html+=`<a href="#page-${line.page}" data-page="${line.page}"><span class="n">${esc(line.label||'')}</span>`+
        `<span>${esc(line.title)}</span><span class="f">${esc(line.folio)}</span></a>`;
}
nav.innerHTML=html;
nav.addEventListener('click',e=>{const a=e.target.closest('a');if(!a)return;e.preventDefault();go(+a.dataset.page)});
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function go(i){const el=document.getElementById('page-'+i);if(el){el.scrollIntoView({block:'start'});flash(el)}}
function flash(el){el.classList.add('hl');setTimeout(()=>el.classList.remove('hl'),900)}
// where am I
const where=document.getElementById('where');
const starts=D.toc.filter(l=>l.kind!=='book').sort((a,b)=>a.page-b.page);
function chapterAt(i){let c=null;for(const s of starts){if(s.page<=i)c=s;else break}return c}
let current=0;
const io=new IntersectionObserver(es=>{for(const e of es){if(e.isIntersecting){current=+e.target.dataset.index;
 const c=chapterAt(current);where.innerHTML=`Page <b>${esc(e.target.dataset.folio||'')}</b> of ${D.pages}`+
 (c?` &middot; ${c.label?esc(c.label)+'. ':''}${esc(c.title)}`:'');store.set('dm-page',current)}}},{rootMargin:'-45% 0px -50% 0px'});
leaves.forEach(l=>io.observe(l));
// controls
const zoom=document.getElementById('zoom');
function setZoom(v){document.documentElement.style.setProperty('--w',v+'px');store.set('dm-zoom',v)}
zoom.addEventListener('input',()=>setZoom(zoom.value));
const spreadBtn=document.getElementById('spreadBtn');
spreadBtn.addEventListener('click',()=>{const single=!body.classList.toggle('single');
 spreadBtn.setAttribute('aria-pressed',single);store.set('dm-single',body.classList.contains('single')?'1':'0');go(current)});
const liveBtn=document.getElementById('liveBtn');
liveBtn.addEventListener('click',()=>{const on=body.classList.toggle('live');liveBtn.setAttribute('aria-pressed',on)});
document.getElementById('tocBtn').addEventListener('click',()=>{body.classList.toggle(
 window.innerWidth<980?'show-toc':'hide-toc')});
// token tooltips
const tip=document.getElementById('tip');
document.addEventListener('mouseover',e=>{const t=e.target.closest&&e.target.closest('.tok');if(!t)return;
 const name=t.getAttribute('data-tok');const info=D.tokens[name];if(!info)return;
 tip.innerHTML=`<code>{{${esc(name)}}}</code><div class="v">${esc(info[0])}</div><div>${esc(info[1]||'')}</div>`+
 `<div class="s">Computed by ${esc(info[2])} when this copy was built.</div>`;tip.classList.add('on')});
document.addEventListener('mousemove',e=>{if(!tip.classList.contains('on'))return;
 const x=Math.min(e.clientX+16,window.innerWidth-360),y=Math.min(e.clientY+18,window.innerHeight-140);
 tip.style.left=x+'px';tip.style.top=y+'px'});
document.addEventListener('mouseout',e=>{if(e.target.closest&&e.target.closest('.tok'))tip.classList.remove('on')});
// search
const q=document.getElementById('q'),results=document.getElementById('results');
let texts=null;
q.addEventListener('input',()=>{const s=q.value.trim().toLowerCase();if(s.length<3){results.hidden=true;return}
 texts=texts||leaves.map(l=>l.textContent.replace(/\s+/g,' ').toLowerCase());
 const found=[];texts.forEach((t,i)=>{const k=t.indexOf(s);if(k>=0&&found.length<60)found.push([i,t.slice(Math.max(0,k-40),k+60)])});
 results.innerHTML=found.length?found.map(([i,t])=>`<a href="#page-${i}" data-page="${i}"><b>${esc(leaves[i].dataset.folio||i+1)}</b>&hellip;${esc(t)}&hellip;</a>`).join(''):'<a>No page has that.</a>';
 results.hidden=false});
results.addEventListener('click',e=>{const a=e.target.closest('a[data-page]');if(!a)return;e.preventDefault();go(+a.dataset.page);results.hidden=true});
// keys
document.addEventListener('keydown',e=>{if(e.target===q)return;const step=body.classList.contains('single')?1:2;
 if(e.key==='ArrowRight'||e.key==='PageDown'){e.preventDefault();go(Math.min(leaves.length-1,current+step))}
 if(e.key==='ArrowLeft'||e.key==='PageUp'){e.preventDefault();go(Math.max(0,current-step))}
 if(e.key==='n'){liveBtn.click()}});
// restore
const z=store.get('dm-zoom');if(z){zoom.value=z;setZoom(z)}
if(store.get('dm-single')==='1'){body.classList.add('single');spreadBtn.setAttribute('aria-pressed','false')}
const p=store.get('dm-page');if(p&&+p<leaves.length)setTimeout(()=>go(+p),60);
})();
</script>
</body></html>
"""
