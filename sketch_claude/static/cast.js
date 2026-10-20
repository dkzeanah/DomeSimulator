// The cast: articulated characters built from primitives, a small motion library (walk, talk,
// point, hammer, carry, crank, fall, cheer...), props in their hands, and their voices.
import { clock } from "/static/clock.js";

// Every character faces +y in its own frame, right is +x, up is +z, standing on z = 0.

export const CAST = {
  hank:  { name: "Hank Hardwick", role: "host of Dome Time", voice: "en-US-GuyNeural", rate: "+8%", pitch: "+0Hz",
           height: 1.80, skin: "#e2b08a", shirt: "#b8432f", shirt2: "#7d2a1d", pants: "#3f5878", hair: "#5a3b26", hairStyle: "short",
           belly: 1.12, toolbelt: true },
  dale:  { name: "Dale Plumb", role: "co-host, measures twice", voice: "en-US-ChristopherNeural", rate: "-6%", pitch: "-2Hz",
           height: 1.86, skin: "#d9a07c", shirt: "#4f6f4a", shirt2: "#2f4a2c", pants: "#6b5a43", hair: "#7a5a3a", hairStyle: "short",
           beard: "#6b4a2e", glasses: true, belly: 1.05 },
  june:  { name: "June Hardwick", role: "the one who will live in it", voice: "en-US-JennyNeural", rate: "+2%", pitch: "+0Hz",
           height: 1.68, skin: "#e8b996", shirt: "#3e7c8c", shirt2: "#2a5866", pants: "#2f3440", hair: "#2e1e14", hairStyle: "long", belly: 0.92 },
  yarrow:{ name: "Mr. Yarrow", role: "the neighbour over the hedge", voice: "en-GB-RyanNeural", rate: "-8%", pitch: "-3Hz",
           height: 1.84, skin: "#d7a585", shirt: "#8a7a5a", shirt2: "#5e5338", pants: "#4c4a42", hair: "#cfcac0", hairStyle: "hat", belly: 1.0 },
  toby:  { name: "Toby Hardwick", role: "eleven, asks the question", voice: "en-US-AnaNeural", rate: "+6%", pitch: "+0Hz",
           height: 1.42, skin: "#e9bc98", shirt: "#e0a53a", shirt2: "#a8761e", pants: "#3a4f7a", hair: "#6a4428", hairStyle: "cap", belly: 0.9 },
};

export class Character {
  constructor(T, id, def, scene) {
    this.T = T; this.id = id; this.def = def;
    this.k = def.height / 1.78;
    this.root = new T.Group();
    this.root.name = id;
    this.root.rotation.order = "ZXY";          // yaw last, so a fall tips the figure about its own hips
    this.ground = () => 0;
    this.yaw = 0;
    this.action = "idle"; this.actionT0 = 0; this.actionArg = null; this.time = 0;
    this.talk = 0;            // 0..1 mouth level, set from the voice
    this.speaking = false;
    this.look = null;          // a world point to look at
    this.walk = null;          // {to, speed, onArrive}
    this.phase = Math.random() * 10;
    this.fallen = 0;
    this.props = {};
    this.build();
    scene.add(this.root);
  }

  mat(color) {
    const T = this.T;
    return new T.MeshLambertMaterial({ color, flatShading: true });
  }

  part(geo, color, parent, pos = [0, 0, 0], outline = true) {
    const T = this.T;
    const m = new T.Mesh(geo, this.mat(color));
    m.position.set(...pos);
    m.castShadow = true;
    parent.add(m);
    if (outline) {
      const o = new T.Mesh(geo, Character.ink || (Character.ink = new T.MeshBasicMaterial({ color: 0x1d1b18, side: T.BackSide })));
      o.scale.setScalar(1.06);
      m.add(o);
    }
    return m;
  }

  build() {
    const T = this.T, d = this.def, k = this.k;
    const cap = (r, l) => new T.CapsuleGeometry(r * k, l * k, 3, 10);
    const sph = (r) => new T.SphereGeometry(r * k, 14, 10);
    const box = (x, y, z) => new T.BoxGeometry(x * k, y * k, z * k);
    const j = (parent, pos) => { const g = new T.Group(); g.position.set(...pos.map((v) => v * k)); parent.add(g); return g; };
    const up = (geo) => { geo.rotateX(Math.PI / 2); return geo; };       // capsules stand along z

    this.hips = j(this.root, [0, 0, 0.93]);
    this.part(up(cap(0.15 * d.belly, 0.06)), d.pants, this.hips, [0, 0, 0.02 * k]);
    this.spine = j(this.hips, [0, 0, 0.08]);
    this.part(up(cap(0.165 * d.belly, 0.26)), d.shirt, this.spine, [0, 0.01 * k * d.belly, 0.2 * k]);
    // a plaid-ish yoke: a darker band across the chest
    this.part(up(cap(0.17 * d.belly, 0.04)), d.shirt2, this.spine, [0, 0.01 * k, 0.36 * k], false);
    this.neck = j(this.spine, [0, 0, 0.47]);
    this.part(up(cap(0.05, 0.06)), d.skin, this.neck, [0, 0, 0.03 * k]);
    this.head = j(this.neck, [0, 0, 0.11]);
    this.part(sph(0.115), d.skin, this.head, [0, 0, 0.1 * k]);
    this.part(sph(0.025), d.skin, this.head, [0, 0.11 * k, 0.09 * k]);                            // nose
    for (const s of [-1, 1]) {                                                                         // eyes and brows
      this.part(sph(0.022), "#f7f3ea", this.head, [s * 0.042 * k, 0.093 * k, 0.122 * k], false);
      const pupil = this.part(sph(0.012), "#1d1b18", this.head, [s * 0.042 * k, 0.113 * k, 0.122 * k], false);
      pupil.userData.home = pupil.position.clone(); this.pupils = (this.pupils || []).concat(pupil);
      const brow = this.part(box(0.045, 0.012, 0.012), d.hair === "#cfcac0" ? "#9a958c" : d.hair, this.head, [s * 0.043 * k, 0.108 * k, 0.153 * k], false);
      brow.rotation.y = s * 0.15; brow.userData.home = brow.position.clone(); brow.userData.side = s; this.brows = (this.brows || []).concat(brow);
    }
    this.mouth = this.part(box(0.06, 0.012, 0.016), "#6a2a24", this.head, [0, 0.106 * k, 0.05 * k], false);
    const hairC = d.hair;
    if (d.hairStyle === "short") this.part(sph(0.118), hairC, this.head, [0, -0.012 * k, 0.135 * k]).scale.set(1, 1, 0.62);
    if (d.hairStyle === "long") {
      this.part(sph(0.12), hairC, this.head, [0, -0.015 * k, 0.13 * k]).scale.set(1.02, 1, 0.7);
      this.part(up(cap(0.1, 0.16)), hairC, this.head, [0, -0.045 * k, 0.02 * k]).scale.set(1.15, 0.7, 1);
    }
    if (d.hairStyle === "princess") {
      // long, full princess hair: a crown of it, then a fall down the back past the shoulder blades
      this.part(sph(0.123), hairC, this.head, [0, -0.012 * k, 0.13 * k]).scale.set(1.06, 1.02, 0.74);
      this.part(up(cap(0.11, 0.34)), hairC, this.head, [0, -0.07 * k, -0.08 * k]).scale.set(1.25, 0.6, 1);
      for (const sd of [-1, 1]) this.part(up(cap(0.04, 0.22)), hairC, this.head, [sd * 0.1 * k, 0.02 * k, -0.02 * k]);
      this.part(new T.TorusGeometry(0.06 * k, 0.008 * k, 5, 14), "#e9d9a8", this.head, [0, -0.05 * k, 0.2 * k]).rotation.x = 1.0;
    }
    if (d.hairStyle === "long" && !d.longDone) {
      // long and straight with a side part, down past the shoulders (the original "long" adds a second fall)
      this.part(up(cap(0.095, 0.24)), hairC, this.head, [0.01 * k, -0.06 * k, -0.04 * k]).scale.set(1.2, 0.6, 1);
      this.part(up(cap(0.035, 0.18)), hairC, this.head, [-0.105 * k, 0.015 * k, 0.0]);
    }
    if (d.hairStyle === "shoulder") {
      // a shoulder-length cut: fuller sides that stop at the jaw-to-shoulder line
      this.part(sph(0.122), hairC, this.head, [0, -0.012 * k, 0.13 * k]).scale.set(1.06, 1.02, 0.7);
      this.part(up(cap(0.105, 0.1)), hairC, this.head, [0, -0.04 * k, 0.03 * k]).scale.set(1.18, 0.82, 1);
    }
    if (d.hairStyle === "spiky") {
      this.part(sph(0.117), hairC, this.head, [0, -0.01 * k, 0.125 * k]).scale.set(1, 1, 0.55);
      for (const [x, y, a] of [[-0.05, 0.04, -0.4], [0, 0.05, 0], [0.05, 0.04, 0.4], [-0.03, -0.02, -0.2], [0.03, -0.02, 0.2]]) {
        const c = this.part(new T.ConeGeometry(0.028 * k, 0.09 * k, 6).rotateX(Math.PI / 2), hairC, this.head, [x * k, y * k, 0.22 * k], false);
        c.rotation.y = a; c.rotation.x = -0.3;
      }
    }
    if (d.hairStyle === "swoop") {
      this.part(sph(0.12), hairC, this.head, [0, -0.012 * k, 0.135 * k]).scale.set(1.02, 1.02, 0.66);
      const q = this.part(sph(0.07), hairC, this.head, [0.03 * k, 0.07 * k, 0.2 * k]); q.scale.set(1.5, 0.9, 0.6);
    }
    if (d.hairStyle === "buzz") this.part(sph(0.117), hairC, this.head, [0, -0.01 * k, 0.125 * k]).scale.set(1, 1, 0.55);
    if (d.hairStyle === "curly") {
      this.part(sph(0.125), hairC, this.head, [0, -0.015 * k, 0.14 * k]).scale.set(1.05, 1.05, 0.72);
      for (const [x, y] of [[-0.09, 0.02], [0.09, 0.02], [0, -0.09], [-0.06, -0.07], [0.06, -0.07]]) this.part(sph(0.05), hairC, this.head, [x * k, y * k, 0.15 * k], false);
    }
    if (d.hairStyle === "ponytail" || d.hairStyle === "bun") {
      this.part(sph(0.12), hairC, this.head, [0, -0.015 * k, 0.13 * k]).scale.set(1.02, 1, 0.68);
      if (d.hairStyle === "bun") this.part(sph(0.055), hairC, this.head, [0, -0.06 * k, 0.24 * k]);
      else { const t = this.part(up(cap(0.035, 0.16)), hairC, this.head, [0, -0.12 * k, 0.06 * k]); t.rotation.x = 0.35; }
    }
    if (d.hairStyle === "cap") {
      this.part(sph(0.12), "#c8432f", this.head, [0, -0.01 * k, 0.14 * k]).scale.set(1, 1, 0.6);
      this.part(box(0.17, 0.12, 0.015), "#c8432f", this.head, [0, 0.11 * k, 0.155 * k]);
    }
    if (d.hairStyle === "hat") {
      this.part(new T.CylinderGeometry(0.2 * k, 0.2 * k, 0.015 * k, 20).rotateX(Math.PI / 2), "#b59a62", this.head, [0, 0, 0.17 * k]);
      this.part(new T.CylinderGeometry(0.1 * k, 0.12 * k, 0.11 * k, 16).rotateX(Math.PI / 2), "#b59a62", this.head, [0, 0, 0.23 * k]);
      this.part(new T.CylinderGeometry(0.121 * k, 0.121 * k, 0.02 * k, 16).rotateX(Math.PI / 2), "#5b4a2c", this.head, [0, 0, 0.19 * k], false);
    }
    if (d.beard && d.beardStyle === "scruff") {
      // a short black beard and moustache: scruff along the jaw, a bar over the lip
      this.part(sph(0.105), d.beard, this.head, [0, 0.022 * k, 0.04 * k], false).scale.set(1.04, 0.86, 0.62);
      this.part(box(0.07, 0.016, 0.014), d.beard, this.head, [0, 0.111 * k, 0.068 * k], false);
    } else if (d.beard) this.part(sph(0.1), d.beard, this.head, [0, 0.035 * k, 0.04 * k]).scale.set(1, 0.8, 0.75);
    if (d.earring) {
      // the self-pierced left ear: a small silver hoop, shown or hidden by the script
      this.earring = this.part(new T.TorusGeometry(0.014 * k, 0.003 * k, 5, 12), "#d6d9de", this.head, [0.118 * k, 0.0, 0.06 * k], false);
      this.earring.rotation.y = Math.PI / 2;
    }
    if (d.glasses) {
      for (const s of [-1, 1]) {
        const g = new T.Mesh(new T.TorusGeometry(0.028 * k, 0.005 * k, 6, 14), this.mat("#2b2925"));
        g.position.set(s * 0.042 * k, 0.11 * k, 0.125 * k); g.rotation.x = Math.PI / 2; this.head.add(g);
      }
    }
    this.arms = {};
    for (const s of [-1, 1]) {
      const sh = j(this.spine, [s * 0.215 * d.belly, 0, 0.4]);
      this.part(sph(0.07), d.shirt, sh);
      const upper = j(sh, [0, 0, 0]);
      this.part(up(cap(0.055, 0.2)), d.sleeveless ? d.skin : d.shirt, upper, [0, 0, -0.14 * k]);
      const elbow = j(upper, [0, 0, -0.29]);
      this.part(up(cap(0.045, 0.19)), d.skin, elbow, [0, 0, -0.13 * k]);
      const hand = j(elbow, [0, 0, -0.27]);
      this.part(sph(0.05), d.skin, hand, [0, 0, -0.03 * k]);
      this.arms[s] = { sh, upper, elbow, hand };
    }
    this.legs = {};
    for (const s of [-1, 1]) {
      const hip = j(this.hips, [s * 0.09, 0, 0]);
      this.part(up(cap(0.07, 0.32)), d.pants, hip, [0, 0, -0.22 * k]);
      const knee = j(hip, [0, 0, -0.44]);
      this.part(up(cap(0.058, 0.32)), d.pants, knee, [0, 0, -0.21 * k]);
      const foot = j(knee, [0, 0, -0.45]);
      this.part(box(0.1, 0.25, 0.08), "#2d2a26", foot, [0, 0.05 * k, -0.02 * k]);
      this.legs[s] = { hip, knee, foot };
    }
    if (d.hoodie) this.part(sph(0.13), d.shirt2, this.spine, [0, -0.13 * k, 0.43 * k]).scale.set(1.2, 0.6, 0.7);
    if (d.necklace) this.part(new T.TorusGeometry(0.08 * k, 0.006 * k, 5, 18), "#d8c27a", this.spine, [0, 0.07 * k, 0.43 * k]).rotation.x = 1.2;
    if (d.toolbelt) {
      this.part(new T.TorusGeometry(0.165 * k * d.belly, 0.022 * k, 6, 20), "#6b4a2a", this.hips, [0, 0, 0.06 * k]);
      this.part(box(0.08, 0.06, 0.12), "#6b4a2a", this.hips, [0.16 * k, 0.04 * k, -0.02 * k]);
      this.part(box(0.02, 0.02, 0.18), "#888", this.hips, [0.19 * k, 0.06 * k, -0.02 * k]);
    }
  }

  // ---------------------------------------------------------------- props
  hold(name, obj, hand = 1, offset = [0, 0, -0.06]) {
    this.drop(name);
    obj.position.set(...offset);
    this.arms[hand].hand.add(obj);
    this.props[name] = obj;
  }
  drop(name) { const o = this.props[name]; if (o) { o.parent?.remove(o); delete this.props[name]; } return o; }

  // ---------------------------------------------------------------- control
  place(x, y, yawDeg = 0) { this.root.position.set(x, y, this.ground(x, y)); this.yaw = yawDeg * Math.PI / 180; this.yawTarget = undefined; this.walk = null; }
  face(x, y) { this.yawTarget = Math.atan2(x - this.root.position.x, y - this.root.position.y) * -1; }
  do(action, arg = null) { this.action = action; this.actionArg = arg; this.actionT0 = this.time; if (action !== "fall") this.fallen = 0; }
  walkTo(x, y, speed = 1.2) {
    return new Promise((res) => { this.walk = { to: new this.T.Vector3(x, y, 0), speed, onArrive: res }; });
  }

  // ---------------------------------------------------------------- the motion
  update(dt, now) {
    const T = this.T, r = this.root;
    this.phase += dt;
    this.time += dt;
    let walking = false;
    if (this.walk) {
      const v = this.walk.to.clone().sub(r.position); v.z = 0;
      const dist = v.length();
      if (dist < 0.03) { const cb = this.walk.onArrive; this.walk = null; cb?.(); }
      else {
        walking = true;
        const step = Math.min(dist, this.walk.speed * dt);
        r.position.addScaledVector(v.normalize(), step);
        this.yawTarget = -Math.atan2(v.x, v.y);
        this.stride = (this.stride || 0) + step / (0.62 * this.k);
      }
    }
    if (this.yawTarget !== undefined) {
      let dy = ((this.yawTarget - this.yaw + Math.PI) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI) - Math.PI;
      this.yaw += dy * Math.min(1, dt * 6);
    }
    r.rotation.set(0, 0, this.yaw);

    // pose: every joint's rotation, from the action, plus breathing and the walk
    const t = this.time - this.actionT0, ph = this.phase;
    const P = { lean: 0, headYaw: 0, headPitch: 0, hipsZ: 0,
                arm: { [-1]: [0.05, 0.08, 0.1], [1]: [0.05, -0.08, 0.1] },     // [pitch, abduct, elbow]
                leg: { [-1]: [0, 0], [1]: [0, 0] } };
    const breathe = Math.sin(ph * 1.7) * 0.015;
    P.lean += breathe;
    const talkWave = this.speaking ? Math.sin(ph * 5.3) : 0;
    switch (this.action) {
      case "talk":
        P.arm[1] = [0.55 + 0.25 * talkWave, -0.15, 1.1 + 0.3 * Math.sin(ph * 3.1)];
        P.arm[-1] = [0.3 + 0.15 * Math.sin(ph * 2.3 + 1), 0.12, 0.8];
        P.headPitch = 0.05 * talkWave;
        break;
      case "point": {
        P.arm[1] = [1.45, -0.1, 0.05]; P.lean = 0.06;
        break;
      }
      case "wave": P.arm[1] = [0.2, -2.6, 0.6 + 0.5 * Math.sin(t * 9)]; break;
      case "shrug": { const s = Math.min(1, t * 3); P.arm[1] = [0.4 * s, -0.5 * s, 1.5 * s]; P.arm[-1] = [0.4 * s, 0.5 * s, 1.5 * s]; P.headPitch = -0.1 * s; break; }
      case "hips": P.arm[1] = [0.1, -0.75, 1.9]; P.arm[-1] = [0.1, 0.75, 1.9]; P.lean = -0.03; break;
      case "think": P.arm[1] = [1.0, -0.2, 2.3]; P.arm[-1] = [0.5, 0.25, 1.6]; P.headPitch = 0.12; P.headYaw = 0.2; break;
      case "facepalm": P.arm[1] = [1.25, -0.15, 2.4]; P.headPitch = 0.3; P.lean = 0.1; break;
      case "cheer": P.arm[1] = [0.2, -2.7 + 0.15 * Math.sin(t * 8), 0.3]; P.arm[-1] = [0.2, 2.7 - 0.15 * Math.sin(t * 8), 0.3]; P.hipsZ = Math.abs(Math.sin(t * 6)) * 0.08; break;
      case "laugh": P.lean = -0.12 + 0.05 * Math.sin(t * 14); P.arm[1] = [0.3, -0.3, 1.8]; P.arm[-1] = [0.3, 0.3, 1.8]; P.headPitch = -0.25; break;
      case "hammer": { const sw = Math.sin(t * 7); P.arm[1] = [1.3 + 0.8 * sw, -0.1, 0.6 + 0.6 * sw]; P.arm[-1] = [0.6, 0.25, 0.9]; P.lean = 0.12; P.headPitch = 0.35; break; }
      case "carry": P.arm[1] = [1.1, -0.05, 0.6]; P.arm[-1] = [1.1, 0.05, 0.6]; P.lean = -0.04; break;
      case "lift": { const s = Math.min(1, t * 1.5); P.arm[1] = [1.1 + 1.6 * s, -0.12, 0.4 - 0.3 * s]; P.arm[-1] = [1.1 + 1.6 * s, 0.12, 0.4 - 0.3 * s]; P.lean = -0.08 * s; break; }
      case "crank": { const c = t * 5; P.arm[1] = [0.9 + 0.25 * Math.sin(c), -0.15 + 0.2 * Math.cos(c), 0.8]; P.lean = 0.2; P.headPitch = 0.3; break; }
      case "measure": P.arm[1] = [0.9, -0.5, 0.3]; P.arm[-1] = [0.9, 0.5, 0.3]; P.lean = 0.25; P.headPitch = 0.4; break;
      case "flex": { const s = Math.min(1, t * 4); P.arm[1] = [0.2, -1.5 * s, 2.3 * s]; P.arm[-1] = [0.2, 1.5 * s, 2.3 * s]; P.lean = -0.06; break; }
      case "grunt": { const s = Math.sin(Math.min(1, t * 3) * Math.PI); P.arm[1] = [0.3, -1.2 * s, 2.0 * s]; P.arm[-1] = [0.3, 1.2 * s, 2.0 * s]; P.headPitch = -0.3 * s; P.lean = -0.1 * s; break; }
      case "peek": P.arm[1] = [0.1, -0.1, 0.2]; P.arm[-1] = [0.1, 0.1, 0.2]; P.hipsZ = -0.05 + 0.03 * Math.sin(t * 2); break;
      case "stomp": {
        // the foot comes down: one knee up, then the stamp, arms folding as it lands
        const s = Math.min(1, t * 3), up = t < 0.25 ? Math.sin(t / 0.25 * Math.PI / 2) : Math.max(0, 1 - (t - 0.25) * 8);
        P.leg[1] = [0.9 * up, -1.2 * up]; P.arm[1] = [0.9 * s, 0.6 * s, 2.2 * s]; P.arm[-1] = [0.9 * s, -0.6 * s, 2.2 * s]; P.lean = -0.06 * s; P.headPitch = -0.1 * s;
        break;
      }
      case "crossed": P.arm[1] = [0.9, 0.6, 2.2]; P.arm[-1] = [0.9, -0.6, 2.2]; P.lean = -0.04; break;
      case "vision": P.arm[1] = [1.6, -0.5, 2.5]; P.arm[-1] = [1.6, 0.5, 2.5]; P.headPitch = -0.15; P.lean = -0.05; break;
      case "ear": P.arm[-1] = [1.5, 0.45, 2.3]; P.headYaw = -0.3; break;
      case "lean": P.lean = -0.08; P.arm[1] = [0.2, -0.2, 0.4]; P.arm[-1] = [0.35, 0.25, 1.4]; P.hipsZ = -0.02; break;
      case "spiral": { const w = Math.sin(t * 2.3); P.arm[1] = [1.2 + 0.3 * w, -0.4, 2.0]; P.arm[-1] = [0.6 - 0.3 * w, 0.4, 1.2 + 0.4 * Math.sin(t * 3.1)]; P.headPitch = -0.15 + 0.1 * Math.sin(t * 1.7); P.headYaw = 0.3 * Math.sin(t * 0.9); break; }
      case "phone": P.arm[1] = [1.2, -0.25, 1.45]; P.arm[-1] = [0.1, 0.12, 0.2]; P.headPitch = 0.1; break;
      case "fall": break;
      case "sit": P.leg[1] = [1.45, -1.5]; P.leg[-1] = [1.45, -1.5]; P.hipsZ = -0.44; P.arm[1] = [0.6, -0.1, 0.9]; P.arm[-1] = [0.6, 0.1, 0.9]; break;
      default:
        P.arm[1] = [0.05 + 0.02 * Math.sin(ph), -0.1, 0.12]; P.arm[-1] = [0.05 + 0.02 * Math.sin(ph + 1), 0.1, 0.12];
        if (this.speaking) { P.arm[1] = [0.45 + 0.2 * talkWave, -0.12, 1.0]; }
    }
    if (walking) {
      const s = Math.sin(this.stride * Math.PI), c = Math.cos(this.stride * Math.PI);
      P.leg[1] = [0.5 * s, -Math.max(0, -c) * 0.9 - 0.1];
      P.leg[-1] = [-0.5 * s, -Math.max(0, c) * 0.9 - 0.1];
      if (["idle", "talk"].includes(this.action)) { P.arm[1][0] = -0.45 * s; P.arm[-1][0] = 0.45 * s; }
      P.hipsZ += Math.abs(c) * 0.03;
      P.lean += 0.05;
    }
    // look at whoever matters
    if (this.look) {
      const w = this.look.clone().sub(r.position);
      const local = Math.atan2(-w.x, w.y) - this.yaw;
      const ly = ((local + Math.PI) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI) - Math.PI;
      P.headYaw += Math.max(-1.1, Math.min(1.1, ly));
      P.headPitch -= Math.atan2(w.z - 1.6 * this.k, Math.hypot(w.x, w.y)) * 0.6;
    }
    // apply, eased so actions blend instead of snapping
    const ease = Math.min(1, dt * 9);
    const set = (o, x, y, z) => { o.rotation.x += (x - o.rotation.x) * ease; o.rotation.y += (y - o.rotation.y) * ease; o.rotation.z += ((z ?? 0) - o.rotation.z) * ease; };
    set(this.spine, P.lean, 0, 0);
    set(this.head, P.headPitch, 0, P.headYaw);
    for (const sd of [-1, 1]) {
      const a = this.arms[sd], [pitch, abd, elb] = P.arm[sd];
      set(a.upper, pitch, abd, 0);
      set(a.elbow, elb, 0, 0);
      const [hp, kn] = P.leg[sd];
      set(this.legs[sd].hip, hp, 0, 0);
      set(this.legs[sd].knee, kn, 0, 0);
    }
    this.hips.position.z += ((0.93 * this.k + P.hipsZ) - this.hips.position.z) * ease;
    // a fall: the whole figure tips back onto the ground and the legs come up
    if (this.action === "fall") this.fallen = Math.min(1, this.fallen + dt * 2.2); else this.fallen = Math.max(0, this.fallen - dt * 1.5);
    const f = this.fallen * this.fallen;
    r.rotation.x = f * 1.45;
    r.position.z = this.ground(r.position.x, r.position.y) + f * 0.18;
    if (this.fallen > 0) { this.legs[1].hip.rotation.x += f * 0.6; this.legs[-1].hip.rotation.x += f * 0.9; }
    // the face: side-eye, glare, wide eyes, a smile, a smirk
    const E = { neutral: [0, 0, 0, 0], sideeye: [1, 0, -0.012, 0.1], sideeyeL: [-1, 0, -0.012, 0.1], glare: [0, 0, -0.016, 0.35],
                wide: [0, 0.006, 0.014, -0.1], smile: [0, 0, 0.004, 0], smirk: [0.4, 0, -0.006, 0.18], sad: [0, -0.004, 0.006, -0.3],
                vision: [0, 0.008, 0.016, -0.2], far: [0.3, 0.004, 0.004, 0] }[this.expr || "neutral"] || [0, 0, 0, 0];
    for (const p of this.pupils || []) {
      const h = p.userData.home;
      p.position.x += (h.x + E[0] * 0.016 * this.k - p.position.x) * Math.min(1, dt * 12);
      p.position.z += (h.z + E[1] * this.k - p.position.z) * Math.min(1, dt * 12);
    }
    for (const b of this.brows || []) {
      const h = b.userData.home, sd = b.userData.side;
      b.position.z += (h.z + E[2] * this.k - b.position.z) * Math.min(1, dt * 12);
      b.rotation.y += (sd * (0.15 + E[3]) - b.rotation.y) * Math.min(1, dt * 12);
    }
    if (this.earring) this.earring.visible = !!this.showEarring;
    // the mouth flaps with the voice
    if (this.talkFn) this.talk = this.talkFn(now);
    this.mouth.scale.z += ((1 + this.talk * 5) - this.mouth.scale.z) * Math.min(1, dt * 18);
  }

  headWorld() { const v = new this.T.Vector3(); this.head.getWorldPosition(v); v.z += 0.08 * this.k; return v; }
  chestWorld() { const v = new this.T.Vector3(); this.spine.getWorldPosition(v); v.z += 0.25 * this.k; return v; }
}

// ---------------------------------------------------------------- voices
export class Voices {
  constructor(cine) {
    this.ac = new (window.AudioContext || window.webkitAudioContext)();
    this.master = this.ac.createGain();
    this.master.gain.value = 1;
    this.dest = this.ac.createMediaStreamDestination();
    this.master.connect(this.ac.destination);
    this.master.connect(this.dest);
    this.cache = new Map();
    cine.audio = this;
  }
  async fetchLine(def, text) {
    const key = `${def.voice}|${def.rate}|${def.pitch}|${text}`;
    if (this.cache.has(key)) return this.cache.get(key);
    const p = (async () => {
      const r = await fetch("/api/voice", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, voice: def.voice, rate: def.rate, pitch: def.pitch }) });
      if (!r.ok) throw new Error("voice failed");
      return await this.ac.decodeAudioData(await r.arrayBuffer());
    })();
    this.cache.set(key, p);
    return p;
  }
  envelope(buf) {
    // loudness every 1/60 s, for the lips during an offline render
    if (buf._env) return buf._env;
    const d = buf.getChannelData(0), step = Math.floor(buf.sampleRate / 60), out = [];
    for (let i = 0; i < d.length; i += step) { let s = 0; for (let j = i; j < Math.min(d.length, i + step); j++) s += d[j] * d[j]; out.push(Math.min(1, Math.sqrt(s / step) * 9)); }
    return (buf._env = out);
  }
  async say(ch, text, onLevel) {
    if (clock.offline) {
      let buf = null;
      try { buf = await this.fetchLine(ch.def, text); } catch { buf = null; }
      const dur = buf ? buf.duration : 0.4 + text.length * 0.055;
      if (buf) this.events?.push({ kind: "voice", buf, t: clock.now() / 1000 });
      const env = buf ? this.envelope(buf) : null, t0 = clock.now();
      ch.speaking = true;
      ch.talkFn = env ? (now) => env[Math.min(env.length - 1, Math.floor((now - t0) / 1000 * 60))] || 0 : null;
      await clock.wait(dur);
      ch.speaking = false; ch.talkFn = null; ch.talk = 0;
      return;
    }
    await this.ac.resume();
    let buf;
    try { buf = await this.fetchLine(ch.def, text); } catch { buf = null; }
    if (!buf) {        // no voice: give the line its reading time
      ch.speaking = true;
      await new Promise((r) => setTimeout(r, 400 + text.length * 55));
      ch.speaking = false;
      return;
    }
    const src = this.ac.createBufferSource(); src.buffer = buf;
    const an = this.ac.createAnalyser(); an.fftSize = 512;
    src.connect(an); an.connect(this.master);
    const data = new Uint8Array(an.fftSize);
    ch.speaking = true;
    let live = true;
    const loop = () => {
      if (!live) return;
      an.getByteTimeDomainData(data);
      let s = 0; for (const v of data) s += (v - 128) * (v - 128);
      ch.talk = Math.min(1, Math.sqrt(s / data.length) / 28);
      onLevel?.(ch.talk);
      requestAnimationFrame(loop);
    };
    loop();
    await new Promise((res) => { src.onended = res; src.start(); });
    live = false; ch.talk = 0; ch.speaking = false;
  }
}
