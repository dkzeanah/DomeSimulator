// zeanahlab-ops: the site's clock and its mail program (see wrangler.toml beside this file).
// Every minute it:
//   1. asks the site to run what is due (sequence mail into the queue, schedules, jobs);
//   2. collects the outbox (GET /api/mailer/outbox, the same protocol any mail program uses),
//      sends each message through Cloudflare Email Sending from zeanahlab.com, and reports
//      each result back (POST /api/mailer/report).
// The site decides what is sent and to whom; this Worker only delivers it.

interface Env { SITE: string; OPS_TOKEN: string; MAILER_TOKEN?: string; EMAIL?: SendEmail }

interface Outgoing {
  id: number; to: string; subject: string; html: string; text: string;
  from: string; replyTo: string | null; archiveBcc: string | null; headers: Record<string, string>;
}
type Result = { id: number; status: "sent" | "failed" | "bounced" | "retry"; messageId?: string; error?: string };

/** "Name <a@b.c>" -> { name, email } */
function address(s: string) {
  const m = /^\s*"?([^"<]*?)"?\s*<([^>]+)>\s*$/.exec(s);
  return m ? { name: m[1].trim() || undefined, email: m[2].trim() } : { email: s.trim() };
}

// Errors that will not change on a second try, and those that mean "later".
const PERMANENT = ["E_VALIDATION_ERROR", "E_FIELD_MISSING", "E_TOO_MANY_RECIPIENTS", "E_CONTENT_TOO_LARGE", "E_RECIPIENT_NOT_ALLOWED"];
const STOP_FOR_NOW = ["E_RATE_LIMIT_EXCEEDED", "E_DAILY_LIMIT_EXCEEDED", "E_SENDER_NOT_VERIFIED", "E_SENDER_DOMAIN_NOT_AVAILABLE"];

async function sendOne(env: Env, m: Outgoing): Promise<Result> {
  const message = (headers: Record<string, string>) => ({
    to: m.to, from: address(m.from), subject: m.subject, html: m.html, text: m.text,
    ...(m.replyTo ? { replyTo: m.replyTo } : {}),
    ...(m.archiveBcc ? { bcc: m.archiveBcc } : {}),
    ...(Object.keys(headers).length ? { headers } : {}),
  });
  try {
    let r: { messageId?: string };
    try {
      r = await env.EMAIL!.send(message(m.headers) as never);
    } catch (e) {
      // if Cloudflare will not carry the one-click unsubscribe headers, the link in the body still works
      if (!String((e as { code?: string }).code || "").startsWith("E_HEADER")) throw e;
      r = await env.EMAIL!.send(message({}) as never);
    }
    return { id: m.id, status: "sent", messageId: r?.messageId };
  } catch (e) {
    const code = String((e as { code?: string }).code || "");
    const error = `${code || "error"}: ${(e as Error).message}`.slice(0, 280);
    if (code === "E_RECIPIENT_SUPPRESSED") return { id: m.id, status: "bounced", error };
    if (PERMANENT.includes(code)) return { id: m.id, status: "failed", error };
    return { id: m.id, status: "retry", error };
  }
}

async function deliver(env: Env) {
  if (!env.EMAIL || !env.MAILER_TOKEN) return "mail: not configured";
  const auth = { Authorization: `Bearer ${env.MAILER_TOKEN}`, "User-Agent": "zeanahlab-ops" };
  const got = await fetch(`${env.SITE}/api/mailer/outbox?limit=50`, { headers: auth });
  if (!got.ok) throw new Error(`outbox answered ${got.status}`);
  const { messages } = (await got.json()) as { messages: Outgoing[] };
  const results: Result[] = [];
  let stopped = "";
  for (const m of messages) {
    if (stopped) { results.push({ id: m.id, status: "retry", error: stopped }); continue; }
    const r = await sendOne(env, m);
    if (r.status === "retry" && STOP_FOR_NOW.some((c) => r.error?.startsWith(c))) stopped = r.error!;
    results.push(r);
  }
  if (results.length) {
    const rep = await fetch(`${env.SITE}/api/mailer/report`, { method: "POST", headers: { ...auth, "Content-Type": "application/json" }, body: JSON.stringify({ results }) });
    if (!rep.ok) throw new Error(`report answered ${rep.status}`);
  }
  const sent = results.filter((r) => r.status === "sent").length;
  return `mail: ${sent}/${results.length} sent${stopped ? `; paused: ${stopped}` : ""}`;
}

async function tick(env: Env) {
  const r = await fetch(`${env.SITE}/api/ops/clock`, { method: "POST", headers: { Authorization: `Bearer ${env.OPS_TOKEN}`, "User-Agent": "zeanahlab-ops" } });
  const text = await r.text();
  if (!r.ok) throw new Error(`clock answered ${r.status}: ${text.slice(0, 300)}`);
  return `clock: ${text}`;
}

export default {
  async scheduled(_event: ScheduledController, env: Env, ctx: ExecutionContext) {
    ctx.waitUntil((async () => {
      // the clock first (it may queue mail), then the mail; one failing never stops the other
      for (const step of [tick, deliver]) {
        try { console.log(await step(env)); } catch (e) { console.error(step.name, e); }
      }
    })());
  },
} satisfies ExportedHandler<Env>;
