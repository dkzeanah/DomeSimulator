// The episode engine. An episode is data (episodes/<id>.json): a list of beats -- scenes, lines,
// walks, actions, camera shots, cards, meme hits, sound cues. The engine plays them on one virtual
// clock, which gives three ways to run the same episode:
//
//   compile   a silent fast run with nothing drawn: every beat's start and end, the shots, the
//             runtime -- the timeline, before a frame is rendered;
//   seek      the same silent run, stopped at any moment, then one frame drawn: scrub anywhere;
//   play      real time from wherever it stands, with the voices and music sounding;
//   render    every frame at 1920x1080 streamed to ffmpeg, the soundtrack mixed offline.
//
// Lines are timed by their voices (Edge TTS, fetched first), so the timeline is the real cut.

import { Character, Voices } from "/static/cast.js";
import { makeShots, fovForLens, fmtTime } from "/static/cine.js";
import { clock } from "/static/clock.js";
import { Band } from "/static/band.js";

const FPS = 30;
const r1 = (x) => (Math.round(x * 10) / 10).toFixed(1);
export function words(n) {
  const ones = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen",
                "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"];
  const tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"];
  n = Math.round(n);
  if (n < 20) return ones[n];
  if (n < 100) return tens[Math.floor(n / 10)] + (n % 10 ? "-" + ones[n % 10] : "");
  if (n < 1000) return ones[Math.floor(n / 100)] + " hundred" + (n % 100 ? " and " + words(n % 100) : "");
  return String(n);
}
const spoken = (x) => { const [a, b] = r1(x).split("."); return `${words(+a)} point ${words(+b)}`; };
const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);

export const SHOT_KINDS = ["single", "two", "ots", "wide", "move"];
export const MOVES = ["hold", "dollyIn", "dollyOut", "orbit", "slide", "pan", "crane", "pedestal", "dollyZoom", "reveal", "flyover", "spiral"];
export const ACTS = ["idle", "talk", "point", "wave", "shrug", "hips", "think", "facepalm", "cheer", "laugh", "hammer", "carry", "lift",
                     "crank", "measure", "flex", "grunt", "peek", "phone", "sit", "fall"];

export class Engine {
  constructor(world, cine, set, series, figures) {
    this.w = world; this.cine = cine; this.set = set; this.series = series; this.T = world.THREE;
    this.shots = makeShots(this.T);
    this.voices = new Voices(cine);
    this.events = [];
    this.band = new Band(this.voices, { audible: () => this.mode === "play", log: (fn, args) => this.events.push({ kind: "band", fn, args, t: clock.now() / 1000 }) });
    this.cast = {};
    this.figures = figures;
    this.mode = "idle";
    this.timeScale = 1;
    this.fill = new this.T.DirectionalLight(0xfff1e0, 1.1);
    world.scene.add(this.fill, this.fill.target);
    world.hooks.push((dt, now) => {
      for (const c of Object.values(this.cast)) c.update(dt, now);
      this.set.update(dt);
      const cam = world.persp, d = new this.T.Vector3();
      cam.getWorldDirection(d);
      this.fill.position.copy(cam.position).add(new this.T.Vector3(0, 0, 1.5));
      this.fill.target.position.copy(cam.position).addScaledVector(d, 4);
    });
    this.tokens = this.makeTokens(figures);
  }

  makeTokens(f) {
    return { bevel: r1(f.bevel), bevel_spoken: spoken(f.bevel), fold: r1(f.fold), fold_spoken: spoken(f.fold), tail: r1(f.tail),
             panels: String(f.panels), panels_words: cap(words(f.panels)), sticks_words: words(f.sticks), cuts_words: words(f.cuts),
             sqft: String(Math.round(f.floor_m2 * 10.7639)), sqft_words: cap(words(Math.round(f.floor_m2 * 10.7639))),
             ft_words: words(Math.round(f.diameter_m / 0.3048)) };
  }
  fillText(s) { return (s || "").replace(/\{(\w+)\}/g, (m, k) => this.tokens[k] ?? m); }

  // ------------------------------------------------------------ the cast
  spawn() {
    for (const c of Object.values(this.cast)) this.w.scene.remove(c.root);
    this.cast = {};
    for (const [id, def] of Object.entries(this.series.cast)) {
      const c = new Character(this.T, id, def, this.w.scene);
      c.ground = (x, y) => this.cine.floorAt(x, y);
      c.root.visible = false;
      this.cast[id] = c;
    }
  }

  // ------------------------------------------------------------ places and points
  point(p) {
    const V = (x, y, z) => new this.T.Vector3(x, y, z), G = this.set.ground, s = this.set;
    if (Array.isArray(p)) return V(p[0], p[1], p[2] ?? G + 1.2);
    if (this.cast[p]) return this.cast[p].headWorld();
    return ({ jig: () => s.jigCentre(), jigHigh: () => s.jigCentre().add(V(0.6, 0, 0.5)), saw: () => V(s.sawAt[0], s.sawAt[1], G + 0.9),
              dome: () => V(0, 0, 1.3), door: () => V(0, this.w.S.data.landmarks.door[1], 1.0), patio: () => V(0, 8.2, G + 1.1),
              hedge: () => V(s.hedgeX, 0.5, G + 1.3) }[p] || (() => V(0, 0, 1.2)))();
  }

  // ------------------------------------------------------------ keeping the subject in sight
  meshesForRays() {
    const out = [];
    const visible = (o) => { for (let p = o; p; p = p.parent) if (!p.visible) return false; return true; };
    this.w.scene.traverse((o) => {
      if (!o.isMesh || o.material?.side === this.T.BackSide || o.material?.transparent) return;
      if (o.geometry?.type === "CircleGeometry") return;                 // the lawn
      if (visible(o)) out.push(o);
    });
    return out;
  }
  ownedBy(o, chars) { for (let p = o; p; p = p.parent) if (chars.some((c) => c.root === p)) return true; return false; }
  /** Move a camera round its subject (and up a little) until nothing stands between them. */
  unblock(pos, target, subjects) {
    const ray = new this.T.Raycaster(), meshes = this.meshesForRays(), chars = subjects.map((w) => this.cast[w]).filter(Boolean);
    const blocked = (p) => {
      const d = p.clone().sub(target), L = d.length();
      ray.set(target, d.normalize()); ray.far = L;
      return ray.intersectObjects(meshes, false).some((h) => h.distance > 0.25 && h.distance < L - 0.15 && !this.ownedBy(h.object, chars));
    };
    if (!blocked(pos)) return pos;
    const rel = pos.clone().sub(target);
    for (const lift of [0, 0.35, 0.8]) for (const a of [25, -25, 50, -50, 80, -80, 120, -120]) for (const k of [1, 0.75, 1.3]) {
      const r = rel.clone().multiplyScalar(k).applyAxisAngle(new this.T.Vector3(0, 0, 1), a * Math.PI / 180);
      const p = target.clone().add(r); p.z += lift;
      if (!blocked(p)) return p;
    }
    return pos;
  }

  // ------------------------------------------------------------ cameras from where the cast stands
  camera(spec, dur) {
    const k = spec.kind, V = (x, y, z) => new this.T.Vector3(x, y, z);
    if (k === "single") return this.camSingle(spec.who, spec.toward ? this.cast[spec.toward] : null, spec, dur);
    if (k === "two") return this.camTwo(spec.a, spec.b, spec, dur);
    if (k === "ots") return this.camOts(spec.over, spec.at, spec, dur);
    if (k === "wide") {
      const pts = (spec.who || []).map((w) => this.cast[w].chestWorld());
      if (spec.at) pts.push(this.point(spec.at));
      return this.camWide(pts.length ? pts : [V(0, 0, 1.2)], V(...(spec.dir || [0, 1, -0.3])), spec.lens || 28, dur);
    }
    if (k === "move") {
      const o = { ...spec, dur, fov: fovForLens(spec.lens || 35) };
      if (spec.from) o.from = this.point(spec.from);
      else o.from = this.w.persp.position.clone();
      o.subject = this.point(spec.subject || "dome");
      return this.shots[spec.move || "hold"](o);
    }
    return null;
  }
  camSingle(who, toward, { size = "medium", side = 1, lens } = {}, dur) {
    const c = this.cast[who], h = c.headWorld(), fwd = new this.T.Vector3(-Math.sin(c.yaw), Math.cos(c.yaw), 0);
    let dir = fwd.clone();
    if (toward) { const t = toward.headWorld().sub(h); t.z = 0; t.normalize(); dir = fwd.clone().add(t).normalize(); }
    const perp = new this.T.Vector3(dir.y, -dir.x, 0).multiplyScalar(side * 0.35);
    const dist = { close: 1.45, medium: 2.5, wide: 4.2 }[size] || 2.5;
    const pos = h.clone().addScaledVector(dir.clone().add(perp).normalize(), dist); pos.z = h.z - (size === "close" ? 0.05 : 0.15);
    const target = h.clone(); target.z -= size === "close" ? 0.06 : 0.22;
    const from = this.unblock(pos, target, [who]);
    return this.shots.hold({ from, subject: target, fov: fovForLens(lens || (size === "close" ? 85 : size === "medium" ? 50 : 35)), drift: 0.06, dur });
  }
  camTwo(a, b, { dist = 3.2, lens = 35, side = 1, height = 0 } = {}, dur) {
    const A = this.cast[a].chestWorld(), B = this.cast[b].chestWorld(), mid = A.clone().add(B).multiplyScalar(0.5);
    const ab = B.clone().sub(A); ab.z = 0;
    const n = new this.T.Vector3(-ab.y, ab.x, 0).normalize().multiplyScalar(side);
    // the side the pair are both facing, if they are
    const fa = new this.T.Vector3(-Math.sin(this.cast[a].yaw), Math.cos(this.cast[a].yaw), 0);
    if (fa.dot(n) < -0.2 && side === 1) n.negate();
    const pos = mid.clone().addScaledVector(n, Math.max(dist, ab.length() * 1.6)); pos.z = mid.z + 0.25 + height;
    const subject = mid.clone().add(new this.T.Vector3(0, 0, 0.1));
    return this.shots.hold({ from: this.unblock(pos, subject, [a, b]), subject, fov: fovForLens(lens), drift: 0.08, dur });
  }
  camOts(over, at, { lens = 50 } = {}, dur) {
    const O = this.cast[over].headWorld(), A = this.cast[at].headWorld(), d = A.clone().sub(O); d.z = 0; d.normalize();
    const pos = O.clone().addScaledVector(d, -0.75).add(new this.T.Vector3(d.y * 0.35, -d.x * 0.35, 0.08));
    const subject = A.clone().add(new this.T.Vector3(0, 0, -0.1));
    return this.shots.hold({ from: this.unblock(pos, subject, [over, at]), subject, fov: fovForLens(lens), drift: 0.05, dur });
  }
  camWide(points, dir, lens, dur) {
    const c = points.reduce((a, p) => a.add(p), new this.T.Vector3()).multiplyScalar(1 / points.length);
    let r = 0; for (const p of points) r = Math.max(r, p.distanceTo(c));
    const d = dir.clone().normalize(), dist = (r + 1.2) / Math.tan(fovForLens(lens) * Math.PI / 360);
    return this.shots.hold({ from: c.clone().addScaledVector(d, -dist), subject: c, fov: fovForLens(lens), drift: 0.1, dur });
  }
  label(spec) {
    if (!spec) return "";
    if (spec.kind === "single") return `${spec.size || "medium"} ${spec.who}${spec.toward ? " to " + spec.toward : ""}`;
    if (spec.kind === "two") return `two-shot ${spec.a} & ${spec.b}`;
    if (spec.kind === "ots") return `over ${spec.over} on ${spec.at}`;
    if (spec.kind === "wide") return `wide ${(spec.who || []).join(", ")}`;
    if (spec.kind === "move") return `${spec.move}${typeof spec.subject === "string" ? " on " + spec.subject : ""}`;
    return spec.kind;
  }
  shoot(spec, dur, beat) {
    const shot = this.camera(spec, dur);
    if (!shot) return;
    this.cine.play({ ...shot, dur });
    this.shotLog.push({ t: clock.now() / 1000, dur, label: this.label(spec), lens: spec.lens || null, kind: spec.kind, move: spec.move, beat });
  }

  // ------------------------------------------------------------ the beats
  wait(s) { return clock.wait(s / Math.max(this.timeScale, 1e-6)); }

  async say(ch, text) {
    let buf = null;
    try { buf = await this.voices.fetchLine(ch.def, text); } catch { buf = null; }
    const dur = buf ? buf.duration : 0.4 + text.length * 0.055, t0 = clock.now();
    if (buf) {
      this.events.push({ kind: "voice", buf, t: t0 / 1000, dur });
      if (this.mode === "play") this.playBuffer(buf, 0);
    }
    const env = buf ? this.voices.envelope(buf) : null;
    ch.speaking = true;
    ch.talkFn = env ? (now) => env[Math.min(env.length - 1, Math.floor((now - t0) / 1000 * 60))] || 0 : null;
    await clock.wait(dur);
    ch.speaking = false; ch.talkFn = null; ch.talk = 0;
  }
  playBuffer(buf, offset) {
    const ac = this.voices.ac, s = ac.createBufferSource(); s.buffer = buf; s.connect(this.voices.master);
    s.start(ac.currentTime + 0.01, Math.max(0, offset));
    (this.live ||= new Set()).add(s); s.onended = () => this.live.delete(s);
  }

  async beat(b, i, g) {
    const c = this.cast, w = this.w, cine = this.cine;
    const W = async (p) => { const r = await p; if (g !== this.gen) throw new Error("stopped"); return r; };
    const mark = { i, k: b.k, t0: clock.now() / 1000 };
    switch (b.k) {
      case "scene": {
        this.sceneLog.push({ t: mark.t0, name: b.name, i });
        cine.stop();
        for (const ch of Object.values(c)) { ch.root.visible = false; ch.look = null; ch.do("idle"); ch.drop("phone"); }
        for (const [who, p] of Object.entries(b.place || {})) { c[who].place(...p); c[who].root.visible = true; }
        for (const who of b.hide || []) c[who].root.visible = false;
        if (b.view) w.setView(b.view);
        if (b.sun) w.placeSun(...b.sun);
        if (b.panelOnBench !== undefined) this.set.showPanelOnBench(b.panelOnBench);
        // a scene opens on a wide of whoever is in it, until a shot says otherwise
        const who = Object.keys(b.place || {});
        if (who.length) this.shoot({ kind: "wide", who, dir: [0.2, 1, -0.25], lens: 28 }, 2.0, i);
        break;
      }
      case "line": {
        const ch = c[b.who], text = this.fillText(b.text);
        const others = b.listeners ?? Object.keys(c).filter((k) => k !== b.who && c[k].root.visible && c[k].root.position.distanceTo(ch.root.position) < 7);
        for (const o of others) c[o].look = ch.headWorld();
        if (b.act) ch.do(b.act);
        if (b.act === "phone") this.set.phone(ch);
        const buf = await W(this.voices.fetchLine(ch.def, text).catch(() => null));
        const dur = (buf ? buf.duration : 0.4 + text.length * 0.055) + (b.pad ?? 0.25);
        if (b.cam) this.shoot(b.cam, dur + 0.15, i);
        cine.subtitle = { name: ch.def.name.split(" ")[0], text };
        mark.who = b.who; mark.text = text;
        await W(this.say(ch, text));
        cine.subtitle = null;
        if (b.after) ch.do(b.after); else if (b.act === "talk" || !b.act) ch.do("idle");
        await W(this.wait(b.pad ?? 0.25));
        break;
      }
      case "walk": {
        const p = b.to, go = c[b.who].walkTo(p[0], p[1], b.speed || 1.3);
        mark.who = b.who;
        if (b.wait) await W(go);
        break;
      }
      case "act": c[b.who].do(b.act); if (b.act === "phone") this.set.phone(c[b.who]); mark.who = b.who; break;
      case "face": { const p = this.point(b.at); c[b.who].face(p.x, p.y); mark.who = b.who; break; }
      case "cam": { this.shoot(b.cam, b.dur || 3, i); if (b.wait) await W(this.wait(b.dur || 3)); break; }
      case "wait": await W(this.wait(b.s || 1)); break;
      case "sfx": this.band[b.name]?.(); break;
      case "music": this.band[b.name]?.(b.bars); break;
      case "view": w.setView(b.view); break;
      case "build": {
        for (let s = b.from; s <= b.to; s++) { w.setView({ step: s }); await W(this.wait(b.every || 0.5)); }
        break;
      }
      case "lower": { const d = c[b.who].def; cine.title(d.name, d.role, 3800, "lower"); break; }
      case "figure": cine.title(this.fillText(b.big), this.fillText(b.small), (b.secs || 4) * 1000, "figure"); break;
      case "card": {
        this.band.whoosh();
        let len = b.secs || 3;
        if (b.music === "theme") len = Math.max(len, this.band.theme(2));
        if (b.music === "sting") len = Math.max(len, this.band.sting() + 1.2);
        cine.title(this.fillText(b.text), this.fillText(b.sub), len * 1000, "card");
        mark.secs = len;
        await W(this.wait(len));
        break;
      }
      case "gag": {
        if (b.name === "tiltBlade") this.set.tiltBlade(b.deg, b.secs || 2);
        if (b.name === "handPanel") this.set.handPanel(c[b.who]);
        if (b.name === "burstPanel") this.set.burstPanel();
        if (b.name === "resetPanel") this.set.resetPanel();
        break;
      }
      case "meme": await W(this.meme(b, W)); break;
      case "credits": {
        const names = Object.values(this.series.cast).map((d) => d.name).join(" · ");
        cine.title(this.series.title.toUpperCase(), `${names}   |   made in Dome Sketch (sketch-claude); every figure from the model`, (b.secs || 6) * 1000, "card");
        this.band.theme(1);
        await W(this.wait(b.secs || 6));
        break;
      }
    }
    mark.t1 = clock.now() / 1000;
    this.marks.push(mark);
  }

  async meme(b, W = (p) => p) {
    const cine = this.cine, secs = b.secs || 2, text = this.fillText(b.text);
    if (b.sfx) this.band[b.sfx]?.();
    if (b.style === "freeze") {
      // everything holds, the picture drains of colour, the narrator's caption comes up
      this.timeScale = 0; cine.freeze = true;
      cine.title(text, "", secs * 1000, "freeze");
      await W(clock.wait(secs));
      this.timeScale = 1; cine.freeze = false;
    } else if (b.style === "zoom") {
      // a hard punch-in on a face with a shake, the reaction-shot meme
      const ch = this.cast[b.who], from = this.w.persp.position.clone(), h = ch.headWorld();
      const close = h.clone().add(from.clone().sub(h).normalize().multiplyScalar(0.9)); close.z = h.z;
      const fov0 = this.w.persp.fov;
      cine.play({ dur: secs, at: (t) => {
        const e = Math.min(1, t * secs / 0.12), shake = (1 - t) * 0.012;
        return { pos: from.clone().lerp(close, e).add(new this.T.Vector3(Math.sin(t * 90) * shake, 0, Math.cos(t * 70) * shake)),
                 target: h, fov: fov0 + (fovForLens(85) - fov0) * e, roll: Math.sin(t * 60) * 0.02 * (1 - t) };
      } });
      if (text) cine.title(text, "", secs * 1000, "caption");
      this.shotLog.push({ t: clock.now() / 1000, dur: secs, label: `punch-in ${b.who}`, kind: "meme" });
      await W(this.wait(secs));
    } else {
      cine.title(text, "", secs * 1000, b.style === "pov" ? "pov" : "caption");
      await W(this.wait(secs));
    }
  }

  check(g) { if (this.stopped || (g !== undefined && g !== this.gen)) throw new Error("stopped"); }

  // ------------------------------------------------------------ running
  resetRun() {
    this.stopped = false; this.marks = []; this.shotLog = []; this.sceneLog = []; this.events = [];
    for (const s of this.live || []) { try { s.stop(); } catch { /* done */ } }
    this.live = new Set();
    this.cine.stop(); this.cine.titles = []; this.cine.subtitle = null; this.cine.freeze = false; this.cine.time = 0;
    this.timeScale = 1;
    this.gen = (this.gen || 0) + 1;          // whatever was running before is dropped, never woken
    clock.offline = true; clock.t = 0; clock.timers = [];
    this.spawn(); this.set.reset();
  }

  async runBeats(beats) {
    const g = this.gen;
    for (let i = 0; i < beats.length; i++) { this.check(g); this.cur = i; await this.beat(beats[i], i, g); }
  }

  async preload(beats, onProgress) {
    const lines = beats.filter((b) => b.k === "line");
    let n = 0;
    await Promise.all(lines.map(async (b) => { await this.voices.fetchLine(this.series.cast[b.who], this.fillText(b.text)).catch(() => null); onProgress?.(++n, lines.length); }));
  }

  // advance the world by one frame of virtual time
  async frame(draw, light = false) {
    await clock.advance(1000 / FPS, light ? 1 : 4);
    const dt = (1 / FPS) * this.timeScale;
    if (draw) this.w.renderFrame(dt, clock.now()); else this.w.step(dt, clock.now());
  }

  /** The silent run: every beat's timing, the shots and the scenes. Stops at ``until`` seconds if given. */
  async simulate(beats, { until = Infinity, onFrame } = {}) {
    this.mode = "dry";
    this.resetRun();
    let done = false, err = null;
    const run = this.runBeats(beats).then(() => (done = true), (e) => { err = e; done = true; });
    let n = 0;
    while (!done && clock.t / 1000 < until - 1e-6) {
      await this.frame(false, true);
      if (onFrame) await onFrame(clock.t / 1000);
      if (++n > FPS * 60 * 20) throw new Error("the episode ran past twenty minutes");
    }
    if (err && err.message !== "stopped") throw err;
    this.pending = done ? null : run;
    return { done, t: clock.t / 1000 };
  }

  async compile(beats, onStatus) {
    onStatus?.("Fetching the voices...");
    await this.preload(beats, (i, n) => onStatus?.(`Fetching the voices: ${i} of ${n}`));
    onStatus?.("Timing the episode...");
    const wall = performance.now();
    await this.simulate(beats);
    const total = clock.t / 1000;
    const timeline = {
      total, marks: this.marks.slice(), shots: this.shotLog.slice(), scenes: this.sceneLog.slice(),
      events: this.events.map((e) => ({ kind: e.kind, fn: e.fn, t: e.t, dur: e.dur ?? this.band.length[e.fn]?.(...(e.args || [])) ?? 0.4 })),
      took: (performance.now() - wall) / 1000,
    };
    for (let i = 0; i < timeline.shots.length; i++) {
      const s = timeline.shots[i], next = timeline.shots[i + 1];
      s.end = Math.min(next ? next.t : total, s.t + s.dur);
      s.shown = (next ? next.t : total) - s.t;
    }
    timeline.shots = timeline.shots.filter((s) => s.shown > 0.05);
    for (let i = 0; i < timeline.scenes.length; i++) timeline.scenes[i].end = timeline.scenes[i + 1]?.t ?? total;
    this.timeline = timeline;
    this.idle();
    return timeline;
  }

  idle() { this.mode = "idle"; clock.offline = true; }

  async seek(beats, t) {
    this.pause();
    const r = await this.simulate(beats, { until: t });
    this.mode = "paused";
    this.w.renderFrame(0, clock.now());
    return r;
  }

  async play(beats, from, onTick) {
    // run on from the current point in real time; voices already mid-line pick up where they are
    if (this.mode !== "paused" || Math.abs(clock.t / 1000 - from) > 0.05) await this.seek(beats, from);
    await this.voices.ac.resume();
    const now = clock.t / 1000;
    for (const e of this.events) if (e.kind === "voice" && e.t <= now && e.t + e.dur > now) { this.mode = "play"; this.playBuffer(e.buf, now - e.t); }
    this.mode = "play";
    let last = performance.now();
    const pending = this.pending;
    let ended = !pending;
    pending?.then(() => (ended = true), () => (ended = true));
    return new Promise((resolve) => {
      const step = async (ts) => {
        if (this.mode !== "play") return resolve("paused");
        const dt = Math.min(0.1, (ts - last) / 1000); last = ts;
        await clock.advance(dt * 1000, 2);
        this.w.renderFrame(dt * this.timeScale, clock.now());
        onTick?.(clock.t / 1000);
        if (ended) { this.mode = "paused"; return resolve("ended"); }
        requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    });
  }

  pause() {
    if (this.mode === "play") this.mode = "paused";
    for (const s of this.live || []) { try { s.stop(); } catch { /* done */ } }
    this.live = new Set();
  }

  /** A strip of thumbnails, one at each shot, in a single silent pass. */
  async storyboard(beats, times, size = [256, 108], onThumb) {
    const out = [];
    let k = 0;
    const W = this.w, canvas = W.canvas;
    await this.simulate(beats, { onFrame: async (t) => {
      while (k < times.length && t >= times[k]) {
        W.renderFrame(0, clock.now());
        const c = document.createElement("canvas"); c.width = size[0]; c.height = size[1];
        const g = c.getContext("2d"), sw = canvas.width, sh = canvas.height, want = size[0] / size[1];
        let cw = sw, ch = sw / want; if (ch > sh) { ch = sh; cw = sh * want; }
        g.drawImage(canvas, (sw - cw) / 2, (sh - ch) / 2, cw, ch, 0, 0, size[0], size[1]);
        out.push(c.toDataURL("image/jpeg", 0.7));
        onThumb?.(k, out[k]);
        k++;
      }
    } });
    this.idle();
    return out;
  }

  /** The frame-accurate render: 1920x1080, every frame to ffmpeg, the soundtrack mixed offline. */
  async render(beats, meta, onStatus, draft = false) {
    const W = this.w, cine = this.cine;
    await this.preload(beats);
    const job = await W.api("/api/render/start", { slug: meta.slug, fps: FPS, draft });
    const saved = { aspect: cine.aspect, pr: W.renderer.getPixelRatio(), w: W.canvas.clientWidth, h: W.canvas.clientHeight };
    W.renderer.setPixelRatio(1); W.resize(1920, 1080);
    cine.aspect = "2.39"; cine.capturing = true;
    this.resetRun();
    this.mode = "render";
    let done = false, failed = null, frames = 0;
    this.runBeats(beats).then(() => (done = true), (e) => { failed = e; done = true; });
    const inflight = [], wall = performance.now();
    try {
      while (!done) {
        await this.frame(true);
        const blob = await new Promise((r) => cine.program.toBlob(r, "image/jpeg", 0.92));
        inflight.push(sendFrame(`/api/render/frame?id=${job.id}&n=${frames}`, blob));
        if (inflight.length > 3) await inflight.shift();
        frames++;
        if (frames % FPS === 0) onStatus?.(`Rendering ${fmtTime(frames / FPS)} of ${fmtTime(this.timeline?.total || 0)} (${(frames / ((performance.now() - wall) / 1000)).toFixed(1)} fps)`, frames / FPS);
        if (this.stopped) throw new Error("stopped");
      }
      await Promise.all(inflight);
      if (failed) throw failed;
      onStatus?.("Mixing the soundtrack...");
      const wav = await this.soundtrack(frames / FPS);
      const body = { id: job.id, draft, ...meta, srt: srt(this.marks.filter((m) => m.k === "line"), this.series),
                     scenes: this.sceneLog.map((s) => ({ t: s.t, name: s.name })) };
      const m = new TextEncoder().encode(JSON.stringify(body));
      const head = new Uint8Array(4); new DataView(head.buffer).setUint32(0, m.length, true);
      onStatus?.("Encoding the cut, the phone cut and the thumbnails...");
      const res = await fetch("/api/render/finish", { method: "POST", body: new Blob([head, m, wav]) }).then((r) => r.json());
      onStatus?.(res.folder ? `Rendered: ${res.folder}` : `Encoding failed: ${res.error || (res.errors || []).join(" ")}`);
      return res;
    } catch (e) {
      onStatus?.(`Render stopped: ${e.message}`);
      fetch(`/api/render/abort?id=${job.id}`, { method: "POST", body: "{}" });
      return null;
    } finally {
      cine.capturing = false; cine.aspect = saved.aspect;
      W.renderer.setPixelRatio(saved.pr); W.resize(saved.w, saved.h);
      this.idle();
    }
  }

  async soundtrack(seconds) {
    const sr = 48000, off = new OfflineAudioContext(2, Math.ceil(sr * (seconds + 1)), sr);
    const master = off.createGain(); master.connect(off.destination);
    const band = new Band({ ac: off, master });
    for (const e of this.events) {
      if (e.kind === "voice") { const s = off.createBufferSource(); s.buffer = e.buf; s.connect(master); s.start(e.t); }
      else { band.at = e.t + 0.02; band[e.fn](...(e.args || [])); }
    }
    return wavBytes(await off.startRendering());
  }
}

async function sendFrame(url, blob) {
  // a frame that fails to arrive is sent again: one dropped request must not end a long render
  for (let k = 0; ; k++) {
    try {
      const r = await fetch(url, { method: "POST", body: blob });
      if (r.ok) return r;
      if (k >= 4) throw new Error(`the server refused a frame: ${r.status} ${await r.text()}`);
    } catch (e) { if (k >= 4) throw e; }
    await new Promise((res) => setTimeout(res, 300 * (k + 1)));
  }
}

export function wavBytes(buf) {
  const ch = buf.numberOfChannels, n = buf.length, sr = buf.sampleRate, out = new DataView(new ArrayBuffer(44 + n * ch * 2));
  const w = (o, s) => { for (let i = 0; i < s.length; i++) out.setUint8(o + i, s.charCodeAt(i)); };
  w(0, "RIFF"); out.setUint32(4, 36 + n * ch * 2, true); w(8, "WAVE"); w(12, "fmt "); out.setUint32(16, 16, true);
  out.setUint16(20, 1, true); out.setUint16(22, ch, true); out.setUint32(24, sr, true); out.setUint32(28, sr * ch * 2, true);
  out.setUint16(32, ch * 2, true); out.setUint16(34, 16, true); w(36, "data"); out.setUint32(40, n * ch * 2, true);
  const data = [...Array(ch)].map((_, c) => buf.getChannelData(c));
  let o = 44;
  for (let i = 0; i < n; i++) for (let c = 0; c < ch; c++) { out.setInt16(o, Math.max(-1, Math.min(1, data[c][i])) * 32767, true); o += 2; }
  return new Blob([out.buffer], { type: "audio/wav" });
}

export function srt(lines, series) {
  const ts = (s) => { const ms = Math.round(s * 1000), h = Math.floor(ms / 3600000), m = Math.floor(ms / 60000) % 60, sec = Math.floor(ms / 1000) % 60;
                      return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")},${String(ms % 1000).padStart(3, "0")}`; };
  return lines.map((l, i) => `${i + 1}\n${ts(l.t0)} --> ${ts(l.t1)}\n${series.cast[l.who].name.split(" ")[0].toUpperCase()}: ${l.text}\n`).join("\n");
}
