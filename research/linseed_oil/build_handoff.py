"""Refresh this film's read-only source audit, script and validation handoff.

Run from DomeSim: py -3.12 research/linseed_oil/build_handoff.py
This does not render, write launcher state, modify the source DB or touch a release.
"""
from __future__ import annotations

import ast
import difflib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent

from two_v_demo import linseed_oil as facts
from two_v_demo.lesson_cabin_linseed_oil import CABIN_LINSEED_OIL_LESSON as lesson
from two_v_demo.narration import narration_script


def main():
    checks = []

    def log(text):
        print(text, flush=True)
        checks.append(text)

    facts.validate_linseed_oil()
    log("Facts selftest: PASS")
    lesson.selftest()
    log("Film geometry, labels, cameras and declarations: PASS")
    from two_v_demo import deliverables
    import render_presets
    from two_v_demo.lesson_registry import LESSONS
    from two_v_demo.teasers import teaser_lesson, estimate_seconds, MAX_SECONDS

    for name, fn in (("Deliverables", deliverables.validate_deliverables),
                     ("Render presets", render_presets.validate_render_presets)):
        try:
            fn()
            log(name + ": PASS")
        except AssertionError as exc:
            # Report pre-existing global discrepancies, never silently pass them.
            log(name + ": FAIL -- " + str(exc))
    assert LESSONS[lesson.key] is lesson
    assert deliverables.DELIVERABLE_BY_LESSON[lesson.key].compose
    assert render_presets.PRESET_BY_KEY[lesson.key].fields["lesson"] == lesson.key
    assert render_presets.PRESET_BY_KEY[lesson.key + "_stills"].fields["action"] == "shots"
    log("New lesson registration, deliverable and launch presets: PASS")

    source = ROOT / "two_v_demo/lesson_cabin_linseed_oil.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "ch":
            narrative = node.args[4]
            # Only spoken literal pieces, not digits in f-string format specs.
            pieces = narrative.values if isinstance(narrative, ast.JoinedStr) else [narrative]
            for value in pieces:
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    assert not any(c.isdigit() for c in value.value), (node.lineno, value.value)
    log("Narration literal-digit audit: PASS")
    teaser = teaser_lesson(lesson.key)
    teaser.validate()
    assert estimate_seconds(teaser) <= MAX_SECONDS
    log(f"Teaser composition: PASS ({estimate_seconds(teaser):.1f}s estimate)")
    log("Visual still review: PENDING -- must run after the other GPU job finishes")
    log("Landscape / phone / release / teaser video: NOT RENDERED")
    (OUT / "validation.txt").write_text("\n".join(checks) + "\n", encoding="utf-8")
    (OUT / "facts-report.txt").write_text(facts.report() + "\n", encoding="utf-8")
    script = narration_script(None, lesson.chapters, lesson.title)
    script = script.replace("The timestamps match the deterministic ModernGL video export.",
                            "PLANNED timing only. Narration and spliced segments change final timestamps. Visual review and export are pending.")
    (OUT / "film-script.md").write_text(script, encoding="utf-8")

    rows = ["# Source audit: Linseed Oil for a Dome", "",
            f"Source: [{facts.SOURCE['title']}]({facts.SOURCE['url']}) by {facts.SOURCE['creator']}.", "",
            f"Transcript-library record {facts.SOURCE['record_id']}, read through SQLite read-only mode. "
            "Rolling caption overlaps were removed by matching token suffixes/prefixes. Original wording and database were not changed. "
            "These timestamps refer to the source video, not the new film.", "",
            "| Item | Source time | Topic | Treatment | Dome application |",
            "|---|---|---|---|---|"]
    for n, t, topic, treatment, note in facts.TOPICS:
        minutes, seconds = map(int, t.split(":"))
        url = facts.SOURCE["url"] + f"&t={minutes * 60 + seconds}"
        rows.append(f"| {n} | [{t}]({url}) | {topic} | {treatment} | {note} |")
    rows += ["", "## Verification sources", "", "Consulted September 30, 2026. "
             "Manufacturer instructions describe the named formulation; they are not independent test results.", ""]
    notes = {
        "danish": "Interior application schedule and product-specific food-contact use.",
        "wax": "Separate application schedule for the oil-and-wax blend.",
        "faq": "Water resistance and exposure/compatibility limits. Coverage wording differs from the product page; the film uses the product page claim and does not treat it as a measurement.",
        "rags": "Fire-service storage and disposal guidance.",
        "fire": "Municipal guidance on heat buildup, rag storage and local disposal.",
        "wood": "FPL discussion of wood species, finish and weather effects on mildew, page 18.",
        "bond": "Oil and wax contamination must be removed before bonding.",
        "glass": "Sash preparation and retainers; plastic panes and IGUs with organic seals are excluded. This sash specification does not establish overhead suitability.",
    }
    rows += [f"- [{name}]({url}): {notes[name]}" for name, url in facts.REFERENCES.items()]
    rows += ["", "## Editorial decisions", "",
             "The transcript provides no controlled test establishing superiority to all hardware-store finishes, "
             "no reliable financial saving and no evidence of structural restoration. These claims are not repeated. "
             "Dome-envelope and joint guidance applies the documented limits to this assembly; it is not a tested new building system.", "",
             "All twenty topics are accounted for above. No source video or audio is reused. "
             "The new narration and procedural scenes are original; the music bed is the existing synthesized Cabin World score."]
    (OUT / "source-audit.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    before = json.loads((OUT / "registration-before.json").read_text(encoding="utf-8"))
    diff = "".join("".join(difflib.unified_diff(text.splitlines(True),
                   (ROOT / path).read_text(encoding="utf-8").splitlines(True),
                   fromfile="before/" + path, tofile="after/" + path)) for path, text in before.items())
    (OUT / "registration.diff").write_text(diff, encoding="utf-8")
    print(f"Wrote script and source audit: {len(lesson.chapters)} chapters; "
          f"{sum(len(ch.narration[0].split()) for ch in lesson.chapters)} narration words.", flush=True)


if __name__ == "__main__":
    main()
