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
import { need } from "./places";

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
  for (const k of Object.keys(w.places)) w.places[k].visible = k === place;
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
  // a person shows in the place the page is set in, and only when the page puts them there
  for (const c of Object.values(w.cast)) if (c.root.parent !== w.places.hill) c.root.visible = false;
  for (const c of Object.values(w.far || {})) { c.root.visible = false; for (const k of Object.keys(c.props)) c.drop(k); }
  if (w.moteField) w.moteField.visible = !!w.ethereal;
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
  // a parent and two children on the blanket, looking up at the sky
  const P = w.places[place].position, y0 = at?.y ?? 0;
  const m = farPerson(w, "parent-" + place, PEOPLE.parent, place), a = farPerson(w, "kidA-" + place, PEOPLE.kidA, place), r = farPerson(w, "kidB-" + place, PEOPLE.kidB, place);
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
      const star = w.brightStar.getWorldPosition(new THREE.Vector3());
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
      const d = farPerson(w, "walker-a", PEOPLE.maker, "blossoms"), m = farPerson(w, "walker-b", PEOPLE.parent, "blossoms");
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
      w.benchMaker.root.visible = true; act(w.benchMaker, "hammer"); w.benchMaker.expr = "neutral";
      w.tick = (t) => act(w.benchMaker, Math.floor(t / 4) % 2 ? "think" : "hammer");
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
      const star = w.brightStar.getWorldPosition(new THREE.Vector3());
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
      const star = w.brightStar.getWorldPosition(new THREE.Vector3());
      const sky = P.clone().add(star.clone().sub(P).normalize().multiplyScalar(30));
      return S.keys({ dur, keys: [
        { pos: P.clone().add(V(0, -3.0, 1.0)), target: P.clone().add(V(0, 0, 0.6)), fov: 40 },
        { pos: P.clone().add(V(0, -2.4, 1.0)), target: P.clone().add(V(0, 6, 4)), fov: 44 },
        { pos: P.clone().add(V(0, -2.2, 0.9)), target: sky, fov: 40 },
      ] });
    },
    ...memoryScenes(w, S),
  };
}

// ------------------------------------------------------------------ the far-away scenes (places.ts)
const CREW = { name: "a sailor", height: 1.76, skin: "#c99572", shirt: "#26324f", shirt2: "#1b243a", pants: "#26324f", hair: "#1d140e", hairStyle: "buzz", sailorCap: true, belly: 1.0 };
const CREW2 = { ...CREW, skin: "#8a5a3e", hair: "#120c08", hairStyle: "short", height: 1.8 };
const BABY = { name: "a baby", height: 0.64, skin: "#d7a585", shirt: "#f4e6c8", shirt2: "#e6d2a8", pants: "#f4e6c8", hair: "#1d140e", hairStyle: "buzz", bucketHat: "#e07a22", belly: 1.15 };
const OFFDUTY = (def) => ({ ...def, sailorCap: false });

function memoryScenes(w, S) {
  const at = (name) => need(w, name).position.clone();
  const P = (name, x, y, z) => at(name).add(V(x, y, z));
  return {
    moonsea(dur) {
      need(w, "moonsea"); stage(w, "moonsea", [], "moon");
      return S.keys({ dur, keys: [
        { pos: P("moonsea", 0, -12, 1.2), target: P("moonsea", 0, 60, 6), fov: 44 },
        { pos: P("moonsea", -3, -4, 2.6), target: P("moonsea", -8, 46, 3), fov: 40 },
        { pos: P("moonsea", -1, 4, 4.2), target: P("moonsea", 0, 150, 22), fov: 34 },
      ] });
    },
    bridge(dur) {
      need(w, "bridge"); stage(w, "bridge", [], "bridge");
      const d = farPerson(w, "helm", PEOPLE.maker, "bridge");
      d.place(0, 1.35, 0); act(d, "measure"); d.expr = "far";
      w.tick = (t) => act(d, t % 9 < 5 ? "measure" : "think");
      return S.keys({ dur, keys: [
        { pos: P("bridge", -3.4, -2.6, 2.2), target: P("bridge", 0, 2.4, 1.6), fov: 42 },
        { pos: P("bridge", -1.6, -0.6, 1.9), target: P("bridge", 0, 2.0, 1.5), fov: 38 },
        { pos: P("bridge", 1.2, 0.4, 1.8), target: P("bridge", 0.6, 3.6, 2.6), fov: 36 },
      ] });
    },
    deck(dur) {
      need(w, "deck"); stage(w, "deck", [], "sea");
      const d = farPerson(w, "deckhand", PEOPLE.maker, "deck"), a = farPerson(w, "crew-a", CREW, "deck"), b = farPerson(w, "crew-b", CREW2, "deck");
      for (const c of [d, a, b]) c.ground = () => 1.25;
      d.place(-1.2, 3.4, 10); a.place(1.4, 3.8, -30); b.place(-2.6, -2.0, 90);
      act(d, "crank"); act(a, "lift"); act(b, "carry"); d.expr = a.expr = b.expr = "smile";
      return S.keys({ dur, keys: [
        { pos: P("deck", 3.8, -5.0, 3.6), target: P("deck", 0, 4, 1.8), fov: 44 },
        { pos: P("deck", 2.4, 0.6, 2.6), target: P("deck", -0.6, 5.6, 1.6), fov: 38 },
        { pos: P("deck", -2.4, 2.0, 4.4), target: P("deck", 0, 12, 0.4), fov: 42 },
      ] });
    },
    tokyo(dur) {
      const g = need(w, "tokyo"); stage(w, "tokyo", [], "city");
      const d = farPerson(w, "photographer", OFFDUTY(PEOPLE.maker), "tokyo");
      d.place(0, -2, 0); act(d, "phone"); d.expr = "smile";
      const flash = g.userData.flash;
      w.tick = (t) => { flash.intensity = (t % 3.1) < 0.12 ? 30 : 0; };
      return S.keys({ dur, keys: [
        { pos: P("tokyo", 0, -12, 1.4), target: P("tokyo", 0, 20, 14), fov: 46 },
        { pos: P("tokyo", 2.6, -5.6, 1.8), target: P("tokyo", 0, -2, 1.5), fov: 40 },
        { pos: P("tokyo", 1.2, -4.2, 1.6), target: P("tokyo", -2, 30, 20), fov: 50 },
      ] });
    },
    museum(dur) {
      need(w, "museum"); stage(w, "museum", [], "day");
      const d = farPerson(w, "visitor-a", OFFDUTY(PEOPLE.maker), "museum"), m = farPerson(w, "visitor-b", PEOPLE.parent, "museum");
      d.place(0.4, -8, 0); m.place(-0.4, -8, 0); d.expr = m.expr = "smile";
      d.walkTo(0.4, 2, 0.6); m.walkTo(-0.4, 2, 0.6);
      w.tick = (t) => { if (t > dur * 0.55) { d.face(-5, 6); m.face(-5, 6); act(m, "point"); } };
      return S.keys({ dur, keys: [
        { pos: P("museum", 8, -14, 3.0), target: P("museum", 0, -4, 1.4), fov: 42 },
        { pos: P("museum", 5, -4, 2.2), target: P("museum", -2, 3, 2.0), fov: 40 },
        { pos: P("museum", -1, -6, 1.4), target: P("museum", -4, 8, 3.2), fov: 44 },
      ] });
    },
    snow(dur) {
      need(w, "snow"); stage(w, "snow", [], "snow");
      const d = farPerson(w, "boarder-a", OFFDUTY(PEOPLE.maker), "snow"), m = farPerson(w, "boarder-b", PEOPLE.parent, "snow");
      d.ground = (x, y) => Math.max(0, y) * 0.28; m.ground = d.ground;
      d.place(1.2, 8, 180); m.place(-1.0, 9, 180); d.expr = m.expr = "wide";
      d.walkTo(1.0, 1, 1.0); m.walkTo(-1.2, 1.5, 1.0);
      w.tick = (t) => { act(d, t > dur * 0.6 ? "fall" : "flex"); act(m, t > dur * 0.6 ? "laugh" : "flex"); };
      return S.keys({ dur, keys: [
        { pos: P("snow", 6, -4, 2.4), target: P("snow", 0, 6, 2.6), fov: 42 },
        { pos: P("snow", 3.4, -3, 1.8), target: P("snow", 0, 3, 1.2), fov: 40 },
        { pos: P("snow", 0, -6, 3.0), target: P("snow", 0, 14, 6), fov: 46 },
      ] });
    },
    street(dur) {
      need(w, "street"); stage(w, "street", [], "night");
      const d = farPerson(w, "stroller-a", OFFDUTY(PEOPLE.maker), "street"), m = farPerson(w, "stroller-b", PEOPLE.parent, "street");
      d.place(0.35, -14, 0); m.place(-0.35, -14, 0); d.expr = m.expr = "smile";
      d.walkTo(0.35, 6, 0.55); m.walkTo(-0.35, 6, 0.55);
      w.tick = () => { if (!m.walk) act(m, "laugh"); };
      return S.keys({ dur, keys: [
        { pos: P("street", 0.9, -20, 1.5), target: P("street", 0, -12, 1.4), fov: 40 },
        { pos: P("street", 1.2, -8, 1.7), target: P("street", 0, -2, 1.4), fov: 40 },
        { pos: P("street", 0.6, 3, 2.4), target: P("street", 0, 12, 1.8), fov: 44 },
      ] });
    },
    tvroom(dur) {
      need(w, "tvroom"); stage(w, "tvroom", [], "lamp");
      const d = farPerson(w, "couch-a", OFFDUTY(PEOPLE.maker), "tvroom"), m = farPerson(w, "couch-b", PEOPLE.parent, "tvroom");
      for (const c of [d, m]) c.ground = () => 0.18;
      d.place(0.5, -0.55, 0); m.place(-0.45, -0.55, 0); act(d, "sit"); act(m, "sit"); d.expr = "far"; m.expr = "smile";
      w.tick = (t) => { if (t > dur * 0.5) { m.look = d.headWorld(); d.look = m.headWorld(); } };
      return S.keys({ dur, keys: [
        { pos: P("tvroom", 0.2, 2.6, 1.3), target: P("tvroom", 0, -0.6, 0.9), fov: 40 },
        { pos: P("tvroom", 1.6, 1.4, 1.2), target: P("tvroom", 0, -0.6, 0.95), fov: 36 },
        { pos: P("tvroom", 0.0, 1.2, 1.1), target: P("tvroom", 0, -0.6, 1.0), fov: 30 },
      ] });
    },
    worklamp(dur) {
      // the same room as "workbench": the lamp, the books, the late night
      stage(w, "bench", [], "lamp");
      const Q = w.places.bench.position;
      w.benchMaker.root.visible = true; act(w.benchMaker, "think"); w.benchMaker.expr = "far";
      w.tick = (t) => act(w.benchMaker, Math.floor(t / 5) % 2 ? "measure" : "think");
      return S.keys({ dur, keys: [
        { pos: Q.clone().add(V(2.4, -1.4, 1.6)), target: Q.clone().add(V(0.6, 1.4, 1.3)), fov: 40 },
        { pos: Q.clone().add(V(1.8, 0.2, 1.7)), target: Q.clone().add(V(0.6, 1.4, 1.5)), fov: 34 },
        { pos: Q.clone().add(V(-1.2, -1.2, 1.9)), target: Q.clone().add(V(-1.4, 2.9, 2.1)), fov: 40 },
      ] });
    },
    newstar(dur) {
      stage(w, "night", [], "night");
      const Q = w.places.night.position;
      const d = farPerson(w, "gazer-a", OFFDUTY(PEOPLE.maker), "night"), m = farPerson(w, "gazer-b", PEOPLE.parent, "night");
      d.place(0.4, 0.2, 0); m.place(-0.4, 0.2, 0); act(d, "idle"); act(m, "idle"); d.expr = "wide"; m.expr = "smile";
      const star = new THREE.Sprite(w.brightStar.material.clone()); star.material.color.set(0xffe2f0);
      const home = w.brightStar.getWorldPosition(new THREE.Vector3()).add(V(18, 0, -6));
      star.position.copy(home); star.scale.set(0.1, 0.1, 1); w.scene.add(star); w.temp.push(star);
      w.tick = (t) => {
        for (const c of [d, m]) c.head.rotation.x = -0.6;
        const s = Math.min(1, Math.max(0, (t - dur * 0.35) / (dur * 0.3))) * (9 + Math.sin(t * 3));
        star.scale.set(s, s, 1);
        if (t > dur * 0.6) { act(m, "cheer"); }
      };
      return S.keys({ dur, keys: [
        { pos: Q.clone().add(V(0.3, 3.4, 1.0)), target: Q.clone().add(V(0, 0, 1.3)), fov: 40 },
        { pos: Q.clone().add(V(0.2, -2.6, 1.3)), target: Q.clone().add(V(0, 2, 2.4)), fov: 44 },
        { pos: Q.clone().add(V(0, -2.4, 1.1)), target: home.clone().sub(Q).normalize().multiplyScalar(30).add(Q), fov: 48 },
      ] });
    },
    base(dur) {
      need(w, "base"); stage(w, "base", [], "rain");
      const d = farPerson(w, "rainwalker", OFFDUTY(PEOPLE.maker), "base");
      d.place(-6, -1, 90); d.expr = "far"; d.walkTo(5, 0.5, 0.75);
      const book = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.16, 0.05), w.mat("#3a6fd1")); d.hold("books", book, 1, [0, 0, -0.08]);
      return S.keys({ dur, keys: [
        { pos: P("base", -9, -7, 1.6), target: P("base", -4, 0, 1.4), fov: 42 },
        { pos: P("base", 0, -5.4, 1.5), target: P("base", 0, 0, 1.4), fov: 40 },
        { pos: P("base", 6, -6, 2.6), target: P("base", 2, 9, 5), fov: 46 },
      ] });
    },
    pumpkin(dur) {
      const g = need(w, "pumpkin"); stage(w, "pumpkin", [], "autumn");
      const d = farPerson(w, "carver-a", OFFDUTY(PEOPLE.maker), "pumpkin"), m = farPerson(w, "carver-b", PEOPLE.parent, "pumpkin"), b = farPerson(w, "baby", BABY, "pumpkin");
      d.place(0.9, -0.9, 30); m.place(-0.9, -0.9, -30); act(d, "sit"); act(m, "sit");
      for (const c of [d, m]) c.ground = () => -0.3 * c.k;
      d.place(0.9, -0.9, 30); m.place(-0.9, -0.9, -30);
      b.ground = () => 0.66; b.place(0, -0.05, 180); act(b, "sit"); b.expr = "wide";   // sitting in the big pumpkin's open top
      d.expr = m.expr = "smile";
      w.tick = (t) => { if (t > dur * 0.45) b.expr = "smile"; d.look = b.headWorld(); m.look = b.headWorld(); };
      return S.keys({ dur, keys: [
        // from above and in front, so the patch and the baby sit in the upper part of the frame, clear of the words
        { pos: P("pumpkin", 0, -4.6, 2.8), target: P("pumpkin", 0, 0.4, -0.1), fov: 42 },
        { pos: P("pumpkin", 0.5, -2.8, 2.0), target: P("pumpkin", 0, 0.2, 0.15), fov: 36 },
        { pos: P("pumpkin", 0.2, -2.0, 1.7), target: P("pumpkin", 0, 0.1, 0.25), fov: 32 },
      ] });
    },
    twostars(dur) {
      stage(w, "night", [], "night");
      const Q = w.places.night.position;
      const { m, a, r } = family(w, "night");
      w.tick = (t) => { for (const c of [m, a, r]) c.head.rotation.x = -0.6; };
      const home = w.brightStar.getWorldPosition(new THREE.Vector3());
      const stars = [V(16, 0, -6), V(-14, 4, -8)].map((o, k) => {
        const st = new THREE.Sprite(w.brightStar.material.clone()); st.material.color.set(k ? 0xd8f0ff : 0xffe2f0);
        st.position.copy(home).add(o); st.scale.set(8, 8, 1); w.scene.add(st); w.temp.push(st); return st;
      });
      w.tick = (t) => { for (const c of [m, a, r]) c.head.rotation.x = -0.6; stars.forEach((st, k) => { const s = 7 + 2 * Math.sin(t * (2 + k)); st.scale.set(s, s, 1); }); };
      return S.keys({ dur, keys: [
        { pos: Q.clone().add(V(0, -3.0, 1.0)), target: Q.clone().add(V(0, 0, 0.6)), fov: 40 },
        { pos: Q.clone().add(V(0, -2.4, 0.9)), target: home.clone().sub(Q).normalize().multiplyScalar(30).add(Q), fov: 50 },
      ] });
    },
    heavy(dur) {
      need(w, "shore"); stage(w, "shore", [], "rain");
      const d = farPerson(w, "alone", OFFDUTY(PEOPLE.maker), "shore");
      d.place(0, -3, 0); act(d, "crossed"); d.expr = "sad";
      w.tick = (t) => act(d, t > dur * 0.6 ? "facepalm" : "crossed");
      return S.keys({ dur, keys: [
        { pos: P("shore", 0, -14, 2.8), target: P("shore", 0, -3, 0.6), fov: 40 },
        { pos: P("shore", 2.4, -7.5, 2.0), target: P("shore", 0, -3, 0.9), fov: 36 },
        { pos: P("shore", 0.6, -5.4, 1.6), target: P("shore", 0, 40, 4), fov: 46 },
      ] });
    },
    lighthouse(dur) {
      stage(w, "sea", [], "night");
      const Q = w.places.sea.position;
      w.ship.visible = false;
      return S.keys({ dur, keys: [
        { pos: Q.clone().add(V(10, -12, 2.0)), target: Q.clone().add(V(-26, 34, 8)), fov: 40 },
        { pos: Q.clone().add(V(2, -4, 3.4)), target: Q.clone().add(V(-26, 34, 12)), fov: 34 },
      ] });
    },
  };
}

/** Every scene a page can be set in, for the Story Studio's picker: name, what it shows, and which book page it re-stages. */
export const SCENES: { name: string; label: string; group: string }[] = [
  { name: "stars", label: "A parent and two children on a blanket, the brightest star", group: "Bedtime" },
  { name: "workbench", label: "A workbench far away, under the lamp", group: "Bedtime" },
  { name: "letter", label: "A glowing story crossing the ocean at night", group: "Bedtime" },
  { name: "goodnight", label: "Goodnight: the blanket, the star over the house", group: "Bedtime" },
  { name: "sea", label: "The ship at dusk", group: "The sea" },
  { name: "blossoms", label: "Two people walking a cherry-blossom path", group: "Far away" },
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
  { name: "moonsea", label: "The open sea under a low moon, a ship's lights far off", group: "The sea" },
  { name: "bridge", label: "A ship's bridge at night: the wheel, the consoles, the windows", group: "The sea" },
  { name: "deck", label: "The deck by day: the anchor chain, the mooring lines, the crew", group: "The sea" },
  { name: "lighthouse", label: "A lighthouse across dark water", group: "The sea" },
  { name: "tokyo", label: "A city of lit towers at night, a camera's flash", group: "Far away" },
  { name: "museum", label: "Sculptures in green hills, two people walking", group: "Far away" },
  { name: "snow", label: "A snowy slope, two people falling and laughing", group: "Far away" },
  { name: "street", label: "A little street of lanterns at night", group: "Far away" },
  { name: "tvroom", label: "Two people on a couch in the television's light", group: "Far away" },
  { name: "worklamp", label: "Studying late under the lamp", group: "Far away" },
  { name: "base", label: "A rainy night outside a barracks", group: "Far away" },
  { name: "pumpkin", label: "A pumpkin patch at dusk, a baby in a tiny orange hat", group: "Far away" },
  { name: "newstar", label: "Two people under the stars as a new one appears", group: "Bedtime" },
  { name: "twostars", label: "The blanket, with two small stars beside the bright one", group: "Bedtime" },
  { name: "heavy", label: "A lone figure on a dark shore in the rain", group: "Far away" },
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
