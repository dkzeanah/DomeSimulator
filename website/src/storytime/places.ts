// @ts-nocheck
// More places for the storytime world: the open sea under a low moon, a ship's bridge at night, the
// deck by day, a city of lit towers, a museum of sculptures in green hills, a snowy slope, a little
// street of lanterns, a room lit by a television, a rainy night outside a barracks, a pumpkin patch,
// and a dark shore in the rain. Each is built the first time a page needs it (need()), far from the
// others, and shown alone; the scenes that use them are in scenes.ts. Nothing here is anybody's
// name: what a place means is up to the story told over it.

import * as THREE from "three";

const V = (x, y, z) => new THREE.Vector3(x, y, z);
const SPOTS = {
  moonsea: V(640, 0, 0), bridge: V(-640, 0, 0), deck: V(0, 640, 0), tokyo: V(0, -640, 0), museum: V(640, 640, 0),
  snow: V(-640, 640, 0), street: V(640, -640, 0), tvroom: V(-640, -640, 0), base: V(-960, 0, 0), pumpkin: V(0, 960, 0), shore: V(960, 0, 0),
};

/** Glowing things: a material that ignores the light, for lamps, windows and screens. */
const glow = (c, o = 1) => new THREE.MeshBasicMaterial({ color: c, transparent: o < 1, opacity: o, fog: true });

function softDot() {
  const c = document.createElement("canvas"); c.width = c.height = 64;
  const g = c.getContext("2d"), gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, "rgba(255,255,255,1)"); gr.addColorStop(0.35, "rgba(255,255,255,0.55)"); gr.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
let DOT = null;
const dot = () => (DOT ||= softDot());

/** Falling things (rain, snow, petals): points that fall, drift, and come back to the top. */
function fall(w, g, { n = 600, box = [24, 24, 10], color = 0xffffff, size = 0.08, speed = 4, drift = 0.3, streak = false }) {
  const pos = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) pos.set([(Math.random() - 0.5) * box[0], (Math.random() - 0.5) * box[1], Math.random() * box[2]], i * 3);
  const geo = new THREE.BufferGeometry(); geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  const pts = new THREE.Points(geo, new THREE.PointsMaterial({ color, size, map: dot(), transparent: true, depthWrite: false, opacity: streak ? 0.55 : 0.9 }));
  g.add(pts);
  w.hooks.push((dt) => {
    if (!g.visible) return;
    for (let i = 0; i < n; i++) {
      pos[i * 3 + 2] -= dt * speed * (0.7 + (i % 7) * 0.06);
      pos[i * 3] += Math.sin(w.time * 0.7 + i) * dt * drift;
      if (pos[i * 3 + 2] < 0) pos[i * 3 + 2] = box[2];
    }
    geo.attributes.position.needsUpdate = true;
  });
  return pts;
}

/** A sea that breathes. */
function sea(w, g, size = 300, color = "#1c3a63") {
  const geo = new THREE.PlaneGeometry(size, size, 70, 70);
  const m = new THREE.Mesh(geo, new THREE.MeshLambertMaterial({ color, flatShading: true })); g.add(m);
  const base = geo.attributes.position.array.slice();
  w.hooks.push(() => {
    if (!g.visible) return;
    const p = geo.attributes.position.array, t = w.time;
    for (let i = 0; i < p.length; i += 3) p[i + 2] = base[i + 2] + Math.sin(base[i] * 0.16 + t * 1.1) * 0.22 + Math.cos(base[i + 1] * 0.21 + t * 0.8) * 0.18;
    geo.attributes.position.needsUpdate = true; geo.computeVertexNormals();
  });
  return m;
}

function windowsTexture(cols, rows, lit = 0.55, warm = "#ffd98a", dark = "#1b2033", seed = 1) {
  const c = document.createElement("canvas"); c.width = cols * 8; c.height = rows * 10;
  const g = c.getContext("2d"); g.fillStyle = dark; g.fillRect(0, 0, c.width, c.height);
  let s = seed * 9301; const rnd = () => ((s = (s * 16807) % 2147483647) / 2147483647);
  for (let x = 0; x < cols; x++) for (let y = 0; y < rows; y++) {
    if (rnd() < lit) { g.fillStyle = rnd() < 0.8 ? warm : "#cfe6ff"; g.fillRect(x * 8 + 2, y * 10 + 2, 4, 6); }
  }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.magFilter = THREE.NearestFilter; return t;
}

// ------------------------------------------------------------------ the places
const BUILD = {
  moonsea(w, g) {
    sea(w, g, 400, "#13294a");
    // the moon, low over the water, and its road of light on the sea
    const moon = new THREE.Sprite(new THREE.SpriteMaterial({ map: dot(), color: 0xfff4d8, fog: false, depthWrite: false, transparent: true }));
    moon.position.set(0, 150, 22); moon.scale.set(34, 34, 1); g.add(moon);
    const disc = new THREE.Mesh(new THREE.CircleGeometry(7, 48), new THREE.MeshBasicMaterial({ color: 0xfff6e0, fog: false }));
    disc.position.set(0, 151, 22); disc.rotation.x = Math.PI / 2; g.add(disc);
    const glade = new THREE.Mesh(new THREE.PlaneGeometry(9, 150), new THREE.MeshBasicMaterial({ color: 0xfff1c8, transparent: true, opacity: 0.22, depthWrite: false, fog: false, blending: THREE.AdditiveBlending }));
    glade.position.set(0, 75, 0.35); g.add(glade);
    w.hooks.push(() => { if (g.visible) glade.material.opacity = 0.18 + 0.05 * Math.sin(w.time * 1.3); });
    // a ship, far off, with its lights
    const ship = new THREE.Group(); ship.position.set(-14, 46, 0.3); g.add(ship);
    w.box(ship, 0, 0, 0.6, 9, 2.2, 1.4, "#0d1220"); w.box(ship, -1.6, 0, 1.9, 3, 1.7, 1.4, "#111829");
    for (const x of [-2.6, -1.8, -1.0, -0.2]) { const l = new THREE.Mesh(new THREE.SphereGeometry(0.12, 8, 6), glow(0xffd98a)); l.position.set(x, -0.9, 2.0); ship.add(l); }
    const mast = new THREE.Mesh(new THREE.SphereGeometry(0.18, 8, 6), glow(0xff5a4a)); mast.position.set(2.4, 0, 5.2); ship.add(mast);
    w.cyl(ship, [2.4, 0, 1.3], [2.4, 0, 5.1], 0.07, "#0d1220", 6);
    w.hooks.push(() => { if (g.visible) { ship.position.z = 0.3 + Math.sin(w.time * 0.9) * 0.15; mast.visible = Math.sin(w.time * 3) > -0.2; } });
  },

  bridge(w, g) {
    // a ship's bridge at night: a wide sweep of windows, glowing consoles, the wheel
    w.box(g, 0, 0, 0.05, 9, 7, 0.1, "#2a2f38");
    w.box(g, 0, 3.4, 2.1, 9, 0.2, 0.9, "#3a414d"); w.box(g, 0, 3.4, 3.8, 9, 0.2, 0.6, "#3a414d");
    for (const x of [-4.4, -2.2, 0, 2.2, 4.4]) w.box(g, x, 3.4, 2.9, 0.18, 0.18, 1.6, "#3a414d");
    const night = new THREE.Mesh(new THREE.PlaneGeometry(9, 1.7), glow(0x0c1a33)); night.position.set(0, 3.55, 2.95); night.rotation.x = Math.PI / 2; g.add(night);
    for (let k = 0; k < 40; k++) { const s = new THREE.Mesh(new THREE.SphereGeometry(0.012, 4, 3), glow(0xfff6d0)); s.position.set(-4.3 + Math.random() * 8.6, 3.6, 2.3 + Math.random() * 1.3); g.add(s); }
    const moon = new THREE.Mesh(new THREE.CircleGeometry(0.22, 24), glow(0xfff1d0)); moon.position.set(1.6, 3.58, 3.4); moon.rotation.x = Math.PI / 2; g.add(moon);
    w.box(g, 0, -3.4, 2, 9, 0.2, 4, "#2c323c"); w.box(g, -4.5, 0, 2, 0.2, 7, 4, "#2c323c"); w.box(g, 4.5, 0, 2, 0.2, 7, 4, "#2c323c");
    w.box(g, 0, 0, 4.05, 9, 7, 0.1, "#1f242c");
    // consoles along the windows, their screens green and amber
    for (const x of [-3.2, -1.4, 1.4, 3.2]) {
      w.box(g, x, 2.6, 0.55, 1.5, 0.8, 1.0, "#39404c");
      const sc = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 0.35), glow(x < 0 ? 0x5fe0a0 : 0xffc25a)); sc.position.set(x, 2.19, 1.0); sc.rotation.x = Math.PI / 2 - 0.5; g.add(sc);
    }
    // the wheel
    const wheel = new THREE.Group(); wheel.position.set(0, 1.9, 1.15); wheel.rotation.x = Math.PI / 2 - 0.2; g.add(wheel);
    const rim = new THREE.Mesh(new THREE.TorusGeometry(0.42, 0.04, 8, 32), w.mat("#8a5a32")); wheel.add(rim);
    for (let k = 0; k < 8; k++) { const sp = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 1.05, 6), w.mat("#8a5a32")); sp.rotation.z = k * Math.PI / 8; wheel.add(sp); }
    w.cyl(g, [0, 2.05, 0], [0, 2.05, 1.1], 0.09, "#39404c", 10);
    const lamp = new THREE.PointLight(0x7fe8c0, 3, 7, 1.6); lamp.position.set(0, 2.3, 1.4); g.add(lamp);
    const red = new THREE.PointLight(0xff5040, 1.4, 9, 1.4); red.position.set(0, 0, 3.6); g.add(red);
    w.hooks.push(() => { if (g.visible) wheel.rotation.z = Math.sin(w.time * 0.4) * 0.25; });
  },

  deck(w, g) {
    sea(w, g, 300, "#2b5d8c");
    // the forward deck, the rails, the anchor windlass and its chain, the mooring lines
    w.box(g, 0, 0, 1.1, 10, 18, 0.3, "#7d8a92");
    for (const s of [-1, 1]) { for (let y = -8; y <= 8; y += 1.6) w.cyl(g, [s * 4.9, y, 1.25], [s * 4.9, y, 2.2], 0.04, "#d8dde0", 6); w.cyl(g, [s * 4.9, -8.5, 2.2], [s * 4.9, 8.5, 2.2], 0.05, "#d8dde0", 6); }
    w.box(g, 0, 5.5, 1.75, 2.2, 1.6, 1.0, "#a33a2e"); w.cyl(g, [-1.4, 5.5, 2.0], [1.4, 5.5, 2.0], 0.4, "#3b3f44", 16);
    const chain = new THREE.Group(); g.add(chain);
    for (let k = 0; k < 18; k++) {
      const l = new THREE.Mesh(new THREE.TorusGeometry(0.16, 0.05, 6, 12), w.mat("#4a4e54"));
      l.position.set(0, 6.4 + k * 0.28, 1.3 - Math.max(0, k - 8) * 0.25); l.rotation.y = k % 2 ? Math.PI / 2 : 0; chain.add(l);
    }
    for (const [x, y] of [[-3.6, -5], [3.6, -5], [-3.6, 0.5], [3.6, 0.5]]) { w.cyl(g, [x, y, 1.25], [x, y, 1.7], 0.18, "#2f3338", 10); w.cyl(g, [x, y, 1.7], [x, y, 1.8], 0.25, "#2f3338", 10); }
    for (const [x, y] of [[-2.2, -2.6], [2.4, -3.4]]) for (let r = 0; r < 4; r++) { const c = new THREE.Mesh(new THREE.TorusGeometry(0.45 - r * 0.08, 0.06, 6, 20), w.mat("#c9a76a")); c.position.set(x, y, 1.32 + r * 0.07); g.add(c); }
    w.box(g, 0, -8.6, 3.4, 9, 1.4, 4.4, "#e8eaec"); w.box(g, 0, -8.0, 4.2, 6, 0.1, 1.0, "#2a3d52");
  },

  tokyo(w, g) {
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(160, 160), w.mat("#1d1f29")); g.add(ground);
    let s = 11; const rnd = () => ((s = (s * 16807) % 2147483647) / 2147483647);
    for (let k = 0; k < 70; k++) {
      const a = rnd() * Math.PI * 2, r = 9 + rnd() * 50, x = Math.cos(a) * r, y = Math.sin(a) * r;
      if (Math.abs(x) < 4 && y < 0) continue;
      const wd = 3 + rnd() * 5, h = 8 + rnd() * (r > 25 ? 60 : 30);
      const tex = windowsTexture(Math.round(wd * 2), Math.round(h * 1.2), 0.35 + rnd() * 0.35, "#ffe2a8", "#141826", k);
      const m = new THREE.Mesh(new THREE.BoxGeometry(wd, wd, h), new THREE.MeshBasicMaterial({ map: tex, fog: true }));
      m.position.set(x, y, h / 2); g.add(m);
      if (rnd() < 0.3) { const b = new THREE.Mesh(new THREE.SphereGeometry(0.35, 8, 6), glow(0xff3b3b)); b.position.set(x, y, h + 0.4); g.add(b); }
    }
    // a big screen, and a red tower in the distance
    const screen = new THREE.Mesh(new THREE.PlaneGeometry(6, 3.5), glow(0x6ab8ff)); screen.position.set(-6, 9, 9); screen.rotation.x = Math.PI / 2; screen.rotation.y = 0.5; g.add(screen);
    w.hooks.push(() => { if (g.visible) screen.material.color.setHSL((w.time * 0.03) % 1, 0.6, 0.6); });
    const tower = new THREE.Group(); tower.position.set(10, 70, 0); g.add(tower);
    for (let k = 0; k < 6; k++) w.cyl(tower, [0, 0, k * 8], [0, 0, k * 8 + 8], 2.6 - k * 0.38, k % 2 ? "#f2f2f2" : "#e2462f", 8, 2.6 - (k + 1) * 0.38);
    const flash = new THREE.PointLight(0xffffff, 0, 8, 1.5); flash.position.set(0, -2.5, 1.6); g.add(flash);
    g.userData.flash = flash;
  },

  museum(w, g) {
    const ground = new THREE.Mesh(new THREE.CircleGeometry(70, 60), w.mat("#7cab5e")); ground.receiveShadow = true; g.add(ground);
    for (const [x, y, r, h] of [[-26, 30, 18, 6], [18, 40, 22, 9], [40, 10, 16, 5], [-40, -6, 18, 7], [6, 60, 30, 14]]) {
      const hill = new THREE.Mesh(new THREE.SphereGeometry(r, 18, 10), w.mat(h > 8 ? "#4f7d46" : "#6d9a55")); hill.scale.set(1, 1, h / r); hill.position.set(x, y, 0); g.add(hill);
    }
    // sculptures in the grass: a great bronze figure, an arch, a stack of colour, a head of stone
    const bronze = "#7a5a3a";
    w.ball(g, -5, 6, 1.2, 1.2, bronze); w.ball(g, -5, 6, 3.0, 0.9, bronze); w.ball(g, -5, 6, 4.4, 0.6, bronze);
    w.cyl(g, [-5.8, 6, 0], [-5.4, 6, 1.0], 0.25, bronze, 8); w.cyl(g, [-4.2, 6, 0], [-4.6, 6, 1.0], 0.25, bronze, 8);
    const arch = new THREE.Mesh(new THREE.TorusGeometry(2.6, 0.35, 10, 40, Math.PI), w.mat("#c9c3b8")); arch.position.set(5, 9, 0); arch.rotation.x = Math.PI / 2; g.add(arch);
    for (const [k, c] of ["#e2462f", "#f2c94c", "#3a7bd5", "#f2f2f2", "#2fae6e"].entries()) {
      const b = w.box(g, 10, 2, 0.6 + k * 1.15, 1.6 - k * 0.12, 1.6 - k * 0.12, 1.1, c); b.rotation.z = k * 0.4;
    }
    const head = new THREE.Mesh(new THREE.SphereGeometry(1.6, 14, 10), w.mat("#9a948a")); head.scale.set(0.8, 0.9, 1.1); head.position.set(-11, 14, 1.7); g.add(head);
    w.box(g, 0, -2, 0.03, 2.4, 40, 0.04, "#d9cdb4");
  },

  snow(w, g) {
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(140, 140, 30, 30), w.mat("#f1f4f8")); g.add(ground);
    const p = ground.geometry.attributes.position.array;
    for (let i = 0; i < p.length; i += 3) p[i + 2] = Math.max(0, p[i + 1]) * 0.28 + Math.sin(p[i] * 0.2) * 0.4;
    ground.geometry.computeVertexNormals();
    for (let k = 0; k < 60; k++) {
      const x = (Math.random() - 0.5) * 70, y = 8 + Math.random() * 50; if (Math.abs(x) < 6) continue;
      const z = y * 0.28, s = 0.8 + Math.random() * 0.8;
      w.cyl(g, [x, y, z], [x, y, z + 0.8 * s], 0.15 * s, "#5a3e2a", 6);
      for (let t = 0; t < 3; t++) { const c = new THREE.Mesh(new THREE.ConeGeometry((1.3 - t * 0.35) * s, 1.5 * s, 8), w.mat(t % 2 ? "#3e6b4b" : "#2f5a3e")); c.rotation.x = Math.PI / 2; c.position.set(x, y, z + (1.2 + t * 0.9) * s); g.add(c); }
    }
    fall(w, g, { n: 700, box: [40, 40, 14], color: 0xffffff, size: 0.12, speed: 1.1, drift: 0.6 });
  },

  street(w, g) {
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), w.mat("#3a3a40")); g.add(ground);
    w.box(g, 0, 0, 0.02, 3.2, 60, 0.02, "#45454c");
    let s = 5; const rnd = () => ((s = (s * 16807) % 2147483647) / 2147483647);
    for (const side of [-1, 1]) for (let y = -24; y < 24; y += 4.2) {
      const h = 3 + rnd() * 2.5, wd = 3.6;
      w.box(g, side * 4.1, y, h / 2, 4.4, wd, h, ["#6b5a4a", "#5a5f66", "#7a6a5a", "#4f555c"][Math.floor(rnd() * 4)]);
      const win = new THREE.Mesh(new THREE.PlaneGeometry(1.4, 1.0), glow(rnd() < 0.7 ? 0xffd08a : 0x9fc8ff)); win.position.set(side * 1.88, y + 0.6, 1.9); win.rotation.y = side * -Math.PI / 2; win.rotation.x = Math.PI / 2; g.add(win);
      // paper lanterns
      const lan = new THREE.Mesh(new THREE.SphereGeometry(0.22, 10, 8), glow(0xff8a5a)); lan.scale.z = 1.3; lan.position.set(side * 1.7, y - 1.2, 2.6); g.add(lan);
      const L = new THREE.PointLight(0xff9a6a, 1.6, 5, 1.6); L.position.copy(lan.position); g.add(L);
    }
    // a glowing vending machine, and a corner store that never closes
    w.box(g, -1.6, 2.4, 0.9, 0.7, 0.6, 1.8, "#e8eef2");
    const vm = new THREE.Mesh(new THREE.PlaneGeometry(0.55, 1.3), glow(0xbfe8ff)); vm.position.set(-1.24, 2.4, 1.0); vm.rotation.y = Math.PI / 2; vm.rotation.x = Math.PI / 2; g.add(vm);
    const shop = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 1.8), glow(0xf4fbff)); shop.position.set(1.86, 8, 1.2); shop.rotation.y = -Math.PI / 2; shop.rotation.x = Math.PI / 2; g.add(shop);
    for (const [c, z] of [["#2fae6e", 2.25], ["#e2462f", 2.4], ["#f29a2f", 2.55]]) { const b = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 0.12), glow(new THREE.Color(c).getHex())); b.position.set(1.85, 8, z); b.rotation.y = -Math.PI / 2; b.rotation.x = Math.PI / 2; g.add(b); }
    const sl = new THREE.PointLight(0xf4fbff, 3, 8, 1.4); sl.position.set(1.2, 8, 1.4); g.add(sl);
  },

  tvroom(w, g) {
    w.box(g, 0, 0, 0.03, 8, 8, 0.06, "#6a5240");
    w.box(g, 0, 3.4, 1.6, 8, 0.15, 3.2, "#3a3446"); w.box(g, -3.4, 0, 1.6, 0.15, 8, 3.2, "#36303f");
    const win = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 1.2), glow(0x14234a)); win.position.set(-3.32, 0.8, 1.8); win.rotation.y = Math.PI / 2; win.rotation.x = Math.PI / 2; g.add(win);
    for (let k = 0; k < 10; k++) { const s = new THREE.Mesh(new THREE.SphereGeometry(0.012, 4, 3), glow(0xfff6d0)); s.position.set(-3.3, 0.2 + Math.random() * 1.2, 1.3 + Math.random() * 1.0); g.add(s); }
    // the couch, a blanket, and the television's light
    w.box(g, 0, -0.6, 0.25, 2.6, 1.0, 0.5, "#7a3a4a"); w.box(g, 0, -1.05, 0.7, 2.6, 0.3, 0.9, "#7a3a4a");
    for (const x of [-1.3, 1.3]) w.box(g, x, -0.6, 0.45, 0.25, 1.0, 0.5, "#6a3040");
    w.box(g, 0.4, -0.5, 0.52, 1.0, 0.9, 0.05, "#e9d8b0");
    w.box(g, 0, 3.1, 0.35, 2.2, 0.5, 0.7, "#2a2630");
    const tv = new THREE.Mesh(new THREE.PlaneGeometry(1.9, 1.1), glow(0x9fd0ff)); tv.position.set(0, 3.0, 1.35); tv.rotation.x = Math.PI / 2; g.add(tv);
    w.box(g, 0, 3.05, 1.35, 2.0, 0.06, 1.2, "#111");
    const L = new THREE.PointLight(0x9fd0ff, 4, 7, 1.5); L.position.set(0, 2.4, 1.3); g.add(L);
    const lampL = new THREE.PointLight(0xffc88a, 2.2, 6, 1.6); lampL.position.set(-2.4, -2.4, 1.6); g.add(lampL);
    w.ball(g, -2.4, -2.4, 1.6, 0.18, "#ffd59a", { emissive: new THREE.Color("#ffb060"), emissiveIntensity: 1 });
    w.hooks.push(() => {
      if (!g.visible) return;
      const f = 0.75 + 0.25 * Math.sin(w.time * 7.3) * Math.sin(w.time * 2.1);
      L.intensity = 3.2 * f; tv.material.color.setHSL(0.58 + 0.06 * Math.sin(w.time * 0.6), 0.6, 0.6 + 0.1 * f);
    });
  },

  base(w, g) {
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), w.mat("#3b4148")); g.add(ground);
    const tex = windowsTexture(14, 6, 0.4, "#ffd98a", "#2a2f3a", 3);
    const bar = new THREE.Mesh(new THREE.BoxGeometry(22, 6, 9), [w.mat("#5a606a"), w.mat("#5a606a"), new THREE.MeshBasicMaterial({ map: tex }), w.mat("#5a606a"), w.mat("#4a5058"), w.mat("#4a5058")]);
    bar.position.set(0, 9, 4.5); g.add(bar);
    for (const x of [-8, 0, 8]) { w.cyl(g, [x, 2, 0], [x, 2, 4.2], 0.08, "#2a2e33", 6); const l = new THREE.Mesh(new THREE.SphereGeometry(0.22, 8, 6), glow(0xffe0a0)); l.position.set(x, 2, 4.3); g.add(l); const L = new THREE.PointLight(0xffd59a, 4.5, 11, 1.4); L.position.set(x, 2, 4.1); g.add(L); }
    fall(w, g, { n: 900, box: [30, 26, 12], color: 0xa8c4e0, size: 0.06, speed: 9, drift: 0.05, streak: true });
  },

  pumpkin(w, g) {
    const ground = new THREE.Mesh(new THREE.CircleGeometry(40, 40), w.mat("#5a4a2e")); g.add(ground);
    for (let k = 0; k < 40; k++) { const l = new THREE.Mesh(new THREE.CircleGeometry(0.25, 5), w.mat(["#c9692f", "#a8452a", "#d8a03a"][k % 3])); l.position.set((Math.random() - 0.5) * 10, (Math.random() - 0.5) * 10, 0.01); g.add(l); }
    const pumpkins = [];
    const make = (x, y, r, lit) => {
      const p = new THREE.Group(); p.position.set(x, y, r * 0.85); g.add(p);
      for (let k = 0; k < 8; k++) { const s = new THREE.Mesh(new THREE.SphereGeometry(r, 12, 10), w.mat("#e07a22")); s.scale.set(0.55, 1, 0.85); s.rotation.z = k * Math.PI / 8; p.add(s); }
      w.cyl(p, [0, 0, r * 0.8], [0.05, 0, r * 1.1], r * 0.1, "#4a6a2a", 6);
      if (lit) {
        for (const [ex, ez] of [[-0.3, 0.2], [0.3, 0.2]]) { const e = new THREE.Mesh(new THREE.CircleGeometry(r * 0.16, 3), glow(0xffd36b)); e.position.set(ex * r, -r * 0.9, ez * r); e.rotation.x = Math.PI / 2; p.add(e); }
        const m = new THREE.Mesh(new THREE.PlaneGeometry(r * 0.7, r * 0.18), glow(0xffd36b)); m.position.set(0, -r * 0.92, -r * 0.22); m.rotation.x = Math.PI / 2; p.add(m);
        const L = new THREE.PointLight(0xff9a3a, 2.2, 5, 1.6); L.position.set(0, -r * 1.2, 0); p.add(L); pumpkins.push(L);
      }
      return p;
    };
    make(-1.6, 0.6, 0.35, true); make(1.8, 0.2, 0.3, true); make(-0.6, 1.8, 0.28, false); make(1.0, 2.2, 0.4, true); make(2.6, -0.8, 0.25, false);
    // the big one, hollowed out, for the baby to sit in
    const big = make(0, 0, 0.55, false); g.userData.big = big;
    big.scale.z = 0.5; big.position.z = 0.24;            // squat and open-topped, a seat for the baby
    const hollow = new THREE.Mesh(new THREE.CircleGeometry(0.42, 20), w.mat("#f2c27a")); hollow.position.set(0, 0, 0.51); g.add(hollow);
    w.hooks.push(() => { if (g.visible) pumpkins.forEach((L, i) => (L.intensity = 2 + 0.5 * Math.sin(w.time * 6 + i * 1.7))); });
    // a camera on a little tripod
    w.cyl(g, [0.2, -2.6, 0], [0.2, -2.6, 1.1], 0.03, "#222", 5); w.box(g, 0.2, -2.6, 1.2, 0.3, 0.2, 0.2, "#222");
  },

  shore(w, g) {
    sea(w, g, 300, "#16243a").position.set(0, 60, -0.2);
    const sand = new THREE.Mesh(new THREE.PlaneGeometry(120, 30), w.mat("#4a4a4c")); sand.position.set(0, -5, 0.05); g.add(sand);
    for (let k = 0; k < 14; k++) w.ball(g, (Math.random() - 0.5) * 40, -6 + Math.random() * 6, 0.1, 0.3 + Math.random() * 0.6, "#2f3236");
    fall(w, g, { n: 1000, box: [30, 30, 12], color: 0x9fb4cc, size: 0.06, speed: 10, drift: 0.05, streak: true });
    // a cold light from the sea behind the figure, so it reads as a shape against the dark
    const rim = new THREE.PointLight(0x9fb8ff, 6, 14, 1.4); rim.position.set(0, 1.5, 3); g.add(rim);
    const lamp = new THREE.PointLight(0xffd59a, 1.4, 10, 1.6); lamp.position.set(-3, -7, 2); g.add(lamp);
  },
};

/** A place, built the first time a page needs it, and shown alone. */
export function need(w, name) {
  if (!w.places[name]) {
    const g = new THREE.Group(); g.position.copy(SPOTS[name]); g.visible = false; w.scene.add(g);
    w.places[name] = g;
    BUILD[name](w, g);
  }
  return w.places[name];
}

export const MEMORY_PLACES = Object.keys(BUILD);

/** Floating motes of light, drifting around the camera: the storytime's ethereal mode. */
export function motes(w) {
  if (w.moteField) return w.moteField;
  const n = 140, pos = new Float32Array(n * 3), base = [];
  for (let i = 0; i < n; i++) { const v = [(Math.random() - 0.5) * 8, Math.random() * 7 + 0.6, (Math.random() - 0.5) * 4]; base.push(v); pos.set(v, i * 3); }
  const geo = new THREE.BufferGeometry(); geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  const pts = new THREE.Points(geo, new THREE.PointsMaterial({ color: 0xfff0c8, size: 0.06, map: dot(), transparent: true, opacity: 0.75, depthWrite: false, blending: THREE.AdditiveBlending, fog: false }));
  pts.frustumCulled = false;
  w.camera.add(pts); w.scene.add(w.camera);
  pts.rotation.x = -Math.PI / 2;            // camera space: x across, y ahead, z up
  w.hooks.push(() => {
    if (!pts.visible) return;
    const t = w.time;
    for (let i = 0; i < n; i++) {
      const b = base[i];
      pos[i * 3] = b[0] + Math.sin(t * 0.21 + i) * 0.35;
      pos[i * 3 + 1] = b[1] + Math.sin(t * 0.13 + i * 1.7) * 0.25;
      pos[i * 3 + 2] = b[2] + Math.sin(t * 0.17 + i * 0.7) * 0.3 + ((t * 0.05 + i * 0.13) % 1) * 0.4;
    }
    geo.attributes.position.needsUpdate = true;
    pts.material.opacity = 0.55 + 0.2 * Math.sin(t * 0.8);
  });
  w.moteField = pts;
  return pts;
}
