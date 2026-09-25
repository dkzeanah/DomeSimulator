---
title: Inward-pointing wedge geometry
kind: section
---

# Inward-pointing wedge geometry

The wedge does not actually have to come to a sharp point for its geometry to have a point.

That distinction is useful.

The physical member has a narrow inside face and a wider outside face. If we extend the two tapered sides inward beyond the actual timber, those sides eventually intersect.

That imaginary intersection is the virtual point of the wedge. For the basic wedge method, that point is directed toward the interior of the dome. The timber itself is therefore a truncated wedge.

We are using only the useful section between the narrow interior face and the wider exterior face instead of continuing the material all the way to a sharp edge.

GEOMETRY

Look at a wedge member directly from the end. For a symmetric wedge, the two side faces spread away from a centerline by equal amounts.

The narrow width is:

$$ w_i $$

The outside width is:

$$ w_o $$

The distance between those two faces is:

$$ t $$

The total widening is:

$$ \Delta w=w_o-w_i $$

Because the wedge is symmetric, each side moves outward by:

$$ \frac{\Delta w}{2} $$

over the thickness \(t\).

The half-angle of the wedge is therefore:

$$ \beta=\tan^{-1}\left(\frac{w_o-w_i}{2t}\right) $$

and the total included wedge angle is:

$$ \alpha=2\beta $$

or:

$$ \alpha=2\tan^{-1}\left(\frac{w_o-w_i}{2t}\right) $$

That is the same basic wedge relationship used earlier, but now we can give it a physical meaning. If we extend the tapered sides inward, they meet at the virtual point.

The narrow face of the timber is simply stopping before the wedge reaches that point.

THE VIRTUAL APEX

For a symmetric wedge, we can calculate how far the narrow face sits from the virtual apex.

Let that inward distance be:

$$ r_i $$

At that distance, the width of the wedge is:

$$ w_i=2r_i\tan\left(\frac{\alpha}{2}\right) $$

so:

$$ r_i= \frac{w_i} {2\tan\left(\frac{\alpha}{2}\right)} $$

The outside face is another thickness \(t\) farther from the virtual apex:

$$ r_o=r_i+t $$

and its width becomes:

$$ w_o=2r_o\tan\left(\frac{\alpha}{2}\right) $$

Because both widths belong to the same pair of taper lines, another useful form is:

$$ r_i=\frac{t\,w_i}{w_o-w_i} $$

and:

$$ r_o=\frac{t\,w_o}{w_o-w_i} $$

These relationships are useful because they show what "pointing inward" actually means. The wedge sides can be imagined as radiating from a common line or point located inward from the physical timber.

The member gets wider as we move away from that virtual apex.

A SHARP WEDGE IS NOT REQUIRED

If the member actually continued all the way to its theoretical point, the inside width would become zero.

That would give us:

$$ w_i=0 $$

For structural timber, that is generally not the shape we are trying to produce.

We need real wood remaining on the interior side.

We may need room for:

* fasteners,
* bearing surfaces,
* plates,
* panel attachment,
* edge distance,
* and practical handling.

So the useful member is a truncated wedge. We preserve the angular relationship without cutting the timber down to a knife edge.

This also gives us another way to design the member.

Instead of thinking only:

"What saw angle makes this wedge?"

we can think:

"What angular relationship are we trying to represent, and where do we want to truncate that wedge into a usable timber section?"

Those are different questions.

THE VIRTUAL POINT IS NOT AUTOMATICALLY THE CENTER OF THE DOME

This is an important distinction. The wedge points inward, but that does not automatically mean that extending every wedge side will make it intersect at the exact center of the geodesic sphere.

There are several different geometric references in the structure:

* the sphere center,
* the theoretical dome vertices,
* the theoretical chord lines,
* the triangular face planes,
* the physical timber,
* the panel surfaces,
* and the wedge's virtual apex.

Those relationships have to be modeled. They should not be assumed. A useful local wedge can point generally toward the dome interior without its extrapolated taper lines literally intersecting at the global center of the sphere.

The exact relationship depends on how the wedge is defined around each geodesic edge. This matters because a dome is not made from radial spokes running from the center to the surface. The struts run between neighboring vertices.

They are chords.

The inward-pointing wedge geometry exists around those chord directions.

LOCAL GEOMETRY

It is useful to think of each wedge as having its own local coordinate system. Along the member is the longitudinal direction. Across the member is the side-to-side direction.

From the narrow face toward the wide face is the inward-to-outward direction.

That gives us three useful local axes:

$$ L=\text{along the strut} $$

$$ W=\text{across the strut} $$

$$ R=\text{inward/outward through the wedge} $$

The geodesic model can tell us where the strut belongs in global three-dimensional space. The local member definition tells us what the timber looks like around that line. This is similar to defining a part in CAD.

First define the coordinate system. Then define the section. Then place the finished part into the assembly.

That prevents the shape of the timber from becoming confused with the position of the timber.

THE WEDGE AND THE FACE-TO-FACE ANGLE

Two neighboring dome triangles are not normally coplanar. They meet with a change in direction along their shared edge. That face-to-face relationship is one of the reasons the wedge exists.

The tempting shortcut would be to take the dihedral angle between those faces and call that the required wedge angle.

That should not be done automatically.

The physical wedge angle depends on how the timber is positioned relative to:

* the theoretical shared edge,
* the neighboring face planes,
* the panel surfaces,
* the timber thickness,
* and the connection datum.

If the tapered side faces of the wedge are deliberately designed to align with particular panel or face planes, then there will be a direct geometric relationship between the wedge and those planes. If the panels sit on another surface of the timber, or if the timber is offset from the theoretical chord, the relationship changes.

So the correct process is:

calculate the face geometry, define the physical reference system, then derive the wedge from that model.

Do not simply copy a dome angle onto the table saw and assume the same number applies.

THREE MEMBERS

With three wedge members forming one triangle, each member follows the same general rule. The narrow portion is directed toward the interior. The wider portion extends outward.

But the important geometry is easier to see when we stop looking at the whole triangle and inspect one shared edge. That edge has one triangular face on one side and another face somewhere else in the completed dome on the other side. The wedge occupies physical space around that edge.

Its profile gives us a controlled way to transition outward from the narrower interior frame toward the larger exterior envelope. When several wedges are connected into one triangle, the interior perimeter and exterior perimeter are therefore not exactly the same shape or size. The exterior side of the triangular assembly occupies a larger envelope because every edge member widens outward.

That becomes important later when we design skins and panels. A panel fitted to the exterior cannot automatically use the same dimensions as a panel fitted to an interior reference surface.

FIVE- AND SIX-MEMBER VERTICES

The inward-pointing idea becomes easier to see at a complete vertex. Imagine several wedge members meeting around one point. From the interior, their narrow sides gather around the connection.

Moving outward, each member becomes wider. The group therefore expands as it approaches the exterior side of the structure. At a five-member vertex, five wedges participate in that pattern.

At a six-member vertex, six do. The exact angles around those vertices depend on the selected geodesic geometry.

The general wedge orientation stays the same:

narrow toward the inside, wide toward the outside. This gives us a useful visual check.

If one member at a vertex appears to flare inward while every neighboring member flares outward, that member deserves inspection before the assembly continues.

THE WEDGE CREATES TWO DIFFERENT ENVELOPES

Once the member has thickness and taper, the structure has more than one geometric envelope. There is an interior structural envelope. There is an exterior structural envelope.

There may also be a theoretical chord or centerline geometry somewhere between them.

If panels or skins are added, more surfaces appear:

* interior finish surface,
* insulation boundary,
* exterior sheathing surface,
* weather surface.

These surfaces are offset from one another. They do not have identical triangle dimensions. This is one of the reasons the wedge should be modeled as a three-dimensional member instead of only as a line on a dome calculator.

A line model is enough to determine the underlying geodesic topology. It is not enough to determine every physical panel dimension. The more functions we add to the wedge, the more those offsets matter.

DESIGN VARIATION

The virtual-apex idea also gives us a way to compare different wedge profiles. Two wedges can have the same included angle but different inside and outside widths. They simply represent different truncated portions of the same theoretical wedge.

For example, one member could begin closer to the virtual apex and therefore have a narrower inside face. Another could use the same taper angle but be shifted farther outward, producing both a larger inside width and a larger outside width. The angular relationship would remain the same while the amount of timber changes.

This can become useful when evaluating:

* different structural member sizes,
* larger connection zones,
* panel attachment requirements,
* different timber thicknesses,
* or laminated sections.

The wedge angle and the wedge size are related, but they are not the same thing.

A wedge should therefore not be specified only by saying:

"Cut this angle." We also need to know where that angle is truncated into the finished member.

MATERIAL YIELD

This also matters when wedges are cut from rectangular lumber. Suppose the required taper angle is already known. There may still be several possible ways to position that wedge inside a rectangular blank.

One layout might produce the widest possible interior face. Another might allow two mirrored wedges to be recovered from one board. Another might leave an offcut useful for another part.

The geometric requirement sets limits. The material layout determines how efficiently we produce that geometry. The same principle applies to a log.

Several rough wedge sectors can radiate around the log center. Those rough sectors already resemble the general inward-pointing geometry, but their final dimensions still have to be brought under control. The fact that a log naturally divides into radial sectors is useful.

It does not eliminate the need to define the finished wedge. FABRICATION ERROR: MOVING THE VIRTUAL APEX A useful way to understand wedge-profile error is to think about what happens to the virtual apex.

If the outside width is cut too large while the inside width and thickness stay fixed, the wedge angle increases. The extrapolated sides meet closer to the timber. If the outside width is too small, the wedge angle decreases.

The virtual apex moves farther away. If one side is cut differently from the other, the virtual apex shifts sideways. So a fabrication error is not only changing the dimensions of a piece of lumber.

It is changing the geometry that piece represents. This is why a wedge jig should control both sides from a known reference. Repeatedly producing a slightly wrong profile means repeatedly producing the same wrong angular relationship.

BUILD NOTE

When the first controlled wedge batches are produced, the inspection record should include enough information to reconstruct the actual cross-section.

At minimum:

* inside width,
* outside width,
* thickness,
* left-side taper,
* right-side taper,
* measurements at more than one point along the member.

From those measurements, the actual wedge angle can be calculated. If a symmetric target was intended, left and right measurements can also show whether the finished profile remained centered. This gives us a better quality-control method than simply recording the table-saw setting.

The saw setting is an input. The finished timber is the output.

The output is what belongs in the dome.

TOOL SETUP

There are several possible ways to create an inward-pointing wedge. A rectangular blank can be run through a taper jig. A fence can be positioned to remove a controlled amount from each side.

A long blank can be processed into continuous wedge stock and then crosscut into individual struts. Larger timber can be resawn. A rough radial sector can be recovered from a log and then refined.

The actual reference-build procedure should eventually document:

* what surface is established first,
* how the stock is restrained,
* which side is cut first,
* how the second cut references the first,
* how the centerline is maintained,
* how long material is supported,
* and how the final profile is checked.

A wedge can be geometrically simple on paper and awkward to manufacture safely if the stock is poorly supported.

The jig and workholding are therefore part of the method.

SAFETY / ENGINEERING

The inward-pointing shape should not be confused with proof of structural behavior. A wider exterior section and narrower interior section change the timber cross-section.

The narrow side may become important around:

* bolt holes,
* screw locations,
* notches,
* bearing areas,
* plates,
* and panel connections.

The usable narrow width cannot be reduced indefinitely simply because the taper geometry continues mathematically toward a point. At some point there may not be enough material for the intended connection or structural demand. That limit has to come from the actual member and connection design.

The mathematical wedge can reach zero width.

The structural timber does not need to.

REFERENCE BUILD

For the 20-foot 2V reference dome, the wedge should eventually be defined from a full three-dimensional model.

For every relevant edge condition, the model should establish:

1. the theoretical chord,
2. the neighboring triangular faces,
3. the chosen physical datum,
4. the inward/outward direction,
5. the member thickness,
6. the required wedge taper,
7. the inside width,
8. the outside width,
9. the connection geometry,
10. and the resulting panel or shell surfaces.

Once those relationships are fixed, the inward-pointing wedge stops being a concept and becomes a shop dimension. We will be able to say exactly what part to cut and why it has that shape.

Until then, the important geometric rule is this:

The physical member is a truncated wedge. Its virtual point lies inward. Its section becomes wider as it moves outward.

And its exact dimensions have to be derived from the physical dome system, not guessed from the appearance of the finished structure.

<!-- NOTES
SECTION GOAL: Explain 'Inward-pointing wedge geometry' as it applies to 2. The Wedge Method.

Development requirements:
- Start with the practical purpose before theory.
- Identify whether the material is geometry, build note, design variation, experimental, or safety/engineering.
- Add exact dimensions only when verified for the stated configuration.
- Recommend a figure when the idea is spatial or difficult to understand from prose alone.
- Record the actual tool setup, workholding, cut order, repeatability method, and measured tolerance when available.
- Describe failure modes and common fabrication errors where they are known from documented work.

Suggested development markers:
[FIGURE: Inward-pointing wedge geometry illustrated for the wedge-method system]
[SOURCE NEEDED: any external technical claim used in Inward-pointing wedge geometry]

--- LLM DEVELOPMENT RETURN ---
[FIGURE: Symmetric truncated wedge cross-section with the two side faces extended inward as dashed lines until they meet at the virtual apex. Label wi, wo, t, alpha, ri, and ro.]

[FIGURE: Same wedge shown as part of a complete theoretical sharp wedge so the reader can see that the structural timber is only a truncated portion of the larger geometric shape.]

[FIGURE: Diagram explicitly separating sphere center, theoretical chord, physical wedge, and wedge virtual apex so the reader does not assume they are automatically the same point/reference.]

[FIGURE: Local coordinate system for one wedge member showing L along the member, W side-to-side, and R inward-to-outward.]

[FIGURE: Two neighboring triangular faces and their shared geodesic edge beside a physical wedge placed around that edge. Show that the relationship between face planes and wedge sides must be deliberately defined.]

[FIGURE: Three-member triangular assembly showing different interior and exterior perimeter envelopes caused by the outward widening of all three wedge members.]

[FIGURE: Five-member vertex with dashed extensions of wedge tapers toward the interior to emphasize the inward-pointing geometry.]

[FIGURE: Six-member vertex where applicable using the same graphical convention.]

[FIGURE: Two wedges with the same taper angle but different truncation positions, demonstrating that wedge angle alone does not completely specify the member.]

[FIGURE: Fabrication-error diagram showing correct virtual apex, excessive taper moving the apex closer, insufficient taper moving it farther away, and asymmetric cutting shifting the apex sideways.]

[FIGURE: Dimensional-lumber blank with several possible wedge placements to illustrate that the geometric wedge profile and the material-yield layout are separate design problems.]

[TABLE: Wedge geometry worksheet with inside width, outside width, thickness, total width change, left offset, right offset, half-angle, included angle, virtual-apex offset, profile family, and inspection measurements.]

[VERIFY: Determine whether the side faces of the reference wedge are intended to align directly with neighboring triangular face planes, panel planes, or another physical reference surface.]

[VERIFY: Establish the exact relationship between the wedge virtual apex, theoretical chord, fastener centerline, and neighboring face geometry before deriving production wedge angles.]

[VERIFY: Use the completed 3D reference model to determine whether one common inward-pointing wedge profile can satisfy all field edges or whether the selected 2V geometry requires multiple profile families.]

[VERIFY: Once the wedge profile is selected, calculate and record the virtual-apex offset from the physical narrow face as an additional geometric cross-check.]

[VERIFY: Determine the minimum practical inside width from the final connection design rather than from geometry alone.]

[VERIFY: Measure actual produced profiles and calculate their resulting included angles instead of relying only on machine settings.]

[AUTHOR INPUT NEEDED: Decide whether the book's diagrams should call the extrapolated intersection the "virtual apex," "virtual point," "wedge apex," or another term. Use one term consistently once selected.]

[AUTHOR INPUT NEEDED: Document the actual taper-cutting method after prototype production so this section can later include the real saw/jig/workholding sequence.]

[SOURCE NEEDED: Structural limits on narrow-section dimensions, fastener edge distances, connection zones, and reduced timber sections require appropriate timber-design or building-code references once the physical connection is finalized.]
-->
