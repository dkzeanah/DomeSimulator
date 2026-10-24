// Dome Sketch on zeanahlab.com: the local modeller's own page (app.js, copied in by
// scripts/sync_sketch_app.py), with this file standing in for its Python server.
//
// The page asks its server six things. Here:
//   /api/defaults   the solved grid's own defaults, presets and declared values (grid.json)
//   /api/model      the nearest solved design (GET /api/sketch/design/<id>), then the options the
//                   page can apply itself: skin, furnished, stove, porch, person (each proven against
//                   a real build by sketch_claude/web_catalogue.py, so nothing shown is approximate)
//   /api/plans      a build pack for this exact design, queued for the owner's machine
//   /api/showcase   not offered online
//   /api/jobs       this account's build packs, as the page's job list
//   /api/outputs    nothing (packs live in the job list and My Links)
// Sizes and window counts become choices from the grid; the stock sizes and door opening are fixed.

const realFetch = window.fetch.bind(window);
const grid = await (await realFetch("/sketch-app/grid.json")).json();
const opts = grid.clientOptions;
const $ = (s) => document.querySelector(s);
const json = (data, status = 200) => new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json" } });
const num = (x) => String(+(+x).toFixed(4));
let locked = false;

function designId(s) {
  return `${s.frequency}v${String(s.cut).replace("/", "-")}-${(+s.diameter_m).toFixed(2)}m-door${s.door ? 1 : 0}-win${s.windows}-sky${s.skylight ? 1 : 0}`;
}

/** The solved design nearest to what the form asks for. */
function snap(spec) {
  const cut = grid.cuts.find((c) => c.frequency === +spec.frequency && c.cut === spec.cut) || grid.cuts[0];
  const near = (list, x) => list.reduce((a, b) => (Math.abs(b - x) < Math.abs(a - x) ? b : a));
  return { ...spec, frequency: cut.frequency, cut: cut.cut, diameter_m: near(grid.diameters, +spec.diameter_m || 5),
           windows: near(grid.windows, +spec.windows || 0), door: !!spec.door, skylight: !!spec.skylight };
}

/** What the page does itself, from the full design: the same pieces a real build with these options keeps. */
function apply(data, spec) {
  const hideGroups = new Set(Object.entries(opts.groups).filter(([k]) => spec[k] === false).map(([, g]) => g));
  const covering = new Set(Object.keys(opts.clearSkin));
  data.pieces = data.pieces.filter((p) => !hideGroups.has(p.group) && !(spec.skin === "none" && p.tag === "skin" && covering.has(p.material)));
  if (spec.skin === "clear") for (const p of data.pieces) if (p.tag === "skin" && opts.clearSkin[p.material]) p.material = opts.clearSkin[p.material];
  data.spec = { ...data.spec, skin: spec.skin, furnish: spec.furnish, porch: spec.porch, stove: spec.stove, people: spec.people };
  return data;
}

function banner(text, href, label) {
  let b = document.getElementById("web-banner");
  if (!b) {
    b = document.createElement("div");
    b.id = "web-banner";
    b.style.cssText = "position:fixed;left:50%;top:58px;transform:translateX(-50%);z-index:50;background:#1d1a15;color:#fff7e8;padding:8px 14px;border-radius:8px;font:13px Inter,Segoe UI,sans-serif;box-shadow:0 4px 16px rgba(0,0,0,.3);max-width:92vw";
    document.body.append(b);
  }
  b.innerHTML = `${text}${href ? ` <a href="${href}" style="color:#ffd27a;font-weight:600;margin-left:6px">${label}</a>` : ""}`;
}

async function model(spec) {
  const want = snap(spec);
  let id = designId(want);
  let r = await realFetch(`/api/sketch/design/${id}`);
  if (r.status === 402) {
    locked = true;
    banner("Trial: two designs are open. Every size, door and window choice, and the build pack, come with Dome Sketch ($10, or free with the book).",
           "/software#dome-sketch", "Unlock");
    // the open design nearest to what was asked: same geodesic first, then size
    const far = (t) => { const s = grid.designs[t].spec;
      return (s.frequency === want.frequency && s.cut === want.cut ? 0 : 100) + Math.abs(s.diameter_m - want.diameter_m); };
    id = grid.trial.includes(id) ? id : [...grid.trial].sort((a, b) => far(a) - far(b))[0];
    r = await realFetch(`/api/sketch/design/${id}`);
  }
  if (!r.ok) return json({ error: (await r.json().catch(() => ({}))).error || "That design could not be loaded." }, r.status);
  const data = apply(await r.json(), want);
  const shown = { ...data.spec, ...grid.designs[id].spec, skin: want.skin, furnish: want.furnish, porch: want.porch, stove: want.stove, people: want.people };
  data.spec = shown;
  // the form shows what is drawn
  $("#f-diameter_m").value = num(shown.diameter_m);
  $("#f-windows").value = String(shown.windows);
  $("#f-cut").value = `${shown.frequency}|${shown.cut}`;
  $("#f-door").checked = !!shown.door; $("#f-skylight").checked = !!shown.skylight;
  return json(data);
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

window.fetch = async (input, init = {}) => {
  const url = typeof input === "string" ? input : input.url;
  const body = () => JSON.parse(init.body || "{}");
  if (url === "/api/defaults") {
    const presets = Object.fromEntries(Object.entries(grid.presets).map(([k, p]) => [k, { ...p, spec: snap({ ...grid.defaults, ...p.spec }) }]));
    return json({ spec: grid.defaults, presets, tag: grid.tag, cuts: grid.cuts, declared: grid.declared });
  }
  if (url === "/api/model") return model(body().spec);
  if (url === "/api/plans") {
    const r = await realFetch("/api/sketch/packs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ spec: snap(body().spec) }) });
    jobsCache.at = 0;
    if (r.status === 401) return json({ error: "Sign in at zeanahlab.com (Account) to make a build pack." }, 401);
    return new Response(await r.text(), { status: r.status, headers: { "Content-Type": "application/json" } });
  }
  if (url === "/api/showcase") return json({ error: "Showcase renders are made on the workshop computer, not online." }, 400);
  if (url === "/api/jobs") return jobs();
  if (url === "/api/outputs") return json([]);
  return realFetch(input, init);
};

// the form: grid choices for what the grid solves, fixed values for what it does not
function toSelect(id, values, label) {
  const old = $(id);
  const sel = document.createElement("select");
  sel.id = old.id;
  sel.innerHTML = values.map((v) => `<option value="${num(v)}">${label(v)}</option>`).join("");
  old.replaceWith(sel);
}
toSelect("#f-diameter_m", grid.diameters, (d) => `${(+d).toFixed(2)} m (${(d / 0.3048).toFixed(1)} ft)`);
toSelect("#f-windows", grid.windows, (w) => `${w}`);
for (const id of ["#f-stick_w_m", "#f-stick_d_m", "#f-riser_m", "#f-door_w_m", "#f-door_h_m"]) {
  const el = $(id); el.disabled = true; el.title = "Fixed in the online version: the full modeller on the workshop computer changes it.";
}
$("#plans").textContent = "Make my build pack";
$("#plans").title = "The full plan set for this exact design: plans, cut list, materials, tools, price estimate and every step, as a PDF";
$("#showcase").hidden = true;
// the studio's own links and notes belong to the workshop computer, not the website
document.querySelectorAll('a[href="/director"], a[href="/season"]').forEach((a) => a.remove());
for (const p of document.querySelectorAll("p.muted")) {
  if (p.textContent.includes("numbered folder")) p.innerHTML = "A build pack is drawn for your design exactly on the workshop computer, usually within the day. It appears here and in My Links, ready to download.";
}
const home = document.createElement("a");
home.href = "/mylinks"; home.textContent = "zeanahlab.com: My Links";
home.style.cssText = "margin-left:12px;font-size:12px;color:inherit;opacity:.8";
document.querySelector("header .brand, header > div")?.append(home);
