"""Efficiency, by the numbers: the one-page chart sheet that goes with the pitch.

    py -3.12 -m master_book.efficiency            # PDF + PNG in deliverables/pitch/
    py -3.12 -m master_book.efficiency --proof X  # printed for looking at
    py -3.12 -m master_book.efficiency --web X    # the screen version, light and dark

Nine panels, every bar drawn to scale from a number the project's own models
compute on the day it is printed:

* price per square foot -- the standard building from :mod:`seed_model`'s quote,
  against the two published benchmarks :mod:`two_v_demo.house_economics` sources
  (NAHB for a new site-built house, Census for a new manufactured home);
* where the standard building's money goes, group by group, with the utility
  core -- column plus services -- marked, because the core is the part that
  moves to the next dome;
* skin, running cost and wind load against a box house of the same floor, from
  :mod:`two_v_demo.dome_advantage` and :mod:`two_v_demo.dome_performance`;
* the rain the shell's own seams catch, from :func:`seed_model.seam_duct`;
* one parts list at three sizes, from the solved frame;
* the silicone-and-cotton skin from :mod:`two_v_demo.sky_web`, and its beeswax
  upkeep -- the one thing no model here prices yet, so it is declared below,
  marked as estimates, and printed on the sheet before it is used;
* wood recovery, split against sawn, from the pine model.

Each panel says what kind of figure it is: measured, modelled, published or
estimated. Nothing on the sheet is typed.
"""

from __future__ import annotations

import html as html_escape
import math
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from two_v_demo.deliverables import next_version_path

from . import outline, pitch, tokens

E = html_escape.escape
OUT_DIR = pitch.OUT_DIR
STEM = "the-40-hour-cabin-efficiency"
PACK_STEM = "the-40-hour-cabin-pitch-pack"
BODY_PT = 7.6


@dataclass(frozen=True)
class Declared:
    key: str
    value: float
    unit: str
    kind: str
    why: str


#: The skin's upkeep. No model in the project prices beeswax, so these are
#: declared here, every one an estimate or the owner's stated practice, and
#: the sheet prints this table beside the figure it makes.
DECLARED: tuple[Declared, ...] = (
    Declared("wax_g_m2", 40.0, "g/m2", "estimate",
             "a maintenance coat rubbed into cloth already proofed with silicone: far less than "
             "a first waxing of bare canvas"),
    Declared("wax_usd_kg", 15.0, "$/kg", "estimate", "beeswax pellets bought by the kilogram"),
    Declared("wax_m2_hour", 10.0, "m2/hour", "estimate", "rubbing in and melting off with a heat gun"),
    Declared("wax_every_lo", 1.0, "years", "owner's practice", "recoat yearly where it is wet and sunny"),
    Declared("wax_every_hi", 2.0, "years", "owner's practice", "every second year where it is not"),
)
D = {d.key: d.value for d in DECLARED}

#: Rainfall the rain panel is drawn at, inches a year: the model's own declared
#: average and a dry and a wet place either side of it, so the bar is not one point.
RAIN_SPREAD = (0.5, 1.0, 1.5)


# ----------------------------------------------------------------------
# The figures
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def facts() -> dict:
    import seed_model

    from two_v_demo import dome_advantage as adv
    from two_v_demo import dome_performance as perf
    from two_v_demo import house_economics as he
    from two_v_demo import sky_web
    from two_v_demo import why_build_economics as why

    q = seed_model.quote()
    groups = {g.key: g.cost for g in q.dome_groups}
    surface, _volume, _heat, wind = adv.advantages()
    dome_run, box_run = perf.running_costs()
    duct = seed_model.seam_duct()
    rain_in = seed_model.declared("rain_in_per_year")
    per_inch = duct.gallons_per_year / rain_in
    skin = sky_web.skin()
    outer_m2 = skin["area_m2"]                       # one layer: the wax goes on the outside
    wax_kg = outer_m2 * D["wax_g_m2"] / 1000
    services = sorted({p.service for p in seed_model.core_parts()})
    t = tokens.tokens()

    def tok(name: str) -> float:
        return float(tokens.resolve("{{" + name + "}}").replace(",", ""))

    sizes = [(tok("flat.small_ft"), tok("flat.small_sqft")),
             (tok("mb.cabin_scale_ft"), float(t["mb.floor_circle_sqft"].value().replace(",", ""))),
             (tok("flat.big_ft"), tok("flat.big_sqft"))]
    return {
        "site_sqft": why.checks().site_usd_per_sqft,
        "mhs_sqft": he.value("mhs_2023_usd_per_sqft"),
        "ours_sqft": q.price_per_sqft,
        "price": q.price, "cost": q.cost_to_build,
        "money": [("Frame", groups.get("frame", 0.0), "frame"),
                  ("Weather shell", groups.get("cap", 0.0), "shell"),
                  ("Utility column", groups.get("column", 0.0), "core"),
                  ("Services", groups.get("services", 0.0), "core"),
                  ("Utility panels", groups.get("polyps", 0.0), "panels"),
                  ("Build labour", groups.get("labour", 0.0), "labour"),
                  ("Overhead and warranty", q.overhead + q.warranty, "over"),
                  ("Maker's margin", q.price - q.cost_to_build, "margin")],
        "core_usd": q.core_cost, "core_share": q.core_share * 100,
        "core_life": seed_model.declared("core_service_life_years"),
        "core_move": seed_model.declared("core_move_usd"),
        "core_services": services,
        "skin_dome": surface.dome, "skin_box": surface.other, "skin_pct": surface.percent_better,
        "run_dome": dome_run.annual_cost, "run_box": box_run.annual_cost,
        "drag_dome": wind.dome, "drag_box": wind.other, "drag_pct": wind.percent_better,
        "rain_in": rain_in, "rain_gal": duct.gallons_per_year, "rain_per_inch": per_inch,
        "catch_sqft": duct.catch_sqft, "catch_eff": seed_model.declared("catch_efficiency") * 100,
        "rain_rows": [(rain_in * f, per_inch * rain_in * f) for f in RAIN_SPREAD],
        "members": tok("dome.members"), "panels": tok("dome.panels"), "sizes": sizes,
        "skin_diy": skin["diy_usd"], "skin_sail": skin["sail_usd"], "skin_m2": skin["cotton_m2"],
        "skin_layers": skin["layers"], "outer_m2": outer_m2,
        "wax_kg": wax_kg, "wax_usd": wax_kg * D["wax_usd_kg"], "wax_hours": outer_m2 / D["wax_m2_hour"],
        "split_pct": tok("pine.kerf_only_pct"), "sawn_pct": tok("pine.sawn_model_pct"),
        "mill_pct": tok("pine.mill_pct"),
        "built": t["mb.built"].value(),
        "panel_types": [(pn.label, pn.usd) for pn in seed_model.PANELS if pn.usd > 0],
        "modules": len(seed_model.MODULES),
        "frame_h": tok("clock.total"), "build_h": tok("money.labour_hours"),
        "split_h": tok("clock.split_h"), "error_h": tok("clock.error_h"),
    }


# ----------------------------------------------------------------------
# Drawing, to scale
# ----------------------------------------------------------------------

def money(v: float, cents: bool = False) -> str:
    return f"${v:,.2f}" if cents else f"${v:,.0f}"


def bars(rows: list[tuple[str, float, str, str]], width: float = 214.0, row_h: float = 21.5,
         label_w: float = 0.0) -> str:
    """Horizontal bars on one scale: (label, value, shown, css class). The
    longest bar is the largest value; every other is in proportion."""
    top = max(v for _, v, _, _ in rows) or 1.0
    track = width - 58.0
    h = row_h * len(rows) + 4
    out = [f'<svg class="chart" viewBox="0 0 {width:.0f} {h:.0f}" role="img" '
           f'aria-label="{E("; ".join(f"{l}: {s}" for l, _, s, _ in rows))}">']
    for i, (label, value, shown, cls) in enumerate(rows):
        y = i * row_h + 2
        w = max(1.5, track * value / top)
        out.append(f'<text class="lab" x="0" y="{y + 8:.1f}">{E(label)}</text>')
        out.append(f'<rect class="{cls}" x="0" y="{y + 10:.1f}" width="{w:.1f}" height="9" rx="1.5"/>')
        out.append(f'<text class="val" x="{w + 4:.1f}" y="{y + 17.8:.1f}">{E(shown)}</text>')
    out.append("</svg>")
    return "".join(out)


def stack(parts: list[tuple[str, float, str]], width: float = 214.0) -> str:
    """One bar, its segments in proportion, the core's two segments marked."""
    total = sum(v for _, v, _ in parts)
    x = 0.0
    segs = []
    for label, value, cls in parts:
        w = width * value / total
        segs.append(f'<rect class="seg {cls}" x="{x:.2f}" y="0" width="{max(w - .8, .4):.2f}" height="16"/>')
        x += w
    core = sum(v for _, v, c in parts if c == "core")
    core_x = width * sum(v for _, v, c in parts[:2]) / total
    core_w = width * core / total
    segs.append(f'<path class="brace" d="M{core_x:.1f} 20 v4 h{core_w:.1f} v-4"/>')
    segs.append(f'<text class="val" x="{core_x + core_w / 2:.1f}" y="33" text-anchor="middle">'
                f"utility core</text>")
    return (f'<svg class="chart" viewBox="0 0 {width:.0f} 36" role="img" aria-label="'
            f'{E("; ".join(f"{l} {money(v)}" for l, v, _ in parts))}">' + "".join(segs) + "</svg>")


def legend(parts: list[tuple[str, float, str]]) -> str:
    total = sum(v for _, v, _ in parts)
    items = "".join(f'<li><i class="{cls}"></i>{E(label)} <b>{money(v)}</b> '
                    f'<span>{100 * v / total:.0f}%</span></li>' for label, v, cls in parts)
    return f'<ul class="legend">{items}</ul>'


def panel(title: str, kind: str, figure: str, note: str) -> str:
    return (f'<section class="panel"><h2>{title}</h2>{figure}<p class="note">{note}</p>'
            f'<p class="kind">{kind}</p></section>')


def panels() -> list[str]:
    f = facts()
    out = []
    out.append(panel(
        "Price a square foot",
        "modelled &middot; published (NAHB, Census)",
        bars([("New site-built house, without land", f["site_sqft"], money(f["site_sqft"]), "them"),
              ("New manufactured home", f["mhs_sqft"], money(f["mhs_sqft"]), "them"),
              ("This standard building", f["ours_sqft"], money(f["ours_sqft"], True), "ours")]),
        f"The standard building is {f['ours_sqft'] / f['mhs_sqft'] * 100:.0f}% of a new manufactured "
        f"home's price a square foot, margin included and the pad extra. Not like for like: one "
        f"room with a service core, not a finished house."))
    out.append(panel(
        f"Where the {money(f['price'])} goes",
        "modelled",
        stack(f["money"]) + legend(f["money"]),
        f"The core is {money(f['core_usd'])}, {f['core_share']:.0f}% of the build. It lasts "
        f"{f['core_life']:.0f} years and moves to the next dome for {money(f['core_move'])}."))
    out.append(panel(
        "Outside skin, same floor",
        "modelled",
        bars([("Box house", f["skin_box"], f"{f['skin_box']:,.0f} sq ft", "them"),
              ("Dome", f["skin_dome"], f"{f['skin_dome']:,.0f} sq ft", "ours")]),
        f"{f['skin_pct']:.0f}% less to build, to weatherproof, and to lose heat through."))
    out.append(panel(
        "Heating and cooling, a year",
        "modelled",
        bars([("Box house", f["run_box"], money(f["run_box"]), "them"),
              ("Dome", f["run_dome"], money(f["run_dome"]), "ours")]),
        f"{money(f['run_box'] - f['run_dome'])} a year never spent, from the shape alone."))
    out.append(panel(
        "Wind load",
        "published coefficients",
        bars([("Box house, drag", f["drag_box"], f"{f['drag_box']:.2f}", "them"),
              ("Dome, drag", f["drag_dome"], f"{f['drag_dome']:.2f}", "ours")]),
        f"{f['drag_pct']:.0f}% less push from the same wind: the shape sheds it."))
    out.append(panel(
        "Rain the seams catch, a year",
        "modelled &middot; rainfall declared",
        bars([(f"{inches:.0f} in of rain a year", gal, f"{gal:,.0f} gal",
               "ours" if abs(inches - f["rain_in"]) < 1e-6 else "soft")
              for inches, gal in f["rain_rows"]]),
        f"{f['catch_sqft']:,.0f} sq ft of shell, {f['catch_eff']:.0f}% caught: "
        f"{f['rain_per_inch']:,.0f} gallons for every inch that falls, run by the seams into the "
        f"pad's tank. No gutters."))
    out.append(panel(
        "One parts list, three sizes",
        "modelled",
        bars([(f"{round(ft, 1):g} ft across", sqft, f"{sqft:,.0f} sq ft", "ours")
              for ft, sqft in f["sizes"]]),
        f"Every size is the same {f['members']:.0f} members and {f['panels']:.0f} panels on the "
        f"same two lengths: one jig, one hardware set, one way of working."))
    out.append(panel(
        "The skin, and keeping it",
        "estimated &middot; see the table",
        bars([("Woven sailcloth", f["skin_sail"], money(f["skin_sail"]), "them"),
              ("Cotton duck + silicone", f["skin_diy"], money(f["skin_diy"]), "ours"),
              ("Beeswax recoat", f["wax_usd"], money(f["wax_usd"]), "soft")]),
        f"{f['skin_layers']:.0f} layers, {f['skin_m2']:,.0f} m&sup2; of 100% cotton soaked in "
        f"silicone. A beeswax coat every {D['wax_every_lo']:.0f}&ndash;{D['wax_every_hi']:.0f} years: "
        f"{f['wax_kg']:.1f} kg, about {f['wax_hours']:.0f} hours."))
    out.append(panel(
        "Wood kept from the log",
        "simulated &middot; mill allowance the author's",
        bars([("Sawn into two-by-fours", f["sawn_pct"], f"{f['sawn_pct']:.0f}%", "them"),
              ("A good mill, mixed sizes", f["mill_pct"], f"{f['mill_pct']:.0f}%", "them"),
              ("Split into wedges", f["split_pct"], f"{f['split_pct']:.0f}%", "ours")]),
        "The frame comes from the tree where it stands; the corners of a log are not waste."))
    picks = sorted(f["panel_types"], key=lambda r: r[1])
    shown = [picks[0], picks[len(picks) // 3], picks[2 * len(picks) // 3], picks[-1]]
    out.append(panel(
        "Snap-in, not built-in",
        "modelled",
        bars([(label, usd, money(usd), "ours") for label, usd in shown]),
        f"{len(picks)} panel types and {f['modules']} snap-in modules, from "
        f"{money(picks[0][1])} to {money(picks[-1][1])}. A bay changes with a driver, not a builder."))
    out.append(panel(
        "The core, over its life",
        "modelled",
        bars([("Build a core", f["core_usd"], money(f["core_usd"]), "ours"),
              ("Move it to the next dome", f["core_move"], money(f["core_move"]), "soft"),
              (f"Each year of its {f['core_life']:.0f}", f["core_usd"] / f["core_life"],
               money(f["core_usd"] / f["core_life"]), "soft")]),
        f"Buy the plumbing once. The core carries {len(f['core_services'])} services "
        f"({E(', '.join(f['core_services']))}) and outlives the shell around it."))
    out.append(panel(
        "Hours of work",
        "measured &middot; estimated",
        bars([("Splitting, measured", f["split_h"], f"{f['split_h']:g} h", "ours"),
              ("Frame, mistakes allowed for", f["frame_h"], f"{f['frame_h']:g} h", "ours"),
              ("Whole building", f["build_h"], f"{f['build_h']:g} h", "soft")]),
        f"The frame clock keeps {f['error_h']:g} hours for getting it wrong. The whole building, "
        f"counted the same way, is about {f['build_h']:g} hours."))
    return out


def declared_table() -> str:
    rows = "".join(f"<tr><td>{E(d.key)}</td><td class='n'>{d.value:g} {E(d.unit)}</td>"
                   f"<td>{E(d.kind)}</td><td>{E(d.why)}</td></tr>" for d in DECLARED)
    return ('<table class="declared"><caption>Declared, not computed: the beeswax upkeep</caption>'
            f"<tbody>{rows}</tbody></table>")


CSS = f"""
@page {{ size: 8.5in 11in; margin: .36in .42in .32in; }}
/* A title, then a three-by-three grid of panels, each one chart drawn to scale. */
:root {{ --paper: #ffffff; --ground: #e9e3d9; --ink: #1d1d1b; --ink-2: #333333; --ink-3: #444444;
         --muted: #666666; --rule: #d8d2c8; --rule-2: #e4dfd6; --tile: #faf6f0;
         --wood: #b0601e; --blue: #2f5d7c; --green: #2f7d4f; --amber: #8a6508; --red: #8c2f1f;
         --them: #9a948a; --soft: #e2b98f; --k: 1; }}
html, body {{ background: var(--paper); margin: 0; }}
body {{ font: {pitch._pt(BODY_PT)}/1.36 {pitch.SANS}; color: var(--ink); }}
.top {{ display: flex; justify-content: space-between; align-items: end; gap: .2in;
        border-bottom: 2px solid var(--wood); padding-bottom: .06in; margin-bottom: .1in; }}
.top .eyebrow {{ font: 700 {pitch._pt(7.2)} {pitch.SANS}; letter-spacing: .2em; text-transform: uppercase;
                 color: var(--wood); margin: 0; }}
.top h1 {{ font: 800 {pitch._pt(24)}/1.05 {pitch.SANS}; margin: .03in 0 0; text-wrap: balance; }}
.top .sub {{ font: italic {pitch._pt(10.5)}/1.3 {pitch.SERIF}; color: var(--ink-2); margin: .03in 0 0; }}
.top .key {{ font-size: {pitch._pt(7.2)}; color: var(--muted); text-align: right; min-width: 0; }}
.key i {{ display: inline-block; width: .16in; height: .08in; margin: 0 .04in 0 .1in; border-radius: 1px; }}
.grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .1in .2in; }}
.panel {{ min-width: 0; border-top: 1px solid var(--rule); padding-top: .05in; break-inside: avoid; }}
.panel h2 {{ font: 800 {pitch._pt(9.2)} {pitch.SANS}; letter-spacing: .04em; text-transform: uppercase;
             color: var(--blue); margin: 0 0 .05in; }}
.panel .note {{ margin: .04in 0 0; color: var(--ink-2); }}
.panel .kind {{ font: 700 {pitch._pt(5.8)} {pitch.SANS}; letter-spacing: .12em; text-transform: uppercase;
                color: var(--muted); margin: .04in 0 0; }}
svg.chart {{ width: 100%; height: auto; display: block; overflow: visible; }}
svg .lab {{ font: {pitch._pt(6.6)} {pitch.SANS}; fill: var(--ink-3); }}
svg .val {{ font: 700 {pitch._pt(6.8)} {pitch.SANS}; fill: var(--ink); }}
.ours, i.ours {{ fill: var(--wood); background: var(--wood); }}
.them, i.them {{ fill: var(--them); background: var(--them); }}
.soft, i.soft {{ fill: var(--soft); background: var(--soft); }}
.seg.frame, i.frame {{ fill: #c98a4b; background: #c98a4b; }}
.seg.shell, i.shell {{ fill: var(--blue); background: var(--blue); }}
.seg.core, i.core {{ fill: var(--wood); background: var(--wood); }}
.seg.panels, i.panels {{ fill: var(--green); background: var(--green); }}
.seg.labour, i.labour {{ fill: var(--amber); background: var(--amber); }}
.seg.over, i.over {{ fill: var(--them); background: var(--them); }}
.seg.margin, i.margin {{ fill: var(--red); background: var(--red); }}
path.brace {{ fill: none; stroke: var(--ink); stroke-width: .8; }}
ul.legend {{ list-style: none; margin: .04in 0 0; padding: 0;
             font-size: {pitch._pt(6.5)}; }}
ul.legend li {{ break-inside: avoid; }}
ul.legend i {{ display: inline-block; width: .09in; height: .09in; margin-right: .04in; vertical-align: -1px; }}
ul.legend span {{ color: var(--muted); }}
table.declared {{ border-collapse: collapse; width: 100%; margin-top: .1in; font-size: {pitch._pt(6.8)}; }}
table.declared caption {{ text-align: left; font: 800 {pitch._pt(7.4)} {pitch.SANS}; letter-spacing: .06em;
                          text-transform: uppercase; color: var(--amber); padding-bottom: .03in; }}
table.declared td {{ border-top: .5px solid var(--rule-2); padding: .02in .06in .02in 0; vertical-align: top; }}
table.declared td.n {{ white-space: nowrap; font-variant-numeric: tabular-nums; }}
.foot {{ margin-top: .1in; padding-top: .04in; border-top: 1px solid var(--rule); font-size: {pitch._pt(6.6)};
         color: var(--muted); }}
.foot a {{ color: var(--ink); font-weight: 700; text-decoration: none; }}
"""

WEB_CSS = f"""
@media screen {{
  :root {{ --k: 1.35; }}
  html {{ background: var(--ground); }}
  body {{ max-width: 10.4in; margin: 0 auto; padding-block: 28px; padding-inline: 32px; background: var(--paper); }}
}}
@media screen and (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{ {pitch.DARK} --them: #77716a; --soft: #8a6a4a; }}
}}
:root[data-theme="dark"] {{ {pitch.DARK} --them: #77716a; --soft: #8a6a4a; }}
@media screen and (max-width: 900px) {{ .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
@media screen and (max-width: 620px) {{
  :root {{ --k: 1.45; }}
  body {{ padding-inline: 16px; padding-block: 20px; }}
  .top {{ flex-direction: column; align-items: start; }}
  .top .key {{ text-align: left; }}
  .grid {{ grid-template-columns: minmax(0, 1fr); }}
  .declared-wrap {{ overflow-x: auto; }}
}}
"""

WEB_TITLE = "40 Hour Cabin Efficiency"


def document(web: bool = False) -> str:
    from wedge_book import print_edition as pe

    f = facts()
    head = ('<div class="top"><div><p class="eyebrow">The 40 Hour Cabin &middot; modular housing &middot; by a veteran, for veterans</p>'
            "<h1>Efficiency, by the numbers</h1>"
            '<p class="sub">One standard body against the houses it would replace.</p></div>'
            '<div class="key"><i class="ours"></i>this building<i class="them"></i>the comparison'
            '<i class="soft"></i>variant or upkeep</div></div>')
    body = (head + '<div class="grid">' + "".join(panels()) + "</div>"
            + f'<div class="declared-wrap">{declared_table()}</div>'
            + f'<p class="foot">Every bar drawn to scale from the project&rsquo;s own models on {E(f["built"])}. '
              f'Sources and code: <a href="https://{E(pe.PROJECT_URL)}">{E(pe.PROJECT_URL)}</a>. '
              "Modelled figures are what the software computes; published ones are cited in its source; "
              "estimates are declared above or in the module that uses them.</p>")
    if web:
        return f"<title>{E(WEB_TITLE)}</title><style>{CSS}{WEB_CSS}</style>{body}"
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>'
            f"{E(outline.TITLE)}: efficiency</title><style>{CSS}</style></head><body>{body}</body></html>")


def problems(doc) -> list[str]:
    from wedge_book import print_edition as pe

    found = []
    if len(doc) != 1:
        found.append(f"the sheet runs to {len(doc)} pages; it must be one")
    shrunk = pe.scale_problem(doc, BODY_PT)
    if shrunk:
        found.append(shrunk)
    return found


def _print(path: Path) -> None:
    from two_v_demo import book_export

    chrome = book_export._chrome_path()
    if not chrome:
        raise RuntimeError("the sheet needs Chrome or Edge to print with")
    book_export._pdf_via_chrome(document(), path, chrome)


def build() -> tuple[Path, Path, Path]:
    """The sheet, its preview, and the two-page pack: the pitch, then this."""
    import pymupdf

    with tempfile.TemporaryDirectory() as scratch:
        sheet_proof = Path(scratch) / "sheet.pdf"
        pitch_proof = Path(scratch) / "pitch.pdf"
        _print(sheet_proof)
        pitch._print(pitch_proof)
        sheet, front = pymupdf.open(sheet_proof), pymupdf.open(pitch_proof)
        try:
            found = problems(sheet) + pitch.problems(front)
            if found:
                raise RuntimeError("; ".join(found))
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            pdf = next_version_path(OUT_DIR / f"{STEM}.pdf")
            png = pdf.with_suffix(".png")
            pack = next_version_path(OUT_DIR / f"{PACK_STEM}.pdf")
            for path in (png,):
                if path.exists():
                    raise FileExistsError(f"{path.name} already exists; deliverables are never overwritten")
            meta = {"author": outline.AUTHOR, "keywords": "modular housing, geodesic dome, efficiency"}
            sheet.set_metadata({**meta, "title": f"{outline.TITLE}: efficiency, by the numbers"})
            sheet.save(pdf, garbage=3, deflate=True)
            sheet[0].get_pixmap(dpi=150).save(png)
            both = pymupdf.open()
            both.insert_pdf(front)
            both.insert_pdf(sheet)
            both.set_metadata({**meta, "title": f"{outline.TITLE}: the project on one page, and its numbers"})
            both.save(pack, garbage=3, deflate=True)
            both.close()
        finally:
            sheet.close()
            front.close()
    return pdf, png, pack


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--proof", type=Path, metavar="PDF", help="print here, outside deliverables/, and report")
    parser.add_argument("--web", type=Path, metavar="FILE", help="write the screen version here and stop")
    args = parser.parse_args(argv)
    if args.web:
        args.web.parent.mkdir(parents=True, exist_ok=True)
        args.web.write_text(document(web=True), encoding="utf-8")
        print(f"wrote {args.web}")
        return 0
    if args.proof:
        import pymupdf

        if OUT_DIR.resolve() in args.proof.resolve().parents:
            parser.error("a proof goes outside deliverables/")
        _print(args.proof)
        doc = pymupdf.open(args.proof)
        found = problems(doc)
        doc.close()
        print(f"wrote {args.proof}" + "".join(f"\n  PROBLEM: {p}" for p in found))
        return 1 if found else 0
    pdf, png, pack = build()
    print(f"wrote {pdf}\n      {png}\n      {pack}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
