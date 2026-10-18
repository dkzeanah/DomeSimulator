// The Portal world's game, on the server: each member's saved progress, and public chat.
// Chat: everyone reads; members write, one message every few seconds, 200 characters; staff
// remove. The game itself runs in the browser (src/world/game/).

import { isStaffRole, normaliseUsername, requireAdmin, requireUser } from "./auth";
import { HttpError, body, json, nowIso, text } from "./http";
import { audit } from "./ops";
import api from "./routes";

const MAX_SAVE = 40_000;          // characters of JSON: a full save is a few kilobytes
const CHAT_GAP_MS = 2500;

api.get("/game/save", async (ctx) => {
  const u = requireUser(ctx);
  const row = await ctx.env.DB.prepare("SELECT data FROM game_saves WHERE user_id = ?").bind(u.id).first<{ data: string }>();
  return json({ save: row ? JSON.parse(row.data) : null });
});

api.put("/game/save", async (ctx) => {
  const u = requireUser(ctx);
  const b = await body(ctx);
  const save = b.save as Record<string, unknown> | undefined;
  if (!save || typeof save !== "object" || save.v !== 1) throw new HttpError(400, "save must be a version-1 game save.");
  const data = JSON.stringify(save);
  if (data.length > MAX_SAVE) throw new HttpError(413, "That save is too large.");
  // the total level, for a high-scores page later: computed here, not trusted from the browser
  const xp = (save.xp || {}) as Record<string, number>;
  let total = 0;
  for (const v of Object.values(xp)) {
    let lvl = 1, points = 0;
    while (lvl < 99) { points += Math.floor(lvl + 300 * Math.pow(2, lvl / 7)); if (Math.floor(points / 4) > Number(v)) break; lvl++; }
    total += lvl;
  }
  await ctx.env.DB.prepare(
    "INSERT INTO game_saves(user_id, data, total_level, updated_at) VALUES(?, ?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET data = excluded.data, total_level = excluded.total_level, updated_at = excluded.updated_at",
  ).bind(u.id, data, total, nowIso()).run();
  return json({ ok: true, totalLevel: total });
});

// The house portal's "Friend's house": anybody's house, by username. Only what the house shows --
// the member's name and how their house is built -- and never an email.
api.get("/game/house/:name", async (ctx) => {
  const u = normaliseUsername(decodeURIComponent(ctx.params.name || ""));
  if (!/^[a-z0-9][a-z0-9._-]{2,29}$/.test(u)) throw new HttpError(404, "Nobody by that name has a house.");
  const row = await ctx.env.DB.prepare(
    "SELECT u.id, u.username, u.display_name, u.suspended_reason, s.data FROM users u LEFT JOIN game_saves s ON s.user_id = u.id WHERE u.username = ?",
  ).bind(u).first<{ id: number; username: string; display_name: string; suspended_reason: string | null; data: string | null }>();
  if (!row || row.suspended_reason) throw new HttpError(404, "Nobody by that name has a house.");
  let style = "starter";
  try { const h = row.data ? (JSON.parse(row.data) as { house?: unknown }).house : undefined; if (typeof h === "string" && /^(starter|[1-5])$/.test(h)) style = h; } catch { /* a bad save keeps the starter */ }
  return json({ username: row.username, name: row.display_name || row.username, style, yours: ctx.user?.id === row.id });
});

api.get("/game/chat", async (ctx) => {
  const after = Math.max(0, Number(ctx.url.searchParams.get("after") || 0) || 0);
  const rows = (await ctx.env.DB.prepare(
    `SELECT c.id, c.name, c.text, c.created_at, u.role FROM game_chat c LEFT JOIN users u ON u.id = c.user_id
     WHERE c.area = 'public' AND c.removed_by IS NULL AND c.id > ? ORDER BY c.id DESC LIMIT 50`,
  ).bind(after).all<{ id: number; name: string; text: string; created_at: string; role: string | null }>()).results.reverse();
  return json({ messages: rows.map((r) => ({ id: r.id, name: r.name, text: r.text, at: r.created_at, staff: isStaffRole(r.role) })) });
});

api.post("/game/chat", async (ctx) => {
  const u = requireUser(ctx);
  const t = (text(await body(ctx), "text", { min: 1, max: 200, required: true }) || "").replace(/[\u0000-\u001f\u007f]/g, " ").trim();
  if (!t) throw new HttpError(400, "Say something first.");
  const last = await ctx.env.DB.prepare("SELECT created_at FROM game_chat WHERE user_id = ? ORDER BY id DESC LIMIT 1").bind(u.id).first<{ created_at: string }>();
  if (last && Date.now() - Date.parse(last.created_at) < CHAT_GAP_MS) throw new HttpError(429, "Slow down a little.");
  const name = u.username || u.display_name;
  await ctx.env.DB.prepare("INSERT INTO game_chat(user_id, name, text, created_at) VALUES(?, ?, ?, ?)").bind(u.id, name, t, nowIso()).run();
  return json({ ok: true }, 201);
});

api.delete("/game/chat/:id", async (ctx) => {
  const u = requireAdmin(ctx);
  const r = await ctx.env.DB.prepare("UPDATE game_chat SET removed_by = ? WHERE id = ? AND removed_by IS NULL").bind(u.id, Number(ctx.params.id)).run();
  if (!r.meta.changes) throw new HttpError(404, "No such message.");
  await audit(ctx, "chat.remove", `chat:${ctx.params.id}`);
  return json({ ok: true });
});
