// Buying anything in the catalogue: pick a price (the triangular book has two), describe a
// donation when the price runs on the buyer's word, or enter a promo code for the friend price,
// and go to Stripe's page.

import { useEffect, useState } from "react";
import { api, money } from "../lib/api";
import type { PriceOption, Product } from "../lib/catalogue";
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
  const [promoOpen, setPromoOpen] = useState(false);
  const [typed, setTyped] = useState("");
  const [promo, setPromo] = useState<{ code: string; price: PriceOption } | null>(null);
  const [promoError, setPromoError] = useState<string | null>(null);
  useEffect(() => { api<{ mode: string | null }>("/shop").then((r) => setMode(r.mode)).catch(() => setMode(null)); }, []);
  const listed = product.prices.find((p) => p.key === priceKey) || product.prices[0];
  const price = promo?.price || listed;
  if (!price) return null;
  const canPromo = ["digital", "service"].includes(product.kind);

  async function applyPromo() {
    setPromoError(null);
    try { setPromo(await api<{ code: string; price: PriceOption }>("/promo/check", { body: { product: product.slug, code: typed } })); }
    catch (err) { setPromo(null); setPromoError((err as Error).message); }
  }

  // The owner's free copy, through the same order, receipt, email and download as a sale.
  async function ownerCopy() {
    setBusy(true);
    setError(null);
    try {
      const r = await api<{ url: string }>("/checkout", { body: { product: product.slug, ownerCopy: true } });
      window.location.href = r.url;
    } catch (err) {
      setError((err as Error).message);
      setBusy(false);
    }
  }

  async function buy(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const r = await api<{ url: string }>("/checkout", { body: { product: product.slug, price: price.key, promoCode: promo?.code, email, honorNote: note, website: trap } });
      window.location.href = r.url;
    } catch (err) {
      setError((err as Error).message);
      setBusy(false);
    }
  }
  if (mode === null) return <p className="text-sm muted">The shop opens soon. Get the free sample and you will hear first.</p>;
  return (
    <form onSubmit={buy} className="grid gap-3 relative text-sm">
      {product.prices.length > 1 && !promo && (
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
      {canPromo && (promo ? (
        <p className="panel-2 p-3 flex items-center justify-between gap-2">
          <span>Code <b className="font-mono">{promo.code}</b>: {promo.price.label}</span>
          <button type="button" className="underline text-xs" onClick={() => { setPromo(null); setTyped(""); }}>Remove</button>
        </p>
      ) : promoOpen ? (
        <div className="grid gap-1">
          <div className="flex gap-2">
            <input className="field font-mono uppercase" placeholder="Promo code" value={typed} onChange={(e) => setTyped(e.target.value)} />
            <button type="button" className="btn-ghost whitespace-nowrap" onClick={applyPromo} disabled={!typed.trim()}>Apply</button>
          </div>
          <ErrorLine error={promoError} />
        </div>
      ) : <button type="button" className="text-xs underline underline-offset-4 justify-self-start" onClick={() => setPromoOpen(true)}>Have a promo code?</button>)}
      <input className="field" type="email" required placeholder="Email for the receipt" value={email} onChange={(e) => setEmail(e.target.value)} />
      <Honeypot value={trap} onChange={setTrap} />
      {product.kind === "physical" && product.shipsNote && <p className="text-xs muted">{product.shipsNote}</p>}
      <button className="btn" disabled={busy || mode === undefined}>
        {busy ? "Opening checkout..." : `${cta || (product.status === "preorder" ? "Pre-order" : "Buy")}, ${money(price.amountCents, price.currency)}`}
      </button>
      {mode === "test" && <p className="text-xs muted">Test checkout: no card is charged.</p>}
      {me?.role === "admin" && product.kind === "digital" && (
        <div className="panel-2 p-3 grid gap-1.5">
          <button type="button" className="btn-ghost" disabled={busy} onClick={() => void ownerCopy()}>Get my owner copy, free</button>
          <p className="text-xs muted">Only you see this. It makes a real order at $0 -- receipt page, email to {me.email}, download, My books -- so you can check the whole path. It is not counted as a sale.</p>
        </div>
      )}
      <ErrorLine error={error} />
    </form>
  );
}
