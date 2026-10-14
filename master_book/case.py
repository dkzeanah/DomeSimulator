"""The case: who it is for, how it is owned, why the benefits stack, why it scales,
why it is hard to fail -- and what could still go wrong. Two pages.

    py -3.12 -m master_book.case          # the case PDF, and a pitch pack with it in front

Positioning, in the owner's words: a storage building, but livable, owned the
way an RV is owned. Every figure is computed by the model that owns it (through
:mod:`master_book.numbers`, :mod:`master_book.efficiency`, :mod:`wedge_zome`
and the books' tokens). Nothing here says it cannot fail; it says how the
design keeps the downside small, and then names the risks that remain.
"""

from __future__ import annotations

import html
import tempfile
from pathlib import Path

from . import outline, pitch

E = html.escape
OUT = pitch.OUT_DIR
STEM = "the-40-hour-cabin-the-case"
BODY_PT = 8.5


def money(v: float) -> str:
    return f"${v:,.0f}"


def facts() -> dict:
    import seed_model

    from square_book import tokens as sq
    from wedge_zome import fabrication as zf

    from . import efficiency, numbers

    n = numbers.facts()
    e = efficiency.facts()
    z = zf.facts("wedge")

    def tok(name: str) -> str:
        return sq.resolve("{{" + name + "}}")

    panels = [p for p in seed_model.PANELS if p.usd > 0]
    return {**n, "e": e, "z": z,
            "small_ft": tok("flat.small_ft"), "small_sqft": tok("flat.small_sqft"),
            "big_ft": tok("flat.big_ft"), "big_sqft": tok("flat.big_sqft"),
            "members": tok("dome.members"), "dome_panels": tok("dome.panels"), "clock": tok("clock.total"),
            "strut_lo": tok("web.strut_lo"), "strut_hi": tok("web.strut_hi"), "seeds": tok("seed.count"),
            "services": tok("core.services"), "halves": f"{seed_model.declared('shell_halves'):.0f}",
            "panel_types": len(panels), "modules": len(seed_model.MODULES),
            "panel_lo": min(p.usd for p in panels), "panel_hi": max(p.usd for p in panels),
            "rain_gal": e["rain_gal"], "rain_in": e["rain_in"], "skin_pct": e["skin_pct"],
            "split_pct": tok("sq.split_pct"), "weeks": tok("why.weeks"),
            "shirts": tok("tt_quilt.shirts_per_layer"), "quilt_r": tok("tt_quilt.r_per_layer"),
            "whole_pads": tok("park.whole_pads"), "whole_build": tok("park.whole_build"),
            "vets": f"{pitch.VETERANS['pit'][0]:,}"}


def stack_rows(f: dict) -> list[tuple[str, str, str]]:
    """The benefits, in the order they stack: (step, what it adds, running cost)."""
    g = dict(f["groups"])
    frame = g.get("Wedge-cut frame", 0.0)
    shell = g.get("Shower-cap shell", 0.0)
    core = g.get("Utility column and seal cap", 0.0) + g.get("Light, fan and cooling", 0.0)
    panels = g.get("Utility panels", 0.0)
    labour = g.get("Build labour", 0.0)
    run = 0.0
    rows = []
    for step, add, cost in (
        ("A frame", f"{f['members']} split-log members, {f['dome_panels']} panels: a covered, shaped space "
                    f"from trees you may already have", frame),
        ("A dry room", f"the weather shell, in {f['halves']} slices that two people carry and snap together", shell),
        ("A home's services", f"the utility core: {f['services']} services in one column, the RV's hookup "
                              f"built in; it lasts {f['core_life']:.0f} years and moves for {money(f['core_move'])}",
         core),
        ("Your building, not a box", f"snap-in panels -- {f['panel_types']} types, {f['modules']} modules -- "
                                     f"make it a home, a studio, a shop or a storage room", panels),
        ("Built for you", f"paid build labour, about {f['labour_hours']:.0f} hours -- or your own", labour),
    ):
        run += cost
        rows.append((step, add, money(run)))
    rows.append(("A business behind it", "overhead, a warranty reserve, and a margin printed on the invoice",
                 money(f["price"])))
    rows.append(("A place to stand", f"a serviced pad, at cost; or rent one from a host, like an RV site",
                 money(f["standing"])))
    return rows


def page() -> str:
    f = facts()
    stack = "".join(f"<tr><td class='s'>{k + 1}. {E(a)}</td><td>{E(b)}</td><td class='n'>{c}</td></tr>"
                    for k, (a, b, c) in enumerate(stack_rows(f)))
    who = [
        ("Veterans", f"{f['vets']} were homeless on one night in {E(f['when'])} (HUD). A small, squared-away "
                     "space, maintained on a schedule, built by a crew: a life a lot of veterans already know. "
                     f"Designed to sit beside {E(', '.join(pitch.VETERAN_PROGRAMS))}."),
        ("Single mothers", "A home that does not eat the household: one price, paid once, no mortgage, "
                           f"running costs of {money(f['run_dome'])} a year to heat and cool, and a building that "
                           "moves when the job or the school does."),
        ("Craftsmen", "A trade, not a product: split, cut on one jig, assemble, maintain. Every cut is "
                      "published; a crew that builds one can build the next, and sell them."),
        ("College students", "A room you own near campus, on a rented pad, that comes with you, or sells to "
                             "the next student, when you graduate."),
        ("Bachelors", "A first place of your own for the price of a used car, that grows a panel at a time "
                      "instead of a mortgage at a time."),
    ]
    who_html = "".join(f"<p><b>{E(a)}.</b> {b}</p>" for a, b in who)
    css = f"""
    @page {{ size: 8.5in 11in; margin: .45in .5in .42in; }}
    html, body {{ background: #fff; margin: 0; }}
    body {{ font: {BODY_PT}pt/1.4 Georgia, "Times New Roman", serif; color: #1d1d1b; }}
    h1 {{ font: 800 24pt/1 "Segoe UI", sans-serif; margin: 0; }}
    .sub {{ font: italic 12pt/1.35 Georgia, serif; color: #333; margin: .05in 0 .12in; }}
    h2 {{ font: 800 9.6pt "Segoe UI", sans-serif; text-transform: uppercase; letter-spacing: .06em; color: #2f5d7c;
          margin: .14in 0 .04in; border-bottom: 1px solid #d8d2c8; padding-bottom: .02in; break-after: avoid; }}
    p {{ margin: 0 0 .06in; }}
    b {{ font-family: "Segoe UI", sans-serif; color: #b0601e; }}
    .cols {{ columns: 2; column-gap: .3in; }}
    .cols p {{ break-inside: avoid; }}
    table {{ border-collapse: collapse; width: 100%; font: 8pt/1.35 "Segoe UI", sans-serif; }}
    td {{ padding: .03in .06in .03in 0; border-bottom: .5px solid #e6e0d6; vertical-align: top; }}
    td.s {{ font-weight: 800; white-space: nowrap; color: #1d1d1b; }}
    td.n {{ text-align: right; white-space: nowrap; font-weight: 700; color: #b0601e; }}
    .objective {{ font: 600 11pt/1.45 "Segoe UI", sans-serif; background: #faf6f0; border-left: 4px solid #b0601e;
                  padding: .08in .12in; margin: 0 0 .06in; }}
    .risk p {{ break-inside: avoid; }}
    .break {{ break-before: page; }}
    """
    body = f"""
    <h1>{E(outline.TITLE)}: the case</h1>
    <p class="sub">A storage building you can live in, owned the way an RV is owned.</p>
    <p class="objective">The objective: a small home a person can own outright for the price of a used car --
    {money(f['price'])} for the building, {money(f['standing'])} standing on its pad -- that moves with them,
    grows with them, and never becomes the thing that sinks them.</p>

    <h2>Who it is for</h2>
    <div class="cols">{who_html}</div>

    <h2>The model: a storage building, but livable; owned like an RV</h2>
    <p>Strip a house down to what it cannot do without and you have a shell, a floor, and the services. Build
    the shell the way a storage building is built -- simple, standard, the same every time -- and put the
    services in one place, the way an RV does: a <b>utility core</b> that plugs into a <b>serviced pad</b>.
    You own the building; you rent the ground, or own it. When you move, the building can come with you: the
    shell in {f['halves']} slices, the core for {money(f['core_move'])}. At {f['small_ft']} ft across the same
    parts make a {f['small_sqft']} sq ft shed; at the standard size, {f['floor']:.0f} sq ft of home; at
    {f['big_ft']} ft, {f['big_sqft']} sq ft.</p>

    <h2>How the benefits stack</h2>
    <table>{stack}</table>
    <p style="margin-top:.05in">And on top, for nothing extra: {f['skin_pct']:.0f}% less outside skin than a box of
    the same floor; heating and cooling {money(f['run_dome'])} a year against {money(f['run_box'])};
    {f['rain_gal']:,.0f} gallons of rain a year off its own seams at {f['rain_in']:.0f} in of rain; insulation
    quilted from recycled clothing, about {f['shirts']} shirts a layer, R-{f['quilt_r']} each.</p>

    <h2 class="break">Why it scales</h2>
    <div class="cols">
    <p><b>Simple.</b> {f['members']} members on two lengths, {f['dome_panels']} flat panels from one jig; the
    zome from the same wedges takes one bevel, {f['z']['half']:.1f}&deg;, for every cut. Nothing that needs a
    specialist, a crane or a factory to start.</p>
    <p><b>Stripped down.</b> A shell, a core, panels. Everything that makes it a particular building plugs in,
    so the body never changes and the factory never retools.</p>
    <p><b>Repeatable.</b> The same parts list at every size, the same cuts every time; the frame clock is
    {f['clock']} hours, measured where it could be. A crew that builds one has the jigs for the next.</p>
    <p><b>Universal.</b> {f['seeds']} buildings from one body, from {money(f['price'])}: a home,
    a studio, a shop, a nursery, cold storage. Wherever a shed can stand, this can.</p>
    <p><b>Modular.</b> {f['panel_types']} snap-in panel types ({money(f['panel_lo'])} to {money(f['panel_hi'])})
    and {f['modules']} modules; the core moves to the next building. Upgrades are a panel at a time.</p>
    <p><b>Open.</b> Every drawing, cut and number is published with the code that computes it. Anyone can
    build one; every builder makes the method stronger and the network bigger.</p>
    </div>

    <h2>Why it is hard to fail</h2>
    <div class="cols">
    <p><b>The floor is a building.</b> If it never becomes anybody's home, it is still a dry, serviced building
    with a use -- storage, a shop, a studio. The worst case is a good shed.</p>
    <p><b>Small stakes.</b> {money(f['price'])} is {f['price'] / f['site_same'] * 100:.0f}% of what the same floor costs
    as a new site-built house ({money(f['site_same'])}) and {f['price'] / f['mhs_same'] * 100:.0f}% of a new
    manufactured home. Nobody loses a house on it.</p>
    <p><b>It keeps its value by moving.</b> No land is tied up in it; it can be sold, moved or re-fitted. The core
    outlives the shell around it.</p>
    <p><b>Cheap to run, cheap to start.</b> {money(f['run_saved'])} a year not spent on heating and cooling; the
    splitting keeps {f['split_pct']}% of a log that might otherwise be firewood.</p>
    <p><b>Each piece is human-sized.</b> Every strut weighs {f['strut_lo']}&ndash;{f['strut_hi']} kg, weighed: one
    person lifts it. No crane, no lender, no specialist trade to begin.</p>
    <p><b>The host side pays.</b> A pad host's {money(f['pad_target'])} pad repays in
    {f['pad_rows'][1][2]:.1f} months at {money(f['pad_rows'][1][0])} a month, before financing and tax (a scenario).</p>
    <p><b>The money repays.</b> The ask, {money(f['ask']['total'])}, is the margin on {f['buildings_to_repay']} buildings.</p>
    </div>

    <h2>What could still go wrong -- and what is done about it</h2>
    <div class="cols risk">
    <p><b>It is not yet rated.</b> No engineer has signed the frame for wind and snow. That review is the first
    line of the ask.</p>
    <p><b>Rules differ by place.</b> Whether a building this size may be lived in, and on what kind of pad, is
    for each county's zoning and code to say. The small size is shed-sized; the standard size needs a permit
    in most places.</p>
    <p><b>It is not yet measured over a year.</b> Moisture in the seams and the skin's upkeep are modelled, not
    measured; the instrumented test dome is in the ask.</p>
    <p><b>The work is real.</b> About {f['labour_hours']:.0f} hours for the whole building, not forty; the starter
    pad computes at {money(f['starter_cost'])}, {money(f['starter_gap'])} over its target. These numbers are
    printed because they argue back.</p>
    </div>

    <h2>The ask</h2>
    <p>{money(f['ask']['total'])}, the sum of its costed lines: prove it ({money(f['ask']['buckets'][0]['usd'])}),
    make it repeatable ({money(f['ask']['buckets'][1]['usd'])}), build what an owner cannot
    ({money(f['ask']['buckets'][2]['usd'])}), seed the network ({money(f['ask']['buckets'][3]['usd'])}). The
    numbers page behind this one shows every line of the arithmetic. Built by {E(outline.AUTHOR)}, a U.S. Navy
    veteran, in the open: github.com/dkzeanah/DomeSimulator.</p>
    """
    return (f'<!doctype html><html><head><meta charset="utf-8"><title>The case</title><style>{css}</style>'
            f"</head><body>{body}</body></html>")


def build() -> list[Path]:
    import pymupdf

    from two_v_demo import book_export
    from two_v_demo.deliverables import next_version_path
    from wedge_book import print_edition as pe

    from . import efficiency, numbers

    with tempfile.TemporaryDirectory() as scratch:
        proof = Path(scratch) / "case.pdf"
        book_export._pdf_via_chrome(page(), proof, book_export._chrome_path())
        doc = pymupdf.open(proof)
        try:
            if len(doc) != 2:
                raise RuntimeError(f"the case runs to {len(doc)} pages; it is two")
            shrunk = pe.scale_problem(doc, BODY_PT)
            if shrunk:
                raise RuntimeError(shrunk)
            pdf = next_version_path(OUT / f"{STEM}.pdf")
            doc.set_metadata({"title": f"{outline.TITLE}: the case", "author": outline.AUTHOR})
            doc.save(pdf, garbage=3, deflate=True)
            for i in range(2):
                doc[i].get_pixmap(dpi=110).save(pdf.with_name(f"{pdf.stem}-p{i + 1}.png"))
        finally:
            doc.close()

    def newest(stem: str) -> Path:
        import medialib
        return max(medialib.locate(OUT / f"{stem}.pdf").parent.glob(f"{stem}*.pdf"),
                   key=lambda p: p.stat().st_mtime)

    pack = pymupdf.open()
    for stem in (STEM, "the-40-hour-cabin-one-pager", numbers.STEM, efficiency.STEM):
        src = pymupdf.open(newest(stem))
        pack.insert_pdf(src)
        src.close()
    dest = next_version_path(OUT / "the-40-hour-cabin-pitch-pack.pdf")
    pack.set_metadata({"title": f"{outline.TITLE}: the case, the page, the numbers, the charts",
                       "author": outline.AUTHOR})
    pack.save(dest, garbage=3, deflate=True)
    pack.close()
    return [pdf, dest]


if __name__ == "__main__":
    for p in build():
        print(f"wrote {p}")
