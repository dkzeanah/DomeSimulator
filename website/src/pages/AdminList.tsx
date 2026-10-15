// The owner's list and email: who is on it and how they arrived, tags, campaigns (compose,
// test to yourself, queue to a segment), the follow-up sequences, and the sending identities.

import { useCallback, useEffect, useState } from "react";
import { ErrorLine, Panel } from "../components/ui";
import { api, n } from "../lib/api";
import { useSession } from "../lib/session";

interface Sub { id: number; email: string; name: string | null; status: string; marketing_consent: number; source: string; first_source: string | null; first_campaign: string | null; created_at: string; confirmed_at: string | null; tags: string | null }
interface Campaign { id: number; name: string; identity: string; subject: string; body: string; segment: string; status: string; queued_count: number; sent: number; opened: number; clicked: number; created_at: string }
interface Sequence { key: string; name: string; trigger: string; active: number; active_runs: number }
interface Step { sequence: string; step: number; delay_hours: number; identity: string; subject: string; body: string }
interface Identity { key: string; from_name: string; from_email: string; reply_to: string | null; archive_bcc: string | null; purpose: string }
interface Data { subscribers: Sub[]; campaigns: Campaign[]; sequences: Sequence[]; steps: Step[]; identities: Identity[]; outbox: { status: string; kind: string; n: number }[]; postalAddressSet: boolean; mailerSet: boolean }

const TOKENS = "{{name}} {{book_pages}} {{book_figures}} {{frame_hours}} {{sample_pages}} {{dome_ft}} {{book_price}} {{site}}";

function StepEditor({ s, onSaved }: { s: Step; onSaved: () => void }) {
  const [subject, setSubject] = useState(s.subject);
  const [body, setBody] = useState(s.body);
  const [delay, setDelay] = useState(String(s.delay_hours));
  const [msg, setMsg] = useState<string | null>(null);
  return (
    <div className="panel-2 p-3 grid gap-2 text-sm">
      <div className="flex gap-2 items-center"><b>Step {s.step + 1}</b><span className="muted">from {s.identity}@, after</span>
        <input className="field !w-24" type="number" min="0" value={delay} onChange={(e) => setDelay(e.target.value)} /><span className="muted">hours</span></div>
      <input className="field" value={subject} onChange={(e) => setSubject(e.target.value)} />
      <textarea className="field font-mono text-xs" rows={8} value={body} onChange={(e) => setBody(e.target.value)} />
      <button className="btn-ghost justify-self-start" onClick={async () => {
        await api(`/admin/sequences/${s.sequence}`, { method: "PATCH", body: { step: s.step, subject, body, delayHours: Number(delay) } });
        setMsg("Saved."); onSaved();
      }}>Save step</button>
      {msg && <span className="accent">{msg}</span>}
    </div>
  );
}

export default function AdminList() {
  const { me } = useSession();
  const [d, setD] = useState<Data | null>(null);
  const [filter, setFilter] = useState("all");
  const [picked, setPicked] = useState<Set<number>>(new Set());
  const [tag, setTag] = useState("");
  const [c, setC] = useState({ name: "", identity: "donovan", subject: "", body: "", tags: "", source: "" });
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(() => api<Data>("/admin/list").then(setD).catch((e) => setError(e.message)), []);
  useEffect(() => { if (me?.role === "admin") void load(); }, [me, load]);
  if (me?.role !== "admin") return <div className="mx-auto max-w-xl px-4 py-10 muted">Admins only.</div>;
  if (!d) return <div className="mx-auto max-w-xl px-4 py-10 muted">{error || "Loading..."}</div>;
  const act = async (fn: () => Promise<unknown>, done: string) => { setError(null); setMsg(null); try { await fn(); setMsg(done); await load(); } catch (e) { setError((e as Error).message); } };
  const shown = d.subscribers.filter((s) => filter === "all" || s.status === filter);
  const counts = d.subscribers.reduce<Record<string, number>>((m, s) => ({ ...m, [s.status]: (m[s.status] || 0) + 1 }), {});
  const mailable = d.subscribers.filter((s) => s.status === "confirmed" && s.marketing_consent).length;

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 grid gap-6">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">Your own list, your own mail</p>
        <h1 className="text-4xl font-bold">The list and email</h1>
      </div>
      {msg && <p className="accent">{msg}</p>}
      <ErrorLine error={error} />
      {(!d.mailerSet || !d.postalAddressSet) && (
        <Panel kicker="Before anything is delivered" title="Two settings missing">
          <ul className="text-sm grid gap-1 muted">
            {!d.mailerSet && <li>- <b>MAILER_TOKEN</b>: the key your mail server uses to collect the queue. Until the server runs, messages wait in the queue; nothing is lost.</li>}
            {!d.postalAddressSet && <li>- <b>MAIL_POSTAL_ADDRESS</b>: the law (CAN-SPAM) requires a postal address in marketing email. Campaigns and sequences are refused until it is set; confirmations and receipts still go.</li>}
          </ul>
        </Panel>
      )}

      <Panel title={`Subscribers: ${n(d.subscribers.length)} (${n(mailable)} can get updates)`}>
        <div className="flex flex-wrap gap-2 text-sm mb-3">
          {["all", "confirmed", "unconfirmed", "unsubscribed", "bounced", "complained"].map((s) => (
            <button key={s} className={filter === s ? "btn !py-1" : "btn-ghost !py-1"} onClick={() => setFilter(s)}>{s} {s === "all" ? d.subscribers.length : counts[s] || 0}</button>
          ))}
        </div>
        <div className="flex flex-wrap gap-2 text-sm mb-3 items-center">
          <span className="muted">{picked.size} picked</span>
          <input className="field !w-40" placeholder="tag" value={tag} onChange={(e) => setTag(e.target.value)} />
          <button className="btn-ghost !py-1" disabled={!tag || !picked.size} onClick={() => act(() => api("/admin/tags", { body: { tag, ids: [...picked] } }), `Tagged ${picked.size}.`)}>Add tag</button>
          <button className="btn-ghost !py-1" disabled={!tag || !picked.size} onClick={() => act(() => api("/admin/tags", { body: { tag, ids: [...picked], remove: true } }), `Untagged ${picked.size}.`)}>Remove tag</button>
          <a className="btn-ghost !py-1" href="/api/admin/subscribers?format=csv">CSV</a>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="muted text-left"><th></th><th className="py-1">Email</th><th>Status</th><th>Came from</th><th>Tags</th><th>Joined</th></tr></thead>
            <tbody>{shown.slice(0, 300).map((s) => (
              <tr key={s.id} className="border-t" style={{ borderColor: "var(--line)" }}>
                <td><input type="checkbox" checked={picked.has(s.id)} onChange={(e) => { const p = new Set(picked); if (e.target.checked) p.add(s.id); else p.delete(s.id); setPicked(p); }} /></td>
                <td className="py-1">{s.email}{s.name ? <span className="muted"> ({s.name})</span> : null}</td>
                <td>{s.status}{s.marketing_consent ? "" : <span className="muted"> - no updates</span>}</td>
                <td>{s.first_source || s.source}{s.first_campaign ? <span className="muted"> / {s.first_campaign}</span> : null}</td>
                <td className="muted">{s.tags || ""}</td>
                <td className="muted">{s.created_at.slice(0, 10)}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </Panel>

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="New campaign">
          <form className="grid gap-2 text-sm" onSubmit={(e) => { e.preventDefault(); void act(() => api("/admin/campaigns", { body: { ...c, tags: c.tags.split(",").map((t) => t.trim()).filter(Boolean) } }), "Saved as a draft. Test it, then queue it."); }}>
            <input className="field" required placeholder="Name (for you)" value={c.name} onChange={(e) => setC({ ...c, name: e.target.value })} />
            <select className="field" value={c.identity} onChange={(e) => setC({ ...c, identity: e.target.value })}>
              {d.identities.map((i) => <option key={i.key} value={i.key}>{i.from_name} &lt;{i.from_email}&gt;</option>)}
            </select>
            <input className="field" required placeholder="Subject" value={c.subject} onChange={(e) => setC({ ...c, subject: e.target.value })} />
            <textarea className="field" rows={9} required placeholder="Plain text. Blank line = new paragraph. Links are tracked." value={c.body} onChange={(e) => setC({ ...c, body: e.target.value })} />
            <p className="text-xs muted">Tokens: {TOKENS}. The unsubscribe line and your postal address are added for you.</p>
            <div className="grid grid-cols-2 gap-2">
              <input className="field" placeholder="Only these tags (comma)" value={c.tags} onChange={(e) => setC({ ...c, tags: e.target.value })} />
              <input className="field" placeholder="Only this first source" value={c.source} onChange={(e) => setC({ ...c, source: e.target.value })} />
            </div>
            <button className="btn">Save draft</button>
          </form>
        </Panel>
        <Panel title="Campaigns">
          <ul className="grid gap-2 text-sm">
            {d.campaigns.map((x) => (
              <li key={x.id} className="panel-2 p-3 grid gap-1">
                <div className="flex justify-between gap-2"><b>{x.name}</b><span className="muted">{x.status}</span></div>
                <span className="muted">{x.identity}@ - "{x.subject}"</span>
                {x.status === "queued" ? <span className="num">queued {x.queued_count} - sent {x.sent} - opened {x.opened} - clicked {x.clicked}</span> : (
                  <div className="flex gap-2">
                    <button className="btn-ghost !py-1" onClick={() => act(() => api(`/admin/campaigns/${x.id}/test`, { body: {} }), "A test copy is queued to you.")}>Test to me</button>
                    <button className="btn !py-1" onClick={() => { if (confirm(`Queue "${x.subject}" to everyone in its segment?`)) void act(() => api(`/admin/campaigns/${x.id}/queue`, { body: {} }), "Queued."); }}>Queue to segment</button>
                  </div>
                )}
              </li>
            ))}
            {!d.campaigns.length && <li className="muted">No campaigns yet.</li>}
          </ul>
        </Panel>
      </div>

      <Panel title="Sequences">
        {d.sequences.map((q) => (
          <div key={q.key} className="grid gap-3 mb-4">
            <div className="flex flex-wrap items-center gap-3">
              <b>{q.name}</b><span className="muted text-sm">starts when someone {q.trigger === "sample" ? "gets the sample (and asked for updates)" : `does: ${q.trigger}`} - {q.active_runs} running</span>
              <button className={q.active ? "btn !py-1" : "btn-ghost !py-1"} onClick={() => act(() => api(`/admin/sequences/${q.key}`, { method: "PATCH", body: { active: !q.active } }), q.active ? "Switched off." : "Switched on.")}>{q.active ? "On - switch off" : "Off - switch on"}</button>
            </div>
            {d.steps.filter((s) => s.sequence === q.key).map((s) => <StepEditor key={s.step} s={s} onSaved={load} />)}
          </div>
        ))}
      </Panel>

      <Panel title="Sending identities">
        <ul className="grid gap-2 text-sm">
          {d.identities.map((i) => (
            <li key={i.key} className="panel-2 p-3"><b>{i.from_name} &lt;{i.from_email}&gt;</b><span className="block muted">{i.purpose}</span>
              <span className="block muted">Replies to {i.reply_to || i.from_email}; a copy of every message to {i.archive_bcc || "nowhere"}.</span></li>
          ))}
        </ul>
        <p className="text-xs muted mt-3">The queue: {d.outbox.map((o) => `${o.kind} ${o.status} ${o.n}`).join(", ") || "empty"}.</p>
      </Panel>
    </div>
  );
}
