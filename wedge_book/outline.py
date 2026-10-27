"""*The Wedge Method* -- the whole book, as a structure.

This is the second book on the engine that made *2 Trees*, and it is here
because the first attempt at this book was not a book. It was three hundred
and thirteen pages of correct, checkable, unreadable technical writing: every
number derived, every figure rendered, and nothing anybody would read for
pleasure or finish.

What *2 Trees* does that the first attempt did not:

* **it is somebody talking.** A chapter opens with a person and a problem,
  not with a definition;
* **it declares its strand.** Story, how-to, explain or reference -- printed
  in the chapter's eyebrow, so a reader in a hurry can take one track and
  skip the rest without feeling they are missing the book;
* **it is short per idea.** Nine hundred words and one thing. The first
  attempt had four thousand-word sections carrying six ideas each;
* **it uses a picture to make one point.** Not to decorate the page.

So this outline is built in that shape, on that engine, with this book's own
geometry, its own pictures and its own argument.

THE ARGUMENT, WHICH IS NEW

*2 Trees* opens Part 1 with: "A dome is a frame, a skin and a floor, and the
frame is the only part of it that has to be got right."

That is backwards, and this book says so in its first part. A dome resolves
its loads axially. Error and asymmetry in the frame do very little to whether
the shell stands up -- you have a lumpy skull and it opposes a baseball bat
exactly as well as a symmetrical one would. The frame is the part that is
*allowed* to be messy, and that permission is the whole reason a split log
can be a structural member.

What has to be right is the skin, because water is the silent killer, and the
floor, because everything you own sits on it. The happy part is that both are
the parts you can defer, upgrade and swap -- if the frame is built with that
in mind from the first panel.

WHAT LIVES WHERE

* this module -- structure, strands, figure placement, word targets;
* :mod:`wedge_book.numbers` -- every derived figure and the token namespace;
* :mod:`wedge_book.figures` and :mod:`wedge_book.plates` -- the pictures;
* :mod:`wedge_book.alternatives` -- the breadth tables;
* ``books/the-40-hour-cabin/manuscript/`` -- the prose, one Markdown file per chapter.
"""

from __future__ import annotations

from pathlib import Path

from two_v_demo.book import Book, Chapter, Figure, Matter, Page, Part

from . import store

ROOT = store.ROOT
MANUSCRIPT_DIR = store.BOOK_DIR / "manuscript"
FIGURE_DIR = store.BOOK_DIR / "figures"
EXPORT_DIR = ROOT / "deliverables" / "book"
STEM = "the-40-hour-cabin"

TITLE = "The 40 Hour Cabin"
SUBTITLE = "Complete Edition"
AUTHOR = "Donovan Zeanah"


# ----------------------------------------------------------------------
# Shorthand, so the outline below reads as an outline
# ----------------------------------------------------------------------

def _p(kind: str, title: str, purpose: str, words: int = 0,
       figures: tuple[Figure, ...] = (), beats: tuple[str, ...] = ()) -> Page:
    return Page(kind=kind, title=title, purpose=purpose, words=words,
                figures=figures, beats=beats)


def _f(key: str, caption: str, source: str = "prerendered",
       full_page: bool = False, note: str = "", **spec) -> Figure:
    """A picture already on disk in ``books/the-40-hour-cabin/figures``.

    Both of this book's picture sources render ahead of the export --
    :mod:`wedge_book.figures` operates the raw-wedge solver,
    :mod:`wedge_book.plates` takes frames out of the project's films -- so
    the outline names a key and the engine finds the newest file for it.
    """
    return Figure(key=key, caption=caption, source=source, spec=spec,
                  full_page=full_page, note=note)


# ----------------------------------------------------------------------
# PART 1 -- What actually has to be right
# ----------------------------------------------------------------------

CH_LUMPY = Chapter(
    number=1, ref="lumpy", strand="story",
    title="Your Skull Is Not Symmetrical Either",
    deck="The frame is the part you are allowed to get wrong, and almost "
         "every dome book has this backwards",
    derives=("wedge_book.numbers.quantities",),
    pages=(
        _p("opener", "Your skull is not symmetrical either",
           "Open the book on its one contentious claim, in the author's "
           "voice, before any geometry.", words=420,
           figures=(_f("standard-dome",
                       "The reference build. Nothing about it is as "
                       "accurate as it looks."),),
           beats=("a dome resolves load axially",
                  "asymmetry in the frame is absorbed, not amplified",
                  "the lumpy skull still stops the bat",
                  "so the frame is where the tolerance lives")),
        _p("text", "What the frame is actually doing",
           "Why a triangulated shell forgives a stick that is out.",
           words=520,
           beats=("every member is mostly in compression along its axis",
                  "a triangle out by a degree is still a triangle",
                  "the error goes into the seam, and the seam has a key in "
                  "it that was going to be there anyway")),
        _p("text", "What this buys you",
           "The permission that makes the whole method possible.",
           words=380,
           beats=("you can use a split log",
                  "you can cut on a bench in a field",
                  "you do not need a mill, a planer or a shed")),
    ))

CH_SILENT_KILLER = Chapter(
    number=2, ref="skin", strand="explain",
    title="Water Is the Silent Killer",
    deck="The skin is the part that has to be right, and it is the part "
         "every dome book treats as a finish",
    derives=("soft_shell.soft_shell", "wedge_book.numbers.money"),
    pages=(
        _p("opener", "Water is the silent killer",
           "State the real hierarchy: skin first, floor second, frame last.",
           words=440,
           figures=(_f("plate-shower-cap",
                       "One watertight layer over everything else."),),
           beats=("a frame that is out by an inch stands for fifty years",
                  "a skin that leaks for one winter takes the frame with it",
                  "rot is silent and is found late")),
        _p("text", "Why domes leak where they do",
           "Seams, penetrations and the apex -- in that order.", words=520,
           figures=(_f("keys-everywhere",
                       "Every seam in the dome, and the key in each one."),),
           beats=("55 interior seams is 309 feet of joint",
                  "every joint is a chance",
                  "one continuous outer layer removes the whole category")),
        _p("text", "And the floor",
           "The second thing to get right, and why.", words=420,
           beats=("everything you own sits on it",
                  "it is the one surface you touch all day",
                  "it is also where the ground sends its water")),
    ))

CH_HOTSWAP = Chapter(
    number=3, ref="hotswap", strand="explain",
    title="Build It So You Can Change Your Mind",
    deck="The skin and the floor are the two things that matter and the two "
         "things you can defer -- if the frame is built for it",
    derives=("seed_model.quote", "wedge_book.numbers.money"),
    pages=(
        _p("opener", "Build it so you can change your mind",
           "The resolution of the argument: what matters most is also what "
           "is most swappable.", words=460,
           figures=(_f("plate-swap-everything",
                       "New insulation? Swap it. Solar? Add it."),),
           beats=("threaded inserts in the wedge faces, from the first panel",
                  "a cap that straps rather than fastens",
                  "a floor that clamps rather than is built in",
                  "none of these cost anything at the time")),
        _p("steps", "The four features that make it swappable",
           "The specific things to do while building that buy the option.",
           words=520,
           beats=("inserts not screws into end grain",
                  "the cap sized a layer bigger than it needs",
                  "the floor on a hub and spokes, not joists into the ring",
                  "services in the seam channel, not in the wall")),
        _p("text", "What deferring actually costs",
           "The honest figure, against building it all at once.", words=380),
    ))

CH_PARTS_LIST = Chapter(
    number=4, ref="parts_list", strand="explain",
    title="A House With a Parts List",
    deck="Count the model, and a building stops being a price opinion: the "
         "cut list makes itself, and the labour is a flat rate",
    derives=("wedge_book.numbers.quantities", "seed_world.geometry",
             "seed_model.FITOUT_ORDER"),
    pages=(
        _p("opener", "The whole argument, start to finish",
           "What the rest of the book proves, said once.", words=320,
           figures=(_f("plate-whole-argument",
                       "Everything this project knows, in one film."),)),
        _p("text", "Nothing here is typed in",
           "The model counts itself.", words=380,
           figures=(_f("plate-model-counts-itself",
                       "The panel on the right is counting the dome behind it."),)),
        _p("worked", "The cut list makes itself",
           "One radius in, a timber order out.", words=420,
           figures=(_f("plate-cut-list",
                       "Pick the radius; the cut list and the order fall out."),)),
        _p("worked", "The flat rate, proved",
           "Nine times the house, the same parts list.", words=400,
           figures=(_f("plate-flat-rate",
                       "Scale the dome and count what changes."),)),
        _p("text", "One skeleton, four buildings",
           "Home, shed, greenhouse, shelter.", words=260,
           figures=(_f("plate-four-lines",
                       "Four buildings, one skeleton."),)),
    ))

CH_UGLY = Chapter(
    number=5, ref="ugly", strand="story",
    title="Why I Built the Ugly One",
    deck="The beautiful maths needed an ugly test: salvage, a folded bracket, "
         "and nothing landing where it should",
    derives=("wedge_book.numbers.quantities",),
    pages=(
        _p("opener", "Why I built the ugly one",
           "Precision against tolerance, and why the difference is the whole "
           "experiment.", words=480,
           figures=(_f("plate-ugly-one",
                       "Take whatever the chainsaw made, and see what the "
                       "geometry forgives."),)),
        _p("text", "Build one. Then build the next one faster.",
           "The argument, closed.", words=320,
           figures=(_f("plate-build-the-next",
                       "The geometry does not check your credit."),)),
    ))

PART_RIGHT = Part(
    number=1, title="What Actually Has to Be Right",
    epigraph="A dome is a frame, a skin and a floor -- and the frame is the "
             "part you are allowed to get wrong.",
    promise="Three chapters that invert the usual advice, and one practical "
            "consequence: build the frame loose and the two layers that "
            "matter stay changeable for the life of the building.",
    chapters=(CH_LUMPY, CH_SILENT_KILLER, CH_HOTSWAP, CH_PARTS_LIST, CH_UGLY))


# ----------------------------------------------------------------------
# PART 2 -- The stick
# ----------------------------------------------------------------------

CH_TREE = Chapter(
    number=12, ref="tree", strand="story",
    title="The Woodpile Is Standing Up",
    deck="What one tree holds, how it comes down, and why the trees decide the "
         "size of the building rather than the other way round",
    derives=("two_v_demo.wedge_facts.steps_trunk", "two_v_demo.wedge_why_facts.steps_yield",
             "two_v_demo.wedge_facts.steps_dome"),
    pages=(
        _p("opener", "The woodpile is standing up",
           "A house frame, before it is cut.", words=360,
           figures=(_f("plate-one-log", "A whole house frame, before it is cut."),)),
        _p("worked", "What is standing there", "One tree, measured.", words=300),
        _p("steps", "The fell line", "The hinge steers the tree.", words=360,
           figures=(_f("plate-fell-line", "The hinge steers the tree."),)),
        _p("text", "All at once", "Every section splits the same way.", words=320),
        _p("worked", "The trees size the building", "Solved backwards from the stick.",
           words=420,
           figures=(_f("plate-two-trees-dome", "The dome two trees make."),)),
    ))

CH_SAW = Chapter(
    number=14, ref="saw", strand="explain",
    title="What the Saw Actually Does",
    deck="Two timed sittings, the fuel written down, a prediction the geometry "
         "makes without being told -- and the cuts counted both ways",
    derives=("two_v_demo.wedge_why_facts.steps_rate", "two_v_demo.book_math.ripping_fuel",
             "two_v_demo.wedge_facts.steps_actions"),
    pages=(
        _p("opener", "What the saw actually does", "Measured, and guessed.", words=300),
        _p("worked", "Two sessions, and do they agree?", "The rate, cross-checked.",
           words=420,
           figures=(_f("plate-saw-sessions", "Two sittings, timed."),)),
        _p("text", "What the harvest took", "Days and fuel.", words=300),
        _p("worked", "Counting the cuts", "Least actions, most building.", words=360,
           figures=(_f("plate-counting-cuts", "One tree to a finished member, "
                                                "counted both ways."),)),
    ))

CH_LINSEED = Chapter(
    number=19, ref="linseed", strand="howto",
    title="Linseed Oil, Where It Belongs",
    deck="Read the can, set up the rag station, oil the faces people touch, and "
         "do not ask a finish to be a roof, a seal or a repair",
    derives=("two_v_demo.linseed_oil.facts",),
    pages=(
        _p("opener", "Linseed oil, where it belongs",
           "Twenty tricks from one video, sorted by what survives in a dome.",
           words=320),
        _p("safety", "The rag station comes first", "Oxidation makes heat.", words=220),
        _p("steps", "Read the can, prepare, apply", "The product, the member, the coat.",
           words=520,
           figures=(_f("plate-thin-coat", "Apply thinly, then wipe dry."),)),
        _p("worked", "How much, and how long", "Measured wood, declared inputs.",
           words=420),
        _p("text", "Where it does not belong", "Seams, weather, glazing.", words=420,
           figures=(_f("plate-oil-seam", "Finish decisions follow the assembly."),)),
        _p("text", "The parts people touch, and keeping them",
           "Interior, tools, maintenance.", words=360),
    ))

CH_SPLIT = Chapter(
    number=13, ref="split", strand="story",
    title="Stop Squaring. Start Splitting.",
    deck="A round log is already rotationally symmetric, and three splits "
         "give you eight identical sticks nobody had to measure",
    derives=("two_v_demo.wedge_geometry.build_plan",),
    pages=(
        _p("opener", "Stop squaring. Start splitting.",
           "The central move of the method, told as what happened.",
           words=480,
           figures=(_f("plate-stop-squaring",
                       "The same log, opened a different way."),),
           beats=("half, half, half again",
                  "the tolerance was held by the tree, not by you",
                  "a mill wants rectangles; a wedge takes the log as it is")),
        _p("spread", "What a mill throws away",
           "The recovery argument, with the figure that does not flatter it.",
           words=420,
           figures=(_f("plate-round-log-corners",
                       "The corners of a round log are not bad wood. They "
                       "are wood of the wrong shape."),)),
    ))

CH_MEMBER = Chapter(
    number=15, ref="member", strand="explain",
    title="One Eighth of a Tree, Used as a Stick",
    deck="What a 45-degree sector actually is, and why its shape is an "
         "advantage rather than something to apologise for",
    derives=("wedge_book.numbers.quantities", "seed_world.geometry"),
    pages=(
        _p("opener", "One eighth of a tree, used as a stick",
           "The member, measured.", words=460,
           figures=(_f("wedge-cross-section",
                       "The end of a member: two sawn faces and a bark "
                       "face, and nothing machined."),)),
        _p("text", "Which way the point faces",
           "The first irreversible decision, and the four ways to make it.",
           words=480,
           figures=(_f("wedge-orientation-point-dome-in",
                       "Point inward: the reference build."),)),
        _p("table", "All four orientations",
           "The gamut, so the choice is visible rather than assumed.",
           words=260,
           figures=(_f("wedge-orientation-point-panel-in",
                       "Points apart, each into its own triangle."),
                    _f("wedge-orientation-point-dome-out",
                       "Both points outward, at the sky."),
                    _f("wedge-orientation-point-panel-out",
                       "Points toward each other, across the seam."))),
    ))

CH_TWO_LENGTHS = Chapter(
    number=16, ref="two_lengths", strand="howto",
    title="Two Lengths, and Neither Is the Chord",
    deck="72.000 and 63.670 inches are what the geometry says; what you cut "
         "is those minus a bite that does not scale",
    derives=("wedge_book.numbers.strut_table",
             "wedge_book.numbers.reference_designs"),
    pages=(
        _p("opener", "Two lengths, and neither is the chord",
           "The single most useful page in the book for somebody cutting.",
           words=440,
           beats=("the chord is what every geodesic reference publishes",
                  "the cut is the chord minus the pinwheel's bite",
                  "the bite is set by the member's width, not the dome's "
                  "size")),
        _p("table", "The cut list at every size",
           "The table a builder comes back to.", words=220),
        _p("errata", "The mistake this table made",
           "Name the scaled-bite error before the reader trusts the table.",
           words=280),
    ))

CH_GREEN = Chapter(
    number=17, ref="green", strand="explain",
    title="Green Wood Moves, and a Split Moves Least",
    deck="A wedge closes its own angle as it dries -- which is why it checks "
         "less than a squared timber, and why the key is cut last",
    derives=("two_v_demo.wood_care.sector_after_drying",
             "two_v_demo.seam_climate.C"),
    pages=(
        _p("opener", "Green wood moves, and a split moves least",
           "What drying does to a 45-degree sector, told from the seam.",
           words=460,
           figures=(_f("plate-the-vee",
                       "Two sawn faces meeting at the ridge and opening to "
                       "the room: the V the key fills."),),
           beats=("wood shrinks twice as much round the rings as across them",
                  "so a sector's angle closes as it dries",
                  "a boxed heart cannot close, so it tears: that is a check",
                  "a wedge was split along the rings' own radius, and "
                  "closes instead")),
        _p("text", "What the key sees",
           "The dried V against the green one, and the rule that follows.",
           words=440,
           beats=("the V opens by exactly what each wedge closes",
                  "the width at the room side barely changes; the faces tilt",
                  "a key cut to the green V bears on one edge",
                  "so print or cut the keys after the frame has dried")),
        _p("text", "How long, and how much water",
           "Drying time by thickness, and what the frame gives up.",
           words=380,
           beats=("drying time goes with the square of thickness",
                  "a wedge's thickest point is its inscribed circle",
                  "thirteen times quicker than the log it came from",
                  "and still slower than a two-by")),
        _p("steps", "Drying the stack",
           "Stickers, cover, airflow, end grain, and the meter.", words=360),
    ))

CH_FINISH = Chapter(
    number=18, ref="finish", strand="howto",
    title="Char the Outside, Oil It, and Leave the Faces Bare",
    deck="Yakisugi and linseed on the round face only, because the two sawn "
         "faces carry the key, the bolts and the seam's air",
    derives=("two_v_demo.wood_care.finish",),
    pages=(
        _p("opener", "Char the outside, oil it, and leave the faces bare",
           "Which faces get a finish, and why only one of the three does.",
           words=420,
           figures=(_f("plate-bark-face",
                       "Round face out, point in: the only face the weather "
                       "ever sees."),),
           beats=("the bark face is the only one exposed",
                  "the sawn faces are a joint, not a surface",
                  "a finish in the seam traps moisture the channel is there "
                  "to move")),
        _p("steps", "Charring the round face",
           "Yakisugi on a wedge: the torch, the depth, the brush, and what "
           "the char costs the section.", words=460),
        _p("steps", "Oiling it",
           "Raw against boiled linseed, thin coats, and how much the frame "
           "takes.", words=400),
        _p("safety", "Oily rags catch fire on their own",
           "The one warning in this chapter that is not about the wood.",
           words=200),
    ))

PART_STICK = Part(
    number=3, title="The Stick",
    epigraph="Every radius of a round log is the same as every other. "
             "That is the whole trick, and the tree held the tolerance.",
    promise="How a standing tree becomes 120 structural members, what a "
            "45-degree sector is, the two lengths you actually cut, what "
            "drying does to them, and the one face that gets a finish.",
    chapters=(CH_TREE, CH_SPLIT, CH_SAW, CH_MEMBER, CH_TWO_LENGTHS, CH_GREEN, CH_FINISH, CH_LINSEED))


# ----------------------------------------------------------------------
# PART 3 -- The panel
# ----------------------------------------------------------------------

CH_PINWHEEL = Chapter(
    number=20, ref="pinwheel", strand="explain",
    title="Nothing Meets at the Corner",
    deck="Three sticks, each butting into the side of the next, and not one "
         "of them reaching the vertex it is named after",
    derives=("wedge_book.numbers.quantities",),
    pages=(
        _p("opener", "Nothing meets at the corner",
           "The joint, and why it removes the hub.", words=470,
           figures=(_f("vertex-five",
                       "Five triangles meeting, and an empty corner."),)),
        _p("spread", "One seam, two members",
           "Replace the schematic with the solved cross-section.",
           words=420,
           figures=(_f("seam-section",
                       "A seam in cross-section, at the angle the solver "
                       "puts it: two sectors, the key between them, drawn "
                       "to the solved dihedral.",
                       note="This replaces the panel-A-plus-key-plus-panel-B "
                            "schematic, which drew two curved blobs and a "
                            "flat bar and showed neither the angle nor the "
                            "shape of the key."),)),
        _p("text", "The price of a panel being a thing",
           "120 members for 65 edges, and what the duplication buys.",
           words=400),
    ))

CH_FRAMES = Chapter(
    number=21, ref="frames", strand="explain",
    title="Forty Frames, Lifted Whole",
    deck="Each triangle is finished before it meets its neighbours -- which "
         "makes a panel a module you can swap, and the air a place nobody works",
    derives=("two_v_demo.wedge_why_facts.orientation_features",),
    pages=(
        _p("opener", "Forty frames, lifted whole", "The shell is not built stick by stick.",
           words=360,
           figures=(_f("plate-forty-frames", "Forty frames, built flat, lifted whole."),)),
        _p("text", "A panel that cannot fall through", "The keystone lip.", words=360,
           figures=(_f("plate-keystone", "The opening tapers; the panel seats."),)),
        _p("text", "Four rotations, four buildings", "What turning the wedge does to "
           "the building.", words=320),
        _p("text", "What holds it together", "Glue, screws, and bolts through the keys.",
           words=320),
    ))

CH_BODY = Chapter(
    number=23, ref="body", strand="explain",
    title="What the Work Costs the Body",
    deck="Follow two people through every motion of a factory-built dome: the "
         "parts that look like effort are cheap, and holding still is the bill",
    derives=("two_v_demo.energetics.build_energy",),
    pages=(
        _p("opener", "What the work costs the body", "A line, and the people on it.",
           words=360,
           figures=(_f("plate-six-motions", "Walk, lift, carry, position, fasten, recover."),)),
        _p("text", "Six motions", "And the one that is not linear.", words=420),
        _p("text", "The body is the heaviest thing you lift", "Limbs, teams, overhead.",
           words=380,
           figures=(_f("plate-trunk-work", "The trunk does most of the lifting."),)),
        _p("worked", "Exact, and modelled", "Work against food.", words=360),
        _p("table", "The ledger", "By motion, by station, by shift, in food.", words=360),
    ))

CH_RECTANGLES = Chapter(
    number=25, ref="rectangles", strand="howto",
    title="If Your Sticks Are Rectangles",
    deck="The same hubless dome from milled stock: two angles on every end, two "
         "machines, six saw settings, and a sled for the angles no saw reaches",
    derives=("two_v_demo.sawing.cut_plans",),
    pages=(
        _p("opener", "If your sticks are rectangles", "The compound cut, both machines.",
           words=380,
           figures=(_f("plate-compound-cut", "Two angles, one pass, every end."),)),
        _p("table", "Every setting the dome needs", "Six setups, and none on the scale.",
           words=360),
        _p("steps", "The sequence", "Eleven steps, in order.", words=620,
           figures=(_f("plate-the-sled", "The crosscut sled, fenced to the complement."),)),
        _p("steps", "Proving it", "The offcut pair and the five-cut test.", words=320,
           figures=(_f("plate-five-cut", "An invisible error, made measurable."),)),
        _p("text", "The five ways it goes wrong", "All of them look right until assembly.",
           words=260),
    ))

CH_NINE = Chapter(
    number=22, ref="nine", strand="explain",
    title="Nine Processes, Whatever Size You Build",
    deck="Nine operations turn standing timber into a shell. Not nine "
         "categories with sub-steps hiding inside them -- nine setups",
    derives=("two_v_demo.franken_economics.PROCESSES",),
    pages=(
        _p("opener", "Nine processes, whatever size you build",
           "The crux of the book: the verb list is shorter than the parts "
           "list, and it does not grow.", words=520,
           beats=("fell, rip, crosscut, fold, drill, screw, raise, sheathe, "
                  "glass",
                  "each is a distinct setup with its own tool and its own "
                  "way of going wrong",
                  "parts are things you buy; processes are things you get "
                  "better at",
                  "a list this short is a list you can attack")),
        _p("steps", "The nine, in the order they happen",
           "Each named, with its tool, its bench and its failure mode.",
           words=760),
        _p("text", "Why the list does not grow with the house",
           "The scaling argument that follows from a short verb list.",
           words=380),
    ))

CH_JIG = Chapter(
    number=24, ref="jig", strand="howto",
    title="One Flat Board, Forty Identical Panels",
    deck="The only thing in the whole build that has to be true is the "
         "bench, and everything else is measured from it",
    derives=("wedge_book.figures.catalogue",),
    pages=(
        _p("opener", "One flat board, forty identical panels",
           "The fixture, and the promise it makes.", words=420,
           figures=(_f("jig-01-bench",
                       "One flat sheet on sawhorses, and nothing else."),)),
        _p("steps", "Building the jig", "Five steps to the fixture.",
           words=620,
           figures=(_f("jig-02-triangle",
                       "The panel's triangle, struck once from the "
                       "solution and never measured again."),
                    _f("jig-03-rails",
                       "Three cleats, one per member, each parallel to that "
                       "member's point-axis."),
                    _f("jig-04-fences",
                       "Red to red, green to green, or the stick does not "
                       "seat."),
                    _f("jig-05-guides",
                       "The magenta plate is the flush-cut fence; the cyan "
                       "is the face the next butt lands on."))),
        _p("steps", "Making one panel",
           "The six steps from stick to finished triangle.", words=680,
           figures=(_f("jig-06-buttcut",
                       "The one cut made before assembly, and the only one "
                       "that can be batched."),
                    _f("jig-08-member2",
                       "End to side: a flat sawn face on a flat sawn face."),
                    _f("jig-09-member3",
                       "The last stick is captured at both ends, which is "
                       "why the head is left long."),
                    _f("jig-11-flush",
                       "The head is never measured. It is cut in place."))),
        _p("text", "Why the head end is left long",
           "Where error is allowed to leave the building.", words=420,
           figures=(_f("heads-uncut",
                       "Uncut, every head trespasses across the vertex."),
                    _f("heads-cut", "And after."))),
    ))

CH_OPENINGS = Chapter(
    number=26, ref="openings", strand="howto",
    title="Doors, Windows, and What Not to Cut",
    deck="An opening is a panel you did not close -- which is why it costs "
         "nothing, and why cutting one afterwards costs everything",
    derives=("wedge_book.numbers.quantities",),
    pages=(
        _p("opener", "Doors, windows, and what not to cut",
           "The cheapest way to put a hole in a dome, and the expensive "
           "way people reach for first.", words=520,
           figures=(_f("plate-openings",
                       "Take whole panels. Cutting a strut means replacing "
                       "a load path."),),
           beats=("openings take whole panels",
                  "cut a strut and you have to replace what it was doing",
                  "a panel left out is free; a panel cut into is a header",
                  "decide late, because the shell tells you where the "
                  "light is")),
        _p("steps", "Putting a door in", "The sequence, and the frame.",
           words=520),
        _p("text", "Windows, and why they go high",
           "Where glazing earns its place in a leaning wall.", words=440),
        _p("text", "The same problem on a different geometry",
           "A zome's answer, which is the same answer.", words=320,
           figures=(_f("plate-openings-zome",
                       "Take out a whole panel and no strut needs "
                       "cutting."),)),
    ))


CH_COVERAGE = Chapter(
    number=27, ref="coverage", strand="explain",
    title="How Much Tree Closes a Dome",
      deck="Separate frame blanks from infill, count both wedges, and measure continuous "
           "coverage: a conditional stock budget from the owner's paired-wedge idea",
      derives=("infill.methodology", "two_v_demo.wedge_coverage_facts"),
    pages=(
        _p("opener", "How much tree closes a dome", "The frame is not the whole of the wood.", words=220),
        _p("worked", "The frame", "Members, nominal and as cut.", words=320),
        _p("text", "The faces", "What is left to close.", words=260),
        _p("table", "Pairs, points in", "The overlap as a dial.", words=520),
        _p("text", "What the overlap is for", "Solid wood or a cavity.", words=220),
    ))

PART_PANEL = Part(
    number=4, title="The Panel",
    epigraph="Forty panels come off one board, and nothing on the board is "
             "adjusted between them. Panel forty is panel one.",
    promise="The joint that removes the hub, the nine processes that make "
            "the whole shop, the one fixture that makes forty panels the "
            "same, and where the door goes.",
    chapters=(CH_PINWHEEL, CH_FRAMES, CH_NINE, CH_BODY, CH_JIG, CH_RECTANGLES, CH_OPENINGS, CH_COVERAGE))


# ----------------------------------------------------------------------
# PART 4 -- The skin, which is the part that matters
# ----------------------------------------------------------------------

CH_RAISE = Chapter(
    number=28, ref="raise", strand="howto",
    title="Raising It",
    deck="Twenty panels round the ring, fifteen above them, and five around the "
         "apex -- in that order, and braced until the second course closes",
    pages=(
        _p("opener", "Raising it", "The fortnight's last three days.",
           words=420,
           figures=(_f("course-first", "The ten panels that stand on the "
                                       "ring."),)),
        _p("steps", "The raising sequence", "Numbered, at the site.",
           words=640,
           figures=(_f("course-second",
                       "The band above: where the dome starts holding its "
                       "own shape."),
                    _f("course-apex", "Closing the top."))),
    ))

CH_ONE_LAYER = Chapter(
    number=29, ref="one_layer", strand="explain",
    title="One Watertight Layer, and Only One",
    deck="Two impermeable skins with insulation between them is a trap, and "
         "this project shipped that design before it noticed",
    derives=("soft_shell.soft_shell", "soft_shell.compare"),
    corrects="The shell used to carry a waterproof membrane under the "
             "panels as well as a cap over them.",
    pages=(
        _p("opener", "One watertight layer, and only one",
           "The shower cap, and the physics behind the analogy.",
           words=500,
           figures=(_f("with-skin", "The frame with its skin on."),)),
        _p("errata", "What this book used to say",
           "Name the two-membrane design and why it was wrong.", words=320),
        _p("text", "The breather has to actually breathe",
           "Perms, the vented gap, and where the water goes.", words=460),
        _p("table", "Every other way to skin it",
           "Four laminates and the cap, priced on this dome.", words=240),
    ))

CH_HATS = Chapter(
    number=31, ref="hats", strand="explain",
    title="A Dome Is a Head, and It Wears Hats",
    deck="Bare skin, then layers, then one rain-slick shell over the lot -- "
         "the way you dress for the Arctic, and for the same reasons",
    derives=("soft_shell.hat_sizes", "quilt_network.dome_totals"),
    pages=(
        _p("opener", "A dome is a head, and it wears hats",
           "The layering model, in the author's own words.", words=520,
           figures=(_f("plate-quilt",
                       "A quilt, and a bigger cap for each one."),)),
        _p("text", "Each hat is a size up",
           "Why the arithmetic of layering is not one number.", words=400),
        _p("text", "It gets warmer every winter",
           "The upgrade path, and what a layer is worth.", words=420,
           figures=(_f("plate-layering",
                       "The envelope gaining a layer a winter."),)),
    ))

CH_SEAM_MODULE = Chapter(
    number=30, ref="seam_module", strand="explain",
    title="The Seam Does Four Jobs",
    deck="Gutter, vent, dehumidifier and air barrier -- all of it in the "
         "space two sawn faces were always going to leave",
    derives=("wedge_book.systems.seam_module",
             "wedge_book.systems.water_comparison"),
    pages=(
        _p("opener", "The seam does four jobs",
           "The channel, fitted out.", words=520,
           figures=(_f("keys-everywhere",
                       "Every seam in the dome, and the channel in each "
                       "one."),),
           beats=("the channel exists whether or not anybody uses it",
                  "rain in at the ridge, water out at the bottom",
                  "air along the wood faces, which is what dries timber",
                  "a desiccant leg for when the air will not do it",
                  "and a plate that condenses on purpose")),
        _p("text", "The air barrier",
           "Positive pressure, and why a leak stops being a leak.",
           words=520),
        _p("text", "Condensing on purpose",
           "The thermoelectric plates, and the number that decides how "
           "seriously to take them.", words=560),
        _p("table", "What the module costs", "Line by line.", words=320),
    ))

CH_BOM = Chapter(
    number=87, ref="bom", strand="reference",
    title="Every Part, Priced",
    deck="The column, the pad, the hardware, the power bench and the water "
         "bench -- the whole bill, with a source on every line",
    derives=("wedge_book.systems.bills",),
    pages=(
        _p("opener", "Every part, priced",
           "How to read the bills and what is deliberately separate.",
           words=420),
        _p("table", "The utility column", "Including the steel.",
           words=260),
        _p("table", "Power and water", "The two benches.", words=300),
        _p("table", "Hardware and pad", "Stainless, and the host's bill.",
           words=280),
    ))


PART_SKIN = Part(
    number=5, title="The Skin",
    epigraph="A frame that is out by an inch stands for fifty years. A skin "
             "that leaks for one winter takes the frame with it.",
    promise="Raising the shell, the single watertight layer over it, and the "
            "hats that go on afterwards -- the part of the building this "
            "book says matters most.",
    chapters=(CH_RAISE, CH_ONE_LAYER, CH_SEAM_MODULE, CH_HATS))


# ----------------------------------------------------------------------
# PART -- The seam at work: air, water and what the channel is made of
# ----------------------------------------------------------------------

CH_CHANNEL = Chapter(
    number=32, ref="channel", strand="reference",
    title="What Fits in the Channel",
    deck="Water and wire, yes. A round duct, no -- and the channel does not "
         "need one, because it already is one",
    derives=("two_v_demo.channel_facts.room", "two_v_demo.channel_facts.fits",
             "two_v_demo.channel_facts.spacer_for",
             "two_v_demo.channel_facts.printing"),
    pages=(
        _p("opener", "What fits in the channel",
           "The room inside one key, and the budget it sets.", words=380,
           figures=(_f("plate-bundle-fits",
                       "A water line, a circuit, the plates' pair and the "
                       "drain, in the tighter of the two seams."),)),
        _p("table", "The sizes this chapter assumed",
           "Nominal where a standard exists, estimates where it does not.",
           words=220),
        _p("table", "What fits, item by item",
           "Every service against both seams.", words=260,
           figures=(_f("plate-no-duct",
                       "The smallest ordinary duct, against the V it would "
                       "have to go in."),)),
        _p("text", "The channel is the duct",
           "The air the dome needs, and the seams that carry it.", words=320),
        _p("text", "If you want a duct anyway: the key becomes a spacer",
           "Moving every panel out, and what the dome grows by.", words=380,
           figures=(_f("plate-spacer",
                       "As built, and with the seams opened for a four-inch "
                       "duct."),)),
        _p("steps", "Printing the key in halves",
           "Two profiles, a half on every member, and what it costs.",
           words=380,
           figures=(_f("plate-half-keys",
                       "Each member carries its own half of the key."),)),
        _p("text", "Where the channels meet",
           "The frame has no hubs; the services do.", words=300,
           figures=(_f("plate-rosettes",
                       "A printed rosette inside a five-way and a six-way "
                       "vertex."),)),
    ))

CH_DEWPOINT = Chapter(
    number=33, ref="dewpoint", strand="explain",
    title="Compare Dew Points, Not Humidity",
    deck="Three questions decide every move the seam's air makes, and none of "
         "them is about relative humidity",
    derives=("two_v_demo.seam_climate.decide",
             "two_v_demo.seam_climate.SCENARIOS"),
    pages=(
        _p("opener", "Compare dew points, not humidity",
           "The one rule, with the example that makes it obvious.", words=460,
           figures=(_f("plate-dew-point",
                       "Two airs, and the only number that says which one is "
                       "drier."),)),
        _p("text", "The three questions",
           "Which air is drier; will it condense; which way should it go.",
           words=480),
        _p("table", "The modes",
           "Every air path the one channel can take.", words=320),
        _p("table", "Eleven weathers, one controller",
           "The owner's table, estimated conditions, and what the code chose.",
           words=360),
        _p("text", "The loop and the purge",
           "Drying the structure is not ventilating the house.", words=340),
        _p("worked", "The controller, as code",
           "What a builder would put on a microcontroller.", words=260),
    ))

CH_LEVELS = Chapter(
    number=34, ref="levels", strand="explain",
    title="Four Levels, and the Ring That Cannot Drain",
    deck="The solver's dome stands on five heights, its seams fall into five "
         "bands, and the slope of each one decides its job",
    derives=("two_v_demo.seam_climate.rings",
             "two_v_demo.seam_climate.stack_pa"),
    corrects="The seam-module chapter took rain in through a slot along "
             "every seam's ridge. Water belongs outside, in a gutter at the rim.",
    pages=(
        _p("opener", "Four levels, and the ring that cannot drain",
           "The rings, counted from the solve rather than from a drawing.",
           words=420,
           figures=(_f("plate-levels",
                       "The seams, coloured by the band they run in."),)),
        _p("table", "The bands, with their slopes", "Which drain and which do not.",
           words=260,
           figures=(_f("plate-dead-level",
                       "The pentagon ring is dead level; the belt's five low "
                       "corners drain it."),)),
        _p("text", "Condense low, drain at the rim",
           "Why the plates belong on the first ring.", words=360),
        _p("errata", "Rain does not come in through the ridge",
           "Correct the seam module's intake slot on the page.", words=300),
        _p("text", "Warm air rises, and the fan still does the work",
           "The stack effect on this dome, in pascals.", words=300),
        _p("text", "The layout", "Every level with one job.", words=320),
    ))

CH_DESICCANT = Chapter(
    number=36, ref="desiccant", strand="explain",
    title="The Desiccant Belongs in a Drawer",
    deck="Molecular sieve holds a fifth of its weight in water -- and a seam "
         "packed with it passes almost no air and can never be dried in place",
    derives=("two_v_demo.seam_climate.beds",
             "two_v_demo.seam_climate.regeneration"),
    pages=(
        _p("opener", "The desiccant belongs in a drawer",
           "Molecular sieve and silica gel, and the question of where.",
           words=380),
        _p("text", "Why not in the seams",
           "The packed bed, the rainbow, and the fan that cannot push it.",
           words=420,
           figures=(_f("plate-packed-seam",
                       "One seam packed with beads, and the pressure it would "
                       "take to push the air through."),)),
        _p("text", "And why it cannot be dried where it sits",
           "Regeneration temperature against the printed key.", words=300),
        _p("steps", "Two drawers and a gate",
           "The twin-tower arrangement at the rim, and the bypass that fails "
           "safe.", words=420,
           figures=(_f("plate-two-drawers",
                       "A drawer of beads and a bypass, switched by a gate "
                       "that falls back open."),)),
        _p("text", "What the desiccant will not do",
           "The wet frame, in drawer fills.", words=300),
        _p("text", "The stove's heat, never its air",
           "A sealed exchanger, and the rule about combustion air.", words=340,
           figures=(_f("plate-stove-exchanger",
                       "The flue sealed away; clean air warmed across a wall "
                       "of steel."),)),
    ))

CH_METAL = Chapter(
    number=37, ref="metal", strand="explain",
    title="Metal in the Seam",
    deck="A Peltier plate is a heat pump that runs both ways, and aluminium, "
         "copper and stainless make a battery the moment the seam is wet",
    derives=("two_v_demo.wood_care.galvanic", "two_v_demo.wood_care.expansion",
             "two_v_demo.seam_climate.cold_channel"),
    pages=(
        _p("opener", "Metal in the seam",
           "Two skins, a plate on each, and the metal between them.",
           words=380,
           figures=(_f("plate-two-skins",
                       "The outer skin at the ridge, the inner skin at the "
                       "room side, and a plate on each."),)),
        _p("text", "The plate runs both ways",
           "Throw the heat to the side you want warmer.", words=320,
           figures=(_f("plate-heat-pump",
                       "Winter: heat to the room. Summer: heat outside."),)),
        _p("text", "Fifteen to twenty degrees colder",
           "The owner's question, with numbers, and the frost that answers "
           "it.", words=420,
           figures=(_f("plate-frost",
                       "A plate driven that far under the dew point freezes."),)),
        _p("text", "Plate first, wood second",
           "Order protects the wood; a colder surface elsewhere does not.",
           words=320,
           figures=(_f("plate-plate-first",
                       "Air over the plate first leaves the wood with room to "
                       "spare."),)),
        _p("table", "Which metals may touch",
           "Aluminium, copper, stainless and galvanised steel, wet.", words=340),
        _p("text", "A liner grows against the wood",
           "Expansion over a seam's length, and how to let it move.",
           words=260),
    ))

CH_BREATHE = Chapter(
    number=35, ref="breathe", strand="explain",
    title="A Cap With No Holes Still Breathes",
    deck="Take the room's air in at the crown, inside the shell; send it down "
         "the seam channels; let it out at the rim, facing the ground. The cap "
         "is never pierced, and the dome still breathes both ways",
    derives=("two_v_demo.seam_vent",),
    corrects="The levels chapter let air out through an apex vent in the cap. "
             "The cap is never opened: the crown takes air in from the room, "
             "under the cap, and every port is at the rim, facing down.",
    pages=(
        _p("opener", "A cap with no holes still breathes",
           "Why a watertight dome must still exchange its air.", words=420,
           figures=(_f("breathing-cap", "The cap is unbroken; the air goes down "
                       "the seams and out at the bottom, facing the ground."),)),
        _p("text", "In at the crown, down the seams, out at the bottom",
           "The path, counted from the solve.", words=420),
        _p("table", "The air falls by itself in winter",
           "The cold siphon, weather by weather.", words=380),
        _p("text", "The water goes the same way as the air",
           "Condensate in the keys, and where it leaves.", words=320),
        _p("text", "Two ways in and out", "Fresh air low, stale air high, both "
           "ports facing the ground.", words=300),
        _p("text", "Where it stops working", "Ice, snow, summer and the fan.",
           words=300),
    ))

CH_RING = Chapter(
    number=38, ref="ring", strand="explain",
    title="Ten Plates, Round the Clock",
    deck="Ten twenty-dollar Peltier modules at the rim ports, run day and night "
         "on the sun: what they really move, what water they really make, and "
         "the array and bank it takes to feed them",
    derives=("two_v_demo.peltier_ring",),
    corrects="The seam-module chapter's condensing figures assumed six plates at "
             "60 W yielding 0.35 litres a kilowatt hour. Solved from the module's "
             "own listing, ten plates draw 65 W a station and yield about 0.2.",
    pages=(
        _p("opener", "Ten plates, round the clock",
           "The owner's proposal and the three questions it asks.", words=300),
        _p("table", "What one module really does",
           "The listing's 70 W against the module's physics, mounted.", words=420),
        _p("table", "Slower is better, until it stops condensing",
           "Voltage against cooling, draw and water.", words=360),
        _p("table", "A day of ten",
           "Heat and water out, against what the room takes on.", words=380),
        _p("table", "Feeding it on the sun",
           "Array, bank and price for twenty-four hours a day.", words=360),
        _p("text", "What to do instead",
           "Daylight surplus, the dew-point controller, and the compressor.",
           words=340),
    ))

CH_IRORI = Chapter(
    number=39, ref="irori", strand="explain",
    title="A Fire in the Middle of the Floor",
    deck="The Japanese irori puts the hearth where a dome has its centre: the "
         "hook hangs from the apex, the seats fit, the warm air dries the frame "
         "-- and the open smoke is the one thing a tight dome cannot take",
    derives=("two_v_demo.irori.facts",),
    pages=(
        _p("opener", "A fire in the middle of the floor",
           "The sunken hearth, and why a dome's centre is its place.", words=360),
        _p("text", "The hook, the seats and the rack",
           "What hangs from the apex and who sits where.", words=520,
           figures=(_f("plate-irori-hook", "The pothook, hung from the apex hub."),
                    _f("plate-irori-seats", "Four seats, the lowest by the entry."))),
        _p("worked", "What the circle costs the floor",
           "Declared inputs, then the fit, honestly counted.", words=380),
        _p("worked", "Warm air and wet wood",
           "The one claim about the building the book can compute.", words=320),
        _p("text", "The smoke, and the fix",
           "Carbon monoxide in a tight room; a hood and a flue.", words=420,
           figures=(_f("plate-irori-flue", "Keep the circle, give the fire a chimney."),)),
    ))

PART_WATER = Part(
    number=6, title="The Seam at Work",
    epigraph="Send air toward the wood only when it is drier than the water "
             "you want to remove -- unless it is going to a cold metal surface "
             "built to catch and drain it.",
    promise="What fits in the channel and what does not, the rule that decides "
            "which way its air moves, what each level of the dome does, where "
            "the desiccant belongs, and the metal that makes it work.",
    chapters=(CH_CHANNEL, CH_DEWPOINT, CH_LEVELS, CH_BREATHE, CH_DESICCANT, CH_METAL,
              CH_RING, CH_IRORI))


# ----------------------------------------------------------------------
# PART 5 -- The floor and the ground
# ----------------------------------------------------------------------

CH_FLOOR = Chapter(
    number=40, ref="floor", strand="howto",
    title="The Floor Is the Other Thing to Get Right",
    deck="It carries everything you own, you touch it all day, and it is "
         "where the ground sends its water",
    derives=("pad_deck.compare", "seed_model.dome_floor_group"),
    pages=(
        _p("opener", "The floor is the other thing to get right",
           "Second half of the thesis, made practical.", words=440),
        _p("table", "Five platforms, taken off board by board",
           "The alternatives, priced on this footprint.", words=280,
           figures=(_f("plate-seven-foundations",
                       "Bare ground to a treehouse platform."),)),
        _p("text", "The floor that clamps rather than is built in",
           "How to keep it swappable.", words=420,
           figures=(_f("mast-and-floor",
                       "The mast through the column, and the floor that "
                       "clamps to it -- sitting on the base ring, where a "
                       "floor goes.",
                       note="Replaces the earlier render, in which the "
                            "floor floated at mid-height and overhung the "
                            "frame on one side."),)),
    ))

CH_PAD = Chapter(
    number=43, ref="pad", strand="explain",
    title="A Pad, Not a Plot",
    deck="The ground is the one thing you cannot take with you, so stop "
         "buying it",
    derives=("pad_deck.deck", "seed_model.quote"),
    pages=(
        _p("opener", "A pad, not a plot",
           "Separating the building from the land it stands on.",
           words=460,
           figures=(_f("plate-pad-is-not-yours",
                       "The landowner builds the pad. It stays when the "
                       "dome leaves."),)),
        _p("text", "What the host builds and keeps",
           "The split, and why it is a clean one.", words=420),
    ))

# ----------------------------------------------------------------------
# PART -- What it costs and what it is worth
# ----------------------------------------------------------------------

CH_TREE_WORTH = Chapter(
    number=44, ref="tree_worth", strand="explain",
    title="A Twenty-Dollar Pine Is Not a Twenty-Dollar Pine",
    deck="One tree priced on every rung: on the stump, burned, sawn, split, built "
         "in, and carried on a mortgage -- the wood never changes, the use does",
    derives=("two_v_demo.pine_value_economics.pine",),
    pages=(
        _p("opener", "What is a pine worth", "Not one price. A ladder of them.", words=360,
           figures=(_f("plate-pine-ladder", "One tree, every rung."),)),
        _p("table", "What the ladder rests on", "Measured, published and mine.", words=200),
        _p("worked", "The rungs", "Stump, fire, lumber, structure, finance.", words=760),
        _p("text", "The household as the whole chain", "Every hand between stump and "
           "wall.", words=360),
    ))

CH_HANDS = Chapter(
    number=45, ref="hands", strand="explain",
    title="Fifteen Sets of Hands",
    deck="Every machine and every middleman between a tree and a stud, counted -- "
         "and the same frame bought at the rack, with everything nobody counts",
    derives=("two_v_demo.wedge_why_facts.steps_mills",
             "two_v_demo.wedge_why_facts.steps_middlemen"),
    pages=(
        _p("opener", "Fifteen sets of hands", "What a shelf price is made of.", words=300),
        _p("worked", "Counting the machines out", "Which survive, which do not.", words=360),
        _p("worked", "What a stud has been through", "Every hand, listed.", words=320),
        _p("worked", "What one wedge is worth", "The rule of thumb, checked.", words=320),
        _p("worked", "The same frame, bought", "With the part nobody counts.", words=360),
    ))

CH_HOUR = Chapter(
    number=46, ref="hour", strand="explain",
    title="How Much Shelter Does an Hour Buy",
    deck="Not how cheap the house is: how much house an hour of your life buys, "
         "how debt multiplies it, and the wage above which you should just buy",
    derives=("two_v_demo.why_build_economics.case",),
    pages=(
        _p("opener", "How much shelter does an hour buy", "The better question.",
           words=340),
        _p("worked", "What an hour produces", "Production value, not a wage.", words=380),
        _p("worked", "Debt makes it larger", "And interest builds nothing.", words=420,
           figures=(_f("plate-interest", "Interest builds no bedroom."),)),
        _p("text", "Out of the commodity chain", "Shocks, and the critical path.",
           words=300),
        _p("text", "When to build, and when to buy", "A rule, not an ideology.",
           words=340),
        _p("table", "The score", "One cycle on one sheet.", words=200),
    ))

CH_HOUSE_MONEY = Chapter(
    number=47, ref="house_money", strand="reference",
    title="Where a House's Money Goes",
    deck="The builders' own survey of a new house, the factory's split of a "
         "trailer, and where the dome's saving actually comes from",
    derives=("two_v_demo.house_economics.house", "two_v_demo.house_economics.stack"),
    pages=(
        _p("opener", "Where a house's money goes", "The land, the building, the "
           "people who sell it.", words=360),
        _p("text", "Labor is not most of it", "And the trailer is built the other way.",
           words=360),
        _p("table", "Every part of the house", "Bought, against the dome way.", words=300),
        _p("text", "Where the saving comes from", "Mostly building your own.", words=360),
        _p("text", "What this does not show", "The half that does not flatter the dome.",
           words=300),
    ))

CH_PRICED = Chapter(
    number=48, ref="priced", strand="reference",
    title="What It Costs, Line by Line",
    deck="The invoice, the price guide, the pad, the stay and the factory -- every "
         "figure typed in declared before anything is claimed",
    derives=("two_v_demo.seed_facts.steps_invoice", "two_v_demo.master_facts.steps_price",
             "two_v_demo.park_facts.steps_stay"),
    pages=(
        _p("opener", "What it costs, line by line", "What was typed in first.", words=300),
        _p("table", "The invoice", "Ten thousand to build.", words=320),
        _p("table", "Four ways to buy it", "The price guide, receipts attached.", words=240),
        _p("table", "The pad, the stay, and the deluxe", "The ground's bill.", words=420),
        _p("text", "The factory's view", "What a line costs its builders.", words=260),
    ))

CH_STAPLE = Chapter(
    number=49, ref="staple", strand="explain",
    title="The Staple House",
    deck="The owner's McDouble: cheap, fast, known, the same every time -- the first "
         "rung of housing built to be a staple instead of a project, and the papercuts "
         "it leaves out, counted on both bills",
    derives=("two_v_demo.staple_facts.steps_papercuts", "two_v_demo.staple_facts.steps_interest",
             "two_v_demo.staple_facts.steps_staple"),
    pages=(
        _p("opener", "The staple house", "The owner's analogy, in his words.", words=260),
        _p("text", "What a staple is", "Always there, always the same, known.", words=300),
        _p("worked", "The papercuts", "The survey house's fee and margin lines, and the loan.", words=520),
        _p("table", "The staple's bill", "Nine lines, one seller, the margin printed.", words=360),
        _p("text", "Why a baseline regulates everything", "The claim, and how far it holds.", words=380),
        _p("text", "A family event, not a transaction", "Known, transparent, added to for life.",
           words=420),
    ))

PART_ECON = Part(
    number=8, title="What It Costs and What It Is Worth",
    epigraph="The tree is the same on every rung. What moves it up the ladder is how "
             "much of it you keep, and how many of the steps between the tree and "
             "the wall you are willing to take yourself.",
    promise="What a tree is worth on every rung, every hand between a stump and a "
            "stud, how much shelter an hour of your life buys, where a house's money "
            "goes, the invoice line by line, and why the first rung should be a staple.",
    chapters=(CH_TREE_WORTH, CH_HANDS, CH_HOUR, CH_HOUSE_MONEY, CH_PRICED, CH_STAPLE))


CH_PENTAGON = Chapter(
    number=41, ref="pentagon", strand="howto",
    title="The Pentagon From Five Logs",
    deck="Five 20 ft half trunks and the star inside them: the golden ratio splits every "
         "diagonal so one log gives one long piece and one short -- the centreline lengths, "
         "the lengths the saw actually cuts, the logs it takes, and the layout on the ground",
    derives=("world3d.structures.foundation_facts", "infill.base"),
    pages=(
        _p("opener", "The pentagon from five logs", "Logs, not boards.", words=220),
        _p("worked", "The diagonal and the star", "The golden ratio, worked.", words=520),
        _p("table", "What the saw actually cuts", "Centreline against cut.", words=380),
        _p("text", "The pinwheel at every crossing", "Nothing meets at a corner.", words=260),
        _p("steps", "Laying it out", "Stakes and string.", words=300),
    ))

CH_WORLD = Chapter(
    number=42, ref="world", strand="howto",
    title="One World, Three Structures",
    deck="The foundation, the dome and the zome on one hilltop, with their jigs and skins: a "
         "layers panel, and every piece selectable, sawn, deleted, added, moved or copied, "
         "snapped to the grid, undone exactly and listed for the saw",
    derives=("world3d.structures", "world3d.document"),
    pages=(
        _p("opener", "One world, three structures", "Nothing drawn by hand.", words=220),
        _p("text", "The layers", "Show, hide, lock.", words=280),
        _p("steps", "Taking it apart", "Select, saw, add, move, undo.", words=620),
        _p("text", "The three jigs", "Stakes, the panel jig, the table.", words=300),
    ))

PART_FLOOR = Part(
    number=7, title="The Floor and the Ground",
    epigraph="Everything you own sits on the floor, and the ground is the "
             "one part of the building you cannot take with you.",
    promise="The second thing that has to be right, the five ways to build "
            "it, and the argument for standing on somebody else's ground.",
    chapters=(CH_FLOOR, CH_PENTAGON, CH_WORLD, CH_PAD))


# ----------------------------------------------------------------------
# PART 6 -- The network
# ----------------------------------------------------------------------

CH_NETWORK = Chapter(
    number=50, ref="network", strand="explain",
    title="Why a Network Beats a Park",
    deck="An RV park rents you a slot for a week. This rents you a "
         "foundation for a decade, and both sides come out ahead",
    derives=("park_model.pad", "pad_deck.deck", "seed_model.quote"),
    pages=(
        _p("opener", "Why a network beats a park",
           "The idea, and why it is not a caravan site.", words=480),
        _p("text", "What the tenant gets",
           "The dome owner's side of the incentive, in numbers.",
           words=560,
           beats=("no land purchase, no mortgage, no property tax",
                  "the building is yours and it moves",
                  "a pad is cheaper than the foundation you would pour",
                  "you can leave, and the thing you leave behind is a "
                  "platform rather than a house",
                  "stay a season or stay a decade")),
        _p("text", "What the host gets",
           "The landowner's side, and why it beats an RV pitch.",
           words=560,
           beats=("the pad is built once and rents for years",
                  "tenants are owners, so they behave like owners",
                  "no plumbing a rig, no turnover every weekend",
                  "the improvement stays on the land and is worth "
                  "something when it is empty")),
        _p("table", "Against an RV park, and against renting",
           "The three-way comparison, per year and per decade.", words=320),
        _p("text", "What would have to be true",
           "The conditions this argument rests on, stated plainly.",
           words=380),
    ))

CH_PAD_KIT = Chapter(
    number=51, ref="pad_kit", strand="explain",
    title="What a Pad Actually Is",
    deck="A deck, a rim, three pipes up the middle and a meter at the edge -- "
         "and the line between the host's half and the tenant's that never moves",
    derives=("two_v_demo.park_facts.steps_fit", "two_v_demo.park_facts.steps_foundation",
             "park_model.iris_cost"),
    pages=(
        _p("opener", "What a pad actually is",
           "Watch one get built, from graded ground to the pedestal.", words=420),
        _p("text", "The reserved spot", "Services up the middle, never across the door.",
           words=340),
        _p("table", "Sizes are rounded up, not invented",
           "The pad catalogue, and the iris that spans three domes.", words=380),
        _p("text", "The pad is the floor", "Nothing poured, nothing dug, nothing left.",
           words=320),
        _p("table", "What the ground is worth", "Design by design, measured.", words=360),
        _p("text", "Below the line and above it", "Who owns what, and why it never moves.",
           words=320),
    ))

CH_HOST = Chapter(
    number=52, ref="host", strand="explain",
    title="What a Host Earns, Line by Line",
    deck="The cheapest pad that works, the ten-thousand-dollar target it misses, "
         "the rents that would repay it, and the bill a host stops paying",
    derives=("two_v_demo.byod_facts.steps_starter", "two_v_demo.byod_facts.steps_target",
             "two_v_demo.park_facts.steps_pad_cost", "two_v_demo.park_facts.steps_exposure"),
    pages=(
        _p("opener", "Why anybody would host a dome", "Income from land, without a house to keep.",
           words=360),
        _p("table", "The cheapest working pad", "Line by line, with the site allowance in.",
           words=380),
        _p("table", "What ten thousand dollars would return", "Three rents, payback on net.",
           words=360),
        _p("text", "What the host maintains", "A deck and a connection. Not a kitchen.", words=320),
        _p("table", "The deluxe pad", "Rotation, iris, column and array -- priced.", words=300),
    ))

CH_TENANT = Chapter(
    number=53, ref="tenant", strand="explain",
    title="A House That Moves, and Grows",
    deck="Start small, reallocate the rooms as life changes, add a layer when you "
         "can afford it, and take all of it with you when you go",
    derives=("two_v_demo.park_facts.steps_hardware", "two_v_demo.park_facts.steps_layers",
             "two_v_demo.byod_facts.steps_growth"),
    pages=(
        _p("opener", "Why buy the dome", "Start small; upgrade the home you own.", words=340),
        _p("text", "The rooms can change", "Nonstructural partitions round a fixed core.",
           words=320),
        _p("text", "Semi-nomadic", "A house that comes apart, moved when it is worth it.",
           words=340),
        _p("table", "One hardware set, three sizes", "Counts fixed; sticks and skin grow.",
           words=360),
        _p("table", "A house that gets warmer every winter", "The layer ladder, and 1 over R.",
           words=400),
    ))

CH_TURNS = Chapter(
    number=54, ref="turns", strand="explain",
    title="The Pad Turns, and the Site Shares",
    deck="A rotating base, cells on the shell, a bathhouse so a house can carry "
         "no plumbing -- and the surplus power a tenant cannot use",
    derives=("two_v_demo.park_facts.steps_solar", "two_v_demo.byod_facts.steps_solar"),
    pages=(
        _p("opener", "The deluxe version", "A house that faces what you want.", words=320),
        _p("table", "What tracking is worth", "A quarter more power, and far more than anyone uses.",
           words=420),
        _p("text", "What a site can share", "A bathhouse, a column, a meter passed through.",
           words=320),
        _p("text", "Another use", "A climate-controlled storage dome.", words=200),
    ))

CH_WHY_ME = Chapter(
    number=55, ref="why_me", strand="story",
    title="Who This Is For",
    deck="A nineteen-year-old with nowhere steady to live, a single mother working "
         "two shifts, and a man on his seventh holiday watching a rental portfolio",
    derives=("two_v_demo.park_facts.steps_ask",),
    pages=(
        _p("opener", "What this would have meant to me", "The person this is designed for.",
           words=420),
        _p("text", "Built with the little guy in mind", "Who it is for, and who it is not.",
           words=340),
        _p("text", "Three things at once", "Quilters, hosts and owners, each needing the others.",
           words=320),
        _p("table", "Small scale, small risk", "What the first site's money is for.", words=380),
        _p("text", "The strategy, stated plainly", "Three phases and one honest endgame.",
           words=300),
    ))

PART_NETWORK = Part(
    number=9, title="The Network",
    epigraph="Own the building. Rent the ground. Move when you want to, and "
             "leave a platform behind rather than a house.",
    promise="The pad network from both sides of it: what a pad is, what a host "
            "earns and stops paying for, what the house that lands on it can "
            "become, the deluxe pad that turns, and who all of it is for.",
    chapters=(CH_NETWORK, CH_PAD_KIT, CH_HOST, CH_TENANT, CH_TURNS, CH_WHY_ME))


# ----------------------------------------------------------------------
# PART 7 -- Variations
# ----------------------------------------------------------------------

CH_ALTERNATIVES = Chapter(
    number=62, ref="alternatives", strand="reference",
    title="Every Other Way of Doing It",
    deck="Eight frame materials, eight sections, sixteen panels, nine "
         "claddings and twelve foundations -- priced on this dome, not in "
         "the abstract",
    derives=("wedge_book.alternatives.catalogue",),
    pages=(
        _p("opener", "Every other way of doing it",
           "How to read the tables, and what is deliberately missing.",
           words=380),
        _p("table", "The frame", "Materials and sections.", words=200,
           figures=(_f("plate-eight-materials",
                       "The same frame, priced and weighed eight ways."),
                    _f("plate-eight-sections",
                       "Round tube to quarter wedge, all at the same "
                       "width."))),
        _p("table", "The envelope", "Panels and claddings.", words=200,
           figures=(_f("plate-sixteen-panels",
                       "Everything the tool can put between the struts."),
                    _f("plate-nine-claddings",
                       "What goes over the sheathing."))),
    ))

CH_FLOATING = Chapter(
    number=77, ref="floating", strand="explain",
    title="Hang It Between Two Trees",
    deck="The most speculative corner of the method: a mast, three cables, "
         "and no ground at all -- priced, and explicitly not rated",
    derives=("seed_model.suspension_group", "seed_model.frame_weight_lb"),
    pages=(
        _p("opener", "Hang it between two trees",
           "The idea, and the sentence that has to go with it.",
           words=460,
           figures=(_f("floating-dome",
                       "The same mast and floor, hung on three cables to "
                       "saddles on two trees.",
                       note="Replaces the earlier render, in which the dome "
                            "came out stretched into a cone."),)),
        _p("safety", "Priced, not rated",
           "The engineer's sentence, boxed and unmissable.", words=200),
    ))

CH_SKYWEB = Chapter(
    number=78, ref="skyweb", strand="howto",
    title="Build It in the Air",
    deck="An X of wire rope between four living trees, a 12 V winch, and forty "
         "triangles hung on three cords each, then gathered to one point, "
         "skinned, and left up -- with the owner's weighed struts, every load "
         "worked, and the numbers that argue back",
    derives=("two_v_demo.sky_web", "two_v_demo.cell_wall.frame_mass_kg"),
    pages=(
        _p("opener", "Build it in the air",
           "The method in one paragraph, the two tables, and two corrections.",
           words=520,
           figures=(_f("plate-sky-floating",
                       "Forty triangles, each on its own three cords."),)),
        _p("text", "Four trees and an X",
           "The span, the sag, the rope, the guys to the next trees.", words=560,
           figures=(_f("plate-sky-guys",
                       "Guyed to the base of the next tree out."),)),
        _p("text", "A tree is a better post",
           "The living trunk against the 6x6 sawn from it.", words=240,
           figures=(_f("plate-sky-treepost",
                       "A milled 6x6 beside the trunk it would be sawn from."),)),
        _p("steps", "One triangle, start to finish",
           "Winch, harness, hoist, swing, pigtails, slip.", words=600,
           figures=(_f("plate-sky-pigtails",
                       "Three pigtails over the spiral, then it slips the harness."),)),
        _p("text", "Rim first, crown last, then join",
           "The order, where the hook runs out, and lashing instead of screws.", words=420),
        _p("text", "Every cord to the apex",
           "Through the air, not along the struts; one winch for the whole dome.", words=560,
           figures=(_f("plate-sky-apex",
                       "Cords from every joint to one free ring under the cap."),)),
        _p("text", "A silicone skin",
           "Cotton soaked in silicone dissolved in naphtha, priced.", words=320,
           figures=(_f("plate-sky-skin",
                       "The silicone-cotton skin, laid from the crown down."),)),
        _p("text", "Building with the trees",
           "Shade, water, no ground contact, wind, and what the trees ask back.", words=440),
        _p("text", "Higher, if the trees allow",
           "An experimental second web, planned before the trees are chosen.", words=300,
           figures=(_f("plate-sky-corners",
                       "The joined dome, raised a corner at a time."),)),
        _p("safety", "What it will and will not carry",
           "A floor full of life, and nobody under the load.", words=300),
    ))

CH_HUBBED = Chapter(
    number=73, ref="hubbed", strand="howto",
    title="If You Build It on Hubs",
    deck="The conventional two-frequency dome, for anybody with a hub system "
         "and no splitting maul: two lengths, one deduction, two bevels, and "
         "the four things that actually go wrong",
    derives=("two_v_demo.geometry", "two_v_demo.book_math"),
    pages=(
        _p("opener", "The five words", "Hub, strut, panel, chord factor, frequency.",
           words=300),
        _p("text", "Two lengths, and the hub that decides every cut",
           "Chord factors, the connector deduction, end cuts.", words=460),
        _p("text", "Bevels, hub types and the stock", "What the bench needs to know.",
           words=360),
        _p("steps", "Cut, jig, raise", "A stop block, a master, triangles flat first.",
           words=360),
        _p("text", "The four things that actually go wrong", "None of them geometry.",
           words=260),
    ))

CH_FRANKEN = Chapter(
    number=74, ref="franken", strand="story",
    title="The Frankendome",
    deck="A hundred and twenty sticks of no particular description, brackets "
         "folded out of a washing machine, ten days, and half a year standing",
    derives=("two_v_demo.franken_economics", "two_v_demo.lesson_franken"),
    pages=(
        _p("opener", "Whatever the chainsaw made", "The experiment, and why it was run.",
           words=360),
        _p("text", "A bracket out of a washing machine", "Shear, drill, fold once.", words=320),
        _p("text", "Nothing lands where it should", "Slack, settling and the skin.", words=380),
        _p("table", "The ledger", "Brackets, screws, days, and the bill.", words=380),
        _p("text", "What it trades", "And what comes after it.", words=340),
    ))

CH_EMPIRE = Chapter(
    number=75, ref="empire", strand="story",
    title="The Evil Dome Empire",
    deck="A house as a platform, a business plan built on ink cartridges, the "
         "one catastrophic weakness in it -- and then the serious part",
    derives=(),
    pages=(
        _p("opener", "What if a house was a platform?", "Keep the bones.", words=300),
        _p("text", "The world's poorest supervillain", "Salvage, and affordable failure.",
           words=360),
        _p("text", "The business plan", "Tribute, the fortress, and the Hoboclass.",
           words=360),
        _p("text", "Now the serious part", "Trillions, a prototype, and one share.",
           words=420),
        _p("text", "Who it is for", "A tornado through a hardware store.", words=300),
    ))

CH_FULLER = Chapter(
    number=76, ref="fuller", strand="story",
    title="So a Mother Could Raise Her Child",
    deck="A single mother, a repossessed trailer, the school lunches I would not "
         "take -- and the sentence of Buckminster Fuller's that made this a mission",
    derives=(),
    pages=(
        _p("opener", "The list of likes", "Programming, wiring, wood, metal, taking things apart.",
           words=280),
        _p("text", "Why women specifically", "A mother who was an angel and a saint.", words=380),
        _p("text", "And then I heard Fuller", "The sentence, and what it did.", words=320),
        _p("text", "The proof already exists", "And forty faces facing the road.", words=280),
    ))

PART_VARIATIONS = Part(
    number=13, title="Variations",
    epigraph="The same frame can wear more than one roof, stand on more than "
             "one ground, and hang from nothing at all.",
    promise="The conventional hubbed dome for anybody who wants one, the "
            "author's first dome framed from whatever the chainsaw made, the "
            "joke and the serious argument behind it, and the floating dome -- "
            "a design possibility, priced and explicitly not rated.",
    chapters=(CH_HUBBED, CH_FRANKEN, CH_EMPIRE, CH_FULLER, CH_FLOATING, CH_SKYWEB))


# ----------------------------------------------------------------------
# PART 8 -- The tools
# ----------------------------------------------------------------------

CH_TOOLING = Chapter(
    number=84, ref="tooling", strand="reference",
    title="The Software That Wrote This Book",
    deck="Eight three-dimensional worlds, a cost model and a solver -- what "
         "each one is for, what it can do, and how to open it",
    derives=("wedge_book.tooling.catalogue",),
    pages=(
        _p("opener", "The software that wrote this book",
           "What is included, and why a builder would open any of it.",
           words=460),
        _p("table", "The worlds", "Each environment, its job and its keys.",
           words=520),
    ))

CH_WORLDS = Chapter(
    number=86, ref="worlds", strand="reference",
    title="What Each World Shows You",
    deck="One picture from every three-dimensional environment in the "
         "project, with what it is for and what to do in it",
    derives=("wedge_book.tooling.catalogue",),
    pages=(
        _p("plate", "The raw-wedge solver",
           "The dome this book is about, solved.", words=180,
           figures=(_f("standard-dome-exploded",
                       "The reference build, opened eight inches."),)),
        _p("plate", "The fabrication jig",
           "The fixture, twelve steps.", words=180,
           figures=(_f("the-jig",
                       "A panel closed on the jig."),)),
        _p("plate", "The Dome Creator",
           "Every building the catalogue makes.", words=180,
           figures=(_f("plate-twelve-domes",
                       "Twelve designs, drawn by the tool that builds "
                       "them."),)),
        _p("plate", "The seed world",
           "The product line, its column and its cap.", words=180,
           figures=(_f("plate-core-socket",
                       "Power and water up the middle and out the apex."),)),
        _p("plate", "The pad and the park",
           "The ground, and the network on it.", words=180,
           figures=(_f("plate-the-pad",
                       "The platform, built one course at a time."),)),
        _p("plate", "The cost console",
           "The price, live, over the solved dome.", words=180,
           figures=(_f("tool-cost-console",
                       "The geometry and the price in one program."),)),
    ))

CH_SCREEN = Chapter(
    number=85, ref="screen", strand="explain",
    title="From One Number to a Lit Pixel",
    deck="How every picture in this book was drawn: a strut given a body, a "
         "camera placed with two angles, three matrices, one divide, one "
         "comparison and three dot products -- thirty times a second",
    derives=("two_v_demo.scratch_facts",),
    pages=(
        _p("opener", "Nothing but arithmetic", "The shape, and then the picture.", words=300),
        _p("worked", "A line with no thickness", "Tubes, normals and the upload.", words=520),
        _p("worked", "Placing the camera", "Two angles, the view matrix, the lens.", words=520),
        _p("worked", "The divide that makes distance work", "One vertex, all the way to a pixel.",
           words=400),
        _p("worked", "What hides what, and how bright", "Depth, culling, light, glass.", words=520),
        _p("worked", "And then it does it again", "The cost of one frame.", words=300),
    ))

CH_EVERY_PIECE = Chapter(
    number=88, ref="everypiece", strand="howto",
    title="Every Piece, Numbered",
    deck="The calculator that fills a triangle and frames the floor: every "
         "piece numbered, every cut set up on the saw before the blade turns, "
         "ten ways to fill one panel, seven ways to frame the platform under "
         "the dome from five 20 ft half trunks -- every span and pier checked, "
         "and the patterns that fail shown failing",
    derives=("infill.facts", "infill.base", "infill.recipes", "infill.sawview", "infill.methodology"),
    pages=(
        _p("opener", "Every piece, numbered",
           "What the calculator does, and the two tables it rests on.", words=420,
           figures=(_f("plate-ep-numbered",
                       "Seventeen wedges in one triangle, every one numbered."),)),
        _p("text", "A triangle is a tray",
           "Two shapes, forty-five degree walls, the folds next door.", words=320),
        _p("worked", "The frame and infill stock budget",
           "First reserve the frame blanks, declare continuous pair coverage, and convert "
           "the conditional infill budget into uniform usable-trunk equivalents.", words=680),
        _p("steps", "One wedge, start to finish",
           "Piece five: its three lengths, the mitre, the bevel, the offcuts.", words=620,
           figures=(_f("plate-ep-saw",
                       "Cut one: sawn face down, bark corner to the fence."),
                    _f("plate-ep-offcut",
                       "Cut two, and an offcut long enough to keep."))),
        _p("text", "When the saw cannot reach",
           "A covering sheet's bevels, marked and cut by hand.", words=240),
        _p("table", "Ten ways to fill one triangle",
           "Every pattern, its piece count, and log rounds cut to fit.", words=420,
           figures=(_f("plate-ep-perms",
                       "One of the ten: the same triangle, another fill."),
                    _f("plate-ep-under",
                       "From underneath, the face the room will see."))),
        _p("text", "Five trunks, one pentagon",
           "The floor's edge, the circle inside it, and every corner one cut.", words=520,
           figures=(_f("plate-ep-frame",
                       "Five half trunks, round backs out, round the dome's centre."),
                    _f("plate-ep-corner",
                       "Thirty-six degrees off square, marked and plumbed for the chainsaw."))),
        _p("text", "A star, and why it needs joists",
           "The star alone fails its deck; joists bring every gap inside reach.", words=460,
           figures=(_f("plate-ep-star",
                       "The star alone: the gaps a deck board cannot cross."),
                    _f("plate-ep-joists",
                       "Joists between the points."))),
        _p("worked", "Where the weight goes",
           "Tributary floor, joists, primaries, piers; bending and sag; pads.", words=560),
        _p("table", "Seven ways to frame the floor",
           "Every pattern compared, on piers and on gravel, and the materials swapped.", words=600,
           figures=(_f("plate-ep-gravel",
                       "Nested rings on a gravel bed, the gaps packed."),
                    _f("plate-ep-dome",
                       "The dome on its floor."))),
        _p("safety", "What these numbers are not",
           "A guessed wood strength, estimated prices, and an engineer's signature.", words=240),
    ))


CH_STY_CABIN = Chapter(
    number=79, ref="stycabin", strand="explain",
    title="The Cabin in the Creator",
    deck="The forty-hour cabin's dome rebuilt in the Dome Creator at its own size -- "
         "the same struts and panels -- priced line by line, with every place the "
         "Creator's figure and the wedge method's own differ, said out loud",
    derives=("two_v_demo.cabin_styles", "two_v_demo.creator_facts"),
    pages=(
        _p("opener", "The same dome, in another tool",
           "Why the Creator, and what it measures.", words=420,
           figures=(_f("plate-sty-bare", "The cabin, bare, in the Creator."),)),
        _p("table", "The bare cabin, line by line",
           "Frame, panels, cladding, foundation; weight and hours.", words=380),
        _p("text", "Where the two tools disagree",
           "Floor area, the frame line, and the hours.", words=420),
    ))

CH_STY_TWELVE = Chapter(
    number=80, ref="stytwelve", strand="howto",
    title="Twelve Ways to Dress One Frame",
    deck="The cabin's frame in the skin, colours and foundation of each of the "
         "Creator's twelve designs: rendered, priced, weighed and timed",
    derives=("two_v_demo.cabin_styles",),
    pages=(
        _p("opener", "A style is a skin and a footing",
           "What carries over from a design, and what stays the cabin's.", words=360),
        _p("text", "Timber and glass", "The workshop, the loft, the homestead.", words=320,
           figures=(_f("plate-sty-timber-workshop", "The cabin as the Timber Workshop."), _f("plate-sty-glass-studio-loft", "The cabin as the Glass Studio Loft."), _f("plate-sty-split-log-homestead", "The cabin as the Split-Log Homestead."),)),
        _p("text", "Trunks, twinwall and hexes", "The lodge, the grow dome, the pavilion.", words=300,
           figures=(_f("plate-sty-whole-trunk-lodge--20-ft", "The cabin as the Whole Trunk Lodge - 20 ft."), _f("plate-sty-grow-dome", "The cabin as the Grow Dome."), _f("plate-sty-hex-cell-pavilion", "The cabin as the Hex Cell Pavilion."),)),
        _p("text", "Open frames and concrete", "The hangar, the garden, the monocoque.", words=300,
           figures=(_f("plate-sty-continuous-steel-arc-hangar", "The cabin as the Continuous Steel Arc Hangar."), _f("plate-sty-rebar-garden-dome", "The cabin as the Rebar Garden Dome."), _f("plate-sty-concrete-monocoque-form", "The cabin as the Concrete Monocoque Form."),)),
        _p("text", "Mirrors and a treehouse", "The two mirrors, and the cabin up a tree.", words=320,
           figures=(_f("plate-sty-woodland-hex-mirror", "The cabin as the Woodland Hex Mirror."), _f("plate-sty-woodland-square-mirror", "The cabin as the Woodland Square Mirror."), _f("plate-sty-treehouse-canopy-dome", "The cabin as the Treehouse Canopy Dome."),)),
        _p("table", "All twelve, side by side", "Totals, weights, hours, and each line.", words=300),
    ))

CH_STY_MENUS = Chapter(
    number=81, ref="stymenus", strand="howto",
    title="One Menu at a Time",
    deck="Every frame material, every panel, every cladding and every foundation "
         "on the bare cabin in turn -- which menu moves the money, and by how much",
    derives=("two_v_demo.cabin_styles",),
    pages=(
        _p("opener", "Change one thing", "The bare cabin as the fixed point.", words=260),
        _p("table", "The frame", "Eight materials, each in its own section.", words=360),
        _p("table", "The panels", "Fifteen skins.", words=300),
        _p("table", "Cladding and foundation", "Over the skin, and under the floor.", words=320),
        _p("text", "Where to spend", "The menus ranked by what they swing.", words=300),
    ))

CH_STY_GRID = Chapter(
    number=82, ref="stygrid", strand="reference",
    title="Every Skin on Every Frame",
    deck="The permutations in full: every panel on every frame material, every "
         "cladding on every foundation, each a priced rebuild of the cabin -- and "
         "how many buildings the menus multiply to",
    derives=("two_v_demo.cabin_styles", "two_v_demo.creator_facts"),
    pages=(
        _p("opener", "Every combination, priced", "How to read the two tables.", words=240),
        _p("table", "Panel on frame", "One hundred and twenty cabins.", words=260),
        _p("table", "Cladding on foundation", "Sixty-three more.", words=220),
        _p("text", "How many domes that is", "The menus multiplied, and the inert settings.", words=300),
    ))

CH_STY_PRICES = Chapter(
    number=83, ref="styprices", strand="reference",
    title="The Price List, Item by Item",
    deck="Every unit price the Creator uses, as declared -- frame, panels, cladding, "
         "foundations, fixings, wire and pipe -- and every piece of equipment it can "
         "put on the floor, with each design's fit-out priced as a package",
    derives=("materials", "workshop", "two_v_demo.cabin_styles"),
    pages=(
        _p("opener", "Declared, not measured", "Whose numbers these are.", words=220),
        _p("table", "The shell", "Frame, panels, cladding, foundations, fixings.", words=300),
        _p("table", "Wire, pipe and walls", "The rates the fit-out uses.", words=200),
        _p("table", "Everything on the floor", "Equipment by category; the fit-out packages.", words=360),
    ))

PART_STYLE = Part(
    number=14, title="Style It",
    epigraph="The frame is forty hours. Everything you will look at for the next "
             "forty years goes on after it.",
    promise="The cabin's frame dressed every way the Dome Creator can dress it -- "
            "twelve styles rendered, every menu swept, every skin on every frame, "
            "and every item on the price list -- each one a priced rebuild of the "
            "same dome.",
    chapters=(CH_STY_CABIN, CH_STY_TWELVE, CH_STY_MENUS, CH_STY_GRID, CH_STY_PRICES))


PART_TOOLS = Part(
    number=15, title="The Tools",
    epigraph="Every number in this book came out of a program about a second "
             "before it reached the page. Here are the programs.",
    promise="What ships with this book: the solver, the worlds, the cost "
            "model and the calculators, what each is for and how to drive "
            "it -- and the arithmetic that turns one number into every "
            "picture in these pages.",
    chapters=(CH_TOOLING, CH_SCREEN, CH_WORLDS, CH_BOM, CH_EVERY_PIECE))


# ----------------------------------------------------------------------
# Front and back
# ----------------------------------------------------------------------

FRONT: tuple[Matter, ...] = (
    Matter("title", "Title page", (
        _p("text", "Title page", "Title, subtitle and the one-line claim.",
           words=120,
           figures=(_f("plate-frame-on-land",
                       "The frame, on its own land."),)),
        _p("text", "Forty hours",
           "The arithmetic the title rests on, and the honest caveat "
           "about doing it linearly.", words=560),
        _p("text", "What this book is", "Three strands and how to read.",
           words=560),
        _p("text", "Every number here is computed",
           "The token discipline, and why it exists.", words=420),
        _p("safety", "The engineer's note",
           "What this book is not, stated before anything else.",
           words=320),
    )),
)

BACK: tuple[Matter, ...] = (
    Matter("tables", "Reference tables", (
        _p("table", "Cut lists at every size", "The builder's page.",
           words=200),
        _p("table", "Angles and counts", "The solved facts, one page.",
           words=200),
    )),
    Matter("claims", "Every claim, and what it rests on", (
        _p("text", "Known geometry, tested construction, design possibility",
           "Restate the three kinds of claim and sort every one.",
           words=620),
    )),
)



# ----------------------------------------------------------------------
# PART -- The geometry, from scratch
# ----------------------------------------------------------------------

CH_TRIANGLES = Chapter(
    number=6, ref="triangles", strand="explain",
    title="Why It Is Triangles",
    deck="Every other polygon is a mechanism. A triangle is the only shape "
         "that cannot change without something breaking",
    derives=("two_v_demo.scratch_facts.steps_phi",),
    pages=(
        _p("opener", "Why it is triangles",
           "The property that makes the whole method possible, before any "
           "dome.", words=460,
           figures=(_f("plate-why-triangles",
                       "Why the shape is triangles at all."),),
           beats=("a four-bar linkage folds; a triangle does not",
                  "so a triangulated frame needs no rigid corner",
                  "which is why the joint can be two flat faces touching")),
        _p("text", "And why an icosahedron",
           "Why the subdivision starts from that solid and not another.",
           words=440,
           figures=(_f("plate-icosahedron",
                       "The solid everything starts from."),)),
    ))

CH_PHI = Chapter(
    number=7, ref="phi", strand="explain",
    title="Twelve Points From One Number",
    deck="Where the golden ratio actually sits in this method -- and the "
         "place everybody expects it and it is not",
    derives=("two_v_demo.scratch_facts.PHI",),
    pages=(
        _p("opener", "Twelve points from one number",
           "The golden ratio's real job: placing the icosahedron's twelve "
           "vertices.", words=520,
           figures=(_f("plate-phi",
                       "Twelve points placed by one irrational number."),),
           beats=("phi is the number whose square is itself plus one",
                  "(0, +/-1, +/-phi) and its rotations give twelve points",
                  "every one of them the same distance from its neighbours",
                  "nobody measured anything")),
        _p("text", "It survives all the way to the cut list",
           "The long chord factor is exactly one over phi.", words=420),
        _p("text", "And the place it is not",
           "The ratio between the two struts is not golden, and that "
           "surprise is worth a page.", words=380),
    ))

CH_SUBDIVIDE = Chapter(
    number=8, ref="subdivide", strand="explain",
    title="Halve Every Edge, Then Push It Out",
    deck="One division puts the icosahedron on a unit sphere; halving its edges "
         "and pushing the midpoints back out is the whole of 2V",
    derives=("two_v_demo.scratch_facts.steps_normalize",
             "two_v_demo.scratch_facts.steps_midpoint",
             "two_v_demo.scratch_facts.steps_project",
             "two_v_demo.scratch_facts.steps_euler"),
    pages=(
        _p("opener", "Halve every edge, then push it out",
           "The two moves that turn a solid into a dome.", words=260),
        _p("text", "Put it on a sphere of radius one",
           "One division, and every length becomes a multiplier.", words=360,
           figures=(_f("plate-unit-sphere",
                       "The icosahedron on a sphere of radius one."),)),
        _p("text", "Halve every edge",
           "Thirty midpoints, every one of them inside the ball.", words=360,
           figures=(_f("plate-halve", "Thirty parent edges, thirty midpoints."),
                    _f("plate-midpoint-sag",
                       "The straight line cuts the corner."),)),
        _p("text", "Push the midpoints out",
           "The one move that makes it geodesic.", words=320,
           figures=(_f("plate-push-out",
                       "Same direction, distance set to the radius."),)),
        _p("text", "Two lengths come out", "Measure every edge again.", words=300,
           figures=(_f("plate-two-classes",
                       "A hundred and twenty edges, exactly two lengths."),)),
        _p("worked", "Euler's check", "One addition proves the model closed.",
           words=220),
    ))

CH_FOUR_WAYS = Chapter(
    number=9, ref="four_ways", strand="explain",
    title="Two Lengths, Four Ways",
    deck="Four independent routes to the same chord factor, and the "
         "residual between them printed rather than promised",
    derives=("two_v_demo.scratch_facts.build_demo_geometry",),
    pages=(
        _p("opener", "Two lengths, four ways",
           "Never trust one calculation.", words=480,
           figures=(_f("plate-chords-four-ways",
                       "The two chord factors, derived four ways."),)),
        _p("worked", "The four routes",
           "Coordinates, central angle, law of cosines, and CAD.",
           words=460,
           figures=(_f("plate-cross-check",
                       "Two ways of computing the same number, and the "
                       "residual between them."),)),
    ))

CH_HEMISPHERE = Chapter(
    number=10, ref="hemisphere", strand="explain",
    title="Half a Sphere Is a Building",
    deck="Where the sphere gets cut, what survives the cut, and how every "
         "count in this book falls out of it",
    derives=("wedge_book.numbers.quantities",),
    pages=(
        _p("opener", "Half a sphere is a building",
           "The truncation, and why this one.", words=440,
           figures=(_f("plate-hemisphere",
                       "Where a sphere gets cut to become a building."),)),
        _p("table", "Counting the building",
           "Vertices, edges, faces, seams, base -- all from the topology.",
           words=360,
           figures=(_f("plate-counting",
                       "Every part of the building, counted."),)),
    ))

CH_SIZE = Chapter(
    number=11, ref="size", strand="howto",
    title="Choosing a Size, At Last",
    deck="One number decides the whole building, and this book picks it "
         "from the stick rather than from the floor plan",
    derives=("wedge_book.numbers.reference_designs",),
    pages=(
        _p("opener", "Choosing a size, at last",
           "From factors to lumber.", words=460,
           figures=(_f("plate-project",
                       "The push that makes it geodesic."),)),
        _p("table", "Five sizes, and what each is for",
           "The reference designs.", words=420),
    ))

PART_MATHS = Part(
    number=2, title="The Geometry, From Scratch",
    epigraph="One irrational number places twelve points in perfectly even "
             "space. Everything else in this book is consequences.",
    promise="The whole derivation, on screen: why triangles, why an "
            "icosahedron, where the golden ratio really sits, and the two "
            "lengths that come out of it.",
    chapters=(CH_TRIANGLES, CH_PHI, CH_SUBDIVIDE, CH_FOUR_WAYS, CH_HEMISPHERE, CH_SIZE))


# ----------------------------------------------------------------------
# PART -- Other shapes
# ----------------------------------------------------------------------

CH_ZOME = Chapter(
    number=56, ref="zome", strand="explain",
    title="A Zome Is Not a Piece of a Sphere",
    deck="Swept from a star of directions instead of subdivided from a "
         "solid -- which is why every panel comes out flat, guaranteed",
    derives=("two_v_demo.zome_geometry",),
    pages=(
        _p("opener", "A zome is not a piece of a sphere",
           "The other way to make a round building.", words=500,
           figures=(_f("plate-zome-what",
                       "A zome is not a piece of a sphere."),)),
        _p("text", "Every panel flat, guaranteed",
           "What the sweep buys and what it costs.", words=420),
        _p("text", "The famous one-panel zome",
           "Where the golden ratio is the design rather than a "
           "coincidence.", words=440,
           figures=(_f("plate-zome-golden",
                       "The famous one-panel zome."),)),
        _p("text", "Against a geodesic dome",
           "The comparison, counted.", words=380,
           figures=(_f("plate-zome-versus",
                       "Zome against geodesic dome."),)),
    ))

CH_HEX = Chapter(
    number=59, ref="hex", strand="explain",
    title="Exactly Twelve Pentagons, Always",
    deck="A sheet of hexagons will not curve. Curvature is bought with "
         "missing angle, and the price is always twelve pentagons",
    derives=("two_v_demo.hex_geometry",),
    pages=(
        _p("opener", "Exactly twelve pentagons, always",
           "The fact that decides every hexagonal dome.", words=480,
           figures=(_f("plate-hex-twelve",
                       "Exactly twelve pentagons. Always."),)),
        _p("text", "Where the panels stop being flat",
           "The warp, and what it costs.", words=420,
           figures=(_f("plate-hex-warp",
                       "The panels stop being flat."),)),
        _p("spread", "The two domes, side by side",
           "Hexagonal against geodesic.", words=360,
           figures=(_f("plate-hex-compare",
                       "The two domes, side by side."),)),
    ))

CH_ZOME_FLAT = Chapter(
    number=58, ref="zome_flat", strand="howto",
    title="A Zome Without a Bevel",
    deck="Four identical sticks to a panel, a miter at each end and no "
         "bevel anywhere -- and the gap on the outside that the method "
         "allows on purpose",
    derives=("two_v_demo.panel_method",),
    pages=(
        _p("opener", "A zome without a bevel",
           "The panel thinking, applied to a zome.", words=420,
           figures=(_f("plate-zome-model", "One stick, one miter, per row."),)),
        _p("text", "Four sticks in a pinwheel",
           "Why every stick in a row is the same stick.", words=380,
           figures=(_f("plate-zome-joint", "Both ends cut parallel; nothing bevelled."),)),
        _p("table", "Row by row",
           "Miters, folds and the gap, computed.", words=300),
        _p("text", "The gap, and what fills it",
           "Square edges, a V outside, and a wedge block.", words=360),
    ))

CH_PANEL_GEO = Chapter(
    number=60, ref="panel_geo", strand="explain",
    title="Three Frequency, Five Eighths",
    deck="The dome most bought plans build: a three-frequency sphere cut "
         "below its middle, a base that zig-zags, and two panel shapes",
    derives=("two_v_demo.panel_method",),
    pages=(
        _p("opener", "Three frequency, five eighths",
           "Another way to frame the same idea.", words=460,
           figures=(_f("plate-panel-two", "Two domes, framed two ways."),)),
        _p("text", "Three lengths, two kinds of point",
           "The sphere, subdivided three to an edge.", words=360,
           figures=(_f("plate-panel-sphere", "Three chords: A, B and C."),)),
        _p("text", "Why five eighths",
           "The cut, and the wall it buys.", words=380,
           figures=(_f("plate-panel-cut", "Cut below the middle."),)),
        _p("text", "A base that zig-zags",
           "Tapered sections, and level ones.", words=360,
           figures=(_f("plate-panel-base", "Ten tapered, five level."),)),
        _p("table", "Two panels, over and over",
           "The jig's two triangles.", words=300,
           figures=(_f("plate-panel-panels", "A pentagon panel and a hexagon panel."),)),
        _p("text", "A floor the shape of the base",
           "The radial deck.", words=360,
           figures=(_f("plate-panel-deck", "Joists to the corners, girders on the five-fold."),)),
    ))

CH_PANEL_JIG = Chapter(
    number=61, ref="panel_jig", strand="howto",
    title="A Panel on a Jig",
    deck="Rip, draw, rail, pinwheel, skin, raise: the framed-panel method "
         "start to finish, and the bevel no single saw setting gets right",
    derives=("two_v_demo.panel_method",),
    pages=(
        _p("opener", "A panel on a jig",
           "Every triangle its own small frame.", words=380),
        _p("text", "Finish, then rip in half",
           "A cut through the centre makes two copies.", words=320),
        _p("text", "Draw the jig with two arcs",
           "A trammel, a base line and three lengths.", words=360,
           figures=(_f("plate-panel-jig", "Where the arcs cross is the apex."),)),
        _p("text", "Sticks that turn like a pinwheel",
           "Why equal sides take different sticks.", words=420,
           figures=(_f("plate-panel-pinwheel", "Three sticks, six kinds in the dome."),)),
        _p("table", "Every stick, cut", "The cut list.", words=200),
        _p("text", "One bevel cannot be exact",
           "The number that does not flatter the method.", words=340,
           figures=(_f("plate-panel-bevel", "Red where one setting is furthest off."),)),
        _p("text", "Skin it in sections, raise it loose",
           "Sections, windows, gaskets, tape and anchors.", words=520,
           figures=(_f("plate-panel-skin", "One sheet per pentagon or hexagon."),
                    _f("plate-panel-window", "A spare frame on two hinges."))),
        _p("table", "Against the wedge dome", "What each method asks of you.", words=320),
    ))

CH_ZOME_BUILD = Chapter(
    number=57, ref="zome_build", strand="howto",
    title="Building a Zome, Ring by Ring",
    deck="Two numbers -- a count and a pitch -- give the parts list, the level "
         "rings, the templates, the hub schedule and the one repeated floor cut",
    derives=("two_v_demo.zome_geometry.polar_zonohedron",),
    pages=(
        _p("opener", "Counting the parts before you buy anything",
           "Panels, struts and hubs as formulas in the count.", words=380),
        _p("text", "The top comes to a point", "Why the roof closes on one vertex.",
           words=260),
        _p("text", "The hubs land on level rings", "No ring is approximate.", words=300),
        _p("table", "How many templates, and what pitch buys",
           "Separation sets the shape; pitch sets the height and nothing else.",
           words=380),
        _p("text", "Meeting the floor", "One angle, one length, all the way round.",
           words=280),
        _p("steps", "The cut list and the raise", "What the shop gets, and the order it goes up.",
           words=360),
    ))

PART_SHAPES = Part(
    number=10, title="Other Shapes",
    epigraph="A zome is swept, a hex dome is tiled, and a geodesic dome is "
             "subdivided. Three answers to one question about curvature.",
    promise="The two other round buildings this project solves, what each "
            "one is good at and what it costs against the dome in the rest "
            "of this book -- and the framed-panel method most bought dome "
            "plans use, solved again from this book's own geometry.",
    chapters=(CH_ZOME, CH_ZOME_BUILD, CH_ZOME_FLAT, CH_HEX, CH_PANEL_GEO, CH_PANEL_JIG))


# ----------------------------------------------------------------------
# PART -- The catalogue
# ----------------------------------------------------------------------

CH_FRAMING = Chapter(
    number=63, ref="framing", strand="explain",
    title="Hubs, or No Hubs",
    deck="The trade this whole method is an answer to, counted across "
         "twelve designs rather than argued",
    derives=("two_v_demo.hubless_geometry",),
    pages=(
        _p("opener", "Hubs, or no hubs",
           "The decision every dome builder makes, and what each side "
           "costs.", words=480,
           figures=(_f("plate-framing", "Hubs, or no hubs."),)),
        _p("text", "The cheapest wall is the one you never build",
           "Envelope per square foot of floor, measured.", words=420,
           figures=(_f("plate-efficiency",
                       "Envelope per floor, measured."),)),
    ))

CH_CREATOR = Chapter(
    number=64, ref="creator", strand="reference",
    title="Twelve Buildings, One Tool",
    deck="Every finish, floor division and fit-out the Dome Creator will "
         "put on a shell, priced against each other",
    derives=("materials.PANEL_TYPES", "wedge_book.alternatives.catalogue"),
    pages=(
        _p("opener", "Twelve buildings, one tool",
           "What the catalogue contains and how to read it.", words=420,
           figures=(_f("plate-economics",
                       "Every design in the catalogue, priced."),)),
        _p("table", "Finishes and floors",
           "The decisions that change how it looks and lives.", words=320,
           figures=(_f("plate-colours", "Sixteen finishes."),
                    _f("plate-floor-divisions",
                       "Four ways to divide a round floor."),
                    _f("plate-fitout", "The part nobody films."))),
    ))

CH_TWELVE = Chapter(
    number=65, ref="twelve", strand="reference",
    title="The Twelve, One at a Time",
    deck="Every design the Dome Creator ships, rebuilt from its preset and "
         "read off its own bill of materials -- from a seven-thousand-dollar "
         "garden dome to a hundred-thousand-dollar hangar",
    derives=("two_v_demo.creator_facts.design_rows", "two_v_demo.creator_facts.steps_catalogue"),
    pages=(
        _p("opener", "One engine, twelve buildings", "Why the spread is the point.", words=320),
        _p("table", "The catalogue, counted", "All twelve, fit-out included.", words=240),
        _p("text", "The timber four", "Workshop, glass loft, homestead, trunk lodge.", words=520),
        _p("text", "The other eight", "Aluminium, steel, rebar, concrete, mirror, canopy.",
           words=640),
        _p("text", "Check it yourself", "Load the preset; read the bill.", words=200),
    ))

CH_CHOICES = Chapter(
    number=66, ref="choices", strand="explain",
    title="What Every Choice Costs",
    deck="Which menu is the expensive one, where the hours go, what the fit-out "
         "adds, how many domes the menus make -- and what no model prices",
    derives=("two_v_demo.creator_facts.steps_price_drivers", "two_v_demo.creator_facts.steps_permutations",
             "two_v_demo.world_chatgpt_facts.steps_production"),
    pages=(
        _p("table", "What is declared and what is measured", "The only typed numbers.", words=300),
        _p("table", "Which menu is the expensive one", "One design, one menu at a time.",
           words=360),
        _p("table", "Six ways to frame one shell", "Including where the tool argues with itself.",
           words=320),
        _p("table", "Where the hours go", "Three hundred work steps, grouped.", words=300),
        _p("table", "The dome is the cheap part of the dome", "The fit-out, priced.", words=300),
        _p("table", "Size is a number you type", "Frequency, dials and scale.", words=360),
        _p("table", "How many domes that is", "Sixteen billion shells, and eight the dice picked.",
           words=360),
        _p("table", "Ten builds, one ledger", "And what the model refuses to hide.", words=360),
    ))

PART_CATALOGUE = Part(
    number=11, title="The Catalogue",
    epigraph="Twelve finished buildings, drawn by the tool that builds "
             "them, with the price of every choice in each one.",
    promise="The whole substitution space -- frame, section, panel, "
            "cladding, foundation, finish and fit-out -- the two arguments "
            "that decide most of it, the twelve designs one at a time, and "
            "what every choice in the tool costs.",
    chapters=(CH_ALTERNATIVES, CH_FRAMING, CH_CREATOR, CH_TWELVE, CH_CHOICES))


# ----------------------------------------------------------------------
# PART -- The stem cell
# ----------------------------------------------------------------------

CH_STEMCELL = Chapter(
    number=67, ref="stemcell", strand="explain",
    title="Why We Call It a Stem Cell",
    deck="One body, undifferentiated, that becomes fifteen different "
         "buildings depending on what you put in it",
    derives=("seed_model.FITOUT_ORDER", "seed_model.quote"),
    pages=(
        _p("opener", "Why we call it a stem cell",
           "The product idea, and why it is not a model range.", words=480,
           figures=(_f("plate-stem-cell",
                       "One body, many things it can become."),)),
        _p("text", "The socket at the top",
           "The utility column, and why everything plugs into one place.",
           words=460,
           figures=(_f("plate-slices", "The roof comes apart too."),)),
    ))

CH_CORE = Chapter(
    number=68, ref="core", strand="explain",
    title="Sink the Money Into the Part That Moves",
    deck="The utility core is thirty per cent of the dome and the only "
         "part that transfers -- so it is the part worth overbuilding",
    derives=("seed_model.core_parts", "seed_model.quote"),
    pages=(
        _p("opener", "Sink the money into the part that moves",
           "The central economic argument of the product line.", words=540,
           figures=(_f("plate-core-cost",
                       "What buying it once is worth."),),
           beats=("the core is 30 per cent of the dome's cost",
                  "it is the only assembly that is not shaped by this dome",
                  "so it outlives the shell it was bought for",
                  "which turns a purchase into a fixed asset")),
        _p("text", "What is actually in it",
           "Fourteen parts, five services, one penetration.", words=520),
        _p("text", "Moving it",
           "What a transfer costs and what it is worth.", words=420,
           figures=(_f("plate-system",
                       "This only works as a system."),)),
    ))

CH_SEEDS = Chapter(
    number=70, ref="seeds", strand="reference",
    title="Fifteen Buildings From One Body",
    deck="The catalogue a homestead wants second, priced from the same "
         "frame and the same core",
    derives=("seed_model.FITOUT_ORDER",),
    pages=(
        _p("opener", "Fifteen buildings from one body",
           "The range, and what differentiates one from another.",
           words=420,
           figures=(_f("plate-seeds-priced",
                       "The catalogue, priced."),)),
        _p("table", "The catalogue", "Every structure, cheapest first.",
           words=300,
           figures=(_f("plate-ladder",
                       "How far down the ladder goes."),)),
        _p("text", "One building, fifteen stations",
           "The manufacturing view of the same nine processes.", words=400,
           figures=(_f("plate-line",
                       "One building, fifteen stations."),)),
    ))

CH_CORE_BUILD = Chapter(
    number=69, ref="core_build", strand="howto",
    title="Build One Utility Core",
    deck="Fourteen steps in five stages: drain first, water proved before anything "
         "electrical exists, power last into a core already known to be dry",
    derives=("two_v_demo.module_build",),
    pages=(
        _p("opener", "Build one utility core", "Why the core is the first thing to learn.",
           words=300),
        _p("table", "What has to be on the bench", "Nine tools, two of them the ones people skip.",
           words=280),
        _p("steps", "Drain, water, power", "In that order, and why.", words=620),
        _p("table", "Everything you buy for one", "Twenty-three lines, nothing exotic.", words=260),
        _p("text", "One core, every dome", "Seven hours, once.", words=200),
    ))

CH_TEN = Chapter(
    number=71, ref="ten", strand="explain",
    title="Ten Reasons This Shape",
    deck="Less skin for the same floor, nothing for the wind to push on, a parts list "
         "that does not grow with the house -- and the stem wall, brim and paint "
         "that fix what a bare dome gets wrong",
    derives=("two_v_demo.dome_advantage.advantages", "two_v_demo.dome_performance.ten_points"),
    pages=(
        _p("opener", "A house that costs what its parts cost", "The campaign's whole argument.",
           words=260),
        _p("text", "Same floor, less building", "Skin, triangles and wind.", words=420),
        _p("text", "Nine times the house, same parts list", "Flat rate, brackets, the first one.",
           words=380),
        _p("text", "Fixing what a dome gets wrong", "The pony wall, the brim, the hat.",
           words=420),
        _p("text", "What it costs to run", "Heating, cooling, and the paint.", words=360),
        _p("text", "One skeleton, many products", "The bones do not care.", words=240),
    ))

CH_ARTICLE = Chapter(
    number=72, ref="article", strand="explain",
    title="The Standard Article, and What the Money Is For",
    deck="Twelve thousand dollars with the invoice on the page, the four ways to build "
         "the same dome, running it on nothing, and two campaigns' asks as lists",
    derives=("seed_model.quote", "two_v_demo.dome_costing.build_variants",
             "two_v_demo.dome_costing.Startup"),
    pages=(
        _p("opener", "A house you can take apart", "The standard article.", words=320),
        _p("table", "Twelve thousand, and here is the invoice", "Built, marked up, stated.",
           words=320),
        _p("table", "Four ways to build the same dome", "Bare to everything, at the till.",
           words=300),
        _p("table", "Running it on nothing", "Panels and a bank against a measured draw.",
           words=320),
        _p("table", "What the money is for", "Two asks, both as lists.", words=420),
        _p("text", "Three kinds of people", "And every number a model you can run.", words=240),
    ))

PART_STEMCELL = Part(
    number=12, title="The Stem Cell",
    epigraph="Buy the plumbing once. The shell is the thing that grows, "
             "and the core is the thing that moves.",
    promise="The product line: one undifferentiated body, the utility core "
            "that is thirty per cent of it and outlives it, how to build "
            "one, the fifteen buildings it becomes, the ten reasons for the "
            "shape, and the standard article with its invoice and its asks.",
    chapters=(CH_STEMCELL, CH_CORE, CH_CORE_BUILD, CH_SEEDS, CH_TEN, CH_ARTICLE))


PARTS: tuple[Part, ...] = (PART_RIGHT, PART_MATHS, PART_STICK, PART_PANEL,
                           PART_SKIN, PART_WATER, PART_FLOOR, PART_ECON, PART_NETWORK, PART_SHAPES,
                           PART_CATALOGUE, PART_STEMCELL, PART_VARIATIONS,
                           PART_STYLE, PART_TOOLS)

BOOK = Book(title=TITLE, subtitle=SUBTITLE, front=FRONT, parts=PARTS,
            back=BACK)


def figure_keys() -> tuple[str, ...]:
    return tuple(fig.key for fig in BOOK.figures)


def validate_outline() -> None:
    """The outline is coherent, and its pictures exist."""
    from two_v_demo.book import STRANDS

    assert BOOK.title and BOOK.subtitle
    assert len(BOOK.parts) >= 6, len(BOOK.parts)

    numbers = [c.number for c in BOOK.chapters]
    assert numbers == sorted(numbers), numbers
    assert len(set(numbers)) == len(numbers), "two chapters share a number"
    refs = [c.key for c in BOOK.chapters]
    assert len(set(refs)) == len(refs), "two chapters share a ref"

    for chapter in BOOK.chapters:
        assert chapter.strand in STRANDS, (chapter.key, chapter.strand)
        assert chapter.deck, chapter.key
        assert chapter.pages, chapter.key
        assert chapter.words > 200, (chapter.key, chapter.words)
        for page in chapter.pages:
            assert page.purpose, (chapter.key, page.title)

    for part in BOOK.parts:
        assert part.epigraph, part.title
        assert part.promise, part.title
        assert part.chapters, part.title

    # The book's own argument, which is the reason it was rebuilt: Part 1
    # says the frame is the part you are allowed to get wrong. If that ever
    # stops being the opening claim, this is a different book.
    assert "allowed to get wrong" in PART_RIGHT.epigraph, PART_RIGHT.epigraph
    assert BOOK.parts[0] is PART_RIGHT

    # Every picture named has to be a file somebody can print.
    missing = [key for key in figure_keys()
               if not (FIGURE_DIR / f"{key}.png").is_file()]
    assert not missing, (
        f"{len(missing)} figures named in the outline are not rendered: "
        f"{missing}")


def main(argv: list[str] | None = None) -> int:
    validate_outline()
    print(f"{BOOK.title} -- {BOOK.subtitle}")
    print(f"{len(BOOK.chapters)} chapters, {BOOK.words:,} words, "
          f"about {BOOK.sheets} pages, {len(BOOK.figures)} figures")
    for part in BOOK.parts:
        print(f"\nPart {part.number}: {part.title}  "
              f"({len(part.chapters)} ch, {part.words:,} w)")
        for chapter in part.chapters:
            print(f"   {chapter.number:2d}. {chapter.title[:46]:46s} "
                  f"{chapter.strand:9s} {chapter.words:>5,}w "
                  f"{len(chapter.figures)} fig")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
