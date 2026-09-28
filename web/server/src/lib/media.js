// Turn a pasted YouTube / TikTok / Instagram URL into something embeddable.
//
// Every platform is embedded through its own iframe URL rather than its
// JavaScript widget, so the page never runs a third party's script and the
// content security policy only has to allow three frame origins.

const YT_ID = /^[A-Za-z0-9_-]{11}$/;

export function parseMediaUrl(input) {
  let url;
  try {
    url = new URL(String(input).trim());
  } catch {
    return null;
  }
  const host = url.hostname.replace(/^www\.|^m\./, '');
  const parts = url.pathname.split('/').filter(Boolean);

  if (host === 'youtu.be' && YT_ID.test(parts[0] || '')) {
    return { platform: 'youtube', embedId: parts[0], kind: 'video' };
  }
  if (host === 'youtube.com' || host === 'youtube-nocookie.com') {
    const v = url.searchParams.get('v');
    if (v && YT_ID.test(v)) return { platform: 'youtube', embedId: v, kind: 'video' };
    if (['shorts', 'embed', 'live'].includes(parts[0]) && YT_ID.test(parts[1] || '')) {
      return { platform: 'youtube', embedId: parts[1], kind: parts[0] === 'shorts' ? 'short' : 'video' };
    }
  }
  if (host === 'tiktok.com') {
    // https://www.tiktok.com/@handle/video/7312345678901234567
    const at = parts.indexOf('video');
    if (at >= 0 && /^\d{8,25}$/.test(parts[at + 1] || '')) {
      return { platform: 'tiktok', embedId: parts[at + 1], kind: 'short' };
    }
  }
  if (host === 'instagram.com') {
    // /p/CODE/, /reel/CODE/, /tv/CODE/ -- optionally after /username/
    const at = parts.findIndex((p) => ['p', 'reel', 'reels', 'tv'].includes(p));
    const code = at >= 0 ? parts[at + 1] : null;
    if (code && /^[A-Za-z0-9_-]{5,40}$/.test(code)) {
      return { platform: 'instagram', embedId: code, kind: parts[at] === 'p' ? 'post' : 'reel' };
    }
  }
  return null;
}

/** The iframe src for an item. Built here so the browser never assembles URLs. */
export function embedUrl(platform, embedId, kind) {
  switch (platform) {
    case 'youtube':
      return `https://www.youtube-nocookie.com/embed/${embedId}?rel=0`;
    case 'tiktok':
      return `https://www.tiktok.com/embed/v2/${embedId}`;
    case 'instagram':
      return `https://www.instagram.com/${kind === 'post' ? 'p' : 'reel'}/${embedId}/embed`;
    default:
      return null;
  }
}

export function thumbnailUrl(platform, embedId) {
  return platform === 'youtube' ? `https://i.ytimg.com/vi/${embedId}/hqdefault.jpg` : null;
}
