"""The one-page summary for a grant panel, computed like everything else here.

    py -3.12 -m master_book.pitch

A panel that funds housing reads one page, so this is one page, and the build
refuses to finish if it runs to two. It says what the project is, why it exists,
what it is worth, what it has and has not proved, what the money is for and who
is asking -- and every figure on it is computed on the day it is printed:

* the dome, the clock, the prices, the catalogue and the book's own counts come
  from the same tokens the books use (:mod:`master_book.tokens`, which hands
  everything it does not hold to the Complete Edition's table);
* the published benchmarks a panel will check -- what a new site-built house and
  a new manufactured home cost a square foot -- come from
  :mod:`two_v_demo.house_economics`, which names its sources;
* the ask is the campaign's own costed list (:func:`kickstarter.goal_lines`)
  with the one line that only a crowdfunding campaign has taken out, grouped
  under four headings. The grouping is editorial and declared below; the
  amounts are the list's.

Every figure carries its kind -- measured, modelled, published -- and the page
keeps a box for the numbers that do not help the argument, because the books do.
A number typed into the copy below stops the build: the copy may only quote.

Each run writes a new numbered PDF and a PNG preview to ``deliverables/pitch/``.
"""

from __future__ import annotations

import base64
import html as html_escape
import io
import re
import tempfile
from functools import lru_cache
from pathlib import Path

from two_v_demo.deliverables import next_version_path

from . import outline, tokens

E = html_escape.escape

OUT_DIR = outline.ROOT / "deliverables" / "pitch"
STEM = "the-40-hour-cabin-one-pager"

#: The page's body type, points -- and the proof it printed at true size.
BODY_PT = 8.3

#: Lines of the campaign's list that a grant would not pay for: making and
#: shipping backers' rewards exists only because a crowdfunding campaign does.
NOT_ASKED = ("fulfilment",)

#: How the campaign's lines read to a panel. Declared: the headings and their
#: order are editorial; every amount under them is the campaign's own.
BUCKETS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("prove", "Prove it", ("test_platform", "instrumentation", "engineering")),
    ("tool", "Make it repeatable", ("cnc_router", "cnc_plasma", "laser_cutter", "strut_tooling",
                                    "automation")),
    ("develop", "Build what an owner cannot", ("hub_rnd", "composite_rnd")),
    ("seed", "Seed the network", ("quilt_seed",)),
)

#: Published figures about veterans, with their sources. Not computed here:
#: quoted, and the page prints the source beside them.
VETERANS = {
    "pit": (32882, "veterans experiencing homelessness on one night, January 2024",
            "HUD, 2024 Annual Homeless Assessment Report, Part 1"),
    "unsheltered": (13851, "of them unsheltered", "HUD, 2024 AHAR Part 1"),
    "village": (49, "tiny homes in the Veterans Community Project village, Kansas City",
                "Veterans Community Project, reported by KSHB"),
}
#: When that count was taken: the night the published figures describe.
VETERANS_COUNTED = "January 2024"
#: The federal programs a veterans' housing project is built to work beside.
#: Named, not claimed: eligibility is for each program to decide.
VETERAN_PROGRAMS = ("HUD-VASH", "SSVF", "VA Grant and Per Diem")


#: The author's own account, from the books' About the Author and chapters
#: fifty and seventy-one, in the author's words. Edit here; nothing else on
#: the page is personal.
AUTHOR_BIO = (
    "U.S. Navy veteran: six years as a Mass Communication Specialist, three of them in "
    "Japan. Learned to program and was certified as an avionics bench technician; now "
    "studying for an A&amp;P certificate on the G.I. Bill, on the way to aerospace engineering."
)
AUTHOR_WHY = (
    "Buckminster Fuller wanted housing cheap enough that a mother is not so burdened by "
    "it she cannot raise her child &mdash; what I took from him, not his words. I grew up "
    "with a single parent and a repossessed trailer, and came home from the Navy asking "
    "<i>what a small home I owned would have done for my eighteen-year-old self.</i>"
)
AUTHOR_CODE = (
    "A dome is a home written like good code: modular, reusable, decoupled, meant to be "
    "extended."
)


# ----------------------------------------------------------------------
# The figures only this page needs
# ----------------------------------------------------------------------

def _short(label: str) -> str:
    """A campaign line's name without its explanation: "CNC router, 4x8 bed" -> "CNC router"."""
    return re.split(r"[:,]", label, maxsplit=1)[0].strip()


@lru_cache(maxsize=1)
def ask() -> dict:
    """The campaign's list as a grant asks it: four headings, every line once."""
    import kickstarter

    lines = {line.key: line for line in kickstarter.goal_lines()}
    placed = [key for *_, keys in BUCKETS for key in keys] + list(NOT_ASKED)
    missing = sorted(set(lines) - set(placed))
    unknown = sorted(set(placed) - set(lines))
    twice = sorted({key for key in placed if placed.count(key) > 1})
    if missing or unknown or twice:
        raise ValueError(f"the ask no longer matches the campaign's list: not placed {missing}, "
                         f"not in the list {unknown}, placed twice {twice}")
    buckets = []
    for key, title, keys in BUCKETS:
        buckets.append({"key": key, "title": title,
                        "items": [_short(lines[k].what) for k in keys],
                        "usd": sum(lines[k].usd for k in keys)})
    total = sum(b["usd"] for b in buckets)
    assert abs(total + sum(lines[k].usd for k in NOT_ASKED) - kickstarter.goal()) < 0.5
    return {"buckets": buckets, "total": total, "campaign": kickstarter.goal()}


@lru_cache(maxsize=1)
def facts() -> dict[str, str]:
    """``pitch.*``: the ask, two published benchmarks and the catalogue's names."""
    import seed_model

    from two_v_demo import house_economics as he

    a = ask()
    out = {"pitch.total": f"{a['total']:,.0f}", "pitch.campaign": f"{a['campaign']:,.0f}"}
    for b in a["buckets"]:
        out[f"pitch.{b['key']}"] = f"{b['usd']:,.0f}"
    out["pitch.mhs"] = f"{he.value('mhs_2023_usd_per_sqft'):,.0f}"
    split = float(tokens.resolve("{{pine.kerf_only_pct}}"))
    out["pitch.split_pct"] = f"{split:.0f}"
    names = []
    for key in seed_model.FITOUT_ORDER:
        try:
            label = seed_model.fitout(key).label
            seed_model.quote(key)
        except Exception:
            continue
        names.append(re.sub(r"\s+seed$", "", label, flags=re.I))
    out["pitch.catalogue"] = " &middot; ".join(E(n) for n in names)

    from . import efficiency

    f = efficiency.facts()
    out["pitch.rain_gal"] = f"{f['rain_gal']:,.0f}"
    out["pitch.rain_in"] = f"{f['rain_in']:.0f}"
    out["pitch.rain_per_inch"] = f"{f['rain_per_inch']:,.0f}"
    out["pitch.catch_sqft"] = f"{f['catch_sqft']:,.0f}"
    out["pitch.panel_types"] = str(len(f["panel_types"]))
    out["pitch.modules"] = str(f["modules"])
    out["pitch.panel_lo"] = f"{min(u for _, u in f['panel_types']):,.0f}"
    out["pitch.panel_hi"] = f"{max(u for _, u in f['panel_types']):,.0f}"
    out["pitch.services"] = ", ".join(f["core_services"])
    out["pitch.skin_usd"] = f"{f['skin_diy']:,.0f}"
    out["pitch.sail_usd"] = f"{f['skin_sail']:,.0f}"
    out["pitch.wax_lo"] = f"{efficiency.D['wax_every_lo']:.0f}"
    out["pitch.wax_hi"] = f"{efficiency.D['wax_every_hi']:.0f}"
    out["pitch.wax_usd"] = f"{f['wax_usd']:,.0f}"
    out["pitch.halves"] = f"{seed_model.declared('shell_halves'):.0f}"
    pad = seed_model.quote().pad_cost
    out["pitch.vets_when"] = VETERANS_COUNTED
    out["pitch.vets_pit"] = f"{VETERANS['pit'][0]:,.0f}"
    out["pitch.vets_out"] = f"{VETERANS['unsheltered'][0]:,.0f}"
    out["pitch.village"] = str(VETERANS["village"][0])
    out["pitch.village_usd"] = f"{VETERANS['village'][0] * (f['price'] + pad) / 1e6:,.2f}"
    out["pitch.programs"] = ", ".join(VETERAN_PROGRAMS)
    return out


def fill(text: str) -> str:
    """``pitch.*`` here, everything else through the books' own tokens."""
    table = facts()
    text = re.sub(r"\{\{(pitch\.[a-z_]+)\}\}", lambda m: table[m.group(1)], text)
    return tokens.resolve(text, strict=True)


# ----------------------------------------------------------------------
# The copy. It quotes numbers; it never types one.
# ----------------------------------------------------------------------

STATS = (
    ("${{money.per_sqft}}", "a sq ft for the standard building, margin in. Published: new "
     "house ${{why.site_usd_per_sqft}}, manufactured ${{pitch.mhs}}", "modelled"),
    ("${{core.cost}}", "utility core: {{core.services}} services, a {{core.life}}-year life, "
     "moves to the next dome for ${{core.moves}}", "modelled"),
    ("{{pitch.rain_gal}} gal", "of rain a year off its own seams, at {{pitch.rain_in}} in of "
     "rain", "modelled"),
    ("{{pitch.panel_types}} + {{pitch.modules}}", "snap-in panel types and modules: a bay "
     "changes with a driver, not a builder", "modelled"),
    ("{{seed.count}}", "buildings from one body, ${{seed.cheapest_usd}} to "
     "${{seed.dearest_usd}}", "modelled"),
    ("{{pitch.vets_pit}}", "veterans homeless on one night in {{pitch.vets_when}}; "
     "{{pitch.vets_out}} unsheltered", "published (HUD)"),
)

LEFT = """
<h2>The problem</h2>
<p>Shelter eats the time and money a family needs for everything else: a new site-built
house costs <b>${{why.site_usd_per_sqft}} a square foot</b> before the land, a new
manufactured home <b>${{pitch.mhs}}</b> <span class="src">(NAHB, Census)</span>. On one
night in {{pitch.vets_when}}, <b>{{pitch.vets_pit}} veterans</b> had no home of their own
<span class="src">(HUD)</span>.</p>

<h2>The idea: a home made like a product</h2>
<p>A manufactured home built as a system, not a one-off. The frame is {{dome.panels}} flat
panels on two strut lengths, so every size from {{flat.small_ft}} to {{flat.big_ft}} feet uses
the same {{dome.members}} members, the same jig and the same hardware set. The shell comes in
{{pitch.halves}} slices that two people carry and snap together. Everything that makes it a
particular building plugs in.</p>

<h2>What plugs in</h2>
<ul>
<li><b>A utility core.</b> One column carries {{pitch.services}}: ${{core.cost}},
{{core.share}}% of the build, a {{core.life}}-year life. Buy the plumbing once.</li>
<li><b>Rain, built in.</b> The seams between panels are channels: {{pitch.rain_per_inch}}
gallons for every inch that falls on {{pitch.catch_sqft}} sq ft of shell, run to the pad's
tank. No gutters.</li>
<li><b>Snap-in panels.</b> Windows, doors, skylights, solar bays, flues: {{pitch.panel_types}}
types and {{pitch.modules}} modules, ${{pitch.panel_lo}} to ${{pitch.panel_hi}}.</li>
<li><b>A skin you renew.</b> Two layers of all-cotton duck soaked in silicone,
${{pitch.skin_usd}} against ${{pitch.sail_usd}} in sailcloth, and a beeswax coat every
{{pitch.wax_lo}}&ndash;{{pitch.wax_hi}} years, about ${{pitch.wax_usd}} a coat (estimated).</li>
</ul>
<p class="cat">{{pitch.catalogue}}: one body, {{seed.count}} buildings. It stands on a
serviced pad and can move: <b>own the building, rent the ground</b>.</p>

<h2>Who</h2>
<p><b>[[author]].</b> [[bio]] Built so far, in the open: the solver, two books
({{mb.vol_a_chapters}} and {{mb.vol_b_chapters}} chapters), {{mb.films}} films and a
{{mb.rungs}}-rung family edition.</p>
"""

RIGHT = """
<h2>Why I am doing this</h2>
<blockquote>[[why]]</blockquote>

<h2>Built by a veteran, for veterans</h2>
<p>The life this fits is one a lot of us already know: a small, squared-away space; a
system you maintain on a schedule; parts you swap in the field; a crew that builds
together. A village of {{pitch.village}} standard buildings on pads, the size of the
Veterans Community Project's Kansas City village <span class="src">(VCP)</span>, is
${{pitch.village_usd}} million in buildings and pads before land. It is designed to sit
beside {{pitch.programs}}, and to be built and kept by veterans.</p>

<h2>Measured, modelled, not yet</h2>
<table class="honest">
<tr><th class="m">Measured</th><td>splitting, {{hr.split_session}} wedges per
{{hr.session}}-hour session; strut weights; a full-size prototype frame.</td></tr>
<tr><th class="d">Modelled</th><td>cost, energy, rain and the core, in open code.</td></tr>
<tr><th class="n">Not yet</th><td>an engineer's rating; an instrumented year
(${{pitch.prove}}); the moulded shell and strut tooling (${{pitch.tool}}).</td></tr>
<tr><th class="a">Against us</th><td>{{mb.stand_pct}}% of the floor has {{mb.head_ft}} ft
of headroom; the whole building is about {{money.labour_hours}} hours, not forty.</td></tr>
</table>

<h2>The ask: ${{pitch.total}}</h2>
<p class="lead">The sum of its lines, not a round number: prove it, then make it
repeatable.</p>
[[ask]]
<p class="next">Costed as the next step, not asked here: a first site of {{park.ask_pads}}
serviced pads, ${{park.ask_goal}}.</p>
"""


def ask_html() -> str:
    rows = []
    for b in ask()["buckets"]:
        items = " &middot; ".join(E(i) for i in b["items"])
        rows.append(f'<tr><td><b>{E(b["title"])}</b> <span class="items">&mdash; {items}</span></td>'
                    f'<td class="usd">${{{{pitch.{b["key"]}}}}}</td></tr>')
    rows.append('<tr class="total"><td>Total</td><td class="usd">${{pitch.total}}</td></tr>')
    return '<table class="ask">' + "".join(rows) + "</table>"


def placeholders(column: str) -> str:
    """A column with its placeholders filled. Not str.format: that would eat the
    braces of every token in it."""
    parts = {"why": AUTHOR_WHY, "code": AUTHOR_CODE, "ask": ask_html(),
             "author": E(outline.AUTHOR), "bio": AUTHOR_BIO}
    return re.sub(r"\[\[(\w+)\]\]", lambda m: parts[m.group(1)], column)


def stats_html() -> str:
    tiles = []
    for big, words, kind in STATS:
        tiles.append(f'<div class="stat"><div class="big">{big}</div>'
                     f'<div class="words">{words}</div><div class="kind">{kind}</div></div>')
    return '<div class="stats">' + "".join(tiles) + "</div>"


#: The catalogue render from the Complete Edition: five buildings from one body.
HERO = outline.ROOT / "books/the-40-hour-cabin" / "figures" / "plate-catalogue.png"
#: The part of it that is the buildings, not the plate's caption, as fractions.
HERO_BOX = (0.2, 0.24, 0.98, 0.58)


def hero_data_uri() -> str:
    """The catalogue's buildings, cropped from the book's own plate."""
    from PIL import Image

    with Image.open(HERO) as im:
        w, h = im.size
        x0, y0, x1, y1 = HERO_BOX
        box = (int(w * x0), int(h * y0), int(w * x1), int(h * y1))
        crop = im.convert("RGB").crop(box)
        crop.thumbnail((1000, 1000))
        buf = io.BytesIO()
        crop.save(buf, "JPEG", quality=84)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


#: The dark set: the same palette, lightened for a dark ground.
DARK = ("--paper: #1a1917; --ground: #100f0e; --ink: #ece7df; --ink-2: #d8d2c8; --ink-3: #c8c1b6; "
        "--muted: #a49d92; --rule: #3c3833; --rule-2: #302d29; --tile: #24221f; --wood: #e3914f; "
        "--blue: #8fb8d9; --green: #7fc79d; --amber: #ddb75f; --red: #ea907d; color-scheme: dark;")


def _pt(size: float) -> str:
    """A type size that scales with the page: --k is 1 in print, larger on screen."""
    return f"calc(var(--k) * {size}pt)"


SANS = '"Segoe UI", system-ui, -apple-system, Helvetica, Arial, sans-serif'
SERIF = 'Georgia, "Times New Roman", serif'

#: The page as printed. Every colour is a token, so the screen version can
#: redefine them for a dark theme without touching a rule.
CSS = f"""
@page {{ size: 8.5in 11in; margin: .38in .42in .34in; }}
/* One page: a title band, six figures, then two columns -- the case and the ask. */
:root {{ --paper: #ffffff; --ground: #e9e3d9; --ink: #1d1d1b; --ink-2: #333333; --ink-3: #444444;
         --muted: #666666; --rule: #d8d2c8; --rule-2: #e4dfd6; --tile: #faf6f0;
         --wood: #b0601e; --blue: #2f5d7c; --green: #2f7d4f; --amber: #8a6508; --red: #8c2f1f;
         --k: 1; }}
html, body {{ background: var(--paper); margin: 0; }}
body {{ font: {_pt(BODY_PT)}/1.34 {SANS}; color: var(--ink); }}
a {{ color: inherit; text-decoration: none; }}
.head {{ display: flex; gap: .22in; align-items: stretch; }}
.head .text {{ flex: 1; min-width: 0; }}
.eyebrow {{ font: 700 {_pt(7.2)} {SANS}; letter-spacing: .2em; text-transform: uppercase;
            color: var(--wood); margin: 0; }}
h1 {{ font: 800 {_pt(29)}/1 {SANS}; margin: .05in 0 .04in; letter-spacing: -.01em; text-wrap: balance; }}
.sub {{ font: italic {_pt(12.2)}/1.3 {SERIF}; color: var(--ink-2); margin: 0 0 .07in; }}
.lede {{ font-size: {_pt(9.3)}; line-height: 1.42; margin: 0; }}
.hero {{ width: 3.05in; height: 1.62in; object-fit: cover; border-radius: 3px; display: block; max-width: 100%; }}
.stats {{ display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: .07in; margin: .12in 0 .1in; }}
.stat {{ border-top: 3px solid var(--wood); background: var(--tile); padding: .05in .07in .05in; min-width: 0; }}
.stat .big {{ font: 800 {_pt(15)}/1.05 {SANS}; color: var(--wood); white-space: nowrap;
              font-variant-numeric: tabular-nums; }}
.stat .words {{ font-size: {_pt(6.8)}; line-height: 1.28; margin-top: .03in; }}
.stat .kind {{ font: 700 {_pt(5.9)} {SANS}; letter-spacing: .12em; text-transform: uppercase;
               color: var(--muted); margin-top: .03in; }}
.cols {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: .24in; }}
.col {{ min-width: 0; }}
h2 {{ font: 800 {_pt(9.4)} {SANS}; letter-spacing: .06em; text-transform: uppercase;
      color: var(--blue); margin: .09in 0 .03in; border-bottom: 1px solid var(--rule); padding-bottom: .015in; }}
.col > h2:first-child {{ margin-top: 0; }}
p {{ margin: 0 0 .05in; }}
ul {{ margin: 0 0 .04in; padding-left: .15in; }}
li {{ margin: 0 0 .025in; }}
.src {{ color: var(--muted); font-size: {_pt(7)}; }}
.cat {{ font-size: {_pt(7.6)}; color: var(--ink-2); }}
blockquote {{ margin: 0 0 .05in; padding: .02in 0 .02in .1in; border-left: 3px solid var(--wood);
              font: italic {_pt(8.7)}/1.38 {SERIF}; color: var(--ink-2); }}
table {{ border-collapse: collapse; width: 100%; }}
table.honest th {{ font: 800 {_pt(6.6)} {SANS}; letter-spacing: .1em; text-transform: uppercase;
                   text-align: left; vertical-align: top; width: .74in; padding: .025in .05in .025in 0;
                   border-bottom: .5px solid var(--rule-2); }}
table.honest td {{ padding: .025in 0; vertical-align: top; border-bottom: .5px solid var(--rule-2); }}
th.m {{ color: var(--green); }} th.d {{ color: var(--blue); }} th.n {{ color: var(--amber); }}
th.a {{ color: var(--red); }}
p.lead {{ font-style: italic; color: var(--muted); margin-bottom: .03in; }}
table.ask td {{ padding: .03in 0; vertical-align: top; border-bottom: .5px solid var(--rule-2); }}
table.ask td.usd {{ text-align: right; font-weight: 700; white-space: nowrap; padding-left: .1in;
                    font-variant-numeric: tabular-nums; }}
table.ask .items {{ font-size: {_pt(7.3)}; color: var(--ink-3); }}
table.ask tr.total td {{ border-top: 1.4px solid var(--ink); border-bottom: 0; font-weight: 800;
                         font-size: {_pt(9.6)}; }}
p.next {{ font-size: {_pt(7.4)}; color: var(--muted); margin-top: .04in; }}
.foot {{ margin-top: .1in; padding-top: .05in; border-top: 1px solid var(--rule); font-size: {_pt(6.9)};
         color: var(--muted); display: flex; justify-content: space-between; gap: .2in; }}
.foot b, .foot a {{ color: var(--ink); font-weight: 700; }}
"""

#: The same page on a screen: larger type, a dark set of the same colours, and
#: one column on a phone. Print never reads any of it.
WEB_CSS = f"""
@media screen {{
  :root {{ --k: 1.28; }}
  html {{ background: var(--ground); }}
  body {{ max-width: 9.8in; margin: 0 auto; padding-block: 28px; padding-inline: 32px;
          background: var(--paper); }}
  a:hover, a:focus-visible {{ text-decoration: underline; }}
}}
@media screen and (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{ {DARK} }}
}}
:root[data-theme="dark"] {{ {DARK} }}
@media screen and (max-width: 900px) {{
  .stats {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
}}
@media screen and (max-width: 700px) {{
  :root {{ --k: 1.3; }}
  body {{ padding-block: 20px; padding-inline: 16px; }}
  .head {{ flex-direction: column; }}
  h1 {{ font-size: {_pt(24)}; }}
  .hero {{ width: 100%; height: auto; aspect-ratio: 16 / 10; }}
  .stats {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
  .cols {{ grid-template-columns: minmax(0, 1fr); }}
  .foot {{ flex-direction: column; }}
}}
"""


#: The page's name as a web page: what it is, not a caption of it.
WEB_TITLE = "40 Hour Cabin One-Pager"


def document(web: bool = False) -> str:
    """The page as a printable document, or (``web``) as a page fragment for
    a viewer that supplies its own skeleton, with the screen styles added."""
    import json

    from wedge_book import print_edition as pe

    site = json.loads((outline.ROOT / "web" / "site.config.json").read_text(encoding="utf-8"))
    contacts = " &middot; ".join(f"{E(k)} {E(v)}" for k, v in pe.CONTACTS)
    lede = ("A small home made like a product: one standard frame, a shell in {{pitch.halves}} "
            "slices, a utility core that carries every service, and snap-in panels that decide "
            "what the building is. The standard building lists at ${{money.price}}, and every "
            "figure on this page is computed by open-source software anyone can run.")
    left, right = placeholders(LEFT), placeholders(RIGHT)
    copy = stats_html() + left + right + lede
    stray = typed_numbers(copy)
    if stray:
        raise ValueError(f"numbers typed into the pitch copy, not computed: {stray[:8]}")
    body = (
        '<div class="head"><div class="text">'
        '<p class="eyebrow">Modular housing &middot; by a veteran, for veterans</p>'
        f"<h1>{E(outline.TITLE)}</h1>"
        '<p class="sub">One standard body, made the same way every time.</p>'
        f'<p class="lede">{lede}</p></div>'
        f'<img class="hero" src="{hero_data_uri()}" alt="A garage, workshop, guest house, studio '
        'and gym: the same dome, five fit-outs."></div>'
        + stats_html()
        + f'<div class="cols"><div class="col">{left}</div><div class="col">'
        + right
        + "</div></div>"
        + f'<div class="foot"><span>Every figure computed {{{{mb.built}}}} by the project&rsquo;s '
          f"own software and labelled by kind. Code, books and films: "
          f'<a href="https://{E(pe.PROJECT_URL)}">{E(pe.PROJECT_URL)}</a></span>'
          f'<span><a href="{E(site.get("url", ""))}">{E(site.get("url", "").replace("https://", ""))}</a>'
          f" &middot; {contacts}</span></div>"
    )
    if web:
        return fill(f"<title>{E(WEB_TITLE)}</title><style>{CSS}{WEB_CSS}</style>{body}")
    page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f"<title>{E(outline.TITLE)}: one page</title><style>{CSS}</style></head>"
            f"<body>{body}</body></html>")
    return fill(page)


def typed_numbers(copy: str) -> list[str]:
    """Digits in the copy that are not inside a token, a tag or an entity."""
    text = re.sub(r"\{\{[a-z_]+\.[a-z_0-9]+\}\}", " ", copy)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&#?\w+;", " ", text)
    return re.findall(r"\S*\d\S*", text)


# ----------------------------------------------------------------------
# Printing
# ----------------------------------------------------------------------

def problems(doc) -> list[str]:
    """What stops a printed copy being the one-pager."""
    from wedge_book import print_edition as pe

    found = []
    if len(doc) != 1:
        found.append(f"the one-pager runs to {len(doc)} pages; cut words until it is one")
    shrunk = pe.scale_problem(doc, BODY_PT)
    if shrunk:
        found.append(shrunk)
    return found


def _print(path: Path) -> None:
    from two_v_demo import book_export

    chrome = book_export._chrome_path()
    if not chrome:
        raise RuntimeError("the one-pager needs Chrome or Edge to print with")
    book_export._pdf_via_chrome(document(), path, chrome)


def build() -> tuple[Path, Path]:
    import pymupdf

    with tempfile.TemporaryDirectory() as scratch:
        proof = Path(scratch) / "pitch.pdf"
        _print(proof)
        doc = pymupdf.open(proof)
        try:
            found = problems(doc)
            if found:
                raise RuntimeError("; ".join(found))
            doc.set_metadata({"title": f"{outline.TITLE}: the project on one page",
                              "author": outline.AUTHOR,
                              "subject": "A one-page summary for grant panels and partners",
                              "keywords": "alternative housing, geodesic dome, timber, owner-built, "
                                          "open source"})
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            pdf = next_version_path(OUT_DIR / f"{STEM}.pdf")
            png = pdf.with_suffix(".png")
            if png.exists():
                raise FileExistsError(f"{png.name} already exists; deliverables are never overwritten")
            doc.save(pdf, garbage=3, deflate=True)
            doc[0].get_pixmap(dpi=150).save(png)
        finally:
            doc.close()
    return pdf, png


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--html", type=Path, metavar="FILE", help="write the page's HTML here and stop")
    parser.add_argument("--web", type=Path, metavar="FILE",
                        help="write the screen version (a page fragment, light and dark) here and stop")
    parser.add_argument("--proof", type=Path, metavar="PDF",
                        help="print to this path (outside deliverables/) and report, whatever its length")
    args = parser.parse_args(argv)
    if args.html or args.web:
        target = args.html or args.web
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(document(web=bool(args.web)), encoding="utf-8")
        print(f"wrote {target}")
        return 0
    if args.proof:
        import pymupdf

        if OUT_DIR.resolve() in args.proof.resolve().parents:
            parser.error("a proof goes outside deliverables/; the copies there are numbered")
        _print(args.proof)
        doc = pymupdf.open(args.proof)
        found = problems(doc)
        doc.close()
        print(f"wrote {args.proof}" + "".join(f"\n  PROBLEM: {p}" for p in found))
        return 1 if found else 0
    pdf, png = build()
    a = ask()
    print(f"wrote {pdf}\n      {png}\n  the ask: ${a['total']:,.0f} of the campaign's "
          f"${a['campaign']:,.0f} (without {', '.join(NOT_ASKED)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
