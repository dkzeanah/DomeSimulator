// Every edition, from the catalogue: the digital book, the triangular book, the Amazon
// paperback and the design session. Prices and states are the database's.

import { useState } from "react";
import { api, money } from "../lib/api";
import { useCatalogue, type Product } from "../lib/catalogue";
import { book as bookFacts } from "../lib/facts";
import Buy from "./Buy";
import { ErrorLine, Panel } from "./ui";

function Waitlist({ source, label }: { source: string; label: string }) {
  const [email, setEmail] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  async function join(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api("/subscribe", { body: { email, source, marketingConsent: true } });
      setDone(true);
    } catch (err) { setError((err as Error).message); }
  }
  return done ? <p className="accent text-sm">You are on the list. You will hear the day it is out.</p> : (
    <form onSubmit={join} className="flex gap-2 flex-col sm:flex-row">
      <input className="field" type="email" required placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} />
      <button className="btn whitespace-nowrap">{label}</button>
      <ErrorLine error={error} />
    </form>
  );
}

function Card({ p }: { p: Product }) {
  const lowest = Math.min(...p.prices.map((x) => x.amountCents));
  if (p.kind === "amazon") {
    return (
      <Panel kicker="The simplified paperback, on Amazon" title={`${p.subtitle}, ${money(lowest)}`}>
        <p className="text-sm muted mb-3">{p.blurb}</p>
        {p.externalUrl ? <a className="btn" href={p.externalUrl}>Buy it on Amazon</a> : <Waitlist source={p.slug} label="Tell me when it is on Amazon" />}
      </Panel>
    );
  }
  if (p.kind === "physical") {
    return (
      <Panel kicker={p.status === "preorder" ? "Pre-order - printed by hand" : "Printed by hand"} title={p.subtitle || p.title}>
        <p className="text-sm muted mb-3">{p.blurb}</p>
        <Buy product={p} />
      </Panel>
    );
  }
  if (p.kind === "service") {
    return (
      <Panel kicker="One on one" title={`${p.title}, ${money(lowest)}`}>
        <p className="text-sm muted mb-3">{p.blurb}</p>
        <Buy product={p} cta="Book a session" />
      </Panel>
    );
  }
  return (
    <Panel kicker="Digital edition" title={money(lowest)}>
      <ul className="text-sm space-y-1.5 mb-4">{(bookFacts.includes || []).map((i) => <li key={i}>- {i}</li>)}</ul>
      <Buy product={p} cta="Buy the book" />
    </Panel>
  );
}

export default function Shelf({ only }: { only?: string[] }) {
  const { products } = useCatalogue();
  if (!products) return <p className="muted text-sm">Loading the shelf...</p>;
  const shown = products.filter((p) => p.prices.every((x) => x.amountCents > 0) && (!only || only.includes(p.slug)))
    .sort((a, b) => (only ? only.indexOf(a.slug) - only.indexOf(b.slug) : 0));
  return <div className="grid gap-6 content-start">{shown.map((p) => <Card key={p.slug} p={p} />)}</div>;
}
