// Only for the site's owner (ADMIN_EMAILS): the list, and recording real backers and
// founder plaques from the campaign's own records.

import { useEffect, useState } from "react";
import { ErrorLine, Panel } from "../components/ui";
import { api, money } from "../lib/api";
import { useCatalogue } from "../lib/catalogue";
import { facts } from "../lib/facts";
import { useSession } from "../lib/session";

interface Sub { email: string; name: string | null; marketing_consent: number; source: string; created_at: string; unsubscribed_at: string | null }

export default function Admin() {
  const { me } = useSession();
  const [subs, setSubs] = useState<Sub[]>([]);
  const [offers, setOffers] = useState<{ kind: string; book_slug: string; n: number }[]>([]);
  const [backers, setBackers] = useState<{ id: number; display_name: string; tier: string; pledge_cents: number }[]>([]);
  const [b, setB] = useState({ displayName: "", tier: facts.tiers[0].key, pledge: "", userEmail: "", public: true });
  const [pl, setPl] = useState({ slot: "", backerId: "", inscription: "" });
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = () => {
    api<{ subscribers: Sub[]; offers: typeof offers }>("/admin/subscribers").then((r) => { setSubs(r.subscribers); setOffers(r.offers); }).catch((e) => setError(e.message));
    api<{ backers: typeof backers }>("/admin/backers").then((r) => setBackers(r.backers)).catch(() => undefined);
  };
  useEffect(() => { if (me?.role === "admin") load(); }, [me]);
  if (me?.role !== "admin") return <div className="mx-auto max-w-xl px-4 py-10 muted">Admins only.</div>;
  const act = async (fn: () => Promise<unknown>, done: string) => { setError(null); try { await fn(); setMsg(done); load(); } catch (e) { setError((e as Error).message); } };
  return (
    <div className="mx-auto max-w-6xl px-4 py-10 grid gap-6">
      <h1 className="text-4xl font-bold">Admin</h1>
      {msg && <p className="accent">{msg}</p>}
      <ErrorLine error={error} />
      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="Record a backer">
          <p className="text-sm muted mb-3">Only from the campaign's own records. The site never takes a pledge itself.</p>
          <form className="grid gap-2 text-sm" onSubmit={(e) => { e.preventDefault(); void act(() => api("/admin/backers", { body: { ...b, pledge: Number(b.pledge) } }), "Backer recorded."); }}>
            <input className="field" required placeholder="Name as they want it shown" value={b.displayName} onChange={(e) => setB({ ...b, displayName: e.target.value })} />
            <select className="field" value={b.tier} onChange={(e) => setB({ ...b, tier: e.target.value })}>{facts.tiers.map((t) => <option key={t.key} value={t.key}>{t.label} (${t.pledge})</option>)}</select>
            <input className="field" required type="number" step="any" placeholder="Pledge ($)" value={b.pledge} onChange={(e) => setB({ ...b, pledge: e.target.value })} />
            <input className="field" placeholder="Their account email (optional, links the badge)" value={b.userEmail} onChange={(e) => setB({ ...b, userEmail: e.target.value })} />
            <label className="flex gap-2"><input type="checkbox" checked={b.public} onChange={(e) => setB({ ...b, public: e.target.checked })} />Show publicly</label>
            <button className="btn">Record</button>
          </form>
        </Panel>
        <Panel title="Claim a founder plaque">
          <form className="grid gap-2 text-sm" onSubmit={(e) => { e.preventDefault(); void act(() => api("/admin/plaques", { body: { slot: Number(pl.slot), backerId: Number(pl.backerId), inscription: pl.inscription } }), "Plaque claimed."); }}>
            <input className="field" required type="number" min={1} max={facts.plaques.slots} placeholder={`Panel 1-${facts.plaques.slots}`} value={pl.slot} onChange={(e) => setPl({ ...pl, slot: e.target.value })} />
            <select className="field" required value={pl.backerId} onChange={(e) => setPl({ ...pl, backerId: e.target.value })}>
              <option value="">Backer...</option>{backers.map((x) => <option key={x.id} value={x.id}>{x.display_name} ({x.tier})</option>)}
            </select>
            <input className="field" placeholder="Inscription" value={pl.inscription} onChange={(e) => setPl({ ...pl, inscription: e.target.value })} />
            <button className="btn">Claim</button>
          </form>
        </Panel>
      </div>
      <CatalogueAdmin onError={setError} />
      <ShipAdmin onError={setError} />
      <Panel title={`The list (${subs.length})`}>
        <a className="btn-ghost" href="/api/admin/subscribers?format=csv">Download CSV</a>
        <ul className="text-sm mt-3 grid gap-1">{offers.map((o) => <li key={o.kind + o.book_slug}>{o.kind} / {o.book_slug}: <b>{o.n}</b></li>)}</ul>
        <div className="overflow-x-auto mt-4">
          <table className="w-full text-sm"><tbody>{subs.slice(0, 200).map((s) => (
            <tr key={s.email} className="border-t" style={{ borderColor: "var(--line)" }}><td className="py-1">{s.email}</td><td>{s.source}</td><td>{s.marketing_consent ? "updates" : ""}</td><td className="muted">{s.created_at.slice(0, 10)}</td></tr>
          ))}</tbody></table>
        </div>
      </Panel>
    </div>
  );
}

/** Prices and states are rows: change them here and every page shows the new value. */
function CatalogueAdmin({ onError }: { onError: (e: string | null) => void }) {
  const { products } = useCatalogue();
  const [list, setList] = useState(products);
  useEffect(() => setList(products), [products]);
  if (!list) return null;
  const save = async (path: string, body: Record<string, unknown>) => {
    onError(null);
    try { setList((await api<{ products: typeof list }>(path, { method: "PATCH", body })).products); } catch (e) { onError((e as Error).message); }
  };
  return (
    <Panel title="Catalogue">
      <div className="grid gap-3 text-sm">
        {list.map((p) => (
          <div key={p.slug} className="panel-2 p-3 grid gap-2">
            <div className="flex flex-wrap justify-between gap-2">
              <b>{p.title}{p.subtitle ? `: ${p.subtitle}` : ""}</b>
              <select className="field !w-auto" value={p.status} onChange={(e) => save(`/admin/products/${p.slug}`, { status: e.target.value })}>
                {["live", "preorder", "waitlist", "hidden"].map((s) => <option key={s}>{s}</option>)}
              </select>
            </div>
            {p.kind === "amazon" && (
              <input className="field" placeholder="Amazon listing URL, once it exists" defaultValue={p.externalUrl || ""}
                onBlur={(e) => e.target.value !== (p.externalUrl || "") && save(`/admin/products/${p.slug}`, { externalUrl: e.target.value })} />
            )}
            {p.prices.map((r) => (
              <label key={r.key} className="flex items-center gap-2">
                <span className="flex-1">{r.label}{r.honor ? " (honor)" : ""}</span>
                <span className="muted">now {money(r.amountCents, r.currency)}</span>
                <input className="field !w-28" type="number" step="0.01" min="0" defaultValue={(r.amountCents / 100).toFixed(2)}
                  onBlur={(e) => Number(e.target.value) * 100 !== r.amountCents && save(`/admin/prices/${p.slug}/${r.key}`, { amount: Number(e.target.value) })} />
              </label>
            ))}
          </div>
        ))}
      </div>
    </Panel>
  );
}

interface ShipOrder { ref: string; book_slug: string; price_key: string; amount_cents: number; email: string; honor_note: string | null; ship_name: string | null; ship_address: string | null; fulfillment: string | null; paid_at: string }

function ShipAdmin({ onError }: { onError: (e: string | null) => void }) {
  const [orders, setOrders] = useState<ShipOrder[]>([]);
  const load = () => api<{ orders: ShipOrder[] }>("/admin/orders").then((r) => setOrders(r.orders.filter((o) => o.fulfillment))).catch((e) => onError(e.message));
  useEffect(() => { void load(); }, []);
  return (
    <Panel title={`To print and ship (${orders.filter((o) => o.fulfillment !== "shipped").length})`}>
      {orders.length ? (
        <ul className="grid gap-2 text-sm">
          {orders.map((o) => {
            const a = o.ship_address ? JSON.parse(o.ship_address) : null;
            return (
              <li key={o.ref} className="panel-2 p-3 grid gap-1">
                <div className="flex justify-between gap-2"><b>{o.ship_name || o.email}</b><span className="num">{money(o.amount_cents)} ({o.price_key})</span></div>
                {a && <span className="muted">{[a.line1, a.line2, a.city, a.state, a.postal_code, a.country].filter(Boolean).join(", ")}</span>}
                {o.honor_note && <span className="muted">Donation: {o.honor_note}</span>}
                <select className="field !w-auto" value={o.fulfillment || "waiting"} onChange={async (e) => {
                  try { await api(`/admin/orders/${o.ref}`, { method: "PATCH", body: { fulfillment: e.target.value } }); void load(); } catch (err) { onError((err as Error).message); }
                }}>
                  {["waiting", "printed", "shipped"].map((s) => <option key={s}>{s}</option>)}
                </select>
              </li>
            );
          })}
        </ul>
      ) : <p className="muted text-sm">No physical orders yet.</p>}
    </Panel>
  );
}
