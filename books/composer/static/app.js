// The Book Composer's page. Plain JavaScript; it talks to books/composer/server.py.
"use strict";

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const h = (tag, attrs = {}, ...kids) => {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") el.className = v;
    else if (k === "style") el.style.cssText = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (v !== false && v != null) el.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat()) if (kid != null) el.append(kid instanceof Node ? kid : document.createTextNode(kid));
  return el;
};
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const api = async (method, url, body) => {
  const r = await fetch(url, { method, headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body) });
  const data = r.headers.get("content-type")?.includes("json") ? await r.json() : await r.text();
  if (!r.ok) throw new Error(data.error || r.statusText);
  return data;
};
const toast = (msg) => { const t = $("#toast"); t.textContent = msg; t.classList.add("show");
  clearTimeout(toast.t); toast.t = setTimeout(() => t.classList.remove("show"), 2600); };
const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* private window */ } } };

// ---------------------------------------------------------------------------
// State

const S = { shelf: null, slug: null, loom: null, dirty: false, sel: null, frame: null, path: null,
  assets: [], pdf: null, pdfPage: 1, pdfPages: 0, linkFrom: null, linkMode: false };
const key = (lv, th) => `${lv}/${th}`;
const level = (k) => S.loom.levels.find((l) => l.key === k);
const thread = (k) => S.loom.threads.find((t) => t.key === k);
const cellOf = (k) => S.loom.cells[k];
const slugify = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "x";

function touch() { S.dirty = true; $("#save").disabled = false; $("#save").textContent = "Save*"; }
async function save() {
  if (!S.slug || !S.dirty) return;
  try { await api("PUT", `/api/loom/${S.slug}`, S.loom); S.dirty = false;
    $("#save").textContent = "Saved"; $("#save").disabled = true; toast("Saved. The previous copy is kept in .history/");
  } catch (e) { toast("Not saved: " + e.message); }
}
setInterval(() => { if (S.dirty) save(); }, 90000);
addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && e.key === "s") { e.preventDefault(); save(); } });
addEventListener("beforeunload", (e) => { if (S.dirty) { e.preventDefault(); e.returnValue = ""; } });

// ---------------------------------------------------------------------------
// Tabs

function show(tab) {
  $$("#tabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === tab));
  $$(".tab").forEach((t) => t.classList.toggle("on", t.id === "tab-" + tab));
  store.set("composer.tab", tab);
  if (tab !== "shelf" && tab !== "reader" && !S.loom) { toast("Open or start a book on the Shelf first"); return show("shelf"); }
  ({ shelf: drawShelf, weave: drawWeave, graph: drawGraph, pages: drawPage, paths: drawPaths,
     reader: drawReader, print: drawPrint })[tab]?.();
}
$$("#tabs button").forEach((b) => b.addEventListener("click", () => show(b.dataset.tab)));
$("#save").addEventListener("click", save);

// ---------------------------------------------------------------------------
// Shelf

async function drawShelf() {
  S.shelf = await api("GET", "/api/shelf");
  const kinds = $("#kinds"); kinds.innerHTML = "";
  for (const [k, label] of Object.entries(S.shelf.templates)) kinds.append(h("option", { value: k }, label));
  const looms = $("#looms"); looms.innerHTML = "";
  if (!S.shelf.looms.length) looms.append(h("p", { class: "empty" }, "None yet. Start one below, or open the Master Edition as a loom."));
  for (const l of S.shelf.looms) {
    looms.append(h("div", { class: "card" },
      h("div", { class: "t" }, l.title), h("div", { class: "m" }, `${l.kind} - ${l.done} of ${l.cells} chapters done`),
      h("div", { class: "row" }, h("button", { class: "primary", onclick: () => openLoom(l.slug) }, "Open"))));
  }
  const shelf = $("#shelf"); shelf.innerHTML = "";
  for (const b of S.shelf.books) {
    shelf.append(h("div", { class: "card" },
      h("div", { class: "t" }, b.title),
      h("div", { class: "m" }, `by ${b.by} - ${b.status}`),
      b.note ? h("div", { class: "m" }, b.note) : null,
      h("div", { class: "m" }, "Words: ", h("code", {}, b.words), "  Build: ", h("code", {}, b.build)),
      h("div", { class: "row" }, b.latest
        ? h("button", { onclick: () => { openPdf(b.latest); show("reader"); } }, "Read the newest copy")
        : h("span", { class: "m" }, "No printed copy in the library yet"))));
  }
}

$("#newbook").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = Object.fromEntries(new FormData(e.target));
  try { const r = await api("POST", "/api/loom", f); toast("Book created"); await openLoom(r.slug); }
  catch (err) { toast(err.message); }
});
$("#import-master").addEventListener("click", async () => {
  try { const r = await api("POST", "/api/loom", { title: "The 40 Hour Cabin: Master Edition (loom)",
      slug: "master-edition-loom", import: "master-edition" });
    toast("Imported: six levels, twelve threads, seventy-two chapters"); await openLoom(r.slug);
  } catch (err) { if (/already exists/.test(err.message)) await openLoom("master-edition-loom"); else toast(err.message); }
});

async function openLoom(slug) {
  if (S.dirty && !confirm("The open book has unsaved changes. Leave them?")) return;
  S.loom = await api("GET", `/api/loom/${slug}`); S.slug = slug; S.dirty = false; S.sel = null; S.path = null;
  S.loom.links ||= []; S.loom.paths ||= []; S.loom.notes ||= [];
  $("#bookname").textContent = S.loom.title; $("#save").disabled = true; $("#save").textContent = "Save";
  store.set("composer.slug", slug);
  show("weave");
}

// ---------------------------------------------------------------------------
// Weave: the grid and the chapter editor

function drawGrid(target, { small = false, onCell, mark } = {}) {
  const L = S.loom; const tbl = h("table", { class: "weave" });
  tbl.append(h("tr", {}, h("th"), ...L.threads.map((t) => h("th", { title: t.idea || "Rename this thread",
    onclick: small ? null : () => editThread(t.key) }, h("span", { class: "sw", style: `background:${t.color}` }), t.name))));
  L.levels.forEach((lv, i) => {
    const row = h("tr", {}, h("th", { class: "lv", title: lv.promise || "", onclick: small ? null : () => editLevel(lv.key) },
      `${i + 1}. ${lv.name}`));
    for (const t of L.threads) {
      const k = key(lv.key, t.key); const c = L.cells[k];
      if (!c) { row.append(h("td", {}, h("div", { class: "cell dim", onclick: () => { L.cells[k] = blank(); touch(); drawWeave(); } }, "+"))); continue; }
      const m = mark?.(k);
      row.append(h("td", {}, h("div", { class: "cell" + (S.sel === k ? " sel" : "") + (m === false ? " dim" : ""),
        style: `--c:${t.color}`, onclick: () => onCell(k) },
        h("span", { class: "st " + (c.status || "empty") }), m ? h("span", { class: "ord" }, m) : null,
        h("div", { class: "ct" }, c.title || "(untitled)"), small ? null : h("div", { class: "cd" }, c.deck || ""))));
    }
    tbl.append(row);
    if (!small && lv.gate && (lv.gate.done_when || lv.gate.title) && i < L.levels.length - 1)
      tbl.append(h("tr", {}, h("td"), h("td", { colspan: L.threads.length, class: "gate" },
        `Gate to level ${i + 2}: ${lv.gate.title || ""} ${lv.gate.done_when ? "- " + lv.gate.done_when : ""}`)));
  });
  target.innerHTML = ""; target.append(tbl);
}
const blank = () => ({ title: "", deck: "", body: "", frames: [], status: "empty", source: "" });

function drawWeave() { drawGrid($("#grid"), { onCell: (k) => { S.sel = k; drawWeave(); } }); drawEditor(); }

function drawEditor() {
  const ed = $("#editor"); ed.innerHTML = "";
  if (!S.sel) { ed.append(h("p", { class: "empty" }, "Pick a square to write it.")); return; }
  const k = S.sel; const c = cellOf(k); const [lk, tk] = k.split("/");
  const field = (label, prop, el) => { el.value = c[prop] ?? ""; el.addEventListener("input", () => { c[prop] = el.value; touch(); if (prop === "body") preview(); if (prop !== "body") drawGridOnly(); }); return h("label", {}, label, el); };
  const prev = h("div", { class: "editor-preview" });
  const preview = () => { prev.innerHTML = md(c.body || ""); };
  const status = h("select", {}, ...["empty", "draft", "review", "done"].map((s) => h("option", { value: s }, s)));
  ed.append(
    h("div", { class: "chips-row" }, h("span", { class: "chip", style: `background:${thread(tk).color}` }, thread(tk).name),
      h("span", { class: "chip", style: "background:#444" }, level(lk).name)),
    field("Title", "title", h("input")), field("Deck (one line under the title)", "deck", h("input")),
    field("Status", "status", status),
    field("Text (Markdown: **bold**, *italic*, # heading, - list; numbers as {{tokens}})", "body", h("textarea", { rows: 12 })),
    h("h3", {}, "How it will read"), prev,
    c.source ? h("p", { class: "hint" }, "Imported from ", h("code", {}, c.source)) : null,
    h("div", { class: "row" }, h("button", { onclick: () => show("pages") }, `Place pictures (${(c.frames || []).length})`),
      h("button", { onclick: () => { S.linkFrom = k; show("graph"); toast("Now click the chapter it links to"); S.linkMode = true; $("#link-mode").classList.add("on"); } }, "Link to...")),
    h("h3", {}, "Links from here"), linksList(k), h("h3", {}, "Notes"), notesFor(k));
  preview();
}
function drawGridOnly() { drawGrid($("#grid"), { onCell: (k) => { S.sel = k; drawWeave(); } }); }

function linksList(k) {
  const ul = h("ul", { class: "links" });
  const all = S.loom.links.filter((l) => l.from === k || l.to === k);
  if (!all.length) ul.append(h("li", { class: "hint" }, "None yet."));
  for (const l of all) {
    const other = l.from === k ? l.to : l.from; const dir = l.from === k ? "->" : "<-";
    ul.append(h("li", {}, `${dir} ${l.kind}: ${cellOf(other)?.title || other} `,
      h("button", { onclick: () => { S.loom.links.splice(S.loom.links.indexOf(l), 1); touch(); drawEditor(); } }, "remove")));
  }
  return ul;
}
function notesFor(target) {
  const box = h("div");
  for (const n of S.loom.notes.filter((n) => n.target === target))
    box.append(h("div", { class: "note" }, n.text, h("small", {}, n.at)));
  const ta = h("textarea", { rows: 2, placeholder: "A note to yourself or a reviewer" });
  box.append(ta, h("button", { onclick: () => { if (!ta.value.trim()) return;
    S.loom.notes.push({ target, text: ta.value.trim(), at: new Date().toISOString().slice(0, 16).replace("T", " ") });
    touch(); drawEditor(); } }, "Add note"));
  return box;
}

function editThread(tk) {
  const t = thread(tk); const ed = $("#editor"); ed.innerHTML = ""; S.sel = null; drawGridOnly();
  const name = h("input", { value: t.name }); const idea = h("input", { value: t.idea || "" });
  const color = h("input", { type: "color", value: t.color });
  ed.append(h("h2", {}, "Thread"), h("label", {}, "Name", name), h("label", {}, "The idea, in one line", idea),
    h("label", {}, "Colour", color),
    h("div", { class: "row" }, h("button", { class: "primary", onclick: () => { t.name = name.value; t.idea = idea.value; t.color = color.value; touch(); drawWeave(); } }, "Apply"),
      h("button", { onclick: () => moveThread(tk, -1) }, "Move left"), h("button", { onclick: () => moveThread(tk, 1) }, "Move right"),
      h("button", { onclick: () => removeThread(tk) }, "Remove thread")));
}
function editLevel(lk) {
  const lv = level(lk); lv.gate ||= { title: "", done_when: "", key: "" };
  const ed = $("#editor"); ed.innerHTML = ""; S.sel = null; drawGridOnly();
  const f = {}; for (const p of ["name", "verb", "promise", "who", "time", "need"]) f[p] = h("input", { value: lv[p] || "" });
  const g = { title: h("input", { value: lv.gate.title || "" }), done_when: h("textarea", { rows: 3 }), key: h("input", { value: lv.gate.key || "" }) };
  g.done_when.value = lv.gate.done_when || "";
  ed.append(h("h2", {}, "Level"),
    h("label", {}, "Name", f.name), h("label", {}, "Verb (what a reader does here)", f.verb),
    h("label", {}, "Promise", f.promise), h("label", {}, "Who it is for", f.who), h("label", {}, "How long", f.time),
    h("label", {}, "What you need", f.need),
    h("h3", {}, "The gate to the next level"),
    h("p", { class: "hint" }, "What a reader can do before going on. In print it becomes a page with a space for a stamp or an answer; on screen, a lock."),
    h("label", {}, "Gate title", g.title), h("label", {}, "Done when...", g.done_when),
    h("label", {}, "Key (an answer that opens the next level; blank for a stamp)", g.key),
    lv.milestones?.length ? h("div", {}, h("h3", {}, "Milestones"), h("ul", { class: "milestones" },
      lv.milestones.map((m) => h("li", {}, h("b", {}, m.title), " - ", m.done_when)))) : null,
    h("div", { class: "row" }, h("button", { class: "primary", onclick: () => {
      for (const p in f) lv[p] = f[p].value; for (const p in g) lv.gate[p] = g[p].value; touch(); drawWeave(); } }, "Apply"),
      h("button", { onclick: () => moveLevel(lk, -1) }, "Move up"), h("button", { onclick: () => moveLevel(lk, 1) }, "Move down"),
      h("button", { onclick: () => removeLevel(lk) }, "Remove level")));
}
function move(arr, i, d) { const j = i + d; if (j < 0 || j >= arr.length) return; [arr[i], arr[j]] = [arr[j], arr[i]]; }
function moveThread(tk, d) { move(S.loom.threads, S.loom.threads.findIndex((t) => t.key === tk), d); touch(); drawWeave(); }
function moveLevel(lk, d) { move(S.loom.levels, S.loom.levels.findIndex((l) => l.key === lk), d); touch(); drawWeave(); }
function dropCells(test) {
  for (const k of Object.keys(S.loom.cells)) if (test(k)) delete S.loom.cells[k];
  S.loom.links = S.loom.links.filter((l) => l.from in S.loom.cells && l.to in S.loom.cells);
  for (const p of S.loom.paths) p.stops = p.stops.filter((s) => s in S.loom.cells);
}
function removeThread(tk) {
  const written = Object.entries(S.loom.cells).filter(([k, c]) => k.endsWith("/" + tk) && (c.body || "").trim()).length;
  if (!confirm(`Remove this thread${written ? ` and the ${written} chapter(s) written in it` : ""}? (The last saved copy keeps them.)`)) return;
  S.loom.threads = S.loom.threads.filter((t) => t.key !== tk); dropCells((k) => k.endsWith("/" + tk)); touch(); drawWeave();
}
function removeLevel(lk) {
  if (!confirm("Remove this level and its chapters? (The last saved copy keeps them.)")) return;
  S.loom.levels = S.loom.levels.filter((l) => l.key !== lk); dropCells((k) => k.startsWith(lk + "/")); touch(); drawWeave();
}
const PALETTE = ["#b0601e", "#2f5d7c", "#5b7f3a", "#8a4f9e", "#c2410c", "#0f766e", "#a16207", "#be185d"];
$("#add-thread").addEventListener("click", () => {
  const name = prompt("The new thread's name (an idea, a character, a subject):"); if (!name) return;
  let k = slugify(name); while (thread(k)) k += "-2";
  S.loom.threads.push({ key: k, name, idea: "", color: PALETTE[S.loom.threads.length % PALETTE.length] });
  for (const lv of S.loom.levels) S.loom.cells[key(lv.key, k)] = blank(); touch(); drawWeave();
});
$("#add-level").addEventListener("click", () => {
  const name = prompt("The new level's name (a depth: Story, Theory, Template, Steps, Family...):"); if (!name) return;
  let k = slugify(name); while (level(k)) k += "-2";
  S.loom.levels.push({ key: k, name, verb: "", promise: "", who: "", time: "", need: "", gate: { title: "", done_when: "", key: "" } });
  for (const t of S.loom.threads) S.loom.cells[key(k, t.key)] = blank(); touch(); drawWeave();
});

// A small Markdown for the editor's preview (the printed book uses the real one).
function md(text) {
  // Lines inside one paragraph are joined, as Markdown does; a blank line ends a paragraph.
  const joined = esc(text).replace(/\{\{([^}]+)\}\}/g, '<span class="chip" style="background:#888">$1</span>')
    .replace(/([^\n])\n(?!\n|\s*[-*] |#|\s*\d+\. )/g, "$1 ");
  const lines = joined.split(/\n/);
  let out = "", list = false;
  for (let l of lines) {
    l = l.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/\*(.+?)\*/g, "<i>$1</i>");
    if (/^\s*[-*] /.test(l)) { if (!list) { out += "<ul>"; list = true; } out += `<li>${l.replace(/^\s*[-*] /, "")}</li>`; continue; }
    if (list) { out += "</ul>"; list = false; }
    const m = l.match(/^(#{1,4}) (.*)/);
    out += m ? `<h${m[1].length + 2}>${m[2]}</h${m[1].length + 2}>` : l.trim() ? `<p>${l}</p>` : "";
  }
  return out + (list ? "</ul>" : "");
}

// ---------------------------------------------------------------------------
// Graph

const KIND_COLOR = { "builds-on": "#94a3b8", explains: "#2f5d7c", "practice-for": "#5b7f3a", contrasts: "#be185d", "see-also": "#b0601e" };
function graphLayout(spread) {
  const L = S.loom; const W = $("#graph").clientWidth || 1000; const H = $("#graph").clientHeight || 600;
  const pos = (L.layout ||= {}).graph ||= {};
  L.levels.forEach((lv, i) => L.threads.forEach((t, j) => {
    const k = key(lv.key, t.key); if (!(k in L.cells)) return;
    const x = 140 + (j + 0.5) * ((W - 160) / L.threads.length); const y = 40 + (i + 0.5) * ((H - 60) / L.levels.length);
    if (spread || !pos[k]) pos[k] = spread ? { x: x + (Math.random() - .5) * 60, y: y + (Math.random() - .5) * 40 } : { x, y };
  }));
  if (spread) relax(pos, 120);
}
function relax(pos, n) {
  const ks = Object.keys(pos); const links = S.loom.links;
  for (let it = 0; it < n; it++) {
    for (const a of ks) for (const b of ks) if (a < b) {
      const dx = pos[a].x - pos[b].x, dy = pos[a].y - pos[b].y; const d2 = dx * dx + dy * dy + 0.01;
      if (d2 < 3600) { const f = 40 / d2; pos[a].x += dx * f; pos[a].y += dy * f; pos[b].x -= dx * f; pos[b].y -= dy * f; }
    }
    for (const l of links) { const a = pos[l.from], b = pos[l.to]; if (!a || !b) continue;
      const dx = b.x - a.x, dy = b.y - a.y; a.x += dx * .01; a.y += dy * .01; b.x -= dx * .01; b.y -= dy * .01; }
  }
}
function drawGraph() {
  const L = S.loom; const svg = $("#graph"); graphLayout(false);
  const kinds = $("#link-kind"); if (!kinds.options.length) for (const k of S.shelf?.link_kinds || Object.keys(KIND_COLOR)) kinds.append(h("option", { value: k }, k));
  $("#legend").innerHTML = Object.entries(KIND_COLOR).map(([k, c]) => `<span><i style="background:${c}"></i>${k}</span>`).join("");
  const pos = L.layout.graph; const NS = "http://www.w3.org/2000/svg";
  const s = (tag, attrs) => { const el = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v); return el; };
  svg.innerHTML = "";
  const H = svg.clientHeight || 600;
  L.levels.forEach((lv, i) => { const t = s("text", { x: 8, y: 40 + (i + 0.5) * ((H - 60) / L.levels.length), class: "lvlab" }); t.textContent = lv.name; svg.append(t); });
  for (const l of L.links) { const a = pos[l.from], b = pos[l.to]; if (!a || !b) continue;
    const mx = (a.x + b.x) / 2 + (b.y - a.y) * .15, my = (a.y + b.y) / 2 - (b.x - a.x) * .15;
    svg.append(s("path", { d: `M${a.x},${a.y} Q${mx},${my} ${b.x},${b.y}`, fill: "none", stroke: KIND_COLOR[l.kind] || "#999", "stroke-width": 2, opacity: .8 })); }
  for (const [k, c] of Object.entries(L.cells)) {
    const p = pos[k]; if (!p) continue; const [, tk] = k.split("/");
    const g = s("g", { class: "node" + (S.sel === k || S.linkFrom === k ? " sel" : ""), transform: `translate(${p.x},${p.y})` });
    g.append(s("circle", { r: c.status === "done" ? 9 : 7, fill: thread(tk)?.color || "#888" }));
    const t = s("text", { x: 11, y: 4 }); t.textContent = (c.title || "").slice(0, 28); g.append(t);
    let drag = null;
    g.addEventListener("pointerdown", (e) => { drag = { x: e.clientX, y: e.clientY, moved: false }; g.setPointerCapture(e.pointerId); });
    g.addEventListener("pointermove", (e) => { if (!drag) return; const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      if (Math.abs(dx) + Math.abs(dy) > 3) drag.moved = true; p.x += dx; p.y += dy; drag.x = e.clientX; drag.y = e.clientY;
      g.setAttribute("transform", `translate(${p.x},${p.y})`); });
    g.addEventListener("pointerup", () => { const moved = drag?.moved; drag = null;
      if (moved) { touch(); drawGraph(); return; } nodeClick(k); });
    svg.append(g);
  }
}
function nodeClick(k) {
  if (S.linkMode) {
    if (!S.linkFrom) { S.linkFrom = k; toast("Now click the chapter it links to"); return drawGraph(); }
    if (S.linkFrom !== k) { S.loom.links.push({ from: S.linkFrom, to: k, kind: $("#link-kind").value, note: "" }); touch();
      toast(`Linked: ${$("#link-kind").value}`); }
    S.linkFrom = null; S.linkMode = false; $("#link-mode").classList.remove("on"); return drawGraph();
  }
  S.sel = k; show("weave");
}
$("#link-mode").addEventListener("click", () => { S.linkMode = !S.linkMode; S.linkFrom = null; $("#link-mode").classList.toggle("on", S.linkMode);
  if (S.linkMode) toast("Click the first chapter, then the one it links to"); drawGraph(); });
$("#graph-grid").addEventListener("click", () => { S.loom.layout = { graph: {} }; touch(); drawGraph(); });
$("#graph-spread").addEventListener("click", () => { graphLayout(true); touch(); drawGraph(); });

// ---------------------------------------------------------------------------
// Pages: placing pictures and text boxes on a chapter's page

async function drawPage() {
  if (!S.sel) { const first = Object.keys(S.loom.cells)[0]; S.sel = first; }
  const k = S.sel; const c = cellOf(k); c.frames ||= [];
  const [lk, tk] = k.split("/");
  $("#page-title").textContent = `Page: ${c.title || "(untitled)"}`;
  const size = (S.loom.page?.size || "8.5in 11in").split(/\s+/).map(parseFloat);
  $("#page").style.aspectRatio = `${size[0]} / ${size[1] || size[0]}`;
  $("#page-head").innerHTML = `<div class="chips-row"><span class="chip" style="background:${thread(tk).color}">${esc(thread(tk).name)}</span>
    <span class="chip" style="background:#444">${esc(level(lk).name)}</span></div><div class="t">${esc(c.title)}</div><div class="d">${esc(c.deck)}</div>`;
  $("#page-body").innerHTML = md(c.body || "");
  const stage = $("#stage"); stage.innerHTML = "";
  c.frames.forEach((f, i) => stage.append(frameEl(f, i)));
  drawFrameProps();
  if (!S.assets.length) S.assets = await api("GET", "/api/assets");
  drawAssets();
}
function frameEl(f, i) {
  const el = h("div", { class: "frame" + (f.type === "text" ? " text" : "") + (f.lineart || S.loom.kind === "coloring" ? " lineart" : "") + (S.frame === i ? " sel" : ""),
    style: `left:${f.x}%;top:${f.y}%;width:${f.w}%;height:${f.h}%` });
  if (f.type === "text") el.innerHTML = md(f.text || "Text"); else el.append(h("img", { src: assetUrl(f.asset), alt: f.caption || "" }));
  const grip = h("div", { class: "grip" }); el.append(grip);
  const stage = $("#stage");
  const drag = (resize) => (e) => {
    e.preventDefault(); e.stopPropagation(); S.frame = i; drawFrameProps();
    const r = stage.getBoundingClientRect(); const sx = e.clientX, sy = e.clientY; const o = { ...f };
    const mv = (ev) => { const dx = (ev.clientX - sx) / r.width * 100, dy = (ev.clientY - sy) / r.height * 100;
      if (resize) { f.w = Math.max(5, Math.min(100 - f.x, o.w + dx)); f.h = Math.max(5, Math.min(100 - f.y, o.h + dy)); }
      else { f.x = Math.max(0, Math.min(100 - f.w, o.x + dx)); f.y = Math.max(0, Math.min(100 - f.h, o.y + dy)); }
      el.style.cssText = `left:${f.x}%;top:${f.y}%;width:${f.w}%;height:${f.h}%`; };
    const up = () => { removeEventListener("pointermove", mv); removeEventListener("pointerup", up); touch(); $$(".frame").forEach((x, j) => x.classList.toggle("sel", j === i)); };
    addEventListener("pointermove", mv); addEventListener("pointerup", up);
  };
  el.addEventListener("pointerdown", drag(false)); grip.addEventListener("pointerdown", drag(true));
  return el;
}
const assetUrl = (a) => !a ? "" : a.includes("/") ? "/file/" + a : (S.assets.find((x) => x.name === a.split("@")[0]) ? "/file/" + S.assets.filter((x) => x.name === a.split("@")[0]).at(-1).file : "");
function drawFrameProps() {
  const box = $("#frame-props"); box.innerHTML = ""; const c = cellOf(S.sel); const f = c.frames[S.frame];
  if (!f) { box.append(h("p", { class: "hint" }, "Click a picture below to place it on this page.")); return; }
  const cap = h("input", { value: f.caption || "" }); const line = h("input", { type: "checkbox", style: "width:auto" }); line.checked = !!f.lineart;
  const text = h("textarea", { rows: 4 }); text.value = f.text || "";
  box.append(h("h3", {}, f.type === "text" ? "Text box" : "Picture"),
    f.type === "text" ? h("label", {}, "Text", text) : h("label", {}, "Caption", cap),
    f.type === "text" ? null : h("label", { class: "row" }, line, "Print as line art (for coloring)"),
    h("div", { class: "row" }, h("button", { class: "primary", onclick: () => { f.caption = cap.value; f.lineart = line.checked; f.text = text.value; touch(); drawPage(); } }, "Apply"),
      h("button", { onclick: () => { c.frames.splice(S.frame, 1); S.frame = null; touch(); drawPage(); } }, "Remove from page")));
}
function drawAssets() {
  const q = $("#asset-filter").value.toLowerCase(); const box = $("#assets"); box.innerHTML = "";
  const latest = {}; for (const a of S.assets) latest[a.name] = a;              // newest version of each
  const list = Object.values(latest).filter((a) => !q || (a.name + a.category + a.note).toLowerCase().includes(q)).slice(0, 90);
  for (const a of list) box.append(h("div", { class: "asset", title: `${a.name} (v${a.version}) ${a.note}`, onclick: () => {
    const c = cellOf(S.sel); c.frames.push({ type: "image", asset: a.file.replace(/^\/?/, ""), x: 10, y: 5, w: 45, h: 60, caption: "" });
    S.frame = c.frames.length - 1; touch(); drawPage(); } },
    a.file.match(/\.(png|jpe?g|webp|gif|svg)$/i) ? h("img", { src: "/file/" + a.file, loading: "lazy" }) : h("div", {}, "PDF"),
    h("span", {}, a.name)));
}
$("#asset-filter").addEventListener("input", drawAssets);
$("#add-text").addEventListener("click", () => { const c = cellOf(S.sel); c.frames.push({ type: "text", text: "A few words", x: 55, y: 5, w: 40, h: 25 });
  S.frame = c.frames.length - 1; touch(); drawPage(); });

// ---------------------------------------------------------------------------
// Paths

function drawPaths() {
  const L = S.loom; const list = $("#path-list"); list.innerHTML = "";
  for (const p of L.paths) list.append(h("button", { class: S.path === p.key ? "on" : "", onclick: () => { S.path = p.key; drawPaths(); } }, p.title || p.key));
  const p = L.paths.find((x) => x.key === S.path);
  drawGrid($("#path-grid"), { small: true, mark: p ? (k) => { const i = p.stops.indexOf(k); return i >= 0 ? i + 1 : null; } : null,
    onCell: (k) => { if (!p) return toast("Pick or make a path first"); const i = p.stops.indexOf(k);
      if (i >= 0) p.stops.splice(i, 1); else p.stops.push(k); touch(); drawPaths(); } });
  const d = $("#path-detail"); d.innerHTML = "";
  if (!p) { d.append(h("p", { class: "empty" }, "Pick or make a path.")); return; }
  const title = h("input", { value: p.title || "" }); const who = h("input", { value: p.who || "" });
  title.addEventListener("input", () => { p.title = title.value; touch(); }); who.addEventListener("input", () => { p.who = who.value; touch(); });
  d.append(h("label", {}, "Name", title), h("label", {}, "For whom", who), h("h3", {}, `Stops (${p.stops.length})`),
    h("ol", {}, p.stops.map((s, i) => h("li", {}, `${cellOf(s)?.title || s} `,
      h("button", { onclick: () => { move(p.stops, i, -1); touch(); drawPaths(); } }, "up"),
      h("button", { onclick: () => { p.stops.splice(i, 1); touch(); drawPaths(); } }, "x")))),
    p.outside_stops?.length ? h("p", { class: "hint" }, `Also visits pages outside the weave: ${p.outside_stops.join(", ")}`) : null,
    h("button", { onclick: () => { if (confirm("Delete this path?")) { L.paths = L.paths.filter((x) => x !== p); S.path = null; touch(); drawPaths(); } } }, "Delete path"));
}
$("#add-path").addEventListener("click", () => { const t = prompt("Name the path (who is it for?):"); if (!t) return;
  let k = slugify(t); while (S.loom.paths.some((p) => p.key === k)) k += "-2";
  S.loom.paths.push({ key: k, title: t, who: "", stops: [] }); S.path = k; touch(); drawPaths(); });

// ---------------------------------------------------------------------------
// Reader

let PDFS = [];
async function drawReader() {
  if (!PDFS.length) PDFS = await api("GET", "/api/pdfs");
  const q = $("#pdf-filter").value.toLowerCase(); const box = $("#pdfs"); box.innerHTML = "";
  for (const p of PDFS.filter((p) => !q || p.path.toLowerCase().includes(q)).slice(0, 200))
    box.append(h("button", { class: S.pdf === p.path ? "on" : "", onclick: () => openPdf(p.path) }, p.name, h("small", {}, `${p.day} ${p.item}`)));
  if (!S.pdf) { const last = store.get("composer.pdf"); if (last) openPdf(last); }
}
$("#pdf-filter").addEventListener("input", drawReader);
async function openPdf(path) {
  try { const info = await api("GET", "/api/pdf/info?path=" + encodeURIComponent(path));
    S.pdf = path; S.pdfPages = info.pages; S.pdfPage = 1; store.set("composer.pdf", path);
    $("#pdf-title").textContent = path.split("/").at(-1); pdfPage(); }
  catch (e) { toast(e.message); }
}
async function pdfPage() {
  $("#pdf-img").src = `/api/pdf/page?path=${encodeURIComponent(S.pdf)}&n=${S.pdfPage}&dpi=110`;
  $("#pdf-pos").textContent = `${S.pdfPage} / ${S.pdfPages}`;
  const notes = await api("GET", "/api/pdf/notes?path=" + encodeURIComponent(S.pdf));
  const box = $("#pdf-notes"); box.innerHTML = "";
  for (const n of notes.filter((n) => n.page === S.pdfPage)) box.append(h("div", { class: "note" }, n.text, h("small", {}, n.at)));
  if (!box.children.length) box.append(h("p", { class: "hint" }, "No notes on this page."));
  S.pdfNotes = notes;
}
$("#pdf-prev").addEventListener("click", () => { if (S.pdf && S.pdfPage > 1) { S.pdfPage--; pdfPage(); } });
$("#pdf-next").addEventListener("click", () => { if (S.pdf && S.pdfPage < S.pdfPages) { S.pdfPage++; pdfPage(); } });
$("#pdf-zoom").addEventListener("click", () => $("#pdf-img").classList.toggle("zoom"));
$("#pdf-add-note").addEventListener("click", async () => { const t = $("#pdf-note").value.trim(); if (!S.pdf || !t) return;
  S.pdfNotes.push({ page: S.pdfPage, text: t, at: new Date().toISOString().slice(0, 16).replace("T", " ") });
  await api("POST", "/api/pdf/notes", { path: S.pdf, notes: S.pdfNotes }); $("#pdf-note").value = ""; pdfPage(); });
$("#pdf-place").addEventListener("click", async () => {
  if (!S.pdf) return toast("Open a PDF first"); if (!S.loom) return toast("Open a book on the Shelf first");
  if (!S.sel) return toast("Pick a chapter in the Weave first");
  const r = await api("POST", "/api/pdf/place", { path: S.pdf, n: S.pdfPage, slug: S.slug });
  cellOf(S.sel).frames.push({ type: "image", asset: r.asset, x: 5, y: 5, w: 60, h: 90, caption: "" }); touch();
  toast("Placed on the page of: " + (cellOf(S.sel).title || S.sel));
});

// ---------------------------------------------------------------------------
// Print

function drawPrint() {
  const o = $("#order"); o.innerHTML = "";
  o.append(h("option", { value: "by-level" }, "Down each level (all stories, then all theory...)"),
    h("option", { value: "by-thread" }, "Up each thread (one idea from story to activity, then the next)"),
    ...S.loom.paths.map((p) => h("option", { value: p.key }, `Path: ${p.title}`)));
}
$("#preview").addEventListener("click", async () => { if (S.dirty) await save();
  $("#preview-frame").src = `/api/loom/${S.slug}/preview?order=${encodeURIComponent($("#order").value)}&t=${Date.now()}`; });
$("#export").addEventListener("click", async () => { if (S.dirty) await save();
  $("#export-result").textContent = "Printing..."; try {
    const r = await api("POST", `/api/loom/${S.slug}/export`, { order: $("#order").value });
    $("#export-result").textContent = "Printed: " + r.path; PDFS = [];
    $("#export-result").append(" ", h("button", { onclick: () => { openPdf(r.path); show("reader"); } }, "Open it"));
  } catch (e) { $("#export-result").textContent = "Not printed: " + e.message; } });

// ---------------------------------------------------------------------------

(async () => {
  await drawShelf();
  const last = store.get("composer.slug");
  if (last && S.shelf.looms.some((l) => l.slug === last)) await openLoom(last);
  const tab = store.get("composer.tab", "shelf"); show(S.loom || tab === "reader" ? tab : "shelf");
})();
