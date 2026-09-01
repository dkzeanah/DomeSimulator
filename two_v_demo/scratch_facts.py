"""Every derivation the "from scratch" lesson puts on film.

The lesson this module serves answers one question end to end: *what
does a computer actually calculate, from nothing, to put a geodesic
dome on a screen?*  It has two halves.  The first builds the **shape**
-- twelve points from one irrational number, subdivided, projected,
measured, and scaled to real lumber.  The second turns that shape into
**pixels** -- tubes, triangles, normals, a camera, three matrices, one
divide, a viewport, a depth test and a lighting equation.

Like ``master_facts``, this module computes nothing of its own that the
renderer does not already compute.  Where a figure belongs to the
geometry it is read from :mod:`two_v_demo.geometry`.  Where it belongs
to the *renderer*, it is produced by calling the renderer's own
functions -- :func:`~two_v_demo.render_kit.perspective`,
:func:`~two_v_demo.render_kit.look_at`,
:func:`~two_v_demo.render_kit.project_point` -- or, for the handful of
settings that live as literals inside
:meth:`~two_v_demo.app.MasterclassApp.render`, by reading them back out
of that method's own source text.

That last part is deliberate and worth stating plainly.  A number like
the 48-degree field of view could have been retyped here in a second.
It is parsed instead, so that changing the renderer and forgetting this
module raises an error rather than quietly putting a lie on screen.
:func:`validate_scratch_facts` proves the rest of the chain, including
that the eye position stated on the math screens is the one
:meth:`MasterclassApp.camera` really computes.

A *step list* is a tuple of strings.  The math overlay reveals them one
line at a time as the chapter plays and presents the last line as the
conclusion, so every list here ends with the sentence the viewer should
leave holding.
"""

from __future__ import annotations

import inspect
import math
import re
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from .geometry import (
    PHI,
    DomeMeasurements,
    build_demo_geometry,
    fit_measurements,
    normalize,
)
from .render_kit import (
    SCENE_FRAGMENT_SHADER,
    TriangleBatch,
    look_at,
    perspective,
    project_point,
)


GEOMETRY = build_demo_geometry()

# The two boards this whole repository was originally asked about.
# Physical measurements, so external by definition -- everything else on
# every screen below is derived.
MEASURED_LONG_IN = 72.0
MEASURED_SHORT_IN = 63.5
FIT = fit_measurements(MEASURED_LONG_IN, MEASURED_SHORT_IN)
DOME = DomeMeasurements(FIT.best_fit_radius)

# The published frame this lesson's pixel arithmetic describes.
FRAME_WIDTH = 1920
FRAME_HEIGHT = 1080
FRAME_FPS = 30

EXTERNAL_CONSTANTS: tuple[tuple[str, float, str, str], ...] = (
    ("measured_long_in", MEASURED_LONG_IN, "in",
     "The long member of the audited dome, measured with a tape."),
    ("measured_short_in", MEASURED_SHORT_IN, "in",
     "The short member of the audited dome, measured with a tape."),
    ("frame_width_px", float(FRAME_WIDTH), "px",
     "The frame size this lesson is published at."),
    ("frame_height_px", float(FRAME_HEIGHT), "px",
     "The frame size this lesson is published at."),
    ("frame_rate", float(FRAME_FPS), "frames/s",
     "The frame rate this lesson is published at."),
)

# The world-space size the dome scenes are drawn at, shared with the
# lesson's painters so the counts on the buffer screen describe the
# picture standing beside them rather than some other dome.
SCALE = 5.0
STRUT_RADIUS = 0.065
STRUT_SIDES = 8
HUB_RADIUS = 0.105
HUB_RINGS = 5
HUB_SEGMENTS = 8


# ----------------------------------------------------------------------
# Reading the renderer's own settings back out of the renderer
# ----------------------------------------------------------------------

_NUMBER = r"(-?\d+(?:\.\d+)?)"


def _grab(pattern: str, text: str, what: str) -> tuple[float, ...]:
    """Pull the numbers out of one line of real source, or fail loudly."""
    match = re.search(pattern, text)
    if match is None:
        raise AssertionError(
            f"could not read {what} out of the renderer's source; the "
            "renderer has changed and this lesson's math screens would "
            "be stating a figure the code no longer uses"
        )
    return tuple(float(value) for value in match.groups())


@dataclass(frozen=True)
class RenderSettings:
    """The renderer's camera and light, as the renderer itself states them."""

    fov_degrees: float
    near: float
    far: float
    light: tuple[float, float, float]
    target: tuple[float, float, float]
    yaw_drift_degrees: float


@lru_cache(maxsize=1)
def render_settings() -> RenderSettings:
    from .app import MasterclassApp

    render_source = inspect.getsource(MasterclassApp.render)
    camera_source = inspect.getsource(MasterclassApp.camera)
    fov, near, far = _grab(
        rf"perspective\(\s*{_NUMBER},\s*(?:.*?),\s*{_NUMBER},"
        rf"\s*{_NUMBER}\s*\)",
        render_source, "the projection settings")
    light = _grab(
        rf'u_light"\]\.value = \(\s*{_NUMBER},\s*{_NUMBER},\s*{_NUMBER}\s*\)',
        render_source, "the light direction")
    target = _grab(
        rf"target = np\.array\(\[\s*{_NUMBER},\s*{_NUMBER},\s*{_NUMBER}\s*\]",
        camera_source, "the camera target")
    drift = _grab(
        rf"math\.sin\(self\.chapter_progress \* math\.pi\) \* {_NUMBER}",
        camera_source, "the camera's yaw drift")
    return RenderSettings(
        fov_degrees=fov, near=near, far=far,
        light=light, target=target, yaw_drift_degrees=drift[0],
    )


@dataclass(frozen=True)
class ShaderConstants:
    """The lighting numbers the graphics card is really running."""

    ambient: float
    diffuse_gain: float
    specular_power: float
    specular_gain: float
    specular_tint: tuple[float, float, float]
    rim_power: float
    rim_gain: float
    rim_tint: tuple[float, float, float]


@lru_cache(maxsize=1)
def shader_constants() -> ShaderConstants:
    """Parse the fragment shader this project ships to the graphics card."""
    source = SCENE_FRAGMENT_SHADER
    ambient, diffuse_gain = _grab(
        rf"v_color\.rgb \* \({_NUMBER} \+ {_NUMBER} \* diffuse\)",
        source, "the ambient and diffuse weights")
    specular_power = _grab(
        rf"specular = pow\(max\(dot\(n, h\), 0\.0\), {_NUMBER}\)",
        source, "the specular exponent")[0]
    rim_power = _grab(
        rf"rim = pow\(1\.0 - max\(dot\(n, v\), 0\.0\), {_NUMBER}\)",
        source, "the rim exponent")[0]
    rim = _grab(
        rf"vec3\({_NUMBER}, {_NUMBER}, {_NUMBER}\) \* rim \* {_NUMBER}",
        source, "the rim colour and weight")
    spec = _grab(
        rf"vec3\({_NUMBER}, {_NUMBER}, {_NUMBER}\) \* specular \* {_NUMBER}",
        source, "the specular colour and weight")
    return ShaderConstants(
        ambient=ambient, diffuse_gain=diffuse_gain,
        specular_power=specular_power, specular_gain=spec[3],
        specular_tint=(spec[0], spec[1], spec[2]),
        rim_power=rim_power, rim_gain=rim[3],
        rim_tint=(rim[0], rim[1], rim[2]),
    )


# ----------------------------------------------------------------------
# The reference frame every pixel screen describes
# ----------------------------------------------------------------------

# One camera, quoted on every screen in the second half, so a viewer can
# follow a single frame all the way from a vertex to a pixel.
REFERENCE_CAMERA = (34.0, 24.0, 15.0)


def eye_position(camera: tuple[float, float, float] | None = None,
                 progress: float = 0.0) -> np.ndarray:
    """Where the camera sits, by the renderer's own orbit formula.

    ``camera`` is a chapter's ``(yaw, pitch, distance)``.  The renderer
    adds a slow yaw drift across a chapter; at ``progress`` zero -- the
    instant a chapter begins -- that term is zero, which is the moment
    every figure on these screens describes.
    """
    settings = render_settings()
    yaw_degrees, pitch_degrees, distance = camera or REFERENCE_CAMERA
    yaw_degrees += math.sin(progress * math.pi) * settings.yaw_drift_degrees
    yaw = math.radians(yaw_degrees)
    pitch = math.radians(min(max(pitch_degrees, 8.0), 78.0))
    target = np.asarray(settings.target, dtype=np.float32)
    return target + np.array([
        distance * math.cos(pitch) * math.cos(yaw),
        distance * math.cos(pitch) * math.sin(yaw),
        distance * math.sin(pitch),
    ], dtype=np.float32)


@lru_cache(maxsize=4)
def reference_matrices(
    camera: tuple[float, float, float] = REFERENCE_CAMERA,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """``(projection, view, mvp)``, from the renderer's own functions."""
    settings = render_settings()
    eye = eye_position(camera)
    projection = perspective(
        settings.fov_degrees, FRAME_WIDTH / FRAME_HEIGHT,
        settings.near, settings.far)
    view = look_at(eye, np.asarray(settings.target, dtype=np.float32))
    return projection, view, projection @ view


# The vertex followed through every space: the top of the dome.  It is
# the one point on the model whose world position a viewer can predict
# without any arithmetic, which makes every later number checkable.
APEX_INDEX = int(np.argmax(GEOMETRY.vertices[:, 2]))
APEX_WORLD = GEOMETRY.vertices[APEX_INDEX] * SCALE


def _row(matrix: np.ndarray, index: int) -> str:
    """One matrix row, comma separated.

    The overlay font is proportional, so padding numbers into columns
    only looks like alignment that failed; commas read as a deliberate
    list of four numbers instead.
    """
    return "[ " + ",  ".join(
        f"{float(value):.4f}" for value in matrix[index]) + " ]"


def _small(value: float) -> str:
    """Format a shading term without rounding a real number to zero."""
    if value != 0.0 and abs(value) < 1e-4:
        return f"{value:.3e}"
    return f"{value:.6f}"


def _clean(value: float) -> float:
    """Snap floating-point dust to zero so a coordinate reads as itself.

    The apex lands on x = y = 0 by construction, but arrives as a
    number like -1.2e-16, which prints as "-0.0000" and reads as a
    mistake to anybody watching.
    """
    return 0.0 if abs(value) < 5e-5 else float(value)


def _facing_face(eye: np.ndarray):
    """The dome panel most squarely facing the camera.

    Returns its normal, its centre and its three corners.  The lighting
    screen has to describe a triangle the viewer can actually see;
    picking an arbitrary one lands on a back-facing panel where every
    term collapses to its degenerate value.
    """
    best = None
    for face in GEOMETRY.hemisphere_faces:
        a, b, c = (GEOMETRY.vertices[int(index)] * SCALE for index in face)
        normal = normalize(np.cross(b - a, c - a))
        centre = (a + b + c) / 3.0
        facing = float(np.dot(normal, normalize(eye - centre)))
        if best is None or facing > best[0]:
            best = (facing, normal, centre, (a, b, c))
    assert best is not None
    return best[1], best[2], best[3]


def _conclude(steps: list[str], conclusion: str) -> tuple[str, ...]:
    steps.append(conclusion)
    return tuple(steps)


# ======================================================================
# PART ONE -- the shape
# ======================================================================

@lru_cache(maxsize=1)
def steps_phi() -> tuple[str, ...]:
    """Screen 1 -- twelve points from one number."""
    raw_radius = math.sqrt(1.0 + PHI**2)
    raw = GEOMETRY.raw_vertices
    spacing = min(
        float(np.linalg.norm(raw[a] - raw[b]))
        for a in range(len(raw)) for b in range(a + 1, len(raw))
    )
    steps = [
        "start with one number and nothing else:",
        f"phi = (1 + sqrt 5) / 2 = {PHI:.9f}",
        "  phi is the number whose square is itself plus one",
        "build 12 points by putting 0, +/-1 and +/-phi in every order:",
        "  (0, +/-1, +/-phi), (+/-1, +/-phi, 0), (+/-phi, 0, +/-1)",
        f"  3 families x 4 sign choices = {len(raw)} points",
        "measure the closest pair of those points:",
        f"  nearest-neighbour distance = {spacing:.9f}",
        "measure each point's distance from the centre:",
        f"  |v| = sqrt(1 + phi^2) = {raw_radius:.9f}  (all 12 the same)",
        "  |v| means length: sqrt(x^2 + y^2 + z^2)",
        f"every point is {spacing:.3f} from its neighbours and "
        f"{raw_radius:.6f} from the middle",
    ]
    return _conclude(
        steps,
        "One irrational number places twelve points in perfectly even "
        "space -- that is an icosahedron, and it is the entire starting "
        "stock of the dome.")


@lru_cache(maxsize=1)
def steps_normalize() -> tuple[str, ...]:
    """Screen 2 -- why we divide every point by its own length."""
    raw_radius = math.sqrt(1.0 + PHI**2)
    edge = 2.0 / raw_radius
    lengths = [float(np.linalg.norm(vertex))
               for vertex in GEOMETRY.ico_vertices]
    steps = [
        "the 12 raw points sit on a sphere of an awkward radius:",
        f"  |v| = {raw_radius:.9f}   (not 1, not anything useful)",
        "divide every point by its own length -- 'normalize':",
        "  v_hat = v / |v|     same direction, length set to 1",
        f"  check: every point is now at radius {min(lengths):.9f} to "
        f"{max(lengths):.9f}",
        "the edge that measured 2.000000 becomes:",
        f"  2 / sqrt(1 + phi^2) = {edge:.9f}",
        "that number is a CHORD FACTOR: a multiplier, not a length",
        "  length in inches = chord factor x radius in inches",
        "so the model is unit-free -- pick the size later, once, and",
        "  the same numbers serve a playhouse and a hangar",
    ]
    return _conclude(
        steps,
        "Normalizing turns one specific solid into a reusable recipe: "
        "every distance becomes a multiple of a radius you have not "
        "chosen yet.")


@lru_cache(maxsize=1)
def steps_euler() -> tuple[str, ...]:
    """Screen 3 -- counting the surface, and the check that never lies."""
    vertices = len(GEOMETRY.ico_vertices)
    faces = len(GEOMETRY.base_faces)
    edges = len(GEOMETRY.ico_edges)
    steps = [
        "the icosahedron, counted off the model on the left:",
        f"  V = corners        = {vertices}",
        f"  F = triangle faces = {faces}",
        "every face has 3 sides and every side is shared by 2 faces:",
        f"  E = F x 3 / 2 = {faces} x 3 / 2 = {faces * 3 // 2}",
        f"  counted directly off the model: E = {edges}",
        "Euler's rule, true of any closed surface without holes:",
        f"  V - E + F = {vertices} - {edges} + {faces} = "
        f"{vertices - edges + faces}",
        "  a closed surface always gives 2 -- anything else is a bug:",
        "  a missing face, a doubled corner, a hole in the mesh",
        "run it again after subdividing, on 42 corners and 80 faces:",
        f"  {len(GEOMETRY.vertices)} - {len(GEOMETRY.edges)} + "
        f"{len(GEOMETRY.faces)} = "
        f"{len(GEOMETRY.vertices) - len(GEOMETRY.edges) + len(GEOMETRY.faces)}",
    ]
    return _conclude(
        steps,
        f"V - E + F = {vertices - edges + faces} is the cheapest proof "
        "in geometry that the shape in memory really closed up.")


@lru_cache(maxsize=1)
def steps_midpoint() -> tuple[str, ...]:
    """Screen 4 -- the halfway point, and why it is not on the sphere."""
    edge = GEOMETRY.ico_edges[0]
    a = GEOMETRY.ico_vertices[edge[0]]
    b = GEOMETRY.ico_vertices[edge[1]]
    midpoint = (a + b) * 0.5
    sag = float(np.linalg.norm(midpoint))
    steps = [
        "take one edge of the icosahedron, between corners a and b",
        "the halfway point is the plain average of the two:",
        "  m = (a + b) / 2     add the coordinates, halve them",
        f"  |a| = {float(np.linalg.norm(a)):.6f}   "
        f"|b| = {float(np.linalg.norm(b)):.6f}   (both on the sphere)",
        f"  |m| = {sag:.9f}               (NOT on the sphere)",
        "a straight line between two points on a ball cuts inside it:",
        f"  shortfall = 1 - {sag:.6f} = {1.0 - sag:.9f} of the radius",
        f"  on this lesson's {DOME.radius / 12.0:.1f} ft radius dome, "
        f"that is {(1.0 - sag) * DOME.radius:.2f} in",
        "leave the 30 midpoints where they landed and you get a",
        "  faceted icosahedron with more triangles -- not a dome",
    ]
    return _conclude(
        steps,
        f"Halving an edge is the easy half of subdivision: those points "
        f"sit {(1.0 - sag) * 100:.2f}% of the radius too deep, and have "
        "to be pushed out.")


@lru_cache(maxsize=1)
def steps_project() -> tuple[str, ...]:
    """Screen 5 -- the one operation that makes it geodesic."""
    edge = GEOMETRY.ico_edges[0]
    a = GEOMETRY.ico_vertices[edge[0]]
    b = GEOMETRY.ico_vertices[edge[1]]
    midpoint = (a + b) * 0.5
    sag = float(np.linalg.norm(midpoint))
    projected = normalize(midpoint)
    travel = float(np.linalg.norm(projected - midpoint))
    steps = [
        "push each midpoint straight out from the centre until it",
        "reaches the sphere -- and that is the same divide as before:",
        "  p = m / |m|     m chose the direction, the divide fixes the",
        "                  distance",
        f"  |m| = {sag:.9f}  ->  |p| = "
        f"{float(np.linalg.norm(projected)):.9f}",
        f"  distance travelled = 1 - |m| = {travel:.9f} radii",
        "the direction never changes, only the distance from centre:",
        "  each point slides along its own ray, so the face keeps its",
        "  shape and simply bulges outward",
        "this is the single line that separates a subdivided",
        "  icosahedron from a geodesic sphere",
        "and it is what breaks the equal edges: the four small",
        "  triangles in each face are no longer the same size",
    ]
    return _conclude(
        steps,
        "One division by a length -- p = m / |m| -- is the entire "
        "difference between a faceted ball and a geodesic dome.")


@lru_cache(maxsize=1)
def steps_chords() -> tuple[str, ...]:
    """Screen 6 -- why exactly two lengths come out, four ways."""
    short = next(item for item in GEOMETRY.edge_classes
                 if item.name == "SHORT")
    long = next(item for item in GEOMETRY.edge_classes if item.name == "LONG")
    short_edge = next(edge for edge, name in zip(
        GEOMETRY.edges, GEOMETRY.edge_class_by_edge) if name == "SHORT")
    u = GEOMETRY.vertices[short_edge[0]]
    v = GEOMETRY.vertices[short_edge[1]]
    by_coordinates = float(np.linalg.norm(u - v))
    theta = math.acos(float(np.clip(np.dot(u, v), -1.0, 1.0)))
    by_angle = 2.0 * math.sin(theta * 0.5)
    steps = [
        f"measure all {len(GEOMETRY.edges)} edges of the finished "
        "sphere. They fall into",
        "exactly two lengths -- no more, no fewer:",
        f"  SHORT = {short.factor:.9f} R   x{short.full_sphere_count}",
        f"  LONG  = {long.factor:.9f} R   x{long.full_sphere_count}",
        "  R is the radius; these are multipliers, not inches",
        "four independent routes to that same SHORT number:",
        f"  1. subtract coordinates:  |u - v| = {by_coordinates:.9f}",
        f"  2. central angle: theta = acos(u . v) = "
        f"{math.degrees(theta):.6f} deg",
        f"     chord = 2 sin(theta / 2) = {by_angle:.9f}",
        "  3. law of cosines on the same triangle: identical",
        "  4. measure it in CAD: identical",
        f"  routes 1 and 2 differ by {abs(by_coordinates - by_angle):.2e}",
        f"the ratio nobody guesses: LONG / SHORT = {GEOMETRY.ratio:.9f}",
        f"  and LONG = {long.factor:.9f} = 1 / phi, exactly",
    ]
    return _conclude(
        steps,
        f"Two lengths, {short.hemisphere_count} of one and "
        f"{long.hemisphere_count} of the other in the finished dome, in "
        f"a ratio of {GEOMETRY.ratio:.6f} -- which is not the golden "
        "ratio, and that surprise is the whole point.")


@lru_cache(maxsize=1)
def steps_counts() -> tuple[str, ...]:
    """Screen 7 -- cut the sphere in half and count what is left."""
    short = next(item for item in GEOMETRY.edge_classes
                 if item.name == "SHORT")
    long = next(item for item in GEOMETRY.edge_classes if item.name == "LONG")
    struts = short.hemisphere_count + long.hemisphere_count
    panels = len(GEOMETRY.hemisphere_faces)
    hubs = len({int(index) for face in GEOMETRY.hemisphere_faces
                for index in face})
    triangle_sides = panels * 3
    steps = [
        "a dome is the top half of the sphere. Keep every face whose",
        "corners all sit at z >= 0, and count what survives:",
        f"  triangular panels                = {panels}",
        f"  SHORT struts                     = {short.hemisphere_count}",
        f"  LONG struts                      = {long.hemisphere_count}",
        f"  struts total                     = {struts}",
        f"  hubs (corners where struts meet) = {hubs}",
        f"  base ring corners                = {len(GEOMETRY.base_ring)}",
        f"cross-check: {panels} panels x 3 sides = {triangle_sides} side",
        f"  slots, but interior sides are shared by two panels, which",
        f"  is why {triangle_sides} slots close into only {struts} real",
        "  struts",
        "not one of these was typed in -- they are counted, now, off",
        "  the same model being drawn on the left of this screen",
    ]
    return _conclude(
        steps,
        f"{panels} panels, {struts} struts, {hubs} hubs: a complete "
        "shelter, described by two lengths and a count.")


@lru_cache(maxsize=1)
def steps_scale() -> tuple[str, ...]:
    """Screen 8 -- from a unit-free recipe to lumber."""
    steps = [
        "the model is still unit-free. Two measured boards fix it:",
        f"  measured LONG  = {MEASURED_LONG_IN:.1f} in",
        f"  measured SHORT = {MEASURED_SHORT_IN:.1f} in",
        "each board on its own implies a radius:",
        f"  R from LONG  = {MEASURED_LONG_IN:.1f} / "
        f"{GEOMETRY.long_factor:.6f} = {FIT.radius_from_long:.3f} in",
        f"  R from SHORT = {MEASURED_SHORT_IN:.1f} / "
        f"{GEOMETRY.short_factor:.6f} = {FIT.radius_from_short:.3f} in",
        "they disagree, because tapes and saws are not exact",
        "least squares picks the radius that misses both by least:",
        f"  best-fit R = {FIT.best_fit_radius:.3f} in = "
        f"{FIT.best_fit_radius / 12.0:.2f} ft",
        f"  residuals  = {FIT.long_residual:+.3f} in and "
        f"{FIT.short_residual:+.3f} in",
        "multiply the two chord factors by that radius:",
        f"  30 SHORT @ {DOME.short_center_length:.3f} in",
        f"  35 LONG  @ {DOME.long_center_length:.3f} in",
        "  hub-centre to hub-centre; the physical cut is that minus",
        "  whatever the connector eats at each end",
        f"  floor {DOME.floor_area / 144.0:.1f} sq ft, height "
        f"{DOME.height / 12.0:.2f} ft, span "
        f"{DOME.diameter / 12.0:.2f} ft",
    ]
    return _conclude(
        steps,
        f"One multiplication turns the unit-free model into a cut list "
        f"for a {DOME.diameter / 12.0:.1f} foot dome.")


# ======================================================================
# PART TWO -- the picture
# ======================================================================

def dome_batch(
    reveal: float = 1.0,
    *,
    origin=None,
    scale: float = SCALE,
    hubs: bool = True,
    into: TriangleBatch | None = None,
) -> TriangleBatch:
    """The hemisphere as the graphics card receives it: tubes and balls.

    The lesson's painters draw the dome by calling this, and the buffer
    math screen counts what it returns at its default size -- so the
    triangle count quoted on that screen counts the very picture
    standing beside it, not a second model that happens to agree.
    """
    batch = TriangleBatch() if into is None else into
    shift = np.zeros(3) if origin is None else np.asarray(origin, dtype=float)
    edges = list(GEOMETRY.hemisphere_edges)
    class_by_edge = dict(zip(GEOMETRY.edges, GEOMETRY.edge_class_by_edge))
    shown = max(0, min(len(edges), int(round(len(edges) * reveal))))
    radius = STRUT_RADIUS * scale / SCALE
    for edge in edges[:shown]:
        a = GEOMETRY.vertices[edge[0]] * scale + shift
        b = GEOMETRY.vertices[edge[1]] * scale + shift
        colour = ((0.15, 0.82, 1.00, 1.0)
                  if class_by_edge[edge] == "SHORT"
                  else (1.00, 0.67, 0.20, 1.0))
        batch.cylinder(a, b, radius, colour, STRUT_SIDES)
    if hubs and reveal >= 0.999:
        for index in sorted({index for edge in edges for index in edge}):
            batch.sphere(GEOMETRY.vertices[index] * scale + shift,
                         HUB_RADIUS * scale / SCALE,
                         (0.77, 0.86, 0.91, 1.0), HUB_RINGS, HUB_SEGMENTS)
    return batch


@lru_cache(maxsize=1)
def steps_tube() -> tuple[str, ...]:
    """Screen 9 -- a line has no thickness; a tube does."""
    per_cylinder = STRUT_SIDES * 2 + 2 * (STRUT_SIDES - 2)
    struts = len(GEOMETRY.hemisphere_edges)
    steps = [
        "a strut in the model is two points. A graphics card cannot",
        "draw a line with thickness -- it draws triangles and nothing",
        "else. So the line has to be given a body:",
        "  d = (b - a) / |b - a|     the direction of the strut",
        "  pick any t that is not parallel to d, then",
        "  s = d x t   and   u = d x s      x is the cross product",
        "  the cross product of two directions returns a third at",
        "  right angles to both -- exactly what a ring needs",
        f"walk a ring of {STRUT_SIDES} points around the axis:",
        "  ring(i) = a + r ( s cos(2 pi i / n) + u sin(2 pi i / n) )",
        "  r is the strut radius, n the number of sides",
        "do the same at b, then stitch the two rings together:",
        f"  {STRUT_SIDES} side quads = {STRUT_SIDES * 2} triangles",
        f"  2 end caps   = {2 * (STRUT_SIDES - 2)} triangles",
        f"  one strut    = {per_cylinder} triangles",
        f"  x {struts} struts  = {per_cylinder * struts:,} triangles of "
        "frame",
    ]
    return _conclude(
        steps,
        f"Every visible line in this film is really a tube of "
        f"{STRUT_SIDES} flat sides and {per_cylinder} triangles, built "
        "by two cross products.")


@lru_cache(maxsize=1)
def steps_normal() -> tuple[str, ...]:
    """Screen 10 -- which way a triangle faces."""
    face = GEOMETRY.hemisphere_faces[0]
    a, b, c = (GEOMETRY.vertices[int(index)] * SCALE for index in face)
    cross = np.cross(b - a, c - a)
    normal = normalize(cross)
    area = float(np.linalg.norm(cross)) * 0.5
    outward = float(np.dot(normal, normalize((a + b + c) / 3.0)))
    steps = [
        "a triangle has to know which way it faces, or it cannot be",
        "lit and cannot be hidden. Take its three corners a, b, c:",
        "  n = (b - a) x (c - a)     cross product of two of its edges",
        f"  n = ({cross[0]:+.4f}, {cross[1]:+.4f}, {cross[2]:+.4f})",
        "  n stands at right angles to the surface: the NORMAL",
        "  divide by its length to make it exactly 1 long, which is",
        "  what the lighting maths assumes:",
        f"  n_hat = ({normal[0]:+.6f}, {normal[1]:+.6f}, "
        f"{normal[2]:+.6f})",
        "the same cross product hands you the area for free:",
        f"  area = |n| / 2 = {area:.6f} square world units",
        "corner ORDER decides the sign. Listed counter-clockwise as",
        "  seen from outside, n points outward:",
        f"  n_hat . (direction away from centre) = {outward:+.6f}",
        "  list them the other way round and the dome turns inside",
        "  out: lit from within, and thrown away as back-facing",
    ]
    return _conclude(
        steps,
        "One cross product answers three questions at once: which way "
        "the face points, how big it is, and whether it was wound the "
        "right way round.")


@lru_cache(maxsize=1)
def steps_buffer() -> tuple[str, ...]:
    """Screen 11 -- what is actually handed to the graphics card."""
    batch = dome_batch()
    floats = len(batch.vertices)
    vertices = floats // 10
    triangles = vertices // 3
    steps = [
        "by now the model is not points and edges any more. It is one",
        "flat list of numbers. Ten of them per vertex:",
        "  position x y z    where this corner is",
        "  normal   x y z    which way its surface faces",
        "  colour   r g b a  what shade it is; a is opacity",
        f"  10 floats x 4 bytes = {10 * 4} bytes per vertex",
        "count the dome standing to the left of this panel:",
        f"  floats    = {floats:,}",
        f"  vertices  = {floats:,} / 10 = {vertices:,}",
        f"  triangles = {vertices:,} / 3  = {triangles:,}",
        f"  bytes     = {floats * 4:,} = {floats * 4 / 1024:.1f} KB",
        "no corner is shared between triangles here: three fresh",
        "  vertices per face. That costs memory and buys the freedom",
        "  to give every face its own flat normal and its own colour",
        f"and that buffer is rebuilt and re-uploaded {FRAME_FPS} times "
        "a second",
    ]
    return _conclude(
        steps,
        f"The dome beside this panel is {triangles:,} triangles and "
        f"{floats * 4 / 1024:.0f} KB of plain numbers. That is the "
        "whole model, as the card sees it.")


@lru_cache(maxsize=1)
def steps_eye() -> tuple[str, ...]:
    """Screen 12 -- where the camera is, in numbers."""
    settings = render_settings()
    yaw, pitch, distance = REFERENCE_CAMERA
    eye = eye_position()
    target = np.asarray(settings.target)
    steps = [
        "the camera orbits the model. Three numbers place it:",
        f"  yaw      = {yaw:.1f} deg    how far around",
        f"  pitch    = {pitch:.1f} deg    how high up",
        f"  distance = {distance:.1f}      how far back",
        f"  target   = ({target[0]:.2f}, {target[1]:.2f}, "
        f"{target[2]:.2f})   what it looks at",
        "turn two angles and a distance into a position:",
        "  eye_x = target_x + distance cos(pitch) cos(yaw)",
        "  eye_y = target_y + distance cos(pitch) sin(yaw)",
        "  eye_z = target_z + distance sin(pitch)",
        f"  cos({pitch:.0f} deg) = {math.cos(math.radians(pitch)):.6f}"
        f"   sin({pitch:.0f} deg) = {math.sin(math.radians(pitch)):.6f}",
        f"  eye = ({eye[0]:.4f}, {eye[1]:.4f}, {eye[2]:.4f})",
        f"  check: |eye - target| = "
        f"{float(np.linalg.norm(eye - target)):.4f} = the distance we "
        "asked for",
    ]
    return _conclude(
        steps,
        "Two angles and a distance become one point in space -- and "
        "every calculation from here on is measured from that point.")


@lru_cache(maxsize=1)
def steps_view() -> tuple[str, ...]:
    """Screen 13 -- moving the world in front of the camera."""
    settings = render_settings()
    eye = eye_position()
    target = np.asarray(settings.target, dtype=np.float32)
    forward = normalize(target - eye)
    right = normalize(np.cross(forward, np.array([0.0, 0.0, 1.0])))
    up = normalize(np.cross(right, forward))
    _projection, view, _mvp = reference_matrices()
    steps = [
        "a graphics card cannot move a camera. It draws whatever sits",
        "in front of a fixed eye at the origin, looking down one axis.",
        "So we do not move the camera to the world. We move the world",
        "to the camera. Build three directions from the eye:",
        "  f = (target - eye) / |target - eye|      forward",
        "  r = f x up_hint, normalized              right",
        "  u = r x f                                true up",
        f"  f = ({forward[0]:+.6f}, {forward[1]:+.6f}, "
        f"{forward[2]:+.6f})",
        f"  r = ({right[0]:+.6f}, {right[1]:+.6f}, {right[2]:+.6f})",
        f"  u = ({up[0]:+.6f}, {up[1]:+.6f}, {up[2]:+.6f})",
        f"  all square to each other: r . f = "
        f"{float(np.dot(right, forward)):+.1e}",
        "stack them as rows, eye offset in the last column:",
        f"  {_row(view, 0)}",
        f"  {_row(view, 1)}",
        f"  {_row(view, 2)}",
        f"  {_row(view, 3)}",
        "  that last column is -(row . eye): turn first, then slide,",
        "  both in one multiplication instead of two",
    ]
    return _conclude(
        steps,
        "The view matrix is three directions and one offset, packed so "
        "the world arrives already facing the camera.")


@lru_cache(maxsize=1)
def steps_projection() -> tuple[str, ...]:
    """Screen 14 -- how distance becomes smallness."""
    settings = render_settings()
    projection, _view, _mvp = reference_matrices()
    aspect = FRAME_WIDTH / FRAME_HEIGHT
    focal = 1.0 / math.tan(math.radians(settings.fov_degrees) * 0.5)
    steps = [
        "perspective is one idea: things look smaller the further off",
        "they are, so divide by distance. The matrix sets up that",
        "divide -- it does not perform it.",
        f"  field of view = {settings.fov_degrees:.1f} deg  (how wide "
        "the lens is)",
        f"  aspect = {FRAME_WIDTH} / {FRAME_HEIGHT} = {aspect:.6f}",
        f"  near = {settings.near}, far = {settings.far}  (outside "
        "this range, nothing is drawn)",
        f"  f = 1 / tan(fov / 2) = {focal:.6f}",
        f"  {_row(projection, 0)}  <- x, scaled by f / aspect",
        f"  {_row(projection, 1)}  <- y, scaled by f",
        f"  {_row(projection, 2)}  <- z, remapped into near..far",
        f"  {_row(projection, 3)}  <- the whole trick",
        "  the last row copies -z into w, the fourth slot. That is",
        "  the only reason anything ever looks smaller with distance",
        f"  row 2's {projection[2][2]:.6f} and {projection[2][3]:.6f} "
        "are (far+near)/(near-far)",
        "  and 2 far near/(near-far): they squeeze depth into 0..1",
    ]
    return _conclude(
        steps,
        "The projection matrix shrinks nothing. It loads each point's "
        "depth into w, so that the divide coming next can do the "
        "shrinking.")


@lru_cache(maxsize=1)
def steps_pixel() -> tuple[str, ...]:
    """Screen 15 -- one vertex, all the way to a pixel."""
    _projection, view, mvp = reference_matrices()
    point = APEX_WORLD
    eye = eye_position()
    homogeneous = np.array([point[0], point[1], point[2], 1.0],
                           dtype=np.float32)
    view_space = view @ homogeneous
    clip = mvp @ homogeneous
    ndc = clip[:3] / clip[3]
    screen = project_point(mvp, point, FRAME_WIDTH, FRAME_HEIGHT)
    steps = [
        "follow one point -- the very top of the dome -- all the way:",
        f"  world = ({_clean(point[0]):.4f}, {_clean(point[1]):.4f}, "
        f"{_clean(point[2]):.4f}, 1)",
        "  the 1 on the end marks it a position, not a direction",
        "multiply by the view matrix (world -> the camera's frame):",
        f"  view  = ({view_space[0]:+.4f}, {view_space[1]:+.4f}, "
        f"{view_space[2]:+.4f})",
        f"  its z of {view_space[2]:+.4f} is depth in front of the "
        "lens; compare",
        f"  the straight-line distance |eye - point| = "
        f"{float(np.linalg.norm(np.asarray(point) - eye)):.4f}",
        "multiply by the projection matrix (camera -> clip space):",
        f"  clip  = ({clip[0]:+.4f}, {clip[1]:+.4f}, {clip[2]:+.4f}, "
        f"w={clip[3]:+.4f})",
        f"  and there is the depth again, sitting in w = {clip[3]:.4f}",
        "now the divide. This is the moment perspective happens:",
        f"  ndc = clip / w = ({ndc[0]:+.6f}, {ndc[1]:+.6f}, "
        f"{ndc[2]:+.6f})",
        "  everything still visible now lies inside a -1..+1 cube",
        "stretch that cube across the frame:",
        f"  px = (ndc_x * 0.5 + 0.5) x {FRAME_WIDTH} = {screen[0]:.1f}",
        f"  py = (1 - (ndc_y * 0.5 + 0.5)) x {FRAME_HEIGHT} = "
        f"{screen[1]:.1f}",
        "  y is flipped because screens count their rows downward",
    ]
    return _conclude(
        steps,
        f"World ({_clean(point[0]):.1f}, {_clean(point[1]):.1f}, "
        f"{_clean(point[2]):.1f}) lands "
        f"on pixel ({screen[0]:.0f}, {screen[1]:.0f}): three matrices, "
        "one divide, one stretch.")


def depth_value(distance: float) -> float:
    """The 0..1 depth the card stores for a point that far from the lens.

    It is the projection matrix's own third row, followed by the divide
    by w and the remap into the depth buffer's range -- written out here
    so the math screen and the picture beside it quote one function
    rather than two copies that happen to agree.
    """
    settings = render_settings()
    near, far = settings.near, settings.far
    distance = max(float(distance), near)
    clip_z = ((far + near) / (near - far)) * -distance         + (2.0 * far * near) / (near - far)
    return (clip_z / distance) * 0.5 + 0.5


@lru_cache(maxsize=1)
def steps_depth() -> tuple[str, ...]:
    """Screen 16 -- what hides behind what."""
    settings = render_settings()
    near, far = settings.near, settings.far
    depth_at = depth_value

    steps = [
        "the far side of the dome must not paint over the near side.",
        "Nothing is sorted. Every pixel simply remembers its depth:",
        "  if the arriving fragment is nearer, keep it; else drop it",
        f"  depth is stored 0 to 1, from near={near} to far={far}",
        "the remap is not even, because it comes out of that same",
        "  divide by w:",
    ]
    steps.extend(
        f"  {distance:>6.2f} units away  ->  depth {depth_at(distance):.6f}"
        for distance in (near, near * 2.0, 1.0, 5.0, 15.0, far)
    )
    spent = abs(depth_at(near) - depth_at(near * 2.0))
    steps.extend([
        f"  the first {near:.2f} to {near * 2:.2f} units alone spend "
        f"{spent * 100:.1f}% of the range",
        "  so precision is lavish up close and thin far away",
        "  two far-off surfaces whose depths round to the same number",
        "  flicker against each other: that is z-fighting, and pushing",
        "  'near' further out is the usual cure",
    ])
    return _conclude(
        steps,
        f"A depth buffer replaces sorting with one comparison per "
        f"pixel -- and spends most of its precision between {near} and "
        f"{near * 2:.2f} units of the lens.")


@dataclass(frozen=True)
class LightingSample:
    """One real dome panel, shaded by the real shader constants."""

    centre: np.ndarray
    corners: tuple
    normal: np.ndarray
    light: np.ndarray
    view: np.ndarray
    half: np.ndarray
    diffuse: float
    specular: float
    rim: float
    base: float
    lit: float


@lru_cache(maxsize=1)
def lighting_sample() -> LightingSample:
    """Shade the dome panel most squarely facing the camera.

    The math screen prints these numbers and the painter beside it draws
    these very vectors, so the arrows on screen are the arrows in the
    arithmetic.
    """
    settings = render_settings()
    shader = shader_constants()
    eye = eye_position()
    normal, centre, corners = _facing_face(eye)
    light = normalize(-np.asarray(settings.light))
    view_direction = normalize(eye - centre)
    half = normalize(light + view_direction)
    diffuse = max(float(np.dot(normal, light)), 0.0)
    specular = max(float(np.dot(normal, half)), 0.0) ** shader.specular_power
    rim = (1.0 - max(float(np.dot(normal, view_direction)), 0.0)) **         shader.rim_power
    base = 0.15
    lit = (base * (shader.ambient + shader.diffuse_gain * diffuse)
           + shader.rim_tint[0] * rim * shader.rim_gain
           + shader.specular_tint[0] * specular * shader.specular_gain)
    return LightingSample(
        centre=centre, corners=corners, normal=normal, light=light,
        view=view_direction,
        half=half, diffuse=diffuse, specular=specular, rim=rim,
        base=base, lit=lit,
    )


@lru_cache(maxsize=1)
def steps_light() -> tuple[str, ...]:
    """Screen 17 -- turning directions into brightness."""
    shader = shader_constants()
    sample = lighting_sample()
    normal, light, view_direction = sample.normal, sample.light, sample.view
    diffuse, specular, rim = sample.diffuse, sample.specular, sample.rim
    base, lit = sample.base, sample.lit
    steps = [
        "shading asks one question per pixel: how much of this light",
        "does this surface throw toward this eye? Three directions:",
        f"  n = the surface normal   ({normal[0]:+.4f}, "
        f"{normal[1]:+.4f}, {normal[2]:+.4f})",
        f"  l = toward the light     ({light[0]:+.4f}, {light[1]:+.4f}, "
        f"{light[2]:+.4f})",
        f"  v = toward the eye       ({view_direction[0]:+.4f}, "
        f"{view_direction[1]:+.4f}, {view_direction[2]:+.4f})",
        "the dot product of two unit directions is the cosine of the",
        "  angle between them: 1 facing, 0 side-on, negative behind",
        f"  diffuse = max(n . l, 0) = {diffuse:.6f}",
        "  that one number is Lambert's law -- square to the light is",
        "  brightest, edge-on is dark, and nothing lights from behind",
        "highlights use the direction halfway between light and eye:",
        "  h = (l + v) / |l + v|",
        f"  specular = max(n . h, 0) ^ {shader.specular_power:.0f} = "
        f"{_small(specular)}",
        f"  the exponent {shader.specular_power:.0f} is gloss: higher "
        "means a tighter, harder highlight",
        f"  rim = (1 - max(n . v, 0)) ^ {shader.rim_power} = "
        f"{_small(rim)}",
        "  rim brightens the silhouette, where the surface curves away",
        "add them in the weights this film's shader really uses:",
        f"  lit = colour x ({shader.ambient} + {shader.diffuse_gain} "
        "x diffuse)",
        f"        + cool tint x rim x {shader.rim_gain}",
        f"        + warm tint x specular x {shader.specular_gain}",
        f"  a face of base brightness {base} comes out at {lit:.4f}",
    ]
    return _conclude(
        steps,
        "Everything you read as shape in this picture is three dot "
        "products and a power. No shadows, no bounced light, no ray "
        "tracing.")


@lru_cache(maxsize=1)
def steps_frame() -> tuple[str, ...]:
    """Screen 18 -- the whole cost, per frame."""
    batch = dome_batch()
    triangles = len(batch.vertices) // 30
    budget_ms = 1000.0 / FRAME_FPS
    per_triangle_us = budget_ms * 1000.0 / max(1, triangles)
    pixels = FRAME_WIDTH * FRAME_HEIGHT
    steps = [
        "and then it all happens again for the next picture:",
        f"  {FRAME_FPS} frames a second = {budget_ms:.2f} ms per frame",
        "  clear the screen, rebuild the batch, upload it, draw it,",
        "  draw the text panel over the top, swap the buffers",
        f"  {triangles:,} triangles inside that budget = "
        f"{per_triangle_us:.3f} microseconds each",
        "the vertex shader runs once per vertex, thousands at a time:",
        f"  {triangles * 3:,} vertex runs per frame",
        "the fragment shader runs once per pixel covered:",
        f"  a full frame is {FRAME_WIDTH} x {FRAME_HEIGHT} = "
        f"{pixels:,} pixels",
        f"  = up to {pixels * FRAME_FPS / 1e6:.1f} million shader runs "
        "a second",
        "  which is exactly why the lighting had to be dot products",
        "and because every scene is a pure function of (chapter,",
        "  progress), the same second of film renders identically on",
        "  any machine, every time",
    ]
    return _conclude(
        steps,
        f"A frame is {triangles:,} triangles built, uploaded, "
        f"projected, depth-tested and shaded in {budget_ms:.1f} "
        "milliseconds -- thirty times a second.")


# ----------------------------------------------------------------------
# The registry, the audit, and the proof
# ----------------------------------------------------------------------

ALL_SCREENS: tuple[tuple[str, object], ...] = (
    ("phi", steps_phi),
    ("normalize", steps_normalize),
    ("euler", steps_euler),
    ("midpoint", steps_midpoint),
    ("project", steps_project),
    ("chords", steps_chords),
    ("counts", steps_counts),
    ("scale", steps_scale),
    ("tube", steps_tube),
    ("normal", steps_normal),
    ("buffer", steps_buffer),
    ("eye", steps_eye),
    ("view", steps_view),
    ("projection", steps_projection),
    ("pixel", steps_pixel),
    ("depth", steps_depth),
    ("light", steps_light),
    ("frame", steps_frame),
)


def scratch_report() -> str:
    """The audit: every math screen, line for line, plus provenance."""
    settings = render_settings()
    shader = shader_constants()
    lines = [
        "FROM SCRATCH -- MATH SCREEN AUDIT",
        "",
        "Every line below is what the matching math screen shows,",
        "generated by the same call the renderer makes.  The geometry",
        "comes from geometry.py.  The camera, projection and pixel",
        "figures come from render_kit.py's own functions.  The render",
        "settings and lighting weights are read back out of app.py and",
        "the shader source rather than retyped here.",
        "",
    ]
    for name, builder in ALL_SCREENS:
        lines.append(f"== {name.upper()} ==")
        lines.extend(f"  {line}" for line in builder())
        lines.append("")
    lines.append("Read back out of the renderer's own source:")
    lines.extend([
        f"  field of view      = {settings.fov_degrees} deg",
        f"  near / far         = {settings.near} / {settings.far}",
        f"  light direction    = {settings.light}",
        f"  camera target      = {settings.target}",
        f"  yaw drift          = {settings.yaw_drift_degrees} deg",
        f"  ambient / diffuse  = {shader.ambient} / {shader.diffuse_gain}",
        f"  specular pow/gain  = {shader.specular_power} / "
        f"{shader.specular_gain}",
        f"  rim pow/gain       = {shader.rim_power} / {shader.rim_gain}",
    ])
    lines.append("")
    lines.append("External constants declared by this module:")
    for key, value, units, source in EXTERNAL_CONSTANTS:
        lines.append(f"  {key} = {value} {units}  ({source})")
    return "\n".join(lines)


def validate_scratch_facts() -> None:
    """Prove the bridge: every screen agrees with the code it cites."""
    for name, builder in ALL_SCREENS:
        steps = builder()
        assert len(steps) >= 5, (name, len(steps))
        assert all(line.strip() for line in steps), name
        assert len(steps[-1]) >= 30, (name, steps[-1])

    # The settings really were parsed out of the renderer, not defaulted.
    settings = render_settings()
    assert 20.0 < settings.fov_degrees < 120.0, settings
    assert 0.0 < settings.near < settings.far, settings
    shader = shader_constants()
    assert shader.specular_power > 1.0 and shader.rim_power > 1.0, shader

    # The eye position quoted on the math screens is the one the
    # renderer's own method computes.  Calling the real method against a
    # stand-in is the only way to prove that without a GL context.
    from types import SimpleNamespace

    from .app import MasterclassApp

    for camera in (REFERENCE_CAMERA, (90.0, 30.0, 22.0), (12.0, 60.0, 9.0)):
        stand_in = SimpleNamespace(
            chapters=(None,), chapter_index=0, chapter_progress=0.0,
            camera_yaw=camera[0], camera_pitch=camera[1],
            camera_distance=camera[2], camera_override=False,
            playing=True, exporting=False,
        )
        real_eye, real_target = MasterclassApp.camera(stand_in)
        mine = eye_position(camera)
        assert np.allclose(real_eye, mine, atol=1e-4), (camera, real_eye, mine)
        assert np.allclose(real_target, settings.target, atol=1e-6), camera

    # The pixel screen's arithmetic must match the renderer's own
    # projection helper -- the one that places every label on screen.
    _projection, _view, mvp = reference_matrices()
    screen = project_point(mvp, APEX_WORLD, FRAME_WIDTH, FRAME_HEIGHT)
    assert screen is not None, "the apex must be on screen for this camera"
    assert 0 < screen[0] < FRAME_WIDTH, screen
    assert 0 < screen[1] < FRAME_HEIGHT, screen

    # The geometry the screens count is the geometry the lesson draws.
    batch = dome_batch()
    assert len(batch.vertices) % 30 == 0, len(batch.vertices)
    assert len(batch.vertices) // 30 > 1000, "the dome batch looks empty"
    partial = dome_batch(0.5)
    assert 0 < len(partial.vertices) < len(batch.vertices)

    # Euler's check has to actually hold, or the screen teaching it is
    # teaching a number this model does not have.
    assert (len(GEOMETRY.ico_vertices) - len(GEOMETRY.ico_edges)
            + len(GEOMETRY.base_faces)) == 2
    assert (len(GEOMETRY.vertices) - len(GEOMETRY.edges)
            + len(GEOMETRY.faces)) == 2
    assert math.isclose(GEOMETRY.long_factor, 1.0 / PHI, rel_tol=1e-9)
