// Dome Sketch on zeanahlab.com: the local modeller's own page (app.js and its modules, copied in by
// scripts/sync_sketch_app.py), with this file standing in for its Python server.
//
// The page asks its server these things. Here:
//   /api/defaults   every kind of dome and its presets from the solved index (grid.json), the forms
//                   fitted to what is solved (sizes and window counts from the grid; the other kinds
//                   as their presets), and this visitor's edition (GET /api/sketch/edition)
//   /api/model      the nearest solved design (GET /api/sketch/design/<id>): a framed-panel dome from
//                   the grid, then the options the page can apply itself (skin, furnished, stove, porch,
//                   person: each proven against a real build by sketch_claude/web_catalogue.py); any
//                   other kind, its preset. A visitor who has not bought Dome Sketch receives the trial
//                   copy, which carries no build steps and no drawings past the first cards.
//   /api/export     the design's fabrication pack (GET /api/sketch/export/<id>): DXF, CSV, OBJ, STL, glTF
//   /api/plans      a build pack for this exact framed-panel design, queued for the owner's machine
//   /api/jobs       this account's build packs, as the page's job list
//   /api/showcase, /api/stills, /api/export-pack, /api/outputs   made on the workshop computer, not here

const realFetch = window.fetch.bind(window);
const grid = await (await realFetch("/sketch-app/grid.json")).json();
const opts = grid.clientOptions;
const $ = (s) => document.querySelector(s);
const json = (data, status = 200) => new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json" } });
const LOCAL = "Made on the workshop computer: the full Dome Sketch there changes every figure.";
let current = null;              // the id of the design on screen
let edition = "trial";

function designId(s) {
  return `${s.frequency}v${String(s.cut).replace("/", "-")}-${(+s.diameter_m).toFixed(2)}m-door${s.door ? 1 : 0}-win${s.windows}-sky${s.skylight ? 1 : 0}`;
}

/** The solved framed-panel design nearest to what the form asks for. */
function snap(spec) {
  const cut = grid.cuts.find((c) => c.frequency === +spec.frequency && c.cut === spec.cut) || grid.cuts[0];
  const near = (list, x) => list.reduce((a, b) => (Math.abs(b - x) < Math.abs(a - x) ? b : a));
  return { ...grid.defaults, ...spec, kind: "panel", frequency: cut.frequency, cut: cut.cut, diameter_m: near(grid.diameters, +spec.diameter_m || 5),
           windows: near(grid.windows, +spec.windows || 0), door: spec.door !== false, skylight: !!spec.skylight };
}

/** The preset of another kind that this spec is (or the kind's first one). */
function kindPreset(spec) {
  const same = (grid.kindPresets || []).filter((p) => p.kind === spec.kind);
  const key = (s) => JSON.stringify(Object.keys(s).sort().map((k) => [k, typeof s[k] === "number" ? +s[k].toFixed(6) : s[k]]));
  return same.find((p) => key(p.spec) === key({ ...p.spec, ...spec })) || same[0] || null;
}

/** What the page does itself, from the full framed-panel design: the same pieces a real build with these options keeps. */
function apply(data, spec) {
  const hideGroups = new Set(Object.entries(opts.groups).filter(([k]) => spec[k] === false).map(([, g]) => g));
  const covering = new Set(Object.keys(opts.clearSkin));
  data.pieces = data.pieces.filter((p) => !hideGroups.has(p.group) && !(spec.skin === "none" && p.tag === "skin" && covering.has(p.material)));
  if (spec.skin === "clear") for (const p of data.pieces) if (p.tag === "skin" && opts.clearSkin[p.material]) p.material = opts.clearSkin[p.material];
  const ids = new Set(data.pieces.map((p) => p.id));
  const t = data.tables;
  if (t.steps) t.steps = t.steps.map((s) => ({ ...s, focus: (s.focus || []).filter((f) => ids.has(f)) })).filter((s) => s.mode !== "add" || s.focus.length);
  if (t.cards) t.cards = t.cards.map((c) => ({ ...c, ids: (c.ids || []).filter((f) => ids.has(f)) }));
  if (t.materials && (spec.porch === false || spec.skin !== "cabin")) {
    t.materials = { ...t.materials, note: `Counted for this size with the porch and the cabin skin, as solved online; your build pack counts your exact choice. ${t.materials.note}` };
  }
  return data;
}

function banner(text, href, label) {
  let b = document.getElementById("web-banner");
  if (text === null) { if (b) b.remove(); return; }
  if (!b) {
    b = document.createElement("div");
    b.id = "web-banner";
    b.style.cssText = "position:fixed;left:50%;top:58px;transform:translateX(-50%);z-index:50;background:#1d1a15;color:#fff7e8;padding:8px 14px;border-radius:8px;font:13px Inter,Segoe UI,sans-serif;box-shadow:0 4px 16px rgba(0,0,0,.3);max-width:92vw";
    document.body.append(b);
  }
  b.innerHTML = `${text}${href ? ` <a href="${href}" style="color:#ffd27a;font-weight:600;margin-left:6px">${label}</a>` : ""}`;
}
const UNLOCK = ["Trial: the wedge dome, the stove and two framed-panel domes are open to look round. Every design, the cut cards, the build guide and the cutting files come with Dome Sketch ($10, or free with the book).",
                "/software#dome-sketch", "Unlock"];

async function fetchDesign(id, nearest) {
  if (edition === "full") banner(null);        // a buyer's banner was about an earlier design
  let r = await realFetch(`/api/sketch/design/${id}`);
  const open = [...grid.trial].sort((a, b) => nearest(a) - nearest(b));
  if (r.status === 402) {
    banner(...UNLOCK);
    id = open[0];
    r = await realFetch(`/api/sketch/design/${id}`);
  }
  // a design not on the server yet (they are published one by one): show the nearest one that is
  for (const t of open) {
    if (r.ok || r.status === 402) break;
    if (t === id) continue;
    const r2 = await realFetch(`/api/sketch/design/${t}`);
    if (r2.ok) { banner("That design is not online yet, so here is one that is. Every design is being published; try it again shortly."); id = t; r = r2; }
  }
  if (!r.ok) {
    banner("The designs are still being published to the website. Try again in a few minutes.");
    return [null, json({ error: (await r.json().catch(() => ({}))).error || "That design could not be loaded." }, r.status)];
  }
  return [id, r];
}

async function model(spec) {
  spec = spec || {};
  if (spec.kind && spec.kind !== "panel") {
    const p = kindPreset(spec);
    if (!p) return json({ error: "That kind of dome is not online yet." }, 404);
    const [id, r] = await fetchDesign(p.id, (t) => (grid.designs[t].kind === spec.kind ? 0 : t === grid.default ? 1 : 2));
    if (!id) return r;
    current = id;
    const data = await r.json();
    data.spec = { ...grid.designs[id].spec };
    return json(data);
  }
  const want = snap(spec);
  const far = (t) => { const s = grid.designs[t].spec;
    return (grid.designs[t].kind && grid.designs[t].kind !== "panel" ? 1000 : 0) + (s.frequency === want.frequency && s.cut === want.cut ? 0 : 100) + Math.abs(s.diameter_m - want.diameter_m); };
  const [id, r] = await fetchDesign(designId(want), far);
  if (!id) return r;
  current = id;
  const data = await r.json();
  if (grid.designs[id].kind && grid.designs[id].kind !== "panel") { data.spec = { ...grid.designs[id].spec }; return json(data); }
  const shown = { ...data.spec, ...grid.designs[id].spec, kind: "panel", skin: want.skin, furnish: want.furnish, porch: want.porch, stove: want.stove, people: want.people };
  apply(data, shown);
  data.spec = shown;           // the form shows what is drawn
  return json(data);
}

async function exportPack(spec) {
  // the design the page asks for (a comparison may have loaded another one since)
  const p = spec && spec.kind && spec.kind !== "panel" ? kindPreset(spec) : null;
  const id = p ? p.id : current;
  if (!id || !(grid.packs || {})[id]) {
    return json({ error: "For a framed-panel dome, the build pack (Make my build pack) is the cutting file: plans, cut list and every step." }, 400);
  }
  const r = await realFetch(`/api/sketch/export/${id}`);
  if (!r.ok) return json({ error: (await r.json().catch(() => ({}))).error || "The pack could not be fetched." }, r.status);
  return r;
}

let jobsCache = { at: 0, data: [] };
async function jobs() {
  if (Date.now() - jobsCache.at < 8000) return json(jobsCache.data);
  const r = await realFetch("/api/sketch/packs");
  if (!r.ok) return json([]);
  const { packs } = await r.json();
  jobsCache = { at: Date.now(), data: packs.map((p) => ({
    id: p.ref, kind: "plans", state: p.status === "done" ? "done" : p.status === "failed" ? "failed" : "running",
    started: Date.parse(p.createdAt) / 1000, ended: p.doneAt ? Date.parse(p.doneAt) / 1000 : null,
    output: p.status === "done" ? `packs/${p.ref}.pdf` : null,
    title: `${p.spec.frequency}V ${p.spec.cut}, ${(+p.spec.diameter_m).toFixed(2)} m build pack`,
    log: p.status === "failed" ? (p.error || "") : p.status === "done" ? "Ready: open the PDF." : "Being drawn on the workshop computer; this page checks by itself.",
  })) };
  return json(jobsCache.data);
}

async function defaults() {
  try { edition = (await (await realFetch("/api/sketch/edition")).json()).edition || "trial"; } catch { edition = "trial"; }
  const ONLINE = "Online, this dome comes as its presets; the full Dome Sketch on your own computer changes every figure.";
  const kinds = {};
  for (const [k, v] of Object.entries(grid.kinds || {})) {
    kinds[k] = { ...v, form: v.form.map((f) => {
      if (k !== "panel") return { ...f, fixed: ONLINE };
      if (f.key === "diameter_m") return { ...f, choices: grid.diameters };
      if (f.key === "windows") return { ...f, choices: grid.windows };
      if (["stick_w_m", "stick_d_m", "riser_m", "door_w_m", "door_h_m"].includes(f.key)) return { ...f, fixed: "Fixed online: the full Dome Sketch on your own computer changes it." };
      return f;
    }) };
  }
  const panel = Object.entries(grid.presets).map(([key, p]) => ({ key, group: "Framed-panel domes", label: p.label, spec: snap({ ...grid.defaults, ...p.spec }) }));
  const others = (grid.kindPresets || []).map((p) => ({ key: p.key, group: p.group, label: p.label, spec: { ...p.spec } }));
  const flagship = others.filter((p) => p.spec.kind === "wedge"), rest = others.filter((p) => p.spec.kind !== "wedge");
  const presets = [...flagship, ...panel, ...rest];
  const first = presets.find((p) => `k-${p.key}` === grid.default) || presets[0];
  if (edition === "trial") banner(...UNLOCK);
  return json({ spec: first.spec, presets, kinds, default: first.key, tag: grid.tag, cuts: grid.cuts, declared: grid.declared, edition,
                exports: [["zip", "Fabrication pack (zip): DXF, CSV, OBJ, STL, glTF"]] });
}

window.fetch = async (input, init = {}) => {
  const url = typeof input === "string" ? input : input.url;
  const body = () => JSON.parse(init.body || "{}");
  if (url === "/api/defaults") return defaults();
  if (url === "/api/model") return model(body().spec);
  if (url === "/api/export") return edition === "full" ? exportPack(body().spec) : json({ error: "The cutting files and models come with the full Dome Sketch." }, 402);
  if (url === "/api/plans") {
    const spec = body().spec || {};
    if (spec.kind && spec.kind !== "panel") return json({ error: "Build packs are drawn for framed-panel domes. For this one, its cut cards, build guide and fabrication pack are on the page." }, 400);
    const r = await realFetch("/api/sketch/packs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ spec: snap(spec) }) });
    jobsCache.at = 0;
    if (r.status === 401) return json({ error: "Sign in at zeanahlab.com (Account) to make a build pack." }, 401);
    return new Response(await r.text(), { status: r.status, headers: { "Content-Type": "application/json" } });
  }
  if (["/api/showcase", "/api/stills", "/api/export-pack"].includes(url)) return json({ error: LOCAL }, 400);
  if (url === "/api/jobs") return jobs();
  if (url === "/api/outputs") return json([]);
  return realFetch(input, init);
};

// the page's own buttons that belong to the workshop computer, not the website
$("#plans").textContent = "Make my build pack";
$("#plans").title = "The full plan set for this exact framed-panel design: plans, cut list, materials, tools, price estimate and every step, as a PDF";
for (const id of ["#showcase", "#render", "#renderall"]) { const el = $(id); if (el) el.hidden = true; }
document.querySelectorAll('a[href="/director"], a[href="/season"]').forEach((a) => a.remove());
for (const p of document.querySelectorAll("p.muted")) {
  if (p.textContent.includes("numbered folder")) p.innerHTML = "A build pack is drawn for your design exactly on the workshop computer, usually within the day. It appears here and in My Links, ready to download.";
}
const home = document.createElement("a");
home.href = "/mylinks"; home.textContent = "zeanahlab.com: My Links";
home.style.cssText = "margin-left:12px;font-size:12px;color:inherit;opacity:.8";
document.querySelector("header .brand, header > div")?.append(home);
