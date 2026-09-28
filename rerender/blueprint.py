"""The copy-prompt: one pasteable package that lets any capable model re-make a film.

"Evergreen" means nothing in it is remembered -- it is regenerated from the
repository every time it is asked for: the rules from ``CLAUDE.md`` as they
stand today, the Cabin World's API read out of its source, the landmarks as
the scene currently places them, the film's chapters read out of the lesson,
and the queue's history for this film, so a second session picks up where
the first stopped.

    py -3.12 -m rerender prompt why          # print it (and save rerender/prompts/why.md)
    py -3.12 -m rerender prompt --queue      # the "work the next item" version
"""

from __future__ import annotations

import inspect
from datetime import date
from pathlib import Path

from . import state
from .catalogue import ROOT, Item, by_key, load

PROMPTS = ROOT / "rerender" / "prompts"

WORKED_EXAMPLE = "two_v_demo/lesson_cabin_pilot.py"
SEPARATOR = "\n\n---\n\n"


def _read(rel: str) -> str:
    try:
        return (ROOT / rel).read_text(encoding="utf-8").strip()
    except OSError:
        return f"(could not read {rel})"


def _api(module, names) -> str:
    lines = []
    for name in names:
        obj = getattr(module, name)
        try:
            sig = str(inspect.signature(obj))
        except (TypeError, ValueError):
            sig = ""
        doc = (inspect.getdoc(obj) or "").strip().split("\n\n")[0].replace("\n", " ")
        lines.append(f"- `{name}{sig}`" + (f" -- {doc}" if doc else ""))
    return "\n".join(lines)


def _demote(markdown: str) -> str:
    """Push a quoted document's headings two levels down, under this one's."""
    return "\n".join("##" + line if line.startswith("#") else line
                     for line in markdown.splitlines())


def _landmarks() -> str:
    from two_v_demo import cabin_world as cw

    m = cw.landmarks()
    rows = []
    for name, value in vars(m).items():
        if hasattr(value, "__len__") and not isinstance(value, str):
            text = "(" + ", ".join(f"{float(v):.2f}" for v in value) + ")"
        else:
            text = f"{value:.3f}" if isinstance(value, float) else str(value)
        rows.append(f"| `{name}` | {text} |")
    return "| landmark | value (m, z up) |\n|---|---|\n" + "\n".join(rows)


def _chapters(item: Item) -> str:
    out = []
    for ch in item.chapters:
        block = [f"#### {ch.number}. {ch.title}"]
        if ch.promise:
            block.append(f"*Promise:* {ch.promise}")
        if ch.narration:
            block.append(f"*Narration:* {ch.narration}")
        if ch.equations:
            block.append("*On-screen figures:* " + "; ".join(f"`{e}`" for e in ch.equations))
        if ch.bullets:
            block.append("*Concepts / callouts:*\n" + "\n".join(f"- {b}" for b in ch.bullets))
        out.append("\n".join(block))
    return "\n\n".join(out)


def _history(item: Item) -> str:
    data = state.load()
    e = state.entry(data, item)
    head = (f"Status **{e['status']}**, priority **{e['priority']}**"
            + (f", held by **{e['owner']}**" if e["owner"] else "")
            + (f", last update {e['updated']}" if e["updated"] else "") + ".")
    if e["outputs"]:
        head += "\n\nOutputs recorded so far:\n" + "\n".join(f"- `{o}`" for o in e["outputs"])
    if e["log"]:
        head += "\n\nLog (oldest first) -- read it; an earlier session may have left work half done:\n"
        head += "\n".join(f"- {x['at']} **{x['by'] or '?'}**: {x['text']}" for x in e["log"][-25:])
    return head


def _related(item: Item, items: list[Item]) -> str:
    data = state.load()
    lines = []
    if item.family:
        family = [i for i in items if i.family == item.family and i.key != item.key]
        if family:
            lines.append(f"Same family (**{item.family}**):")
            for i in family:
                st = state.entry(data, i)["status"]
                lines.append(f"- `{i.key}` -- {i.title} ({i.family_note or i.kind}; queue: {st})")
    # A module nearly every film imports (the basic geometry) says nothing
    # about kinship; only the rarer ones count.
    uses: dict[str, int] = {}
    for i in items:
        for m in i.number_modules:
            uses[m] = uses.get(m, 0) + 1
    mine = {m for m in item.number_modules if uses[m] <= max(3, len(items) // 6)}
    sharing = sorted((i for i in items if i.key != item.key and mine & set(i.number_modules)),
                     key=lambda i: -len(mine & set(i.number_modules)))
    if sharing:
        lines.append("\nOther films that read the same number modules -- their chapters may "
                     "already have solved a shot you need:")
        for i in sharing[:12]:
            common = ", ".join(sorted(mine & set(i.number_modules)))
            lines.append(f"- `{i.key}` -- {i.title} (shares {common})")
    if item.graph_nodes:
        lines.append("\nKnowledge-graph keywords this film covers (research/knowledge-graph.json):")
        lines.extend(f"- **{label}** (`{node}`) -- {summary}" for node, label, summary in item.graph_nodes)
    return "\n".join(lines) or "Nothing recorded."


def item_prompt(item: Item, items: list[Item] | None = None) -> str:
    from two_v_demo import cabin_world as cw
    from two_v_demo import score, shots

    items = items or load()
    originals = "\n".join(f"- `{o}`" for o in item.originals) or \
        "- (no rendered original found on disk -- the source file below is the film)"
    releases = "\n".join(f"- `{r}`" for r in item.releases) or "- (none)"
    numbers = "\n".join(f"- `{m}`" for m in item.number_modules) or \
        "- (none detected -- look for the figures in the source file; every figure must be computed)"
    first = item.originals[0] if item.originals else ""
    stem = Path(item.target_file).stem
    voice = []
    if item.voice_rate:
        voice.append(f"voice_rate `{item.voice_rate}`")
    if item.audio_bed:
        voice.append(f"audio_bed `{item.audio_bed}`")
    if item.style:
        voice.append(f"style `{item.style}`")
    parts = [
        f"# Cabin World re-render: {item.title}\n\n"
        f"Queue item `{item.key}` · generated {date.today().isoformat()} from the repository "
        f"at `{ROOT}`.\n\n"
        "This package is complete: it is everything you need to re-make one finished film. "
        "It is regenerated from the live code each time it is copied, so if this copy is "
        f"old, get a fresh one with `py -3.12 -m rerender prompt {item.key}` before starting.",

        "## 0. The two commands that make the film\n\n"
        "Once the new lesson module exists (sections 7 and 8), these are the whole "
        "rendering process. Run them from the repository folder, in a terminal:\n\n"
        "```bash\n"
        f"py -3.12 -m rerender stills {item.key}\n"
        f"py -3.12 -m rerender render {item.key}\n"
        "```\n\n"
        f"- `stills` writes one picture per chapter to `two_v_demo_output/{item.target_key}/` "
        "(add `--size 1080x1920` for the phone framing). Look at every one before rendering.\n"
        f"- `render` makes the finished film: `{item.target_file}`, its phone cut "
        f"`{Path(item.target_file).stem}-vertical.mp4` beside it, and the release folder in "
        "`deliverables/releases/`. It takes one to two hours and prints its progress; it "
        "never overwrites an existing file (a second render becomes `-v2`).",

        "## 1. The job\n\n"
        f"Re-create the film **{item.title}** with the **Cabin World** as its picture: "
        "the baseline scene at sunset -- the raw-wedge simulator's own 2V dome on its "
        "pad, the builder, the log with its end grain, the stump and the chainsaw, the "
        "member stack. Keep what the film *teaches* (its chapters, below) and every "
        "number it states; change how it *looks*. Where the original drew an abstract "
        "diagram, show the idea on the real objects in the world instead: the member in "
        "the stack, the seam on the dome, the wedge from the log.\n\n"
        "**The original is read-only.** Do not edit, re-render over, rename or delete "
        "any file listed under *Originals* or the original source module. You write new "
        "files only. The queue checks this: it recorded each original's size and date "
        "when the item was claimed, and refuses `done` if one changed.\n\n"
        + (f"**How this film fits the world:** {item.fit}\n\n" if item.fit else "")
        + (f"**Priority note:** this is {item.family_note}; it is superseded by "
           f"`{item.superseded_by}`. Check with the user before spending a render on it "
           "unless it was given to you on purpose.\n\n" if item.superseded_by else ""),

        "## 2. Take the item, and keep the queue current\n\n"
        "Every session and every model shares one queue, `rerender/queue.json`. Use the "
        "command line so two workers never collide (replace NAME with who you are, e.g. "
        "`claude-2026-09-28` or `gpt-session-3`):\n\n"
        "```bash\n"
        f"py -3.12 -m rerender claim {item.key} --by NAME\n"
        f"py -3.12 -m rerender note {item.key} \"what you did or found\" --by NAME\n"
        f"py -3.12 -m rerender status {item.key} rendering --by NAME\n"
        f"py -3.12 -m rerender status {item.key} review --by NAME --output {item.target_file}\n"
        "```\n\n"
        "If the claim is refused, someone else has it: stop and pick another item "
        "(`py -3.12 -m rerender next`). Leave a note whenever you stop, even mid-way, so "
        "the next session can continue. If you are blocked, note why and run "
        f"`py -3.12 -m rerender status {item.key} todo --by NAME`. Only the user marks an "
        "item `done`, after watching it.\n\n"
        "**Where this item stands now:** " + _history(item),

        "## 3. The house rules (CLAUDE.md, verbatim)\n\n" + _demote(_read("CLAUDE.md")),

        "## 4. The film to re-make\n\n"
        f"- **Title:** {item.title}\n- **Kind:** {item.kind}\n"
        f"- **Made by:** `{item.source}`\n"
        + (f"- **What it is:** {item.note}\n" if item.note else "")
        + (f"- **Voice and style of the original:** {', '.join(voice)}\n" if voice else "")
        + f"- **Chapters:** {len(item.chapters)}\n\n"
        "**Originals (read-only):**\n" + originals + "\n\n**Release folders of the original:**\n"
        + releases + "\n\n"
        + (f"To see the original, pull a frame from the middle of each chapter with ffmpeg, "
           f"e.g. `ffmpeg -ss 30 -i {first} -frames:v 1 check.png`, and read the image.\n\n"
           if first else "")
        + "### Chapters, in full\n\n"
        "This is the teaching content. You may tighten wording and re-order a little for "
        "the new pictures, but a fact, figure or caveat that is here must survive, and "
        "an unflattering number stays on screen.\n\n" + _chapters(item),

        "## 5. Where the numbers come from\n\n"
        "Every figure on screen must be computed by code (CLAUDE.md). The original read "
        "its figures from these modules -- import the same functions; never retype a "
        "number from the narration above:\n\n" + numbers + "\n\n"
        "Where the narration above contains a figure, find the function that produced it "
        "(search the source module for the f-string) and call that function. Scene "
        "dressing that is not a figure (a camera distance, a colour) may be typed.",

        "## 6. The Cabin World: the baseline you build on\n\n"
        "Read these files before writing anything:\n\n"
        "- `two_v_demo/cabin_world.py` -- the world: layers, landmarks, the painted sky, "
        "the offscreen studio, lettering. Its docstring shows both ways to use it.\n"
        f"- `{WORKED_EXAMPLE}` -- **the worked example: a complete two-chapter film set in "
        "the Cabin World, rendered through the standard exporter.** Copy its shape.\n"
        "- `wedge_book/cold_open.py` -- a standalone short (no narration) made with the "
        "studio and the score.\n"
        "- `wedge_book/cover_scene.py` -- how every object in the world is built "
        "(`wedge_prism`, `end_grain`, `chainsaw`, `props`, `builder`, `deck_batch`).\n"
        "- `two_v_demo/shots.py` -- camera moves; `two_v_demo/score.py` -- original music.\n"
        "- `two_v_demo/lessons.py` -- `Lesson` and `Chapter`; note the `backdrop` and "
        "`light` fields the Cabin World uses.\n"
        "- The original source module above, for its painters and figures.\n\n"
        "### cabin_world API\n\n" + _api(cw, [
            "paint", "landmarks", "layer", "missing_faces", "backdrop", "Studio",
            "letter", "lower_third", "subject_points"]) + "\n\n"
        f"Layers you can hide per scene with `paint(app, hide=...)`: {', '.join(cw.LAYERS)}.\n\n"
        "### Landmarks, as the scene places them today\n\nAim cameras and labels at these "
        "by name (`cw.landmarks().gap`), never by copying the numbers:\n\n" + _landmarks()
        + "\n\n### Camera moves (two_v_demo/shots.py)\n\n" + _api(shots, [
            "orbit", "crane_reveal", "push_in", "dolly_zoom", "low_hero", "fly_through",
            "top_down_spin", "hold", "by_chapter"])
        + "\n\n### Music (two_v_demo/score.py)\n\n" + _api(score, ["compose", "write_wav"])
        + "\n\nA narrated film uses the exporter's own audio. To put the Cabin World's "
        "music under narration, write a bed with `score.compose(seconds, bed=True)` to "
        "`assets/audio/beds/cabin-<name>.wav` and set `audio_bed=\"beds/cabin-<name>\"` on "
        "the lesson; the exporter ducks it under the voice.",

        "## 7. What to make, and where it goes\n\n"
        f"- **New lesson module:** `{item.target_module}` defining a `Lesson` with key "
        f"`{item.target_key}` (copy `{WORKED_EXAMPLE}`: `ground=\"off\"`, "
        "`backdrop=cw.backdrop`, `light=cw.LIGHT`, a `camera_fn`, painters that call "
        "`cw.paint(app)` and then add the chapter's own geometry and labels).\n"
        f"- **Register it:** import it in `two_v_demo/lesson_registry.py` and add it to "
        f"`LESSONS`; add a `Deliverable(\"{item.target_key}\", \"{Path(item.target_file).name}\", "
        "\"<one line>\", compose=True)` at the end of `DELIVERABLES` in "
        "`two_v_demo/deliverables.py`; add a `HASHTAG_BANK` entry under "
        f"`\"{item.target_key}\"` in `two_v_demo/release.py`.\n"
        f"- **Output:** `{item.target_file}` and its phone cut beside it (the exporter makes "
        "both), plus the release folder in `deliverables/releases/`. Never reuse an "
        "existing filename; the exporter versions it for you if one exists.\n"
        "- Keep the original's voice settings unless the user says otherwise.",

        "## 8. The procedure\n\n"
        "1. Claim the item (section 2). Read the original source module and the files in "
        "section 6. Pull a few frames of the original to see what each chapter showed.\n"
        "2. Plan each chapter: which landmark it is about, which camera move, which extra "
        "geometry (a highlighted member, an exploded wedge, a ghosted seam) goes on top of "
        "the world. Note the plan in the queue.\n"
        "3. Write the lesson module. Figures through the number modules; narration from "
        "section 4. Add a `selftest` that checks the figures and that every chapter has a "
        "painter and a camera.\n"
        "4. Run the selftest:\n\n"
        "```bash\n"
        f"py -3.12 -c \"from two_v_demo.lesson_registry import LESSONS as L; "
        f"L['{item.target_key}'].selftest()\"\n"
        "```\n\n"
        "5. **Stills before rendering -- one per chapter, and look at every one.** A render "
        "takes one to two hours; a wrong camera found afterwards costs all of it:\n\n"
        "```bash\n"
        f"py -3.12 -m rerender stills {item.key}\n"
        f"py -3.12 -m rerender stills {item.key} --size 1080x1920\n"
        "```\n\n"
        f"   The pictures land in `two_v_demo_output/{item.target_key}/`. Check: the subject "
        "is not hidden behind the teaching card (left ~28%) or the calculation panel "
        "(lower right); labels do not overlap; nothing sits inside the dome or below the "
        "ground; the camera is not inside a tree. Fix and re-shoot until every still is "
        "right.\n"
        "6. Set the status to `rendering`, then render. Both cuts and the release folder "
        "are made automatically:\n\n"
        "```bash\n"
        f"py -3.12 -m rerender render {item.key}\n"
        "```\n\n"
        "   Run it in the background; it prints progress. Narration is synthesised "
        "online, so run one render at a time. (Under the hood it writes an "
        "`export_video` ticket for `two_v_masterclass.py`, the same as the launcher's "
        "Masterclass page.)\n"
        f"7. Check the landscape cut, the `{stem}-vertical.mp4` phone cut and the release "
        "folder exist; pull a frame from three chapters of the finished file and look.\n"
        "8. Mark it for review with every output (section 2), and tell the user what was "
        "made, where, and anything you could not do.\n"
        "9. Do not commit or push unless the user asks you to.",

        "## 9. Definition of done\n\n"
        "- [ ] New lesson module, registered, deliverable and hashtags added\n"
        "- [ ] Every chapter of section 4 is present; no fact or caveat dropped\n"
        "- [ ] Every figure on screen comes from a function, none typed\n"
        "- [ ] Every chapter is set in the Cabin World and shows its idea on real objects\n"
        "- [ ] Selftest passes; one still per chapter looked at, landscape and phone\n"
        "- [ ] Landscape cut, phone cut and release folder on disk, under new names\n"
        "- [ ] Originals untouched; the queue item is at `review` with its outputs",

        "## 10. Related\n\n" + _related(item, items),

        "## 11. Environment\n\n"
        f"- Repository: `{ROOT}` (Windows; Python is `py -3.12`; ffmpeg is on PATH).\n"
        "- Rendering uses moderngl on the local GPU; the masterclass exporter opens a "
        "window while it works.\n"
        "- Narration uses the online neural voice through `two_v_demo/audio.py`; voice "
        "clips are cached next to the output, so a re-run does not re-synthesise.\n"
        "- If you are not running inside this repository (a model without file access), "
        "ask the user to run each command and paste back the output and the stills.",
    ]
    return SEPARATOR.join(p.strip() for p in parts) + "\n"


def queue_prompt(items: list[Item] | None = None) -> str:
    """For a session that should just take the next film and do it."""
    items = items or load()
    nxt = state.next_item(items)
    data = state.load()
    counts: dict[str, int] = {}
    for i in items:
        s = state.entry(data, i)["status"]
        counts[s] = counts.get(s, 0) + 1
    summary = ", ".join(f"{n} {s}" for s, n in sorted(counts.items()))
    head = (
        "# Work the Cabin World re-render queue\n\n"
        f"The repository at `{ROOT}` keeps a queue of every film it has rendered, to be "
        "re-made one at a time with the Cabin World as the picture. Right now: "
        f"{summary}.\n\n"
        "1. Run `py -3.12 -m rerender next` to see the next open item.\n"
        "2. Run `py -3.12 -m rerender prompt <key>` and follow that blueprint exactly -- it "
        "has the rules, the files, the chapters and the commands.\n"
        "3. When it is at `review`, stop and report; do not start a second film unless "
        "the user asks.\n")
    if nxt:
        head += f"\nThe next item is `{nxt.key}` ({nxt.title}); its blueprint follows."
        return head + SEPARATOR + item_prompt(nxt, items)
    return head + "\nThe queue is empty -- every item is claimed, in review, done or skipped."


def save(key: str, text: str) -> Path:
    PROMPTS.mkdir(parents=True, exist_ok=True)
    path = PROMPTS / f"{key}.md"
    path.write_text(text, encoding="utf-8")
    return path


def prompt_for(key: str) -> str:
    items = load()
    table = by_key(items)
    if key not in table:
        raise KeyError(f"no queue item {key!r}; `py -3.12 -m rerender list` shows them")
    return item_prompt(table[key], items)
