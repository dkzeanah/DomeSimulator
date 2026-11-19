// /studio: what the lab sells -- its software, and design work done with that software on a
// client's own dome. Products and prices are the catalogue's (the Shelf); services without a
// listed price are enquiries through the contact card.
import { Link } from "react-router-dom";
import { Band, Halves, Head, PageHero, Pillar } from "../components/brand";
import Shelf from "../components/Shelf";
import { facts } from "../lib/facts";
import { PUBLIC_TOOLS } from "../lib/lab";
import { useMeta } from "../lib/meta";
import grid from "../generated/sketch-grid.json";

const G = grid as unknown as { cuts: unknown[]; diameters: number[] };

const SOFTWARE = [
  { mark: "Design", title: "Dome Sketch", to: "/sketch", cta: "Open Dome Sketch",
    body: `Shape a framed-panel geodesic dome in the browser -- ${G.cuts.length} geodesic choices, ${G.diameters.length} sizes, doors, windows, skylight and skin -- then make its build pack: plans, cut list, materials, tools, price and every assembly step.` },
  { mark: "Cut", title: "Wedge Builder", to: "/software#wedge-builder", cta: "See the Wedge Builder",
    body: "A cut list for your own wedge dome and your own logs: what each split keeps, where each member comes from, solved on your machine." },
  { mark: "Calculate", title: "Wedge calculator", to: "/calculator", cta: "Use it free",
    body: "What each split keeps of a log at your saw's kerf -- the arithmetic the whole method starts from, free in the browser." },
] as const;

const SERVICES = [
  { mark: "Session", title: "One-on-one design session", body: "A one-on-one session with the author, designing your dome live in the project's own tools: size, cut, openings, skin and site." },
  { mark: "Study", title: "Custom dome study", body: "Your dome worked out completely: geometry, member schedule, panel types, materials and a line-by-line cost, as a document you keep." },
  { mark: "Pack", title: "Build and fabrication packs", body: "Plan sets, cut cards and jig drawings for a builder or a shop, generated from the solver so every dimension agrees." },
  { mark: "Visual", title: "Renders and films", body: "Showcase stills and narrated walkthroughs of a design, rendered from its real geometry -- for a listing, a pitch or a permit meeting." },
  { mark: "Systems", title: "Computational design and AI workflows", body: "For teams and educators: the lab's method -- declared inputs, computed outputs, AI-assisted and verified -- applied to your own project or course." },
] as const;

const PROCESS = [
  ["Talk", "What you want to build, where, and with what."],
  ["Model", "Your dome in the solver: every number derived, every assumption declared."],
  ["Review", "Renders, schedules and costs to check together, including the numbers that argue against it."],
  ["Deliver", "The pack, the files and the source of every figure."],
] as const;

export default function Studio() {
  useMeta("Studio", "Software and design from Zeanah Lab: Dome Sketch, the Wedge Builder, design sessions, custom dome studies, build packs and renders, all from the project's own solvers.", "/studio");
  return (
    <>
      <PageHero eyebrow="Studio -- software and design" image="/img/dome-filled-bowtie-pairs-close.jpg"
        title={<>The tools that worked out the dome, <span className="accent italic">working on yours.</span></>}
        lede={`Every product here runs on the same solvers that wrote the book and rendered the films. ${PUBLIC_TOOLS} tools are open to try; design work applies them to your site, your logs and your budget.`}>
        <Link className="btn" to="/software">Try the software</Link>
        <Link className="btn-ghost" to="/card">Start a project</Link>
      </PageHero>

      <Band ground="yang" texture="rings">
        <Head eyebrow="Software" title="Design, cut and calculate." lede="Each tool has a free trial. The full versions are one-time purchases, listed below with their current prices." />
        <div className="grid md:grid-cols-3 gap-4 mt-12">
          {SOFTWARE.map((s) => <Pillar key={s.title} mark={s.mark} title={s.title} to={s.to} cta={s.cta}>{s.body}</Pillar>)}
        </div>
      </Band>

      <Band ground="yin" texture="grid">
        <Head eyebrow="Design services" title="Your dome, worked out completely."
          lede="Design work is done in the open method: every number traceable, every assumption on the page, every unflattering figure shown." />
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-12">
          {SERVICES.map((s) => <Pillar key={s.title} mark={s.mark} title={s.title}>{s.body}</Pillar>)}
          <div className="panel p-6 flex flex-col justify-between" style={{ borderColor: "var(--accent)" }}>
            <div>
              <p className="eyebrow">Enquire</p>
              <p className="display text-2xl font-semibold mt-3">Tell us what you want to build.</p>
              <p className="muted text-sm mt-2">Scope and price are agreed before any work starts.</p>
            </div>
            <Link className="btn mt-6 text-center" to="/card">Contact the studio</Link>
          </div>
        </div>
        <ol className="mt-14 grid sm:grid-cols-4 gap-px rounded-xl overflow-hidden border" style={{ borderColor: "var(--line)", background: "var(--line)" }}>
          {PROCESS.map(([step, body], i) => (
            <li key={step} className="p-5" style={{ background: "var(--panel)" }}>
              <p className="mono text-xs muted">Step {i + 1}</p>
              <p className="display text-xl font-semibold mt-1">{step}</p>
              <p className="muted text-sm mt-1">{body}</p>
            </li>
          ))}
        </ol>
      </Band>

      <Band ground="plain">
        <Head eyebrow="Buy" title="Current editions and tools" lede="Prices and availability come straight from the store, so they are always current." />
        <div className="mt-10 max-w-3xl">
          <Shelf only={["dome-sketch", "wedge-builder", "design-session", "the-40-hour-cabin"]} />
        </div>
        <div className="mt-16">
          <Halves
            left={<>
              <p className="eyebrow">Proof of work</p>
              <h3 className="text-2xl mt-3">See what the tools have already built</h3>
              <Link className="btn mt-6" to="/work">The work</Link>
            </>}
            right={<>
              <p className="eyebrow">{facts.site.name}</p>
              <h3 className="text-2xl mt-3">Questions first? Write to the studio.</h3>
              <Link className="btn mt-6" to="/card">Contact</Link>
            </>}
          />
        </div>
      </Band>
    </>
  );
}
