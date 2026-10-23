# sketch-gpt: standalone dome design studio specification

Use this entire specification with either language prompt below. Deliver running
software, build instructions, tests, and a generated sample release. Do not stop
at architecture, mockups, pseudocode, or a marketing site.

## Product

Build a desktop architectural modeling and documentation app named **sketch-gpt**.
It specializes in geodesic timber domes, especially duplicated triangular frames
made from raw log sectors with cyclic end-to-side pinwheel joints. Offer a
SketchUp-like workflow: orbit, pan, zoom, select, measure, snap, add, cut, move,
copy, hide, lock, group, section, undo/redo, and save. Use an original interface
and implementation; do not depend on SketchUp being installed.

The same authoritative model must drive the interactive viewport, dimensioned
drawings, fabrication schedules, promotional renders, and PDFs. Never substitute
a generic sphere mesh for the physical fabrication model.

## Geometry contract

Use double precision for geometry, inches internally, Z up, and explicit units
in every exchange format. Display inches, feet/inches, or metric without changing
the authoritative geometry. Assign stable IDs to topology vertices, faces, edges,
members, joints, seams, skins, props, and user-created pieces.

Separate nominal geodesic edges, physical member axes, maximum finished stock
lengths, uncut blanks, butt sacrificial tails, and head overfit. Each triangular
panel owns three distinct members, even where neighboring panels share a nominal
edge. Store receiving and butt planes, contact polygons, pinwheel handedness,
wedge orientation, seam allowance, and mate IDs. Enforce a closed directed
three-member cycle, a vertex-clean triangle envelope, finite coordinates,
positive lengths, coplanar contacts, and consistent outward normals.

Prefer porting and testing DomeSim's existing solvers when the repository is
available: `geodesic_raw_wedge_dome_dihedral.py`, `world3d/structures.py`,
`world3d/pieces.py`, `world3d/document.py`, `infill/base.py`, and
`infill/solids.py`. Existing solver output is the golden reference. If source is
unavailable, implement the solver explicitly and publish its assumptions; do not
claim parity until compared with known reference fixtures.

Keep foundation, deck, frame, seams, skin, fixtures, furnishings, dimensions, and
annotations on separate layers. All edits are commands with deterministic
replay, undo and redo. A project contains a schema version, units, solver
parameters/version, stable IDs, operation log, camera bookmarks, material
assignments, annotation objects, construction sequence, and export settings.
Reject malformed projects without altering the active document. Save atomically.

Parameters include frequency and dome cut where supported by the solver,
nominal long-edge length, log diameter, sector divisions, orientation,
handedness, seam treatment, and skin offset. Parameter changes invalidate
dependent geometry and schedules together. Do not scale a foundation or skin
independently and leave stale fabrication data attached.

## Workspace

Provide a project browser, central 3D viewport, layer tree, properties inspector,
scene/style library, construction timeline and sheet composer. Essential tools:

- Orbit/pan/zoom, standard orthographic views, perspective, section planes,
  clipping, exploded panels, fit model, and saved camera bookmarks.
- Click or box select, stable-ID search, hover highlights, snapping with visible
  feedback, numerical input, measuring, aligned dimensions and leader callouts.
- Add members from snapped endpoints; translate/rotate/copy; cut by a plane;
  remove/hide/lock; undo/redo; precise units in each numeric field.
- Select a panel to see its three member IDs, directed mates, nominal dimensions,
  physical cuts, cut-plane references and assigned construction step.
- Editable presentation props: bed, seating, kitchen and bathroom blocks, storage,
  lighting and plants. Label generic object dimensions as declared assumptions.
- Door/window design workflow that shows structural conflicts. A cosmetic hole
  in a skin must never imply that a structural member has been safely removed.
- A list of unresolved design decisions visible in the project and exports.

## Drawings and construction guide

Create editable sheets with title blocks, revision, units, scale bars, page
numbers, dimension styles, legends and linked viewport objects. Offer cover,
design basis/constants, site assumptions, plan, elevations, sections, foundation
layout, member/panel identity map, exploded assembly, joint details, individual
panel sheets, cutting schedules, seam schedule and inspection checklists.

Every dimension comes from geometry. Assumed prices, rates and prop sizes come
from an explicit visible constants table. Label estimates and unresolved details.
Keep baseline solver schedules separate from edited models until edits are
reconciled; block any "fabrication ready" claim for stale schedules.

Illustrate set-out, foundation, floor, stock preparation, panel fabrication,
lower course, frame closure, envelope and fit-out. Include the twelve physical
jig states: bare bench; reference triangle; axis rails; orientation fences;
cut planes; off-jig butt cut; first member; second member; third-member slide;
closed loop; flush heads; completed panel. Each state is generated from the real
fixture and current panel geometry. Each step has tools, inputs, actions,
callouts, a completed-state view, inspection criteria and prerequisites. Show
temporary bracing requirements as unresolved until a design is supplied.

Construction documentation must distinguish geometry from verified structural
design. Do not invent fastener capacities, code compliance, foundation bearing,
waterproof assemblies, lifting procedures or connection sizes. Support user-
supplied engineered details and record their provenance and revision.

Reference PDF import must accept local files, render pages for comparison, and
allow sheet style matching. Do not claim equivalence to reference PDFs that
have not been supplied or inspected.

## Rendering and exports

Use a real depth buffer, antialiasing, correct normals, physically meaningful
materials, sun/sky lighting, contact shadows and configurable backgrounds. Offer
clean technical linework, shaded architectural illustration and a high-quality
showcase preset. Include transparent cutaway, exploded panels and interior views.
Never show foundation timber through an opaque floor because of painter sorting.

Export vector PDF/SVG drawings, CSV schedules, JSON project and manifest, and
OBJ plus glTF/GLB with explicit unit metadata. Preserve labels as PDF text and
draw technical linework as vectors where possible. Supply a calibration bar and
printer instructions for genuinely full-scale tiled templates; fit-to-page
references must say they are not cutting templates.

Each export creates a new numbered, immutable release folder. Include PDF,
source project, mesh exports, schedules, landscape and portrait promotional
images, thumbnails, platform copy, assumptions, validation report, solver hash,
operation hash and SHA-256 file manifest. Never overwrite existing deliverables.
Use temporary files and atomic finalization so a failed export is visibly
incomplete and never presented as a completed release. Make long jobs cancellable.

## Acceptance tests

1. A reproducible default project produces stable topology, IDs, member counts,
   stock lengths and cut-plane normals; compare with golden solver fixtures.
2. Changing a parameter changes the frame, dimensions, schedules and PDF together.
3. Add, cut, move and copy a member; undo/redo all changes; save/load reproduces
   geometry and hashes. Reject NaN, degenerate cuts and corrupt/unsupported files.
4. Picking matches visible depth. Test occluded pieces and orthographic views.
5. Inspect stills for every construction and jig stage before a full release.
6. PDF text contains correct computed values, embedded fonts, units and complete
   labels. Render every page and inspect for clipping, overlap and empty views.
7. Re-export twice: two distinct releases, unchanged hashes for the first release.
8. Export counts and identities match the project. Edited fabrication data is
   regenerated or clearly marked invalid; no silent baseline substitution.
9. Package sample project, sample release, screenshots, dependency licenses,
   documented build commands and a working native app. Describe remaining gaps.

## Implementation sequence

Deliver vertical slices: authoritative geometry and fixture tests; viewer and
selection; document edits and persistence; linked technical drawings; staged
guide; rendering; immutable release exporter; packaged app. Keep the application
working at every milestone. Choose current stable library versions and verify
their official documentation when implementing; do not fabricate API calls.

## Cinematic production and episodic characters

Extend the same modeled world with a director workspace. Provide real-time GPU
first-person scouting at eye height and an inertial drone rig with pitch/yaw,
vertical movement, speed, acceleration/damping, focus selection, lens changes and
camera-path recording. State whether structural collisions are simulated. Keep
metres, internal model units and sensor/lens units explicit at their boundaries.

Provide editable hold, push-in, pull-out, slider, pan, tilt, orbit, crane, dolly
zoom and spline shots. Distinguish moving the camera, turning it and changing
focal length. Solve dolly-zoom framing from the actual subject distance. Support
timestamped eye/target/lens keys, selectable easing and uniform-time resampling
of recorded motion. Provide thirds, safe areas, horizon and aspect guides, plus
separately composed landscape/phone outputs. A recorded camera path is not
represented as a captured video file.

The timeline needs zoom, scrolling, frame stepping, timecode, playback-rate
control, In/Out loops, shot trimming, ripple timing, reorder/duplicate/delete,
undo/redo and camera/dialogue/actor-action/marker tracks. Shot-owned actions and
dialogue must remain attached when a shot is trimmed or reordered. Analyze
camera speed, angular speed, path length, focus framing, structure occlusion and
dialogue pace, with readable units and independently labeled graph scales.
Tests must distinguish an in-frame subject from one hidden behind a timber.

Start an original PG-13 family DIY comedy, titled Nearly Level in the Python
reference. Include two parents, an older sister aged 19 and two brothers aged
18. Give everyone distinct costumes, personalities and stable IDs. Use original
scripts with household mishaps, sibling rivalry, dry reactions and meme captions.
The dome is a recurring lived-in setting; stories do not require product lectures
or invented performance claims. Avoid copying existing shows' characters or lines.

Support per-shot actor blocking, articulated gestures, walking/carrying,
expressions and dialogue. State which animation channels are implemented and
whether lip motion is text-timed or audio-synchronized. Provide a complete timed
pilot and series premises. Label captioned animatics, narrated drafts and finished
voice-acted episodes accurately. Export the complete episode JSON, script,
storyboard, shot list, timing/analysis data and an EDL or equivalent edit exchange.

Rendering must freeze the episode source before either cut starts. Landscape and
phone cuts must use the same source/timing, then produce captions, thumbnails and
release copy through the existing release pipeline. Keep UI review rendering,
live scouting and final film rendering consistent in geometry and camera data;
clearly identify scout lighting or quality differences.
