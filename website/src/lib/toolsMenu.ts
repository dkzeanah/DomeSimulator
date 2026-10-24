// Every tool the site leads to, in one list: the nav's Tools menu and the /tools page both read it.
// `key` matches a card from /api/me/tools (functions/_lib/tools.ts), which says whether this
// account may open it; `staff` items show only to the owner and managers. Studio tools run on the
// owner's computer (py -3.12 -m sketch_claude serve), so their links are to 127.0.0.1.

export interface ToolLink { key: string; label: string; to: string; blurb: string; external?: boolean; staff?: boolean }
export interface ToolGroup { title: string; staff?: boolean; items: ToolLink[] }

const STUDIO = "http://127.0.0.1:8767";

export const TOOL_GROUPS: ToolGroup[] = [
  {
    title: "Design and build",
    items: [
      { key: "domesketch", label: "Dome Sketch", to: "/sketch", blurb: "Design a framed-panel dome in 3-D and get its build pack." },
      { key: "calculator", label: "Wedge calculator", to: "/calculator", blurb: "What each split keeps of a log, at your kerf." },
      { key: "wedgebuilder", label: "Wedge Builder", to: "/software#wedge-builder", blurb: "A cut list for your own wedge dome and logs." },
      { key: "portal", label: "The Portal", to: "/portal", blurb: "Every tool as a place in one 3-D world, and a game of dome know-how." },
    ],
  },
  {
    title: "Yours",
    items: [
      { key: "mylinks", label: "My Links", to: "/mylinks", blurb: "The tools your account can open, and your build packs." },
      { key: "trial", label: "Software trial", to: "/software", blurb: "Try each tool before you buy it." },
      { key: "episodes", label: "Episodes", to: "/episodes", blurb: "Every film, free to watch." },
    ],
  },
  {
    title: "The studio (owner)",
    staff: true,
    items: [
      { key: "admintools", label: "Tools and releases", to: "/admin/tools", blurb: "Staging, promote to live, the build-pack queue.", staff: true },
      { key: "director", label: "Episode Director", to: `${STUDIO}/director`, blurb: "Edit and render episodes.", external: true, staff: true },
      { key: "season", label: "Season room", to: `${STUDIO}/season`, blurb: "The season's episodes and threads.", external: true, staff: true },
      { key: "modeller", label: "Modeller (full)", to: `${STUDIO}/`, blurb: "Every setting, plan sets and showcase renders.", external: true, staff: true },
      { key: "lessons", label: "Lesson Studio", to: `${STUDIO}/lesson?lesson=2v`, blurb: "Lesson films on the web engine.", external: true, staff: true },
    ],
  },
];
