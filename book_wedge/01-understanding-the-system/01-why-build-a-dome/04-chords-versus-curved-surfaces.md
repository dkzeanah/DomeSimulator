---
title: Chords versus curved surfaces
kind: section
---

# Chords versus curved surfaces

A dome may follow a curved surface, but the timber member between two connection points is straight. That difference is where the chord comes in. If we mark two points on a circle or sphere, there are two basic ways to describe the distance between them.

One is to follow the curved surface. The other is to connect the two points directly with a straight line.

That straight line is a chord.

GEOMETRY

For dome construction, the structural member normally follows the chord between two vertices rather than following the curved surface of the sphere.

If two points on a circle are separated by a central angle \(\theta\), and the sphere or circle has radius \(R\), the straight chord length between those points is:

$$ c = 2R\sin\left(\frac{\theta}{2}\right) $$

where:

* \(c\) is the straight chord length,
* \(R\) is the radius,
* and \(\theta\) is the central angle between the two points.

The curved distance along the circle between the same two points is the arc length:

$$ s = R\theta $$ when \(\theta\) is measured in radians. Those two distances are not the same.

The arc follows the curve. The chord cuts straight across between the endpoints. For any normal dome segment, the chord is shorter than the arc connecting the same two points.

That matters because we are cutting straight structural members. If a calculator gives us the spherical surface distance but we cut a straight timber to that number, the member will be too long for the chord it is supposed to occupy. The dome geometry therefore has to distinguish between the mathematical sphere we are approximating and the straight pieces we are actually building from.

STRAIGHT MEMBERS, CURVED RESULT

A geodesic dome does not need its struts bent into the spherical radius. Each individual strut is straight. The curved form appears because the endpoints of those straight struts are positioned on or near the intended spherical geometry.

A single triangle is flat. The triangle beside it is also flat. But the two triangles do not remain in the same plane.

They meet at an angle. Repeat that relationship over many faces and the collection of flat triangles begins to surround a volume that approximates part of a sphere.

This gives us three different things that are easy to accidentally treat as one:

1. the ideal curved sphere,
2. the flat triangular faces approximating that sphere,
3. the straight structural members forming the edges of those faces.

They are related, but they are not geometrically identical. A drawing of a smooth sphere represents the intended overall surface. A geodesic frame replaces that smooth surface with flat triangular facets.

The timber then forms the straight edges of those facets.

THE GAP BETWEEN A CHORD AND THE CURVE

We can also describe how far a chord falls inside the ideal curved surface. For a circular section, the maximum distance between a chord and the corresponding arc occurs at the midpoint of the chord.

That distance is commonly called the sagitta.

If the radius is \(R\) and the chord length is \(c\), it can be calculated as:

$$ h = R-\sqrt{R^2-\left(\frac{c}{2}\right)^2} $$

where:

* \(h\) is the sagitta,
* \(R\) is the radius,
* and \(c\) is the chord length.

This gives us a useful way to think about frequency. Longer chords create larger flat facets across the curved surface. Shorter chords generally reduce the distance between each flat facet and the ideal spherical surface.

That is one reason increasing frequency makes the finished form appear smoother. We are not making the members curved. We are using more, smaller straight sections to approximate the curve more closely.

WHY THIS MATTERS WHEN BUILDING

This distinction affects more than the mathematical drawing. It affects where the shell sits. It affects how neighboring panels meet.

It affects the outer profile of the dome. It can also affect how we define the diameter. Suppose somebody says they are building a 20-foot dome.

That sounds specific, but we still need to know what surface the 20 feet refers to.

It could mean:

* the diameter through the theoretical spherical vertex locations,
* the outside face of the structural frame,
* the inside face of the structural frame,
* the outer surface of the enclosure,
* or another construction reference.

Those numbers do not have to be identical once the frame has real thickness. For mathematical work, the cleanest starting point is usually a defined spherical radius and a defined set of vertex locations. Physical timber dimensions can then be developed around that geometry.

The alternative is dangerous: allowing the thickness of the material to silently change the geometry while still using calculations based on another radius.

THE WEDGE METHOD AND THE SPHERICAL SURFACE

This distinction becomes particularly important with wedge-shaped members. A rectangular strut has parallel major faces. A wedge member does not.

Its cross-section changes from a narrow interior side to a wider exterior side. Because of that, we need to be explicit about which line through the member corresponds to the calculated geodesic chord. Possible reference lines could include the interior edge, exterior edge, centerline, fastener centerline, or another deliberately chosen construction datum.

They cannot all represent the exact same spherical radius. If the calculated chord is based on vertex centerlines but the physical cut length is measured along the outside edge of a thick wedge, those two measurements may differ. That does not mean the geometry is wrong.

It means the mathematical model and the physical member are being measured from different references. The solution is to establish one reference system and keep using it. For example, the geometry may define every vertex from a common spherical center and establish each theoretical strut as the straight chord between those vertices.

The physical wedge can then be positioned around that theoretical line according to the joint design. Once that relationship is fixed, other dimensions can be derived from it instead of being guessed independently.

This is particularly useful when we start generating cut lists.

A cut list should not simply say:

"A strut = this long."

It should eventually make clear what that dimension represents.

Is it:

* theoretical vertex-to-vertex chord length,
* bolt-center distance,
* full timber length before end cuts,
* finished timber length,
* inside-edge length,
* or outside-edge length?

If we do not define that reference, two builders can use the same number and still manufacture different parts.

REFERENCE BUILD

For the 20-foot-diameter 2V reference dome, the process will be:

First, define exactly what the 20-foot diameter refers to.

Then establish the radius:

$$ R=\frac{D}{2} $$

If the defined mathematical diameter is 20 feet, then:

$$ R=10\text{ ft} $$

or:

$$ R=120\text{ in} $$ That radius alone is not enough to calculate every member. We still need the verified angular relationship between each pair of neighboring vertices in the selected 2V geometry.

Once a central angle \(\theta\) for a particular strut family is known, its theoretical chord can be calculated from:

$$ c = 2R\sin\left(\frac{\theta}{2}\right) $$ That gives us the straight geometric distance between those vertices. The physical wedge member can then be developed from that chord according to the connection method and whichever construction reference line we decide to use.

This order matters. We should not begin with the outside surface of a piece of lumber and try to make the spherical geometry conform to it afterward. We establish the geometry first.

Then we decide how the real material fits around it. That keeps the ideal dome, the straight chord, and the finished wedge member as three separate but connected parts of the same system.

<!-- NOTES
SECTION GOAL: Explain 'Chords versus curved surfaces' as it applies to 1. Why Build a Dome?.

Development requirements:
- Start with the practical purpose before theory.
- Identify whether the material is geometry, build note, design variation, experimental, or safety/engineering.
- Add exact dimensions only when verified for the stated configuration.
- Recommend a figure when the idea is spatial or difficult to understand from prose alone.
- Include the governing relationship or formula if it can be stated accurately.
- Include a worked reference-build example after the formula is verified.
- Record assumptions about sphere subdivision, truncation, and units.

Suggested development markers:
[FIGURE: Chords versus curved surfaces illustrated for the wedge-method system]
[SOURCE NEEDED: any external technical claim used in Chords versus curved surfaces]

--- LLM DEVELOPMENT RETURN ---
[FIGURE: Circle cross-section showing two vertex points, the curved arc between them, the straight chord between them, the radius to each point, central angle theta, and midpoint sagitta.]

[FIGURE: Three-stage diagram showing ideal smooth spherical surface, flat triangular geodesic facets, and straight timber members along the facet edges.]

[FIGURE: Enlarged dome cross-section showing the ideal spherical surface outside a straight chord to make the chord-versus-curve difference visually obvious.]

[FIGURE: Conventional rectangular strut and wedge strut placed around the same theoretical vertex-to-vertex chord centerline, with interior face, exterior face, and geometric reference line identified.]

[FIGURE: Diameter-reference comparison showing theoretical sphere diameter, structural centerline diameter, inside frame diameter, outside frame diameter, and finished shell diameter as different possible measurements.]

[TABLE: Define all dimensional reference terms used later in the book, including theoretical chord length, vertex-to-vertex distance, fastener-center distance, raw timber length, finished cut length, interior-edge length, and exterior-edge length.]

[VERIFY: Decide the permanent geometric reference line used for wedge members in this book before finalizing cut lists. Candidate references include theoretical chord centerline, fastener centerline, or another explicitly modeled datum.]

[VERIFY: Decide exactly what the stated 20-foot diameter of the reference build measures. Keep this definition consistent throughout all geometry, fabrication, shell, floor, and foundation chapters.]

[VERIFY: After the exact 2V geometry is frozen, calculate at least one verified reference-build example showing radius, central angle, theoretical chord, corresponding arc length, and sagitta for a selected strut family.]

[AUTHOR INPUT NEEDED: Decide whether builder-facing finished dimensions will primarily reference bolt centers, finished timber ends, wedge centerline, or another repeatable shop measurement. Mathematical chord values can remain separately listed even if the shop dimension uses a different datum.]
-->
