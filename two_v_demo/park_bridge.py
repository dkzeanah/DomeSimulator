"""The dome park, handed to a film as meshes the Creator's shader can draw.

:mod:`park_world` builds the park with the Dome Creator's own
:class:`mesh_builder.MeshBuilder`, so its vertices already carry the eleven
floats that shader wants.  What it does not do is package them the way
:mod:`two_v_demo.creator_bridge` packages a dome, and a painter needs both in
the same list or the pad and the building on it go through different programs.

So this module wraps park geometry in :class:`creator_bridge.Build` objects and
caches them.  A painter then draws a pad and the dome standing on it with two
calls to the same :func:`creator_bridge.draw`, and the renderer never learns
that one of them came from a different file.

Three things are deliberate here:

* **A pad is built at the origin, and placed by the draw request.**  Baking a
  pad's position into its mesh would mean rebuilding it to move it, and a film
  that lays out four pads would be building four meshes of the same pad.
  ``Draw.offset`` places it instead, and ``Draw.yaw`` turns what should turn:
  on a real turntable the bearing race and the pedestal stay put and the
  platter rotates, so the *dome* carries the yaw and the pad only re-aims its
  drive motor and its sun arrow.
* **The site is a separate build from the pads.**  Ground, trunk services and
  the bathhouse do not move; pads do.
* **Nothing here decides a number.**  Sizes come from :mod:`park_model` and
  layouts come from the caller.
"""

from __future__ import annotations

import json
from functools import lru_cache

import numpy as np

import park_model
import park_world
from park_world import Placed

from . import creator_bridge as creator


def _wrap(key: str, name: str, mesh) -> creator.Build:
    """Package a park mesh as the thing a painter already knows how to draw.

    ``stats`` is filled from the mesh's own bounds rather than left empty:
    a painter hangs labels off ``Build.apex``, and a build with no stats
    reports an apex of zero, which puts every caption on the floor.
    """
    vertices = mesh.vertices
    if len(vertices):
        points = vertices[:, 0:3]
        top = float(points[:, 2].max())
        reach = float(np.abs(points[:, 0:2]).max())
    else:
        top, reach = 0.0, 0.0
    return creator.Build(
        key=key, name=name, config={}, model=None, mesh=mesh, events=(),
        stats={"height": top, "radius": reach},
    )


# ----------------------------------------------------------------------
# One pad
# ----------------------------------------------------------------------

def _pad_key(pad: park_model.Pad, occupied: bool, stage: int | None,
             heading: float) -> str:
    return json.dumps({
        "d": pad.diameter_ft, "deck": pad.deck, "rot": pad.rotating,
        "col": pad.utility_column, "solar": round(pad.solar_watts, 1),
        "occupied": occupied, "stage": stage, "heading": heading,
    }, sort_keys=True)


@lru_cache(maxsize=256)
def _pad_build(key: str) -> creator.Build:
    spec = json.loads(key)
    pad = park_model.Pad(
        diameter_ft=spec["d"], deck=spec["deck"], rotating=spec["rot"],
        utility_column=spec["col"], solar_watts=spec["solar"])
    placed = Placed(pad=pad, origin=(0.0, 0.0),
                    dome="x" if spec["occupied"] else "",
                    heading_deg=spec["heading"])
    builder = park_world.MeshBuilder()
    park_world.build_pad(builder, placed, stage=spec["stage"])
    return _wrap(key, f"{pad.diameter_ft:.0f} ft pad", builder.build())


HEADING_STEP = 15.0
"""Aim is quantised so a turning pad reuses a handful of cached meshes.

The deck, the bearing race and the pedestal do not turn on a real turntable --
the platter does -- so a film turns the *dome* with its draw request and moves
only the drive motor and the aim arrow with the pad."""


def pad(pad_spec: park_model.Pad, *, occupied: bool = True,
        stage: int | None = None, heading: float = 0.0) -> creator.Build:
    """One pad, centred on the origin, as far through its build as asked.

    ``occupied`` only lights the meter, which is the pad saying a tenant is
    drawing power through it.  ``heading`` aims the drive motor and the sun
    arrow, snapped to :data:`HEADING_STEP`.
    """
    snapped = round(heading / HEADING_STEP) * HEADING_STEP
    return _pad_build(_pad_key(pad_spec, occupied, stage, snapped))


PAD_STAGES = park_world.PAD_STAGES


def pad_stage_at(fraction: float) -> int:
    """Which build stage a chapter is at, from its 0..1 progress."""
    count = len(PAD_STAGES)
    return int(min(count - 1, max(0.0, fraction) * count))


# ----------------------------------------------------------------------
# The site the pads stand on
# ----------------------------------------------------------------------

def _site_key(park: park_world.Park) -> str:
    return json.dumps({
        "ground": round(park.site_radius, 3),
        "service": [round(v, 3) for v in park.service_point],
        "bath": None if park.bathhouse is None
                else [round(v, 3) for v in park.bathhouse],
        "pads": [[round(p.origin[0], 3), round(p.origin[1], 3),
                  round(p.radius_m, 3)] for p in park.placements],
    }, sort_keys=True)


@lru_cache(maxsize=16)
def _site_build(key: str, park_ref: int, ground: bool) -> creator.Build:
    park = _PARKS[park_ref]
    builder = park_world.MeshBuilder()
    if ground:
        park_world.build_ground(builder, park.site_radius)
    park_world.build_service_spine(builder, park.placements,
                                   park.service_point)
    if park.bathhouse is not None:
        park_world.build_bathhouse(builder, park.bathhouse)
    return _wrap(key, "site", builder.build())


_PARKS: dict[int, park_world.Park] = {}


def site(park: park_world.Park, *, ground: bool = True) -> creator.Build:
    """Trunk services, the bathhouse, and optionally the ground under them.

    ``ground=False`` leaves the graded disc out, for a film standing the park
    on :func:`field` instead: two flat discs a centimetre apart fight for the
    depth buffer, and the result is a site drawn in horizontal stripes.
    """
    _PARKS[id(park)] = park
    return _site_build(f"{_site_key(park)}|{ground}", id(park), ground)


@lru_cache(maxsize=4)
def ground_only(radius: float) -> creator.Build:
    """Just the graded field, for the scenes that want one pad on open land."""
    builder = park_world.MeshBuilder()
    park_world.build_ground(builder, radius)
    return _wrap(f"ground:{radius}", "ground", builder.build())


def field() -> creator.Build:
    """The Dome Creator's own build field: graded ground and a tree line.

    A bare disc of grass ends in a hard curved edge against a black sky, and
    a dome standing on one looks like it is floating on an island. The
    Creator already ships a site with a wooded perimeter; standing the park
    in it costs nothing, gives the frame a horizon, and has the useful side
    effect of putting the film in the same place the tool designs in.
    """
    return creator.environment()


@lru_cache(maxsize=4)
def bathhouse() -> creator.Build:
    """The shower house on its own, for the chapter that is about it."""
    builder = park_world.MeshBuilder()
    park_world.build_bathhouse(builder, (0.0, 0.0))
    return _wrap("bathhouse", "bathhouse", builder.build())


# ----------------------------------------------------------------------
# The dome that lands on a pad
# ----------------------------------------------------------------------

@lru_cache(maxsize=64)
def dome_on_pad(name: str) -> creator.Build:
    """A shipped design with its own foundation taken out from under it.

    The one line the whole idea rests on, and the reason it lives here rather
    than in a painter: a dome that arrives on a pad brings no foundation,
    because the pad *is* the foundation.  Leave the Creator's default in and
    every dome lands on a second slab sitting on the host's first one.
    """
    placed = Placed(pad=park_model.basic_pad(), origin=(0.0, 0.0), dome=name)
    return creator.build(placed.dome_config(), name)


@lru_cache(maxsize=64)
def dome_as_shipped(name: str) -> creator.Build:
    """The same design standing on its own ground, foundation and all.

    Drawn beside the one above in the chapter that prices the difference.
    """
    return creator.preset(name)


def dome_lift(pad_spec: park_model.Pad, *, rotating: bool | None = None
              ) -> float:
    """How far above grade a dome's floor sits once it is on this pad."""
    placed = Placed(
        pad=pad_spec if rotating is None
        else park_model.Pad(pad_spec.diameter_ft, pad_spec.deck, rotating,
                            pad_spec.utility_column, pad_spec.solar_watts),
        origin=(0.0, 0.0))
    return placed.dome_base_z


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_park_bridge() -> None:
    """Everything a painter will ask for has to come back with geometry in it."""
    park_world.validate_park_world()

    spec = park_model.standard_pad()
    whole = pad(spec)
    assert whole.triangles > 400, whole.triangles
    assert len(whole.mesh.vertices[0]) == creator.VERTEX_FLOATS
    assert whole.apex > 0.2, whole.apex

    # A pad builds up: every stage has to add geometry, and the last stage has
    # to be the finished pad. A stage that silently drew nothing would show up
    # on film as a pad that appears fully formed after a long empty pause.
    counts = [pad(spec, stage=index).triangles
              for index in range(len(PAD_STAGES))]
    assert counts[0] == 0, counts
    assert counts == sorted(counts), counts
    assert counts[-1] == whole.triangles, (counts[-1], whole.triangles)
    assert pad_stage_at(0.0) == 0
    assert pad_stage_at(1.0) == len(PAD_STAGES) - 1

    # Options have to be visible as geometry, or the film is describing
    # something the picture does not contain.
    bare = park_model.Pad(spec.diameter_ft, spec.deck)
    assert pad(bare).triangles < whole.triangles

    # Aiming a pad must change the geometry (the motor and the arrow move)
    # without changing how much of it there is.
    aimed = pad(spec, heading=90.0)
    assert aimed.triangles == whole.triangles
    assert aimed is not whole
    assert pad(spec, heading=91.0) is pad(spec, heading=88.0), (
        "headings should snap, or a turning pad rebuilds its mesh per frame")

    demo = park_world.default_park()
    ground = site(demo)
    assert ground.triangles > 200, ground.triangles
    assert site(demo) is ground, "the site mesh should be cached"
    bare = site(demo, ground=False)
    assert bare.triangles < ground.triangles, "the ground was not left out"

    backdrop = field()
    assert backdrop.triangles > 1000, backdrop.triangles
    # The backdrop has to reach well past anything a film stands on it, or
    # the horizon problem it exists to solve comes straight back.
    assert float(backdrop.mesh.vertices[:, 0].max()) > 120.0

    # The dome that lands on a pad must not bring a foundation with it.
    name = park_model.FLAGSHIP_DOME
    on_pad = dome_on_pad(name)
    shipped = dome_as_shipped(name)
    assert on_pad.triangles > 1000, on_pad.triangles
    assert on_pad.triangles < shipped.triangles, (
        "the on-pad dome still has a foundation under it")
    assert on_pad.model.foundation.height == 0.0
    assert dome_lift(spec) > 0.0
