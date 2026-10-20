// The episode's sets, around the same dome: the Hank's Hardware Hour studio bench (the model's own
// jig, rails, sticks and table saw, from /api/set), the neighbour's hedge and house, and the
// Hardwicks' back patio. Plus the gags: the saw blade that tilts and the panel that comes apart.

export class EpisodeSet {
  constructor(ctx, data) {
    this.ctx = ctx; const T = ctx.THREE; this.T = T;
    this.group = new T.Group(); this.group.name = "episode-set";
    this.figures = data.figures;
    this.benchAt = data.bench_at; this.sawAt = data.saw_at; this.ground = data.ground; this.benchTop = data.bench_top;
    this.hedgeX = 5.6;
    this.pieces = {};
    for (const p of data.pieces) { const g = ctx.makePieceGroup(p); g.matrixAutoUpdate = true; this.group.add(g); this.pieces[p.id] = g; }
    // the loose panel the cast can carry
    this.prop = new T.Group();
    this.propSticks = data.prop.map((p) => { const g = ctx.makePieceGroup(p); g.matrixAutoUpdate = true; this.prop.add(g); return g; });
    this.prop.visible = false;
    ctx.scene.add(this.prop);
    // the saw's blade, on a pivot so it can be tilted
    const blade = Object.values(this.pieces).find((g) => g.userData.piece.id.endsWith("ts-blade"));
    if (blade) {
      const box = new T.Box3().setFromObject(blade), c = box.getCenter(new T.Vector3());
      this.bladePivot = new T.Group(); this.bladePivot.position.copy(c);
      this.group.add(this.bladePivot);
      blade.position.sub(c); this.bladePivot.add(blade);
      this.bladeBase = data.figures.bevel; this.bladeAngle = data.figures.bevel; this.bladeTo = this.bladeAngle;
    }
    this.dress();
    ctx.scene.add(this.group);
  }

  mat(c) { return new this.T.MeshLambertMaterial({ color: c, flatShading: true }); }
  box(x, y, z, sx, sy, sz, color, edges = true) {
    const T = this.T, geo = new T.BoxGeometry(sx, sy, sz), m = new T.Mesh(geo, this.mat(color));
    m.position.set(x, y, z); m.castShadow = true; m.receiveShadow = true; this.group.add(m);
    if (edges) m.add(new T.LineSegments(new T.EdgesGeometry(geo), this.ctx.edgeMat));
    return m;
  }

  dress() {
    const T = this.T, G = this.ground, [bx, by] = this.benchAt;
    // the studio: a backdrop wall behind the bench with the show's sign, and lights on stands
    this.box(bx - 1.6, by - 1.2, G + 1.6, 0.12, 6.4, 3.2, "#d8d2c4");
    const sign = document.createElement("canvas"); sign.width = 1024; sign.height = 256;
    const g = sign.getContext("2d");
    g.fillStyle = "#1d1b18"; g.fillRect(0, 0, 1024, 256);
    g.fillStyle = "#c45e29"; g.fillRect(0, 210, 1024, 46);
    g.fillStyle = "#f2d48a"; g.font = "900 92px Segoe UI, sans-serif"; g.textAlign = "center"; g.fillText("HANK'S HARDWARE HOUR", 512, 150);
    g.fillStyle = "#e9e4d8"; g.font = "600 34px Segoe UI, sans-serif"; g.fillText("CHANNEL 47", 512, 198);
    const tex = new T.CanvasTexture(sign); tex.colorSpace = T.SRGBColorSpace;
    const plane = new T.Mesh(new T.PlaneGeometry(3.2, 0.8), new T.MeshBasicMaterial({ map: tex }));
    plane.position.set(bx - 1.53, by - 1.2, G + 2.45); plane.rotation.set(Math.PI / 2, Math.PI / 2, 0);
    this.group.add(plane);
    for (const dy of [-3.6, 1.6]) {
      const x = bx + 2.6, y = by + dy * 0.8;
      this.box(x, y, G + 1.0, 0.04, 0.04, 2.0, "#2b2a28", false);
      const head = this.box(x, y, G + 2.05, 0.3, 0.3, 0.26, "#2b2a28");
      head.lookAt(bx, by, G + 1.2);
    }
    // a stack of 2x3s and a pair of sawhorses
    for (let i = 0; i < 6; i++) this.box(bx + 0.2 + (i % 3) * 0.07, by - 3.6, G + 0.04 + Math.floor(i / 3) * 0.04, 0.064, 2.4, 0.038, "#dcb57e");
    for (const dy of [-4.5, -2.9]) { this.box(bx + 0.25, by + dy + 1.2, G + 0.5, 0.9, 0.08, 0.08, "#c69c64"); }
    // the backyard: a hedge, the neighbour's fence and the side of his house beyond it
    const hx = this.hedgeX;
    for (let i = 0; i < 9; i++) {
      const y = -3.4 + i * 0.85;
      // chest-high, so the neighbour's head and shoulders show over it
      const h = this.box(hx, y, G + 0.66 + (i % 2) * 0.02, 0.9, 0.9, 1.32 + (i % 3) * 0.04, i % 2 ? "#5d8a4a" : "#6a9654", false);
      h.scale.set(1, 1, 1);
    }
    this.box(hx + 2.6, 0.2, G + 1.6, 0.2, 9, 3.2, "#c9b49a");
    for (let i = 0; i < 4; i++) this.box(hx + 2.49, -2.5 + i * 1.9, G + 1.7, 0.03, 0.9, 1.1, "#7fa7c0");
    this.patio();
  }

  patio() {
    // the Hardwicks' back patio, behind the dome: the house wall, a slider, a table, a grill, string lights
    const G = this.ground, T = this.T;
    this.box(0, 10.4, G + 1.5, 11, 0.25, 3.0, "#e6dccb");                      // the back wall
    this.box(0, 10.25, G + 1.15, 2.4, 0.06, 2.2, "#7fa7c0");                   // the sliding door
    this.box(0, 10.22, G + 1.15, 0.05, 0.08, 2.2, "#ece6da", false);
    for (const x of [-3.6, 3.6]) this.box(x, 10.25, G + 1.5, 1.2, 0.06, 1.0, "#7fa7c0");
    this.box(0, 10.35, G + 3.05, 11.6, 1.0, 0.12, "#8a6f55");                  // eave
    this.box(0, 8.1, G + 0.025, 8.0, 4.2, 0.05, "#b9b2a6");                   // the slab
    this.box(0, 8.2, G + 0.74, 1.6, 0.9, 0.05, "#c99a5e");                    // table top
    for (const [x, y] of [[-0.7, 7.85], [0.7, 7.85], [-0.7, 8.55], [0.7, 8.55]]) this.box(x, y, G + 0.37, 0.06, 0.06, 0.7, "#3b3d40", false);
    this.box(0, 8.2, G + 0.78, 0.5, 0.3, 0.06, "#e9e4d8", false);              // a tray of plates
    const grill = this.box(2.9, 8.9, G + 0.85, 0.7, 0.45, 0.35, "#2b2a28");
    this.box(2.9, 8.9, G + 0.4, 0.06, 0.06, 0.8, "#3b3d40", false);
    for (let i = 0; i < 9; i++) {                                               // string lights
      const m = new T.Mesh(new T.SphereGeometry(0.05, 8, 6), new T.MeshBasicMaterial({ color: 0xffd59a }));
      m.position.set(-3.6 + i * 0.9, 9.9 - Math.sin(i / 8 * Math.PI) * 0.5, G + 2.6 - Math.sin(i / 8 * Math.PI) * 0.35);
      this.group.add(m);
    }
    // the driveway at the side of the house, and Dusty's car: a red coupe he cannot afford
    this.box(-7.4, 7.6, G + 0.02, 3.2, 7.5, 0.04, "#a7a39b", false);
    const cx = -7.4, cy = 8.4;
    this.box(cx, cy, G + 0.55, 1.8, 4.2, 0.6, "#a3202c");
    this.box(cx, cy - 0.2, G + 1.05, 1.6, 2.0, 0.45, "#a3202c");
    this.box(cx, cy - 0.2, G + 1.06, 1.62, 1.7, 0.36, "#2b3440", false);       // the glass
    for (const [dx, dy] of [[-0.85, -1.4], [0.85, -1.4], [-0.85, 1.4], [0.85, 1.4]]) {
      const wh = new T.Mesh(new T.CylinderGeometry(0.34, 0.34, 0.24, 18), this.mat("#1d1b18")); wh.rotation.z = Math.PI / 2;
      wh.position.set(cx + dx, cy + dy, G + 0.34); wh.castShadow = true; this.group.add(wh);
    }
    for (const [x, y] of [[-4.2, 7.0], [4.4, 7.4]]) {                         // planters
      this.box(x, y, G + 0.25, 0.6, 0.6, 0.5, "#b8735a");
      const b = new T.Mesh(new T.SphereGeometry(0.45, 10, 8), this.mat("#5f8a4c")); b.position.set(x, y, G + 0.85); b.castShadow = true; this.group.add(b);
    }
  }

  phone(ch) {
    // Maya's phone, in her right hand
    if (ch.props.phone) return;
    const m = new this.T.Mesh(new this.T.BoxGeometry(0.075 * ch.k, 0.01, 0.15 * ch.k), this.mat("#1d1b18"));
    ch.hold("phone", m, 1, [0, 0.03, -0.08]);
  }

  jigCentre() { const [bx, by] = this.benchAt; return new this.T.Vector3(bx, by, this.benchTop + 0.05); }
  showPanelOnBench(on) { for (const [id, g] of Object.entries(this.pieces)) if (id.includes("-jig-") && id.includes("-s")) g.visible = on; }

  tiltBlade(deg, secs) { this.bladeTo = deg; this.bladeRate = Math.abs(deg - this.bladeAngle) / Math.max(secs, 0.01); }

  reset() {
    this.resetPanel(); this.showPanelOnBench(true);
    if (this.bladePivot) { this.bladeAngle = this.bladeTo = this.bladeBase; this.bladePivot.rotation.set(0, 0, 0); }
  }

  handPanel(ch) { this.holder = ch; this.prop.visible = true; this.burst = null; this.propSticks.forEach((s) => { s.position.set(0, 0, 0); s.rotation.set(0, 0, 0); }); }
  burstPanel() {
    this.burst = this.propSticks.map((s, i) => ({ s, v: new this.T.Vector3((i - 1) * 1.6, -1.2 + Math.random(), 2.0 + i * 0.5), w: new this.T.Vector3(Math.random() * 6, Math.random() * 6, Math.random() * 6) }));
    this.holder = null;
  }
  resetPanel() { this.prop.visible = false; this.burst = null; this.holder = null; }

  update(dt) {
    const T = this.T;
    if (this.bladePivot && this.bladeAngle !== this.bladeTo) {
      const step = (this.bladeRate || 10) * dt, d = this.bladeTo - this.bladeAngle;
      this.bladeAngle += Math.sign(d) * Math.min(Math.abs(d), step);
      // the saw stands turned a quarter turn, so the blade tilts about world y
      this.bladePivot.rotation.set(0, (this.bladeAngle - this.bladeBase) * Math.PI / 180, 0);
    }
    if (this.holder) {
      const c = this.holder, a = new T.Vector3(), b = new T.Vector3();
      c.arms[1].hand.getWorldPosition(a); c.arms[-1].hand.getWorldPosition(b);
      const mid = a.add(b).multiplyScalar(0.5);
      this.prop.position.copy(mid).add(new T.Vector3(0, 0, 0.35));
      this.prop.rotation.set(Math.PI / 2, 0, c.yaw, "ZXY");
    }
    if (this.burst) {
      for (const b of this.burst) {
        const p = new T.Vector3(); b.s.getWorldPosition(p);
        if (p.z > this.ground + 0.03) {
          b.v.z -= 9.8 * dt;
          b.s.position.addScaledVector(b.v.clone().applyQuaternion(this.prop.quaternion.clone().invert()), dt);
          b.s.rotation.x += b.w.x * dt; b.s.rotation.y += b.w.y * dt; b.s.rotation.z += b.w.z * dt;
        }
      }
    }
  }
}

