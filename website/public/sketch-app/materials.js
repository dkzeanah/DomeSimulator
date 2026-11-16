// copied from sketch_claude/static/materials.js by website/scripts/sync_sketch_app.py: edit that file, then re-run
// Materials and cost: the quantities the solver counted for this design, the declared prices they
// are multiplied by, and the estimated total. The two tables stay apart: quantities are computed,
// prices are estimates. Type your own supplier's price over any of them and the total follows;
// your prices are kept in this browser and go with the materials CSV when you export it.

const $ = (s) => document.querySelector(s);
const KEY = "dome-sketch-prices";
const usd = (v) => `$${(+v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const usd0 = (v) => `$${Math.round(v).toLocaleString()}`;
const div = (per) => (per === "100" ? 100 : per === "1000" ? 1000 : 1);

function mine() { try { return JSON.parse(localStorage.getItem(KEY) || "{}"); } catch { return {}; } }
function keep(o) { try { localStorage.setItem(KEY, JSON.stringify(o)); } catch { /* not kept */ } }

export function initMaterials(ctx) {
  const { S, U, esc } = ctx;

  /** The table at the viewer's prices: the same sum the server's costing.reprice makes. */
  function priced() {
    const mt = S.data && S.data.tables.materials;
    if (!mt) return null;
    const own = mine();
    const prices = mt.prices.map((p) => (own[p.key] !== undefined && isFinite(own[p.key]) && own[p.key] >= 0 ? { ...p, usd: +own[p.key], kind: "yours" } : p));
    const by = Object.fromEntries(prices.map((p) => [p.key, p]));
    let total = 0;
    const rows = mt.rows.map((r) => {
      const p = by[r.price];
      const cost = p ? Math.round(r.units * p.usd / div(p.per) * 100) / 100 : null;
      if (cost !== null) total += cost;
      return { ...r, usd: cost };
    });
    return { ...mt, rows, prices, total };
  }

  function render() {
    const box = $("#materials");
    const t = priced();
    if (!t) { box.innerHTML = `<p class="muted">No materials table for this design.</p>`; return; }
    const own = mine();
    box.innerHTML =
      `<div class="mt-total"><span>Materials, estimated</span><b>${usd0(t.total)}</b></div>` +
      `<table class="mt"><tr><th>Item</th><th>Qty</th><th>Cost</th></tr>${t.rows.map((r) =>
        `<tr title="${esc(U.tokens(r.from))}"><td>${esc(U.tokens(r.item))}<br><span class="muted">${esc(U.tokens(r.from))}</span></td>` +
        `<td class="n">${esc(U.tokens(r.qty_text))}</td><td class="n">${r.usd === null ? "" : usd0(r.usd)}</td></tr>`).join("")}</table>` +
      `<h5>Prices used <span class="est">estimates</span></h5>` +
      `<table class="mt prices">${t.prices.map((p) =>
        `<tr title="${esc(p.why)} (${esc(p.source || "")})"><td>${esc(p.label)}<br><span class="muted">${esc(p.kind === "yours" ? "your price" : `${p.kind}: ${p.why}`)}</span></td>` +
        `<td class="n"><input type="number" min="0" step="0.01" data-k="${esc(p.key)}" value="${p.usd}" class="${own[p.key] !== undefined ? "yours" : ""}"></td>` +
        `<td class="per">/ ${esc(p.per)}</td></tr>`).join("")}</table>` +
      `<div class="row"><button id="mt-reset" title="Back to the declared estimates">Reset prices</button>` +
      `<button id="mt-csv" class="pro" title="Quantities, prices and the total as a spreadsheet">Materials CSV</button></div>` +
      `<p class="muted small">${esc(t.note)}</p>` +
      ((t.assumed || []).length ? `<p class="muted small">Assumed: ${t.assumed.map((a) => `${esc(a.name.replace(/_/g, " "))} ${esc(typeof a.value === "number" && a.name.endsWith("_m") ? U.len(a.value) : String(a.value))} (${esc(a.why)})`).join("; ")}.</p>` : "");
    box.querySelectorAll("input[data-k]").forEach((el) => el.onchange = () => {
      const o = mine(), v = parseFloat(el.value);
      if (isFinite(v) && v >= 0) o[el.dataset.k] = v; else delete o[el.dataset.k];
      keep(o); render();
    });
    $("#mt-reset").onclick = () => { const o = mine(); for (const p of S.data.tables.materials.prices) delete o[p.key]; keep(o); render(); };
    $("#mt-csv").onclick = () => ctx.exportFile("materials");
  }

  return { render, priced, overrides: mine };
}
