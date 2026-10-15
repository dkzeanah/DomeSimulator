import { Link } from "react-router-dom";
import { useMeta } from "../lib/meta";
import { LivePanel, useStats } from "../components/Live";
import SampleForm from "../components/SampleForm";
import { JoinQuest, Panel } from "../components/ui";
import { usd } from "../lib/api";
import { cabin, facts, sample } from "../lib/facts";

const FILLS = [
  ["dome-filled-dialled-pairs", "Pairs, dialled: nested at the corners, open through the middle"],
  ["dome-filled-rings-flipflop", "Rings, flip-flop: the frame repeated inward"],
  ["dome-filled-louvers", "Louvers: covered from above, open to the air"],
  ["dome-filled-chevron-flipflop", "Chevron, flip-flop: two sides meeting on the centre line"],
] as const;

export default function Home() {
  useMeta("Zeanah Lab", `Build a ${facts.dome.acrossFt}-foot geodesic dome cabin from split logs in ${cabin.numbers.frameHours} hours of frame work. The 40 Hour Cabin, a free sample, every cost computed, and the pad network.`, "/");
  const stats = useStats();
  const d = facts.dome;
  return (
    <>
      <section className="relative">
        <img src="/img/dome-filled-dialled-pairs.jpg" alt="The stem-cell dome with every triangle filled with wedge pairs, at sunset" className="w-full h-[58vh] min-h-[360px] object-cover" />
        {/* a dark scrim in both themes: the words sit on the picture, so they need their own ground */}
        <div className="absolute inset-0" style={{ background: "linear-gradient(180deg, rgba(8,10,14,0.12) 0%, rgba(8,10,14,0.62) 45%, rgba(8,10,14,0.92) 100%)" }} />
        <div className="absolute inset-x-0 bottom-0 mx-auto max-w-6xl px-4 pb-8 text-[#f4efe6] [&_.accent]:text-[#e8b45a]">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] accent">A home you can read like an account</p>
          <h1 className="text-4xl sm:text-6xl font-bold mt-2 max-w-3xl leading-[1.05]">Split from a log. Every number shown.</h1>
          <p className="mt-3 max-w-2xl text-lg">
            A {d.acrossFt}-foot dome of {d.members} wedge members, built in {cabin.numbers.frameHours} hours of frame work,
            for {usd(facts.price.stemCell)} -- and a place where what it costs, what it earns and who built it is written down for anyone to inspect.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link className="btn" to="/start">Look inside: the first {sample.pages} pages free</Link>
            <Link className="btn-ghost !border-white/40" to="/build">See the build, live</Link>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-6xl px-4 mt-10 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <Panel kicker="Counted, not claimed" title="The build, live">
          <LivePanel stats={stats} />
        </Panel>
        <div className="grid gap-6 content-start">
          <JoinQuest />
          <Panel kicker="Free" title="The opening of the book">
            <p className="muted text-sm mb-4">
              {sample.front.join(", ")} and {sample.chapters.length} chapters of {sample.ofChapters}:
              {" "}{sample.chapters.map((c) => c.title).join("; ")}.
            </p>
            <SampleForm />
          </Panel>
        </div>
      </div>

      <section className="mx-auto max-w-6xl px-4 mt-14">
        <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">The same frame, finished many ways</p>
        <h2 className="text-3xl sm:text-4xl font-semibold mt-1">Every triangle closed, every piece cut flush</h2>
        <p className="muted mt-2 max-w-3xl">
          These are not sketches. Each dome below is the Triangle Infill tool's own solids -- every wedge trimmed to its triangle's walls
          with the cut the cut list gives -- placed on all forty panels.
        </p>
        <div className="grid sm:grid-cols-2 gap-4 mt-6">
          {FILLS.map(([img, cap]) => (
            <figure key={img} className="panel overflow-hidden">
              <img src={`/img/${img}.jpg`} alt={cap} loading="lazy" className="w-full aspect-video object-cover" />
              <figcaption className="p-3 text-sm">{cap}</figcaption>
            </figure>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 mt-14 grid md:grid-cols-3 gap-4">
        {[
          ["Build", `${cabin.numbers.frameHours} hours of frame work`, "From standing tree to raised shell, one chainsaw rip at a time."],
          ["Count", `${cabin.figures} figures, all computed`, "Every figure in the book is drawn and priced by code you can read."],
          ["Convert", `${usd(facts.price.stemCell)} for the stem cell`, `${usd(facts.price.perSqft)} a square foot of floor, from the cost model.`],
        ].map(([side, big, small]) => (
          <div key={side} className="panel p-5">
            <div className="tri w-8 h-7 bg-[var(--accent)] mb-3" aria-hidden />
            <p className="text-xs uppercase tracking-[0.2em] muted">{side}</p>
            <p className="display text-2xl font-semibold mt-1">{big}</p>
            <p className="muted text-sm mt-1">{small}</p>
          </div>
        ))}
      </section>

      <section className="mx-auto max-w-6xl px-4 mt-14 grid md:grid-cols-2 gap-6 items-center">
        <img src="/img/dome-frame-open-triangles.jpg" alt="The bare frame: forty open triangles on the deck" className="panel w-full" loading="lazy" />
        <div>
          <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">A sanctuary with your name in it</p>
          <h2 className="text-3xl font-semibold mt-1">{facts.plaques.slots} panels. {facts.plaques.slots} founders.</h2>
          <p className="muted mt-2">
            The first dome has {facts.plaques.slots} triangular panels. Each founder's name goes on one -- a plaque that is also a piece of the building,
            mounted where it carries load, and listed here for anyone to verify.
          </p>
          <Link to="/back" className="btn mt-4">See the plaque wall</Link>
        </div>
      </section>
    </>
  );
}
