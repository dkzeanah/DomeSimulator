// /api/agent/* -- LLM and agent access, under the owner's control -- and the admin routes that
// make keys, read the call log and decide proposals. Registered on the same router as every
// other route (functions/api/[[path]].ts imports this file).

import { SCOPES, TOOLS, agentAuth, makeKey } from "./agent";
import { report } from "./analytics";
import { requireAdmin, requireOwner } from "./auth";
import { Ctx, HttpError, body, json, nowIso, num, text } from "./http";
import { queueCampaign } from "./mail";
import { audit, emit } from "./ops";
import api, { catalogue } from "./routes";

/** Reuse a public route's answer (the same numbers the pages show). */
async function inner(ctx: Ctx, method: string, path: string) {
  const hit = api.match(method, path)!;
  return (await hit.handler({ ...ctx, params: hit.params })).json();
}

api.get("/agent/tools", async (ctx) => {
  const key = await agentAuth(ctx);
  return json({
    key: { name: key.name, prefix: key.prefix, scopes: key.scopes, ratePerMinute: key.rate_per_min },
    rules: [
      "Send the key as: Authorization: Bearer <key>.",
      "Only the tools below are available to this key; others answer 403.",
      "Tools marked approval:true never act: they create a proposal the owner approves or rejects. Check it with get_proposal.",
      "Every call is logged with this key's name.",
    ],
    tools: TOOLS.filter((t) => !t.scope || key.scopes.includes(t.scope)),
  });
});

api.get("/agent/stats", async (ctx) => {
  await agentAuth(ctx, "stats:read");
  return json(await inner(ctx, "GET", "/stats"));
});

api.get("/agent/analytics", async (ctx) => {
  await agentAuth(ctx, "analytics:read");
  return json(await report(ctx, Math.min(365, Math.max(1, Number(ctx.url.searchParams.get("days") || 30)))));
});

api.get("/agent/catalogue", async (ctx) => {
  await agentAuth(ctx, "catalogue:read");
  return json({ products: await catalogue(ctx) });
});

api.get("/agent/orders", async (ctx) => {
  await agentAuth(ctx, "orders:read");
  const limit = Math.min(500, Number(ctx.url.searchParams.get("limit") || 100));
  return json({ orders: (await ctx.env.DB.prepare(
    "SELECT ref, book_slug product, price_key, amount_cents, currency, status, fulfillment, provider, created_at, paid_at FROM orders WHERE status = 'paid' AND provider != 'owner' ORDER BY id DESC LIMIT ?",
  ).bind(limit).all()).results });
});

api.get("/agent/list", async (ctx) => {
  await agentAuth(ctx, "list:read");
  const db = ctx.env.DB;
  const all = async (sql: string) => (await db.prepare(sql).all()).results;
  return json({
    byStatus: await all("SELECT status, COUNT(*) n FROM subscribers GROUP BY status"),
    mailable: (await db.prepare("SELECT COUNT(*) n FROM subscribers WHERE status = 'confirmed' AND marketing_consent = 1").first<{ n: number }>())!.n,
    bySource: await all("SELECT COALESCE(first_source, source) source, first_campaign campaign, COUNT(*) n FROM subscribers GROUP BY 1, 2 ORDER BY n DESC LIMIT 30"),
    byTag: await all("SELECT tag, COUNT(*) n FROM subscriber_tags GROUP BY tag ORDER BY n DESC"),
    campaigns: await all(`SELECT c.id, c.name, c.identity, c.subject, c.status, c.queued_count,
      (SELECT COUNT(*) FROM outbox o WHERE o.campaign_id = c.id AND o.status = 'sent') sent,
      (SELECT COUNT(DISTINCT e.outbox_id) FROM email_events e JOIN outbox o ON o.id = e.outbox_id WHERE o.campaign_id = c.id AND e.kind = 'open') opened,
      (SELECT COUNT(DISTINCT e.outbox_id) FROM email_events e JOIN outbox o ON o.id = e.outbox_id WHERE o.campaign_id = c.id AND e.kind = 'click') clicked
      FROM campaigns c ORDER BY c.id DESC LIMIT 50`),
    sequences: await all("SELECT key, name, trigger, active FROM sequences"),
  });
});

api.get("/agent/subscribers", async (ctx) => {
  await agentAuth(ctx, "list:read_emails");
  const st = ctx.url.searchParams.get("status");
  const cols = "SELECT email, name, status, first_source, first_campaign, created_at FROM subscribers";
  const q = st ? ctx.env.DB.prepare(`${cols} WHERE status = ? ORDER BY id DESC LIMIT 2000`).bind(st) : ctx.env.DB.prepare(`${cols} ORDER BY id DESC LIMIT 2000`);
  return json({ subscribers: (await q.all()).results });
});

api.get("/agent/network", async (ctx) => {
  await agentAuth(ctx, "network:read");
  return json(await inner({ ...ctx, user: null }, "GET", "/network"));   // as a visitor: no contacts
});

api.post("/agent/campaigns", async (ctx) => {
  const key = await agentAuth(ctx, "campaigns:draft");
  const b = await body(ctx);
  const identity = text(b, "identity", { max: 20, required: true })!;
  if (!(await ctx.env.DB.prepare("SELECT 1 FROM identities WHERE key = ?").bind(identity).first())) throw new HttpError(400, "No such identity.");
  const seg = { tags: Array.isArray(b.tags) ? b.tags.map(String).slice(0, 10) : [], source: text(b, "source", { max: 80 }) || undefined };
  const r = await ctx.env.DB.prepare("INSERT INTO campaigns(name, identity, subject, body, segment, created_at) VALUES(?, ?, ?, ?, ?, ?) RETURNING id")
    .bind(`[${key.name}] ${text(b, "name", { min: 1, max: 80, required: true })}`, identity, text(b, "subject", { min: 1, max: 160, required: true }),
      text(b, "body", { min: 1, max: 20000, required: true }), JSON.stringify(seg), nowIso()).first<{ id: number }>();
  await audit(ctx, "campaign.draft", `campaign:${r!.id}`, null, { kind: "agent", id: key.id, name: key.name });
  return json({ id: r!.id, status: "draft", note: "Saved as a draft. Nothing was sent." }, 201);
});

api.post("/agent/proposals", async (ctx) => {
  const b = await body(ctx);
  const action = String(b.action || "");
  const scope = action === "campaign.queue" ? "campaigns:propose_send" : ["price.set", "product.status"].includes(action) ? "catalogue:propose" : null;
  if (!scope) throw new HttpError(400, "action is campaign.queue, price.set or product.status.");
  const key = await agentAuth(ctx, scope);
  const reason = text(b, "reason", { min: 5, max: 1000, required: true });
  let payload: Record<string, unknown>;
  if (action === "campaign.queue") {
    const id = num(b, "campaignId", { min: 1, required: true })!;
    const c = await ctx.env.DB.prepare("SELECT status FROM campaigns WHERE id = ?").bind(id).first<{ status: string }>();
    if (!c || c.status !== "draft") throw new HttpError(400, "That campaign is not a draft.");
    payload = { campaignId: id };
  } else {
    const product = text(b, "product", { max: 80, required: true })!;
    if (!(await ctx.env.DB.prepare("SELECT 1 FROM products WHERE slug = ?").bind(product).first())) throw new HttpError(400, "No such product.");
    if (action === "price.set") {
      payload = { product, price: text(b, "price", { max: 40 }) || "standard", amount: num(b, "amount", { min: 0, max: 1e6, required: true }) };
    } else {
      const status = String(b.status || "");
      if (!["live", "preorder", "waitlist", "hidden"].includes(status)) throw new HttpError(400, "status is live, preorder, waitlist or hidden.");
      payload = { product, status };
    }
  }
  const r = await ctx.env.DB.prepare("INSERT INTO agent_proposals(key_id, action, payload, reason, created_at) VALUES(?, ?, ?, ?, ?) RETURNING id")
    .bind(key.id, action, JSON.stringify(payload), reason, nowIso()).first<{ id: number }>();
  await emit(ctx, "proposal.created", { proposalId: r!.id, action, key: key.name, reason: reason || "" });
  await audit(ctx, "proposal.create", `proposal:${r!.id}`, payload, { kind: "agent", id: key.id, name: key.name });
  return json({ id: r!.id, status: "pending", note: "Waiting for the owner. Nothing has changed yet." }, 201);
});

api.get("/agent/proposals/:id", async (ctx) => {
  const key = await agentAuth(ctx);
  const p = await ctx.env.DB.prepare("SELECT id, action, payload, reason, status, result, created_at, decided_at FROM agent_proposals WHERE id = ? AND key_id = ?")
    .bind(Number(ctx.params.id), key.id).first();
  if (!p) throw new HttpError(404, "No proposal from this key with that number.");
  return json({ proposal: p });
});

// ---------------------------------------------------------------- the owner's controls

api.get("/admin/agents", async (ctx) => {
  requireAdmin(ctx);
  const db = ctx.env.DB;
  return json({
    scopes: SCOPES,
    keys: (await db.prepare("SELECT id, name, prefix, scopes, rate_per_min, created_at, expires_at, last_used_at, revoked_at, (SELECT COUNT(*) FROM api_calls c WHERE c.key_id = k.id) calls FROM api_keys k ORDER BY id DESC").all()).results,
    calls: (await db.prepare("SELECT c.ts, c.method, c.path, c.status, c.note, k.name FROM api_calls c LEFT JOIN api_keys k ON k.id = c.key_id ORDER BY c.id DESC LIMIT 100").all()).results,
    proposals: (await db.prepare("SELECT p.*, k.name key_name FROM agent_proposals p LEFT JOIN api_keys k ON k.id = p.key_id ORDER BY (p.status = 'pending') DESC, p.id DESC LIMIT 100").all()).results,
  });
});

api.post("/admin/agents", async (ctx) => {
  const u = requireOwner(ctx);
  const b = await body(ctx);
  const scopes = (Array.isArray(b.scopes) ? b.scopes.map(String) : []).filter((s) => s in SCOPES);
  if (!scopes.length) throw new HttpError(400, "Tick at least one scope.");
  const days = num(b, "days", { min: 0, max: 3650 });
  const k = await makeKey();
  await ctx.env.DB.prepare("INSERT INTO api_keys(name, prefix, key_hash, scopes, rate_per_min, created_by, created_at, expires_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?)")
    .bind(text(b, "name", { min: 2, max: 80, required: true }), k.prefix, k.hash, JSON.stringify(scopes), num(b, "ratePerMin", { min: 1, max: 600 }) ?? 30,
      u.id, nowIso(), days ? nowIso(days * 86_400_000) : null).run();
  await audit(ctx, "agent_key.create", `key:${k.prefix}`, { scopes });
  return json({ key: k.key, note: "Copy it now: it is shown once and stored only as a hash." }, 201);
});

api.post("/admin/agents/:id/revoke", async (ctx) => {
  requireOwner(ctx);
  await ctx.env.DB.prepare("UPDATE api_keys SET revoked_at = COALESCE(revoked_at, ?) WHERE id = ?").bind(nowIso(), Number(ctx.params.id)).run();
  await audit(ctx, "agent_key.revoke", `key:${ctx.params.id}`);
  return json({ ok: true });
});

/** Approve (and carry out) or reject an agent's proposal. */
api.post("/admin/proposals/:id", async (ctx) => {
  const u = requireAdmin(ctx);
  const b = await body(ctx);
  const p = await ctx.env.DB.prepare("SELECT * FROM agent_proposals WHERE id = ? AND status = 'pending'").bind(Number(ctx.params.id)).first<{ id: number; action: string; payload: string }>();
  if (!p) throw new HttpError(404, "No pending proposal with that number.");
  const decide = (status: string, result: string) => ctx.env.DB.prepare("UPDATE agent_proposals SET status = ?, result = ?, decided_at = ?, decided_by = ? WHERE id = ?")
    .bind(status, result, nowIso(), u.id, p.id).run()
    .then(() => audit(ctx, `proposal.${status}`, `proposal:${p.id}`, { action: p.action, result }));
  if (b.decision !== "approve") {
    await decide("rejected", "Rejected by the owner.");
    return json({ ok: true, status: "rejected" });
  }
  const x = JSON.parse(p.payload);
  try {
    let result = "";
    if (p.action === "campaign.queue") result = `Queued to ${await queueCampaign(ctx, Number(x.campaignId))} subscribers.`;
    else if (p.action === "price.set") {
      const r = await ctx.env.DB.prepare("UPDATE prices SET amount_cents = ? WHERE product = ? AND key = ?").bind(Math.round(Number(x.amount) * 100), x.product, x.price).run();
      if (!r.meta.changes) throw new HttpError(404, "That price no longer exists.");
      result = `${x.product}/${x.price} is now $${Number(x.amount).toFixed(2)}.`;
    } else if (p.action === "listing.hide") {
      await ctx.env.DB.prepare("UPDATE listings SET visible = 0, updated_at = ? WHERE id = ?").bind(nowIso(), Number(x.listingId)).run();
      result = `Listing #${x.listingId} is hidden. Its owner can still see it in their account.`;
    } else if (p.action === "product.status") {
      await ctx.env.DB.prepare("UPDATE products SET status = ?, updated_at = ? WHERE slug = ?").bind(x.status, nowIso(), x.product).run();
      result = `${x.product} is now ${x.status}.`;
    }
    await decide("approved", result);
    return json({ ok: true, status: "approved", result });
  } catch (e) {
    await decide("failed", (e as Error).message);
    throw e;
  }
});
