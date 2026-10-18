// Media: the owner's latest YouTube videos and Shorts, and their TikTok, on one page. Both keep
// themselves current: YouTube is read by the site (/api/media, refreshed every half hour) and
// TikTok's own creator embed loads the newest posts in the visitor's browser.

import { useEffect, useRef, useState } from "react";
import { Panel } from "../components/ui";
import { api } from "../lib/api";
import { useMeta } from "../lib/meta";

interface Video { id: string; title: string; published: string | null; age: string | null; kind: "video" | "short" }
interface Media {
  youtube: { channelUrl: string; videos: Video[]; checkedAt: string | null; source: string | null };
  tiktok: { handle: string; profileUrl: string };
}

const thumb = (id: string) => `https://i.ytimg.com/vi/${id}/hqdefault.jpg`;
const when = (v: Video) => v.age || (v.published ? new Date(v.published).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" }) : "");

/** A picture until it is clicked, then the player -- so the page loads light and sets no
 *  YouTube cookies until someone chooses to watch (youtube-nocookie). */
function Player({ v, big = false }: { v: Video; big?: boolean }) {
  const [on, setOn] = useState(false);
  const ratio = v.kind === "short" && !big ? "aspect-[9/16]" : "aspect-video";
  return (
    <figure className="panel overflow-hidden">
      <div className={`relative ${ratio} bg-black`}>
        {on ? (
          <iframe className="absolute inset-0 w-full h-full" src={`https://www.youtube-nocookie.com/embed/${v.id}?autoplay=1&rel=0`} title={v.title}
            allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowFullScreen />
        ) : (
          <button className="absolute inset-0 w-full h-full group" onClick={() => setOn(true)} aria-label={`Play: ${v.title}`}>
            <img src={thumb(v.id)} alt="" loading="lazy" className="w-full h-full object-cover" />
            <span className="absolute inset-0 grid place-items-center">
              <span className="rounded-full w-14 h-14 grid place-items-center group-hover:scale-110 transition" style={{ background: "rgba(0,0,0,0.65)" }}>
                <svg viewBox="0 0 24 24" className="w-7 h-7 ml-1" fill="#fff" aria-hidden><path d="M8 5v14l11-7z" /></svg>
              </span>
            </span>
          </button>
        )}
      </div>
      <figcaption className={`p-3 ${big ? "" : "text-sm"}`}>
        <span className={big ? "text-xl font-semibold" : "font-semibold"}>{v.title}</span>
        {when(v) && <span className="block text-xs muted mt-0.5">{v.kind === "short" ? "Short -- " : ""}{when(v)}</span>}
      </figcaption>
    </figure>
  );
}

/** TikTok's own creator embed: it fetches the latest posts itself. */
function TikTok({ handle, url }: { handle: string; url: string }) {
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!handle || !box.current) return;
    box.current.innerHTML = `<blockquote class="tiktok-embed" cite="${url}" data-unique-id="${handle}" data-embed-type="creator" style="max-width:780px;min-width:288px;margin:0"><section><a target="_blank" rel="noopener" href="${url}">@${handle}</a></section></blockquote>`;
    const s = document.createElement("script");
    s.src = "https://www.tiktok.com/embed.js";
    s.async = true;
    box.current.appendChild(s);
  }, [handle, url]);
  return <div ref={box} className="min-h-[200px]" />;
}

export default function MediaPage() {
  useMeta("Media", "The latest films and shorts from Donovan Zeanah: the dome builds, the wedge method and the lab, on YouTube and TikTok.", "/media");
  const [m, setM] = useState<Media | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => { api<Media>("/media").then(setM).catch(() => setFailed(true)); }, []);
  const vids = m?.youtube.videos.filter((v) => v.kind === "video") ?? [];
  const shorts = m?.youtube.videos.filter((v) => v.kind === "short") ?? [];
  const [first, ...rest] = vids;
  return (
    <div className="mx-auto max-w-6xl px-4 py-10 grid gap-8">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">Media</p>
        <h1 className="text-4xl sm:text-5xl font-bold mt-1">The latest films</h1>
        <p className="mt-2 muted max-w-2xl">New uploads show up here on their own. Subscribe where you watch, and you will see them first.</p>
        <div className="flex flex-wrap gap-3 mt-4">
          {m?.youtube.channelUrl && <a className="btn" href={`${m.youtube.channelUrl}?sub_confirmation=1`} target="_blank" rel="noopener">Subscribe on YouTube</a>}
          {m?.tiktok.profileUrl && <a className="btn-ghost" href={m.tiktok.profileUrl} target="_blank" rel="noopener">Follow on TikTok</a>}
        </div>
      </div>

      <section className="grid gap-4" aria-label="YouTube">
        <h2 className="text-3xl font-semibold">YouTube</h2>
        {!m && !failed && <p className="muted">Loading the latest videos...</p>}
        {(failed || (m && !m.youtube.videos.length)) && (
          <p className="muted">The video list could not be loaded just now. <a className="underline" href="https://www.youtube.com/@donovanzeanah" target="_blank" rel="noopener">See the channel on YouTube</a>.</p>
        )}
        {first && <Player v={first} big />}
        {rest.length > 0 && <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">{rest.slice(0, 12).map((v) => <Player key={v.id} v={v} />)}</div>}
        {shorts.length > 0 && (
          <>
            <h3 className="text-2xl font-semibold mt-4">Shorts</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">{shorts.slice(0, 12).map((v) => <Player key={v.id} v={v} />)}</div>
          </>
        )}
      </section>

      {m?.tiktok.handle && (
        <Panel kicker="TikTok" title={`@${m.tiktok.handle}`}>
          <TikTok handle={m.tiktok.handle} url={m.tiktok.profileUrl} />
        </Panel>
      )}
    </div>
  );
}
