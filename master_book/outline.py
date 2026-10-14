"""The Master Edition, as a structure: six rungs, twelve threads, two volumes.

THE IDEA

The two books this project is writing each tell the whole method once, at
one depth. This edition tells it six times, at six depths, so that a family
can climb it:

* a **rung** is a depth -- from a story read aloud at bedtime to the
  experiments nobody has run yet. Every rung tells the *whole* idea, start to
  finish, so a reader can stop on any rung and still have the whole thing;
* a **thread** is one idea -- the tree, the split, the triangle -- followed
  up through every rung. A reader who wants one idea can climb its thread
  alone and skip everything else;
* every chapter carries the **three reads** the first book was built on --
  the story, the doing, and the why -- as labelled boxes, so a reader can
  take one strand across the whole book.

So the book can be read down a rung, up a thread, or along a strand, in any
order: that is what "asynchronous" means here, and it is why every chapter
ends with the way down, the way up and the way to everything else on its
thread.

Rungs one to three are written for this edition. Rungs four to six are
reading routes: short cards that say what the thread becomes at that depth
and then send the reader, in order, to the chapters of the two volumes that
do it in full. The volumes are bound in whole, unchanged, behind the rungs.

Chapters are named by stable references into the two books' own outlines
(``wedge_book.outline`` and ``two_v_demo.book``), never by number, so a
chapter inserted into either book cannot leave this edition pointing at the
wrong page.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOK_DIR = ROOT / "books/master-edition"
MANUSCRIPT_DIR = BOOK_DIR / "manuscript"
COVER_DIR = BOOK_DIR / "cover"
EXPORT_DIR = ROOT / "deliverables" / "book"
STEM = "the-40-hour-cabin-master-edition"

TITLE = "The 40 Hour Cabin"
SUBTITLE = "Master Edition"
STRAP = "Six reads of one idea, from a bedtime story to the frontier -- with both books inside"
AUTHOR = "Donovan Zeanah"


# ----------------------------------------------------------------------
# The twelve threads
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Thread:
    number: int
    key: str
    name: str
    idea: str
    """The thread's one-line idea, the same at every rung."""


THREADS: tuple[Thread, ...] = (
    Thread(1, "tree", "The Tree", "Wood that is already standing"),
    Thread(2, "split", "The Split", "Eight from one"),
    Thread(3, "triangle", "The Triangle", "The shape that will not wobble"),
    Thread(4, "dome", "The Dome", "A ball of triangles, cut in half"),
    Thread(5, "joint", "The Joint", "Nothing meets at the corner"),
    Thread(6, "panel", "The Panel", "Build it flat, forty times"),
    Thread(7, "raise", "The Raising", "Up it goes"),
    Thread(8, "skin", "The Skin", "Keep the weather out"),
    Thread(9, "ground", "The Ground", "Where it stands"),
    Thread(10, "uses", "The Uses", "One body, many buildings"),
    Thread(11, "count", "The Count", "Hours, dollars, and what we know"),
    Thread(12, "care", "Taking Care", "Who holds the saw"),
)
THREAD = {t.key: t for t in THREADS}


# ----------------------------------------------------------------------
# The six rungs and their milestones
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Milestone:
    key: str
    title: str
    who: str
    time: str
    need: str
    done_when: str


@dataclass(frozen=True)
class Rung:
    number: int
    key: str
    title: str
    verb: str
    who: str
    time: str
    need: str
    promise: str
    ready: str
    milestones: tuple[Milestone, ...]
    written: bool
    """True for the rungs written in full here; False for the reading routes."""

    @property
    def anchor(self) -> str:
        return f"rung{self.number}"


RUNGS: tuple[Rung, ...] = (
    Rung(1, "wonder", "Read It Together", "Wonder",
         who="A grown-up reading aloud with a child of four or more -- or anyone "
             "who wants the whole idea in twenty minutes.",
         time="About ten minutes a chapter: twelve bedtimes.",
         need="This book, and things already in the house.",
         promise="Tell the whole story of a house made from a tree: where the wood "
                 "comes from, why triangles, how it goes up, and what it can become.",
         ready="Anyone is ready. This rung is the front door.",
         milestones=(
             Milestone("m-walk", "The wonder walk",
                       "Everyone", "An afternoon", "Shoes",
                       "You have found three triangles holding something up in your "
                       "house, and one fallen tree outside, and said why each one "
                       "matters."),
             Milestone("m-twelve", "Twelve bedtimes",
                       "A grown-up and a child", "Twelve evenings", "This rung",
                       "Every chapter of this rung has been read aloud and every "
                       "“Try it together” has been tried."),
         ),
         written=True),
    Rung(2, "understand", "Make It Small", "Understand",
         who="Children of eight or more with a grown-up, and any beginner who "
             "learns with their hands.",
         time="An hour or two a chapter; a long weekend for the whole rung.",
         need="Paper, scissors, tape, straws, a ruler, string -- and an adult for "
              "anything sharp.",
         promise="Build the whole idea at kitchen-table size, and understand why each "
                 "part is the way it is.",
         ready="You can tell the story of rung one in your own words.",
         milestones=(
             Milestone("m-paper", "The paper dome",
                       "A child with a grown-up", "Two hours",
                       "The two template pages, scissors, tape",
                       "All forty triangles are taped into one dome that stands on "
                       "the table by itself, and you can point to a five-way corner "
                       "and a six-way corner."),
             Milestone("m-straw", "The straw dome",
                       "A family", "An afternoon",
                       "Straws cut to two lengths, pipe cleaners or tape",
                       "The straw dome stands, every straw is one of the two "
                       "lengths, and pushing on it does not fold it."),
             Milestone("m-eight", "Eight from one",
                       "Everyone", "One snack", "Something round to share",
                       "Something round has been cut into eight equal wedges by "
                       "halving it three times, and nothing was thrown away."),
         ),
         written=True),
    Rung(3, "plan", "Plan It", "Plan",
         who="Teenagers and adults deciding whether, what and how big to build.",
         time="An evening a chapter; a month of evenings for a real plan.",
         need="A tape measure, a notebook, a calculator, and somebody to argue with.",
         promise="Turn your own trees, your own ground and your own purpose into a "
                 "one-page plan: a size, a cut list, a calendar, a budget and a "
                 "safety plan.",
         ready="You have built the paper dome and can say why it has two kinds of "
               "triangle.",
         milestones=(
             Milestone("m-tree", "Measure a real tree",
                       "A teenager or adult", "An hour outdoors",
                       "A tape, string, a notebook",
                       "You have the butt, the top and the straight length of a real "
                       "trunk, and the number of struts it would give."),
             Milestone("m-plan", "The one-page plan",
                       "The family together", "A month of evenings",
                       "The twelve worksheets in this rung",
                       "All twelve worksheets are filled in, and somebody who was not "
                       "in the room can read the plan and say what you are building, "
                       "how big, by when, for how much and how safely."),
         ),
         written=True),
    Rung(4, "build", "Build It", "Build",
         who="Adults with tools, training and help -- never alone at the saw.",
         time="A fortnight of part days for the frame; a season for the rest.",
         need="The plan from rung three, a chainsaw and its safety gear, a jig, "
              "and the two volumes behind these cards.",
         promise="Raise a real frame from your own trees, and close it against the "
                 "weather.",
         ready="Your one-page plan is finished, your safety plan is signed by the "
               "people who will follow it, and an engineer and your building "
               "department have seen what you mean to build.",
         milestones=(
             Milestone("m-panel", "One true panel",
                       "The builder", "A day", "A jig and three members",
                       "A full-size panel comes off the jig and matches its drawing "
                       "within a pencil line."),
             Milestone("m-frame", "The frame stands",
                       "The builder and a helper", "A fortnight",
                       "Forty panels, props, the keys",
                       "Forty panels stand closed as one frame with nothing holding "
                       "them but each other."),
             Milestone("m-dry", "Weathertight",
                       "The family", "A season", "One watertight layer",
                       "A night of rain leaves the inside dry."),
         ),
         written=False),
    Rung(5, "design", "Make It Yours", "Design",
         who="Anyone who has understood the reference build and wants a different "
             "one: another size, another skin, another use.",
         time="As long as you like. This rung is a catalogue, not a schedule.",
         need="The price lists and catalogues in Volume A, and an idea.",
         promise="Design and price your own building on the same frame -- or decide, "
                 "with the numbers up, that a different frame suits you better.",
         ready="You know which parts of the reference build you would keep, and why.",
         milestones=(
             Milestone("m-design", "A costed design of your own",
                       "A family or a maker", "A few evenings",
                       "The catalogues and price lists",
                       "Your design has a size, a skin, a ground, a use and a price "
                       "built line by line from the book's own tables."),
             Milestone("m-show", "Show it",
                       "Anyone", "An evening", "A drawing, a model or a render",
                       "Somebody else can look at your design and tell you what it "
                       "is for."),
         ),
         written=False),
    Rung(6, "experiment", "Push It Further", "Experiment",
         who="Builders, makers, students and engineers who want to find out what "
             "nobody has measured yet.",
         time="A season or a year -- an experiment is finished when its result is "
              "published, whichever way it came out.",
         need="Something built, a notebook, and the honesty to print the number "
              "that does not help.",
         promise="Run one of the open experiments this project names, and publish the "
                 "result so the next family starts from it.",
         ready="You have built something on rung two or four and you want to know "
               "more than the books can tell you.",
         milestones=(
             Milestone("m-experiment", "One experiment, published",
                       "A builder or a class", "A season",
                       "A built thing and a logbook",
                       "Your measurement, your method and your conclusion are "
                       "written down where somebody else can repeat them."),
             Milestone("m-teach", "Teach it",
                       "Anyone who has climbed this far", "An afternoon",
                       "A friend and this book",
                       "Somebody you taught has built one panel, or read rung one "
                       "aloud to somebody else."),
         ),
         written=False),
)
RUNG = {r.number: r for r in RUNGS}


# ----------------------------------------------------------------------
# The cells: one rung, one thread
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Cell:
    rung: int
    thread: str
    title: str
    deck: str
    short: str
    """The few words the map prints in its grid."""
    figure: str = ""
    """A figure key. ``A:`` or ``B:`` picks the volume whose pictures it is
    from; unprefixed means the Complete Edition's print figures."""
    vol_a: tuple[str, ...] = ()
    """Complete Edition chapter refs, in reading order. ``front:engineer`` is
    that volume's Engineer's Note."""
    vol_b: tuple[str, ...] = ()
    """Amazon paperback chapter refs, in reading order."""

    @property
    def anchor(self) -> str:
        return f"r{self.rung}-{self.thread}"

    @property
    def thread_obj(self) -> Thread:
        return THREAD[self.thread]

    @property
    def path(self) -> Path:
        t = THREAD[self.thread]
        return MANUSCRIPT_DIR / f"rung{self.rung}" / f"{t.number:02d}-{t.key}.md"


def _row(rung: int, *cells: tuple) -> tuple[Cell, ...]:
    out = []
    for thread, (title, deck, short, *rest) in zip(THREADS, cells):
        figure = rest[0] if rest else ""
        vol_a = rest[1] if len(rest) > 1 else ()
        vol_b = rest[2] if len(rest) > 2 else ()
        out.append(Cell(rung, thread.key, title, deck, short, figure, vol_a, vol_b))
    return tuple(out)


RUNG_1 = _row(
    1,
    ("The Tree That Fell Down",
     "A storm, a pine on the ground, and a question nobody had asked",
     "The fallen tree", "A:plate-one-log|The trunk on the ground, with the saw beside it."),
    ("Cut It Like a Cake",
     "Half, half again, and half once more -- and every piece the same",
     "Like a cake", "A:plate-round-log-corners|Eight wedges from one round, beside the squares a mill would cut from it."),
    ("The Shape That Will Not Wobble",
     "Push a square and it leans; push a triangle and it holds",
     "No wobble", "A:plate-why-triangles|A square leans over. A triangle cannot."),
    ("A Ball Made of Triangles",
     "Twenty triangles make a ball, a few more make it round, and half of it "
     "is a house",
     "A ball, halved", "A:plate-hemisphere|Half a ball made of triangles: a house."),
    ("Holding Hands Around the Corner",
     "Three sticks, no knot in the middle, and a corner left empty on purpose",
     "Hands, not knots", "B:pinwheel-exploded|Three sticks, each end resting on the side of the next."),
    ("Forty Triangles on a Table",
     "Build every piece flat, on one table, the same way every time",
     "Forty on a table", "A:plate-forty-frames|Forty triangles, each one built flat on the ground first."),
    ("Up, Up, Up",
     "The bottom ring first, then the next, then the very top",
     "Up it goes", "A:plate-sky-apex|The author's way: the dome built up in the air between the trees."),
    ("A Coat for the Rain",
     "One coat that keeps the water out, and soft warm layers underneath",
     "A raincoat", "A:plate-shower-cap|One coat to keep the rain out, and warm layers underneath."),
    ("A Good Place to Stand",
     "A house is only as steady as the ground under its ring",
     "Good ground", "A:plate-the-pad|A level ring of good ground for the dome to stand on."),
    ("What Will It Be?",
     "The same round frame can be a bedroom, a workshop, a greenhouse or a sauna",
     "What it becomes", "A:plate-seeds-priced|The same dome, built for different jobs."),
    ("Counting the Hours",
     "How long a house takes, and why counting honestly matters",
     "Counting hours", "A:plate-why-hour|How much house an hour of work can buy."),
    ("Grown-Up Jobs and Helper Jobs",
     "The saw is a grown-up's job; the counting, sorting and painting are yours",
     "Who does what", "A:plate-fell-line|Where a tree falls is planned before the first cut."),
)

RUNG_2 = _row(
    2,
    ("Measure a Tree",
     "Three numbers -- the fat end, the thin end and the straight length -- "
     "and a string to find them",
     "Measure a tree", "B:tree-measured|Volume B's worked tree: fat at the butt, thinner at the top, cut into sections of one length."),
    ("Eight From One",
     "Halve something round three times, then try to cut squares out of it, "
     "and count what is left over",
     "Eight from one", "B:split-sequence|Halve, then quarter, then eighth: every cut through the middle."),
    ("The Wobble Test",
     "Paper strips and paper fasteners prove the oldest rule in building",
     "The wobble test", "B:racking-compare|The same push: the rectangle folds, the triangle cannot."),
    ("Build the Paper Dome",
     "Forty paper triangles in two shapes, cut from the template and taped "
     "into the dome itself",
     "The paper dome", "A:plate-two-classes|Every edge of the dome is one of two lengths, shown in two colours."),
    ("Craft-Stick Pinwheels",
     "Three sticks, each end resting on the next one's side, and the corner "
     "left empty",
     "Pinwheel sticks", "A:vertex-five|A corner of the real frame where five panels meet: nothing touches at the point."),
    ("A Jig From a Box",
     "Pins in cardboard make every triangle the same, and a ruler cannot",
     "A cardboard jig", "B:jig-labelled|A jig, labelled: the bench, the stops, the rails and the cut planes."),
    ("Raise It Ring by Ring",
     "The straw dome goes up from the bottom, one ring at a time, with props",
     "Ring by ring", "A:course-first|The first ring of panels, standing on its own."),
    ("The Raincoat Test",
     "A spray bottle shows why roofs overlap instead of trying to seal",
     "The raincoat test", "A:plate-quilt|Quilted layers inside, and one watertight cap over them all."),
    ("The Wobbly Table Test",
     "A dome on a bumpy floor, and the measurement that finds it",
     "The level ring", "B:ring-plan|The bottom ring from above: ten edges on one circle."),
    ("Draw Your Round Room",
     "Rings of headroom on a paper floor, and where the bed goes",
     "A round room", "A:plate-furnished|A round room, furnished from the middle out."),
    ("Time It and Count It",
     "Make five paper triangles against a clock, then work out forty",
     "Time it", ""),
    ("The Job Sorting Game",
     "Cards, gear and the one rule that has no exceptions",
     "Sorting jobs", ""),
)

RUNG_3 = _row(
    3,
    ("Your Trees, Measured",
     "From three numbers on a real trunk to the struts it gives and the dome "
     "it can make",
     "Your trees", "A:plate-yield|The same round, split and sawn: the wedges keep the corners a mill throws away."),
    ("The Splitting Plan",
     "Sections, sectors, sessions and fuel: the part of the work that is "
     "measured, not guessed",
     "Splitting plan", "B:recovery-compare|One log converted two ways, in Volume B's tree."),
    ("What Must Be Right, and What May Be Rough",
     "The frame forgives; the skin and the ground do not -- so plan the care "
     "where it counts",
     "Where care goes", "A:plate-lumpy-one|A frame with no two members alike, standing."),
    ("Choose Your Size",
     "One number decides the building, and the two books chose it two "
     "different ways",
     "Choose a size", "B:design-lookup|Volume B's lookup: pick a floor, read off the dome and the trees it takes."),
    ("Your Cut List",
     "Two chords, two cut lengths, three saw settings and two keys",
     "The cut list", "A:seam-section|One seam cut across: two members, and the key between them."),
    ("Plan the Jig and the Panel Run",
     "One bench, twelve stages, forty panels in two shapes",
     "The panel run", "A:the-jig|The jig the simulator models, with every stop that holds a member."),
    ("Choose How It Goes Up",
     "On blocks and props, or in the air between trees -- and who holds what",
     "How it goes up", "A:plate-sky-corners|The sky web: an X of rope between four trees, with the spiral over the footprint."),
    ("Choose the First Coat",
     "One watertight layer now, warm layers when the winters ask",
     "The first coat", "B:shell-ladder|Each quilted layer takes away a share of the winter's heating bill."),
    ("Choose the Ground",
     "Gravel, deck, piers, slab or a pad somebody else owns",
     "The ground", "A:plate-seven-foundations|Seven ways to stand a dome on the ground."),
    ("Choose What It Is For",
     "Fifteen buildings from one body, priced, and the utility buildings that "
     "pay for themselves",
     "What it is for", "A:plate-twelve-domes|Twelve finished designs from the same engine."),
    ("Your Clock and Your Budget",
     "The forty-hour clock, the whole build's hours, and the invoice line by "
     "line",
     "Clock and budget", "A:plate-the-invoice|The standard article: the skinned stem-cell dome, invoiced line by line."),
    ("Your Safety Plan",
     "Who signs off, who holds the saw, who stands where, and what is never "
     "done alone",
     "Safety plan", "B:felling-hinge|The hinge steers the tree: left whole, it holds the fall on its line."),
)

RUNG_4 = _row(
    4,
    ("Fell and Buck", "Put the trees on the ground and cut them to the one length",
     "Fell and buck", "",
     ("tree", "green"),
     ("days_one_and_two_felling", "days_three_and_four_bucking", "small_units")),
    ("Rip the Wedges", "The saw, the three passes and the stacked pile",
     "Rip the wedges", "",
     ("split", "saw", "member"),
     ("day_zero_the_saw", "split", "days_five_to_eight_ripping", "orientations")),
    ("Trust the Frame", "Why the frame forgives a rough stick, from the forces up",
     "Trust the frame", "",
     ("lumpy", "triangles"),
     ("triangles", "versus_board", "forces")),
    ("Solve Your Dome", "Size it from the dome you want or the tree you have, and check it both ways",
     "Solve the dome", "",
     ("hemisphere", "size", "two_lengths"),
     ("which_way", "method_a", "method_b", "round_trip", "worked_build", "numbers_say_no")),
    ("Cut the Joints", "The pinwheel, the butt cut, the long head and the key",
     "Cut the joints", "",
     ("pinwheel",),
     ("pinwheel", "seams", "connector", "butt_cut", "head_overfit", "flush_cutting_in_place",
      "where_error_goes")),
    ("Run the Jig", "One flat board, forty identical panels",
     "Run the jig", "",
     ("frames", "jig", "everypiece"),
     ("own_edge", "the_jig", "days_ten_to_twelve_forty_panels", "jig_reference", "panel_drawings")),
    ("Raise It", "Bottom ring first, props until the top closes",
     "Raise it", "",
     ("raise",),
     ("days_thirteen_and_fourteen_raising",)),
    ("Close the Shell", "One watertight layer, the seams, the water, the finish",
     "Close the shell", "",
     ("skin", "one_layer", "finish", "linseed"),
     ("closing_the_shell", "weather_and_water", "finishing")),
    ("Set the Ground", "The floor, the ring and what it all stands on",
     "Set the ground", "",
     ("floor", "pad"),
     ("the_footing_and_the_ring",)),
    ("Make It Livable", "Doors, windows, services and a round room to live in",
     "Make it livable", "",
     ("openings", "core_build"),
     ("openings", "round_room", "heat_power_and_the_small_systems")),
    ("Log Every Hour", "What the build cost in money, hours and the body",
     "Log every hour", "",
     ("nine", "body", "priced"),
     ("money", "the_hours")),
    ("The Rules at the Log", "Chainsaw, felling, ladders, lifts and trades",
     "The rules", "",
     ("front:engineer",),
     ("day_zero_the_saw", "days_one_and_two_felling", "building_with_other_people")),
)

RUNG_5 = _row(
    5,
    ("Other Trees, Other Sticks", "What changes with the species, the trunk and the market",
     "Other trees", "",
     ("tree_worth",),
     ("other_species_other_sections", "small_units")),
    ("Other Sections", "When your sticks are rectangles, tubes or bought",
     "Other sections", "",
     ("rectangles", "alternatives"),
     ("versus_board",)),
    ("Hubs or No Hubs", "The trade this method answers, and when the other side wins",
     "Hubs or none", "",
     ("framing", "hubbed"),
     ("forty_panels_one_hundred_and_twenty_members",)),
    ("Other Shapes and Sizes", "Frequencies, zomes, hexagons and the 3V panel dome",
     "Other shapes", "",
     ("size", "zome", "zome_build", "hex", "panel_geo"),
     ("frequencies",)),
    ("The Seam as a Service Channel", "Water and wire in the gap the key leaves",
     "The seam's uses", "",
     ("seam_module", "channel", "metal"),
     ("connector",)),
    ("Panels With a Purpose", "Doors, windows and panels that do a job",
     "Purposeful panels", "",
     ("openings", "zome_flat", "panel_jig"),
     ("openings",)),
    ("Hang It", "The owner's way: build it in the air between living trees",
     "Hang it", "",
     ("floating", "skyweb")),
    ("Style It", "Twelve styles, every skin, every cladding, priced",
     "Style it", "",
     ("hats", "stycabin", "stytwelve", "stymenus", "stygrid"),
     ("less_skin", "shell_ladder")),
    ("Pads and Platforms", "Ground you build once and lend to the next dome",
     "Pads", "",
     ("pad", "pad_kit"),
     ("pony_wall", "brim_gutter")),
    ("Fifteen Buildings From One Body", "The stem cell, its core and its catalogue",
     "Fifteen buildings", "",
     ("stemcell", "core", "seeds", "creator", "twelve", "choices"),
     ("round_room",)),
    ("Price It Item by Item", "Every line, every item, every package",
     "Price it", "",
     ("styprices", "bom", "article", "house_money"),
     ("money",)),
    ("Design It Safe", "What a design must hand to an engineer, and how",
     "Design safe", "",
     ("front:engineer", "hotswap"),
     ("building_with_other_people",)),
)

RUNG_6 = _row(
    6,
    ("Weigh Your Own Wood", "What a tree is worth, measured on your own trees",
     "Your own wood", "",
     ("tree_worth", "hands"),
     ("recovery",)),
    ("Time Your Own Split", "Your rate at the log, and what an hour there buys",
     "Your own rate", "",
     ("hour", "body"),
     ("recovery", "the_hours")),
    ("What the Ugly One Taught", "The frame that should not have stood, and why it did",
     "The ugly one", "",
     ("ugly", "franken"),
     ("the_frankendome", "the_v_bracket_afternoon")),
    ("Check the Geometry Yourself", "Derive the two lengths four ways and close the round trip",
     "Check the maths", "",
     ("phi", "subdivide", "four_ways"),
     ("round_trip",)),
    ("Run the Seam Climate", "Dew points, levels, drawers and plates -- the experiment in the gap",
     "Seam climate", "",
     ("dewpoint", "levels", "breathe", "desiccant", "ring")),
    ("Count Every Piece", "The software that numbers every piece and draws every picture",
     "Every piece", "",
     ("tooling", "worlds", "screen", "everypiece")),
    ("The Sky Web", "The winch, the web and the owner's weighed struts",
     "The sky web", "",
     ("skyweb", "floating")),
    ("Log a Winter", "The measurement this whole project is waiting for",
     "Log a winter", "",
     ("ring", "breathe"),
     ("shell_ladder",)),
    ("The Pad Network", "Hosts, tenants, resale -- proposed, priced, not yet built",
     "The network", "",
     ("network", "host", "tenant", "turns")),
    ("Who It Is For", "A home people can afford to start with -- and why this author cares",
     "Who it is for", "",
     ("why_me", "fuller", "empire")),
    ("Publish Your Numbers", "Real hours, real receipts, and the corrections",
     "Publish numbers", "",
     ("hour", "house_money"),
     ("the_hours", "what_i_would_do_differently")),
    ("Report the Near Misses", "Testing safely, and writing down what nearly went wrong",
     "Near misses", "",
     ("front:engineer",),
     ("what_i_would_do_differently",)),
)

CELLS: tuple[Cell, ...] = RUNG_1 + RUNG_2 + RUNG_3 + RUNG_4 + RUNG_5 + RUNG_6
CELL = {c.anchor: c for c in CELLS}


def cells_in_rung(rung: int) -> tuple[Cell, ...]:
    return tuple(c for c in CELLS if c.rung == rung)


def cells_in_thread(thread: str) -> tuple[Cell, ...]:
    return tuple(c for c in CELLS if c.thread == thread)


def cell(rung: int, thread: str) -> Cell:
    return CELL[f"r{rung}-{thread}"]


# ----------------------------------------------------------------------
# Front and back matter, and the reading paths
# ----------------------------------------------------------------------

FRONT_FILES = ("letter", "how-to-read")
BACK_FILES = ("two-domes", "what-to-check", "colophon")


@dataclass(frozen=True)
class Path_:
    key: str
    title: str
    who: str
    stops: tuple[str, ...]
    """Anchors, in order. ``r1-tree`` is a cell; ``a:split`` and ``b:split`` are
    volume chapters by ref; anything else is a named page of this edition."""


PATHS: tuple[Path_, ...] = (
    Path_("bedtime", "Twelve bedtimes",
          "A grown-up and a child, one chapter a night",
          tuple(f"r1-{t.key}" for t in THREADS)),
    Path_("weekend", "A weekend of models",
          "A family with paper, straws and tape",
          ("r2-split", "r2-triangle", "r2-dome", "r2-joint", "r2-panel", "r2-raise",
           "r2-skin")),
    Path_("tree", "We have a tree",
          "Somebody with standing timber, wondering what it could become",
          ("r1-tree", "r2-tree", "r3-tree", "r3-split", "r3-dome", "r3-joint",
           "r3-count", "r4-tree", "r4-split", "b:method_b")),
    Path_("purpose", "We need a building for something",
          "A family that knows what it needs and not yet how",
          ("r1-uses", "r2-uses", "r3-uses", "r3-ground", "r3-count", "r5-uses",
           "r5-count", "a:seeds")),
    Path_("funder", "Is this worth backing?",
          "A grant panel, a lender or a partner with fifteen minutes",
          ("letter", "r1-uses", "r3-count", "r3-care", "two-domes", "r6-uses",
           "r6-count", "a:why_me", "a:fuller")),
    Path_("veterans", "Veterans, and the crews that build with them",
          "A veteran, a crew leader, or a program that houses veterans",
          ("letter", "r3-care", "r4-tree", "r4-split", "r4-panel", "r4-raise", "r4-care",
           "r5-uses", "r5-ground", "r6-ground", "a:why_me")),
    Path_("engineer", "Check the maths",
          "An engineer, a teacher or a sceptic",
          ("r3-dome", "r3-joint", "a:subdivide", "a:four_ways", "b:round_trip",
           "two-domes", "r6-dome", "r6-joint")),
    Path_("safety", "Safety first",
          "Anyone about to pick up a tool",
          tuple(f"r{n}-care" for n in range(1, 7)) + ("a:front:engineer",)),
    Path_("checker", "A proof-reader's hour",
          "A friend asked to check the work",
          ("letter", "how", "r1-tree", "r2-dome", "r3-dome", "r3-count",
           "two-domes", "what-to-check", "feedback")),
)


def validate_outline() -> None:
    """The grid is whole: every rung has every thread, and every reference is
    to a chapter that exists in its volume."""
    from two_v_demo import book as volume_b
    from wedge_book import outline as volume_a

    assert len(THREADS) == 12 and len(RUNGS) == 6
    assert len(CELLS) == len(THREADS) * len(RUNGS), len(CELLS)
    for rung in RUNGS:
        got = [c.thread for c in cells_in_rung(rung.number)]
        assert got == [t.key for t in THREADS], (rung.number, got)
        assert rung.milestones, rung.number

    a_refs = {c.key for c in volume_a.BOOK.chapters}
    b_refs = {c.key for c in volume_b.BOOK.chapters}
    for c in CELLS:
        assert c.title and c.deck and c.short, c.anchor
        for ref in c.vol_a:
            assert ref == "front:engineer" or ref in a_refs, (c.anchor, ref)
        for ref in c.vol_b:
            assert ref in b_refs, (c.anchor, ref)
        if not RUNG[c.rung].written:
            assert c.vol_a or c.vol_b, f"{c.anchor} is a reading route with nowhere to go"
    for path in PATHS:
        for stop in path.stops:
            if stop.startswith("a:"):
                ref = stop[2:]
                assert ref == "front:engineer" or ref in a_refs, (path.key, stop)
            elif stop.startswith("b:"):
                assert stop[2:] in b_refs, (path.key, stop)
            elif stop.startswith("r") and "-" in stop:
                assert stop in CELL, (path.key, stop)
