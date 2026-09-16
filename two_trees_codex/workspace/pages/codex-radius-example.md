# 8. Worked example: a ten-foot radius

Use a sphere radius of 10 feet, or 120 inches. The nominal diameter is 20 feet. Multiply the exact mesh factors by 120 to obtain a long chord of approximately 74.164 inches and a short chord of approximately 65.584 inches.

The panelized frame requires sixty members associated with A edges and sixty associated with B edges. These labels identify edge families, not necessarily just two physical cut lengths. A member's surrounding triangle and joint relationships can split a nominal family into multiple fabrication cases.

The enclosing base circle has area π × 10², approximately 314.159 square feet. The straight-sided decagonal base has area 5 × 10² × sin(36°), approximately 293.893 square feet. Neither quantity is the finished usable floor area after wall build-up, foundations, doors, and fittings. The circle is a useful reference; the polygon describes this mesh's base.

For a concrete physical comparison, the current raw-wedge solver with an eight-inch trunk diameter, point facing into the dome, raw-trapezoid seams, and no additional fabrication allowance produces a longest finished stock envelope of approximately 72.952 inches at this radius. That is different from the 74.164-inch nominal A chord because the member's actual ends and offsets are solved separately.

This example reveals why a six-foot blank cannot simply be assigned to a “six-foot dome edge,” and why the error does not always have the same sign. Some physical parts are shorter than the nominal edge; different settings and additional holding stock can change what the blank must provide. Inspect the physical schedule instead of assuming a fixed deduction.

The Sizing lab reproduces this example from the repository's solver. If the solver is revised, insert a fresh result page and retain the former page as a dated record. The published example should match the configuration and code version used to fabricate the actual frame.
