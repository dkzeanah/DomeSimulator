// Workers AI, on Cloudflare's own GPUs (the AI binding in wrangler.toml). No outside AI
// company sees the site's data. Every call is written to ai_runs so the owner can see what
// it was for, how long it took and whether it worked.
//
// What the model writes is always labelled as written by it, and it never supplies a
// figure: numbers come from the database (counted) or the {{tokens}} the mail fills in.

import { Env, HttpError, nowIso } from "./http";

export const MODEL = "@cf/meta/llama-3.3-70b-instruct-fp8-fast";

export const aiReady = (env: Env) => Boolean(env.AI);

export async function ask(env: Env, purpose: string, system: string, prompt: string, maxTokens = 700): Promise<string> {
  if (!env.AI) throw new HttpError(503, "Workers AI is not connected (the [ai] binding in wrangler.toml).");
  const t0 = Date.now();
  let out = "";
  let error: string | null = null;
  try {
    const r = (await env.AI.run(MODEL as Parameters<Ai["run"]>[0], {
      messages: [{ role: "system", content: system }, { role: "user", content: prompt }],
      max_tokens: maxTokens,
    } as never)) as { response?: unknown };
    out = typeof r?.response === "string" ? r.response : JSON.stringify(r?.response ?? "");
  } catch (e) {
    error = (e as Error).message || String(e);
  }
  await env.DB.prepare("INSERT INTO ai_runs(purpose, model, input_chars, output_chars, ms, ok, error, created_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?)")
    .bind(purpose, MODEL, system.length + prompt.length, out.length, Date.now() - t0, error ? 0 : 1, error, nowIso()).run();
  if (error) throw new Error(`Workers AI: ${error}`);
  return out.trim();
}

/** The first JSON object in a model's answer, or null. */
export function parseJson<T>(s: string): T | null {
  for (const candidate of [s, s.match(/\{[\s\S]*\}/)?.[0]]) {
    if (!candidate) continue;
    try {
      return JSON.parse(candidate) as T;
    } catch { /* try the next */ }
  }
  return null;
}

/** Figures typed into a draft instead of taken from a {{token}}: each one needs checking. */
export function typedFigures(text: string): string[] {
  const bare = text.replace(/\{\{[^}]*\}\}/g, " ");
  return [...new Set(bare.match(/\$?\d[\d,.]*%?/g) || [])];
}
