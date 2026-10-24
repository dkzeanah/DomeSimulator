// Lesson Studio: a two_v_demo lesson drawn on the web engine (sketch_claude/lesson_web.py).
//
// A frame is a pure function of film time: which chapter, how far into it, the stage posed for
// that, the camera, and the chapter's graphics. So the preview, the stills and the render are the
// same picture. The words and their timing come from the server, timed by the house voice; the
// sound is mixed there too. This page only draws.
//
//   /lesson?lesson=2v                       preview: scrub, play (silent), pick a chapter
//   /lesson?lesson=2v&orient=phone          the 9:16 layout
//   /lesson?lesson=2v&stills=1              one still per chapter to tmp/lesson-stills/ (headless)
//   /lesson?lesson=2v&autorender=1          every frame to the render pipe, then the release (headless)

import * as THREE from "three";
import { Stage } from "/static/lessonstage.js";

const qs = new URLSearchParams(location.search);
const KEY = qs.get("lesson") || "2v";
let ORIENT = qs.get("orient") === "phone" ? "phone" : "landscape";
const log = (s) => { console.log(s); const el = document.getElementById("status"); if (el) el.textContent = s.replace(/^\[lesson[^\]]*\]\s*/, ""); };

const L = { spec: null, stage: null, renderer: null, scene: null, cam: null, W: 1920, H: 1080, pg: null };

async function boot() {
  L.spec = await (await fetch(`/api/lesson/${KEY}`)).json();
  document.title = `${L.spec.title} - Lesson Studio`;
  setup();
  if (qs.get("stills")) return stills();
  if (qs.get("autorender")) return render();
  preview();
}

function setup() {
  const W = ORIENT === "phone" ? 1080 : 1920, H = ORIENT === "phone" ? 1920 : 1080;
  L.W = W; L.H = H;
  const gl = document.getElementById("gl");
  if (!L.renderer) {
    L.renderer = new THREE.WebGLRenderer({ canvas: gl, antialias: true, preserveDrawingBuffer: true });
    L.renderer.setPixelRatio(1);
    L.renderer.shadowMap.enabled = true;
    L.renderer.outputColorSpace = THREE.SRGBColorSpace;
    L.scene = new THREE.Scene();
    buildWorld(L.scene);
    L.stage = new Stage(THREE, L.scene, L.spec.stage);
    L.cam = new THREE.PerspectiveCamera(36, W / H, 0.05, 400);
    L.cam.up.set(0, 0, 1);
  }
  L.renderer.setSize(W, H, false);
  L.cam.aspect = W / H; L.cam.updateProjectionMatrix();
  const pc = document.getElementById("program");
  pc.width = W; pc.height = H;
  L.pg = pc.getContext("2d");
}

// ------------------------------------------------------------ the world: a hilltop at dusk and an exhibit plinth
function buildWorld(scene) {
  const sky = document.createElement("canvas"); sky.width = 2; sky.height = 512;
  const g = sky.getContext("2d"), gr = g.createLinearGradient(0, 0, 0, 512);
  gr.addColorStop(0, "#162038"); gr.addColorStop(0.45, "#4b3d66"); gr.addColorStop(0.72, "#c9785a"); gr.addColorStop(1, "#f2c48d");
  g.fillStyle = gr; g.fillRect(0, 0, 2, 512);
  scene.background = new THREE.CanvasTexture(sky); scene.background.colorSpace = THREE.SRGBColorSpace;
  scene.fog = new THREE.Fog(0x6a4f5e, 40, 140);
  scene.add(new THREE.HemisphereLight(0xffe6c8, 0x2a2430, 1.15));
  const sun = new THREE.DirectionalLight(0xffc48a, 2.4);
  sun.position.set(-14, -18, 9); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, { left: -8, right: 8, top: 8, bottom: -8, near: 1, far: 60 });
  const rim = new THREE.DirectionalLight(0x9fc4ff, 0.9); rim.position.set(12, 14, 6);
  scene.add(sun, rim);
  const ground = new THREE.Mesh(new THREE.CircleGeometry(160, 64), new THREE.MeshLambertMaterial({ color: 0x3a3a2c }));
  ground.position.z = -0.32; ground.receiveShadow = true; scene.add(ground);
  const plinth = new THREE.Mesh(new THREE.CylinderGeometry(3.9, 4.1, 0.3, 64), new THREE.MeshStandardMaterial({ color: 0x232a35, roughness: 0.8 }));
  plinth.rotation.x = Math.PI / 2; plinth.position.z = -0.15; plinth.receiveShadow = true; scene.add(plinth);
  const ring = new THREE.Mesh(new THREE.RingGeometry(3.6, 3.66, 96), new THREE.MeshBasicMaterial({ color: 0xffd27a, transparent: true, opacity: 0.55 }));
  ring.position.z = 0.005; scene.add(ring);
}

// ------------------------------------------------------------ time
function chapterAt(t) {
  const cs = L.spec.chapters;
  let i = cs.findIndex((c) => t < c.start + c.duration);
  if (i < 0) i = cs.length - 1;
  return { i, c: cs[i], p: Math.min(1, Math.max(0, (t - cs[i].start) / cs[i].duration)) };
}

function drawFrame(t) {
  const { i, c, p } = chapterAt(t);
  L.stage.set(c.stage, p, t);
  // the chapter's own camera direction (the moderngl film's), the stage's framing, a slow drift
  const f = L.stage.frame(c.stage);
  const dir = (f.dir ? f.dir.clone() : new THREE.Vector3(...c.camera).normalize());
  const drift = (t - c.start) * (f.dir ? 0.012 : 0.035);
  dir.applyAxisAngle(new THREE.Vector3(0, 0, 1), drift);
  // the room the graphics leave: the sheet takes the right third of a wide frame, the lower
  // half of a phone frame. Put the subject in the middle of what is left, and stand back far
  // enough for its width to fit there (the phone-cut lesson: frame for the frame you have).
  const phone = ORIENT === "phone", sheet = (c.equations || []).length > 0;
  const fx = phone ? 0.5 : sheet ? 0.33 : 0.5, fy = phone ? 0.34 : 0.48, room = phone ? 0.86 : sheet ? 0.6 : 0.86;
  const hfov = 2 * Math.atan(Math.tan((L.cam.fov * Math.PI) / 360) * L.cam.aspect);
  const fit = f.half / Math.tan(hfov / 2) / room;
  const dist = Math.max(f.dist * (phone ? 1.05 : 1.0), fit * 1.08) * (1.04 - 0.04 * p);
  L.cam.setViewOffset(L.W, L.H, (0.5 - fx) * L.W, (0.5 - fy) * L.H, L.W, L.H);
  L.cam.position.copy(f.target).addScaledVector(dir, dist);
  L.cam.lookAt(f.target);
  L.renderer.render(L.scene, L.cam);
  const g = L.pg, W = L.W, H = L.H;
  g.drawImage(L.renderer.domElement, 0, 0, W, H);
  overlays(g, W, H, t, i, c, p);
}

// ------------------------------------------------------------ graphics
const INK = "#fff7e8", MUTED = "#c9c1b2", GOLD = "#ffd27a";

function overlays(g, W, H, t, i, c, p) {
  const k = ORIENT === "phone" ? W / 1080 : W / 1920, phone = ORIENT === "phone";
  const local = t - c.start, n = L.spec.chapters.length;
  // the fade between chapters
  const edge = Math.min(local, c.start + c.duration - t);
  // beat number, top left, on every frame
  g.save();
  g.font = `800 ${46 * k}px Inter, Segoe UI, sans-serif`;
  const bx = 40 * k, by = 40 * k, bw = 112 * k, bh = 74 * k;
  g.fillStyle = "rgba(10,13,20,0.72)"; rr(g, bx, by, bw, bh, 14 * k); g.fill();
  g.fillStyle = GOLD; g.textBaseline = "middle"; g.fillText(c.number, bx + 18 * k, by + bh / 2 + 2 * k);
  g.font = `600 ${18 * k}px Inter, Segoe UI, sans-serif`; g.fillStyle = MUTED; g.fillText(`/ ${n}`, bx + 74 * k, by + bh / 2 + 4 * k);
  if (local > L.spec.titleHold) {
    g.font = `600 ${24 * k}px Inter, Segoe UI, sans-serif`; g.fillStyle = INK;
    g.fillText(c.title, bx + bw + 16 * k, by + bh / 2);
  }
  // the brand, top right (landscape) or under the badge (phone)
  g.font = `700 ${16 * k}px Inter, Segoe UI, sans-serif`; g.fillStyle = MUTED; g.textAlign = phone ? "left" : "right";
  g.fillText(L.spec.brand, phone ? bx : W - 40 * k, phone ? by + bh + 28 * k : by + 22 * k);
  g.textAlign = "left";
  // the title card
  const hold = L.spec.titleHold, a = local < hold ? Math.min(1, local / 0.35, (hold - local) / 0.45 + 0.0) : 0;
  if (a > 0) {
    g.globalAlpha = Math.max(0, Math.min(1, a));
    const ty = phone ? H * 0.17 : H * 0.62, tw = phone ? W - 80 * k : W * 0.56;
    g.fillStyle = "rgba(10,13,20,0.78)"; rr(g, 40 * k, ty, tw, 168 * k, 18 * k); g.fill();
    g.fillStyle = GOLD; g.font = `700 ${22 * k}px Inter, Segoe UI, sans-serif`; g.fillText(`CHAPTER ${c.number}`, 70 * k, ty + 40 * k);
    g.fillStyle = INK; g.font = `800 ${phone ? 50 : 54}px Inter, Segoe UI, sans-serif`.replace(/\d+px/, (m) => `${parseInt(m) * k}px`);
    wrap(g, c.title, 70 * k, ty + 92 * k, tw - 60 * k, 58 * k, 1);
    g.fillStyle = MUTED; g.font = `500 ${22 * k}px Inter, Segoe UI, sans-serif`;
    wrap(g, c.promise, 70 * k, ty + 140 * k, tw - 60 * k, 28 * k, 1);
    g.globalAlpha = 1;
  }
  // the equation sheet: each line arrives as the narration reaches it
  const eqs = c.equations || [];
  if (eqs.length && local > hold * 0.7) {
    const sx = phone ? 40 * k : W * 0.635, sw = phone ? W - 80 * k : W * 0.33;
    const lineH = 46 * k, sh = 74 * k + eqs.length * lineH + (c.computed ? 30 * k : 0);
    const sy = phone ? H * 0.60 : H * 0.20;
    g.globalAlpha = Math.min(1, (local - hold * 0.7) / 0.5);
    g.fillStyle = "rgba(10,13,20,0.80)"; rr(g, sx, sy, sw, sh, 16 * k); g.fill();
    g.strokeStyle = "rgba(255,210,122,0.35)"; g.lineWidth = 1.5 * k; rr(g, sx, sy, sw, sh, 16 * k); g.stroke();
    g.fillStyle = GOLD; g.font = `700 ${17 * k}px Inter, Segoe UI, sans-serif`; g.fillText("THE ARITHMETIC", sx + 24 * k, sy + 36 * k);
    eqs.forEach((e, j) => {
      const due = c.speechStart + c.speech * (0.12 + 0.75 * (j / Math.max(1, eqs.length)));
      const on = Math.max(0, Math.min(1, (t - due) / 0.4));
      if (on <= 0) return;
      g.globalAlpha = Math.min(g.globalAlpha, 1) * 0 + on;
      g.fillStyle = j === eqs.length - 1 ? INK : "#e8e0cf";
      g.font = `${j === eqs.length - 1 ? 700 : 500} ${(eqs.some((x) => x.length > 44) ? 21 : 24) * k}px Consolas, "Cascadia Mono", monospace`;
      wrap(g, e, sx + 24 * k, sy + 78 * k + j * lineH, sw - 48 * k, 26 * k, 2);
    });
    g.globalAlpha = 1;
    if (c.computed) {
      g.fillStyle = MUTED; g.font = `500 ${14 * k}px Inter, Segoe UI, sans-serif`;
      g.fillText("computed by two_v_demo/geometry.py", sx + 24 * k, sy + sh - 18 * k);
    }
  }
  // captions: the release's own subtitle cues
  const cue = L.spec.captions.find(([a0, b0]) => t >= a0 && t < b0);
  if (cue) {
    g.font = `600 ${(phone ? 38 : 34) * k}px Inter, Segoe UI, sans-serif`;
    const maxW = phone ? W - 100 * k : W * 0.62, lines = split(g, cue[2], maxW);
    const lh = (phone ? 48 : 44) * k, boxH = lines.length * lh + 26 * k;
    const cy = phone ? H * 0.88 - boxH : H - 70 * k - boxH, cx = W / 2;
    const bwid = Math.max(...lines.map((l) => g.measureText(l).width)) + 48 * k;
    g.fillStyle = "rgba(8,10,16,0.78)"; rr(g, cx - bwid / 2, cy, bwid, boxH, 12 * k); g.fill();
    g.fillStyle = INK; g.textAlign = "center";
    lines.forEach((l, j) => g.fillText(l, cx, cy + 13 * k + lh * (j + 0.72)));
    g.textAlign = "left";
  }
  // where we are in the film
  g.fillStyle = "rgba(255,255,255,0.12)"; g.fillRect(0, H - 6 * k, W, 6 * k);
  g.fillStyle = GOLD; g.fillRect(0, H - 6 * k, W * (t / L.spec.total), 6 * k);
  // a short dip between chapters
  if (edge < 0.18 && i > 0 && local < 0.18) { g.fillStyle = `rgba(0,0,0,${0.6 * (1 - edge / 0.18)})`; g.fillRect(0, 0, W, H); }
  g.restore();
}

function rr(g, x, y, w, h, r) { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); }
function split(g, text, maxW) {
  const words = String(text).split(/\s+/), out = [];
  let line = "";
  for (const w of words) { const tr = line ? line + " " + w : w; if (g.measureText(tr).width > maxW && line) { out.push(line); line = w; } else line = tr; }
  if (line) out.push(line);
  return out;
}
function wrap(g, text, x, y, maxW, lh, maxLines) {
  split(g, text, maxW).slice(0, maxLines).forEach((l, j) => g.fillText(l, x, y + j * lh));
}

// ------------------------------------------------------------ stills, render, preview
async function post(url, body, tries = 5) {
  for (let k = 0; ; k++) {
    try { const r = await fetch(url, { method: "POST", body }); if (r.ok) return r; if (k >= tries) throw new Error(`${r.status} ${await r.text()}`); }
    catch (e) { if (k >= tries) throw e; }
    await new Promise((res) => setTimeout(res, 300 * (k + 1)));
  }
}
const blob = (type, q) => new Promise((r) => document.getElementById("program").toBlob(r, type, q));

async function stills() {
  try {
    for (const [n, c] of L.spec.chapters.entries()) {
      drawFrame(c.start + c.duration * 0.62);
      await post(`/api/lesson-still?lesson=${KEY}&orient=${ORIENT}&n=${n}`, await blob("image/png"));
      log(`[lesson] still ${n + 1} of ${L.spec.chapters.length}`);
    }
    log("[lesson-done] stills");
  } catch (e) { log(`[lesson-failed] ${e.message}`); }
}

async function render() {
  const fps = L.spec.fps, frames = Math.ceil(L.spec.total * fps), draft = qs.get("draft") === "1";
  try {
    const job = await (await post("/api/render/start", JSON.stringify({ slug: `lesson-${KEY}-${ORIENT}`, fps, draft }))).json();
    const inflight = [], wall = performance.now();
    for (let n = 0; n < frames; n++) {
      drawFrame(n / fps);
      inflight.push(post(`/api/render/frame?id=${job.id}&n=${n}`, await blob("image/jpeg", 0.93)));
      if (inflight.length > 4) await inflight.shift();
      if (n % (fps * 5) === 0) log(`[lesson] ${ORIENT} ${(n / fps).toFixed(0)} of ${L.spec.total.toFixed(0)} s (${(n / ((performance.now() - wall) / 1000)).toFixed(1)} fps)`);
    }
    await Promise.all(inflight);
    log("[lesson] mixing the sound and filing the release...");
    const res = await (await post(`/api/lesson-finish?id=${job.id}`, JSON.stringify({ lesson: KEY, orient: ORIENT }))).json();
    log(`[lesson-done] ${JSON.stringify(res)}`);
  } catch (e) { log(`[lesson-failed] ${e.message}`); }
}

function preview() {
  const scrub = document.getElementById("scrub"), sel = document.getElementById("chapter"), clock = document.getElementById("clock");
  const orient = document.getElementById("orient");
  orient.value = ORIENT;
  sel.innerHTML = L.spec.chapters.map((c, i) => `<option value="${i}">${c.number} ${c.title}</option>`).join("");
  let t = 0, playing = false, last = 0;
  const show = () => {
    drawFrame(t);
    scrub.value = Math.round((t / L.spec.total) * 1000);
    clock.textContent = `${Math.floor(t / 60)}:${String(Math.floor(t % 60)).padStart(2, "0")} / ${Math.floor(L.spec.total / 60)}:${String(Math.floor(L.spec.total % 60)).padStart(2, "0")}`;
    sel.value = String(chapterAt(t).i);
  };
  scrub.oninput = () => { t = (scrub.value / 1000) * L.spec.total; show(); };
  sel.onchange = () => { t = L.spec.chapters[+sel.value].start + 0.01; show(); };
  orient.onchange = () => { ORIENT = orient.value; setup(); show(); };
  document.getElementById("play").onclick = (e) => { playing = !playing; e.target.textContent = playing ? "Pause" : "Play"; last = performance.now(); };
  const tick = (now) => {
    if (playing) { t = Math.min(L.spec.total, t + (now - last) / 1000); last = now; show(); if (t >= L.spec.total) playing = false; }
    requestAnimationFrame(tick);
  };
  show();
  log(`${L.spec.chapters.length} chapters, ${L.spec.total.toFixed(1)} s. The picture only: the sound is mixed with the render.`);
  requestAnimationFrame(tick);
}

boot().catch((e) => log(`[lesson-failed] ${e.message}`));
