"""The object library: everything you can put on a stage, and its knobs.

The scene composer needs more than a list of emitter functions. For a
person who has never written code to place a water tank and then change
how full it is, the editor has to know that "level" is a number between 0
and 1, that it means *how full*, and that it is worth a slider.

So each placeable object is described here by an :class:`ObjectSpec`
carrying a plain-English blurb and a tuple of :class:`ParamSpec` knobs.
The same ``ParamSpec`` type the dome builder already uses is reused, so
there is one description of "what a tunable knob is" in the project
rather than two.

Three families of object are catalogued:

* the star objects from :mod:`presenter.world` (dome, plenum, blower...),
* the accessories and appliances from :mod:`presenter.accessories`,
* every layer the Dome Forge builder can draw, bridged in as-is, so a
  movie can use the rain veins, cistern and panel work already modelled
  there instead of a second copy of them.
"""

from __future__ import annotations

from dataclasses import dataclass

from dome_forge.layers import LAYER_KINDS, ParamSpec

FORGE_PREFIX = "forge:"


@dataclass(frozen=True)
class ObjectSpec:
    """One placeable thing, and everything the editor needs to show it."""

    key: str
    label: str
    category: str
    blurb: str
    params: tuple[ParamSpec, ...] = ()

    def spec(self, key: str) -> ParamSpec | None:
        for param in self.params:
            if param.key == key:
                return param
        return None

    def defaults(self) -> dict:
        return {param.key: param.default for param in self.params}


def _radius(default: float = 4.8) -> ParamSpec:
    return ParamSpec(
        "radius", "Dome radius", "float", default, 1.5, 12.0, 0.1, unit="m",
        help="How big the dome is, measured from the middle of the floor "
             "to the shell. Accessories use it to stay attached when you "
             "resize the dome.")


def _az(key: str = "az_deg", label: str = "Bearing",
        default: float = 0.0) -> ParamSpec:
    return ParamSpec(
        key, label, "float", default, -180.0, 360.0, 1.0, unit="deg",
        help="Which way around the dome this sits, like a compass "
             "bearing. Change it to move the piece around the circle.")


def _ring(default: float = 0.6) -> ParamSpec:
    return ParamSpec(
        "ring_frac", "Distance out", "float", default, 0.0, 2.0, 0.01,
        unit="x", help="How far from the middle of the floor it stands, "
                       "as a fraction of the dome radius. 1.0 is right at "
                       "the wall; above 1.0 is outside the dome.")


def _reveal(label: str = "How much is there") -> ParamSpec:
    return ParamSpec(
        "reveal", label, "float", 1.0, 0.0, 1.0, 0.01,
        help="0 is nothing, 1 is all of it. Animate it across a shot and "
             "the pieces appear one after another while the camera "
             "watches.")


# ---------------------------------------------------------------------------
# The stage's star objects (presenter/world.py)
# ---------------------------------------------------------------------------

_STAGE_SPECS: tuple[ObjectSpec, ...] = (
    ObjectSpec(
        "dome", "2V dome frame", "Dome",
        "The geodesic frame itself, built from the project's real 2V "
        "geometry: 65 struts in exactly two lengths, 40 triangles, 26 "
        "hubs. Everything else is positioned against it.",
        (_radius(),
         ParamSpec("strut", "Strut thickness", "float", 0.055, 0.01, 0.25,
                   0.005, unit="m",
                   help="How thick each frame member looks."),
         ParamSpec("skin_alpha", "Skin haze", "float", 0.16, 0.0, 1.0, 0.01,
                   help="How solid the covering over the triangles looks. "
                        "0 leaves a bare frame you can see straight "
                        "through."))),
    ObjectSpec(
        "shell_layers", "Shell build-up", "Dome",
        "The wall as it really goes together, one layer at a time: "
        "insulation, sheetrock, sheathing, wrap, shingles, then the outer "
        "shell. Drive 'Layers shown' up across a shot to build the wall "
        "on camera.",
        (_radius(),
         ParamSpec("stage", "Layers shown", "float", 6.0, 0.0, 6.0, 0.05,
                   help="0 is a bare frame; 6 is a finished wall. Halfway "
                        "values fade the next layer in."),
         ParamSpec("explode", "Gap between layers", "float", 0.35, 0.0, 1.2,
                   0.01, unit="m",
                   help="Pulls the layers apart so you can see each one. "
                        "Set it to 0 for a realistic, tight wall."),
         ParamSpec("alpha_mult", "See-through", "float", 1.0, 0.0, 1.0, 0.01,
                   help="Fade the whole wall out to look at something "
                        "inside it without deleting the wall."))),
    ObjectSpec(
        "solar_band", "Solar array", "Dome",
        "Photovoltaic panels laid on the actual dome triangles that face "
        "near enough to the sun. It picks the faces by angle, so the "
        "array is always a real, buildable set of panels.",
        (_radius(),
         _az("south_az_deg", "Sun bearing", -90.0),
         ParamSpec("tolerance_deg", "Angle allowance", "float", 55.0, 5.0,
                   90.0, 1.0, unit="deg",
                   help="How far off the sun a face may point and still be "
                        "worth a panel. Bigger means more panels."),
         ParamSpec("min_polar_deg", "Skip the crown", "float", 18.0, 0.0,
                   80.0, 1.0, unit="deg",
                   help="Leaves the flat area right at the top bare."),
         ParamSpec("coverage", "How many fitted", "float", 1.0, 0.0, 1.0,
                   0.01,
                   help="Fit only part of the qualifying faces, so a shot "
                        "can show the array going on."))),
    ObjectSpec(
        "hatch", "Deck hatch", "Dome",
        "A watertight hatch with a raised curb, a hinged door and a "
        "locking wheel. 'Open' swings it.",
        (_radius(),
         ParamSpec("polar_deg", "Height on the shell", "float", 62.0, 0.0,
                   90.0, 1.0, unit="deg",
                   help="Measured down from the very top: 0 is the crown, "
                        "90 is down at the floor."),
         _az(),
         ParamSpec("hatch_r", "Hatch size", "float", 0.5, 0.15, 1.5, 0.01,
                   unit="m", help="Radius of the opening."),
         ParamSpec("open", "Open", "float", 0.0, 0.0, 1.0, 0.01,
                   help="0 is dogged shut, 1 is swung wide."))),
    ObjectSpec(
        "plenum", "Perimeter plenum", "Air & water",
        "The ring duct around the base with louvred grilles: the air path "
        "that lets one blower hold a whole dome at negative pressure.",
        (_radius(),
         ParamSpec("ring_frac", "Ring size", "float", 0.96, 0.5, 1.2, 0.01,
                   unit="x",
                   help="Ring radius as a fraction of the dome radius."),
         ParamSpec("tube", "Duct thickness", "float", 0.30, 0.05, 0.8, 0.01,
                   unit="m", help="How fat the ring duct is."),
         ParamSpec("ports", "Grilles", "int", 10, 2, 24, 1,
                   help="How many grilles are spaced around the ring."),
         ParamSpec("grille_open", "Louvres open", "float", 1.0, 0.0, 1.0,
                   0.01, help="Tilts the louvre blades open or shut."),
         _az("blower_az", "Blower bearing", -30.0),
         _az("hose_az", "Hose bearing", 150.0))),
    ObjectSpec(
        "blower", "Blower + hose", "Air & water",
        "The leaf blower on the ring, its nozzle, and the hose inlet on "
        "the far side. Turn 'Vacuum can' on for the suction story.",
        (_radius(),
         ParamSpec("spin", "Fan speed", "float", 3.0, 0.0, 12.0, 0.1,
                   help="Turns of the fan per second. 0 stops it dead."),
         ParamSpec("vacuum", "Vacuum can", "float", 0.0, 0.0, 1.0, 1.0,
                   help="Adds the collection canister beside the blower."),
         ParamSpec("ring_frac", "Ring size", "float", 0.96, 0.5, 1.2, 0.01,
                   unit="x", help="Match this to the plenum's ring size."),
         ParamSpec("tube", "Duct thickness", "float", 0.30, 0.05, 0.8, 0.01,
                   unit="m", help="Match this to the plenum's duct."),
         _az("blower_az", "Blower bearing", -30.0),
         _az("hose_az", "Hose bearing", 150.0))),
    ObjectSpec(
        "airflow", "Moving air", "Air & water",
        "The air itself, drawn as moving particles: room air sinking to "
        "the grilles, racing around the ring, and jetting outside. Switch "
        "'Direction' to run the same loop backwards as a shop vacuum.",
        (_radius(),
         ParamSpec("intensity", "How much air", "float", 0.7, 0.0, 1.0,
                   0.01, help="Fewer or more particles, moving slower or "
                              "faster. 0 turns the air off."),
         ParamSpec("mode", "Direction", "float", 0.0, 0.0, 1.0, 1.0,
                   help="0 blows air out of the dome; 1 sucks debris in "
                        "through the hose instead."),
         ParamSpec("ring_frac", "Ring size", "float", 0.96, 0.5, 1.2, 0.01,
                   unit="x", help="Match this to the plenum's ring size."),
         ParamSpec("ports", "Grilles", "int", 10, 2, 24, 1,
                   help="Match this to the plenum's grille count."),
         _az("blower_az", "Blower bearing", -30.0),
         _az("hose_az", "Hose bearing", 150.0))),
    ObjectSpec(
        "utility_column", "Utility column", "Inside",
        "The floor-to-crown column carrying water and power, with a "
        "lifting ring at the top. This is the answer to 'you can't put "
        "cabinets against a curved wall'.",
        (_radius(),
         _reveal("How tall so far"),
         ParamSpec("col_r", "Column thickness", "float", 0.22, 0.05, 0.8,
                   0.01, unit="m", help="Radius of the main column."),
         ParamSpec("anchor", "Lifting ring", "float", 1.0, 0.0, 1.0, 1.0,
                   help="Adds the ring and hooks at the top."))),
    ObjectSpec(
        "interior_fixtures", "Fixture blocks", "Inside",
        "Quick massing blocks for a kitchen, a bed and a bathroom, to "
        "show a floor plan working without modelling every appliance.",
        (_radius(), _reveal(),
         _az("kitchen_az", "Kitchen bearing", -35.0),
         _az("bed_az", "Bed bearing", 130.0),
         _az("bath_az", "Bath bearing", 220.0))),
    ObjectSpec(
        "comparison_pair", "Box vs dome", "Diagrams",
        "A rectangular building and a dome side by side, both drawn from "
        "real dimensions you set, for an honest size comparison.",
        (ParamSpec("box_w", "Box width", "float", 4.0, 1.0, 20.0, 0.1,
                   unit="m", help="Width of the rectangular building."),
         ParamSpec("box_l", "Box depth", "float", 4.0, 1.0, 20.0, 0.1,
                   unit="m", help="Depth of the rectangular building."),
         ParamSpec("box_h", "Box height", "float", 3.0, 1.0, 12.0, 0.1,
                   unit="m", help="Wall height of the rectangular "
                                  "building."),
         ParamSpec("dome_r", "Dome radius", "float", 2.6, 1.0, 12.0, 0.1,
                   unit="m", help="Radius of the dome beside it."),
         ParamSpec("gap", "Gap between", "float", 2.5, 0.0, 12.0, 0.1,
                   unit="m", help="Space left between the two."))),
    ObjectSpec(
        "triangle_vs_square", "Racking test", "Diagrams",
        "The rigidity demonstration: push a plain square frame and it "
        "leans over; a triangle, or a square with one diagonal, does not.",
        (ParamSpec("size", "Frame size", "float", 2.4, 0.5, 8.0, 0.1,
                   unit="m", help="Side length of both frames."),
         ParamSpec("shear", "Push", "float", 0.0, 0.0, 1.0, 0.01,
                   help="How hard you are shoving sideways. Animate this "
                        "from 0 to 1 to make the square rack on camera."),
         ParamSpec("braced", "Add the diagonal", "float", 0.0, 0.0, 1.0,
                   1.0, help="Puts one diagonal in the square, which stops "
                             "it racking however hard you push."),
         ParamSpec("gap", "Gap between", "float", 3.2, 0.5, 12.0, 0.1,
                   unit="m", help="Space between the two frames."))),
)


# ---------------------------------------------------------------------------
# Accessories and appliances (presenter/accessories.py)
# ---------------------------------------------------------------------------

_ACCESSORY_SPECS: tuple[ObjectSpec, ...] = (
    ObjectSpec(
        "door", "Entry door", "Dome",
        "A framed door standing in the dome's lower band, with jambs, a "
        "header, a threshold and a handle. 'Open' swings the leaf.",
        (_radius(), _az(),
         ParamSpec("width", "Door width", "float", 0.92, 0.6, 1.8, 0.01,
                   unit="m", help="Clear width of the opening."),
         ParamSpec("height", "Door height", "float", 2.05, 1.6, 2.6, 0.01,
                   unit="m", help="Height of the opening."),
         ParamSpec("open", "Open", "float", 0.0, 0.0, 1.0, 0.01,
                   help="0 is shut, 1 is swung wide open."))),
    ObjectSpec(
        "window_band", "Windows", "Dome",
        "Glazes the dome's own triangles in a band around the shell, so "
        "the windows are real panels of the structure rather than holes "
        "cut in it.",
        (_radius(),
         ParamSpec("polar_deg", "Band height", "float", 58.0, 0.0, 90.0,
                   1.0, unit="deg",
                   help="Measured down from the crown: small numbers are "
                        "high up, 90 is down at the floor."),
         ParamSpec("spread_deg", "Band thickness", "float", 16.0, 2.0, 45.0,
                   1.0, unit="deg",
                   help="How tall a band of triangles gets glazed."),
         _az(),
         ParamSpec("arc_deg", "How far around", "float", 360.0, 20.0, 360.0,
                   5.0, unit="deg",
                   help="360 rings the whole dome; smaller values glaze "
                        "only one side, centred on the bearing."),
         ParamSpec("tint", "Glass tint", "float", 0.30, 0.02, 0.9, 0.01,
                   help="How dark the glass is. Low values are nearly "
                        "clear."))),
    ObjectSpec(
        "skylight", "Skylight", "Dome",
        "Glazing over the crown triangles with a raised curb around the "
        "ring, for daylight straight down the middle.",
        (_radius(),
         ParamSpec("polar_deg", "How wide", "float", 30.0, 5.0, 70.0, 1.0,
                   unit="deg",
                   help="How far down from the very top the glazing "
                        "reaches."),
         ParamSpec("tint", "Glass tint", "float", 0.24, 0.02, 0.9, 0.01,
                   help="How dark the glass is."),
         ParamSpec("curb", "Curb ring", "float", 1.0, 0.0, 1.0, 1.0,
                   help="Adds the raised flashing ring around the "
                        "glazing."))),
    ObjectSpec(
        "wood_stove", "Wood stove", "Inside",
        "A stove on a hearth pad with a flue running up to the crown. "
        "Turn the fire up and the firebox glows and heat rises.",
        (_radius(), _az("az_deg", "Bearing", 150.0), _ring(0.45),
         ParamSpec("fire", "Fire", "float", 0.6, 0.0, 1.0, 0.01,
                   help="0 is cold and dark; 1 is roaring."),
         ParamSpec("flue_h", "Flue height", "float", 3.2, 1.0, 9.0, 0.1,
                   unit="m", help="How far up the flue pipe runs."))),
    ObjectSpec(
        "water_tank", "Water tank", "Air & water",
        "A cistern with hoop ribs, a tap and a visible water line. "
        "Animate 'How full' to fill or drain it on camera.",
        (_radius(), _az("az_deg", "Bearing", 210.0), _ring(1.35),
         ParamSpec("tank_r", "Tank radius", "float", 0.62, 0.2, 2.5, 0.01,
                   unit="m", help="How wide the tank is."),
         ParamSpec("tank_h", "Tank height", "float", 1.90, 0.5, 5.0, 0.05,
                   unit="m", help="How tall the tank is."),
         ParamSpec("level", "How full", "float", 0.62, 0.0, 1.0, 0.01,
                   help="0 is empty, 1 is brimming."))),
    ObjectSpec(
        "rain_catch", "Rain catchment", "Air & water",
        "A gutter ring around the base with a downspout. A dome is one "
        "continuous catchment surface, and this shows the water running "
        "down it into the ring.",
        (_radius(),
         ParamSpec("ring_frac", "Ring size", "float", 1.0, 0.6, 1.4, 0.01,
                   unit="x",
                   help="Gutter radius as a fraction of the dome radius."),
         ParamSpec("flow", "Rainfall", "float", 0.7, 0.0, 1.0, 0.01,
                   help="How hard it is raining. 0 is dry."),
         _az("spout_az_deg", "Downspout bearing", 300.0))),
    ObjectSpec(
        "battery_rack", "Batteries + inverter", "Inside",
        "The off-grid power wall: a rack of cells with charge lights and "
        "an inverter cabinet beside it.",
        (_radius(), _az("az_deg", "Bearing", 250.0), _ring(0.72),
         ParamSpec("cells", "Battery count", "int", 6, 2, 16, 1,
                   help="How many battery boxes are in the rack."),
         ParamSpec("charge", "State of charge", "float", 0.75, 0.0, 1.0,
                   0.01, help="How many cells show a green light."))),
    ObjectSpec(
        "mini_split", "Heat pump", "Inside",
        "A ductless heat pump: the indoor head mounted on the shell and "
        "the condenser outside, joined by its line set. 'Air output' "
        "streams conditioned air off the head.",
        (_radius(), _az("az_deg", "Bearing", 40.0),
         ParamSpec("polar_deg", "Head height", "float", 55.0, 10.0, 85.0,
                   1.0, unit="deg",
                   help="How high up the wall the indoor unit is, measured "
                        "down from the crown."),
         ParamSpec("spin", "Fan speed", "float", 2.0, 0.0, 10.0, 0.1,
                   help="Turns per second of the outdoor fan."),
         ParamSpec("flow", "Air output", "float", 0.6, 0.0, 1.0, 0.01,
                   help="How much air the indoor head is throwing."),
         ParamSpec("ring_frac", "Condenser distance", "float", 1.22, 1.0,
                   2.5, 0.01, unit="x",
                   help="How far outside the dome the condenser sits."))),
    ObjectSpec(
        "loft", "Loft deck", "Inside",
        "A mezzanine floor with a guard rail and a ladder. A dome's upper "
        "volume only counts as living space if you can stand on some of "
        "it.",
        (_radius(),
         ParamSpec("deck_z", "Deck height", "float", 2.35, 0.8, 6.0, 0.05,
                   unit="m", help="How high above the floor the deck is."),
         ParamSpec("span", "Deck reach", "float", 0.62, 0.2, 0.95, 0.01,
                   unit="x",
                   help="How far out to the wall the deck goes, as a "
                        "fraction of the dome radius."),
         ParamSpec("arc_deg", "How far around", "float", 190.0, 30.0, 350.0,
                   5.0, unit="deg",
                   help="How much of the circle the deck covers."),
         _az("az_deg", "Bearing", 90.0),
         ParamSpec("rail_h", "Rail height", "float", 1.0, 0.4, 1.4, 0.01,
                   unit="m", help="Height of the guard rail."))),
    ObjectSpec(
        "deck", "Outside deck", "Outside",
        "An exterior deck with a rail and steps, sitting outside the "
        "door.",
        (_radius(), _az(),
         ParamSpec("width", "Deck width", "float", 3.4, 1.0, 10.0, 0.1,
                   unit="m", help="How wide the deck is along the wall."),
         ParamSpec("depth", "Deck depth", "float", 2.2, 0.8, 8.0, 0.1,
                   unit="m", help="How far it reaches away from the dome."),
         ParamSpec("deck_z", "Deck height", "float", 0.34, 0.05, 2.0, 0.01,
                   unit="m", help="How high the deck floor sits."),
         ParamSpec("steps", "Steps", "int", 3, 0, 8, 1,
                   help="How many steps down to the ground."))),
    ObjectSpec(
        "kitchen_run", "Kitchen", "Inside",
        "A counter run with a sink and tap, a range with burners, and a "
        "refrigerator. 'How much is there' brings them in one at a time.",
        (_radius(), _az("az_deg", "Bearing", -35.0), _ring(0.60),
         ParamSpec("run", "Counter length", "float", 2.80, 1.0, 6.0, 0.05,
                   unit="m", help="How long the counter run is."),
         _reveal())),
    ObjectSpec(
        "furniture", "Living set", "Inside",
        "A table with chairs around it and a sofa facing the middle -- "
        "enough furniture to read the room as somewhere people live.",
        (_radius(), _az("az_deg", "Bearing", 60.0), _ring(0.42),
         ParamSpec("table_r", "Table size", "float", 0.62, 0.3, 1.6, 0.01,
                   unit="m", help="Radius of the table top."),
         ParamSpec("chairs", "Chairs", "int", 4, 0, 10, 1,
                   help="How many chairs are set around the table."))),
    ObjectSpec(
        "wheelchair", "Wheelchair + rider", "Accessibility",
        "A person in a manual wheelchair that follows one continuous route: "
        "up the entry ramp, in through the door, a full turn in place, and "
        "a tour of the open floor. Animate 'Along the route' across a shot "
        "and, with the camera looking at it, they roll through the home.",
        (_radius(),
         ParamSpec("progress", "Along the route", "float", 0.0, 0.0, 1.0,
                   0.01,
                   help="0 is out on the approach; ~0.4 is inside after the "
                        "ramp; ~0.5 is mid-pivot; 1 is settled by the "
                        "living set. Animate it to make them move."),
         ParamSpec("occupant", "Show the rider", "float", 1.0, 0.0, 1.0, 1.0,
                   help="Turn off for an empty chair."),
         ParamSpec("ramp_rise", "Match the ramp rise", "float", 0.30, 0.05,
                   0.9, 0.01, unit="m",
                   help="Keep this equal to the ramp's rise so the chair "
                        "meets the ramp cleanly."),
         ParamSpec("ramp_slope", "Match the ramp slope", "float", 12.0, 8.0,
                   20.0, 0.5,
                   help="Keep this equal to the ramp's slope number."))),
    ObjectSpec(
        "ramp", "Entry ramp", "Accessibility",
        "A zero-threshold ramp at the door: a level landing, then a slope "
        "down to the ground, with handrails. The run is derived from the "
        "rise and the slope, so it is always drawn to the slope you ask "
        "for -- 1:12 is the ADA maximum.",
        (_radius(), _az(),
         ParamSpec("width", "Ramp width", "float", 1.5, 0.9, 3.0, 0.05,
                   unit="m", help="How wide the ramp and landing are."),
         ParamSpec("rise", "Height climbed", "float", 0.30, 0.05, 0.9, 0.01,
                   unit="m", help="How far up from the ground to the floor."),
         ParamSpec("slope", "Slope (1 : this)", "float", 12.0, 8.0, 20.0,
                   0.5,
                   help="One unit up for this many along. 12 is the ADA "
                        "maximum; bigger numbers are gentler."))),
    ObjectSpec(
        "ceiling_lift", "Ceiling hoist", "Accessibility",
        "A ceiling-track patient lift slung between two points on the "
        "frame, with a carriage and a strap that lowers a sling. Because "
        "the shell is a rigid space frame, a hoist can anchor to it "
        "anywhere. Animate 'Lower the sling' for a transfer.",
        (_radius(),
         _az("az_deg", "Track bearing", 90.0),
         ParamSpec("polar_deg", "Track height", "float", 42.0, 20.0, 70.0,
                   1.0, unit="deg",
                   help="How high the track sits, measured down from the "
                        "crown. Smaller is higher."),
         ParamSpec("carriage", "Along the track", "float", 0.5, 0.0, 1.0,
                   0.01, help="Where the hoist sits along its rail."),
         ParamSpec("lower", "Lower the sling", "float", 0.4, 0.0, 1.0, 0.01,
                   help="0 is stowed up at the track; 1 is lowered for a "
                        "transfer."))),
    ObjectSpec(
        "grab_bar", "Grab bar", "Accessibility",
        "A wall grab bar mounted on the shell. It anchors straight to a "
        "frame member, which a stud wall can rarely promise at the exact "
        "spot a transfer needs one.",
        (_radius(), _az("az_deg", "Bearing", 210.0),
         ParamSpec("polar_deg", "Height on the wall", "float", 74.0, 40.0,
                   88.0, 1.0, unit="deg",
                   help="Measured down from the crown; bigger is lower on "
                        "the wall."),
         ParamSpec("length", "Bar length", "float", 0.9, 0.3, 1.6, 0.05,
                   unit="m", help="How long the grab bar is."))),
)


# ---------------------------------------------------------------------------
# Dome Forge layers, bridged in
# ---------------------------------------------------------------------------

def _forge_specs() -> tuple[ObjectSpec, ...]:
    """Expose every Dome Forge layer as a placeable stage object.

    These are the same emitters the dome builder draws with -- the strut
    frame, the dimpled panels, the vein network, the cistern, the rain --
    so a movie is showing the real modelled dome, not a stand-in."""
    out = []
    for kind in LAYER_KINDS:
        out.append(ObjectSpec(
            key=FORGE_PREFIX + kind.key,
            label=kind.label,
            category="Dome Forge layers",
            blurb=kind.blurb,
            params=(_radius(),) + kind.params,
        ))
    return tuple(out)


OBJECT_SPECS: tuple[ObjectSpec, ...] = (
    _STAGE_SPECS + _ACCESSORY_SPECS + _forge_specs())

SPEC_BY_KEY: dict[str, ObjectSpec] = {s.key: s for s in OBJECT_SPECS}

CATEGORIES: tuple[str, ...] = tuple(
    dict.fromkeys(spec.category for spec in OBJECT_SPECS))


def specs_in(category: str) -> tuple[ObjectSpec, ...]:
    return tuple(s for s in OBJECT_SPECS if s.category == category)


def defaults_for(key: str) -> dict:
    """The starting parameters for a freshly placed object."""
    spec = SPEC_BY_KEY.get(key)
    return spec.defaults() if spec else {}


def label_for(key: str) -> str:
    spec = SPEC_BY_KEY.get(key)
    return spec.label if spec else key


def clamp_param(key: str, param: str, value):
    """Keep an edited value inside what the object can actually accept."""
    spec = SPEC_BY_KEY.get(key)
    if spec is None:
        return value
    ps = spec.spec(param)
    return ps.clamp(value) if ps else value
