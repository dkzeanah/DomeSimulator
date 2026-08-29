

# ----------------------------------------------------------------------
# The lesson
# ----------------------------------------------------------------------

# Every figure in the narration below is interpolated from the model at
# import time.  Nothing here is a typed-in number, so the script cannot
# drift away from the calculation the way a hand-written one would.
_ELEMENT_KG = float(DEMO_ELEMENT.weight)
_HEAVIEST = max(CATALOG.elements, key=lambda item: float(item.weight))
_FASTEN_SHARE = MOTION_KCAL["fasten"] / max(ENERGY.kcal_per_worker, 1e-9) * 100.0
_SERIAL_H = THROUGHPUT["total_cycle_min"] / 60.0
_BOTTLENECK = THROUGHPUT["bottleneck"]
_LIMB_TOTAL = sum(LIMB_WORK.values()) or 1.0
_FOOD = ENERGY.food_equivalent()
_LIFT_HEIGHT = float(DEMO_ELEMENT.centroid[2])
_LIFT_WORK = _ELEMENT_KG * 9.80665 * _LIFT_HEIGHT


CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        "overview", "01", "One building, fifteen stations",
        f"{len(CATALOG.elements)} parts, {CATALOG.total_weight():,.0f} kilograms, "
        f"and two people at every station.",
        (
            f"This is the {SPEC.name}: a {SPEC.radius:.2f} metre {SPEC.frequency}V dome home",
            f"that leaves the line as {len(CATALOG.elements)} placed parts weighing",
            f"{CATALOG.total_weight():,.0f} kilograms in total. It passes through",
            f"{len(SPEC.stages)} stations, and a crew of {CREW} works each one.",
            "Over the next chapters we are going to follow those two people through",
            "every motion they make, and account for the energy each motion costs them.",
        ),
        (f"parts = {len(CATALOG.elements)}",
         f"mass = {CATALOG.total_weight():,.0f} kg",
         f"labour = {CATALOG.labor_minutes() / 60.0:,.0f} h"),
        20.0, (24.0, 20.0, 22.0), "line_overview",
    ),
    Chapter(
        "why", "02", "What a line actually buys you",
        "Not less work. Less waiting.",
        (
            f"One crew doing all {len(SPEC.stages)} stations spends {_SERIAL_H:,.0f} hours",
            "on a dome, and the next dome cannot start until the last one is finished.",
            f"Split the same work across {len(SPEC.stages)} stations and a dome comes off",
            f"the end every {_BOTTLENECK['cycle_min'] / 60.0:.1f} hours instead.",
            "The total labour did not change at all. What changed is that nobody",
            "is standing still waiting for someone else to finish.",
        ),
        (f"serial = {_SERIAL_H:,.0f} h per dome",
         f"pipelined = {_BOTTLENECK['cycle_min'] / 60.0:.1f} h per dome"),
        20.0, (30.0, 24.0, 13.0), "line_why",
    ),
    Chapter(
        "station", "03", "Inside one station",
        "A stockpile, a dome, and two people who never leave.",
        (
            "Every station holds the same three things: the material waiting in a",
            "stockpile, the dome that arrived from the station before, and the crew.",
            "The crew does not follow the dome down the line. They stay, they learn",
            "one job completely, and a different dome arrives in front of them.",
            "That is the trade a line makes: depth of skill against variety of work.",
        ),
        (f"crew = {CREW}", f"stockpile at {DEMO_MOTIONS[0].distance:.1f} m"),
        20.0, (36.0, 26.0, 11.0), "line_station",
    ),
    Chapter(
        "bottleneck", "04", "The line runs at the speed of its slowest station",
        f"Here that is {_BOTTLENECK['key']}, and nothing else matters until it changes.",
        (
            f"Station cycle times are not equal. The {_BOTTLENECK['key']} station takes",
            f"{_BOTTLENECK['cycle_min'] / 60.0:.1f} hours, and every other station",
            "finishes early and then waits. Speeding up a fast station buys you nothing.",
            "This is the first place the energy question becomes a design question:",
            "the busiest station is also the one spending the most out of its crew.",
        ),
        (f"bottleneck = {_BOTTLENECK['key']}",
         f"cycle = {_BOTTLENECK['cycle_min'] / 60.0:.2f} h"),
        20.0, (28.0, 30.0, 13.0), "line_bottleneck",
    ),
    Chapter(
        "cycle", "05", "Every part is the same six motions",
        f"Walk, lift, carry, position, fasten, recover. {DEMO_SECONDS:.0f} seconds, "
        f"{DEMO_KCAL:.1f} kilocalories.",
        (
            "Whatever the part, the body does the same six things with it.",
            "It walks to the stockpile empty. It squats, grips, and stands the load up.",
            "It carries the load to where the part goes. It lifts the part into position,",
            "fixes it there, and straightens back up. Every one of those six has a",
            "duration taken from the part itself and a cost we can put a number on.",
        ),
        (f"one part = {DEMO_SECONDS:.0f} s",
         f"one part = {DEMO_KCAL:.2f} kcal",
         f"x {len(CATALOG.elements)} parts"),
        22.0, (18.0, 16.0, 15.0), "line_cycle",
    ),
    Chapter(
        "walk", "06", "The walk out",
        f"{DEMO_MOTIONS[0].distance:.1f} metres, empty-handed, and it still costs something.",
        (
            f"The stockpile sits {DEMO_MOTIONS[0].distance:.1f} metres from where this part",
            f"lands, so the trip out is {DEMO_MOTIONS[0].duration:.1f} seconds of walking",
            f"at {DEMO_COSTS[0].watts:.0f} watts. That is a small number on its own.",
            f"Across the whole dome those trips add up to {MOTION_KCAL['walk_out']:,.0f}",
            "kilocalories, which is exactly why stockpile placement is a real decision",
            "and not a detail left to whoever unloads the truck.",
        ),
        (f"distance = {DEMO_MOTIONS[0].distance:.2f} m",
         f"rate = {DEMO_COSTS[0].watts:.0f} W"),
        20.0, (16.0, 18.0, 14.0), "line_walk",
    ),
    Chapter(
        "lift", "07", "The lift, limb by limb",
        "Most of what you raise is yourself.",
        (
            f"Here is the squat and the stand, slowed down, with a {DEMO_MOTIONS[1].load_kg:.1f}",
            "kilogram part in the hands. Watch what the colours say: the legs straighten,",
            "the trunk comes up, the arms barely move. The trunk alone is about half the",
            f"body's mass, so raising it accounts for {LIMB_WORK['trunk'] / _LIMB_TOTAL * 100:.0f}",
            "per cent of the lifting work across the entire dome. The part is almost an",
            "afterthought next to the body carrying it.",
        ),
        (f"work = {DEMO_COSTS[1].mechanical_joules:.0f} J",
         f"fuel = {DEMO_COSTS[1].metabolic_joules:.0f} J"),
        24.0, (34.0, 14.0, 7.5), "line_lift",
    ),
    Chapter(
        "carry", "08", "Carrying is not linear in the load",
        "Double what someone carries and you more than double what it costs them.",
        (
            "Walking with a load is the one part of this that has a proper published",
            "equation behind it. Pandolf and colleagues measured it in 1977, and the",
            "load term in their equation is squared, not linear. Twenty kilograms does",
            "not cost twice what ten kilograms costs. It costs appreciably more.",
            "That single fact is the argument for carts, for conveyors, and for putting",
            "the stockpile closer, in one line.",
        ),
        (f"0 kg = {pandolf_watts(BODY_MASS_KG, 0.0, 1.05):.0f} W",
         f"40 kg = {pandolf_watts(BODY_MASS_KG, 40.0, 1.05):.0f} W"),
        22.0, (20.0, 22.0, 14.5), "line_carry",
    ),
    Chapter(
        "position", "09", "Getting it where it lands",
        f"This one goes to {_LIFT_HEIGHT:.2f} metres, and the height changes the price.",
        (
            "Positioning is the short motion between carrying a part and fastening it.",
            f"This part lands at {_LIFT_HEIGHT:.2f} metres.",
            f"Anything above {OVERHEAD_HEIGHT_M:.2f} metres is overhead work, which means",
            "the arms are above the heart, the posture costs more, and the crew fatigues",
            "faster. The dome's own geometry decides how much of the shell falls into",
            "that band, which is a design decision disguised as a shape.",
        ),
        (f"height = {_LIFT_HEIGHT:.2f} m",
         f"overhead above {OVERHEAD_HEIGHT_M:.2f} m"),
        20.0, (40.0, 18.0, 10.0), "line_position",
    ),
    Chapter(
        "fasten", "10", "Where the shift actually goes",
        f"Fastening raises nothing and spends {_FASTEN_SHARE:.0f} per cent of the fuel.",
        (
            "Here is the result that surprises people. Fastening does no lifting at all.",
            "Nothing rises. No mechanical work is done against gravity in any meaningful",
            f"amount. And it consumes {_FASTEN_SHARE:.0f} per cent of everything the crew",
            f"burns, because it is {DEMO_MOTIONS[4].duration:.0f} seconds per part of",
            "holding a posture, gripping a tool, and stabilising against its torque.",
            "The body pays for holding still. It pays a lot.",
        ),
        (f"{DEMO_MOTIONS[4].duration:.0f} s per part",
         f"{MOTION_KCAL['fasten']:,.0f} kcal per dome",
         f"mechanical share = {MOTION_EFFICIENCY['fasten'] * 100:.2f} %"),
        24.0, (26.0, 16.0, 11.0), "line_fasten",
    ),
    Chapter(
        "allowance", "11", "The rest that is not slacking",
        f"{ENERGY.rest_seconds / 3600.0:.0f} hours of this build are recovery, by design.",
        (
            "Industrial engineering has added a recovery allowance to every task time",
            "for a century. It is called the personal, fatigue and delay allowance, and",
            f"the standard figure is about {PFD_ALLOWANCE * 100:.0f} per cent on top of",
            f"the task. Overhead work earns another {PFD_OVERHEAD_EXTRA * 100:.0f} per cent",
            "because it fatigues fastest. A schedule written without it is not an",
            "efficient schedule, it is a schedule that will not be met.",
        ),
        (f"allowance = {PFD_ALLOWANCE * 100:.0f} %",
         f"overhead + {PFD_OVERHEAD_EXTRA * 100:.0f} %",
         f"total = {ENERGY.rest_seconds / 3600.0:.1f} h"),
        20.0, (22.0, 20.0, 12.5), "line_allowance",
    ),
    Chapter(
        "skeleton", "12", "The body doing the work",
        f"{BODY_MASS_KG:.0f} kilograms, and every segment of it has a known mass.",
        (
            "To cost a movement you have to know what is being moved. This figure uses",
            "Winter's anthropometric tables, the standard reference in biomechanics:",
            "each body segment is a fixed fraction of total mass, and its centre of mass",
            "sits at a fixed fraction along its length. A thigh is a tenth of the body.",
            "The trunk is almost half. Those fractions are why the numbers in this lesson",
            "come out the way they do.",
        ),
        (f"body = {BODY_MASS_KG:.0f} kg",
         f"trunk = {SEGMENTS[6].mass(BODY_MASS_KG):.1f} kg",
         f"thigh = {SEGMENTS[0].mass(BODY_MASS_KG):.1f} kg"),
        22.0, (30.0, 12.0, 7.0), "line_skeleton",
    ),
    Chapter(
        "selflift", "13", "You are the heaviest thing you lift",
        "The part is the small number in this comparison.",
        (
            f"Placing this {_ELEMENT_KG:.1f} kilogram part takes a certain amount of work",
            "to raise the part itself. It takes considerably more to raise the body that",
            "is doing it, because the body outweighs the part several times over and it",
            "goes up and down with every single placement.",
            "This is the honest reason a lower stockpile, a taller bench, or a part",
            "presented at waist height changes a shift so much.",
        ),
        (f"part = {_ELEMENT_KG:.1f} kg",
         f"body = {BODY_MASS_KG:.0f} kg"),
        20.0, (26.0, 18.0, 12.0), "line_selflift",
    ),
    Chapter(
        "limbs", "14", "Legs, trunk, arms",
        f"The trunk does {LIMB_WORK['trunk'] / _LIMB_TOTAL * 100:.0f} per cent of the "
        "lifting work.",
        (
            "Splitting the lifting work by limb group across the whole dome gives a",
            f"clear answer: legs {LIMB_WORK['legs'] / _LIMB_TOTAL * 100:.0f} per cent,",
            f"trunk {LIMB_WORK['trunk'] / _LIMB_TOTAL * 100:.0f} per cent,",
            f"arms {LIMB_WORK['arms'] / _LIMB_TOTAL * 100:.0f} per cent.",
            "The arms get all the attention because they are what you watch, but they",
            "are the lightest part of the body and they do the least raising. The back",
            "is where the work is, and that is also where the injuries are.",
        ),
        tuple(f"{group} = {LIMB_WORK[group] / _LIMB_TOTAL * 100:.1f} %"
              for group in LIMB_GROUPS),
        22.0, (28.0, 18.0, 12.5), "line_limbs",
    ),
    Chapter(
        "team", "15", "When one person stops lifting alone",
        f"Above {TWO_PERSON_LIFT_KG:.0f} kilograms it takes both of them.",
        (
            "Manual handling guidance puts the single-person limit near",
            f"{TWO_PERSON_LIFT_KG:.0f} kilograms. Above that the crew lifts together and",
            "each person carries half. The heaviest part on this dome is the",
            f"{_HEAVIEST.label.lower()} at {float(_HEAVIEST.weight):,.0f} kilograms,",
            f"which is {float(_HEAVIEST.weight) / CREW:,.0f} kilograms each.",
            "Even with every team lift split, one worker still raises",
            f"{ENERGY.lifted_mass_kg:,.0f} kilograms to build one dome.",
        ),
        (f"threshold = {TWO_PERSON_LIFT_KG:.0f} kg",
         f"heaviest = {float(_HEAVIEST.weight):,.0f} kg",
         f"raised per worker = {ENERGY.lifted_mass_kg:,.0f} kg"),
        22.0, (34.0, 14.0, 8.5), "line_team",
    ),
    Chapter(
        "overhead", "16", "The same part costs more up high",
        "Arms above the heart is the most expensive posture on the line.",
        (
            "Two workers, the same fastener, the same number of turns. One is working",
            "at deck height and one is working above their shoulders. The overhead",
            "worker is spending noticeably more per second, is fatiguing faster, and",
            "will need more recovery for the same output.",
            "Whenever the dome's geometry pushes work above that line, the cost lands",
            "on a body rather than on a spreadsheet.",
        ),
        (f"deck = {DEMO_COSTS[4].watts:.0f} W",
         f"overhead = {met_watts(4.2):.0f} W"),
        20.0, (32.0, 14.0, 9.5), "line_overhead",
    ),
    Chapter(
        "work", "17", "The part that is exact",
        "Mass times gravity times height. No estimate anywhere in it.",
        (
            "Raising a part is the one piece of this with no modelling in it at all.",
            f"This part weighs {_ELEMENT_KG:.1f} kilograms and rises",
            f"{_LIFT_HEIGHT:.2f} metres, so the work done on it is",
            f"{_LIFT_WORK:,.0f} joules.",
            "The mass comes from the catalogue, the height comes from the dome's",
            "geometry, and gravity is gravity. Every mechanical number in this lesson",
            "is that calculation, run once per segment and once per part.",
        ),
        (f"m = {_ELEMENT_KG:.1f} kg",
         f"h = {_LIFT_HEIGHT:.2f} m",
         f"W = {_LIFT_WORK:,.0f} J"),
        20.0, (24.0, 16.0, 10.0), "line_work",
    ),
    Chapter(
        "model", "18", "The part that is a model",
        "Kilocalories are not measured here. They are estimated, and here is from what.",
        (
            "A muscle holding a panel steady does no mechanical work and still burns",
            "fuel, so there is no way to get from joules of lifting to kilocalories of",
            "food without external information. This lesson uses published task",
            "intensities for stationary work and the Pandolf equation for walking.",
            f"There are {len(EXTERNAL_CONSTANTS)} such constants, every one of them named",
            "in the report. Change the efficiency figure and every calorie here moves.",
        ),
        (f"external constants = {len(EXTERNAL_CONSTANTS)}",
         "computed: mass, height, distance",
         "assumed: intensity, efficiency"),
        22.0, (18.0, 22.0, 13.0), "line_model",
    ),
    Chapter(
        "efficiency", "19", "Nineteen per cent, and a fifth of one per cent",
        "Both are true. They answer different questions.",
        (
            f"During the lift itself, {MOTION_EFFICIENCY['lift'] * 100:.0f} per cent of the",
            "fuel becomes height, which is close to what muscle can manage at best.",
            f"Across the whole dome, mechanical work is {ENERGY.mechanical_fraction * 100:.2f}",
            "per cent of the food energy. The difference is not an error. It is that",
            "almost none of a working day is spent lifting. The rest is posture, grip,",
            "stabilising, and holding still, and none of that raises anything.",
        ),
        (f"lift = {MOTION_EFFICIENCY['lift'] * 100:.1f} %",
         f"build = {ENERGY.mechanical_fraction * 100:.3f} %",
         f"muscle ceiling = {CONCENTRIC_EFFICIENCY * 100:.0f} %"),
        24.0, (26.0, 22.0, 13.0), "line_efficiency",
    ),
    Chapter(
        "motions", "20", "The whole dome, by motion",
        f"{ENERGY.kcal_per_worker:,.0f} kilocalories per worker, and where each one went.",
        (
            "Here is every motion of every part, totalled. Fastening dominates, because",
            "fastening is where the time is. Walking, lifting, carrying and positioning",
            "together are a small fraction, even though they are the parts that look",
            "like work and the parts a manager would think to optimise.",
            "If you want to reduce what this line costs its crew, the target is the",
            "posture people hold while fastening, not the distance they walk.",
        ),
        tuple(f"{name} = {kcal:,.0f} kcal"
              for name, kcal in sorted(MOTION_KCAL.items(),
                                       key=lambda kv: -kv[1])[:4]),
        22.0, (24.0, 26.0, 13.5), "line_motions",
    ),
    Chapter(
        "stations", "21", "The ledger, station by station",
        "The busiest station is also the hungriest one.",
        (
            "Broken down per station, the energy follows the part count and the time,",
            "not the tonnage. Stations that place many light pieces slowly cost their",
            "crews more than stations that place a few heavy ones quickly.",
            "This is the table to look at when deciding where a jig, a lift assist, or",
            "an extra pair of hands would actually change someone's day.",
        ),
        tuple(f"{key} = {row['kcal']:,.0f} kcal"
              for key, row in sorted(STAGE_ENERGY.items(),
                                     key=lambda kv: -kv[1]["kcal"])[:4]),
        22.0, (26.0, 26.0, 13.5), "line_stations",
    ),
    Chapter(
        "shift", "22", "What one working day costs",
        f"{ENERGY.kcal_per_shift:,.0f} kilocalories, at {ENERGY.mean_met:.2f} METs.",
        (
            f"Averaged over the build, the crew works at {ENERGY.mean_watts:.0f} watts,",
            f"which is {ENERGY.mean_met:.2f} times resting metabolism.",
            "Occupational physiology puts the ceiling for a sustained eight-hour shift",
            f"at roughly {SUSTAINABLE_SHIFT_WATTS:.0f} watts, so this line sits just",
            "under it, with the recovery allowance included. Take the allowance away",
            "and the same work stops being sustainable, which is the whole point of it.",
        ),
        (f"rate = {ENERGY.mean_watts:.0f} W",
         f"per shift = {ENERGY.kcal_per_shift:,.0f} kcal",
         f"shifts = {ENERGY.shifts:.1f} per dome"),
        22.0, (28.0, 22.0, 13.0), "line_shift",
    ),
    Chapter(
        "food", "23", "The total, in food",
        f"{ENERGY.kcal_crew:,.0f} kilocalories to build one house.",
        (
            f"The two of them together spend {ENERGY.kcal_crew:,.0f} kilocalories turning",
            f"{CATALOG.total_weight():,.0f} kilograms of material into a finished dome.",
            f"That is about {_FOOD[0][1]:,.0f} slices of bread, or",
            f"{_FOOD[1][1]:,.0f} bananas, or {_FOOD[2][1]:.0f} days of eating at",
            "two and a half thousand kilocalories a day.",
            "It is a real cost, it is paid by people, and until now it was not on any",
            "drawing of this building.",
        ),
        (f"crew total = {ENERGY.kcal_crew:,.0f} kcal",
         f"= {_FOOD[0][1]:,.0f} slices of bread",
         f"= {_FOOD[2][1]:.0f} days of eating"),
        22.0, (20.0, 20.0, 15.0), "line_food",
    ),
    Chapter(
        "recap", "24", "What the ledger changes",
        "Design the posture, not just the part.",
        (
            "We followed two people through every motion needed to build one dome and",
            "put a number on each one. The parts that look like effort turned out to be",
            "cheap. The part that looks like nothing, holding a position while fastening,",
            "turned out to be almost the whole bill.",
            "Every figure came from a part mass, a placement height, a walk distance, or",
            "a named published constant, and every one of them can be recomputed rather",
            "than trusted. That is the only reason it is worth putting on screen.",
        ),
        (f"{len(CATALOG.elements)} parts",
         f"{ENERGY.hours_per_worker:.0f} h per worker",
         f"{ENERGY.kcal_crew:,.0f} kcal for the crew"),
        22.0, (24.0, 24.0, 20.0), "line_recap",
    ),
)


def _selftest() -> None:
    validate_figure()
    validate_energetics()


LINE_LESSON = Lesson(
    key="line",
    brand="ASSEMBLY LINE / THE ENERGY LEDGER",
    title="Assembly Line Energy Masterclass",
    chapters=CHAPTERS,
    scenes=SCENES,
    equations=line_equations,
    selftest=_selftest,
    report=energy_report,
    snapshot_prefix="line",
)
