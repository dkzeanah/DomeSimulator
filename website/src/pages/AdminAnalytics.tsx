// The owner's analytics, counted by the site itself: visits, the funnel, where people come
// from and what each source earned, the list's growth, and how each sending identity's mail
// is read. One accent colour per chart (every chart is a single measure); hover any bar for
// its value; every chart has its table.

import AdminNav from "../components/AdminNav";
import { useEffect, useState } from "react";
import { Panel, Stat } from "../components/ui";
import { api, money, n } from "../lib/api";
import { useSession } from "../lib/session";

interface Report {
  days: number;
  totals: { views: number; visitors: number; sessions: number };
  daily: { day: string; views: number; visitors: number }[];
  pages: { path: string; views: number }[];
  sources: { source: string; visitors: number; views: number }[];
  devices: { device: string; views: number }[];
  countries: { country: string; views: number }[];
  funnel: { step: string; n: number }[];
  bySource: { source: string; samples: number; signups: number; purchases: number; revenue_cents: number }[];
  listDaily: { day: string; joined: number }[];
  listStatus: { status: string; n: number }[];
  outbox: { status: string; n: number }[];
  mailByKind: { identity: string; kind: string; sent: number; opened: number; clicked: number }[];
}

/** Columns over days, one measure. Hover a column for its value; the table is one click away. */
function Columns({ rows, label }: { rows: { key: string; value: number }[]; label: string }) {
  const [hover, setHover] = useState<number | null>(null);
  const [table, setTable] = useState(false);
  const max = Math.max(1, ...rows.map((r) => r.value));
  if (!rows.length) return <p className="muted text-sm">Nothing counted in this window yet.</p>;
  return (
    <div>
      <div className="flex justify-between items-baseline text-sm mb-2">
        <span className="muted">{hover !== null ? `${rows[hover].key}: ${n(rows[hover].value)} ${label}` : `Hover a day for its ${label}`}</span>
        <button className="underline text-xs" onClick={() => setTable(!table)}>{table ? "Show chart" : "Show table"}</button>
      </div>
      {table ? (
        <table className="w-full text-sm num"><tbody>{rows.map((r) => <tr key={r.key} className="border-t" style={{ borderColor: "var(--line)" }}><td className="py-1">{r.key}</td><td className="text-right">{n(r.value)}</td></tr>)}</tbody></table>
      ) : (
        <div className="flex items-end h-40 border-b" style={{ gap: 2, borderColor: "var(--line)" }} role="img" aria-label={`${label} by day`}>
          {rows.map((r, i) => (
            <div key={r.key} className="flex-1 h-full flex items-end cursor-default" onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}>
              <div className="w-full" style={{ height: `${Math.max(2, (r.value / max) * 100)}%`, background: "var(--accent)", opacity: hover === null || hover === i ? 1 : 0.45, borderRadius: "4px 4px 0 0" }} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/** Horizontal bars for a ranked list, the value printed beside each (text in ink, not colour). */
function Bars({ rows, fmt = n }: { rows: { key: string; value: number; note?: string }[]; fmt?: (v: number) => string }) {
  const max = Math.max(1, ...rows.map((r) => r.value));
  if (!rows.length) return <p className="muted text-sm">Nothing yet.</p>;
  return (
    <ul className="grid gap-2 text-sm">
      {rows.map((r) => (
        <li key={r.key} title={`${r.key}: ${fmt(r.value)}${r.note ? ` (${r.note})` : ""}`}>
          <div className="flex justify-between gap-3"><span className="truncate">{r.key}</span><span className="num">{fmt(r.value)}{r.note ? <span className="muted"> {r.note}</span> : null}</span></div>
          <div className="h-2 mt-1 rounded-full" style={{ background: "var(--panel-2)" }}>
            <div className="h-2 rounded-full" style={{ width: `${(r.value / max) * 100}%`, background: "var(--accent)" }} />
          </div>
        </li>
      ))}
    </ul>
  );
}

export default function AdminAnalytics() {
  const { me } = useSession();
  const [days, setDays] = useState(30);
  const [r, setR] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { if (me?.role === "admin") api<Report>(`/admin/analytics?days=${days}`).then(setR).catch((e) => setError(e.message)); }, [me, days]);
  if (me?.role !== "admin") return <div className="mx-auto max-w-xl px-4 py-10 muted">Admins only.</div>;
  if (error) return <div className="mx-auto max-w-xl px-4 py-10">{error}</div>;
  if (!r) return <div className="mx-auto max-w-xl px-4 py-10 muted">Counting...</div>;
  const f = r.funnel;
  const purchases = r.bySource.reduce((s, x) => s + Number(x.purchases || 0), 0);
  const revenue = r.bySource.reduce((s, x) => s + Number(x.revenue_cents || 0), 0);
  const pct = (a: number, b: number) => (b ? `${Math.round((a / b) * 1000) / 10}%` : "-");
  return (
    <div className="mx-auto max-w-6xl px-4 py-10 grid gap-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">Counted by this site, kept in its own database</p>
          <h1 className="text-4xl font-bold">Analytics</h1>
        </div>
        <div className="flex gap-2" role="group" aria-label="Time range">
          {[7, 30, 90].map((d) => <button key={d} className={d === days ? "btn !py-1.5" : "btn-ghost !py-1.5"} onClick={() => setDays(d)}>{d} days</button>)}
        </div>
      </div>
      <AdminNav />

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <Stat value={n(r.totals.visitors)} label="visitors" />
        <Stat value={n(r.totals.views)} label="page views" />
        <Stat value={n(r.totals.sessions)} label="visits (sessions)" />
        <Stat value={n(f[1].n)} label="got the sample" note={pct(f[1].n, f[0].n) + " of visitors"} />
        <Stat value={n(purchases)} label="purchases" />
        <Stat value={money(revenue)} label="revenue" />
      </div>

      <Panel title="Visitors by day"><Columns rows={r.daily.map((d) => ({ key: d.day, value: d.visitors }))} label="visitors" /></Panel>

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="The funnel">
          <Bars rows={f.map((s, i) => ({ key: s.step, value: s.n, note: i ? `${pct(s.n, f[i - 1].n)} of the step before` : undefined }))} />
          <p className="text-xs muted mt-3">Distinct visitors reaching each step in the window. Visitors whose browsers ask not to be tracked are counted as views but cannot be followed through the funnel.</p>
        </Panel>
        <Panel title="Where visitors come from">
          <Bars rows={r.sources.map((s) => ({ key: s.source, value: s.visitors }))} />
          <p className="text-xs muted mt-3">The campaign tag on the link (utm_source) when there is one, otherwise the site that linked here, otherwise "direct". Tag every link you post: ?utm_source=instagram&amp;utm_campaign=closing-the-triangle</p>
        </Panel>
      </div>

      <Panel title="What each source earned">
        <div className="overflow-x-auto">
          <table className="w-full text-sm num">
            <thead><tr className="muted text-left"><th className="py-1">First came from</th><th>Samples</th><th>Accounts</th><th>Purchases</th><th>Revenue</th></tr></thead>
            <tbody>{r.bySource.map((s) => (
              <tr key={s.source} className="border-t" style={{ borderColor: "var(--line)" }}><td className="py-1.5">{s.source}</td><td>{s.samples}</td><td>{s.signups}</td><td>{s.purchases}</td><td>{money(Number(s.revenue_cents || 0))}</td></tr>
            ))}</tbody>
          </table>
          {!r.bySource.length && <p className="muted text-sm">No conversions in this window yet.</p>}
        </div>
      </Panel>

      <div className="grid gap-6 lg:grid-cols-3">
        <Panel title="Top pages"><Bars rows={r.pages.map((p) => ({ key: p.path, value: p.views }))} /></Panel>
        <Panel title="Devices"><Bars rows={r.devices.map((d) => ({ key: d.device, value: d.views }))} /></Panel>
        <Panel title="Countries"><Bars rows={r.countries.map((c) => ({ key: c.country, value: c.views }))} /></Panel>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="The list: joined by day"><Columns rows={r.listDaily.map((d) => ({ key: d.day, value: d.joined }))} label="joined" /></Panel>
        <Panel title="The list, as it stands">
          <Bars rows={r.listStatus.map((s) => ({ key: s.status, value: s.n }))} />
          <h3 className="text-lg font-semibold mt-5 mb-2">The mail queue</h3>
          <Bars rows={r.outbox.map((s) => ({ key: s.status, value: s.n }))} />
        </Panel>
      </div>

      <Panel title="Mail by identity">
        <table className="w-full text-sm num">
          <thead><tr className="muted text-left"><th className="py-1">From</th><th>Kind</th><th>Sent</th><th>Opened</th><th>Clicked</th></tr></thead>
          <tbody>{r.mailByKind.map((m) => (
            <tr key={m.identity + m.kind} className="border-t" style={{ borderColor: "var(--line)" }}><td className="py-1.5">{m.identity}@</td><td>{m.kind}</td><td>{m.sent}</td><td>{m.opened} ({pct(m.opened, m.sent)})</td><td>{m.clicked} ({pct(m.clicked, m.sent)})</td></tr>
          ))}</tbody>
        </table>
        {!r.mailByKind.length && <p className="muted text-sm">Nothing sent yet -- the queue waits for the mail server.</p>}
        <p className="text-xs muted mt-3">Opens are a lower bound: many mail apps block the image that counts them. Clicks are exact.</p>
      </Panel>
    </div>
  );
}
