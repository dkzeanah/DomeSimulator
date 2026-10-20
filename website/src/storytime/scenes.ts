// @ts-nocheck
// The pages of a story as scenes in the Storyworld: where we are, who is there, what they do, what
// is lettered in, and the camera move that runs for as long as the page is read. The book's own
// sixteen pictures (kids_book/pictures.py) are re-staged here one for one: the town of boxes, the
// dream, the lumber yard, the log, the tools on the stump, the split, the wedges, the chalk number,
// what the number tells, the pinwheel, the rising rings, the neighbours, the ledger, the fallen
// panel, the club and the night. The figures lettered in come from the manifest, which takes them
// from the book's reference build (kids_book.pictures.sheet), so nothing here is typed by hand.

import * as THREE from "three";
import { Character } from "./cast";
import { PEOPLE, V, type Storyworld } from "./engine";

type Figures = { longIn: number; shortIn: number; members: number; triangles: number; woodCuft: number; frameLb: number; frameCost: number; hours: string | number; diameterFt: number; heightFt: number };

const HILL_PROPS = ["dome", "domeWest", "domeEast", "dreamDome", "town", "lumber", "log", "wedgesSplit", "stump", "stack", "board", "panel"];
const act = (c, a) => { if (c.action !== a) c.do(a); };
const fmt = (n: number) => n.toLocaleString("en-US");

/** Lettering that floats in the picture: a soft card with chalky words, always facing the camera. */
function tag(w, text, at, { size = 0.9, bg = "rgba(255,250,235,0.92)", fg = "#3b2a1a", lines = null } = {}) {
  const L = lines || [text], c = document.createElement("canvas"), g = c.getContext("2d");
  const fs = 96, pad = 40;
  g.font = `bold ${fs}px "Comic Sans MS", "Chalkboard SE", "Marker Felt", cursive`;
  const wpx = Math.max(...L.map((t) => g.measureText(t).width)) + pad * 2, hpx = L.length * fs * 1.2 + pad * 1.4;
  c.width = Math.ceil(wpx); c.height = Math.ceil(hpx);
  g.font = `bold ${fs}px "Comic Sans MS", "Chalkboard SE", "Marker Felt", cursive`;
  g.fillStyle = bg; const r = 46;
  g.beginPath(); g.roundRect(0, 0, c.width, c.height, r); g.fill();
  g.fillStyle = fg; g.textAlign = "center"; g.textBaseline = "middle";
  L.forEach((t, i) => g.fillText(t, c.width / 2, pad * 0.7 + fs * 1.2 * (i + 0.5)));
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, depthTest: false, transparent: true, fog: false }));
  s.renderOrder = 10; s.scale.set(size * c.width / c.height, size, 1); s.position.copy(at);
  s.material.opacity = 0; s.userData.fadeIn = true;
  w.scene.add(s); w.temp.push(s); return s;
}

/** The chalkboard's face, written fresh for the page. */
function writeBoard(w, lines, { bg = "#1f3a2c", fg = "#f4f1e6" } = {}) {
  if (!w.boardFace) {
    w.boardCanvas = document.createElement("canvas"); w.boardCanvas.width = 1024; w.boardCanvas.height = 640;
    w.boardTex = new THREE.CanvasTexture(w.boardCanvas); w.boardTex.colorSpace = THREE.SRGBColorSpace;
    w.boardFace = new THREE.Mesh(new THREE.PlaneGeometry(1.5, 0.9), new THREE.MeshBasicMaterial({ map: w.boardTex }));
    w.boardFace.rotation.x = Math.PI / 2; w.boardFace.position.set(0, -0.035, 1.3); w.board.add(w.boardFace);
  }
  const g = w.boardCanvas.getContext("2d");
  g.fillStyle = bg; g.fillRect(0, 0, 1024, 640);
  g.fillStyle = fg; g.textAlign = "center"; g.textBaseline = "middle";
  lines.forEach((t, i) => { g.font = `bold ${i === 0 && lines.length > 1 ? 74 : 92}px "Comic Sans MS", "Chalkboard SE", cursive`; g.fillText(t, 512, 640 * (i + 0.5) / lines.length); });
  w.boardTex.needsUpdate = true;
}

/** Reset the stage, then show only what the page names. */
function stage(w, place, show = [], mood = "day") {
  for (const k of ["hill", "night", "sea", "blossoms", "bench"]) w.places[k].visible = k === place;
  for (const k of HILL_PROPS) if (w[k]) w[k].visible = show.includes(k);
  for (const s of w.temp) { s.parent?.remove(s); s.material?.map?.dispose(); }
  w.temp = [];
  w.hideCast();
  w.dome.userData.build(1);
  w.wedgesSplit.userData.split(0);
  w.glow.forEach((l) => (l.intensity = 0));
  w.letter.visible = false;
  w.ship.visible = true;
  w.mood(mood, w.places[place].position.clone());
  w.tick = null;
  w.board.position.set(3.0, 4.6, 0);
  // a person shows in the place the page is set in
  for (const c of Object.values(w.cast)) if (c.root.parent !== w.places.hill) c.root.visible = false;
}

function who(w, id, x, y, yaw, action = "idle", opts = {}) {
  const c = w.person(id, PEOPLE[opts.as || id], opts.parent);
  c.place(x, y, yaw); act(c, action); c.expr = opts.expr || "smile"; c.look = opts.look || null; c.speaking = !!opts.speaking;
  for (const k of Object.keys(c.props)) c.drop(k);
  return c;
}
const lookTo = (c, x, y) => (c.yaw = c.yawTarget = -Math.atan2(x - c.root.position.x, y - c.root.position.y));

// the far places' people, kept apart from the hill's
function farPerson(w, key, def, place) {
  w.far = w.far || {};
  if (!w.far[key]) { const c = new Character(THREE, key, def, w.places[place]); c.ground = () => 0; w.far[key] = c; w.hooks.push((dt) => { if (c.root.visible && w.places[place].visible) c.update(dt, w.time); }); }
  const c = w.far[key]; c.root.visible = true; c.walk = null; return c;
}

function family(w, place, at) {
  // Mama and the two of them on the blanket, looking up at the sky
  const P = w.places[place].position, y0 = at?.y ?? 0;
  const m = farPerson(w, "mama-" + place, PEOPLE.mama, place), a = farPerson(w, "annika-" + place, PEOPLE.annika, place), r = farPerson(w, "amara-" + place, PEOPLE.amara, place);
  m.place(0, y0 + 0.15, 0); a.place(-0.65, y0, 0); r.place(0.62, y0 - 0.05, 0);
  for (const c of [m, a, r]) { c.ground = () => -0.3 * c.k; c.place(c.root.position.x, c.root.position.y, 0); act(c, "sit"); c.expr = "smile"; }
  return { m, a, r, P };
}

export function makeScenes(w: Storyworld, F: Figures) {
  const R = w.domeRadius, H = w.domeHeight;
  const domeMid = V(0, 0, H * 0.45);
  const S = w.shots;
  return {
    // ---------------------------------------------------------------- the introduction
    stars(dur) {
      stage(w, "night", [], "night");
      const { m, a, r, P } = family(w, "night");
      m.headPitchBias = 0; [m, a, r].forEach((c) => (c.look = null));
      w.tick = () => { for (const c of [m, a, r]) c.head.rotation.x = -0.55; };
      const star = w.dadaStar.getWorldPosition(new THREE.Vector3());
      const sky = P.clone().add(star.clone().sub(P).normalize().multiplyScalar(30));
      return S.keys({ dur, keys: [
        { pos: P.clone().add(V(0.4, 4.2, 1.1)), target: P.clone().add(V(0, 0, 0.6)), fov: 38 },
        { pos: P.clone().add(V(0.2, -2.4, 1.3)), target: P.clone().add(V(0, 2, 1.4)), fov: 42 },
        { pos: P.clone().add(V(0, -2.2, 0.9)), target: sky, fov: 46 },
      ] });
    },
    sea(dur) {
      stage(w, "sea", [], "dusk");
      const P = w.places.sea.position, ship = P.clone().add(V(0, 0, 2.5));
      w.sailor.root.visible = true; act(w.sailor, "point"); w.sailor.expr = "far";
      return S.orbit({ subject: ship, radius: 16, height: 3.5, from: -140, sweep: 70, dur, fov: 36 });
    },
    blossoms(dur) {
      stage(w, "blossoms", [], "blossom");
      const P = w.places.blossoms.position;
      const d = farPerson(w, "dada-young", PEOPLE.dada, "blossoms"), m = farPerson(w, "mama-young", PEOPLE.mama, "blossoms");
      d.place(0.38, -6, 0); m.place(-0.38, -6, 0); d.expr = m.expr = "smile"; act(d, "idle"); act(m, "idle");
      d.walkTo(0.38, 4, 0.55); m.walkTo(-0.38, 4, 0.55);
      return S.keys({ dur, keys: [
        { pos: P.clone().add(V(4.5, -9, 1.6)), target: P.clone().add(V(0, -5, 1.3)), fov: 40 },
        { pos: P.clone().add(V(4.0, -3, 2.2)), target: P.clone().add(V(0, -0.5, 1.5)), fov: 40 },
        { pos: P.clone().add(V(1.5, 6, 3.4)), target: P.clone().add(V(0, 1.5, 2.2)), fov: 44 },
      ] });
    },
    workbench(dur) {
      stage(w, "bench", [], "lamp");
      const P = w.places.bench.position;
      w.benchDada.root.visible = true; act(w.benchDada, "hammer"); w.benchDada.expr = "neutral";
      w.tick = (t) => act(w.benchDada, Math.floor(t / 4) % 2 ? "think" : "hammer");
      return S.keys({ dur, keys: [
        // past his left shoulder, never through him (he stands at 0.6, 1.25), onto the little dome on the bench
        { pos: P.clone().add(V(-1.0, -1.6, 1.9)), target: P.clone().add(V(0.6, 2.0, 1.2)), fov: 40 },
        { pos: P.clone().add(V(-0.6, -0.4, 1.8)), target: P.clone().add(V(0.55, 2.2, 1.0)), fov: 38 },
        { pos: P.clone().add(V(-0.4, 0.6, 1.5)), target: P.clone().add(V(0.55, 2.2, 0.95)), fov: 34 },
      ] });
    },
    letter(dur) {
      stage(w, "sea", [], "night");
      const P = w.places.sea.position;
      w.letter.visible = true; w.ship.visible = false;
      const a = V(-40, 60, 18), b = V(4.2, -4.5, 3.2); w.letter.scale.setScalar(2.2);
      w.tick = (t) => {
        const f = Math.min(1, t / (dur * 0.8)), e = f * f * (3 - 2 * f);
        w.letter.position.copy(a.clone().lerp(b, e)); w.letter.position.z += Math.sin(t * 2) * 0.3;
        w.letter.rotation.set(Math.sin(t * 1.6) * 0.3, 0, Math.atan2(b.y - a.y, b.x - a.x) + Math.PI / 2 + Math.sin(t) * 0.2);
      };
      const at = (t) => w.letter.getWorldPosition(new THREE.Vector3());
      return { dur, at: (t) => { const L = at(t); return { pos: P.clone().add(V(5, -9, 3.0)), target: L, fov: 42 }; } };
    },
    cover(dur) {
      stage(w, "hill", ["dome"], "golden");
      who(w, "pip", 0.6, -R - 1.4, 200, "wave");
      return S.reveal({ subject: V(0, 0, H * 0.6), radius: R * 3.2, dur: Math.max(dur, 3), fov: 42 });
    },
    // ---------------------------------------------------------------- the story
    town(dur) {
      stage(w, "hill", ["town"], "day");
      const p = who(w, "pip", 0, 0, 0, "hips", { expr: "glare" });
      w.tick = (t) => act(p, t > dur * 0.55 ? "stomp" : "hips");
      return S.crane({ from: V(2.2, -3.4, 1.2), subject: V(0, 0, 0.9), rise: 7, back: 6, dur, fov: 44 });
    },
    dream(dur) {
      stage(w, "hill", ["dreamDome"], "dream");
      w.glow[0].intensity = 6;
      who(w, "pip", 0.2, -R - 1.2, 0, "vision", { expr: "vision" });
      return S.orbit({ subject: V(0, -R * 0.4, H * 0.45), radius: R * 2.9, height: 1.1, from: -125, sweep: 60, dur, fov: 44, lift: 1.4 });
    },
    lumber(dur) {
      stage(w, "hill", ["lumber"], "day");
      const p = who(w, "pip", 3.2, -9.4, 90, "idle");
      p.walkTo(10.5, -9.4, (7.3) / Math.max(4, dur - 3));
      w.tick = () => { if (!p.walk) act(p, "shrug"); };
      return S.slide({ from: V(6.8, -15.5, 1.6), subject: V(7.2, -8.4, 0.8), dist: 5, dur, fov: 40 });
    },
    log(dur) {
      stage(w, "hill", ["log"], "golden");
      const p = who(w, "pip", -6.4, 1.75, 0, "wave");
      w.tick = (t) => { if (t > 3) act(p, t > dur * 0.6 ? "point" : "idle"); };
      return S.dollyIn({ from: V(-2.6, -1.6, 1.4), subject: V(-6.3, 2.6, 0.6), dist: 0.55, dur, fov: 40 });
    },
    tools(dur) {
      stage(w, "hill", ["stump", "log"], "golden");
      const p = who(w, "pip", -5.25, -3.75, 0, "point");
      lookTo(p, -4.3, -3.4);
      return S.orbit({ subject: V(-4.3, -3.4, 0.45), radius: 2.1, height: 1.0, from: -80, sweep: 70, dur, fov: 40 });
    },
    zzzip(dur) {
      stage(w, "hill", ["wedgesSplit", "stump"], "golden");
      const p = who(w, "pip", -5.2, 2.05, 20, "crank");
      w.tick = (t) => w.wedgesSplit.userData.split(Math.min(1, Math.max(0, (t - 1.2) / (dur * 0.7))));
      return S.orbit({ subject: V(-4.6, 3.2, 0.45), radius: 3.6, height: 1.1, from: -40, sweep: 55, dur, fov: 42 });
    },
    wedges(dur) {
      stage(w, "hill", ["stack"], "day");
      const p = who(w, "pip", 4.6, 1.3, 0, "lift");
      const stick = w.wedgeStick(1.0); stick.rotation.y = Math.PI / 2; p.hold("wedge", stick, 1, [0, 0, -0.1]);
      return S.dollyIn({ from: V(6.8, -2.6, 1.2), subject: V(4.6, 1.6, 0.8), dist: 0.5, dur, fov: 40 });
    },
    chalk(dur) {
      stage(w, "hill", ["board"], "day");
      writeBoard(w, ["the longest strut", `${F.longIn} inches`]);
      const p = who(w, "pip", 2.0, 3.9, -35, "point", { expr: "smile" });
      w.tick = (t) => act(p, t > dur * 0.6 ? "cheer" : "point");
      return S.dollyIn({ from: V(1.9, 0.6, 1.4), subject: V(2.8, 4.6, 1.15), dist: 0.38, dur, fov: 40 });
    },
    measure(dur) {
      stage(w, "hill", ["dome"], "day");
      who(w, "pip", R + 1.1, -R * 0.6, 240, "think", { expr: "far" });
      const items = [
        [`${F.diameterFt} ft wide`, V(-R * 0.8, -R * 0.95, H * 0.45)],
        [`${F.heightFt} ft tall`, V(0.4, -0.2, H + 0.65)],
        [`${F.triangles} triangles`, V(-R * 0.9, -R * 0.2, H * 0.75)],
        [`${fmt(F.frameLb)} lb`, V(R * 0.9, -R * 0.1, H * 0.7)],
        [`${F.members} wedges`, V(R * 0.95, -R * 0.75, H * 0.35)],
      ];
      const tags = items.map(([t, at]) => tag(w, t, at, { size: 0.55 }));
      w.tick = (t) => tags.forEach((s, i) => (s.material.opacity = Math.min(1, Math.max(0, (t - 1.5 - i * (dur - 4) / items.length) * 2))));
      return S.orbit({ subject: V(0, 0, H * 0.5), radius: R * 3.4, height: 1.6, from: -120, sweep: 50, dur, fov: 44 });
    },
    pinwheel(dur) {
      stage(w, "hill", ["dome"], "golden");
      return S.orbit({ subject: V(0, 0, H), radius: 1.5, height: 0.7, from: -90, sweep: 120, dur, fov: 38 });
    },
    rising(dur) {
      stage(w, "hill", ["dome"], "golden");
      const p = who(w, "pip", R + 1.4, -R - 0.6, 225, "idle");
      w.tick = (t) => { const f = Math.min(1, 0.06 + t / (dur * 0.85)); w.dome.userData.build(f); if (f >= 1) act(p, "cheer"); };
      return S.spiral({ subject: V(0, 0, H * 0.45), radius: R * 3.0, height: 4.0, turns: 0.4, dur, fov: 44 });
    },
    neighbours(dur) {
      stage(w, "hill", ["dome"], "day");
      const p = who(w, "pip", 0, -R - 0.9, 180, "hips");
      const spots = [["n1", -2.6, -R - 2.8], ["n2", -1.2, -R - 3.3], ["n3", 1.4, -R - 3.2], ["n4", 2.7, -R - 2.7]];
      const ns = spots.map(([id, x, y], i) => { const c = who(w, id, x * 3, y - 8, 0, "idle", { expr: "wide" }); c.walkTo(x, y, 1.6 + i * 0.15); return c; });
      w.tick = (t) => {
        ns.forEach((c, i) => { if (!c.walk) { lookTo(c, 0, 0); act(c, i % 2 ? "cheer" : "point"); } });
        if (t > dur * 0.5) act(p, "talk"); p.speaking = t > dur * 0.5;
      };
      return S.crane({ from: V(1.2, -R - 7.5, 1.2), subject: V(0, -R * 0.4, 1.4), rise: 3.5, back: 2.5, dur, fov: 44 });
    },
    ledger(dur) {
      stage(w, "hill", ["dome", "board"], "golden");
      writeBoard(w, ["Pip's book", `wood: ${F.woodCuft} cu ft`, `frame: $${fmt(F.frameCost)}`, `${F.hours} hours`], { bg: "#f3ead2", fg: "#3b2a1a" });
      w.board.position.set(R + 1.2, -R + 0.2, 0);
      const p = who(w, "pip", R + 0.2, -R - 0.5, 210, "talk", { speaking: true });
      return S.dollyIn({ from: V(R + 0.6, -R - 4.2, 1.5), subject: V(R + 1.2, -R + 0.2, 1.45), dist: 0.62, dur, fov: 40 });
    },
    panel(dur) {
      stage(w, "hill", ["dome", "panel"], "day");
      const b = who(w, "boy", -1.8, -6.2, 90, "shrug", { expr: "sad" });
      const p = who(w, "pip", 0.9, -5.5, 250, "idle");
      w.tick = (t) => {
        if (t > dur * 0.35) act(p, "talk");
        if (t > dur * 0.62) { act(b, "cheer"); b.expr = "wide"; act(p, "cheer"); }
      };
      return S.slide({ from: V(-0.6, -10.2, 1.3), subject: V(-0.4, -5.9, 0.75), dist: 2.4, dur, fov: 40 });
    },
    club(dur) {
      stage(w, "hill", ["dome", "domeWest", "domeEast"], "golden");
      const kids = [["pip", -3.4, -3.8], ["boy", 3.6, -3.2], ["n2", -5.6, -0.6], ["n4", 5.8, -1.0]];
      kids.forEach(([id, x, y], i) => {
        const c = who(w, id, x, y, 0, "carry");
        const panel = w.makeLoosePanel(); panel.scale.setScalar(0.45); panel.rotation.x = Math.PI / 2; c.hold("panel", panel, 1, [0.1, 0.25, -0.3]);
        const to = kids[(i + 1) % kids.length]; c.walkTo(to[1], to[2], 0.7);
      });
      return S.flyover({ subject: V(0, 1.5, 1.6), radius: 13, height: 6, dur, fov: 46 });
    },
    night(dur) {
      stage(w, "hill", ["dome", "domeWest", "domeEast", "town"], "night");
      w.glow.forEach((l) => (l.intensity = 5));
      who(w, "pip", 0.4, -R + 1.0, 180, "sit");
      const star = w.dadaStar.getWorldPosition(new THREE.Vector3());
      return S.keys({ dur, keys: [
        { pos: V(1.5, -6.8, 1.5), target: V(0, 0, 1.4), fov: 44 },
        { pos: V(0.8, -7.8, 3.6), target: V(0, 0, 2.5), fov: 46 },
        { pos: V(0, -8.4, 5.0), target: star.clone().multiplyScalar(0.2), fov: 50 },
      ] });
    },
    // ---------------------------------------------------------------- goodnight
    goodnight(dur) {
      stage(w, "night", [], "night");
      const { m, a, r, P } = family(w, "night", { y: 0 });
      w.tick = () => { for (const c of [m, a, r]) c.head.rotation.x = -0.6; };
      const star = w.dadaStar.getWorldPosition(new THREE.Vector3());
      const sky = P.clone().add(star.clone().sub(P).normalize().multiplyScalar(30));
      return S.keys({ dur, keys: [
        { pos: P.clone().add(V(0, -3.0, 1.0)), target: P.clone().add(V(0, 0, 0.6)), fov: 40 },
        { pos: P.clone().add(V(0, -2.4, 1.0)), target: P.clone().add(V(0, 6, 4)), fov: 44 },
        { pos: P.clone().add(V(0, -2.2, 0.9)), target: sky, fov: 40 },
      ] });
    },
  };
}

/** Every scene a page can be set in, for the Story Studio's picker: name, what it shows, and which book page it re-stages. */
export const SCENES: { name: string; label: string; group: string }[] = [
  { name: "stars", label: "Mama and the two of them on the blanket, Dada's star", group: "Bedtime" },
  { name: "workbench", label: "Dada's workbench far away, under the lamp", group: "Bedtime" },
  { name: "letter", label: "A glowing story crossing the ocean at night", group: "Bedtime" },
  { name: "goodnight", label: "Goodnight: the blanket, the star over the house", group: "Bedtime" },
  { name: "sea", label: "The ship at dusk (origin story -- on hold)", group: "On hold" },
  { name: "blossoms", label: "The cherry-blossom path (origin story -- on hold)", group: "On hold" },
  { name: "cover", label: "Title card over the finished dome", group: "The hill" },
  { name: "town", label: "The town of boxes", group: "The hill" },
  { name: "dream", label: "A dream of a dome, glowing", group: "The hill" },
  { name: "lumber", label: "Walking past the lumber yard", group: "The hill" },
  { name: "log", label: "The fallen pine", group: "The hill" },
  { name: "tools", label: "The tools on the stump", group: "The hill" },
  { name: "zzzip", label: "The log splitting into eight wedges", group: "The hill" },
  { name: "wedges", label: "Holding up a wedge by the stack", group: "The hill" },
  { name: "chalk", label: "The longest strut, in chalk", group: "The hill" },
  { name: "measure", label: "What the number tells: width, height, weight", group: "The hill" },
  { name: "pinwheel", label: "Close on the pinwheel at the top", group: "The hill" },
  { name: "rising", label: "The dome rising ring by ring", group: "The hill" },
  { name: "neighbours", label: "The neighbours come running", group: "The hill" },
  { name: "ledger", label: "Pip's book of numbers", group: "The hill" },
  { name: "panel", label: "The boy with the fallen panel", group: "The hill" },
  { name: "club", label: "The dome club swapping panels", group: "The hill" },
  { name: "night", label: "Domes on the hill at night", group: "The hill" },
];

/** Camera moves a page can use instead of its scene's own: the Episode Director's shot library. */
export const SHOTS: { name: string; label: string }[] = [
  { name: "scene", label: "The scene's own move" },
  { name: "hold", label: "Hold (a slow breath in)" },
  { name: "dollyIn", label: "Dolly in" },
  { name: "dollyOut", label: "Dolly out" },
  { name: "slide", label: "Slide sideways" },
  { name: "pan", label: "Pan" },
  { name: "crane", label: "Crane up" },
  { name: "pedestal", label: "Pedestal up" },
  { name: "dollyZoom", label: "Dolly zoom (vertigo)" },
  { name: "orbit", label: "Orbit" },
  { name: "reveal", label: "Reveal (low to high)" },
  { name: "spiral", label: "Spiral down" },
  { name: "flyover", label: "Drone flyover" },
];

/** The page's scene, shot another way: the new move starts where the scene's camera starts, on the same subject. */
export function reshoot(w: Storyworld, shot, name: string, dur: number) {
  const S = w.shots, first = shot.at(0), from = first.pos.clone(), subject = first.target.clone();
  const flat = Math.hypot(from.x - subject.x, from.y - subject.y), fov = first.fov || 40;
  const from_deg = Math.atan2(from.y - subject.y, from.x - subject.x) * 180 / Math.PI;
  switch (name) {
    case "orbit": return S.orbit({ subject, radius: flat, height: from.z - subject.z, from: from_deg, sweep: 70, dur, fov });
    case "reveal": return S.reveal({ subject, radius: flat, dur, fov });
    case "spiral": return S.spiral({ subject, radius: flat, height: Math.max(2, from.z - subject.z + 3), turns: 0.4, dur, fov });
    case "flyover": return S.flyover({ subject, radius: flat, height: Math.max(3, from.z), dur, fov });
    case "dollyZoom": return S.dollyZoom({ from, subject, dur, fovFrom: fov * 0.8, fovTo: fov * 1.6 });
    case "crane": return S.crane({ from, subject, rise: Math.max(2, flat * 0.5), back: flat * 0.3, dur, fov });
    case "pedestal": return S.pedestal({ from, subject, rise: 1.5, dur, fov });
    default: return S[name] ? S[name]({ from, subject, dur, fov }) : shot;
  }
}
