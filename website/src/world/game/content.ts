// What the Portal world holds: skills, items, lore, monsters, teachers and quests. Every number a
// teacher says, a lore page states or a quest asks is read from the project's exports -- the
// solver's dome (dome-mesh.json), the dome classes (dome-classes.json), the Dome Creator's
// geometry (creator.json) and the book's facts (facts.json) -- never typed (CLAUDE.md).

import mesh from "../../generated/dome-mesh.json";
import classes from "../../generated/dome-classes.json";
import creator from "../../generated/creator.json";
import facts from "../../generated/facts.json";

// ----------------------------------------------------------------------
// The computed figures the lessons cite
// ----------------------------------------------------------------------

const edgeCount = (t: string) => (mesh.edges as [number, number, string, boolean][]).filter((e) => e[2] === t).length;
const bookClass = classes.classes.find((c) => c.longIn === classes.bookLongIn)!;
const byFreq = (f: number) => creator.geometry.find((g) => g.frequency === f)!;

export const F = {
  nodes: mesh.vertices.length,
  struts: mesh.edges.length,
  strutsA: edgeCount("A"),
  strutsB: edgeCount("B"),
  triangles: mesh.faces.length,
  baseEdges: (mesh.edges as [number, number, string, boolean][]).filter((e) => e[3]).length,
  longIn: bookClass.longIn,
  shortIn: bookClass.shortIn,
  acrossFt: bookClass.diameterFt,
  tallFt: bookClass.heightFt,
  floorSqft: bookClass.floorSqft,
  frameLb: bookClass.frameLb,
  panelsAAA: bookClass.panels.find((p) => p.name === "AAA")!.count,
  panelsBAB: bookClass.panels.find((p) => p.name === "BAB")!.count,
  logIn: classes.logIn,
  wedgesPerLog: classes.wedgesPerLog,
  members: facts.dome.members,
  frameHours: facts.bookFacts.digital.numbers.frameHours,
  stemCell: facts.price.stemCell,
  wedgeVsMilled: facts.wood.wedgeVsMilled,
  struts1V: byFreq(1).struts.length, struts2V: byFreq(2).struts.length, struts3V: byFreq(3).struts.length, struts4V: byFreq(4).struts.length,
  panels3V: byFreq(3).panelAreas.length,
};

// ----------------------------------------------------------------------
// Skills
// ----------------------------------------------------------------------

/** The stages of building a house, in the order the work happens, and combat. Every job a house
 *  takes falls in one of them. */
export const STAGES = [
  { key: "combat", name: "Combat", blurb: "Fighting what destroys buildings." },
  { key: "plan", name: "1. Plan and design", blurb: "Before a shovel goes in: the site, the design, the rules, the money." },
  { key: "timber", name: "2. Timber", blurb: "Standing trees to frame stock: fell, buck, split, cut." },
  { key: "site", name: "3. Site and foundation", blurb: "Clear and grade the ground, pour or set the base, bring in the services." },
  { key: "structure", name: "4. Structure", blurb: "The frame, and getting it up." },
  { key: "envelope", name: "5. Envelope", blurb: "Closing it in against water, wind and cold." },
  { key: "systems", name: "6. Systems", blurb: "Water, power, heat and air." },
  { key: "finish", name: "7. Interior and finish", blurb: "Linings, floors, trim and coatings." },
  { key: "after", name: "8. Grounds and upkeep", blurb: "The land round it, and keeping it standing." },
  { key: "job", name: "9. Running the job", blurb: "The work that holds all the others together." },
] as const;
export type StageKey = (typeof STAGES)[number]["key"];

/** trainedBy: where in the game the skill earns XP today; empty while nothing trains it yet. */
export const SKILLS = [
  { key: "attack", name: "Attack", icon: "\u{1f5e1}", stage: "combat", blurb: "How often your blows land.", trainedBy: "Fighting with the Flick (accurate) style." },
  { key: "strength", name: "Strength", icon: "\u{1f4aa}", stage: "combat", blurb: "How hard your blows land.", trainedBy: "Fighting with the Lash (controlled) style." },
  { key: "defence", name: "Defence", icon: "\u{1f6e1}", stage: "combat", blurb: "How often blows miss you.", trainedBy: "Fighting with the Deflect (defensive) or Lash style." },
  { key: "hitpoints", name: "Hitpoints", icon: "♥", stage: "combat", blurb: "How much punishment you can take.", trainedBy: "Any damage you deal." },

  { key: "geometry", name: "Geometry and Design", icon: "△", stage: "plan", blurb: "Icosahedra, frequency, chord factors, strut classes, angles: the design itself.", trainedBy: "Tutor Tess's quest, and the geometry lore pages." },
  { key: "surveying", name: "Site Survey", icon: "\u{1f9ed}", stage: "plan", blurb: "Reading the land: slope, sun, water, soil, setbacks, where the house goes.", trainedBy: "" },
  { key: "permitting", name: "Permits and Codes", icon: "\u{1f4cb}", stage: "plan", blurb: "Zoning, building codes, drawings for the inspector, the paper trail.", trainedBy: "" },
  { key: "trading", name: "Estimating and Trading", icon: "⚖", stage: "plan", blurb: "Quantities, costs, buying materials, and the exchange.", trainedBy: "" },

  { key: "forestry", name: "Forestry", icon: "\u{1f332}", stage: "timber", blurb: "Choosing, felling and bucking trees safely with a chainsaw.", trainedBy: "Felling and bucking the pine on Wedge Island." },
  { key: "splitting", name: "Splitting", icon: "\u{1fa93}", stage: "timber", blurb: "Sections to wedges: halves, quarters, eighths, along the grain.", trainedBy: "Ripping log sections with the chainsaw: the hub's log pile, the island's block." },
  { key: "milling", name: "Milling", icon: "\u{1fa9a}", stage: "timber", blurb: "Cutting wedges to strut length: butt cuts, saw setups, the cut list.", trainedBy: "The saw bench on Wedge Island." },

  { key: "sitework", name: "Site Work", icon: "\u{1f69c}", stage: "site", blurb: "Clearing, excavation, grading and drainage.", trainedBy: "" },
  { key: "foundations", name: "Foundations", icon: "⬢", stage: "site", blurb: "Pads, piers, footings, decks and the base ring.", trainedBy: "The foundation lore pages." },
  { key: "utilities", name: "Utilities", icon: "\u{1f50c}", stage: "site", blurb: "Hookups: water, sewer or septic, power and data to the pad.", trainedBy: "" },

  { key: "framing", name: "Framing and Joinery", icon: "⌂", stage: "structure", blurb: "Members, pinwheel joints, the jig, the panel frames.", trainedBy: "The jig on Wedge Island, and the framing lore pages." },
  { key: "rigging", name: "Rigging and Raising", icon: "\u{1fa9d}", stage: "structure", blurb: "Lifting panels into place: ropes, winch, ladders, the order they go up.", trainedBy: "Raising panels at the Wedge Island site." },

  { key: "paneling", name: "Paneling and Sheathing", icon: "◩", stage: "envelope", blurb: "Closing the triangles: infill, sheathing, skins.", trainedBy: "Sheathing the Wedge Island dome." },
  { key: "roofing", name: "Seams and Waterproofing", icon: "\u{1f327}", stage: "envelope", blurb: "Seam keys, laps, membranes and flashing: water runs over, never in.", trainedBy: "Keying the seams on Wedge Island." },
  { key: "glazing", name: "Windows and Doors", icon: "\u{1fa9f}", stage: "envelope", blurb: "Openings: framing them, glazing, hanging and sealing.", trainedBy: "" },
  { key: "climate", name: "Insulation and Climate", icon: "☁", stage: "envelope", blurb: "Condensation, dew point, insulation, the breathing wall.", trainedBy: "Warden Wren's quest, and the climate lore pages." },

  { key: "plumbing", name: "Plumbing", icon: "\u{1f6b0}", stage: "systems", blurb: "Supply, drains, vents and fixtures.", trainedBy: "" },
  { key: "electrical", name: "Electrical", icon: "⚡", stage: "systems", blurb: "Service, circuits, wiring in the seams, solar and batteries.", trainedBy: "" },
  { key: "hvac", name: "Heating and Ventilation", icon: "\u{1f525}", stage: "systems", blurb: "Stoves, heat pumps, fresh air and exhaust.", trainedBy: "" },

  { key: "interiors", name: "Interior Linings", icon: "\u{1f9f1}", stage: "finish", blurb: "Drywall, boards and panelling over the frame.", trainedBy: "" },
  { key: "flooring", name: "Flooring", icon: "\u{1f7eb}", stage: "finish", blurb: "Subfloor to finished floor: boards, tile, the loft deck.", trainedBy: "" },
  { key: "carpentry", name: "Finish Carpentry", icon: "\u{1fa9b}", stage: "finish", blurb: "Trim, stairs, cabinets and built-ins.", trainedBy: "" },
  { key: "coatings", name: "Paint and Coatings", icon: "\u{1f58c}", stage: "finish", blurb: "Stains, oils, paint and sealers, inside and out.", trainedBy: "" },

  { key: "landscaping", name: "Landscaping", icon: "\u{1f33f}", stage: "after", blurb: "Paths, planting, drainage and the land round the house.", trainedBy: "" },
  { key: "upkeep", name: "Upkeep and Repair", icon: "\u{1f527}", stage: "after", blurb: "Inspecting, repairing and keeping rot, pests and the wet out.", trainedBy: "The rot lore page." },

  { key: "management", name: "Project Management", icon: "\u{1f4c5}", stage: "job", blurb: "Scheduling, crews, deliveries, inspections, the budget.", trainedBy: "" },
  { key: "safety", name: "Site Safety", icon: "\u{1f9ba}", stage: "job", blurb: "Chainsaws, heights, lifting, PPE and first aid.", trainedBy: "" },
  { key: "teaching", name: "Teaching", icon: "✎", stage: "job", blurb: "Hosting lessons for others.", trainedBy: "" },
] as const satisfies readonly { key: string; name: string; icon: string; stage: StageKey; blurb: string; trainedBy: string }[];
export type SkillKey = (typeof SKILLS)[number]["key"];

/** RuneScape's combat level, from the combat skills. */
export function combatLevel(lv: (k: SkillKey) => number) {
  const base = 0.25 * (lv("defence") + lv("hitpoints"));
  return Math.floor(base + 0.325 * (lv("attack") + lv("strength")));
}

/** RuneScape's experience table: the XP a level needs. */
export function xpForLevel(level: number) {
  let points = 0;
  for (let l = 1; l < level; l++) points += Math.floor(l + 300 * Math.pow(2, l / 7));
  return Math.floor(points / 4);
}
const XP_TABLE = Array.from({ length: 100 }, (_, i) => xpForLevel(i + 1));
export function levelForXp(xp: number) {
  let l = 1;
  while (l < 99 && xp >= XP_TABLE[l]) l++;
  return l;
}
export const nextLevelXp = (level: number) => XP_TABLE[Math.min(98, level)];

// ----------------------------------------------------------------------
// Lore: the lessons, collected as pages and read for XP
// ----------------------------------------------------------------------

export interface Lore { id: string; title: string; skill: SkillKey; xp: number; text: string[] }

export const LORE: Lore[] = [
  { id: "icosahedron", title: "The twenty faces", skill: "geometry", xp: 120, text: [
    "Every geodesic dome starts as an icosahedron: twenty equal triangles, the closest any regular solid of flat faces comes to a sphere.",
    "Split each face into smaller triangles and push their corners out onto the sphere, and you have a geodesic dome. How many times you split an edge is the dome's frequency.",
  ] },
  { id: "frequency", title: "What frequency means", skill: "geometry", xp: 160, text: [
    `More splits, more pieces, rounder dome. In the Dome Creator: a 1V dome has ${F.struts1V} struts, 2V ${F.struts2V}, 3V ${F.struts3V} and 4V ${F.struts4V}.`,
    "Rounder is not always better: more pieces means more cuts, more joints, more seams to keep dry. The book's dome is 2V.",
  ] },
  { id: "two-lengths", title: "Only two lengths", skill: "geometry", xp: 200, text: [
    `A 2V hemisphere is built from just two strut lengths. The book's dome has ${F.strutsA} long struts (A, ${F.longIn} in) and ${F.strutsB} short ones (B, ${F.shortIn} in): ${F.struts} in all, meeting at ${F.nodes} nodes.`,
    `They close ${F.triangles} triangles: ${F.panelsAAA} with three long sides (AAA) and ${F.panelsBAB} with two short and one long (BAB).`,
  ] },
  { id: "one-number", title: "One number names the dome", skill: "geometry", xp: 220, text: [
    `Give the longest strut and everything follows. At ${F.longIn} in the dome is ${F.acrossFt} ft across and ${F.tallFt} ft tall, with ${F.floorSqft} sq ft of floor and a frame of about ${F.frameLb.toLocaleString()} lb of green pine.`,
    "Domes with the same longest strut take the same panels. That is why members of one dome class can trade them.",
  ] },
  { id: "wedge", title: "From log to wedge", skill: "splitting", xp: 180, text: [
    `The book's frame is split, not sawn into boards: a ${F.logIn}-inch log halved, quartered, then halved again gives ${F.wedgesPerLog} wedges, each a 45-degree slice of the round.`,
    `Split along the grain, a wedge keeps the tree's own strength. Per the book's model, wedge stock yields ${F.wedgeVsMilled} times the board feet of milled lumber from the same tree.`,
  ] },
  { id: "pinwheel", title: "The pinwheel joint", skill: "framing", xp: 180, text: [
    `The wedge dome has no hubs. Members lean on each other in pinwheels round every node, so the frame is ${F.members} members rather than ${F.struts} shared struts: each of the ${F.struts - F.baseEdges} interior edges carries two members side by side, and each of the ${F.baseEdges} base edges one.`,
    `The book's frame goes up in ${F.frameHours} hours of frame work.`,
  ] },
  { id: "water", title: "Water is the silent killer", skill: "climate", xp: 200, text: [
    "A dome has no eaves and every panel faces a different way, so water finds every seam. Most dome failures are not structural: they are wet.",
    "Lap every seam so water runs over it, never into it; treat the seam as a gutter, and give it somewhere to drain.",
  ] },
  { id: "dew", title: "Dew point", skill: "climate", xp: 220, text: [
    "Warm indoor air carries water. Where it meets a surface colder than its dew point, the water comes out -- inside your wall.",
    "Keep the warm side vapour-tight, the cold side able to breathe, and the cavity ventilated. A damp cavity is a Damp Wraith's home.",
  ] },
  { id: "rot", title: "Rot", skill: "upkeep", xp: 160, text: [
    "Rot fungi need wood that stays wet. End grain drinks water like straws; keep it off the ground and sealed, and let every timber dry out between wettings.",
  ] },
  { id: "termites", title: "Termites", skill: "foundations", xp: 160, text: [
    "Subterranean termites travel up from the soil. Keep timber off the ground on piers, leave a gap they must cross in the open, and inspect the piers.",
  ] },
  { id: "wind", title: "Wind on a dome", skill: "framing", xp: 220, text: [
    "Triangles cannot rack, and a sphere has no flat face for wind to push on: load spreads through the whole shell. The weak points are the anchors and the base ring.",
  ] },
  { id: "frost", title: "Frost heave", skill: "foundations", xp: 240, text: [
    "Water in the soil freezes, swells and lifts whatever sits on it. Footings go below the frost line, or the soil under them is kept dry and drained.",
  ] },
];
export const loreById = (id: string) => LORE.find((l) => l.id === id);

// ----------------------------------------------------------------------
// Items
// ----------------------------------------------------------------------

/** A weapon: RuneScape's bonuses, its speed in ticks, and its special attack if it has one. */
export interface Weapon { look: "whip" | "mallet" | "maul"; attack: number; strength: number; speed: number; styles: [string, string, string]; spec?: { name: string; cost: number; accuracy: number; blurb: string } }
export interface Item { id: string; name: string; icon: string; examine: string; stack?: boolean; heals?: number; weapon?: Weapon; lore?: string; value: number }

/** The fraction of a section one wedge is: the seed model's radial splits. */
const PER_SECTION = `1/${F.wedgesPerLog}`;

export const ITEMS: Item[] = [
  { id: "coins", name: "Dome credits", icon: "\u{1fa99}", examine: "The world's currency. Spent at the exchange, one day.", stack: true, value: 1 },
  { id: "wedge", name: `Wedge (${PER_SECTION})`, icon: "\u{1fab5}", examine: `One ${PER_SECTION} of a log section, ripped radially through the pith with the chainsaw.`, stack: true, value: 6 },
  { id: "bark", name: "Bark strip", icon: "\u{1f342}", examine: "Peeled off a wedge. The frame is better without it.", value: 1 },
  { id: "screws", name: "Structural screws", icon: "\u{1f529}", examine: "They hold a pinwheel joint together.", stack: true, value: 1 },
  { id: "hose", name: "Seam hose", icon: "〰", examine: "Compressible tube that seals the seam between two panels.", stack: true, value: 2 },
  { id: "sealant", name: "Tube of sealant", icon: "\u{1f9f4}", examine: "For a seam that has started to leak.", value: 8 },
  { id: "panel", name: "Triangle panel", icon: "▲", examine: "A closed bay, ready to fit.", value: 20 },
  { id: "mix", name: "Trail mix", icon: "\u{1f95c}", examine: "Builder's lunch. Heals 6.", heals: 6, value: 3 },
  { id: "coffee", name: "Thermos of coffee", icon: "☕", examine: "Heals 10, and the afternoon.", heals: 10, value: 6 },
  { id: "whip", name: "Abyssal whip", icon: "➰", examine: "A weapon from the abyss. +82 slash attack, +82 strength, four ticks a swing. Special: Energy Drain.", value: 120000,
    weapon: { look: "whip", attack: 82, strength: 82, speed: 4, styles: ["Flick", "Lash", "Deflect"],
      spec: { name: "Energy Drain", cost: 50, accuracy: 1.25, blurb: "25% more accurate; drains the target and gives you 10% run energy." } } },
  { id: "mallet", name: "Mallet", icon: "\u{1f528}", examine: "Better than bare hands against a grub. +8 crush, +10 strength.", value: 15,
    weapon: { look: "mallet", attack: 8, strength: 10, speed: 5, styles: ["Pound", "Pummel", "Block"] } },
  { id: "maul", name: "Splitting maul", icon: "\u{1fa93}", examine: "For logs, mostly. +20 crush, +25 strength, slow.", value: 60,
    weapon: { look: "maul", attack: 20, strength: 25, speed: 6, styles: ["Pound", "Pummel", "Block"] } },
  // Wedge Island's tools and what they make (src/world/game/island.ts)
  { id: "chainsaw", name: "Chainsaw", icon: "\u{1fa9a}", examine: "Fells a pine and bucks it into sections. Never alone.", value: 80 },
  { id: "section", name: "Log section", icon: "\u{1fab5}", examine: `A pine bucked to the long strut's length, ${F.longIn} in, about ${F.logIn} in across.`, value: 12 },
  { id: "strutA", name: "A strut", icon: "\u{1f4cf}", examine: `A wedge cut for one of the ${F.strutsA} long edges (${F.longIn} in nominal).`, value: 10 },
  { id: "strutB", name: "B strut", icon: "\u{1f4d0}", examine: `A wedge cut for one of the ${F.strutsB} short edges (${F.shortIn} in nominal).`, value: 9 },
  { id: "meter", name: "Moisture meter", icon: "\u{1f4df}", examine: "Finds the damp before it finds you.", value: 40 },
  ...LORE.map((l) => ({ id: `lore:${l.id}`, name: `Lore: ${l.title}`, icon: "\u{1f4dc}", examine: "A page of dome know-how. Read it.", lore: l.id, value: 0 })),
];
export const itemById = (id: string) => ITEMS.find((i) => i.id === id);

// ----------------------------------------------------------------------
// Monsters: the things that destroy buildings
// ----------------------------------------------------------------------

export interface Drop { item: string; qty: [number, number]; chance: number }   // chance per kill, 0..1
export interface Monster {
  id: string; name: string; level: number; hp: number; maxHit: number; speed: number; // ticks between attacks
  colour: string; size: number; shape: "grub" | "swarm" | "wraith" | "sprite" | "gust" | "golem";
  examine: string; lore: string; xp: number; drops: Drop[];
}

export const MONSTERS: Monster[] = [
  { id: "grub", name: "Rot Grub", level: 2, hp: 5, maxHit: 1, speed: 5, colour: "#c9b27a", size: 1, shape: "grub", xp: 5, lore: "rot",
    examine: "It eats wood that stays wet. Keep timber dry and it starves.",
    drops: [{ item: "coins", qty: [2, 8], chance: 1 }, { item: "bark", qty: [1, 1], chance: 0.4 }, { item: "mix", qty: [1, 1], chance: 0.15 }, { item: "lore:rot", qty: [1, 1], chance: 0.12 }, { item: "mallet", qty: [1, 1], chance: 0.04 }] },
  { id: "termite", name: "Termite Swarm", level: 5, hp: 10, maxHit: 2, speed: 4, colour: "#d9a46a", size: 1.3, shape: "swarm", xp: 10, lore: "termites",
    examine: "They climb up from the soil. Timber on piers, with a gap to cross in the open, stops them.",
    drops: [{ item: "coins", qty: [5, 15], chance: 1 }, { item: "screws", qty: [4, 12], chance: 0.4 }, { item: "lore:termites", qty: [1, 1], chance: 0.12 }, { item: "coffee", qty: [1, 1], chance: 0.1 }] },
  { id: "leak", name: "Leak Sprite", level: 8, hp: 14, maxHit: 3, speed: 4, colour: "#7cc4f0", size: 1.1, shape: "sprite", xp: 15, lore: "water",
    examine: "Born where a seam was butted instead of lapped. Water runs into it, not over it.",
    drops: [{ item: "coins", qty: [8, 20], chance: 1 }, { item: "hose", qty: [3, 9], chance: 0.45 }, { item: "sealant", qty: [1, 1], chance: 0.25 }, { item: "lore:water", qty: [1, 1], chance: 0.12 }] },
  { id: "wraith", name: "Damp Wraith", level: 12, hp: 20, maxHit: 4, speed: 5, colour: "#9fb8c8", size: 1.6, shape: "wraith", xp: 22, lore: "dew",
    examine: "Warm, wet air that crossed its dew point inside a wall. A vapour-tight warm side and a ventilated cavity banish it.",
    drops: [{ item: "coins", qty: [12, 30], chance: 1 }, { item: "meter", qty: [1, 1], chance: 0.06 }, { item: "lore:dew", qty: [1, 1], chance: 0.15 }, { item: "coffee", qty: [1, 1], chance: 0.2 }] },
  { id: "gust", name: "Wind Shear", level: 18, hp: 28, maxHit: 5, speed: 3, colour: "#dfe8ee", size: 1.8, shape: "gust", xp: 32, lore: "wind",
    examine: "It finds the flat wall and the loose anchor. A dome has no flat wall; check the anchors.",
    drops: [{ item: "coins", qty: [20, 45], chance: 1 }, { item: "panel", qty: [1, 1], chance: 0.2 }, { item: "lore:wind", qty: [1, 1], chance: 0.15 }] },
  { id: "frost", name: "Frost Heave", level: 25, hp: 40, maxHit: 7, speed: 6, colour: "#bcd8f0", size: 2.4, shape: "golem", xp: 48, lore: "frost",
    examine: "Frozen ground, rising. Footings below the frost line, or dry drained soil, leave it nothing to lift.",
    drops: [{ item: "coins", qty: [35, 80], chance: 1 }, { item: "maul", qty: [1, 1], chance: 0.05 }, { item: "lore:frost", qty: [1, 1], chance: 0.2 }] },
];
export const monsterById = (id: string) => MONSTERS.find((m) => m.id === id)!;

/** Where monsters live: in the hub, out past the gateways; in a space, round its rim. */
export const SPAWNS: { area: string; monster: string; at: [number, number]; roam: number }[] = [
  { area: "hub", monster: "grub", at: [-34, 30], roam: 6 }, { area: "hub", monster: "grub", at: [-38, 24], roam: 6 },
  { area: "hub", monster: "grub", at: [-30, 36], roam: 6 },
  { area: "hub", monster: "termite", at: [36, 30], roam: 6 }, { area: "hub", monster: "termite", at: [40, 22], roam: 6 },
  { area: "hub", monster: "leak", at: [38, -30], roam: 7 }, { area: "hub", monster: "leak", at: [32, -38], roam: 7 },
  { area: "hub", monster: "wraith", at: [-36, -34], roam: 7 }, { area: "hub", monster: "wraith", at: [-42, -26], roam: 7 },
  { area: "hub", monster: "gust", at: [0, -52], roam: 8 },
  { area: "hub", monster: "frost", at: [0, 54], roam: 6 },
  { area: "cell-wall", monster: "wraith", at: [-22, 6], roam: 6 }, { area: "cell-wall", monster: "wraith", at: [22, 4], roam: 6 },
  { area: "panel-creator", monster: "leak", at: [-22, 0], roam: 6 }, { area: "panel-creator", monster: "leak", at: [22, 0], roam: 6 },
  { area: "foundation", monster: "termite", at: [-22, 2], roam: 6 }, { area: "foundation", monster: "frost", at: [22, 4], roam: 5 },
  { area: "zome", monster: "gust", at: [-22, 2], roam: 6 },
  { area: "wedge-method", monster: "grub", at: [-22, 4], roam: 6 }, { area: "wedge-method", monster: "grub", at: [22, 4], roam: 6 },
];

// ----------------------------------------------------------------------
// Teachers and quests
// ----------------------------------------------------------------------

export interface Line { who: "npc" | "you"; text: string }
export interface Choice { text: string; correct?: boolean; reply: string }

export interface QuestStep {
  /** What the journal says to do. */
  task: string;
}
export interface Quest { id: string; name: string; teacher: string; skill: SkillKey; xp: number; coins: number; badge: string; lore: string; steps: QuestStep[]; blurb: string }

export const QUESTS: Quest[] = [
  { id: "twenty", name: "The Twenty Faces", teacher: "tess", skill: "geometry", xp: 900, coins: 60, badge: "Twenty Faces", lore: "two-lengths",
    blurb: "Tutor Tess on the plaza will show you where every geodesic dome begins.",
    steps: [
      { task: "Talk to Tutor Tess on the plaza." },
      { task: "Examine the dome in the middle of the plaza (right-click it)." },
      { task: "Go through the Dome Creator gateway and look at a 3V dome." },
      { task: "Go back to Tutor Tess and answer her question." },
    ] },
  { id: "split", name: "Split the Log", teacher: "sam", skill: "splitting", xp: 800, coins: 50, badge: "Wedge Splitter", lore: "pinwheel",
    blurb: "Splitter Sam by the log pile turns trees into frames. He needs a hand.",
    steps: [
      { task: "Talk to Splitter Sam by the log pile." },
      { task: `Split the log pile until you have ${F.wedgesPerLog} split wedges.` },
      { task: "Bring the wedges to Splitter Sam and answer his question." },
    ] },
  { id: "water", name: "Keep the Water Out", teacher: "wren", skill: "climate", xp: 1100, coins: 90, badge: "Dry Keeper", lore: "dew",
    blurb: "Warden Wren is losing a dome to the wet. The Damp Wraiths gather to the north-west.",
    steps: [
      { task: "Talk to Warden Wren near the Cell Wall gateway." },
      { task: "Defeat 3 Damp Wraiths (north-west of the plaza) or Leak Sprites (north-east)." },
      { task: "Go back to Warden Wren and answer her question." },
    ] },
];
export const questById = (id: string) => QUESTS.find((q) => q.id === id)!;

export interface Npc { id: string; name: string; title: string; area: string; at: [number, number]; colour: string; examine: string; hair: boolean }

export const NPCS: Npc[] = [
  { id: "tess", name: "Tutor Tess", title: "Geometry", area: "hub", at: [6, 14], colour: "#7c5ac8", hair: true, examine: "She knows why there are only two lengths." },
  { id: "sam", name: "Splitter Sam", title: "Splitting", area: "hub", at: [-14, 22], colour: "#a8642a", hair: false, examine: "Arms like logs. Speaks fluent grain." },
  { id: "wren", name: "Warden Wren", title: "Climate", area: "hub", at: [16, -16], colour: "#3a8a7a", hair: true, examine: "Always looking at the seams." },
];
export const npcById = (id: string) => NPCS.find((n) => n.id === id)!;

/** Things in the world that are not people or monsters. */
export const OBJECTS: { id: string; name: string; area: string; at: [number, number]; examine: string; options: string[] }[] = [
  { id: "logpile", name: "Log pile", area: "hub", at: [-19, 25], options: ["Split", "Examine"],
    examine: `Pine sections about ${F.logIn} inches across, bucked to the long strut's length. The chainsaw rips each into ${F.wedgesPerLog} wedges: halves, quarters, eighths.` },
  // RuneScape's house portal: your house, your house in build mode, or anybody's by name
  { id: "houseportal", name: "House portal", area: "hub", at: [-30, 30], options: ["Enter", "Home", "Build mode", "Friend's house", "Examine"],
    examine: "The portal to the members' houses. Type a member's name, or 1 to 5 for the five grand houses." },
  // and inside every house, the way back out
  { id: "houseexit", name: "Portal", area: "house", at: [-20, 104], options: ["Enter", "Examine"],
    examine: "The way back to the hilltop." },
];

/** What a house can be built as: the starter dome, or one of the five grand houses (src/world/estates.ts). */
export const HOUSE_STYLES: { key: string; name: string; blurb: string }[] = [
  { key: "starter", name: "The starter dome", blurb: "One 2V dome on its deck, a path and a garden: where every member begins." },
  { key: "1", name: "West Egg", blurb: "A great gold-crowned dome over a marble terrace, its wings, its fountain and its lanterns: the party house." },
  { key: "2", name: "East Egg", blurb: "White domes in a crescent behind a colonnade, a lawn down to the water, and a green light at the end of the dock." },
  { key: "3", name: "The Deco Palace", blurb: "A stepped ziggurat of terraces, a gold dome on top, sunbursts and searchlights." },
  { key: "4", name: "The Conservatory", blurb: "Glass domes over a garden: a hedge maze, a gazebo and the palm house." },
  { key: "5", name: "The Ballroom", blurb: "One vast ballroom dome lit from inside, a chandelier, a dance floor and fireworks over the lawn." },
];
export const houseStyle = (key: string | undefined) => HOUSE_STYLES.find((h) => h.key === key) ?? HOUSE_STYLES[0];

/** Each teacher's words, by quest stage. Numbers come from F. */
export const TALK: Record<string, (stage: number) => { lines: Line[]; question?: { ask: string; choices: Choice[] } }> = {
  tess: (stage) => {
    if (stage === 0) return { lines: [
      { who: "npc", text: "Every geodesic dome begins as an icosahedron: twenty equal triangles." },
      { who: "npc", text: "Split each edge and push the new corners out onto a sphere. The number of splits is the frequency." },
      { who: "npc", text: "Look closely at the dome behind me -- right-click it and Examine. Then visit the Dome Creator and see a 3V dome. Come back and tell me what you learned." },
    ] };
    if (stage === 1 || stage === 2) return { lines: [{ who: "npc", text: stage === 1 ? "Right-click the dome and Examine it first." : "Now the Dome Creator: through its gateway, set the frequency to 3V and look at it." }] };
    if (stage === 3) return { lines: [{ who: "npc", text: "So. A question." }], question: {
      ask: `The dome on the plaza is 2V. How many struts does it have?`,
      choices: [
        { text: `${F.triangles}`, reply: `That is the number of triangles, not struts.` },
        { text: `${F.struts}`, correct: true, reply: `Yes: ${F.strutsA} long and ${F.strutsB} short, only two lengths. Take this page; it is yours.` },
        { text: `${F.members}`, reply: `That is the wedge frame's members -- two side by side on every edge but the base ring. Count the edges.` },
      ] } };
    return { lines: [{ who: "npc", text: `Frequency is the whole trade-off: a 3V dome has ${F.struts3V} struts and ${F.panels3V} panels to close. Rounder, and more seams to keep dry.` }] };
  },
  sam: (stage) => {
    if (stage === 0) return { lines: [
      { who: "npc", text: "We don't buy boards here. We split logs." },
      { who: "npc", text: `Rip a section with the chainsaw, straight down through the pith: halves, quarters, then eighths. ${F.wedgesPerLog} wedges, each ${PER_SECTION} of the round, every one running with the grain.` },
      { who: "npc", text: `Go and split a section from that pile. Bring me its ${F.wedgesPerLog} wedges.` },
    ] };
    if (stage === 1) return { lines: [{ who: "npc", text: `Right-click the log pile and Split a section with your chainsaw. ${F.wedgesPerLog} wedges.` }] };
    if (stage === 2) return { lines: [{ who: "npc", text: "Good wedges. One question before you go." }], question: {
      ask: "Why split a log into wedges instead of sawing it into boards?",
      choices: [
        { text: "It is faster to saw.", reply: "Faster is the chainsaw's job either way. Think about the grain." },
        { text: "A split follows the grain, so the wood keeps the tree's strength.", correct: true, reply: `That's it. And the book's model gets ${F.wedgeVsMilled} times the board feet that way. Here, read this.` },
        { text: "Wedges are lighter.", reply: "Heavier, if anything. Think about the grain." },
      ] } };
    return { lines: [{ who: "npc", text: `The frame's ${F.members} members lean on each other in pinwheels. No hubs. Ask Tess about the two lengths.` }] };
  },
  wren: (stage) => {
    if (stage === 0) return { lines: [
      { who: "npc", text: "Most domes don't fall down. They rot, from the wet." },
      { who: "npc", text: "Warm indoor air carries water. Where it meets a surface colder than its dew point, the water comes out -- inside the wall." },
      { who: "npc", text: "The Damp Wraiths gather north-west of the plaza, the Leak Sprites north-east. Clear out three and come back." },
    ] };
    if (stage === 1) return { lines: [{ who: "npc", text: "Three of them. Damp Wraiths or Leak Sprites -- either will do." }] };
    if (stage === 2) return { lines: [{ who: "npc", text: "Better. Now, what keeps them away for good?" }], question: {
      ask: "How do you stop condensation inside a dome's wall?",
      choices: [
        { text: "Seal both sides of the wall tight.", reply: "Then whatever water gets in can never get out. One side must breathe." },
        { text: "A vapour-tight warm side, a breathable cold side, and a ventilated cavity.", correct: true, reply: "Exactly that. Take this page, and keep the seams lapped." },
        { text: "Heat the dome hotter.", reply: "Warmer air carries more water, not less." },
      ] } };
    return { lines: [{ who: "npc", text: "Lap every seam so water runs over it, never into it. And let the wall dry." }] };
  },
};

export const START_ITEMS: [string, number][] = [["chainsaw", 1], ["mix", 3], ["coins", 25]];
/** What every character starts wielding, and the levels they start at (RuneScape's pure). */
export const START_WEAPON = "whip";
export const START_LEVELS: Partial<Record<SkillKey, number>> = { attack: 60, strength: 60, hitpoints: 10 };   // store.ts adds the hitpoints the 60s earn
