import { hmac } from "./crypto";
import { Ctx, Env, HttpError } from "./http";
import { enqueue, site } from "./mail";

export interface DeliveryOrder {
  id: number; ref: string; status: string; book_slug: string; email: string | null;
  subscriber_id: number | null; amount_cents: number; currency: string;
}

// Purpose-specific, server-signed access: no need to retain checkout's random
// plaintext key. Old checkout links remain valid as well.
export async function receiptKey(env: Env, ref: string) {
  if (!env.SESSION_SECRET) throw new HttpError(503, "Receipt delivery is not configured.");
  return hmac(env.SESSION_SECRET, `order-receipt:v1:${ref}`);
}

// Called only for the individual paid order being processed. No bulk sends or
// automatic mail to historical purchasers.
export async function queueOrderReceipt(ctx: Ctx, o: DeliveryOrder) {
  if (o.status !== "paid") return null;
  const p = await ctx.env.DB.prepare("SELECT title,kind,status,file_key FROM products WHERE slug=?").bind(o.book_slug)
    .first<{ title: string; kind: string; status: string; file_key: string | null }>();
  if (!p || p.kind !== "digital" || p.status !== "live" || !p.file_key || !ctx.env.BOOKS || !await ctx.env.BOOKS.head(p.file_key)) return null;
  const sub = await ctx.env.DB.prepare("SELECT id,email,name,marketing_consent,status FROM subscribers WHERE id=? OR email=? ORDER BY CASE WHEN id=? THEN 0 ELSE 1 END LIMIT 1")
    .bind(o.subscriber_id, o.email, o.subscriber_id)
    .first<{ id: number; email: string; name: string | null; marketing_consent: number; status: string }>();
  if (!sub) return null;
  const base = site(ctx.env, ctx), key = encodeURIComponent(await receiptKey(ctx.env, o.ref));
  return enqueue(ctx, {
    sub, identity: "owner", kind: "transactional", dedupeKey: `order:${o.id}:download`,
    subject: `Your book is ready: ${p.title}`,
    body: `Hi {{name}},\n\nThank you for purchasing ${p.title}. Your complete PDF is ready now.\n\nDownload your book:\n${base}/api/orders/${encodeURIComponent(o.ref)}/download?key=${key}\n\nYour receipt and future downloads:\n${base}/thanks/${encodeURIComponent(o.ref)}?key=${key}\n\nKeep that private link. You can download without making an account. To keep it in My books, sign in or create an account from your receipt page:\n${base}/account/books\n\nOrder reference: ${o.ref}\n\nIf you need help, reply to this email.`,
  });
}
