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
* ``book_wedge/manuscript/`` -- the prose, one Markdown file per chapter.
"""

from __future__ import annotations

from pathlib import Path

from two_v_demo.book import Book, Chapter, Figure, Matter, Page, Part

from . import store

ROOT = store.ROOT
MANUSCRIPT_DIR = store.BOOK_DIR / "manuscript"
FIGURE_DIR = store.BOOK_DIR / "figures"
EXPORT_DIR = ROOT / "deliverables" / "book"
STEM = "the-wedge-method"

TITLE = "The Wedge Method"
SUBTITLE = ("Let the frame be lumpy. Get the skin and the floor right. "
            "A dome from split logs, and the two layers that decide "
            "whether it lasts")


# ----------------------------------------------------------------------
# Shorthand, so the outline below reads as an outline
# ----------------------------------------------------------------------

def _p(kind: str, title: str, purpose: str, words: int = 0,
       figures: tuple[Figure, ...] = (), beats: tuple[str, ...] = ()) -> Page:
    return Page(kind=kind, title=title, purpose=purpose, words=words,
                figures=figures, beats=beats)


def _f(key: str, caption: str, source: str = "prerendered",
       full_page: bool = False, note: str = "", **spec) -> Figure:
    """A picture already on disk in ``book_wedge/figures``.

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

PART_RIGHT = Part(
    number=1, title="What Actually Has to Be Right",
    epigraph="A dome is a frame, a skin and a floor -- and the frame is the "
             "part you are allowed to get wrong.",
    promise="Three chapters that invert the usual advice, and one practical "
            "consequence: build the frame loose and the two layers that "
            "matter stay changeable for the life of the building.",
    chapters=(CH_LUMPY, CH_SILENT_KILLER, CH_HOTSWAP))


# ----------------------------------------------------------------------
# PART 2 -- The stick
# ----------------------------------------------------------------------

CH_SPLIT = Chapter(
    number=9, ref="split", strand="story",
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
    number=10, ref="member", strand="explain",
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
    number=11, ref="two_lengths", strand="howto",
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

PART_STICK = Part(
    number=3, title="The Stick",
    epigraph="Every radius of a round log is the same as every other. "
             "That is the whole trick, and the tree held the tolerance.",
    promise="How a standing tree becomes 120 structural members, what a "
            "45-degree sector is, and the two lengths you actually cut.",
    chapters=(CH_SPLIT, CH_MEMBER, CH_TWO_LENGTHS))


# ----------------------------------------------------------------------
# PART 3 -- The panel
# ----------------------------------------------------------------------

CH_PINWHEEL = Chapter(
    number=12, ref="pinwheel", strand="explain",
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

CH_NINE = Chapter(
    number=13, ref="nine", strand="explain",
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
    number=14, ref="jig", strand="howto",
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

PART_PANEL = Part(
    number=4, title="The Panel",
    epigraph="Forty panels come off one board, and nothing on the board is "
             "adjusted between them. Panel forty is panel one.",
    promise="The joint that removes the hub, the nine processes that make "
            "the whole shop, and the one fixture that makes forty panels "
            "the same.",
    chapters=(CH_PINWHEEL, CH_NINE, CH_JIG))


# ----------------------------------------------------------------------
# PART 4 -- The skin, which is the part that matters
# ----------------------------------------------------------------------

CH_RAISE = Chapter(
    number=15, ref="raise", strand="howto",
    title="Raising It",
    deck="Ten panels on the ring, thirty above them, and five around the "
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
    number=16, ref="one_layer", strand="explain",
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
    number=17, ref="hats", strand="explain",
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

PART_SKIN = Part(
    number=5, title="The Skin",
    epigraph="A frame that is out by an inch stands for fifty years. A skin "
             "that leaks for one winter takes the frame with it.",
    promise="Raising the shell, the single watertight layer over it, and the "
            "hats that go on afterwards -- the part of the building this "
            "book says matters most.",
    chapters=(CH_RAISE, CH_ONE_LAYER, CH_HATS))


# ----------------------------------------------------------------------
# PART 5 -- The floor and the ground
# ----------------------------------------------------------------------

CH_FLOOR = Chapter(
    number=18, ref="floor", strand="howto",
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
    number=19, ref="pad", strand="explain",
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

PART_FLOOR = Part(
    number=6, title="The Floor and the Ground",
    epigraph="Everything you own sits on the floor, and the ground is the "
             "one part of the building you cannot take with you.",
    promise="The second thing that has to be right, the five ways to build "
            "it, and the argument for standing on somebody else's ground.",
    chapters=(CH_FLOOR, CH_PAD))


# ----------------------------------------------------------------------
# PART 6 -- The network
# ----------------------------------------------------------------------

CH_NETWORK = Chapter(
    number=20, ref="network", strand="explain",
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

PART_NETWORK = Part(
    number=7, title="The Network",
    epigraph="Own the building. Rent the ground. Move when you want to, and "
             "leave a platform behind rather than a house.",
    promise="One chapter, the economics of a pad network from both sides of "
            "it: what the dome owner saves, what the landowner earns, and "
            "what would have to be true for either.",
    chapters=(CH_NETWORK,))


# ----------------------------------------------------------------------
# PART 7 -- Variations
# ----------------------------------------------------------------------

CH_ALTERNATIVES = Chapter(
    number=23, ref="alternatives", strand="reference",
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
    number=29, ref="floating", strand="explain",
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

PART_VARIATIONS = Part(
    number=11, title="Variations",
    epigraph="The same frame can wear more than one roof, stand on more than "
             "one ground, and hang from nothing at all.",
    promise="The one variation that is a design possibility rather than a "
            "tested build, priced and explicitly not rated.",
    chapters=(CH_FLOATING,))


# ----------------------------------------------------------------------
# PART 8 -- The tools
# ----------------------------------------------------------------------

CH_TOOLING = Chapter(
    number=30, ref="tooling", strand="reference",
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
    number=31, ref="worlds", strand="reference",
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

PART_TOOLS = Part(
    number=12, title="The Tools",
    epigraph="Every number in this book came out of a program about a second "
             "before it reached the page. Here are the programs.",
    promise="What ships with this book: the solver, the worlds, the cost "
            "model and the calculators, with what each is for and how to "
            "drive it.",
    chapters=(CH_TOOLING, CH_WORLDS))


# ----------------------------------------------------------------------
# Front and back
# ----------------------------------------------------------------------

FRONT: tuple[Matter, ...] = (
    Matter("title", "Title page", (
        _p("text", "Title page", "Title, subtitle and the one-line claim.",
           words=120),
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
    number=4, ref="triangles", strand="explain",
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
    number=5, ref="phi", strand="explain",
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

CH_FOUR_WAYS = Chapter(
    number=6, ref="four_ways", strand="explain",
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
    number=7, ref="hemisphere", strand="explain",
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
    number=8, ref="size", strand="howto",
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
    chapters=(CH_TRIANGLES, CH_PHI, CH_FOUR_WAYS, CH_HEMISPHERE, CH_SIZE))


# ----------------------------------------------------------------------
# PART -- Other shapes
# ----------------------------------------------------------------------

CH_ZOME = Chapter(
    number=21, ref="zome", strand="explain",
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
    number=22, ref="hex", strand="explain",
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

PART_SHAPES = Part(
    number=8, title="Other Shapes",
    epigraph="A zome is swept, a hex dome is tiled, and a geodesic dome is "
             "subdivided. Three answers to one question about curvature.",
    promise="The two other round buildings this project solves, what each "
            "one is good at, and what it costs against the dome in the "
            "rest of this book.",
    chapters=(CH_ZOME, CH_HEX))


# ----------------------------------------------------------------------
# PART -- The catalogue
# ----------------------------------------------------------------------

CH_FRAMING = Chapter(
    number=24, ref="framing", strand="explain",
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
    number=25, ref="creator", strand="reference",
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

PART_CATALOGUE = Part(
    number=9, title="The Catalogue",
    epigraph="Twelve finished buildings, drawn by the tool that builds "
             "them, with the price of every choice in each one.",
    promise="The whole substitution space -- frame, section, panel, "
            "cladding, foundation, finish and fit-out -- and the two "
            "arguments that decide most of it.",
    chapters=(CH_ALTERNATIVES, CH_FRAMING, CH_CREATOR))


# ----------------------------------------------------------------------
# PART -- The stem cell
# ----------------------------------------------------------------------

CH_STEMCELL = Chapter(
    number=26, ref="stemcell", strand="explain",
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
    number=27, ref="core", strand="explain",
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
    number=28, ref="seeds", strand="reference",
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

PART_STEMCELL = Part(
    number=10, title="The Stem Cell",
    epigraph="Buy the plumbing once. The shell is the thing that grows, "
             "and the core is the thing that moves.",
    promise="The product line: one undifferentiated body, the utility core "
            "that is thirty per cent of it and outlives it, and the "
            "fifteen buildings it becomes.",
    chapters=(CH_STEMCELL, CH_CORE, CH_SEEDS))


PARTS: tuple[Part, ...] = (PART_RIGHT, PART_MATHS, PART_STICK, PART_PANEL,
                           PART_SKIN, PART_FLOOR, PART_NETWORK, PART_SHAPES,
                           PART_CATALOGUE, PART_STEMCELL, PART_VARIATIONS,
                           PART_TOOLS)

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
