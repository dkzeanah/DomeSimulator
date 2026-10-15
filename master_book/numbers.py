"""The numbers page: the arithmetic an investor or a grant panel will ask for, on one page.

    py -3.12 -m master_book.numbers        # numbers PDF, and the pitch and summary packs that include it

Every figure is computed by the model that owns it -- the standard building's
cost stack and margin (:func:`kickstarter.cost_stack`), the reward tiers
(:func:`kickstarter.tiers`), the startup (:class:`two_v_demo.dome_costing.Startup`),
the pad host's payback (:func:`two_v_demo.byod_facts.payback_rows`), the
mortgage comparison (``why.*``), the published benchmarks
(:mod:`two_v_demo.house_economics`, HUD) -- and every row says whether it is
modelled, declared or published. The last table is the numbers that argue back.
"""

from __future__ import annotations

import html
import math
import tempfile
from pathlib import Path

from . import outline, pitch

E = html.escape
OUT = pitch.OUT_DIR
STEM = "the-40-hour-cabin-numbers"
BODY_PT = 7.9


def money(v: float) -> str:
    return f"${v:,.0f}"


def facts() -> dict:
    import kickstarter as k
    import seed_model

    from square_book import tokens as sq
    from two_v_demo import byod_facts as bf
    from two_v_demo.dome_costing import Startup
    from wedge_zome import fabrication as zf

    def tok(name: str) -> str:
        return sq.resolve("{{" + name + "}}")

    def num(name: str) -> float:
        return float(tok(name).replace(",", "").replace("$", ""))

    cs = k.cost_stack()
    floor = seed_model.seed_geometry().floor_decagon_sqft
    standing = cs.price + cs.ground
    ask = pitch.ask()
    site = num("why.site_usd_per_sqft")
    from two_v_demo import house_economics as he
    mhs = he.value("mhs_2023_usd_per_sqft")
    from two_v_demo.dome_costing import build_variants

    s = Startup()
    budget = build_variants()[1]
    tiers = list(k.tiers())
    pad_rows = bf.payback_rows()
    unsheltered = pitch.VETERANS["unsheltered"][0]
    return {
        "groups": [(label, cost) for _k, label, cost in cs.groups], "direct": cs.direct, "overhead": cs.overhead,
        "warranty": cs.warranty, "built": cs.built, "margin": cs.margin, "margin_pct": k.MARGIN * 100,
        "price": cs.price, "per_sqft": cs.per_sqft, "ground": cs.ground, "standing": standing, "floor": floor,
        "site_sqft": site, "mhs_sqft": mhs, "site_same": site * floor, "mhs_same": mhs * floor,
        "ask": ask, "buildings_to_repay": math.ceil(ask["total"] / cs.margin),
        "startup_equipment": s.equipment_total, "startup_working": s.working_capital, "startup_units": s.units_fundable(budget), "budget_name": budget.name.title(),
        "tiers": tiers,
        "run_dome": num("kick.run_dome"), "run_box": num("kick.run_box"), "run_saved": num("kick.run_saved"),
        "core": num("core.cost"), "core_life": num("core.life"), "core_move": num("core.moves"),
        "loan": num("why.loan"), "loan_total": num("why.loan_total"), "loan_interest": num("why.loan_interest"),
        "loan_pct": num("why.mortgage_pct"), "loan_years": num("why.mortgage_years"),
        "pad_target": num("park.pad_target"), "starter_cost": num("park.starter_cost"),
        "starter_gap": num("park.starter_gap"), "occupancy": num("park.occupancy"),
        "pad_costs": num("park.yearly_costs"), "pad_rows": pad_rows,
        "unsheltered": unsheltered, "vets_scale": unsheltered * standing, "when": pitch.VETERANS_COUNTED,
        "labour_hours": num("money.labour_hours"), "squares_pct": num("sq.squares_pct"),
        "sawn_pct": num("sq.sawn_pct"), "zome_sections": zf.facts("wedge")["stock"]["sections"],
        "dome_sections": num("parts.sections"),
    }


def _table(title: str, kind: str, rows, head=None, total=None) -> str:
    out = [f'<section><h2>{E(title)}<span class="kind">{E(kind)}</span></h2><table>']
    if head:
        out.append("<tr>" + "".join(f"<th>{E(h)}</th>" for h in head) + "</tr>")
    for r in rows:
        out.append("<tr>" + "".join(f'<td class="{"n" if j else ""}">{c}</td>' for j, c in enumerate(r)) + "</tr>")
    if total:
        out.append('<tr class="total">' + "".join(f'<td class="{"n" if j else ""}">{c}</td>' for j, c in enumerate(total))
                   + "</tr>")
    out.append("</table></section>")
    return "".join(out)


def page() -> str:
    f = facts()
    unit = _table(
        "One standard building: cost to price", "modelled",
        [[E(label), money(c)] for label, c in f["groups"]] +
        [["Materials and labour", money(f["direct"])], ["Overhead", money(f["overhead"])],
         ["Warranty reserve", money(f["warranty"])], ["<b>Cost to build</b>", f"<b>{money(f['built'])}</b>"],
         [f"Maker's margin, {f['margin_pct']:.0f}% on cost (declared)", money(f["margin"])]],
        total=["List price", money(f["price"])])
    compare = _table(
        f"The same {f['floor']:.0f} sq ft, bought three ways", "published · modelled",
        [["New site-built house, without land (NAHB)", money(f["site_same"]), f"${f['site_sqft']:.0f}"],
         ["New manufactured home (Census 2023)", money(f["mhs_same"]), f"${f['mhs_sqft']:.0f}"],
         ["This standard building", money(f["price"]), f"${f['per_sqft']:.2f}"],
         ["... standing on its pad, at cost", money(f["standing"]), f"${f['standing'] / f['floor']:.2f}"]],
        head=["", "for the floor", "a sq ft"])
    buckets = _table(
        f"What the ask buys: {money(f['ask']['total'])}", "the campaign's costed lines",
        [[E(b["title"]), money(b["usd"])] for b in f["ask"]["buckets"]] +
        [["Margins that repay the ask, at one building's margin each",
          f"{f['buildings_to_repay']} buildings"],
         ["Startup model: equipment + working capital",
          f"{money(f['startup_equipment'])} + {money(f['startup_working'])}"],
         [f"Materials the working capital buys, at the {E(f['budget_name'])} build's price",
          f"{f['startup_units']:.1f} domes"]])
    tiers = _table(
        "Campaign rewards: what each tier leaves", "modelled",
        [[E(t.label), money(t.pledge), money(t.cost), f"{t.margin_fraction * 100:.0f}%"] for t in f["tiers"]],
        head=["tier", "pledge", "cost to send", "kept"])
    owner = _table(
        "For the owner", "modelled · illustrative",
        [["Heating and cooling, a year: this building / a box of the same floor",
          f"{money(f['run_dome'])} / {money(f['run_box'])}"],
         ["Never spent, every year", money(f["run_saved"])],
         [f"Utility core, over its {f['core_life']:.0f}-year life", f"{money(f['core'] / f['core_life'])} a year"],
         ["Moving the core to the next building", money(f["core_move"])],
         [f"For comparison: a {money(f['loan'])} mortgage at {f['loan_pct']:.1f}% for {f['loan_years']:.0f} years",
          f"{money(f['loan_total'])} repaid, {money(f['loan_interest'])} of it interest"],
         ["This building on its pad, at cost, paid once", money(f["standing"])]])
    host = _table(
        f"For a pad host: a {money(f['pad_target'])} pad (the author's target) at {f['occupancy']:.0f}% occupancy",
        "scenario",
        [[f"{money(rent)} a month", f"{money(net)} a year net", f"{months:.1f} months to repay"]
         for rent, net, months in f["pad_rows"]] +
        [["Management, tax and insurance, a year", money(f["pad_costs"]), ""]],
        head=["rent", "after costs", "payback"])
    scale = _table(
        "For scale", "published · modelled",
        [[f"Unsheltered veterans, one night in {E(f['when'])} (HUD)", f"{f['unsheltered']:,}", ""],
         ["A standard building on its pad for each, at cost, before land", money(f["vets_scale"]), ""]])
    against = _table(
        "The numbers that argue back", "computed",
        [[f"The starter pad, computed, against the {money(f['pad_target'])} target",
          f"{money(f['starter_cost'])} ({money(f['starter_gap'])} over)"],
         ["Labour in the standard building", f"about {f['labour_hours']:.0f} hours, not forty"],
         ["Two wedges planed square keep of the log / a mill's 2x4s",
          f"{f['squares_pct']:.0f}% / {f['sawn_pct']:.0f}%"],
         ["Rated by an engineer", "not yet -- the first line of the ask"],
         ["Margin, prices, rents", "declared or estimated, each named in the code"]])
    css = f"""
    @page {{ size: 8.5in 11in; margin: .4in .42in .36in; }}
    html, body {{ background: #fff; margin: 0; }}
    body {{ font: {BODY_PT}pt/1.3 "Segoe UI", Helvetica, Arial, sans-serif; color: #1d1d1b; }}
    h1 {{ font: 800 21pt/1 "Segoe UI", sans-serif; margin: 0; }}
    .sub {{ font: italic 10pt Georgia, serif; color: #444; margin: .04in 0 .1in; }}
    .grid {{ columns: 2; column-gap: .26in; }}
    section {{ break-inside: avoid; margin-bottom: .1in; }}
    h2 {{ font: 800 8.6pt "Segoe UI", sans-serif; text-transform: uppercase; letter-spacing: .05em; color: #2f5d7c;
          margin: 0 0 .03in; border-bottom: 1px solid #d8d2c8; padding-bottom: .015in; }}
    .kind {{ float: right; font: 700 6pt "Segoe UI", sans-serif; color: #8a8478; letter-spacing: .1em; }}
    table {{ border-collapse: collapse; width: 100%; }}
    td, th {{ padding: .018in .04in .018in 0; border-bottom: .5px solid #ebe6dd; vertical-align: top; text-align: left; }}
    th {{ font-size: 6.8pt; color: #666; }}
    td.n {{ text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }}
    tr.total td {{ font-weight: 800; border-top: 1.2px solid #1d1d1b; border-bottom: 0; color: #b0601e; }}
    .foot {{ margin-top: .06in; font-size: 6.6pt; color: #777; }}
    """
    body = (f"<h1>{E(outline.TITLE)}: the numbers</h1>"
            '<p class="sub">What one building costs, what it sells for, what the money buys, and what argues back.</p>'
            f'<div class="grid">{unit}{compare}{buckets}{owner}{host}{tiers}{scale}{against}</div>'
            '<p class="foot">Every figure computed by the project\'s own models on the day this page was printed; '
            "modelled figures are the software's, published ones are cited (NAHB, Census, HUD), declared ones are named "
            f"with their reason in the code. github.com/dkzeanah/DomeSimulator</p>")
    return (f'<!doctype html><html><head><meta charset="utf-8"><title>The numbers</title><style>{css}</style>'
            f"</head><body>{body}</body></html>")


def build() -> list[Path]:
    import pymupdf

    from two_v_demo import book_export
    from two_v_demo.deliverables import next_version_path
    from wedge_book import print_edition as pe

    from . import efficiency

    chrome = book_export._chrome_path()
    out = []
    with tempfile.TemporaryDirectory() as scratch:
        sheet = Path(scratch) / "numbers.pdf"
        book_export._pdf_via_chrome(page(), sheet, chrome)
        doc = pymupdf.open(sheet)
        try:
            if len(doc) != 1:
                raise RuntimeError(f"the numbers page runs to {len(doc)} pages; it must be one")
            shrunk = pe.scale_problem(doc, BODY_PT)
            if shrunk:
                raise RuntimeError(shrunk)
            pdf = next_version_path(OUT / f"{STEM}.pdf")
            doc.set_metadata({"title": f"{outline.TITLE}: the numbers", "author": outline.AUTHOR})
            doc.save(pdf, garbage=3, deflate=True)
            png = pdf.with_suffix(".png")
            if not png.exists():
                doc[0].get_pixmap(dpi=150).save(png)
            out += [pdf, png]
        finally:
            doc.close()

    def newest(stem: str) -> Path:
        import medialib
        found = [p for p in medialib.locate(OUT / f"{stem}.pdf").parent.glob(f"{stem}*.pdf")]
        return max(found, key=lambda p: p.stat().st_mtime)

    # The packs: the pitch with its numbers and charts; the summary with its numbers.
    for name, parts in (("the-40-hour-cabin-pitch-pack", ("the-40-hour-cabin-one-pager", STEM,
                                                          efficiency.STEM)),
                        ("domesim-summary-pack", ("domesim-project-summary", STEM))):
        pack = pymupdf.open()
        for stem in parts:
            src = pymupdf.open(newest(stem))
            pack.insert_pdf(src)
            src.close()
        dest = next_version_path(OUT / f"{name}.pdf")
        pack.set_metadata({"title": name.replace("-", " "), "author": outline.AUTHOR})
        pack.save(dest, garbage=3, deflate=True)
        pack.close()
        out.append(dest)
    return out


if __name__ == "__main__":
    for p in build():
        print(f"wrote {p}")
