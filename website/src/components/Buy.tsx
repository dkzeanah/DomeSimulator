// Buying anything in the catalogue: pick a price (the triangular book has two), describe a
// donation when the price runs on the buyer's word, and go to Stripe's page.

import { useEffect, useState } from "react";
import { api, money } from "../lib/api";
import type { Product } from "../lib/catalogue";
import { useSession } from "../lib/session";
import { ErrorLine, Honeypot } from "./ui";

export default function Buy({ product, cta }: { product: Product; cta?: string }) {
  const { me } = useSession();
  const [email, setEmail] = useState(me?.email || "");
  const [priceKey, setPriceKey] = useState(product.prices[0]?.key || "standard");
  const [note, setNote] = useState("");
  const [mode, setMode] = useState<string | null | undefined>(undefined);
  const [trap, setTrap] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { api<{ mode: string | null }>("/shop").then((r) => setMode(r.mode)).catch(() => setMode(null)); }, []);
  const price = product.prices.find((p) => p.key === priceKey) || product.prices[0];
  if (!price) return null;

  async function buy(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const r = await api<{ url: string }>("/checkout", { body: { product: product.slug, price: price.key, email, honorNote: note, website: trap } });
      window.location.href = r.url;
    } catch (err) {
      setError((err as Error).message);
      setBusy(false);
    }
  }
  if (mode === null) return <p className="text-sm muted">The shop opens soon. Get the free sample and you will hear first.</p>;
  return (
    <form onSubmit={buy} className="grid gap-3 relative text-sm">
      {product.prices.length > 1 && (
        <fieldset className="grid gap-2">
          {product.prices.map((p) => (
            <label key={p.key} className={`panel-2 p-3 flex items-start gap-2 cursor-pointer ${p.key === price.key ? "ring-2 ring-[var(--accent)]" : ""}`}>
              <input type="radio" name={`price-${product.slug}`} className="mt-1" checked={p.key === price.key} onChange={() => setPriceKey(p.key)} />
              <span className="flex-1">{p.label}{p.honor && <span className="block text-xs muted">On the honor system.</span>}</span>
              <span className="num font-semibold accent">{money(p.amountCents, p.currency)}</span>
            </label>
          ))}
        </fieldset>
      )}
      {price.honor && (
        <label className="grid gap-1">
          <span>{price.honorPrompt}</span>
          <textarea className="field" rows={3} required minLength={10} value={note} onChange={(e) => setNote(e.target.value)} />
        </label>
      )}
      <input className="field" type="email" required placeholder="Email for the receipt" value={email} onChange={(e) => setEmail(e.target.value)} />
      <Honeypot value={trap} onChange={setTrap} />
      {product.kind === "physical" && product.shipsNote && <p className="text-xs muted">{product.shipsNote}</p>}
      <button className="btn" disabled={busy || mode === undefined}>
        {busy ? "Opening checkout..." : `${cta || (product.status === "preorder" ? "Pre-order" : "Buy")}, ${money(price.amountCents, price.currency)}`}
      </button>
      {mode === "test" && <p className="text-xs muted">Test checkout: no card is charged.</p>}
      <ErrorLine error={error} />
    </form>
  );
}
