// The Dome Creator's design, drawn on the space's stage: its struts in their own cross section
// (a wedge's bark faces in, out or alternates, as creator.ts says), each panel its own piece in
// its own type's colour (so the studio can paint them one by one), the cladding layers as shells
// over the panels, and the fit-out on the floor -- rooms, partition walls, props, wiring and
// plumbing -- all exactly as creator.ts computed them, scaled to stand on the pedestal (the
// Creator works in metres, the world in feet). Colours are the Creator's own (materials.py).

import * as THREE from "three";
import { T, type Design } from "./creator";

const FRAME: Record<string, string> = {
  "Galvanized Steel": "#a9b0b8", "Structural Steel": "#6f767e", "Rebar Steel": "#7a5a44", Aluminum: "#cfd4da",
  "Timber (SPF)": "#c8914e", "Whole Tree Trunk": "#6a4a2e", "PVC Pipe": "#eeeeea", Bamboo: "#c9b26a",
};

/** Fit the dome to a stage this many feet in radius. */
export const STAGE_RADIUS_FT = 8.2;

const rgb = (c: number[], k = 1) => new THREE.Color(Math.min(1, c[0] * k), Math.min(1, c[1] * k), Math.min(1, c[2] * k));

export interface DrawOptions {
  /** Hide the cladding layers (so the panels underneath can be painted). */
  layers?: boolean;
  /** Draw the fit-out: rooms, walls, props, runs. */
  fitout?: boolean;
  /** Pull the layers apart from the panels, in metres, to see the stack. */
  explode?: number;
  /** The panel the studio's brush is over. */
  highlight?: number | null;
  /** Painting panels: the layers turn see-through, and clicks pass through them to the panels. */
  paint?: boolean;
}

export function drawDesign(d: Design, o: DrawOptions = {}): THREE.Group {
  const g = new THREE.Group();
  const r = d.config.radius;
  const s = STAGE_RADIUS_FT / r;
  const lift = -d.baseZ * r;                     // the Creator's base plane sits on the stage
  const at = (p: number[]) => new THREE.Vector3(p[0] * s, (p[2] + lift) * s, -p[1] * s);
  const centre = at([0, 0, 0]);

  // ---- the frame: each strut swept along its own profile, its radial axis outward
  const shape = T.strutShapes.find((x) => x.name === d.config.strutShape) ?? T.strutShapes[0];
  const frameRgb = T.frameColors.find((c) => c.name === d.config.frameColor);
  const frameColour = frameRgb && frameRgb.rgb[0] >= 0 ? rgb(frameRgb.rgb) : new THREE.Color(FRAME[d.config.frameMaterial] || "#c8914e");
  const w = Math.max(0.05, d.config.strutWidth * s * 1.6);        // drawn a little heavier than scale, to read on the stage
  const section = (flip: boolean) => {
    const pts = shape.profile.map(([u, v]) => new THREE.Vector2(u * w, (flip ? -v : v) * w));
    return new THREE.ExtrudeGeometry(new THREE.Shape(flip ? pts.reverse() : pts), { depth: 1, bevelEnabled: false, steps: 1 });
  };
  const frameMat = new THREE.MeshLambertMaterial({ color: frameColour, flatShading: shape.kind !== "circle" });
  const kinds = [section(false), section(true)];
  const counts = [0, 0];
  const flipOf = (i: number) => (shape.kind === "wedge" ? d.wedgeFlips[d.strutPiece[i]] ?? false : false);
  d.struts.forEach((_, i) => counts[flipOf(i) ? 1 : 0]++);
  const bars = kinds.map((geo, k) => new THREE.InstancedMesh(geo, frameMat, Math.max(1, counts[k])));
  const fill = [0, 0];
  const m = new THREE.Matrix4();
  d.struts.forEach(([p0, p1], i) => {
    const a = at(p0), b = at(p1), axis = b.clone().sub(a);
    const lenS = axis.length(); axis.normalize();
    const radial = a.clone().add(b).multiplyScalar(0.5).sub(centre).normalize();
    const u = new THREE.Vector3().crossVectors(radial, axis).normalize();
    const v = new THREE.Vector3().crossVectors(axis, u).normalize();     // radial, outward
    // the extrusion runs along +z of the shape: point it along the strut
    m.makeBasis(u, v, axis.clone().multiplyScalar(lenS)).setPosition(a);
    const k = flipOf(i) ? 1 : 0;
    bars[k].setMatrixAt(fill[k]++, m);
  });
  bars.forEach((b2, k) => { b2.count = counts[k]; b2.castShadow = true; g.add(b2); });

  if (d.hubCount) {
    const nodes = new THREE.InstancedMesh(new THREE.SphereGeometry(w * 1.25, 8, 6),
      new THREE.MeshLambertMaterial({ color: d.config.hubStyle === "Metal Brackets" ? "#8a9098" : "#3a3a3a" }), d.hubCount);
    const seen = new Map<string, THREE.Vector3>();
    for (const [p0, p1] of d.struts) for (const p of [p0, p1]) seen.set(p.map((x) => x.toFixed(4)).join(","), at(p));
    [...seen.values()].slice(0, d.hubCount).forEach((vv, i) => { m.makeTranslation(vv.x, vv.y, vv.z); nodes.setMatrixAt(i, m); });
    g.add(nodes);
  }

  // ---- the panels, one piece each, in their own type's colour
  const tint = T.panelColors.find((c) => c.name === d.config.panelColor)?.rgb ?? [1, 1, 1];
  const mats = new Map<string, THREE.Material>();
  const matFor = (name: string, hot: boolean) => {
    const key = `${name}|${hot}`;
    if (!mats.has(key)) {
      const pt = T.panels.find((p) => p.name === name) ?? T.panels.find((p) => p.name === "Plywood")!;
      const col = rgb(pt.rgb);
      if (pt.colorable) col.multiply(new THREE.Color(tint[0], tint[1], tint[2]));
      if (hot) col.lerp(new THREE.Color("#ffe24a"), 0.55);
      const alpha = pt.name === "Open" ? (hot ? 0.35 : 0) : Math.max(0.18, pt.alpha);
      mats.set(key, new THREE.MeshLambertMaterial({ color: col, transparent: alpha < 0.95, opacity: alpha, side: THREE.DoubleSide,
        depthWrite: alpha >= 0.95, emissive: pt.wattsPerM2 > 0 ? new THREE.Color("#0a1440") : new THREE.Color(0) }));
    }
    return mats.get(key)!;
  };
  d.panels.forEach((t, i) => {
    const name = d.panelTypes[i];
    // a custom (Panel Lab) panel looks like its base
    const shown = d.config.customPanels?.[name]?.base ?? name;
    const pts = t.map((p) => at(p).sub(centre).multiplyScalar(0.993).add(centre));     // just inside the struts
    const pg = new THREE.BufferGeometry().setFromPoints(pts);
    pg.setIndex([0, 1, 2]); pg.computeVertexNormals();
    const mesh = new THREE.Mesh(pg, matFor(shown, o.highlight === i));
    mesh.userData.part = { id: `panel:${i}`, name: `Panel ${i + 1}: ${name}`, examine: `Panel ${i + 1} of ${d.panelCount}, ${name}.` };
    g.add(mesh);
  });

  // ---- the cladding layers: a shell each, stacked outward by their thickness
  if (o.layers !== false && d.layerRows.length) {
    let out = 0.02 + (o.explode ?? 0);
    for (const row of d.layerRows) {
      const l = T.layers.find((x) => x.name === row.name)!;
      out += Math.max(0.012, l.thickness) + (o.explode ?? 0);
      const pos: number[] = [];
      d.panels.forEach((t, i) => {
        const pt = T.panels.find((p) => p.name === (d.config.customPanels?.[d.panelTypes[i]]?.base ?? d.panelTypes[i]));
        if (!pt || pt.name === "Open" || pt.isWindow) return;
        for (const p of t) {
          const n = Math.hypot(p[0], p[1], p[2]);
          const q = at(p.map((x) => (x * (n + out)) / n));
          pos.push(q.x, q.y, q.z);
        }
      });
      const lg = new THREE.BufferGeometry();
      lg.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
      lg.computeVertexNormals();
      const lm = new THREE.Mesh(lg, new THREE.MeshLambertMaterial({ color: rgb(l.rgb), transparent: true, opacity: o.paint ? 0.18 : Math.min(0.85, l.alpha * 0.75), side: THREE.DoubleSide, depthWrite: false, flatShading: true }));
      if (!o.paint) lm.userData.part = { id: `layer:${row.name}`, name: `Cladding: ${row.name}`, examine: `${row.name}, ${row.area.toFixed(1)} m² over the closed panels.` };
      g.add(lm);
    }
  }

  // ---- the fit-out: the floor's sections, walls, props and runs
  if (o.fitout !== false) {
    const fr = d.floorRadius, y0 = lift * s + 0.03;
    const floorAt = (x: number, y: number, z = 0) => new THREE.Vector3(x * s, y0 + z * s, -y * s);
    const sections = d.config.sections ?? [];
    const roomCol = (name: string) => rgb(T.fitout.rooms.find((x) => x.name === name)?.rgb ?? [0.55, 0.55, 0.55]);
    const inner = fr * T.fitout.centerFraction;
    const disc = new THREE.Mesh(new THREE.CircleGeometry(inner * s, 40), new THREE.MeshLambertMaterial({ color: roomCol(sections[0] ?? "Unassigned"), transparent: true, opacity: 0.75 }));
    disc.rotation.x = -Math.PI / 2; disc.position.copy(floorAt(0, 0, 0.002));
    disc.userData.part = { id: "section:0", name: `S1 · Center: ${sections[0] ?? "Unassigned"}` };
    g.add(disc);
    for (let k = 0; k < 9; k++) {
      const a0 = (k * T.fitout.wedgeDegrees * Math.PI) / 180, a1 = ((k + 1) * T.fitout.wedgeDegrees * Math.PI) / 180;
      // a ring sector; RingGeometry's angles run from +x counter-clockwise, the Creator's from +y clockwise
      const ringGeo = new THREE.RingGeometry(inner * s, fr * s, 12, 1, Math.PI / 2 - a1, a1 - a0);
      const sec = new THREE.Mesh(ringGeo, new THREE.MeshLambertMaterial({ color: roomCol(sections[k + 1] ?? "Unassigned"), transparent: true, opacity: 0.6 }));
      sec.rotation.x = -Math.PI / 2; sec.position.copy(floorAt(0, 0, 0.001));
      sec.userData.part = { id: `section:${k + 1}`, name: `S${k + 2}: ${sections[k + 1] ?? "Unassigned"}` };
      g.add(sec);
    }
    const wallMat = new THREE.MeshLambertMaterial({ color: "#e8e2d6" });
    for (const wl of d.walls) {
      const a = floorAt(wl.inner[0], wl.inner[1]), b = floorAt(wl.outer[0], wl.outer[1]);
      const wall = new THREE.Mesh(new THREE.BoxGeometry(0.08 * s, wl.height * s, wl.length * s), wallMat);
      wall.position.copy(a.clone().add(b).multiplyScalar(0.5)).setY(y0 + (wl.height * s) / 2);
      wall.lookAt(b.x, wall.position.y, b.z);
      wall.userData.part = { id: `wall:${wl.azimuth}`, name: `Partition at ${wl.azimuth}°`, examine: `${wl.length.toFixed(2)} m long, ${wl.height} m high.` };
      g.add(wall);
    }
    const propMat = new Map<string, THREE.Material>();
    const cat = (c: string) => ({ WORKSHOP: "#b07a44", STORAGE: "#8a8a6a", OFFICE: "#5a7ab0", "KITCHEN / BATH": "#7ac0d0", LIGHTING: "#ffe07a", ELECTRICAL: "#e0a030",
      "SITE POWER": "#c06030", FABRICATION: "#8a96a4", "CONCRETE / REBAR": "#9a968c", "ACCESS / HANDLING": "#d0b050", SAFETY: "#d04040", "WATER / CLIMATE": "#4a9ad0" } as Record<string, string>)[c] ?? "#aaaaaa";
    (d.config.props ?? []).forEach((p, i) => {
      const q = T.fitout.props.find((x) => x.name === p.type);
      if (!q) return;
      const mat = propMat.get(q.category) ?? new THREE.MeshLambertMaterial({ color: cat(q.category) });
      propMat.set(q.category, mat);
      const box = new THREE.Mesh(new THREE.BoxGeometry(q.radius * 1.3 * s, q.height * s, q.radius * 1.3 * s), mat);
      box.position.copy(floorAt(p.x, p.y)).setY(y0 + (q.height * s) / 2);
      box.rotation.y = (-p.yaw * Math.PI) / 180;
      box.castShadow = true;
      box.userData.part = { id: `prop:${i}`, name: p.type, examine: `${p.type}: $${q.cost}, ${q.weight} kg${q.watts ? `, ${q.watts} W` : ""}.` };
      g.add(box);
    });
    const line = (runs: typeof d.wireRuns, colour: string, z: number) => {
      if (!runs.length) return;
      const pts: THREE.Vector3[] = [];
      for (const run of runs) pts.push(floorAt(run.from[0], run.from[1], z), floorAt(run.to[0], run.to[1], z));
      g.add(new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color: colour })));
    };
    line(d.wireRuns, "#ffb020", 0.03);
    line(d.pipeRuns, "#3aa0ff", 0.015);
  }
  return g;
}
