// The Wedge Builder's cut lists (/cutlist/:ref, migrations/0015).
//
// A paid order whose product has a tool_grants row may make that many cut lists. The buyer
// proves the order the way a receipt does (its private key, or a signed-in owner) and sends a
// request: a size, a log and two choices, checked against the same limits the solver uses
// (src/generated/wedge-builder.json, written by `npm run facts` from wedge_builder/design.py).
// The request is queued. The site never solves anything: website/scripts/render_cutlists.py,
// on the owner's machine with an agent key (scope cutlists:render), claims the next request,
// solves and renders it with the project's wedge_builder package, and uploads the PDF to R2.
// A failed render returns its credit and shows the buyer the solver's reason.

import { agentAuth } from "./agent";
import { randomToken } from "./crypto";
import { DeliveryOrder, queueCutlistReady, toolCredits } from "./fulfillment";
import { requireAdmin } from "./auth";
import { Ctx, HttpError, body, json, nowIso, text } from "./http";
import { audit, emit } from "./ops";
import api, { loadOrder, OrderRow } from "./routes";
import wb from "../../src/generated/wedge-builder.json";

const STALE_MS = 30 * 60_000;   // a claimed render not finished in this long goes back on the queue
const MAX_ATTEMPTS = 3;
const MAX_PDF = 20_000_000;

interface Job {
  id: number; ref: string; order_id: number; params: string; status: string; attempts: number; error: string | null;
  design: string | null; summary: string | null; file_key: string | null; size: number | null; downloads: number;
  created_at: string; claimed_at: string | null; done_at: string | null;
}

type Params = { diameter_ft: number; log_in: number; log_ft: number; orientation: string; seam_join: string; label: string; pattern: string; ground_in: string };

/** The request, checked as wedge_builder.design.Request.from_json checks it. */
function params(b: Record<string, unknown>): Params {
  const out: Record<string, number> = {};
  for (const [k, lim] of Object.entries(wb.limits) as [keyof typeof wb.limits, { min: number; max: number }][]) {
    const v = Number(b[k]);
    if (!Number.isFinite(v) || v < lim.min || v > lim.max) throw new HttpError(400, `${label(k)} must be between ${lim.min} and ${lim.max}.`);
    out[k] = Math.round(v * 1000) / 1000;
  }
  const orientation = String(b.orientation || wb.defaults.orientation);
  const seam = String(b.seam_join || wb.defaults.seam_join);
  if (!wb.orientations.some((o) => o.key === orientation)) throw new HttpError(400, "Pick one of the wedge orientations.");
  if (!wb.seamJoins.some((o) => o.key === seam)) throw new HttpError(400, "Pick one of the seam joins.");
  const name = (text(b, "label", { max: 60 }) || "").replace(/\s+/g, " ").trim();
  const pattern = String(b.pattern || "uniform");
  const ground = String(b.ground_in || "auto");
  if (!wb.patterns.some((o) => o.key === pattern)) throw new HttpError(400, "Pick one of the build patterns.");
  if (!wb.groundIn.some((o) => o.key === ground)) throw new HttpError(400, "Pick which ground panels point in.");
  // a mixed dome chooses in and out itself and uses raw trapezoid seams (wedge_builder.design)
  const mixed = pattern !== "uniform";
  return { diameter_ft: out.diameter_ft, log_in: out.log_in, log_ft: out.log_ft, orientation: mixed ? "point_dome_in" : orientation,
    seam_join: mixed ? "raw_trapezoid" : seam, label: name, pattern, ground_in: mixed ? ground : "auto" };
}

function label(k: string) {
  return ({ diameter_ft: "The floor diameter (ft)", log_in: "The log diameter (in)", log_ft: "The log length (ft)" } as Record<string, string>)[k] || k;
}

function publicJob(j: Job, ref: string, key: string) {
  return {
    ref: j.ref, status: j.status, params: JSON.parse(j.params) as Params, error: j.status === "failed" ? j.error : null,
    design: j.design, summary: j.summary ? JSON.parse(j.summary) : null, size: j.size, createdAt: j.created_at, doneAt: j.done_at,
    pdfUrl: j.status === "done" ? `/api/orders/${ref}/cutlists/${j.ref}/pdf${key ? `?key=${encodeURIComponent(key)}` : ""}` : null,
  };
}

async function jobsOf(ctx: Ctx, orderId: number) {
  return (await ctx.env.DB.prepare("SELECT * FROM cutlists WHERE order_id = ? ORDER BY id DESC").bind(orderId).all<Job>()).results;
}

async function access(ctx: Ctx) {
  const { order, key } = await loadOrder(ctx);
  if (order.status !== "paid") throw new HttpError(402, "This order has not been paid yet.");
  const credits = await toolCredits(ctx, order.book_slug, "cutlist");
  if (!credits) throw new HttpError(404, "This order does not include cut lists.");
  const jobs = await jobsOf(ctx, order.id);
  return { order, key, credits, jobs, used: jobs.filter((j) => j.status !== "failed").length };
}

// ---------------------------------------------------------------- the buyer

api.get("/orders/:ref/cutlists", async (ctx) => {
  const a = await access(ctx);
  const title = await ctx.env.DB.prepare("SELECT title FROM products WHERE slug = ?").bind(a.order.book_slug).first<{ title: string }>();
  const queued = (await ctx.env.DB.prepare("SELECT COUNT(*) n FROM cutlists WHERE status IN ('queued', 'rendering')").first<{ n: number }>())!.n;
  return json({
    order: { ref: a.order.ref, product: title?.title || a.order.book_slug }, credits: a.credits, used: a.used, queueLength: queued,
    form: { limits: wb.limits, orientations: wb.orientations, seamJoins: wb.seamJoins, patterns: wb.patterns, groundIn: wb.groundIn, defaults: wb.defaults },
    jobs: a.jobs.map((j) => publicJob(j, a.order.ref, a.key)),
  });
});

api.post("/orders/:ref/cutlists", async (ctx) => {
  const a = await access(ctx);
  if (a.used >= a.credits) throw new HttpError(409, `This order's ${a.credits === 1 ? "cut list is" : `${a.credits} cut lists are all`} used. Each one stays here to download.`);
  if (a.jobs.some((j) => j.status === "queued" || j.status === "rendering")) throw new HttpError(409, "One cut list is already being solved. Ask for the next when it is ready.");
  const p = params(await body(ctx));
  const ref = randomToken(9);
  await ctx.env.DB.prepare("INSERT INTO cutlists(ref, order_id, params, status, created_at) VALUES(?, ?, ?, 'queued', ?)")
    .bind(ref, a.order.id, JSON.stringify(p), nowIso()).run();
  await audit(ctx, "cutlist.request", `order:${a.order.ref}`, { cutlist: ref, ...p });
  await emit(ctx, "cutlist.requested", { ref, order: a.order.ref, product: a.order.book_slug, diameter_ft: p.diameter_ft });
  const j = (await ctx.env.DB.prepare("SELECT * FROM cutlists WHERE ref = ?").bind(ref).first<Job>())!;
  return json({ job: publicJob(j, a.order.ref, a.key) }, 201);
});

api.get("/orders/:ref/cutlists/:job/pdf", async (ctx) => {
  const { order } = await loadOrder(ctx);
  const j = await ctx.env.DB.prepare("SELECT * FROM cutlists WHERE ref = ? AND order_id = ?").bind(ctx.params.job, order.id).first<Job>();
  if (!j || j.status !== "done" || !j.file_key) throw new HttpError(404, "That cut list is not ready.");
  if (!ctx.env.BOOKS) throw new HttpError(503, "File storage is not connected yet.");
  const obj = await ctx.env.BOOKS.get(j.file_key);
  if (!obj) throw new HttpError(404, "That cut list's file is missing. Reply to your receipt email and it will be re-made.");
  if (ctx.request.method === "GET") await ctx.env.DB.prepare("UPDATE cutlists SET downloads = downloads + 1 WHERE id = ?").bind(j.id).run();
  const p = JSON.parse(j.params) as Params;
  const name = `wedge-dome-cut-list-${String(p.diameter_ft).replace(".", "_")}ft-${j.design || j.ref}.pdf`;
  return new Response(ctx.request.method === "HEAD" ? null : obj.body, {
    headers: { "Content-Type": "application/pdf", "Content-Length": String(obj.size), "Content-Disposition": `attachment; filename="${name}"`, "Cache-Control": "private, no-store" },
  });
});

// ---------------------------------------------------------------- the render script (an agent key, scope cutlists:render)

/** Claim the oldest waiting request (or one whose render went quiet). Nothing to do: { job: null }. */
api.post("/agent/cutlists/claim", async (ctx) => {
  const key = await agentAuth(ctx, "cutlists:render");
  const stale = new Date(Date.now() - STALE_MS).toISOString();
  // a render that went quiet MAX_ATTEMPTS times is given up, so one bad request cannot block the queue
  await ctx.env.DB.prepare("UPDATE cutlists SET status = 'failed', error = 'It could not be solved after several tries. Your credit is returned; reply to your receipt email.' "
    + "WHERE status = 'rendering' AND claimed_at < ? AND attempts >= ?").bind(stale, MAX_ATTEMPTS).run();
  const j = await ctx.env.DB.prepare(
    "UPDATE cutlists SET status = 'rendering', attempts = attempts + 1, claimed_at = ? WHERE id = ("
    + "SELECT id FROM cutlists WHERE status = 'queued' OR (status = 'rendering' AND claimed_at < ?) ORDER BY id LIMIT 1) RETURNING *",
  ).bind(nowIso(), stale).first<Job>();
  if (!j) return json({ job: null });
  const o = (await ctx.env.DB.prepare("SELECT ref FROM orders WHERE id = ?").bind(j.order_id).first<{ ref: string }>())!;
  await audit(ctx, "cutlist.claim", `cutlist:${j.ref}`, { attempt: j.attempts }, { kind: "agent", id: key.id, name: key.name });
  return json({ job: { ref: j.ref, order: o.ref, params: JSON.parse(j.params), attempt: j.attempts } });
});

async function claimed(ctx: Ctx) {
  const j = await ctx.env.DB.prepare("SELECT * FROM cutlists WHERE ref = ?").bind(ctx.params.job).first<Job>();
  if (!j) throw new HttpError(404, "No such cut list.");
  if (j.status !== "rendering") throw new HttpError(409, `That cut list is ${j.status}, not rendering.`);
  return j;
}

api.post("/agent/cutlists/:job/done", async (ctx) => {
  const key = await agentAuth(ctx, "cutlists:render");
  const j = await claimed(ctx);
  const b = await body(ctx);
  if (!ctx.env.BOOKS) throw new HttpError(503, "File storage (R2) is not set up here.");
  const bytes = Uint8Array.from(atob(String(b.pdf || "")), (c) => c.charCodeAt(0));
  if (bytes.length < 1000 || bytes.length > MAX_PDF || String.fromCharCode(...bytes.slice(0, 5)) !== "%PDF-") throw new HttpError(400, "That is not a PDF, or it is over 20 MB.");
  const design = (text(b, "design", { max: 40 }) || "").replace(/[^a-z0-9]/g, "");
  const summary = b.summary && typeof b.summary === "object" ? JSON.stringify(b.summary).slice(0, 4000) : null;
  const order = (await ctx.env.DB.prepare("SELECT * FROM orders WHERE id = ?").bind(j.order_id).first<OrderRow>())!;
  const r2 = `cutlists/${order.ref}/${j.ref}.pdf`;
  await ctx.env.BOOKS.put(r2, bytes, { httpMetadata: { contentType: "application/pdf" } });
  await ctx.env.DB.prepare("UPDATE cutlists SET status = 'done', file_key = ?, size = ?, design = ?, summary = ?, error = NULL, done_at = ? WHERE id = ?")
    .bind(r2, bytes.length, design || null, summary, nowIso(), j.id).run();
  await audit(ctx, "cutlist.done", `cutlist:${j.ref}`, { size: bytes.length, design }, { kind: "agent", id: key.id, name: key.name });
  const p = JSON.parse(j.params) as Params;
  const s = summary ? JSON.parse(summary) as { logs?: number; families?: number } : {};
  await queueCutlistReady(ctx, order as DeliveryOrder, {
    id: j.id, label: p.label,
    summary: `a ${p.diameter_ft} ft dome from ${p.log_in} in logs${s.logs ? `, ${s.logs} logs of ${p.log_ft} ft` : ""}${s.families ? `, ${s.families} cut families` : ""}`,
  });
  return json({ ref: j.ref, status: "done" });
});

api.post("/agent/cutlists/:job/failed", async (ctx) => {
  const key = await agentAuth(ctx, "cutlists:render");
  const j = await claimed(ctx);
  const b = await body(ctx);
  // refused: the solver said no (e.g. logs too short) -- a reason for the buyer, and the credit back
  const reason = text(b, "error", { max: 500 }) || "The solver could not build this dome.";
  await ctx.env.DB.prepare("UPDATE cutlists SET status = 'failed', error = ?, done_at = ? WHERE id = ?").bind(reason, nowIso(), j.id).run();
  await audit(ctx, "cutlist.failed", `cutlist:${j.ref}`, { reason }, { kind: "agent", id: key.id, name: key.name });
  return json({ ref: j.ref, status: "failed" });
});

// ---------------------------------------------------------------- the owner

api.get("/admin/cutlists", async (ctx) => {
  requireAdmin(ctx);
  const rows = (await ctx.env.DB.prepare(
    "SELECT c.ref, c.status, c.params, c.attempts, c.error, c.design, c.size, c.downloads, c.created_at, c.done_at, o.ref AS order_ref, o.book_slug "
    + "FROM cutlists c JOIN orders o ON o.id = c.order_id ORDER BY c.id DESC LIMIT 200").all()).results;
  return json({ cutlists: rows });
});
