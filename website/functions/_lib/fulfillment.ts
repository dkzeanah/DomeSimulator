import { hmac } from "./crypto";
import { Ctx, Env, HttpError } from "./http";
import { enqueue, site } from "./mail";

export interface DeliveryOrder {
  id: number; ref: string; status: string; book_slug: string; email: string | null;
  subscriber_id: number | null; amount_cents: number; currency: string;
}

/** How many of `tool` one paid order of `product` may make (migrations/0015: tool_grants rows); 0 if none. */
export async function toolCredits(ctx: Ctx, product: string, tool: string) {
  const r = await ctx.env.DB.prepare("SELECT credits FROM tool_grants WHERE product = ? AND tool = ?").bind(product, tool).first<{ credits: number }>();
  return r?.credits ?? 0;
}

// Purpose-specific, server-signed access: no need to retain checkout's random
// plaintext key. Old checkout links remain valid as well.
export async function receiptKey(env: Env, ref: string) {
  if (!env.SESSION_SECRET) throw new HttpError(503, "Receipt delivery is not configured.");
  return hmac(env.SESSION_SECRET, `order-receipt:v1:${ref}`);
}

type Buyer = { id: number; email: string; name: string | null; marketing_consent: number; status: string };

async function buyerOf(ctx: Ctx, o: DeliveryOrder) {
  return ctx.env.DB.prepare("SELECT id,email,name,marketing_consent,status FROM subscribers WHERE id=? OR email=? ORDER BY CASE WHEN id=? THEN 0 ELSE 1 END LIMIT 1")
    .bind(o.subscriber_id, o.email, o.subscriber_id).first<Buyer>();
}

/** The buyer's private cut-list page (functions/_lib/cutlists.ts, src/pages/CutList.tsx). */
export async function cutlistLink(ctx: Ctx, ref: string) {
  return `${site(ctx.env, ctx)}/cutlist/${encodeURIComponent(ref)}?key=${encodeURIComponent(await receiptKey(ctx.env, ref))}`;
}

// Called only for the individual paid order being processed. No bulk sends or
// automatic mail to historical purchasers.
export async function queueOrderReceipt(ctx: Ctx, o: DeliveryOrder) {
  if (o.status !== "paid") return null;
  const p = await ctx.env.DB.prepare("SELECT title,kind,status,file_key FROM products WHERE slug=?").bind(o.book_slug)
    .first<{ title: string; kind: string; status: string; file_key: string | null }>();
  if (p?.kind === "tool") return queueToolReceipt(ctx, o, p.title);
  if (!p || p.kind !== "digital" || p.status !== "live" || !p.file_key || !ctx.env.BOOKS || !await ctx.env.BOOKS.head(p.file_key)) return null;
  const sub = await buyerOf(ctx, o);
  if (!sub) return null;
  const base = site(ctx.env, ctx), key = encodeURIComponent(await receiptKey(ctx.env, o.ref));
  const credits = await toolCredits(ctx, o.book_slug, "cutlist");
  const cutlist = credits
    ? `\n\nYour book also comes with ${credits === 1 ? "a cut list" : `${credits} cut lists`} solved for your own dome. Type your size and your logs here:\n${await cutlistLink(ctx, o.ref)}`
    : "";
  return enqueue(ctx, {
    sub, identity: "owner", kind: "transactional", dedupeKey: `order:${o.id}:download`,
    subject: `Your book is ready: ${p.title}`,
    body: `Hi {{name}},\n\nThank you for purchasing ${p.title}. Your complete PDF is ready now.\n\nDownload your book:\n${base}/api/orders/${encodeURIComponent(o.ref)}/download?key=${key}\n\nYour receipt and future downloads:\n${base}/thanks/${encodeURIComponent(o.ref)}?key=${key}${cutlist}\n\nKeep that private link. You can download without making an account. To keep it in My books, sign in or create an account from your receipt page:\n${base}/account/books\n\nOrder reference: ${o.ref}\n\nIf you need help, reply to this email.`,
  });
}

async function queueToolReceipt(ctx: Ctx, o: DeliveryOrder, title: string) {
  const sub = await buyerOf(ctx, o);
  if (!sub) return null;
  const credits = await toolCredits(ctx, o.book_slug, "cutlist");
  return enqueue(ctx, {
    sub, identity: "owner", kind: "transactional", dedupeKey: `order:${o.id}:download`,
    subject: `${title}: make your first cut list`,
    body: `Hi {{name}},\n\nThank you for buying ${title}. Your order makes up to ${credits} cut lists, each one solved for the dome and logs you type in.\n\nMake one here:\n${await cutlistLink(ctx, o.ref)}\n\nEach takes a few minutes to solve. We email you when it is ready, and every cut list you make stays on that page to download again.\n\nKeep that private link. To keep it in your account, sign in or create one from the page.\n\nOrder reference: ${o.ref}\n\nIf you need help, reply to this email.`,
  });
}

/** One finished cut list, to the buyer who asked for it. */
export async function queueCutlistReady(ctx: Ctx, o: DeliveryOrder, job: { id: number; label: string; summary: string }) {
  const sub = await buyerOf(ctx, o);
  if (!sub) return null;
  return enqueue(ctx, {
    sub, identity: "owner", kind: "transactional", dedupeKey: `cutlist:${job.id}:ready`,
    subject: `Your cut list is ready${job.label ? `: ${job.label}` : ""}`,
    body: `Hi {{name}},\n\nYour cut list is solved: ${job.summary}.\n\nDownload it here:\n${await cutlistLink(ctx, o.ref)}\n\nOrder reference: ${o.ref}\n\nIf anything in it looks wrong, reply to this email.`,
  });
}
