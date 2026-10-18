// What the people, monsters, objects and loot of the Portal world look like. Low-poly, in the
// world's palette; each monster's shape says what it is (a grub, a swarm, a wraith of damp air).

import * as THREE from "three";

const lambert = (color: string, extra: THREE.MeshLambertMaterialParameters = {}) =>
  new THREE.MeshLambertMaterial({ color, flatShading: true, ...extra });

/** A teacher: robe in their colour, a head, and long hair if they have it. */
export function npcMesh(colour: string, hair: boolean) {
  const g = new THREE.Group();
  const robe = new THREE.Mesh(new THREE.CylinderGeometry(0.75, 1.15, 3.6, 8), lambert(colour)); robe.position.y = 1.8;
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.62, 12, 10), lambert("#d8a47e")); head.position.y = 4.25;
  const arms = new THREE.Mesh(new THREE.BoxGeometry(2.3, 0.45, 0.5), lambert(colour)); arms.position.y = 3.1;
  g.add(robe, head, arms);
  if (hair) {
    const h = lambert("#3a2416");
    const crown = new THREE.Mesh(new THREE.SphereGeometry(0.68, 12, 10), h); crown.position.set(0, 4.4, -0.12);
    const back = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.35, 1.8, 8), h); back.position.set(0, 3.5, -0.42);
    g.add(crown, back);
  } else {
    const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.66, 0.66, 0.3, 10), lambert("#5a3a22")); cap.position.y = 4.75;
    g.add(cap);
  }
  // a quest marker that floats over a teacher with something to say
  const mark = new THREE.Mesh(new THREE.OctahedronGeometry(0.42), new THREE.MeshBasicMaterial({ color: "#ffd84a" }));
  mark.position.y = 6.1; mark.name = "marker";
  g.add(mark);
  g.traverse((o) => { if ((o as THREE.Mesh).isMesh) (o as THREE.Mesh).castShadow = true; });
  return g;
}

export function monsterMesh(shape: string, colour: string, size: number) {
  const g = new THREE.Group();
  const c = new THREE.Color(colour);
  const glow = new THREE.MeshStandardMaterial({ color: c, emissive: c, emissiveIntensity: 0.35, flatShading: true, roughness: 0.6 });
  const ghost = new THREE.MeshStandardMaterial({ color: c, emissive: c, emissiveIntensity: 0.5, transparent: true, opacity: 0.6, flatShading: true });
  const eye = new THREE.MeshBasicMaterial({ color: "#1a0f08" });
  const eyes = (y: number, z: number, gap: number, r = 0.12) => {
    for (const x of [-gap, gap]) { const e = new THREE.Mesh(new THREE.SphereGeometry(r, 6, 4), eye); e.position.set(x, y, z); g.add(e); }
  };
  switch (shape) {
    case "grub": {
      for (let i = 0; i < 5; i++) {
        const s = new THREE.Mesh(new THREE.SphereGeometry(0.55 - i * 0.06, 8, 6), glow);
        s.position.set(0, 0.5, -i * 0.62); g.add(s);
      }
      eyes(0.75, 0.42, 0.2);
      break;
    }
    case "swarm": {
      for (let i = 0; i < 26; i++) {
        const b = new THREE.Mesh(new THREE.SphereGeometry(0.16, 5, 4), glow);
        b.position.set((Math.random() - 0.5) * 2.4, 0.3 + Math.random() * 1.6, (Math.random() - 0.5) * 2.4);
        b.name = "mote"; g.add(b);
      }
      break;
    }
    case "wraith": {
      const body = new THREE.Mesh(new THREE.ConeGeometry(1.0, 3.6, 10, 1, true), ghost); body.position.y = 2.2; body.rotation.x = Math.PI;
      const head = new THREE.Mesh(new THREE.SphereGeometry(0.75, 10, 8), ghost); head.position.y = 3.9;
      g.add(body, head); eyes(4.0, 0.62, 0.26, 0.14);
      break;
    }
    case "sprite": {
      const drop = new THREE.Mesh(new THREE.SphereGeometry(0.85, 12, 10), ghost); drop.scale.y = 1.25; drop.position.y = 1.6;
      const tip = new THREE.Mesh(new THREE.ConeGeometry(0.6, 1.0, 10), ghost); tip.position.y = 2.75;
      g.add(drop, tip); eyes(1.8, 0.75, 0.25);
      break;
    }
    case "gust": {
      for (let i = 0; i < 4; i++) {
        const ring = new THREE.Mesh(new THREE.TorusGeometry(1.4 - i * 0.25, 0.12, 6, 18), ghost);
        ring.rotation.x = Math.PI / 2; ring.position.y = 0.8 + i * 0.9; ring.name = "ring"; g.add(ring);
      }
      break;
    }
    default: {   // golem
      const ice = lambert(colour);
      const body = new THREE.Mesh(new THREE.DodecahedronGeometry(1.4), ice); body.position.y = 2.2;
      const head = new THREE.Mesh(new THREE.IcosahedronGeometry(0.7), ice); head.position.y = 3.9;
      for (const x of [-1.6, 1.6]) { const arm = new THREE.Mesh(new THREE.BoxGeometry(0.6, 1.9, 0.6), ice); arm.position.set(x, 2.0, 0); g.add(arm); }
      g.add(body, head); eyes(4.0, 0.6, 0.25, 0.13);
    }
  }
  g.scale.setScalar(size);
  g.traverse((o) => { if ((o as THREE.Mesh).isMesh) (o as THREE.Mesh).castShadow = true; });
  return g;
}

/** Loot on the ground: a small sack that bobs. */
export function lootMesh() {
  const g = new THREE.Group();
  const sack = new THREE.Mesh(new THREE.SphereGeometry(0.5, 8, 6), lambert("#c8a46a"));
  sack.scale.y = 0.8; sack.position.y = 0.4;
  const tie = new THREE.Mesh(new THREE.ConeGeometry(0.22, 0.4, 6), lambert("#8a6a3a")); tie.position.y = 0.95;
  g.add(sack, tie);
  return g;
}

export function logPileMesh() {
  const g = new THREE.Group();
  const bark = lambert("#5a3a22"), end = lambert("#d9b07a");
  let n = 0;
  for (let row = 0; row < 3; row++) {
    for (let i = 0; i < 4 - row; i++) {
      const log = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.55, 5.5, 10), [bark, end, end]);
      log.rotation.z = Math.PI / 2; log.position.set(0, 0.55 + row * 0.95, (i - (3 - row) / 2) * 1.12); g.add(log); n++;
    }
  }
  g.traverse((o) => { if ((o as THREE.Mesh).isMesh) (o as THREE.Mesh).castShadow = true; });
  return g;
}

/** RuneScape's house portal: a stone arch on a step, a swirl of light in it, and a little
 *  dome of the same light on top. */
export function housePortalMesh(colour = "#b07cff") {
  const g = new THREE.Group();
  const stone = lambert("#9a9384"), dark = lambert("#6a655a");
  const step = new THREE.Mesh(new THREE.CylinderGeometry(4.2, 4.8, 0.7, 8), dark); step.position.y = 0.35; g.add(step);
  for (const x of [-3.1, 3.1]) {
    const p = new THREE.Mesh(new THREE.BoxGeometry(1.3, 7.6, 1.3), stone); p.position.set(x, 4.5, 0); g.add(p);
    const cap = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.5, 1.7), dark); cap.position.set(x, 8.5, 0); g.add(cap);
  }
  const arch = new THREE.Mesh(new THREE.TorusGeometry(3.1, 0.6, 6, 16, Math.PI), stone); arch.position.y = 8.3; g.add(arch);
  const c = new THREE.Color(colour);
  const glow = new THREE.MeshStandardMaterial({ color: c, emissive: c, emissiveIntensity: 1.4, transparent: true, opacity: 0.8, side: THREE.DoubleSide, depthWrite: false });
  const swirl = new THREE.Mesh(new THREE.CircleGeometry(2.5, 6, 0, Math.PI * 2), glow); swirl.position.y = 4.6; swirl.name = "swirl"; g.add(swirl);
  const inner = new THREE.Mesh(new THREE.RingGeometry(0.8, 1.7, 6), new THREE.MeshBasicMaterial({ color: "#ffffff", transparent: true, opacity: 0.45, side: THREE.DoubleSide, depthWrite: false }));
  inner.position.set(0, 4.6, 0.02); inner.name = "swirl"; g.add(inner);
  const top = new THREE.Mesh(new THREE.IcosahedronGeometry(1.1, 1), glow); top.position.y = 11.4; top.name = "marker2"; g.add(top);
  const light = new THREE.PointLight(c, 20, 18, 1.6); light.position.set(0, 5, 1.5); g.add(light);
  g.traverse((o) => { if ((o as THREE.Mesh).isMesh) (o as THREE.Mesh).castShadow = true; });
  return g;
}

/** Animate what moves by itself: swarm motes jitter, gust rings turn, markers spin. */
export function idle(g: THREE.Object3D, t: number, seed: number) {
  g.traverse((o) => {
    if (o.name === "mote") { o.position.y += Math.sin(t * 9 + o.id) * 0.01; o.position.x += Math.cos(t * 7 + o.id) * 0.01; }
    if (o.name === "ring") o.rotation.z = t * 2.5 + o.id;
    if (o.name === "marker") { o.rotation.y = t * 2; o.position.y = 6.1 + Math.sin(t * 2 + seed) * 0.15; }
    if (o.name === "swirl") o.rotation.z = t * (o.id % 2 ? 1.6 : -2.3);
    if (o.name === "marker2") { o.rotation.y = t; o.position.y = 11.4 + Math.sin(t * 1.5) * 0.25; }
  });
}
