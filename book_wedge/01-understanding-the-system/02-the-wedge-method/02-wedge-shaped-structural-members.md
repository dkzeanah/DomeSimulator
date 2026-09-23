---
title: Wedge-shaped structural members
kind: section
---

# Wedge-shaped structural members

A wedge-shaped structural member is still a strut.

It still has to connect two vertices, hold its place in the triangle, and fit the other members around it.

The difference is in the cross-section.

Instead of carrying the same width from the inside of the dome to the outside, the member becomes wider toward the exterior.

That shape gives us another geometric variable to work with.

We are no longer defining a strut only by length.

We are defining it by length and profile.

For the wedge method, that profile is part of the building system.

GEOMETRY

A basic wedge member can be described with four primary dimensions:

* member length,
* inside width,
* outside width,
* thickness.

The difference between the outside and inside widths is:

$$
\Delta w = w_o-w_i
$$

where:

* \(w_o\) is the outside width,
* \(w_i\) is the inside width.

For a symmetric wedge, half of that width change occurs on each side of the member:

$$
x=\frac{w_o-w_i}{2}
$$

If the distance between the interior and exterior faces is \(t\), the taper angle on each side is:

$$
\beta=\tan^{-1}\left(\frac{x}{t}\right)
$$

or:

$$
\beta=\tan^{-1}\left(\frac{w_o-w_i}{2t}\right)
$$

The full included wedge angle is:

$$
\alpha=2\beta
$$

which gives:

$$
\alpha=2\tan^{-1}\left(\frac{w_o-w_i}{2t}\right)
$$

Those equations describe the physical cross-section once its dimensions are known.

They do not determine what the correct wedge should be for the dome.

That comes from the dome geometry and the way the neighboring faces are intended to meet.

A wedge can be mathematically consistent as a piece of timber and still be the wrong wedge for the structure.

THE MEMBER HAS TWO DIFFERENT GEOMETRIES

It helps to separate the strut into longitudinal geometry and cross-sectional geometry.

Longitudinal geometry runs from one end of the member to the other.

That includes:

* theoretical chord length,
* physical cut length,
* end cuts,
* fastener locations,
* and the relationship between the finished timber and the two vertices it connects.

Cross-sectional geometry is what we see when looking directly at the end of the member.

That includes:

* inside width,
* outside width,
* thickness,
* side tapers,
* centerline,
* and any grooves, rabbets, bevels, or panel seats added later.

Those two geometries solve different problems.

The length helps place the vertices.

The wedge profile helps the member occupy the space between neighboring faces.

Changing one does not automatically correct the other.

A member can have the correct wedge profile and still be too long.

It can have the correct length and still have the wrong taper.

For production purposes, both have to be inspected.

STARTING STOCK

A finished wedge may begin as rectangular dimensional lumber, a larger sawn timber, a laminated blank, or a rough section recovered from a log.

Whatever the source, the starting material needs a known reference.

With dressed lumber, that means recording the actual measured dimensions rather than relying only on the nominal lumber name.

The nominal size tells us what class of material we started with.

The actual measured size tells us what material is physically available for cutting the wedge.

Those are not interchangeable in the fabrication record.

If the wedge calculation requires a specific outside width, inside width, and thickness, the stock has to contain enough material to produce those dimensions after cutting and cleanup.

The first question is therefore not:

"What size board is this called?"

It is:

"What dimensions do I actually have?"

REFERENCE SURFACES

A repeatable wedge needs repeatable reference surfaces.

If every cut is referenced from a different irregular face, errors begin stacking on top of one another.

A controlled process should establish which surface is the datum.

That might be:

* the interior face,
* the exterior face,
* one side face,
* a centerline,
* or a fixture that locates the part independently of an unfinished edge.

Once that datum is chosen, later operations should reference it intentionally.

This becomes even more important when the starting material comes from rough-sawn timber or a log-derived sector.

A rough wedge may already have approximately the right shape, but "approximately wedge-shaped" is not enough for a repeated structural part.

At least some surfaces have to be brought under dimensional control.

SYMMETRIC AND ASYMMETRIC WEDGES

The easiest wedge to describe is symmetric.

Its left and right sides taper equally away from the centerline.

If the total width difference is:

$$
\Delta w=w_o-w_i
$$

then each side accounts for:

$$
\frac{\Delta w}{2}
$$

That gives the member a centered profile.

A wedge does not have to be symmetric, however.

DESIGN VARIATION

An asymmetric wedge could place more of the taper on one side than the other.

That might become useful if the connection system, panel geometry, fabrication method, or dome-face relationship requires it.

In that case, the left and right offsets should be recorded separately:

$$
x_L+x_R=w_o-w_i
$$

where:

* \(x_L\) is the width increase on the left,
* \(x_R\) is the width increase on the right.

If:

$$
x_L=x_R
$$

the wedge is symmetric.

If they differ, the member is asymmetric.

This distinction matters because an asymmetric member also gains a left-hand and right-hand orientation.

That increases the possibility of installing a geometrically correct part in the wrong direction.

Unless a later design requires asymmetry, a symmetric member is easier to manufacture, label, inspect, and reverse end-for-end.

THE CENTERLINE

The wedge needs a clearly defined centerline.

That centerline gives us a stable way to describe the part even though its side faces are angled.

It can be used to locate:

* fastener holes,
* end cuts,
* labels,
* panel features,
* and the member relative to the theoretical chord.

The physical timber does not automatically have to be centered on the mathematical chord.

That is a design decision.

But once that relationship is chosen, it should remain fixed.

For example, if the theoretical chord passes through the cross-sectional center of the wedge, that becomes one kind of member definition.

If the fastener-center line is offset from the geometric center of the wedge, that becomes another.

Both can be modeled.

What creates problems is changing references between calculations and shop drawings without stating it.

END GEOMETRY

The wedge profile describes the long body of the member.

The ends are another problem.

A member might terminate with:

* a square end,
* an angled end,
* a compound cut,
* a relieved end,
* a drilled connection zone,
* a plate interface,
* or another prepared joint.

The end treatment can change the physical overall length even when the theoretical chord remains unchanged.

For that reason, the final member drawing should eventually distinguish between at least:

$$
L_c=\text{theoretical chord length}
$$

and:

$$
L_f=\text{finished physical member length}
$$

If fastener centers define the structural reference, we may also need:

$$
L_b=\text{bolt-center to bolt-center distance}
$$

Those three numbers should not be assumed to be equal.

A production drawing has to tell the builder which one is being measured.

HOLES AND CONNECTION FEATURES

Drilling a wedge is also different from merely drilling a rectangular board if the angled side surfaces are being used as references.

A hole location should be defined from controlled dimensions.

That can include:

* distance from the end,
* distance from the member centerline,
* distance from the inside or outside face,
* hole diameter,
* drilling direction,
* and which surface the drill or jig references.

A hole that is shifted along the member changes the effective connection location.

A hole that wanders sideways may change edge distance or interfere with neighboring hardware.

A hole drilled at the wrong angle may prevent plates, washers, or neighboring members from seating correctly.

For repeated production, the drilling operation should eventually use a jig or fixed reference instead of being independently laid out on every member.

THE PROFILE HAS TO SURVIVE THE FULL LENGTH

A wedge is not useful if the correct dimensions exist only at one end.

The profile has to remain controlled along the member.

If the inside width changes unexpectedly from one end to the other, then the member contains a second taper running along its length.

That may happen intentionally with some future design.

For the basic wedge member, it should not happen accidentally.

This gives us another inspection problem.

Checking only one cross-section may miss:

* saw drift,
* stock taper,
* bow,
* twist,
* uneven feed,
* or a jig that moved during the cut.

A finished member may therefore need width checks at more than one location.

A practical inspection record might include:

* end A,
* midpoint,
* end B.

If the target profile is supposed to be constant, those measurements should show whether the production process is actually maintaining it.

TWIST

Twist deserves separate attention.

A member can have the correct width at both ends and still have one end rotated relative to the other.

That matters because the wedge has a defined inward and outward orientation.

If the cross-section twists along the member, the side surfaces no longer remain in the intended planes.

Some twist may originate in the stock.

Some may appear as timber dries.

Some may come from poor workholding during machining.

Whatever the cause, a member that cannot sit consistently in the intended geometry should not be treated as correct merely because its tape-measure dimensions match.

BUILD NOTE

The final inspection process for the reference build should include an actual method for checking twist.

That could be a flat inspection table, winding sticks, a dedicated fixture, a straightedge arrangement, or another repeatable method.

The method and acceptable measured variation should come from the actual build record rather than being invented here.

MEMBER FAMILIES

Different strut lengths do not automatically require different wedge profiles.

That depends on the geometry.

It is possible for several length families to share the same cross-section.

It is also possible that different edge relationships require different profiles.

Until the reference geometry is fully modeled, we should not assume either result.

This creates two separate classification systems.

A member can belong to a length family:

A, B, C, and so forth.

It can also belong to a profile family:

W1, W2, W3, and so forth.

If every strut uses the same profile, the system becomes simple.

For example:

A-W1

B-W1

If different profiles are required, the labeling system can still keep them distinct:

A-W1

A-W2

B-W1

The point is not the exact naming scheme.

The point is to avoid hiding multiple geometric properties inside one ambiguous letter.

A member family should tell us enough to manufacture the correct part.

FABRICATION FAILURE MODES

Several mistakes can produce a part that looks close but is not actually the correct member.

Wrong inside width:

The wedge may be too narrow or too wide at the interior.

Wrong outside width:

The face-to-face relationship changes even if the inside dimension is correct.

Wrong thickness:

The entire cross-sectional relationship changes and panel or connection dimensions may no longer align.

Unequal side taper:

A member intended to be symmetric becomes offset.

Longitudinal taper:

The profile changes from one end to the other.

Twist:

The wedge orientation rotates along the member.

Wrong finished length:

The triangular geometry changes.

Wrong end treatment:

The theoretical geometry may be correct while the physical members interfere or leave unintended gaps.

Wrong drilling:

The connection reference moves.

Wrong label:

A perfectly manufactured part can still be installed in the wrong position.

Reversed orientation:

The wide side and narrow side trade places relative to the dome.

Those failures should eventually be incorporated into a shop inspection sheet.

A finished member should be accepted because it matches its definition, not because it looks close enough to the previous piece.

REPEATABLE FABRICATION

The production goal is to convert all of those dimensions into controlled operations.

One possible sequence is:

1. inspect the starting stock,
2. establish the primary datum,
3. cut the wedge profile,
4. verify the profile,
5. cut the member to its family length,
6. prepare the ends,
7. drill or machine connection features,
8. mark inward and outward orientation,
9. apply the member-family label,
10. perform final inspection.

The exact order may change once the actual tooling is developed.

For example, it may be easier to cut long continuous wedge stock first and crosscut individual struts afterward.

Another process may cut blanks to length before tapering.

A log-derived process may require an entirely different sequence.

That is why the actual shop setup has to be documented instead of assumed.

The final method should be selected based on repeatability, workholding, material yield, tool access, and the ability to inspect the result.

DESIGN VARIATION

Once the basic wedge is controlled, other features can be built into it.

The exterior portion could receive a panel seat.

The interior face could receive a finish strip.

A groove could locate a gasket.

A machined recess could locate a plate.

A laminated wedge could place stronger or more durable material where the connection occurs.

A replaceable exterior attachment could be added without changing the underlying chord geometry.

Those features create new member types, but they should all grow from the same controlled base profile.

The more functions a single timber performs, the more important its drawing becomes.

At that point, it is no longer enough to call it a "wedge strut."

It is a manufactured component with defined interfaces.

SAFETY / ENGINEERING

Removing material to create a wedge changes the physical cross-section of the timber.

Adding bolt holes, notches, grooves, rabbets, or other features changes it again.

Those changes can affect structural behavior.

The fact that a profile fits the dome geometry does not establish its capacity.

Structural evaluation has to use the actual finished section, actual material, actual connections, and actual loading conditions.

The same applies to defects in the starting timber.

A knot, split, check, or other defect does not disappear because the outside dimensions of the wedge are correct.

Dimensional inspection and structural material inspection are separate requirements.

For this book, the geometry defines the intended part.

Structural engineering determines whether that part is adequate for a particular building and load condition.

THE USEFUL WAY TO DEFINE A WEDGE MEMBER

By the time the system is fully developed, a wedge member should be describable without needing to hold the physical piece in our hands.

A complete member definition should eventually tell us:

* what stock it starts from,
* its actual finished length,
* its theoretical chord relationship,
* its inside width,
* its outside width,
* its thickness,
* its taper,
* its end geometry,
* its connection features,
* its inward/outward orientation,
* its member-family ID,
* its quantity,
* its inspection dimensions,
* and where it belongs in the dome.

Once all of those values are known, the wedge becomes something we can reproduce.

That is the point.

We are not trying to make a collection of similar-looking pieces of timber.

We are defining structural parts.

<!-- NOTES
SECTION GOAL: Explain 'Wedge-shaped structural members' as it applies to 2. The Wedge Method.

Development requirements:
- Start with the practical purpose before theory.
- Identify whether the material is geometry, build note, design variation, experimental, or safety/engineering.
- Add exact dimensions only when verified for the stated configuration.
- Recommend a figure when the idea is spatial or difficult to understand from prose alone.
- Record the actual tool setup, workholding, cut order, repeatability method, and measured tolerance when available.
- Describe failure modes and common fabrication errors where they are known from documented work.

Suggested development markers:
[FIGURE: Wedge-shaped structural members illustrated for the wedge-method system]
[SOURCE NEEDED: any external technical claim used in Wedge-shaped structural members]

--- LLM DEVELOPMENT RETURN ---
[FIGURE: Fully dimensioned generic wedge-member anatomy showing length, inside width, outside width, thickness, centerline, end A, end B, and inward/outward orientation.]

[FIGURE: Wedge end view showing symmetric taper with wo, wi, t, beta, and alpha labeled.]

[FIGURE: Symmetric wedge beside an exaggerated asymmetric wedge, with left and right offsets labeled separately.]

[FIGURE: Longitudinal view showing theoretical chord length, physical finished length, and bolt-center distance as three separate dimensional references.]

[FIGURE: Correct constant-profile wedge compared with unintended longitudinal taper and twist.]

[FIGURE: Three-station inspection diagram measuring wedge width at end A, midpoint, and end B.]

[FIGURE: Drilling-reference diagram showing hole location relative to end datum, member centerline, and inside/outside surfaces.]

[FIGURE: Member-family labeling example separating strut-length family from wedge-profile family, such as A-W1, B-W1, and A-W2.]

[FIGURE: Production sequence from starting stock through profile cutting, crosscutting, end preparation, drilling, orientation marking, labeling, and final inspection.]

[FIGURE: Fabrication failure board showing wrong width, asymmetric error, longitudinal taper, twist, wrong length, incorrect hole location, reversed orientation, and mislabeled member.]

[TABLE: Generic wedge-member specification sheet containing member ID, length family, profile family, quantity, theoretical chord, finished length, bolt-center distance, inside width, outside width, thickness, left taper, right taper, connection features, orientation mark, and inspection status.]

[TABLE: Three-station dimensional inspection sheet for end A, midpoint, and end B, with target, measured value, deviation, and pass/fail fields.]

[VERIFY: Determine whether the primary reference member is symmetric around its longitudinal centerline or requires an asymmetric profile.]

[VERIFY: Establish the permanent dimensional datum for wedge manufacture and state which surface or fixture controls every subsequent operation.]

[VERIFY: Determine whether profile cutting occurs before or after individual members are crosscut to length in the actual production workflow.]

[VERIFY: Determine whether long continuous wedge stock can be produced and then divided into multiple struts without unacceptable profile variation.]

[VERIFY: Measure actual stock dimensions before developing any cutting layout based on nominal dimensional-lumber sizes.]

[VERIFY: Determine which measurements must be checked at multiple locations along the finished member to detect longitudinal taper and twist.]

[VERIFY: Develop and test the actual drilling fixture before publishing hole coordinates, drill angles, or connection-center tolerances.]

[VERIFY: Determine whether the 20-foot 2V reference build requires one wedge-profile family or multiple profiles.]

[AUTHOR INPUT NEEDED: Record the actual saw, blade, taper jig/fence arrangement, workholding, feed method, and cut order used when the first controlled batch of wedge members is produced.]

[AUTHOR INPUT NEEDED: Select the final member-labeling convention, including how length family, wedge-profile family, orientation, and possibly installation location will be marked on the timber.]

[SOURCE NEEDED: Structural claims involving reduced or tapered timber cross-sections, knots and defects, drilled holes, notches, connection edge distances, or allowable loads require appropriate timber-engineering or building-code references.]
-->
