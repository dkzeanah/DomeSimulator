// The list's machinery, all on the site: who may be mailed, what a message says, the queue it
// waits in, and the signed links that confirm, unsubscribe and count clicks. No third party:
// the owner's own mail program collects the queue (/api/mailer/*), delivers, and reports.
//
// Rules the code enforces, not the copy:
//   * marketing (campaign, sequence) goes only to subscribers who consented, confirmed by the
//     double opt-in link, and are not suppressed;
//   * every marketing message carries a one-click unsubscribe (RFC 8058 header and a link) and
//     the sender's postal address (CAN-SPAM); with no MAIL_POSTAL_ADDRESS set, marketing is
//     refused -- confirmations and receipts still go;
//   * an unsubscribe, bounce or complaint suppresses the address for good.

import facts from "../../src/generated/facts.json";
import { hmac, sameString } from "./crypto";
import { Ctx, Env, HttpError, nowIso } from "./http";

export type Kind = "confirm" | "transactional" | "campaign" | "sequence";
const MARKETING: Kind[] = ["campaign", "sequence"];

const esc = (s: string) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]!);
export const site = (env: Env, ctx?: Ctx) => (env.PUBLIC_URL || ctx?.url.origin || "https://www.zeanahlab.com").replace(/\/$/, "");

function secret(env: Env) {
  if (!env.SESSION_SECRET) throw new HttpError(500, "SESSION_SECRET is not set.");
  return env.SESSION_SECRET;
}

// ---------------------------------------------------------------- signed links

/** A token naming one subscriber for one purpose; no database row, cannot be forged. */
export async function subscriberToken(env: Env, purpose: "confirm" | "unsub", id: number) {
  return `${id}.${(await hmac(secret(env), `${purpose}:${id}`)).slice(0, 32)}`;
}

export async function readSubscriberToken(env: Env, purpose: "confirm" | "unsub", token: string): Promise<number | null> {
  const [id, sig] = String(token || "").split(".");
  if (!id || !sig || !/^\d+$/.test(id)) return null;
  return sameString(sig, (await hmac(secret(env), `${purpose}:${id}`)).slice(0, 32)) ? Number(id) : null;
}

async function clickSig(env: Env, outboxId: number, url: string) {
  return (await hmac(secret(env), `click:${outboxId}:${url}`)).slice(0, 22);
}

export async function checkClick(env: Env, outboxId: number, url: string, sig: string) {
  return sameString(sig, await clickSig(env, outboxId, url));
}

// ---------------------------------------------------------------- the words

/** The figures a body may name, from the same facts the pages read. */
async function tokens(ctx: Ctx, name: string | null): Promise<Record<string, string>> {
  const c = facts.bookFacts.digital;
  const price = await ctx.env.DB.prepare("SELECT amount_cents FROM prices WHERE product = 'the-40-hour-cabin' AND key = 'standard'").first<{ amount_cents: number }>();
  return {
    name: name || "there",
    site: site(ctx.env, ctx),
    book_pages: String(c.pages ?? ""),
    book_figures: String(c.figures),
    frame_hours: String(c.numbers.frameHours),
    sample_pages: String(facts.bookFacts.sample.pages),
    dome_ft: String(facts.dome.acrossFt),
    book_price: price ? `$${(price.amount_cents / 100).toFixed(price.amount_cents % 100 ? 2 : 0)}` : "",
  };
}

export const fill = (text: string, t: Record<string, string>) => text.replace(/\{\{\s*(\w+)\s*\}\}/g, (m, k) => (k in t ? t[k] : m));

/** Plain text -> simple, readable HTML: paragraphs, and bare links made clickable. */
function toHtml(text: string) {
  return text.split(/\n{2,}/).map((p) => `<p style="margin:0 0 14px">${esc(p).replace(/\n/g, "<br>").replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1">$1</a>')}</p>`).join("");
}

/** Count clicks through this domain: every link in the HTML goes via a signed redirect. */
async function track(env: Env, base: string, outboxId: number, html: string) {
  const urls = [...new Set([...html.matchAll(/href="(https?:\/\/[^"]+)"/g)].map((m) => m[1]))];
  for (const u of urls) {
    const via = `${base}/api/t/c/${outboxId}?u=${encodeURIComponent(u)}&s=${await clickSig(env, outboxId, u)}`;
    html = html.split(`href="${u}"`).join(`href="${via}"`);
  }
  return html + `<img src="${base}/api/t/o/${outboxId}.gif" width="1" height="1" alt="" style="display:block;border:0">`;
}

// ---------------------------------------------------------------- the queue

interface Sub { id: number; email: string; name: string | null; marketing_consent: number; status: string }

export async function suppressed(ctx: Ctx, email: string) {
  return Boolean(await ctx.env.DB.prepare("SELECT 1 FROM suppressions WHERE email = ?").bind(email).first());
}

/** May this subscriber get this kind of message? Returns the reason when not. */
export async function mayMail(ctx: Ctx, s: Sub, kind: Kind): Promise<string | null> {
  if (await suppressed(ctx, s.email)) return "suppressed";
  if (MARKETING.includes(kind)) {
    if (!s.marketing_consent) return "no consent";
    if (s.status !== "confirmed") return `not confirmed (${s.status})`;
    if (!ctx.env.MAIL_POSTAL_ADDRESS) return "no postal address set (MAIL_POSTAL_ADDRESS)";
  }
  return null;
}

/** Put one message in the queue. Returns the outbox id, or null with the reason it was not queued. */
export async function enqueue(ctx: Ctx, o: {
  sub: Sub; identity: string; kind: Kind; subject: string; body: string;
  campaignId?: number | null; sequence?: string | null; step?: number | null; extraTokens?: Record<string, string>;
}): Promise<{ id: number | null; why?: string }> {
  const why = await mayMail(ctx, o.sub, o.kind);
  if (why) return { id: null, why };
  const t = { ...(await tokens(ctx, o.sub.name)), ...(o.extraTokens || {}) };
  const subject = fill(o.subject, t);
  let text = fill(o.body, t);
  const base = site(ctx.env, ctx);
  const r = await ctx.env.DB.prepare(
    "INSERT INTO outbox(subscriber_id, to_email, identity, kind, campaign_id, sequence, step, subject, html, text, created_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?, '', '', ?) RETURNING id",
  ).bind(o.sub.id, o.sub.email, o.identity, o.kind, o.campaignId ?? null, o.sequence ?? null, o.step ?? null, subject, nowIso()).first<{ id: number }>();
  const id = r!.id;
  if (MARKETING.includes(o.kind)) {
    const unsub = `${base}/unsubscribe?t=${await subscriberToken(ctx.env, "unsub", o.sub.id)}`;
    text += `\n\n--\nYou are getting this because you asked for build updates at ${base}.\nUnsubscribe in one click: ${unsub}\n${ctx.env.MAIL_POSTAL_ADDRESS}`;
  }
  let html = `<div style="font-family:Georgia,serif;font-size:16px;line-height:1.55;color:#1d1a15;max-width:600px">${toHtml(text)}</div>`;
  html = await track(ctx.env, base, id, html);
  await ctx.env.DB.prepare("UPDATE outbox SET html = ?, text = ? WHERE id = ?").bind(html, text, id).run();
  return { id };
}

/** The double opt-in letter: one link, and nothing else is sent until it is clicked. */
export async function queueConfirm(ctx: Ctx, sub: Sub) {
  const link = `${site(ctx.env, ctx)}/confirm?t=${await subscriberToken(ctx.env, "confirm", sub.id)}`;
  return enqueue(ctx, {
    sub, identity: "owner", kind: "confirm", subject: "Confirm your build updates",
    body: `Hi {{name}},\n\nYou asked for build updates from Zeanah Lab. Confirm with one click:\n${link}\n\nIf this was not you, ignore this email and nothing more will come.`,
  });
}

/** The sample's link, by email as well as on the page. */
export async function queueSample(ctx: Ctx, sub: Sub, downloadUrl: string, hours: number) {
  return enqueue(ctx, {
    sub, identity: "owner", kind: "transactional", subject: "Your sample of The 40 Hour Cabin",
    body: `Hi {{name}},\n\nHere are the first {{sample_pages}} pages you asked for:\n{{site}}${downloadUrl}\n\nThe link works for ${hours} hours. If it runs out, ask again at {{site}}/sample.`,
  });
}

/** Start every active sequence whose trigger this is. */
export async function enroll(ctx: Ctx, subscriberId: number, trigger: string) {
  const seqs = (await ctx.env.DB.prepare("SELECT key FROM sequences WHERE trigger = ? AND active = 1").bind(trigger).all<{ key: string }>()).results;
  for (const s of seqs) {
    await ctx.env.DB.prepare("INSERT INTO enrollments(subscriber_id, sequence, enrolled_at) VALUES(?, ?, ?) ON CONFLICT DO NOTHING").bind(subscriberId, s.key, nowIso()).run();
  }
}

/** Move every sequence step that has come due into the queue. Run by the mail program's
 *  every collection, so the site needs no clock of its own. */
export async function tick(ctx: Ctx) {
  const due = (await ctx.env.DB.prepare(
    `SELECT e.subscriber_id, e.sequence, e.next_step, e.enrolled_at, st.delay_hours, st.identity, st.subject, st.body
     FROM enrollments e JOIN sequences q ON q.key = e.sequence AND q.active = 1
     JOIN sequence_steps st ON st.sequence = e.sequence AND st.step = e.next_step
     WHERE e.status = 'active' LIMIT 200`,
  ).all<{ subscriber_id: number; sequence: string; next_step: number; enrolled_at: string; delay_hours: number; identity: string; subject: string; body: string }>()).results;
  let queued = 0;
  for (const d of due) {
    if (Date.parse(d.enrolled_at) + d.delay_hours * 3_600_000 > Date.now()) continue;
    const sub = await ctx.env.DB.prepare("SELECT id, email, name, marketing_consent, status FROM subscribers WHERE id = ?").bind(d.subscriber_id).first<Sub>();
    if (sub) {
      const r = await enqueue(ctx, { sub, identity: d.identity, kind: "sequence", subject: d.subject, body: d.body, sequence: d.sequence, step: d.next_step });
      if (r.id) queued++;
      else if (r.why && r.why !== "not confirmed (unconfirmed)") {
        // out of the list for good: stop the run rather than retry forever
        await ctx.env.DB.prepare("UPDATE enrollments SET status = 'stopped' WHERE subscriber_id = ? AND sequence = ?").bind(d.subscriber_id, d.sequence).run();
        continue;
      } else continue;    // waiting on confirmation: try again next time
    }
    const more = await ctx.env.DB.prepare("SELECT 1 FROM sequence_steps WHERE sequence = ? AND step = ?").bind(d.sequence, d.next_step + 1).first();
    await ctx.env.DB.prepare("UPDATE enrollments SET next_step = next_step + 1, status = ? WHERE subscriber_id = ? AND sequence = ?")
      .bind(more ? "active" : "done", d.subscriber_id, d.sequence).run();
  }
  return queued;
}

/** A campaign to its segment: confirmed, consenting, not suppressed, optionally by tag/source. */
export async function queueCampaign(ctx: Ctx, campaignId: number) {
  const c = await ctx.env.DB.prepare("SELECT * FROM campaigns WHERE id = ?").bind(campaignId).first<{ id: number; identity: string; subject: string; body: string; segment: string; status: string }>();
  if (!c) throw new HttpError(404, "No such campaign.");
  if (c.status !== "draft") throw new HttpError(409, "This campaign has already been queued.");
  if (!ctx.env.MAIL_POSTAL_ADDRESS) throw new HttpError(400, "Set MAIL_POSTAL_ADDRESS (the postal address the law requires in marketing email) first.");
  const seg = JSON.parse(c.segment || "{}") as { tags?: string[]; source?: string };
  let sql = "SELECT id, email, name, marketing_consent, status FROM subscribers s WHERE status = 'confirmed' AND marketing_consent = 1 AND email NOT IN (SELECT email FROM suppressions)";
  const args: unknown[] = [];
  if (seg.source) { sql += " AND first_source = ?"; args.push(seg.source); }
  for (const tag of seg.tags || []) { sql += " AND EXISTS (SELECT 1 FROM subscriber_tags t WHERE t.subscriber_id = s.id AND t.tag = ?)"; args.push(tag); }
  const subs = (await ctx.env.DB.prepare(sql).bind(...args).all<Sub>()).results;
  let n = 0;
  for (const s of subs) if ((await enqueue(ctx, { sub: s, identity: c.identity, kind: "campaign", subject: c.subject, body: c.body, campaignId: c.id })).id) n++;
  await ctx.env.DB.prepare("UPDATE campaigns SET status = 'queued', queued_count = ?, queued_at = ? WHERE id = ?").bind(n, nowIso(), c.id).run();
  return n;
}

/** Take an address off the list for good. */
export async function suppress(ctx: Ctx, email: string, reason: string) {
  await ctx.env.DB.prepare("INSERT INTO suppressions(email, reason, created_at) VALUES(?, ?, ?) ON CONFLICT(email) DO NOTHING").bind(email, reason, nowIso()).run();
  const status = reason === "unsubscribed" ? "unsubscribed" : reason === "bounced" ? "bounced" : reason === "complained" ? "complained" : "unsubscribed";
  await ctx.env.DB.prepare("UPDATE subscribers SET status = ?, marketing_consent = 0, unsubscribed_at = COALESCE(unsubscribed_at, ?) WHERE email = ?").bind(status, nowIso(), email).run();
  await ctx.env.DB.prepare("UPDATE outbox SET status = 'cancelled' WHERE to_email = ? AND status = 'queued' AND kind IN ('campaign', 'sequence')").bind(email).run();
  await ctx.env.DB.prepare("UPDATE enrollments SET status = 'stopped' WHERE subscriber_id IN (SELECT id FROM subscribers WHERE email = ?)").bind(email).run();
}
