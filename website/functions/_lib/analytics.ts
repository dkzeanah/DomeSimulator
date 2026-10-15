// First-party analytics: counted on the site, from the site's own requests, kept in its own
// database. No third-party script, no cross-site cookie, no fingerprinting. A visitor gets a
// random id in a first-party cookie (so a sale can be traced to the source that brought it);
// a browser that sends Global Privacy Control or Do Not Track is counted without one.

import { randomToken } from "./crypto";
import { Ctx, nowIso } from "./http";

const VID = "zl_v", SID = "zl_s";
const BOTS = /bot|crawl|spider|slurp|preview|monitor|headless|lighthouse|facebookexternalhit|embedly/i;

export function cookie(request: Request, name: string): string | null {
  for (const part of (request.headers.get("Cookie") || "").split(";")) {
    const [k, ...v] = part.trim().split("=");
    if (k === name) return v.join("=") || null;
  }
  return null;
}

export const optedOut = (r: Request) => r.headers.get("Sec-GPC") === "1" || r.headers.get("DNT") === "1";
export const visitorOf = (ctx: Ctx) => (optedOut(ctx.request) ? null : cookie(ctx.request, VID));

function device(ua: string) {
  if (/iPad|Tablet/i.test(ua)) return "tablet";
  if (/Mobi|Android|iPhone/i.test(ua)) return "mobile";
  return "desktop";
}

/** One page view. Sets the visitor (1 year) and session (30 min, renewed) cookies. */
export async function recordVisit(ctx: Ctx, v: { path: string; referrer?: string; utm?: Record<string, string> }) {
  const ua = ctx.request.headers.get("User-Agent") || "";
  if (BOTS.test(ua)) return;
  let vid: string | null = null, sid: string | null = null;
  if (!optedOut(ctx.request)) {
    vid = cookie(ctx.request, VID) || randomToken(12);
    sid = cookie(ctx.request, SID) || randomToken(9);
    const secure = ctx.url.protocol === "https:" ? "; Secure" : "";
    ctx.setCookies.push(`${VID}=${vid}; Path=/; Max-Age=31536000; HttpOnly; SameSite=Lax${secure}`);
    ctx.setCookies.push(`${SID}=${sid}; Path=/; Max-Age=1800; HttpOnly; SameSite=Lax${secure}`);
  }
  let refHost: string | null = null;
  try {
    const h = v.referrer ? new URL(v.referrer).host : "";
    refHost = h && h !== ctx.url.host && !h.endsWith("zeanahlab.com") ? h.replace(/^www\./, "") : null;
  } catch { /* not a URL */ }
  const u = v.utm || {};
  const clip = (s?: string) => (s ? String(s).slice(0, 80) : null);
  const country = (ctx.request as Request & { cf?: { country?: string } }).cf?.country || null;
  await ctx.env.DB.prepare(
    "INSERT INTO visits(ts, visitor_id, session_id, path, referrer_host, utm_source, utm_medium, utm_campaign, utm_content, country, device) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
  ).bind(nowIso(), vid, sid, String(v.path || "/").slice(0, 200), refHost, clip(u.source), clip(u.medium), clip(u.campaign), clip(u.content), country, device(ua)).run();
}

/** A step that matters, tied to the visitor who took it. */
export async function convert(ctx: Ctx, kind: string, ref?: string | null, valueCents = 0, visitorId?: string | null) {
  await ctx.env.DB.prepare("INSERT INTO conversions(ts, visitor_id, kind, ref, value_cents) VALUES(?, ?, ?, ?, ?)")
    .bind(nowIso(), visitorId === undefined ? visitorOf(ctx) : visitorId, kind, ref ?? null, valueCents).run();
}

/** Where this visitor first came from: their first visit's source, for a new subscriber. */
export async function firstTouch(ctx: Ctx) {
  const vid = visitorOf(ctx);
  if (!vid) return null;
  const v = await ctx.env.DB.prepare("SELECT utm_source, utm_medium, utm_campaign, referrer_host, path FROM visits WHERE visitor_id = ? ORDER BY id LIMIT 1")
    .bind(vid).first<{ utm_source: string | null; utm_medium: string | null; utm_campaign: string | null; referrer_host: string | null; path: string }>();
  return {
    visitor_id: vid,
    source: v?.utm_source || v?.referrer_host || "direct",
    medium: v?.utm_medium || (v?.referrer_host ? "referral" : "none"),
    campaign: v?.utm_campaign || null,
    referrer: v?.referrer_host || null,
    landing: v?.path || null,
  };
}

// ---------------------------------------------------------------- the reports

const SOURCE = "COALESCE(v.utm_source, v.referrer_host, 'direct')";

export async function report(ctx: Ctx, days: number) {
  const db = ctx.env.DB;
  const since = new Date(Date.now() - days * 86_400_000).toISOString();
  const all = async <T>(sql: string, ...a: unknown[]) => (await db.prepare(sql).bind(...a).all<T>()).results;

  const daily = await all<{ day: string; views: number; visitors: number }>(
    "SELECT substr(ts, 1, 10) day, COUNT(*) views, COUNT(DISTINCT COALESCE(visitor_id, 'anon-' || id)) visitors FROM visits WHERE ts >= ? GROUP BY day ORDER BY day", since);
  const totals = (await db.prepare("SELECT COUNT(*) views, COUNT(DISTINCT visitor_id) visitors, COUNT(DISTINCT session_id) sessions FROM visits WHERE ts >= ?").bind(since).first<{ views: number; visitors: number; sessions: number }>())!;
  const pages = await all("SELECT path, COUNT(*) views FROM visits WHERE ts >= ? GROUP BY path ORDER BY views DESC LIMIT 12", since);
  const sources = await all(
    `SELECT ${SOURCE} source, COUNT(DISTINCT v.visitor_id) visitors, COUNT(*) views FROM visits v WHERE v.ts >= ? GROUP BY source ORDER BY visitors DESC LIMIT 12`, since);
  const devices = await all("SELECT device, COUNT(*) views FROM visits WHERE ts >= ? GROUP BY device ORDER BY views DESC", since);
  const countries = await all("SELECT COALESCE(country, '?') country, COUNT(*) views FROM visits WHERE ts >= ? GROUP BY country ORDER BY views DESC LIMIT 10", since);

  // The funnel: distinct visitors reaching each step in the window.
  const step = async (kind: string) => (await db.prepare("SELECT COUNT(DISTINCT visitor_id) n FROM conversions WHERE kind = ? AND ts >= ? AND visitor_id IS NOT NULL").bind(kind, since).first<{ n: number }>())!.n;
  const funnel = [
    { step: "Visited", n: totals.visitors },
    { step: "Got the sample", n: await step("sample") },
    { step: "Made an account", n: await step("signup") },
    { step: "Started checkout", n: await step("checkout") },
    { step: "Bought", n: await step("purchase") },
  ];

  // Revenue and conversions by the source that first brought the visitor.
  const bySource = await all(
    `SELECT COALESCE(f.src, 'unknown') source, SUM(c.kind = 'sample') samples, SUM(c.kind = 'signup') signups,
            SUM(c.kind = 'purchase') purchases, SUM(CASE WHEN c.kind = 'purchase' THEN c.value_cents ELSE 0 END) revenue_cents
     FROM conversions c LEFT JOIN (
       SELECT v.visitor_id, ${SOURCE} src FROM visits v WHERE v.id IN (SELECT MIN(id) FROM visits WHERE visitor_id IS NOT NULL GROUP BY visitor_id)
     ) f ON f.visitor_id = c.visitor_id
     WHERE c.ts >= ? GROUP BY source ORDER BY revenue_cents DESC, samples DESC LIMIT 12`, since);

  // The list: growth by day, and where it stands.
  const listDaily = await all("SELECT substr(created_at, 1, 10) day, COUNT(*) joined FROM subscribers WHERE created_at >= ? GROUP BY day ORDER BY day", since);
  const listStatus = await all("SELECT status, COUNT(*) n FROM subscribers GROUP BY status");
  const outbox = await all("SELECT status, COUNT(*) n FROM outbox GROUP BY status");
  const mailByKind = await all(
    `SELECT o.identity, o.kind, COUNT(DISTINCT o.id) sent,
            COUNT(DISTINCT CASE WHEN e.kind = 'open' THEN o.id END) opened,
            COUNT(DISTINCT CASE WHEN e.kind = 'click' THEN o.id END) clicked
     FROM outbox o LEFT JOIN email_events e ON e.outbox_id = o.id
     WHERE o.status = 'sent' AND o.created_at >= ? GROUP BY o.identity, o.kind`, since);

  return { days, totals, daily, pages, sources, devices, countries, funnel, bySource, listDaily, listStatus, outbox, mailByKind };
}
