// The camera department: lenses, composition guides, letterboxing, first-person walk, drone,
// automated cinematic moves, a keyframe sequencer, and the program feed that gets recorded.

import { clock } from "/static/clock.js";

const E = {
  linear: (t) => t,
  smooth: (t) => t * t * (3 - 2 * t),
  smoother: (t) => t * t * t * (t * (t * 6 - 15) + 10),
  outCubic: (t) => 1 - Math.pow(1 - t, 3),
  inOutSine: (t) => -(Math.cos(Math.PI * t) - 1) / 2,
};
export const EASE = E;

export function fovForLens(mm) { return 2 * Math.atan(24 / (2 * mm)) * 180 / Math.PI; }   // full-frame, vertical

export class Cine {
  constructor(ctx) {
    this.ctx = ctx;
    const T = ctx.THREE;
    this.T = T;
    this.mode = "edit";              // edit | walk | drone | shot
    this.lens = 35;
    this.aspect = "off";             // off | 16:9 | 2.39 | 1.85 | 9:16 | 1:1
    this.guides = { thirds: true, centre: false, safe: false };
    this.keys = new Set();
    this.yaw = 0; this.pitch = 0; this.roll = 0;
    this.vel = new T.Vector3();
    this.droneSpeed = 4;
    this.shot = null;               // {dur, at(t), t0, onEnd}
    this.titles = [];               // program graphics: [{text, sub, until, kind}]
    this.subtitle = null;           // {name, text}
    this.fade = 0;                  // 0..1 to black
    this.recording = null;
    this.audio = null;              // set by the cast: an AudioContext and its recordable destination
    this.overlay = this.makeOverlay();
    this.program = document.createElement("canvas");
    this.program.width = 1920; this.program.height = 1080;
    this.pg = this.program.getContext("2d");
    ctx.hooks.push((dt, now) => this.tick(dt, now));
    ctx.post.push(() => this.compose());
    this.bindInput();
  }

  // ------------------------------------------------------------ lens
  setLens(mm) {
    this.lens = mm;
    this.ctx.persp.fov = fovForLens(mm);
    this.ctx.persp.updateProjectionMatrix();
  }

  // ------------------------------------------------------------ overlay: guides and the frame
  makeOverlay() {
    const c = document.createElement("canvas");
    c.className = "cine-overlay";
    this.ctx.canvas.parentElement.append(c);
    new ResizeObserver(() => { c.width = c.clientWidth * devicePixelRatio; c.height = c.clientHeight * devicePixelRatio; }).observe(c);
    return c;
  }

  frameRect(w, h) {
    const want = { "16:9": 16 / 9, "2.39": 2.39, "1.85": 1.85, "9:16": 9 / 16, "1:1": 1 }[this.aspect];
    if (!want) return { x: 0, y: 0, w, h };
    let fw = w, fh = w / want;
    if (fh > h) { fh = h; fw = h * want; }
    return { x: (w - fw) / 2, y: (h - fh) / 2, w: fw, h: fh };
  }

  drawGraphics(g, w, h, live) {
    const r = this.frameRect(w, h);
    // letterbox / pillarbox
    if (this.aspect !== "off") {
      g.fillStyle = live ? "rgba(0,0,0,0.78)" : "#000";
      g.fillRect(0, 0, w, r.y); g.fillRect(0, r.y + r.h, w, h - r.y - r.h);
      g.fillRect(0, 0, r.x, h); g.fillRect(r.x + r.w, 0, w - r.x - r.w, h);
    }
    if (live) {
      g.strokeStyle = "rgba(255,255,255,0.55)"; g.lineWidth = 1 * devicePixelRatio;
      if (this.guides.thirds) {
        g.beginPath();
        for (const k of [1 / 3, 2 / 3]) {
          g.moveTo(r.x + r.w * k, r.y); g.lineTo(r.x + r.w * k, r.y + r.h);
          g.moveTo(r.x, r.y + r.h * k); g.lineTo(r.x + r.w, r.y + r.h * k);
        }
        g.stroke();
        g.fillStyle = "rgba(255,255,255,0.7)";
        for (const a of [1 / 3, 2 / 3]) for (const b of [1 / 3, 2 / 3]) { g.beginPath(); g.arc(r.x + r.w * a, r.y + r.h * b, 3 * devicePixelRatio, 0, 7); g.fill(); }
      }
      if (this.guides.centre) {
        const cx = r.x + r.w / 2, cy = r.y + r.h / 2, s = 14 * devicePixelRatio;
        g.beginPath(); g.moveTo(cx - s, cy); g.lineTo(cx + s, cy); g.moveTo(cx, cy - s); g.lineTo(cx, cy + s); g.stroke();
      }
      if (this.guides.safe) {
        g.setLineDash([6, 4]);
        g.strokeRect(r.x + r.w * 0.05, r.y + r.h * 0.05, r.w * 0.9, r.h * 0.9);      // action safe
        g.strokeRect(r.x + r.w * 0.1, r.y + r.h * 0.1, r.w * 0.8, r.h * 0.8);        // title safe
        g.setLineDash([]);
      }
      if (this.mode === "walk" || this.mode === "drone") this.drawHud(g, r);
      if (this.recording) {
        g.fillStyle = "#d22"; g.beginPath(); g.arc(r.x + 22 * devicePixelRatio, r.y + 22 * devicePixelRatio, 7 * devicePixelRatio, 0, 7); g.fill();
        g.fillStyle = "#fff"; g.font = `${13 * devicePixelRatio}px Segoe UI`;
        g.fillText(`REC ${fmtTime((clock.now() - this.recording.t0) / 1000)}`, r.x + 36 * devicePixelRatio, r.y + 27 * devicePixelRatio);
      }
    }
    if (this.grade === "inner" || this.grade === "vision") {
      const cx = r.x + r.w / 2, cy = r.y + r.h / 2, R = Math.hypot(r.w, r.h) / 2;
      const vg = g.createRadialGradient(cx, cy, R * (this.grade === "inner" ? 0.25 : 0.4), cx, cy, R);
      vg.addColorStop(0, "rgba(0,0,0,0)");
      vg.addColorStop(1, this.grade === "inner" ? "rgba(10,0,30,0.85)" : "rgba(255,240,255,0.6)");
      g.fillStyle = vg; g.fillRect(r.x, r.y, r.w, r.h);
      if (this.grade === "vision") {
        // the shimmer at the edge of a vision: slow rings
        const ph = (clock.now() / 900) % 1;
        g.strokeStyle = "rgba(255,255,255,0.18)"; g.lineWidth = r.h * 0.01;
        for (let k = 0; k < 3; k++) { g.beginPath(); g.arc(cx, cy, R * (0.55 + ((ph + k / 3) % 1) * 0.5), 0, Math.PI * 2); g.stroke(); }
      }
    }
    this.drawTitles(g, r, live ? devicePixelRatio : w / 1280);
    if (this.flash) {
      const k = 1 - (clock.now() - this.flash.t0) / (this.flash.dur * 1000);
      if (k > 0) { g.fillStyle = `rgba(255,255,255,${Math.min(1, k * 1.4)})`; g.fillRect(r.x, r.y, r.w, r.h); } else this.flash = null;
    }
    if (this.fade > 0) { g.fillStyle = `rgba(0,0,0,${this.fade})`; g.fillRect(r.x, r.y, r.w, r.h); }
  }

  drawHud(g, r) {
    const k = devicePixelRatio, p = this.ctx.camera.position;
    g.fillStyle = "rgba(0,0,0,0.45)"; g.fillRect(r.x + 10 * k, r.y + r.h - 64 * k, 250 * k, 54 * k);
    g.fillStyle = "#fff"; g.font = `${12 * k}px Consolas, monospace`;
    const head = ((90 - this.yaw * 180 / Math.PI) % 360 + 360) % 360;
    g.fillText(this.mode === "drone" ? `DRONE  alt ${(p.z + 0.45).toFixed(1)} m  ${this.vel.length().toFixed(1)} m/s` : `WALK  eye ${(p.z - this.floorAt(p.x, p.y)).toFixed(2)} m`, r.x + 18 * k, r.y + r.h - 44 * k);
    g.fillText(`heading ${head.toFixed(0)}°  lens ${this.lens} mm`, r.x + 18 * k, r.y + r.h - 26 * k);
    if (this.mode === "walk" || this.mode === "drone") {
      const cx = r.x + r.w / 2, cy = r.y + r.h / 2;
      g.strokeStyle = "rgba(255,255,255,0.8)"; g.beginPath(); g.arc(cx, cy, 4 * k, 0, 7); g.stroke();
    }
  }

  drawTitles(g, r, k) {
    const now = clock.now();
    this.titles = this.titles.filter((t) => t.until > now);
    for (const t of this.titles) {
      const a = Math.min(1, (t.until - now) / 400, (now - t.from) / 400);
      g.globalAlpha = Math.max(0, a);
      if (t.kind === "card") {
        g.fillStyle = t.bg || "#1b1a17"; g.fillRect(r.x, r.y, r.w, r.h);
        g.fillStyle = t.color || "#f2d48a"; g.textAlign = "center";
        g.font = `800 ${r.h * 0.11}px "Segoe UI", sans-serif`;
        g.fillText(t.text, r.x + r.w / 2, r.y + r.h * 0.47);
        if (t.sub) {
          // the line under the title wraps to the frame (a "previously" runs to several lines)
          g.fillStyle = "#e9e4d8"; g.font = `${r.h * 0.04}px "Segoe UI", sans-serif`;
          const max = r.w * 0.78, lines = [];
          for (const word of String(t.sub).split(/\s+/)) {
            const cur = lines.length ? lines[lines.length - 1] : null;
            if (cur !== null && g.measureText(cur + " " + word).width <= max) lines[lines.length - 1] = cur + " " + word; else lines.push(word);
          }
          lines.forEach((ln, k) => g.fillText(ln, r.x + r.w / 2, r.y + r.h * (0.6 + k * 0.06)));
        }
        g.textAlign = "left";
      } else if (t.kind === "word") {
        // a word from the thought, hanging by the copy of him that thought it, drifting up
        const life = (now - t.from) / (t.until - t.from);
        const p = t.at.clone(); p.z += 0.25 + life * 0.5; p.x += (t.drift || 1) * life * 0.25;
        const v = p.project(this.ctx.persp);
        if (v.z < 1) {
          const x = r.x + (v.x + 1) / 2 * r.w, y = r.y + (1 - v.y) / 2 * r.h, fs = r.h * 0.05;
          g.font = `italic 700 ${fs}px Georgia, serif`; g.textAlign = "center";
          g.fillStyle = "rgba(255,230,160,0.95)"; g.shadowColor = "rgba(120,60,255,0.9)"; g.shadowBlur = fs * 0.6;
          g.fillText(t.text, x, y); g.shadowBlur = 0; g.textAlign = "left";
        }
      } else if (t.kind === "inner") {
        if (t.text) {
          const fs = r.h * 0.035; g.font = `italic ${fs}px Georgia, serif`; g.textAlign = "center"; g.fillStyle = "rgba(255,240,210,0.85)";
          g.fillText(t.text, r.x + r.w / 2, r.y + r.h * 0.12); g.textAlign = "left";
        }
      } else if (t.kind === "lower") {
        const x = r.x + r.w * 0.06, y = r.y + r.h * 0.74;
        g.fillStyle = "rgba(24,22,19,0.82)"; g.fillRect(x, y, r.w * 0.3, r.h * 0.09);
        g.fillStyle = "#c45e29"; g.fillRect(x, y, r.w * 0.006, r.h * 0.09);
        g.fillStyle = "#fff"; g.font = `700 ${r.h * 0.035}px "Segoe UI", sans-serif`; g.fillText(t.text, x + r.w * 0.02, y + r.h * 0.04);
        g.fillStyle = "#d9d3c7"; g.font = `${r.h * 0.024}px "Segoe UI", sans-serif`; g.fillText(t.sub || "", x + r.w * 0.02, y + r.h * 0.072);
      } else if (t.kind === "freeze") {
        // the freeze-frame narrator: a yellow caption box over a drained, held frame
        const fs = r.h * 0.045, x = r.x + r.w * 0.05, w = r.w * 0.62;
        g.font = `700 ${fs}px "Segoe UI", sans-serif`;
        const lines = wrap(g, t.text, w - fs);
        const h = lines.length * fs * 1.3 + fs * 0.8, y = r.y + r.h * 0.83 - h;
        g.fillStyle = "#f2d048"; g.fillRect(x, y, w, h);
        g.fillStyle = "#1b1a17"; lines.forEach((ln, i) => g.fillText(ln, x + fs * 0.5, y + fs * 1.25 + i * fs * 1.3));
      } else if (t.kind === "caption") {
        // the impact-font meme caption, top of frame
        const fs = r.h * 0.085;
        g.font = `900 ${fs}px Impact, "Arial Black", sans-serif`; g.textAlign = "center";
        const lines = wrap(g, t.text.toUpperCase(), r.w * 0.9);
        lines.forEach((ln, i) => { const y = r.y + r.h * 0.16 + i * fs * 1.05; g.lineWidth = fs * 0.12; g.strokeStyle = "#000"; g.strokeText(ln, r.x + r.w / 2, y); g.fillStyle = "#fff"; g.fillText(ln, r.x + r.w / 2, y); });
        g.textAlign = "left";
      } else if (t.kind === "pov") {
        // the phone-video caption: white text on a dark pill, centred near the top
        const fs = r.h * 0.045;
        g.font = `600 ${fs}px "Segoe UI", sans-serif`; g.textAlign = "center";
        const tw = g.measureText(t.text).width, x = r.x + r.w / 2, y = r.y + r.h * 0.18;
        g.fillStyle = "rgba(0,0,0,0.62)"; g.fillRect(x - tw / 2 - fs * 0.6, y - fs * 1.1, tw + fs * 1.2, fs * 1.6);
        g.fillStyle = "#fff"; g.fillText(t.text, x, y);
        g.textAlign = "left";
      } else if (t.kind === "figure") {
        const x = r.x + r.w * 0.66, y = r.y + r.h * 0.12;
        g.fillStyle = "rgba(255,253,247,0.92)"; g.fillRect(x, y, r.w * 0.3, r.h * 0.12);
        g.fillStyle = "#1b1a17"; g.font = `800 ${r.h * 0.05}px "Segoe UI", sans-serif`; g.fillText(t.text, x + r.w * 0.015, y + r.h * 0.065);
        g.fillStyle = "#6d6a63"; g.font = `${r.h * 0.022}px "Segoe UI", sans-serif`; g.fillText(t.sub || "", x + r.w * 0.015, y + r.h * 0.1);
      }
      g.globalAlpha = 1;
    }
    if (this.subtitle) {
      const fs = Math.max(12, r.h * 0.04);
      g.font = `600 ${fs}px "Segoe UI", sans-serif`; g.textAlign = "center";
      const lines = wrap(g, (this.subtitle.name ? this.subtitle.name.toUpperCase() + ": " : "") + this.subtitle.text, r.w * 0.8);
      lines.forEach((ln, i) => {
        const y = r.y + r.h * 0.93 - (lines.length - 1 - i) * fs * 1.25;
        g.lineWidth = fs * 0.18; g.strokeStyle = "rgba(0,0,0,0.85)"; g.strokeText(ln, r.x + r.w / 2, y);
        g.fillStyle = "#fff"; g.fillText(ln, r.x + r.w / 2, y);
      });
      g.textAlign = "left";
    }
  }

  title(text, sub, ms, kind = "card", extra = {}) {
    const now = clock.now();
    this.titles.push({ text, sub, from: now, until: now + ms, kind, ...extra });
  }

  gradeFilter() {
    if (this.freeze) return "grayscale(1) contrast(1.15) brightness(0.92)";
    return { inner: "hue-rotate(-28deg) saturate(1.5) contrast(1.12) brightness(0.88)",
             vision: "sepia(0.55) saturate(1.6) hue-rotate(205deg) brightness(1.18) contrast(0.92)",
             night: "saturate(0.85) brightness(0.95)" }[this.grade] || "";
  }
  compose() {
    const f = this.gradeFilter();
    if (this.ctx.canvas.style.filter !== f) this.ctx.canvas.style.filter = f;
    const o = this.overlay, g = o.getContext("2d");
    g.clearRect(0, 0, o.width, o.height);
    this.drawGraphics(g, o.width, o.height, true);
    if (this.recording || this.capturing) {
      const pg = this.pg, W = this.program.width, H = this.program.height, src = this.ctx.canvas;
      pg.fillStyle = "#000"; pg.fillRect(0, 0, W, H);
      // the GL frame, cropped to the program's 16:9 from the middle
      const sw = src.width, sh = src.height, want = W / H;
      let cw = sw, ch = sw / want;
      if (ch > sh) { ch = sh; cw = sh * want; }
      pg.filter = this.gradeFilter() || "none";
      pg.drawImage(src, (sw - cw) / 2, (sh - ch) / 2, cw, ch, 0, 0, W, H);
      pg.filter = "none";
      this.drawGraphics(pg, W, H, false);
    }
  }

  // ------------------------------------------------------------ modes
  enter(mode) {
    const c = this.ctx, cam = c.camera;
    if (this.mode === mode) mode = "edit";
    if (mode !== "edit" && cam !== c.persp) c.setProjection(false);
    this.mode = mode;
    c.controls.enabled = mode === "edit";
    if (mode === "walk" || mode === "drone") {
      const d = new this.T.Vector3();
      c.persp.getWorldDirection(d);
      this.yaw = Math.atan2(d.y, d.x);
      this.pitch = Math.asin(Math.max(-1, Math.min(1, d.z)));
      this.roll = 0; this.vel.set(0, 0, 0);
      if (mode === "walk") {
        const p = c.persp.position;
        if (p.length() > 12 || p.z > 3) {        // start on the porch, looking at the door
          const door = c.S.data.landmarks.door;
          p.set(0.4, door[1] - 3.2, 1.65); this.yaw = Math.PI / 2; this.pitch = -0.05;
        }
      }
      c.canvas.requestPointerLock?.();
    } else {
      document.exitPointerLock?.();
      const d = new this.T.Vector3(); c.persp.getWorldDirection(d);
      c.controls.target.copy(c.persp.position).addScaledVector(d, 4);
      c.persp.up.set(0, 0, 1);
    }
    this.onMode?.(this.mode);
  }

  bindInput() {
    const c = this.ctx;
    window.addEventListener("keydown", (e) => {
      if (e.target.closest("input, select, textarea")) return;
      if (this.mode === "walk" || this.mode === "drone") { this.keys.add(e.code); if (e.code === "Escape") this.enter("edit"); e.preventDefault(); }
      if (this.mode === "drone" && e.code === "KeyR") this.droneSpeed = 4;
    }, true);
    window.addEventListener("keyup", (e) => this.keys.delete(e.code), true);
    document.addEventListener("mousemove", (e) => {
      if (!(this.mode === "walk" || this.mode === "drone")) return;
      const locked = document.pointerLockElement === c.canvas;
      if (!locked && !(e.buttons & 1)) return;
      this.yaw -= e.movementX * 0.0022;
      this.pitch = Math.max(-1.45, Math.min(1.45, this.pitch - e.movementY * 0.0022));
    });
    c.canvas.addEventListener("click", () => {
      if ((this.mode === "walk" || this.mode === "drone") && document.pointerLockElement !== c.canvas) c.canvas.requestPointerLock?.();
    });
    c.canvas.addEventListener("wheel", (e) => {
      if (this.mode === "drone") { this.droneSpeed = Math.max(0.5, Math.min(20, this.droneSpeed * (e.deltaY < 0 ? 1.15 : 0.87))); e.preventDefault(); }
      if (this.mode === "walk") { this.setLens(Math.max(14, Math.min(85, this.lens + (e.deltaY < 0 ? 2 : -2)))); e.preventDefault(); }
    }, { passive: false });
  }

  floorAt(x, y) {
    const S = this.ctx.S, d = S.data.tables.door, R = S.data.tables.diameter_m / 2 + 0.06;
    if (Math.hypot(x, y) < R) return 0;
    const lm = S.data.landmarks;
    if (S.spec.porch && d && Math.abs(x) < 1.6 && y < -R + 0.25 && y > -R - 2.25) return 0;
    return -0.45;
  }

  walkCollide(p, q) {
    // the dome's wall: no walking through it except through the door
    const S = this.ctx.S, R = S.data.tables.diameter_m / 2, d = S.data.tables.door;
    const r0 = Math.hypot(p.x, p.y), r1 = Math.hypot(q.x, q.y), wall = R - 0.25, outer = R + 0.25;
    const crossing = (r0 < wall) !== (r1 < wall) || (r1 > wall && r1 < outer);
    if (!crossing) return q;
    const inDoor = d && Math.abs(q.x) < d.W / 2 - 0.12 && q.y < 0;
    if (inDoor) return q;
    // slide along the wall
    const ang = Math.atan2(q.y, q.x), keep = r0 < wall ? wall - 0.01 : outer + 0.01;
    return new this.T.Vector3(Math.cos(ang) * keep, Math.sin(ang) * keep, q.z);
  }

  tick(dt, now) {
    const c = this.ctx, cam = c.persp, T = this.T, k = this.keys;
    if (this.shot) {
      // shots run on the world's own time, so a freeze-frame holds the camera too
      this.time = (this.time || 0) + dt * 1000;
      const s = this.shot, t = Math.min(1, (this.time - s.t0) / (s.dur * 1000));
      const v = s.at(t);
      cam.position.copy(v.pos);
      cam.up.set(0, 0, 1);
      cam.lookAt(v.target);
      if (v.roll) cam.rotateZ(v.roll);
      if (v.fov) { cam.fov = v.fov; cam.updateProjectionMatrix(); }
      if (t >= 1) { const done = s.onEnd; this.shot = null; if (!this.holdShot) c.controls.target.copy(v.target); done?.(); }
      return;
    }
    if (this.mode !== "walk" && this.mode !== "drone") return;
    const fwd = new T.Vector3(Math.cos(this.yaw), Math.sin(this.yaw), 0);
    const right = new T.Vector3(Math.sin(this.yaw), -Math.cos(this.yaw), 0);
    const wish = new T.Vector3();
    if (k.has("KeyW") || k.has("ArrowUp")) wish.add(fwd);
    if (k.has("KeyS") || k.has("ArrowDown")) wish.sub(fwd);
    if (k.has("KeyD") || k.has("ArrowRight")) wish.add(right);
    if (k.has("KeyA") || k.has("ArrowLeft")) wish.sub(right);
    if (this.mode === "walk") {
      const speed = k.has("ShiftLeft") || k.has("ShiftRight") ? 3.2 : 1.4;
      if (wish.lengthSq()) wish.normalize().multiplyScalar(speed * dt);
      let q = cam.position.clone().add(wish);
      q = this.walkCollide(cam.position, q);
      const eye = this.floorAt(q.x, q.y) + (k.has("KeyC") ? 1.0 : 1.65);
      q.z += (eye - q.z) * Math.min(1, dt * 8);
      // a little head bob while walking
      this.bob = (this.bob || 0) + wish.length() * 6;
      cam.position.copy(q);
      cam.position.z += Math.sin(this.bob) * 0.012 * Math.min(1, wish.length() / (dt + 1e-6));
      this.roll = 0;
    } else {
      if (k.has("KeyE") || k.has("Space")) wish.z += 1;
      if (k.has("KeyQ") || k.has("KeyC")) wish.z -= 1;
      const target = wish.lengthSq() ? wish.normalize().multiplyScalar(this.droneSpeed) : new T.Vector3();
      this.vel.lerp(target, Math.min(1, dt * 2.2));                    // inertia: a drone eases in and out
      const q = cam.position.clone().addScaledVector(this.vel, dt);
      q.z = Math.max(this.floorAt(q.x, q.y) + 0.35, q.z);
      cam.position.copy(q);
      // bank into turns and lean with sideways speed, like a real quad
      const side = this.vel.dot(right);
      const yawRate = (this.yaw - (this.lastYaw ?? this.yaw)) / Math.max(dt, 1e-3);
      this.lastYaw = this.yaw;
      this.roll += ((-side * 0.05) - yawRate * 0.04 - this.roll) * Math.min(1, dt * 3);
    }
    const dir = new T.Vector3(Math.cos(this.yaw) * Math.cos(this.pitch), Math.sin(this.yaw) * Math.cos(this.pitch), Math.sin(this.pitch));
    cam.up.set(0, 0, 1);
    cam.lookAt(cam.position.clone().add(dir));
    if (this.roll) cam.rotateZ(this.roll);
  }

  // ------------------------------------------------------------ shots
  play(shot, onEnd) {
    if (this.mode !== "edit") this.enter("edit");
    this.ctx.controls.enabled = false;
    this.time = this.time || 0;
    this.shot = { ...shot, t0: this.time, onEnd: () => { this.ctx.controls.enabled = this.mode === "edit"; onEnd?.(); } };
  }
  stop() { this.shot = null; this.ctx.controls.enabled = this.mode === "edit"; }

  // ------------------------------------------------------------ recording
  async startRecording(slug = "take") {
    if (this.recording) return;
    const stream = this.program.captureStream(30);
    if (this.audio?.dest) for (const tr of this.audio.dest.stream.getAudioTracks()) stream.addTrack(tr);
    const type = ["video/webm;codecs=vp9,opus", "video/webm;codecs=vp8,opus", "video/webm"].find((t) => MediaRecorder.isTypeSupported(t));
    const rec = new MediaRecorder(stream, { mimeType: type, videoBitsPerSecond: 16_000_000 });
    const chunks = [];
    rec.ondataavailable = (e) => e.data.size && chunks.push(e.data);
    const c = this.ctx;
    // render at full HD while recording; the stage shows it letterboxed
    this.savedSize = [c.canvas.clientWidth, c.canvas.clientHeight];
    c.renderer.setPixelRatio(1);
    c.renderer.setSize(1920, 1080, false);
    c.canvas.style.objectFit = "contain";
    c.persp.aspect = 16 / 9; c.persp.updateProjectionMatrix();
    this.recording = { rec, chunks, t0: clock.now(), slug, done: new Promise((res) => (rec.onstop = res)) };
    rec.start(1000);
  }

  async stopRecording(meta = {}) {
    const r = this.recording;
    if (!r) return null;
    r.rec.stop();
    await r.done;
    this.recording = null;
    const c = this.ctx;
    c.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    c.canvas.style.objectFit = "";
    window.dispatchEvent(new Event("resize"));
    c.renderer.setSize(c.canvas.clientWidth, c.canvas.clientHeight, false);
    c.persp.aspect = c.canvas.clientWidth / Math.max(1, c.canvas.clientHeight); c.persp.updateProjectionMatrix();
    const blob = new Blob(r.chunks, { type: "video/webm" });
    const m = new TextEncoder().encode(JSON.stringify({ slug: r.slug, ...meta }));
    const head = new Uint8Array(4); new DataView(head.buffer).setUint32(0, m.length, true);
    const body = new Blob([head, m, blob]);
    c.toast("Saving the take: converting to MP4 and a phone cut...");
    const res = await fetch("/api/recording", { method: "POST", body });
    const j = await res.json();
    c.toast(j.folder ? `Saved to ${j.folder}` : `Saving failed: ${j.error}`);
    return j;
  }
}

function wrap(g, text, w) {
  const words = text.split(/\s+/), out = [];
  let line = "";
  for (const wd of words) {
    const t = line ? line + " " + wd : wd;
    if (g.measureText(t).width > w && line) { out.push(line); line = wd; } else line = t;
  }
  if (line) out.push(line);
  return out.slice(-3);
}
export function fmtTime(s) { s = Math.max(0, s); return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`; }

// ------------------------------------------------------------ the shot library
// Every shot is a function of t in [0, 1] giving the camera's position, target and lens. They are
// built against a subject point and the camera where it is now, so any of them works from anywhere.

export function makeShots(T) {
  const V = (x, y, z) => new T.Vector3(x, y, z);
  const fromTo = (a, b, e = E.smoother) => (t) => a.clone().lerp(b, e(t));
  return {
    dollyIn({ from, subject, dist = 0.45, dur = 5, fov }) {
      const end = subject.clone().lerp(from, dist);
      const p = fromTo(from, end);
      return { dur, at: (t) => ({ pos: p(t), target: subject, fov }) };
    },
    dollyOut({ from, subject, factor = 1.9, dur = 5, fov }) {
      const end = subject.clone().add(from.clone().sub(subject).multiplyScalar(factor));
      const p = fromTo(from, end);
      return { dur, at: (t) => ({ pos: p(t), target: subject, fov }) };
    },
    orbit({ subject, radius = 8, height = 2.5, from = 0, sweep = 120, dur = 8, fov, lift = 0 }) {
      return { dur, at: (t) => {
        const a = (from + sweep * E.inOutSine(t)) * Math.PI / 180;
        return { pos: V(subject.x + Math.cos(a) * radius, subject.y + Math.sin(a) * radius, subject.z + height + lift * t), target: subject, fov };
      } };
    },
    slide({ from, subject, dist = 3, dur = 6, fov }) {
      // a slider: the camera tracks sideways, parallel to the subject, keeping the same aim
      const view = subject.clone().sub(from), side = V(view.y, -view.x, 0).normalize().multiplyScalar(dist);
      const p0 = from.clone().sub(side.clone().multiplyScalar(0.5)), p1 = from.clone().add(side.clone().multiplyScalar(0.5));
      return { dur, at: (t) => { const e = E.smooth(t), off = side.clone().multiplyScalar(e - 0.5); return { pos: p0.clone().lerp(p1, e), target: subject.clone().add(off.multiplyScalar(0.7)), fov }; } };
    },
    pan({ from, subject, sweep = 60, dur = 6, fov }) {
      const v = subject.clone().sub(from), r = Math.hypot(v.x, v.y), a0 = Math.atan2(v.y, v.x) - sweep / 2 * Math.PI / 180;
      return { dur, at: (t) => { const a = a0 + sweep * Math.PI / 180 * E.inOutSine(t); return { pos: from, target: V(from.x + Math.cos(a) * r, from.y + Math.sin(a) * r, subject.z), fov }; } };
    },
    crane({ from, subject, rise = 4, back = 2, dur = 7, fov }) {
      const d = from.clone().sub(subject); d.z = 0; d.normalize();
      const end = from.clone().addScaledVector(d, back); end.z += rise;
      const p = fromTo(from, end);
      return { dur, at: (t) => ({ pos: p(t), target: subject, fov }) };
    },
    pedestal({ from, subject, rise = 2, dur = 5, fov }) {
      const p = fromTo(from, from.clone().add(V(0, 0, rise))), q = fromTo(subject, subject.clone().add(V(0, 0, rise)));
      return { dur, at: (t) => ({ pos: p(t), target: q(t), fov }) };
    },
    dollyZoom({ from, subject, dur = 5, fovFrom = 30, fovTo = 70 }) {
      // the vertigo shot: the camera closes in while the lens widens, the subject stays the same size
      const d0 = from.distanceTo(subject), w = d0 * Math.tan(fovFrom * Math.PI / 360);
      return { dur, at: (t) => {
        const f = fovFrom + (fovTo - fovFrom) * E.smooth(t), d = w / Math.tan(f * Math.PI / 360);
        return { pos: subject.clone().add(from.clone().sub(subject).normalize().multiplyScalar(d)), target: subject, fov: f };
      } };
    },
    reveal({ subject, radius = 7, dur = 7, fov }) {
      // from low behind the deck, rising over it to the whole dome
      return { dur, at: (t) => {
        const e = E.smoother(t), a = (-120 + 40 * e) * Math.PI / 180;
        return { pos: V(subject.x + Math.cos(a) * radius * (1.3 - 0.3 * e), subject.y + Math.sin(a) * radius * (1.3 - 0.3 * e), 0.2 + 3.2 * e),
                 target: V(subject.x, subject.y, subject.z * (0.4 + 0.6 * e)), fov };
      } };
    },
    flyover({ subject, radius = 9, height = 6, dur = 10, fov }) {
      // a drone pass: in low from one side, up over the top, out the other side, banking
      return { dur, at: (t) => {
        const e = E.inOutSine(t), x = -radius + 2 * radius * e;
        return { pos: V(subject.x + x, subject.y - radius * 0.8, subject.z + 1.5 + height * Math.sin(Math.PI * e)),
                 target: V(subject.x + x * 0.25, subject.y, subject.z), fov, roll: Math.sin(Math.PI * 2 * e) * 0.06 };
      } };
    },
    spiral({ subject, radius = 7, height = 7, turns = 0.8, dur = 9, fov }) {
      return { dur, at: (t) => {
        const e = E.smoother(t), a = (turns * 360 * e - 90) * Math.PI / 180, r = radius * (1.2 - 0.5 * e);
        return { pos: V(subject.x + Math.cos(a) * r, subject.y + Math.sin(a) * r, subject.z + height * (1 - e) + 1.2), target: subject, fov };
      } };
    },
    hold({ from, subject, dur = 3, fov, drift = 0.15 }) {
      // a locked-off shot that breathes: a slow push so a static frame never looks frozen
      const end = from.clone().lerp(subject, drift);
      const p = fromTo(from, end, E.linear);
      return { dur, at: (t) => ({ pos: p(t), target: subject, fov }) };
    },
    keys({ keys, dur }) {
      // a camera path through keyframes (Catmull-Rom), each key {pos, target, fov}
      const P = new T.CatmullRomCurve3(keys.map((k) => k.pos), false, "centripetal");
      const Q = new T.CatmullRomCurve3(keys.map((k) => k.target), false, "centripetal");
      return { dur: dur || keys.length * 3, at: (t) => {
        const e = E.smoother(t), i = Math.min(keys.length - 2, Math.floor(e * (keys.length - 1))), f = e * (keys.length - 1) - i;
        const fov = keys[i].fov + ((keys[i + 1]?.fov ?? keys[i].fov) - keys[i].fov) * f;
        return { pos: P.getPoint(e), target: Q.getPoint(e), fov };
      } };
    },
  };
}
