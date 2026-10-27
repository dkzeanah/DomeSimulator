// The lesson stage: the geometry a chapter talks about, drawn from the solver's own numbers
// (lesson_web.stage_2v: two_v_demo.geometry), on an exhibit plinth. Every look is a pure
// function of (chapter, progress 0..1, film time), so any frame can be drawn on its own.
//
// Units: the unit sphere is drawn at radius S; z is up; the plinth top is z = 0.

const S = 2.2;                   // the unit sphere, in world units
const LIFT = S + 0.35;           // a whole sphere's centre, floating over the plinth
export const COLORS = { SHORT: 0x5ec8f2, LONG: 0xffb04a, plain: 0xe9e1d0, node: 0xf6f1e6, accent: 0xffd27a, red: 0xff6a4d };

const ease = (x) => (x <= 0 ? 0 : x >= 1 ? 1 : x * x * (3 - 2 * x));
const span = (p, a, b) => ease((p - a) / (b - a));

export class Stage {
  constructor(T, scene, data) {
    this.T = T; this.scene = scene; this.d = data;
    this.root = new T.Group(); scene.add(this.root);
    this.looks = {};
    this.unitCyl = new T.CylinderGeometry(1, 1, 1, 10, 1, false);
    this.unitCyl.rotateX(Math.PI / 2);                 // along +z
    this.unitSph = new T.SphereGeometry(1, 16, 12);
    this.labelCache = new Map();
    const d = data;
    if (d.verts) {
      this.verts = d.verts.map((v) => new T.Vector3(...v));
      this.hemiEdges = (d.hemiEdges || d.edges).map(([a, b]) => [a, b]);
      this.edgeClass = new Map((d.edges || []).map(([a, b], i) => [key(a, b), (d.edgeClass || [])[i] || "plain"]));
    }
  }

  // ------------------------------------------------------------ building blocks
  struts(segs, r, color, opacity = 1) {
    const T = this.T;
    const mat = new T.MeshStandardMaterial({ color: 0xffffff, roughness: 0.55, metalness: 0.05, transparent: opacity < 1, opacity });
    const m = new T.InstancedMesh(this.unitCyl, mat, Math.max(1, segs.length));
    const M = new T.Matrix4(), q = new T.Quaternion(), z = new T.Vector3(0, 0, 1), c = new T.Color();
    segs.forEach(([a, b, col], i) => {
      const dir = new T.Vector3().subVectors(b, a), len = dir.length();
      q.setFromUnitVectors(z, dir.clone().normalize());
      M.compose(new T.Vector3().addVectors(a, b).multiplyScalar(0.5), q, new T.Vector3(r, r, len));
      m.setMatrixAt(i, M);
      m.setColorAt(i, c.set(col ?? color));
    });
    m.count = segs.length;
    m.castShadow = true;
    return m;
  }

  /** Re-pose an existing strut mesh: same count, new ends (nothing allocated per frame). */
  moveStruts(m, segs, r) {
    const T = this.T, M = new T.Matrix4(), q = new T.Quaternion(), z = new T.Vector3(0, 0, 1);
    const dir = new T.Vector3(), mid = new T.Vector3(), sc = new T.Vector3();
    segs.forEach(([a, b], i) => {
      dir.subVectors(b, a); const len = dir.length();
      q.setFromUnitVectors(z, dir.normalize());
      M.compose(mid.addVectors(a, b).multiplyScalar(0.5), q, sc.set(r, r, len));
      m.setMatrixAt(i, M);
    });
    m.instanceMatrix.needsUpdate = true;
  }

  moveNodes(m, points, r) {
    const M = new this.T.Matrix4();
    points.forEach((p, i) => m.setMatrixAt(i, M.makeScale(r, r, r).setPosition(p)));
    m.instanceMatrix.needsUpdate = true;
  }

  nodes(points, r, color) {
    const T = this.T;
    const m = new T.InstancedMesh(this.unitSph, new T.MeshStandardMaterial({ color, roughness: 0.4 }), Math.max(1, points.length));
    const M = new T.Matrix4();
    points.forEach((p, i) => m.setMatrixAt(i, M.makeScale(r, r, r).setPosition(p)));
    m.count = points.length;
    return m;
  }

  sphere(r, opacity = 0.08, wire = true) {
    const T = this.T, g = new T.Group();
    g.add(new T.Mesh(new T.SphereGeometry(r, 48, 32), new T.MeshStandardMaterial({ color: 0x9fd4ff, transparent: true, opacity, depthWrite: false })));
    if (wire) g.add(new T.LineSegments(new T.WireframeGeometry(new T.SphereGeometry(r, 24, 16)),
      new T.LineBasicMaterial({ color: 0xbfe4ff, transparent: true, opacity: 0.18 })));
    return g;
  }

  label(text, size = 0.32, color = "#fff7e8") {
    const T = this.T, k = `${text}|${size}|${color}`;
    if (!this.labelCache.has(k)) {
      const c = document.createElement("canvas"), g = c.getContext("2d"), px = 64;
      g.font = `600 ${px}px Inter, Segoe UI, sans-serif`;
      c.width = Math.ceil(g.measureText(text).width) + 40; c.height = px + 34;
      g.font = `600 ${px}px Inter, Segoe UI, sans-serif`;
      g.fillStyle = "rgba(14,18,26,0.72)"; roundRect(g, 0, 0, c.width, c.height, 18); g.fill();
      g.fillStyle = color; g.textBaseline = "middle"; g.fillText(text, 20, c.height / 2 + 2);
      const tex = new T.CanvasTexture(c); tex.colorSpace = T.SRGBColorSpace;
      this.labelCache.set(k, { tex, aspect: c.width / c.height });
    }
    const { tex, aspect } = this.labelCache.get(k);
    const s = new T.Sprite(new T.SpriteMaterial({ map: tex, depthTest: false, transparent: true }));
    s.scale.set(size * aspect, size, 1);
    s.renderOrder = 10;
    return s;
  }

  at(p, x, y, z) { p.position.set(x, y, z); return p; }

  // ------------------------------------------------------------ the 2V geometry, scaled
  sv(i, centre = LIFT) { return this.verts[i].clone().multiplyScalar(S).add(new this.T.Vector3(0, 0, centre)); }

  domeStruts(r = 0.05, filter = null, centre = 0) {
    const segs = [];
    for (const [a, b] of this.hemiEdges) {
      if (filter && !filter(a, b)) continue;
      const cls = this.edgeClass.get(key(a, b)) || "plain";
      segs.push([this.sv(a, centre), this.sv(b, centre), COLORS[cls] ?? COLORS.plain]);
    }
    return this.struts(segs, r);
  }

  domeNodes(r = 0.075, centre = 0) {
    const used = new Set(this.hemiEdges.flat());
    return this.nodes([...used].map((i) => this.sv(i, centre)), r, COLORS.node);
  }

  // ------------------------------------------------------------ looks: built once, posed every frame
  look(name) {
    if (!this.looks[name]) {
      const g = new this.T.Group(); g.visible = false; this.root.add(g);
      const builder = this["build_" + name] || this.build_generic;
      this.looks[name] = { g, pose: builder.call(this, g) || (() => {}) };
    }
    return this.looks[name];
  }

  set(stage, p, t) {
    for (const [n, l] of Object.entries(this.looks)) l.g.visible = n === stage;
    const l = this.look(stage);
    l.g.visible = true;
    l.pose(p, t);
  }

  /** Where the camera looks, how far it stands, and how wide the subject is (half-width, world units),
   *  so the frame can stand back far enough for the room the graphics leave. ``dir``, when given,
   *  overrides the chapter's own camera direction (a diagram that must be seen square). */
  frame(stage) {
    const T = this.T;
    const sphereStages = new Set(["coordinates", "icosahedron", "midpoints", "projection", "classes"]);
    if (sphereStages.has(stage)) return { target: new T.Vector3(0, 0, LIFT), dist: 9.2, half: S * 1.15 };
    if (stage === "derivations") { this.look("derivations"); return { target: new T.Vector3(0, 0, LIFT), dist: 8.4, half: S * 1.1, dir: this.derivDir }; }
    if (stage === "platonic") return { target: new T.Vector3(0, 0, 1.0), dist: 10.5, half: 5.8 };
    if (stage === "rigidity") return { target: new T.Vector3(0, 0, 1.2), dist: 8.0, half: 4.0 };
    if (stage === "cutlist") return { target: new T.Vector3(0, 0, 0.4), dist: 9.0, half: 3.2 };
    if (stage === "finale") return { target: new T.Vector3(0, 0, 1.6), dist: 9.6, half: S * 1.2 };
    return { target: new T.Vector3(0, 0, S * 0.45), dist: 8.6, half: S * 1.2 };
  }

  build_generic(g) {
    if (!this.verts) return;
    const dome = new this.T.Group(); dome.add(this.domeStruts(), this.domeNodes()); g.add(dome);
    return (p, t) => { dome.rotation.z = t * 0.06; };
  }

  build_hero(g) {
    const dome = new this.T.Group(); dome.add(this.domeStruts(0.055), this.domeNodes()); g.add(dome);
    const a = this.at(this.label("LONG", 0.34, "#ffb04a"), -0.55, 0, S * 1.32), b = this.at(this.label("SHORT", 0.34, "#5ec8f2"), 0.65, 0, S * 1.32);
    g.add(a, b);
    return (p, t) => { dome.rotation.z = t * 0.07; a.material.opacity = b.material.opacity = span(p, 0.35, 0.55); };
  }

  build_rigidity(g) {
    const T = this.T;
    const tri = new T.Group(), sq = new T.Group(); g.add(tri, sq);
    const triPts = [new T.Vector3(-3.4, 0, 0.05), new T.Vector3(-1.2, 0, 0.05), new T.Vector3(-2.3, 0, 1.95)];
    tri.add(this.struts(triPts.map((p, i) => [p, triPts[(i + 1) % 3], COLORS.LONG]), 0.07), this.nodes(triPts, 0.11, COLORS.node));
    const tl = this.at(this.label("holds its shape", 0.3), -2.3, 0, 2.55), sl = this.at(this.label("racks without a brace", 0.3), 2.3, 0, 2.55);
    const push = this.at(this.label("push", 0.28, "#ff6a4d"), -2.3, 0, 3.05);
    g.add(tl, sl, push);
    const corners = (shear) => [new T.Vector3(1.3, 0, 0.05), new T.Vector3(3.3, 0, 0.05), new T.Vector3(3.3 + shear, 0, 2.0), new T.Vector3(1.3 + shear, 0, 2.0)];
    const p0 = corners(0);
    const sqS = this.struts(p0.map((q, i) => [q, p0[(i + 1) % 4], COLORS.SHORT]), 0.07), sqN = this.nodes(p0, 0.11, COLORS.node);
    sq.add(sqS, sqN);
    return (p) => {
      const shear = Math.sin(Math.min(1, p * 1.4) * Math.PI * 1.5) * 0.6 * span(p, 0.2, 0.4);
      const pts = corners(shear);
      this.moveStruts(sqS, pts.map((q, i) => [q, pts[(i + 1) % 4]]), 0.07);
      this.moveNodes(sqN, pts, 0.11);
      push.material.opacity = span(p, 0.1, 0.25);
    };
  }

  build_platonic(g) {
    const T = this.T, solids = this.d.platonic || [], items = [];
    solids.forEach((s, i) => {
      const grp = new T.Group(), x = (i - (solids.length - 1) / 2) * 2.35, r = 0.85;
      const pts = s.verts.map((v) => new T.Vector3(...v).multiplyScalar(r));
      grp.add(this.struts(s.edges.map(([a, b]) => [pts[a], pts[b], s.name === "Icosahedron" ? COLORS.LONG : COLORS.plain]), 0.035));
      grp.add(this.nodes(pts, 0.05, COLORS.node));
      grp.position.set(x, 0, 1.25);
      const lab = this.at(this.label(`${s.name}  ${s.faces}`, 0.24), x, 0, 0.18);
      g.add(grp, lab);
      items.push({ grp, lab, ico: s.name === "Icosahedron" });
    });
    return (p, t) => items.forEach((it, i) => {
      it.grp.rotation.z = t * 0.3 + i; it.grp.rotation.x = 0.35;
      const on = span(p, i * 0.1, i * 0.1 + 0.12);
      it.grp.scale.setScalar(Math.max(0.001, on * (it.ico ? 1 + 0.25 * span(p, 0.7, 0.85) : 1 - 0.25 * span(p, 0.7, 0.85))));
      it.lab.material.opacity = on;
    });
  }

  build_coordinates(g) {
    const T = this.T, phi = this.d.phi, k = S / Math.sqrt(1 + phi * phi);
    const planes = [];
    const rects = [[[0, 1, phi], [1, 2]], [[1, phi, 0], [0, 1]], [[phi, 0, 1], [0, 2]]];
    const tints = [0xff9e6b, 0x7fd0ff, 0xb6ef8a];
    rects.forEach(([[a, b, c]], i) => {
      const w = [a, b, c];
      const corners = [[1, 1], [1, -1], [-1, -1], [-1, 1]].map(([s1, s2]) => {
        const v = [0, 0, 0], idx = [0, 1, 2].filter((j) => w[j] !== 0);
        v[idx[0]] = w[idx[0]] * s1; v[idx[1]] = w[idx[1]] * s2;
        return new T.Vector3(...v).multiplyScalar(k).add(new T.Vector3(0, 0, LIFT));
      });
      const geo = new T.BufferGeometry().setFromPoints([corners[0], corners[1], corners[2], corners[0], corners[2], corners[3]]);
      geo.computeVertexNormals();
      const mesh = new T.Mesh(geo, new T.MeshBasicMaterial({ color: tints[i], transparent: true, opacity: 0.32, side: T.DoubleSide, depthWrite: false }));
      const edge = this.struts(corners.map((q, j) => [q, corners[(j + 1) % 4], tints[i]]), 0.03);
      const grp = new T.Group(); grp.add(mesh, edge); g.add(grp); planes.push(grp);
    });
    const raw = this.d.raw.map((v) => new T.Vector3(...v).multiplyScalar(k).add(new T.Vector3(0, 0, LIFT)));
    const dots = this.nodes(raw, 0.09, COLORS.accent); g.add(dots);
    const tags = [this.at(this.label("(0, ±1, ±φ)", 0.26), 0, -k * 1.4, LIFT + k * phi + 0.3), this.at(this.label("(±1, ±φ, 0)", 0.26), k * 1.6, -k * phi, LIFT + 0.2),
                  this.at(this.label("(±φ, 0, ±1)", 0.26), -k * phi - 0.6, 0, LIFT + k * 1.2)];
    g.add(...tags);
    return (p, t) => {
      planes.forEach((pl, i) => { pl.visible = p > 0.08 + i * 0.16; pl.scale.setScalar(Math.max(0.001, span(p, 0.08 + i * 0.16, 0.24 + i * 0.16))); });
      dots.visible = p > 0.55; tags.forEach((tg, i) => (tg.material.opacity = span(p, 0.6 + i * 0.08, 0.7 + i * 0.08)));
      g.rotation.z = t * 0.05;
    };
  }

  build_icosahedron(g) {
    const T = this.T, phi = this.d.phi, raw = this.d.raw.map((v) => new T.Vector3(...v));
    const sph = this.sphere(S); sph.position.z = LIFT; g.add(sph);
    const lab = this.at(this.label("radius 1", 0.3, "#bfe4ff"), S * 0.75, 0, LIFT + S * 0.85); g.add(lab);
    const rr = Math.sqrt(1 + phi * phi);
    const posed = (scale) => raw.map((v) => v.clone().multiplyScalar(scale).add(new T.Vector3(0, 0, LIFT)));
    const p0 = posed(S);
    const icoS = this.struts(this.d.icoEdges.map(([a, b]) => [p0[a], p0[b], COLORS.LONG]), 0.045), icoN = this.nodes(p0, 0.08, COLORS.node);
    g.add(icoS, icoN);
    return (p, t) => {
      const scale = S / rr * (1 + (rr - 1) * (1 - span(p, 0.25, 0.7)));       // raw size shrinks to the unit sphere
      const pts = posed(scale);
      this.moveStruts(icoS, this.d.icoEdges.map(([a, b]) => [pts[a], pts[b]]), 0.045);
      this.moveNodes(icoN, pts, 0.08);
      lab.material.opacity = span(p, 0.7, 0.85);
      g.rotation.z = t * 0.06;
    };
  }

  _icoUnit() {
    const T = this.T;
    return this.d.ico.map((v) => new T.Vector3(...v).multiplyScalar(S).add(new T.Vector3(0, 0, LIFT)));
  }

  _midpoints() {
    // flat vertices nearer the centre than 1 are the 30 edge midpoints (the 12 corners sit on the sphere)
    const T = this.T, out = [];
    this.d.mid.forEach((v, i) => { const m = new T.Vector3(...v); if (m.length() < 0.999) out.push({ i, m }); });
    return out;
  }

  build_midpoints(g) {
    const T = this.T, pts = this._icoUnit();
    const sph = this.sphere(S, 0.06); sph.position.z = LIFT; g.add(sph);
    g.add(this.struts(this.d.icoEdges.map(([a, b]) => [pts[a], pts[b], COLORS.plain]), 0.03), this.nodes(pts, 0.07, COLORS.node));
    const mids = this._midpoints().map(({ m }) => m.clone().multiplyScalar(S).add(new T.Vector3(0, 0, LIFT)));
    const dots = mids.map((m) => { const d = this.nodes([m], 0.075, COLORS.red); g.add(d); return d; });
    const lab = this.at(this.label("inside the sphere", 0.3, "#ff8a6a"), S * 0.7, -S * 0.6, LIFT + S * 1.05); g.add(lab);
    return (p, t) => { dots.forEach((d, i) => (d.visible = p > 0.12 + 0.55 * (i / dots.length))); lab.material.opacity = span(p, 0.7, 0.8); g.rotation.z = t * 0.05; };
  }

  build_projection(g) {
    const T = this.T, pts = this._icoUnit(), C = new T.Vector3(0, 0, LIFT);
    const sph = this.sphere(S, 0.06); sph.position.z = LIFT; g.add(sph);
    g.add(this.nodes(pts, 0.07, COLORS.node));
    const mids = this._midpoints();
    const rays = this.struts(mids.map(({ m }) => [C, m.clone().normalize().multiplyScalar(S * 1.08).add(C), 0x8fa3b8]), 0.008, 0x8fa3b8, 0.5);
    g.add(rays);
    const at = (k) => mids.map(({ m }) => m.clone().multiplyScalar(1 + (1 / m.length() - 1) * k).multiplyScalar(S).add(C));
    const moving = this.nodes(at(0), 0.075, COLORS.red); g.add(moving);
    const edges = this.struts(this.d.edges.map(([a, b]) => [new T.Vector3(...this.d.verts[a]).multiplyScalar(S).add(C), new T.Vector3(...this.d.verts[b]).multiplyScalar(S).add(C), COLORS.plain]), 0.025, COLORS.plain, 0.999);
    g.add(edges);
    return (p, t) => {
      this.moveNodes(moving, at(span(p, 0.15, 0.7)), 0.075);
      edges.visible = p > 0.72; edges.material.opacity = span(p, 0.72, 0.9);
      rays.visible = p < 0.85;
      g.rotation.z = t * 0.05;
    };
  }

  build_classes(g) {
    const T = this.T, C = new T.Vector3(0, 0, LIFT);
    const sel = (cls) => this.d.edges.map(([a, b], i) => [new T.Vector3(...this.d.verts[a]).multiplyScalar(S).add(C), new T.Vector3(...this.d.verts[b]).multiplyScalar(S).add(C), COLORS[this.d.edgeClass[i]], this.d.edgeClass[i]])
      .filter((s) => s[3] === cls);
    const sh = this.struts(sel("SHORT"), 0.035), lo = this.struts(sel("LONG"), 0.035);
    g.add(sh, lo, this.nodes(this.d.verts.map((v) => new T.Vector3(...v).multiplyScalar(S).add(C)), 0.06, COLORS.node));
    const n = (cls) => this.d.edgeClass.filter((c) => c === cls).length;
    const ls = this.at(this.label(`SHORT  ${n("SHORT")}`, 0.32, "#5ec8f2"), 3.0, 0, LIFT + 0.4), ll = this.at(this.label(`LONG  ${n("LONG")}`, 0.32, "#ffb04a"), 3.0, 0, LIFT - 0.2);
    g.add(ls, ll);
    return (p, t) => { sh.visible = p > 0.15; lo.visible = p > 0.4; ls.material.opacity = span(p, 0.15, 0.25); ll.material.opacity = span(p, 0.4, 0.5); g.rotation.z = t * 0.06; };
  }

  build_derivations(g) {
    const T = this.T, C = new T.Vector3(0, 0, LIFT);
    const sph = this.sphere(S, 0.05); sph.position.z = LIFT; g.add(sph);
    // the LONG chord nearest the equator, so the diagram stands upright and can be seen square
    const longs = this.d.edges.filter((_, i) => this.d.edgeClass[i] === "LONG");
    const [ia, ib] = longs.reduce((best, e) => Math.abs(this.d.verts[e[0]][2] + this.d.verts[e[1]][2]) < Math.abs(this.d.verts[best[0]][2] + this.d.verts[best[1]][2]) ? e : best);
    const u = new T.Vector3(...this.d.verts[ia]).multiplyScalar(S).add(C), v = new T.Vector3(...this.d.verts[ib]).multiplyScalar(S).add(C);
    g.add(this.struts([[C, u, COLORS.plain], [C, v, COLORS.plain]], 0.03), this.nodes([C, u, v], 0.08, COLORS.node));
    const chord = this.struts([[u, v, COLORS.LONG]], 0.05); g.add(chord);
    const arcPts = [];
    for (let k = 0; k <= 24; k++) arcPts.push(new T.Vector3().copy(u).sub(C).lerp(new T.Vector3().copy(v).sub(C), k / 24).normalize().multiplyScalar(S * 0.35).add(C));
    const arc = this.struts(arcPts.slice(1).map((q, k) => [arcPts[k], q, COLORS.accent]), 0.015); g.add(arc);
    const lu = this.at(this.label("u", 0.34), ...u.clone().lerp(C, 0.45).toArray()), lv = this.at(this.label("v", 0.34), ...v.clone().lerp(C, 0.45).toArray());
    const lt = this.at(this.label("θ", 0.36, "#ffd27a"), ...arcPts[12].clone().lerp(C, -0.6).toArray()), lc = this.at(this.label("c", 0.38, "#ffb04a"), ...u.clone().lerp(v, 0.5).lerp(C, -0.12).toArray());
    g.add(lu, lv, lt, lc);
    this.derivDir = new T.Vector3((u.x + v.x) / 2, (u.y + v.y) / 2, 0).normalize().add(new T.Vector3(0, 0, 0.28)).normalize();
    return (p, t) => { arc.visible = p > 0.3; lt.material.opacity = span(p, 0.3, 0.4); chord.visible = p > 0.55; lc.material.opacity = span(p, 0.55, 0.65); };
  }

  build_audit(g) {
    const T = this.T, f = this.d.fit;
    const dome = new T.Group(); dome.add(this.domeStruts(0.05), this.domeNodes()); g.add(dome);
    const iL = this.hemiEdges.find(([a, b]) => this.edgeClass.get(key(a, b)) === "LONG"), iS = this.hemiEdges.find(([a, b]) => this.edgeClass.get(key(a, b)) === "SHORT");
    const hl = this.struts([[this.sv(iL[0], 0), this.sv(iL[1], 0), 0xffffff], [this.sv(iS[0], 0), this.sv(iS[1], 0), 0xffffff]], 0.085, 0xffffff);
    dome.add(hl);
    const top = this.verts.reduce((a, v, i) => (v.z > this.verts[a].z ? i : a), 0);
    const rline = this.struts([[new T.Vector3(0, 0, 0), this.sv(top, 0), COLORS.accent]], 0.03); g.add(rline);
    const lL = this.label(`LONG measured ${f.long} in`, 0.28, "#ffb04a"), lS = this.label(`SHORT measured ${f.short} in`, 0.28, "#5ec8f2"), lR = this.label(`R = ${f.R.toFixed(2)} in`, 0.32, "#ffd27a");
    this.at(lL, ...this.sv(iL[0], 0).lerp(this.sv(iL[1], 0), 0.5).multiplyScalar(1.25).toArray());
    this.at(lS, ...this.sv(iS[0], 0).lerp(this.sv(iS[1], 0), 0.5).multiplyScalar(1.25).toArray());
    this.at(lR, 0.35, 0, S * 0.5);
    g.add(lL, lS, lR);
    return (p, t) => { hl.visible = p > 0.1; lL.material.opacity = lS.material.opacity = span(p, 0.12, 0.25); rline.visible = lR.visible = p > 0.5; lR.material.opacity = span(p, 0.5, 0.6); };
  }

  build_cutlist(g) {
    const T = this.T, f = this.d.fit, k = 4.6 / (this.d.long * f.R);
    const L = this.d.long * f.R, Sh = this.d.short * f.R;
    const nL = [...this.edgeClass.entries()].filter(([kk, c]) => c === "LONG" && this.hemiEdges.some(([a, b]) => key(a, b) === kk)).length;
    const nS = [...this.edgeClass.entries()].filter(([kk, c]) => c === "SHORT" && this.hemiEdges.some(([a, b]) => key(a, b) === kk)).length;
    const stack = (n, len, y, col) => {
      const segs = [];
      for (let i = 0; i < n; i++) {
        const row = Math.floor(i / 7), colm = i % 7, z = 0.09 + row * 0.13, yy = y + (colm - 3) * 0.14;
        segs.push([new T.Vector3(-len * k / 2, yy, z), new T.Vector3(len * k / 2, yy, z), col]);
      }
      return this.struts(segs, 0.055);
    };
    const a = stack(nL, L, -0.75, COLORS.LONG), b = stack(nS, Sh, 0.95, COLORS.SHORT);
    g.add(a, b);
    const la = this.at(this.label(`${nL} x LONG  ${L.toFixed(2)} in centre to centre`, 0.26, "#ffb04a"), 0, -0.75, 1.15);
    const lb = this.at(this.label(`${nS} x SHORT  ${Sh.toFixed(2)} in centre to centre`, 0.26, "#5ec8f2"), 0, 0.95, 1.15);
    g.add(la, lb);
    return (p) => { a.visible = la.visible = p > 0.08; b.visible = lb.visible = p > 0.3; la.material.opacity = span(p, 0.08, 0.2); lb.material.opacity = span(p, 0.3, 0.42); };
  }

  build_assembly(g) {
    const T = this.T;
    const faces = (this.d.hemiFaces || []).map((f) => ({ f, z: f.reduce((s, i) => s + this.verts[i].z, 0) / 3 })).sort((a, b) => a.z - b.z);
    const items = faces.map(({ f }) => {
      const pts = f.map((i) => this.sv(i, 0));
      const grp = new T.Group();
      grp.add(this.struts(pts.map((q, j) => [q, pts[(j + 1) % 3], COLORS[this.edgeClass.get(key(f[j], f[(j + 1) % 3]))] ?? COLORS.plain]), 0.05));
      const geo = new T.BufferGeometry().setFromPoints(pts); geo.setIndex([0, 1, 2]); geo.computeVertexNormals();
      grp.add(new T.Mesh(geo, new T.MeshStandardMaterial({ color: 0xf3ead8, transparent: true, opacity: 0.18, side: T.DoubleSide, depthWrite: false })));
      g.add(grp);
      return grp;
    });
    return (p, t) => {
      items.forEach((it, i) => {
        const at = 0.06 + 0.8 * (i / items.length), k = span(p, at, at + 0.05);
        it.visible = k > 0; it.position.z = (1 - k) * 0.6;
      });
      g.rotation.z = t * 0.05;
    };
  }

  build_verification(g) {
    const T = this.T, f = this.d.fit;
    const dome = new T.Group(); dome.add(this.domeStruts(0.045), this.domeNodes()); g.add(dome);
    const ring = this.d.baseRing || [];
    const diag = [];
    for (let i = 0; i < ring.length / 2; i++) diag.push([this.sv(ring[i], 0).setZ(0.03), this.sv(ring[i + ring.length / 2], 0).setZ(0.03), COLORS.accent]);
    const diags = this.struts(diag, 0.02); g.add(diags);
    const top = this.verts.reduce((a, v, i) => (v.z > this.verts[a].z ? i : a), 0);
    const h = this.struts([[new T.Vector3(0, 0, 0), this.sv(top, 0), COLORS.red]], 0.025); g.add(h);
    const ld = this.at(this.label(`base diagonals: 2R = ${(2 * f.R).toFixed(1)} in`, 0.28, "#ffd27a"), 0, -S * 1.25, 0.25);
    const lh = this.at(this.label(`height: R = ${f.R.toFixed(1)} in`, 0.28, "#ff8a6a"), 0.4, 0, S * 1.1);
    g.add(ld, lh);
    return (p, t) => { diags.visible = p > 0.15; ld.material.opacity = span(p, 0.15, 0.25); h.visible = p > 0.45; lh.material.opacity = span(p, 0.45, 0.55); dome.rotation.z = t * 0.04; };
  }

  build_finale(g) {
    const T = this.T, phases = ["icosahedron", "midpoints", "projection", "hero"];
    const subs = phases.map((n) => { const sub = new T.Group(); g.add(sub); const pose = this["build_" + n].call(this, sub); return { sub, pose, n }; });
    return (p, t) => {
      const i = Math.min(phases.length - 1, Math.floor(p * phases.length)), lp = (p * phases.length) - i;
      subs.forEach((s, k) => (s.sub.visible = k === i));
      subs[i].pose(Math.min(1, lp * 1.15), t);
      if (subs[i].n === "hero") subs[i].sub.position.z = 0.0; else subs[i].sub.position.z = -0.6;
    };
  }
}

function key(a, b) { return a < b ? `${a}-${b}` : `${b}-${a}`; }
function roundRect(g, x, y, w, h, r) { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); }
