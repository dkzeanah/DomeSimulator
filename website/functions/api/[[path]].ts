// Every /api/* request lands here (Pages Functions' catch-all) and is dispatched by the
// small router in _lib/http.ts to the handlers in _lib/routes.ts.

import { loadUser } from "../_lib/auth";
import { Ctx, Env, HttpError, json } from "../_lib/http";
import api from "../_lib/routes";
import "../_lib/agent_routes";   // registers /api/agent/* and its admin controls on the same router
import "../_lib/ops_routes";     // automations, jobs, notices, the clock, the assistant
import "../_lib/user_routes";    // password reset, sessions, data export, the owner's user controls
import "../_lib/studio_routes";  // home focus, invite codes, promo codes, dome classes
import "../_lib/project_routes"; // the owner's projects and tasks
import "../_lib/media";          // the Media page: the latest YouTube videos, cached
import "../_lib/game_routes";    // the Portal world: saves and public chat
import "../_lib/stories";        // bedtime stories (/kids) and the Story Studio

export const onRequest: PagesFunction<Env> = async (context) => {
  const { request, env } = context;
  const url = new URL(request.url);
  const path = url.pathname.replace(/^\/api/, "") || "/";
  const hit = api.match(request.method, path);
  if (!hit) return json({ error: "No such API route." }, 404);
  const ctx: Ctx = { request, env, url, params: hit.params, user: null, setCookies: [], waitUntil: (p) => context.waitUntil(p) };
  try {
    // A state-changing request must come from this site's own pages.
    // Routes that other machines call are proved by a signature or token instead of the
    // origin: Stripe's webhook, the one-click unsubscribe a mail app POSTs, the mail program.
    const machine = path === "/stripe/webhook" || path.startsWith("/u/") || path.startsWith("/mailer/") || path.startsWith("/agent/") || path === "/ops/clock";
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
