// The channel's latest uploads, from YouTube's public RSS feed.
//
// No API key and no quota: every channel publishes
// https://www.youtube.com/feeds/videos.xml?channel_id=UC... with its newest
// fifteen videos. Cached for an hour so a busy page makes one request.

import { config } from '../config.js';

const HOUR = 60 * 60 * 1000;
let cache = { at: 0, channel: '', items: [] };

const decode = (s) =>
  s.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'");

export function parseFeed(xml) {
  const entries = xml.split('<entry>').slice(1);
  return entries
    .map((entry) => {
      const id = entry.match(/<yt:videoId>([^<]+)<\/yt:videoId>/)?.[1];
      const title = entry.match(/<title>([^<]*)<\/title>/)?.[1];
      const published = entry.match(/<published>([^<]+)<\/published>/)?.[1];
      const link = entry.match(/<link rel="alternate" href="([^"]+)"/)?.[1] || '';
      return id ? { embedId: id, title: decode(title || ''), publishedAt: published || null, short: link.includes('/shorts/') } : null;
    })
    .filter(Boolean);
}

export async function latestUploads(channelId = config.youtubeChannelId, fetchImpl = fetch) {
  if (!channelId) return [];
  if (cache.channel === channelId && Date.now() - cache.at < HOUR) return cache.items;
  try {
    const response = await fetchImpl(
      `https://www.youtube.com/feeds/videos.xml?channel_id=${encodeURIComponent(channelId)}`,
      { signal: AbortSignal.timeout(8000) },
    );
    if (!response.ok) throw new Error(`YouTube feed ${response.status}`);
    const items = parseFeed(await response.text());
    cache = { at: Date.now(), channel: channelId, items };
    return items;
  } catch (error) {
    console.warn(`[youtube] ${error.message} -- showing the last good copy`);
    return cache.channel === channelId ? cache.items : [];
  }
}
