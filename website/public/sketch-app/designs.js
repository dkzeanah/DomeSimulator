// copied from sketch_claude/static/designs.js by website/scripts/sync_sketch_app.py: edit that file, then re-run
// Designs: save the dome on screen under a name (with a small picture of it), open it again, share
// it as a link, and compare any two side by side -- every figure on the summary, the materials
// estimate and the cut list's size, with the differences marked. Saved designs live in this
// browser; a design's link carries the whole design, so it opens the same anywhere.

const $ = (s) => document.querySelector(s);
const KEY = "dome-sketch-designs";

function list() { try { return JSON.parse(localStorage.getItem(KEY) || "[]"); } catch { return []; } }
function keep(v) {
  try { localStorage.setItem(KEY, JSON.stringify(v)); return true; }
  catch { return false; }
}

function thumb(png) {
  // a small JPEG of the view, so a dozen designs fit in the browser's storage
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const c = document.createElement("canvas"); c.width = 240; c.height = 150;
      c.getContext("2d").drawImage(img, 0, 0, 240, 150);
      resolve(c.toDataURL("image/jpeg", 0.78));
    };
    img.onerror = () => resolve("");
    img.src = png;
  });
}

export function initDesigns(ctx) {
  const { S, U, esc } = ctx;

  const link = (spec) => `${location.origin}${location.pathname}?spec=${encodeURIComponent(JSON.stringify(spec))}`;
  const facts = (t) => ({
    title: t.title, kind: t.kind, summary: t.summary || [],
    total: t.materials ? t.materials.total : null,
    cards: (t.cards || []).length, pieces: (t.cards || []).reduce((a, c) => a + (c.count || 0), 0), steps: (t.steps || []).length,
  });

  async function save() {
    const name = ($("#ds-name").value || S.data.tables.title || "My dome").trim();
    const d = { id: Date.now().toString(36), name, spec: S.spec, saved: new Date().toISOString(), thumb: await thumb(ctx.still(480, 300)), ...facts(S.data.tables) };
    const all = [d, ...list().filter((x) => x.name !== name)];
    while (!keep(all) && all.length > 1) all.pop();       // the browser is full: the oldest go first
    $("#ds-name").value = "";
    ctx.toast(`Saved "${name}".`);
    render();
  }

  async function share() {
    const url = link(S.spec);
    try { await navigator.clipboard.writeText(url); ctx.toast("The link to this design is copied: it opens this exact dome."); }
    catch { prompt("The link to this design:", url); }
  }

  function render() {
    const box = $("#designs");
    const all = list();
    box.innerHTML =
      `<div class="row ds-save"><input id="ds-name" placeholder="${esc(S.data ? S.data.tables.title : "Name")}" maxlength="60">` +
      `<button id="ds-save" title="Keep this design in this browser">Save</button></div>` +
      `<div class="row"><button id="ds-share" title="Copy a link that opens this exact design">Copy link</button>` +
      `<button id="ds-cmp" ${all.length ? "" : "disabled"} title="Compare this design with a saved one">Compare</button></div>` +
      (all.length ? all.map((d) => `<div class="ds" data-id="${d.id}">` +
        (d.thumb ? `<img src="${d.thumb}" alt="">` : `<div class="ph"></div>`) +
        `<div><b>${esc(d.name)}</b><br><span class="muted">${esc(d.title || "")}${d.total !== null && d.total !== undefined ? ` &middot; ${"$" + Math.round(d.total).toLocaleString()}` : ""}</span><br>` +
        `<span class="muted small">${new Date(d.saved).toLocaleDateString()}</span></div>` +
        `<div class="ds-act"><button data-a="open" title="Open">Open</button><button data-a="cmp" title="Compare with the design on screen">&#8646;</button>` +
        `<button data-a="del" title="Forget this design">&#10005;</button></div></div>`).join("")
        : `<p class="muted">Nothing saved yet. Name the design and Save it; it stays in this browser.</p>`);
    $("#ds-save").onclick = () => save().catch((e) => ctx.toast(e.message));
    $("#ds-share").onclick = share;
    $("#ds-cmp").onclick = () => { const d = list()[0]; if (d) compare(d); };
    box.querySelectorAll(".ds").forEach((el) => {
      const d = list().find((x) => x.id === el.dataset.id);
      el.querySelectorAll("button").forEach((b) => b.onclick = (ev) => {
        ev.stopPropagation();
        if (b.dataset.a === "open") ctx.openSpec(d.spec);
        if (b.dataset.a === "cmp") compare(d);
        if (b.dataset.a === "del" && confirm(`Forget "${d.name}"?`)) { keep(list().filter((x) => x.id !== d.id)); render(); }
      });
    });
  }

  // ---------------------------------------------------------------- compare two designs
  async function compare(other) {
    const modal = $("#compare");
    modal.hidden = false;
    modal.innerHTML = `<div class="modal-box"><p>Solving "${esc(other.name)}"...</p></div>`;
    let b;
    try { b = (await ctx.api("/api/model", { spec: other.spec })).tables; }
    catch (e) { modal.innerHTML = `<div class="modal-box"><p>${esc(e.message)}</p><button id="cmp-x">Close</button></div>`; $("#cmp-x").onclick = () => (modal.hidden = true); return; }
    const A = { name: "On screen", thumb: ctx.still(480, 300), ...facts(S.data.tables) };
    const B = { name: other.name, thumb: other.thumb, ...facts(b) };
    const labels = [...new Set([...A.summary.map(([k]) => k), ...B.summary.map(([k]) => k)])];
    const val = (d, k) => (d.summary.find(([kk]) => kk === k) || [k, ""])[1];
    const rows = [
      ...labels.map((k) => [k, U.tokens(val(A, k)), U.tokens(val(B, k))]),
      ["Materials, estimated", A.total === null ? "" : "$" + Math.round(A.total).toLocaleString(), B.total === null ? "" : "$" + Math.round(B.total).toLocaleString()],
      ["Cut families", String(A.cards), String(B.cards)], ["Pieces to cut", A.pieces.toLocaleString(), B.pieces.toLocaleString()],
      ["Build steps", String(A.steps), String(B.steps)],
    ];
    modal.innerHTML = `<div class="modal-box wide"><div class="bp-head"><b>Compare</b><span class="grow"></span><button id="cmp-x" title="Close">&#10005;</button></div>` +
      `<table class="cmp"><tr><th></th><th>${A.thumb ? `<img src="${A.thumb}" alt="">` : ""}<br>${esc(A.title)}<br><span class="muted">on screen</span></th>` +
      `<th>${B.thumb ? `<img src="${B.thumb}" alt="">` : ""}<br>${esc(B.title)}<br><span class="muted">${esc(B.name)}</span></th></tr>` +
      rows.map(([k, a, c]) => `<tr class="${a !== c ? "diff" : ""}"><td>${esc(k)}</td><td>${esc(a)}</td><td>${esc(c)}</td></tr>`).join("") +
      `</table><p class="muted small">Rows that differ are marked. Every figure is each design's own solver's; the cost is an estimate at the declared prices.</p>` +
      `<div class="row"><button id="cmp-open">Open "${esc(other.name)}"</button></div></div>`;
    $("#cmp-x").onclick = () => (modal.hidden = true);
    $("#cmp-open").onclick = () => { modal.hidden = true; ctx.openSpec(other.spec); };
  }
  $("#compare").addEventListener("click", (ev) => { if (ev.target.id === "compare") $("#compare").hidden = true; });

  return { render };
}
