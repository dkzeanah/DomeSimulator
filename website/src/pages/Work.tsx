// /work: the résumé -- who does the work, the scope of the dome as a smart-home learning
// model, every project with its scope, stack and outputs, and the skills it took. Project
// figures come from lib/lab.ts, which reads facts; nothing here is typed.
import { Link } from "react-router-dom";
import { Band, Figures, Head, PageHero } from "../components/brand";
import { cabin, facts } from "../lib/facts";
import { BOOK_FIGURES, FILM_COUNT, LAYERS, PROJECTS, PUBLIC_TOOLS, SKILLS } from "../lib/lab";
import { useMeta } from "../lib/meta";

export default function Work() {
  const author = cabin.author;
  useMeta("Work", `${author}: builder, author and software developer. The dome as a smart-home learning model, and every project behind it -- the book, the solver, the films, Dome Sketch and this site.`, "/work");
  const youtube = facts.site.links.find((l) => l.icon === "youtube");
  const github = facts.site.links.find((l) => l.icon === "github");
  return (
    <>
      <PageHero eyebrow="Work -- résumé and projects"
        title={<>{author}</>}
        lede="Builder, author and software developer. One project, worked from every side: the timber, the geometry, the code, the book, the films and the business -- built with AI as a disciplined collaborator.">
        <Link className="btn" to="/card">Get in touch</Link>
        {github && <a className="btn-ghost" href={github.url} target="_blank" rel="noopener">The code on GitHub &#8599;</a>}
        {youtube && <a className="btn-ghost" href={youtube.url} target="_blank" rel="noopener">The films on YouTube &#8599;</a>}
      </PageHero>

      <Band ground="yang" texture="rings">
        <div className="grid gap-12 lg:grid-cols-[1fr_1.3fr]">
          <div>
            <p className="eyebrow">Summary</p>
            <h2 className="text-3xl sm:text-4xl leading-tight mt-3">Scope: the dome as the complete smart-home learning model.</h2>
          </div>
          <div className="grid gap-4 text-lg leading-relaxed">
            <p>
              The work is a single building treated as a whole curriculum: a {facts.dome.acrossFt}-foot geodesic dome framed from split logs,
              taken from the standing tree through geometry, structure, envelope, systems and cost to the screen it is explained on.
            </p>
            <p className="muted">
              Every layer is modelled in open code and every figure in the book, the films and this site is computed from it. That makes
              the dome both a house and a working framework for teaching computational thinking -- abstraction, decomposition, simulation,
              control, evaluation and communication -- and for using AI honestly: declared inputs, computed outputs, verified results.
            </p>
            <Link to="/mission#framework" className="link-arrow text-base">The framework in full</Link>
          </div>
        </div>
        <div className="mt-14">
          <Figures items={[
            [BOOK_FIGURES.chapters, "book chapters"],
            [BOOK_FIGURES.figures, "computed figures"],
            [FILM_COUNT, "films produced"],
            [PUBLIC_TOOLS, "public tools"],
          ]} />
        </div>
      </Band>

      <Band ground="yin" texture="grid">
        <Head eyebrow="Projects" title="Selected work" lede="Each project is a different face of the same model. Scope, stack and what it produced." />
        <div className="mt-12 grid gap-4">
          {PROJECTS.map((p, i) => (
            <article key={p.key} className="panel p-6 sm:p-7 grid gap-5 md:grid-cols-[200px_1fr_220px]">
              <div>
                <p className="mono text-xs muted">{String(i + 1).padStart(2, "0")}</p>
                <p className="eyebrow mt-2">{p.kind}</p>
              </div>
              <div>
                <h3 className="text-2xl font-semibold">{p.name}</h3>
                <p className="muted mt-2 leading-relaxed">{p.scope}</p>
                <div className="flex flex-wrap gap-2 mt-4">{p.stack.map((s) => <span key={s} className="tag">{s}</span>)}</div>
              </div>
              <div className="md:border-l md:pl-5" style={{ borderColor: "var(--line)" }}>
                <p className="mono text-[11px] uppercase tracking-[0.14em] muted">Outputs</p>
                <ul className="mt-2 grid gap-1 text-sm">{p.outputs.map((o) => <li key={o}>{o}</li>)}</ul>
                {p.to && <Link to={p.to} className="link-arrow text-sm mt-3">View</Link>}
              </div>
            </article>
          ))}
        </div>
      </Band>

      <Band ground="yang" texture="rings">
        <Head eyebrow="Learning outcomes" title="What each layer of the dome teaches" />
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-10">
          {LAYERS.map((l) => (
            <div key={l.layer} className="panel p-5">
              <p className="mono text-xs muted">{l.layer}</p>
              <h3 className="text-xl font-semibold mt-1 accent">{l.skill}</h3>
              <p className="text-sm mt-2 leading-relaxed">{l.ai}</p>
            </div>
          ))}
        </div>
      </Band>

      <Band ground="plain">
        <Head eyebrow="Skills" title="What the work takes" />
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8 mt-10">
          {SKILLS.map(([group, items]) => (
            <div key={group} className="border-t pt-4" style={{ borderColor: "var(--accent)" }}>
              <h3 className="text-2xl font-semibold">{group}</h3>
              <ul className="mt-3 grid gap-1.5 muted">{items.map((s) => <li key={s}>{s}</li>)}</ul>
            </div>
          ))}
        </div>
        <div className="panel p-8 mt-16 flex flex-wrap items-center justify-between gap-6">
          <div>
            <p className="eyebrow">Work together</p>
            <p className="display text-3xl font-semibold mt-2">Design work, teaching, or the build itself.</p>
          </div>
          <div className="flex flex-wrap gap-3"><Link className="btn" to="/studio">The studio</Link><Link className="btn-ghost" to="/card">Contact</Link></div>
        </div>
      </Band>
    </>
  );
}
