"""What a person decided about the vocabulary: which words are nouns, what kind of
thing each noun names, and how that kind of thing is shown on screen.

:mod:`two_v_demo.lexicon_words` finds the nouns in every script by the company they
keep. Evidence gets most of them right and some of them wrong, and it cannot tell a
tool from a tree. This module is where those two gaps are closed by hand, in plain
lists a non-programmer can read and edit.

Every category carries a **rendering mode** -- the default way a film puts a noun of
that kind in front of an audience. That is the bridge between the vocabulary and the
visual engine: a noun is either drawn by one of the codified visual objects in
:mod:`two_v_demo.visual_objects`, or it falls back to its category's mode and is
presented the way everything of its kind is presented.

``object``       a 3-D visual object on the stage
``animation``    an action performed on objects (a process noun: felling, bucking)
``diagram``      arrows, dimension lines and labelled geometry
``figure``       a number callout: a value, its unit, and where it came from
``icon``         a flat pictogram in the overlay, beside a figure or a word
``person``       the articulated figure
``environment``  the stage itself: ground, sky, weather
``screen``       the film's own chrome: captions, cards, chapter titles
``type``         a word on a card; abstractions have no shape to draw

Words are listed in the singular, as the tagger reduces them. A few words are listed
before any script says them, because the harvest film needs them; the catalogue
report shows those as anticipated rather than counted.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache


RENDERING_MODES: dict[str, str] = {
    "object": "a 3-D visual object on the stage",
    "animation": "an action performed on objects",
    "diagram": "arrows, dimension lines and labelled geometry",
    "figure": "a number callout: value, unit and source",
    "icon": "a flat pictogram in the overlay",
    "person": "the articulated figure",
    "environment": "the stage itself: ground, sky and weather",
    "screen": "the film's own chrome: captions, cards and titles",
    "type": "a word on a card",
}


@dataclass(frozen=True)
class Category:
    key: str
    name: str
    blurb: str
    rendering: str
    words: frozenset[str]


def _c(key: str, name: str, rendering: str, blurb: str, words: str) -> Category:
    return Category(key, name, blurb, rendering, frozenset(words.split()))


_SPECS: tuple[Category, ...] = (
    _c("structure", "Domes and structures", "object",
       "Whole structures, and the metaphors the films use for them.",
       """dome shell frame structure skeleton bone chassis frankendome
       franken-dome framework prototype monocoque"""),
    _c("members", "Members, panels and joints", "object",
       "The sticks a frame is made of, and everything that joins one to the next.",
       """strut member stick beam panel hub node joint seam key spline gasket
       hose spacer bracket v-bracket connector fastener screw bolt nut washer
       plate pinwheel lap relief setback inset overfit head tail butt keystone
       profile brace bracing truss rafter joist lintel header post module
       component contact end rim puck bulb filler extrusion casing band strip vee
       coping connection channel vein pin a-seam b-seam edge-member duplicate
       junction head-end side-slot cassette"""),
    _c("wood", "Trees and wood", "object",
       "The tree, what comes out of it, and what can be wrong with it.",
       """tree pine trunk log bark pith grain knot branch stump timber lumber wood
       woodpile firewood kindling sawdust shaving slab cant board plank stud
       two-by-four 2x4 2x4x16 2x4x12 sector wedge section offcut blank stock
       stockpile species hardwood hemlock cedar sawlog windfall taper bend defect
       flaw crescent waney edging rot flare woodlot forest heartwood sapwood waste
       slice cull sliver"""),
    _c("envelope", "Skin, openings and finishes", "object",
       "What closes the frame against the weather, and the holes left in it.",
       """skin sheathing cladding insulation membrane shingle osb plywood sheetrock
       glazing coating rainscreen brim hat cap seal flashing drip overhang lip door
       window opening hatch coaming skylight eave dormer gable cover covering tile
       exterior envelope enclosure barrier wrap latch finish layer leak coat
       penetration pore sandwich"""),
    _c("base", "Foundations and the base", "object",
       "What the dome stands on, and the ring it starts from.",
       """foundation footing pier deck platform riser base anchor anchorage plinth
       stem pony formwork"""),
    _c("geometry", "Geometry and shape", "diagram",
       "Shapes, the parts of shapes, and the ways a shape sits in space.",
       """geometry triangle edge face angle radius sphere diameter vertex corner
       chord circle arc axis plane normal midpoint projection frequency
       subdivision lattice mesh cage star cone cylinder prism pyramid frustum cube
       ball ellipse helix curvature curve symmetry topology equator apex crown
       centre center centroid bisector diagonal perpendicular deficit dual segment
       span triangulation icosahedron polyhedron tetrahedron octahedron
       dodecahedron triacontahedron zonohedron zome pentagon hexagon rhombus
       parallelogram quadrilateral polygon decagon square rectangle hemisphere 2v
       3v 4v 1v zigzag spire saucer facet cross-section circumference circumcircle
       circumradius direction side line shape surface orientation rotation position
       row course ring boundary silhouette pattern grid cell gap offset slot hole
       groove dihedral bevel mitre miter splay pitch configuration arrangement
       a-a-a b-a-b a-a-b b-b-b long-long-long short-short-long long-short-short
       honeycomb half-triangle top path middle box neighbour neighbor bottom form
       hex network solid front perimeter complement layout rise centreline
       endpoint intersection isosceles tip placement separation slope warp
       football baseball basketball bulge closure disc oval sag angle-bisector
       bowl diamond fold-angle hoop pole twist peak"""),
    _c("math", "Mathematics and models", "figure",
       "Numbers, the operations on them, and the models built out of them.",
       """number ratio phi pi factor formula equation root sine cosine tangent
       theta vector matrix dot sum fraction percent percentage average residual
       least-square count total multiplier multiplication division divisor
       numerator denominator addition subtraction coordinate arithmetic
       trigonometry mathematics math calculation computation derivation proof
       identity inverse exponent decimal magnitude law constant variable parameter
       function estimate approximation coefficient range limit extreme maximum
       minimum prediction model fit r x y z w divide spread origin variation
       breakdown candidate incidence overshoot transformation continuum
       distribution inversion parity progression declared-constant"""),
    _c("measure", "Measurement and units", "figure",
       "How big, how far, how heavy -- and how sure of it anyone is.",
       """inch foot ft metre meter millimetre mile degree deg kilogram kg tonnage
       gallon gal litre cc kilowatt kwh watt joule calorie kilocalorie kcal btu
       cfm ach r-value micron ounce bf sq mi yd cu square-foot sixteenth length
       width height depth thickness area volume weight mass density distance size
       dimension scale measurement measure precision accuracy error tolerance
       uncertainty allowance deduction clearance headroom reference datum unit
       recovery yield crossover slack travel mismatch slop sloppiness"""),
    _c("tools", "Tools, machines and vehicles", "object",
       "What does the cutting, holding, lifting and carrying.",
       """chainsaw saw bar chain file blade sled fence jig bench clamp tape level
       drill driver gun ladder scaffold scaffolding crane hoist gantry truck pickup
       trailer flatbed telehandler compressor machine mill sawmill bandsaw planer
       edger trimmer kiln headrig cutter laser cnc router featherboard protractor
       trammel straightedge sawhorse cradle fixture gauge master template stop
       block rail pencil tool toolkit toolset equipment machinery hardware kit
       tilt swing mixer bender gear chap helmet glove boot wheel wheelchair caster
       car boat ship aircraft cart conveyor sensor motor handle pallet saw-stop
       instrument knob aid bucket carriage nameplate needle workpiece"""),
    _c("processes", "Processes and operations", "animation",
       "What gets done to the wood and the frame. Drawn as motion, not as a thing.",
       """cut crosscut rip split notch hinge kerf felling bucking limbing splitting
       ripping milling sawing squaring trimming grading drying planing seasoning
       sorting stacking hauling haul handling loading unloading marking halving
       quartering assembly raising fabrication production construction build
       installation inspection check verification calibration dry-fit batch pass
       setup setting operation procedure step sequence method process route
       conversion packing nesting flush-cut flush-cutting sharpening fastening
       bolting welding weld laminating painting sealing waterproofing repair
       upgrade maintenance recutting skinning turn flip sweep fold work cycle test
       trial audit harvest harvesting logging processing manufacturing
       prefabrication erection demolition deconstruction disassembly retrofit
       renovation machining framing insulating transport transportation shipping
       trucking freight delivery joinery carpentry woodworking metalworking
       crosscutting bevelling mitering clamping gauging labelling labeling
       propping anchoring surfacing cutting run station stage job fall mark trip
       loop bottleneck action preparation replacement acceptance adjustment
       removal task treatment activity cross-check logistics transit diy end-cut
       industrialization re-cut rework sign-off wedge-build queue"""),
    _c("forces", "Forces, energy and physics", "diagram",
       "What pushes, pulls, bends and flows. Drawn as arrows and fields.",
       """force load compression tension bending shear stress strain stiffness
       strength gravity pressure energy heat temperature moment torque modulus
       deflection buckling stability rigidity racking collapse deformation drag
       aerodynamics turbulence uplift vibration friction flow airflow suction
       entrainment convection stratification destratification inertia ductility
       bearing preload capacity physics mechanics stretching resistance impact jet
       movement reaction emitter heat-loss"""),
    _c("money", "Money and economics", "figure",
       "Prices, costs, markets and the paperwork of paying for a house.",
       """cost price dollar cent money cash budget margin markup profit wage salary
       rate value labor labour overhead tax loan mortgage apr payment amortization
       insurance premium market store shelf receipt bill bom bid revenue
       investment capital capex factory break-even benchmark tier product sale
       appraisal underwriting financing finance credit income saving subsidy
       discount fee ledger accounting portfolio rent rental economics inflation
       spending expense expenditure purchase purchasing pricing costing valuation
       shopping retail supply demand industry company business interest principal
       affordability procurement warranty liability contract estate usd
       crowdfunding marketing advertising rack trade loss account substitute
       comparable resource allocation leverage organization cooperative luxury
       rollout moat niche perk"""),
    _c("buildings", "Buildings, rooms and furnishings", "object",
       "Kinds of building, the rooms inside them, and what goes in the rooms.",
       """house home building room floor wall roof ceiling kitchen bathroom bath
       bedroom loft shed cabin cottage greenhouse shelter workshop shop garage
       studio lodge pavilion hangar hanga treehouse playhouse igloo dwelling adu
       adus residence housing interior porch hallway hall stair ramp doorway
       entrance threshold courtyard office classroom warehouse homestead community
       campus footprint furniture sofa armchair chair bed cabinet cabinetry stove
       cooktop bathtub furnishing fit-out fitting pod space partition high-rise
       rowhouse venue bay aisle corridor storage laundry dining architecture
       cavity canopy lab seat coop runner tower commune facility"""),
    _c("land", "Land, places and weather", "environment",
       "Where a dome stands and what the sky does to it.",
       """site land property field ground soil dirt terrain parcel yard backyard
       garden park beach desert lake valley road highway street sidewalk arctic
       planet earth world place location spot zone region jurisdiction shoreline
       farm frontier cityscape municipality sky sun sunlight rain rainfall
       rainwater water snow wind weather climate storm tornado flood flooding
       earthquake fire air atmosphere moisture humidity condensation debris dust
       hazard disaster exposure runoff woodland darkness traffic wave junkyard"""),
    _c("services", "Energy, water and services", "object",
       "Power, plumbing, air and the machines that move them.",
       """power electricity battery solar array generator inverter wiring wire
       cable conduit plumbing pipe drain drainage tank cistern blower plenum duct
       ductwork grille vent fan hvac heating cooling heater appliance conditioner
       vacuum canister pump utility service surplus catchment gutter downpipe
       irrigation airlock exhaust draught flue chimney filter harness switch
       ventilation circulation tube core column port infrastructure plant register
       collector dish baffle inlet"""),
    _c("materials", "Materials and consumables", "object",
       "Everything that is not wood: metal, glass, plastics, fuel and scrap.",
       """material steel metal sheet aluminium aluminum concrete rebar plastic
       polycarbonate polycarb resin epoxy rubber foam glass fiberglass fibreglass
       cardboard tarp canvas cloth fabric paper oil fuel gas glue paint scrap junk
       garbage salvage mirror consumable masonry basalt soap froth bag gold"""),
    _c("people", "People and roles", "person",
       "Who builds, buys, lends, inspects, watches and lives inside.",
       """person builder owner owner-builder crew worker team carpenter engineer
       inspector buyer viewer reader audience author friend mother father child
       kid woman man girl teenager veteran programmer technician fabricator
       mechanic sawyer logger grader broker distributor retailer supplier
       contractor developer designer architect surveyor investor lender appraiser
       underwriter homesteader prepper maker tinkerer character cast resident
       occupant user customer competitor landlord renter homie brother household
       insurer borrower manager colleague student cousin girlfriend angel saint
       sinner hippy madman scavenger artist draftsman cabinetmaker installer
       operator haulier scaler bundler official professional employer marketer
       advocate human mathematician personnel workforce individual public
       humanity middleman manufacturer academic incumbent senior"""),
    _c("body", "The body, effort and dress", "person",
       "The worker's body and what it spends, and the lookbook's clothes.",
       """body arm leg hand shoulder knee hip thigh heart muscle brain mouth
       posture grip lift lifting carrying positioning walk motion stride footstep
       squat fatigue metabolism effort injury food banana bread hair scalp anatomy
       pose dress wardrobe garment outfit bodice skirt sleeve heel hem clothe
       landmark waist disability flesh"""),
    _c("time", "Time and schedule", "icon",
       "Hours, days and the fortnight, and the order things happen in.",
       """time day week fortnight month year hour minute afternoon morning night
       weekend holiday season summer winter daylight schedule timeline calendar
       deadline date session shift duration delay pause clock century history
       timing rhythm cadence chronology milestone future lifetime millisecond
       microsecond hr yr mo min ms event phase interruption sprint"""),
    _c("media", "Films, pages and language", "screen",
       "The films and books themselves, and the words they are made of.",
       """film video movie chapter lesson masterclass presentation presenter screen
       shot scene narration voice speech caption subtitle card headline title book
       page manuscript figure diagram chart drawing sketch illustration photograph
       photo image picture label legend glossary appendix outline paragraph
       sentence word text letter story narrative documentation playlist launcher
       editor composer simulator creator forge record journal report table brief
       note draft edition copyright imprint frontispiece half-title colophon
       opener slide slogan catalogue catalog manual guide handbook worksheet
       checklist listing description definition vocabulary language term name
       footage animation cutaway tour demo series cue script desk token strand
       information paperwork specification adjective instruction content
       demonstration map recipe spec statement atlas conversation discussion typo
       brochure how-to nickname parenthesis plan-view shortlist summary track"""),
    _c("computing", "Computing and rendering", "diagram",
       "What turns the geometry into the picture on screen.",
       """code codebase program programming software buffer gpu graphics shader
       pixel lighting light render renderer rendering shading fragment viewport eye
       target camera view perspective yaw orbit fov clip clipping winding float
       byte kilobyte kb memory upload ray tracing bug debug python json csv obj
       stl cad id ids ui interface algorithm computer calculator spreadsheet
       simulation solver engine repository repo app internet wireframe texture
       resolution background shadow highlight brightness shade tint opacity
       transparency ghost lens slider button placeholder todo dependency adapter
       helper subsystem format text-to-video avatar game ai prompt self-test
       validation mode colour color amber purple focus output application default
       preset data generation implementation input visualization aspect bridge
       command tone reflection serial falloff override painter regeneration
       stream click"""),
    _c("ideas", "Ideas, arguments and judgements", "type",
       "Abstractions. They have no shape, so a film sets them in type.",
       """idea question answer reason point way thing part problem solution claim
       argument approach system paradigm result fact example difference case
       choice decision assumption evidence truth honesty caveat hedge trade-off
       tradeoff advantage benefit penalty constraint requirement goal mission
       purpose principle rule theory concept detail feature option alternative
       version style habit mistake failure success experiment study research
       investigation observation discovery invention insight learning
       understanding skill craft craftsmanship discipline logic reasoning
       explanation mind sense attention curiosity luck chance risk hope wish faith
       confidence opportunity possibility potential life love romance joke shame
       reality impression perception aesthetic aesthetics plan design strategy
       intent aim ambition opinion instinct superstition consequence outcome
       effect cause context condition sample relationship relation association
       category classification hierarchy order exception distinction comparison
       compromise balance priority guess expectation warning guarantee promise
       objection complaint boast concession counterfactual hypothesis maxim trick
       magic cleverness simplicity complexity variety freedom independence
       control ownership access accessibility mobility safety comfort peace
       quality performance efficiency resilience durability repeatability
       consistency redundancy standardization standardizability scalability
       adaptability circularity credibility traceability provenance correction fix
       accident incident breakage technology science engineering object element
       stuff permit permission approval regulation zoning statute compliance
       certification standard change project source combination surprise
       convention identification attempt disagreement role subject trace basis
       behavior behaviour cake pie coincidence hobby proposal recommendation
       scheme simplification smoothness survival agreement criterion duplication
       fudge mechanism obstacle pathway request ability accomplishment
       accountability afterthought artefact attribute authority confusion
       diagnosis difficulty excuse favor flexibility harm hybrid inheritance
       journey mentality methodology ordeal policy proposition temptation upside
       urge usage state stamp"""),
    _c("quantities", "Quantities and groupings", "figure",
       "How much, how many, and what things are grouped into.",
       """half quarter pair set group kind type class family variant lot bulk
       majority remainder portion share rest amount quantity handful piece item
       stack pile collection inventory list cluster bundle package suite grade bit
       deal plenty excess shortage shortfall spare leftover trillion roll couple
       lump"""),
    _c("story", "Story, satire and drama", "type",
       "The montage's jokes and the micro-drama's plot: props with no geometry.",
       """empire tribute monopoly predator fortress weapon villain supervillain
       hobo hoboclass heir heiress council charge vote charter clause vault vellum
       blueprint betrayal release printer ink cartridge plague weakness funeral
       enemy monster whippersnapper psyche civilization treasury reveal organ
       chicken disco endgame explosive"""),
    _c("names", "Names", "type",
       "People, companies, agencies, places and works, by name.",
       """husqvarna lowe euler pandolf lambert goldberg fuller buckminster
       frankenstein bond inuit donovan zeanah aurelia vance silas leo elon musk
       teslabot rocky onlyfan alabama navy github instagram facebook tiktok
       youtube kickstarter chatgpt grok gemini domesim hud gao usda fema harvard
       jch fannie mae american greek jesus christ pythagoras descartes platonic
       february harbor iris"""),
)


# Words the context evidence calls nouns and a person says are not: adjectives
# used before a noun ("the raw wedge"), verbs after a determiner ("the make"),
# participles the ending rule in lexicon_words does not already hold back, and a
# handful of typos in the author's notes that are not worth a category.
NOT_NOUNS: frozenset[str] = frozenset("""
    whole real different long actual structural short small single straight full
    flat geodesic triangular entire raw rectangular usable identical sawn
    conventional honest green golden custom ideal wooden nominal compound
    continuous modular off-grid final physical local radial independent circular
    representative visible mathematical parent common central distinct important
    wide large better mechanical original exact specific new high low available
    regular useful true last longer longest cannot good bad big little great fat
    thin thick tight narrow deep dense heavy empty free open wrong right left far
    next previous early late certain particular basic simple easy hard plain pure
    proper strong weak stiff rigid smooth rough sharp soft dark warm cold hot cool
    dry wet fresh old young modern classic classical famous perfect nice serious
    ordinary typical cheap cheaper cheapest smaller larger bigger shorter harder
    wider stronger weaker stiffer closer higher lower faster easier thinner
    tighter heavier lighter flatter deeper narrower finer rounder smallest
    largest shortest heaviest lightest hardest strongest narrowest thinnest
    deepest flattest fattest tallest busiest hungriest slowest weakest steepest
    biggest cleanest simplest plainest worst best closest lowest earliest oldest
    dearest scarcest harshest densest favourite genuine precise accurate careful
    efficient stable possible impossible able willing ready sure aware necessary
    sufficient appropriate additional initial primary major minor main extra
    optional various numerous multiple separate equal parallel vertical
    horizontal outer inner upper external internal polar equilateral hexagonal
    spherical cubic angular longitudinal geometric hubless raw-wedge split-log
    tree-first design-first one-off full-size flat-pack low-rise bare-shell
    curved-wall shaved-flat direct-sale product-family engineer-stamped
    code-compliant store-bought raw-sector end-to-side cross-sectional odd-shaped
    left-handed right-handed same-handed near-identical one-person two-person
    single-person three-dimensional two-dimensional out-of-round head-to-head
    full-page strut-agnostic zero-threshold step-free stick-built turnkey modest
    generous enormous weird ugly beautiful magnificent flawless terrible awful
    strange unusual familiar unfamiliar convenient elegant pleasant comfortable
    rightful catastrophic evil excellent sensible reliable valid similar tiny huge
    lumpy sloppy wasteful buildable repeatable measurable provable defensible
    scalable swappable rentable walkable habitable readable followable editable
    manageable weatherable livable skippable acceptable applicable capable
    adequate round flush urban rural remote national federal regional personal
    industrial economic financial legal residential commercial traditional
    historic natural universal special correct alone alike halfway false worth
    seen given shown known taught chosen drawn written found held lost paid sold
    spent bought went came said gave took kept met fell built made thought
    make need come become give take want keep sit mean carry put meet start show
    say hold add buy exist ask let arrive remain contain tell find stay draw
    choose care reach happen decide grow lie solve reduce explain sell pick clear
    compare describe include create repeat require multiply remove establish
    apply disagree watch throw survive compute match sound preserve belong prove
    spend swap accept double think refuse begin connect agree halve fail return
    assume appear serve lean earn define sign print help transfer concentrate
    retain imply write fight pay occupy assemble trim save hide differ
    approximate recover accumulate afford expect shrink ignore touch convert
    represent cancel absorb hang collect inspect reconcile notice introduce
    feel enter resist burn slow forgive attack sink pack perform feed fill catch
    sort push move look go goe stand leaf that's aco
    matter complete cross depend live allow raise bare dimensional starter unique
    win quote expensive practical pull break irregular awkward fast lose tall
    temporary bear current locate present stretch accessible adjacent attractive
    call compressible contribute disappear effective electrical net send vary
    affect avoid compliant critical interactive lit minimize odd conservative
    converge explanatory gross normalize taller uncertain watertight adapt argue
    best-fit consistent determine direct disruptive eat fasten generic govern grab
    hit invisible mid numerical safe strict swept thermal uniform virtual ago
    annual arbitrary climb compact cure dangerous deliberate downstream drive dull
    everyday extend iii insist miss monolithic onsite panel-to-panel parametric
    plausible pristine procedural quiet recompute redundant reflect repetitive
    rescue resolve shared-edge shared-strut smoother straight-line suggest
    tolerate unconventional usual utility-core woodp wound acoustic afterwards
    agnostic apparent bucke build-a-home competitive construction-event convex
    cyclic decisive declare dominant exhale explicit fair far-off flatten
    full-dimension graded-lumber grew ill imperial intact intermediate irrational
    kill lightweight meaningful mid-trunk partial permanent protect radial-sawn
    regulatory remap reopen revise rhombic seasonal shallow single-hexagon squeeze
    straighten tidy top-down translate trustworthy unglamorous valuable
    woodmember accountable adjacent-panel asap assist asymmetric authoritative
    bab bespoke broader broke buy-here-pay-here cardinal circularhoseprofile
    class-i communicate compressedhoseprofile consumer-price controllable
    custompolygonprofile dead-end definitive demonstrate descend deterministic
    diametral digital dimensionless diverge dodge dome-specific drove economical
    fallen fascinate finished-home flexible forgave former fussy gentle glamorous
    gray grid-pack gross-material hardware-store heavier-duty high-impact
    high-leverage homogeneous hoped-for hopeful illustrative impressive
    incomplete independent-panel invert jump kit-of-part labor-shortage
    labor-time latter lead learning-curve lifelong material-price motivate mush
    nasty near-square neat newer non-negotiable non-obvious non-technical oblique
    offsite older organizational panel-and-jig panel-edge permeable point-axis
    portable preparatory productive radical radius-length radius-long
    recognizable recolour refer relate responsible restore revolutionary robotic
    round-room seamb see-through semi-permanent shallower shed-vs-dome
    short-section shuffle silent slip smaller-end snowbound soften spacerprofile
    spatial specify standalone starter-home station-by-station status-quo steady
    strategic sub-two-thousand-dollar subsequent substitue subtend suitable
    suspicious swung teaching-video tend theoretical thermal-mass tiny-home
    traceable trickiest twinw undercut unhelpful unique-edge unwelcome
    user-editable widow wind-effect y-z zonohedral drop
""".split())


@lru_cache(maxsize=1)
def categories() -> tuple[Category, ...]:
    return _SPECS


@lru_cache(maxsize=1)
def _index() -> dict[str, Category]:
    index: dict[str, Category] = {}
    for category in _SPECS:
        for word in category.words:
            if word in index:
                raise ValueError(
                    f"{word!r} is in both {index[word].key!r} and {category.key!r}; "
                    "a noun belongs to one category")
            index[word] = category
    return index


def category_of(lemma: str) -> str | None:
    """The category name a person gave this noun, or None."""
    category = _index().get(lemma)
    return category.name if category else None


def category_record(lemma: str) -> Category | None:
    return _index().get(lemma)


def rendering_of(lemma: str) -> str | None:
    category = _index().get(lemma)
    return category.rendering if category else None


def validate_taxonomy() -> None:
    """One category per noun, a known rendering mode for every category."""
    index = _index()
    keys = [category.key for category in _SPECS]
    assert len(set(keys)) == len(keys), "a category key repeats"
    for category in _SPECS:
        assert category.rendering in RENDERING_MODES, (category.key,
                                                       category.rendering)
        assert category.words, category.key
        assert category.blurb.strip(), category.key
    clash = sorted(set(index) & NOT_NOUNS)
    assert not clash, f"words both categorised and refused: {clash}"
