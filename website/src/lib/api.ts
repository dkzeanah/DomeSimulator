// Talking to /api. Errors come back as the sentence the server wrote.

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function api<T = any>(path: string, opts: { method?: string; body?: unknown } = {}): Promise<T> {
  const r = await fetch(`/api${path}`, {
    method: opts.method || (opts.body ? "POST" : "GET"),
    headers: opts.body ? { "Content-Type": "application/json" } : undefined,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
    credentials: "same-origin",
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new ApiError(r.status, data.error || `Request failed (${r.status}).`);
  return data as T;
}

export const money = (cents: number, currency = "usd") =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: currency.toUpperCase(), maximumFractionDigits: cents % 100 ? 2 : 0 }).format(cents / 100);

export const usd = (dollars: number) => money(Math.round(dollars * 100));

export const n = (x: number) => new Intl.NumberFormat("en-US").format(x);
