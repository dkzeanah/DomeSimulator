// Agents and keys: give an LLM or a script its own key with only the scopes it needs, see
// every call it made, and approve or reject what it proposes. Nothing an agent does sends
// mail or changes a price without the owner's click here.

import { useCallback, useEffect, useState } from "react";
import AdminNav from "../components/AdminNav";
import { ErrorLine, Panel } from "../components/ui";
import { api, n } from "../lib/api";
import { useSession } from "../lib/session";

interface Key { id: number; name: string; prefix: string; scopes: string; rate_per_min: number; created_at: string; expires_at: string | null; last_used_at: string | null; revoked_at: string | null; calls: number }
interface Call { ts: string; method: string; path: string; status: number; note: string | null; name: string | null }
interface Proposal { id: number; key_name: string | null; action: string; payload: string; reason: string | null; status: string; result: string | null; created_at: string; decided_at: string | null }
interface Data { scopes: Record<string, string>; keys: Key[]; calls: Call[]; proposals: Proposal[] }

const day = (s: string | null) => (s ? s.slice(0, 16).replace("T", " ") : "--");

export default function AdminAgents() {
  const { me } = useSession();
  const [d, setD] = useState<Data | null>(null);
  const [f, setF] = useState({ name: "", days: "90", ratePerMin: "30", scopes: new Set<string>(["stats:read", "analytics:read"]) });
  const [made, setMade] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(() => api<Data>("/admin/agents").then(setD).catch((e) => setError(e.message)), []);
  useEffect(() => { if (me?.role === "admin") void load(); }, [me, load]);
  if (me?.role !== "admin") return <div className="mx-auto max-w-xl px-4 py-10 muted">Admins only.</div>;
  if (!d) return <div className="mx-auto max-w-xl px-4 py-10 muted">{error || "Loading..."}</div>;
  const act = async (fn: () => Promise<unknown>, done: string) => { setError(null); setMsg(null); try { await fn(); setMsg(done); await load(); } catch (e) { setError((e as Error).message); } };
  const pending = d.proposals.filter((p) => p.status === "pending");
  const base = typeof window !== "undefined" ? window.location.origin : "https://www.zeanahlab.com";

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 grid gap-6">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">LLMs and scripts, on a short lead</p>
        <h1 className="text-4xl font-bold">Agents and keys</h1>
      </div>
      <AdminNav />
      {msg && <p className="accent">{msg}</p>}
      <ErrorLine error={error} />

      <Panel title={`Waiting for you: ${pending.length}`} kicker="Proposals">
        {!pending.length && <p className="muted text-sm">Nothing is waiting. When an agent (or Workers AI) proposes sending mail, a price change or hiding a listing, it appears here and nothing happens until you decide.</p>}
        <div className="grid gap-3">
          {pending.map((p) => (
            <div key={p.id} className="panel-2 p-3 text-sm grid gap-2">
              <div className="flex flex-wrap gap-2 items-baseline"><b>#{p.id} {p.action}</b><span className="muted">from {p.key_name || "Workers AI"}, {day(p.created_at)}</span></div>
              <code className="text-xs break-all">{p.payload}</code>
              {p.reason && <p className="muted">"{p.reason}"</p>}
              <div className="flex gap-2">
                <button className="btn !py-1.5" onClick={() => act(() => api(`/admin/proposals/${p.id}`, { body: { decision: "approve" } }), `Approved #${p.id}.`)}>Approve and do it</button>
                <button className="btn-ghost !py-1.5" onClick={() => act(() => api(`/admin/proposals/${p.id}`, { body: { decision: "reject" } }), `Rejected #${p.id}.`)}>Reject</button>
              </div>
            </div>
          ))}
        </div>
      </Panel>

      <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
        <Panel title="Make a key">
          <form className="grid gap-3 text-sm" onSubmit={(e) => {
            e.preventDefault();
            void act(async () => {
              const r = await api<{ key: string }>("/admin/agents", { body: { name: f.name, days: Number(f.days) || 0, ratePerMin: Number(f.ratePerMin) || 30, scopes: [...f.scopes] } });
              setMade(r.key);
            }, "Key made. Copy it now -- it will not be shown again.");
          }}>
            <label className="grid gap-1">What it is for<input className="field" required minLength={2} maxLength={80} placeholder="e.g. Claude: weekly numbers" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></label>
            <fieldset className="grid gap-1.5">
              <legend className="mb-1">What it may do</legend>
              {Object.entries(d.scopes).map(([s, why]) => (
                <label key={s} className="flex gap-2 items-start">
                  <input type="checkbox" className="mt-1" checked={f.scopes.has(s)} onChange={(e) => { const x = new Set(f.scopes); if (e.target.checked) x.add(s); else x.delete(s); setF({ ...f, scopes: x }); }} />
                  <span><code className="text-xs">{s}</code> <span className="muted">{why}</span></span>
                </label>
              ))}
            </fieldset>
            <div className="grid grid-cols-2 gap-2">
              <label className="grid gap-1">Expires after (days, 0 = never)<input className="field" type="number" min="0" max="3650" value={f.days} onChange={(e) => setF({ ...f, days: e.target.value })} /></label>
              <label className="grid gap-1">Calls a minute, at most<input className="field" type="number" min="1" max="600" value={f.ratePerMin} onChange={(e) => setF({ ...f, ratePerMin: e.target.value })} /></label>
            </div>
            <button className="btn justify-self-start">Make the key</button>
          </form>
          {made && (
            <div className="panel-2 p-3 mt-4 text-sm grid gap-2">
              <b>The key (shown once):</b>
              <code className="break-all select-all">{made}</code>
              <button className="btn-ghost !py-1 justify-self-start" onClick={() => navigator.clipboard?.writeText(made)}>Copy</button>
              <p className="muted">Give the agent this, and tell it to start with:<br /><code className="text-xs break-all">GET {base}/api/agent/tools</code><br />with the header <code className="text-xs">Authorization: Bearer &lt;key&gt;</code>. That page lists exactly what this key may do, with inputs, so an LLM can use them as tools.</p>
            </div>
          )}
        </Panel>

        <Panel title={`Keys: ${d.keys.filter((k) => !k.revoked_at).length} live`}>
          {!d.keys.length && <p className="muted text-sm">No keys yet.</p>}
          <div className="grid gap-2">
            {d.keys.map((k) => (
              <div key={k.id} className={`panel-2 p-3 text-sm grid gap-1 ${k.revoked_at ? "opacity-60" : ""}`}>
                <div className="flex flex-wrap gap-2 items-baseline justify-between">
                  <span><b>{k.name}</b> <code className="text-xs muted">zl_{k.prefix}_...</code></span>
                  {k.revoked_at ? <span className="muted">revoked {day(k.revoked_at)}</span>
                    : <button className="btn-ghost !py-1 !px-2" onClick={() => { if (confirm(`Revoke "${k.name}"? Anything using it stops at once.`)) void act(() => api(`/admin/agents/${k.id}/revoke`, { body: {} }), "Revoked."); }}>Revoke</button>}
                </div>
                <div className="flex flex-wrap gap-1">{(JSON.parse(k.scopes) as string[]).map((s) => <code key={s} className="text-xs rounded px-1.5" style={{ border: "1px solid var(--line)" }}>{s}</code>)}</div>
                <span className="muted text-xs">{n(k.calls)} calls, last {day(k.last_used_at)}; {k.rate_per_min}/min; expires {k.expires_at ? day(k.expires_at) : "never"}</span>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <Panel title="Every call, newest first">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-left muted"><th className="py-1 pr-3">When (UTC)</th><th className="pr-3">Key</th><th className="pr-3">Call</th><th className="pr-3">Answer</th><th>Note</th></tr></thead>
            <tbody>
              {d.calls.map((c, i) => (
                <tr key={i} style={{ borderTop: "1px solid var(--line)" }}>
                  <td className="py-1 pr-3 whitespace-nowrap">{day(c.ts)}</td><td className="pr-3">{c.name || "unknown key"}</td>
                  <td className="pr-3"><code className="text-xs">{c.method} {c.path}</code></td>
                  <td className="pr-3" style={{ color: c.status >= 400 ? "var(--color-ember)" : undefined }}>{c.status}</td><td className="muted">{c.note || ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!d.calls.length && <p className="muted text-sm">No calls yet.</p>}
        </div>
      </Panel>

      <Panel title="Decided proposals">
        <div className="grid gap-1 text-sm">
          {d.proposals.filter((p) => p.status !== "pending").map((p) => (
            <div key={p.id} className="flex flex-wrap gap-2"><b>#{p.id}</b><span>{p.action}</span><span className="muted">{p.status}</span><span className="muted">{p.result}</span></div>
          ))}
          {!d.proposals.some((p) => p.status !== "pending") && <p className="muted">None yet.</p>}
        </div>
      </Panel>
    </div>
  );
}
