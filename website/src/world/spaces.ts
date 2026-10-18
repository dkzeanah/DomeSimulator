// The places the portal world leads to: one per tool of the project. Each names the Python
// tool it will port, the colour of its gateway, and the controls its space will carry, so the
// hub, the minimap and every space read one list. The spaces are stages today; each tool's
// working interface is built into its space next.

export interface Space {
  key: string;
  name: string;
  blurb: string;
  ports: string;            // the desktop tool this space becomes
  colour: string;           // the gateway's glow
  sky: [string, string];    // the space's sky, top and horizon
  ground: string;
  controls: string[];       // what its control panel will hold
}

export const SPACES: Space[] = [
  {
    key: "dome-creator", name: "Dome Creator", colour: "#e8b45a", sky: ["#1b2a4a", "#e8a25a"], ground: "#4c5a2c",
    blurb: "Pick a frequency, a size and a method; see the dome, its struts, its hubs and its cost.",
    ports: "dome_creator.py (the Dome Creator) and seed_model",
    controls: ["Frequency (2V, 3V, 4V)", "Size: longest strut or floor", "Method: wedge, hub, hubless", "Cut list and cost", "Export the dome"],
  },
  {
    key: "assembly-line", name: "Dome Assembly Line", colour: "#e07a3c", sky: ["#241c18", "#a8643a"], ground: "#5a4a3a",
    blurb: "The factory floor: every station, every member's path from log to dome, timed.",
    ports: "al_build (the assembly line build)",
    controls: ["Stations and crews", "Line speed and takt time", "Members in flight", "Bottlenecks", "Cost per dome"],
  },
  {
    key: "wedge-method", name: "3D Wedge Method", colour: "#c98a3e", sky: ["#1f2d22", "#d8a050"], ground: "#3f5a2a",
    blurb: "Split the log into wedges, cut them to length, and pinwheel them into the frame.",
    ports: "geodesic_raw_wedge_dome_dihedral.py (the raw-wedge solver)",
    controls: ["Log diameter and splits", "Strut lengths", "Seam and dihedral angles", "Pinwheel joints", "Fabrication package"],
  },
  {
    key: "zome", name: "3D Zome", colour: "#7cc4f0", sky: ["#14223a", "#5a8ac0"], ground: "#34504a",
    blurb: "The wedge zome: one bevel, inside channels, nine sections.",
    ports: "wedge_zome (the zome tool and its cut package)",
    controls: ["Sections and height", "The 22.5 degree bevel", "Inside V channels", "Cut package"],
  },
  {
    key: "panel-creator", name: "Panel Creator", colour: "#6fdc9b", sky: ["#1a2a24", "#6aa880"], ground: "#3a5a3a",
    blurb: "Fill the triangles: wedge pairs, patterns and covers, numbered and cut flush.",
    ports: "infill/ (the Triangle Infill studio and 3-D cutting tool)",
    controls: ["Triangle and pattern", "Pairs, rings, louvers, chevrons", "Numbered pieces", "Saw setups", "The whole dome filled"],
  },
  {
    key: "foundation", name: "Foundation & Pads", colour: "#b8a07a", sky: ["#232323", "#9a8a6a"], ground: "#55503f",
    blurb: "The pentagon foundation, the pad deck, piers and hookups.",
    ports: "world3d foundation and pad_deck",
    controls: ["Pad size and deck", "Piers and footings", "Hookups", "Host costs"],
  },
  {
    key: "cell-wall", name: "Cell Wall & Seams", colour: "#d47ac0", sky: ["#26182a", "#a06a9a"], ground: "#4a3a4a",
    blurb: "The layered skin, its channels and the seam climate.",
    ports: "cabin_cell_wall and seam_climate",
    controls: ["Layers of the skin", "Local, global and ring channels", "Dew point and modes", "Insulation"],
  },
  {
    key: "masterclass", name: "Masterclass Theatre", colour: "#9aa4ff", sky: ["#101426", "#4a5a9a"], ground: "#2a3040",
    blurb: "Every lesson of the films, chapter by chapter, with its live calculations.",
    ports: "two_v_masterclass.py (the lessons)",
    controls: ["Lesson and chapter", "Play, pause, scrub", "Live calculation", "Stills"],
  },
];

export const spaceByKey = (key: string | undefined) => SPACES.find((s) => s.key === key);
