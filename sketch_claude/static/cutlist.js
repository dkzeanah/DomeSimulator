// The visual cut list: one card per cut family -- the piece drawn to scale with every edge
// dimensioned, every corner's angle and every end's cut written on it, how many to cut, and the
// saw setup or group it shares -- then the sheets the plates nest on. Clicking a card lights up
// every piece of that family in the model. printCards() lays the same cards out on paper.

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

/** An SVG of a card's drawing (metres in, pixels out), y up, dimensions outside the outline. */
export function svgOf(d, U, w = 260, opt = {}) {
  if (!d || !d.poly || !d.poly.length) return "";
  const pts = [...d.poly, ...(d.inner || []), ...(d.lines || []).flat(), ...(d.notes || []).map((n) => n.at)];
  for (const h of d.holes || []) pts.push([h.c[0] - h.r, h.c[1] - h.r], [h.c[0] + h.r, h.c[1] + h.r]);
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const [x, y] of pts) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
  const bw = Math.max(x1 - x0, 1e-6), bh = Math.max(y1 - y0, 1e-6), pad = 34;
  const h = Math.max(90, Math.min(opt.maxH || 240, (w - 2 * pad) * bh / bw + 2 * pad));
  const s = Math.min((w - 2 * pad) / bw, (h - 2 * pad) / bh);
  const ox = (w - bw * s) / 2, oy = (h - bh * s) / 2;
  const X = (x) => ox + (x - x0) * s, Y = (y) => h - oy - (y - y0) * s;
  const P = (p) => `${X(p[0]).toFixed(1)},${Y(p[1]).toFixed(1)}`;
  const cx = d.poly.reduce((a, p) => a + p[0], 0) / d.poly.length, cy = d.poly.reduce((a, p) => a + p[1], 0) / d.poly.length;
  const fill = opt.fill || "#efe3cf";
  let out = `<svg class="cardsvg" viewBox="0 0 ${w} ${h.toFixed(0)}" width="${w}" height="${h.toFixed(0)}" xmlns="http://www.w3.org/2000/svg">`;
  out += `<polygon points="${d.poly.map(P).join(" ")}" fill="${fill}" stroke="#1d1b18" stroke-width="1.3"/>`;
  if (d.inner) out += `<polygon points="${d.inner.map(P).join(" ")}" fill="none" stroke="#1d1b18" stroke-width="0.8" stroke-dasharray="4 3"/>`;
  for (const [a, b] of d.lines || []) out += `<line x1="${X(a[0])}" y1="${Y(a[1])}" x2="${X(b[0])}" y2="${Y(b[1])}" stroke="#c45e29" stroke-width="1" stroke-dasharray="3 3"/>`;
  for (const hl of d.holes || []) out += `<circle cx="${X(hl.c[0])}" cy="${Y(hl.c[1])}" r="${(hl.r * s).toFixed(1)}" fill="#fff" stroke="#1d1b18" stroke-width="1.1"/>`;
  for (const dm of d.dims || []) {
    const ax = X(dm.a[0]), ay = Y(dm.a[1]), bx = X(dm.b[0]), by = Y(dm.b[1]);
    const L = Math.hypot(bx - ax, by - ay);
    if (L < 8) continue;
    let nx = -(by - ay) / L, ny = (bx - ax) / L;
    const mx = (ax + bx) / 2, my = (ay + by) / 2;
    if ((mx - X(cx)) * nx + (my - Y(cy)) * ny < 0) { nx = -nx; ny = -ny; }
    const o = 11, a2x = ax + nx * o, a2y = ay + ny * o, b2x = bx + nx * o, b2y = by + ny * o;
    let ang = Math.atan2(by - ay, bx - ax) * 180 / Math.PI;
    if (ang > 90) ang -= 180; if (ang < -90) ang += 180;
    out += `<line x1="${a2x.toFixed(1)}" y1="${a2y.toFixed(1)}" x2="${b2x.toFixed(1)}" y2="${b2y.toFixed(1)}" stroke="#1f6fd1" stroke-width="0.8"/>`;
    out += `<line x1="${ax}" y1="${ay}" x2="${(a2x + nx * 3).toFixed(1)}" y2="${(a2y + ny * 3).toFixed(1)}" stroke="#1f6fd1" stroke-width="0.6"/>`;
    out += `<line x1="${bx}" y1="${by}" x2="${(b2x + nx * 3).toFixed(1)}" y2="${(b2y + ny * 3).toFixed(1)}" stroke="#1f6fd1" stroke-width="0.6"/>`;
    const tx = (a2x + b2x) / 2 + nx * 8, ty = (a2y + b2y) / 2 + ny * 8;
    out += `<text x="${tx.toFixed(1)}" y="${ty.toFixed(1)}" font-size="10" fill="#1f4f99" text-anchor="middle" dominant-baseline="middle" transform="rotate(${ang.toFixed(1)} ${tx.toFixed(1)} ${ty.toFixed(1)})">${esc(U.len(dm.m))}</text>`;
  }
  for (const an of d.angles || []) {
    const px = X(an.at[0]), py = Y(an.at[1]), vx = X(cx) - px, vy = Y(cy) - py, vl = Math.hypot(vx, vy) || 1;
    const k = Math.min(20, vl * 0.42);
    out += `<text x="${(px + vx / vl * k).toFixed(1)}" y="${(py + vy / vl * k).toFixed(1)}" font-size="9" fill="#8a4b12" text-anchor="middle" dominant-baseline="middle">${esc(U.deg(an.deg))}</text>`;
  }
  for (const n of d.notes || []) {
    out += `<text x="${X(n.at[0]).toFixed(1)}" y="${Y(n.at[1]).toFixed(1)}" font-size="9.5" fill="#5b3a12" text-anchor="middle" dominant-baseline="middle">${esc(U.tokens(n.text))}</text>`;
  }
  return out + `</svg>`;
}

function sheetSvg(sh, U, w, colour) {
  const s = (w - 20) / sh.w, h = sh.h * s + 20;
  let out = `<svg class="cardsvg" viewBox="0 0 ${w} ${h.toFixed(0)}" width="${w}" height="${h.toFixed(0)}" xmlns="http://www.w3.org/2000/svg">`;
  out += `<rect x="10" y="10" width="${(sh.w * s).toFixed(1)}" height="${(sh.h * s).toFixed(1)}" fill="#f6f4ef" stroke="#1d1b18"/>`;
  for (const p of sh.parts) {
    const pts = p.pts.map(([x, y]) => `${(10 + x * s).toFixed(1)},${(10 + sh.h * s - y * s).toFixed(1)}`).join(" ");
    const cx = p.pts.reduce((a, q) => a + q[0], 0) / p.pts.length, cy = p.pts.reduce((a, q) => a + q[1], 0) / p.pts.length;
    out += `<polygon points="${pts}" fill="${(colour && colour(p.mark)) || "#e8d9bd"}" stroke="#1d1b18" stroke-width="0.7"/>`;
    out += `<text x="${(10 + cx * s).toFixed(1)}" y="${(10 + sh.h * s - cy * s).toFixed(1)}" font-size="8" text-anchor="middle" dominant-baseline="middle">${esc(p.mark)}</text>`;
  }
  return out + `</svg>`;
}

function grouped(cards) {
  const g = new Map();
  cards.forEach((c, i) => { const k = c.group || "Pieces"; if (!g.has(k)) g.set(k, []); g.get(k).push([c, i]); });
  return g;
}

function cardHtml(c, i, U, w, colour) {
  const col = colour ? colour(c.mark) : null;
  if (c.locked) {
    // the trial copy online: the card's name and count, its drawing and figures in the full program
    return `<div class="card locked"><div class="ch"><span class="mk">${esc(c.mark)}</span><b>${esc(c.title)}</b><span class="qty">&times; ${c.count}</span></div>` +
      `<p class="muted small">The drawing and every cut on this card come with the full Dome Sketch.</p></div>`;
  }
  return `<div class="card" data-i="${i}" title="${c.ids.length ? "Click to light these up in the model" : ""}">` +
    `<div class="ch"><span class="mk" style="${col ? `background:${col}` : ""}">${esc(c.mark)}</span><b>${esc(c.title)}</b><span class="qty">&times; ${c.count}</span></div>` +
    (c.draw ? svgOf(c.draw, U, w) : "") +
    `<table>${c.rows.map(([k, v]) => `<tr><td>${esc(k)}</td><td>${esc(U.tokens(v))}</td></tr>`).join("")}</table></div>`;
}

export function renderCards(el, t, U, opt = {}) {
  const cards = t.cards || [];
  const total = cards.reduce((a, c) => a + (c.count || 0), 0);
  let html = `<p class="muted">${cards.length} cards, ${total.toLocaleString()} pieces. Every figure is the solver's; click a card to find its pieces.</p>`;
  for (const [g, list] of grouped(cards)) {
    html += `<div class="cardgrp"><h5>${esc(g)}</h5>${list.map(([c, i]) => cardHtml(c, i, U, 262, opt.colour)).join("")}</div>`;
  }
  if ((t.sheets || []).length) {
    html += `<div class="cardgrp"><h5>Nesting: ${t.sheets.length} sheet${t.sheets.length === 1 ? "" : "s"}</h5>` +
      t.sheets.map((sh, k) => `<div class="card"><div class="ch"><b>Sheet ${k + 1}</b><span class="qty">${esc(U.len(sh.w))} x ${esc(U.len(sh.h))}</span></div>${sheetSvg(sh, U, 262, opt.colour)}</div>`).join("") + `</div>`;
  }
  el.innerHTML = html;
  el.querySelectorAll(".card[data-i]").forEach((d) => d.onclick = () => {
    const c = cards[+d.dataset.i];
    el.querySelectorAll(".card.on").forEach((x) => x.classList.remove("on"));
    d.classList.add("on");
    if (c.ids.length && opt.pick) opt.pick(c.ids);
  });
}

export function printCards(t, U, opt = {}) {
  const w = window.open("", "_blank");
  if (!w) return;
  const cards = t.cards || [];
  let body = `<h1>${esc(t.title || "Dome Sketch")}: cut list</h1>`;
  body += `<table class="sum">${(t.summary || []).map(([k, v]) => `<tr><td>${esc(k)}</td><td>${esc(U.tokens(v))}</td></tr>`).join("")}</table>`;
  for (const [g, list] of grouped(cards)) {
    body += `<h2>${esc(g)}</h2><div class="grid">${list.map(([c, i]) => cardHtml(c, i, U, 330, opt.colour)).join("")}</div>`;
  }
  if ((t.sheets || []).length) body += `<h2>Nesting</h2><div class="grid">${t.sheets.map((sh, k) => `<div class="card"><div class="ch"><b>Sheet ${k + 1}</b></div>${sheetSvg(sh, U, 330, opt.colour)}</div>`).join("")}</div>`;
  if ((t.declared || []).length) body += `<h2>Declared inputs</h2><table class="sum">${t.declared.map((r) => `<tr><td>${esc(r.name)}</td><td>${esc(U.tokens(r.value))}</td><td>${esc(U.tokens(r.why))}</td></tr>`).join("")}</table>`;
  w.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>${esc(t.title || "Cut list")}</title><style>
    body{font:12px "Segoe UI",system-ui,sans-serif;color:#1d1b18;margin:18px}h1{font-size:20px}h2{font-size:15px;margin:18px 0 6px;border-bottom:2px solid #c45e29}
    .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:10px}.card{border:1px solid #cfccc4;border-radius:6px;padding:6px;break-inside:avoid}
    .ch{display:flex;gap:6px;align-items:center;margin-bottom:4px}.mk{background:#e8d9bd;border-radius:3px;padding:0 5px;font-weight:700}.qty{margin-left:auto;font-weight:700}
    table{border-collapse:collapse;width:100%}td{border-bottom:1px dotted #cfccc4;padding:1px 3px;vertical-align:top}.sum{max-width:720px}
    @media print{h2{break-after:avoid}}</style></head><body>${body}<script>setTimeout(()=>print(),400)<\/script></body></html>`);
  w.document.close();
}
