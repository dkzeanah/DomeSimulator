// /mission: why the lab exists, what it offers whom, and the method it works by -- including
// the dome as a learning model for computational thinking and the rules for using AI.
import { Link } from "react-router-dom";
import { Band, Figures, Halves, Head, PageHero, Pillar } from "../components/brand";
import { usd } from "../lib/api";
import { cabin, facts } from "../lib/facts";
import { AUDIENCES, BOOK_FIGURES, FILM_COUNT, LAYERS, METHOD, MISSION } from "../lib/lab";
import { useMeta } from "../lib/meta";

const VALUES = [
  ["Computed, never claimed", "Every strut, dollar, labour-hour and tree is produced by code anyone can read and run. Where the case is uncertain, the page says so."],
  ["Show the unflattering number", "A screen exists in this project for every figure that does not help the argument. Hiding it would make the rest worthless."],
  ["Shared load", "The triangle's argument: no member carries the roof alone. Strength comes from how things are joined, not from what they cost."],
  ["Repeatable, not miraculous", "Two jigs mean a shop, a shop means a line, and the second house goes up faster than the first."],
] as const;

export default function Mission() {
  useMeta("Mission", `Why Zeanah Lab exists: a ${facts.dome.acrossFt}-foot dome framed from split logs, worked out in open code, and the dome as a learning model for computational thinking and the honest use of AI.`, "/mission");
  const d = facts.dome;
  return (
    <>
      <PageHero eyebrow="Mission" image="/img/dome-frame-open-triangles.jpg"
        title={<>A home you can <span className="accent italic">account for.</span></>}
        lede={MISSION.long}>
        <Link className="btn" to="/book">Read the method</Link>
        <Link className="btn-ghost" to="/work">See the work</Link>
      </PageHero>

      <Band ground="yang" texture="rings">
        <div className="grid gap-12 lg:grid-cols-2">
          <div>
            <p className="eyebrow">The mission</p>
            <p className="display text-3xl sm:text-4xl leading-tight mt-4">{MISSION.line}</p>
          </div>
          <div>
            <p className="eyebrow">The vision</p>
            <p className="text-lg leading-relaxed mt-4">{MISSION.vision}</p>
            <p className="muted leading-relaxed mt-4">
              A dome is {d.bays} triangles and two lengths of wood. Cut them once, cut them true, and the same two numbers raise a shelter
              on a mountainside or a field outside town. The geometry does not check anyone's credit -- so the lab writes the whole
              argument down, in code, and lets anyone check it.
            </p>
          </div>
        </div>
        <div className="mt-14">
          <Figures items={[
            [d.floorSqft, "sq ft of floor"],
            [usd(facts.price.perSqft), "per sq ft, computed"],
            [BOOK_FIGURES.chapters, "chapters, open method"],
            [FILM_COUNT, "films, free to watch"],
          ]} />
        </div>
      </Band>

      <Band ground="yin" texture="grid">
        <Head eyebrow="The value proposition" title="One source of truth, four ways to use it."
          lede="The lab works out one building completely. What that is worth depends on who you are." />
        <div className="grid sm:grid-cols-2 gap-4 mt-12">
          {AUDIENCES.map((a) => <Pillar key={a.key} mark={a.mark} title={a.title} to={a.to} cta={a.cta}>{a.body}</Pillar>)}
        </div>
      </Band>

      <Band ground="yang" texture="rings" id="framework">
        <Head eyebrow="The learning model" title="The dome as a course in computational thinking."
          lede={`A house is the most complicated thing most people will ever own and the least understood. A ${d.acrossFt}-foot dome is a complete one -- geometry, structure, envelope, systems, money and media -- small enough to hold in your head. Each layer teaches one way of thinking, and one rule for working alongside AI.`} />
        <div className="mt-12 overflow-x-auto">
          <table className="w-full text-left text-[0.95rem] border-collapse min-w-[720px]">
            <thead>
              <tr className="mono text-[11px] uppercase tracking-[0.14em] muted">
                <th className="py-3 pr-4 font-medium">Layer</th><th className="py-3 pr-4 font-medium">Thinking skill</th>
                <th className="py-3 pr-4 font-medium">What the dome teaches</th><th className="py-3 font-medium">The AI rule</th>
              </tr>
            </thead>
            <tbody>
              {LAYERS.map((l) => (
                <tr key={l.layer} className="border-t align-top" style={{ borderColor: "var(--line)" }}>
                  <td className="py-4 pr-4 display text-lg font-semibold whitespace-nowrap">{l.layer}</td>
                  <td className="py-4 pr-4 accent font-semibold whitespace-nowrap">{l.skill}</td>
                  <td className="py-4 pr-4 muted leading-relaxed">{l.what}</td>
                  <td className="py-4 leading-relaxed">{l.ai}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Band>

      <Band ground="yin" texture="grid">
        <Head eyebrow="The AI usage framework" title="How the work is done: five rules."
          lede={`The whole project -- ${BOOK_FIGURES.chapters} chapters, ${FILM_COUNT} films, the solvers and this site -- is built with AI as a working collaborator. These are the rules that keep that honest. They are written into the repository, and every contributor, human or model, works under them.`} />
        <ol className="mt-12 grid gap-4 md:grid-cols-5">
          {METHOD.map(([name, body], i) => (
            <li key={name} className="panel p-5">
              <p className="mono text-xs accent">{String(i + 1).padStart(2, "0")}</p>
              <h3 className="text-xl font-semibold mt-2">{name}</h3>
              <p className="muted text-sm mt-2 leading-relaxed">{body}</p>
            </li>
          ))}
        </ol>
      </Band>

      <Band ground="plain">
        <Head eyebrow="What we hold to" title="Values" />
        <div className="grid sm:grid-cols-2 gap-x-12 gap-y-8 mt-10">
          {VALUES.map(([name, body]) => (
            <div key={name} className="border-t pt-5" style={{ borderColor: "var(--line)" }}>
              <h3 className="text-2xl font-semibold">{name}</h3>
              <p className="muted mt-2 leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
        <div className="mt-16">
          <Halves
            left={<>
              <p className="eyebrow">Start with the code</p>
              <h3 className="text-2xl mt-3">Try the tools, or have your dome designed</h3>
              <Link className="btn mt-6" to="/studio">The studio</Link>
            </>}
            right={<>
              <p className="eyebrow">Start with the timber</p>
              <h3 className="text-2xl mt-3">Read the opening of {cabin.title}, free</h3>
              <Link className="btn mt-6" to="/start">Read free</Link>
            </>}
          />
        </div>
      </Band>
    </>
  );
}
