import { Link } from "react-router-dom";
import { useMeta } from "../lib/meta";
import { LivePanel, useStats } from "../components/Live";
import SampleForm from "../components/SampleForm";
import { JoinQuest } from "../components/ui";
import { Band, Figures, Halves, Head, Pillar } from "../components/brand";
import { money, usd } from "../lib/api";
import { cabin, facts, sample } from "../lib/facts";
import { useCatalogue } from "../lib/catalogue";
import { AUDIENCES, BOOK_FIGURES, FILM_COUNT, LAYERS, MISSION } from "../lib/lab";
import { FOCI, useFocus, type Focus } from "../lib/site";

const FILLS = [
  ["dome-filled-dialled-pairs", "Pairs, dialled: nested at the corners, open through the middle"],
  ["dome-filled-rings-flipflop", "Rings, flip-flop: the frame repeated inward"],
  ["dome-filled-louvers", "Louvers: covered from above, open to the air"],
  ["dome-filled-chevron-flipflop", "Chevron, flip-flop: two sides meeting on the centre line"],
] as const;

/** What the owner has chosen to feature (admin studio, /api/site), shown as one card in the hero. */
const FEATURE: Record<Focus, { eyebrow: string; title: string; body: string; to: string; cta: string }> = {
  book: { eyebrow: "Featured -- the book", title: `${cabin.title}`, body: `${BOOK_FIGURES.chapters} chapters, ${BOOK_FIGURES.figures} figures, every one computed.`, to: "/book", cta: "See the book" },
  kids: { eyebrow: "Featured -- a picture book", title: facts.kidsBook.title, body: `${facts.kidsBook.stanzaCount} rhyming spreads: the whole build, told for reading aloud.`, to: "/kids", cta: "Watch the bedtime story" },
  domes: { eyebrow: "Featured -- dome classes", title: "One number names your dome", body: "Measure your longest strut; its size, weight, panels and frame all follow.", to: "/domes", cta: "Find my class" },
  network: { eyebrow: "Featured -- the pad network", title: "Land for domes. Domes for land.", body: "Hosts, owners, builders and recyclers on one map, each pad with its own numbers.", to: "/network", cta: "See the network" },
};

export default function Home() {
  useMeta("Zeanah Lab", `Timber and code: a ${facts.dome.acrossFt}-foot geodesic dome framed from split logs, the software that works out every piece of it, and The 40 Hour Cabin. Every cost computed.`, "/");
  const stats = useStats();
  const focus = useFocus() || "book";
  const feature = FEATURE[focus];
  const { get } = useCatalogue();
  const price = get("the-40-hour-cabin")?.prices.find((x) => x.key === "standard");
  const d = facts.dome;
  return (
    <>
      {/* ------------------------------------------------------------ hero: the code over the woods */}
      <section className="yin relative overflow-hidden">
        <img src="/img/dome-filled-dialled-pairs.jpg" alt="" aria-hidden className="absolute inset-0 w-full h-full object-cover" />
        <div aria-hidden className="absolute inset-0" style={{ background: "linear-gradient(100deg, rgba(14,18,16,0.96) 0%, rgba(14,18,16,0.86) 42%, rgba(14,18,16,0.35) 75%, rgba(14,18,16,0.55) 100%)" }} />
        <div aria-hidden className="absolute inset-0 grid-lines opacity-70" />
        <div className="relative mx-auto max-w-6xl px-4 pt-20 pb-14 sm:pt-28 sm:pb-20 grid gap-10 lg:grid-cols-[1.35fr_1fr] items-end">
          <div>
            <p className="eyebrow">Zeanah Lab &middot; timber and code</p>
            <h1 className="text-[2.6rem] sm:text-7xl leading-[1.02] mt-5">
              Split a log.<br />Raise a home.<br /><span className="accent italic">Know every number in it.</span>
            </h1>
            <p className="mt-6 text-lg sm:text-xl max-w-xl muted leading-relaxed">{MISSION.line}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link className="btn" to="/start">Read {sample.pages} pages free</Link>
              <Link className="btn-ghost" to="/mission">Our mission</Link>
            </div>
          </div>
          <Link to={feature.to} className="panel lift p-5 block max-w-sm lg:justify-self-end" style={{ background: "color-mix(in srgb, var(--panel) 82%, transparent)", backdropFilter: "blur(6px)" }}>
            <p className="eyebrow">{feature.eyebrow}</p>
            <p className="display text-2xl font-semibold mt-2">{feature.title}</p>
            <p className="muted text-sm mt-1.5">{feature.body}</p>
            <span className="link-arrow text-sm mt-3">{feature.cta}</span>
          </Link>
        </div>
        <div className="relative mx-auto max-w-6xl px-4 pb-10">
          <Figures items={[
            [`${d.acrossFt} ft`, "across the floor"],
            [d.members, "split-log members"],
            [`${cabin.numbers.frameHours} h`, "of frame work"],
            [usd(facts.price.stemCell), "the stem-cell dome"],
          ]} />
        </div>
      </section>

      {/* ------------------------------------------------------------ the value proposition */}
      <Band ground="yang" texture="rings">
        <Head eyebrow="What the lab offers" title="One building, worked out completely -- and shared."
          lede={MISSION.long} />
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-12">
          {AUDIENCES.map((a) => <Pillar key={a.key} mark={a.mark} title={a.title} to={a.to} cta={a.cta}>{a.body}</Pillar>)}
        </div>
      </Band>

      {/* ------------------------------------------------------------ the book, with its cover */}
      <Band ground="yin" texture="grid">
        <div className="grid gap-12 md:grid-cols-[minmax(0,320px)_1fr] items-center">
          <Link to="/book" className="block mx-auto md:mx-0">
            <img src="/img/the-40-hour-cabin-cover.jpg" alt={`${cabin.title} cover`} className="w-full max-w-[320px] rounded-md"
              style={{ boxShadow: "0 30px 60px -20px rgba(0,0,0,0.75), 0 0 0 1px var(--line)" }} />
          </Link>
          <div>
            <p className="eyebrow">The book &middot; {cabin.subtitle}</p>
            <h2 className="text-4xl sm:text-5xl leading-[1.05] mt-3">{cabin.title}</h2>
            <p className="muted text-lg mt-4 leading-relaxed max-w-2xl">
              The {d.acrossFt}-foot dome from standing tree to raised shell, then every way to finish it. Measure one strut and the book works out
              the rest -- what it weighs, what it is made of, what panels it takes and what it costs.
            </p>
            <div className="mt-8 max-w-xl">
              <Figures items={[
                [BOOK_FIGURES.chapters, "chapters"],
                [BOOK_FIGURES.parts, "parts"],
                [BOOK_FIGURES.figures, "figures"],
                [BOOK_FIGURES.pages, "pages"],
              ]} />
            </div>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link className="btn" to="/book">Get the book{price ? ` -- ${money(price.amountCents, price.currency)}` : ""}</Link>
              <Link className="btn-ghost" to="/start">Read the opening free</Link>
            </div>
          </div>
        </div>
      </Band>

      {/* ------------------------------------------------------------ the dome as a learning model */}
      <Band ground="yang" texture="rings">
        <Head eyebrow="The learning model" title="The dome is a whole smart home, small enough to understand."
          lede="Every layer of the building teaches one way of thinking -- and one rule for working with AI. Together they make a complete course in computational thinking that ends in a house." />
        <ol className="mt-12 grid md:grid-cols-2 lg:grid-cols-3 gap-px rounded-xl overflow-hidden border" style={{ borderColor: "var(--line)", background: "var(--line)" }}>
          {LAYERS.map((l, i) => (
            <li key={l.layer} className="p-6" style={{ background: "var(--panel)" }}>
              <p className="mono text-xs muted">{String(i + 1).padStart(2, "0")} &middot; {l.layer}</p>
              <h3 className="text-xl font-semibold mt-2">{l.skill}</h3>
              <p className="muted text-[0.95rem] mt-2 leading-relaxed">{l.what}</p>
            </li>
          ))}
        </ol>
        <Link to="/mission#framework" className="link-arrow mt-8">The full framework, and the AI rules</Link>
      </Band>

      {/* ------------------------------------------------------------ timber and code, the two halves */}
      <section className="mx-auto max-w-6xl px-4 py-16 sm:py-20">
        <Halves
          left={<>
            <p className="eyebrow">The code</p>
            <h3 className="text-3xl mt-3">Software and design</h3>
            <p className="muted mt-3 leading-relaxed">Dome Sketch, the Wedge Builder and the calculator run on the project's own solvers. Design sessions and custom build packs use the same tools on your dome.</p>
            <div className="mt-6 flex flex-wrap gap-3"><Link className="btn" to="/studio">The studio</Link><Link className="btn-ghost" to="/software">Try the tools</Link></div>
          </>}
          right={<>
            <p className="eyebrow">The timber</p>
            <h3 className="text-3xl mt-3">The first dome, in the open</h3>
            <p className="muted mt-3 leading-relaxed">{facts.plaques.slots} panels, {facts.plaques.slots} founder plaques: each founder's name goes on a piece of the building that carries load, listed here for anyone to verify. Watch it go up in {FILM_COUNT} films.</p>
            <div className="mt-6 flex flex-wrap gap-3"><Link className="btn" to="/back">See the plaque wall</Link><Link className="btn-ghost" to="/episodes">Watch the films</Link></div>
          </>}
        />
      </section>

      {/* ------------------------------------------------------------ the gallery */}
      <Band ground="yin" texture="grid">
        <Head eyebrow="The same frame, finished many ways" title="Every triangle closed, every piece cut flush."
          lede="Not sketches: each dome below is the Triangle Infill tool's own solids -- every wedge trimmed to its triangle with the cut the cut list gives -- placed on all forty panels." />
        <div className="grid sm:grid-cols-2 gap-4 mt-10">
          {FILLS.map(([img, cap]) => (
            <figure key={img} className="panel overflow-hidden lift">
              <img src={`/img/${img}.jpg`} alt={cap} loading="lazy" className="w-full aspect-video object-cover" />
              <figcaption className="px-4 py-3 text-sm muted">{cap}</figcaption>
            </figure>
          ))}
        </div>
      </Band>

      {/* ------------------------------------------------------------ live numbers and joining */}
      <Band ground="plain">
        <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          <div className="panel p-6 self-start">
            <p className="eyebrow">Counted, not claimed</p>
            <h2 className="text-3xl font-semibold mt-2 mb-5">The build, live</h2>
            <LivePanel stats={stats} />
          </div>
          <div className="grid gap-6 content-start">
            <JoinQuest />
            <div className="panel p-6">
              <p className="eyebrow">Free</p>
              <h2 className="text-2xl font-semibold mt-2">The opening of the book</h2>
              <p className="muted text-sm mt-2 mb-4">
                {sample.front.join(", ")} and {sample.chapters.length} chapters of {sample.ofChapters}:
                {" "}{sample.chapters.map((c) => c.title).join("; ")}.
              </p>
              <SampleForm />
            </div>
          </div>
        </div>
        <nav aria-label="More of the lab" className="mt-10 grid grid-cols-2 sm:grid-cols-4 gap-3">
          {FOCI.map((f) => (
            <Link key={f.key} to={f.to} className={`panel-2 lift p-4 text-sm ${f.key === focus ? "ring-1 ring-[var(--accent)]" : ""}`}>
              <span className="font-semibold">{f.label}</span>
              <span className="block mono text-[11px] muted mt-1">{f.to}</span>
            </Link>
          ))}
        </nav>
      </Band>
    </>
  );
}
