---
title: Using lumber versus logs
kind: section
---

# Using lumber versus logs

The wedge method can start from two very different kinds of material. One approach starts with lumber that has already been sawn into rectangular boards or timbers. The other starts much closer to the tree.

A log can be divided lengthwise into rough wedge-shaped sectors and those sectors can then be refined into structural members. Both approaches can produce a wedge. They just solve the manufacturing problem from opposite directions.

With dimensional lumber, we start with a rectangle and remove material until a wedge remains. With a log, we can start with radial material that already resembles a wedge and then create controlled reference surfaces from it. That difference affects material yield, tooling, drying, workholding, inspection, and how repeatable the finished members are.

DIMENSIONAL LUMBER

Dimensional lumber gives us a convenient starting point because the stock already has flat reference surfaces. That is useful in a fabrication system. A flat face can ride against a fence.

A square edge can sit against a stop. A jig can locate the same board repeatedly. The starting stock may therefore require less preparation before the actual wedge cut begins.

The basic process is:

$$ \text{rectangular stock} \rightarrow \text{wedge profile} \rightarrow \text{finished strut} $$

That looks simple, but the layout matters. Suppose a rectangular timber has a starting width \(W\) and thickness \(T\).

The final wedge requires an inside width \(w_i\) and an outside width \(w_o\).

The starting stock has to contain the complete finished profile:

$$ W \geq w_o $$

before allowing for saw kerf, cleanup, irregular stock, or another machining allowance. The actual board should be measured.

A nominal lumber designation is not enough to develop the final wedge dimensions. If a board is sold under a nominal size, the finished dressed dimensions may be smaller.

The shop drawing should therefore distinguish between:

**nominal stock size** and **actual measured stock size.**

The wedge is cut from the actual wood.

CUTTING A WEDGE FROM A RECTANGLE

A simple wedge can be laid out inside the rectangular section. If the finished wedge is symmetric, the narrow face remains centered beneath the wide face.

Material is removed from both sides.

The amount removed on each side at the narrow face is:

$$ x=\frac{w_o-w_i}{2} $$

The actual saw setup depends on how the blank is oriented during the cut. One process might tilt the workpiece.

Another might use a taper sled. Another may guide the stock along an angled fence while keeping the blade vertical. The geometry of the finished piece matters more than which specific machine configuration is used.

The production setup should eventually be chosen based on:

* safe workholding,
* adequate stock support,
* repeatability,
* available tooling,
* material length,
* cut quality,
* and the ability to verify the result.

The saw-angle setting by itself is not the specification.

The finished wedge dimensions are the specification.

MATERIAL REMOVED FROM LUMBER

Starting with rectangular lumber means some material has to be removed to create the taper. For one rectangular blank, the offcuts may appear wasteful. Across an entire dome, those offcuts represent enough material that they should be considered during the design of the cutting pattern.

There are several possibilities.

An offcut may become:

* another wedge,
* a smaller strut,
* panel blocking,
* battens,
* cleats,
* spacers,
* trim,
* jig material,
* or another repeated building component.

A cutting pattern should therefore be evaluated as a complete material layout.

The question is not only:

"How much wood does one wedge remove?"

The better question is:

"How much useful material can we recover from the starting timber?"

MIRRORED WEDGES

Some rectangular stock may allow two complementary or mirrored wedge-like parts to be recovered from the same blank. Whether that is practical depends on the required profile and the saw kerf. Conceptually, if one diagonal or tapered cut divides the stock into two useful pieces, material efficiency improves because the removed section becomes another part rather than scrap.

But the two resulting pieces have to be inspected independently. Saw kerf removes material between them. Any bow or taper in the starting stock may affect each piece differently.

And if the required finished dimensions include cleanup passes, the theoretical nesting pattern has to include enough material for those operations. A perfect CAD layout with zero-width saw cuts is not a real cutting plan.

Kerf has to be included.

LOG-DERIVED WEDGES

A log offers a different starting geometry. Viewed from the end, the log is approximately circular. Lines running outward from the center divide that circle into radial sectors.

Those sectors already have the basic relationship we want:

narrower toward the center, wider toward the bark. That makes the wedge method naturally compatible with radial breakdown.

Instead of first producing rectangular boards, we can potentially divide the log lengthwise into wedge-like sections.

The process becomes:

$$ \text{log} \rightarrow \text{radial sectors} \rightarrow \text{controlled wedge blanks} \rightarrow \text{finished struts} $$

This can remove one intermediate manufacturing step. It also creates several new ones.

A log is not a manufactured blank.

THE LOG IS NOT A CYLINDER

A drawing usually shows a log as a straight cylinder. A real log may not behave that way. Its diameter can change from one end to the other.

It may curve. Its center may not follow a perfectly straight line. The cross-section may not be circular.

The pith may not sit at the geometric center. The surface may contain butt swell, knots, branch transitions, damage, or other irregularities. This means a radial division that looks equal at one end may not produce the same dimensions at the other.

The first step in log processing is therefore understanding the material that actually exists.

For a controlled wedge system, useful measurements can include:

* diameter at several positions,
* log length,
* centerline or pith location,
* sweep,
* major knots,
* checks,
* visible decay or damage,
* and the intended usable section of the log.

Only then does it make sense to decide how many sectors can be recovered.

RADIAL BREAKDOWN

Suppose the usable log section is divided into \(n\) equal angular sectors.

The nominal sector angle is:

$$ \theta_s=\frac{360^\circ}{n} $$

For example, dividing the cross-section into eight equal sectors gives:

$$ \theta_s=\frac{360^\circ}{8}=45^\circ $$

That does not mean an eight-sector log automatically produces the correct wedge profile for a dome. It only describes the rough radial breakdown.

The structural wedge may require a different included angle, different truncation, different width, or further resawing. The radial sector is raw material. The finished wedge is the controlled part.

This distinction matters because it allows us to choose the log breakdown for material recovery without forcing the final dome geometry to equal the rough sector angle. One rough sector may become one structural wedge. It may also be split again.

Or it may be squared and machined to another profile. The number of sectors recovered from the tree and the number of finished dome members recovered from those sectors are separate decisions.

REMOVING THE PITH

The center of a log deserves special attention. If several wedges are divided exactly through the center, their narrow tips may all contain the pith or material immediately surrounding it. That region may not be where we want the finished narrow structural face to remain.

The rough wedge can instead be truncated. Material near the center can be removed to create a flat interior reference surface. That operation turns a sharp radial sector into the kind of truncated wedge used throughout this system.

Conceptually:

$$ \text{sharp radial sector} \rightarrow \text{remove inner tip} \rightarrow \text{flat narrow face} $$

The amount removed should come from the final wedge dimensions and material condition rather than from an arbitrary distance from the log center. The result gives us a surface that can be measured, jigged, drilled, and connected more easily than a sharp point.

ESTABLISHING REFERENCES ON A ROUGH WEDGE

A wedge cut from dressed lumber starts with useful flat surfaces. A wedge cut from a log may not. The bark-side surface is curved.

The radial cuts may vary. The log itself may taper along its length.

So a log-derived wedge needs a process for creating datums.

One possible order is:

1. divide the log into rough sectors,
2. remove the bark or irregular outer material as required,
3. establish one controlled reference surface,
4. establish the narrow interior face,
5. reference the remaining cuts from those surfaces,
6. bring the outside width under control,
7. verify the profile along the full length,
8. cut the member to final length,
9. machine the connection features,
10. label and inspect the part.

The final shop process may use a different order. The important part is that rough surfaces do not remain the dimensional reference indefinitely. At some point the work has to transition from tree geometry to manufactured-part geometry.

TAPER ALONG THE LOG

A log gets smaller as it approaches the top of the tree. That natural taper creates a problem if the goal is a constant wedge cross-section. A rough sector from a tapered log will also tend to become smaller along its length.

If we simply cut radial sectors and leave them untouched, the wide face at one end may not match the wide face at the other. For a member intended to have a constant profile, that taper has to be removed or deliberately accounted for. This may mean cutting the finished member to dimensions that can be maintained across the smallest usable portion of the blank.

In other words, the limiting end of the log may determine the recoverable finished wedge size. That can affect yield. A large butt diameter does not automatically mean the entire length can produce members sized from the butt.

The top end has to contain the required profile too.

LENGTH RECOVERY

Log length and member length also interact. If one log is long enough to produce several struts end-to-end, the log can potentially be divided longitudinally first and then each rough wedge can be crosscut into several shorter members. Another process could crosscut the log into manageable lengths before radial breakdown.

Each approach changes material handling. Longitudinal-first processing may preserve more flexibility for choosing final member positions around defects. Crosscut-first processing may make the material easier to handle on smaller equipment.

The best method depends on the tools, log size, final strut lengths, and defects. This is another place where material yield should be treated as an optimization problem rather than one fixed recipe.

GRAIN DIRECTION

One major difference between lumber and log-derived members is how clearly we can choose the wedge relative to the original tree. A radial sector preserves a direct relationship to the log center. The grain pattern visible in the cross-section may therefore be different from a wedge ripped out of commercially sawn rectangular stock.

That can affect:

* drying behavior,
* checking,
* movement,
* machining,
* and structural characteristics.

Those effects depend on species, moisture, sawing pattern, grade, dimensions, and the individual timber. They should not be reduced to a simple claim that one orientation is always better. The book should document the orientation being used and rely on appropriate timber references when structural consequences are stated.

MOISTURE AND DRYING

A freshly processed log and purchased dry lumber may begin at very different moisture conditions. That matters because the wedge is a geometric part. If the member changes dimensions after fabrication, its profile may also change.

Drying can affect:

* width,
* thickness,
* straightness,
* twist,
* checking,
* and connection fit.

That does not mean all log-derived material has to be handled in one particular way. It means moisture condition belongs in the fabrication record. If wedges are cut green and later assembled after drying, their final dimensions should be verified after drying.

If they are assembled green, the design has to account for whatever dimensional movement occurs afterward. The same principle applies to dimensional lumber, even if the amount of change is different. The actual moisture condition matters more than the label attached to the material.

BUILD NOTE

For the reference build, material records should eventually include:

* material source,
* species where known,
* nominal lumber size if applicable,
* actual starting dimensions,
* log diameter measurements if applicable,
* moisture measurement,
* visible defects,
* breakdown method,
* recovered blank dimensions,
* finished wedge dimensions,
* and rejected pieces.

That gives us real yield information. Without those records, statements about how many wedges come from a board or tree are only estimates.

TOOLING FOR LUMBER

Rectangular stock works naturally with common shop machines because the material already has flat surfaces.

Possible tools include:

* table saw,
* band saw,
* circular saw with guide,
* track saw,
* planer,
* jointer,
* router,
* drill press,
* and dedicated jigs.

The exact tool is less important than the workholding and reference system. Long wedge stock can become difficult to control if most of its weight hangs beyond the machine. Support tables, rollers, extensions, or another fixture may be needed so the cut is not affected by the operator trying to hold the stock level.

A repeatable cut requires the jig to control the wood. The operator should not have to manually steer the taper by eye.

TOOLING FOR LOGS

Logs introduce another scale of workholding. Before a rough sector can be treated like lumber, the log itself has to be restrained.

Possible processing methods could involve:

* sawmill equipment,
* band saw systems,
* chainsaw milling,
* circular saw systems,
* guide rails,
* cradles,
* dogs,
* clamps,
* or purpose-built fixtures.

The important part is that the log cannot be allowed to roll or shift during a longitudinal cut. A radial layout line is only useful if the saw follows it while the material remains fixed. Once the log has been divided into manageable rough wedges, those pieces can transition to smaller fixtures and more conventional shop operations.

The log-processing system and the wedge-finishing system may therefore be two different stages with different tools.

MATERIAL YIELD

The log approach creates the possibility of recovering many wedge blanks from one original tree. That is one of the main reasons to investigate it. But yield should be calculated from usable finished parts, not from a theoretical circle.

A theoretical cross-section may suggest that eight, ten, twelve, or another number of sectors fit around the center.

Real yield may be lower because of:

* saw kerf,
* bark and sapwood removal if required,
* defects,
* pith removal,
* log taper,
* sweep,
* minimum finished width,
* minimum finished thickness,
* and rejected pieces.

The useful yield equation is therefore not simply:

$$ \text{number of radial sectors} = \text{number of finished struts} $$

Instead:

$$ \text{finished yield} = \frac{\text{usable finished members}} {\text{starting material}} $$

The starting material can be measured by board feet, cubic volume, log count, or another consistent quantity depending on what we are comparing. That gives us a way to compare lumber and logs with actual production data later.

LABOR IS PART OF YIELD

Material efficiency is only one part of the comparison. A log may contain a large amount of useful wood while requiring more handling and preparation. Commercial lumber may cost more per unit of wood but arrive straight, surfaced, graded, and ready to fixture.

A useful comparison should eventually include:

* starting material cost,
* transport,
* drying,
* equipment,
* setup time,
* number of cuts,
* material handling,
* rejected material,
* finishing operations,
* and finished usable part count.

This is important because "free tree" does not mean "free wedge." The processing work still exists. On the other hand, access to local timber and the ability to process it directly may make the log route practical in situations where buying large quantities of finished lumber is not.

The book should show both paths rather than pretending one is always the correct choice.

REPEATABILITY

Dimensional lumber has an obvious advantage when repeatability is the priority. The starting material is already closer to a standardized blank. That reduces the number of variables the jig has to remove.

Log-derived material can still become repeatable.

It simply requires more processing before the member reaches that state.

A good way to think about the transition is:

$$ \text{irregular natural material} \rightarrow \text{controlled blank} \rightarrow \text{controlled part} $$

Once a log sector has been converted into a controlled blank, the later operations should look much more like the lumber process. At that stage we should no longer be compensating individually for the shape of the tree.

The jig should be manufacturing the defined wedge.

FAILURE MODES WITH LUMBER

Dimensional lumber can still create bad wedge members.

Common fabrication problems can include:

* using nominal dimensions in place of actual measurements,
* insufficient stock width for the required profile,
* bow,
* twist,
* cup,
* taper,
* incorrect fence setup,
* wrong jig orientation,
* saw drift,
* inconsistent feed,
* and labeling errors.

The flat starting surfaces reduce some problems.

They do not remove the need for inspection.

FAILURE MODES WITH LOG-DERIVED MEMBERS

Log processing adds another group of possible errors:

* incorrect radial layout,
* shifting log during cutting,
* following the bark instead of a controlled reference,
* sector angle changing along the log,
* pith off-center,
* excessive taper,
* sweep,
* hidden defects,
* irregular drying,
* insufficient finished dimensions at the small end,
* and assuming the rough radial surface is already accurate enough.

The rough wedge should therefore be treated as stock. Not as the finished strut. That one distinction can prevent a large amount of cumulative geometric error.

DESIGN VARIATION

There is also no requirement that a build choose only one material path.

A hybrid system could use:

* log-derived wedges for the main frame,
* dimensional lumber for special openings,
* laminated blanks for highly controlled connection areas,
* and smaller offcuts for panel framing.

Another build might use commercial lumber for the reference dome and treat log-derived construction as a later variation. The geometry can remain the same while the manufacturing path changes. That is useful because it separates the definition of the part from the source of the material.

The dome should not need a new mathematical model simply because the timber came from a different saw.

The finished part still has to meet the same dimensional definition.

SAFETY / ENGINEERING

Material source does not establish structural capacity. A wedge cut from a large tree is not automatically stronger because it came directly from a log. A commercially sawn board is not automatically appropriate simply because it has straight edges.

Structural use can depend on:

* species,
* grade,
* grain,
* knots,
* slope of grain,
* checks,
* splits,
* decay,
* moisture,
* member size,
* connection details,
* and the applicable design requirements.

Log-derived members may also fall outside ordinary assumptions used for standard dimensional lumber unless they are evaluated under an appropriate design method. For structural applications, the finished member has to be evaluated as the material and section it actually is.

REFERENCE BUILD

For the 20-foot 2V reference dome, the cleanest development path is to define the wedge member independently from the raw stock. The finished-part drawing should specify what the dome needs. Then we can develop at least two manufacturing routes.

**Route A — Dimensional lumber**

$$ \text{commercial blank} \rightarrow \text{wedge rip} \rightarrow \text{family length} \rightarrow \text{connection machining} \rightarrow \text{finished member} $$

**Route B — Log-derived timber**

$$ \text{log} \rightarrow \text{rough radial sector} \rightarrow \text{controlled blank} \rightarrow \text{finished wedge profile} \rightarrow \text{family length} \rightarrow \text{connection machining} \rightarrow \text{finished member} $$

Both routes should end at the same inspection drawing if they are producing the same member family. That is the important part.

The tree and the board are starting materials.

The wedge is the part.

<!-- NOTES
SECTION GOAL: Explain 'Using lumber versus logs' as it applies to 2. The Wedge Method.

Development requirements:
- Start with the practical purpose before theory.
- Identify whether the material is geometry, build note, design variation, experimental, or safety/engineering.
- Add exact dimensions only when verified for the stated configuration.
- Recommend a figure when the idea is spatial or difficult to understand from prose alone.
- Record the actual tool setup, workholding, cut order, repeatability method, and measured tolerance when available.
- Describe failure modes and common fabrication errors where they are known from documented work.

Suggested development markers:
[FIGURE: Using lumber versus logs illustrated for the wedge-method system]
[SOURCE NEEDED: any external technical claim used in Using lumber versus logs]

--- LLM DEVELOPMENT RETURN ---
[FIGURE: Side-by-side process diagram comparing dimensional lumber route and log-derived route, both converging on the same finished wedge-member specification.]

[FIGURE: Rectangular lumber cross-section with a symmetric wedge nested inside it, showing wi, wo, stock width W, thickness, saw kerf, and removable offcuts.]

[FIGURE: Two mirrored wedge-layout concepts inside one rectangular blank, with kerf shown explicitly rather than as a zero-width line.]

[FIGURE: Log end view divided into equal radial sectors with the rough sector angle theta_s labeled. Show that the rough sector is not automatically the finished wedge.]

[FIGURE: One log-derived sector progressing through pith-tip removal, outer-surface cleanup, datum establishment, and final controlled wedge profile.]

[FIGURE: Longitudinal log diagram showing butt diameter, smaller top diameter, natural taper, pith path, sweep, and how the smallest usable section can limit finished wedge size.]

[FIGURE: Eight-sector example using theta_s = 360 degrees / 8 = 45 degrees solely as a geometric illustration, clearly marked as NOT a prescribed reference-build wedge angle.]

[FIGURE: Rough radial wedge versus finished structural wedge, emphasizing the transition from natural surfaces to controlled manufacturing datums.]

[FIGURE: Crosscut strategy comparison: process a long log sector first and crosscut later versus crosscut log billets first and then produce sectors.]

[FIGURE: Hybrid material system showing log-derived field members, dimensional-lumber opening members, and smaller recovered offcuts used for secondary components.]

[TABLE: Lumber-versus-log development comparison with starting geometry, required preparation, flat reference surfaces, handling, drying considerations, tooling, material yield, repeatability, defect inspection, and finished-part inspection.]

[TABLE: Material-yield worksheet containing starting piece ID, starting dimensions/diameters, initial volume or board-foot measure, number of rough blanks, number of finished members, offcut use, rejected material, and final usable yield.]

[TABLE: Log survey sheet recording diameter at several stations, pith position, sweep, major knots, visible checks, moisture reading, usable length, proposed sector count, and recovered member families.]

[VERIFY: Measure actual saw kerf for the intended lumber and log-processing equipment before generating material-yield cutting diagrams.]

[VERIFY: Do not assume the rough radial sector angle is equal to the required structural wedge angle. Derive the finished profile independently from the reference-dome geometry.]

[VERIFY: Determine the minimum log diameter required at the smallest end to recover each intended finished wedge profile after kerf, pith removal, cleanup, and defects.]

[VERIFY: Determine whether log-derived blanks will be processed green, partially dried, or dried before final wedge machining and record how final dimensions are checked afterward.]

[VERIFY: Measure actual diameter taper along representative logs before publishing expected wedge counts per tree.]

[VERIFY: Test whether a long rough radial sector can be brought to a constant profile without excessive material loss caused by natural log taper.]

[VERIFY: Compare actual labor and usable yield for at least one dimensional-lumber batch and one log-derived batch before making efficiency claims.]

[AUTHOR INPUT NEEDED: Record the author's intended primary log-breakdown method, including sector count, log-length strategy, saw system, workholding, and how the pith-side tip is converted into the finished narrow face.]

[AUTHOR INPUT NEEDED: Decide which material route is the main worked reference-build method and which is presented as the variation. Both can remain in the book, but the fabrication chapters will be clearer if one carries the primary step-by-step procedure.]

[SOURCE NEEDED: Structural statements involving wood species, grading, moisture, shrinkage, checks, slope of grain, log-derived structural members, or allowable design values require appropriate timber-engineering, forestry, or building-code sources.]
-->
