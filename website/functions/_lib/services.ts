// The two outside services: Resend for email, Stripe for card payments. Both spoken to
// over plain HTTPS, no SDKs. Either may be unconfigured; then the site says so honestly
// instead of pretending (no email is "sent", the shop says it opens soon).

import { hmacHex, sameString } from "./crypto";
import { Env, HttpError } from "./http";

// ---------------------------------------------------------------- email (Resend)

export function mailReady(env: Env) {
  return Boolean(env.RESEND_API_KEY && env.MAIL_FROM);
}

/** Send one email. Returns false (and sends nothing) when mail is not configured. */
export async function sendMail(env: Env, to: string, subject: string, html: string, textBody: string): Promise<boolean> {
  if (!mailReady(env)) return false;
  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify({ from: env.MAIL_FROM, to: [to], subject, html, text: textBody }),
  });
  return r.ok;
}

const esc = (s: string) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]!);

/** The one letter the list sends on its own: here is what you asked for. */
export function sampleLetter(site: string, downloadUrl: string, hours: number) {
  const link = `${site}${downloadUrl}`;
  return {
    subject: "Your sample of The 40 Hour Cabin",
    text: `Here is the sample you asked for:\n${link}\n\nThe link works for ${hours} hours. If it runs out, ask again on ${site}/sample.\n\nZeanah Lab`,
    html: `<p>Here is the sample you asked for:</p><p><a href="${esc(link)}">Download the sample (PDF)</a></p>`
      + `<p>The link works for ${hours} hours. If it runs out, ask again on <a href="${esc(site)}/sample">the sample page</a>.</p><p>Zeanah Lab</p>`,
  };
}

// ---------------------------------------------------------------- payments (Stripe)

const STRIPE = "https://api.stripe.com/v1";

/** Stripe's form encoding: nested keys as a[b][c]=v. */
function formEncode(value: unknown, prefix = "", out = new URLSearchParams()): URLSearchParams {
  if (value === undefined || value === null) return out;
  if (typeof value === "object") {
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) formEncode(v, prefix ? `${prefix}[${k}]` : k, out);
  } else out.append(prefix, String(value));
  return out;
}

async function stripe(env: Env, method: string, path: string, payload?: unknown) {
  const r = await fetch(`${STRIPE}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${env.STRIPE_SECRET_KEY}`,
      ...(payload ? { "Content-Type": "application/x-www-form-urlencoded" } : {}),
    },
    body: payload ? formEncode(payload).toString() : undefined,
  });
  const data = (await r.json().catch(() => ({}))) as Record<string, any>;
  if (!r.ok) throw new HttpError(502, `Stripe said: ${data.error?.message || r.status}`);
  return data;
}

export function checkoutMode(env: Env): "stripe" | "test" | null {
  if (env.STRIPE_SECRET_KEY) return "stripe";
  if (env.TEST_CHECKOUT === "1") return "test";
  return null;
}

export function createCheckoutSession(env: Env, o: { ref: string; name: string; description: string; cents: number; currency: string; email: string; successUrl: string; cancelUrl: string; slug: string; shipTo?: string[] }) {
  return stripe(env, "POST", "/checkout/sessions", {
    mode: "payment",
    // a physical product: Stripe's page asks for the address, limited to where it ships
    shipping_address_collection: o.shipTo?.length ? { allowed_countries: Object.fromEntries(o.shipTo.map((c, i) => [i, c])) } : undefined,
    // Stripe Tax works out sales tax from the buyer's address. Off until the owner has set the
    // business address and registrations in Stripe (Tax -> Settings), then STRIPE_TAX=1.
    automatic_tax: env.STRIPE_TAX === "1" ? { enabled: true } : undefined,
    billing_address_collection: env.STRIPE_TAX === "1" ? "required" : undefined,
    // A real invoice (PDF, numbered) for every purchase, emailed by Stripe: STRIPE_INVOICES=1.
    // Stripe charges a small fee per invoice, so it is off unless chosen.
    invoice_creation: env.STRIPE_INVOICES === "1" ? { enabled: true } : undefined,
    line_items: { 0: { quantity: 1, price_data: { currency: o.currency, unit_amount: o.cents, product_data: { name: o.name, description: o.description } } } },
    customer_email: o.email || undefined,
    client_reference_id: o.ref,
    metadata: { ref: o.ref, book: o.slug },
    success_url: o.successUrl,
    cancel_url: o.cancelUrl,
  });
}

export function retrieveCheckoutSession(env: Env, id: string) {
  return stripe(env, "GET", `/checkout/sessions/${encodeURIComponent(id)}`);
}

/** Stripe-Signature: "t=<unix>,v1=<hex>"; v1 = HMAC-SHA256(secret, "<t>.<raw body>"). Five-minute window. */
export async function verifyStripeSignature(raw: string, header: string | null, secret: string | undefined): Promise<boolean> {
  if (!header || !secret) return false;
  const parts = header.split(",").map((p) => p.split("="));
  const t = parts.find(([k]) => k === "t")?.[1];
  const sigs = parts.filter(([k]) => k === "v1").map(([, v]) => v);
  if (!t || !sigs.length || Math.abs(Date.now() / 1000 - Number(t)) > 300) return false;
  const expected = await hmacHex(secret, `${t}.${raw}`);
  return sigs.some((s) => sameString(s, expected));
}
