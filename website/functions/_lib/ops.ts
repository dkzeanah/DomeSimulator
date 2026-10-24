// The site's own operations engine. Things that happen are EVENTS (a sale, a confirmation,
// a new pad, an agent's proposal, the clock striking Monday). An AUTOMATION says: when this
// event happens and these fields match, do these actions -- now, or after a delay. Each
// firing is a JOB row; the table is the truth, so nothing is lost if a run is cut short:
// the clock (the zeanahlab-ops Worker, every minute) finds what is due or stuck and runs it.
//
// The actions are deliberately few and owner-facing. Nothing here sends marketing mail on its
// own or changes what anyone pays: an AI that thinks a listing is spam PROPOSES hiding it,
// and an AI-written update is saved as a DRAFT.

import { ask, aiReady, parseJson, typedFigures } from "./ai";
import { report } from "./analytics";
import { hmacHex } from "./crypto";
import { Ctx, HttpError, nowIso } from "./http";
import { enqueue, fill, tick } from "./mail";

export const TRIGGERS: Record<string, string> = {
  "subscriber.created": "Someone joins the list. Fields: subscriberId, source, campaign, consent (yes/no).",
  "subscriber.confirmed": "Someone clicks the confirmation link. Fields: subscriberId, source.",
  "subscriber.left": "Someone unsubscribes. Fields: subscriberId.",
  "member.joined": "Someone makes an account. Fields: userId, subscriberId, source.",
  "order.paid": "An order is paid. Fields: ref, product, price, amount, amount_cents, subscriberId, source.",
  "buildpack.requested": "A Dome Sketch owner asks for a build pack (render it with website/scripts/render_packs.py). Fields: ref, userId.",
  "cutlist.requested": "A buyer asks the Wedge Builder for a cut list (render it with website/scripts/render_cutlists.py). Fields: ref, order, product, diameter_ft.",
  "listing.created": "A network listing is added. Fields: listingId, kind, title.",
  "proposal.created": "An agent (or Workers AI) proposes an action for you to approve. Fields: proposalId, action, key, reason.",
  "task.created": "A task is added on the projects board. Fields: taskId, project, title, due (YYYY-MM-DD or empty).",
  "task.done": "A task on the projects board is marked done. Fields: taskId, project, title.",
  "schedule.hourly": "Every hour, on the hour.",
  "schedule.daily": "Every day at 13:00 UTC (morning in the US).",
  "schedule.weekly": "Mondays at 13:00 UTC.",
  "schedule.monthly": "The 1st of the month at 13:00 UTC.",
};

export const ACTIONS: Record<string, { label: string; fields: Record<string, string> }> = {
  notify: { label: "Put a notice on the admin page (and email it to you)", fields: { title: "Title; {{field}} fills in", body: "Text; {{field}} fills in", level: "info, action or warning", email: "true to email a copy to you", link: "a page on this site, e.g. /admin" } },
  tag: { label: "Tag the subscriber", fields: { tag: "e.g. buyer:{{product}} or came-from:{{source}}" } },
  enroll: { label: "Start a mail sequence for the subscriber", fields: { sequence: "the sequence's key" } },
  webhook: { label: "POST the event to a web address you own (signed)", fields: { url: "https://..." } },
  report: { label: "Write the numbers report (counted) with a short Workers AI reading", fields: { days: "how many days back", email: "true to email it to you" } },
  ai_review_listing: { label: "Workers AI reads a new listing; if it looks like spam, it proposes hiding it", fields: {} },
  ai_draft_campaign: { label: "Workers AI drafts a list update and saves it as a DRAFT (never sent)", fields: { brief: "what the update is about", identity: "donovan or owner" } },
};

type Data = Record<string, unknown>;
interface Action { type: string; [k: string]: unknown }
interface Step { type: string; ok: boolean; note: string }

const strings = (d: Data) => Object.fromEntries(Object.entries(d).map(([k, v]) => [k, v == null ? "" : String(v)]));

// ---------------------------------------------------------------- small shared pieces

export async function getSetting(ctx: Ctx, key: string) {
  return (await ctx.env.DB.prepare("SELECT value FROM settings WHERE key = ?").bind(key).first<{ value: string }>())?.value ?? null;
}

export async function setSetting(ctx: Ctx, key: string, value: string) {
  await ctx.env.DB.prepare("INSERT INTO settings(key, value, updated_at) VALUES(?, ?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at")
    .bind(key, value, nowIso()).run();
}

/** Write who did what. The actor is the signed-in person unless named. */
export async function audit(ctx: Ctx, action: string, target: string | null, detail?: unknown, actor?: { kind: string; id?: number | null; name?: string | null }) {
  const a = actor || (ctx.user ? { kind: "user", id: ctx.user.id, name: ctx.user.email } : { kind: "system", id: null, name: null });
  await ctx.env.DB.prepare("INSERT INTO audit_log(ts, actor_kind, actor_id, actor_name, action, target, detail) VALUES(?, ?, ?, ?, ?, ?, ?)")
    .bind(nowIso(), a.kind, a.id ?? null, a.name ?? null, action, target, detail == null ? null : typeof detail === "string" ? detail : JSON.stringify(detail)).run();
}

export async function notice(ctx: Ctx, n: { level?: string; title: string; body?: string; link?: string }) {
  await ctx.env.DB.prepare("INSERT INTO notices(level, title, body, link, created_at) VALUES(?, ?, ?, ?, ?)")
    .bind(n.level || "info", n.title.slice(0, 200), n.body?.slice(0, 8000) ?? null, n.link ?? null, nowIso()).run();
}

/** The owner's own list entry, for mail to the owner. Only an address already on the list. */
async function ownerSub(ctx: Ctx) {
  const owner = String(ctx.env.ADMIN_EMAILS || "").split(",")[0]?.trim().toLowerCase();
  if (!owner) return null;
  return ctx.env.DB.prepare("SELECT id, email, name, marketing_consent, status FROM subscribers WHERE email = ?").bind(owner)
    .first<{ id: number; email: string; name: string | null; marketing_consent: number; status: string }>();
}

async function mailOwner(ctx: Ctx, subject: string, text: string) {
  const sub = await ownerSub(ctx);
  if (!sub) return "no email: your address is not on the list yet";
  const r = await enqueue(ctx, { sub, identity: "owner", kind: "transactional", subject, body: text });
  return r.id ? "emailed (queued)" : `not emailed: ${r.why}`;
}

// ---------------------------------------------------------------- events -> jobs

function matches(conditions: Record<string, unknown>, data: Data) {
  for (const [k, want] of Object.entries(conditions)) {
    if (k.endsWith("_min")) {
      if (!(Number(data[k.slice(0, -4)]) >= Number(want))) return false;
    } else if (String(data[k] ?? "") !== String(want)) return false;
  }
  return true;
}

/** Something happened. Record it, make a job for each automation it fires, and start the
 *  immediate ones after the response has gone (the clock catches any that do not finish).
 *  Never throws: an automation problem must not break a signup or a sale. */
export async function emit(ctx: Ctx, type: string, data: Data = {}) {
  try {
    const db = ctx.env.DB;
    const ev = await db.prepare("INSERT INTO ops_events(type, data, created_at) VALUES(?, ?, ?) RETURNING id").bind(type, JSON.stringify(data), nowIso()).first<{ id: number }>();
    const autos = (await db.prepare("SELECT id, name, conditions, delay_minutes FROM automations WHERE trigger = ? AND active = 1").bind(type)
      .all<{ id: number; name: string; conditions: string; delay_minutes: number }>()).results;
    const now: number[] = [];
    for (const a of autos) {
      if (!matches(JSON.parse(a.conditions || "{}"), data)) continue;
      const j = await db.prepare("INSERT INTO jobs(automation_id, event_id, label, run_at, created_at) VALUES(?, ?, ?, ?, ?) RETURNING id")
        .bind(a.id, ev!.id, a.name, nowIso(a.delay_minutes * 60_000), nowIso()).first<{ id: number }>();
      if (!a.delay_minutes) now.push(j!.id);
    }
    if (now.length) {
      const run = (async () => { for (const id of now) await runJob(ctx, id); })().catch((e) => console.error("jobs", e));
      if (ctx.waitUntil) ctx.waitUntil(run);
      else await run;
    }
  } catch (e) {
    console.error("emit", type, e);
  }
}

// ---------------------------------------------------------------- running a job

export async function runJob(ctx: Ctx, id: number) {
  const db = ctx.env.DB;
  const t = nowIso();
  const claim = await db.prepare("UPDATE jobs SET status = 'running', started_at = ?, attempts = attempts + 1 WHERE id = ? AND status = 'queued' AND run_at <= ?").bind(t, id, t).run();
  if (!claim.meta.changes) return null;
  const job = (await db.prepare(
    `SELECT j.id, j.attempts, j.result, j.automation_id, a.name, a.actions, e.type, e.data
     FROM jobs j LEFT JOIN automations a ON a.id = j.automation_id LEFT JOIN ops_events e ON e.id = j.event_id WHERE j.id = ?`,
  ).bind(id).first<{ id: number; attempts: number; result: string | null; automation_id: number | null; name: string | null; actions: string | null; type: string | null; data: string | null }>())!;
  if (!job.actions) {
    await db.prepare("UPDATE jobs SET status = 'cancelled', finished_at = ?, error = 'The automation was deleted.' WHERE id = ?").bind(nowIso(), id).run();
    return "cancelled";
  }
  const actions = JSON.parse(job.actions) as Action[];
  const before = (job.result ? JSON.parse(job.result) : []) as Step[];
  const data: Data = { ...(job.data ? JSON.parse(job.data) : {}), event: job.type };
  const steps: Step[] = [];
  for (const [i, a] of actions.entries()) {
    if (before[i]?.ok) { steps.push(before[i]); continue; }   // a retry never repeats what worked
    try {
      steps.push({ type: a.type, ok: true, note: await act(ctx, a, data, job.name || "automation") });
    } catch (e) {
      steps.push({ type: a.type, ok: false, note: (e as Error).message });
    }
  }
  const failed = steps.filter((s) => !s.ok);
  let status = "done";
  if (failed.length && job.attempts < 3) status = "queued";
  else if (failed.length) status = "failed";
  await db.prepare("UPDATE jobs SET status = ?, result = ?, error = ?, finished_at = ?, run_at = ? WHERE id = ?")
    .bind(status, JSON.stringify(steps), failed.map((f) => `${f.type}: ${f.note}`).join("; ") || null,
      status === "queued" ? null : nowIso(), nowIso(status === "queued" ? job.attempts * 5 * 60_000 : 0), id).run();
  if (status !== "queued" && job.automation_id) {
    await db.prepare("UPDATE automations SET runs = runs + 1, last_run_at = ? WHERE id = ?").bind(nowIso(), job.automation_id).run();
  }
  if (status === "failed") {
    await notice(ctx, { level: "warning", title: `An automation failed three times: ${job.name}`, body: failed.map((f) => `${f.type}: ${f.note}`).join("\n"), link: "/admin/ops" });
  }
  return status;
}

async function act(ctx: Ctx, a: Action, data: Data, automation: string): Promise<string> {
  const db = ctx.env.DB;
  const f = (s: unknown) => fill(String(s ?? ""), strings(data));
  const subscriberId = Number(data.subscriberId) || null;
  switch (a.type) {
    case "notify": {
      const title = f(a.title || automation), text = f(a.body || "");
      await notice(ctx, { level: String(a.level || "info"), title, body: text, link: a.link ? String(a.link) : undefined });
      return a.email ? `noticed; ${await mailOwner(ctx, title, text)}` : "noticed";
    }
    case "tag": {
      if (!subscriberId) return "skipped: this event has no subscriber";
      const tag = f(a.tag).toLowerCase().slice(0, 40);
      if (!tag) throw new Error("The tag is empty.");
      await db.prepare("INSERT INTO subscriber_tags(subscriber_id, tag, created_at) VALUES(?, ?, ?) ON CONFLICT DO NOTHING").bind(subscriberId, tag, nowIso()).run();
      return `tagged ${tag}`;
    }
    case "enroll": {
      if (!subscriberId) return "skipped: this event has no subscriber";
      const seq = String(a.sequence || "");
      if (!(await db.prepare("SELECT 1 FROM sequences WHERE key = ?").bind(seq).first())) throw new Error(`No sequence called ${seq}.`);
      await db.prepare("INSERT INTO enrollments(subscriber_id, sequence, enrolled_at) VALUES(?, ?, ?) ON CONFLICT DO NOTHING").bind(subscriberId, seq, nowIso()).run();
      return `enrolled in ${seq} (it sends only while the sequence is switched on)`;
    }
    case "webhook": {
      const url = String(a.url || "");
      if (!/^https:\/\//.test(url)) throw new Error("A webhook address must start with https://");
      const payload = JSON.stringify({ event: data.event, data, automation, at: nowIso() });
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (ctx.env.SESSION_SECRET) headers["X-Zeanahlab-Signature"] = await hmacHex(ctx.env.SESSION_SECRET, payload);
      const r = await fetch(url, { method: "POST", headers, body: payload, signal: AbortSignal.timeout(10_000) });
      if (!r.ok) throw new Error(`${url} answered ${r.status}.`);
      return `posted (${r.status})`;
    }
    case "report":
      return weeklyReport(ctx, Math.max(1, Math.min(90, Number(a.days) || 7)), Boolean(a.email));
    case "ai_review_listing":
      return reviewListing(ctx, Number(data.listingId));
    case "ai_draft_campaign":
      return draftCampaign(ctx, String(a.brief || "A short build update."), String(a.identity || "donovan"));
    default:
      throw new Error(`Unknown action ${a.type}.`);
  }
}

// ---------------------------------------------------------------- the actions that think

const money = (c: number) => `$${(c / 100).toFixed(c % 100 ? 2 : 0)}`;

/** The numbers, counted by the site, as plain lines. The report and the assistant both read this. */
export async function numbers(ctx: Ctx, days: number) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const r = (await report(ctx, days)) as unknown as Record<string, any[]> & { totals: { visitors: number; views: number }; funnel: { step: string; n: number }[] };
  const since = nowIso(-days * 86_400_000);
  const sales = (await ctx.env.DB.prepare("SELECT COUNT(*) n, COALESCE(SUM(amount_cents), 0) c FROM orders WHERE status = 'paid' AND provider != 'owner' AND paid_at >= ?").bind(since).first<{ n: number; c: number }>())!;
  const byProduct = (await ctx.env.DB.prepare("SELECT book_slug p, COUNT(*) n, SUM(amount_cents) c FROM orders WHERE status = 'paid' AND provider != 'owner' AND paid_at >= ? GROUP BY p").bind(since).all<{ p: string; n: number; c: number }>()).results;
  const members = (await ctx.env.DB.prepare("SELECT COUNT(*) n FROM users WHERE created_at >= ?").bind(since).first<{ n: number }>())!.n;
  const listings = (await ctx.env.DB.prepare("SELECT COUNT(*) n FROM listings WHERE created_at >= ?").bind(since).first<{ n: number }>())!.n;
  const joined = r.listDaily.reduce((s: number, d) => s + Number(d.joined), 0);
  const sent = r.mailByKind.reduce((s: number, m) => s + Number(m.sent), 0);
  const opened = r.mailByKind.reduce((s: number, m) => s + Number(m.opened), 0);
  const clicked = r.mailByKind.reduce((s: number, m) => s + Number(m.clicked), 0);
  const lines = [
    `Last ${days} days, counted by the site:`,
    `Visitors: ${r.totals.visitors} (${r.totals.views} page views)`,
    `Funnel: ${r.funnel.map((s) => `${s.step} ${s.n}`).join(" -> ")}`,
    `Sales: ${sales.n} paid orders, ${money(sales.c)}${byProduct.length ? ` (${byProduct.map((p) => `${p.p}: ${p.n}, ${money(p.c)}`).join("; ")})` : ""}`,
    `List: ${joined} joined; now ${r.listStatus.map((s) => `${s.status} ${s.n}`).join(", ") || "empty"}`,
    `New members: ${members}. New network listings: ${listings}.`,
    `Top sources: ${r.sources.slice(0, 5).map((s) => `${s.source} ${s.visitors}`).join(", ") || "none yet"}`,
    `Top pages: ${r.pages.slice(0, 5).map((p) => `${p.path} ${p.views}`).join(", ") || "none yet"}`,
    `Mail delivered: ${sent}, opened ${opened}, clicked ${clicked}. Waiting in the queue: ${r.outbox.find((o) => o.status === "queued")?.n ?? 0}.`,
  ];
  return lines.join("\n");
}

const READER = "You read a small website's numbers for its owner, who sells a book on building geodesic domes and runs a builders' network. "
  + "Use ONLY the numbers given; never invent, estimate or round one. If a number is zero or small, say so plainly. "
  + "Write 3 to 5 short sentences of plain English, then one line starting 'Worth doing:' with a single concrete suggestion.";

async function weeklyReport(ctx: Ctx, days: number, email: boolean) {
  const counted = await numbers(ctx, days);
  let reading = "";
  if (aiReady(ctx.env)) {
    try {
      reading = await ask(ctx.env, "report", READER, counted, 350);
    } catch (e) {
      reading = `(No reading this time: ${(e as Error).message})`;
    }
  }
  const text = `${counted}${reading ? `\n\nA reading by Workers AI (it can be wrong; the numbers above are counted):\n${reading}` : ""}`;
  await notice(ctx, { level: "info", title: `Report: the last ${days} days`, body: text, link: "/admin/analytics" });
  return email ? `report written; ${await mailOwner(ctx, `Zeanah Lab: the last ${days} days`, text)}` : "report written";
}

async function reviewListing(ctx: Ctx, id: number) {
  const l = await ctx.env.DB.prepare("SELECT id, kind, title, body, contact, city, region, country, visible FROM listings WHERE id = ?").bind(id)
    .first<{ id: number; kind: string; title: string; body: string | null; contact: string | null; city: string | null; region: string | null; country: string | null; visible: number }>();
  if (!l) return "skipped: the listing is gone";
  if (!aiReady(ctx.env)) return "skipped: Workers AI is not connected";
  const answer = await ask(ctx.env, "review_listing",
    "You check new listings on a network for people building small domes: pad hosts, builders, recyclers, suppliers. "
    + "Spam is advertising unrelated to building or land, scams, links to unrelated sites, abuse or gibberish. "
    + 'Answer with JSON only: {"verdict":"ok"|"spam"|"unsure","reason":"one short sentence"}.',
    JSON.stringify({ kind: l.kind, title: l.title, body: l.body, contact: l.contact, place: [l.city, l.region, l.country].filter(Boolean).join(", ") }), 120);
  const v = parseJson<{ verdict?: string; reason?: string }>(answer) || { verdict: "unsure", reason: `Unreadable answer: ${answer.slice(0, 120)}` };
  if (v.verdict === "ok") return `looks fine: ${v.reason || ""}`;
  const p = await ctx.env.DB.prepare("INSERT INTO agent_proposals(key_id, action, payload, reason, created_at) VALUES(NULL, 'listing.hide', ?, ?, ?) RETURNING id")
    .bind(JSON.stringify({ listingId: l.id, title: l.title }), `Workers AI (${v.verdict}): ${v.reason || ""}`, nowIso()).first<{ id: number }>();
  await notice(ctx, { level: "action", title: `A listing may be spam: ${l.title}`, body: `${v.reason || ""}\nIt is still visible. Approve proposal #${p!.id} to hide it, or reject it to leave it.`, link: "/admin/agents" });
  return `${v.verdict}: proposed hiding it (#${p!.id})`;
}

const TOKEN_HELP = "{{name}} the reader's first name; {{book_pages}} pages in the book; {{book_figures}} figures in the book; {{frame_hours}} hours to frame the dome; "
  + "{{sample_pages}} pages in the free sample; {{dome_ft}} the dome's width in feet; {{book_price}} the book's price; {{site}} the site's address";

async function draftCampaign(ctx: Ctx, brief: string, identity: string) {
  if (!aiReady(ctx.env)) throw new Error("Workers AI is not connected.");
  const happened = (await ctx.env.DB.prepare("SELECT label FROM events WHERE created_at >= ? ORDER BY id DESC LIMIT 15").bind(nowIso(-30 * 86_400_000)).all<{ label: string }>()).results.map((e) => e.label);
  const answer = await ask(ctx.env, "draft_campaign",
    "You draft short email updates for Donovan Zeanah, who wrote 'The 40 Hour Cabin', a book on building a geodesic dome cabin from split logs by the wedge method. "
    + "Voice: plain, direct, first person, no hype, no exclamation marks. Under 180 words. Plain text, no markdown. "
    + `NEVER type a number. Where a figure is needed use one of these tokens exactly: ${TOKEN_HELP}. `
    + 'Answer with JSON only: {"subject":"...","body":"..."}. Start the body with "Hi {{name}},".',
    `Brief: ${brief}\nThings that happened on the site lately (for colour only; do not count them): ${happened.join("; ") || "nothing recorded"}`, 700);
  const d = parseJson<{ subject?: string; body?: string }>(answer);
  if (!d?.subject || !d?.body) throw new Error(`Workers AI did not return a draft: ${answer.slice(0, 160)}`);
  const figures = typedFigures(`${d.subject} ${d.body}`);
  const r = await ctx.env.DB.prepare("INSERT INTO campaigns(name, identity, subject, body, segment, created_at) VALUES(?, ?, ?, ?, '{}', ?) RETURNING id")
    .bind(`[Workers AI draft] ${nowIso().slice(0, 10)}`, identity, d.subject.slice(0, 160), d.body.slice(0, 20000), nowIso()).first<{ id: number }>();
  await notice(ctx, {
    level: "action", title: `A draft update is ready to read: ${d.subject}`,
    body: `Saved as campaign #${r!.id}. Nothing has been sent.${figures.length ? `\nIt typed these figures instead of using tokens -- check or replace them: ${figures.join(", ")}` : ""}`,
    link: "/admin/list",
  });
  return `draft #${r!.id} saved${figures.length ? `; typed figures to check: ${figures.join(", ")}` : ""}`;
}

/** The owner asks a question; the answer is written only from the counted numbers, which come back with it. */
export async function assistant(ctx: Ctx, question: string, days: number) {
  if (!aiReady(ctx.env)) throw new HttpError(503, "Workers AI is not connected.");
  const counted = await numbers(ctx, days);
  const answer = await ask(ctx.env, "assistant",
    "You answer the owner's questions about their website using ONLY the numbers given. If the numbers cannot answer it, say what is missing. "
    + "Never invent a figure. Short, plain sentences.", `${counted}\n\nQuestion: ${question}`, 500);
  return { answer, numbers: counted };
}

// ---------------------------------------------------------------- the clock

/** Run once a minute by the zeanahlab-ops Worker (or by the owner's button). Moves sequence
 *  mail into the queue, fires the schedules, frees stuck jobs, runs what is due, tidies daily. */
export async function clock(ctx: Ctx) {
  const db = ctx.env.DB;
  const d = new Date();
  const iso = d.toISOString();
  const morning = d.getUTCHours() >= 13;
  const periods: [string, string | null][] = [
    ["schedule.hourly", iso.slice(0, 13)],
    ["schedule.daily", morning ? iso.slice(0, 10) : null],
    ["schedule.weekly", morning && d.getUTCDay() === 1 ? iso.slice(0, 10) : null],
    ["schedule.monthly", morning && d.getUTCDate() === 1 ? iso.slice(0, 7) : null],
  ];
  const fired: string[] = [];
  for (const [type, key] of periods) {
    if (!key || (await getSetting(ctx, `clock.${type}`)) === key) continue;
    await setSetting(ctx, `clock.${type}`, key);
    await emit({ ...ctx, waitUntil: undefined }, type, { period: key });
    fired.push(type);
  }
  const sequenceMail = await tick(ctx);
  const freed = (await db.prepare("UPDATE jobs SET status = 'queued' WHERE status = 'running' AND started_at < ?").bind(nowIso(-15 * 60_000)).run()).meta.changes;
  const due = (await db.prepare("SELECT id FROM jobs WHERE status = 'queued' AND run_at <= ? ORDER BY run_at LIMIT 25").bind(nowIso()).all<{ id: number }>()).results;
  let ran = 0;
  for (const j of due) if (await runJob(ctx, j.id)) ran++;
  if (fired.includes("schedule.daily")) await tidy(ctx);
  await setSetting(ctx, "clock.last", nowIso());
  return { fired, sequenceMail, freed, ran };
}

/** Old rows that only cost space: kept long enough to answer any question about them. */
async function tidy(ctx: Ctx) {
  const db = ctx.env.DB;
  const ago = (days: number) => nowIso(-days * 86_400_000);
  await db.batch([
    db.prepare("DELETE FROM api_calls WHERE ts < ?").bind(ago(90)),
    db.prepare("DELETE FROM login_attempts WHERE ts < ?").bind(ago(30)),
    db.prepare("DELETE FROM sessions WHERE expires_at < ?").bind(nowIso()),
    db.prepare("DELETE FROM user_tokens WHERE expires_at < ?").bind(ago(1)),
    db.prepare("DELETE FROM ops_events WHERE created_at < ?").bind(ago(180)),
    db.prepare("DELETE FROM jobs WHERE finished_at < ?").bind(ago(180)),
    db.prepare("DELETE FROM notices WHERE read_at IS NOT NULL AND read_at < ?").bind(ago(180)),
  ]);
}
