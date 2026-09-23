# KDP layout adaptation — how the guidance was applied

Status: **applied, 2026-09-17.** This page maps the publisher's layout
guidance for an illustrated construction manual onto the book as it
actually exists, section by section, and names what was changed and what
was deliberately left alone.

## What the book already was

The book is a two-part manual built on a computed manuscript: 68 chapters
(24 written, the rest scaffolds), 885 live number tokens, 77 figures, every
figure generated at build time by the project's own solver. It is already
calculation-driven, already separates claims by status, and already prints
the unflattering numbers. The guidance below is therefore an adaptation,
not a restructure: the book's machinery is its selling point, and none of
it was thrown away.

## The adaptation, section by section

| Guidance | Where it lands in this book |
|---|---|
| Introduction to geodesic domes (what a dome is, frequencies, why triangles, hub-and-strut vs panelized) | Part 1: *Why a Dome Lets You Do This* (Ch. 6–11) — triangles, axial loads, the 2V frequency chapter (Ch. 14), the not-a-worse-2x4 comparison (Ch. 7) |
| Where the wedge method differs | Ch. 6–7, 15–18: the pinwheel, the hubless lap, why the wedge points in |
| The Wedge Method (cutting wedges, orientation, why the point faces in, how members meet, material efficiency) | Ch. 12–19: split like a cake, the pinwheel, the seam and its key, the wedge-versus-board audit |
| Geometry (chords, radius/diameter, 2V ratios, triangle dimensions, dihedral and compound angles, wedge angles, scaling) | Ch. 20–23: the two calculations and the round trip. Method A is the scaling chapter — the k·D relationships are derived, not stated, and the round trip proves both methods are one calculation |
| Making the members (logs vs dimensional lumber, ripping, saw setups, jigs, stops, labelling, tolerance, grain, moisture) | Ch. 26–38: the fortnight, the saw, the jig, panel drawings, where error goes |
| Connections (screwed, bolted, plates, brackets, wood-to-wood, temporary vs permanent) | Ch. 17 (the key), Ch. 4 (the V-bracket), Ch. 47 (what broke — the screwed-not-bolted correction) |
| Building the dome (foundation layout, base ring, courses, bracing, apex, error correction, lifting) | Ch. 39–41: footing and ring, closing the shell, the fortnight's raise |
| Variations of the wedge system (solid, split, laminated, log-derived, standard lumber, skins, removable panels, glazing, openings) | Ch. 49–50 (frequencies, species), Ch. 41 (doors/windows/rim), Part 2's shell ladder (Ch. 60) and skin chapters (Ch. 57, 59) |
| The dome as a building system (utilities, weather sealing, replaceable shell, central column) | Ch. 43–44 (inside a round room, heat/power), Part 2's pad and utility column (Ch. 64) |
| Foundations and interfaces (slab, ring, piers, raised floor, mobile, pad attachment) | Ch. 39, and Part 2's foundation-share and pad chapters (Ch. 63–64) |
| Example builds (shed, workshop, 20-ft, cabin, greenhouse, semi-mobile, larger residential) | The dome catalogue runs through Part 2 (Ch. 61–67): the Creator's shipped designs, the three dome classes, the pad catalogue. A dedicated example-builds gallery is the one section the book does not yet carry in full and is the natural next chapter of work |
| Cut lists and reference tables | The back matter's Master Tables: full cut list, seam schedule, butt-cut setups, declared constants — written and exported |
| Design possibilities (multiple domes, lofts, partial domes, dome-on-knee-wall, removable shell, pads, kits) | Part 2 Ch. 65–67 (rotation, iris, network) and the closing audit (Ch. 68), each labelled as design possibility |

## The three kinds of information

The guidance's central distinction — known geometry, tested construction,
design possibility — is now stated in the book's front matter (title
pages) and restated in the closing audit, where the claim table's statuses
map onto it: **measured** = tested construction, **modelled** = known
geometry with declared constants, **proposed** = design possibility. Every
experimental idea in the book (rotation, iris, network) carries the
proposed label where it appears.

## The engineer's note

The front matter now carries the disclaimer, in the book's own voice: the
book documents methods, geometry and prototypes; it is not a substitute
for site-specific structural engineering; anything for permanent occupancy
should be reviewed by a qualified engineer and the local authority. It
sits on the copyright page, where a reader meets it before any claim.

## What was deliberately not changed

- **The title.** *2 Trees: Build Your (D)Home* is already distinctive and
  already names the wedge method in its subtitle ("120 wedge struts").
  Changing it now would orphan every existing export and reference; if a
  KDP listing wants the search phrase, the subtitle line can carry "the
  wedge method for hubless geodesic domes" at upload time.
- **The page size.** The export is US letter, which is the guidance's
  8.5×11 choice; the PDF print stylesheet already sets it.
- **The prose voice.** First person, blunt, corrections on camera. The
  guidance's style is a publisher's; the book's voice is the author's, and
  the credibility machinery (computed figures, declared constants, the
  closing audit) is the stronger version of the same idea.
- **Kindle.** Not designed for; fixed print layout first, per the
  guidance.

## Illustrations are film frames, not sketches

The book's plates of the dome itself are real film stills. The
frontispiece, the worked build's plate and the raising plate are frames of
the decluttered wedge film — the orientation chapter at 425 s, the assemble
chapter at 842.5 s and the closing shot at 973 s respectively — copied out
of the stills archive as 1920×1080 frames, so a plate and the film cannot
disagree about what the dome looks like. On a machine with PyOpenGL the
same figure re-renders that exact second; without it, the archived frame is
used. (The frankendome plate names the film's settle chapter, at 158 s;
that frame still awaits a PyOpenGL machine or the launcher's shots action.)

## What remains, in order

1. The 44 unwritten Part 1 chapters (the manual's body) — the next big
   writing pass.
2. The example-builds gallery the guidance calls for.
3. The two film-still figures, once a machine with PyOpenGL renders them.
4. Print-only finishing at upload time: bleed on full-page plates, a
   paperback cover, and the KDP-format interior if the print run wants the
   6×9 fallback.
