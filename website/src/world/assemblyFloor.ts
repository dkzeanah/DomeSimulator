// The Dome Assembly Line's factory floor, as the desktop demo (assembly_line.py) runs it: a carriage
// carries the unit from station to station round the line; at each station its crew walks each
// element from the stockpile to where it goes and places it, taking that element's own install
// time (al_build's labor minutes, shown at assembly_line's PLACE_ANIM_PER_LABOR_MIN); a disruption
// stalls the station or takes a worker away; at the end a gantry crane hooks the finished unit by
// its apex, lifts it, carries it in and lowers it onto the turntable in the middle, which keeps
// turning; and every finished unit joins the yard. The unit's money, labor, steps and distance
// accrue as the elements are placed (ProductionRun). The scene is drawn small -- the units at
// SCALE_FT_PER_M -- so the whole line fits the space; every figure is al_build's.

import * as THREE from "three";
import type { Element, Factory, Phase, Run, YardRecord } from "./assembly";
import { phasesFor } from "./assembly";

/** The units on the line, drawn this many feet to the metre (1 : 5.5). */
export const SCALE_FT_PER_M = 0.6;
const LINE_R = 23, YARD_R = 33.5, GROUND = -1.2;        // the stage sits on the pedestal, 1.2 ft up
const ARC0 = (25 * Math.PI) / 180, ARC1 = (315 * Math.PI) / 180, PICKUP = (338 * Math.PI) / 180;
const at = (a: number, r: number) => new THREE.Vector3(Math.sin(a) * r, 0, Math.cos(a) * r);

interface Buffers { pos: Int16Array; col: Uint8Array; alpha: Uint8Array; opaque: Uint16Array; transparent: Uint16Array }
const meshCache = new Map<string, Promise<Buffers>>();
export function loadBuffers(run: Run): Promise<Buffers> {
  const h = run.mesh;
  let p = meshCache.get(h.file);
  if (!p) {
    p = fetch(h.file).then((r) => { if (!r.ok) throw new Error(`${h.file}: ${r.status}`); return r.arrayBuffer(); }).then((buf) => {
      const V = h.vertices;
      let off = V * 6 + V + V;
      off += off % 2;
      return { pos: new Int16Array(buf, 0, V * 3), col: new Uint8Array(buf, V * 6, V), alpha: new Uint8Array(buf, V * 7, V),
        opaque: new Uint16Array(buf, off, h.opaque), transparent: new Uint16Array(buf, off + h.opaque * 2, h.transparent) };
    });
    p.catch(() => meshCache.delete(h.file));
    meshCache.set(h.file, p);
  }
  return p;
}

/** A unit's whole mesh at the floor's scale, metres -> feet, z up -> y up; drawn up to what is built. */
function unitMesh(run: Run, b: Buffers) {
  const h = run.mesh, k = SCALE_FT_PER_M;
  const pos = new Float32Array(h.vertices * 3), col = new Float32Array(h.vertices * 3);
  for (let i = 0; i < h.vertices; i++) {
    pos[i * 3] = b.pos[i * 3] * h.scale * k; pos[i * 3 + 1] = b.pos[i * 3 + 2] * h.scale * k; pos[i * 3 + 2] = -b.pos[i * 3 + 1] * h.scale * k;
    const c = h.palette[b.col[i]] || [0.8, 0.6, 0.4];
    col[i * 3] = c[0]; col[i * 3 + 1] = c[1]; col[i * 3 + 2] = c[2];
  }
  const geo = (idx: Uint16Array) => {
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    g.setAttribute("color", new THREE.BufferAttribute(col, 3));
    g.setIndex(new THREE.BufferAttribute(new Uint16Array(idx), 1));
    g.computeVertexNormals();
    return g;
  };
  const group = new THREE.Group();
  const solid = new THREE.Mesh(geo(b.opaque), new THREE.MeshLambertMaterial({ vertexColors: true, flatShading: true, side: THREE.DoubleSide }));
  const glass = new THREE.Mesh(geo(b.transparent), new THREE.MeshLambertMaterial({ vertexColors: true, transparent: true, opacity: 0.45, side: THREE.DoubleSide, depthWrite: false }));
  solid.castShadow = true;
  solid.userData.part = { id: `unit:${run.serial}`, name: `${run.model}, a ${run.name.toLowerCase()} (#${run.serial})` };
  group.add(solid, glass);
  let top = 0;
  for (let i = 0; i < h.vertices; i++) top = Math.max(top, pos[i * 3 + 1]);
  return { group, solid, glass, top };
}

const box = (w: number, h: number, d: number, colour: string) => new THREE.Mesh(new THREE.BoxGeometry(w, h, d), new THREE.MeshLambertMaterial({ color: colour, flatShading: true }));

function worker(colour: string) {
  const g = new THREE.Group(), k = SCALE_FT_PER_M;
  const body = new THREE.Mesh(new THREE.CylinderGeometry(0.22 * k, 0.26 * k, 1.1 * k, 8), new THREE.MeshLambertMaterial({ color: colour }));
  body.position.y = 0.75 * k;
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.17 * k, 8, 6), new THREE.MeshLambertMaterial({ color: "#d8a47e" }));
  head.position.y = 1.5 * k;
  const hat = new THREE.Mesh(new THREE.SphereGeometry(0.18 * k, 8, 4, 0, Math.PI * 2, 0, Math.PI / 2), new THREE.MeshLambertMaterial({ color: "#f2c230" }));
  hat.position.y = 1.56 * k;
  const load = box(0.5 * k, 0.25 * k, 0.35 * k, "#c8914e"); load.position.set(0, 1.05 * k, 0.3 * k); load.name = "load";
  g.add(body, head, hat, load);
  return g;
}

interface Worker { g: THREE.Group; pos: THREE.Vector2; home: THREE.Vector2; stock: THREE.Vector2; queue: Element[]; qi: number; state: "idle" | "fetch" | "walk" | "place"; timer: number; target: THREE.Vector2 }

export interface FloorState {
  run: Run | null; phase: Phase | null; phaseIndex: number; phases: number;
  placed: Record<string, number>; totals: Record<string, number>; elementsDone: number;
  material: number; laborMin: number; distanceM: number; crew: number; stall: number; stallReason: string;
  log: string[]; last: Element | null;
}

export class FactoryFloor {
  group = new THREE.Group();
  private f: Factory;
  private stages: { key: string; title: string; colour: number[] }[];
  private run: Run | null = null;
  private unit: ReturnType<typeof unitMesh> | null = null;
  private phases: Phase[] = [];
  private pi = 0;
  private pt = 0;
  private workers: Worker[] = [];
  private crewWanted = 2;
  private carriage = box(9 * SCALE_FT_PER_M, 0.62 * SCALE_FT_PER_M, 9 * SCALE_FT_PER_M, "#3a3a3a");
  private turntable = new THREE.Group();
  private hook = new THREE.Group();
  private cable: THREE.Line;
  private finished: THREE.Group | null = null;
  private yardGroup = new THREE.Group();
  private stationGroup = new THREE.Group();
  private stockpile = box(1.4, 0.5, 1, "#a8742e");
  private maxO = 0;
  private maxT = 0;
  state: FloorState;
  onFinish: ((rec: Omit<YardRecord, "serial" | "created">) => void) | null = null;
  private started = 0;

  constructor(f: Factory, stages: { key: string; title: string; colour: number[] }[]) {
    this.f = f; this.stages = stages;
    this.state = { run: null, phase: null, phaseIndex: 0, phases: 0, placed: {}, totals: {}, elementsDone: 0, material: 0, laborMin: 0, distanceM: 0, crew: 2, stall: 0, stallReason: "", log: [], last: null };
    // the floor: the rail round the line, the turntable on the pedestal, the crane from the pickup to it
    const railPts: THREE.Vector3[] = [];
    for (let a = ARC0 - 0.08; a <= PICKUP + 0.02; a += 0.02) railPts.push(at(a, LINE_R).setY(GROUND + 0.12));
    this.group.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(railPts), new THREE.LineBasicMaterial({ color: "#d8d0c0" })));
    const platter = new THREE.Mesh(new THREE.CylinderGeometry(6.5, 6.8, 0.5, 40), new THREE.MeshLambertMaterial({ color: "#5a5a5a" }));
    platter.position.y = 0.25;
    const stripe = box(12.6, 0.06, 0.4, "#f2c230"); stripe.position.y = 0.52;
    this.turntable.add(platter, stripe);
    this.turntable.userData.part = { id: "turntable", name: "The turntable", examine: "The finished home rides it, turning to keep its solar band on the sun." };
    platter.userData.part = this.turntable.userData.part;
    this.group.add(this.turntable);
    const pick = at(PICKUP, LINE_R), yellow = "#f0b21e";
    for (const p of [pick, new THREE.Vector3(0, 0, 0)]) {
      const tower = box(0.6, 14, 0.6, yellow); tower.position.set(p.x * (p.length() ? 1.12 : 1), GROUND + 7, p.z * (p.length() ? 1.12 : 1) - (p.length() ? 0 : 7.5));
      this.group.add(tower);
    }
    const beamLen = LINE_R * 1.12 + 7.5;
    const beam = box(0.5, 0.5, beamLen, yellow);
    beam.position.set((pick.x * 1.12) / 2, GROUND + 14, (pick.z * 1.12 - 7.5) / 2);
    beam.lookAt(pick.x * 1.12, GROUND + 14, pick.z * 1.12);
    this.group.add(beam);
    const block = box(0.9, 0.7, 0.9, "#d04a2a"); this.hook.add(block);
    this.group.add(this.hook);
    this.cable = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]), new THREE.LineBasicMaterial({ color: "#202020" }));
    this.group.add(this.cable);
    this.carriage.userData.part = { id: "carriage", name: "The transfer carriage" };
    this.group.add(this.carriage, this.stationGroup, this.yardGroup, this.stockpile);
  }

  // -------------------------------------------------------------- the stations of this unit's line
  private buildStations(run: Run) {
    this.stationGroup.clear();
    const n = run.stages.length;
    run.stages.forEach((key, i) => {
      const a = this.stationAngle(i, n), p = at(a, LINE_R);
      const st = this.stages.find((s) => s.key === key);
      const c = st ? new THREE.Color(st.colour[0], st.colour[1], st.colour[2]) : new THREE.Color("#888888");
      const g = new THREE.Group();
      const mat = new THREE.MeshLambertMaterial({ color: c, emissive: c, emissiveIntensity: 0.15 });
      for (const side of [-1, 1]) {
        const post = new THREE.Mesh(new THREE.BoxGeometry(0.35, 6.5, 0.35), mat);
        post.position.set(side * 3.6, 3.25, 0); g.add(post);
      }
      const beam = new THREE.Mesh(new THREE.BoxGeometry(7.6, 0.4, 0.5), mat); beam.position.y = 6.5; g.add(beam);
      const sign = new THREE.Mesh(new THREE.BoxGeometry(2.4, 1.2, 0.15), new THREE.MeshLambertMaterial({ color: "#1a1a1a" }));
      sign.position.y = 7.5; g.add(sign);
      const num = makeLabel(String(i + 1), c.getStyle()); num.position.set(0, 7.5, 0.1); g.add(num);
      g.position.set(p.x, GROUND, p.z);
      g.lookAt(0, GROUND, 0);
      g.traverse((o) => { o.userData.part = { id: `station:${i}`, name: `Station ${i + 1}: ${st?.title ?? key}` }; });
      this.stationGroup.add(g);
    });
  }

  private stationAngle(i: number, n: number) { return ARC0 + ((ARC1 - ARC0) * (i + 0.5)) / n; }

  // -------------------------------------------------------------- a new unit onto the line
  start(run: Run, buffers: Buffers, crew: number) {
    if (this.unit) this.group.remove(this.unit.group);
    this.run = run;
    this.unit = unitMesh(run, buffers);
    this.unit.solid.geometry.setDrawRange(0, 0); this.unit.glass.geometry.setDrawRange(0, 0);
    this.group.add(this.unit.group);
    this.maxO = 0; this.maxT = 0;
    this.buildStations(run);
    this.phases = phasesFor(this.f, run.stages.length);
    this.pi = 0; this.pt = 0;
    this.crewWanted = crew;
    const totals: Record<string, number> = {}, placed: Record<string, number> = {};
    for (const k of run.stages) { totals[k] = run.elements.filter((e) => e.stage === k).length; placed[k] = 0; }
    this.state = { ...this.state, run, phase: this.phases[0], phaseIndex: 0, phases: this.phases.length, placed, totals, elementsDone: 0,
      material: 0, laborMin: 0, distanceM: 0, crew, stall: 0, stallReason: "", last: null };
    this.setCrew(crew);
    this.say(`#${run.serial} ${run.model} onto the line: a ${run.name.toLowerCase()}, ${run.radius} m, ${run.frequency}V${run.key === "home" ? `, ${run.layout}` : ""}`);
    this.started = 0;
  }

  setCrew(n: number) {
    this.crewWanted = Math.max(1, Math.min(6, n));
    this.state.crew = this.crewWanted;
    for (const w of this.workers) this.group.remove(w.g);
    const colours = ["#2f6ad0", "#d0502f", "#3a9a4a", "#9a3ad0", "#d0a02f", "#2fa0a0"];
    this.workers = Array.from({ length: this.crewWanted }, (_, i) => {
      const g = worker(colours[i % colours.length]);
      this.group.add(g);
      return { g, pos: new THREE.Vector2(), home: new THREE.Vector2(), stock: new THREE.Vector2(), queue: [], qi: 0, state: "idle", timer: 0, target: new THREE.Vector2() };
    });
    if (this.state.phase?.kind === "work") this.beginStation(this.state.phase.station);
  }

  /** assembly_line.App.inject */
  inject(key: string) {
    const d = this.f.disruptions.find((x) => x.key === key);
    if (!d) return;
    if (d.stall) { this.state.stall = d.stall; this.state.stallReason = d.label; this.say(`! ${d.label}: ${d.note}`); }
    if (d.crew && this.workers.length > 1) { this.setCrew(this.workers.length + d.crew); this.say(`! ${d.label}: crew down to ${this.workers.length}`); }
  }

  private say(msg: string) { this.state.log = [...this.state.log.slice(-7), msg]; }

  /** App._begin_station: the station's unplaced elements, shared out w::n, from the stockpile at the deck's edge. */
  private beginStation(i: number) {
    const run = this.run!;
    const key = run.stages[i];
    const els = run.elements.filter((e) => e.stage === key).slice(this.state.placed[key] || 0);
    const n = this.workers.length;
    const stockY = -Math.min(3.4, run.floorR - 0.2);
    this.workers.forEach((w, k) => {
      w.queue = els.filter((_, j) => j % n === k); w.qi = 0;
      w.home.set((k % 2 ? -1.6 : 1.6) * (0.5 + 0.35 * Math.floor(k / 2)), stockY + 0.4);
      w.stock.set((k % 2 ? -0.9 : 0.9) * (0.4 + 0.3 * Math.floor(k / 2)), stockY);
      w.pos.copy(w.home);
      this.aim(w);
    });
  }

  private aim(w: Worker) {
    if (w.qi < w.queue.length) { w.state = "fetch"; w.target.copy(w.stock); } else { w.state = "idle"; w.target.copy(w.home); }
  }

  private placed(el: Element) {
    const s = this.state;
    s.placed[el.stage] = (s.placed[el.stage] || 0) + 1;
    s.material += el.cost; s.laborMin += el.labor; s.elementsDone++; s.last = el;
    this.maxO = Math.max(this.maxO, el.o[1]); this.maxT = Math.max(this.maxT, el.t[1]);
    this.unit?.solid.geometry.setDrawRange(0, this.maxO); this.unit?.glass.geometry.setDrawRange(0, this.maxT);
  }

  // -------------------------------------------------------------- the clock
  /** Advance the floor by dt animation seconds (the speed already applied). */
  update(dt: number, t: number) {
    this.turntable.rotation.y = t * 0.12;
    if (this.finished) this.finished.rotation.y = t * 0.12;
    const run = this.run, unit = this.unit;
    if (!run || !unit) return;
    const s = this.state, ph = this.phases[this.pi];
    s.phase = ph; s.phaseIndex = this.pi;
    const n = run.stages.length;
    // where the carriage is, and the unit on it
    let a = this.stationAngle(0, n) - 0.12;
    if (ph.kind === "travel") { const a0 = ph.station === 0 ? a : this.stationAngle(ph.station - 1, n); a = a0 + (this.stationAngle(ph.station, n) - a0) * ease(this.pt / ph.dur); }
    else if (ph.kind === "work") a = this.stationAngle(ph.station, n);
    else if (ph.kind === "tocrane") a = this.stationAngle(n - 1, n) + (PICKUP - this.stationAngle(n - 1, n)) * ease(this.pt / ph.dur);
    else if (ph.kind !== "intro") a = PICKUP;
    const deck = at(a, LINE_R);
    this.carriage.position.set(deck.x, GROUND + 0.3, deck.z);
    this.carriage.rotation.y = a;
    this.stockpile.position.set(deck.x * 0.86, GROUND + 0.25, deck.z * 0.86);
    this.stockpile.visible = ph.kind === "work";
    const pickup = at(PICKUP, LINE_R);
    let up = 0, toward = 0;               // lift height and how far in toward the turntable (0..1)
    if (ph.kind === "lift") up = ease(this.pt / ph.dur);
    if (ph.kind === "carry") { up = 1; toward = ease(this.pt / ph.dur); }
    if (ph.kind === "lower") { up = 1 - ease(this.pt / ph.dur); toward = 1; }
    if (ph.kind === "unhook" || ph.kind === "park") toward = 1;
    const liftFt = 9;
    const onDeck = new THREE.Vector3(deck.x, GROUND + 0.62 * SCALE_FT_PER_M + 0.3, deck.z);
    const onTable = new THREE.Vector3(0, 0.5, 0);
    const base = onDeck.clone().lerp(onTable, toward);
    unit.group.position.set(base.x, base.y + up * liftFt, base.z);
    unit.group.rotation.y = toward >= 1 ? t * 0.12 : a;
    // the hook: over the pickup, down to the apex, along the beam with the load
    const hookTop = GROUND + 13.6;
    const apex = unit.group.position.y + unit.top;
    const hookAt = pickup.clone().lerp(new THREE.Vector3(0, 0, 0), toward);
    let hy = hookTop;
    if (ph.kind === "hook") hy = hookTop + (apex + 0.5 - hookTop) * ease(this.pt / ph.dur);
    else if (["lift", "carry", "lower"].includes(ph.kind)) hy = apex + 0.5;
    else if (ph.kind === "unhook") hy = apex + 0.5 + (hookTop - apex - 0.5) * ease(this.pt / ph.dur);
    this.hook.position.set(hookAt.x, hy, hookAt.z);
    const cp = this.cable.geometry.getAttribute("position") as THREE.BufferAttribute;
    cp.setXYZ(0, hookAt.x, hookTop + 0.4, hookAt.z); cp.setXYZ(1, hookAt.x, hy, hookAt.z); cp.needsUpdate = true;

    // the crew
    const stalled = s.stall > 0;
    if (stalled) { s.stall = Math.max(0, s.stall - dt); if (!s.stall) this.say(`${s.stallReason} cleared`); }
    const toWorld = (p: THREE.Vector2) => {
      const c = Math.cos(a), sn = Math.sin(a), k = SCALE_FT_PER_M;
      return new THREE.Vector3(onDeck.x + (p.x * c + p.y * sn) * k, onDeck.y, onDeck.z + (-p.x * sn + p.y * c) * k);
    };
    for (const w of this.workers) {
      w.g.visible = ph.kind === "work";
      if (ph.kind !== "work") continue;
      if (!stalled && w.state !== "idle") {
        if (w.state === "fetch" || w.state === "walk") {
          const d = w.target.clone().sub(w.pos), dist = d.length(), step = this.f.walkSpeed * dt;
          if (dist <= step) {
            w.pos.copy(w.target); s.distanceM += dist;
            if (w.state === "fetch") { const el = w.queue[w.qi]; w.target.set(el.fp[0], el.fp[1]); w.state = "walk"; }
            else { w.state = "place"; w.timer = Math.max(0.12, w.queue[w.qi].labor * this.f.placeAnimPerLaborMin); }
          } else { w.pos.add(d.multiplyScalar(step / dist)); s.distanceM += step; w.g.rotation.y = Math.atan2(d.x, d.y) + a; }
        } else if (w.state === "place") {
          w.timer -= dt;
          if (w.timer <= 0) { this.placed(w.queue[w.qi]); w.qi++; this.aim(w); }
        }
      }
      const p = toWorld(w.pos);
      w.g.position.copy(p);
      const load = w.g.getObjectByName("load");
      if (load) load.visible = w.state === "walk";
    }

    // the phase clock
    if (ph.kind === "work") {
      const key = run.stages[ph.station];
      if (!this.started) { this.started = 1; this.beginStation(ph.station); }
      if ((s.placed[key] || 0) >= (s.totals[key] || 0)) { this.say(`Station ${ph.station + 1} done`); this.next(); }
    } else if (!stalled) {
      this.pt += dt;
      if (this.pt >= ph.dur) this.next();
    }
  }

  private next() {
    this.pi++; this.pt = 0; this.started = 0;
    if (this.pi < this.phases.length) return;
    // the unit is finished: it stays on the turntable until the next one comes; the yard keeps it
    const run = this.run!, s = this.state;
    if (this.finished) this.group.remove(this.finished);
    this.finished = this.unit!.group;
    this.unit = null;
    this.pi = this.phases.length - 1;
    this.say(`#${run.serial} ${run.model} built: to the yard`);
    this.onFinish?.({ name: run.model, dtype: run.key, radius: run.radius, frequency: run.frequency, layout: run.layout, cladding: run.cladding, rgb: run.claddingRgb,
      floorArea: run.floorArea, material: s.material, laborCost: 0, overhead: 0, totalCost: 0, price: run.price, margin: 0, monthly: run.monthly,
      laborHours: s.laborMin / 60, steps: 0, distanceM: s.distanceM, solarKw: 0, rValue: 0, seconds: 0 });
    this.run = null;
  }

  /** Step one element (paused): the next element of the station being worked, placed at once. */
  stepElement() {
    const run = this.run, ph = this.phases[this.pi];
    if (!run || !ph) return;
    if (ph.kind !== "work") { this.next(); return; }
    const key = run.stages[ph.station];
    const el = run.elements.filter((e) => e.stage === key)[this.state.placed[key] || 0];
    if (el) { this.placed(el); this.beginStation(ph.station); } else this.next();
  }

  /** The yard: every finished unit, a small dome in its cladding colour, round the outside. */
  setYard(records: YardRecord[]) {
    this.yardGroup.clear();
    records.forEach((r, i) => {
      const a = ARC0 + (i % 18) * 0.31, ring = YARD_R + Math.floor(i / 18) * 5;
      const p = at(a, ring);
      const rr = r.radius * SCALE_FT_PER_M;
      const dome = new THREE.Mesh(new THREE.SphereGeometry(rr, 14, 8, 0, Math.PI * 2, 0, Math.PI / 2),
        new THREE.MeshLambertMaterial({ color: new THREE.Color(r.rgb[0], r.rgb[1], r.rgb[2]), flatShading: true }));
      dome.position.set(p.x, GROUND, p.z);
      dome.userData.part = { id: `yard:${r.serial}`, name: `#${r.serial} ${r.name}`, examine: `#${r.serial} ${r.name}: a ${r.dtype}, ${r.radius} m, built ${r.created}.` };
      this.yardGroup.add(dome);
    });
  }
}

const ease = (x: number) => { const t = Math.max(0, Math.min(1, x)); return t * t * (3 - 2 * t); };

/** A number on a station's sign, drawn into a little canvas. */
function makeLabel(text: string, colour: string) {
  const c = document.createElement("canvas"); c.width = 128; c.height = 64;
  const g = c.getContext("2d")!;
  g.fillStyle = "#111"; g.fillRect(0, 0, 128, 64);
  g.fillStyle = colour; g.font = "bold 46px Inter, Segoe UI, sans-serif"; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText(text, 64, 34);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  return new THREE.Mesh(new THREE.PlaneGeometry(2.2, 1.1), new THREE.MeshBasicMaterial({ map: tex }));
}
