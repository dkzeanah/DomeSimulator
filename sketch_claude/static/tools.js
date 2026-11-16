// The floating toolbar's drawing tools: lines (struts), dimensions that stay, notes pinned to a
// point, paint for a piece / a family / a material, an eraser, undo and redo. What you draw and
// paint is kept with the design (in this browser) and can be exported or imported as JSON.

const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const STORE = "dome-sketch-marks:";
const POS = "dome-sketch-toolbar";

function hash(s) { let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(36); }
function load(key, fallback) { try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback; } catch { return fallback; } }
function save(key, v) { try { localStorage.setItem(key, JSON.stringify(v)); } catch { /* not kept */ } }

export function initTools(ctx) {
  const { THREE, S, U, overlay, canvas } = ctx;
  const group = new THREE.Group();
  overlay.add(group);
  const labels = $("#labels");
  let undo = [], redo = [], start = null, rubber = null, labelEls = [];

  const HINT = {
    dim: "Dimension: click two points (they snap to corners). It stays, and is saved with the design.",
    line: "Line: click to start, click again for each corner. Esc ends the line.",
    note: "Note: click a point and type the note.",
    paint: "Paint: click a piece. Shift-click paints its whole family, Alt-click its whole material. The colour is beside the bucket.",
    erase: "Eraser: click a line, dimension or note, or a painted piece to clear its paint.",
  };

  const key = () => STORE + `${S.kind}:` + hash(JSON.stringify(S.spec || {}));
  function persist() { save(key(), S.marks); }
  function snapshot() { undo.push(JSON.stringify(S.marks)); if (undo.length > 100) undo.shift(); redo = []; }
  function changed() { persist(); draw(); ctx.applyStyle(); }

  // ---------------------------------------------------------------- drawing what is kept
  const lineMat = (c) => new THREE.MeshLambertMaterial({ color: c });
  const dimMat = new THREE.LineDashedMaterial({ color: 0x1f6fd1, dashSize: 0.06, gapSize: 0.03, depthTest: false });
  function rod(a, b, r, mat) {
    const A = new THREE.Vector3(...a), B = new THREE.Vector3(...b), L = A.distanceTo(B);
    const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, Math.max(L, 1e-4), 10), mat);
    m.position.copy(A).add(B).multiplyScalar(0.5);
    m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), B.clone().sub(A).normalize());
    return m;
  }
  function draw() {
    group.clear();
    for (const el of labelEls) el.remove();
    labelEls = [];
    for (const it of S.marks.items) {
      if (it.type === "line") {
        const mat = lineMat(it.color || "#c45e29");
        group.add(rod(it.a, it.b, 0.012, mat));
        for (const p of [it.a, it.b]) { const s = new THREE.Mesh(new THREE.SphereGeometry(0.02, 10, 8), mat); s.position.set(...p); group.add(s); }
        addLabel(it, "linelabel", U.len(dist(it.a, it.b)), mid(it.a, it.b));
      } else if (it.type === "dim") {
        const g = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(...it.a), new THREE.Vector3(...it.b)]);
        const l = new THREE.Line(g, dimMat); l.computeLineDistances(); l.renderOrder = 11; group.add(l);
        addLabel(it, "dimlabel keep", U.len(dist(it.a, it.b)), mid(it.a, it.b));
      } else if (it.type === "note") {
        const s = new THREE.Mesh(new THREE.SphereGeometry(0.025, 10, 8), new THREE.MeshBasicMaterial({ color: it.color || "#1d1b18", depthTest: false }));
        s.position.set(...it.p); s.renderOrder = 12; group.add(s);
        addLabel(it, "notelabel", it.text, it.p);
      }
    }
  }
  function addLabel(it, cls, text, p) {
    const el = document.createElement("div");
    el.className = cls; el.textContent = text; el.dataset.id = it.id;
    labels.append(el);
    labelEls.push(el);
    el._p = new THREE.Vector3(...p);
  }
  ctx.post.push(() => {
    for (const el of labelEls) {
      const s = ctx.screenOf(el._p);
      el.style.left = `${s.x}px`; el.style.top = `${s.y}px`; el.style.display = s.on ? "" : "none";
    }
  });
  const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
  const mid = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2];
  const arr = (v) => [v.x, v.y, v.z];

  // ---------------------------------------------------------------- the pointer
  function pointOf(ev, hit) {
    if (hit) return ctx.snapPoint(hit, ev).p;
    return ctx.pickGround(ev);
  }
  function clearRubber() { if (rubber) { overlay.remove(rubber); rubber = null; } }
  function click(tool, ev, hit) {
    if (tool === "line" || tool === "dim") {
      const p = pointOf(ev, hit);
      if (!p) return;
      if (!start) { start = p; return; }
      snapshot();
      S.marks.items.push({ id: crypto.randomUUID ? crypto.randomUUID() : String(Date.now() + Math.random()), type: tool, a: arr(start), b: arr(p),
                           color: tool === "line" ? $("#paintcol").value : undefined });
      start = tool === "line" ? p : null;              // a line goes on from where it ended
      if (!start) clearRubber();
      changed();
      ctx.toast(tool === "line" ? `Line: ${U.len(dist(S.marks.items.at(-1).a, S.marks.items.at(-1).b))}. Click the next corner, or Esc.` : "Dimension kept.");
    } else if (tool === "note") {
      const p = pointOf(ev, hit);
      if (!p) return;
      const text = window.prompt("Note");
      if (!text) return;
      snapshot();
      S.marks.items.push({ id: String(Date.now() + Math.random()), type: "note", p: arr(p), text });
      changed();
    } else if (tool === "paint") {
      if (!hit) return;
      const p = hit.object.userData.piece, col = $("#paintcol").value;
      snapshot();
      const ids = ev.shiftKey && p.info.mark ? all((q) => q.info.mark === p.info.mark)
        : ev.altKey ? all((q) => q.material === p.material) : [p.id];
      for (const id of ids) S.marks.paint[id] = col;
      changed();
      ctx.toast(`Painted ${ids.length} piece${ids.length === 1 ? "" : "s"}.`);
    } else if (tool === "erase") {
      if (hit && S.marks.paint[hit.object.userData.piece.id]) {
        snapshot(); delete S.marks.paint[hit.object.userData.piece.id]; changed(); return;
      }
      const near = nearest(ev);
      if (near) { snapshot(); S.marks.items = S.marks.items.filter((it) => it !== near); changed(); }
    }
  }
  function all(f) { return [...S.pieces.values()].map((g) => g.userData.piece).filter(f).map((p) => p.id); }
  function nearest(ev) {
    const r = canvas.getBoundingClientRect(), x = ev.clientX - r.left, y = ev.clientY - r.top;
    let best = null, bd = 12;
    for (const it of S.marks.items) {
      let d;
      if (it.type === "note") { const s = ctx.screenOf(new THREE.Vector3(...it.p)); d = Math.hypot(s.x - x, s.y - y); }
      else {
        const a = ctx.screenOf(new THREE.Vector3(...it.a)), b = ctx.screenOf(new THREE.Vector3(...it.b));
        const vx = b.x - a.x, vy = b.y - a.y, t = Math.max(0, Math.min(1, ((x - a.x) * vx + (y - a.y) * vy) / (vx * vx + vy * vy || 1)));
        d = Math.hypot(a.x + vx * t - x, a.y + vy * t - y);
      }
      if (d < bd) { bd = d; best = it; }
    }
    return best;
  }
  function move(tool, ev) {
    if (!(tool === "line" || tool === "dim") || !start) return;
    const p = pointOf(ev, ctx.pick(ev));
    if (!p) return;
    clearRubber();
    const g = new THREE.BufferGeometry().setFromPoints([start, p]);
    rubber = new THREE.Line(g, new THREE.LineDashedMaterial({ color: tool === "line" ? 0xc45e29 : 0x1f6fd1, dashSize: 0.05, gapSize: 0.03, depthTest: false }));
    rubber.computeLineDistances(); rubber.renderOrder = 12;
    overlay.add(rubber);
    ctx.toast(`${tool === "line" ? "Line" : "Dimension"}: ${U.len(start.distanceTo(p))}`);
  }
  function cancel() { start = null; clearRubber(); }

  // ---------------------------------------------------------------- undo, settings, the toolbar itself
  function doUndo() { if (!undo.length) return; redo.push(JSON.stringify(S.marks)); S.marks = JSON.parse(undo.pop()); changed(); }
  function doRedo() { if (!redo.length) return; undo.push(JSON.stringify(S.marks)); S.marks = JSON.parse(redo.pop()); changed(); }
  $("#undo").onclick = doUndo;
  $("#redo").onclick = doRedo;

  $("#settings-btn").onclick = (e) => { e.stopPropagation(); $("#settings").hidden = !$("#settings").hidden; };
  document.addEventListener("pointerdown", (e) => { if (!$("#settings").hidden && !e.target.closest("#settings, #settings-btn")) $("#settings").hidden = true; });
  $("#edges").onchange = () => { S.edges = $("#edges").value; ctx.applyStyle(); };
  $("#skinop").oninput = () => { S.skinOpacity = $("#skinop").value / 100; ctx.applyStyle(); };
  $("#bgcol").oninput = () => { S.bg = $("#bgcol").value; ctx.applyStyle(); };
  $("#bgreset").onclick = () => { S.bg = null; ctx.applyStyle(); };
  $("#marks-export").onclick = () => {
    const blob = new Blob([JSON.stringify({ spec: S.spec, marks: S.marks }, null, 1)], { type: "application/json" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "dome-sketch-drawings.json"; a.click();
  };
  $("#marks-import").onclick = () => $("#marks-file").click();
  $("#marks-file").onchange = async () => {
    const f = $("#marks-file").files[0]; if (!f) return;
    try { const d = JSON.parse(await f.text()); snapshot(); S.marks = { items: d.marks.items || [], paint: d.marks.paint || {} }; changed(); ctx.toast("Drawings imported."); }
    catch { ctx.toast("That file is not a Dome Sketch drawings file."); }
    $("#marks-file").value = "";
  };
  $("#marks-clear").onclick = () => { if (!confirm("Clear every line, dimension, note and paint on this design?")) return; snapshot(); S.marks = { items: [], paint: {} }; changed(); };

  // drag, fold, remember
  const bar = $("#ftb"), grip = $("#ftb-grip");
  const pos = load(POS, null);
  if (pos) { bar.style.left = `${pos.x}px`; bar.style.top = `${pos.y}px`; bar.classList.toggle("folded", !!pos.folded); }
  let drag = null;
  grip.addEventListener("pointerdown", (e) => { drag = { dx: e.clientX - bar.offsetLeft, dy: e.clientY - bar.offsetTop }; grip.setPointerCapture(e.pointerId); });
  grip.addEventListener("pointermove", (e) => {
    if (!drag) return;
    const st = $("#stage").getBoundingClientRect();
    const x = Math.max(0, Math.min(st.width - 60, e.clientX - drag.dx)), y = Math.max(0, Math.min(st.height - 40, e.clientY - drag.dy));
    bar.style.left = `${x}px`; bar.style.top = `${y}px`;
  });
  grip.addEventListener("pointerup", () => { if (!drag) return; drag = null; keepPos(); });
  grip.addEventListener("dblclick", () => { bar.style.left = ""; bar.style.top = ""; keepPos(); });
  $("#ftb-fold").onclick = () => { bar.classList.toggle("folded"); $("#ftb-fold").innerHTML = bar.classList.contains("folded") ? "&#9654;" : "&#9664;"; keepPos(); };
  function keepPos() { save(POS, { x: bar.offsetLeft, y: bar.offsetTop, folded: bar.classList.contains("folded") }); }

  return {
    click, move, cancel, undo: doUndo, redo: doRedo,
    hint: (t) => HINT[t],
    toolChanged: (t) => { if (t !== "line" && t !== "dim") cancel(); },
    loadMarks: () => { const m = load(key(), null); S.marks = m && m.items ? m : { items: [], paint: {} }; undo = []; redo = []; draw(); },
    relabel: draw,
  };
}
