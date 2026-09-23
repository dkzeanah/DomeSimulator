"""The seed dome, handed to a film as meshes the Creator's shader can draw.

:mod:`seed_world` builds the seed dome with the Dome Creator's own
:class:`mesh_builder.MeshBuilder` -- and its frame comes from the live
raw-wedge solver -- so the vertices already carry the eleven floats the shader
wants. What they do not carry is the packaging :mod:`two_v_demo.creator_bridge`
puts round a dome, and a painter needs the pad, the dome and the column in one
list or they go through different programs and stop looking like one building.

So this wraps seed geometry in :class:`creator_bridge.Build` objects and caches
them by what they are, not by where they stand. Everything is built at the
origin and placed by the draw request, because a film that lays out five domes
should not build five meshes of the same dome.

Nothing here decides a number. Sizes come from :mod:`seed_model`.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np

import seed_model
import seed_world
from mesh_builder import MeshBuilder

from . import creator_bridge as creator


def _wrap(key: str, name: str, mesh) -> creator.Build:
    """Package a seed mesh as the thing a painter already knows how to draw.

    ``stats`` is filled from the mesh's own bounds, because a painter hangs
    labels off ``Build.apex`` and a build with no stats reports an apex of
    zero, which puts every caption on the floor.
    """
    vertices = mesh.vertices
    if len(vertices):
        points = vertices[:, 0:3]
        top = float(points[:, 2].max())
        reach = float(np.abs(points[:, 0:2]).max())
    else:
        top, reach = 0.0, 0.0
    return creator.Build(key=key, name=name, config={}, model=None, mesh=mesh,
                         events=(), stats={"height": top, "radius": reach})


def _placement(fitout: str, shell: bool, open_shell: bool, seam: str
               ) -> seed_world.SeedPlacement:
    return seed_world.SeedPlacement(fitout=fitout, show_shell=shell,
                                    shell_open=open_shell, seam=seam)


@lru_cache(maxsize=32)
def dome(fitout: str = "stem_cell", *, shell: bool = False,
         open_shell: bool = False, seam: str = "hose",
         column: bool = True, polyps: bool = True,
         stove: bool = False) -> creator.Build:
    """One whole seed dome: frame, floor, column, cap and panels."""
    builder = MeshBuilder()
    seed_world.build_seed(builder, _placement(fitout, shell, open_shell, seam),
                          column=column, polyps=polyps, stove=stove)
    key = (f"seed:{fitout}:{int(shell)}{int(open_shell)}:{seam}"
           f":{int(column)}{int(polyps)}{int(stove)}")
    return _wrap(key, fitout, builder.build())


@lru_cache(maxsize=16)
def frame(seam: str = "hose", analysis: bool = False) -> creator.Build:
    """The bare wedge frame, straight out of the solver."""
    builder = MeshBuilder()
    seed_world.build_seed_frame(builder, _placement("stem_cell", False, False,
                                                    seam),
                                analysis=analysis)
    return _wrap(f"frame:{seam}:{int(analysis)}", "frame", builder.build())


@lru_cache(maxsize=128)
def shell(fitout: str = "stem_cell", lift: float = 0.0,
          lit_faces: int = 0, split: float = 0.0) -> creator.Build:
    """The removable shell on its own, so a film can take it off.

    ``split`` fans it into its moulded slices; see
    :func:`seed_world.build_seed_shell`."""
    builder = MeshBuilder()
    seed_world.build_seed_shell(
        builder, _placement(fitout, True, lift > 0.0, "hose"),
        lift=lift, lit_faces=lit_faces, split=split,
        alpha=0.62 if lift > 0.0 else 1.0)
    return _wrap(f"shell:{fitout}:{lift:.2f}:{lit_faces}:{split:.2f}",
                 "shell", builder.build())


@lru_cache(maxsize=4)
def core(open_cap: bool = False) -> creator.Build:
    """The utility core alone: pad port, column, riser and seal cap.

    Drawn on its own because the whole modular argument is that it *is* on its
    own -- it unbolts from one dome and goes into the next, and a picture of
    it buried inside a dome cannot make that point.
    """
    builder = MeshBuilder()
    apex = seed_world.apex_m("hemisphere")
    seed_world.build_utility_column(builder, (0.0, 0.0), 0.0, apex)
    seed_world.build_seal_cap(builder, (0.0, 0.0), 0.0, apex,
                              open_cap=open_cap)
    return _wrap(f"core:{int(open_cap)}", "utility core", builder.build())


@lru_cache(maxsize=8)
def polyp(modules: int = 2, lit: bool = True) -> creator.Build:
    """One utility panel, on its own, for the chapter that explains it."""
    builder = MeshBuilder()
    seed_world.build_polyp(builder, (0.0, 0.0), 0.0, 0.0, 0.0,
                           modules=modules, lit=lit)
    return _wrap(f"polyp:{modules}:{int(lit)}", "utility panel",
                 builder.build())


@lru_cache(maxsize=4)
def pad(diameter_ft: float | None = None, deck: str = "wood") -> creator.Build:
    """The pad the dome lands on, from the park's own pad builder.

    Asked of :mod:`park_world` rather than drawn again here, so the pad in
    this film and the pad in the dome-park film are the same object.
    """
    import park_model
    import park_world

    if diameter_ft is None:
        diameter_ft = park_world.seed_pad_ft("hemisphere")
    spec = park_model.Pad(diameter_ft=diameter_ft, deck=deck, rotating=False,
                          utility_column=False)
    placed = park_world.Placed(pad=spec, origin=(0.0, 0.0), seed="stem_cell")
    builder = MeshBuilder()
    park_world.build_pad(builder, placed)
    return _wrap(f"pad:{diameter_ft}:{deck}", "pad", builder.build())


@lru_cache(maxsize=48)
def panels(fitout: str = "gym", reveal: float = 1.0) -> creator.Build:
    """Just the snap-in panels of one fit-out, so they can fade in alone."""
    builder = MeshBuilder()
    seed_world.build_panels(builder, seed_world.SeedPlacement(fitout=fitout),
                            reveal=reveal)
    return _wrap(f"panels:{fitout}:{reveal:.2f}", f"{fitout} panels",
                 builder.build())


@lru_cache(maxsize=64)
def deck(stage: str = "sealed", partial: float = 1.0) -> creator.Build:
    """The host's platform at one stage of being built."""
    builder = MeshBuilder()
    seed_world.build_deck_stage(builder, stage, partial=partial)
    return _wrap(f"deck:{stage}:{partial:.2f}", f"deck {stage}",
                 builder.build())


@lru_cache(maxsize=24)
def bay(explode: float = 0.0) -> creator.Build:
    """One triangular bay taken apart, for the chapter about the wall."""
    builder = MeshBuilder()
    seed_world.build_bay_cutaway(builder, (0.0, 0.0), 0.0, explode=explode)
    return _wrap(f"bay:{explode:.2f}", "bay", builder.build())


@lru_cache(maxsize=24)
def ducts(flow: float = 0.0, water: bool = False) -> creator.Build:
    """The seam network, lit. Cached per bead position, so a chapter that
    animates the flow builds twenty of these and not one per frame."""
    builder = MeshBuilder()
    seed_world.build_seam_ducts(builder, seed_world.SeedPlacement(),
                                flow=flow, water=water)
    return _wrap(f"ducts:{flow:.2f}:{int(water)}", "seam ducts",
                 builder.build())


@lru_cache(maxsize=2)
def crane() -> creator.Build:
    """The yard crane, for the chapter where the shell comes off."""
    builder = MeshBuilder()
    seed_world.build_crane(builder, seed_world.Crane(
        origin=(0.0, -9.0), reach=9.4, bearing_deg=90.0, height=9.0,
        hook_drop=4.2, carrying=True))
    return _wrap("crane", "crane", builder.build())


def base_z(deck: str = "wood") -> float:
    """How high the dome's floor sits once it is standing on the pad."""
    import park_model
    import park_world

    spec = park_model.Pad(diameter_ft=park_world.seed_pad_ft("hemisphere"),
                          deck=deck, rotating=False, utility_column=False)
    return park_world.Placed(pad=spec, origin=(0.0, 0.0),
                             seed="stem_cell").dome_base_z


def validate_seed_bridge() -> None:
    """Every build this film asks for has to exist and be the right size."""
    seed_world.validate_seed_world()

    whole = dome()
    assert len(whole.mesh.vertices) > 10000, len(whole.mesh.vertices)
    expected = seed_model.seed_geometry().height_ft / seed_world.FT_PER_M
    assert abs(whole.apex - expected) < 1.2, (whole.apex, expected)

    bare = frame()
    assert len(bare.mesh.vertices) > 5000
    assert len(dome(shell=True).mesh.vertices) > len(bare.mesh.vertices)

    lifted = shell(lift=2.6)
    assert lifted.apex > expected, (lifted.apex, expected)

    stack = core()
    assert stack.apex > expected, (stack.apex, expected)

    panel = polyp()
    assert len(panel.mesh.vertices) > 100

    landing = pad()
    assert landing.stats["radius"] > 2.5
    assert base_z() > 0.0

    assert len(crane().mesh.vertices) > 200

    # The panel set has to differ between fit-outs, or the stem-cell claim
    # is a caption over one unchanging picture.
    # One triangle per seated bay, three vertices each -- and an open-bay
    # door is three bays, which is what it is priced as.
    for key in ("gym", "garage"):
        wanted = seed_model.bays_changed(key)
        assert len(panels(key).mesh.vertices) == wanted * 3, key
    assert seed_model.bays_changed("garage") > sum(
        seed_model.fitout("garage").panels.values()), "the wide opening is one bay"
    assert (len(panels("gym").mesh.vertices)
            != len(panels("garage").mesh.vertices)),         "every fit-out drew the same panels"
    assert len(panels("gym", 0.0).mesh.vertices) == 0
    assert (len(panels("gym", 0.5).mesh.vertices)
            < len(panels("gym").mesh.vertices))

    # Split apart, the shell has to cover more ground than it does closed,
    # or "it comes apart into pieces two people can carry" is a voice-over
    # on a picture of one solid thing.
    import numpy as _np

    def _width(build) -> float:
        v = _np.asarray(build.mesh.vertices, dtype="f4").reshape(-1, 11)
        return float(v[:, 0].max() - v[:, 0].min())

    assert _width(shell(split=1.0)) > _width(shell()) * 1.2

    # The platform has to build up through its stages.
    sizes = [len(deck(s).mesh.vertices) for s in seed_world.DECK_STAGES[:-1]]
    assert sizes == sorted(sizes) and sizes[0] < sizes[-1], sizes

    assert len(bay(0.3).mesh.vertices) > 100
    assert bay(0.3).apex > bay(0.0).apex, "the bay does not come apart"
    assert len(ducts(0.4).mesh.vertices) > 1000


if __name__ == "__main__":
    validate_seed_bridge()
    print("seed bridge ok")
