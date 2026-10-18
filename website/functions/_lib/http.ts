// The API's plumbing: the environment, JSON in and out, errors people can read, and a
// router small enough to read in one sitting (Pages Functions hand every /api/* request
// to functions/api/[[path]].ts, which dispatches here).

export interface Env {
  DB: D1Database;
  BOOKS?: R2Bucket;
  PUBLIC_URL?: string;
  SESSION_SECRET?: string;
  ADMIN_EMAILS?: string;
  OWNER_USERNAME?: string; // the owner's sign-in name, reserved for the ADMIN_EMAILS address (wrangler.toml)
  STRIPE_SECRET_KEY?: string;
  STRIPE_WEBHOOK_SECRET?: string;
  TEST_CHECKOUT?: string; // "1" locally: a stand-in for Stripe's page. Never set in production.
  STRIPE_TAX?: string; // "1": Stripe Tax on every checkout (set up Tax in Stripe first)
  STRIPE_INVOICES?: string; // "1": Stripe makes and emails an invoice for every purchase
  MAILER_TOKEN?: string; // the owner's mail program presents this to collect the queue
  MAIL_POSTAL_ADDRESS?: string; // required by law in marketing email; marketing is refused without it
  OPS_TOKEN?: string; // the zeanahlab-ops Worker presents this to run the clock
  AI?: Ai; // Workers AI (the [ai] binding)
}

export interface User {
  id: number;
  email: string;
  password_hash: string;
  display_name: string;
  role: string;
  bio: string | null;
  city: string | null;
  region: string | null;
  country: string | null;
  public_profile: number;
  created_at: string;
  status?: string;
  last_seen_at?: string | null;
  email_verified_at?: string | null;
  username?: string | null;
  joined_with?: string | null;
  dome_long_in?: number | null;
  dome_status?: string | null;
  dome_note?: string | null;
}

export interface Ctx {
  request: Request;
  env: Env;
  url: URL;
  params: Record<string, string>;
  user: User | null;
  /** cookies to set on the way out */
  setCookies: string[];
  /** keep working after the response has gone (Pages' waitUntil) */
  waitUntil?: (p: Promise<unknown>) => void;
}

export class HttpError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export const nowIso = (offsetMs = 0) => new Date(Date.now() + offsetMs).toISOString();

export function json(data: unknown, status = 200, ctx?: Ctx): Response {
  const headers = new Headers({ "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" });
  for (const c of ctx?.setCookies ?? []) headers.append("Set-Cookie", c);
  return new Response(JSON.stringify(data), { status, headers });
}

export async function body(ctx: Ctx): Promise<Record<string, unknown>> {
  try {
    const data = await ctx.request.json();
    if (data && typeof data === "object" && !Array.isArray(data)) return data as Record<string, unknown>;
  } catch {
    /* fall through */
  }
  throw new HttpError(400, "That request was not valid JSON.");
}

// ---------------------------------------------------------------- validation
// Small, explicit checks. Every message finishes the sentence "<field> ...".

export function text(b: Record<string, unknown>, key: string, opts: { min?: number; max: number; required?: boolean }): string | null {
  const v = b[key];
  if (v === undefined || v === null || v === "") {
    if (opts.required) throw new HttpError(400, `${key} is required.`);
    return null;
  }
  if (typeof v !== "string") throw new HttpError(400, `${key} must be text.`);
  const t = v.trim();
  if (opts.min && t.length < opts.min) throw new HttpError(400, `${key} needs at least ${opts.min} characters.`);
  if (t.length > opts.max) throw new HttpError(400, `${key} is too long (at most ${opts.max}).`);
  return t || null;
}

export function num(b: Record<string, unknown>, key: string, opts: { min?: number; max?: number; required?: boolean } = {}): number | null {
  const v = b[key];
  if (v === undefined || v === null || v === "") {
    if (opts.required) throw new HttpError(400, `${key} is required.`);
    return null;
  }
  const n = typeof v === "number" ? v : Number(v);
  if (!Number.isFinite(n)) throw new HttpError(400, `${key} must be a number.`);
  if (opts.min !== undefined && n < opts.min) throw new HttpError(400, `${key} must be at least ${opts.min}.`);
  if (opts.max !== undefined && n > opts.max) throw new HttpError(400, `${key} must be at most ${opts.max}.`);
  return n;
}

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export function email(b: Record<string, unknown>, key = "email"): string {
  const v = text(b, key, { max: 320, required: true })!.toLowerCase();
  if (!EMAIL.test(v)) throw new HttpError(400, "That email address does not look right.");
  return v;
}

/** The field real people never see. Bots fill it in. */
export function honeypot(b: Record<string, unknown>) {
  if (typeof b.website === "string" && b.website.length > 0) throw new HttpError(400, "Leave the last field empty.");
}

// ---------------------------------------------------------------- router

type Handler = (ctx: Ctx) => Promise<Response> | Response;
interface Route { method: string; parts: string[]; handler: Handler }

export class Router {
  private routes: Route[] = [];
  on(method: string, path: string, handler: Handler) {
    this.routes.push({ method, parts: path.split("/").filter(Boolean), handler });
    return this;
  }
  get(p: string, h: Handler) { return this.on("GET", p, h); }
  post(p: string, h: Handler) { return this.on("POST", p, h); }
  patch(p: string, h: Handler) { return this.on("PATCH", p, h); }
  put(p: string, h: Handler) { return this.on("PUT", p, h); }
  delete(p: string, h: Handler) { return this.on("DELETE", p, h); }

  match(method: string, path: string): { handler: Handler; params: Record<string, string> } | null {
    const parts = path.split("/").filter(Boolean);
    for (const r of this.routes) {
      const sameMethod = r.method === method || (method === "HEAD" && r.method === "GET");
      if (!sameMethod || r.parts.length !== parts.length) continue;
      const params: Record<string, string> = {};
      let ok = true;
      for (let i = 0; i < parts.length; i++) {
        if (r.parts[i].startsWith(":")) params[r.parts[i].slice(1)] = decodeURIComponent(parts[i]);
        else if (r.parts[i] !== parts[i]) { ok = false; break; }
      }
      if (ok) return { handler: r.handler, params };
    }
    return null;
  }
}
