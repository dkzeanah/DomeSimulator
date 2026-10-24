// Episodes: every finished film, played from this site (R2), grouped by series.
//
// The list is src/generated/episodes.json (scripts/export_episodes.py), written from the
// project's own library: each film's newest finished cut, with the title, description and
// chapters of its own release copy. /episodes lists them; /episodes/:slug plays one, with
// captions, chapter links and the phone cut where there is one.

import { useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import data from "../generated/episodes.json";
import { useMeta } from "../lib/meta";

interface Part { key: string; bytes?: number }
interface Episode {
  slug: string; series: string; title: string; description: string; chapters: { t: number; title: string }[];
  made: string; duration: number; width: number; height: number; episode: string | null;
  video: Part; vertical: Part | null; captions: Part | null; thumb: Part;
}

const EPISODES = (data as { episodes: Episode[] }).episodes;
const src = (p: Part) => `/api/media/${p.key}`;
const clock = (s: number) => {
  const m = Math.floor(s / 60), r = Math.floor(s % 60);
  return m >= 60 ? `${Math.floor(m / 60)}:${String(m % 60).padStart(2, "0")}:${String(r).padStart(2, "0")}` : `${m}:${String(r).padStart(2, "0")}`;
};
const ABOUT: Record<string, string> = {
  "Cabin World": "The films remade in one place: a hilltop at sunset, the solver's dome on its pad.",
  "Films": "The method, one idea at a time. Every number on screen is computed by the model that drew it.",
  "Level With Me": "A sitcom about building a dome with people who disagree about everything except the numbers.",
  "Masterclasses": "Long-form walk-throughs of a whole build.",
  "Bedtime Stories": "Read aloud, for small builders.",
  "The Dome Case": "The argument for the dome as housing, in short chapters.",
  "Early films": "Where it started. Kept up because the corrections are on camera, not hidden.",
};

function Card({ e }: { e: Episode }) {
  return (
    <Link to={`/episodes/${e.slug}`} className="panel overflow-hidden group block">
      <div className="relative aspect-video bg-black">
        <img src={src(e.thumb)} alt="" loading="lazy" className="absolute inset-0 w-full h-full object-cover group-hover:opacity-90" />
        <span className="absolute bottom-2 right-2 text-xs font-semibold px-1.5 py-0.5 rounded" style={{ background: "rgba(0,0,0,.75)", color: "#fff" }}>
          {clock(e.duration)}
        </span>
      </div>
      <div className="p-3">
        {e.episode && <p className="text-xs accent font-semibold">{e.episode}</p>}
        <p className="font-semibold leading-snug">{e.episode ? e.title.replace(/^.*?:\s*/, "") : e.title}</p>
      </div>
    </Link>
  );
}

export function EpisodeList() {
  useMeta("Episodes", "Every film from the dome project, free to watch: the wedge method, the cabin films, Level With Me and the masterclasses.", "/episodes");
  const series = useMemo(() => {
    const out: [string, Episode[]][] = [];
    for (const e of EPISODES) {
      const last = out[out.length - 1];
      if (last && last[0] === e.series) last[1].push(e);
      else out.push([e.series, [e]]);
    }
    return out;
  }, []);
  const hours = EPISODES.reduce((t, e) => t + e.duration, 0) / 3600;
  return (
    <div className="mx-auto max-w-6xl px-4 py-10 grid gap-10">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">Episodes</p>
        <h1 className="text-4xl sm:text-5xl font-bold mt-1">Every film, free to watch</h1>
        <p className="mt-2 muted max-w-2xl">
          {EPISODES.length} films, {hours.toFixed(1)} hours: how to build a dome from split logs, and the numbers behind every step.
        </p>
        <nav className="flex flex-wrap gap-2 mt-4 text-sm">
          {series.map(([name, list]) => (
            <a key={name} href={`#${name.toLowerCase().replace(/\W+/g, "-")}`} className="btn-ghost !py-1">{name} ({list.length})</a>
          ))}
        </nav>
      </div>
      {series.map(([name, list]) => (
        <section key={name} id={name.toLowerCase().replace(/\W+/g, "-")} className="grid gap-4 scroll-mt-20">
          <div>
            <h2 className="text-3xl font-semibold">{name}</h2>
            {ABOUT[name] && <p className="muted text-sm mt-1">{ABOUT[name]}</p>}
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">{list.map((e) => <Card key={e.slug} e={e} />)}</div>
        </section>
      ))}
    </div>
  );
}

export function EpisodePage() {
  const { slug } = useParams();
  const e = EPISODES.find((x) => x.slug === slug);
  const video = useRef<HTMLVideoElement>(null);
  const [phone, setPhone] = useState(false);
  useMeta(e?.title || "Episode not found", e?.description.split("\n")[0] || "A film from the dome project.", `/episodes/${slug}`);
  if (!e) {
    return (
      <div className="mx-auto max-w-xl px-4 py-10">
        <p>There is no episode at this address. <Link className="underline" to="/episodes">Every episode</Link>.</p>
      </div>
    );
  }
  const same = EPISODES.filter((x) => x.series === e.series);
  const at = same.findIndex((x) => x.slug === e.slug);
  const prev = same[at - 1], next = same[at + 1];
  const part = phone && e.vertical ? e.vertical : e.video;
  const seek = (t: number) => {
    if (!video.current) return;
    video.current.currentTime = t;
    void video.current.play();
    video.current.scrollIntoView({ behavior: "smooth", block: "center" });
  };
  return (
    <div className="mx-auto max-w-5xl px-4 py-8 grid gap-6">
      <p className="text-sm"><Link className="underline" to="/episodes">Episodes</Link> / {e.series}{e.episode ? ` / ${e.episode}` : ""}</p>
      <div className={phone ? "mx-auto w-full max-w-sm" : ""}>
        <video key={part.key} ref={video} controls preload="metadata" playsInline poster={src(e.thumb)}
          className={`w-full bg-black rounded-lg ${phone ? "aspect-[9/16]" : "aspect-video"}`}>
          <source src={src(part)} type="video/mp4" />
          {e.captions && <track kind="captions" src={src(e.captions)} srcLang="en" label="English" />}
          Your browser cannot play this video.
        </video>
      </div>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-3xl">
          <h1 className="text-3xl sm:text-4xl font-bold">{e.title}</h1>
          <p className="muted text-sm mt-1">{clock(e.duration)} -- {new Date(e.made).toLocaleDateString(undefined, { month: "long", day: "numeric", year: "numeric" })}</p>
        </div>
        {e.vertical && (
          <button className="btn-ghost" onClick={() => setPhone(!phone)}>{phone ? "Watch the wide cut" : "Watch the phone cut"}</button>
        )}
      </div>
      {e.description && <div className="max-w-3xl whitespace-pre-line">{e.description}</div>}
      {e.chapters.length > 0 && !phone && (
        <section className="panel p-4 max-w-3xl">
          <h2 className="font-semibold mb-2">Chapters</h2>
          <ol className="grid sm:grid-cols-2 gap-x-6 gap-y-1 text-sm">
            {e.chapters.map((c) => (
              <li key={c.t}><button className="underline-offset-2 hover:underline text-left" onClick={() => seek(c.t)}>
                <span className="accent font-mono mr-2">{clock(c.t)}</span>{c.title}
              </button></li>
            ))}
          </ol>
        </section>
      )}
      <nav className="flex flex-wrap justify-between gap-3 text-sm">
        {prev ? <Link className="btn-ghost" to={`/episodes/${prev.slug}`}>Previous: {prev.title}</Link> : <span />}
        {next && <Link className="btn" to={`/episodes/${next.slug}`}>Next: {next.title}</Link>}
      </nav>
    </div>
  );
}
