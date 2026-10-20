// The Episode Director: its own copy of the dome's world, and everything for shooting an episode in
// it -- the timeline (scenes, storyboard, shots, dialogue, action, sound, graphics), a transport that
// plays from anywhere, an inspector that edits any beat, the script, the cast, an analysis of the
// cut, free cameras (orbit, walk, drone, automated moves) and the frame-accurate render.

import { createWorld } from "/static/world.js";
import { Cine, makeShots, fovForLens, fmtTime } from "/static/cine.js";
import { EpisodeSet } from "/static/set.js";
import { Engine, ACTS, MOVES, SHOT_KINDS } from "/static/engine.js";
import { clock } from "/static/clock.js";

const $ = (s, el = document) => el.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const tfmt = (s) => `${Math.floor(s / 60)}:${(s % 60).toFixed(1).padStart(4, "0")}`;
const status = (s) => ($("#status").textContent = s);

const TRACKS = [["ruler", "", 18], ["scenes", "Scenes", 22], ["board", "Storyboard", 48], ["shots", "Shots", 24], ["dialogue", "Dialogue", 30],
                ["action", "Action", 20], ["sound", "Sound", 20], ["graphics", "Graphics", 20]];
const ACTION_KINDS = new Set(["walk", "act", "face", "gag", "build", "view"]);
const GRAPHIC_KINDS = new Set(["card", "meme", "figure", "lower", "credits"]);

const D = { ep: null, series: null, engine: null, world: null, cine: null, tl: null, sel: null, t: 0, zoom: 14, thumbs: [], freeCam: false, busy: false, dirty: false };

async function boot() {
  const qs = new URLSearchParams(location.search);
  const epId = qs.get("episode") || "s01e01";
  D.series = await (await fetch("/api/series")).json();
  const list = await (await fetch("/api/episodes")).json();
  $("#episode").innerHTML = list.map((e) => `<option value="${e.id}" ${e.id === epId ? "selected" : ""}>${esc(e.number)}: ${esc(e.title)}</option>`).join("");
  $("#episode").onchange = () => { location.search = `?episode=${$("#episode").value}`; };
  D.ep = await (await fetch(`/api/episode/${epId}`)).json();
  document.title = `${D.ep.number} ${D.ep.title} - Episode Director`;
  let spec = {};
  try { spec = JSON.parse(qs.get("spec") || "{}"); } catch { spec = {}; }
  D.world = await createWorld($("#gl"), spec);
  sizeCanvas();
  new ResizeObserver(sizeCanvas).observe($("#frame"));
  D.cine = new Cine(D.world);
  D.cine.aspect = "2.39";
  D.cine.guides.thirds = false;
  D.cine.setLens(35);
  const setData = await D.world.api("/api/set", { spec: D.world.S.spec });
  const set = new EpisodeSet(D.world, setData);
  D.engine = new Engine(D.world, D.cine, set, D.series, setData.figures);
  wire();
  renderCastTab(); renderCameraTab(); renderRenderTab();
  loop();
  if (qs.get("autorender")) {        // a headless render job opened this page
    await compile();
    const res = await D.engine.render(D.ep.beats, meta(), (s) => { status(s); console.log("[render] " + s); }, qs.get("draft") === "1");
    console.log("[render-done] " + JSON.stringify(res || {}));
    return;
  }
  await compile();
  await seek(0);
}

function sizeCanvas() {
  if (D.engine?.mode === "render") return;
  const f = $("#frame"), dpr = Math.min(devicePixelRatio, 2);
  D.world.resize(Math.max(320, Math.round(f.clientWidth * dpr)), Math.max(180, Math.round(f.clientHeight * dpr)));
}

function meta() {
  const s = D.series, e = D.ep;
  return { slug: `${s.title}-${e.id}-${e.title}`.toLowerCase().replace(/[^a-z0-9]+/g, "-"), title: `${s.title}, ${e.number}: ${e.title}`,
           logline: e.logline, cast: Object.values(s.cast).map((d) => `${d.name}, ${d.role} (voice: ${d.voice})`),
           copy: `${s.title}: ${s.logline}`, tags: "#sitcom #comedy #familycomedy #diy #homeimprovement #geodesicdome #tinyhouse" };
}

// ------------------------------------------------------------------ the loop: draw whenever nothing else is driving
function loop() {
  const tick = () => {
    const mode = D.engine?.mode;
    if (D.engine && mode !== "play" && mode !== "render" && mode !== "dry" && !D.busy) D.world.renderFrame(0, clock.now());
    const s = D.engine?.timeline?.shots?.filter((x) => x.t <= D.t + 1e-6).pop();
    $("#shotinfo").textContent = s ? `${s.label}${s.lens ? "  " + s.lens + " mm" : ""}  ·  ${mode}` : mode || "";
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

// ------------------------------------------------------------------ compile, seek, play
async function compile() {
  D.busy = true;
  try {
    const tl = await D.engine.compile(D.ep.beats, status);
    D.tl = tl;
    $("#t-total").textContent = tfmt(tl.total);
    status(`${tfmt(tl.total)} runtime: ${tl.scenes.length} scenes, ${tl.shots.length} shots, ${tl.marks.filter((m) => m.k === "line").length} lines (timed in ${tl.took.toFixed(1)} s)`);
    D.thumbs = [];
    drawTimeline(); renderScript(); renderStats(); renderCastTab();
  } catch (e) { status(`Could not time the episode: ${e.message}`); console.error(e); }
  D.busy = false;
}

async function seek(t) {
  if (!D.tl) return;
  t = Math.max(0, Math.min(D.tl.total - 0.01, t));
  D.engine.pause(); setPlayIcon(false);
  D.busy = true;
  await D.engine.seek(D.ep.beats, t);
  D.busy = false;
  setTime(t);
}

function setTime(t) {
  D.t = t;
  $("#t-now").textContent = tfmt(t);
  $("#tl-head").style.left = `${t * D.zoom}px`;
  if ($("#tl-follow").checked) {
    const sc = $("#tl-scroll"), x = t * D.zoom;
    if (x < sc.scrollLeft + 40 || x > sc.scrollLeft + sc.clientWidth - 80) sc.scrollLeft = x - sc.clientWidth * 0.3;
  }
}

async function togglePlay() {
  if (!D.tl) return;
  if (D.engine.mode === "play") { D.engine.pause(); setPlayIcon(false); return; }
  if (D.freeCam) { D.freeCam = false; D.world.controls.enabled = false; $("#c-free")?.classList.remove("on"); }
  setPlayIcon(true);
  const res = await D.engine.play(D.ep.beats, D.t, (t) => setTime(t));
  setPlayIcon(false);
  if (res === "ended") setTime(D.tl.total);
}
function setPlayIcon(on) { $("#t-play").innerHTML = on ? "&#10074;&#10074;" : "&#9654;"; }

function shotAt(dir) {
  const shots = D.tl?.shots || [];
  if (dir > 0) return shots.find((s) => s.t > D.t + 0.05)?.t ?? D.t;
  const prev = shots.filter((s) => s.t < D.t - 0.3);
  return prev.length ? prev[prev.length - 1].t : 0;
}

// ------------------------------------------------------------------ the timeline
function colourOf(who) { return D.series.cast[who]?.colour || "#888"; }

function drawTimeline() {
  const tl = D.tl, Z = D.zoom, W = Math.max(400, tl.total * Z + 120);
  const canvas = $("#tl-canvas"), labels = $("#tl-labels");
  canvas.style.width = `${W}px`;
  canvas.querySelectorAll(".tl-track").forEach((e) => e.remove());
  labels.innerHTML = "";
  let y = 0;
  const track = (key, label, h) => {
    const d = document.createElement("div"); d.className = "tl-track"; d.style.top = `${y}px`; d.style.height = `${h}px`; d.dataset.key = key;
    canvas.append(d);
    const l = document.createElement("div"); l.textContent = label; l.style.setProperty("--h", `${h}px`); labels.append(l);
    y += h; return d;
  };
  const blk = (tr, t0, t1, text, colour, beat, title) => {
    const b = document.createElement("div"); b.className = "blk"; b.style.left = `${t0 * Z}px`; b.style.width = `${Math.max(3, (t1 - t0) * Z - 1)}px`;
    b.style.background = colour; b.textContent = text; b.title = title || text;
    if (beat !== undefined && beat !== null) { b.dataset.beat = beat; if (D.sel === beat) b.classList.add("sel"); }
    tr.append(b); return b;
  };
  const T = {};
  for (const [k, label, h] of TRACKS) T[k] = track(k, label, h);
  const step = Z > 60 ? 1 : Z > 25 ? 5 : Z > 10 ? 10 : 30;
  for (let s = 0; s <= tl.total; s += step) { const t = document.createElement("div"); t.className = "tick"; t.style.left = `${s * Z}px`; t.textContent = fmtTime(s); T.ruler.append(t); }
  tl.scenes.forEach((s, i) => blk(T.scenes, s.t, s.end, s.name, ["#c9a46b", "#8fb0c9", "#a9c48b", "#d6a0a0", "#b8a3d6", "#d8cd7c"][i % 6], s.i, `${s.name}  ${tfmt(s.t)} - ${tfmt(s.end)}`));
  tl.shots.forEach((s, i) => {
    const b = blk(T.shots, s.t, s.t + s.shown, `${s.label}`, s.kind === "move" ? "#e0a36b" : s.kind === "meme" ? "#ff7a7a" : "#9db8d9", s.beat,
                  `Shot ${i + 1}: ${s.label}${s.lens ? ", " + s.lens + " mm" : ""}  ${tfmt(s.t)}, ${s.shown.toFixed(1)} s on screen`);
    const th = blk(T.board, s.t, s.t + s.shown, "", "#000", s.beat, b.title);
    th.classList.add("thumb");
    if (D.thumbs[i]) th.innerHTML = `<img src="${D.thumbs[i]}">`;
    th.dataset.shot = i;
  });
  for (const m of tl.marks) {
    if (m.k === "line") blk(T.dialogue, m.t0, m.t1, `${D.series.cast[m.who].name.split(" ")[0]}: ${m.text}`, colourOf(m.who), m.i, `${tfmt(m.t0)}  ${m.text}`);
    else if (ACTION_KINDS.has(m.k)) {
      const b = D.ep.beats[m.i];
      blk(T.action, m.t0, Math.max(m.t1, m.t0 + 0.6), `${m.k}${b.who ? " " + b.who : ""}${b.act ? " " + b.act : ""}${b.name ? " " + b.name : ""}`, "#c7c2b6", m.i);
    } else if (GRAPHIC_KINDS.has(m.k)) {
      const b = D.ep.beats[m.i], secs = m.k === "lower" ? 3.8 : m.k === "figure" ? (b.secs || 4) : Math.max(m.t1 - m.t0, b.secs || 0);
      blk(T.graphics, m.t0, m.t0 + Math.max(0.6, secs), D.engine.fillText(`${m.k}: ${b.text || b.big || b.who || b.style || ""}`), m.k === "meme" ? "#ff9a9a" : "#e6d27a", m.i);
    }
  }
  for (const e of tl.events) if (e.kind === "band") blk(T.sound, e.t, e.t + Math.max(0.4, e.dur || 0.4), e.fn, e.fn === "theme" ? "#b7a1e6" : "#a3d1c4", null);
  canvas.style.height = `${y}px`;
  $("#tl-head").style.height = `${y}px`;
  $("#tl-legend").innerHTML = Object.entries(D.series.cast).map(([, d]) => `<span><i style="background:${d.colour}"></i>${esc(d.name.split(" ")[0])}</span>`).join("");
  setTime(D.t);
}

function timeAtEvent(ev) { return (ev.clientX - $("#tl-canvas").getBoundingClientRect().left) / D.zoom; }

// ------------------------------------------------------------------ the inspector
function selectBeat(i, jump = true) {
  D.sel = i;
  document.querySelectorAll(".blk.sel").forEach((e) => e.classList.remove("sel"));
  document.querySelectorAll(`.blk[data-beat="${i}"]`).forEach((e) => e.classList.add("sel"));
  document.querySelectorAll(".script .ln").forEach((e) => e.classList.toggle("sel", +e.dataset.beat === i));
  showTab("inspect");
  renderInspector();
  const m = D.tl?.marks.find((x) => x.i === i);
  if (jump && m) seek(m.t0 + 0.05);
}

function renderInspector() {
  const box = $("#tab-inspect"), i = D.sel, b = D.ep.beats[i];
  if (b === undefined) { box.innerHTML = `<p class="muted">Click a block on the timeline, or a line in the Script, to see and edit its beat.</p>`; return; }
  const m = D.tl?.marks.find((x) => x.i === i);
  const cast = Object.keys(D.series.cast);
  const opt = (list, v) => list.map((x) => `<option ${x === v ? "selected" : ""}>${x}</option>`).join("");
  let html = `<h3>Beat ${i + 1} of ${D.ep.beats.length}: ${esc(b.k)}</h3>`;
  if (m) html += `<p class="muted">${tfmt(m.t0)} to ${tfmt(m.t1)} (${(m.t1 - m.t0).toFixed(2)} s)</p>`;
  if (b.k === "line") {
    const c = b.cam || {};
    html += `<label><span>Who</span><select id="f-who">${opt(cast, b.who)}</select></label>
      <label><span>Line</span></label><textarea id="f-text" rows="4">${esc(b.text)}</textarea>
      <p class="muted">Spoken as: ${esc(D.engine.fillText(b.text))}</p>
      <label><span>Action</span><select id="f-act">${opt(["", ...ACTS], b.act || "")}</select></label>
      <label><span>Then</span><select id="f-after">${opt(["", ...ACTS], b.after || "")}</select></label>
      <label><span>Pause after</span><input id="f-pad" type="number" step="0.05" value="${b.pad ?? 0.25}"> s</label>
      <h3>Camera</h3>
      <label><span>Shot</span><select id="f-kind">${opt(["(keep)", ...SHOT_KINDS], "(keep)")}</select></label>
      <p class="muted">Now: ${esc(D.engine.label(b.cam) || "the shot before carries on")}</p>
      <label><span>Subject</span><select id="f-cwho">${opt(["", ...cast], c.who || c.a || c.over || "")}</select></label>
      <label><span>Toward / with</span><select id="f-ctoward">${opt(["", ...cast], c.toward || c.b || c.at || "")}</select></label>
      <label><span>Size</span><select id="f-size">${opt(["close", "medium", "wide"], c.size || "medium")}</select></label>
      <label><span>Lens</span><input id="f-lens" type="number" step="1" min="12" max="200" value="${c.lens || ""}" placeholder="auto"> mm</label>
      <label><span>Move</span><select id="f-move">${opt(MOVES, c.move || "hold")}</select></label>`;
  }
  html += `<details ${b.k === "line" ? "" : "open"}><summary>All of the beat (JSON)</summary><textarea id="f-json" rows="9" spellcheck="false">${esc(JSON.stringify(b, null, 1))}</textarea></details>
    <div class="row"><button id="i-apply" class="primary">Apply and re-time</button><button id="i-play">Play from here</button></div>
    <div class="row"><button id="i-up">Move up</button><button id="i-down">Move down</button><button id="i-dup">Duplicate</button><button id="i-line">+ Line after</button><button id="i-del">Delete</button></div>
    <div class="row"><button id="i-save">Save episode</button><button id="i-revert">Revert to saved</button></div>`;
  box.innerHTML = html;
  const read = () => {
    let nb;
    try { nb = JSON.parse($("#f-json").value); } catch (e) { status(`The JSON does not parse: ${e.message}`); return null; }
    if (b.k === "line") {
      nb.who = $("#f-who").value; nb.text = $("#f-text").value; nb.pad = +$("#f-pad").value;
      if ($("#f-act").value) nb.act = $("#f-act").value; else delete nb.act;
      if ($("#f-after").value) nb.after = $("#f-after").value; else delete nb.after;
      const kind = $("#f-kind").value, who = $("#f-cwho").value, to = $("#f-ctoward").value, lens = +$("#f-lens").value || undefined;
      if (kind !== "(keep)") {
        const c = { kind };
        if (kind === "single") Object.assign(c, { who: who || nb.who, size: $("#f-size").value }, to ? { toward: to } : {});
        if (kind === "two") Object.assign(c, { a: who || nb.who, b: to || Object.keys(D.series.cast).find((x) => x !== nb.who) });
        if (kind === "ots") Object.assign(c, { over: who || nb.who, at: to || nb.who });
        if (kind === "wide") Object.assign(c, { who: [who || nb.who, ...(to ? [to] : [])] });
        if (kind === "move") Object.assign(c, { move: $("#f-move").value, subject: who || nb.who });
        if (lens) c.lens = lens;
        nb.cam = c;
      } else if (b.cam && lens) nb.cam = { ...b.cam, lens };
    }
    return nb;
  };
  const redo = async (sel) => { D.dirty = true; await compile(); selectBeat(sel); };
  $("#i-apply").onclick = () => { const nb = read(); if (!nb) return; D.ep.beats[i] = nb; redo(i); };
  $("#i-play").onclick = async () => { const m2 = D.tl.marks.find((x) => x.i === i); if (m2) { await seek(m2.t0); togglePlay(); } };
  const move = (d) => { const j = i + d; if (j < 0 || j >= D.ep.beats.length) return; const a = D.ep.beats; [a[i], a[j]] = [a[j], a[i]]; redo(j); };
  $("#i-up").onclick = () => move(-1);
  $("#i-down").onclick = () => move(1);
  $("#i-dup").onclick = () => { D.ep.beats.splice(i + 1, 0, JSON.parse(JSON.stringify(b))); redo(i + 1); };
  $("#i-line").onclick = () => { D.ep.beats.splice(i + 1, 0, { k: "line", who: b.who || "hank", text: "New line.", act: "talk" }); redo(i + 1); };
  $("#i-del").onclick = async () => { if (!confirm("Delete this beat?")) return; D.ep.beats.splice(i, 1); D.dirty = true; D.sel = null; await compile(); renderInspector(); };
  $("#i-save").onclick = saveEpisode;
  $("#i-revert").onclick = async () => { D.ep = await (await fetch(`/api/episode/${D.ep.id}`)).json(); D.dirty = false; await compile(); renderInspector(); };
}

async function saveEpisode() {
  const r = await fetch(`/api/episode/${D.ep.id}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(D.ep) });
  const j = await r.json();
  status(r.ok ? `Saved ${D.ep.id}${j.kept ? "; the previous version is kept as " + j.kept : ""}` : `Save failed: ${j.error}`);
  if (r.ok) D.dirty = false;
}

// ------------------------------------------------------------------ the script
function renderScript() {
  const f = ($("#sc-filter").value || "").toLowerCase();
  $("#script").innerHTML = D.ep.beats.map((b, i) => {
    const m = D.tl?.marks.find((x) => x.i === i), t = m ? fmtTime(m.t0) : "";
    if (b.k === "scene") return `<div class="ln scene" data-beat="${i}"><span class="t">${t}</span><span>${esc(b.name)}</span></div>`;
    if (b.k === "line") {
      const text = D.engine.fillText(b.text);
      if (f && !(`${b.who} ${text}`.toLowerCase().includes(f))) return "";
      return `<div class="ln" data-beat="${i}"><span class="t">${t}</span><span><span class="who" style="color:${colourOf(b.who)}">${esc(D.series.cast[b.who].name.split(" ")[0].toUpperCase())}</span>${b.act ? ` <i class="muted">(${esc(b.act)})</i>` : ""} ${esc(text)}</span></div>`;
    }
    if (f) return "";
    const what = b.k === "card" ? `CARD: ${b.text}` : b.k === "meme" ? `MEME (${b.style}): ${b.text || b.who || ""}` : b.k === "cam" ? `SHOT: ${D.engine.label(b.cam)}` :
                 b.k === "walk" ? `${b.who} walks` : b.k === "act" ? `${b.who}: ${b.act}` : b.k === "sfx" || b.k === "music" ? `SOUND: ${b.name}` : b.k;
    return `<div class="ln" data-beat="${i}"><span class="t">${t}</span><span class="muted">${esc(what)}</span></div>`;
  }).join("");
  $("#script").querySelectorAll(".ln").forEach((e) => (e.onclick = () => selectBeat(+e.dataset.beat)));
}

// ------------------------------------------------------------------ the cast
function castFigures() {
  const out = {};
  for (const k of Object.keys(D.series.cast)) out[k] = { lines: 0, words: 0, secs: 0, scenes: new Set() };
  if (!D.tl) return out;
  for (const m of D.tl.marks) {
    const b = D.ep.beats[m.i];
    if (m.k === "scene") for (const w of Object.keys(b.place || {})) if (!(b.hide || []).includes(w)) out[w]?.scenes.add(b.name);
    if (m.k === "line") { const o = out[m.who]; o.lines++; o.words += m.text.split(/\s+/).length; o.secs += m.t1 - m.t0; }
  }
  return out;
}
function renderCastTab() {
  const f = castFigures();
  $("#cast").innerHTML = `<h3>${esc(D.series.title)}</h3><p class="muted">${esc(D.series.logline)}</p><p class="muted">Rated ${esc(D.series.rating)}. ${esc(D.series.tone)}</p>` +
    Object.entries(D.series.cast).map(([k, d]) => `<div style="border-left:4px solid ${d.colour};padding:4px 8px;margin:8px 0;background:#1a1b1f">
      <button data-hear="${k}" style="float:right">Hear</button><b>${esc(d.name)}</b><br><span class="muted">${esc(d.role)}</span><br>
      <span class="muted">voice ${esc(d.voice)} ${esc(d.rate)}</span><br>
      ${f[k].lines} lines, ${f[k].words} words, ${f[k].secs.toFixed(1)} s talking, in ${f[k].scenes.size} scenes</div>`).join("");
  $("#cast").querySelectorAll("[data-hear]").forEach((b) => (b.onclick = async () => {
    const d = D.series.cast[b.dataset.hear], v = D.engine.voices;
    await v.ac.resume();
    const buf = await v.fetchLine(d, `Hi. I'm ${d.name.split(" ")[0]}.`);
    const s = v.ac.createBufferSource(); s.buffer = buf; s.connect(v.master); s.start();
  }));
}

// ------------------------------------------------------------------ analysis
function renderStats() {
  const tl = D.tl;
  if (!tl) return;
  const lines = tl.marks.filter((m) => m.k === "line");
  const wordsN = lines.reduce((a, m) => a + m.text.split(/\s+/).length, 0);
  const talk = lines.reduce((a, m) => a + (m.t1 - m.t0), 0);
  const shown = tl.shots.map((s) => s.shown).sort((a, b) => a - b);
  const asl = shown.reduce((a, b) => a + b, 0) / Math.max(1, shown.length);
  const median = shown[Math.floor(shown.length / 2)] || 0;
  // dead air: two seconds or more with nobody speaking and no card or meme on screen
  const busy = [...lines.map((m) => [m.t0, m.t1]), ...tl.marks.filter((m) => ["card", "meme", "credits", "build"].includes(m.k)).map((m) => [m.t0, m.t1])].sort((a, b) => a[0] - b[0]);
  const gaps = []; let end = 0;
  for (const [a, b] of busy) { if (a - end >= 2) gaps.push([end, a]); end = Math.max(end, b); }
  if (tl.total - end >= 2) gaps.push([end, tl.total]);
  const f = castFigures(), maxS = Math.max(...Object.values(f).map((x) => x.secs), 1);
  const kinds = {}; for (const s of tl.shots) { const k = s.kind === "move" ? s.move || "move" : s.kind; kinds[k] = (kinds[k] || 0) + 1; }
  const maxK = Math.max(...Object.values(kinds), 1);
  const kv = (k, v) => `<div class="kv"><span>${k}</span><b>${v}</b></div>`;
  $("#stats").innerHTML = `<h3>The cut</h3>` + kv("Runtime", tfmt(tl.total)) + kv("Scenes", tl.scenes.length) + kv("Shots", tl.shots.length) +
    kv("Average shot", `${asl.toFixed(1)} s (median ${median.toFixed(1)} s)`) + kv("Longest shot", `${(shown[shown.length - 1] || 0).toFixed(1)} s`) +
    kv("Lines", lines.length) + kv("Words", wordsN) + kv("Pace", `${(wordsN / (talk / 60 || 1)).toFixed(0)} words a minute while talking`) +
    kv("Talk time", `${talk.toFixed(0)} s (${(talk / tl.total * 100).toFixed(0)}% of the runtime)`) +
    kv("Dead air", gaps.length ? gaps.map(([a, b]) => `${fmtTime(a)} (${(b - a).toFixed(1)} s)`).join(", ") : "none over 2 s") +
    `<h3>Scenes</h3>` + tl.scenes.map((s) => `<div class="kv" style="cursor:pointer" data-t="${s.t}"><span>${esc(s.name)}</span><b>${fmtTime(s.t)} · ${(s.end - s.t).toFixed(0)} s</b></div>`).join("") +
    `<h3>Talking time</h3><div class="bars">` + Object.entries(f).map(([k, x]) => `<div class="b"><span style="width:62px">${esc(D.series.cast[k].name.split(" ")[0])}</span><i style="width:${x.secs / maxS * 190}px;background:${colourOf(k)}"></i><span class="muted">${x.secs.toFixed(0)} s</span></div>`).join("") + `</div>` +
    `<h3>Shots by kind</h3><div class="bars">` + Object.entries(kinds).sort((a, b) => b[1] - a[1]).map(([k, n]) => `<div class="b"><span style="width:90px">${esc(k)}</span><i style="width:${n / maxK * 160}px;background:#9db8d9"></i><span class="muted">${n}</span></div>`).join("") + `</div>` +
    `<p class="muted">Timed from the beats and the length of every recorded voice line: this is the cut the render will make.</p>`;
  $("#stats").querySelectorAll("[data-t]").forEach((e) => (e.onclick = () => seek(+e.dataset.t + 0.05)));
}

// ------------------------------------------------------------------ the free camera
function renderCameraTab() {
  const cine = D.cine, shots = makeShots(D.world.THREE);
  $("#camera").innerHTML = `<div class="dir">
    <h3>Camera</h3>
    <p class="muted">Paused, the viewer shows the episode's own shot. A free camera looks round the set instead; Play goes back to the cut.</p>
    <div class="row"><button id="c-free">Free camera (orbit)</button><button data-m="walk">Walk</button><button data-m="drone">Drone</button></div>
    <p class="muted">Orbit: drag, right-drag to pan, wheel to zoom. Walk: WASD, mouse to look, Shift to run. Drone: WASD, E up, Q down, wheel for speed. Esc to stop.</p>
    <label><span>Lens</span><input type="range" id="c-lens" min="14" max="135" value="35"><output id="c-lens-v">35 mm</output></label>
    <label><span>Frame</span><select id="c-aspect"><option value="2.39" selected>2.39 : 1 scope</option><option value="16:9">16:9</option><option value="1.85">1.85 : 1</option><option value="9:16">9:16 phone</option><option value="off">full</option></select></label>
    <label><input type="checkbox" id="c-thirds"> Rule-of-thirds grid</label><label><input type="checkbox" id="c-safe"> Safe areas</label><label><input type="checkbox" id="c-centre"> Centre mark</label>
    <h3>Automated moves</h3><p class="muted">From the free camera's position, aimed at its orbit centre.</p><div class="moves" id="c-moves"></div>
    <label><span>Length</span><input type="range" id="c-dur" min="2" max="20" value="7"><output id="c-dur-v">7 s</output></label>
  </div>`;
  const free = (on) => { D.freeCam = on; D.world.controls.enabled = on; $("#c-free").classList.toggle("on", on); if (on) { D.engine.pause(); cine.stop(); } };
  $("#c-free").onclick = () => free(!D.freeCam);
  $("#camera").querySelectorAll("[data-m]").forEach((b) => (b.onclick = () => { free(true); cine.enter(b.dataset.m); }));
  $("#c-lens").oninput = () => { cine.setLens(+$("#c-lens").value); $("#c-lens-v").textContent = `${$("#c-lens").value} mm`; };
  $("#c-aspect").onchange = () => (cine.aspect = $("#c-aspect").value);
  $("#c-thirds").onchange = (e) => (cine.guides.thirds = e.target.checked);
  $("#c-safe").onchange = (e) => (cine.guides.safe = e.target.checked);
  $("#c-centre").onchange = (e) => (cine.guides.centre = e.target.checked);
  $("#c-dur").oninput = () => ($("#c-dur-v").textContent = `${$("#c-dur").value} s`);
  for (const name of MOVES.filter((m) => m !== "hold")) {
    const b = document.createElement("button"); b.textContent = name;
    b.onclick = () => {
      free(true);
      const o = { from: D.world.persp.position.clone(), subject: D.world.controls.target.clone(), dur: +$("#c-dur").value, fov: fovForLens(cine.lens), radius: 8, height: 4 };
      cine.play(shots[name](o));
      const t0 = performance.now(), run = (ts) => { D.world.renderFrame(1 / 60, clock.now()); if (cine.shot && performance.now() - t0 < o.dur * 1000 + 200) requestAnimationFrame(run); };
      requestAnimationFrame(run);
    };
    $("#c-moves").append(b);
  }
  // walk and drone run on the cine's own tick, driven here while the episode is paused
  const drive = () => { if (cine.mode === "walk" || cine.mode === "drone") D.world.renderFrame(1 / 60, clock.now()); requestAnimationFrame(drive); };
  requestAnimationFrame(drive);
}

// ------------------------------------------------------------------ render
function renderRenderTab() {
  $("#render").innerHTML = `<h3>Render the episode</h3>
    <p class="muted">Every frame at 1920x1080, 30 fps, in the 2.39 : 1 frame, with the voices and music mixed offline. The result is a
    release in a new numbered folder: the cut, a phone cut, captions, a thumbnail per scene and the description.</p>
    <div class="row"><button id="r-job" class="primary" title="Runs in a headless browser on this PC: it keeps going with this window hidden">Render (background job)</button>
      <button id="r-draft" title="The same, kept in tmp/ instead of the library">Rehearsal render</button></div>
    <div class="row"><button id="r-here" title="Renders in this tab: keep the tab on screen">Render in this tab</button><button id="r-stop">Stop</button></div>
    <p id="r-est" class="muted"></p>
    <div id="r-jobs"></div><h3>Made so far</h3><div id="r-outs"></div>`;
  const est = () => { if (D.tl) $("#r-est").textContent = `${tfmt(D.tl.total)} of episode is ${Math.round(D.tl.total * 30)} frames; at about 6 frames a second the render takes ${Math.round(D.tl.total * 30 / 6 / 60)} minutes.`; };
  est(); setInterval(est, 4000);
  const job = async (draft) => {
    if (D.dirty) await saveEpisode();
    await fetch("/api/episode-render", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ episode: D.ep.id, draft, spec: D.world.S.spec }) });
    pollJobs();
  };
  $("#r-job").onclick = () => job(false);
  $("#r-draft").onclick = () => job(true);
  $("#r-here").onclick = async () => { if (D.dirty) await saveEpisode(); D.busy = true; await D.engine.render(D.ep.beats, meta(), status, false); D.busy = false; pollJobs(); };
  $("#r-stop").onclick = () => { D.engine.stopped = true; };
  pollJobs();
}
let pollTimer = null;
async function pollJobs() {
  const jobs = (await (await fetch("/api/jobs")).json()).filter((j) => j.kind === "episode");
  $("#r-jobs").innerHTML = jobs.slice(0, 4).map((j) => `<div class="job"><b>${esc(j.state)}</b> <span class="muted">${Math.round(((j.ended || Date.now() / 1000) - j.started))} s</span>
    <pre>${esc(j.log.split("\n").filter(Boolean).slice(-3).join("\n"))}</pre>${j.output ? `<span class="muted">${esc(j.output)}</span>` : ""}</div>`).join("");
  const outs = (await (await fetch("/api/outputs")).json()).filter((o) => /level-with-me/.test(o.folder));
  $("#r-outs").innerHTML = outs.slice(-5).reverse().map((o) => `<div class="out"><b>${esc(o.folder.split("/").pop())}</b>${o.files.filter((f) => /\.(mp4|jpg|md|srt)$/i.test(f)).slice(0, 8).map((f) => `<a href="/api/file?path=${encodeURIComponent(f)}" target="_blank">${esc(f.split("/").pop())}</a>`).join("")}</div>`).join("") || `<p class="muted">Nothing yet.</p>`;
  clearTimeout(pollTimer);
  if (jobs.some((j) => j.state === "running")) pollTimer = setTimeout(pollJobs, 3000);
}

// ------------------------------------------------------------------ wiring
function showTab(t) {
  document.querySelectorAll("#tabs button").forEach((b) => b.classList.toggle("on", b.dataset.t === t));
  document.querySelectorAll(".tab").forEach((d) => d.classList.toggle("on", d.id === `tab-${t}`));
}
function wire() {
  document.querySelectorAll("#tabs button").forEach((b) => (b.onclick = () => showTab(b.dataset.t)));
  $("#t-play").onclick = togglePlay;
  $("#t-start").onclick = () => seek(0);
  $("#t-prev").onclick = () => seek(shotAt(-1) + 0.05);
  $("#t-next").onclick = () => seek(shotAt(1) + 0.05);
  $("#b-compile").onclick = compile;
  $("#b-board").onclick = storyboard;
  $("#sc-filter").oninput = renderScript;
  $("#tl-zoom").oninput = () => { D.zoom = +$("#tl-zoom").value; drawTimeline(); };
  $("#tl-fit").onclick = () => { D.zoom = Math.max(4, ($("#tl-scroll").clientWidth - 30) / (D.tl?.total || 60)); $("#tl-zoom").value = D.zoom; drawTimeline(); };
  const canvas = $("#tl-canvas");
  let drag = false;
  canvas.addEventListener("mousedown", (ev) => {
    const blk = ev.target.closest(".blk");
    if (blk && blk.dataset.beat !== undefined) { selectBeat(+blk.dataset.beat); return; }
    drag = true; setTime(Math.max(0, timeAtEvent(ev)));
  });
  window.addEventListener("mousemove", (ev) => { if (drag) setTime(Math.max(0, Math.min(D.tl?.total || 0, timeAtEvent(ev)))); });
  window.addEventListener("mouseup", () => { if (drag) { drag = false; seek(D.t); } });
  window.addEventListener("keydown", (ev) => {
    if (ev.target.closest("input, textarea, select")) return;
    if (D.cine.mode === "walk" || D.cine.mode === "drone") return;
    if (ev.code === "Space") { ev.preventDefault(); togglePlay(); }
    else if (ev.code === "ArrowRight") seek(D.t + (ev.shiftKey ? 5 : 1));
    else if (ev.code === "ArrowLeft") seek(D.t - (ev.shiftKey ? 5 : 1));
    else if (ev.code === "Home") seek(0);
    else if (ev.key === "]") seek(shotAt(1) + 0.05);
    else if (ev.key === "[") seek(shotAt(-1) + 0.05);
  });
  window.addEventListener("beforeunload", (e) => { if (D.dirty) { e.preventDefault(); e.returnValue = ""; } });
}

async function storyboard() {
  if (!D.tl) return;
  D.busy = true;
  status("Drawing the storyboard...");
  const times = D.tl.shots.map((s) => s.t + Math.min(0.6, s.shown / 2));
  D.thumbs = [];
  await D.engine.storyboard(D.ep.beats, times, [256, 108], (k, url) => {
    D.thumbs[k] = url;
    const el = document.querySelector(`.blk.thumb[data-shot="${k}"]`);
    if (el) el.innerHTML = `<img src="${url}">`;
    status(`Drawing the storyboard: ${k + 1} of ${times.length}`);
  });
  D.busy = false;
  status(`Storyboard: ${times.length} shots`);
  await seek(D.t);
}

boot().catch((e) => { status(`Failed: ${e.message}`); console.error(e); });
