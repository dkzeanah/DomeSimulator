// The bedtime stories, free. /kids opens on My Own Home, My Own Dome (/kids/<story> on any other
// published story): read aloud full screen, or read by a grown-up with the narrator off, its scenes
// staged in the 3-D world (src/storytime). The story is the version the Story Studio (Admin ->
// Stories) last published; if the API cannot be reached, the copy baked into the site is read.
// Behind "For grown-ups" are the words to read, the other stories, and the printed edition of the
// book, which is pending: the list is how a reader hears the day it can be ordered.

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Waitlist } from "../components/Shelf";
import { Panel } from "../components/ui";
import { api } from "../lib/api";
import { useCatalogue } from "../lib/catalogue";
import { facts } from "../lib/facts";
import { useMeta } from "../lib/meta";
import Storytime, { type Manifest } from "../storytime/Storytime";

const SLUG = "my-own-home-my-own-dome";
const FIRST = "my-own-home";

export default function Kids() {
  const kb = facts.kidsBook;
  useMeta(`${kb.title} -- bedtime storytime`, `${kb.title}: the wedge-dome build told in rhyme, read aloud as a bedtime story. Free.`, "/kids");
  const { get } = useCatalogue();
  const p = get(SLUG);
  const slug = useParams().story || FIRST;
  const [story, setStory] = useState(true);
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [failed, setFailed] = useState(false);
  const [others, setOthers] = useState<{ slug: string; title: string }[]>([]);
  useEffect(() => {
    setManifest(null); setFailed(false);
    api<Manifest>(`/stories/${slug}`)
      .catch(() => fetch(`/storytime/${slug}/manifest.json`).then((r) => { if (!r.ok) throw new Error(); return r.json() as Promise<Manifest>; }))
      .then(setManifest).catch(() => setFailed(true));
    api<{ stories: { slug: string; title: string }[] }>("/stories").then((r) => setOthers(r.stories)).catch(() => undefined);
  }, [slug]);
  useEffect(() => {
    if (!story) return;
    const prev = document.body.style.overflow; document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = prev; };
  }, [story]);
  const verse = manifest?.pages.filter((q) => !q.kind || q.kind === "page") ?? [];

  return (
    <>
      {story && manifest && <Storytime key={slug} manifest={manifest} onGrownups={() => setStory(false)} />}
      {story && failed && <div className="fixed inset-0 z-[60] grid place-items-center bg-[#05070f] text-white text-xl px-6 text-center">That story is not here. <Link className="underline ml-2" to="/kids" onClick={() => setStory(false)}>Back</Link></div>}
      <div className="mx-auto max-w-6xl px-4 py-10 grid gap-8 lg:grid-cols-[1.3fr_1fr]">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">A rhyming picture book -- free</p>
          <h1 className="text-4xl sm:text-6xl font-bold mt-1 leading-[1.05]">{kb.title}</h1>
          <p className="mt-3 max-w-2xl text-lg">
            In a town full of boxes, one girl wants a home with no corners. So she finds a fallen pine, splits it into wedges,
            and builds a dome -- and finds out that one number tells her everything about it.
          </p>
          <button className="btn mt-5 !text-lg !px-6 !py-3" onClick={() => { setStory(true); window.scrollTo(0, 0); }}>Watch the bedtime story</button>
          <div className="mt-8 grid gap-5">
            {(verse.length ? verse.map((q) => q.text) : kb.preview).map((stanza, i) => (
              <blockquote key={i} className="panel p-5 display text-lg xl:text-2xl leading-snug whitespace-pre-line" style={{ borderLeft: "4px solid var(--accent)" }}>
                {stanza}
              </blockquote>
            ))}
            <p className="muted text-sm">{verse.length ? `All ${verse.length} spreads, free to read aloud.` : `The opening ${kb.preview.length} of ${kb.stanzaCount} spreads.`}</p>
          </div>
        </div>
        <div className="grid gap-6 content-start lg:sticky lg:top-20">
          <Panel kicker="Free to read and watch" title="The bedtime story">
            <p className="text-sm muted mb-3">
              The whole book, read aloud, with every page staged in the dome's own 3-D world. Made for tablets: it reads by
              itself, turns its own pages and keeps the screen awake. Or switch the narrator off and read it to them yourself{manifest ? `, about ${Math.round(manifest.runtime / 60)} minutes` : ""}.
            </p>
            <button className="btn" onClick={() => { setStory(true); window.scrollTo(0, 0); }}>Play it</button>
          </Panel>
          {others.length > 1 && (
            <Panel kicker="Bedtime Stories" title="More bedtime stories">
              <ul className="grid gap-2">
                {others.map((o) => (
                  <li key={o.slug}><Link className={`btn-ghost w-full justify-start ${o.slug === slug ? "accent font-semibold" : ""}`} to={o.slug === FIRST ? "/kids" : `/kids/${o.slug}`} onClick={() => { setStory(true); window.scrollTo(0, 0); }}>{o.title}</Link></li>
                ))}
              </ul>
            </Panel>
          )}
          <Panel kicker="Printed edition -- pending" title={p ? p.title : kb.title}>
            <p className="text-sm muted mb-3">
              {p?.shipsNote ?? "A printed picture book is on the way. It cannot be ordered yet; leave your email and you will hear the day it can."}
            </p>
            <Waitlist source={SLUG} label="Tell me when I can order it" />
          </Panel>
          <p className="text-sm muted">For the grown-ups: <Link className="underline" to="/book">The 40 Hour Cabin</Link> is the build itself, every number worked out.</p>
        </div>
      </div>
    </>
  );
}
