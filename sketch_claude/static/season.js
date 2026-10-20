// The Season Planner: the season's arc, its threads and its episodes in one place, and the tools to
// turn an outline into a script -- a skeleton to write into, or a DeepSeek draft -- then open it in
// the Episode Director. Its checks read the scripts themselves: who talks, how often each quirk
// shows, which threads go quiet, and how the drama and the comedy rise and fall over the season.

const $ = (s, el = document) => el.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const status = (s) => ($("#status").textContent = s);
const P = { season: null, series: null, cover: null, dirty: false };
const SID = new URLSearchParams(location.search).get("season") || "season01";

async function boot() {
  P.series = await (await fetch("/api/series")).json();
  P.season = await (await fetch(`/api/season/${SID}`)).json();
  $("#title").textContent = `${P.series.title}: ${P.season.title}`;
  document.title = `${P.season.title} - Season Planner`;
  $("#arc").value = P.season.arc;
  $("#arc").oninput = () => { P.season.arc = $("#arc").value; dirty(); };
  $("#save").onclick = save;
  renderThemes(); renderCast(); renderEpisodes(); renderThreads(); renderCurve();
  await refreshCoverage();
  window.addEventListener("beforeunload", (e) => { if (P.dirty) { e.preventDefault(); e.returnValue = ""; } });
}
function dirty() { P.dirty = true; status("Unsaved changes"); }
async function save() {
  const r = await fetch(`/api/season/${SID}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(P.season) });
  const j = await r.json();
  if (r.ok) { P.dirty = false; status(`Saved${j.kept ? "; the previous plan is kept as " + j.kept : ""}`); } else status(`Save failed: ${j.error}`);
}

function renderThemes() {
  const w = P.series.writers_room;
  $("#themes").innerHTML = `<p class="muted small">${esc(w.never_on_screen)}</p>` +
    w.themes.map((t) => `<p style="font-size:12.5px;margin:6px 0">${esc(t)}</p>`).join("") +
    `<h2>House rules</h2>` + w.rules.map((t) => `<p style="font-size:12.5px;margin:6px 0">• ${esc(t)}</p>`).join("");
}
function renderCast() {
  $("#cast").innerHTML = Object.entries(P.series.cast).map(([k, d]) => `<div class="c" style="border-color:${d.colour}"><b>${esc(d.name)}</b>, ${esc(d.role)}<br>
    <span class="muted">${esc(d.quirk || "")}</span>${d.secret ? `<br><i class="muted">${esc(d.secret)}</i>` : ""}</div>`).join("");
}

function renderEpisodes() {
  $("#eps").innerHTML = P.season.episodes.map((e, i) => {
    const t = e.tone || { drama: 0.5, comedy: 0.5 };
    return `<div class="ep" data-i="${i}">
      <header><span class="n">${esc(e.number)}</span><b>${esc(e.title)}</b><span class="grow"></span><span class="badge ${esc(e.status)}" data-badge="${i}">${esc(e.status)}</span></header>
      <p>${esc(e.logline)}</p>
      <p><span class="lab">A</span> ${esc(e.plots?.A || "")}</p><p><span class="lab">B</span> ${esc(e.plots?.B || "")}</p><p><span class="lab">C</span> ${esc(e.plots?.C || "")}</p>
      <p><span class="lab">The dome becomes</span> ${esc(e.dome_program || "")}</p>
      <p><span class="lab">Under it (never said)</span> ${esc(e.hidden_lesson || "")}</p>
      <p><span class="lab">Ends on</span> ${esc(e.cliffhanger || "")}</p>
      <div class="tone" title="drama ${Math.round(t.drama * 100)}% / comedy ${Math.round(t.comedy * 100)}%"><i style="width:${t.drama * 100}%"></i><i style="width:${t.comedy * 100}%"></i></div>
      <div class="row"><button data-edit="${i}">Edit outline</button><button data-open="${e.id}">Open in Director</button>
        <button data-skel="${e.id}" title="An episode file from this outline, to write into">Skeleton</button>
        <button data-draft="${e.id}" title="DeepSeek writes the whole episode from the bible, the season plan and this outline">Draft with DeepSeek</button></div>
      <div class="edit" id="edit-${i}">
        <label>Title <input data-f="title" value="${esc(e.title)}"></label>
        <label>Logline <textarea data-f="logline" rows="3">${esc(e.logline)}</textarea></label>
        <label>A plot <textarea data-f="plots.A" rows="2">${esc(e.plots?.A || "")}</textarea></label>
        <label>B plot <textarea data-f="plots.B" rows="2">${esc(e.plots?.B || "")}</textarea></label>
        <label>C plot <textarea data-f="plots.C" rows="2">${esc(e.plots?.C || "")}</textarea></label>
        <label>The dome becomes <input data-f="dome_program" value="${esc(e.dome_program || "")}"></label>
        <label>Hidden lesson <input data-f="hidden_lesson" value="${esc(e.hidden_lesson || "")}"></label>
        <label>Cliffhanger <input data-f="cliffhanger" value="${esc(e.cliffhanger || "")}"></label>
        <label>Drama <input type="range" min="0" max="100" data-f="tone" value="${Math.round(t.drama * 100)}"></label>
      </div></div>`;
  }).join("");
  document.querySelectorAll("[data-edit]").forEach((b) => (b.onclick = () => { const el = $(`#edit-${b.dataset.edit}`); el.style.display = el.style.display === "block" ? "none" : "block"; }));
  document.querySelectorAll(".edit [data-f]").forEach((inp) => (inp.oninput = () => {
    const e = P.season.episodes[+inp.closest(".ep").dataset.i], f = inp.dataset.f;
    if (f === "tone") { const d = +inp.value / 100; e.tone = { drama: d, comedy: 1 - d }; renderCurve(); }
    else if (f.startsWith("plots.")) { e.plots ||= {}; e.plots[f.slice(6)] = inp.value; }
    else e[f] = inp.value;
    dirty();
  }));
  document.querySelectorAll("[data-open]").forEach((b) => (b.onclick = () => window.open(`/director?episode=${b.dataset.open}`, "_blank")));
  document.querySelectorAll("[data-skel]").forEach((b) => (b.onclick = () => make("skeleton", b.dataset.skel)));
  document.querySelectorAll("[data-draft]").forEach((b) => (b.onclick = () => make("draft", b.dataset.draft)));
}

async function make(what, eid) {
  if (P.dirty) await save();
  const has = P.cover?.episodes.find((x) => x.id === eid)?.scripted;
  if (has && !confirm(`${eid} already has a script. Keep it as a version and make a new ${what}?`)) return;
  status(what === "draft" ? `DeepSeek is writing ${eid}... (a minute or two)` : `Making the skeleton for ${eid}...`);
  const r = await fetch(`/api/season/${SID}/${what}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ episode: eid, replace: true }) });
  const j = await r.json();
  if (!r.ok) { status(`${what} failed: ${j.error}`); return; }
  const e = P.season.episodes.find((x) => x.id === eid);
  if (e && e.status !== "scripted") { e.status = what === "draft" ? "draft" : "skeleton"; await save(); renderEpisodes(); }
  status(`${eid}: ${j.beats} beats${j.notes?.length ? `; ${j.notes.length} beats dropped as unplayable` : ""}. Open it in the Director to time, watch and edit.`);
  refreshCoverage();
}

function renderThreads() {
  const S = P.season;
  $("#threads").innerHTML = `<tr><th>Thread</th>${S.episodes.map((e) => `<th title="${esc(e.title)}">${esc(e.number)}</th>`).join("")}</tr>` +
    S.threads.map((t, ti) => `<tr><th style="text-align:left" title="${esc(t.about)}">${esc(t.name)}<br><span class="muted">${esc(t.owner)} · ${esc(t.kind)}</span></th>` +
      S.episodes.map((e, ei) => { const v = e.threads?.[t.id] || ""; return `<td contenteditable data-t="${ti}" data-e="${ei}" class="${v ? "" : "empty"}">${esc(v)}</td>`; }).join("") + `</tr>`).join("");
  $("#threads").querySelectorAll("td[contenteditable]").forEach((td) => (td.oninput = () => {
    const e = S.episodes[+td.dataset.e], t = S.threads[+td.dataset.t];
    e.threads ||= {};
    const v = td.textContent.trim();
    if (v) e.threads[t.id] = v; else delete e.threads[t.id];
    td.classList.toggle("empty", !v);
    dirty();
  }));
}

function renderCurve() {
  const eps = P.season.episodes, n = eps.length, x = (i) => 30 + i * (940 / Math.max(1, n - 1));
  const line = (key, col) => `<polyline fill="none" stroke="${col}" stroke-width="3" points="${eps.map((e, i) => `${x(i)},${110 - (e.tone?.[key] ?? 0.5) * 100}`).join(" ")}"/>` +
    eps.map((e, i) => `<circle cx="${x(i)}" cy="${110 - (e.tone?.[key] ?? 0.5) * 100}" r="4" fill="${col}"/>`).join("");
  $("#curve").innerHTML = `<line x1="0" x2="1000" y1="60" y2="60" stroke="#333"/>` + line("drama", "#d0566a") + line("comedy", "#e0c25a") +
    eps.map((e, i) => `<text x="${x(i)}" y="118" fill="#9a978f" font-size="10" text-anchor="middle">${esc(e.number)}</text>`).join("");
}

async function refreshCoverage() {
  P.cover = await (await fetch(`/api/season/${SID}/coverage`)).json();
  $("#warnings").innerHTML = P.cover.warnings.map((w) => `<p class="warn">⚠ ${esc(w)}</p>`).join("") || `<p class="muted">No gaps.</p>`;
  const cast = Object.keys(P.series.cast), Q = ["scenes", "thought", "vision", "frags", "sideeye", "earring", "stomp", "meme"];
  const QL = { scenes: "scenes", thought: "Hank's spirals", vision: "Cody's visions", frags: "stop-and-go lines", sideeye: "Maya's side-eyes", earring: "Jet's earring", stomp: "Krystal's foot", meme: "meme hits" };
  const maxL = Math.max(1, ...P.cover.episodes.flatMap((e) => Object.values(e.lines)));
  const heat = (v) => v ? `background:rgba(91,156,255,${0.15 + 0.6 * v / maxL})` : "";
  $("#cover").innerHTML = `<tr><th>Lines</th>${P.cover.episodes.map((e) => `<th>${esc(e.number)}${e.scripted ? "" : "<br><span class='muted'>-</span>"}</th>`).join("")}</tr>` +
    cast.map((c) => `<tr><th style="text-align:left;color:${P.series.cast[c].colour}">${esc(P.series.cast[c].name)}</th>` +
      P.cover.episodes.map((e) => `<td style="${heat(e.lines[c] || 0)}">${e.scripted ? (e.lines[c] || 0) : ""}</td>`).join("") + `</tr>`).join("") +
    `<tr><th>Quirks and texture</th>${P.cover.episodes.map(() => "<th></th>").join("")}</tr>` +
    Q.map((q) => `<tr><th style="text-align:left">${QL[q]}</th>` + P.cover.episodes.map((e) => `<td>${e.scripted ? (e.quirks[q] ?? 0) : ""}</td>`).join("") + `</tr>`).join("");
  P.season.episodes.forEach((e, i) => { const row = P.cover.episodes[i]; const b = document.querySelector(`[data-badge="${i}"]`); if (b && row?.scripted && row.status) { b.textContent = row.status; b.className = `badge ${row.status}`; } });
}

boot().catch((e) => status(`Failed: ${e.message}`));
