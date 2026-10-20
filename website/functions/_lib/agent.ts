// Controlled access for LLMs and agents (/api/agent/*).
//
// The owner makes a key on the admin page and ticks its scopes. An agent sends the key as
// "Authorization: Bearer zl_...", reads GET /api/agent/tools to learn exactly what it may do
// (names, descriptions, inputs as JSON Schema), and calls those routes. Every call is logged;
// each key has a per-minute limit and an optional expiry; anything that sends mail or changes
// what customers pay is never done by an agent -- it becomes a PROPOSAL the owner approves or
// rejects. Customer emails and addresses need their own scope, off unless ticked.

import { randomToken, sha256Hex } from "./crypto";
import { Ctx, HttpError, nowIso } from "./http";

export const SCOPES: Record<string, string> = {
  "stats:read": "The public numbers: list size, members, pads, backers, plaques.",
  "analytics:read": "Visits, the funnel, sources and what each earned, list growth, mail reads.",
  "catalogue:read": "Products, prices and their states.",
  "orders:read": "Orders: product, price, status, fulfilment, date -- no names, emails or addresses.",
  "list:read": "The list as counts: by status, by source, by tag -- no email addresses.",
  "list:read_emails": "Subscriber email addresses and names (personal data -- tick only if needed).",
  "network:read": "Network listings and pad numbers -- no contact details.",
  "campaigns:draft": "Write campaign drafts (saved, never sent).",
  "campaigns:propose_send": "Propose sending a campaign; the owner approves before anything goes.",
  "catalogue:propose": "Propose a price or product-state change; the owner approves before it applies.",
  "stories:write": "Bedtime stories: save new versions (never publish) and upload narration (scripts/export_storytime.py).",
};

export interface AgentKey { id: number; name: string; prefix: string; scopes: string[]; rate_per_min: number }

/** A new key: shown to the owner once, stored only as its hash. */
export async function makeKey(): Promise<{ key: string; prefix: string; hash: string }> {
  const prefix = randomToken(6).replace(/[-_]/g, "x").slice(0, 8);
  const key = `zl_${prefix}_${randomToken(30)}`;
  return { key, prefix, hash: await sha256Hex(key) };
}

async function log(ctx: Ctx, keyId: number | null, status: number, note?: string) {
  await ctx.env.DB.prepare("INSERT INTO api_calls(key_id, ts, method, path, status, note) VALUES(?, ?, ?, ?, ?, ?)")
    .bind(keyId, nowIso(), ctx.request.method, ctx.url.pathname.slice(0, 200), status, note ? note.slice(0, 200) : null).run();
}

/** Check the key, its expiry, its rate and the scope this route needs. Logs the call. */
export async function agentAuth(ctx: Ctx, scope?: string): Promise<AgentKey> {
  const raw = ctx.request.headers.get("Authorization")?.replace(/^Bearer /, "") || "";
  const m = /^zl_([A-Za-z0-9]{8})_/.exec(raw);
  const row = m ? await ctx.env.DB.prepare("SELECT * FROM api_keys WHERE prefix = ?").bind(m[1]).first<{
    id: number; name: string; prefix: string; key_hash: string; scopes: string; rate_per_min: number; expires_at: string | null; revoked_at: string | null }>() : null;
  if (!row || row.key_hash !== (await sha256Hex(raw))) {
    await log(ctx, null, 401, "bad key");
    throw new HttpError(401, "Not a valid agent key.");
  }
  if (row.revoked_at || (row.expires_at && row.expires_at < nowIso())) {
    await log(ctx, row.id, 401, row.revoked_at ? "revoked" : "expired");
    throw new HttpError(401, row.revoked_at ? "This key has been revoked." : "This key has expired.");
  }
  const recent = (await ctx.env.DB.prepare("SELECT COUNT(*) n FROM api_calls WHERE key_id = ? AND ts >= ?").bind(row.id, nowIso(-60_000)).first<{ n: number }>())!.n;
  if (recent >= row.rate_per_min) {
    await log(ctx, row.id, 429, "rate limit");
    throw new HttpError(429, `Limit is ${row.rate_per_min} calls a minute for this key.`);
  }
  const scopes = JSON.parse(row.scopes) as string[];
  if (scope && !scopes.includes(scope)) {
    await log(ctx, row.id, 403, `needs ${scope}`);
    throw new HttpError(403, `This key does not have the "${scope}" scope.`);
  }
  await log(ctx, row.id, 200);
  await ctx.env.DB.prepare("UPDATE api_keys SET last_used_at = ? WHERE id = ?").bind(nowIso(), row.id).run();
  return { id: row.id, name: row.name, prefix: row.prefix, scopes, rate_per_min: row.rate_per_min };
}

/** What an agent may do, described so an LLM can call it as a tool. */
export const TOOLS = [
  { name: "get_stats", scope: "stats:read", method: "GET", path: "/api/agent/stats", approval: false,
    description: "The site's public numbers: subscribers, members, pads, backers, recorded backing against the goal, founder plaques.",
    input: { type: "object", properties: {} } },
  { name: "get_analytics", scope: "analytics:read", method: "GET", path: "/api/agent/analytics", approval: false,
    description: "First-party analytics for the last N days: visitors by day, top pages, sources, the funnel, conversions and revenue by source, list growth, mail opens and clicks.",
    input: { type: "object", properties: { days: { type: "integer", minimum: 1, maximum: 365, default: 30 } } } },
  { name: "get_catalogue", scope: "catalogue:read", method: "GET", path: "/api/agent/catalogue", approval: false,
    description: "Every product with its prices (in cents), status (live, preorder, waitlist, hidden) and shipping note.",
    input: { type: "object", properties: {} } },
  { name: "get_orders", scope: "orders:read", method: "GET", path: "/api/agent/orders", approval: false,
    description: "Recent paid orders: product, price option, amount, fulfilment state, date. No personal data.",
    input: { type: "object", properties: { limit: { type: "integer", minimum: 1, maximum: 500, default: 100 } } } },
  { name: "get_list_summary", scope: "list:read", method: "GET", path: "/api/agent/list", approval: false,
    description: "The email list as counts: by status, by first source and campaign, by tag; campaign and sequence results.",
    input: { type: "object", properties: {} } },
  { name: "get_subscribers", scope: "list:read_emails", method: "GET", path: "/api/agent/subscribers", approval: false,
    description: "Subscribers with email, name, status, source and tags. Personal data: use only for the owner's own purposes.",
    input: { type: "object", properties: { status: { type: "string", enum: ["confirmed", "unconfirmed", "unsubscribed", "bounced", "complained"] } } } },
  { name: "get_network", scope: "network:read", method: "GET", path: "/api/agent/network", approval: false,
    description: "Network listings (pads, builders, recyclers...) with each pad's numbers. No contact details.",
    input: { type: "object", properties: {} } },
  { name: "draft_campaign", scope: "campaigns:draft", method: "POST", path: "/api/agent/campaigns", approval: false,
    description: "Save a campaign DRAFT for the owner to read. Nothing is sent. Body is plain text; tokens {{name}} {{book_pages}} {{book_figures}} {{frame_hours}} {{sample_pages}} {{dome_ft}} {{book_price}} {{site}} are filled in per reader.",
    input: { type: "object", required: ["name", "identity", "subject", "body"], properties: {
      name: { type: "string" }, identity: { type: "string", enum: ["owner", "donovan"] }, subject: { type: "string" }, body: { type: "string" },
      tags: { type: "array", items: { type: "string" } }, source: { type: "string" } } } },
  { name: "propose_send_campaign", scope: "campaigns:propose_send", method: "POST", path: "/api/agent/proposals", approval: true,
    description: "Ask the owner to send a draft campaign to its segment. Nothing is sent until the owner approves on the admin page.",
    input: { type: "object", required: ["action", "campaignId", "reason"], properties: {
      action: { const: "campaign.queue" }, campaignId: { type: "integer" }, reason: { type: "string" } } } },
  { name: "propose_price_change", scope: "catalogue:propose", method: "POST", path: "/api/agent/proposals", approval: true,
    description: "Ask the owner to change a price (in dollars) or a product's status. Applies only when the owner approves.",
    input: { type: "object", required: ["action", "product", "reason"], properties: {
      action: { enum: ["price.set", "product.status"] }, product: { type: "string" }, price: { type: "string", description: "price key, e.g. standard" },
      amount: { type: "number" }, status: { enum: ["live", "preorder", "waitlist", "hidden"] }, reason: { type: "string" } } } },
  { name: "get_story_narration_todo", scope: "stories:write", method: "GET", path: "/api/agent/stories/{slug}/narration", approval: false,
    description: "A bedtime story's pages that have no narration yet in version v (default the newest): id, narration key, the words to show and the words to speak, and the voice.",
    input: { type: "object", required: ["slug"], properties: { slug: { type: "string" }, v: { type: "integer" } } } },
  { name: "upload_story_narration", scope: "stories:write", method: "POST", path: "/api/agent/stories/{slug}/narration", approval: false,
    description: "Upload one page's narration: its key, base64 audio, contentType, duration in seconds and word timings [[t0, t1, charStart, charEnd], ...].",
    input: { type: "object", required: ["slug", "key", "audio", "duration"], properties: { slug: { type: "string" }, key: { type: "string" }, audio: { type: "string" },
      contentType: { type: "string" }, duration: { type: "number" }, words: { type: "array" } } } },
  { name: "save_story_version", scope: "stories:write", method: "POST", path: "/api/agent/stories/{slug}/versions", approval: false,
    description: "Save a new version of a bedtime story (append-only; only the owner publishes). doc is {title, series, voice, figures, pages: [{id, kind, scene, shot, text}]}.",
    input: { type: "object", required: ["slug", "doc"], properties: { slug: { type: "string" }, doc: { type: "object" }, note: { type: "string" } } } },
  { name: "get_proposal", scope: null, method: "GET", path: "/api/agent/proposals/{id}", approval: false,
    description: "Whether a proposal this key made was approved, rejected or is still waiting.",
    input: { type: "object", required: ["id"], properties: { id: { type: "integer" } } } },
] as const;
