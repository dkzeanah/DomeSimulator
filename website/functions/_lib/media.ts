// The Media page's YouTube list: the owner's latest videos and Shorts, read from YouTube itself
// so a new upload appears without anyone touching the site. No API key: YouTube's public feed
// first, and, because that feed has been answering "not found" for some channels, the channel's
// own pages as the fallback. The last good list is kept (settings: media.youtube) and served while
// a fresh one is fetched in the background, at most every thirty minutes -- so the page is fast,
// and a YouTube outage shows the last list rather than nothing. TikTok needs none of this: its
// creator embed updates itself in the visitor's browser.

import facts from "../../src/generated/facts.json";
import { Ctx, json, nowIso } from "./http";
import { getSetting, setSetting } from "./ops";
import api from "./routes";

export interface Video { id: string; title: string; published: string | null; age: string | null; kind: "video" | "short" }
interface Cached { at: string; source: string; videos: Video[] }

const KEY = "media.youtube";
const FRESH_MS = 30 * 60_000;
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36";
const site = facts.site as { youtubeChannelUrl?: string; youtubeChannelId?: string; tiktokHandle?: string };

const decode = (s: string) => s.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'");

/** YouTube's Atom feed: id, title and publish date for the latest fifteen. */
export function parseFeed(xml: string): Video[] {
  return [...xml.matchAll(/<entry>([\s\S]*?)<\/entry>/g)].map(([, e]) => ({
    id: /<yt:videoId>([^<]+)<\/yt:videoId>/.exec(e)?.[1] || "",
    title: decode(/<title>([^<]*)<\/title>/.exec(e)?.[1] || ""),
    published: /<published>([^<]+)<\/published>/.exec(e)?.[1] || null,
    age: null,
    kind: /\/shorts\//.test(e) ? "short" as const : "video" as const,
  })).filter((v) => v.id);
}

function initialData(html: string): unknown {
  const m = /var ytInitialData = (\{.*?\});<\/script>/s.exec(html);
  if (!m) return null;
  try { return JSON.parse(m[1]); } catch { return null; }
}

/** The channel's Videos or Shorts tab, as YouTube draws it: newest first. */
export function parseChannelPage(html: string, kind: "video" | "short"): Video[] {
  const out: Video[] = [];
  const walk = (o: unknown): void => {
    if (Array.isArray(o)) { o.forEach(walk); return; }
    if (!o || typeof o !== "object") return;
    const r = o as Record<string, any>;
    const l = r.lockupViewModel;
    if (kind === "video" && l?.contentType === "LOCKUP_CONTENT_TYPE_VIDEO" && l.contentId) {
      const meta = l.metadata?.lockupMetadataViewModel;
      const parts = (meta?.metadata?.contentMetadataViewModel?.metadataRows || []).flatMap((row: any) => row.metadataParts || []);
      out.push({ id: l.contentId, title: meta?.title?.content || "", published: null, age: parts.map((p: any) => p.text?.content).find((t: string) => /ago$/.test(t || "")) || null, kind });
    }
    const s = r.shortsLockupViewModel;
    if (kind === "short" && s) {
      const id = s.onTap?.innertubeCommand?.reelWatchEndpoint?.videoId;
      if (id) out.push({ id, title: s.overlayMetadata?.primaryText?.content || "", published: null, age: null, kind });
    }
    for (const v of Object.values(r)) walk(v);
  };
  walk(initialData(html));
  return out.filter((v, i, a) => a.findIndex((x) => x.id === v.id) === i);
}

async function get(url: string) {
  const r = await fetch(url, { headers: { "User-Agent": UA, "Accept-Language": "en-US,en;q=0.8" }, cf: { cacheTtl: 300 } } as RequestInit);
  return r.ok ? r.text() : null;
}

/** Ask YouTube now. Throws only when every source fails. */
export async function fetchYouTube(): Promise<Cached> {
  const id = site.youtubeChannelId, url = (site.youtubeChannelUrl || "").replace(/\/$/, "");
  if (id) {
    const xml = await get(`https://www.youtube.com/feeds/videos.xml?channel_id=${id}`).catch(() => null);
    const videos = xml ? parseFeed(xml) : [];
    if (videos.length) return { at: nowIso(), source: "feed", videos };
  }
  if (!url) throw new Error("No YouTube channel is configured (web/site.config.json).");
  const [videosHtml, shortsHtml] = await Promise.all([get(`${url}/videos`).catch(() => null), get(`${url}/shorts`).catch(() => null)]);
  const videos = [...(videosHtml ? parseChannelPage(videosHtml, "video") : []), ...(shortsHtml ? parseChannelPage(shortsHtml, "short") : [])];
  if (!videos.length) throw new Error("YouTube gave no videos.");
  return { at: nowIso(), source: "channel page", videos };
}

async function refresh(ctx: Ctx): Promise<Cached | null> {
  try {
    const fresh = await fetchYouTube();
    await setSetting(ctx, KEY, JSON.stringify(fresh));
    return fresh;
  } catch (e) {
    console.error("media refresh failed", e);
    return null;
  }
}

api.get("/media", async (ctx) => {
  const raw = await getSetting(ctx, KEY);
  let cached: Cached | null = raw ? JSON.parse(raw) : null;
  const stale = !cached || Date.now() - Date.parse(cached.at) > FRESH_MS;
  if (!cached) cached = await refresh(ctx);
  else if (stale) ctx.waitUntil ? ctx.waitUntil(refresh(ctx)) : await refresh(ctx);
  return json({
    youtube: { channelUrl: site.youtubeChannelUrl || "", videos: cached?.videos.slice(0, 24) ?? [], checkedAt: cached?.at ?? null, source: cached?.source ?? null },
    tiktok: { handle: site.tiktokHandle || "", profileUrl: site.tiktokHandle ? `https://www.tiktok.com/@${site.tiktokHandle}` : "" },
  });
});
