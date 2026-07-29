"""The perimeter-plenum dome: one leaf blower, a whole-building lung.

Explains the mechanism: a tube ringing the base circumference of a 2V
dome, grilles opening into every floor bay, and a single blower port.
Blow outward and the tube goes below room pressure — every grille
becomes an exhaust register and the envelope is held at gentle negative
pressure. Reverse the intent and the same loop is a central vacuum:
plug a hose into any port and the debris rides the ring to a canister.

Also a deliberate showcase of the engine: environments composed from
text prompts, macro / portrait / wide / ultrawide lenses, snap-to focus
targets, animated parametric objects, and 1-point, fisheye, and full
360-degree perspective shots.
"""

from presenter.script import OverlayPanel, Presentation, Scene, Shot

R = 4.8
WORLD = (
    ("dome", {"radius": R, "skin_alpha": 0.14}),
    ("plenum", {"radius": R, "ports": 10, "blower_az": -30.0,
                "hose_az": 150.0}),
    ("blower", {"radius": R, "spin": 0.0}),
    ("airflow", {"radius": R, "intensity": 0.0}),
)


def _world(**overrides):
    out = []
    for name, params in WORLD:
        p = dict(params)
        p.update(overrides.get(name, {}))
        out.append((name, p))
    return tuple(out)


def build() -> Presentation:
    scenes = (
        Scene(
            "arrival", "A dome anywhere",
            "on a beach at a lake in the desert",
            world=_world(),
            shots=(
                Shot("establish", 9.0, lens="ultrawide", focus="dome",
                     yaw=-118, pitch=13, orbit=16,
                     caption="A 2V geodesic dome — desert lake, "
                             "beach shoreline",
                     narration=(
                         "This is a two V geodesic dome, dropped onto a "
                         "beach beside a desert lake.",
                         "Every scene in this video was composed from a "
                         "one line text prompt, and every shot you will "
                         "see is scripted: lens, focus target, and "
                         "camera perspective.",
                     )),
                Shot("one_point", 7.0, lens="wide", focus="dome",
                     perspective=1, yaw=0, pitch=4,
                     caption="One-point perspective — a single "
                             "vanishing point",
                     narration=(
                         "Here is the same dome in strict one point "
                         "perspective, the camera squared to the world "
                         "axes the way a draftsman would set it.",
                     )),
                Shot("apex_macro", 6.5, lens="macro", focus="apex",
                     yaw=-40, pitch=32, orbit=9,
                     caption="Two strut lengths build the whole shell",
                     narration=(
                         "Look close. Only two strut lengths, long and "
                         "short, repeat all the way around the shell.",
                     )),
            ),
        ),
        Scene(
            "problem", "Sealed buildings need lungs",
            "on a beach at a lake in the desert",
            world=_world(dome={"radius": R, "skin_alpha": 0.30}),
            shots=(
                Shot("sealed", 8.0, lens="portrait", focus="dome",
                     yaw=-95, pitch=20, orbit=10,
                     caption="Tight envelope · no windows · "
                             "where does stale air go?",
                     panel=OverlayPanel(
                         title="THE PROBLEM",
                         bullets=("A sealed dome is efficient — and "
                                  "airtight",
                                  "Moisture, CO2 and odors accumulate",
                                  "Fans in walls break the envelope"),
                         position="right"),
                     narration=(
                         "A dome this tight has a problem: it holds "
                         "heat brilliantly, but it also holds moisture, "
                         "carbon dioxide, and stale air.",
                         "Punching fan holes through a watertight shell "
                         "defeats the point of building one.",
                     )),
            ),
        ),
        Scene(
            "mechanism", "The perimeter plenum",
            "on a beach at a lake in the desert",
            world=_world(),
            shots=(
                Shot("ring_wide", 8.0, lens="wide", focus="plenum",
                     yaw=-60, pitch=34, orbit=14,
                     caption="A tube rings the base circumference",
                     narration=(
                         "The answer is already part of the "
                         "architecture. A sealed tube rings the base "
                         "circumference of the floor, hugging the "
                         "perimeter where the shell meets the deck.",
                     )),
                Shot("grille_macro", 8.5, lens="macro", focus="grille",
                     yaw=-25, pitch=10, orbit=6,
                     actions=(("plenum", "grille_open", 0.0, 1.0),),
                     caption="Louvered grilles open into every "
                             "floor bay",
                     narration=(
                         "Every bay gets a louvered grille into that "
                         "tube. Watch them open: ten small mouths "
                         "around the room, all feeding one ring.",
                     )),
                Shot("blower_macro", 8.0, lens="macro", focus="blower",
                     yaw=-70, pitch=14, orbit=8,
                     actions=(("blower", "spin", 0.0, 4.0),),
                     caption="One ordinary leaf blower at one port",
                     narration=(
                         "And here is the entire mechanical plant: one "
                         "ordinary leaf blower, clamped to a single "
                         "port, blowing from the inside of the tube "
                         "toward the outside.",
                     )),
            ),
        ),
        Scene(
            "exhaust", "Negative pressure: the building exhales",
            "on a beach at a lake in the desert",
            world=_world(dome={"radius": R, "skin_alpha": 0.10},
                         blower={"radius": R, "spin": 4.0},
                         airflow={"radius": R, "intensity": 0.0}),
            shots=(
                Shot("flow_start", 10.0, lens="wide", focus="airflow",
                     yaw=-120, pitch=30, orbit=12,
                     actions=(("airflow", "intensity", 0.0, 1.0),),
                     caption="Air: room → grilles → ring → out",
                     panel=OverlayPanel(
                         title="EXHAUST MODE",
                         stats=(("Plenum pressure", "−45 Pa"),
                                ("Room pressure", "−3 to −5 Pa"),
                                ("Air changes", "4–6 per hour"),
                                ("Moving parts", "1")),
                         position="right"),
                     narration=(
                         "Switch it on. The jet leaving the port drags "
                         "the air in the tube with it, so the ring "
                         "drops below room pressure.",
                         "Every grille becomes an exhaust register at "
                         "once. Cyan is room air sinking to the "
                         "perimeter, racing around the ring, and "
                         "leaving as the amber jet.",
                     )),
                Shot("flow_fisheye", 8.0, lens="wide", focus="airflow",
                     perspective=5, yaw=-150, pitch=42,
                     caption="Five-point fisheye — the whole loop "
                             "in one frame",
                     narration=(
                         "A five point fisheye swallows the entire "
                         "loop in a single frame: one fan, ten inlets, "
                         "one continuous current of fresh air.",
                     )),
                Shot("physics", 9.0, lens="portrait", focus="blower",
                     yaw=-45, pitch=16, orbit=8,
                     caption="Entrainment does the work",
                     panel=OverlayPanel(
                         title="WHY IT WORKS",
                         equations=("Q_ring ≈ 3–5 × Q_blower "
                                    "(entrainment)",
                                    "ΔP = ½ ρ v²  — jet trades "
                                    "pressure for speed",
                                    "leaks flow INWARD under −ΔP"),
                         bullets=("The shell stays watertight",
                                  "Backdraft impossible: air only "
                                  "leaves",),
                         position="left"),
                     narration=(
                         "The physics is a jet pump. The fast jet "
                         "entrains several times its own volume, the "
                         "ring runs at negative pressure, and every "
                         "leak in the envelope flows inward. Nothing "
                         "musty can seep out into the walls, because "
                         "the walls are always inhaling.",
                     )),
            ),
        ),
        Scene(
            "vacuum", "Reverse the intent: a central vacuum",
            "in the snow",
            world=_world(dome={"radius": R, "skin_alpha": 0.10},
                         blower={"radius": R, "spin": 4.0,
                                 "vacuum": 1.0},
                         airflow={"radius": R, "intensity": 1.0,
                                  "mode": 1.0}),
            shots=(
                Shot("vac_wide", 9.5, lens="wide", focus="hose",
                     yaw=140, pitch=24, orbit=12,
                     caption="Same ring, opposite intent — "
                             "plug in a hose anywhere",
                     panel=OverlayPanel(
                         title="VACUUM MODE",
                         bullets=("The blower already holds the ring "
                                  "below room pressure",
                                  "Any grille port accepts a hose",
                                  "Debris rides the ring to a "
                                  "canister at the blower"),
                         position="right"),
                     narration=(
                         "Now reverse the intent, not the fan. The "
                         "ring is already a suction main held below "
                         "room pressure, so plug a hose into any "
                         "port and it becomes a whole home central "
                         "vacuum.",
                         "Here in a snowbound version of the same "
                         "dome, green debris rides the ring from the "
                         "hose straight to a canister beside the "
                         "blower.",
                     )),
                Shot("vac_macro", 7.5, lens="macro", focus="canister",
                     yaw=-10, pitch=18, orbit=7,
                     caption="One canister to empty · one fan "
                             "to maintain",
                     narration=(
                         "Everything you suck up lands in one "
                         "canister, next to the one moving part in "
                         "the entire system.",
                     )),
            ),
        ),
        Scene(
            "finale", "One tube, two machines",
            "tropical beach at dusk",
            world=_world(blower={"radius": R, "spin": 4.0},
                         airflow={"radius": R, "intensity": 0.9}),
            shots=(
                Shot("finale_360", 11.0, lens="wide", focus="dome",
                     perspective=6, yaw=-90, pitch=24,
                     caption="Six-point 360° — the whole world "
                             "in one shot",
                     panel=OverlayPanel(
                         title="ONE TUBE, TWO MACHINES",
                         bullets=("Whole-building exhaust extraction",
                                  "Whole-building central vacuum",
                                  "One leaf blower · zero holes in "
                                  "the shell"),
                         position="bottom"),
                     narration=(
                         "One tube around the base circumference. "
                         "Blow through it, and the building exhales "
                         "through every pore at once. Plug into it, "
                         "and it cleans your floors.",
                         "This is what geodesic thinking looks like "
                         "applied to services: one part, bent around "
                         "a circle, doing the work of two whole "
                         "mechanical systems.",
                     )),
            ),
        ),
    )
    return Presentation(
        title="The Dome That Breathes",
        author="Presenter Studio",
        scenes=scenes,
    )
