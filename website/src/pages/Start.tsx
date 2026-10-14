// The funnel: stranger -> reader -> owner -> backer. Each stage shows the real thing (the
// sample's actual pages, the catalogue's actual prices, the plaque wall's actual count) and
// the bar at the top moves only when the visitor really takes the step.

import { useState } from "react";
import { useMeta } from "../lib/meta";
import { Link } from "react-router-dom";
import SampleForm from "../components/SampleForm";
import Shelf from "../components/Shelf";
import { Fraction, Panel } from "../components/ui";
import { usd } from "../lib/api";
import { cabin, facts, sample } from "../lib/facts";
import { useSession } from "../lib/session";
import pages from "../generated/sample-pages.json";

const STAGES = ["Look inside", "Read the opening", "Own the book", "Put your name on it"];

export default function Start() {
  useMeta("Free pages: The 40 Hour Cabin", `Look inside The 40 Hour Cabin: real pages from the ${cabin.pages}-page build manual, then the first ${sample.pages} pages free for your email.`, "/start");
  const { steps } = useSession();
  const [big, setBig] = useState<string | null>(null);
  const [readNow, setReadNow] = useState(false);
  const read = steps.sample || readNow;
  const stage = read ? 2 : 1;
  return (
    <div className="mx-auto max-w-6xl px-4 py-10 grid gap-8">
      <div className="grid gap-6 md:grid-cols-[1.2fr_1fr] items-center">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">Free, the first {sample.pages} pages</p>
          <h1 className="text-4xl sm:text-5xl font-bold mt-1 leading-tight">A cabin in {cabin.numbers.frameHours} hours of frame work. Every number shown.</h1>
          <p className="muted mt-3 text-lg">
            {cabin.title} is {cabin.pages} pages and {cabin.figures} figures, every one drawn and priced by code you can read.
            Here are its real pages -- then the opening is yours for an email.
          </p>
        </div>
        <img src="/img/dome-filled-dialled-pairs.jpg" alt="The dome with every triangle filled" className="panel w-full" />
      </div>

      <Panel>
        <Fraction have={stage} need={STAGES.length} label={`Stage ${stage} of ${STAGES.length}: ${STAGES[stage - 1]}`} />
        <ol className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-3 text-xs">
          {STAGES.map((s, i) => <li key={s} className={i < stage ? "accent font-semibold" : "muted"}>{i + 1}. {s}</li>)}
        </ol>
      </Panel>

      <section>
        <h2 className="text-3xl font-semibold">Look inside</h2>
        <p className="muted mt-1">Pages from the free sample, exactly as printed.</p>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-4">
          {pages.pages.map((p) => (
            <button key={p.src} className="panel overflow-hidden text-left" onClick={() => setBig(p.src)}>
              <img src={p.src} alt={`Sample page ${p.page}: ${p.caption}`} loading="lazy" className="w-full aspect-[1/1.29] object-cover object-top" />
              <span className="block p-3 text-sm">{p.caption} <span className="muted">- page {p.page}</span></span>
            </button>
          ))}
        </div>
      </section>

      {big && (
        <div role="dialog" aria-modal className="fixed inset-0 z-50 bg-black/80 grid place-items-center p-4" onClick={() => setBig(null)}>
          <img src={big} alt="" className="max-h-[92vh] max-w-full rounded-lg shadow-2xl" />
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-[1fr_1fr]">
        <Panel kicker="Stage 2" title="Read the opening, free">
          <p className="muted text-sm mb-4">
            {sample.front.join(", ")} and {sample.chapters.length} chapters: {sample.chapters.map((c) => c.title).join("; ")}.
          </p>
          <SampleForm onDone={() => setReadNow(true)} />
        </Panel>
        <Panel kicker="What the rest proves" title="The numbers in the full book">
          <ul className="text-sm grid gap-1.5">
            <li>{cabin.numbers.members} wedge members, {cabin.numbers.panels} panels, {cabin.numbers.floorSqft} sq ft of floor</li>
            <li>The whole shell for ${cabin.numbers.shellUsd} -- ${cabin.numbers.perSqftUsd} a square foot</li>
            <li>{cabin.numbers.styles} finishes rendered and priced, ${cabin.numbers.styleLowUsd} to ${cabin.numbers.styleHighUsd}</li>
            <li>{cabin.chapters} chapters in {cabin.parts.length} parts, with the code that computed all of it</li>
          </ul>
        </Panel>
      </div>

      <section className={read ? "" : "opacity-90"}>
        <h2 className="text-3xl font-semibold">{read ? "You can now: own the book" : "Stage 3: own the book"}</h2>
        <p className="muted mt-1">Three ways to have it. The triangular edition is made by hand, and it pays for the build.</p>
        <div className="grid gap-6 lg:grid-cols-3 mt-4">
          <Shelf only={["the-40-hour-cabin"]} />
          <Shelf only={["triangular-book"]} />
          <Shelf only={["2-trees"]} />
        </div>
      </section>

      <Panel kicker="Stage 4" title={`Put your name on it: ${facts.plaques.slots} panels, ${facts.plaques.slots} founders`}>
        <div className="grid md:grid-cols-[1fr_auto] gap-4 items-center">
          <p className="muted text-sm">
            The first dome has {facts.plaques.slots} triangular panels. Each founder's name is cut into one and mounted in the building. The campaign that
            stands it up for a year is {usd(facts.goal.total)}, line by line.
          </p>
          <Link className="btn" to="/back">See the plaque wall</Link>
        </div>
      </Panel>
    </div>
  );
}
