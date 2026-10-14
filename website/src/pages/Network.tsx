// The pad network: every pad is a method -- a rate and a gate. Its numbers are the
// host's own, worked out the same way for every pad, so they can be compared on one page.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ErrorLine, Panel } from "../components/ui";
import { api, money } from "../lib/api";
import { useSession } from "../lib/session";

interface Pad { nightlyRateCents: number | null; occupancyPct: number | null; seasonCostCents: number | null; seasonNights: number | null; hookups: string[]; status: string;
  numbers: { nightsLet: number; revenueCents: number; costCents: number; netCents: number; netPerNightCents: number | null } | null }
interface Listing { id: number; kind: string; title: string; body: string; city: string; region: string; country: string; contact: string | null; contactHidden: boolean; pad: Pad | null; owner: { displayName: string }; mine: boolean }
interface Kind { key: string; label: string; blurb: string }

const HOOKUPS = ["water", "power", "septic", "internet"];

function PadCard({ l }: { l: Listing }) {
  const p = l.pad!;
  const x = p.numbers;
  return (
    <article className="panel p-5">
      <div className="flex justify-between gap-3">
        <h3 className="text-xl font-semibold">{l.title}</h3>
        <span className="text-xs uppercase tracking-[0.15em] accent whitespace-nowrap">{p.status}</span>
      </div>
      <p className="text-sm muted">{[l.city, l.region, l.country].filter(Boolean).join(", ")} - hosted by {l.owner.displayName}</p>
      {l.body && <p className="text-sm mt-2">{l.body}</p>}
      <table className="w-full text-sm mt-3 num">
        <tbody>
          <tr><td className="muted">Rate</td><td className="text-right">{p.nightlyRateCents != null ? `${money(p.nightlyRateCents)} a night` : "not given"}</td></tr>
          <tr><td className="muted">Let</td><td className="text-right">{p.occupancyPct != null && p.seasonNights != null ? `${p.occupancyPct}% of ${p.seasonNights} nights` : "not given"}</td></tr>
          <tr><td className="muted">Season running cost</td><td className="text-right">{p.seasonCostCents != null ? money(p.seasonCostCents) : "not given"}</td></tr>
          {x && <tr className="font-semibold"><td>Season, after cost</td><td className="text-right accent">{money(x.netCents)}{x.netPerNightCents != null ? ` (${money(x.netPerNightCents)} a night let)` : ""}</td></tr>}
        </tbody>
      </table>
      <p className="text-xs muted mt-2">Gate: {p.hookups.length ? `has ${p.hookups.join(", ")}` : "no hookups listed"}. Host-reported figures.</p>
      <p className="text-sm mt-3">{l.contact ? <>Contact: {l.contact}</> : l.contactHidden ? <Link className="underline" to="/account">Sign in to see the contact</Link> : null}</p>
    </article>
  );
}

function OtherCard({ l, kinds }: { l: Listing; kinds: Kind[] }) {
  return (
    <article className="panel p-5">
      <p className="text-xs uppercase tracking-[0.15em] accent">{kinds.find((k) => k.key === l.kind)?.label || l.kind}</p>
      <h3 className="text-xl font-semibold mt-1">{l.title}</h3>
      <p className="text-sm muted">{[l.city, l.region, l.country].filter(Boolean).join(", ")} - {l.owner.displayName}</p>
      {l.body && <p className="text-sm mt-2">{l.body}</p>}
      <p className="text-sm mt-3">{l.contact ? <>Contact: {l.contact}</> : l.contactHidden ? <Link className="underline" to="/account">Sign in to see the contact</Link> : null}</p>
    </article>
  );
}

function AddListing({ kinds, onSaved }: { kinds: Kind[]; onSaved: () => void }) {
  const { mark } = useSession();
  const [f, setF] = useState<Record<string, any>>({ kind: "pad_host", padStatus: "planned", hookups: [] as string[] });
  const [error, setError] = useState<string | null>(null);
  const set = (k: string, v: unknown) => setF((x) => ({ ...x, [k]: v }));
  async function save(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const payload: Record<string, unknown> = { ...f };
    for (const k of ["nightlyRate", "seasonCost", "occupancyPct", "seasonNights"]) payload[k] = f[k] === "" || f[k] === undefined ? null : Number(f[k]);
    if (f.kind !== "pad_host") for (const k of ["nightlyRate", "seasonCost", "occupancyPct", "seasonNights", "hookups", "padStatus"]) delete payload[k];
    try {
      await api("/network", { body: payload });
      mark("network");
      setF({ kind: "pad_host", padStatus: "planned", hookups: [] });
      onSaved();
    } catch (err) { setError((err as Error).message); }
  }
  const pad = f.kind === "pad_host";
  return (
    <form onSubmit={save} className="grid gap-3 text-sm">
      <select className="field" value={f.kind} onChange={(e) => set("kind", e.target.value)}>
        {kinds.map((k) => <option key={k.key} value={k.key}>{k.label}</option>)}
      </select>
      <p className="muted text-xs">{kinds.find((k) => k.key === f.kind)?.blurb}</p>
      <input className="field" required minLength={3} placeholder="Title" value={f.title || ""} onChange={(e) => set("title", e.target.value)} />
      <textarea className="field" rows={3} placeholder="What you have or need" value={f.body || ""} onChange={(e) => set("body", e.target.value)} />
      <div className="grid grid-cols-3 gap-2">
        <input className="field" placeholder="City" value={f.city || ""} onChange={(e) => set("city", e.target.value)} />
        <input className="field" placeholder="State / region" value={f.region || ""} onChange={(e) => set("region", e.target.value)} />
        <input className="field" placeholder="Country" value={f.country || ""} onChange={(e) => set("country", e.target.value)} />
      </div>
      <input className="field" placeholder="Contact shown to members (email, phone, link)" value={f.contact || ""} onChange={(e) => set("contact", e.target.value)} />
      {pad && (
        <fieldset className="panel-2 p-3 grid gap-2">
          <legend className="px-1 font-semibold">The pad's numbers</legend>
          <div className="grid grid-cols-2 gap-2">
            <label className="grid gap-1">Nightly rate ($)<input className="field" type="number" min="0" step="1" value={f.nightlyRate ?? ""} onChange={(e) => set("nightlyRate", e.target.value)} /></label>
            <label className="grid gap-1">Season running cost ($)<input className="field" type="number" min="0" step="1" value={f.seasonCost ?? ""} onChange={(e) => set("seasonCost", e.target.value)} /></label>
            <label className="grid gap-1">Nights in your season<input className="field" type="number" min="0" max="366" value={f.seasonNights ?? ""} onChange={(e) => set("seasonNights", e.target.value)} /></label>
            <label className="grid gap-1">Share of nights let (%)<input className="field" type="number" min="0" max="100" value={f.occupancyPct ?? ""} onChange={(e) => set("occupancyPct", e.target.value)} /></label>
          </div>
          <div className="flex flex-wrap gap-3">
            {HOOKUPS.map((h) => (
              <label key={h} className="flex gap-1 items-center"><input type="checkbox" checked={f.hookups.includes(h)}
                onChange={(e) => set("hookups", e.target.checked ? [...f.hookups, h] : f.hookups.filter((x: string) => x !== h))} />{h}</label>
            ))}
          </div>
          <select className="field" value={f.padStatus} onChange={(e) => set("padStatus", e.target.value)}>
            <option value="planned">Planned</option><option value="built">Built</option><option value="hosting">Hosting now</option>
          </select>
        </fieldset>
      )}
      <button className="btn">Add to the network</button>
      <ErrorLine error={error} />
    </form>
  );
}

export default function Network() {
  const { me } = useSession();
  const [kinds, setKinds] = useState<Kind[]>([]);
  const [kind, setKind] = useState("");
  const [q, setQ] = useState("");
  const [rows, setRows] = useState<Listing[] | null>(null);
  const [tick, setTick] = useState(0);
  useEffect(() => { api<{ kinds: Kind[] }>("/network/kinds").then((r) => setKinds(r.kinds)).catch(() => undefined); }, []);
  useEffect(() => {
    const p = new URLSearchParams();
    if (kind) p.set("kind", kind);
    if (q) p.set("q", q);
    api<{ results: Listing[] }>(`/network?${p}`).then((r) => setRows(r.results)).catch(() => setRows([]));
  }, [kind, q, tick]);
  const pads = (rows || []).filter((r) => r.kind === "pad_host");
  const others = (rows || []).filter((r) => r.kind !== "pad_host");
  return (
    <div className="mx-auto max-w-6xl px-4 py-10 grid gap-6">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">The network</p>
        <h1 className="text-4xl sm:text-5xl font-bold mt-1">Pads, and the people around them</h1>
        <p className="muted mt-2 max-w-3xl">
          A pad is a serviced place a dome can stand. Every pad here carries its own numbers -- what a night costs, how often it is let,
          what a season costs to run -- worked out the same way for each, so any two can be compared on one page.
        </p>
      </div>
      <div className="flex flex-col sm:flex-row gap-2">
        <input className="field" placeholder="Search by place or word" value={q} onChange={(e) => setQ(e.target.value)} />
        <select className="field sm:w-60" value={kind} onChange={(e) => setKind(e.target.value)}>
          <option value="">Everyone</option>
          {kinds.map((k) => <option key={k.key} value={k.key}>{k.label}</option>)}
        </select>
      </div>
      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <div className="grid gap-4 content-start">
          {rows === null ? <p className="muted">Loading...</p> : rows.length === 0 ? (
            <Panel title="No one here yet">
              <p className="muted">The network is empty so far. The first pad listed will be the first one shown -- nothing here is placeholder.</p>
            </Panel>
          ) : (
            <>
              {pads.length > 0 && <div className="grid md:grid-cols-2 gap-4">{pads.map((l) => <PadCard key={l.id} l={l} />)}</div>}
              {others.length > 0 && <div className="grid md:grid-cols-2 gap-4">{others.map((l) => <OtherCard key={l.id} l={l} kinds={kinds} />)}</div>}
            </>
          )}
        </div>
        <Panel title="List yourself">
          {me ? <AddListing kinds={kinds} onSaved={() => setTick((t) => t + 1)} /> : (
            <p className="text-sm"><Link className="underline" to="/account">Make an account</Link> to list a pad, a dome, timber, or yourself as a builder or recycler.</p>
          )}
        </Panel>
      </div>
    </div>
  );
}
