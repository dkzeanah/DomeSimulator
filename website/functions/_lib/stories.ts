// Bedtime stories (/kids) and the Story Studio (Admin -> Stories).
//
// A story is a slug, a title and a run of VERSIONS. A version is the whole story as a document --
// its voice, its figures and its pages, each page a scene, an optional camera move and its words --
// and versions are append-only: saving makes version n + 1, publishing points the story at one of
// them, and every earlier version stays readable and publishable.
//
// Narration belongs to the words, not the version. Each page's narration is found by a KEY, the
// first 16 hex digits of SHA-256(spoken words, voice, rate, pitch joined by NUL), which
// scripts/export_storytime.py computes the same way. A page whose words did not change keeps its
// narration in every version; a changed page needs narrating again, and the Studio says which.
// Narration is stored three ways: baked into the site (static:/storytime/...), spoken by the
// script and uploaded to R2 with an agent key, or recorded by the owner in the Studio in his own
// voice ("mine").

import { agentAuth } from "./agent";
import { requireAdmin } from "./auth";
import { Ctx, HttpError, body, json, nowIso, text } from "./http";
import { audit, emit } from "./ops";
import api from "./routes";

export const STORY_STATUSES = ["draft", "live", "hidden"] as const;
const SLUG = /^[a-z0-9][a-z0-9-]{1,58}[a-z0-9]$/;
const GAP = 1.4;

export interface Voice { name: string; rate?: string; pitch?: string }
export interface Page { id: string; kind?: string; scene: string; shot?: string; text: string }
export interface Doc { title: string; series?: string; voice: Voice; figures?: Record<string, unknown>; pages: Page[] }
interface StoryRow { slug: string; title: string; series: string; status: string; live_version: number | null; sort: number; created_at: string; updated_at: string }
interface AudioRow { key: string; src: string; content_type: string; words: string; duration: number; voice: string; created_at: string }

export const speakable = (t: string) => t.replace(/\s+--\s+/g, ", ").replace(/\n/g, " ");

async function sha256Hex(s: string) {
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export async function narrationKey(t: string, v: Voice) {
  return (await sha256Hex([speakable(t), v.name, v.rate || "+0%", v.pitch || "+0Hz"].join("\u0000"))).slice(0, 16);
}

/** A rough read-aloud time for a page with no narration yet: what the camera move and the turn wait for. */
const readingTime = (t: string) => Math.max(3, t.split(/\s+/).filter(Boolean).length * 0.42 + 1.2);

function checkDoc(raw: unknown): Doc {
  if (!raw || typeof raw !== "object") throw new HttpError(400, "doc is the story as an object.");
  const d = raw as Record<string, unknown>;
  const title = String(d.title || "").trim();
  if (!title || title.length > 120) throw new HttpError(400, "A story has a title of up to 120 characters.");
  const v = (d.voice || {}) as Record<string, unknown>;
  const voice: Voice = { name: String(v.name || "en-US-JennyNeural").slice(0, 60), rate: String(v.rate || "+0%").slice(0, 8), pitch: String(v.pitch || "+0Hz").slice(0, 8) };
  if (!Array.isArray(d.pages) || !d.pages.length || d.pages.length > 120) throw new HttpError(400, "A story has 1 to 120 pages.");
  const ids = new Set<string>();
  const pages = d.pages.map((p: Record<string, unknown>, i: number): Page => {
    const id = String(p.id || `p${i + 1}`).slice(0, 40);
    if (ids.has(id)) throw new HttpError(400, `Two pages are called "${id}".`);
    ids.add(id);
    const t = String(p.text ?? "");
    if (t.length > 2000) throw new HttpError(400, `Page "${id}" is over 2,000 characters.`);
    const page: Page = { id, kind: String(p.kind || "page").slice(0, 12), scene: String(p.scene || "stars").slice(0, 40), text: t };
    if (p.shot) page.shot = String(p.shot).slice(0, 30);
    return page;
  });
  const doc: Doc = { title, series: String(d.series || "").slice(0, 80), voice, pages };
  if (d.figures && typeof d.figures === "object") doc.figures = d.figures as Record<string, unknown>;
  if (JSON.stringify(doc).length > 200_000) throw new HttpError(400, "That story is too long to save.");
  return doc;
}

async function storyOf(ctx: Ctx, slug: string) {
  const s = await ctx.env.DB.prepare("SELECT * FROM stories WHERE slug = ?").bind(slug).first<StoryRow>();
  if (!s) throw new HttpError(404, "No such story.");
  return s;
}

async function versionOf(ctx: Ctx, slug: string, n?: number | null) {
  const row = n
    ? await ctx.env.DB.prepare("SELECT * FROM story_versions WHERE story = ? AND n = ?").bind(slug, n).first<{ n: number; doc: string; note: string; author: string; created_at: string }>()
    : await ctx.env.DB.prepare("SELECT * FROM story_versions WHERE story = ? ORDER BY n DESC LIMIT 1").bind(slug).first<{ n: number; doc: string; note: string; author: string; created_at: string }>();
  if (!row) throw new HttpError(404, "No such version.");
  return { n: row.n, doc: JSON.parse(row.doc) as Doc, note: row.note, author: row.author, createdAt: row.created_at };
}

const audioUrl = (slug: string, a: AudioRow) => a.src.startsWith("static:") ? a.src.slice(7) : `/api/storytime/audio/${slug}/${a.key}`;

/** What the player reads: every page with its narration (or none yet), its words' timings and how long it lasts. */
async function manifest(ctx: Ctx, slug: string, doc: Doc, n: number | null) {
  const keys = await Promise.all(doc.pages.map((p) => narrationKey(p.text, doc.voice)));
  const audio = new Map<string, AudioRow>();
  if (keys.length) {
    const rows = (await ctx.env.DB.prepare(`SELECT * FROM story_audio WHERE story = ? AND key IN (${keys.map(() => "?").join(",")})`).bind(slug, ...keys).all<AudioRow>()).results;
    for (const r of rows) audio.set(r.key, r);
  }
  const pages = doc.pages.map((p, i) => {
    const a = audio.get(keys[i]);
    return { ...p, key: keys[i], audio: a ? audioUrl(slug, a) : null, words: a ? JSON.parse(a.words) : [], duration: a ? a.duration : readingTime(p.text) };
  });
  return { id: slug, slug, version: n, title: doc.title, series: doc.series, voice: doc.voice, figures: doc.figures || {}, pages,
           runtime: Math.round(pages.reduce((s, p) => s + p.duration + GAP, 0) * 10) / 10,
           narrated: pages.filter((p) => p.audio).length };
}

async function saveVersion(ctx: Ctx, slug: string, raw: unknown, note: string, author: string) {
  const doc = checkDoc(raw);
  const n = (await ctx.env.DB.prepare("SELECT COALESCE(MAX(n), 0) + 1 n FROM story_versions WHERE story = ?").bind(slug).first<{ n: number }>())!.n;
  await ctx.env.DB.prepare("INSERT INTO story_versions(story, n, doc, note, author, created_at) VALUES(?, ?, ?, ?, ?, ?)")
    .bind(slug, n, JSON.stringify(doc), note.slice(0, 300), author, nowIso()).run();
  await ctx.env.DB.prepare("UPDATE stories SET title = ?, series = ?, updated_at = ? WHERE slug = ?").bind(doc.title, doc.series || "", nowIso(), slug).run();
  await emit(ctx, "story.version", { story: slug, version: n, note });
  return n;
}

async function storeNarration(ctx: Ctx, slug: string, b: Record<string, unknown>, voice: string) {
  const key = String(b.key || "");
  if (!/^[0-9a-f]{16}$/.test(key)) throw new HttpError(400, "key is the page's 16-digit narration key.");
  const type = String(b.contentType || "audio/mpeg");
  if (!/^audio\/(mpeg|webm|ogg|mp4|aac|wav)(;.*)?$/.test(type)) throw new HttpError(400, "That is not an audio type the player can use.");
  const bytes = Uint8Array.from(atob(String(b.audio || "")), (c) => c.charCodeAt(0));
  if (bytes.length < 200 || bytes.length > 12_000_000) throw new HttpError(400, "The narration is empty or over 12 MB.");
  if (!ctx.env.BOOKS) throw new HttpError(503, "Narration storage (R2) is not set up here.");
  const duration = Math.max(0.5, Math.min(600, Number(b.duration) || 0));
  const words = Array.isArray(b.words) ? b.words.slice(0, 2000) : [];
  const r2 = `storytime/${slug}/${key}-${Date.now()}`;
  await ctx.env.BOOKS.put(r2, bytes, { httpMetadata: { contentType: type } });
  await ctx.env.DB.prepare(
    "INSERT INTO story_audio(story, key, src, content_type, words, duration, voice, created_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?) "
    + "ON CONFLICT(story, key) DO UPDATE SET src = excluded.src, content_type = excluded.content_type, words = excluded.words, duration = excluded.duration, voice = excluded.voice, created_at = excluded.created_at",
  ).bind(slug, key, `r2:${r2}`, type, JSON.stringify(words), duration, voice, nowIso()).run();
  return { key, duration };
}

// ---------------------------------------------------------------- public: the stories and their narration

api.get("/stories", async (ctx) => {
  const rows = (await ctx.env.DB.prepare("SELECT slug, title, series, live_version FROM stories WHERE status = 'live' ORDER BY sort, created_at DESC").all<StoryRow>()).results;
  return json({ stories: rows.map((s) => ({ slug: s.slug, title: s.title, series: s.series })) });
});

api.get("/stories/:slug", async (ctx) => {
  const s = await storyOf(ctx, ctx.params.slug);
  const v = Number(ctx.url.searchParams.get("v")) || null;
  if (v || s.status !== "live" || !s.live_version) requireAdmin(ctx);    // drafts and old versions: the owner's preview only
  const ver = await versionOf(ctx, s.slug, v || s.live_version);
  return json(await manifest(ctx, s.slug, ver.doc, ver.n));
});

api.get("/storytime/audio/:slug/:key", async (ctx) => {
  const a = await ctx.env.DB.prepare("SELECT * FROM story_audio WHERE story = ? AND key = ?").bind(ctx.params.slug, ctx.params.key).first<AudioRow>();
  if (!a || !a.src.startsWith("r2:") || !ctx.env.BOOKS) throw new HttpError(404, "No such narration.");
  const obj = await ctx.env.BOOKS.get(a.src.slice(3));
  if (!obj) throw new HttpError(404, "No such narration.");
  return new Response(obj.body, { headers: { "Content-Type": a.content_type, "Cache-Control": "public, max-age=31536000, immutable" } });
});

// ---------------------------------------------------------------- the Story Studio

api.get("/admin/stories", async (ctx) => {
  requireAdmin(ctx);
  const rows = (await ctx.env.DB.prepare(
    "SELECT stories.*, (SELECT MAX(n) FROM story_versions WHERE story = slug) latest, (SELECT COUNT(*) FROM story_versions WHERE story = slug) versions FROM stories ORDER BY sort, created_at DESC",
  ).all<StoryRow & { latest: number; versions: number }>()).results;
  return json({ stories: rows.map((s) => ({ slug: s.slug, title: s.title, series: s.series, status: s.status, liveVersion: s.live_version, latest: s.latest, versions: s.versions, updatedAt: s.updated_at })), statuses: STORY_STATUSES });
});

/** A new story starts from the series' frame: hello by name, the story, goodnight. */
api.post("/admin/stories", async (ctx) => {
  const u = requireAdmin(ctx);
  const b = await body(ctx);
  const slug = String(b.slug || "").trim().toLowerCase();
  if (!SLUG.test(slug)) throw new HttpError(400, "The story's address is 3-60 lowercase letters, digits and dashes.");
  if (await ctx.env.DB.prepare("SELECT 1 FROM stories WHERE slug = ?").bind(slug).first()) throw new HttpError(409, "A story already has that address.");
  const title = text(b, "title", { min: 1, max: 120, required: true })!;
  let doc: unknown = b.doc;
  if (!doc && b.from) {
    // a new story can start as a copy of another's newest version (its intro, its voice, its outro)
    const from = await versionOf(ctx, String(b.from));
    doc = { ...from.doc, title, pages: from.doc.pages.filter((p) => p.kind === "intro" || p.kind === "outro") };
  }
  doc = doc || {
    title, series: "Dada's Stories", voice: { name: "en-US-JennyNeural", rate: "-12%", pitch: "+0Hz" },
    pages: [
      { id: "intro-1", kind: "intro", scene: "stars", text: "Hello, Annika. Hello, Amara. Are you all cozy? Look out the window, way up high. Do you see Dada's star?" },
      { id: "cover", kind: "title", scene: "cover", text: `${title}.` },
      { id: "p1", kind: "page", scene: "town", text: "" },
      { id: "outro", kind: "outro", scene: "goodnight", text: "The end. Goodnight, Annika. Goodnight, Amara. Sweet dreams." },
    ],
  };
  await ctx.env.DB.prepare("INSERT INTO stories(slug, title, series, status, live_version, sort, created_at, updated_at) VALUES(?, ?, ?, 'draft', NULL, 0, ?, ?)")
    .bind(slug, title, String((doc as Doc).series || ""), nowIso(), nowIso()).run();
  const n = await saveVersion(ctx, slug, doc, "started", u.email);
  await audit(ctx, "story.create", `story:${slug}`, { title });
  return json({ slug, n }, 201);
});

api.get("/admin/stories/:slug", async (ctx) => {
  requireAdmin(ctx);
  const s = await storyOf(ctx, ctx.params.slug);
  const versions = (await ctx.env.DB.prepare("SELECT n, note, author, created_at FROM story_versions WHERE story = ? ORDER BY n DESC").bind(s.slug).all<{ n: number; note: string; author: string; created_at: string }>()).results;
  const v = Number(ctx.url.searchParams.get("v")) || null;
  const ver = await versionOf(ctx, s.slug, v);
  return json({
    story: { slug: s.slug, title: s.title, series: s.series, status: s.status, liveVersion: s.live_version },
    versions: versions.map((x) => ({ n: x.n, note: x.note, author: x.author, createdAt: x.created_at })),
    version: { n: ver.n, note: ver.note, doc: ver.doc },
    manifest: await manifest(ctx, s.slug, ver.doc, ver.n),
  });
});

/** The player's view of a draft that has not been saved: the Studio's live preview. */
api.post("/admin/stories/:slug/preview", async (ctx) => {
  requireAdmin(ctx);
  const s = await storyOf(ctx, ctx.params.slug);
  const b = await body(ctx);
  return json(await manifest(ctx, s.slug, checkDoc(b.doc), null));
});

api.post("/admin/stories/:slug/versions", async (ctx) => {
  const u = requireAdmin(ctx);
  const s = await storyOf(ctx, ctx.params.slug);
  const b = await body(ctx);
  const n = await saveVersion(ctx, s.slug, b.doc, text(b, "note", { max: 300 }) || "", u.email);
  await audit(ctx, "story.version", `story:${s.slug}`, { n });
  return json({ n }, 201);
});

api.post("/admin/stories/:slug/publish", async (ctx) => {
  requireAdmin(ctx);
  const s = await storyOf(ctx, ctx.params.slug);
  const b = await body(ctx);
  const ver = await versionOf(ctx, s.slug, Number(b.n) || null);
  await ctx.env.DB.prepare("UPDATE stories SET status = 'live', live_version = ?, title = ?, updated_at = ? WHERE slug = ?").bind(ver.n, ver.doc.title, nowIso(), s.slug).run();
  await audit(ctx, "story.publish", `story:${s.slug}`, { n: ver.n });
  await emit(ctx, "story.published", { story: s.slug, version: ver.n, title: ver.doc.title });
  return json({ ok: true, liveVersion: ver.n });
});

api.patch("/admin/stories/:slug", async (ctx) => {
  requireAdmin(ctx);
  const s = await storyOf(ctx, ctx.params.slug);
  const b = await body(ctx);
  const sets: string[] = [], vals: unknown[] = [];
  if ("status" in b) {
    const st = String(b.status);
    if (!(STORY_STATUSES as readonly string[]).includes(st)) throw new HttpError(400, "status is draft, live or hidden.");
    if (st === "live" && !s.live_version) throw new HttpError(400, "Publish a version first.");
    sets.push("status = ?"); vals.push(st);
  }
  if ("sort" in b) { sets.push("sort = ?"); vals.push(Math.round(Number(b.sort) || 0)); }
  if (!sets.length) throw new HttpError(400, "Nothing to change.");
  sets.push("updated_at = ?"); vals.push(nowIso());
  await ctx.env.DB.prepare(`UPDATE stories SET ${sets.join(", ")} WHERE slug = ?`).bind(...vals, s.slug).run();
  await audit(ctx, "story.edit", `story:${s.slug}`, b);
  return json({ ok: true });
});

/** The owner's own voice, recorded in the Studio, page by page. */
api.post("/admin/stories/:slug/narration", async (ctx) => {
  requireAdmin(ctx);
  const s = await storyOf(ctx, ctx.params.slug);
  const b = await body(ctx);
  const r = await storeNarration(ctx, s.slug, b, String(b.voice || "mine").slice(0, 60));
  await audit(ctx, "story.narrate", `story:${s.slug}`, { key: r.key, by: "studio" });
  return json(r, 201);
});

// ---------------------------------------------------------------- the narration script (an agent key, scope stories:write)

api.get("/agent/stories/:slug/narration", async (ctx) => {
  await agentAuth(ctx, "stories:write");
  const s = await storyOf(ctx, ctx.params.slug);
  const ver = await versionOf(ctx, s.slug, Number(ctx.url.searchParams.get("v")) || null);
  const m = await manifest(ctx, s.slug, ver.doc, ver.n);
  const seen = new Set<string>();
  const pages = m.pages.filter((p) => !p.audio && p.text.trim() && !seen.has(p.key) && seen.add(p.key))
    .map((p) => ({ id: p.id, key: p.key, text: p.text, spoken: speakable(p.text) }));
  return json({ n: ver.n, voice: ver.doc.voice, pages });
});

api.post("/agent/stories/:slug/narration", async (ctx) => {
  const key = await agentAuth(ctx, "stories:write");
  const s = await storyOf(ctx, ctx.params.slug);
  const b = await body(ctx);
  const ver = await versionOf(ctx, s.slug);
  const r = await storeNarration(ctx, s.slug, b, ver.doc.voice.name);
  await audit(ctx, "story.narrate", `story:${s.slug}`, { key: r.key }, { kind: "agent", id: key.id, name: key.name });
  return json(r, 201);
});

api.post("/agent/stories/:slug/versions", async (ctx) => {
  const key = await agentAuth(ctx, "stories:write");
  const s = await storyOf(ctx, ctx.params.slug);
  const b = await body(ctx);
  const n = await saveVersion(ctx, s.slug, b.doc, text(b, "note", { max: 300 }) || "", `agent:${key.name}`);
  await audit(ctx, "story.version", `story:${s.slug}`, { n }, { kind: "agent", id: key.id, name: key.name });
  return json({ n }, 201);
});
