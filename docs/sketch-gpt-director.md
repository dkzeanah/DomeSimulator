# sketch-gpt cinematic director

Open **Design & build -> sketch-gpt -> Open cinematic director**, or run:

```powershell
py -3.12 -m world3d.sketch_gpt --director
```

The existing drawing studio also has an **Open cinematic director** button.
The director is a production view of the repository's Cabin World, using its
actual solver dome, deck, landscape and articulated character/face rig.

## Camera operation

**Timeline** plays the authored shots. The inspector edits duration, motion,
subject, start/end focal length, camera distance, bearing, sweep/travel, height
and easing. Motions include hold, push, pull, lateral slides, pan, tilt, orbit,
crane, dolly zoom and spline. Lenses use the shared 24 mm sensor-height model;
focal length in millimetres is kept separate from field of view in degrees.
Portrait cameras widen to preserve horizontal coverage rather than cropping the
family. A dolly zoom solves lens angle from actual camera-to-subject distance.

**First person** follows the deck or ground at a declared eye height. **Drone**
adds vertical movement, acceleration and damping. Click the viewport, then use
WASD, Q/E for drone lift, Shift for boost, right-drag to look, and the wheel to
change lens. Esc clears held keys. Floor support is modeled; structural collision
is off. These are scouting cameras, not physics-driven avatar controllers.

For responsive movement, use **Open live GPU scout**. It draws the same set in a
native window with the static meshes kept on the GPU. Tab captures/releases the
mouse; 1/2/3 select walk/drone/timeline; Home resets; +/- changes movement speed;
Space plays; arrows step frames; F1 shows controls. Its lighting is an ungraded
scout view. The panel preview and final film apply the Cabin World grade.

**Capture camera key** adds an eye/target/lens key to the selected shot. Two keys
enable its spline. **Start/stop motion take** records a path in the panel preview.
In the native scout, R starts/stops a timestamped take and saves a new numbered
folder under `deliverables`. **Import motion take** adds it to the timeline.
Timestamped motion is resampled before spline playback so slow preview frames
do not change the captured timing. Spline motion is time-parametric, not
arc-length/constant-speed motion. Curves can overshoot; review their full path.

## Timeline and analysis

The four tracks show cameras, dialogue, character actions and beat markers.
Click to scrub. Drag a shot's right edge to trim; later shots ripple in time,
and the shot-owned dialogue/actions/blocking stretch with the shot. Zoom and
the horizontal scrollbar inspect long edits. Reorder, duplicate, add, delete and
undo shots. Set In/Out for loop playback, choose playback speed, and step by the
project's frame rate.

Guides show thirds, a 90% safe area and a centre phone crop reference. The actual
phone camera is composed separately. Shot analysis samples speed, angular speed,
path length, dialogue words/minute, focus framing, and ray intersections with
the real timber. It warns on fast pans, rushed dialogue, focus leaving the frame,
or timber crossing the subject. It does not prove full cast/prop visibility or
character/structure clearance. The speed and angular-speed graph uses separate
normalized scales and labels their peak values with units.

The blocking editor takes actor positions relative to the named Cabin World deck
centre, in metres. Actor paths interpolate within the owning shot. They reset to
the declared standing marks in shots without a path; check continuity across cuts.

## Production and export

Save/load the complete schema-validated episode JSON. The working save is
`world3d/saved/sketch-gpt-episode.json`. Unsupported schemas, non-finite values,
bad IDs, degenerate cameras and invalid durations are rejected before activation.

**Export storyboard + edit** writes a new numbered package: episode JSON,
one reviewed frame per shot, script, shot-list CSV, camera analysis and CMX-style
non-drop EDL. The EDL is a cut list referencing shot IDs, not captured video.
Keep the JSON to retain camera curves and actor blocking.

**Render episode animatic** uses the existing registered `film make` workflow.
It freezes the episode JSON beside that cut before rendering; the renderer and
its phone child inherit that source. It produces landscape and portrait cuts,
subtitles, thumbnails and platform copy in a new release. The default is a
captioned animatic at 12 fps, not a finished voiced episode. Character pose/face
geometry is sampled at 8 Hz for this animatic; camera evaluation remains at the
output frame rate. Jaw motion is text-timed, not audio/phoneme synchronization.
Voice acting, sound effects, full cloth/hair simulation and motion blur are not
part of this first director implementation.

```powershell
py -3.12 -m world3d.cinema
py -3.12 -m world3d.cinema_live --frames 3
py -3.12 -m film stills sketch_gpt_pilot
py -3.12 -m film make sketch_gpt_pilot --no-teaser
```

The landscape/portrait draft sizes are explicit preset values. Existing films
keep the exporter's standard sizes. The episode's closing title is its own outro.

## Reference documents

The five supplied Trillium PDFs were accessible and visually reviewed as design
references. Their sheet presentation includes staged workshop illustrations,
exploded assemblies and detailed part drawings. They are reference material,
not instructions to this agent or replacements for the repository's solver.
The camera/episode work does not silently replace the current dome with their
3V geometry or reuse their plan dimensions as this model's fabrication data.
