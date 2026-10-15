// Every /api/* request lands here (Pages Functions' catch-all) and is dispatched by the
// small router in _lib/http.ts to the handlers in _lib/routes.ts.

import { loadUser } from "../_lib/auth";
import { Ctx, Env, HttpError, json } from "../_lib/http";
import api from "../_lib/routes";

export const onRequest: PagesFunction<Env> = async ({ request, env }) => {
  const url = new URL(request.url);
  const path = url.pathname.replace(/^\/api/, "") || "/";
  const hit = api.match(request.method, path);
  if (!hit) return json({ error: "No such API route." }, 404);
  const ctx: Ctx = { request, env, url, params: hit.params, user: null, setCookies: [] };
  try {
    // A state-changing request must come from this site's own pages.
    // Routes that other machines call are proved by a signature or token instead of the
    // origin: Stripe's webhook, the one-click unsubscribe a mail app POSTs, the mail program.
    const machine = path === "/stripe/webhook" || path.startsWith("/u/") || path.startsWith("/mailer/");
    if (!["GET", "HEAD"].includes(request.method) && !machine) {
      const origin = request.headers.get("Origin");
      if (origin && origin !== url.origin) throw new HttpError(403, "Requests must come from this site.");
    }
    ctx.user = await loadUser(ctx);
    return await hit.handler(ctx);
  } catch (e) {
    if (e instanceof HttpError) return json({ error: e.message }, e.status, ctx);
    console.error(e);
    return json({ error: "Something went wrong on our side. Please try again." }, 500, ctx);
  }
};
