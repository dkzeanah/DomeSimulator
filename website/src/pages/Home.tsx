import { Link } from "react-router-dom";
import { useMeta } from "../lib/meta";
import { LivePanel, useStats } from "../components/Live";
import SampleForm from "../components/SampleForm";
import { JoinQuest, Panel } from "../components/ui";
import { usd } from "../lib/api";
import { cabin, facts, sample } from "../lib/facts";
import { useCatalogue } from "../lib/catalogue";
import { FOCI, useFocus, type Focus } from "../lib/site";
import { money } from "../lib/api";

const FILLS = [
  ["dome-filled-dialled-pairs", "Pairs, dialled: nested at the corners, open through the middle"],
  ["dome-filled-rings-flipflop", "Rings, flip-flop: the frame repeated inward"],
  ["dome-filled-louvers", "Louvers: covered from above, open to the air"],
  ["dome-filled-chevron-flipflop", "Chevron, flip-flop: two sides meeting on the centre line"],
] as const;

/** One line under each module's name, worked from the same numbers as its page. */
const TEASER: Record<Focus, string> = {
  book: `${cabin.pages ?? cabin.chapters} pages, ${cabin.figures} figures, all computed`,
  kids: `${facts.kidsBook.stanzaCount} rhyming spreads, for reading aloud`,
  domes: "Enter one strut, get the whole dome",
  network: "Pads, builders, recyclers and timber",
};

function Hero({ focus }: { focus: Focus }) {
  const { get } = useCatalogue();
  const d = facts.dome;
  const priceOf = (slug: string) => {
    const p = get(slug)?.prices.find((x) => x.key === "standard");
    return p ? ` -- ${money(p.amountCents, p.currency)}` : "";
  };
  if (focus === "kids") {
    return (
      <>
        <p className="text-xs font-semibold uppercase tracking-[0.22em] accent">New -- a picture book</p>
        <h1 className="text-4xl sm:text-6xl font-bold mt-2 max-w-3xl leading-[1.05]">{facts.kidsBook.title}</h1>
        <p className="mt-3 max-w-2xl text-lg">One girl, one fallen pine and one saw -- and a round home with no corners, built wedge by wedge. The whole build, told in rhyme for reading aloud.</p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link className="btn" to="/kids">Watch the bedtime story -- free</Link>
          <Link className="btn-ghost !border-white/40" to="/book">The grown-ups' book</Link>
        </div>
      </>
    );
  }
  if (focus === "domes") {
    return (
      <>
        <p className="text-xs font-semibold uppercase tracking-[0.22em] accent">Dome classes</p>
        <h1 className="text-4xl sm:text-6xl font-bold mt-2 max-w-3xl leading-[1.05]">One number names your whole dome.</h1>
        <p className="mt-3 max-w-2xl text-lg">
          Measure your longest strut. Its size, its weight, its panels and its frame all follow -- and everyone with the same number
          can swap panels with you.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link className="btn" to="/domes">Find my class</Link>
          <Link className="btn-ghost !border-white/40" to="/account/dome">Add my dome</Link>
        </div>
      </>
    );
  }
  if (focus === "network") {
    return (
      <>
        <p className="text-xs font-semibold uppercase tracking-[0.22em] accent">The pad network</p>
        <h1 className="text-4xl sm:text-6xl font-bold mt-2 max-w-3xl leading-[1.05]">Land for domes. Domes for land.</h1>
        <p className="mt-3 max-w-2xl text-lg">Pad hosts, dome owners, builders, recyclers and people with standing timber -- on one map, each pad with its own numbers.</p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link className="btn" to="/network">See the network</Link>
          <Link className="btn-ghost !border-white/40" to="/book">Read the book</Link>
        </div>
      </>
    );
  }
  return (
    <>
      <p className="text-xs font-semibold uppercase tracking-[0.22em] accent">{cabin.title}: {cabin.subtitle}</p>
      <h1 className="text-4xl sm:text-6xl font-bold mt-2 max-w-3xl leading-[1.05]">Split a log. Raise a home. Know every number in it.</h1>
      <p className="mt-3 max-w-2xl text-lg">
        A {d.acrossFt}-foot geodesic dome framed from {d.members} wedges split out of logs, in {cabin.numbers.frameHours} hours of frame work.
        Measure one strut and the book works out the rest -- what it weighs, how much of it is wood and how much is hardware,
        what size panels it takes, what it costs. A home you can account for: {usd(facts.price.stemCell)} for the stem cell.
      </p>
      <div className="mt-5 flex flex-wrap gap-3">
        <Link className="btn" to="/start">Read {sample.pages} pages free</Link>
        <Link className="btn-ghost !border-white/40" to="/book">Get the book{priceOf("the-40-hour-cabin")}</Link>
      </div>
    </>
  );
}

export default function Home() {
  useMeta("Zeanah Lab", `Build a ${facts.dome.acrossFt}-foot geodesic dome cabin from split logs in ${cabin.numbers.frameHours} hours of frame work. The 40 Hour Cabin, a free sample, every cost computed, and the pad network.`, "/");
  const stats = useStats();
  const focus = useFocus();
  return (
    <>
      <section className="relative">
        <img src="/img/dome-filled-dialled-pairs.jpg" alt="The stem-cell dome with every triangle filled with wedge pairs, at sunset" className="w-full h-[58vh] min-h-[420px] object-cover" />
        {/* a dark scrim in both themes: the words sit on the picture, so they need their own ground */}
        <div className="absolute inset-0" style={{ background: "linear-gradient(180deg, rgba(8,10,14,0.12) 0%, rgba(8,10,14,0.62) 45%, rgba(8,10,14,0.92) 100%)" }} />
        <div className="absolute inset-x-0 bottom-0 mx-auto max-w-6xl px-4 pb-8 text-[#f4efe6] [&_.accent]:text-[#e8b45a]">
          <Hero focus={focus || "book"} />
        </div>
      </section>

      <nav aria-label="What is here" className="mx-auto max-w-6xl px-4 mt-6 grid grid-cols-2 sm:grid-cols-4 gap-3">
        {FOCI.map((f) => (
          <Link key={f.key} to={f.to} className={`panel-2 p-3 text-sm ${f.key === (focus || "book") ? "ring-2 ring-[var(--accent)]" : ""}`}>
            <span className="font-semibold">{f.label}</span>
            <span className="block text-xs muted mt-0.5">{TEASER[f.key]}</span>
          </Link>
        ))}
      </nav>

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
