"""Linseed Oil for a Dome: a source-audited Cabin World workshop film."""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from . import cabin_world as cw, cabin_stage, channel_scene as sc, shots
from . import linseed_oil as oil
from .lessons import Chapter, Lesson
from .render_kit import TriangleBatch, WorldLabel

F, C = oil.facts(), oil.C
WHITE, AMBER, GREEN, RED = (240, 236, 226), (255, 205, 130), (111, 235, 155), (255, 140, 120)
WOOD = (0.80, 0.58, 0.33, 1.0)
OILED = (0.53, 0.29, 0.10, 1.0)
STEEL = (0.58, 0.64, 0.70, 1.0)

# Scene dressing, metres, not fabrication dimensions. The finish station uses
# the existing second bench landmark; the seam specimen remains at BENCH_A.
TABLE_SIZE = (1.12, sc.SPECIMEN_LEN, 0.055)
TABLE_TOP = sc.SAWHORSE_TOP + 0.06
TABLE = np.array([*sc.BENCH_B, TABLE_TOP])
SAMPLE_SIZE = (0.56, 0.25, 0.045)


def label(app, position, text, colour=WHITE):
    app.world_labels.append(WorldLabel(np.asarray(position, dtype=np.float32), text, colour))


@lru_cache(maxsize=1)
def station():
    batch = TriangleBatch()
    sc._sawhorses(batch, sc.BENCH_B)
    batch.box(TABLE - [0, 0, TABLE_SIZE[2] / 2], TABLE_SIZE, (0.30, 0.22, 0.14, 1))
    return batch


def bench(app):
    cw.paint(app, subject=False)
    points = [TABLE + [x, y, z] for x in (-0.58, 0.58)
              for y in (-0.46, 0.46) for z in (0, 0.50)]
    app.static_layer("linseed:station", station, points)


def solid_cylinder(batch, start, end, radius, colour, sides=16):
    """Reuse the house cylinder, correcting its winding for these closed props.

    The shared primitive's side winding faces inward under back-face culling,
    and its cap fan omits the first and closing sectors. Fix only this new
    film's props so earlier films keep their original geometry.
    """
    mesh = TriangleBatch()
    start, end = np.asarray(start, float), np.asarray(end, float)
    mesh.cylinder(start, end, radius, colour, sides)
    axis = end - start
    axis /= np.linalg.norm(axis)
    trial = np.array([0., 1., 0.]) if abs(axis[2]) > 0.88 else np.array([0., 0., 1.])
    tangent = np.cross(axis, trial)
    tangent /= np.linalg.norm(tangent)
    bitangent = np.cross(axis, tangent)
    for centre, normal in ((start, -axis), (end, axis)):
        for k in (0, sides - 1):
            points = [centre + radius * (tangent * math.cos(math.tau * j / sides)
                                         + bitangent * math.sin(math.tau * j / sides))
                      for j in (k, k + 1)]
            mesh.triangle(centre, *points, colour, normal)
    triangles = np.asarray(mesh.vertices).reshape(-1, 3, 10)
    geometric = np.cross(triangles[:, 1, :3] - triangles[:, 0, :3],
                         triangles[:, 2, :3] - triangles[:, 0, :3])
    inward = np.sum(geometric * triangles[:, :, 3:6].mean(axis=1), axis=1) < 0
    triangles[inward] = triangles[inward][:, [0, 2, 1], :]
    batch.vertices.extend(triangles.ravel().tolist())


def bottle(batch, pos, tint, height=0.22):
    pos = np.asarray(pos)
    solid_cylinder(batch, pos, pos + [0, 0, height], 0.055, tint, 16)
    solid_cylinder(batch, pos + [0, 0, height], pos + [0, 0, height + 0.025],
                   0.034, STEEL, 12)


def specimen(batch, p=0.0):
    at = TABLE + [0, -0.09, SAMPLE_SIZE[2] / 2]
    batch.box(at, SAMPLE_SIZE, WOOD)
    width = SAMPLE_SIZE[0] * max(0.001, min(1, p))
    batch.box(at + [(width - SAMPLE_SIZE[0]) / 2, 0, SAMPLE_SIZE[2] / 2 + 0.001],
              (width, SAMPLE_SIZE[1], 0.002), OILED)
    return at


def p_dome(app, opaque, transparent, p):
    cw.paint(app)
    label(app, cw.landmarks().apex + [0, 0, 0.55], "FINISH THE WOOD; DETAIL THE BUILDING", AMBER)


def p_rags(app, opaque, transparent, p):
    bench(app)
    base = TABLE + [0.25, 0.07, 0]
    solid_cylinder(opaque, base, base + [0, 0, 0.23], 0.13, STEEL, 24)
    opaque.disc(base + [0, 0, 0.237], 0.132, STEEL, 24)
    opaque.box(base + [0, 0, 0.257], (0.075, 0.035, 0.018), STEEL)
    # A red tray is a diagram of the rejected heap; no simulated fire is needed.
    heap = TABLE + [-0.25, -0.08, 0.045]
    opaque.box(heap, (0.26, 0.23, 0.07), (0.63, 0.27, 0.18, 1))
    for k in range(3):
        a = heap + [-0.07 + k * 0.07, 0, 0.05]
        opaque.arrow(a, a + [0, 0, 0.12 + p * 0.05], 0.008, (1, 0.35, 0.16, 1))
    label(app, heap + [0, -0.14, 0.12], "NO HEAP", RED)
    label(app, base + [0, 0, 0.36], "LID + WATER + DETERGENT", GREEN)


def p_oils(app, opaque, transparent, p):
    bench(app)
    for x, name, tint in ((-0.34, "RAW", (0.70, 0.46, 0.13, 1)),
                          (0, "BOILED? READ LABEL", (0.48, 0.28, 0.08, 1)),
                          (0.34, "POLYMERIZED", (0.91, 0.65, 0.21, 1))):
        pos = TABLE + [x, 0.07, 0]
        bottle(opaque, pos, tint)
        label(app, pos + [0, 0, 0.37], name, AMBER)


def p_prepare(app, opaque, transparent, p):
    bench(app)
    at = specimen(opaque)
    # Masked bond land remains visibly bare beside the finish sample.
    opaque.box(at + [0.23, 0, 0.025], (0.10, 0.255, 0.003), (0.36, 0.70, 0.91, 1))
    label(app, at + [0, 0, 0.25], "SOUND, DRY, CLEAN WOOD", AMBER)
    label(app, at + [0.20, -0.16, 0.10], "MASK BOND LANDS", GREEN)


def p_apply(app, opaque, transparent, p):
    bench(app)
    at = specimen(opaque, p)
    rag = at + [-SAMPLE_SIZE[0] / 2 + SAMPLE_SIZE[0] * p, 0, 0.04]
    opaque.box(rag, (0.09, 0.12, 0.018), (0.94, 0.92, 0.83, 1))
    bottle(opaque, TABLE + [-0.39, 0.26, 0], (0.77, 0.47, 0.13, 1))
    label(app, TABLE + [0, 0.12, 0.42], "THIN COAT / WIPE COMPLETELY DRY", AMBER)


def p_seam(app, opaque, transparent, p):
    cw.paint(app, subject=False)
    frame = sc.paint_bench(app, "a", bundle=True, bolted=True)
    sc.key_shell(transparent, frame, sc.tight(), 0)
    label(app, frame.at(0, 2.2, 0.14), "KEEP SEALS + CHANNEL CLEAN", AMBER)
    label(app, frame.at(0, -7.5, 0.0), "CHECK FINISH / GASKET COMPATIBILITY", WHITE)


def p_rain(app, opaque, transparent, p):
    cw.paint(app)
    m = cw.landmarks()
    # Stylized rain outside the actual solver frame. It is a concept illustration,
    # not a tested shell assembly or a simulated leakage rate.
    for a, b in sc.world_seams(3.0):
        transparent.cylinder(a, b, 0.025, (0.3, 0.75, 1, 0.45), 6)
    for k in range(7):
        start = m.dome_centre + [(k - 3) * m.dome_r / 3.5, -m.dome_r * 0.9,
                                  m.dome_r * (1.1 + ((k / 7 - p) % 1) * 0.35)]
        opaque.arrow(start, start + [0, 0, -0.35], 0.018, (0.3, 0.75, 1, 1))
    label(app, m.apex + [0, 0, 0.7], "OIL IS NOT THE WEATHER BARRIER", RED)


def p_quantity(app, opaque, transparent, p):
    bench(app)
    for x, height, name, colour in ((-0.23, 0.35 * F["base_gal"] / F["allowance_gal"], "NET OIL", (0.4, 0.7, 0.9, 1)),
                                   (0.23, 0.35, "WITH ALLOWANCE", (0.95, 0.65, 0.2, 1))):
        opaque.box(TABLE + [x, 0, height / 2], (0.23, 0.22, height), colour)
        label(app, TABLE + [x, 0, height + 0.13], name, AMBER)


def p_tools(app, opaque, transparent, p):
    bench(app)
    a, b = TABLE + [-0.38, -0.08, 0.045], TABLE + [0.26, 0.04, 0.045]
    solid_cylinder(opaque, a, b, 0.026, OILED, 12)
    opaque.box(b, (0.16, 0.10, 0.085), STEEL)
    label(app, TABLE + [0, 0.12, 0.38], "INSPECT HANDLE; KEEP MOVING PARTS CLEAN", AMBER)


def p_glazing(app, opaque, transparent, p):
    bench(app)
    centre = TABLE + [0, 0.06, 0.25]
    for x in (-0.30, 0.30):
        opaque.box(centre + [x, 0, 0], (0.055, 0.065, 0.46), WOOD)
    for z in (-0.22, 0.22):
        opaque.box(centre + [0, 0, z], (0.65, 0.065, 0.055), WOOD)
    transparent.box(centre, (0.55, 0.010, 0.40), (0.5, 0.8, 0.95, 0.27))
    for x in (-0.267, 0.267):
        opaque.box(centre + [x, -0.035, 0], (0.018, 0.018, 0.40), (0.92, 0.88, 0.76, 1))
    for z in (-0.195, 0.195):
        opaque.box(centre + [0, -0.035, z], (0.54, 0.018, 0.018), (0.92, 0.88, 0.76, 1))
    for x in (-0.265, 0.265):
        opaque.triangle(centre + [x, -0.047, -0.035], centre + [x, -0.047, 0.035],
                        centre + [x * 0.88, -0.047, 0], STEEL)
    label(app, centre + [0, 0, 0.37], "SASH DEMO: GLASS NEEDS RETAINERS", AMBER)


def p_finish(app, opaque, transparent, p):
    bench(app)
    specimen(opaque, 1)
    bottle(opaque, TABLE + [0.38, 0.20, 0], (0.76, 0.52, 0.18, 1), 0.10)
    label(app, TABLE + [0, 0.08, 0.39], "TRIM / SHELVES / SERVICEABLE WOOD", GREEN)


def ch(number, slug, title, promise, narration, equations):
    return Chapter(slug, f"{number:02}", title, promise, (narration,), tuple(equations),
                   max(8, len(narration.split()) / 2.5 + 1.5), (0, 0, 0), slug)


CHAPTERS = (
    ch(1, "purpose", "Linseed oil for a dome", "Where it earns a place in the build.",
       f"The Lost Handyman video offers {F['topic_count']} linseed oil tricks. Here we bring the useful ones into the wedge dome workshop. "
       "Start with the exposed interior wood, shelves, trim and hand tools. Then look at the seams, windows and weather skin, "
       "where a finish must work with the rest of the assembly. The source is a set of claims, not a comparison test. "
       "We will show the work, the quantities and the limits before calling anything a saving.",
       ("SOURCE: The Lost Handyman / transcript record", "Applications adapted to the solver's wedge dome", "No measured service-life or cost comparison")),
    ch(2, "rags", "Set up the rag station first", "Oxidation makes heat.",
       "Before opening the oil, prepare for the used cloths. Linseed oil reacts with oxygen as it cures and gives off heat. "
       "A pile of oily cloths can trap that heat and ignite without a spark. Keep them out of pockets, sawdust and ordinary bins. "
       "Follow the label and local fire-service guidance: fully cover used rags with water and an oil-breaking detergent in a tight-lidded metal container, "
       "stored away from the building and combustibles. Arrange proper disposal. A wet rag can become hazardous again if it dries in a heap.",
       ("Oxygen + drying oil -> curing + heat", "Never accumulate oily rags in a heap", "Water + detergent + tight metal lid; local disposal")),
    ch(3, "oils", "Read the exact can", "Raw, boiled and polymerized are not interchangeable.",
       "Raw linseed oil generally cures slowly. Many hardware-store boiled oils contain drying additives; some products use heat-polymerized oil instead. "
       "Read the ingredient information, safety sheet and intended uses. Do not boil oil yourself. The source's raw-only rule for food contact is too broad: "
       "some polymerized finishes are specifically sold for kitchen wood. Choose the exact product for that use and follow its cure instructions. "
       "A name like natural, boiled or Danish does not identify a complete formulation.",
       ("Product label + safety sheet + intended use", "Kitchen contact: verify the exact formulation", "No universal drying time")),
    ch(4, "prepare", "Prepare the member", "Finish sound wood; preserve clean joint surfaces.",
       "Inspect the wedges before finishing. Reject decay and address splits or loose joints through the actual repair design. Oil cannot restore lost load capacity. "
       "Let the timber reach the moisture condition required by the finish and the building design; check with an appropriate wood meter. "
       "Remove dirt and unsuitable old coatings, smooth splinters and clear the dust. Test an offcut for color and cure. "
       "Mark and mask the places that must bond to adhesive, tape, sealant or gaskets. Finish accessible approved faces while the members are easy to reach.",
       ("Inspect -> dry -> prepare -> test offcut", "Moisture target: selected finish and assembly", "Keep glue, tape and sealant lands uncontaminated")),
    ch(5, "label_inputs", "Two product labels, two schedules", "Manufacturer claims, not DomeSim measurements.",
       f"Here are declared examples from Tried and True. Its Danish Oil lists at least {C['danish_wait']} minutes before rubbing dry "
       f"and at least {C['danish_cure']} hours of curing. Its Original oil-and-wax finish lists at least {C['wax_wait']} minutes "
       f"before rubbing dry and at least {C['wax_cure']} hours of curing. These are different products for interior work. "
       "They demonstrate why the original video's generic timing cannot be applied to every can. Minimum intervals do not guarantee full readiness in cold, damp conditions.",
       (f"CLAIMED / Tried & True Danish: {C['danish_wait']} min; {C['danish_cure']} h minimum",
        f"CLAIMED / Original: {C['wax_wait']} min; {C['wax_cure']} h minimum",
        "Manufacturer application pages / accessed September 2026", "Use the current label for the product actually bought")),
    ch(6, "apply", "Apply thinly, then wipe dry", "The sample should not carry puddles.",
       "On the prepared sample, rub on a very thin coat using the applicator the manufacturer specifies. Work in a manageable area and wet it evenly. "
       "After that product's penetration interval, rub away the excess until the surface is dry to the touch. "
       "Provide the specified ventilation and cure conditions, then assess the surface before another coat. "
       "Do not bury a sticky layer under more oil. Check end grain for extra uptake but prevent drips into joints. "
       "Do not enclose uncured finishes inside panels or occupied air passages. Handle every cloth through the rag station.",
       ("Thin application -> label interval -> wipe dry", "Cure with suitable temperature and ventilation", "End grain: inspect uptake; remove excess")),
    ch(7, "seam", "Keep the seam doing its jobs", "Finish decisions follow the assembly.",
       "This is the actual wedge seam specimen and its service channel. Oil on an exposed interior face is different from oil on a sealing land. "
       "Adhesives and tapes need compatible, prepared substrates. Keep the printed key, gasket lands, drainage route and electrical services clean. "
       "Before coating wood beside a gasket or sealant, check both manufacturers' compatibility instructions and test the complete joint. "
       "Do not treat an oil coat as the air seal, rain seal or a remedy for condensation. Inspect the finished seam before closing the panel.",
       ("Approved exposed face != bonding or sealing land", "Key + gasket + drainage remain independent", "WEST SYSTEM: bonding surfaces free of oil and wax")),
    ch(8, "weather", "The outside needs a weather system", "Rain shedding is an assembly job.",
       "The source describes linseed oil as outdoor protection and waterproofing. A dome roof still needs a specified weather skin, flashed openings, drained joints and a drying path. "
       "Plain oil does not establish those functions or prove resistance to ultraviolet light, decay or insects. Damp linseed-rich finishes can also support mildew. "
       "Use an exterior system rated for the substrate and exposure when the wood is outdoors. A compatible pigmented finish may be appropriate, "
       "but adding pigment at home does not establish weathering performance. Keep timber off persistent wet surfaces and repair leaks at their source.",
       ("No roof, rot, insect or UV rating inferred", "Water control: skin + flashing + drains + drying", "Exterior product and exposure determine upkeep")),
    ch(9, "planning_inputs", "Declare the planning assumptions", "These are estimates to replace with an offcut trial.",
       f"For a worked allowance, assume {C['faces']} flat sawn faces per member and {C['coats']} coats. "
       f"Use an estimated coverage of {C['coverage']} square feet per US gallon per coat, plus {C['handling']} percent extra volume for handling. "
       f"For active application work, assume {C['minutes']} minutes per member per coat. "
       "These are illustrative inputs, not measurements. The face allowance is an area calculation, not an instruction to oil every joint. "
       "Measure the actual selected surfaces and the consumption on representative offcuts before purchasing.",
       (f"ASSUMED: {C['faces']} flat faces; {C['coats']} coats",
        f"ESTIMATE: {C['coverage']} sq ft / US gal / coat",
        f"ASSUMED: +{C['handling']}% volume for handling",
        f"ESTIMATE: {C['minutes']} min / member / coat; active work only")),
    ch(10, "area", "Measure wood, not floor area", "Use the dome model's actual stock schedule.",
       f"The reference solver gives {F['members']} members and {F['stock_ft']:.1f} feet of total member stock. "
       f"Each flat radial face is {F['depth_in']:.1f} inches deep. Multiply total stock length by that depth in feet "
       f"and the declared face count: the planning envelope is {F['area_sqft']:.0f} square feet. "
       "This includes the stock allowance already in the model. It excludes curved backs, end cuts, panels, floors and trim. "
       "Subtract masked or hidden surfaces and add only the other surfaces you actually intend to finish.",
       (f"Solver: {F['members']} members; {F['stock_ft']:.1f} ft stock",
        f"Area = {F['stock_ft']:.1f} x ({F['depth_in']:.1f} / 12) x {C['faces']}",
        f"Flat-face planning envelope = {F['area_sqft']:.0f} sq ft",
        "Not shell area; subtract uncoated lands")),
    ch(11, "quantity", "The oil allowance", "A calculation is only as good as the coverage input.",
       f"At our estimated coverage, the declared coats consume {F['base_gal']:.2f} US gallons for that planning envelope. "
       f"The handling allowance brings it to {F['allowance_gal']:.2f} gallons. "
       "This is a scenario, not a shopping prescription or a cost saving. Roughness, end grain, masking and the actual finish change consumption. "
       "Measure how much you dispense for a known sample area through the complete coat schedule. Scale that result to the approved finish surfaces. "
       "Account for cloth uptake and leftover material as part of the job.",
       (f"{F['area_sqft']:.0f} x {C['coats']} / {C['coverage']} = {F['base_gal']:.2f} US gal",
        f"{F['base_gal']:.2f} x (1 + {C['handling']} / 100) = {F['allowance_gal']:.2f} US gal",
        "Illustrative allowance; replace with sample results")),
    ch(12, "limits", "The number that argues against it", "Low material cost does not remove labour.",
       f"The Danish Oil label advertises coverage up to {C['label_coverage']} square feet per gallon. That is a manufacturer claim, "
       "not a rough-sawn wedge measurement. Even without a price comparison, hand application has a real time cost. "
       f"Our estimated {C['minutes']} minutes per member per coat, multiplied by {F['members']} members and {C['coats']} coats, "
       f"is {F['labour_hours']:.1f} hours of active work. That excludes preparation, access equipment, inspection and waiting for cure. "
       "A cheap can can still make an expensive finishing job.",
       (f"CLAIMED: label coverage UP TO {C['label_coverage']} sq ft / US gal",
        f"Active labour = {F['members']} x {C['coats']} x {C['minutes']} / 60",
        f"= {F['labour_hours']:.1f} hours (estimate), plus prep and cure",
        "No measured lifespan or savings advantage")),
    ch(13, "tools", "Look after the builder's tools", "Sound handles first; moving parts need their own lubricant.",
       "The handle trick transfers well to the dome workshop when the handle is sound. Inspect the hammer, mallet and jig handles for cracks, "
       "splinters and loose fittings before finishing. Prepare bare wood, apply the selected finish thinly, wipe it dry and let it cure before gripping it. "
       "Oil does not repair a broken handle or tighten a structural joint reliably. A compatible drying-oil film can be considered on clean nonmoving steel for storage. "
       "Keep it out of bearings, hinges, chainsaw chains, brakes, electrical contacts and fastener threads. Those need their specified products.",
       ("Sound wood -> thin finish -> full usability check", "Storage film is not moving-part lubrication", "Structural fasteners retain specified protection")),
    ch(14, "glazing", "Putty belongs to a specified window", "A sash demonstration is not a dome skylight design.",
       "Linseed-based putty has a real place in traditional sash glazing. Use a formulated glazing compound and follow its sash preparation, bedding, retention and painting instructions. "
       "This demonstration includes mechanical retainers: putty alone must not carry the glass. "
       "The DAP glazing sheet excludes plastic panes and insulating glass units with organic seals, and requires retainers to hold the glass. "
       "For sloped or overhead dome glazing, use a complete system explicitly specified for that location; a sash putty example does not establish suitability. "
       "Do not transfer the video's homemade chalk-and-oil recipe to the dome's weather seams.",
       ("Traditional sash: compatible bedding + retainers", "Glazing putty is not a structural adhesive", "Check IGU / plastic / overhead restrictions")),
    ch(15, "interior", "Finish the parts people touch", "Match the finish to use and future repairs.",
       "Interior shelves, trim and sound furniture are the most straightforward uses. Test for ambering and for compatibility with any old coating. "
       "A labelled linseed-and-wax blend can give a low-sheen surface, but wax complicates later bonding or recoating. Use a floor-rated system for floors; "
       "assess wear, cure and slip instead of assuming a furniture oil fits. Kitchen surfaces need a product explicitly suitable for that contact. "
       "Use a prepared blend instead of heating an unknown oil formulation. Follow product directions for thinning; the source supplies no universal safe mix.",
       ("Shelves and trim: sample first", "Floor and food use: exact product suitability", "Wax affects later coats; no heated DIY mixture")),
    ch(16, "maintenance", "Inspect, clean, then renew", "Improved color is not restored strength.",
       "Make a finish record: product, batch, preparation, application date and where it was used. Keep a sample with the building notes. "
       "Inspect exposed surfaces for wear, tack, mildew and water marks; renew only after finding the cause and following the finish instructions. "
       "Gray wood can darken beautifully under oil, but that does not reverse decay. Loose toolbox joints still need repair. "
       "The transcript's leather, gunstock and masonry tricks add no validated building function here. In particular, give no foundation waterproofing or freeze-thaw credit to an oil wipe.",
       ("Record -> inspect -> repair cause -> compatible renewal", "Color change != structural repair", "No annual promise for every exposure")),
    ch(17, "close", "A useful finish in the right places", "Plan the surfaces, joints, work and cleanup together.",
       "Use linseed oil where a maintainable wood finish suits the job: accessible interior faces, selected trim and sound tool handles. "
       "Keep sealing and bonding lands compatible, give the roof its own weather system, and choose glazing for the actual opening. "
       "Base quantities on measured surfaces and a representative sample. Allow for hand labour and cure time. "
       "Finish the day by accounting for every oily cloth and arranging its disposal. The worthwhile old skill is careful application, "
       "backed by a clear understanding of what the finish can and cannot do for the dome.",
       ("Test the finish and the complete joint", "Count material, labour and curing", "Every oily cloth accounted for")),
)

SCENES = dict(zip((ch.slug for ch in CHAPTERS),
                 (p_dome, p_rags, p_oils, p_prepare, p_oils, p_apply, p_seam,
                  p_rain, p_prepare, p_seam, p_quantity, p_quantity, p_tools,
                  p_glazing, p_finish, p_finish, p_dome)))


def _moves():
    m = cw.landmarks()
    target = TABLE + [0, 0, 0.20]
    workshop = shots.push_in(target, target + [0.85, -1.8, 1.03],
                             target + [0.62, -1.62, 0.90], 43, 41)
    sash = shots.push_in(TABLE + [0, 0.06, 0.25], TABLE + [0.18, -1.8, 0.73],
                         TABLE + [0.12, -1.6, 0.65], 43, 41)
    near = sc.Frame(sc.BENCH_A, sc.tight()).near
    seam = shots.push_in(near + [0, 0.13, 0], near + [0.35, -1.25, 0.40],
                         near + [0.25, -1.08, 0.33], 43, 40)
    dome = shots.orbit(m.dome_centre + [0, 0, m.dome_r * 0.48],
                       m.dome_r * 3.5, m.dome_r * 0.85, -97, 12, 47)
    table = {ch.slug: workshop for ch in CHAPTERS}
    table.update(purpose=dome, weather=dome, close=dome, seam=seam, area=seam, glazing=sash)
    return {name: cabin_stage.clear_view(move) for name, move in table.items()}


MOVES = _moves()
camera = shots.by_chapter(MOVES)


def validate_cabin_linseed_oil():
    oil.validate_linseed_oil()
    cw.validate_cabin_world()
    cylinder = TriangleBatch()
    solid_cylinder(cylinder, (0, 0, 0), (0, 0, 1), 0.5, STEEL)
    tris = np.asarray(cylinder.vertices).reshape(-1, 3, 10)
    normals = np.cross(tris[:, 1, :3] - tris[:, 0, :3], tris[:, 2, :3] - tris[:, 0, :3])
    assert np.all(np.sum(normals * tris[:, :, 3:6].mean(axis=1), axis=1) > 0)
    # Closed-cylinder signed volume catches a missing cap sector.
    volume = np.einsum('ij,ij->i', tris[:, 0, :3],
                       np.cross(tris[:, 1, :3], tris[:, 2, :3])).sum() / 6
    assert math.isclose(volume, 16 * 0.5**2 * math.sin(math.tau / 16) / 2)
    assert set(SCENES) == set(MOVES) == {ch.slug for ch in CHAPTERS}
    assert [ch.slug for ch in CHAPTERS].index("planning_inputs") < [ch.slug for ch in CHAPTERS].index("quantity")
    assert [ch.slug for ch in CHAPTERS].index("label_inputs") < [ch.slug for ch in CHAPTERS].index("apply")
    assert f"{F['labour_hours']:.1f} hours" in next(ch for ch in CHAPTERS if ch.slug == "limits").narration[0]
    for ch in CHAPTERS:
        for p in (0, 0.25, 0.5, 0.75, 1):
            eye, target, fov = MOVES[ch.slug](p)
            assert np.all(np.isfinite(eye)) and np.all(np.isfinite(target))
            assert 20 < fov < 70 and eye[2] > 0
            assert np.linalg.norm(eye - target) > 0.3
            assert not cabin_stage.blocked(eye, target), ch.slug
    # Exercise every painter without allocating a GPU or competing with a render.
    class App:
        def __init__(self):
            self.world_labels = []
        def static_layer(self, key, builder, subject_points=None):
            batch = builder()
            assert np.all(np.isfinite(batch.vertices)), key
    for painter in set(SCENES.values()):
        app, opaque, transparent = App(), TriangleBatch(), TriangleBatch()
        painter(app, opaque, transparent, 0.7)
        assert np.all(np.isfinite(opaque.vertices)) and np.all(np.isfinite(transparent.vertices))
        assert app.world_labels
        for item in app.world_labels:
            assert np.all(np.isfinite(item.point))
            assert all(isinstance(x, int) and 0 <= x <= 255 for x in item.color)
    CABIN_LINSEED_OIL_LESSON.validate()


CABIN_LINSEED_OIL_LESSON = Lesson(
    key="cabin_linseed_oil", brand="DOMESIM", title="Linseed Oil for a Dome: Uses, Limits and Method",
    chapters=CHAPTERS, scenes=SCENES, selftest=validate_cabin_linseed_oil, report=oil.report,
    snapshot_prefix="cabin_linseed_oil", camera_fn=camera, ground="off",
    backdrop=cw.backdrop, light=cw.LIGHT, label_layout="declutter",
    audio_bed="beds/cabin-explained", audio_bed_gain=0.12,
)
