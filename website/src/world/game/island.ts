// Wedge Island: the Portal's Tutorial Island. A new player builds the solver's 2V wedge dome from
// standing trees, one hands-on step at a time, with an instructor at every station: fell a pine and
// buck it, split a section eight ways, cut the two lengths of strut, frame a triangle on the
// simulator's own jig, raise the panels, key the seams and sheathe it. Every figure is the
// solver's (F from the exported facts; the raw-wedge simulator's tables in wedge.ts), and the dome
// that goes up is the simulator's own mesh.

import * as THREE from "three";
import mesh from "../../generated/dome-mesh.json";
import { World, type Pick } from "../engine";
import { housePortalMesh, idle, npcMesh } from "../entities";
import { AT, buck, buildIsland, fell, pineMesh, type IslandScene } from "../islandScene";
import { W, summary } from "../wedge";
import type { AreaGame, AreaScript, Option } from "./area";
import { F, type Line } from "./content";
import type { Store } from "./store";

const G = summary(W.defaults.orientation, W.defaults.longEdge, W.defaults.trunk);
const A = G.families.find((f) => f.type === "A")!, B = G.families.find((f) => f.type === "B")!;
const JIG = W.jigStages;
const jigFace = mesh.faces[W.jig.panel] as [number, number, number, string];
const JIG_A = [...jigFace[3]].filter((c) => c === "A").length, JIG_B = 3 - JIG_A;
const inch = (x: number) => `${x.toFixed(1)} in`;
const YOU_DO = 3;                      // panels, keys and sheets the player places before the crew joins in

interface Person { id: string; name: string; at: [number, number]; colour: string; hair: boolean; examine: string }
const PEOPLE: Person[] = [
  { id: "gale", name: "Guide Gale", at: AT.gale, colour: "#3a7ac8", hair: true, examine: "She has built more domes than she can count, and counts everything." },
  { id: "finn", name: "Forester Finn", at: AT.finn, colour: "#3a6a2a", hair: false, examine: "Knows every pine on the island by its lean." },
  { id: "sage", name: "Splitter Sage", at: AT.sage, colour: "#a8642a", hair: true, examine: "Reads the end grain like a clock face." },
  { id: "sol", name: "Sawyer Sol", at: AT.sol, colour: "#c84a2a", hair: false, examine: "Measures twice. Cuts once. Mostly." },
  { id: "jo", name: "Jig Master Jo", at: AT.jo, colour: "#7c5ac8", hair: true, examine: "Built the jig once, and has never had to measure since." },
  { id: "bo", name: "Builder Bo", at: AT.bo, colour: "#e8b45a", hair: false, examine: "Runs the site. Ropes, ladders, coffee." },
  { id: "gale2", name: "Guide Gale", at: AT.galeEnd, colour: "#3a7ac8", hair: true, examine: "Waiting by the portal to the mainland." },
];

/** The lesson, step by step: who teaches it, what to do, where the arrow points. */
interface Step { title: string; text: string; target: string }
const STEPS: Step[] = [
  { title: "Welcome to Wedge Island", text: "Talk to Guide Gale. Right-click anyone or anything to see what you can do with it.", target: "isl:npc:gale" },
  { title: "The forest", text: "Follow the path to Forester Finn and talk to him.", target: "isl:npc:finn" },
  { title: "Fell a pine", text: "Right-click a pine and choose Fell. The chainsaw is in your pack.", target: "isl:tree:0" },
  { title: "Buck it", text: "The pine is down. Click it to buck the trunk into sections the length of the long strut.", target: "isl:tree:0" },
  { title: "The block", text: "Take your log section to Splitter Sage at the block.", target: "isl:npc:sage" },
  { title: "Split it eight ways", text: "Click the block to rip the section with the chainsaw: in half, in quarters, in eighths.", target: "isl:block" },
  { title: "The saw", text: "Take your wedges to Sawyer Sol at the saw.", target: "isl:npc:sol" },
  { title: "Two lengths", text: `Click the saw to cut the struts for one triangle: ${JIG_A} A and ${JIG_B} B.`, target: "isl:saw" },
  { title: "The jig", text: "Take your struts to Jig Master Jo.", target: "isl:npc:jo" },
  { title: "Frame a triangle", text: "Click the jig to work it, one step at a time, until the panel comes off.", target: "isl:jig" },
  { title: "The site", text: "Carry your panel to Builder Bo at the site.", target: "isl:npc:bo" },
  { title: "Raise the dome", text: `Click the dome to raise your panel and the next. After ${YOU_DO}, the crew brings the rest.`, target: "isl:site" },
  { title: "Hardware", text: "Talk to Builder Bo about the seams.", target: "isl:npc:bo" },
  { title: "Key the seams", text: `Click the dome to fit seam keys. After ${YOU_DO}, the crew fits the rest.`, target: "isl:site" },
  { title: "Sheathe it", text: `Click the dome to sheathe a triangle. After ${YOU_DO}, the crew closes it in.`, target: "isl:site" },
  { title: "Done", text: "Talk to Guide Gale by the portal.", target: "isl:npc:gale2" },
  { title: "To the mainland", text: "Step through the portal to the mainland: the Portal's hilltop.", target: "isl:exit" },
];

const say = (who: "npc" | "you", text: string): Line => ({ who, text });
export { AT, GROUND, SKY } from "../islandScene";

export function createIsland(world: World, store: Store, game: AreaGame, changed: () => void, leave: () => void): { script: AreaScript; scene: IslandScene } {
  const scene = buildIsland();
  world.setEstate(scene.group, scene.obstacles, scene.tick);
  const s = store;
  if (!s.s.tut) s.s.tut = { step: 0, n: 0 };
  const T = () => s.s.tut!;
  const set = (step: number, n = 0) => { s.s.tut = { ...T(), step, n }; s.emit(); show(); };

  for (const p of PEOPLE) {
    const body = npcMesh(p.colour, p.hair);
    const mark = body.getObjectByName("marker");
    if (mark) mark.visible = false;                 // on the island the hint arrow does the pointing
    world.addThing({ id: `isl:npc:${p.id}`, kind: "npc", name: p.name }, body, p.at[0], p.at[1],
      { facing: Math.atan2(AT.spawn[0] - p.at[0], AT.spawn[1] - p.at[1]), height: 5.6, animate: idle });
  }
  AT.trees.forEach(([x, z], i) => world.addThing({ id: `isl:tree:${i}`, kind: "object", name: "Pine tree" }, pineMesh(), x, z, { height: 30, facing: 0 }));
  // the stations are drawn by the scene; these are the invisible volumes a click finds them by
  const hit = (r: number, h: number) => {
    const g = new THREE.Group();
    const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, 10), new THREE.MeshBasicMaterial({ visible: false }));
    m.position.y = h / 2; g.add(m);
    return g;
  };
  world.addThing({ id: "isl:block", kind: "object", name: "Splitting block" }, hit(2.2, 3.6), AT.block[0], AT.block[1], { height: 3.5 });
  world.addThing({ id: "isl:saw", kind: "object", name: "Saw bench" }, hit(4.5, 5), AT.saw[0], AT.saw[1], { height: 6 });
  world.addThing({ id: "isl:jig", kind: "object", name: "Assembly jig" }, hit(7, 5), AT.jig[0], AT.jig[1], { height: 6 });
  world.addThing({ id: "isl:site", kind: "object", name: "Dome site" }, hit(mesh.radiusFt * 1.12, mesh.radiusFt + 2), AT.site[0], AT.site[1], { height: 24 });
  world.addThing({ id: "isl:exit", kind: "object", name: "Portal to the mainland" }, housePortalMesh("#e8b45a"), AT.exit[0], AT.exit[1],
    { height: 12.5, facing: Math.atan2(-AT.exit[0], -AT.exit[1]) + Math.PI, animate: idle });

  // what the stations show for where the lesson stands
  let felling = -1, feltF = 0, crew: "panels" | "keys" | "skin" | null = null;
  const show = () => {
    const { step, n } = T();
    const tree = world.thingObject("isl:tree:0");
    if (tree) { if (step >= 3 && step < 4) fell(tree, 1); if (step >= 4) { fell(tree, 1); buck(tree); } }
    scene.setSplit(step === 5 ? n : -1);
    const cut = step === 7 ? n : step >= 8 && step <= 9 ? 3 : 0;
    scene.setStruts(Math.min(cut, JIG_A), Math.max(0, cut - JIG_A));
    scene.setJig(step === 9 ? n : step > 9 ? JIG.length - 1 : 0);
    const panels = step === 11 ? n : step > 11 ? scene.counts.panels : 0;
    const keys = step === 13 ? n : step > 13 ? scene.counts.keys : 0;
    const skin = step === 14 ? n : step > 14 ? scene.counts.panels : 0;
    scene.setDome(panels, keys, skin);
    world.setHint(T().done && step >= 16 ? "isl:exit" : STEPS[Math.min(step, STEPS.length - 1)].target, step === 11 || step >= 13 && step <= 14 ? 26 : 8.5);
    changed();
  };
  scene.ready.then(show);
  show();
  // a reload in the middle of a crew job: the crew carries on
  { const { step, n } = T(); if (n >= YOU_DO) crew = step === 11 ? "panels" : step === 13 ? "keys" : step === 14 ? "skin" : null; }

  const talk = (id: string, lines: Line[]) => {
    const p = PEOPLE.find((x) => x.id === id)!;
    world.walkNear(`isl:npc:${id}`, 3.6, () => { game.dialog = { npc: `isl:${id}`, name: p.name, lines, at: 0 }; changed(); });
  };
  const notYet = (id: string) => talk(id, [say("npc", "Not yet. The yellow arrow shows where to go next, and the box above the chat says what to do.")]);

  const lines: Record<string, () => Line[] | null> = {
    gale: () => T().step === 0 ? [
      say("npc", "Welcome to Wedge Island. Before you leave it you will have built a dome, from standing trees."),
      say("npc", `The solver's 2V dome: ${F.nodes} nodes, ${F.struts} edges in two lengths, ${F.triangles} triangles.`),
      say("npc", `Each triangle is framed on its own, by three wedges, so every edge inside the dome carries two. That is ${G.members} wedges, ${A.count} long and ${B.count} short, from ${G.logsAtSplits} log sections split ${W.declared.splits} ways.`),
      say("npc", "You will do one of each job yourself. The crew does the rest, at the same stations, the same way."),
      say("npc", "Click to walk. Right-click anything for its options. Follow the yellow arrow to Forester Finn."),
    ] : null,
    finn: () => T().step === 1 ? [
      say("npc", `Get your chainsaw out. A pine this size gives sections the length of the long strut, and the same saw rips every section into ${W.declared.splits} wedges.`),
      say("npc", "Fell from the side away from the path, and never alone. Right-click a pine and choose Fell."),
    ] : null,
    sage: () => T().step === 4 ? [
      say("npc", `A section ${F.logIn} in across is ripped with the chainsaw, straight down through the pith: in half, then quarters, then eighths. Each eighth is a ${360 / W.declared.splits}° wedge, 1/${W.declared.splits} of the round.`),
      say("npc", "Halves first, always: every cut runs radially, through the middle, so each wedge keeps the grain from bark to pith. Stand the section on the block and click it."),
    ] : null,
    sol: () => T().step === 6 ? [
      say("npc", `Two lengths, that is all. A for the ${F.strutsA} long edges, ${inch(A.nominal)} nominal; B for the ${F.strutsB} short ones, ${inch(B.nominal)}. Framing each triangle on its own takes ${A.count} long and ${B.count} short.`),
      say("npc", `The blanks are shorter than the edges: A ${inch(A.blankMin)} to ${inch(A.blankMax)}, B ${inch(B.blankMin)} to ${inch(B.blankMax)}. The corners are solved, not measured.`),
      say("npc", `The butt end is the only cut made before the jig. Every stick of a length takes the same one. Your triangle wants ${JIG_A} A and ${JIG_B} B.`),
    ] : null,
    jo: () => T().step === 8 ? [
      say("npc", `This is the simulator's own jig for panel ${W.jig.panel + 1}. It has ${JIG.length} steps, and nothing on it is adjusted between panels.`),
      say("npc", "Each stick's butt bears on the side of the next: a pinwheel. The heads stay long until the loop is closed, then they are flush-cut in place."),
      say("npc", "Click the jig to work it, one step at a time."),
    ] : null,
    bo: () => T().step === 10 ? [
      say("npc", `${F.triangles} panels make the dome. They go up from the bottom ring, each one bolted to its neighbours.`),
      say("npc", `Raise yours, and ${YOU_DO - 1} more. Then the crew raises the rest.`),
    ] : T().step === 12 ? [
      say("npc", `${G.seams} seams. Where two panels meet they fold ${A.fold!.toFixed(1)}° on a long edge and ${B.fold!.toFixed(1)}° on a short one.`),
      say("npc", `The raw wedge faces leave a ${A.gap!.toFixed(1)}° and ${B.gap!.toFixed(1)}° gap, and a key fills it: ${inch(A.keyBase!)} and ${inch(B.keyBase!)} across at the base.`),
      say("npc", "Fit a few keys, screw them home. The crew will finish."),
    ] : null,
    gale2: () => T().step === 15 ? [
      say("npc", `That is a dome: ${G.members} wedges, ${G.joints} pinwheel joints, ${G.seams} keyed seams, ${F.triangles} triangles closed in.`),
      say("npc", `About ${G.volumeFt3.toFixed(0)} cubic feet of wood, ${Math.round(G.dryLb).toLocaleString()} lb dry. The stock flush-cut off the heads: ${(G.headOffcutIn / 12).toFixed(0)} ft of it.`),
      say("npc", "On the mainland the teachers, the tools and the Dome Creator are waiting. Step through the portal when you are ready."),
    ] : null,
  };

  const finishTalk = (npc: string) => {
    const step = T().step;
    if (npc === "isl:gale" && step === 0) set(1);
    else if (npc === "isl:finn" && step === 1) {
      if (s.count("chainsaw")) s.say("Forester Finn checks the chain on your chainsaw and hands it back.", "quest");
      else { s.give("chainsaw", 1); s.say("Forester Finn hands you a chainsaw.", "quest"); }
      set(2);
    }
    else if (npc === "isl:sage" && step === 4) { if (!s.count("chainsaw")) s.give("chainsaw", 1); s.say("Splitter Sage stands your section on the block. Your chainsaw does the splitting.", "quest"); set(5, 0); }
    else if (npc === "isl:sol" && step === 6) set(7, 0);
    else if (npc === "isl:jo" && step === 8) set(9, 0);
    else if (npc === "isl:bo" && step === 10) set(11, 0);
    else if (npc === "isl:bo" && step === 12) { s.give("screws", 12); s.say("Builder Bo gives you a box of structural screws.", "quest"); set(13, 0); }
    else if (npc === "isl:gale2" && step === 15) {
      s.addXp("forestry", 300); s.addXp("splitting", 300); s.addXp("milling", 200); s.addXp("framing", 300);
      s.addXp("rigging", 200); s.addXp("roofing", 200); s.addXp("paneling", 200);
      s.give("coins", 50);
      if (!s.s.badges.includes("Islander")) s.s.badges.push("Islander");
      s.say("Congratulations! You have built a wedge dome from standing trees. You earn the Islander badge.", "quest");
      s.s.tut = { step: 16, n: 0, done: true }; s.emit(); show();
    }
  };

  // the jobs, each a few ticks of work
  let busy: { left: number; done: () => void } | null = null;
  const work = (id: string, ticks: number, start: string, done: () => void) => {
    // close enough to work: just outside what the walker goes round at each station
    const reach = id === "isl:site" ? mesh.radiusFt * 1.12 + 3 : id === "isl:jig" ? 9.5 : id === "isl:saw" ? 6.5 : 4.2;
    world.walkNear(id, reach, () => { if (busy) return; s.say(start); busy = { left: ticks, done }; world.face(id); });
  };

  const options = (p: Pick): Option[] | null => {
    const id = p.thing?.id;
    if (!id || !id.startsWith("isl:")) return null;
    const t = p.thing!, { step, n } = T();
    const ex = (text: string): Option => ({ label: "Examine", target: t.name, colour: "#3ad6ff", run: () => s.say(text) });
    if (id.startsWith("isl:npc:")) {
      const who = id.slice(8), person = PEOPLE.find((x) => x.id === who)!;
      return [{ label: "Talk-to", target: t.name, colour: "#ffe24a", run: () => { const l = lines[who]?.(); if (l) talk(who, l); else notYet(who); } }, ex(person.examine)];
    }
    if (id.startsWith("isl:tree:")) {
      const first = id === "isl:tree:0";
      if (first && step === 3) return [{ label: "Buck", target: "Felled pine", colour: "#3ad6ff", run: () => work(id, 4, "You buck the trunk...", () => {
        s.give("section", 1); s.addXp("forestry", 40); world.splat("player", "+40 Forestry", "xp");
        s.say(`You buck the trunk into sections. You keep one; the crew stacks the rest. The dome takes ${G.logsAtSplits}.`); set(4);
      }) }, ex("A felled pine, ready to buck.")];
      if (first && step >= 4) return [ex("A stump, and the crew's sections.")];
      return [{ label: "Fell", target: t.name, colour: "#3ad6ff", run: () => {
        if (step !== 2) { s.say(step < 2 ? "You need a chainsaw, and Forester Finn's word, first." : "One pine is enough for the lesson."); return; }
        if (!first) { s.say("Forester Finn marked the nearest pine for you."); return; }
        work(id, 5, "You rev the chainsaw and cut the notch...", () => { felling = 0; feltF = 0; s.addXp("forestry", 60); world.splat("player", "+60 Forestry", "xp"); });
      } }, ex("A straight pine about a foot across. Good wedges in it.")];
    }
    if (id === "isl:block") return [{ label: "Split", target: t.name, colour: "#3ad6ff", run: () => {
      if (step !== 5) { s.say(step < 5 ? "You have nothing to split yet." : "The section is already eighths."); return; }
      if (!s.count("chainsaw")) { s.say("You need your chainsaw. Forester Finn gave you one."); return; }
      const names = ["in half", "into quarters", "into eighths"];
      work(id, 3, `You rip the section ${names[n]} with the chainsaw...`, () => {
        s.addXp("splitting", 30); world.splat("player", "+30 Splitting", "xp");
        if (n + 1 < 3) { set(5, n + 1); return; }
        s.take("section", 1); s.give("wedge", W.declared.splits); s.say(`${W.declared.splits} wedges, each 1/${W.declared.splits} of the section: a ${360 / W.declared.splits}° sector with its bark on the back.`); set(6);
      });
    } }, ex("A stump for splitting on.")];
    if (id === "isl:saw") return [{ label: "Cut", target: t.name, colour: "#3ad6ff", run: () => {
      if (step !== 7) { s.say(step < 7 ? "Talk to Sawyer Sol first." : "You have the struts you need."); return; }
      const isA = n < JIG_A;
      if (!s.count("wedge")) { s.say("You need a wedge."); return; }
      work(id, 3, `You cut a ${isA ? "long A" : "short B"} strut...`, () => {
        if (!s.take("wedge", 1)) { s.say("You need a wedge."); return; }
        s.give(isA ? "strutA" : "strutB", 1); s.addXp("milling", 25); world.splat("player", "+25 Milling", "xp");
        s.say(isA ? `An A strut: a blank about ${inch(A.blankMax)}, its butt ${inch(A.buttSetback)} back from the vertex.` : `A B strut: a blank about ${inch(B.blankMax)}, its butt ${inch(B.buttSetback)} back.`);
        if (n + 1 < 3) set(7, n + 1); else { s.say("Three struts for one triangle. The other wedges go to the crew."); set(8); }
      });
    } }, ex("A chop saw on a bench, set for the butt cut.")];
    if (id === "isl:jig") return [{ label: "Work", target: t.name, colour: "#3ad6ff", run: () => {
      if (step !== 9) { s.say(step < 9 ? "Talk to Jig Master Jo first." : "The panel is off the jig."); return; }
      const next = n + 1;
      work(id, 2, `${JIG[next].title.replace(/^\d+\.\s*/, "")}...`, () => {
        s.addXp("framing", 20);
        s.say(`${JIG[next].title}: ${JIG[next].does}`);
        if (["member1", "member2", "member3"].includes(JIG[next].slug)) {
          const want = JIG[next].slug === "member1" ? "strutA" : "strutB";
          s.take(s.count(want) ? want : s.count("strutA") ? "strutA" : "strutB", 1);
        }
        if (next < JIG.length - 1) set(9, next);
        else { s.give("panel", 1); s.addXp("paneling", 80); world.splat("player", "+80 Paneling", "xp"); set(10); }
      });
    } }, ex(`The simulator's jig for panel ${W.jig.panel + 1}. Every panel comes off it the same.`)];
    if (id === "isl:site") {
      const job = step === 11 ? "Raise" : step === 13 ? "Fit keys" : step === 14 ? "Sheathe" : null;
      const o: Option[] = [];
      if (job) o.push({ label: job, target: t.name, colour: "#3ad6ff", run: () => {
        if (crew) { s.say("The crew is on it. Watch."); return; }
        work(id, 2, step === 11 ? "You raise a panel and bolt it to its neighbours..." : step === 13 ? "You set a key in a seam and screw it home..." : "You fit a sheet over a triangle...", () => {
          const k = n + 1;
          if (step === 11) { if (n === 0) s.take("panel", 1); s.addXp("rigging", 30); }
          if (step === 13) { s.take("screws", 4); s.addXp("roofing", 20); }
          if (step === 14) s.addXp("paneling", 30);
          set(step, k);
          if (k >= YOU_DO) { crew = step === 11 ? "panels" : step === 13 ? "keys" : "skin"; s.say("The crew joins in."); }
        });
      } });
      return [...o, ex(step < 11 ? "The deck, waiting for its dome." : "The solver's own dome, going up.")];
    }
    if (id === "isl:exit") return [{ label: "Enter", target: t.name, colour: "#3ad6ff", run: () => {
      if (!T().done) { s.say("Finish the dome first. Guide Gale will send you over."); return; }
      world.walkNear(id, 5, leave);
    } }, ex("The way to the mainland.")];
    return null;
  };

  const script: AreaScript = {
    options,
    dialogDone: finishTalk,
    tick() {
      if (busy && --busy.left <= 0) { const b = busy; busy = null; b.done(); }
      if (felling >= 0) {
        feltF = Math.min(1, feltF + 0.18);
        const tree = world.thingObject("isl:tree:0");
        if (tree) fell(tree, feltF * feltF);
        if (feltF >= 1) { felling = -1; s.say("Timber! The pine is down."); set(3); }
      }
      if (crew) {
        const { step, n } = T();
        const total = crew === "keys" ? scene.counts.keys : scene.counts.panels;
        const k = Math.min(total, n + (crew === "keys" ? 2 : 1));
        if (k >= total) {
          const was = crew; crew = null;
          if (was === "panels") { s.say(`All ${total} panels are up. Talk to Builder Bo.`, "quest"); set(12); }
          else if (was === "keys") { s.say(`All ${total} seams are keyed.`, "quest"); set(14, 0); }
          else { s.say("The dome is closed in. Guide Gale is waiting by the portal.", "quest"); set(15); }
        } else set(step, k);
      }
    },
    guide() {
      const { step, n } = T();
      const st = STEPS[Math.min(step, STEPS.length - 1)];
      let text = st.text;
      if (step === 5) text += ` (${["whole", "halves", "quarters"][n]} so far)`;
      if (step === 7) text += ` (${n} of 3 cut)`;
      if (step === 9) text = `${JIG[n + 1]?.title ?? ""}: ${JIG[n + 1]?.see ?? ""} Click the jig for the next step.`;
      if (step === 11) text += ` (${n} of ${scene.counts.panels} up)`;
      if (step === 13) text += ` (${n} of ${scene.counts.keys} keyed)`;
      if (step === 14) text += ` (${n} of ${scene.counts.panels} sheathed)`;
      return { title: st.title, text, step: Math.min(step + 1, STEPS.length), of: STEPS.length };
    },
    skip() { s.s.tut = { step: 16, n: 0, done: true }; s.emit(); leave(); },
    dispose() { world.setHint(null); },
  };
  return { script, scene };
}
