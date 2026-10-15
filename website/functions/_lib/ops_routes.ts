// /api/ops/clock -- the zeanahlab-ops Worker's once-a-minute knock -- and the owner's
// controls for the operations engine: automations, the job log, notices, the assistant.

import { MODEL, aiReady } from "./ai";
import { requireAdmin } from "./auth";
import { sameString } from "./crypto";
import { Ctx, HttpError, body, json, nowIso, num, text } from "./http";
import { ACTIONS, TRIGGERS, assistant, audit, clock, getSetting, runJob } from "./ops";
import api from "./routes";

/** The Worker proves itself with OPS_TOKEN; the owner may also press the button. */
function clockCaller(ctx: Ctx) {
  const given = ctx.request.headers.get("Authorization")?.replace(/^Bearer /, "") || "";
  if (ctx.env.OPS_TOKEN && given && sameString(given, ctx.env.OPS_TOKEN)) return "worker";
  requireAdmin(ctx);
  return "owner";
}

api.post("/ops/clock", async (ctx) => {
  const who = clockCaller(ctx);
  const r = await clock(ctx);
  if (who === "owner") await audit(ctx, "clock.run", null, r);
  return json(r);
});

api.get("/admin/ops", async (ctx) => {
  requireAdmin(ctx);
  const db = ctx.env.DB;
  const all = async (sql: string, ...a: unknown[]) => (await db.prepare(sql).bind(...a).all()).results;
  const last = await getSetting(ctx, "clock.last");
  return json({
    triggers: TRIGGERS,
    actions: ACTIONS,
    automations: await all("SELECT * FROM automations ORDER BY active DESC, id"),
    jobs: await all("SELECT j.id, j.label, j.status, j.attempts, j.run_at, j.started_at, j.finished_at, j.result, j.error, e.type event FROM jobs j LEFT JOIN ops_events e ON e.id = j.event_id ORDER BY j.id DESC LIMIT 100"),
    notices: await all("SELECT * FROM notices ORDER BY (read_at IS NULL) DESC, id DESC LIMIT 60"),
    unread: (await db.prepare("SELECT COUNT(*) n FROM notices WHERE read_at IS NULL").first<{ n: number }>())!.n,
    events: await all("SELECT type, COUNT(*) n, MAX(created_at) last FROM ops_events WHERE created_at >= ? GROUP BY type ORDER BY n DESC", nowIso(-30 * 86_400_000)),
    ai: {
      connected: aiReady(ctx.env), model: MODEL,
      usage: await all("SELECT purpose, COUNT(*) calls, SUM(ok) ok, SUM(ms) ms, SUM(input_chars) input_chars, SUM(output_chars) output_chars FROM ai_runs WHERE created_at >= ? GROUP BY purpose", nowIso(-30 * 86_400_000)),
    },
    clock: { last, running: Boolean(last && Date.parse(last) > Date.now() - 5 * 60_000), tokenSet: Boolean(ctx.env.OPS_TOKEN) },
    audit: await all("SELECT * FROM audit_log ORDER BY id DESC LIMIT 100"),
  });
});

function automationFields(b: Record<string, unknown>, partial: boolean) {
  const f: Record<string, unknown> = {};
  if (!partial || "name" in b) f.name = text(b, "name", { min: 2, max: 80, required: true });
  if ("description" in b) f.description = text(b, "description", { max: 400 });
  if (!partial || "trigger" in b) {
    const t = String(b.trigger || "");
    if (!(t in TRIGGERS)) throw new HttpError(400, `trigger is one of: ${Object.keys(TRIGGERS).join(", ")}.`);
    f.trigger = t;
  }
  if ("conditions" in b) {
    const c = b.conditions;
    if (!c || typeof c !== "object" || Array.isArray(c)) throw new HttpError(400, "conditions is an object of field: value.");
    f.conditions = JSON.stringify(c);
  }
  if (!partial || "actions" in b) {
    const a = b.actions;
    if (!Array.isArray(a) || !a.length || a.length > 10) throw new HttpError(400, "actions is a list of one to ten actions.");
    for (const x of a) if (!x || typeof x !== "object" || !((x as { type?: string }).type! in ACTIONS)) throw new HttpError(400, `Each action's type is one of: ${Object.keys(ACTIONS).join(", ")}.`);
    f.actions = JSON.stringify(a);
  }
  if ("delayMinutes" in b) f.delay_minutes = num(b, "delayMinutes", { min: 0, max: 60 * 24 * 60 }) ?? 0;
  if ("active" in b) f.active = b.active === true ? 1 : 0;
  return f;
}

api.post("/admin/automations", async (ctx) => {
  requireAdmin(ctx);
  const f = automationFields(await body(ctx), false);
  const cols = Object.keys(f);
  const r = await ctx.env.DB.prepare(`INSERT INTO automations(${cols.join(", ")}, created_by, created_at, updated_at) VALUES(${cols.map(() => "?").join(", ")}, 'owner', ?, ?) RETURNING id`)
    .bind(...Object.values(f), nowIso(), nowIso()).first<{ id: number }>();
  await audit(ctx, "automation.create", `automation:${r!.id}`, f);
  return json({ id: r!.id }, 201);
});

api.patch("/admin/automations/:id", async (ctx) => {
  requireAdmin(ctx);
  const f = automationFields(await body(ctx), true);
  if (!Object.keys(f).length) throw new HttpError(400, "Nothing to change.");
  const r = await ctx.env.DB.prepare(`UPDATE automations SET ${Object.keys(f).map((k) => `${k} = ?`).join(", ")}, updated_at = ? WHERE id = ?`)
    .bind(...Object.values(f), nowIso(), Number(ctx.params.id)).run();
  if (!r.meta.changes) throw new HttpError(404, "No such automation.");
  await audit(ctx, "automation.edit", `automation:${ctx.params.id}`, f);
  return json({ ok: true });
});

api.delete("/admin/automations/:id", async (ctx) => {
  requireAdmin(ctx);
  await ctx.env.DB.prepare("DELETE FROM automations WHERE id = ?").bind(Number(ctx.params.id)).run();
  await audit(ctx, "automation.delete", `automation:${ctx.params.id}`);
  return json({ ok: true });
});

/** Run an automation once, now, on a test event (the fields you give, or none). */
api.post("/admin/automations/:id/test", async (ctx) => {
  requireAdmin(ctx);
  const a = await ctx.env.DB.prepare("SELECT id, name, trigger FROM automations WHERE id = ?").bind(Number(ctx.params.id)).first<{ id: number; name: string; trigger: string }>();
  if (!a) throw new HttpError(404, "No such automation.");
  const b = await body(ctx);
  const data = { test: true, ...(b.data && typeof b.data === "object" ? b.data as Record<string, unknown> : {}) };
  const ev = await ctx.env.DB.prepare("INSERT INTO ops_events(type, data, created_at) VALUES(?, ?, ?) RETURNING id").bind(a.trigger, JSON.stringify(data), nowIso()).first<{ id: number }>();
  const j = await ctx.env.DB.prepare("INSERT INTO jobs(automation_id, event_id, label, run_at, created_at) VALUES(?, ?, ?, ?, ?) RETURNING id")
    .bind(a.id, ev!.id, `${a.name} (test)`, nowIso(), nowIso()).first<{ id: number }>();
  await audit(ctx, "automation.test", `automation:${a.id}`, data);
  const status = await runJob(ctx, j!.id);
  const job = await ctx.env.DB.prepare("SELECT status, result, error FROM jobs WHERE id = ?").bind(j!.id).first();
  return json({ status, job });
});

api.post("/admin/jobs/:id/retry", async (ctx) => {
  requireAdmin(ctx);
  await ctx.env.DB.prepare("UPDATE jobs SET status = 'queued', attempts = 0, run_at = ? WHERE id = ? AND status IN ('failed', 'cancelled')").bind(nowIso(), Number(ctx.params.id)).run();
  await audit(ctx, "job.retry", `job:${ctx.params.id}`);
  return json({ status: await runJob(ctx, Number(ctx.params.id)) });
});

api.post("/admin/jobs/:id/cancel", async (ctx) => {
  requireAdmin(ctx);
  await ctx.env.DB.prepare("UPDATE jobs SET status = 'cancelled', finished_at = ? WHERE id = ? AND status = 'queued'").bind(nowIso(), Number(ctx.params.id)).run();
  await audit(ctx, "job.cancel", `job:${ctx.params.id}`);
  return json({ ok: true });
});

api.post("/admin/notices/read", async (ctx) => {
  requireAdmin(ctx);
  const b = await body(ctx);
  if (b.all === true) await ctx.env.DB.prepare("UPDATE notices SET read_at = ? WHERE read_at IS NULL").bind(nowIso()).run();
  else for (const id of (Array.isArray(b.ids) ? b.ids : []).slice(0, 200)) await ctx.env.DB.prepare("UPDATE notices SET read_at = COALESCE(read_at, ?) WHERE id = ?").bind(nowIso(), Number(id)).run();
  return json({ ok: true });
});

api.get("/admin/notices/unread", async (ctx) => {
  requireAdmin(ctx);
  return json({ unread: (await ctx.env.DB.prepare("SELECT COUNT(*) n FROM notices WHERE read_at IS NULL").first<{ n: number }>())!.n });
});

api.post("/admin/assistant", async (ctx) => {
  requireAdmin(ctx);
  const b = await body(ctx);
  const q = text(b, "question", { min: 3, max: 1000, required: true })!;
  return json(await assistant(ctx, q, num(b, "days", { min: 1, max: 365 }) ?? 30));
});

/** Is everything wired? Says which kind of key each secret holds -- never the key -- and whether
 *  Stripe and Workers AI answer. For the owner's page, and for checking a deploy. */
api.get("/ops/health", async (ctx) => {
  clockCaller(ctx);
  const env = ctx.env;
  const kind = (v: string | undefined) => (v ? v.replace(/^(sk_live|sk_test|rk_live|rk_test|whsec|pk_live|pk_test)_.*$/, "$1") : "missing");
  const stripeKey = kind(env.STRIPE_SECRET_KEY);
  let stripe = "not set";
  if (env.STRIPE_SECRET_KEY) {
    const r = await fetch("https://api.stripe.com/v1/checkout/sessions?limit=1", { headers: { Authorization: `Bearer ${env.STRIPE_SECRET_KEY}` } });
    const j = (await r.json().catch(() => ({}))) as { error?: { message?: string } };
    stripe = r.ok ? "ok: Stripe accepts the key" : `refused (${r.status}): ${(j.error?.message || "").replace(/(sk|rk|whsec)_\w+\*+\w+/g, "[key]")}`;
  }
  let ai = "not connected";
  if (env.AI) {
    try { ai = `ok: ${(await (await import("./ai")).ask(env, "health", "Reply with the single word OK.", "Are you there?", 5)).slice(0, 20)}`; } catch (e) { ai = (e as Error).message; }
  }
  return json({
    stripe: { secretKey: stripeKey, webhookSecret: kind(env.STRIPE_WEBHOOK_SECRET), check: stripe,
      problems: [
        stripeKey === "whsec" && "STRIPE_SECRET_KEY holds a webhook signing secret (whsec_...); it needs the secret API key (sk_live_... or rk_live_...).",
        env.STRIPE_WEBHOOK_SECRET && !env.STRIPE_WEBHOOK_SECRET.startsWith("whsec_") && "STRIPE_WEBHOOK_SECRET should start with whsec_.",
      ].filter(Boolean) },
    ai, mail: { mailerToken: Boolean(env.MAILER_TOKEN), postalAddress: Boolean(env.MAIL_POSTAL_ADDRESS) },
    clock: { last: await getSetting(ctx, "clock.last") },
    secrets: { session: Boolean(env.SESSION_SECRET), admins: Boolean(env.ADMIN_EMAILS), ops: Boolean(env.OPS_TOKEN) },
  });
});
