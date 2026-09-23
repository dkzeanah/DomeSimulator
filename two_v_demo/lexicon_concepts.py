"""The concepts of the visual lexicon: the ideas the films and the book argue.

A concept is a claim a viewer should leave with, explained in a few plain sentences,
with the figures it rests on (as live tokens), the caveat it owes, the places it is
already taught, and a *recipe* -- the ordered visual steps that show it, drawn from
the codified objects, the painters published films already use, number callouts and
checked tallies. A recipe is the storyboard a new chapter starts from.

Recipe steps are ``kind:detail``:

``object:key(knobs)``  a registered visual object, with the knob values that matter
``scene:lesson/stage``  a painter a published film already draws
``callout:template``    one figure, in token language
``tally:template``      a checked column, summarised
``icon:key``            a pinned pictogram
``type:words``          a card with words on it
``diagram:words``       arrows and dimensions, described
"""

from __future__ import annotations

from .lexicon import Concept


def _c(key, name, domain, claim, explain, terms, figures=(), caveat="", taught=(),
       recipe=()) -> Concept:
    squash = lambda text: " ".join(text.split())  # noqa: E731
    return Concept(key, name, domain, squash(claim), squash(explain), tuple(terms),
                   tuple(figures), squash(caveat), tuple(taught), tuple(recipe))


CONCEPTS: tuple[Concept, ...] = (
    # ============================================================ geometry
    _c("golden_ratio_not_struts", "Phi places the corners, not the struts",
       "geometry",
       """The golden ratio builds an icosahedron's twelve corners; a 2V dome's two
       strut lengths are not in the golden ratio.""",
       """The icosahedron's corners sit on three golden rectangles, so phi really
       is in the shape. But a 2V dome's struts come from splitting each edge in
       half and pushing the midpoints out to the sphere, and that step, not phi,
       decides their lengths.""",
       ("golden ratio", "icosahedron", "frequency", "projected midpoint"),
       taught=("film:2v/phi", "film:build/phi", "film:scratch/m_phi",
               "film:master/b_phi", "presenter:dome_housing_case/fundamentals"),
       recipe=("scene:2v/coordinates", "scene:2v/projection",
               "type:NOT THE STRUT RATIO")),
    _c("two_lengths", "Projection makes exactly two lengths", "geometry",
       """Push a split icosahedron's midpoints out to the sphere and every edge of
       a 2V hemisphere falls into just two lengths.""",
       """Splitting each edge in half leaves the new points inside the sphere.
       Moving them out onto it changes the distances, and when every edge is
       measured they group into two classes and no more.""",
       ("frequency", "projected midpoint", "chord factor", "strut"),
       taught=("film:2v/classes", "film:build/classes", "film:scratch/classes",
               "film:master/b_classes"),
       recipe=("scene:2v/midpoints", "scene:2v/projection", "scene:2v/classes")),
    _c("triangles_rigid", "A triangle cannot change shape", "geometry",
       """A triangle cannot change shape without a side changing length, so a frame
       of triangles holds its shape with no bracing.""",
       """Four hinged sides fold into a lozenge; three cannot, because three lengths
       fix a triangle completely. A dome is triangles curved round in every
       direction, so the whole shell is braced by its own shape.""",
       ("triangle", "racking", "network"),
       caveat="""Geometry explains why the shape stands; it does not size the
       members. Joints and foundations still need engineering.""",
       taught=("film:2v/triangles", "film:build/why_triangle",
               "film:scratch/why_triangles", "film:kick/triangle",
               "presenter:dome_case_triangles/the_problem", "book:2trees/ch06"),
       recipe=("scene:2v/rigidity", "object:force_arrow(kind=0)",
               "type:A TRIANGLE CANNOT RACK")),
    _c("icosahedron_start", "Start from the icosahedron", "geometry",
       """Of the five regular solids, the icosahedron starts closest to a
       sphere.""",
       """It has the most faces of the regular solids, so its corners are already
       spread most evenly over a ball, and the correction to reach a true sphere is
       the smallest.""",
       ("icosahedron", "hemisphere"),
       taught=("film:2v/platonic", "film:build/parent", "film:scratch/why_ico"),
       recipe=("scene:2v/platonic", "scene:2v/icosahedron")),
    _c("unit_then_scale", "Solve at radius one, then scale", "geometry",
       """Work every length out on a sphere of radius one; one multiplication then
       sizes the dome to any radius.""",
       """On a unit sphere every strut length is a pure factor. Multiply the factors
       by the real radius and the cut list appears, in any unit, for any size.""",
       ("unit sphere", "chord factor", "radius", "cut list"),
       figures=("dome.radius_in",),
       taught=("film:2v/normalize", "film:2v/cut_list", "film:build/unit",
               "film:scratch/scale"),
       recipe=("scene:2v/icosahedron", "scene:2v/cutlist",
               "callout:{{dome.radius_in}} in")),
    _c("two_fold_angles", "Only two fold angles close the dome", "geometry",
       """The wedge dome's {{frame.seams}} seams close at only
       {{seam.distinct_angles}} fold angles.""",
       """Each seam is where two panels meet at an angle. Solved seam by seam, those
       angles come in just two values, so two key profiles close the whole
       shell.""",
       ("seam", "fold angle", "seam key"),
       figures=("frame.seams", "seam.distinct_angles", "seam.fold_a_deg",
                "seam.fold_b_deg", "seam.count_a", "seam.count_b"),
       taught=("film:why/fold", "film:why/dihedral", "book:2trees/ch16"),
       recipe=("object:solved_dome(keys=1)", "scene:why/ww_fold",
               "tally:{{seam.count_a}} at {{seam.fold_a_deg}} deg + "
               "{{seam.count_b}} at {{seam.fold_b_deg}} deg = {{frame.seams}} "
               "seams")),
    _c("twelve_pentagons", "Every hexagon cage needs twelve pentagons",
       "geometry",
       """A sheet of hexagons stays flat forever; to close into a ball it needs
       exactly twelve pentagons, however many hexagons it has.""",
       """Three hexagon corners use up a full circle, so the sheet cannot curve.
       Each pentagon leaves a gap that lifts it, and the gaps only add up to a
       closed ball when there are twelve.""",
       ("hexagon", "pentagon"),
       taught=("film:hex/flat_forever", "film:hex/pentagon", "film:hex/twelve"),
       recipe=("type:TWELVE, ALWAYS",
               "diagram:a flat hexagon sheet curling up as pentagons replace "
               "hexagons")),
    _c("zome_flat", "A zome's panels are flat by construction", "geometry",
       """Two directions define a plane, so every panel a zome sweeps is flat, and
       equal directions give a single strut length.""",
       """A zome is swept from a star of directions rather than cut from a sphere.
       Each panel is made of two of those directions, which cannot warp, and when
       the directions are equal the panel is a rhombus with one side length.""",
       ("zome",),
       taught=("film:zome/sweep", "film:zome/flat", "film:zome/rhombus"),
       recipe=("diagram:two direction vectors sweeping out a rhombus",
               "type:FLAT BY CONSTRUCTION")),
    _c("ring_multiplies_error", "A ring multiplies small errors", "geometry",
       """Errors in a ring of struts add up as they go round; on the dome's base
       ring a strut error comes back amplified by the golden ratio.""",
       """A ring has nowhere to put a small mistake except into the next piece, so
       mistakes accumulate around it. That is why a build is checked member,
       triangle, ring, radius and height, in that order, before the crown.""",
       ("base ring", "tolerance", "golden ratio"),
       taught=("film:build/error", "film:build/check", "film:2v/verify",
               "film:master/ms_math_error"),
       recipe=("scene:2v/verification", "type:ERRORS ADD UP ROUND A RING")),

    # ============================================================ structure
    _c("shape_does_the_work", "The shape does the work, not the stick",
       "structure",
       """A triangulated shell loads its members mostly in compression and
       tension, so it needs sticks whose ends meet, not perfect boards.""",
       """A beam in a house bends under load, so it needs a strong, true section. A
       dome's triangles send load along their members instead, and every interior
       edge is doubled, so a raw wedge is enough.""",
       ("shell", "compression", "tension", "bending", "wedge"),
       figures=("versus.strength_pct", "versus.diameter_in"),
       caveat="""From a small log a single wedge is the weaker stick in bending:
       {{versus.strength_pct}} percent against a dressed two-by-four at
       {{versus.diameter_in}} inches.""",
       taught=("film:why/close", "film:why/stick", "film:wedge/triangles",
               "book:2trees/ch06", "book:2trees/ch10"),
       recipe=("object:force_arrow(kind=0)", "object:force_arrow(kind=1)",
               "object:solved_dome",
               "callout:{{versus.strength_pct}}% bending strength")),
    _c("crossover_diameter", "Above a certain trunk, the wedge is stiffer",
       "structure",
       """Stiffness grows much faster than size, so above some trunk diameter one
       wedge out-stiffens a dressed two-by-four.""",
       """A section's resistance to bending grows with roughly the cube of its
       size. A small wedge loses to the board; a big one wins; the crossover
       diameter is where they tie.""",
       ("crossover", "bending", "stiffness", "wedge"),
       caveat="""Below the crossover the wedge is the weaker stick, and the films
       say so with the number on screen.""",
       taught=("film:why/stick", "film:why/structure", "film:wedge/m_sector"),
       recipe=("scene:why/ww_stick", "type:THE CROSSOVER")),
    _c("independent_panels", "Forty frames, each finished on the ground",
       "structure",
       """Each triangle is built flat and finished before it meets its neighbours,
       so all the precise work happens at waist height.""",
       """The frame is {{frame.panels}} independent panels of
       {{frame.members_per_panel}} members each. They are made one at a time on the
       jig, then lifted whole, rather than assembled stick by stick in the air.""",
       ("panel", "jig", "raising"),
       figures=("frame.panels", "frame.members_per_panel"),
       taught=("film:why/panels", "film:wedge/panels", "film:wedge/assemble",
               "book:2trees/ch08"),
       recipe=("object:wedge_shell(reveal=1)", "scene:wedge/wg_explode",
               "scene:wedge/wg_assemble")),
    _c("doubled_edges", "Neighbours never share a stick", "structure",
       """Every interior edge carries two members, one from each panel, so the
       frame has {{frame.members}} members for {{frame.edges}} edges.""",
       """Because each panel keeps its own three members, two of them lie side by
       side along every shared edge, with a key between. That doubling is what
       lets a panel be finished on its own.""",
       ("edge", "member", "seam", "seam key"),
       figures=("frame.members", "frame.edges", "edges.duplicated"),
       caveat="""It costs more wood and more cuts than a hub dome. The trade is no
       hubs and no shared bevels.""",
       taught=("film:why/duplicate", "film:wedge/duplicate",
               "film:build/hubless_edge", "film:franken/doubling",
               "book:2trees/ch18"),
       recipe=("scene:wedge/wg_pair",
               "tally:{{frame.edges}} edges + {{edges.duplicated}} doubled = "
               "{{frame.members}} members")),
    _c("pinwheel_no_mitres", "The joint with no mitres in it", "structure",
       """In a pinwheel panel each member's end butts into the side of the next, so
       no end is mitred, coped or shaved to a point.""",
       """The three members chase each other round the triangle the same way. The
       mathematical corners are reference points no stick reaches, and each end
       bears on a flat sawn face.""",
       ("pinwheel", "joint", "mitre", "butt cut"),
       caveat="""There is still one compound cut per member, the butt cut. An
       earlier film said there was none, and a later chapter corrects it on
       camera.""",
       taught=("film:why/pinwheel", "film:why/buttcut", "film:wedge/pinwheel",
               "book:2trees/ch15", "book:2trees/ch34"),
       recipe=("scene:wedge/wg_pinwheel", "scene:why/ww_buttcut")),
    _c("key_holds_the_angle", "Let the key hold the angle", "structure",
       """A key in every seam takes up the angle between panels, so the variation
       lives in one cheap part instead of in every stick.""",
       """Cutting each seam's angle into the wood would mean a different bevel on
       every member. A spline, hose or gasket between the panels absorbs it
       instead, and the wood stays raw.""",
       ("seam key", "seam", "fold angle"),
       figures=("jig.gasket_in", "seam.distinct_angles"),
       taught=("film:why/fold", "film:wedge/gasket", "book:2trees/ch17"),
       recipe=("object:solved_dome(keys=1)", "scene:wedge/wg_gasket")),
    _c("four_orientations", "Four ways up, four buildings", "structure",
       """A wedge is not symmetric, so the way it is turned in its panel is a design
       decision, and each rotation gives the frame a different feature.""",
       """Point the wedges one way and the panel openings taper so a panel cannot
       fall through; turn them another and every seam becomes a channel for
       services. Same sticks, different building.""",
       ("orientation", "keystone", "wedge"),
       taught=("film:why/turn", "film:why/keystone", "film:why/channel",
               "film:why/features", "book:2trees/ch14"),
       recipe=("scene:why/ww_turn", "scene:why/ww_keystone",
               "scene:why/ww_channel")),
    _c("short_members_forgive", "Short members forgive defects", "structure",
       """A defect ruins the length that has to be thrown away around it, so short
       members lose little to a knot or a bend.""",
       """On a long board, one bad spot condemns the whole board. Bucked to
       {{tree.section_length_ft}} feet, the same spot costs one section, and even a
       crooked farm tree gives structure above and below its bend.""",
       ("defect", "section", "strut length"),
       figures=("tree.section_length_ft",),
       taught=("film:why/short", "film:why/defects", "film:wedge/short",
               "book:2trees/ch19"),
       recipe=("scene:why/ww_bend", "scene:wedge/wg_short")),

    # ============================================================ wood
    _c("split_keeps_the_tree", "A split log keeps most of itself", "wood",
       """Split along its radius, a trunk keeps {{tree.recovery_pct}} percent of its
       wood; the only loss is the kerf.""",
       """Every split follows the grain through the pith and removes only a saw's
       width. Of the {{tree.solid_bf}} board feet in the book's trunk the cuts take
       {{tree.kerf_bf}}, and the wedges keep the rest.""",
       ("splitting", "kerf", "recovery", "board foot"),
       figures=("tree.solid_bf", "tree.kerf_bf", "tree.wedge_bf",
                "tree.recovery_pct"),
       caveat="""Recovery measures volume, not quality: a split stick keeps its
       knots.""",
       taught=("film:why/yield", "film:wedge/m_radial", "film:wedge/split",
               "book:2trees/ch12", "book:2trees/ch13", "film:harvest/why"),
       recipe=("object:log_sections(explode=1)",
               "tally:{{tree.solid_bf}} solid - {{tree.kerf_bf}} kerf = "
               "{{tree.wedge_bf}} board feet",
               "callout:{{tree.recovery_pct}}% kept")),
    _c("corners_not_waste", "Waste is the wrong shape, not bad wood", "wood",
       """A round log packed with rectangles loses its corners, and those corners
       are good wood of the wrong shape.""",
       """A mill has to square a circle before it can make boards, so the slabs,
       edgings and shavings go. Nothing is wrong with that wood; it failed a
       geometry test, not a strength test.""",
       ("board", "slab", "cant", "milling", "recovery"),
       figures=("tree.sawn_recovery_pct",),
       caveat="""The packing comparison is made on the films' log, which is not the
       book's tree; the two recoveries are different cuts of different trees.""",
       taught=("film:why/round", "film:wedge/pack", "film:wedge/m_rectangles",
               "film:wedge/square"),
       recipe=("scene:why/ww_round", "scene:wedge/wg_pack")),
    _c("wedge_is_the_member", "One eighth of a tree, used as a stick", "wood",
       """A member is literally a sector of the trunk: pith edge in, bark face out,
       two flat sawn faces.""",
       """Nothing about it is milled. The densest wood ends up on the weather side,
       the deep dimension faces the load, and its section is worth
       {{member.as_nominal_2x4s}} nominal two-by-fours.""",
       ("wedge", "pith", "bark face", "sawn face", "sector"),
       figures=("member.width_in", "member.depth_in", "member.area_in2",
                "member.as_nominal_2x4s"),
       taught=("film:why/member", "film:why/sector", "film:wedge/member",
               "film:wedge/m_sector", "book:2trees/ch07"),
       recipe=("object:wedge_member", "scene:wedge/wg_section",
               "callout:{{member.area_in2}} sq in")),
    _c("tree_sizes_the_dome", "The tree sizes the building", "wood",
       """Buck to the longest length the trunk gives and the dome's radius, floor
       and height all follow: you find out the size instead of choosing it.""",
       """The section length is the longest member the frame may have. Solve the
       dome backwards from it and the book's trees give {{dome.floor_sqft}} square
       feet under a {{dome.diameter_ft}}-foot shell.""",
       ("section", "radius", "floor area"),
       figures=("tree.section_length_ft", "dome.radius_in", "dome.floor_sqft",
                "dome.diameter_ft"),
       taught=("film:why/dome", "film:why/sizing", "film:wedge/sizing",
               "film:wedge/m_dome", "book:2trees/ch22"),
       recipe=("object:harvest(explode=1)", "object:solved_dome",
               "callout:{{dome.floor_sqft}} sq ft")),
    _c("design_first", "Or start from the dome you want", "wood",
       """Pick a floor area and the method gives the longest member, the bucking
       length, the sections and the trees: {{method_a.floor_sqft}} square feet
       needs {{method_a.whole_trees}} trees.""",
       """Floor area sets the radius; the radius sets the longest member; that sets
       the bucking length, and the sections and trunk feet follow. It is the
       tree-first method run the other way.""",
       ("floor area", "strut length", "section", "tree"),
       figures=("method_a.floor_sqft", "method_a.longest_in", "method_a.buck_ft",
                "method_a.sections", "method_a.trees", "method_a.whole_trees"),
       taught=("book:2trees/ch20", "book:2trees/ch21", "film:harvest/tree"),
       recipe=("callout:{{method_a.floor_sqft}} sq ft",
               "tally:{{method_a.sections}} sections of {{method_a.buck_ft}} ft "
               "= {{method_a.trunk_ft}} ft of trunk",
               "object:pine_tree")),
    _c("round_trip", "The two methods are one calculation", "wood",
       """Run design-first and tree-first against each other and they close on the
       same dome, to within {{roundtrip.residual_in}} inches.""",
       """One function maps a radius to a longest member and another inverts it.
       Feeding either method's answer into the other gets back where it started,
       which is the proof that neither is a rule of thumb.""",
       ("radius", "strut length"),
       figures=("roundtrip.residual_in",),
       taught=("book:2trees/ch23",),
       recipe=("type:THE ROUND TRIP",
               "diagram:two arrows between radius and longest member, closing")),
    _c("two_trees_enough", "Two trees, one frame", "wood",
       """{{dome.trees}} trees give {{dome.struts_available}} struts for a frame
       that needs {{frame.members}}, with {{dome.spare_struts}} to spare.""",
       """Each tree is {{tree.sections}} sections of {{tree.sectors}} struts. The
       spares cover the pieces a knot or a bad split spoils.""",
       ("tree", "strut", "section", "sector"),
       figures=("dome.trees", "dome.struts_available", "frame.members",
                "dome.spare_struts", "tree.struts_per_tree"),
       taught=("film:wedge/open", "film:why/dome", "book:2trees/ch24",
               "film:harvest/explode"),
       recipe=("object:harvest(explode=1)",
               "tally:{{tree.sections}} x {{tree.sectors}} = "
               "{{tree.struts_per_tree}} x {{dome.trees}} = "
               "{{dome.struts_available}}")),

    # ============================================================ method
    _c("fewer_operations", "Fewer operations, fewer machines", "method",
       """From standing tree to member in the frame takes {{route.wedge_steps}}
       operations; from tree to graded board takes {{route.mill_steps}}, and the
       board still has to be bought and cut.""",
       """Every conversion step between a log and a rack is a machine, a building
       and somebody's wages. Splitting skips the squaring, resawing, edging,
       drying and planing entirely.""",
       ("milling", "splitting", "sawmill"),
       figures=("route.wedge_steps", "route.mill_steps"),
       caveat="""The two lists do not end in the same place. Counted to the same
       finish line the gap is wider, but the films print both lists rather than
       claim it.""",
       taught=("film:why/chain", "film:why/mills", "film:wedge/actions",
               "film:wedge/m_actions"),
       recipe=("scene:wedge/wg_chain", "scene:why/ww_chain")),
    _c("jig_not_tape", "The jig, not the tape measure", "method",
       """One flat bench holds every part in the same place, so forty panels come
       out the same without measuring any of them.""",
       """Repeatability beats accuracy when there are many of something. The jig
       fixes where each member sits and where each cut falls, so a mistake would
       have to be made the same way forty times to matter.""",
       ("jig", "panel", "flush-cut", "tolerance"),
       taught=("film:why/bench", "film:why/jig", "book:2trees/ch30",
               "book:2trees/ch33"),
       recipe=("scene:why/ww_bench", "scene:why/ww_flush")),
    _c("cut_it_long", "Cut it too long on purpose", "method",
       """Leave the head end long, flush-cut it in place, and the error leaves as
       an offcut instead of building up round the triangle.""",
       """Each member arrives {{jig.head_overfit_in}} inches long at its head. On
       the jig the long end is cut off level with its neighbour, so the panel is
       true whatever the stick's length error was.""",
       ("head overfit", "flush-cut", "offcut"),
       figures=("jig.head_overfit_in",),
       taught=("film:why/flush", "book:2trees/ch35", "book:2trees/ch36"),
       recipe=("scene:why/ww_flush", "type:NEVER MEASURED")),
    _c("two_machines", "The compound cut needs two saws", "method",
       """A hubless strut end carries two angles: the table saw rips the bevel, and
       a crosscut sled makes the end angle, because no mitre saw reaches it.""",
       """Each machine can do only the cut the other cannot. The bevel decides how
       a triangle meets its neighbour; the end angle decides how a strut meets the
       other two in its own triangle.""",
       ("bevel", "mitre", "table saw", "mitre saw", "crosscut sled"),
       taught=("film:cuts/two_angles", "film:cuts/machines", "film:cuts/limit",
               "film:cuts/sled", "film:build/hubless_saw"),
       recipe=("type:PAST THE STOP",
               "diagram:the blade tilt beside the sled fence angle")),
    _c("turn_not_flip", "Turn it, do not flip it", "method",
       """The second end of a strut is not a mirror of the first: rotate the strut
       end for end, never face over face.""",
       """Flipping it keeps the angle and puts the bevel on the wrong side, and the
       strut refuses to close its triangle, though it looks right on the
       bench.""",
       ("end cut", "bevel"),
       taught=("film:cuts/turn", "film:master/c_turn"),
       recipe=("type:TURN, DON'T FLIP",
               "diagram:a rotation arrow about the strut's long axis")),
    _c("hinge_steers", "The hinge steers the tree", "method",
       """A face notch and a back cut leave a hinge of uncut wood, and the hinge,
       not the saw, steers the tree down.""",
       """The notch opens on the side the tree should fall. The back cut frees it
       from the other side, and the strip between them bends instead of breaking,
       holding the tree to the stump as it goes over.""",
       ("felling", "notch", "back cut", "hinge", "chainsaw"),
       caveat="""Felling is the most dangerous part of the whole build; the book
       puts its safety page before the notch.""",
       taught=("book:2trees/ch27", "film:harvest/fell"),
       recipe=("object:pine_tree(fell=0.6)", "icon:chainsaw",
               "type:THE HINGE STEERS IT")),
    _c("tree_to_struts", "Buck and split: a tree becomes struts", "method",
       """Cut the trunk into {{tree.sections}} sections and split each into
       {{tree.sectors}}, and one tree is {{tree.struts_per_tree}} struts.""",
       """Bucking makes the lengths; three rip passes per section make the
       eighths. The section length is the strut length, so there is no crosscut
       after the split.""",
       ("bucking", "splitting", "section", "sector", "strut"),
       figures=("tree.sections", "tree.sectors", "tree.struts_per_tree",
                "tree.section_length_ft"),
       taught=("film:harvest/explode", "book:2trees/ch28", "book:2trees/ch29",
               "film:wedge/split"),
       recipe=("object:harvest(buck=1, explode=1)", "icon:chainsaw",
               "tally:{{tree.sections}} sections x {{tree.sectors}} = "
               "{{tree.struts_per_tree}} struts")),

    # ============================================================ build
    _c("harvest_in_days", "The harvest, in days", "build",
       """The whole harvest takes {{work.harvest_days}} days of the
       {{work.days}}-day fortnight: {{work.felling_days}} felling,
       {{work.bucking_days}} bucking and {{work.ripping_days}} ripping.""",
       """The day plan is a decision, but it is held to the arithmetic: the ripping
       block is exactly the afternoons the measured cutting rate needs, and the
       fortnight ends on the declared build length.""",
       ("harvest", "felling", "bucking", "ripping", "fortnight"),
       figures=("work.harvest_days", "work.days", "work.felling_days",
                "work.bucking_days", "work.ripping_days", "work.afternoons"),
       taught=("book:2trees/ch27", "book:2trees/ch28", "book:2trees/ch29",
               "film:harvest/cost"),
       recipe=("object:harvest", "icon:calendar",
               "callout:{{work.harvest_days}} days")),
    _c("fuel_as_a_range", "A few gallons of fuel, shown as a range", "build",
       """Ripping the whole frame burns {{fuel.rip_tanks}} tanks of fuel, between
       {{fuel.rip_gallons}} and {{fuel.rip_gallons_high}} US gallons.""",
       """The burn rate was measured in a timed session and the hours come from the
       measured cutting rate. Only the saw's tank size is a guess, so the answer is
       a range instead of a point that pretends to know it.""",
       ("fuel", "ripping", "session", "chainsaw"),
       figures=("fuel.tanks_per_hour", "fuel.rip_hours", "fuel.rip_tanks",
                "fuel.tank_l", "fuel.tank_high_l", "fuel.rip_gallons",
                "fuel.rip_gallons_high"),
       caveat="""Felling and bucking were never metered and are not in the
       figure, and the tank size still has to be read off the actual saw.""",
       taught=("film:harvest/cost", "film:harvest/assume", "film:why/sessions",
               "film:why/rate"),
       recipe=("tally:{{fuel.tanks_per_hour}} tanks an hour x {{fuel.rip_hours}} "
               "hours = {{fuel.rip_tanks}} tanks",
               "icon:fuel",
               "callout:{{fuel.rip_gallons}} to {{fuel.rip_gallons_high}} gal")),
    _c("raise_by_rings", "Raise it one complete ring at a time", "build",
       """Never build up one side: the shell is not stable until a ring
       closes.""",
       """Each ring braces the one below it only once it is complete. Built up one
       side, the frame is a leaning partial arch; built ring by ring, it is a
       smaller finished shell at every stage.""",
       ("raising", "base ring"),
       taught=("film:build/raise", "film:zome/raise", "film:hex/raise_it",
               "book:2trees/ch32"),
       recipe=("scene:wedge/wg_assemble", "object:wedge_shell(reveal=0.5)")),
    _c("openings_whole_panels", "Openings come out as whole panels", "build",
       """Doors and windows go where whole panels come out; cutting through a
       member means replacing a load path.""",
       """Every member is part of the network that holds the shell up. Taking out a
       complete panel removes a triangle the rest can bridge; cutting a stick in
       half removes a path the load was using.""",
       ("opening", "panel", "load"),
       taught=("film:build/openings", "film:zome/openings", "book:2trees/ch41"),
       recipe=("object:solved_dome", "type:TAKE WHOLE PANELS")),
    _c("measurement_loop", "Close the measurement loop", "build",
       """Check member, triangle, ring, radius and height, in that order, and fix an
       error before the crown.""",
       """A good build is calculated, made, measured and corrected. Each check
       catches what the one before it would have passed on, and the last one, the
       height, is the dome telling you whether the sphere closed.""",
       ("tolerance", "base ring"),
       taught=("film:2v/verify", "film:build/check"),
       recipe=("scene:2v/verification",)),
    _c("skin_rim_upward", "Skin it from the rim upward", "build",
       """Lay the covering so that every lap sheds water downhill.""",
       """Start at the bottom and work up, each piece lapping over the one below,
       like shingles on a roof. Water then runs over every joint instead of into
       it.""",
       ("skin", "rim"),
       taught=("film:build/skin", "book:2trees/ch40", "book:2trees/ch42"),
       recipe=("object:solved_dome",
               "diagram:overlapping laps, water running over each joint")),
    _c("frame_is_not_a_home", "A standing frame is not a home", "build",
       """The fortnight ends with a frame, not a shelter: skin, openings, weather
       and services all come after.""",
       """The frame is the part the method changes. Everything that makes it a
       place to live is ordinary building work, and the book gives it its own part
       rather than pretending it is included.""",
       ("skin", "opening", "utility core"),
       taught=("book:2trees/ch32", "book:2trees/ch40", "book:2trees/ch44"),
       recipe=("object:solved_dome", "type:NOT FINISHED")),

    # ============================================================ economics
    _c("shelf_price_stack", "A shelf price is mostly not the tree", "economics",
       """Stack up who takes what between a standing tree and the rack, and very
       little of a board's price is the wood.""",
       """Logger, hauler, mill, dryer, grader, distributor, retailer: each handles
       the board and takes a share. The why film lists them one by one rather than
       quoting a round number.""",
       ("shelf price", "middleman", "milling"),
       figures=("board.price_usd",),
       taught=("film:why/middlemen", "film:why/middlemen_math",
               "book:2trees/ch02"),
       recipe=("scene:why/ww_stack", "callout:${{board.price_usd}}")),
    _c("an_hour_at_the_log", "What an hour at the log is worth", "economics",
       """Valued by the boards it replaces, an hour of cutting is worth
       {{work.rate_dressed_usd}} dollars against dressed two-by-fours.""",
       """It is a substitution value, not a wage: {{work.struts_per_hour}} struts
       an hour, each worth the store boards of the same section and length.""",
       ("rate", "ripping", "two-by-four"),
       figures=("work.rate_dressed_usd", "work.rate_nominal_usd",
                "work.struts_per_hour"),
       caveat="""Against nominal two-by-fours it is {{work.rate_nominal_usd}}
       dollars. The book prints both and says which question each answers.""",
       taught=("film:why/worth", "film:why/value", "film:why/rate",
               "book:2trees/ch45"),
       recipe=("scene:why/ww_worth", "icon:dollar",
               "callout:${{work.rate_dressed_usd}} an hour")),
    _c("hidden_overheads", "The part nobody counts", "economics",
       """Buying lumber carries costs that never appear on the receipt: trips,
       culls, waiting, and boards that never make it.""",
       """They feel like part of life, so nobody times them. Counted, they add real
       money and real hours to the store-bought side.""",
       ("overhead", "cull", "truck"),
       taught=("film:why/store", "film:why/overhead"),
       recipe=("scene:why/ww_store", "icon:truck")),
    _c("measured_before_money", "Measured and guessed, kept apart", "economics",
       """Every money figure comes after a table that says which inputs were
       measured and which were assumed.""",
       """A number is only as good as what it rests on. Putting the measured and
       the guessed side by side before any money is discussed lets a viewer
       disagree with an assumption and still follow the arithmetic.""",
       ("session", "rate"),
       taught=("film:why/assumptions", "film:harvest/assume"),
       recipe=("type:MEASURED, AND GUESSED", "scene:harvest/hv_harvest")),
    _c("flat_rate_labour", "Dome labour is a flat rate", "economics",
       """Floor area grows with the radius, but the parts list does not: the same
       number of struts frames a small dome or a large one.""",
       """The work is counted in pieces and operations, and those stay fixed as the
       dome grows. What changes is how long each piece is.""",
       ("strut", "floor area"),
       caveat="""It is a flat rate inside a band, and the band is set by what one
       pair of hands can handle, not by the arithmetic. The declared limit is a
       {{flat.solo_member_ft}} ft longest cut member -- the most the builder
       will carry, stand both ends of and set alone -- which solves to a dome
       {{flat.solo_dome_ft}} ft across, the same dome two trees yield. Under it
       nothing changes: same assembly pattern, same hardware counts, same nine
       operations, same strut preparation, only shorter sticks. Over it you are
       either buying help or raising the frequency, and raising the frequency is
       the one move that genuinely lengthens the parts list.""",
       taught=("film:franken/flatrate", "film:kick/flatrate",
               "film:master/ms_math_flatrate"),
       recipe=("type:SAME PARTS LIST", "object:hub_dome")),

    # ============================================================ performance
    _c("less_skin_per_floor", "Same floor, less building", "performance",
       """A dome covers a floor with less outside surface than a box of the same
       floor, and the wall you never build never costs anything.""",
       """A sphere encloses the most volume for its surface. Half of one, standing
       on a floor, needs noticeably less skin, framing and weatherproofing than a
       box doing the same job.""",
       ("dome", "skin", "floor area"),
       taught=("film:kick/problem", "film:kick/versus", "film:master/k_versus",
               "presenter:dome_case_bare_shell/the_numbers", "film:world/efficiency"),
       recipe=("object:solved_dome", "type:LESS SKIN PER FLOOR")),
    _c("brim_is_a_gutter", "The brim is already a gutter", "performance",
       """An overhanging brim throws water clear of the joints and collects it at
       the same time.""",
       """Without an overhang, rain runs down the shell into every joint at the
       base. With one, it drips clear, and a gutter along the brim sends it to a
       tank.""",
       ("rim", "skin"),
       taught=("film:kick2/brim", "film:kick2/water", "film:master/k_brim",
               "film:master/ms_math_water"),
       recipe=("diagram:rain running off the brim into a tank", "icon:drop")),
    _c("one_tube_two_machines", "One tube, one blower", "performance",
       """A ring duct round the base and one blower move air through the whole
       dome, either way round.""",
       """Blow in and the building breathes out through its skin; pull out and the
       same ring becomes a central vacuum. The flow is computed; whether the wall
       filters is not proven.""",
       ("plenum",),
       taught=("presenter:airflow_dome/mechanism", "presenter:airflow_dome/exhaust",
               "film:build/air_origin", "film:build/air_direction"),
       recipe=("type:ONE TUBE, TWO MACHINES",)),
    _c("energy_not_claimed", "The energy claim this project will not make",
       "performance",
       """Less skin per floor is real, but a flat promise of lower energy bills is
       a claim this project refuses; its own model is shown instead.""",
       """How much a dome saves depends on insulation, climate, site and systems.
       The presentation shows one modelled build and names the popular percentage
       it will not repeat.""",
       ("dome", "skin"),
       taught=("presenter:dome_case_energy/the_hedge",),
       recipe=("type:NOT CLAIMED",)),

    # ============================================================ housing
    _c("honest_finished_number", "The finished-home number is the honest one",
       "housing",
       """Stripped to a bare shell a dome is much cheaper to build; finished with
       the same kitchens and baths, most of that gap closes.""",
       """Kitchens, bathrooms and mechanicals cost the same whatever shape the walls
       are. The bare-shell comparison measures the shape; the finished-home one
       measures the house, and it is the one to trust.""",
       ("dome", "floor area"),
       caveat="""The bare-shell figure flatters the dome, and the presentations
       show it only beside the finished one.""",
       taught=("presenter:dome_housing_case/home_numbers",
               "presenter:dome_case_more_room/the_honest_number",
               "presenter:dome_case_bare_shell/the_numbers"),
       recipe=("type:THE SMALLER NUMBER IS THE TRUSTWORTHY ONE",)),
    _c("more_room_same_money", "More room for the same money", "housing",
       """The real win is volume: the same footprint and budget enclose more space
       inside a dome.""",
       """Once the house is finished the costs are close, so the argument moves
       from price to what the price buys: height and air a box of the same floor
       does not have.""",
       ("dome", "floor area"),
       taught=("presenter:dome_case_more_room/the_real_win",
               "presenter:dome_housing_case/home_numbers"),
       recipe=("type:MORE ROOM, SAME MONEY", "object:solved_dome")),
    _c("straight_core", "The curved-wall answer is a straight core", "housing",
       """Put plumbing and power in one straight column and the round walls never
       have to meet a pipe.""",
       """The first objection to a round room is always where the plumbing goes.
       Concentrating every straight line in one core answers it, and leaves the
       curved shell to be a shell.""",
       ("utility core",),
       taught=("presenter:dome_case_utility_core/the_core",
               "presenter:dome_housing_case/core"),
       recipe=("type:ONE STRAIGHT CORE",)),
    _c("narrower_claim", "Where a dome actually wins", "housing",
       """Starter homes, backyard units, rural and off-grid sites and
       disaster-prone low-rise; not dense cities, and the project says so.""",
       """A claim small enough to defend beats a large one nobody believes. The
       market-fit presentation names where the case holds and where it does
       not.""",
       ("dome",),
       taught=("presenter:dome_case_market_fit/where_it_fits",
               "presenter:dome_housing_case/honesty"),
       recipe=("type:A NARROWER CLAIM",)),
    _c("lending_door_open", "The lending door is already open", "housing",
       """Mainstream mortgage guidance already allows dome-secured loans, so
       financing is paperwork, not a barrier of principle.""",
       """A buyer needs a lender before an argument about geometry. The financing
       presentation computes a real payment and points at the guidance that
       already covers it.""",
       ("dome",),
       taught=("presenter:dome_case_financing/close",
               "presenter:dome_case_financing/the_model"),
       recipe=("icon:dollar", "type:COMPUTED, NOT PROMISED")),
    _c("step_free_home", "A home that meets you halfway", "housing",
       """One level, one ramp and one open room make a dome a natural fit for
       someone with limited mobility.""",
       """There are no interior bearing walls to squeeze a hallway between, so the
       whole floor is turning space, and the rigid shell can carry a hoist or a
       grab bar anywhere.""",
       ("dome", "floor area"),
       taught=("presenter:dome_accessibility/entry",
               "presenter:dome_accessibility/open_floor",
               "presenter:dome_accessibility/transfers"),
       recipe=("object:person(walk=0.3)", "type:STEP-FREE")),

    # ============================================================ rendering
    _c("numbers_are_computed", "Nothing on screen is typed in", "rendering",
       """Every figure a film shows is computed by code that also proves it, and a
       figure that cannot be computed is declared, with its reason, on screen.""",
       """A film that asserts numbers cannot be checked; one that computes them can
       be re-derived by anyone. The same functions feed the films, the book and
       the tools, so they cannot disagree.""",
       ("token", "callout"),
       taught=("film:master/ms_math_counted", "film:master/ms_engine",
               "film:world_chatgpt/cg_close"),
       recipe=("type:COMPUTED, NOT TYPED",)),
    _c("frames_are_pure", "Every frame is a pure function of time", "rendering",
       """The same moment always draws the same picture, so a still is exact and a
       render is repeatable.""",
       """Nothing accumulates between frames. Ask for any second of any chapter and
       the painter draws it from scratch, which is how a single still can be
       checked before a ninety-minute render.""",
       ("painter", "camera"),
       taught=("film:scratch/frame", "film:master/ms_engine"),
       recipe=("type:SAME MOMENT, SAME FRAME",)),
    _c("triangle_to_pixel", "From a triangle to a lit pixel", "rendering",
       """A frame is a chain of small calculations: world, camera, projection, the
       divide, the viewport, depth and light.""",
       """Each step is simple on its own, and each is computed on screen in the
       from-scratch film with the renderer's own settings read back out of its
       code.""",
       ("pixel", "camera", "painter"),
       taught=("film:scratch/pipeline", "film:scratch/m_pixel",
               "film:scratch/close"),
       recipe=("diagram:a vertex travelling world, camera, clip, screen",
               "type:SEVEN STATIONS")),
    _c("figures_with_words", "Figures arrive with the words that say them",
       "rendering",
       """A callout lands on the phrase that says it, and a tally builds its sum a
       row at a time, checked so it cannot show arithmetic that does not work
       out.""",
       """The voice track is synthesized first and timed sentence by sentence;
       every figure is a token resolved from the same functions the book uses; and
       a column that said eight times eight is sixty-five would refuse to
       build.""",
       ("callout", "tally", "token"),
       taught=("film:harvest/explode",),
       recipe=("tally:{{tree.sections}} x {{tree.sectors}} = "
               "{{tree.struts_per_tree}}", "icon:split")),
    _c("beats_not_films", "Render beats, not films", "rendering",
       """A film is rendered as beats, so fixing one chapter costs one short render
       instead of the whole film.""",
       """Sections and whole films are joins of the beats, not new renders, so a
       corrected beat folds back in at every level in seconds.""",
       ("beat", "chapter"),
       recipe=("type:ONE BEAT, ONE FIX",)),
    _c("corrections_on_camera", "Corrections belong on camera", "rendering",
       """When a published film is wrong, the fix is a chapter that names the error
       and corrects it, not a silent re-cut.""",
       """The wedge film once said the joint needed no compound cut. The why film
       has a chapter that says so, shows the cut, and then the number that
       rescues the method.""",
       ("chapter", "butt cut"),
       taught=("film:why/buttcut", "book:2trees/ch48"),
       recipe=("scene:why/ww_buttcut", "type:THE CUT I SAID DID NOT EXIST")),

    # ============================================================ story
    _c("keep_the_bones", "Build the skeleton once, keep the bones", "story",
       """Treat a dome as a platform you keep upgrading rather than a house you
       finish once.""",
       """The frame lasts; the skins, services and fittings change. Swap the
       insulation, add the solar, reskin it for a new use, and the bones stay
       where they are.""",
       ("frankendome", "skin"),
       taught=("film:hype/bones", "film:hype/chassis", "film:master/h_bones"),
       recipe=("object:hub_dome(rough=1)", "type:KEEP THE BONES")),
    _c("failure_is_affordable", "When the material is scrap, failure is cheap",
       "story",
       """Building from salvage makes experiments cheap enough to fail, which is
       what makes them worth running.""",
       """The frankendome's brackets came out of a washing machine. A mistake in
       scrap costs an afternoon, not a lumber order, so the next attempt comes
       sooner.""",
       ("frankendome", "v-bracket", "sheet metal"),
       taught=("film:hype/affordable", "film:hype/mistakes", "film:why/franken"),
       recipe=("scene:why/seg_franken_plain", "type:FAILURE BECOMES AFFORDABLE")),
    _c("send_it_to_one_person", "Send it to one person", "story",
       """One share from somebody with reach does more than a month of cutting in a
       field.""",
       """Every film ends with the same small ask, packaged once as a segment so
       nobody maintains nine copies of it.""",
       ("chapter",),
       taught=("segment:cta_share/cta_share", "film:hype/share"),
       recipe=("type:SEND IT TO ONE PERSON",)),
)
