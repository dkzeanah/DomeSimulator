// What the lab is for, in one place: the mission, the value it offers each kind of visitor, the
// dome as a learning model, the working method, and the projects. Home, /mission, /studio and
// /work all read this module, so the pages cannot disagree. Every figure is computed: it comes
// from facts (scripts/export_facts.py), the film list or the tools menu -- never typed here.

import episodes from "../generated/episodes.json";
import { cabin, facts } from "./facts";
import { TOOL_GROUPS } from "./toolsMenu";

const d = facts.dome;

export const MISSION = {
  line: "A home you can account for -- built from the woods, worked out in code, and taught in the open.",
  long: `Zeanah Lab designs a ${d.acrossFt}-foot geodesic dome that can be framed from split logs, and builds the software that works out every piece of it. The same code writes the book, renders the films, prices the build and runs the tools -- so anyone can check the numbers, learn the method, and build their own.`,
  vision: "Shelter that a person can understand end to end: where the wood came from, how every joint carries load, what each part costs, and how the house thinks.",
};

export const BOOK_FIGURES = {
  chapters: cabin.chapters,
  figures: cabin.figures,
  pages: cabin.pages ?? cabin.chapters,
  parts: cabin.parts.length,
};

/** Films, counted from the list the site plays. */
export const FILM_COUNT = episodes.episodes.length;
/** Series the films fall into. */
export const SERIES_COUNT = new Set(episodes.episodes.map((e) => e.series)).size;
/** Tools a visitor can open (the owner's studio tools are not counted). */
export const PUBLIC_TOOLS = TOOL_GROUPS.filter((g) => !g.staff).flatMap((g) => g.items).length;

/** The value proposition, by who is asking. */
export const AUDIENCES = [
  {
    key: "builders", mark: "01 / Builders", title: "Build it yourself",
    body: `A complete method from standing tree to raised shell: ${d.members} members, ${d.bays} panels, two jigs, and ${cabin.numbers.frameHours} hours of frame work -- with every cut worked out for your own logs.`,
    to: "/book", cta: "The book",
  },
  {
    key: "clients", mark: "02 / Clients", title: "Have it designed",
    body: "Design sessions, custom dome studies and build packs produced with the same solvers the book uses: cut cards, plan sets, costing and renders of your own dome.",
    to: "/studio", cta: "The studio",
  },
  {
    key: "learners", mark: "03 / Learners", title: "Learn how a house thinks",
    body: "The dome is a complete, small system -- geometry, structure, moisture, energy and controls -- small enough to understand whole, and a working model for computational thinking and the honest use of AI.",
    to: "/mission#framework", cta: "The framework",
  },
  {
    key: "land", mark: "04 / Landowners", title: "Host a pad",
    body: "The ground is the one thing a dome cannot take with it. Pad hosts, owners, builders and recyclers meet on one network, each pad with its own numbers.",
    to: "/network", cta: "The network",
  },
] as const;

/** The dome as a learning model: each layer of the building, the thinking skill it teaches,
 *  and what an AI is (and is not) trusted to do there. */
export const LAYERS = [
  {
    layer: "Geometry", skill: "Abstraction",
    what: `An icosahedron, subdivided once and pushed out to a sphere: ${d.vertices} hubs and two member lengths. One measured strut names the whole dome.`,
    ai: "The model may derive the formula; the solver is what is believed.",
  },
  {
    layer: "Structure", skill: "Decomposition",
    what: `${d.members} members in ${d.bays} panels, each a small problem with its own cut, jig and check -- a house broken into pieces a person can finish in a day.`,
    ai: "Generate cut lists and assembly orders, then verify every one against the model.",
  },
  {
    layer: "Envelope", skill: "Modelling and simulation",
    what: "The seam, the skin and the air in them: dew points, drying paths and where water goes, simulated before anything is sealed.",
    ai: "Use it to explore the physics; never accept a number that does not trace to code.",
  },
  {
    layer: "Systems", skill: "Algorithms and control",
    what: "The utility core and the smart-home layer as the project models them: sensors, a dew-point controller, energy budgets -- rules that run the house, written down and tested.",
    ai: "Draft the control logic; keep a human-readable rule and a test for every action it takes.",
  },
  {
    layer: "Economics", skill: "Data and evaluation",
    what: `Every material, hour and dollar priced from the same model: ${facts.price.perSqft.toLocaleString("en-US", { style: "currency", currency: "USD" })} a square foot of floor, and the figures that argue against it shown too.`,
    ai: "Let it assemble the tables; declare every assumption it used, on screen.",
  },
  {
    layer: "Media", skill: "Communication",
    what: `One source of truth feeds a ${BOOK_FIGURES.chapters}-chapter book, ${FILM_COUNT} films and this site -- so a correction in the code corrects every place it is said.`,
    ai: "Write, narrate and render with it; publish corrections on camera, not silently.",
  },
] as const;

/** The working method -- the AI usage framework the whole project runs on. */
export const METHOD = [
  ["Declare", "Every input that cannot be derived -- a price, a rate, a guess -- goes in a table with its reason, before it is used."],
  ["Compute", "Every figure is produced by code that anyone can run. Nothing on a page or in a film is typed by hand."],
  ["Generate", "AI drafts the code, the prose, the scenes and the tests -- as a collaborator working inside those rules, not around them."],
  ["Verify", "Selftests, stills and checks run before anything ships. A render is reviewed one still per chapter before it is made."],
  ["Disclose", "When the honest number is unflattering, it goes on screen. When something published is wrong, the fix is a chapter that names the error."],
] as const;

export interface Project {
  key: string; name: string; kind: string; scope: string; stack: string[]; outputs: string[]; to?: string;
}

/** The body of work: what each project is, how big it is, and what it produced. */
export const PROJECTS: Project[] = [
  {
    key: "book", name: cabin.title, kind: "Book",
    scope: `The complete edition: ${BOOK_FIGURES.chapters} chapters in ${BOOK_FIGURES.parts} parts, ${BOOK_FIGURES.figures} figures and about ${BOOK_FIGURES.pages} pages, every number resolved from the project's models at build time.`,
    stack: ["Python", "Book engine", "Typeset PDF and web reader"],
    outputs: ["Digital complete edition", "Paperback", "Free sample"], to: "/book",
  },
  {
    key: "solver", name: "The raw-wedge dome solver", kind: "Computational geometry",
    scope: `Solves a 2V geodesic dome for split-log members: ${d.vertices} hubs, ${d.members} members, dihedral angles and every wedge cut, then builds it as a walkable 3-D world.`,
    stack: ["Python", "NumPy", "OpenGL (moderngl)"],
    outputs: ["Cut lists", "Book figures", "The film geometry"],
  },
  {
    key: "films", name: "The film pipeline", kind: "Video production",
    scope: `${FILM_COUNT} films in ${SERIES_COUNT} series, rendered from the solver's own geometry with narration, captions, a phone cut and a release folder made in one command.`,
    stack: ["Python", "OpenGL", "FFmpeg", "Neural voice"],
    outputs: ["Lessons and masterclasses", "Teasers", "Thumbnails and copy"], to: "/episodes",
  },
  {
    key: "sketch", name: "Dome Sketch", kind: "Design software",
    scope: "A framed-panel dome modeller that draws its own plan set: every dome type, cut cards, a build guide, exports and costing, in the browser and on the desktop.",
    stack: ["TypeScript", "Three.js", "Python"],
    outputs: ["Plan sets", "Build packs", "Showcase renders"], to: "/sketch",
  },
  {
    key: "world", name: "World3D and the Portal", kind: "Interactive 3-D",
    scope: "One 3-D world holding the foundation, the dome and the zome with their jigs and skins, plus a playable portal where every tool is a place.",
    stack: ["Python", "Three.js", "Game design"],
    outputs: ["Simulator", "The Portal"], to: "/portal",
  },
  {
    key: "site", name: "zeanahlab.com", kind: "Web platform",
    scope: `This site: the book store, accounts, the pad network, backers and founder plaques, ${PUBLIC_TOOLS} public tools, and the numbers exported straight from the models.`,
    stack: ["React", "TypeScript", "Tailwind", "Cloudflare Pages, D1, R2"],
    outputs: ["Store", "Accounts", "Network map"],
  },
  {
    key: "kids", name: facts.kidsBook.title, kind: "Picture book",
    scope: `The build told for children: ${facts.kidsBook.stanzaCount} rhyming spreads, illustrated, with a narrated bedtime film.`,
    stack: ["Writing", "Illustration", "Animation"],
    outputs: ["Picture book", "Bedtime story film"], to: "/kids",
  },
  {
    key: "economics", name: "The cost and network model", kind: "Economics",
    scope: `The stem-cell dome priced line by line (${facts.price.stemCell.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 })}), the pad network's terms for host and tenant, and the founder campaign's goal broken into ${facts.goal.lines.length} lines.`,
    stack: ["Python", "Cost modelling"],
    outputs: ["Price lists", "Pad terms", "Campaign plan"], to: "/network",
  },
];

/** What the work asks of whoever does it, grouped. */
export const SKILLS = [
  ["Build", ["Timber framing", "Chainsaw milling", "Jigs and fixtures", "Site and foundation"]],
  ["Compute", ["Computational geometry", "Python and NumPy", "3-D rendering", "Simulation"]],
  ["Ship", ["TypeScript and React", "Cloudflare platform", "E-commerce", "Automation"]],
  ["Tell", ["Technical writing", "Film and narration", "Publishing", "AI-assisted production"]],
] as const;
