// The paid tools and who may open them: Dome Sketch, its build packs, the Wedge Builder, and the
// owner's studio tools. Access comes from orders (an account's paid orders and the tool_grants
// rows of what they bought, migrations/0016); the owner (admin) has everything.
//
//   GET  /api/me/tools                    every tool, whether this account may open it, and where
//   GET  /api/sketch/design/:id           one solved Dome Sketch design (R2 sketch/<id>.json.gz);
//                                         the trial designs open to anyone, the rest need "domesketch"
//   POST /api/sketch/packs {spec}         queue a build pack for the design (needs "buildpack" credit)
//   GET  /api/sketch/packs                this account's packs; GET .../:ref/pdf downloads one
//   /api/agent/packs/*                    the render script (scope packs:render), as for cut lists
//   GET  /api/admin/deploys, POST /api/admin/deploys/promote    staging and live, from the dashboard

import { agentAuth } from "./agent";
import { requireAdmin, requireUser } from "./auth";
import { randomToken } from "./crypto";
import { Ctx, HttpError, User, body, json, nowIso, text } from "./http";
import { audit, emit } from "./ops";
import api from "./routes";
import grid from "../../src/generated/sketch-grid.json";

type Grid = { cuts: { frequency: number; cut: string }[]; diameters: number[]; windows: number[]; trial: string[]; designs: Record<string, { spec: Record<string, unknown>; title: string }> };
const G = grid as unknown as Grid;

export interface ToolCard { key: string; title: string; blurb: string; href: string; access: boolean; why: string; credits?: number; used?: number; local?: boolean; buy?: string }

/** What each grant key this account's paid orders carry adds up to. */
export async function grantsOf(ctx: Ctx, u: User | null): Promise<Record<string, number>> {
  if (!u) return {};
  const rows = (await ctx.env.DB.prepare(
    "SELECT g.tool, SUM(g.credits) AS credits FROM orders o JOIN tool_grants g ON g.product = o.book_slug "
    + "WHERE o.user_id = ? AND o.status = 'paid' GROUP BY g.tool").bind(u.id).all<{ tool: string; credits: number }>()).results;
  return Object.fromEntries(rows.map((r) => [r.tool, r.credits]));
}

const isAdmin = (u: User | null) => u?.role === "admin";

async function packsUsed(ctx: Ctx, u: User) {
  return (await ctx.env.DB.prepare("SELECT COUNT(*) AS n FROM tool_jobs WHERE user_id = ? AND tool = 'buildpack' AND status != 'failed'").bind(u.id).first<{ n: number }>())!.n;
}

api.get("/me/tools", async (ctx) => {
  const u = ctx.user, admin = isAdmin(u), g = await grantsOf(ctx, u);
  const used = u ? await packsUsed(ctx, u) : 0;
  const has = (k: string) => admin || (g[k] ?? 0) > 0;
  const cards: ToolCard[] = [
    { key: "domesketch", title: "Dome Sketch", href: "/sketch-app/", access: has("domesketch"),
      blurb: "Design a framed-panel dome in 3-D and get its build pack: plans, cut list, materials, tools, prices, every step.",
      why: admin ? "owner" : g.domesketch ? "bought" : "comes with the book, or $10 on its own", buy: "dome-sketch",
      credits: admin ? undefined : g.buildpack ?? 0, used },
    { key: "wedgebuilder", title: "Wedge Builder", href: "/account/books", access: admin || (g.cutlist ?? 0) > 0,
      blurb: "A cut list solved for your own wedge dome and logs: saw setups, cut families, the log plan, jigs, seams.",
      why: admin ? "owner" : g.cutlist ? "from your receipt (My books)" : "comes with the book or the Wedge Builder", buy: "wedge-builder" },
    { key: "calculator", title: "Wedge calculator", href: "/calculator", access: true, blurb: "Wedges or lumber: what each split keeps of a log, at your kerf.", why: "free" },
    { key: "episodes", title: "Episodes", href: "/episodes", access: true, blurb: "Every film, free to watch.", why: "free" },
    { key: "trial", title: "Software trial", href: "/software", access: true, blurb: "Try the tools before you buy.", why: "free" },
  ];
  if (admin) {
    // the owner's studio runs on the owner's computer (py -3.12 -m sketch_claude serve); the dashboard links to it
    const local = "http://127.0.0.1:8767";
    cards.push(
      { key: "director", title: "Episode Director", href: `${local}/director`, access: true, local: true, why: "owner",
        blurb: "Load any episode, edit scenes, lines, shots and graphics on the timeline, play it, render it." },
      { key: "season", title: "Season room", href: `${local}/season`, access: true, local: true, why: "owner",
        blurb: "Season one's ten episodes, their story threads and how much each is covered." },
      { key: "modeller", title: "Modeller (full)", href: `${local}/`, access: true, local: true, why: "owner",
        blurb: "Every setting free, plan sets and showcase renders made on the spot." },
      { key: "lessons", title: "Lesson Studio", href: `${local}/lesson?lesson=2v`, access: true, local: true, why: "owner",
        blurb: "Lesson films on the web engine: preview, stills, render." },
      { key: "admin", title: "Admin dashboard", href: "/admin", access: true, why: "owner", blurb: "The list, orders, tools, staging and live." },
    );
  }
  return json({ admin, tools: cards });
});

// ---------------------------------------------------------------- Dome Sketch

async function mayDesign(ctx: Ctx) {
  const u = ctx.user;
  if (isAdmin(u)) return true;
  return ((await grantsOf(ctx, u)).domesketch ?? 0) > 0;
}

api.get("/sketch/design/:id", async (ctx) => {
  const id = ctx.params.id;
  if (!G.designs[id]) throw new HttpError(404, "No such design.");
  if (!G.trial.includes(id) && !(await mayDesign(ctx))) {
    throw new HttpError(402, "This design is in the full Dome Sketch. It comes with the book, or $10 on its own.");
  }
  if (!ctx.env.MEDIA) throw new HttpError(503, "The design store is not connected yet.");
  const obj = await ctx.env.MEDIA.get(`sketch/${id}.json.gz`);
  if (!obj) throw new HttpError(404, "That design has not been uploaded yet.");
  // already gzipped: hand it to the browser as it is
  return new Response(obj.body, {
    headers: { "Content-Type": "application/json", "Content-Encoding": "gzip", "Cache-Control": "private, max-age=86400" },
    encodeBody: "manual",
  } as ResponseInit);
});

/** A design this site can build a pack for: a solved structural design plus the page-side options. */
function checkSpec(raw: unknown): Record<string, unknown> {
  const s = (raw && typeof raw === "object" ? raw : {}) as Record<string, unknown>;
  const pick = { frequency: Number(s.frequency), cut: String(s.cut), diameter_m: Number(s.diameter_m), door: Boolean(s.door),
                 windows: Number(s.windows), skylight: Boolean(s.skylight) };
  const hit = Object.entries(G.designs).find(([, d]) => ["frequency", "cut", "diameter_m", "door", "windows", "skylight"]
    .every((k) => String(d.spec[k]) === String((pick as Record<string, unknown>)[k])));
  if (!hit) throw new HttpError(400, "That design is not one the site can solve. Pick it from the form.");
  const skin = ["cabin", "clear", "none"].includes(String(s.skin)) ? String(s.skin) : "cabin";
  const flag = (k: string) => s[k] === undefined ? true : Boolean(s[k]);
  return { ...hit[1].spec, skin, furnish: flag("furnish"), porch: flag("porch"), stove: flag("stove"), people: flag("people") };
}

api.post("/sketch/packs", async (ctx) => {
  const u = requireUser(ctx);
  const admin = isAdmin(u);
  const g = await grantsOf(ctx, u);
  if (!admin && !(g.domesketch > 0)) throw new HttpError(402, "Build packs come with Dome Sketch.");
  const used = await packsUsed(ctx, u);
  if (!admin && used >= (g.buildpack ?? 0)) throw new HttpError(409, `Your ${g.buildpack ?? 0} build packs are all used. Each one stays in My Links to download again.`);
  const b = await body(ctx);
  const spec = checkSpec(b.spec);
  const waiting = (await ctx.env.DB.prepare("SELECT COUNT(*) AS n FROM tool_jobs WHERE user_id = ? AND status IN ('queued','rendering')").bind(u.id).first<{ n: number }>())!.n;
  if (waiting >= 2) throw new HttpError(409, "Two packs are already being drawn for you. Ask for the next when one is ready.");
  const ref = randomToken(9);
  await ctx.env.DB.prepare("INSERT INTO tool_jobs(ref, tool, user_id, params, status, created_at) VALUES(?, 'buildpack', ?, ?, 'queued', ?)")
    .bind(ref, u.id, JSON.stringify(spec), nowIso()).run();
  await emit(ctx, "buildpack.requested", { ref, userId: u.id, diameter_m: Number(spec.diameter_m), frequency: Number(spec.frequency) });
  return json({ ref, spec }, 201);
});

interface Job { id: number; ref: string; tool: string; user_id: number; params: string; status: string; attempts: number; error: string | null; summary: string | null; file_key: string | null; size: number | null; created_at: string; claimed_at: string | null; done_at: string | null }

const publicJob = (j: Job) => ({ ref: j.ref, status: j.status, spec: JSON.parse(j.params), error: j.status === "failed" ? j.error : null,
  size: j.size, createdAt: j.created_at, doneAt: j.done_at, pdfUrl: j.status === "done" ? `/api/sketch/packs/${j.ref}/pdf` : null });

api.get("/sketch/packs", async (ctx) => {
  const u = requireUser(ctx);
  const rows = (await ctx.env.DB.prepare("SELECT * FROM tool_jobs WHERE user_id = ? AND tool = 'buildpack' ORDER BY id DESC LIMIT 50").bind(u.id).all<Job>()).results;
  return json({ packs: rows.map(publicJob) });
});

api.get("/sketch/packs/:ref/pdf", async (ctx) => {
  const u = requireUser(ctx);
  const j = await ctx.env.DB.prepare("SELECT * FROM tool_jobs WHERE ref = ?").bind(ctx.params.ref).first<Job>();
  if (!j || (j.user_id !== u.id && !isAdmin(u)) || j.status !== "done" || !j.file_key) throw new HttpError(404, "That pack is not ready.");
  const obj = await ctx.env.BOOKS?.get(j.file_key);
  if (!obj) throw new HttpError(404, "That pack's file is missing. Ask for it again; it will not use a credit.");
  await ctx.env.DB.prepare("UPDATE tool_jobs SET downloads = downloads + 1 WHERE id = ?").bind(j.id).run();
  const s = JSON.parse(j.params);
  return new Response(obj.body, { headers: { "Content-Type": "application/pdf", "Content-Length": String(obj.size), "Cache-Control": "private, no-store",
    "Content-Disposition": `attachment; filename="dome-build-pack-${s.frequency}v-${String(s.diameter_m).replace(".", "_")}m-${j.ref}.pdf"` } });
});

/** The modeller links a finished job as /api/file?path=...; online that is a build pack. */
api.get("/file", async (ctx) => {
  const m = /^packs\/([A-Za-z0-9_-]+)\.pdf$/.exec(ctx.url.searchParams.get("path") || "");
  if (!m) throw new HttpError(404, "Not found.");
  return Response.redirect(new URL(`/api/sketch/packs/${m[1]}/pdf`, ctx.url).toString(), 302);
});

// ---------------------------------------------------------------- the render script (scope packs:render)

const STALE_MS = 60 * 60_000;

api.post("/agent/packs/claim", async (ctx) => {
  const key = await agentAuth(ctx, "packs:render");
  const stale = new Date(Date.now() - STALE_MS).toISOString();
  await ctx.env.DB.prepare("UPDATE tool_jobs SET status = 'failed', error = 'It could not be drawn after several tries. Your credit is returned.' "
    + "WHERE status = 'rendering' AND claimed_at < ? AND attempts >= 3").bind(stale).run();
  const j = await ctx.env.DB.prepare("UPDATE tool_jobs SET status = 'rendering', attempts = attempts + 1, claimed_at = ? WHERE id = ("
    + "SELECT id FROM tool_jobs WHERE tool = 'buildpack' AND (status = 'queued' OR (status = 'rendering' AND claimed_at < ?)) ORDER BY id LIMIT 1) RETURNING *")
    .bind(nowIso(), stale).first<Job>();
  if (!j) return json({ job: null });
  await audit(ctx, "buildpack.claim", `pack:${j.ref}`, { attempt: j.attempts }, { kind: "agent", id: key.id, name: key.name });
  return json({ job: { ref: j.ref, spec: JSON.parse(j.params), attempt: j.attempts } });
});

async function claimedJob(ctx: Ctx) {
  const j = await ctx.env.DB.prepare("SELECT * FROM tool_jobs WHERE ref = ?").bind(ctx.params.ref).first<Job>();
  if (!j) throw new HttpError(404, "No such pack.");
  if (j.status !== "rendering") throw new HttpError(409, `That pack is ${j.status}, not rendering.`);
  return j;
}

api.post("/agent/packs/:ref/done", async (ctx) => {
  const key = await agentAuth(ctx, "packs:render");
  const j = await claimedJob(ctx);
  const b = await body(ctx);
  if (!ctx.env.BOOKS) throw new HttpError(503, "File storage (R2) is not set up here.");
  const bytes = Uint8Array.from(atob(String(b.pdf || "")), (c) => c.charCodeAt(0));
  if (bytes.length < 1000 || bytes.length > 60_000_000 || String.fromCharCode(...bytes.slice(0, 5)) !== "%PDF-") throw new HttpError(400, "That is not a PDF, or it is over 60 MB.");
  const r2 = `packs/${j.user_id}/${j.ref}.pdf`;
  await ctx.env.BOOKS.put(r2, bytes, { httpMetadata: { contentType: "application/pdf" } });
  await ctx.env.DB.prepare("UPDATE tool_jobs SET status = 'done', file_key = ?, size = ?, summary = ?, error = NULL, done_at = ? WHERE id = ?")
    .bind(r2, bytes.length, b.summary ? JSON.stringify(b.summary).slice(0, 2000) : null, nowIso(), j.id).run();
  await audit(ctx, "buildpack.done", `pack:${j.ref}`, { size: bytes.length }, { kind: "agent", id: key.id, name: key.name });
  return json({ ref: j.ref, status: "done" });
});

api.post("/agent/packs/:ref/failed", async (ctx) => {
  const key = await agentAuth(ctx, "packs:render");
  const j = await claimedJob(ctx);
  const reason = text(await body(ctx), "error", { max: 500 }) || "The pack could not be drawn.";
  await ctx.env.DB.prepare("UPDATE tool_jobs SET status = 'failed', error = ?, done_at = ? WHERE id = ?").bind(reason, nowIso(), j.id).run();
  await audit(ctx, "buildpack.failed", `pack:${j.ref}`, { reason }, { kind: "agent", id: key.id, name: key.name });
  return json({ ref: j.ref, status: "failed" });
});

// ---------------------------------------------------------------- the owner: queues, staging and live

api.get("/admin/tool-jobs", async (ctx) => {
  requireAdmin(ctx);
  const rows = (await ctx.env.DB.prepare("SELECT j.ref, j.tool, j.status, j.params, j.attempts, j.error, j.size, j.downloads, j.created_at, j.done_at, u.email "
    + "FROM tool_jobs j JOIN users u ON u.id = j.user_id ORDER BY j.id DESC LIMIT 100").all()).results;
  return json({ jobs: rows });
});

const REPO = (ctx: Ctx) => ctx.env.GITHUB_REPO || "dkzeanah/DomeSimulator";

async function gh(ctx: Ctx, path: string, init: RequestInit = {}) {
  if (!ctx.env.GITHUB_TOKEN) throw new HttpError(503, "Add a GITHUB_TOKEN secret (Actions: read and write on the repository) to use this from the dashboard.");
  const r = await fetch(`https://api.github.com/repos/${REPO(ctx)}${path}`, { ...init, headers: {
    Authorization: `Bearer ${ctx.env.GITHUB_TOKEN}`, Accept: "application/vnd.github+json", "User-Agent": "zeanahlab-dashboard",
    "X-GitHub-Api-Version": "2022-11-28", ...(init.headers || {}) } });
  if (!r.ok && r.status !== 204) throw new HttpError(502, `GitHub said ${r.status}: ${(await r.text()).slice(0, 200)}`);
  return r.status === 204 ? null : r.json();
}

api.get("/admin/deploys", async (ctx) => {
  requireAdmin(ctx);
  const runs = (await gh(ctx, "/actions/workflows/website.yml/runs?per_page=20")) as { workflow_runs: Record<string, any>[] };
  const view = (r: Record<string, any>) => ({ id: r.id, branch: r.head_branch, event: r.event, status: r.status, conclusion: r.conclusion,
    sha: String(r.head_sha).slice(0, 7), title: r.display_title, at: r.created_at, url: r.html_url });
  const all = runs.workflow_runs.map(view);
  const staging = all.find((r) => r.branch === "staging" && r.event === "push" && r.conclusion === "success") || null;
  const promotions = all.filter((r) => r.event === "workflow_dispatch");
  return json({ staging, lastPromotion: promotions[0] || null, runs: all.slice(0, 12), stagingUrl: "https://staging.zeanahlab.pages.dev" });
});

api.post("/admin/deploys/promote", async (ctx) => {
  const u = requireAdmin(ctx);
  const b = await body(ctx);
  const run = b.stagingRun ? String(Number(b.stagingRun)) : "";
  if (b.confirm !== "LIVE") throw new HttpError(400, "Type LIVE to confirm: this publishes staging to zeanahlab.com.");
  await gh(ctx, "/actions/workflows/website.yml/dispatches", { method: "POST", body: JSON.stringify({ ref: "main", inputs: { staging_run: run } }) });
  await audit(ctx, "deploy.promote", "site:live", { stagingRun: run || "newest", by: u.email });
  return json({ ok: true, message: "Promotion started. It takes about two minutes; the runs list shows it." }, 202);
});
