"""Storycraft: capture first, explain second -- as a planner for our films.

The films in this project explain well. What they do less often is make
somebody who did not come for an explanation stay for one. This module is
the craft half of the research engine:

* ``HOOKS`` -- the openings that earn the next thirty seconds, each tied to
  something this project can actually put on screen;
* ``SHOTS`` -- the camera grammar, each move implemented in
  :mod:`two_v_demo.shots` so a plan's shot list is renderable, not aspirational;
* ``ARCS`` -- story shapes for a long film and a vertical short;
* ``RETENTION`` -- the devices that carry a viewer through the explaining;
* :func:`plan` -- an episode plan for one keyword of the knowledge graph,
  using what :mod:`research.engine` found (the best phrase, the searches
  people make around it, the strongest video on it).

Every figure a plan puts in a title comes from the model's exported facts
(``web/server/src/generated/facts.json``, written by ``web/export_facts.py``).
The craft notes are guidance, not measured statistics, and say so.

    py -3.12 -m research.storycraft pinwheel-joint     # one plan
    py -3.12 -m research.storycraft --top 10           # the ten best-scoring
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FACTS = ROOT / "web" / "server" / "src" / "generated" / "facts.json"
OUT = HERE / "out" / "plans"


@dataclass(frozen=True)
class Hook:
    key: str
    name: str
    move: str          # what the first 3-8 seconds do
    line: str          # a first line, with {placeholders} filled from facts
    shot: str          # key into SHOTS
    why: str


HOOKS: dict[str, Hook] = {h.key: h for h in (
    Hook("result-first", "Show the ending first",
         "Open on the finished frame at golden hour, then cut to the bare log.",
         "This is {members} pieces of one kind of cut, and there is no hub anywhere in it.",
         "orbit-golden", "A viewer decides in seconds whether the payoff is worth waiting for; show it."),
    Hook("impossible-claim", "The claim that sounds wrong",
         "A single line over a still: a claim a sceptic wants to disprove.",
         "A dome frame from one tree, one chainsaw, and {frame_hours} hours of work.",
         "push-in-log", "Disbelief is attention. The film then earns the claim, number by number."),
    Hook("question", "The question you cannot un-ask",
         "Ask something the viewer never thought to ask, over the thing that answers it.",
         "Why does every dome kit sell you metal hubs -- and what happens if there are none?",
         "dolly-zoom-junction", "An open loop: the answer arrives at the reveal, not before."),
    Hook("mistake", "The mistake, confessed",
         "Start on the failure: the lumpy first dome, the gap you could put a thumb in.",
         "My first dome was so crooked I could fit my thumb in a joint. It is still standing.",
         "hold-frankendome", "Honesty reads as authority; the fix is the story."),
    Hook("number", "One number, then the proof",
         "Put a single computed figure on screen and hold it.",
         "{price}. That is the whole standard building, and I will show every line of it.",
         "hold-number", "A precise number promises a precise film. Round numbers promise marketing."),
    Hook("process", "The satisfying process",
         "Slow, tactile process with no talking: a log opening into wedges, a panel dropping in.",
         "",
         "crane-log-to-dome", "Pure process holds attention before any argument is made."),
    Hook("versus", "Head to head",
         "Two things side by side, same scale, one clear difference.",
         "Split the log: {wedge_vs_milled}x the usable wood of sawing it into boards.",
         "split-screen", "Comparison is the fastest explanation there is."),
    Hook("stakes", "Why it matters to a person",
         "A person, a reason, a deadline: whose life changes if this works.",
         "[Your words, not a script: why you are building this -- the Navy years, Japan, the G.I. Bill, the housing market.]",
         "low-hero", "Stakes give the geometry somebody to happen to."),
)}

SHOTS: dict[str, tuple[str, str]] = {
    # key: (how, implemented by)
    "orbit-golden": ("Slow 40-degree orbit of the finished frame, sun low behind it.",
                     "shots.orbit + wedge_book.cover_scene lighting"),
    "push-in-log": ("Push in on the log's end grain while the lens narrows; the split lines resolve.",
                    "shots.push_in"),
    "dolly-zoom-junction": ("Dolly zoom on one junction: the empty centre holds, the dome swells behind.",
                            "shots.dolly_zoom"),
    "hold-frankendome": ("Locked-off frame on the first dome, no music, a beat of silence.",
                         "shots.hold + lesson_franken scenes"),
    "hold-number": ("Locked frame, the number set large over a dimmed render.",
                    "shots.hold + the film overlay"),
    "crane-log-to-dome": ("Start on the log's end grain, rise and pull back to reveal the dome behind it.",
                          "shots.crane_reveal(look_start=log)"),
    "split-screen": ("Two renders, same camera, side by side.",
                     "two lessons rendered with one shots.orbit"),
    "low-hero": ("Low arc near the deck looking up at the builder and the crown gap.",
                 "shots.low_hero"),
    "time-lapse-build": ("The frame assembling bay by bay from the base ring up, locked camera.",
                         "jig/build stages + shots.hold"),
    "exploded-assemble": ("Panels flying in from exploded to closed while the camera orbits.",
                          "simulator panel_explode_in + shots.orbit"),
    "macro-seam": ("A slow slide along one seam: two wedges back to back, the key between.",
                   "shots.fly_through along a seam"),
    "top-plan": ("Straight down on the dome, turning: six stars appear.",
                 "shots.top_down_spin"),
}

ARCS = {
    "long": (
        ("0:00", "Hook", "One of HOOKS. No logo, no greeting, no 'in this video'."),
        ("0:10", "Promise", "Say what the viewer will be able to do or know by the end."),
        ("0:30", "Stakes", "Why it is hard, or why the usual way fails."),
        ("1:00", "Journey", "The work, in order, with one small payoff every minute."),
        ("mid", "Turn", "The mistake, the surprise, or the number that argues back."),
        ("late", "Reveal", "The hook's promise, delivered on screen."),
        ("end-1:00", "Explain", "Now the geometry and the numbers -- the viewer has reason to want them."),
        ("end", "Payoff + CTA", "One next step: the free book, the simulator, the network."),
    ),
    "short": (
        ("0-2s", "Hook", "Motion in the first frame. The claim or question on screen."),
        ("2-15s", "Show", "The process or the reveal, fast, no setup."),
        ("15-40s", "One idea", "A single explanation, one number, one image."),
        ("40-55s", "Loop", "End on a frame that cuts cleanly back to the first."),
    ),
}

RETENTION = (
    "Open a loop in the first ten seconds and close it late (the question hook).",
    "Change something on screen every few seconds in the hook: a cut, a move, a caption.",
    "Pattern-interrupt at each chapter: new location, new shot type, or Lumen.",
    "Title chapters as questions the viewer now has, not as topics.",
    "Put the unflattering number on screen: it buys trust for the flattering ones.",
    "Every explanation gets a picture first and the words second.",
)

TITLE_PATTERNS = (
    "I Built a {topic} From One Tree",
    "Why {topic} Changes Everything About Dome Building",
    "{topic}: What Nobody Tells You",
    "The {topic} Mistake That Almost Cost Me the Build",
    "{topic} in {frame_hours} Hours (With Every Number)",
    "{topic} vs. The Normal Way",
)

CATEGORY_HOOKS = {
    "geometry": ("question", "versus", "result-first"),
    "wedge": ("question", "process", "result-first"),
    "timber": ("process", "versus", "impossible-claim"),
    "envelope": ("mistake", "versus", "question"),
    "systems": ("question", "result-first", "number"),
    "site": ("stakes", "number", "question"),
    "modular": ("result-first", "stakes", "versus"),
    "economics": ("number", "impossible-claim", "mistake"),
    "structure": ("question", "mistake", "result-first"),
    "media": ("result-first", "process", "stakes"),
}


def facts() -> dict:
    data = json.loads(FACTS.read_text(encoding="utf-8"))
    return {
        "members": data["dome"]["members"],
        "price": f"${data['price']['stemCell']:,}",
        "wedge_vs_milled": data["wood"]["wedgeVsMilled"],
        # The week the book is named after, from the book's own clock.
        "frame_hours": int(_clock()["week"]),
    }


def _clock() -> dict:
    import sys
    sys.path.insert(0, str(ROOT))
    from wedge_book import systems
    return systems.build_clock()


def _research(node_id: str) -> dict:
    path = HERE / "out" / "graph-scores.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get(node_id, {})


def _completions(node: dict, limit: int = 12) -> list[str]:
    db = HERE / "research.sqlite3"
    if not db.exists():
        return []
    conn = sqlite3.connect(db)
    seen: dict[str, int] = {}
    for phrase in node["seeds"]:
        row = conn.execute("select suggestions from suggest where query=?", (phrase,)).fetchone()
        for rank, s in enumerate(json.loads(row[0]) if row else []):
            seen[s] = min(seen.get(s, 99), rank)
    return [s for s, _ in sorted(seen.items(), key=lambda kv: kv[1])][:limit]


def plan(node: dict) -> str:
    f = facts()
    r = _research(node["id"])
    hooks = [HOOKS[k] for k in CATEGORY_HOOKS.get(node["category"], ("result-first",))]
    topic = node["label"]
    lines = [f"# Episode plan: {topic}", "",
             f"*{node['summary']}*", ""]
    if r:
        lines += ["## What the research says", "",
                  f"- Best search phrase: **{r.get('phrase')}** (score {r.get('score')}, {r.get('basis')})",
                  f"- Demand: {r.get('demand')} distinct searches around it"]
        if r.get("views_per_day") is not None:
            lines.append(f"- Top results: {r['views_per_day']:,} median views a day; breakout rate {r['outlier_rate']}")
        if r.get("top_title"):
            lines.append(f"- Strongest video on it: \"{r['top_title']}\" ({r.get('top_channel', '')})")
        lines.append("")
    comps = _completions(node)
    if comps:
        lines += ["## What people type around it", "", *[f"- {c}" for c in comps], ""]
    lines += ["## Title options", ""]
    lines += [f"- {p.format(topic=topic.title(), **f)}" for p in TITLE_PATTERNS[:4]]
    lines += ["", "## Hooks (pick one; the first is the category's strongest)", ""]
    for h in hooks:
        first = h.line.format(**f) if h.line else "(no words -- let the process play)"
        how, impl = SHOTS[h.shot]
        lines += [f"### {h.name}", f"- **Open:** {h.move}", f"- **First line:** {first}",
                  f"- **Shot:** {how} *({impl})*", f"- *Why:* {h.why}", ""]
    lines += ["## Beat sheet (long film)", ""]
    lines += [f"- **{t} {name}** -- {what}" for t, name, what in ARCS["long"]]
    lines += ["", "## Vertical short", ""]
    lines += [f"- **{t} {name}** -- {what}" for t, name, what in ARCS["short"]]
    lines += ["", "## Retention, while explaining", "", *[f"- {x}" for x in RETENTION], ""]
    if node.get("files"):
        lines += ["## Where the material already is", "", *[f"- `{x}`" for x in node["files"]], ""]
    lines += ["*Craft notes are guidance, not measured statistics. Numbers in lines and titles "
              "come from the model's exported facts.*"]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("node", nargs="?", help="a keyword id from the graph")
    parser.add_argument("--top", type=int, default=0, help="plan the N best-scoring keywords")
    args = parser.parse_args(argv)
    graph = json.loads((HERE / "knowledge-graph.json").read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in graph["nodes"]}
    if args.top:
        scores = json.loads((HERE / "out" / "graph-scores.json").read_text(encoding="utf-8"))
        chosen = [k for k, _ in sorted(scores.items(), key=lambda kv: -kv[1]["score"])][:args.top]
    elif args.node:
        chosen = [args.node]
    else:
        parser.error("name a keyword id or pass --top N")
    OUT.mkdir(parents=True, exist_ok=True)
    for key in chosen:
        path = OUT / f"{key}.md"
        path.write_text(plan(nodes[key]), encoding="utf-8")
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
