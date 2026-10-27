// Episodes (/episodes): every finished film, played from R2.
//
// The list is src/generated/episodes.json, written by scripts/export_episodes.py from the
// project's own library, so the page needs no API to know what exists. This file only serves
// the files: GET /api/media/episodes/<slug>/v<n>/<file> streams from the MEDIA bucket with
// HTTP ranges, which is what lets a video seek. Keys carry the version, so a file never changes
// under its key and is cached for a year. Only keys the manifest names are served.

import { HttpError } from "./http";
import api from "./routes";
import manifest from "../../src/generated/episodes.json";

type Part = { key: string } | null;
const KEYS = new Set<string>();
for (const e of (manifest as { episodes: Record<string, unknown>[] }).episodes) {
  for (const part of ["video", "vertical", "captions", "thumb"]) {
    const p = e[part] as Part;
    if (p?.key) KEYS.add(p.key);
  }
}

const TYPES: Record<string, string> = { mp4: "video/mp4", vtt: "text/vtt; charset=utf-8", jpg: "image/jpeg" };

api.get("/media/episodes/:slug/:version/:file", async (ctx) => {
  const key = `episodes/${ctx.params.slug}/${ctx.params.version}/${ctx.params.file}`;
  if (!KEYS.has(key)) throw new HttpError(404, "No such episode file.");
  if (!ctx.env.MEDIA) throw new HttpError(503, "The media store is not connected yet.");
  const type = TYPES[key.split(".").pop() || ""] || "application/octet-stream";
  const range = ctx.request.headers.get("Range");
  const head = await ctx.env.MEDIA.head(key);
  if (!head) throw new HttpError(404, "That episode file has not been uploaded yet.");
  const size = head.size;
  const common = {
    "Content-Type": type, "Accept-Ranges": "bytes", "Cache-Control": "public, max-age=31536000, immutable",
    "ETag": head.httpEtag,
  };
  const m = range ? /^bytes=(\d*)-(\d*)$/.exec(range.trim()) : null;
  if (m && (m[1] || m[2])) {
    let start: number, end: number;
    if (m[1]) {
      start = Number(m[1]);
      end = m[2] ? Math.min(Number(m[2]), size - 1) : size - 1;
    } else {
      start = Math.max(0, size - Number(m[2]));
      end = size - 1;
    }
    if (start >= size || start > end) {
      return new Response(null, { status: 416, headers: { ...common, "Content-Range": `bytes */${size}` } });
    }
    const obj = await ctx.env.MEDIA.get(key, { range: { offset: start, length: end - start + 1 } });
    if (!obj) throw new HttpError(404, "That episode file has not been uploaded yet.");
    return new Response(ctx.request.method === "HEAD" ? null : obj.body, {
      status: 206, headers: { ...common, "Content-Length": String(end - start + 1), "Content-Range": `bytes ${start}-${end}/${size}` },
    });
  }
  const obj = ctx.request.method === "HEAD" ? null : await ctx.env.MEDIA.get(key);
  return new Response(obj ? obj.body : null, { headers: { ...common, "Content-Length": String(size) } });
});
