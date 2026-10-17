// My Own Home, My Own Dome: the children's book. The opening stanzas come from its manuscript
// (books/my-own-home-my-own-dome/verse.md, through scripts/export_facts.py); the price and
// whether it is still a pre-order come from the catalogue.

import { Link } from "react-router-dom";
import Buy from "../components/Buy";
import { Panel } from "../components/ui";
import { useCatalogue } from "../lib/catalogue";
import { facts } from "../lib/facts";
import { useMeta } from "../lib/meta";

const SLUG = "my-own-home-my-own-dome";

export default function Kids() {
  const kb = facts.kidsBook;
  useMeta(kb.title, `${kb.title}: the wedge-dome build told in rhyme, ${kb.stanzaCount} spreads for reading aloud.`, "/kids");
  const { get, products } = useCatalogue();
  const p = get(SLUG);
  return (
    <div className="mx-auto max-w-6xl px-4 py-10 grid gap-8 lg:grid-cols-[1.3fr_1fr]">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">A rhyming picture book</p>
        <h1 className="text-4xl sm:text-6xl font-bold mt-1 leading-[1.05]">{kb.title}</h1>
        <p className="mt-3 max-w-2xl text-lg">
          In a town full of boxes, one girl wants a home with no corners. So she finds a fallen pine, splits it into wedges,
          and builds a dome -- and finds out that one number tells her everything about it.
        </p>
        <div className="mt-8 grid gap-5">
          {kb.preview.map((stanza, i) => (
            <blockquote key={i} className="panel p-5 display text-lg xl:text-2xl leading-snug whitespace-pre-line" style={{ borderLeft: "4px solid var(--accent)" }}>
              {stanza}
            </blockquote>
          ))}
          <p className="muted text-sm">The opening {kb.preview.length} of {kb.stanzaCount} spreads.</p>
        </div>
      </div>
      <div className="grid gap-6 content-start lg:sticky lg:top-20">
        <Panel kicker={p?.status === "preorder" ? "Pre-order -- being illustrated" : "Digital picture book"} title={p ? p.title : kb.title}>
          {!products ? <p className="muted text-sm">Loading...</p> : p ? (
            <>
              <p className="text-sm muted mb-3">{p.blurb}</p>
              {p.status === "preorder" && p.shipsNote && <p className="text-xs muted mb-3">{p.shipsNote}</p>}
              <Buy product={p} cta={p.status === "preorder" ? "Pre-order" : "Buy the book"} />
            </>
          ) : <p className="text-sm muted">Not on sale right now.</p>}
        </Panel>
        <p className="text-sm muted">For the grown-ups: <Link className="underline" to="/book">The 40 Hour Cabin</Link> is the build itself, every number worked out.</p>
      </div>
    </div>
  );
}
