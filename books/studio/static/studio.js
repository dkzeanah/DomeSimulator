// The Book Studio's page: an InDesign-style layout editor for the layout books, and a chapter
// editor with the newest PDF and the book's own build for the manuscript books. Every change to a
// layout goes through op(), which mirrors books/studio/doc.py's OPS, onto an undo stack; nothing is
// written until Save. The DeepSeek agent works on a copy on the server and hands it back here.

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const api = async (path, opts = {}) => {
  const r = await fetch(path, { method: opts.method || (opts.body ? "POST" : "GET"), headers: { "Content-Type": "application/json" }, body: opts.body ? JSON.stringify(opts.body) : undefined });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || r.statusText);
  return j;
};
const toast = (t, ms = 2600) => { const el = $("#toast"); el.textContent = t; el.hidden = false; clearTimeout(toast.t); toast.t = setTimeout(() => (el.hidden = true), ms); };
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const uid = (p) => p + Math.random().toString(16).slice(2, 10);
const clone = (x) => JSON.parse(JSON.stringify(x));

const S = { books: null, mode: null, slug: null, doc: null, page: 0, sel: [], tool: "select", zoom: 1, undo: [], redo: [], dirty: false,
  preview: false, editing: null, fills: new Map(), lib: [], chat: [], ms: { key: null, path: null, text: "", dirty: false, pdf: null, n: 1, pages: 0, chat: [] } };
const PX = 96;  // CSS pixels per inch at 100%

// ------------------------------------------------------------------ operations (doc.py's OPS)
const OPS = {
  add_page(d, { after, name = "", copy_of }) {
    const pg = { id: uid("p"), name, frames: [] };
    if (copy_of != null) { const src = pageOf(d, copy_of); pg.frames = src.frames.map((f) => ({ ...clone(f), id: uid("f") })); pg.name = name || (src.name || "") + " (copy)"; }
    const at = after == null ? d.pages.length : Math.max(0, Math.min(d.pages.length, after));
    d.pages.splice(at, 0, pg); return { page: pg.id, number: at + 1 };
  },
  delete_page(d, { page }) { const p = pageOf(d, page); d.pages.splice(d.pages.indexOf(p), 1); return {}; },
  move_page(d, { page, to }) { const p = pageOf(d, page); d.pages.splice(d.pages.indexOf(p), 1); d.pages.splice(Math.max(0, Math.min(d.pages.length, to - 1)), 0, p); return {}; },
  add_frame(d, { page, kind, x, y, w, h, ...rest }) {
    const f = { id: uid("f"), kind, x, y, w, h, rot: 0 };
    if (kind === "text") Object.assign(f, { text: "", style: "body" });
    else if (kind === "image") Object.assign(f, { src: "", fit: "cover" });
    else Object.assign(f, { shape: "rect", fill: "#e8dcc0", stroke: "", strokeW: 0 });
    Object.assign(f, rest); pageOf(d, page).frames.push(f); return { frame: f.id };
  },
  update_frame(d, { frame, ...fields }) { Object.assign(frameOf(d, frame)[1], fields); return {}; },
  delete_frame(d, { frame }) { const [p, f] = frameOf(d, frame); p.frames.splice(p.frames.indexOf(f), 1); return {}; },
  arrange(d, { frame, to }) {
    const [p, f] = frameOf(d, frame); const fs = p.frames; const i = fs.indexOf(f); fs.splice(i, 1);
    fs.splice({ front: fs.length, back: 0, forward: Math.min(fs.length, i + 1), backward: Math.max(0, i - 1) }[to], 0, f); return {};
  },
  set_style(d, { name, ...fields }) { d.styles[name] = { ...(d.styles[name] || clone(d.styles.body)), ...fields }; return {}; },
  set_page_size(d, fields) { for (const [k, v] of Object.entries(fields)) if (v != null && v !== "") d.page[k] = k === "paper" ? v : Number(v); return {}; },
};
const pageOf = (d, page) => (typeof page === "number" ? d.pages[page - 1] : d.pages.find((p) => p.id === page)) || (() => { throw new Error("no page " + page); })();
const frameOf = (d, id) => { for (const p of d.pages) for (const f of p.frames) if (f.id === id) return [p, f]; throw new Error("no frame " + id); };
const cur = () => S.doc.pages[S.page];

function commit(before, label) {
  S.undo.push(before); if (S.undo.length > 150) S.undo.shift();
  S.redo = []; dirty(true, label); draw();
}
function op(name, args, label) {
  const before = clone(S.doc);
  const res = OPS[name](S.doc, args);
  commit(before, label || name.replace("_", " ")); return res;
}
function dirty(on, label) { S.dirty = on; $("#save").disabled = !on; $("#status").textContent = on ? `unsaved${label ? ": " + label : ""}` : "saved"; }

// ------------------------------------------------------------------ rendering
function styleCss(st) {
  const stack = String(st.font).split(",").map((f) => f.trim()).filter(Boolean).map((f) => `'${f}'`).join(",") + ",serif";
  return `font-family:${stack};font-size:${st.size}pt;line-height:${st.leading};color:${st.colour};text-align:${st.align};font-weight:${st.weight};font-style:${st.italic ? "italic" : "normal"}`;
}
function inline(s) { return esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/\*(.+?)\*/g, "<i>$1</i>"); }
function textHtml(text) {
  let t = text || "";
  if (t.includes("{{")) { const filled = S.fills.get(t); if (filled != null) t = filled; else { fill(t); t = t.replace(/\{\{([^}]+)\}\}/g, '‹$1›'); } }
  return t.trim().split(/\n\s*\n/).filter((p) => p.trim()).map((p) => `<p>${p.split("\n").map(inline).join("<br>")}</p>`).join("");
}
const filling = new Set();
async function fill(t) {
  if (filling.has(t)) return; filling.add(t);
  try { const r = await api("/api/studio/fill", { body: { text: t } }); S.fills.set(t, r.text); draw(); } catch { S.fills.set(t, t); }
}
function frameEl(f, scale = 1) {
  const el = document.createElement("div");
  el.className = `fr ${f.kind}` + (f.kind === "image" && !f.src ? " empty" : "");
  el.dataset.id = f.id;
  el.style.cssText = `left:${f.x * PX * scale}px;top:${f.y * PX * scale}px;width:${f.w * PX * scale}px;height:${f.h * PX * scale}px;transform:rotate(${f.rot || 0}deg);opacity:${f.opacity ?? 1}`;
  if (f.kind === "text") {
    const st = S.doc.styles[f.style] || S.doc.styles.body;
    el.style.cssText += ";" + styleCss({ ...st, size: st.size * scale });
    el.innerHTML = textHtml(f.text);
  } else if (f.kind === "image" && f.src) {
    el.innerHTML = `<img src="/file/${esc(f.src)}" style="object-fit:${f.fit || "cover"};object-position:${f.focus || "50% 50%"}" draggable="false">`;
  } else if (f.kind === "shape") {
    el.style.background = f.fill || "transparent";
    el.style.borderRadius = f.shape === "ellipse" ? "50%" : `${(f.radius || 0) * PX * scale}px`;
    if (f.strokeW) el.style.border = `${f.strokeW * scale}pt solid ${f.stroke || "#000"}`;
  }
  return el;
}

function draw() {
  if (S.mode !== "layout" || !S.doc) return;
  const pg = S.doc.page, page = $("#page"), p = cur();
  page.style.width = pg.w * PX * S.zoom + "px"; page.style.height = pg.h * PX * S.zoom + "px"; page.style.background = pg.paper || "#fff";
  page.className = "page" + (S.preview ? "" : " edit");
  page.innerHTML = "";
  for (const f of p.frames) {
    const el = frameEl(f, S.zoom);
    if (S.sel.includes(f.id) && !S.preview) el.classList.add("sel");
    if (S.editing === f.id) { el.classList.add("editing"); el.contentEditable = "plaintext-only"; el.textContent = f.text; }
    page.appendChild(el);
  }
  if (!S.preview) {
    const m = (pg.margin || 0) * PX * S.zoom;
    const g = document.createElement("div"); g.className = "guide"; g.style.cssText = `left:${m}px;top:${m}px;right:${m}px;bottom:${m}px`; page.appendChild(g);
    if (S.sel.length === 1 && S.editing !== S.sel[0]) handles(page);
  }
  if (S.editing) { const el = $(`.fr[data-id="${S.editing}"]`, page); if (el && document.activeElement !== el) { el.focus(); placeCaretEnd(el); } }
  thumbs(); props(); $("#undo").disabled = !S.undo.length; $("#redo").disabled = !S.redo.length;
  $("#zval").textContent = Math.round(S.zoom * 100) + "%";
  const o = $("#book").selectedOptions[0]; if (o) o.textContent = `${S.doc.title} (${S.doc.pages.length} pages)`;
}
function placeCaretEnd(el) { const r = document.createRange(); r.selectNodeContents(el); r.collapse(false); const s = getSelection(); s.removeAllRanges(); s.addRange(r); }

let thumbTimer = 0;
function thumbs() {
  clearTimeout(thumbTimer);
  thumbTimer = setTimeout(() => {
    const box = $("#pages"); box.innerHTML = "";
    const pg = S.doc.page, w = 150, scale = w / (pg.w * PX);
    S.doc.pages.forEach((p, i) => {
      const t = document.createElement("div"); t.className = "thumb" + (i === S.page ? " on" : ""); t.draggable = true; t.dataset.i = i;
      const tp = document.createElement("div"); tp.className = "tp"; tp.style.cssText = `width:${w}px;height:${pg.h * PX * scale}px;background:${pg.paper || "#fff"}`;
      for (const f of p.frames) tp.appendChild(frameEl(f, scale));
      t.appendChild(tp); t.appendChild(document.createTextNode(`${i + 1}${p.name ? " · " + p.name : ""}`));
      t.onclick = () => { S.page = i; S.sel = []; S.editing = null; draw(); };
      t.ondragstart = (e) => { e.dataTransfer.setData("text/page", String(i)); t.classList.add("drag"); };
      t.ondragend = () => t.classList.remove("drag");
      t.ondragover = (e) => { e.preventDefault(); t.classList.add("over"); };
      t.ondragleave = () => t.classList.remove("over");
      t.ondrop = (e) => { e.preventDefault(); t.classList.remove("over"); const from = Number(e.dataTransfer.getData("text/page")); if (from === i) return; const id = S.doc.pages[from].id; op("move_page", { page: id, to: i + 1 }, "move page"); S.page = i; draw(); };
      box.appendChild(t);
    });
  }, 60);
}

// ------------------------------------------------------------------ selection, moving, resizing, drawing
function handles(page) {
  const f = frameOf(S.doc, S.sel[0])[1], z = S.zoom * PX;
  const spots = { nw: [0, 0], n: [.5, 0], ne: [1, 0], e: [1, .5], se: [1, 1], s: [.5, 1], sw: [0, 1], w: [0, .5] };
  for (const [k, [u, v]] of Object.entries(spots)) {
    const h = document.createElement("div"); h.className = "handle"; h.dataset.h = k;
    h.style.cssText = `left:${(f.x + f.w * u) * z - 5}px;top:${(f.y + f.h * v) * z - 5}px;cursor:${k}-resize`;
    page.appendChild(h);
  }
}
const toIn = (e) => { const r = $("#page").getBoundingClientRect(); return { x: (e.clientX - r.left) / (PX * S.zoom), y: (e.clientY - r.top) / (PX * S.zoom) }; };
const snap = (v) => { const pg = S.doc.page, m = pg.margin || 0; for (const s of [0, m, pg.w / 2, pg.w - m, pg.w, pg.h / 2, pg.h - m, pg.h]) if (Math.abs(v - s) < 0.06) return s; return Math.round(v * 100) / 100; };

let drag = null;
$("#page").addEventListener("pointerdown", (e) => {
  if (S.preview || S.mode !== "layout") return;
  const at = toIn(e), hEl = e.target.closest(".handle"), fEl = e.target.closest(".fr");
  if (S.editing && fEl && fEl.dataset.id === S.editing) return;          // typing in it
  if (S.editing) finishEdit();
  if (S.tool !== "select") { drag = { kind: "draw", from: at, tool: S.tool }; $("#page").setPointerCapture(e.pointerId); return; }
  if (hEl) { const f = frameOf(S.doc, S.sel[0])[1]; drag = { kind: "resize", h: hEl.dataset.h, start: at, orig: { ...f }, before: clone(S.doc) }; }
  else if (fEl) {
    const id = fEl.dataset.id;
    if (e.shiftKey) S.sel = S.sel.includes(id) ? S.sel.filter((x) => x !== id) : [...S.sel, id];
    else if (!S.sel.includes(id)) S.sel = [id];
    drag = { kind: "move", start: at, orig: S.sel.map((i) => ({ ...frameOf(S.doc, i)[1] })), before: clone(S.doc), moved: false };
  } else { S.sel = []; drag = null; }
  $("#page").setPointerCapture(e.pointerId); draw();
});
$("#page").addEventListener("pointermove", (e) => {
  if (!drag) return;
  const at = toIn(e);
  if (drag.kind === "move") {
    const dx = at.x - drag.start.x, dy = at.y - drag.start.y;
    if (Math.abs(dx) + Math.abs(dy) > 0.01) drag.moved = true;
    drag.orig.forEach((o) => { const f = frameOf(S.doc, o.id)[1]; f.x = snap(o.x + dx); f.y = snap(o.y + dy); });
    draw();
  } else if (drag.kind === "resize") {
    const o = drag.orig, f = frameOf(S.doc, o.id)[1], h = drag.h, dx = at.x - drag.start.x, dy = at.y - drag.start.y;
    let { x, y, w, h: hh } = o;
    if (h.includes("e")) w = o.w + dx; if (h.includes("s")) hh = o.h + dy;
    if (h.includes("w")) { x = o.x + dx; w = o.w - dx; } if (h.includes("n")) { y = o.y + dy; hh = o.h - dy; }
    if (e.shiftKey && (h.length === 2)) { const r = o.w / o.h; if (w / hh > r) w = hh * r; else hh = w / r; if (h.includes("w")) x = o.x + o.w - w; if (h.includes("n")) y = o.y + o.h - hh; }
    Object.assign(f, { x: snap(x), y: snap(y), w: Math.max(0.1, snap(w)), h: Math.max(0.1, snap(hh)) }); draw();
  } else if (drag.kind === "draw") {
    let rb = $(".rubber", $("#page")); if (!rb) { rb = document.createElement("div"); rb.className = "rubber"; $("#page").appendChild(rb); }
    const x = Math.min(at.x, drag.from.x), y = Math.min(at.y, drag.from.y), z = PX * S.zoom;
    rb.style.cssText = `left:${x * z}px;top:${y * z}px;width:${Math.abs(at.x - drag.from.x) * z}px;height:${Math.abs(at.y - drag.from.y) * z}px`;
  }
});
$("#page").addEventListener("pointerup", (e) => {
  if (!drag) return;
  const d = drag; drag = null;
  if (d.kind === "move" && d.moved) commit(d.before, "move");
  else if (d.kind === "resize") commit(d.before, "resize");
  else if (d.kind === "draw") {
    const at = toIn(e);
    let x = Math.min(at.x, d.from.x), y = Math.min(at.y, d.from.y), w = Math.abs(at.x - d.from.x), h = Math.abs(at.y - d.from.y);
    if (w < 0.15 || h < 0.15) { w = d.tool === "text" ? 3 : 2; h = d.tool === "text" ? 1 : 2; }
    const kind = d.tool === "text" ? "text" : d.tool === "image" ? "image" : "shape";
    const extra = d.tool === "ellipse" ? { shape: "ellipse" } : {};
    const r = op("add_frame", { page: cur().id, kind, x: snap(x), y: snap(y), w: snap(w), h: snap(h), ...extra }, "new frame");
    S.sel = [r.frame]; setTool("select");
    if (kind === "text") { S.editing = r.frame; }
    if (kind === "image") rtab("library");
    draw();
  }
});
$("#page").addEventListener("dblclick", (e) => {
  const fEl = e.target.closest(".fr.text"); if (!fEl || S.preview) return;
  S.sel = [fEl.dataset.id]; S.editing = fEl.dataset.id; S.editBefore = clone(S.doc); draw();
});
function finishEdit() {
  const id = S.editing; if (!id) return;
  const el = $(`.fr[data-id="${id}"]`, $("#page")); S.editing = null;
  if (el) { const before = S.editBefore || clone(S.doc); const f = frameOf(S.doc, id)[1]; const text = el.innerText.replace(/ /g, " ").replace(/\n{3,}/g, "\n\n"); if (text !== f.text) { f.text = text; commit(before, "edit text"); return; } }
  draw();
}
document.addEventListener("pointerdown", (e) => { if (S.editing && !e.target.closest(".fr.editing") && !e.target.closest(".right")) finishEdit(); }, true);

function setTool(t) { S.tool = t; $$("#tools button").forEach((b) => b.classList.toggle("on", b.dataset.tool === t)); $("#page").style.cursor = t === "select" ? "default" : "crosshair"; }
$$("#tools button").forEach((b) => (b.onclick = () => setTool(b.dataset.tool)));

// ------------------------------------------------------------------ the right-hand panels
function rtab(name) { $$("#rtabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === name)); $$("#layout-mode .rtab").forEach((t) => t.classList.toggle("on", t.id === "tab-" + name)); if (name === "library") library(); if (name === "styles") styles(); }
$$("#rtabs button").forEach((b) => (b.onclick = () => rtab(b.dataset.tab)));

function field(label, value, onset, attrs = "") {
  if (typeof value === "number") value = Math.round(value * 1000) / 1000;
  const l = document.createElement("label"); l.innerHTML = `${label} <input ${attrs} value="${esc(value)}">`;
  const i = $("input", l); i.onchange = () => onset(i.type === "number" ? Number(i.value) : i.value); return l;
}
function props() {
  const box = $("#tab-props"); if (!$("#tab-props").classList.contains("on")) return;
  if (S.editing) return;
  box.innerHTML = "";
  if (!S.sel.length) {
    const pg = S.doc.page, p = cur();
    box.insertAdjacentHTML("beforeend", `<h4>Page ${S.page + 1}</h4>`);
    box.appendChild(field("Name", p.name || "", (v) => { const b = clone(S.doc); p.name = v; commit(b, "rename page"); }));
    box.insertAdjacentHTML("beforeend", `<h4>The book</h4>`);
    box.appendChild(field("Title", S.doc.title, (v) => { const b = clone(S.doc); S.doc.title = v; commit(b, "title"); }));
    const g = document.createElement("div"); g.className = "grid4";
    for (const [k, l] of [["w", "W in"], ["h", "H in"], ["margin", "Margin"]]) g.appendChild(field(l, pg[k] ?? 0, (v) => op("set_page_size", { [k]: v }, "page size"), 'type="number" step="0.05"'));
    g.appendChild(field("Paper", pg.paper || "#ffffff", (v) => op("set_page_size", { paper: v }, "paper"), 'type="color"'));
    box.appendChild(g);
    box.insertAdjacentHTML("beforeend", `<p class="empty">Select a frame to change it. Double-click text to type. Shift-drag a corner keeps the shape.</p>`);
    return;
  }
  const f = frameOf(S.doc, S.sel[0])[1];
  const upd = (k) => (v) => op("update_frame", { frame: f.id, [k]: v }, k);
  box.insertAdjacentHTML("beforeend", `<h4>${f.kind} frame${S.sel.length > 1 ? ` (+${S.sel.length - 1} more)` : ""}</h4>`);
  const g = document.createElement("div"); g.className = "grid4";
  for (const k of ["x", "y", "w", "h"]) g.appendChild(field(k.toUpperCase() + " in", f[k], upd(k), 'type="number" step="0.05"'));
  box.appendChild(g);
  const g2 = document.createElement("div"); g2.className = "grid2";
  g2.appendChild(field("Rotate °", f.rot || 0, upd("rot"), 'type="number" step="1"'));
  g2.appendChild(field("Opacity", f.opacity ?? 1, upd("opacity"), 'type="number" step="0.05" min="0" max="1"'));
  box.appendChild(g2);
  if (f.kind === "text") {
    const l = document.createElement("label"); l.innerHTML = `Style <select>${Object.keys(S.doc.styles).map((s) => `<option ${s === f.style ? "selected" : ""}>${esc(s)}</option>`).join("")}</select>`;
    $("select", l).onchange = (e) => upd("style")(e.target.value); box.appendChild(l);
    const t = document.createElement("label"); t.innerHTML = `Text <textarea rows="8">${esc(f.text)}</textarea><small class="muted">A blank line starts a paragraph. **bold**, *italic*, numbers as {{tokens}}.</small>`;
    $("textarea", t).onchange = (e) => upd("text")(e.target.value); box.appendChild(t);
  } else if (f.kind === "image") {
    box.appendChild(field("Picture", f.src || "", upd("src")));
    const l = document.createElement("label"); l.innerHTML = `Fit <select>${["cover", "contain", "fill"].map((s) => `<option ${s === f.fit ? "selected" : ""}>${s}</option>`).join("")}</select>`;
    $("select", l).onchange = (e) => upd("fit")(e.target.value); box.appendChild(l);
    box.appendChild(field("Focus (x% y%)", f.focus || "50% 50%", upd("focus")));
    const b = document.createElement("button"); b.textContent = "Choose from the library"; b.onclick = () => rtab("library"); box.appendChild(b);
  } else {
    const g3 = document.createElement("div"); g3.className = "grid2";
    g3.appendChild(field("Fill", f.fill || "", upd("fill")));
    g3.appendChild(field("Stroke", f.stroke || "", upd("stroke")));
    g3.appendChild(field("Stroke pt", f.strokeW || 0, upd("strokeW"), 'type="number" step="0.5"'));
    const l = document.createElement("label"); l.innerHTML = `Shape <select><option ${f.shape !== "ellipse" ? "selected" : ""}>rect</option><option ${f.shape === "ellipse" ? "selected" : ""}>ellipse</option></select>`;
    $("select", l).onchange = (e) => upd("shape")(e.target.value); g3.appendChild(l);
    box.appendChild(g3);
  }
  const row = document.createElement("div"); row.className = "row";
  for (const [t, to] of [["To front", "front"], ["Forward", "forward"], ["Backward", "backward"], ["To back", "back"]]) { const b = document.createElement("button"); b.textContent = t; b.onclick = () => op("arrange", { frame: f.id, to }, "arrange"); row.appendChild(b); }
  const del = document.createElement("button"); del.textContent = "Delete"; del.onclick = () => deleteSel(); row.appendChild(del);
  box.appendChild(row);
}
function deleteSel() { if (!S.sel.length) return; const b = clone(S.doc); for (const id of S.sel) OPS.delete_frame(S.doc, { frame: id }); S.sel = []; commit(b, "delete"); }

function styles() {
  const box = $("#tab-styles"); box.innerHTML = "<h4>Text styles</h4>";
  for (const [name, st] of Object.entries(S.doc.styles)) {
    const d = document.createElement("details"); d.innerHTML = `<summary style="${styleCss({ ...st, size: Math.min(st.size, 16), colour: st.colour })};background:#f4efe4;padding:2px 6px;cursor:pointer">${esc(name)}</summary>`;
    const g = document.createElement("div"); g.className = "grid2";
    const set = (k, num) => (v) => op("set_style", { name, [k]: num ? Number(v) : v }, "style " + name);
    g.appendChild(field("Font", st.font, set("font")));
    g.appendChild(field("Size pt", st.size, set("size", 1), 'type="number" step="0.5"'));
    g.appendChild(field("Leading", st.leading, set("leading", 1), 'type="number" step="0.05"'));
    g.appendChild(field("Colour", st.colour, set("colour"), 'type="color"'));
    g.appendChild(field("Weight", st.weight, set("weight", 1), 'type="number" step="100"'));
    const al = document.createElement("label"); al.innerHTML = `Align <select>${["left", "center", "right", "justify"].map((a) => `<option ${a === st.align ? "selected" : ""}>${a}</option>`).join("")}</select>`;
    $("select", al).onchange = (e) => set("align")(e.target.value); g.appendChild(al);
    const it = document.createElement("label"); it.innerHTML = `Italic <input type="checkbox" ${st.italic ? "checked" : ""}>`; $("input", it).onchange = (e) => op("set_style", { name, italic: e.target.checked }, "style"); g.appendChild(it);
    d.appendChild(g); box.appendChild(d);
  }
  const add = document.createElement("button"); add.textContent = "+ New style"; add.onclick = () => { const n = prompt("Name the style"); if (n) op("set_style", { name: n }, "new style"); styles(); }; box.appendChild(add);
}

// ------------------------------------------------------------------ the library and illustrating
async function library() {
  try { S.lib = await api("/api/studio/library?text=" + encodeURIComponent($("#libsearch").value || "")); } catch (e) { toast(e.message); return; }
  const g = $("#libgrid"); g.innerHTML = "";
  for (const e of S.lib) {
    const it = document.createElement("div"); it.className = "libitem"; it.title = `${e.name}\n${e.prompt || e.note || ""}\n(${e.origin}, ${e.category})`;
    it.innerHTML = `<img src="/file/${esc(e.file)}" loading="lazy"><span>${esc(e.name)}</span>${e.origin && e.origin !== "author" ? `<b class="org">${esc(e.origin)}</b>` : ""}`;
    it.onclick = () => place(e);
    g.appendChild(it);
  }
}
$("#libsearch").oninput = () => { clearTimeout(library.t); library.t = setTimeout(library, 200); };
function place(e) {
  if (S.mode !== "layout") return;
  const f = S.sel.length === 1 ? frameOf(S.doc, S.sel[0])[1] : null;
  if (f && f.kind === "image") { op("update_frame", { frame: f.id, src: e.file }, "place picture"); toast(`Placed ${e.name}`); return; }
  const pg = S.doc.page, w = pg.w * 0.5, h = w;
  const r = op("add_frame", { page: cur().id, kind: "image", x: (pg.w - w) / 2, y: (pg.h - h) / 2, w, h, src: e.file, fit: "contain" }, "place picture");
  S.sel = [r.frame]; draw(); toast(`Placed ${e.name} in a new frame`);
}
$("#ill-size").onclick = () => { if (S.sel.length !== 1) return toast("Select a frame first"); const f = frameOf(S.doc, S.sel[0])[1]; $("#ill-w").value = f.w.toFixed(2); $("#ill-h").value = f.h.toFixed(2); };
const illArgs = () => ({ name: $("#ill-name").value.trim() || "illustration", description: $("#ill-desc").value.trim(), w: Number($("#ill-w").value) || 1, h: Number($("#ill-h").value) || 1, book: S.doc?.title || "" });
$("#ill-deepseek").onclick = async () => {
  const a = illArgs(); if (!a.description) return toast("Say what it shows");
  const b = $("#ill-deepseek"); b.disabled = true; b.textContent = "DeepSeek is drawing...";
  try { const r = await api("/api/studio/illustrate", { body: a }); $("#ill-out").innerHTML = `<p>Filed <b>${esc(r.name)}</b> (v${r.version}). Click it below to place it.</p>`; $("#libsearch").value = r.name; await library(); }
  catch (e) { $("#ill-out").innerHTML = `<p style="color:#ff8a7a">${esc(e.message)}</p>`; }
  b.disabled = false; b.textContent = "DeepSeek: draw it";
};
$("#ill-claude").onclick = async () => {
  const a = illArgs(); if (!a.description) return toast("Say what it shows");
  const r = await api("/api/studio/claude-prompt", { body: a });
  $("#ill-out").innerHTML = `<p>Paste this into Claude Code in this project. When Claude has filed it, search the library for <b>${esc(a.name)}</b>.</p><div class="promptbox">${esc(r.prompt)}</div><button id="copyp">Copy it</button>`;
  $("#copyp").onclick = () => { navigator.clipboard.writeText(r.prompt); toast("Copied"); };
};
$("#ill-paste").onclick = async () => {
  const a = illArgs(); const svg = $("#ill-svg").value; if (!svg.includes("<svg")) return toast("Paste an <svg>...</svg>");
  try { const r = await api("/api/studio/library/svg", { body: { name: a.name, svg, origin: "owner", prompt: a.description || null } }); toast(`Filed ${r.name}`); $("#libsearch").value = r.name; library(); } catch (e) { toast(e.message); }
};
$("#ill-file").onchange = async (e) => {
  const file = e.target.files[0]; if (!file) return;
  const data = await new Promise((res) => { const fr = new FileReader(); fr.onload = () => res(String(fr.result).split(",")[1]); fr.readAsDataURL(file); });
  const name = $("#ill-name").value.trim() || file.name.replace(/\.[^.]+$/, "");
  try { const r = await api("/api/studio/library/upload", { body: { name, data, ext: file.name.split(".").pop(), origin: "owner" } }); toast(`Filed ${r.name}`); $("#libsearch").value = r.name; library(); } catch (er) { toast(er.message); }
  e.target.value = "";
};

// ------------------------------------------------------------------ the agent
function chatLine(box, who, text, calls) {
  const m = document.createElement("div"); m.className = "msg " + who; m.textContent = text;
  if (calls?.length) { const c = document.createElement("div"); c.className = "calls"; c.textContent = calls.map((x) => (x.ok ? "✓ " : "✗ ") + x.name + (x.error ? `: ${x.error}` : "")).join("\n"); m.appendChild(c); }
  box.appendChild(m); box.scrollTop = box.scrollHeight;
}
$("#ask").onsubmit = async (e) => {
  e.preventDefault();
  const text = $("#instr").value.trim(); if (!text || !S.doc) return;
  chatLine($("#chat"), "you", text); $("#instr").value = ""; $("#agent-state").textContent = "thinking...";
  try {
    const r = await api("/api/studio/agent", { body: { instruction: text, doc: S.doc, page: S.page + 1, selected: S.sel, history: S.chat } });
    S.chat.push({ role: "user", content: text }, { role: "assistant", content: r.reply });
    if (r.changed && r.doc) { const before = clone(S.doc); S.doc = r.doc; S.page = Math.min(S.page, S.doc.pages.length - 1); S.sel = S.sel.filter((id) => { try { frameOf(S.doc, id); return true; } catch { return false; } }); commit(before, "the agent's changes"); }
    chatLine($("#chat"), "agent", r.reply + (r.changed ? "\n\n(Undo takes it all back in one step. Nothing is saved until you Save.)" : ""), r.calls);
    if (r.drawn?.length) library();
  } catch (er) { chatLine($("#chat"), "agent", "Error: " + er.message); }
  $("#agent-state").textContent = "";
};

// ------------------------------------------------------------------ books, saving, exporting
async function loadBooks() {
  S.books = await api("/api/studio/books");
  const sel = $("#book"); sel.innerHTML = "";
  const add = (label, items) => { const g = document.createElement("optgroup"); g.label = label; items.forEach((o) => g.appendChild(o)); if (items.length) sel.appendChild(g); };
  const opt = (v, t) => { const o = document.createElement("option"); o.value = v; o.textContent = t; return o; };
  add("Layout books (edit every page)", S.books.layouts.map((b) => opt("layout:" + b.slug, `${b.title} (${b.pages} pages)`)));
  add("Make a layout from", S.books.importable.map((b) => opt("import:" + b.slug, `${b.title}: lay it out`)));
  add("Manuscript books (chapters, build, PDF)", S.books.manuscripts.map((b) => opt("ms:" + b.key, `${b.title} (${b.by})`)));
  sel.appendChild(opt("new:", "+ A new layout book..."));
}
$("#book").onchange = async (e) => {
  const v = e.target.value;
  if (S.dirty && !confirm("Leave without saving?")) { e.target.value = S.current; return; }
  const [kind, id] = v.split(":");
  if (kind === "import") { const r = await api("/api/studio/layout", { body: { import: id } }); await loadBooks(); return open("layout:" + r.slug); }
  if (kind === "new") {
    const title = prompt("Title of the new book"); if (!title) { e.target.value = S.current; return; }
    const size = prompt("Trim size in inches, width x height", "8.5 x 11") || "8.5 x 11"; const [w, h] = size.split(/x/i).map(Number);
    const r = await api("/api/studio/layout", { body: { title, w: w || 8.5, h: h || 11, pages: 2 } }); await loadBooks(); return open("layout:" + r.slug);
  }
  open(v);
};
async function open(v) {
  S.current = v; $("#book").value = v; localStorage.setItem("studio.book", v);
  const [kind, id] = v.split(":");
  $("#layout-mode").hidden = kind !== "layout"; $("#ms-mode").hidden = kind !== "ms";
  $$(".tools button, #zin, #zout, #zfit, #undo, #redo, #preview, #export").forEach((b) => (b.disabled = kind !== "layout"));
  if (kind === "layout") {
    S.mode = "layout"; S.slug = id; S.doc = await api("/api/studio/layout/" + id); S.page = 0; S.sel = []; S.undo = []; S.redo = []; S.chat = [];
    $("#chat").innerHTML = ""; chatLine($("#chat"), "agent", `I can change anything in "${S.doc.title}": text, pictures, styles, pages. I can draw new illustrations too. Tell me what you want.`);
    dirty(false); fit(); draw(); if ($("#tab-library").classList.contains("on")) library();
  } else { S.mode = "ms"; await openMs(id); }
}
$("#save").onclick = async () => {
  if (S.mode === "layout") { finishEdit(); try { await api("/api/studio/layout/" + S.slug, { method: "PUT", body: S.doc }); dirty(false); toast("Saved (the previous copy is kept)"); } catch (e) { toast(e.message, 5000); } }
};
$("#export").onclick = async () => {
  finishEdit(); const b = $("#export"); b.disabled = true; b.textContent = "Printing...";
  try { const r = await api(`/api/studio/layout/${S.slug}/export`, { body: { doc: S.doc } }); toast("Printed: " + r.path, 6000); } catch (e) { toast(e.message, 6000); }
  b.disabled = false; b.textContent = "PDF";
};

// ------------------------------------------------------------------ zoom, keys
function fit() { const bd = $("#board").getBoundingClientRect(), pg = S.doc.page; S.zoom = Math.max(0.1, Math.min((bd.width - 120) / (pg.w * PX), (bd.height - 120) / (pg.h * PX))); }
$("#zin").onclick = () => { S.zoom = Math.min(8, S.zoom * 1.25); draw(); };
$("#zout").onclick = () => { S.zoom = Math.max(0.1, S.zoom / 1.25); draw(); };
$("#zfit").onclick = () => { fit(); draw(); };
$("#undo").onclick = () => { if (!S.undo.length) return; S.redo.push(clone(S.doc)); S.doc = S.undo.pop(); S.page = Math.min(S.page, S.doc.pages.length - 1); S.sel = []; dirty(true, "undo"); draw(); };
$("#redo").onclick = () => { if (!S.redo.length) return; S.undo.push(clone(S.doc)); S.doc = S.redo.pop(); S.sel = []; dirty(true, "redo"); draw(); };
$("#preview").onchange = (e) => { S.preview = e.target.checked; S.sel = []; draw(); };
$("#addpage").onclick = () => { const r = op("add_page", { after: S.page + 1 }, "add page"); S.page = r.number - 1; draw(); };
$("#duppage").onclick = () => { const r = op("add_page", { after: S.page + 1, copy_of: cur().id }, "duplicate page"); S.page = r.number - 1; draw(); };
$("#delpage").onclick = () => { if (S.doc.pages.length < 2 || !confirm(`Delete page ${S.page + 1}?`)) return; op("delete_page", { page: cur().id }, "delete page"); S.page = Math.max(0, S.page - 1); draw(); };
document.addEventListener("keydown", (e) => {
  const typing = e.target.closest("input, textarea, select, [contenteditable]");
  const mod = e.ctrlKey || e.metaKey;
  if (mod && e.key.toLowerCase() === "s") { e.preventDefault(); S.mode === "ms" ? $("#ms-save").click() : $("#save").click(); return; }
  if (S.mode !== "layout") return;
  if (S.editing && e.key === "Escape") { finishEdit(); return; }
  if (typing) return;
  if (mod && e.key.toLowerCase() === "z") { e.preventDefault(); (e.shiftKey ? $("#redo") : $("#undo")).click(); return; }
  if (mod && (e.key === "=" || e.key === "+")) { e.preventDefault(); $("#zin").click(); return; }
  if (mod && e.key === "-") { e.preventDefault(); $("#zout").click(); return; }
  if (mod && e.key === "0") { e.preventDefault(); $("#zfit").click(); return; }
  if (mod && e.key.toLowerCase() === "d" && S.sel.length) { e.preventDefault(); const b = clone(S.doc); const ids = []; for (const id of S.sel) { const f = frameOf(S.doc, id)[1]; const c = { ...clone(f), id: uid("f"), x: f.x + 0.2, y: f.y + 0.2 }; cur().frames.push(c); ids.push(c.id); } S.sel = ids; commit(b, "duplicate"); return; }
  if (e.key === "Delete" || e.key === "Backspace") { deleteSel(); return; }
  if (e.key.startsWith("Arrow") && S.sel.length) {
    e.preventDefault(); const b = clone(S.doc), step = e.shiftKey ? 0.25 : 0.02;
    for (const id of S.sel) { const f = frameOf(S.doc, id)[1]; if (e.key === "ArrowLeft") f.x -= step; if (e.key === "ArrowRight") f.x += step; if (e.key === "ArrowUp") f.y -= step; if (e.key === "ArrowDown") f.y += step; }
    commit(b, "nudge"); return;
  }
  if (e.key === "PageDown") { S.page = Math.min(S.doc.pages.length - 1, S.page + 1); S.sel = []; draw(); return; }
  if (e.key === "PageUp") { S.page = Math.max(0, S.page - 1); S.sel = []; draw(); return; }
  const k = e.key.toLowerCase(); const t = { v: "select", t: "text", f: "image", m: "rect", l: "ellipse" }[k]; if (t && !mod) setTool(t);
  if (e.key === "Escape") { S.sel = []; draw(); }
});
window.addEventListener("beforeunload", (e) => { if (S.dirty || S.ms.dirty) { e.preventDefault(); e.returnValue = ""; } });
window.addEventListener("resize", () => { if (S.mode === "layout") draw(); });

// ------------------------------------------------------------------ manuscript books
async function openMs(key) {
  S.ms = { ...S.ms, key, path: null, dirty: false, chat: [] };
  const r = await api("/api/studio/chapters?book=" + key);
  S.ms.all = r.chapters; S.ms.pdf = r.latest; S.ms.n = 1;
  const b = S.books.manuscripts.find((x) => x.key === key);
  $("#bd-cmd").textContent = `${b.title} is built by ${b.engine}: ${b.build}`;
  $("#ms-count").textContent = `${r.chapters.length}`;
  $("#ms-title").textContent = r.chapters.length ? "Pick a chapter" : "This book's words are not Markdown chapters: read and build it here.";
  $("#ms-text").value = ""; $("#ms-text").disabled = true; $("#ms-save").disabled = true;
  $("#mschat").innerHTML = ""; $("#proposals").innerHTML = "";
  chatLine($("#mschat"), "agent", `I can read ${b.title}'s chapters and propose exact replacements. You apply each one.`);
  chapters(); reader(); dirty(false); $("#status").textContent = "";
}
function chapters() {
  const box = $("#chapters"); box.innerHTML = ""; const q = ($("#ms-filter").value || "").toLowerCase();
  for (const c of S.ms.all.filter((c) => !q || (c.title + c.path).toLowerCase().includes(q))) {
    const d = document.createElement("div"); d.className = "ch" + (c.path === S.ms.path ? " on" : ""); d.innerHTML = `${esc(c.title)}<small>${esc(c.path.split("/").slice(-2).join("/"))} · ${c.words} words</small>`;
    d.onclick = () => openChapter(c.path); box.appendChild(d);
  }
}
$("#ms-filter").oninput = chapters;
async function openChapter(path) {
  if (S.ms.dirty && !confirm("Leave this chapter without saving?")) return;
  const r = await api(`/api/studio/chapter?book=${S.ms.key}&path=${encodeURIComponent(path)}`);
  S.ms.path = path; S.ms.text = r.text; S.ms.dirty = false;
  $("#ms-text").value = r.text; $("#ms-text").disabled = false; $("#ms-save").disabled = true;
  $("#ms-title").textContent = path; chapters(); renderMd();
}
$("#ms-text").oninput = () => { S.ms.dirty = $("#ms-text").value !== S.ms.text; $("#ms-save").disabled = !S.ms.dirty; if (!$("#ms-rendered").hidden) renderMd(); };
$("#ms-save").onclick = async () => {
  try { const r = await api("/api/studio/chapter", { method: "PUT", body: { book: S.ms.key, path: S.ms.path, text: $("#ms-text").value } }); S.ms.text = $("#ms-text").value; S.ms.dirty = false; $("#ms-save").disabled = true; toast(r.saved ? "Saved (the previous copy is kept). Build to see it in the PDF." : "No change"); } catch (e) { toast(e.message); }
};
$("#ms-preview").onchange = (e) => { $("#ms-rendered").hidden = !e.target.checked; $("#ms-text").hidden = e.target.checked; renderMd(); };
function renderMd() {
  if ($("#ms-rendered").hidden) return;
  const md = $("#ms-text").value;
  $("#ms-rendered").innerHTML = md.split(/\n\s*\n/).map((b) => {
    const h = b.match(/^(#{1,6})\s+(.*)/); if (h) return `<h${h[1].length}>${inline(h[2])}</h${h[1].length}>`;
    if (/^\s*[-*] /.test(b)) return "<ul>" + b.split("\n").map((l) => `<li>${inline(l.replace(/^\s*[-*] /, ""))}</li>`).join("") + "</ul>";
    return `<p>${b.split("\n").map(inline).join("<br>")}</p>`;
  }).join("");
}
async function reader() {
  const img = $("#rd-img"), none = $("#rd-none");
  if (!S.ms.pdf) { img.hidden = true; none.textContent = "No printed copy in the library yet: build one."; $("#rd-n").textContent = ""; return; }
  if (!S.ms.pages) { try { S.ms.pages = (await api("/api/pdf/info?path=" + encodeURIComponent(S.ms.pdf))).pages; } catch { S.ms.pages = 0; } }
  img.hidden = false; none.textContent = S.ms.pdf;
  img.src = `/api/pdf/page?path=${encodeURIComponent(S.ms.pdf)}&n=${S.ms.n}&dpi=110`;
  $("#rd-n").textContent = `page ${S.ms.n} of ${S.ms.pages}`;
}
$("#rd-prev").onclick = () => { S.ms.n = Math.max(1, S.ms.n - 1); reader(); };
$("#rd-next").onclick = () => { S.ms.n = Math.min(S.ms.pages || 1, S.ms.n + 1); reader(); };
$$("#mstabs button").forEach((b) => (b.onclick = () => { $$("#mstabs button").forEach((x) => x.classList.toggle("on", x === b)); $$("#ms-mode .rtab").forEach((t) => t.classList.toggle("on", t.id === "tab-" + b.dataset.tab)); }));
$("#bd-run").onclick = async () => {
  try { await api("/api/studio/build", { body: { book: S.ms.key } }); } catch (e) { return toast(e.message); }
  $("#bd-run").disabled = true;
  const poll = async () => {
    const j = await api("/api/studio/build?book=" + S.ms.key);
    $("#bd-log").textContent = `${j.state}${j.code != null ? ` (exit ${j.code})` : ""}\n\n${j.log || ""}`; $("#bd-log").scrollTop = 1e9;
    if (j.state === "running") return setTimeout(poll, 1500);
    $("#bd-run").disabled = false;
    if (j.state === "done") { const r = await api("/api/studio/chapters?book=" + S.ms.key); S.ms.pdf = r.latest; S.ms.pages = 0; S.ms.n = 1; reader(); toast("Built: " + (r.latest || "")); }
  };
  poll();
};
$("#msask").onsubmit = async (e) => {
  e.preventDefault(); const text = $("#msinstr").value.trim(); if (!text) return;
  chatLine($("#mschat"), "you", text); $("#msinstr").value = ""; $("#msagent-state").textContent = "thinking...";
  try {
    const r = await api("/api/studio/agent", { body: { instruction: (S.ms.path ? `(The owner has ${S.ms.path} open.) ` : "") + text, book: S.ms.key, history: S.ms.chat } });
    S.ms.chat.push({ role: "user", content: text }, { role: "assistant", content: r.reply });
    chatLine($("#mschat"), "agent", r.reply, r.calls);
    for (const p of r.proposals || []) proposal(p);
  } catch (er) { chatLine($("#mschat"), "agent", "Error: " + er.message); }
  $("#msagent-state").textContent = "";
};
function proposal(p) {
  const d = document.createElement("div"); d.className = "prop";
  d.innerHTML = `<b>${esc(p.path)}</b>${p.why ? `<span class="muted">${esc(p.why)}</span>` : ""}<pre>- ${esc(p.find)}</pre><pre>+ ${esc(p.replace)}</pre><div class="row"><button class="primary">Apply</button><button>Dismiss</button></div>`;
  const [ap, ds] = $$("button", d);
  ap.onclick = async () => {
    if (S.ms.dirty && S.ms.path === p.path) return toast("Save or discard your own edits to this chapter first");
    try { const r = await api("/api/studio/chapter/replace", { body: { book: S.ms.key, path: p.path, find: p.find, replace: p.replace } }); toast(`Applied (${r.replaced}). The previous copy is kept.`); d.remove(); if (S.ms.path === p.path) openChapter(p.path); } catch (e) { toast(e.message); }
  };
  ds.onclick = () => d.remove();
  $("#proposals").appendChild(d);
}

// ------------------------------------------------------------------ start
(async () => {
  await loadBooks();
  const last = localStorage.getItem("studio.book");
  const first = S.books.layouts[0] ? "layout:" + S.books.layouts[0].slug : S.books.importable[0] ? null : "ms:" + S.books.manuscripts[0].key;
  if (last && [...$("#book").options].some((o) => o.value === last)) open(last);
  else if (first) open(first);
  else {
    // first time: lay out the first book that can be (the kids book), then open it
    const slug = S.books.importable[0].slug;
    $("#status").textContent = "laying out " + S.books.importable[0].title + "...";
    try { await api("/api/studio/layout", { body: { import: slug } }); } catch (e) { if (!/already/.test(e.message)) toast(e.message, 6000); }
    await loadBooks(); open("layout:" + slug);
  }
})().catch((e) => toast("The studio could not start: " + e.message, 8000));
