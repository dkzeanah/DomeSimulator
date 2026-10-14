import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import Shelf from "../components/Shelf";
import { Panel, Stat } from "../components/ui";
import { usd } from "../lib/api";
import { book, cabin, facts } from "../lib/facts";
import { useSession } from "../lib/session";

export default function Book() {
  const { mark } = useSession();
  const [params] = useSearchParams();
  useEffect(() => { mark("read"); }, [mark]);
  const x = cabin.numbers;
  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      {params.get("cancelled") && <p className="panel-2 p-3 mb-6 text-sm">Checkout was cancelled. Nothing was charged.</p>}
      <div className="grid gap-8 md:grid-cols-[280px_1fr]">
        <img src="/img/the-40-hour-cabin-cover.jpg" alt={`${cabin.title} cover`} className="rounded-xl w-full max-w-[280px]" />
        <div>
          <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">{cabin.subtitle}</p>
          <h1 className="text-4xl sm:text-5xl font-bold mt-1">{cabin.title}</h1>
          <p className="mt-3 max-w-2xl">{book.blurb}</p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6">
            <Stat value={cabin.pages ?? "-"} label="pages" />
            <Stat value={cabin.chapters} label="chapters" />
            <Stat value={cabin.figures} label="figures, all computed" />
            <Stat value={x.frameHours} label="hours of frame work" />
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_380px] mt-10">
        <Panel kicker="What it proves" title="The numbers inside">
          <dl className="grid sm:grid-cols-2 gap-x-6 gap-y-2 text-sm">
            {[
              ["Members in the frame", x.members], ["Panels", x.panels], ["Floor", `${x.floorSqft} sq ft`], ["Across", `${x.diameterFt} ft`],
              ["Frame, in timber", `$${x.frameUsd}`], ["The whole shell", `$${x.shellUsd}`], ["Per square foot", `$${x.perSqftUsd}`],
              ["Labour hours", x.labourHours], ["Finishes rendered and priced", x.styles], ["Cheapest to dearest finish", `$${x.styleLowUsd} to $${x.styleHighUsd}`],
            ].map(([k, v]) => (
              <div key={String(k)} className="flex justify-between gap-3 border-b py-1.5" style={{ borderColor: "var(--line)" }}>
                <dt className="muted">{k}</dt><dd className="num font-semibold">{v}</dd>
              </div>
            ))}
          </dl>
          <h3 className="text-2xl font-semibold mt-8 mb-2">Contents</h3>
          <ol className="grid sm:grid-cols-2 gap-2 text-sm">
            {cabin.parts.map((p) => (
              <li key={p.number} className="panel-2 p-3">
                <span className="muted mr-2">Part {p.number}</span>{p.title}
                <span className="block text-xs muted mt-1">{p.chapters.length} chapters</span>
              </li>
            ))}
          </ol>
        </Panel>

        <div className="grid gap-6 content-start">
          <Shelf only={["the-40-hour-cabin", "triangular-book", "2-trees", "design-session"]} />
          <p className="text-xs muted">The stem cell itself is priced at {usd(facts.price.stemCell)} by <code>kickstarter.cost_stack()</code>.</p>
        </div>
      </div>
    </div>
  );
}
