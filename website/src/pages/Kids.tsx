// My Own Home, My Own Dome: the children's book, free. The page opens on the bedtime storytime
// (src/storytime): the book read aloud, full screen, its scenes staged in the 3-D world. Behind
// "For grown-ups" is the whole book to read, and the printed edition, which is pending: the
// catalogue says so, and the list is how a reader hears the day it can be ordered.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Waitlist } from "../components/Shelf";
import { Panel } from "../components/ui";
import { useCatalogue } from "../lib/catalogue";
import { facts } from "../lib/facts";
import { useMeta } from "../lib/meta";
import Storytime, { type Manifest } from "../storytime/Storytime";

const SLUG = "my-own-home-my-own-dome";
const STORY = "/storytime/my-own-home/manifest.json";

export default function Kids() {
  const kb = facts.kidsBook;
  useMeta(`${kb.title} -- bedtime storytime`, `${kb.title}: the wedge-dome build told in rhyme, read aloud as a bedtime story. Free.`, "/kids");
  const { get } = useCatalogue();
  const p = get(SLUG);
  const [story, setStory] = useState(true);
  const [manifest, setManifest] = useState<Manifest | null>(null);
  useEffect(() => { fetch(STORY).then((r) => (r.ok ? r.json() : null)).then(setManifest).catch(() => {}); }, []);
  useEffect(() => {
    if (!story) return;
    const prev = document.body.style.overflow; document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = prev; };
  }, [story]);
  const verse = manifest?.pages.filter((q) => !q.kind) ?? [];

  return (
    <>
      {story && <Storytime src={STORY} onGrownups={() => setStory(false)} />}
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
              itself, turns its own pages and keeps the screen awake{manifest ? `, about ${Math.round(manifest.runtime / 60)} minutes` : ""}.
            </p>
            <button className="btn" onClick={() => { setStory(true); window.scrollTo(0, 0); }}>Play it</button>
          </Panel>
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
