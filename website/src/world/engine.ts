// The portal world: one small engine for the hub and every tool's space. Walk by clicking the
// ground (RuneScape-style) or with WASD; turn the camera with the arrow keys or by dragging;
// zoom with the wheel. Gateways stand around the clearing; walk into one to go through it.
//
// Units are feet, y up. The dome in the hub is the raw-wedge solver's own (generated/dome-mesh.json,
// written by scripts/export_facts.py), not a drawing of one.

import * as THREE from "three";
import mesh from "../generated/dome-mesh.json";
import type { Space } from "./spaces";

export interface Gate { key: string; name: string; colour: string; at: THREE.Vector2; facing: number; sub?: string }

/** Something in the world a person can point at: a teacher, a monster, loot, an object. */
export interface Thing { id: string; kind: "npc" | "monster" | "loot" | "object" | "dome" | "gate"; name: string; level?: number }
/** What is under the pointer: a thing, a gateway, or the ground (or nothing), and where on screen. */
/** A piece of a tool's model on a space's stage (a stick, a seam key): the mesh carries it in userData.part. */
export interface Part { id: string; name: string; examine?: string }
export interface Pick { thing: Thing | null; gate: Gate | null; part: Part | null; ground: { x: number; z: number } | null; x: number; y: number }

export type Kind = "hub" | "space" | "house";
/** Something the walker goes round: a circle on the ground, feet. */
export interface Obstacle { x: number; z: number; r: number }

export interface WorldOptions {
  /** The hilltop, a tool's island, or a member's house: a wide flat estate. */
  kind: Kind;
  space?: Space;
  gates: Gate[];
  spawn: { x: number; z: number; facing: number };
  labels: HTMLElement;           // the layer gateway names are drawn in
  minimap?: HTMLCanvasElement;
  onNear: (gate: Gate | null) => void;
  onEnter: (gate: Gate) => void;
  /** Left click: the game decides the default action. Without it, a click just walks. */
  onPick?: (p: Pick) => void;
  /** Right click (or a long press on touch): the game opens its menu of options. */
  onContext?: (p: Pick) => void;
  /** The pointer moved over something (or off it): for the hover text. */
  onHover?: (p: Pick | null) => void;
  /** Places nothing grows: kept clear of trees, [x, z, radius]. */
  clear?: [number, number, number][];
}

interface Ent {
  thing: Thing; group: THREE.Group; x: number; z: number; tx: number; tz: number; speed: number; height: number;
  bar: HTMLDivElement | null; frac: number | null; seed: number; animate?: (g: THREE.Group, t: number, seed: number) => void;
}

const WALK = 11;                 // ft per second
const PLAYER_R = 1.2;
const CLEARING = 34;             // the flat ground around the centre
const DOME_BLOCK = 11.5;         // nobody walks through the dome or its deck

// ----------------------------------------------------------------------
// Ground
// ----------------------------------------------------------------------

function noise(x: number, z: number) {
  return Math.sin(x * 0.071 + Math.sin(z * 0.053) * 1.7) * 0.5 + Math.sin(z * 0.093 - x * 0.031) * 0.35 + Math.sin((x + z) * 0.017) * 0.6;
}

/** How far a house's estate runs flat before the land falls away. */
export const ESTATE_R = 128;

export function groundHeight(kind: Kind, x: number, z: number) {
  const r = Math.hypot(x, z);
  if (kind === "house") return r < ESTATE_R ? 0 : -(r - ESTATE_R) * (r - ESTATE_R) * 0.03;
  if (kind === "space") {
    // an island: flat to 44 ft, then falling away to a rim of rock
    return r < 44 ? 0 : -(r - 44) * (r - 44) * 0.05;
  }
  const rise = Math.max(0, r - CLEARING);
  return rise * rise * 0.012 + noise(x, z) * Math.min(1, rise / 20) * 3.5;
}

function distToSegment(px: number, pz: number, ax: number, az: number, bx: number, bz: number) {
  const dx = bx - ax, dz = bz - az;
  const t = Math.max(0, Math.min(1, ((px - ax) * dx + (pz - az) * dz) / (dx * dx + dz * dz || 1)));
  return Math.hypot(px - (ax + t * dx), pz - (az + t * dz));
}

function terrain(opts: WorldOptions) {
  const size = opts.kind === "hub" ? 360 : opts.kind === "house" ? 330 : 140;
  const seg = opts.kind === "hub" ? 180 : opts.kind === "house" ? 110 : 90;
  const geo = new THREE.PlaneGeometry(size, size, seg, seg);
  geo.rotateX(-Math.PI / 2);
  const pos = geo.attributes.position as THREE.BufferAttribute;
  const colours: number[] = [];
  const grassA = new THREE.Color(opts.space?.ground || "#4f6a2a"), grassB = new THREE.Color(opts.space ? opts.space.ground : "#7a7a34").offsetHSL(0.02, 0, 0.08);
  const path = new THREE.Color("#8a7350"), rock = new THREE.Color("#5a5348");
  const c = new THREE.Color();
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i), z = pos.getZ(i);
    const y = groundHeight(opts.kind, x, z);
    pos.setY(i, y);
    const t = 0.5 + 0.5 * Math.sin(x * 0.21 + Math.cos(z * 0.17) * 2) * Math.cos(z * 0.13 - x * 0.05);
    c.copy(grassA).lerp(grassB, t * 0.8);
    // paths from the centre to each gateway
    let d = Infinity;
    for (const g of opts.gates) d = Math.min(d, distToSegment(x, z, 0, 0, g.at.x, g.at.y));
    if (opts.kind === "hub" && d < 2.6) c.lerp(path, 1 - Math.max(0, (d - 1.6) / 1.0));
    if (opts.kind === "hub" && Math.hypot(x, z) < 15.5) c.lerp(path, 0.55);
    if (opts.kind === "space" && Math.hypot(x, z) > 44) c.copy(rock);
    if (opts.kind === "space" && Math.hypot(x, z) < 44 && Math.hypot(x, z) > 42.5) c.lerp(rock, 0.6);
    colours.push(c.r, c.g, c.b);
  }
  geo.setAttribute("color", new THREE.Float32BufferAttribute(colours, 3));
  geo.computeVertexNormals();
  const m = new THREE.Mesh(geo, new THREE.MeshLambertMaterial({ vertexColors: true, flatShading: true }));
  m.receiveShadow = true;
  m.name = "ground";
  return m;
}

function sky(top: string, horizon: string) {
  const geo = new THREE.SphereGeometry(900, 32, 16);
  const mat = new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, fog: false,
    uniforms: { top: { value: new THREE.Color(top) }, horizon: { value: new THREE.Color(horizon) } },
    vertexShader: "varying vec3 vp; void main(){ vp = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }",
    fragmentShader: `uniform vec3 top; uniform vec3 horizon; varying vec3 vp;
      void main(){ float h = clamp(normalize(vp).y * 1.6 + 0.05, 0.0, 1.0); vec3 c = mix(horizon, top, pow(h, 0.7));
      float sun = pow(max(dot(normalize(vp), normalize(vec3(-0.6, 0.18, -0.75))), 0.0), 220.0);
      gl_FragColor = vec4(c + vec3(1.0, 0.85, 0.55) * sun * 1.4, 1.0); }`,
  });
  return new THREE.Mesh(geo, mat);
}

function trees(opts: WorldOptions, scene: THREE.Scene) {
  const rnd = mulberry(7);
  const spots: [number, number, number][] = [];
  const inner = opts.kind === "hub" ? 46 : opts.kind === "house" ? ESTATE_R + 4 : 30, outer = opts.kind === "hub" ? 150 : opts.kind === "house" ? ESTATE_R + 34 : 40;
  for (let tries = 0; spots.length < (opts.kind === "hub" ? 150 : opts.kind === "house" ? 90 : 22) && tries < 4000; tries++) {
    const a = rnd() * Math.PI * 2, r = inner + Math.sqrt(rnd()) * (outer - inner);
    const x = Math.cos(a) * r, z = Math.sin(a) * r;
    if (opts.gates.some((g) => distToSegment(x, z, 0, 0, g.at.x * 3, g.at.y * 3) < 7 || Math.hypot(x - g.at.x, z - g.at.y) < 9)) continue;
    if (opts.clear?.some(([cx, cz, cr]) => Math.hypot(x - cx, z - cz) < cr)) continue;
    // in a space, nothing grows on the side you arrive from, where the camera stands
    if (opts.kind === "space" && Math.abs(Math.atan2(x - opts.spawn.x, z - opts.spawn.z)) < 1.0) continue;
    spots.push([x, z, 14 + rnd() * 18]);
  }
  const trunkG = new THREE.CylinderGeometry(0.45, 0.7, 1, 6);
  const trunk = new THREE.InstancedMesh(trunkG, new THREE.MeshLambertMaterial({ color: "#4a3020" }), spots.length);
  const tiers = 3;
  const cone = new THREE.InstancedMesh(new THREE.ConeGeometry(1, 1, 7), new THREE.MeshLambertMaterial({ color: "#2c4a26", flatShading: true }), spots.length * tiers);
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(), p = new THREE.Vector3();
  const col = new THREE.Color();
  spots.forEach(([x, z, h], i) => {
    const y = groundHeight(opts.kind, x, z);
    m.compose(p.set(x, y + h * 0.18, z), q.identity(), s.set(1, h * 0.36, 1)); trunk.setMatrixAt(i, m);
    for (let k = 0; k < tiers; k++) {
      const w = h * (0.32 - k * 0.07);
      m.compose(p.set(x, y + h * (0.38 + k * 0.2), z), q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), k + i), s.set(w, h * 0.36, w));
      cone.setMatrixAt(i * tiers + k, m);
      cone.setColorAt(i * tiers + k, col.set("#2c4a26").offsetHSL(0, 0, (k * 0.03) + (i % 5) * 0.012));
    }
  });
  trunk.castShadow = cone.castShadow = true;
  scene.add(trunk, cone);
}

function mulberry(seed: number) {
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ----------------------------------------------------------------------
// The solver's dome on its pad
// ----------------------------------------------------------------------

/** The dome from the solver's mesh: one wedge strut per edge, on a ten-sided deck. z-up feet
 *  become y-up feet. */
export function solverDome(opts: { deck?: boolean; colour?: string; glow?: string } = {}) {
  const g = new THREE.Group();
  const lift = opts.deck === false ? 0 : 2.2;
  const v = (mesh.vertices as number[][]).map(([x, y, z]) => new THREE.Vector3(x, z + lift, -y));
  const strutMat = opts.glow
    ? new THREE.MeshBasicMaterial({ color: opts.glow })
    : new THREE.MeshLambertMaterial({ color: opts.colour || "#c8914e", flatShading: true });
  const strut = new THREE.CylinderGeometry(0.22, 0.22, 1, 3);   // three sides: a wedge, near enough at this size
  for (const [a, b] of mesh.edges as [number, number, string, boolean][]) {
    const p = v[a], q = v[b];
    const m = new THREE.Mesh(strut, strutMat);
    m.position.copy(p).add(q).multiplyScalar(0.5);
    m.scale.set(1, p.distanceTo(q), 1);
    m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), q.clone().sub(p).normalize());
    m.castShadow = true;
    g.add(m);
  }
  for (const p of v) {
    const n = new THREE.Mesh(new THREE.SphereGeometry(0.34, 6, 4), strutMat);
    n.position.copy(p);
    g.add(n);
  }
  if (opts.deck !== false) {
    const r = mesh.radiusFt * 1.08;
    const deck = new THREE.Mesh(new THREE.CylinderGeometry(r, r, 0.5, 10), new THREE.MeshLambertMaterial({ color: "#8a6440", flatShading: true }));
    deck.position.y = lift - 0.25;
    deck.castShadow = deck.receiveShadow = true;
    g.add(deck);
    const pier = new THREE.BoxGeometry(0.9, lift - 0.4, 0.9);
    const pmat = new THREE.MeshLambertMaterial({ color: "#9a958a" });
    for (let i = 0; i < 10; i++) {
      const a = (i / 10) * Math.PI * 2, pm = new THREE.Mesh(pier, pmat);
      pm.position.set(Math.cos(a) * r * 0.85, (lift - 0.4) / 2, Math.sin(a) * r * 0.85);
      g.add(pm);
    }
  }
  return g;
}

// ----------------------------------------------------------------------
// Gateways
// ----------------------------------------------------------------------

function gateway(gate: Gate, kind: Kind) {
  const g = new THREE.Group();
  const colour = new THREE.Color(gate.colour);
  const stone = new THREE.MeshLambertMaterial({ color: "#8a8478", flatShading: true });
  const base = new THREE.Mesh(new THREE.CylinderGeometry(4.6, 5.2, 0.8, 8), stone);
  base.position.y = 0.4;
  base.receiveShadow = true;
  const pillarG = new THREE.BoxGeometry(1.1, 9.5, 1.1);
  const left = new THREE.Mesh(pillarG, stone), right = new THREE.Mesh(pillarG, stone);
  left.position.set(-4.1, 5.2, 0); right.position.set(4.1, 5.2, 0);
  left.castShadow = right.castShadow = true;
  const ring = new THREE.Mesh(new THREE.TorusGeometry(3.4, 0.38, 10, 40),
    new THREE.MeshStandardMaterial({ color: colour, emissive: colour, emissiveIntensity: 1.3, roughness: 0.4 }));
  ring.position.y = 5.6;
  const swirl = new THREE.Mesh(new THREE.CircleGeometry(3.15, 48), new THREE.ShaderMaterial({
    transparent: true, side: THREE.DoubleSide, depthWrite: false,
    uniforms: { t: { value: 0 }, c: { value: colour } },
    vertexShader: "varying vec2 vu; void main(){ vu = uv - 0.5; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }",
    fragmentShader: `uniform float t; uniform vec3 c; varying vec2 vu;
      void main(){ float r = length(vu) * 2.0; float a = atan(vu.y, vu.x);
      float s = 0.5 + 0.5 * sin(a * 5.0 + r * 12.0 - t * 3.0); float s2 = 0.5 + 0.5 * sin(a * 3.0 - r * 7.0 + t * 1.7);
      vec3 col = mix(c * 0.4, c * 1.6 + 0.25, s * s2); float alpha = smoothstep(1.0, 0.82, r) * (0.55 + 0.35 * s);
      gl_FragColor = vec4(col, alpha); }`,
  }));
  swirl.position.y = 5.6;
  const light = new THREE.PointLight(colour, kind === "hub" ? 30 : 45, 26, 1.6);
  light.position.set(0, 5.6, 1.5);
  g.add(base, left, right, ring, swirl, light);
  g.position.set(gate.at.x, 0, gate.at.y);
  g.rotation.y = gate.facing;
  return { group: g, swirl: swirl.material as THREE.ShaderMaterial, ring };
}

// ----------------------------------------------------------------------
// The walker
// ----------------------------------------------------------------------

function walker() {
  const g = new THREE.Group();
  const skin = new THREE.MeshLambertMaterial({ color: "#d8a47e" });
  const shirt = new THREE.MeshLambertMaterial({ color: "#e8b45a" });
  const trousers = new THREE.MeshLambertMaterial({ color: "#2f3a52" });
  const body = new THREE.Mesh(new THREE.BoxGeometry(1.5, 2.1, 0.85), shirt); body.position.y = 3.35;
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.62, 12, 10), skin); head.position.y = 5.0;
  const hat = new THREE.Mesh(new THREE.ConeGeometry(0.7, 0.55, 10), new THREE.MeshLambertMaterial({ color: "#2f6a44" })); hat.position.y = 5.6;
  const leg = () => { const p = new THREE.Group(); const m = new THREE.Mesh(new THREE.BoxGeometry(0.55, 2.2, 0.6), trousers); m.position.y = -1.1; p.add(m); p.position.y = 2.3; return p; };
  const arm = () => { const p = new THREE.Group(); const m = new THREE.Mesh(new THREE.BoxGeometry(0.4, 1.9, 0.45), shirt); m.position.y = -0.95; p.add(m); p.position.y = 4.3; return p; };
  const l = leg(), r = leg(), la = arm(), ra = arm();
  l.position.x = -0.38; r.position.x = 0.38; la.position.x = -0.98; ra.position.x = 0.98;
  g.add(body, head, hat, l, r, la, ra);
  g.traverse((o) => { if ((o as THREE.Mesh).isMesh) (o as THREE.Mesh).castShadow = true; });
  return { group: g, legs: [l, r], arms: [la, ra] };
}

// ----------------------------------------------------------------------
// The world
// ----------------------------------------------------------------------

export class World {
  private renderer: THREE.WebGLRenderer;
  private scene = new THREE.Scene();
  private camera = new THREE.PerspectiveCamera(50, 1, 0.5, 2000);
  private ground: THREE.Mesh;
  private player = walker();
  private gates: { gate: Gate; swirl: THREE.ShaderMaterial; group: THREE.Group; label: HTMLDivElement }[] = [];
  private keys = new Set<string>();
  private target: THREE.Vector3 | null = null;
  private marker: THREE.Mesh;
  private yaw: number;
  private pitch = 0.5;
  private dist = 36;
  private clock = new THREE.Clock();
  private raf = 0;
  private near: Gate | null = null;
  private entering = false;
  private stepT = 0;
  private extras: ((t: number, dt: number) => void)[] = [];
  private drag: { x: number; y: number; moved: boolean; button: number } | null = null;
  private cleanup: (() => void)[] = [];
  private frameNo = 0;
  private stage: THREE.Group | null = null;
  private ents = new Map<string, Ent>();
  private approach: { id: string | null; x: number; z: number; range: number; done: () => void } | null = null;
  private splats: { el: HTMLDivElement; id: string; born: number }[] = [];
  private hoverAt = 0;
  private press: number | null = null;
  private obstacles: Obstacle[] = [];
  private estate: THREE.Group | null = null;
  private hintArrow: THREE.Mesh | null = null;
  private hintId: string | null = null;
  private hintHeight = 9;

  constructor(private canvas: HTMLCanvasElement, private opts: WorldOptions) {
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    const [top, horizon] = opts.space?.sky || ["#2a4a7a", "#e8a25a"];
    this.scene.add(sky(top, horizon));
    this.scene.fog = new THREE.Fog(horizon, opts.kind === "hub" ? 120 : opts.kind === "house" ? 150 : 70, opts.kind === "hub" ? 420 : opts.kind === "house" ? 520 : 220);

    this.scene.add(new THREE.HemisphereLight("#cfe0ff", "#4a3a20", 1.4));
    const sun = new THREE.DirectionalLight("#ffd9a0", 2.6);
    sun.position.set(-60, 70, -75);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    const sc = sun.shadow.camera as THREE.OrthographicCamera;
    const reach = opts.kind === "house" ? 125 : 70;
    sc.left = sc.bottom = -reach; sc.right = sc.top = reach; sc.far = 340;
    this.scene.add(sun);

    this.ground = terrain(opts);
    this.scene.add(this.ground);
    trees(opts, this.scene);
    if (opts.kind === "hub") {
      this.domeGroup = solverDome();
      // an invisible shell over the frame, so a click between struts still finds the dome
      const shell = new THREE.Mesh(new THREE.SphereGeometry(mesh.radiusFt, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2),
        new THREE.MeshBasicMaterial({ visible: false, side: THREE.DoubleSide }));
      shell.position.y = 2.2;
      this.domeGroup.add(shell);
      this.scene.add(this.domeGroup);
      const plaza = new THREE.Mesh(new THREE.CircleGeometry(15.5, 40), new THREE.MeshLambertMaterial({ color: "#9a8360" }));
      plaza.rotation.x = -Math.PI / 2; plaza.position.y = 0.02; plaza.receiveShadow = true;
      this.scene.add(plaza);
    } else if (opts.space) {
      this.centrepiece(opts.space);
    }
    for (const gate of opts.gates) {
      const gw = gateway(gate, opts.kind);
      gw.group.position.y = groundHeight(opts.kind, gate.at.x, gate.at.y);
      this.scene.add(gw.group);
      const label = document.createElement("div");
      label.className = "world-label";
      label.innerHTML = `<b>${gate.name}</b>${gate.sub ? `<span>${gate.sub}</span>` : ""}`;
      label.style.setProperty("--gate", gate.colour);
      opts.labels.appendChild(label);
      this.gates.push({ gate, swirl: gw.swirl, group: gw.group, label });
    }

    this.player.group.position.set(opts.spawn.x, groundHeight(opts.kind, opts.spawn.x, opts.spawn.z), opts.spawn.z);
    this.player.group.rotation.y = opts.spawn.facing;
    this.yaw = opts.spawn.facing + Math.PI;
    if (opts.kind === "space") this.dist = 26;
    if (opts.kind === "house") this.dist = 40;
    this.obstacles = opts.kind === "hub" ? [{ x: 0, z: 0, r: DOME_BLOCK }] : opts.kind === "space" ? [{ x: 0, z: 0, r: 10.5 }] : [];
    this.scene.add(this.player.group);

    this.marker = new THREE.Mesh(new THREE.RingGeometry(0.5, 0.9, 20), new THREE.MeshBasicMaterial({ color: "#ffe066", transparent: true, depthWrite: false }));
    this.marker.rotation.x = -Math.PI / 2;
    this.marker.visible = false;
    this.scene.add(this.marker);

    this.listen();
    this.resize();
    this.loop();
  }

  // -------------------------------------------------------------- the tools' stages
  private centrepiece(space: Space) {
    const c = new THREE.Color(space.colour);
    const glow = new THREE.MeshStandardMaterial({ color: c, emissive: c, emissiveIntensity: 0.5, roughness: 0.5, flatShading: true });
    const wood = new THREE.MeshLambertMaterial({ color: "#c8914e", flatShading: true });
    const pedestal = new THREE.Mesh(new THREE.CylinderGeometry(9, 10, 1.2, 10), new THREE.MeshLambertMaterial({ color: "#6a655a", flatShading: true }));
    pedestal.position.y = 0.6; pedestal.receiveShadow = true;
    this.scene.add(pedestal);
    const stage = new THREE.Group(); stage.position.y = 1.2;
    this.scene.add(stage);
    this.stage = stage;
    const spin = (o: THREE.Object3D, speed: number) => this.extras.push((_t, dt) => { o.rotation.y += dt * speed; });
    switch (space.key) {
      case "dome-creator": {
        // the Creator panel puts the design here (setModel); the whole stage turns slowly
        const d = solverDome({ deck: false, glow: space.colour }); d.scale.setScalar(0.62); stage.add(d); spin(stage, 0.12); break;
      }
      case "assembly-line": {
        const belt = new THREE.Mesh(new THREE.BoxGeometry(17, 0.6, 3), new THREE.MeshLambertMaterial({ color: "#3a3a3a" }));
        belt.position.y = 2; stage.add(belt);
        const parts: THREE.Mesh[] = [];
        for (let i = 0; i < 7; i++) {
          const p = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.5, 0.6), wood); p.position.set(-8 + i * 2.6, 2.6, 0); stage.add(p); parts.push(p);
        }
        this.extras.push((_t, dt) => parts.forEach((p) => { p.position.x += dt * 2.2; if (p.position.x > 8.5) p.position.x = -8.5; }));
        break;
      }
      case "wedge-method": {
        const log = new THREE.Mesh(new THREE.CylinderGeometry(1.3, 1.4, 8, 16), new THREE.MeshLambertMaterial({ color: "#5a3a22" }));
        log.rotation.z = Math.PI / 2; log.position.set(-4, 1.4, 0); stage.add(log);
        for (let i = 0; i < 8; i++) {
          const w = new THREE.Mesh(new THREE.CylinderGeometry(1.3, 1.3, 7, 2, 1, false, 0, Math.PI / 4), wood);
          w.rotation.z = Math.PI / 2; w.rotation.x = (i * Math.PI) / 4; w.position.set(4, 1.6 + Math.sin(i) * 0.1, 0);
          w.position.addScaledVector(new THREE.Vector3(0, Math.sin((i + 0.5) * Math.PI / 4), Math.cos((i + 0.5) * Math.PI / 4)), 0.5);
          stage.add(w);
        }
        break;
      }
      case "zome": {
        const z = new THREE.Group();
        for (let k = 0; k < 9; k++) {
          const ring = new THREE.Mesh(new THREE.TorusGeometry(6 - k * 0.6, 0.18, 4, 12), glow);
          ring.rotation.x = Math.PI / 2; ring.rotation.z = k * 0.2; ring.position.y = 0.8 + k * 0.9; z.add(ring);
        }
        stage.add(z); spin(z, 0.2); break;
      }
      case "panel-creator": {
        const tri = new THREE.Shape([new THREE.Vector2(-2.4, -1.4), new THREE.Vector2(2.4, -1.4), new THREE.Vector2(0, 2.7)]);
        const g = new THREE.ExtrudeGeometry(tri, { depth: 0.4, bevelEnabled: false });
        for (let i = 0; i < 6; i++) {
          const m = new THREE.Mesh(g, i % 2 ? wood : glow);
          m.position.set(Math.cos((i / 6) * Math.PI * 2) * 5, 3.2, Math.sin((i / 6) * Math.PI * 2) * 5);
          m.lookAt(0, 3.2, 0); stage.add(m);
          this.extras.push((t) => { m.position.y = 3.2 + Math.sin(t * 1.2 + i) * 0.4; });
        }
        break;
      }
      case "foundation": {
        const pad = new THREE.Mesh(new THREE.CylinderGeometry(7, 7, 0.5, 10), wood); pad.position.y = 2; stage.add(pad);
        for (let i = 0; i < 10; i++) {
          const a = (i / 10) * Math.PI * 2, p = new THREE.Mesh(new THREE.BoxGeometry(0.9, 1.8, 0.9), new THREE.MeshLambertMaterial({ color: "#9a958a" }));
          p.position.set(Math.cos(a) * 6, 0.9, Math.sin(a) * 6); stage.add(p);
        }
        break;
      }
      case "cell-wall": {
        for (let k = 0; k < 4; k++) {
          const shell = new THREE.Mesh(new THREE.SphereGeometry(5.5 + k * 0.7, 18, 10, 0, Math.PI, 0, Math.PI / 2),
            new THREE.MeshStandardMaterial({ color: new THREE.Color(space.colour).offsetHSL(k * 0.05, 0, -k * 0.06), transparent: true, opacity: 0.5 - k * 0.08, side: THREE.DoubleSide, flatShading: true }));
          stage.add(shell);
        }
        break;
      }
      case "masterclass": {
        const screen = new THREE.Mesh(new THREE.PlaneGeometry(16, 9), new THREE.MeshBasicMaterial({ color: "#0d1426" }));
        screen.position.set(0, 6.5, -2); stage.add(screen);
        const frame = new THREE.Mesh(new THREE.PlaneGeometry(16.6, 9.6), glow); frame.position.set(0, 6.5, -2.05); stage.add(frame);
        const d = solverDome({ deck: false, glow: space.colour }); d.scale.setScalar(0.3); d.position.set(0, 3, -1.8); stage.add(d); spin(d, 0.4);
        break;
      }
      default: break;
    }
  }

  // -------------------------------------------------------------- input
  private listen() {
    const c = this.canvas;
    const on = <K extends keyof HTMLElementEventMap>(el: HTMLElement | Window, ev: K | string, fn: (e: any) => void, o?: AddEventListenerOptions) => {
      el.addEventListener(ev, fn, o); this.cleanup.push(() => el.removeEventListener(ev, fn, o));
    };
    on(window, "keydown", (e: KeyboardEvent) => {
      if ((e.target as HTMLElement)?.closest?.("input, textarea, select")) return;
      const k = e.key.toLowerCase();
      if (["w", "a", "s", "d", "arrowup", "arrowdown", "arrowleft", "arrowright", "q", "e"].includes(k)) { this.keys.add(k); e.preventDefault(); }
    });
    on(window, "keyup", (e: KeyboardEvent) => this.keys.delete(e.key.toLowerCase()));
    on(window, "blur", () => this.keys.clear());
    on(c, "contextmenu", (e: MouseEvent) => {
      e.preventDefault();
      if (this.opts.onContext) this.opts.onContext(this.pick(e.clientX, e.clientY));
    });
    on(c, "pointerdown", (e: PointerEvent) => {
      c.setPointerCapture(e.pointerId);
      this.drag = { x: e.clientX, y: e.clientY, moved: false, button: e.button };
      // a long press on a touch screen is a right click
      if (e.pointerType === "touch" && this.opts.onContext) {
        const x = e.clientX, y = e.clientY;
        this.press = window.setTimeout(() => {
          if (this.drag && !this.drag.moved) { this.drag = null; this.opts.onContext!(this.pick(x, y)); }
        }, 520);
      }
    });
    on(c, "pointermove", (e: PointerEvent) => {
      if (!this.drag) {
        const now = performance.now();
        if (this.opts.onHover && now - this.hoverAt > 60) { this.hoverAt = now; this.opts.onHover(this.pick(e.clientX, e.clientY)); }
        return;
      }
      const dx = e.clientX - this.drag.x, dy = e.clientY - this.drag.y;
      if (!this.drag.moved && Math.hypot(dx, dy) < 6) return;
      this.drag.moved = true;
      this.yaw -= dx * 0.006;
      this.pitch = Math.min(1.25, Math.max(0.18, this.pitch + dy * 0.005));
      this.drag.x = e.clientX; this.drag.y = e.clientY;
    });
    on(c, "pointerup", (e: PointerEvent) => {
      if (this.press) { window.clearTimeout(this.press); this.press = null; }
      const d = this.drag; this.drag = null;
      if (!d || d.moved || d.button !== 0) return;
      if (this.opts.onPick) {
        const p = this.pick(e.clientX, e.clientY);
        if (!p.thing && !p.gate && !p.part && p.ground) this.walkPoint(p.ground.x, p.ground.z);
        this.opts.onPick(p);
      } else this.walkTo(e.clientX, e.clientY);
    });
    on(c, "pointerleave", () => this.opts.onHover?.(null));
    on(c, "wheel", (e: WheelEvent) => { e.preventDefault(); this.zoom(e.deltaY > 0 ? 1.1 : 0.9); }, { passive: false });
    on(window, "resize", () => this.resize());
  }

  /** RuneScape's yellow hint arrow, bobbing over the thing to go to next (null hides it). */
  setHint(id: string | null, height = 9) {
    if (!this.hintArrow) {
      const a = new THREE.Mesh(new THREE.ConeGeometry(1.1, 2.4, 4), new THREE.MeshBasicMaterial({ color: "#ffe24a" }));
      a.rotation.x = Math.PI;                       // pointing down
      a.visible = false;
      this.scene.add(a);
      this.hintArrow = a;
      this.extras.push((t) => {
        const id2 = this.hintId, at = id2 ? this.thingAt(id2) : null;
        a.visible = Boolean(at);
        if (at) { a.position.set(at.x, this.hintHeight + Math.sin(t * 4) * 0.6, at.z); a.rotation.y = t * 2; }
      });
    }
    this.hintId = id;
    this.hintHeight = height;
  }

  /** Build a house's estate: its buildings and grounds, what the walker goes round, and what moves. */
  setEstate(group: THREE.Group, obstacles: Obstacle[], tick?: (t: number, dt: number) => void) {
    if (this.estate) this.scene.remove(this.estate);
    this.estate = group;
    this.scene.add(group);
    this.obstacles = obstacles;
    if (tick) this.extras.push(tick);
  }

  /** Put a tool's own model on the space's stage, replacing what stood there. */
  setModel(obj: THREE.Object3D) {
    if (!this.stage) return;
    for (const child of [...this.stage.children]) {
      this.stage.remove(child);
      child.traverse((o) => {
        const m = o as THREE.Mesh;
        m.geometry?.dispose?.();
        const mat = m.material as THREE.Material | THREE.Material[] | undefined;
        if (Array.isArray(mat)) mat.forEach((x) => x.dispose()); else mat?.dispose?.();
      });
    }
    this.stage.add(obj);
  }

  // -------------------------------------------------------------- things in the world
  private ray(cx: number, cy: number) {
    const r = this.canvas.getBoundingClientRect();
    const ray = new THREE.Raycaster();
    ray.setFromCamera(new THREE.Vector2(((cx - r.left) / r.width) * 2 - 1, -((cy - r.top) / r.height) * 2 + 1), this.camera);
    return ray;
  }

  /** What is under a point of the screen: the nearest thing or gateway, and the ground. */
  pick(cx: number, cy: number): Pick {
    const ray = this.ray(cx, cy);
    let best: { d: number; thing: Thing | null; gate: Gate | null } | null = null;
    for (const e of this.ents.values()) {
      const h = ray.intersectObject(e.group, true)[0];
      if (h && (!best || h.distance < best.d)) best = { d: h.distance, thing: e.thing, gate: null };
    }
    for (const g of this.gates) {
      if (!g.group.visible) continue;
      const h = ray.intersectObject(g.group, true)[0];
      if (h && (!best || h.distance < best.d)) best = { d: h.distance, thing: null, gate: g.gate };
    }
    // a piece of the tool's model on the stage
    let part: Part | null = null;
    if (this.stage && !best) {
      for (const h of ray.intersectObject(this.stage, true)) {
        let o: THREE.Object3D | null = h.object;
        while (o && !o.userData.part) o = o.parent;
        if (o && o.visible !== false) { part = o.userData.part as Part; break; }
      }
    }
    // the dome's shell is big and see-through: it counts only when nothing else is under the pointer
    if (this.domeGroup && !best) {
      const h = ray.intersectObject(this.domeGroup, true)[0];
      if (h) best = { d: h.distance, thing: { id: "dome", kind: "dome", name: "The plaza dome" }, gate: null };
    }
    const g = ray.intersectObject(this.ground)[0];
    return { thing: best?.thing ?? null, gate: best?.gate ?? null, part, ground: g ? { x: g.point.x, z: g.point.z } : null, x: cx, y: cy };
  }

  addThing(thing: Thing, group: THREE.Group, x: number, z: number, o: { speed?: number; height?: number; facing?: number; animate?: Ent["animate"] } = {}) {
    this.removeThing(thing.id);
    group.position.set(x, groundHeight(this.opts.kind, x, z), z);
    if (o.facing !== undefined) group.rotation.y = o.facing;
    this.scene.add(group);
    this.ents.set(thing.id, { thing, group, x, z, tx: x, tz: z, speed: o.speed ?? 4, height: o.height ?? 5, bar: null, frac: null, seed: Math.random() * 10, animate: o.animate });
  }

  removeThing(id: string) {
    const e = this.ents.get(id);
    if (!e) return;
    this.scene.remove(e.group);
    e.bar?.remove();
    this.ents.delete(id);
  }

  hasThing(id: string) { return this.ents.has(id); }
  thingAt(id: string) { const e = this.ents.get(id); return e ? { x: e.x, z: e.z } : null; }
  thingObject(id: string) { return this.ents.get(id)?.group ?? null; }
  /** Send a thing walking toward a point (monsters roaming, chasing). */
  moveThing(id: string, x: number, z: number) { const e = this.ents.get(id); if (e) { e.tx = x; e.tz = z; } }
  playerAt() { const p = this.player.group.position; return { x: p.x, z: p.z }; }

  walkPoint(x: number, z: number) {
    this.approach = null;
    this.target = new THREE.Vector3(x, 0, z);
    this.showMarker(this.target);
  }

  /** Walk until within `range` of a thing (or a point), then do `done`. */
  walkNear(id: string | null, range: number, done: () => void, point?: { x: number; z: number }) {
    const at = id ? this.thingAt(id) : point;
    if (!at) return;
    // already there: do it now, not a frame later
    const p = this.player.group.position;
    if (Math.hypot(at.x - p.x, at.z - p.z) <= range) { this.stopWalking(); if (id) this.face(id); done(); return; }
    this.approach = { id, x: at.x, z: at.z, range, done };
    this.target = new THREE.Vector3(at.x, 0, at.z);
  }

  stopWalking() { this.target = null; this.approach = null; }

  /** Put the walker somewhere at once (respawning after a defeat). */
  teleport(x: number, z: number) {
    this.stopWalking();
    this.player.group.position.set(x, groundHeight(this.opts.kind, x, z), z);
  }

  face(id: string) {
    const e = this.ents.get(id), p = this.player.group.position;
    if (e) this.player.group.rotation.y = Math.atan2(e.x - p.x, e.z - p.z);
  }

  /** A health bar over a thing (or the player): a fraction 0..1, or null to hide it. */
  setBar(id: string, frac: number | null) {
    if (id === "player") { this.playerFrac = frac; this.ensurePlayerBar(); return; }
    const e = this.ents.get(id);
    if (!e) return;
    e.frac = frac;
    if (frac === null) { e.bar?.remove(); e.bar = null; return; }
    if (!e.bar) { e.bar = document.createElement("div"); e.bar.className = "world-bar"; e.bar.innerHTML = "<i></i>"; this.opts.labels.appendChild(e.bar); }
    (e.bar.firstChild as HTMLElement).style.width = `${Math.max(0, Math.min(1, frac)) * 100}%`;
  }

  private playerFrac: number | null = null;
  private playerBar: HTMLDivElement | null = null;
  private ensurePlayerBar() {
    if (this.playerFrac === null) { this.playerBar?.remove(); this.playerBar = null; return; }
    if (!this.playerBar) { this.playerBar = document.createElement("div"); this.playerBar.className = "world-bar"; this.playerBar.innerHTML = "<i></i>"; this.opts.labels.appendChild(this.playerBar); }
    (this.playerBar.firstChild as HTMLElement).style.width = `${Math.max(0, Math.min(1, this.playerFrac)) * 100}%`;
  }

  /** A hitsplat (or any short text) over a thing or the player. */
  splat(id: string, text: string, kind: "hit" | "miss" | "heal" | "xp" = "hit") {
    const el = document.createElement("div");
    el.className = `world-splat ${kind}`;
    el.textContent = text;
    this.opts.labels.appendChild(el);
    this.splats.push({ el, id, born: performance.now() });
  }

  private domeGroup: THREE.Group | null = null;

  zoom(f: number) { this.dist = Math.min(80, Math.max(12, this.dist * f)); }
  turn(rad: number) { this.yaw += rad; }

  private walkTo(cx: number, cy: number) {
    const r = this.canvas.getBoundingClientRect();
    const ndc = new THREE.Vector2(((cx - r.left) / r.width) * 2 - 1, -((cy - r.top) / r.height) * 2 + 1);
    const ray = new THREE.Raycaster();
    ray.setFromCamera(ndc, this.camera);
    // a click on a gateway walks to its middle
    for (const g of this.gates) {
      if (ray.intersectObject(g.group, true).length) { this.target = new THREE.Vector3(g.gate.at.x, 0, g.gate.at.y); this.showMarker(this.target); return; }
    }
    const hit = ray.intersectObject(this.ground)[0];
    if (hit) { this.target = hit.point.clone(); this.showMarker(this.target); }
  }

  private showMarker(p: THREE.Vector3) {
    this.marker.position.set(p.x, groundHeight(this.opts.kind, p.x, p.z) + 0.08, p.z);
    this.marker.visible = true;
    (this.marker.material as THREE.MeshBasicMaterial).opacity = 1;
  }

  // -------------------------------------------------------------- the loop
  private resize() {
    const w = this.canvas.clientWidth, h = this.canvas.clientHeight;
    if (!w || !h) return;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  private loop = () => {
    this.raf = requestAnimationFrame(this.loop);
    const dt = Math.min(0.05, this.clock.getDelta()), t = this.clock.elapsedTime;
    this.update(dt, t);
    this.renderer.render(this.scene, this.camera);
    this.place();
    this.overlays();
    if (this.opts.minimap && this.frameNo % 4 === 0) this.drawMap();
    this.frameNo++;
  };

  private update(dt: number, t: number) {
    const k = this.keys, p = this.player.group.position;
    if (k.has("arrowleft") || k.has("q")) this.yaw += dt * 1.8;
    if (k.has("arrowright") || k.has("e")) this.yaw -= dt * 1.8;
    if (k.has("arrowup")) this.pitch = Math.min(1.25, this.pitch + dt);
    if (k.has("arrowdown")) this.pitch = Math.max(0.18, this.pitch - dt);
    // where to go: the keys, or the clicked point
    const move = new THREE.Vector2();
    const fwd = new THREE.Vector2(-Math.sin(this.yaw), -Math.cos(this.yaw)), right = new THREE.Vector2(-fwd.y, fwd.x);
    if (k.has("w")) move.add(fwd);
    if (k.has("s")) move.sub(fwd);
    if (k.has("d")) move.add(right);
    if (k.has("a")) move.sub(right);
    if (move.lengthSq() > 0) { this.target = null; this.approach = null; this.marker.visible = false; }
    else if (this.approach) {
      const a = this.approach;
      const at = a.id ? this.thingAt(a.id) : { x: a.x, z: a.z };
      if (!at) this.approach = null;
      else {
        if (Math.hypot(at.x - p.x, at.z - p.z) <= a.range) {
          this.approach = null; this.target = null;
          if (a.id) this.face(a.id);
          a.done();
        } else {
          this.target = new THREE.Vector3(at.x, 0, at.z);
          move.set(at.x - p.x, at.z - p.z);
        }
      }
    } else if (this.target) {
      move.set(this.target.x - p.x, this.target.z - p.z);
      if (move.length() < 0.4) { this.target = null; move.set(0, 0); }
    }
    const moving = move.lengthSq() > 0;
    if (moving) {
      move.normalize().multiplyScalar(WALK * dt);
      let nx = p.x + move.x, nz = p.z + move.y;
      // the dome, a space's stage or a house's buildings: walk round each, the shorter way,
      // instead of stopping at its edge
      for (const ob of this.obstacles) {
        if (Math.hypot(nx - ob.x, nz - ob.z) >= ob.r) continue;
        const dx = p.x - ob.x, dz = p.z - ob.z;
        const r0 = Math.hypot(dx, dz) || 1, rx = dx / r0, rz = dz / r0;
        let tx = -rz, tz = rx;
        const aim = this.target ? new THREE.Vector2(this.target.x - p.x, this.target.z - p.z) : move;
        if (tx * aim.x + tz * aim.y < 0) { tx = -tx; tz = -tz; }
        const step = move.length();
        nx = p.x + tx * step; nz = p.z + tz * step;
        const r = Math.hypot(nx - ob.x, nz - ob.z) || 1;
        nx = ob.x + (nx - ob.x) * (ob.r / r); nz = ob.z + (nz - ob.z) * (ob.r / r);
      }
      const lim = this.opts.kind === "hub" ? 70 : this.opts.kind === "house" ? ESTATE_R - 3 : 42;
      const rr = Math.hypot(nx, nz);
      if (rr > lim) { nx *= lim / rr; nz *= lim / rr; }
      this.player.group.rotation.y = Math.atan2(nx - p.x, nz - p.z);
      p.x = nx; p.z = nz;
      this.stepT += dt * 9;
    } else {
      this.stepT *= 0.85;
    }
    p.y = groundHeight(this.opts.kind, p.x, p.z);
    const swing = Math.sin(this.stepT) * (moving ? 0.6 : 0);
    this.player.legs[0].rotation.x = swing; this.player.legs[1].rotation.x = -swing;
    this.player.arms[0].rotation.x = -swing * 0.8; this.player.arms[1].rotation.x = swing * 0.8;
    if (this.marker.visible) {
      const m = this.marker.material as THREE.MeshBasicMaterial;
      m.opacity = Math.max(0, m.opacity - dt * 0.9);
      this.marker.scale.setScalar(1 + (1 - m.opacity) * 0.6);
      if (m.opacity <= 0) this.marker.visible = false;
    }
    // the camera follows, behind and above
    const target = new THREE.Vector3(p.x, p.y + 4.2, p.z);
    const cp = new THREE.Vector3(
      target.x + Math.sin(this.yaw) * Math.cos(this.pitch) * this.dist,
      target.y + Math.sin(this.pitch) * this.dist,
      target.z + Math.cos(this.yaw) * Math.cos(this.pitch) * this.dist);
    cp.y = Math.max(cp.y, groundHeight(this.opts.kind, cp.x, cp.z) + 2);
    // the first frame starts where the camera belongs; after that it follows smoothly
    if (this.frameNo === 0) this.camera.position.copy(cp); else this.camera.position.lerp(cp, 1 - Math.pow(0.0005, dt));
    this.camera.lookAt(target);
    for (const g of this.gates) {
      g.swirl.uniforms.t.value = t;
      // a gateway between the camera and the walker would fill the view: it steps aside until the
      // camera moves on (the usual third-person fix for a wall in the way)
      const cam = this.camera.position;
      const between = distToSegment(g.gate.at.x, g.gate.at.y, cam.x, cam.z, p.x, p.z) < 7.5
        && Math.hypot(cam.x - g.gate.at.x, cam.z - g.gate.at.y) < Math.hypot(cam.x - p.x, cam.z - p.z);
      g.group.visible = !between;
    }
    for (const f of this.extras) f(t, dt);
    for (const e of this.ents.values()) {
      const dx = e.tx - e.x, dz = e.tz - e.z, d = Math.hypot(dx, dz);
      if (d > 0.05) {
        const step = Math.min(d, e.speed * dt);
        e.x += (dx / d) * step; e.z += (dz / d) * step;
        e.group.rotation.y = Math.atan2(dx, dz);
      }
      e.group.position.set(e.x, groundHeight(this.opts.kind, e.x, e.z), e.z);
      e.animate?.(e.group, t, e.seed);
    }
    // near a gateway, and through it
    let near: Gate | null = null;
    for (const g of this.gates) {
      const d = Math.hypot(p.x - g.gate.at.x, p.z - g.gate.at.y);
      if (d < 9) near = g.gate;
      if (d < 1.6 && !this.entering) { this.entering = true; this.opts.onEnter(g.gate); }
    }
    if (near !== this.near) { this.near = near; this.opts.onNear(near); }
  }

  /** Gateway names float above their rings, in the labels layer. */
  private place() {
    const w = this.canvas.clientWidth, h = this.canvas.clientHeight;
    const v = new THREE.Vector3();
    for (const g of this.gates) {
      v.set(g.gate.at.x, g.group.position.y + 11.2, g.gate.at.y).project(this.camera);
      const visible = g.group.visible && v.z < 1 && Math.abs(v.x) < 1.15 && Math.abs(v.y) < 1.15;
      const d = this.camera.position.distanceTo(new THREE.Vector3(g.gate.at.x, g.group.position.y + 6, g.gate.at.y));
      g.label.style.display = visible ? "" : "none";
      if (visible) {
        g.label.style.transform = `translate(-50%, -100%) translate(${(v.x * 0.5 + 0.5) * w}px, ${(-v.y * 0.5 + 0.5) * h}px) scale(${Math.max(0.55, Math.min(1.1, 40 / d))})`;
        g.label.classList.toggle("near", g.gate === this.near);
      }
    }
  }

  private overlays() {
    const w = this.canvas.clientWidth, h = this.canvas.clientHeight, v = new THREE.Vector3();
    const screen = (x: number, y: number, z: number) => {
      v.set(x, y, z).project(this.camera);
      return v.z < 1 ? { sx: (v.x * 0.5 + 0.5) * w, sy: (-v.y * 0.5 + 0.5) * h } : null;
    };
    for (const e of this.ents.values()) {
      if (!e.bar) continue;
      const s = screen(e.x, e.group.position.y + e.height + 0.8, e.z);
      e.bar.style.display = s ? "" : "none";
      if (s) e.bar.style.transform = `translate(-50%, -50%) translate(${s.sx}px, ${s.sy}px)`;
    }
    const pp = this.player.group.position;
    if (this.playerBar) {
      const s = screen(pp.x, pp.y + 6.6, pp.z);
      this.playerBar.style.display = s ? "" : "none";
      if (s) this.playerBar.style.transform = `translate(-50%, -50%) translate(${s.sx}px, ${s.sy}px)`;
    }
    const now = performance.now();
    this.splats = this.splats.filter((sp) => {
      const age = (now - sp.born) / 1000;
      if (age > 1.1) { sp.el.remove(); return false; }
      const at = sp.id === "player" ? { x: pp.x, y: pp.y + 4, z: pp.z } : (() => { const e = this.ents.get(sp.id); return e ? { x: e.x, y: e.group.position.y + e.height * 0.6, z: e.z } : null; })();
      const s = at && screen(at.x, at.y, at.z);
      if (!s) { sp.el.style.display = "none"; return true; }
      sp.el.style.display = "";
      sp.el.style.opacity = String(Math.min(1, 2.2 - age * 2));
      sp.el.style.transform = `translate(-50%, -50%) translate(${s.sx}px, ${s.sy - age * 26}px)`;
      return true;
    });
  }

  private drawMap() {
    const m = this.opts.minimap!, ctx = m.getContext("2d")!;
    const s = m.width, half = s / 2, scale = half / (this.opts.kind === "hub" ? 62 : this.opts.kind === "house" ? 90 : 46);
    ctx.clearRect(0, 0, s, s);
    ctx.save();
    ctx.beginPath(); ctx.arc(half, half, half - 2, 0, Math.PI * 2); ctx.clip();
    ctx.fillStyle = this.opts.space?.ground || "#4f6a2a"; ctx.fillRect(0, 0, s, s);
    ctx.translate(half, half);
    ctx.rotate(this.yaw);                                   // north-up would lose the player; the map turns with the camera
    const p = this.player.group.position;
    ctx.translate(-p.x * scale, -p.z * scale);
    ctx.fillStyle = "rgba(140,115,80,0.9)";
    ctx.beginPath(); ctx.arc(0, 0, 15.5 * scale, 0, Math.PI * 2); ctx.fill();
    if (this.opts.kind === "hub") {
      ctx.strokeStyle = "rgba(140,115,80,0.9)"; ctx.lineWidth = 4 * scale;
      for (const g of this.gates) { ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(g.gate.at.x * scale, g.gate.at.y * scale); ctx.stroke(); }
      ctx.fillStyle = "#c8914e"; ctx.beginPath(); ctx.arc(0, 0, mesh.radiusFt * scale, 0, Math.PI * 2); ctx.fill();
    }
    if (this.opts.kind === "house") {
      ctx.fillStyle = "rgba(240,232,214,0.85)";
      for (const ob of this.obstacles) { ctx.beginPath(); ctx.arc(ob.x * scale, ob.z * scale, ob.r * scale, 0, Math.PI * 2); ctx.fill(); }
    }
    for (const g of this.gates) {
      ctx.fillStyle = g.gate.colour; ctx.beginPath(); ctx.arc(g.gate.at.x * scale, g.gate.at.y * scale, 4.5, 0, Math.PI * 2); ctx.fill();
    }
    for (const e of this.ents.values()) {
      // RuneScape's dots: yellow for people, red for monsters, red-ringed for loot
      ctx.fillStyle = e.thing.kind === "npc" ? "#ffe24a" : e.thing.kind === "monster" ? "#ff4a3a" : e.thing.kind === "loot" ? "#ff9a3a" : "#e8e0d0";
      ctx.beginPath(); ctx.arc(e.x * scale, e.z * scale, e.thing.kind === "loot" ? 2 : 2.6, 0, Math.PI * 2); ctx.fill();
    }
    ctx.restore();
    // the player, always in the middle, pointing where they face relative to the camera
    ctx.save(); ctx.translate(half, half); ctx.rotate(-(this.player.group.rotation.y - this.yaw) + Math.PI);
    ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.moveTo(0, -7); ctx.lineTo(5, 5); ctx.lineTo(-5, 5); ctx.closePath(); ctx.fill();
    ctx.restore();
    ctx.strokeStyle = "rgba(255,255,255,0.5)"; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(half, half, half - 2, 0, Math.PI * 2); ctx.stroke();
  }

  dispose() {
    cancelAnimationFrame(this.raf);
    for (const f of this.cleanup) f();
    for (const g of this.gates) g.label.remove();
    for (const e of this.ents.values()) e.bar?.remove();
    for (const sp of this.splats) sp.el.remove();
    this.playerBar?.remove();
    if (this.press) window.clearTimeout(this.press);
    this.scene.traverse((o) => {
      const m = o as THREE.Mesh;
      m.geometry?.dispose?.();
      const mat = m.material as THREE.Material | THREE.Material[] | undefined;
      if (Array.isArray(mat)) mat.forEach((x) => x.dispose()); else mat?.dispose?.();
    });
    this.renderer.dispose();
  }
}

/** The hub's gateways: evenly round the clearing, each facing the dome. */
export function hubGates(spaces: { key: string; name: string; colour: string }[], radius = 27): Gate[] {
  return spaces.map((s, i) => {
    const a = (i / spaces.length) * Math.PI * 2 + Math.PI / spaces.length;
    const x = Math.sin(a) * radius, z = Math.cos(a) * radius;
    return { key: s.key, name: s.name, colour: s.colour, at: new THREE.Vector2(x, z), facing: Math.atan2(-x, -z) };
  });
}

export { THREE };
