"""The defined terms of the visual lexicon.

Each entry is a noun or phrase the subject is built from, written for someone who
has never built anything: what it is, in plain words; the figures that quantify it,
always as live tokens; and how a film shows it -- a codified visual object from
:mod:`two_v_demo.visual_objects`, a pictogram from :mod:`two_v_demo.icons`, and
where one exists, a painter a published film already uses.

Keys and aliases are lemmas, singular and lower case, the form
:mod:`two_v_demo.lexicon_words` reduces the scripts to, so the catalogue can count
how often each term is actually said and where.
"""

from __future__ import annotations

from .lexicon import Term


def _t(key, name, category, define, aliases=(), visual="", icon="", figures=(),
       scene="", see=()) -> Term:
    return Term(key, name, category, " ".join(define.split()), tuple(aliases),
                visual, icon, tuple(figures), scene, tuple(see))


TERMS: tuple[Term, ...] = (
    # ------------------------------------------------------------ the tree
    _t("tree", "Tree", "wood",
       """A standing pine: the raw material of the whole method. The book's tree
       has {{tree.usable_length_ft}} feet of straight trunk, {{tree.butt_diameter_in}}
       inches across at the butt and {{tree.top_diameter_in}} at the top.""",
       aliases=("pine", "standing tree"), visual="pine_tree", icon="pine",
       figures=("tree.usable_length_ft", "tree.butt_diameter_in",
                "tree.top_diameter_in"),
       scene="harvest:hv_harvest", see=("trunk", "felling")),
    _t("trunk", "Trunk", "wood",
       """The main stem of a tree, from the stump to the branches. Only its
       straight lower part becomes struts.""",
       aliases=("whole trunk", "usable trunk", "source trunk"), visual="pine_tree",
       figures=("tree.usable_length_ft",), see=("log", "taper")),
    _t("log", "Log", "wood",
       """A length of trunk once the tree is down and the branches are off.""",
       aliases=("split log",), visual="log_sections", icon="log",
       scene="harvest:hv_harvest", see=("section", "bucking")),
    _t("bark", "Bark", "wood",
       """The rough outer skin of a tree. On a wedge it stays on the outside face,
       the one that ends up facing the weather.""",
       visual="wedge_member", see=("bark face", "pith")),
    _t("bark face", "Bark face", "wood",
       """The curved outer face of a wedge, still wearing its bark or the
       outermost growth rings. It faces out of the dome.""",
       aliases=("curved bark",), visual="wedge_member", scene="wedge:wg_section",
       figures=("member.width_in",), see=("pith", "sawn face")),
    _t("pith", "Pith", "wood",
       """The soft thread of wood at the exact centre of a trunk. Every wedge has
       it as its sharp inner edge, pointing into the dome.""",
       visual="wedge_member", scene="wedge:wg_section", see=("bark face",)),
    _t("sawn face", "Sawn face", "wood",
       """One of the two flat faces a wedge gets from the rip cuts that split it.
       Flat enough for the end of the next member to bear against.""",
       aliases=("split face", "radial face", "flat face", "flat sawn face"),
       visual="wedge_member", scene="wedge:wg_section", see=("ripping",)),
    _t("grain", "Grain", "wood",
       """The direction the wood fibres run: along the trunk. A split follows it,
       which is why a split face comes out flat.""", see=("splitting",)),
    _t("knot", "Knot", "wood",
       """Where a branch grew out of the trunk: a hard, dark spot that weakens the
       wood around it.""", see=("defect",)),
    _t("defect", "Defect", "wood",
       """Anything that spoils a length of wood for structure: a knot, a bend, a
       crack. Short members limit what one defect can cost.""",
       aliases=("flaw", "bend"), scene="why:ww_bend", see=("knot", "section")),
    _t("taper", "Taper", "wood",
       """How a trunk narrows toward its top: here from
       {{tree.butt_diameter_in}} inches at the butt to {{tree.top_diameter_in}} at
       the top of the usable length.""",
       figures=("tree.butt_diameter_in", "tree.top_diameter_in"),
       visual="pine_tree"),
    _t("stump", "Stump", "wood",
       """What stays in the ground after felling, with the notch and the back cut
       still readable on its top.""", visual="pine_tree", see=("felling",)),
    _t("section", "Section", "wood",
       """One length of trunk, bucked to {{tree.section_length_ft}} feet. A tree
       gives {{tree.sections}} of them, and each splits into {{tree.sectors}}
       struts.""",
       aliases=("six-foot section", "foot section", "bucked section"),
       visual="log_sections", icon="slice",
       figures=("tree.section_length_ft", "tree.sections", "tree.sectors"),
       scene="harvest:hv_harvest", see=("bucking", "sector")),
    _t("sector", "Sector", "wood",
       """One of the equal pie-slice pieces a round section splits into:
       {{tree.sectors}} of them, {{tree.sector_angle_deg}} degrees each.""",
       aliases=("raw sector", "radial sector", "circular sector"),
       visual="section_disc", icon="split",
       figures=("tree.sectors", "tree.sector_angle_deg"),
       scene="wedge:wg_split", see=("wedge",)),
    _t("wedge", "Wedge", "wood",
       """A sector of a log used as a structural member without squaring it: two
       flat sawn faces, a curved bark face, and the pith as a sharp edge. This
       book's is {{member.width_in}} inches across the bark and
       {{member.depth_in}} deep.""",
       aliases=("raw wedge", "wedge strut", "wedge member", "wooden wedge"),
       visual="wedge_member", icon="wedge",
       figures=("member.width_in", "member.depth_in", "member.area_in2"),
       scene="wedge:wg_section", see=("sector", "member", "bark face")),
    _t("board", "Board", "wood",
       """A sawn rectangle of wood: what a mill makes, and what the wedge method
       does without.""", visual="board_2x4", icon="board",
       see=("two-by-four", "milling")),
    _t("two-by-four", "Two-by-four", "wood",
       """The commonest framing board, sold as two by four inches but dressed
       down to {{board.dressed_in2}} square inches of section. Its shelf price
       here is {{board.price_usd}} dollars.""",
       aliases=("2x4", "stud", "dressed 2x4", "dressed stud", "true two-by-four"),
       visual="board_2x4", icon="board",
       figures=("board.dressed_in2", "board.nominal_in2", "board.price_usd"),
       see=("board", "shelf price")),
    _t("dimensional lumber", "Dimensional lumber", "wood",
       """Boards sawn, dried and planed to standard sizes. The whole store-bought
       route exists to make it.""",
       aliases=("framing lumber", "milled lumber", "rectangular lumber"),
       visual="board_2x4", scene="why:ww_chain", see=("milling",)),
    _t("slab", "Slab", "wood",
       """The rounded outer strip a sawmill cuts off each side of a log to square
       it. Wood lost to shape, not to quality.""", scene="wedge:wg_mill",
       see=("cant", "milling")),
    _t("cant", "Cant", "wood",
       """The squared middle of a log once the slabs are off. Boards are sawn from
       it.""", scene="wedge:wg_mill", see=("slab",)),
    _t("offcut", "Offcut", "wood",
       """The piece left over when a length is cut from a longer one. A
       deliberately long head end leaves its error in the offcut.""",
       see=("head overfit",)),
    _t("sawdust", "Sawdust", "wood",
       """The chips a saw throws out of its cut. In a split, the kerf's sawdust is
       the only wood lost.""", visual="log_sections", see=("kerf",)),
    _t("cull", "Cull", "wood",
       """A board bought and then not used: bowed, twisted, wet or split. It is
       paid for anyway.""", scene="why:ww_store", see=("overhead",)),
    _t("woodlot", "Woodlot", "wood",
       """The patch of trees a builder can actually cut from. The method sizes the
       dome to what grows there.""", aliases=("forest", "woods"),
       see=("tree",)),
    _t("species", "Species", "wood",
       """The kind of tree. The method is worked out on pine; another species
       changes how strong the stick is, not the arithmetic.""", see=("tree",)),

    # ------------------------------------------------------------ members and joints
    _t("strut", "Strut", "members",
       """A straight member of a dome frame. An ordinary 2V hub dome has
       {{frame.edges}}; the panelised wedge dome has {{frame.members}}, because
       every panel keeps its own.""",
       aliases=("stick", "structural strut", "short strut", "long strut"),
       visual="timber_stick", figures=("frame.edges", "frame.members"),
       see=("member", "hub")),
    _t("member", "Member", "members",
       """Any structural piece of the frame. In the wedge dome every member is one
       raw wedge, and there are {{frame.members}} of them.""",
       aliases=("structural member", "wooden member", "wood member", "edge member"),
       visual="wedge_member", figures=("frame.members", "frame.members_per_panel"),
       see=("wedge", "panel")),
    _t("panel", "Panel", "members",
       """One triangle of the frame, built flat on the jig and finished before it
       is lifted. The hemisphere has {{frame.panels}}.""",
       aliases=("triangular panel", "triangular frame", "independent frame"),
       visual="wedge_shell", figures=("frame.panels",),
       scene="wedge:wg_explode", see=("pinwheel", "jig")),
    _t("hub", "Hub", "members",
       """A connector where several struts meet at one point. The ordinary 2V dome
       needs them; the wedge dome has none.""",
       aliases=("hub connector", "node connector", "node"), visual="hub_dome",
       see=("strut", "pinwheel")),
    _t("joint", "Joint", "members",
       """Where members meet. In a pinwheel panel every joint is one member's end
       pressed against the side of the next.""", aliases=("connection",),
       scene="why:ww_joinery", see=("pinwheel",)),
    _t("pinwheel", "Pinwheel joint", "members",
       """How a wedge panel's three members meet: each end butts into the side of
       the next, all the same way round, like the blades of a pinwheel. No end is
       mitred and nothing is shaved to a point.""",
       aliases=("pinwheel joint", "pinwheel member"), visual="wedge_shell",
       scene="wedge:wg_pinwheel", see=("panel", "butt cut")),
    _t("seam", "Seam", "members",
       """The line where two neighbouring panels meet. The hemisphere has
       {{frame.seams}}, and they close at only {{seam.distinct_angles}} different
       fold angles.""",
       aliases=("interior seam", "shared seam"), visual="solved_dome",
       figures=("frame.seams", "seam.distinct_angles"), scene="why:ww_fold",
       see=("seam key", "fold angle")),
    _t("seam key", "Seam key", "members",
       """The separate strip that sits in every seam between two panels' members
       and takes up the angle between them, so the wood never has to be cut to
       it. It can be a rigid spline, a rubber hose or a gasket,
       {{jig.gasket_in}} inches thick here.""",
       aliases=("key", "spline", "gasket", "rigid spline", "compressible gasket",
                "key profile"),
       visual="solved_dome", figures=("jig.gasket_in",), scene="wedge:wg_gasket",
       see=("seam",)),
    _t("v-bracket", "V bracket", "members",
       """A strip of scrap sheet metal folded into a V and screwed into two
       struts. It joined the frankendome's mismatched sticks.""",
       aliases=("v bracket", "bracket", "folded bracket"), scene="why:ww_vbracket",
       see=("frankendome",)),
    _t("head overfit", "Head overfit", "members",
       """Stock left {{jig.head_overfit_in}} inches long at a member's head end on
       purpose, so cutting error leaves as an offcut instead of building up around
       the triangle.""",
       aliases=("overfit",), figures=("jig.head_overfit_in",),
       scene="why:ww_flush", see=("flush-cut", "offcut")),
    _t("rim", "Rim", "members",
       """The bottom edge of the dome, where panels meet the base. Its
       {{frame.rim_edges}} edges join nothing.""",
       aliases=("rim edge",), figures=("frame.rim_edges",), see=("base ring",)),
    _t("keystone", "Keystone panel", "members",
       """A panel whose opening tapers because its wedges point outward, so it
       cannot fall through the frame.""", scene="why:ww_keystone",
       see=("orientation",)),
    _t("connector", "Connector", "members",
       """Any part that joins members: a hub, a bracket, a bolt plate. The size of
       the connector sets how much is cut off every strut.""",
       see=("connector deduction", "hub")),

    # ------------------------------------------------------------ geometry
    _t("dome", "Geodesic dome", "structure",
       """A roughly spherical shell built from triangles. The book's is half a
       sphere of {{frame.panels}} triangles, {{dome.diameter_ft}} feet across and
       {{dome.height_ft}} tall at the centre.""",
       aliases=("geodesic dome", "2v dome", "2v geodesic dome", "wedge dome",
                "geodesic shell"),
       visual="solved_dome", icon="dome",
       figures=("frame.panels", "dome.diameter_ft", "dome.height_ft"),
       scene="why:ww_realdome", see=("hemisphere", "shell")),
    _t("shell", "Shell", "structure",
       """The dome as one closed surface: the frame plus whatever covers it. A
       triangulated shell carries load as a whole.""",
       aliases=("triangulated shell", "whole shell", "curved shell"),
       visual="solved_dome", see=("dome", "network")),
    _t("frankendome", "Frankendome", "structure",
       """The author's first dome: {{frame.panels}} triangles of mismatched sticks
       held by V brackets. The failure that taught the wedge method.""",
       aliases=("franken-dome",), visual="hub_dome", scene="why:seg_franken_plain",
       see=("v-bracket",)),
    _t("hemisphere", "Hemisphere", "geometry",
       """Half a sphere. A 2V hemisphere is the dome this project builds.""",
       aliases=("2v hemisphere",), visual="hub_dome", see=("dome",)),
    _t("icosahedron", "Icosahedron", "geometry",
       """The twenty-faced regular solid every geodesic dome starts from. Its
       triangles are split and pushed out onto a sphere.""",
       scene="2v:icosahedron", see=("frequency",)),
    _t("frequency", "Frequency", "geometry",
       """How many pieces each edge of the starting icosahedron is split into. 2V
       means two, which leaves just two strut lengths.""",
       aliases=("2v", "2v frequency"), visual="hub_dome", scene="2v:midpoints",
       see=("icosahedron", "chord factor")),
    _t("chord factor", "Chord factor", "geometry",
       """The length of a strut when the sphere's radius is one. Multiply it by
       any real radius to get real lengths.""",
       scene="2v:classes", see=("radius", "cut list")),
    _t("golden ratio", "Golden ratio", "math",
       """Phi: the number that places an icosahedron's twelve corners. It is not
       the ratio of a 2V dome's two strut lengths, whatever is often said.""",
       aliases=("phi",), scene="2v:coordinates", see=("icosahedron",)),
    _t("triangle", "Triangle", "geometry",
       """The only shape that cannot change without changing a side's length,
       which is why every dome panel is one.""",
       aliases=("triangle shape",), scene="2v:rigidity", see=("racking",)),
    _t("pentagon", "Pentagon", "geometry",
       """A five-sided shape. Every closed cage of hexagons needs exactly twelve
       of them to curve round.""", see=("hexagon",)),
    _t("hexagon", "Hexagon", "geometry",
       """A six-sided shape. A sheet of them lies flat forever; only pentagons let
       it curve.""", see=("pentagon",)),
    _t("zome", "Zome", "geometry",
       """A dome swept from a star of directions rather than cut from a sphere.
       Its panels are flat rhombuses and it closes on a point.""",
       aliases=("polar zome",)),
    _t("vertex", "Vertex", "geometry",
       """A corner of the geometry, where edges meet. In the wedge dome no stick
       reaches one: the corners are reference points.""",
       aliases=("corner",), see=("edge",)),
    _t("edge", "Edge", "geometry",
       """A straight line between two corners of the geometry. The hemisphere has
       {{frame.edges}} unique edges, and the panelised frame puts two members on
       each interior one.""",
       aliases=("unique edge", "shared edge", "interior edge"),
       figures=("frame.edges", "edges.duplicated"), see=("member", "seam")),
    _t("radius", "Radius", "geometry",
       """The distance from the centre of the sphere to the shell. The book's dome
       has a radius of {{dome.radius_in}} inches, set by the tree.""",
       aliases=("sphere radius", "dome radius"), visual="dimension",
       figures=("dome.radius_in",), see=("chord factor",)),
    _t("fold angle", "Fold angle", "geometry",
       """The angle between two neighbouring panels at their seam. The wedge
       dome's seams take only {{seam.distinct_angles}}: {{seam.fold_a_deg}} and
       {{seam.fold_b_deg}} degrees.""",
       aliases=("dihedral", "fold", "panel fold"), visual="solved_dome",
       figures=("seam.distinct_angles", "seam.fold_a_deg", "seam.fold_b_deg"),
       scene="why:ww_fold", see=("seam key",)),
    _t("bevel", "Bevel", "geometry",
       """An angle cut along the length of a board so that two faces meet at the
       fold they need.""", see=("mitre", "fold angle")),
    _t("mitre", "Mitre", "geometry",
       """An angle cut across the end of a board. The pinwheel panel needs
       none.""", aliases=("miter",), see=("pinwheel",)),
    _t("cross-section", "Cross-section", "geometry",
       """The shape you see when a member is cut straight across. A wedge's is a
       slice of pie; a board's is a rectangle.""",
       visual="section_disc", scene="wedge:wg_section", see=("sector",)),
    _t("orientation", "Orientation", "geometry",
       """Which of the four ways a wedge is turned in its panel. Each one gives
       the frame a different feature.""", visual="solved_dome",
       scene="why:ww_turn", see=("keystone",)),
    _t("network", "Triangulated network", "geometry",
       """The web of members that carries load together, so no single stick has to
       carry it alone.""", aliases=("lattice", "triangulated lattice"),
       scene="2v:rigidity", see=("shell",)),
    _t("central angle", "Central angle", "geometry",
       """The angle a strut spans as seen from the sphere's centre. Every end cut
       follows from it.""", see=("end cut",)),
    _t("unit sphere", "Unit sphere", "geometry",
       """A sphere of radius one. Working on it first turns every length into a
       factor that scales to any size.""", scene="2v:icosahedron",
       see=("chord factor",)),
    _t("projected midpoint", "Projected midpoint", "geometry",
       """The middle of an icosahedron's edge, pushed out onto the sphere. That one
       move is what creates the second strut length.""",
       aliases=("midpoint",), scene="2v:projection", see=("frequency",)),

    # ------------------------------------------------------------ measurement
    _t("board foot", "Board foot", "measure",
       """A volume of wood: a board one foot square and one inch thick. This book's
       trunk holds {{tree.solid_bf}} of them.""",
       aliases=("bf",), figures=("tree.solid_bf", "tree.wedge_bf", "tree.kerf_bf"),
       see=("recovery",)),
    _t("recovery", "Wood recovery", "measure",
       """The share of a trunk that ends up in usable pieces. Split into wedges
       this book's tree keeps {{tree.recovery_pct}} percent.""",
       aliases=("yield",), figures=("tree.recovery_pct", "tree.sawn_recovery_pct"),
       scene="why:ww_round", see=("kerf", "board foot")),
    _t("square foot", "Square foot", "measure",
       """An area one foot by one foot, the unit floors are quoted in. The book's
       dome floors {{dome.floor_sqft}} of them.""",
       aliases=("sq ft",), figures=("dome.floor_sqft",), see=("floor area",)),
    _t("strut length", "Strut length", "measure",
       """How long a member is. The longest in the book's frame is
       {{dome.longest_member_in}} inches, and there are only
       {{dome.member_lengths}} lengths to cut.""",
       aliases=("member length", "stick length", "longest member"),
       figures=("dome.longest_member_in", "dome.member_lengths"),
       visual="dimension", see=("cut list",)),
    _t("connector deduction", "Connector deduction", "measure",
       """The length taken off a strut's centre-to-centre length so its connector
       fits. The geometry gives hub centres; the saw needs something shorter.""",
       aliases=("deduction",), scene="2v:cutlist", see=("connector",)),
    _t("tolerance", "Tolerance", "measure",
       """How far a cut or a length may be off and still work. The jig is how a
       builder keeps inside it forty times.""", see=("jig",)),
    _t("crossover", "Crossover diameter", "measure",
       """The trunk diameter above which one wedge is the stiffer member than a
       dressed two-by-four. Below it the wedge loses, and the films say so.""",
       aliases=("crossover diameter",), scene="why:ww_stick",
       see=("bending",)),

    # ------------------------------------------------------------ tools
    _t("chainsaw", "Chainsaw", "tools",
       """A hand-held saw with a toothed chain running round a bar. The whole
       harvest is done with one small one: {{saw.displacement_cc}} cc, a
       {{saw.bar_in}}-inch bar, {{saw.price_usd}} dollars.""",
       aliases=("small saw", "cheap chainsaw"), visual="icon", icon="chainsaw",
       figures=("saw.displacement_cc", "saw.bar_in", "saw.price_usd"),
       scene="harvest:hv_harvest", see=("kerf", "felling")),
    _t("sawmill", "Sawmill", "tools",
       """The machines that square logs into boards. The wedge method removes the
       whole step.""", aliases=("mill", "planing mill"), icon="factory",
       scene="why:ww_chain", see=("milling",)),
    _t("jig", "Jig", "tools",
       """A fixture that holds parts in the same place every time, so that forty
       panels come out identical. Here it is one flat bench.""",
       aliases=("fixture", "bench"), scene="why:ww_bench",
       see=("flush-cut", "panel")),
    _t("table saw", "Table saw", "tools",
       """A saw whose blade sticks up through a table, used to rip a board along
       its length at a set tilt.""", see=("bevel",)),
    _t("mitre saw", "Mitre saw", "tools",
       """A saw that swings to crosscut the end of a board at an angle. Its scale
       runs out before a hubless dome's angles do.""",
       aliases=("miter saw",), see=("mitre", "crosscut sled")),
    _t("crosscut sled", "Crosscut sled", "tools",
       """A tray that slides past a table saw's blade and holds a board at a fixed
       angle, for cuts a mitre saw cannot reach.""", aliases=("sled",),
       see=("mitre saw",)),
    _t("stop block", "Stop block", "tools",
       """A block clamped at a set distance, so every piece is cut to exactly the
       same length without measuring any of them.""", aliases=("saw stop",),
       see=("tolerance",)),
    _t("truck", "Truck", "tools",
       """The pickup store-bought lumber rides home in. The wedge method never
       makes the trip.""", aliases=("pickup",), icon="truck",
       scene="why:ww_store", see=("overhead",)),

    # ------------------------------------------------------------ processes
    _t("felling", "Felling", "processes",
       """Bringing a standing tree down where you want it: a face notch on the side
       it should fall, a back cut from the other side, and the hinge between them
       steering it. The plan gives it {{work.felling_days}} days.""",
       aliases=("fell",), visual="pine_tree", icon="chainsaw",
       figures=("work.felling_days",), scene="harvest:hv_harvest",
       see=("notch", "hinge", "back cut")),
    _t("notch", "Face notch", "processes",
       """The wedge-shaped opening cut into the side a tree is meant to fall
       toward.""", aliases=("face notch",), visual="pine_tree",
       see=("hinge", "felling")),
    _t("back cut", "Back cut", "processes",
       """The felling cut made from the far side, a little above the notch. It
       frees the tree and leaves the hinge.""", visual="pine_tree",
       see=("notch", "hinge")),
    _t("hinge", "Hinge", "processes",
       """The strip of uncut wood between the notch and the back cut. It holds the
       tree to the stump as it falls and steers it.""", visual="pine_tree",
       see=("felling",)),
    _t("limbing", "Limbing", "processes",
       """Cutting the branches off a felled tree.""", visual="harvest",
       see=("bucking",)),
    _t("bucking", "Bucking", "processes",
       """Cutting a felled trunk into lengths: here {{tree.section_length_ft}}-foot
       sections, over {{work.bucking_days}} days.""",
       aliases=("buck",), visual="log_sections", icon="chainsaw",
       figures=("tree.section_length_ft", "work.bucking_days"),
       scene="harvest:hv_harvest", see=("section",)),
    _t("splitting", "Splitting", "processes",
       """Cutting a section lengthwise through its centre: halves, then quarters,
       then eighths. Nothing is squared and nothing is thrown away but the
       kerf.""",
       aliases=("split", "halving"), visual="log_sections", icon="split",
       scene="wedge:wg_split", see=("sector", "kerf", "ripping")),
    _t("ripping", "Ripping", "processes",
       """Sawing along the grain. For the wedges, ripping is how a section is
       split, and it is the bulk of the saw work: {{work.ripping_hours}} hours for
       a whole frame.""",
       aliases=("rip",), icon="chainsaw",
       figures=("work.ripping_hours", "work.struts_per_hour", "work.ripping_days"),
       scene="why:ww_sessions", see=("splitting", "fuel")),
    _t("kerf", "Kerf", "processes",
       """The width of wood a saw cut turns into sawdust. A chain's kerf is
       {{saw.kerf_in}} inches, and across a trunk it costs {{tree.kerf_bf}} board
       feet: the only wood a split loses.""",
       figures=("saw.kerf_in", "tree.kerf_bf"), visual="log_sections",
       scene="wedge:wg_split", see=("recovery",)),
    _t("milling", "Milling", "processes",
       """Turning a log into boards: slabbing, squaring, resawing, edging,
       trimming, drying and planing. From tree to graded board it takes
       {{route.mill_steps}} operations.""",
       aliases=("square milling", "squaring"), icon="factory",
       figures=("route.mill_steps", "route.wedge_steps"), scene="why:ww_chain",
       see=("sawmill", "splitting")),
    _t("crosscut", "Crosscut", "processes",
       """A cut straight across the grain.""", aliases=("square crosscut",),
       see=("bucking",)),
    _t("drying", "Drying", "processes",
       """Letting green wood lose water, so it shrinks before it is in the frame
       rather than after.""", see=("grain",)),
    _t("butt cut", "Butt cut", "processes",
       """The one compound-angle cut on each wedge, made at the end that presses
       into its neighbour, with the member held in a cradle.""",
       aliases=("compound cut", "compound butt cut"), scene="why:ww_buttcut",
       see=("pinwheel", "jig")),
    _t("flush-cut", "Flush cut", "processes",
       """Cutting a member's deliberately long head off level with its neighbour,
       in place on the jig, so the panel comes out true without measuring.""",
       aliases=("flush-cutting", "flush cut"), scene="why:ww_flush",
       see=("head overfit",)),
    _t("end cut", "End cut", "processes",
       """The angled cut at a strut's end where it meets a hub. Its angle is half
       the strut's central angle.""", see=("central angle",)),
    _t("raising", "Raising", "processes",
       """Lifting the finished panels into place, bottom ring first. The plan's
       last two days.""", aliases=("assembly",), scene="wedge:wg_assemble",
       see=("panel",)),
    _t("harvest", "The harvest", "processes",
       """Everything the chainsaw does, from the first felling cut to the last
       strut stacked: {{work.harvest_days}} days in the plan.""",
       visual="harvest", icon="calendar",
       figures=("work.harvest_days", "work.felling_days", "work.bucking_days",
                "work.ripping_days"),
       scene="harvest:hv_harvest", see=("felling", "bucking", "ripping")),
    _t("cut list", "Cut list", "processes",
       """The list of every length to cut and how many of each: the step from a
       drawing to a pile of sticks.""",
       aliases=("whole cut list", "complete cut list", "cut schedule"),
       scene="2v:cutlist", see=("strut length",)),

    # ------------------------------------------------------------ forces
    _t("compression", "Compression", "forces",
       """Being pushed on along a member's length. A triangulated shell loads its
       members mostly this way or in tension, not in bending.""",
       visual="force_arrow", see=("tension", "bending")),
    _t("tension", "Tension", "forces",
       """Being pulled along a member's length.""", visual="force_arrow",
       see=("compression",)),
    _t("bending", "Bending", "forces",
       """Being loaded across a member's length, like a plank bridging a gap. It is
       where a wedge is weakest: {{versus.strength_pct}} percent against a dressed
       two-by-four from a {{versus.diameter_in}}-inch log.""",
       aliases=("bending strength", "bending stiffness"),
       figures=("versus.strength_pct", "versus.stiffness_pct",
                "versus.diameter_in"),
       scene="why:ww_stick", see=("crossover", "compression")),
    _t("load", "Load", "forces",
       """The weight and push a structure has to carry: its own weight, snow,
       wind and people.""", aliases=("load path", "snow load", "wind load"),
       visual="force_arrow", see=("network",)),
    _t("racking", "Racking", "forces",
       """A rectangle folding into a parallelogram under a sideways push. A
       triangle cannot rack.""", scene="2v:rigidity", see=("triangle",)),
    _t("stiffness", "Stiffness", "forces",
       """How much a member resists bending. It grows fast with a section's
       depth, which is why a wedge turned the right way does well.""",
       see=("bending",)),

    # ------------------------------------------------------------ money
    _t("shelf price", "Shelf price", "money",
       """What a board costs on the store rack: {{board.price_usd}} dollars for the
       two-by-four compared here. Very little of it is the tree.""",
       aliases=("direct-sale price",), icon="dollar",
       figures=("board.price_usd",), scene="why:ww_stack",
       see=("middleman",)),
    _t("middleman", "Middleman", "money",
       """Anyone who handles a board between the tree and the rack and takes a
       share of its price. The why film lists every one.""",
       aliases=("middle man",), scene="why:ww_stack", see=("shelf price",)),
    _t("overhead", "Overhead", "money",
       """Costs that ride along with a purchase without being on the receipt:
       trips, culls, time spent waiting.""", scene="why:ww_store",
       see=("cull", "truck")),
    _t("rate", "Rate", "money",
       """How fast the work goes, or what an hour of it is worth. Measured by what
       it replaces, an hour of cutting is worth {{work.rate_dressed_usd}} dollars
       against dressed two-by-fours.""",
       figures=("work.struts_per_hour", "work.rate_dressed_usd",
                "work.rate_nominal_usd"),
       icon="dollar", scene="why:ww_worth", see=("ripping",)),
    _t("bom", "Bill of materials", "money",
       """The full list of parts to buy, with quantities and prices.""",
       aliases=("bill",), icon="dollar", see=("cut list",)),

    # ------------------------------------------------------------ building
    _t("floor area", "Floor area", "buildings",
       """How much floor the dome gives: {{dome.floor_sqft}} square feet for the
       book's dome, sized by the tree rather than chosen.""",
       aliases=("usable floor",), icon="house", figures=("dome.floor_sqft",),
       visual="solved_dome", see=("square foot",)),
    _t("riser wall", "Riser wall", "buildings",
       """A short upright wall under the dome that buys headroom near the edge.""",
       aliases=("pony wall", "stem wall"), see=("floor area",)),
    _t("base ring", "Base ring", "base",
       """The bottom ring where the lowest panels land. An error in it is carried
       all the way round.""", aliases=("bottom ring",), see=("rim",)),
    _t("foundation", "Foundation", "base",
       """What the dome stands on. Whichever kind it is, it has to be level and it
       has to hold the ring.""", aliases=("footing", "ring beam"),
       see=("base ring",)),
    _t("opening", "Opening", "envelope",
       """A doorway or window. In a dome, take out whole panels rather than
       cutting members.""", aliases=("door", "window"), see=("panel",)),
    _t("skin", "Skin", "envelope",
       """What covers the frame against weather: sheathing, membrane, cladding.
       A frame is not a shelter until it has one.""",
       aliases=("sheathing", "cladding", "exterior skin"), see=("shell",)),

    # ------------------------------------------------------------ services
    _t("utility core", "Utility core", "services",
       """One straight column carrying plumbing and power, so a round room's
       curves never have to meet a pipe.""", aliases=("utility column",),
       see=("plenum",)),
    _t("plenum", "Plenum", "services",
       """A duct ring round the base that lets one blower move air through the
       whole dome.""", aliases=("perimeter plenum",), see=("utility core",)),
    _t("solar panel", "Solar panel", "services",
       """A panel that turns sunlight into electricity. The model puts them only on
       dome faces that actually face the sun.""", aliases=("solar array",),
       icon="sun"),

    # ------------------------------------------------------------ materials
    _t("fuel", "Chainsaw fuel", "materials",
       """What the saw burns. Ripping the whole frame takes {{fuel.rip_tanks}}
       tanks: between {{fuel.rip_gallons}} and {{fuel.rip_gallons_high}} US
       gallons, a range because the saw's tank size is not confirmed.""",
       aliases=("gas", "fuel tank"), icon="fuel",
       figures=("fuel.tanks_per_hour", "fuel.rip_tanks", "fuel.rip_gallons",
                "fuel.rip_gallons_high"),
       scene="harvest:hv_harvest", see=("ripping", "bar oil")),
    _t("bar oil", "Bar oil", "materials",
       """Oil the saw drips onto its chain as it cuts, counted alongside the fuel
       in the timed sessions.""", icon="drop", scene="why:ww_sessions",
       see=("fuel",)),
    _t("sheet metal", "Sheet metal", "materials",
       """Thin flat metal. The frankendome's V brackets were cut from a washing
       machine's casing.""", aliases=("flat band",), see=("v-bracket",)),

    # ------------------------------------------------------------ people and time
    _t("builder", "Builder", "people",
       """Whoever cuts, assembles and raises the dome. In this story, one person
       with a saw and occasional help.""", aliases=("crew", "worker"),
       visual="person", icon="person", see=("harvest",)),
    _t("engineer", "Engineer", "people",
       """The professional who sizes members and signs off a structure meant to be
       lived in. The films say where one is needed.""", icon="person",
       see=("load",)),
    _t("fortnight", "The fortnight", "time",
       """The book's build window: {{work.days}} days from the saw to a standing
       frame, {{work.harvest_days}} of them spent harvesting.""",
       icon="calendar", figures=("work.days", "work.harvest_days"),
       see=("harvest",)),
    _t("session", "Timed session", "time",
       """One sitting of cutting, timed, with the output and the fuel written
       down. The whole cost argument rests on two of them.""",
       aliases=("sitting",), icon="clock", scene="why:ww_sessions",
       see=("rate", "fuel")),

    # ------------------------------------------------------------ how the films work
    _t("token", "Number token", "media",
       """A named figure written into a script in double braces and filled in from
       the code on every build, so the words and the arithmetic cannot drift
       apart.""", see=("callout",)),
    _t("callout", "Callout", "media",
       """A figure on screen that arrives with the words that say it: a value, a
       unit, a pictogram and a short note, held long enough to read.""",
       see=("tally", "token")),
    _t("tally", "Tally", "media",
       """A column of figures that builds an arithmetic chain a row at a time, and
       is checked so it cannot show a sum that does not work out.""",
       see=("callout",)),
    _t("beat", "Beat", "media",
       """One chapter, or a claim with the screen that proves it, rendered to its
       own file so that fixing it costs one short render.""",
       see=("chapter",)),
    _t("chapter", "Chapter", "media",
       """One step of a film: a headline, the narration, the figures on screen,
       and the picture that goes with them.""", see=("beat",)),
    _t("visual object", "Visual object", "computing",
       """A drawable noun with named knobs -- a tree with a felling knob, a log
       with an exploded-view knob -- that any film or presentation can place and
       animate by moving one number.""", visual="harvest",
       see=("painter",)),
    _t("painter", "Scene painter", "computing",
       """The function that draws one kind of picture as a pure function of how
       far through its chapter the film is. The same moment always gives the same
       frame.""", aliases=("scene painter",), see=("visual object",)),
    _t("camera", "Camera", "computing",
       """The viewpoint the frame is drawn from: where it is, what it looks at, and
       how wide it sees.""", scene="2v:hero"),
    _t("pixel", "Pixel", "computing",
       """One dot of the picture. Everything the films compute ends as a colour for
       each of them.""", see=("camera",)),
)
