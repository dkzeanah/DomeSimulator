// The Proof Desk: a finished PDF, page by page -- read it, pin notes, fix the source, run KDP's checks, certify.
"use strict";
const $ = (s, el = document) => el.querySelector(s), $$ = (s, el = document) => [...el.querySelectorAll(s)];
const PT = 72;
const st = {
  book: null, build: null, builds: [], certs: [], pages: 0, n: 1, zoom: 1, fit: true, spread: false, tool: "hand",
  meta: {}, notes: [], pre: null, found: {}, changed: null, selNote: null, chapter: null, chapterText: "", history: [], job: null,
};
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const q = o => new URLSearchParams(o).toString();

async function api(path, opts = {}) {
  const r = await fetch("/api/studio/proof/" + path, opts.body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(opts.body) } : {});
  const ct = r.headers.get("content-type") || "";
  const data = ct.includes("json") ? await r.json() : await r.text();
  if (!r.ok) throw new Error(data.error || data || r.statusText);
  return data;
}
const ctx = () => ({ book: st.book, build: st.build });
function status(t, bad) { const s = $("#status"); s.textContent = t || ""; s.className = "status" + (bad ? " bad" : ""); }

// ---------------------------------------------------------------- books and builds
async function boot() {
  const books = await api("books");
  $("#book").innerHTML = books.map(b => `<option value="${b.key}">${esc(b.title)} (${b.builds} builds${b.status ? ", " + esc(b.status) : ""})</option>`).join("");
  const want = new URLSearchParams(location.search).get("book") || (books.find(b => b.key === "two-trees") || books[0]).key;
  $("#book").value = want;
  await openBook(want);
}

async function openBook(key) {
  st.book = key; st.history = []; $("#chat").innerHTML = ""; $("#proposals").innerHTML = "";
  const r = await api("builds?" + q({ book: key }));
  st.builds = r.builds; st.certs = r.certificates; st.job = r.job;
  $("#build").innerHTML = st.builds.map(b => `<option value="${b.build}">${b.build} -- ${b.made}${certFor(b) ? " -- certified" : ""}</option>`).join("")
    || `<option value="">no printed copy yet</option>`;
  $("#cmp").innerHTML = st.builds.map(b => `<option value="${b.build}">${b.build}</option>`).join("");
  const chs = await api("chapters?" + q({ book: key }));
  $("#chapter").innerHTML = chs.chapters.map(c => `<option value="${esc(c.path)}">${esc(c.title)} (${c.words} words)</option>`).join("");
  $("#buildcmd").textContent = chs.build || "";
  showJob(st.job);
  if (st.builds.length) await openBuild(new URLSearchParams(location.search).get("build") || st.builds[0].build);
}
const certFor = b => st.certs.find(c => c.build === b.build);

async function openBuild(build) {
  if (!st.builds.find(b => b.build === build)) build = st.builds[0].build;
  st.build = build; st.meta = {}; st.found = {}; st.changed = null; st.pre = null;
  $("#build").value = build;
  const i = st.builds.findIndex(b => b.build === build);
  if (st.builds[i + 1]) $("#cmp").value = st.builds[i + 1].build;
  history.replaceState(null, "", "?" + q({ book: st.book, build }));
  const first = await api("page?" + q({ ...ctx(), n: 1 }));
  st.pages = first.pages; st.meta[1] = first;
  $("#pno").max = st.pages; $("#pcount").textContent = "/ " + st.pages;
  $("#nreport").href = "/api/studio/proof/report?" + q(ctx());
  await loadNotes();
  thumbs();
  await go(Math.min(st.n, st.pages) || 1);
  preflight();
  if (st.builds[i + 1]) compare(st.builds[i + 1].build, true);
  renderCerts();
}

// ---------------------------------------------------------------- thumbnails
// thumbnails are drawn only as they scroll near the strip's view
function loadThumbs() {
  const L = $(".left"), top = L.scrollTop - 600, bottom = L.scrollTop + L.clientHeight + 600;
  for (const t of $$("#thumbs .thumb")) {
    if (t.hidden || t.offsetTop + t.offsetHeight < top || t.offsetTop > bottom) continue;
    const img = t.querySelector("img");
    if (!img.getAttribute("src")) img.src = "/api/studio/proof/page.png?" + q({ ...ctx(), n: t.dataset.n, scale: 0.22 });
  }
}
let thumbRaf = 0;
$(".left").addEventListener("scroll", () => { cancelAnimationFrame(thumbRaf); thumbRaf = requestAnimationFrame(loadThumbs); });
function thumbs() {
  const el = $("#thumbs"); el.innerHTML = "";
  const w = 118, h = 118 * (st.meta[1].h / st.meta[1].w);
  for (let n = 1; n <= st.pages; n++) {
    const t = document.createElement("div");
    t.className = "thumb"; t.dataset.n = n;
    t.innerHTML = `<div class="tp" style="height:${h}px"><img alt="" width="${w}" height="${h}"><div class="badges"></div></div>${n}`;
    t.onclick = () => go(n);
    el.appendChild(t);
  }
  badges();
}
function flagged() {
  const m = {};
  for (const c of st.pre?.checks || []) for (const p of c.pages) if (c.status !== "pass") (m[p] = m[p] || []).push(c.status);
  return m;
}
function badges() {
  const fl = flagged(), byPage = {};
  for (const x of st.notes) if (x.here && x.status === "open") byPage[x.here] = (byPage[x.here] || 0) + 1;
  const ch = new Set(st.changed?.changed || []);
  for (const t of $$("#thumbs .thumb")) {
    const n = +t.dataset.n, b = [];
    if (byPage[n]) b.push(`<span class="b n" title="open notes">${byPage[n]}</span>`);
    if (fl[n]) b.push(`<span class="b ${fl[n].includes("fail") ? "f" : "w"}" title="flagged by the preflight">!</span>`);
    if (ch.has(n)) b.push(`<span class="b c" title="changed since ${st.changed.a}">&#916;</span>`);
    if (st.found[n]) b.push(`<span class="b h" title="found">${st.found[n].length}</span>`);
    t.querySelector(".badges").innerHTML = b.join("");
    t.classList.toggle("on", visible().includes(n));
  }
  applyFilter();
}
function applyFilter() {
  const f = $("#filter").value, fl = flagged(), ch = new Set(st.changed?.changed || []);
  const notes = new Set(st.notes.filter(x => x.here).map(x => x.here));
  for (const t of $$("#thumbs .thumb")) {
    const n = +t.dataset.n;
    t.hidden = !(f === "all" || (f === "notes" && notes.has(n)) || (f === "flagged" && fl[n]) || (f === "changed" && ch.has(n)) || (f === "found" && st.found[n]));
  }  loadThumbs();
}

// ---------------------------------------------------------------- the page or spread
function visible() {
  if (!st.spread) return [st.n];
  // page 1 is a right-hand page on its own; then 2|3, 4|5, ...
  if (st.n === 1) return [1];
  const left = st.n % 2 === 0 ? st.n : st.n - 1;
  return [left, left + 1].filter(n => n <= st.pages);
}
async function meta(n) {
  if (!st.meta[n]) st.meta[n] = await api("page?" + q({ ...ctx(), n }));
  return st.meta[n];
}
function fitZoom() {
  const b = $("#board"), m = st.meta[1], cols = st.spread ? 2 : 1;
  return Math.max(0.2, Math.min((b.clientWidth - 90) / (m.w * cols), (b.clientHeight - 100) / m.h));
}
async function go(n) {
  n = Math.max(1, Math.min(st.pages, n | 0));
  st.n = n; $("#pno").value = n;
  const ns = visible();
  await Promise.all(ns.map(meta));
  if (st.fit) st.zoom = fitZoom();
  $("#zval").textContent = Math.round(st.zoom * 100) + "%";
  const sp = $("#spread"); sp.innerHTML = "";
  const scale = Math.min(4, st.zoom * (window.devicePixelRatio || 1));
  for (const p of ns) {
    const m = st.meta[p];
    const s = document.createElement("div");
    s.className = "sheet" + (p === n ? " on" : ""); s.dataset.n = p;
    s.style.width = m.w * st.zoom + "px"; s.style.height = m.h * st.zoom + "px";
    s.innerHTML = `<img alt="page ${p}" src="/api/studio/proof/page.png?${q({ ...ctx(), n: p, scale: scale.toFixed(2) })}">${overlay(m, p)}<div class="num">${p}${p % 2 ? " (right)" : " (left)"}</div>`;
    sp.appendChild(s);
  }
  wireSheets();
  for (const t of $$("#thumbs .thumb")) t.classList.toggle("on", ns.includes(+t.dataset.n));
  $(`#thumbs .thumb[data-n="${n}"]`)?.scrollIntoView({ block: "nearest" });
  loadThumbs();
  pageInfo(); renderNotes();
  if ($(".rtabs .on").dataset.tab === "source") openSourceFor(n);
}

function overlay(m, p) {
  const W = m.w, H = m.h, parts = [];
  if ($("#o-kdp").checked && st.pre) {
    const gi = (st.pre.need_gutter_in ?? 0) * PT, go = st.pre.need_outside_in * PT;
    const x0 = m.inside === "left" ? gi : go, x1 = W - (m.inside === "left" ? go : gi);
    parts.push(`<rect x="${x0}" y="${go}" width="${x1 - x0}" height="${H - 2 * go}" fill="none" stroke="#d85ad8" stroke-dasharray="6 4" stroke-width="1"><title>KDP's least margins: inside ${st.pre.need_gutter_in} in, outside ${st.pre.need_outside_in} in</title></rect>`);
    // the gutter side, shaded
    parts.push(m.inside === "left" ? `<rect x="0" y="0" width="${gi}" height="${H}" fill="#d85ad8" opacity=".07"/>` : `<rect x="${W - gi}" y="0" width="${gi}" height="${H}" fill="#d85ad8" opacity=".07"/>`);
  }
  if ($("#o-box").checked && m.box) {
    const [a, b, c, d] = m.box, bad = st.pre && tooTight(m);
    parts.push(`<rect x="${a}" y="${b}" width="${c - a}" height="${d - b}" fill="none" stroke="${bad ? "#e74c3c" : "#3a8ee8"}" stroke-width="${bad ? 2 : 1}"><title>Printed area: margins inside ${m.margins.inside}, outside ${m.margins.outside}, top ${m.margins.top}, bottom ${m.margins.bottom} in</title></rect>`);
    for (const im of m.images) if (im.cut) {
      const [x, y, x2, y2] = im.bbox;
      parts.push(`<rect x="${Math.max(0, x)}" y="${Math.max(0, y)}" width="${Math.min(W, x2) - Math.max(0, x)}" height="${Math.min(H, y2) - Math.max(0, y)}" fill="#e74c3c" opacity=".18"><title>This picture runs off the page: the rest of it is on the next or previous page</title></rect>`);
    }
  }
  for (const r of st.found[p] || []) parts.push(`<rect x="${r[0] - 1}" y="${r[1] - 1}" width="${r[2] - r[0] + 2}" height="${r[3] - r[1] + 2}" fill="#2ecc71" opacity=".35"/>`);
  if ($("#o-notes").checked) {
    let i = 0;
    for (const x of st.notes) {
      if (x.here !== p) continue;
      i++;
      const r = x.carried ? x.rect_here : x.rect, col = { fix: "#e74c3c", question: "#e8b45a", ok: "#2ecc71", note: "#3a8ee8" }[x.kind];
      const op = x.status === "resolved" ? .35 : 1, sel = st.selNote === x.id;
      if (r) parts.push(`<rect class="pin" data-id="${x.id}" x="${r[0]}" y="${r[1]}" width="${r[2] - r[0]}" height="${r[3] - r[1]}" fill="${col}" fill-opacity=".12" stroke="${col}" stroke-width="${sel ? 3 : 1.5}" opacity="${op}"><title>${esc(x.text)}</title></rect>`);
      const px = r ? r[2] : W - 18, py = r ? r[1] : 10 + i * 22;
      parts.push(`<g class="pin" data-id="${x.id}" opacity="${op}"><circle cx="${px}" cy="${py}" r="${sel ? 10 : 8}" fill="${col}"/><text x="${px}" y="${py + 3.5}" font-size="10" text-anchor="middle" fill="#fff" font-family="Segoe UI">${i}</text><title>${esc(x.text)}</title></g>`);
    }
  }
  parts.push(`<rect class="drag" fill="#3a8ee822" stroke="#3a8ee8" stroke-dasharray="4 3" width="0" height="0" display="none"/>`);
  return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">${parts.join("")}</svg>`;
}
function tooTight(m) {
  const g = st.pre.need_gutter_in ?? 0, o = st.pre.need_outside_in, e = 0.005;
  return m.margins.inside < g - e || (!st.pre.bleed && Math.min(m.margins.outside, m.margins.top, m.margins.bottom) < o - e);
}
function redraw() { go(st.n); }

// note-drawing on a sheet
function wireSheets() {
  for (const s of $$("#spread .sheet")) {
    const p = +s.dataset.n, svg = s.querySelector("svg"), rect = svg.querySelector(".drag");
    const at = e => { const b = s.getBoundingClientRect(); return [(e.clientX - b.left) / st.zoom, (e.clientY - b.top) / st.zoom]; };
    s.addEventListener("click", e => {
      const pin = e.target.closest(".pin");
      if (pin) { selectNote(pin.dataset.id); return; }
      if (st.tool === "hand" && p !== st.n) go(p);
    });
    s.addEventListener("pointerdown", e => {
      if (st.tool !== "note" || e.button !== 0 || e.target.closest(".pin")) return;
      e.preventDefault();
      const a = at(e);
      s.setPointerCapture(e.pointerId);
      const move = ev => {
        const b = at(ev), x = Math.min(a[0], b[0]), y = Math.min(a[1], b[1]);
        rect.setAttribute("display", ""); rect.setAttribute("x", x); rect.setAttribute("y", y);
        rect.setAttribute("width", Math.abs(b[0] - a[0])); rect.setAttribute("height", Math.abs(b[1] - a[1]));
      };
      const up = ev => {
        s.removeEventListener("pointermove", move); s.removeEventListener("pointerup", up);
        const b = at(ev);
        let r = [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[0], b[0]), Math.max(a[1], b[1])];
        if (r[2] - r[0] < 6 && r[3] - r[1] < 6) r = [a[0] - 40, a[1] - 10, a[0] + 40, a[1] + 10];   // a click: a small box round it
        notePop(p, r, ev);
      };
      s.addEventListener("pointermove", move); s.addEventListener("pointerup", up);
    });
  }
}

// ---------------------------------------------------------------- notes
let pending = null;
function notePop(p, r, ev) {
  pending = { page: p, rect: r.map(v => +v.toFixed(1)) };
  const m = st.meta[p];
  const under = m.words.filter(w => w[0] >= r[0] - 2 && w[2] <= r[2] + 2 && w[1] >= r[1] - 2 && w[3] <= r[3] + 2).map(w => w[4]).join(" ");
  pending.under = under;
  $("#np-under").textContent = under ? `"${under.slice(0, 160)}"` : "(no words under the box)";
  const pop = $("#notepop"), b = $("#board").getBoundingClientRect();
  pop.hidden = false;
  pop.style.left = Math.min(b.width - 340, Math.max(10, ev.clientX - b.left + $("#board").scrollLeft + 12)) + "px";
  pop.style.top = Math.max(10, ev.clientY - b.top + $("#board").scrollTop + 12) + "px";
  $("#np-text").value = ""; $("#np-text").focus();
}
function closePop() { $("#notepop").hidden = true; pending = null; $$(".drag").forEach(r => r.setAttribute("display", "none")); }
$("#np-cancel").onclick = closePop;
$("#np-save").onclick = async () => {
  if (!pending) return;
  const text = $("#np-text").value.trim();
  if (!text) { $("#np-text").focus(); return; }
  try {
    const x = await api("notes", { body: { ...ctx(), page: pending.page, rect: pending.rect, text, kind: $("#np-kind").value } });
    closePop(); await loadNotes(); st.selNote = x.id; redraw(); tab("notes");
  } catch (e) { status(e.message, true); }
};
$("#np-ask").onclick = () => {
  if (!pending) return;
  const p = pending; closePop();
  tab("agent");
  $("#ask").value = `On page ${p.page}, at the spot that reads "${p.under || "(no words)"}": ${$("#np-text").value || "what is wrong here? Propose a fix."}`;
  $("#ask").focus();
};
$("#np-text").addEventListener("keydown", e => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) $("#np-save").click(); if (e.key === "Escape") closePop(); });

async function loadNotes() {
  st.notes = await api("notes?" + q(ctx()));
  const open = st.notes.filter(x => x.status === "open").length;
  $("#ncount").textContent = open || ""; $("#ncount").className = "pill" + (st.notes.some(x => x.status === "open" && x.kind === "fix") ? " bad" : "");
  badges();
}
function renderNotes() {
  const show = $("#nshow").value;
  const list = st.notes.filter(x => show === "all" || (show === "open" ? x.status === "open" : x.here === st.n))
    .sort((a, b) => (a.here || 1e9) - (b.here || 1e9) || a.created.localeCompare(b.created));
  $("#notes").innerHTML = list.map(x => `
    <div class="note ${x.kind} ${x.status}${st.selNote === x.id ? " sel" : ""}" data-id="${x.id}">
      <div class="meta"><b>${x.kind}</b><a data-go="${x.here || ""}">${x.here ? "page " + x.here : "not found in this build"}</a>
        ${x.carried ? `<span title="pinned on ${x.build}, found again here by its words">from ${x.build.replace(/^\d+-/, "")}</span>` : ""}
        <span>${esc(x.author)}, ${x.created}</span><span class="grow"></span><span>${x.status}</span></div>
      <div>${esc(x.text)}</div>
      ${x.anchor ? `<div class="muted small">on "${esc(x.anchor.slice(0, 100))}"</div>` : ""}
      ${(x.replies || []).map(r => `<div class="reply"><b>${esc(r.by)}</b>, ${r.at}: ${esc(r.text)}</div>`).join("")}
      <div class="acts">
        ${x.status === "open" ? `<button data-act="resolve">Resolve</button>` : `<button data-act="reopen">Reopen</button>`}
        <button data-act="reply">Reply</button><button data-act="agent">Ask the agent</button><button data-act="source">Source</button><button data-act="delete" title="Delete this note">&#128465;</button>
      </div>
    </div>`).join("") || `<div class="empty">No notes ${show === "page" ? "on this page" : "yet"}.</div>`;
}
$("#nshow").onchange = renderNotes;
$("#notes").addEventListener("click", async e => {
  const el = e.target.closest(".note"); if (!el) return;
  const id = el.dataset.id, x = st.notes.find(y => y.id === id);
  const goTo = e.target.closest("[data-go]");
  if (goTo && goTo.dataset.go) { st.selNote = id; return go(+goTo.dataset.go); }
  const act = e.target.dataset.act;
  try {
    if (act === "resolve" || act === "reopen") await api("notes/" + id, { body: { book: st.book, status: act === "resolve" ? "resolved" : "open" } });
    else if (act === "reply") { const t = prompt("Reply"); if (!t) return; await api("notes/" + id, { body: { book: st.book, reply: t } }); }
    else if (act === "delete") { if (!confirm("Delete this note?")) return; await api(`notes/${id}/delete`, { body: { book: st.book } }); }
    else if (act === "agent") { tab("agent"); $("#ask").value = `Note on page ${x.here}: "${x.text}"${x.anchor ? ` (on the words "${x.anchor.slice(0, 120)}")` : ""}. Find the source and propose a fix.`; $("#ask").focus(); return; }
    else if (act === "source") { if (x.here) await go(x.here); tab("source"); return; }
    else { st.selNote = id; redraw(); return; }
    await loadNotes(); redraw();
  } catch (err) { status(err.message, true); }
});
function selectNote(id) {
  st.selNote = id; tab("notes");
  const x = st.notes.find(y => y.id === id);
  if (x && x.here !== st.n) $("#nshow").value = "all";
  redraw();
  setTimeout(() => $(`.note[data-id="${id}"]`)?.scrollIntoView({ block: "nearest" }), 50);
}

// ---------------------------------------------------------------- the page tab
function pageInfo() {
  const m = st.meta[st.n]; if (!m) return;
  const g = st.pre?.need_gutter_in, o = st.pre?.need_outside_in;
  const cls = (v, need) => need == null ? "" : v < need - 0.005 ? "bad" : "ok";
  const mg = m.margins;
  $("#pageinfo").innerHTML = `
    <div class="kv">
      <b>Page</b><span>${m.n} of ${m.pages}, a ${m.n % 2 ? "right" : "left"}-hand page (inside edge on the ${m.inside})</span>
      <b>Size</b><span>${(m.w / PT).toFixed(3)} x ${(m.h / PT).toFixed(3)} in</span>
      ${m.blank ? `<b>Printed</b><span>nothing: a blank page</span>` : `
      <b>Inside</b><span class="${cls(mg.inside, g)}">${mg.inside.toFixed(3)} in${g != null ? ` (KDP asks ${g})` : ""}</span>
      <b>Outside</b><span class="${cls(mg.outside, o)}">${mg.outside.toFixed(3)} in${o != null ? ` (KDP asks ${o})` : ""}</span>
      <b>Top</b><span class="${cls(mg.top, o)}">${mg.top.toFixed(3)} in</span>
      <b>Bottom</b><span class="${cls(mg.bottom, o)}">${mg.bottom.toFixed(3)} in</span>`}
      <b>Words</b><span>${m.words.length}</span>
      <b>Source</b><span>${m.source ? `<a href="#" id="tosrc">${esc(m.source.path.split("/").pop())}</a>, near line ${m.source.line} <span class="muted">(${m.source.matched} of ${m.source.of} lines matched)</span>` : `<span class="muted">not found in the chapters (a picture, a table or front matter)</span>`}</span>
    </div>
    <h4>Pictures</h4>
    ${m.images.length ? m.images.map(im => `<div class="small ${im.ppi && im.ppi < 300 ? "warnc" : ""}">${im.px[0]} x ${im.px[1]} px at ${((im.bbox[2] - im.bbox[0]) / PT).toFixed(2)} x ${((im.bbox[3] - im.bbox[1]) / PT).toFixed(2)} in = <b>${im.ppi} ppi</b>${im.ppi < 300 ? " (KDP wants 300)" : ""}${im.cut ? ` <span class="bad">runs off the page</span>` : ""}</div>`).join("") : `<div class="muted small">none</div>`}
    <h4>Words on the page</h4>
    <pre class="promptbox">${esc(m.text)}</pre>`;
  $("#tosrc")?.addEventListener("click", e => { e.preventDefault(); tab("source"); });
}

// ---------------------------------------------------------------- source
async function openSourceFor(n) {
  const m = await meta(n);
  if (!m.source) { $("#srcwhere").textContent = `Page ${n}'s words were not found in a chapter; pick one below.`; if (!st.chapter) await openChapter($("#chapter").value); return; }
  $("#srcwhere").textContent = `Page ${n}'s words come from ${m.source.path}, near line ${m.source.line}.`;
  if (dirty() && st.chapter !== m.source.path) { status("unsaved chapter: save or revert first"); return; }
  await openChapter(m.source.path, m.source.line);
}
const dirty = () => st.chapter && $("#srctext").value !== st.chapterText;
async function openChapter(path, line) {
  if (st.chapter !== path) {
    const r = await api("chapter?" + q({ book: st.book, path }));
    st.chapter = path; st.chapterText = r.text; $("#srctext").value = r.text; $("#chapter").value = path;
  }
  srcState();
  if (line) {
    const ta = $("#srctext"), lines = ta.value.split("\n");
    const at = lines.slice(0, line - 1).reduce((s, l) => s + l.length + 1, 0);
    ta.focus({ preventScroll: true }); ta.setSelectionRange(at, at + (lines[line - 1] || "").length);
    const lh = parseFloat(getComputedStyle(ta).lineHeight) || 18;
    // wrapped lines make this approximate; the selection marks the exact spot
    ta.scrollTop = Math.max(0, (at / Math.max(1, ta.value.length)) * ta.scrollHeight - 4 * lh);
  }
}
function srcState() { $("#srcstate").textContent = dirty() ? "unsaved changes" : st.chapter ? "saved" : ""; $("#srcsave").disabled = !dirty(); }
$("#srctext").addEventListener("input", srcState);
$("#chapter").onchange = () => { if (dirty() && !confirm("Drop the unsaved changes?")) { $("#chapter").value = st.chapter; return; } st.chapter = null; openChapter($("#chapter").value); };
$("#srcrevert").onclick = () => { $("#srctext").value = st.chapterText; srcState(); };
$("#srcsave").onclick = async () => {
  try {
    const r = await api("chapter", { body: { book: st.book, path: st.chapter, text: $("#srctext").value } });
    st.chapterText = $("#srctext").value; srcState();
    status(r.saved ? `saved ${st.chapter.split("/").pop()} (${r.words} words); rebuild to see it printed` : "nothing changed");
  } catch (e) { status(e.message, true); }
};
$("#rebuild").onclick = async () => {
  if (dirty() && !confirm("The chapter has unsaved changes. Rebuild without them?")) return;
  try { showJob(await api("rebuild", { body: { book: st.book } })); pollJob(); } catch (e) { status(e.message, true); }
};
function showJob(j) {
  st.job = j;
  if (!j) { $("#buildstate").textContent = ""; $("#buildlog").hidden = true; $("#rebuild").disabled = false; return; }
  $("#rebuild").disabled = j.state === "running";
  const secs = Math.round(((j.ended || Date.now() / 1000) - j.started));
  $("#buildstate").textContent = { running: `building... ${secs} s`, done: `built in ${secs} s`, failed: `failed (code ${j.code})` }[j.state];
  $("#buildlog").hidden = false; $("#buildlog").textContent = j.log.slice(-4000);
  $("#buildlog").scrollTop = 1e9;
}
async function pollJob() {
  const r = await api("builds?" + q({ book: st.book }));
  showJob(r.job);
  if (r.job?.state === "running") return setTimeout(pollJob, 2000);
  if (r.job?.state === "done") {
    st.builds = r.builds; st.certs = r.certificates;
    status("a new copy is in the library");
    await openBook(st.book);
  }
}

// ---------------------------------------------------------------- preflight
async function preflight() {
  $("#checks").innerHTML = `<div class="muted">Checking every page...</div>`;
  try {
    st.pre = await api("preflight?" + q({ ...ctx(), paper: $("#paper").value }));
  } catch (e) { $("#checks").innerHTML = `<div class="bad">${esc(e.message)}</div>`; return; }
  const p = st.pre;
  const v = p.fails ? "fail" : p.warns ? "warn" : "pass";
  const sum = `<div><b class="${v === "fail" ? "bad" : v === "warn" ? "warnc" : "ok"}">${p.fails ? `${p.fails} checks fail` : p.warns ? `passes, with ${p.warns} warnings` : "every check passes"}</b></div>
    <div class="small muted">${p.pages} pages, ${p.trim ? `${p.trim[0]} x ${p.trim[1]} in` : "no KDP trim"}${p.bleed ? " with bleed" : ""}, ${(p.bytes / 1e6).toFixed(1)} MB</div>`;
  $("#pfsum").className = "pfsum " + v; $("#pfsum").innerHTML = sum;
  $("#certsum").className = "pfsum " + v; $("#certsum").innerHTML = sum + p.checks.filter(c => c.status !== "pass").map(c => `<div class="small"><span class="${c.status === "fail" ? "bad" : "warnc"}">${c.status}</span> ${esc(c.title)}: ${esc(c.detail)}</div>`).join("");
  $("#pfcount").textContent = p.fails || p.warns || ""; $("#pfcount").className = "pill" + (p.fails ? " bad" : p.warns ? " warn" : "");
  $("#checks").innerHTML = p.checks.map(c => `
    <div class="check"><span class="st ${c.status}">${c.status.toUpperCase()}</span><div><b>${esc(c.title)}</b><div class="muted">${esc(c.detail)}</div>
      ${c.pages.length ? `<div class="pgs">${c.pages.slice(0, 60).map(n => `<button data-go="${n}">${n}</button>`).join("")}${c.count > 60 ? `<span class="muted">+${c.count - 60} more</span>` : ""}</div>` : ""}</div></div>`).join("");
  $("#cover").innerHTML = p.cover_in ? `<div class="kv">
      <b>Spine</b><span>${p.spine_in.toFixed(3)} in (${p.pages} pages x ${$("#paper").selectedOptions[0].text})</span>
      <b>Spine text</b><span>${p.spine_text ? "allowed" : "not allowed under " + 79 + " pages"}</span>
      <b>Full cover</b><span>${p.cover_in[0].toFixed(3)} x ${p.cover_in[1].toFixed(3)} in, bleed included</span>
      <b>At 300 ppi</b><span>${Math.ceil(p.cover_in[0] * 300)} x ${Math.ceil(p.cover_in[1] * 300)} px</span></div>` : "";
  const rules = await api("rules");
  $("#rules").innerHTML = `<div class="muted">${esc(rules.source)}</div><div class="kv">${rules.table.map(r => `<b>${esc(r.rule)}</b><span>${esc(r.value)}</span>`).join("")}</div>`;
  badges(); redraw();
}
$("#rerun").onclick = preflight; $("#paper").onchange = preflight;
$("#checks").addEventListener("click", e => { const b = e.target.closest("[data-go]"); if (b) go(+b.dataset.go); });

async function compare(other, quiet) {
  if (!other || other === st.build) { $("#cmpout").textContent = "pick another build"; return; }
  if (!quiet) $("#cmpout").textContent = "comparing...";
  try {
    st.changed = await api("changed?" + q({ book: st.book, a: other, b: st.build }));
    const c = st.changed;
    $("#cmpout").innerHTML = `${c.changed.length} of ${c.pages_b} pages differ from ${esc(c.a)} (${c.pages_a} pages). ` +
      (c.changed.length ? `Show them with the page filter "changed". <div class="pgs">${c.changed.slice(0, 80).map(n => `<button data-go="${n}">${n}</button>`).join("")}</div>` : "");
    badges();
  } catch (e) { $("#cmpout").textContent = e.message; }
}
$("#cmpgo").onclick = () => compare($("#cmp").value);
$("#cmpout").addEventListener("click", e => { const b = e.target.closest("[data-go]"); if (b) go(+b.dataset.go); });

// ---------------------------------------------------------------- find
let findT;
$("#find").addEventListener("input", () => { clearTimeout(findT); findT = setTimeout(find, 350); });
$("#find").addEventListener("keydown", e => {
  if (e.key !== "Enter") return;
  const ns = Object.keys(st.found).map(Number).sort((a, b) => a - b);
  if (!ns.length) return;
  go(e.shiftKey ? (ns.filter(n => n < st.n).pop() ?? ns[ns.length - 1]) : (ns.find(n => n > st.n) ?? ns[0]));
});
async function find() {
  const t = $("#find").value.trim();
  st.found = {};
  if (t.length >= 2) for (const r of await api("search?" + q({ ...ctx(), q: t }))) st.found[r.n] = r.hits;
  const ns = Object.keys(st.found).length;
  status(t.length >= 2 ? `"${t}" on ${ns} pages${ns ? " (Enter: next)" : ""}` : "");
  if (ns && !st.found[st.n]) go(+Object.keys(st.found)[0]); else redraw();
  badges();
}

// ---------------------------------------------------------------- agent
function line(who, html) { const d = document.createElement("div"); d.className = "msg" + (who === "you" ? " you" : ""); d.innerHTML = html; $("#chat").appendChild(d); d.scrollIntoView({ block: "end" }); return d; }
async function send(text) {
  text = (text ?? $("#ask").value).trim(); if (!text) return;
  $("#ask").value = ""; line("you", esc(text));
  const wait = line("agent", `<span class="muted">reading page ${st.n}...</span>`);
  $("#send").disabled = true; $("#agentstate").textContent = "DeepSeek is working";
  try {
    const r = await api("agent", { body: { ...ctx(), page: st.n, message: text, history: st.history } });
    st.history.push({ role: "user", content: text }, { role: "assistant", content: r.reply });
    const calls = r.calls.map(c => `${c.ok ? "" : "x "}${c.name}${c.args.page ? " " + c.args.page : ""}${c.args.path ? " " + c.args.path.split("/").pop() : ""}`).join(", ");
    wait.innerHTML = esc(r.reply) + (calls ? `<div class="calls">${esc(calls)}</div>` : "");
    for (const p of r.proposals) proposal(p);
    if (r.notes.length) { await loadNotes(); redraw(); }
  } catch (e) { wait.innerHTML = `<span class="bad">${esc(e.message)}</span>`; }
  $("#send").disabled = false; $("#agentstate").textContent = "";
}
function proposal(p) {
  const d = document.createElement("div"); d.className = "prop";
  d.innerHTML = `<div class="meta muted">${esc(p.path.split("/").pop())}, from page ${p.page}</div>
    <div>${esc(p.why)}</div><del>${esc(p.find)}</del><ins>${esc(p.replace)}</ins>
    <div class="row"><span class="grow"></span><button data-a="no">Discard</button><button data-a="edit">Open in Source</button><button data-a="yes" class="primary">Apply</button></div>`;
  d.addEventListener("click", async e => {
    const a = e.target.dataset.a; if (!a) return;
    if (a === "no") { d.classList.add("done"); d.querySelector(".row").innerHTML = `<span class="muted">discarded</span>`; return; }
    if (a === "edit") { tab("source"); st.chapter = null; await openChapter(p.path); const i = $("#srctext").value.indexOf(p.find); if (i >= 0) $("#srctext").setSelectionRange(i, i + p.find.length); return; }
    try {
      if (dirty() && st.chapter === p.path) throw new Error("the chapter has unsaved edits in Source; save or revert first");
      await api("replace", { body: { book: st.book, path: p.path, find: p.find, replace: p.replace } });
      d.classList.add("done"); d.querySelector(".row").innerHTML = `<span class="ok">applied to ${esc(p.path.split("/").pop())}; rebuild to print it</span>`;
      if (st.chapter === p.path) { st.chapter = null; await openChapter(p.path); }
    } catch (err) { status(err.message, true); }
  });
  $("#proposals").appendChild(d);
}
$("#send").onclick = () => send();
$("#ask").addEventListener("keydown", e => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) send(); });
$("#asks").addEventListener("click", e => { const b = e.target.closest("[data-ask]"); if (b) send(b.dataset.ask); });

// ---------------------------------------------------------------- certify
function renderCerts() {
  const b = st.builds.find(x => x.build === st.build);
  $("#certs").innerHTML = st.certs.map(c => `
    <div class="cert"><div><b>${esc(c.build)}</b> ${c.build === st.build ? "(on the desk)" : ""}, ${esc(c.at)} by ${esc(c.by)}</div>
      <div class="muted">${c.pages} pages, ${c.trim_in ? c.trim_in.join(" x ") + " in" : ""}, ${esc(c.paper)}; spine ${c.spine_in} in; ${c.warnings_accepted.length} warnings accepted</div>
      <div>${esc(c.file)}</div><code>sha256 ${c.sha256}</code><div class="muted">${esc(c.statement)}</div>
      <div class="row"><button data-v="${c.sha256}" data-b="${c.build}">Check the file still matches</button><span class="vres small"></span></div></div>`).join("")
    || `<div class="empty">None yet.</div>`;
  $("#certify").disabled = !b;
}
$("#certs").addEventListener("click", async e => {
  const btn = e.target.closest("[data-v]"); if (!btn) return;
  const out = btn.parentElement.querySelector(".vres");
  try { const r = await api("verify?" + q({ book: st.book, build: btn.dataset.b, sha: btn.dataset.v })); out.innerHTML = r.same ? `<span class="ok">matches, byte for byte</span>` : `<span class="bad">the file has changed since</span>`; }
  catch (err) { out.innerHTML = `<span class="bad">${esc(err.message)}</span>`; }
});
$("#certify").onclick = async () => {
  $("#certmsg").textContent = "";
  try {
    const c = await api("certify", { body: { ...ctx(), paper: $("#paper").value, statement: $("#statement").value, by: $("#by").value, acceptWarnings: $("#acceptw").checked } });
    $("#certmsg").innerHTML = `<span class="ok">Certified.</span> Upload <b>${esc(c.file)}</b>. Saved as ${esc(c.saved)}.`;
    st.certs = (await api("builds?" + q({ book: st.book }))).certificates; renderCerts();
  } catch (e) { $("#certmsg").innerHTML = `<span class="bad">${esc(e.message)}</span>`; }
};

// ---------------------------------------------------------------- chrome
function tab(name) {
  $$("#rtabs button").forEach(b => b.classList.toggle("on", b.dataset.tab === name));
  $$(".rtab").forEach(s => s.classList.toggle("on", s.dataset.tab === name));
  if (name === "source") openSourceFor(st.n);
}
$("#rtabs").addEventListener("click", e => { const b = e.target.closest("button"); if (b) tab(b.dataset.tab); });
function setTool(t) { st.tool = t; $("#t-hand").classList.toggle("on", t === "hand"); $("#t-note").classList.toggle("on", t === "note"); $("#board").classList.toggle("notetool", t === "note"); }
$("#t-hand").onclick = () => setTool("hand"); $("#t-note").onclick = () => setTool("note");
function setView(spread) { st.spread = spread; $("#v-page").classList.toggle("on", !spread); $("#v-spread").classList.toggle("on", spread); st.fit = true; redraw(); }
$("#v-page").onclick = () => setView(false); $("#v-spread").onclick = () => setView(true);
const zoomBy = f => { st.fit = false; st.zoom = Math.max(0.2, Math.min(4, st.zoom * f)); redraw(); };
$("#zin").onclick = () => zoomBy(1.25); $("#zout").onclick = () => zoomBy(0.8); $("#zfit").onclick = () => { st.fit = true; redraw(); };
const step = d => go(st.spread ? (st.n === 1 && d > 0 ? 2 : visible()[0] + 2 * d) : st.n + d);
$("#prev").onclick = () => step(-1); $("#next").onclick = () => step(1);
$("#pno").onchange = () => go(+$("#pno").value);
["#o-kdp", "#o-box", "#o-notes"].forEach(s => $(s).onchange = redraw);
$("#filter").onchange = applyFilter;
$("#book").onchange = () => { st.n = 1; history.replaceState(null, "", "?" + q({ book: $("#book").value })); openBook($("#book").value); };
$("#build").onchange = () => openBuild($("#build").value);
window.addEventListener("resize", () => { if (st.fit && st.pages) redraw(); });
document.addEventListener("keydown", e => {
  const typing = /INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName);
  if ((e.ctrlKey || e.metaKey) && e.key === "s" && $(".rtabs .on").dataset.tab === "source") { e.preventDefault(); if (dirty()) $("#srcsave").click(); return; }
  if ((e.ctrlKey || e.metaKey) && e.key === "f") { e.preventDefault(); $("#find").focus(); $("#find").select(); return; }
  if (typing) return;
  const k = e.key;
  if (k === "ArrowRight" || k === "PageDown") { e.preventDefault(); step(1); }
  else if (k === "ArrowLeft" || k === "PageUp") { e.preventDefault(); step(-1); }
  else if (k === "Home") go(1); else if (k === "End") go(st.pages);
  else if (k === "+" || k === "=") zoomBy(1.25); else if (k === "-") zoomBy(0.8); else if (k === "0") { st.fit = true; redraw(); }
  else if (k === "n" || k === "N") setTool("note"); else if (k === "v" || k === "V") setTool("hand");
  else if (k === "s" || k === "S") setView(!st.spread);
  else if (k === "Escape") { closePop(); setTool("hand"); }
});
window.addEventListener("beforeunload", e => { if (dirty()) { e.preventDefault(); e.returnValue = ""; } });

boot().catch(e => status(e.message, true));
