// The build guide: the dome put up step by step, piece by piece, from the solver's own list of
// steps (tables.steps). An "add" step shows everything built so far, lights the pieces it adds and
// hides what comes later; a "prep" step (cutting, bevelling, welding out) shows the finished dome
// ghosted with the pieces it is about lit. Each step says what to do, with what, and how to check
// it, in the viewer's units. The step book prints every step with its picture.
//
// Renders live here too: Render draws this design from the page's own view -- every scene and a
// spread of build steps -- and the local server saves them to a new numbered folder.

const $ = (s) => document.querySelector(s);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const slug = (s) => String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

export function initBuild(ctx) {
  const { S, U, THREE } = ctx;
  let play = null, focus = new Set();
  const steps = () => (S.data && S.data.tables.steps) || [];

  function role(p) {
    const st = steps()[S.build.i];
    if (!st) return null;
    if (p.tag === "person") return "hidden";
    if (p.tag === "site" || p.step < 0) return null;
    if (st.mode === "prep") return focus.size ? (focus.has(p.id) ? "hi" : "ghost") : null;
    if (p.step > st.show) return "hidden";
    return focus.has(p.id) ? "hi" : null;
  }

  function show(i, instant = false) {
    const list = steps();
    if (!list.length) return;
    S.build.i = Math.max(0, Math.min(list.length - 1, i));
    const st = list[S.build.i];
    focus = new Set(st.focus || []);
    S.build.role = role;
    ctx.applyVisibility(); ctx.applyStyle();
    // frame what the step is about; a step about everything frames the dome
    const ids = focus.size ? focus : null;
    ctx.zoomExtents(!instant, null, ids);
    $("#bp-phase").textContent = st.phase || (st.mode === "prep" ? "Prepare" : "Build");
    $("#bp-count").textContent = `Step ${S.build.i + 1} of ${list.length}`;
    $("#bp-title").textContent = st.title;
    $("#bp-text").textContent = U.tokens(st.text);
    $("#bp-tools").innerHTML = (st.tools || []).map((t) => `<span class="chip">${esc(t)}</span>`).join("");
    $("#bp-check").innerHTML = st.check ? `<b>Check:</b> ${esc(U.tokens(st.check))}` : "";
    $("#bp-check").hidden = !st.check;
    $("#bp-fill").style.width = `${(100 * (S.build.i + 1)) / list.length}%`;
    $("#bp-jump").value = String(S.build.i);
    $("#bp-prev").disabled = S.build.i === 0;
    $("#bp-next").disabled = S.build.i === list.length - 1;
    const added = st.mode === "add" ? focus.size : 0;
    ctx.toast(st.mode === "add" ? `Step ${S.build.i + 1}: ${added} piece${added === 1 ? "" : "s"} go up.` : `Step ${S.build.i + 1}: ${st.title}`);
  }

  function open(i = S.build.i || 0) {
    if (S.defaults && S.defaults.edition === "trial") { ctx.toast("The build guide is part of the full Dome Sketch."); return; }
    if (!steps().length) { ctx.toast("This design has no build steps."); return; }
    S.build.on = true;
    S.colour = false;                              // a scene's family colours would hide the lit pieces
    S.explode = 0; $("#explode").value = 0; ctx.applyTransforms();
    S.tagsOff = new Set(); ctx.renderTags();
    $("#buildpanel").hidden = false;
    $("#guide").classList.add("on");
    $("#bp-jump").innerHTML = steps().map((s, k) => `<option value="${k}">${k + 1}. ${esc(s.title)}</option>`).join("");
    show(i);
  }
  function close() {
    stop();
    S.build.on = false; S.build.role = null; focus = new Set();
    $("#buildpanel").hidden = true;
    $("#guide").classList.remove("on");
    ctx.applyVisibility(); ctx.applyStyle();
  }
  function stop() { if (play) { clearInterval(play); play = null; $("#bp-play").innerHTML = "&#9654; Play"; } }
  function toggle() { S.build.on ? close() : open(); }
  const next = () => { stop(); show(S.build.i + 1); };
  const prev = () => { stop(); show(S.build.i - 1); };

  $("#bp-next").onclick = next;
  $("#bp-prev").onclick = prev;
  $("#bp-close").onclick = close;
  $("#bp-jump").onchange = () => { stop(); show(+$("#bp-jump").value); };
  $("#bp-play").onclick = () => {
    if (play) { stop(); return; }
    $("#bp-play").innerHTML = "&#10074;&#10074; Pause";
    play = setInterval(() => { if (S.build.i >= steps().length - 1) stop(); else show(S.build.i + 1); }, 3200);
  };

  // ---------------------------------------------------------------- the step book
  async function printBook() {
    if (S.defaults && S.defaults.edition === "trial") { ctx.toast("The step book is part of the full Dome Sketch."); return; }
    const list = steps(), was = S.build.on ? S.build.i : null;
    if (!S.build.on) open(0);
    const pages = [];
    for (let k = 0; k < list.length; k++) {
      show(k, true);
      await new Promise((r) => requestAnimationFrame(r));
      pages.push(ctx.still(960, 600));
    }
    if (was === null) close(); else show(was, true);
    const t = S.data.tables;
    const w = window.open("", "_blank");
    if (!w) return;
    const body = list.map((st, k) => `<section class="step"><img src="${pages[k]}"><div><p class="ph">${esc(st.phase || "")} &middot; step ${k + 1} of ${list.length}</p>` +
      `<h2>${esc(st.title)}</h2><p>${esc(U.tokens(st.text))}</p>` +
      (st.tools && st.tools.length ? `<p class="tools">${st.tools.map((x) => `<span>${esc(x)}</span>`).join("")}</p>` : "") +
      (st.check ? `<p class="check"><b>Check:</b> ${esc(U.tokens(st.check))}</p>` : "") + `</div></section>`).join("");
    w.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>${esc(t.title)}: the build, step by step</title><style>
      body{font:13px "Segoe UI",system-ui,sans-serif;color:#1d1b18;margin:18px}h1{font-size:22px}.step{display:grid;grid-template-columns:480px 1fr;gap:16px;
      border-top:2px solid #c45e29;padding:12px 0;break-inside:avoid}.step img{width:480px;border:1px solid #cfccc4;border-radius:6px}.ph{color:#c45e29;font-weight:600;margin:0}
      h2{margin:4px 0 8px;font-size:17px}.tools span{display:inline-block;background:#efe9df;border-radius:10px;padding:1px 8px;margin:0 4px 4px 0}
      .check{background:#eef4fb;border-left:3px solid #1f6fd1;padding:4px 8px}@media print{.step{grid-template-columns:330px 1fr}.step img{width:330px}}</style></head>
      <body><h1>${esc(t.title)}: the build, step by step</h1><p>${(t.summary || []).slice(0, 6).map(([k, v]) => `${esc(k)}: <b>${esc(U.tokens(v))}</b>`).join(" &middot; ")}</p>
      ${body}<script>setTimeout(()=>print(),600)<\/script></body></html>`);
    w.document.close();
  }
  $("#bp-print").onclick = printBook;

  // ---------------------------------------------------------------- renders from this view
  async function shots() {
    const t = S.data.tables, out = [];
    const keepScene = ctx.SCENES.find((s) => s.name === S.scene) || ctx.SCENES[0];
    let n = 1;
    for (const sc of ctx.SCENES.slice()) {
      ctx.goScene(sc, true);
      await new Promise((r) => requestAnimationFrame(r));
      out.push({ file: `${String(n++).padStart(2, "0")}-${slug(sc.name)}`, caption: `${t.title}: ${sc.name}.`, png: ctx.still(1920, 1080) });
    }
    const list = steps(), adds = list.map((s, k) => [s, k]).filter(([s]) => s.mode === "add");
    const pick = adds.length <= 8 ? adds : Array.from({ length: 8 }, (_, j) => adds[Math.round(j * (adds.length - 1) / 7)]);
    if (pick.length) {
      open(pick[0][1]);
      for (const [s, k] of pick) {
        show(k, true);
        await new Promise((r) => requestAnimationFrame(r));
        out.push({ file: `${String(n++).padStart(2, "0")}-step-${String(k + 1).padStart(2, "0")}-${slug(s.title)}`,
                   caption: `Step ${k + 1} of ${list.length}: ${s.title}. ${U.tokens(s.text)}`, png: ctx.still(1920, 1080) });
      }
      close();
    }
    ctx.goScene(keepScene);
    return out;
  }
  async function renderThis() {
    const t = S.data.tables;
    ctx.toast(`Rendering ${t.title}...`);
    const list = await shots();
    const facts = (t.summary || []).map(([k, v]) => [k, U.tokens(v)]);
    const r = await ctx.api("/api/stills", { name: `renders-${S.kind}-${slug(t.title)}`, title: t.title, shots: list, facts });
    ctx.toast(`Saved ${r.files} pictures to ${r.folder}.`);
    return r;
  }
  $("#render").onclick = () => renderThis().catch((e) => ctx.toast(e.message));
  $("#renderall").onclick = async () => {
    const all = S.defaults.presets, done = [];
    for (const p of all) {
      ctx.toast(`Rendering preset ${done.length + 1} of ${all.length}: ${p.label}...`);
      try { await ctx.usePreset(p); done.push((await renderThis()).folder); }
      catch (e) { ctx.toast(`${p.label}: ${e.message}`); }
    }
    ctx.toast(`Rendered ${done.length} presets into ${done.length} new folders.`);
  };

  return {
    toggle, open, close, next, prev,
    reset: () => { if (S.build.on) close(); S.build.i = 0; },
    refresh: () => { if (S.build.on) show(S.build.i, true); },
  };
}
