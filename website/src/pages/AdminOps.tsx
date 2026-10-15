// Automations: the site's own work, done while the owner is away. Notices (the inbox), the
// assistant (questions answered only from counted numbers), the automations themselves (when
// THIS happens, do THESE), the log of every job they ran, Workers AI's use, and the audit trail.

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import AdminNav from "../components/AdminNav";
import { ErrorLine, Panel } from "../components/ui";
import { api, n } from "../lib/api";
import { isStaff, useSession } from "../lib/session";

interface Automation { id: number; name: string; description: string | null; trigger: string; conditions: string; actions: string; delay_minutes: number; active: number; runs: number; last_run_at: string | null; created_by: string | null }
interface Job { id: number; label: string; status: string; attempts: number; run_at: string; finished_at: string | null; result: string | null; error: string | null; event: string | null }
interface Notice { id: number; level: string; title: string; body: string | null; link: string | null; created_at: string; read_at: string | null }
interface Audit { id: number; ts: string; actor_kind: string; actor_name: string | null; action: string; target: string | null; detail: string | null }
interface Data {
  triggers: Record<string, string>; actions: Record<string, { label: string; fields: Record<string, string> }>;
  automations: Automation[]; jobs: Job[]; notices: Notice[]; unread: number; events: { type: string; n: number; last: string }[];
  ai: { connected: boolean; model: string; usage: { purpose: string; calls: number; ok: number; ms: number }[] };
  clock: { last: string | null; running: boolean; tokenSet: boolean }; audit: Audit[];
}
interface Act { type: string; [k: string]: unknown }
interface Draft { id?: number; name: string; description: string; trigger: string; conditions: [string, string][]; actions: Act[]; delayMinutes: string; active: boolean }

const when = (s: string | null) => (s ? s.slice(0, 16).replace("T", " ") : "--");
const ember = { color: "var(--color-ember)" };

function toDraft(a?: Automation): Draft {
  if (!a) return { name: "", description: "", trigger: "order.paid", conditions: [], actions: [{ type: "notify", title: "", body: "" }], delayMinutes: "0", active: true };
  return { id: a.id, name: a.name, description: a.description || "", trigger: a.trigger, conditions: Object.entries(JSON.parse(a.conditions || "{}")).map(([k, v]) => [k, String(v)]),
    actions: JSON.parse(a.actions), delayMinutes: String(a.delay_minutes), active: Boolean(a.active) };
}

function Editor({ d, data, onDone, onCancel }: { d: Draft; data: Data; onDone: () => void; onCancel: () => void }) {
  const [x, setX] = useState<Draft>(d);
  const [error, setError] = useState<string | null>(null);
  const setAct = (i: number, patch: Partial<Act>) => setX({ ...x, actions: x.actions.map((a, j) => (j === i ? { ...a, ...patch } as Act : a)) });
  async function save(e: React.FormEvent) {
    e.preventDefault();
    const payload = { name: x.name, description: x.description, trigger: x.trigger, delayMinutes: Number(x.delayMinutes) || 0, active: x.active,
      conditions: Object.fromEntries(x.conditions.filter(([k]) => k.trim()).map(([k, v]) => [k.trim(), v])), actions: x.actions };
    try {
      if (x.id) await api(`/admin/automations/${x.id}`, { method: "PATCH", body: payload });
      else await api("/admin/automations", { body: payload });
      onDone();
    } catch (err) { setError((err as Error).message); }
  }
  return (
    <form onSubmit={save} className="panel-2 p-4 grid gap-3 text-sm">
      <div className="grid gap-2 sm:grid-cols-2">
        <label className="grid gap-1">Name<input className="field" required minLength={2} value={x.name} onChange={(e) => setX({ ...x, name: e.target.value })} /></label>
        <label className="grid gap-1">When this happens
          <select className="field" value={x.trigger} onChange={(e) => setX({ ...x, trigger: e.target.value })}>{Object.keys(data.triggers).map((t) => <option key={t}>{t}</option>)}</select>
        </label>
      </div>
      <p className="muted">{data.triggers[x.trigger]}</p>
      <label className="grid gap-1">What it is for (for you)<input className="field" value={x.description} onChange={(e) => setX({ ...x, description: e.target.value })} /></label>
      <div className="grid gap-1">
        <span>Only when these fields match <span className="muted">(none = every time; a field ending _min means "at least")</span></span>
        {x.conditions.map(([k, v], i) => (
          <div key={i} className="flex gap-2">
            <input className="field" placeholder="field, e.g. source" value={k} onChange={(e) => setX({ ...x, conditions: x.conditions.map((c, j) => (j === i ? [e.target.value, c[1]] : c)) })} />
            <input className="field" placeholder="value, e.g. youtube" value={v} onChange={(e) => setX({ ...x, conditions: x.conditions.map((c, j) => (j === i ? [c[0], e.target.value] : c)) })} />
            <button type="button" className="btn-ghost !py-1" onClick={() => setX({ ...x, conditions: x.conditions.filter((_, j) => j !== i) })}>Remove</button>
          </div>
        ))}
        <button type="button" className="btn-ghost !py-1 justify-self-start" onClick={() => setX({ ...x, conditions: [...x.conditions, ["", ""]] })}>Add a condition</button>
      </div>
      <div className="grid gap-2">
        <span>Do these, in order</span>
        {x.actions.map((a, i) => (
          <div key={i} className="grid gap-2 p-3 rounded-lg" style={{ border: "1px solid var(--line)" }}>
            <div className="flex gap-2">
              <select className="field" value={a.type} onChange={(e) => setAct(i, { type: e.target.value })}>{Object.entries(data.actions).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}</select>
              <button type="button" className="btn-ghost !py-1" onClick={() => setX({ ...x, actions: x.actions.filter((_, j) => j !== i) })}>Remove</button>
            </div>
            {Object.entries(data.actions[a.type]?.fields || {}).map(([field, help]) => field === "email" ? (
              <label key={field} className="flex gap-2 items-center"><input type="checkbox" checked={a[field] === true} onChange={(e) => setAct(i, { [field]: e.target.checked })} /><span className="muted">{help}</span></label>
            ) : (
              <label key={field} className="grid gap-1"><span className="muted">{field}: {help}</span>
                {field === "body" || field === "brief"
                  ? <textarea className="field" rows={3} value={String(a[field] ?? "")} onChange={(e) => setAct(i, { [field]: e.target.value })} />
                  : <input className="field" value={String(a[field] ?? "")} onChange={(e) => setAct(i, { [field]: e.target.value })} />}
              </label>
            ))}
          </div>
        ))}
        <button type="button" className="btn-ghost !py-1 justify-self-start" onClick={() => setX({ ...x, actions: [...x.actions, { type: "notify", title: "", body: "" }] })}>Add an action</button>
      </div>
      <div className="flex flex-wrap gap-4 items-center">
        <label className="flex gap-2 items-center">Wait<input className="field !w-24" type="number" min="0" value={x.delayMinutes} onChange={(e) => setX({ ...x, delayMinutes: e.target.value })} />minutes first</label>
        <label className="flex gap-2 items-center"><input type="checkbox" checked={x.active} onChange={(e) => setX({ ...x, active: e.target.checked })} />Switched on</label>
      </div>
      <div className="flex gap-2"><button className="btn">Save</button><button type="button" className="btn-ghost" onClick={onCancel}>Cancel</button></div>
      <ErrorLine error={error} />
    </form>
  );
}

export default function AdminOps() {
  const { me } = useSession();
  const [d, setD] = useState<Data | null>(null);
  const [editing, setEditing] = useState<Draft | null>(null);
  const [q, setQ] = useState({ question: "", days: "30" });
  const [answer, setAnswer] = useState<{ answer: string; numbers: string } | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(() => api<Data>("/admin/ops").then(setD).catch((e) => setError(e.message)), []);
  useEffect(() => { if (isStaff(me)) void load(); }, [me, load]);
  if (!isStaff(me)) return <div className="mx-auto max-w-xl px-4 py-10 muted">Admins only.</div>;
  if (!d) return <div className="mx-auto max-w-xl px-4 py-10 muted">{error || "Loading..."}</div>;
  const act = async (label: string, fn: () => Promise<unknown>, done: string) => {
    setError(null); setMsg(null); setBusy(label);
    try { await fn(); setMsg(done); await load(); } catch (e) { setError((e as Error).message); } finally { setBusy(null); }
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 grid gap-6">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">The site's own work</p>
        <h1 className="text-4xl font-bold">Automations</h1>
      </div>
      <AdminNav />
      {msg && <p className="accent">{msg}</p>}
      <ErrorLine error={error} />

      <div className="grid gap-3 sm:grid-cols-3 text-sm">
        <div className="panel-2 p-3"><b>The clock</b><p className={d.clock.running ? "accent" : "muted"}>{d.clock.running ? `Running; last ${when(d.clock.last)} UTC` : d.clock.last ? `Stopped; last ${when(d.clock.last)} UTC` : "Not running yet"}</p>
          {!d.clock.running && <p className="muted text-xs">{d.clock.tokenSet ? "Deploy the zeanahlab-ops Worker (SETUP.md step 10)." : "OPS_TOKEN is not set on the site (SETUP.md step 10)."}</p>}
          <button className="btn-ghost !py-1 mt-2" disabled={busy === "clock"} onClick={() => act("clock", async () => { const r = await api<{ fired: string[]; ran: number; sequenceMail: number }>("/ops/clock", { body: {} }); setMsg(`Ran: ${r.ran} jobs, ${r.sequenceMail} sequence messages queued${r.fired.length ? `, fired ${r.fired.join(", ")}` : ""}.`); }, "")}>Run it now</button></div>
        <div className="panel-2 p-3"><b>Workers AI</b><p className={d.ai.connected ? "accent" : "muted"}>{d.ai.connected ? "Connected" : "Not connected"}</p><p className="muted text-xs break-all">{d.ai.model}</p>
          <p className="muted text-xs">Last 30 days: {n(d.ai.usage.reduce((s, u) => s + u.calls, 0))} calls</p></div>
        <div className="panel-2 p-3"><b>Notices</b><p className={d.unread ? "accent" : "muted"}>{d.unread} unread</p><p className="muted text-xs">Events in 30 days: {n(d.events.reduce((s, e) => s + e.n, 0))}</p></div>
      </div>

      <Panel title="Notices" kicker="Your inbox on the site">
        {d.unread > 0 && <button className="btn-ghost !py-1 mb-3" onClick={() => act("read", () => api("/admin/notices/read", { body: { all: true } }), "All marked read.")}>Mark all read</button>}
        {!d.notices.length && <p className="muted text-sm">Nothing yet. Sales, agent proposals, listings that look like spam, the Monday report and any failures will appear here.</p>}
        <div className="grid gap-2">
          {d.notices.map((x) => (
            <details key={x.id} className={`panel-2 p-3 text-sm ${x.read_at ? "opacity-70" : ""}`} onToggle={(e) => { if ((e.target as HTMLDetailsElement).open && !x.read_at) void api("/admin/notices/read", { body: { ids: [x.id] } }); }}>
              <summary className="cursor-pointer"><span style={x.level === "warning" ? ember : undefined} className={x.level === "action" ? "accent font-semibold" : "font-semibold"}>{x.title}</span> <span className="muted">{when(x.created_at)}</span></summary>
              {x.body && <pre className="whitespace-pre-wrap font-sans mt-2 muted">{x.body}</pre>}
              {x.link && <Link className="underline text-xs" to={x.link}>Open</Link>}
            </details>
          ))}
        </div>
      </Panel>

      <Panel title="Ask about your numbers" kicker="Assistant">
        <form className="grid gap-2 text-sm" onSubmit={(e) => { e.preventDefault(); void act("ask", async () => setAnswer(await api("/admin/assistant", { body: { question: q.question, days: Number(q.days) } })), ""); }}>
          <textarea className="field" rows={2} required minLength={3} placeholder="e.g. Where are buyers coming from, and where do people drop off?" value={q.question} onChange={(e) => setQ({ ...q, question: e.target.value })} />
          <div className="flex gap-2 items-center">
            <select className="field !w-auto" value={q.days} onChange={(e) => setQ({ ...q, days: e.target.value })}>{["7", "30", "90", "365"].map((x) => <option key={x} value={x}>last {x} days</option>)}</select>
            <button className="btn" disabled={busy === "ask" || !d.ai.connected}>{busy === "ask" ? "Reading the numbers..." : "Ask"}</button>
          </div>
        </form>
        {answer && (
          <div className="grid gap-3 mt-4 text-sm md:grid-cols-2">
            <div className="panel-2 p-3"><b>Workers AI's answer</b><p className="muted text-xs mb-2">Written from the counted numbers beside it. It can be wrong; the numbers are not.</p><p className="whitespace-pre-wrap">{answer.answer}</p></div>
            <div className="panel-2 p-3"><b>The numbers it was given (counted)</b><pre className="whitespace-pre-wrap font-sans muted mt-2">{answer.numbers}</pre></div>
          </div>
        )}
      </Panel>

      <Panel title="Automations" kicker="When this happens, do these">
        {editing ? <Editor d={editing} data={d} onCancel={() => setEditing(null)} onDone={() => { setEditing(null); setMsg("Saved."); void load(); }} />
          : <button className="btn mb-4" onClick={() => setEditing(toDraft())}>New automation</button>}
        <div className="grid gap-3 mt-3">
          {d.automations.map((a) => (
            <div key={a.id} className={`panel-2 p-3 text-sm grid gap-1 ${a.active ? "" : "opacity-70"}`}>
              <div className="flex flex-wrap gap-2 items-center justify-between">
                <span><b>{a.name}</b> <code className="text-xs muted">{a.trigger}{a.delay_minutes ? ` + ${a.delay_minutes} min` : ""}</code></span>
                <span className="flex gap-2 flex-wrap">
                  <button className="btn-ghost !py-1 !px-2" onClick={() => act(`t${a.id}`, () => api(`/admin/automations/${a.id}`, { method: "PATCH", body: { active: !a.active } }), a.active ? "Switched off." : "Switched on.")}>{a.active ? "Switch off" : "Switch on"}</button>
                  <button className="btn-ghost !py-1 !px-2" disabled={busy === `x${a.id}`} onClick={() => act(`x${a.id}`, async () => {
                    const r = await api<{ job: { status: string; result: string | null; error: string | null } }>(`/admin/automations/${a.id}/test`, { body: {} });
                    const steps = JSON.parse(r.job.result || "[]") as { type: string; note: string }[];
                    setMsg(`Test: ${r.job.status}. ${steps.map((s) => `${s.type}: ${s.note}`).join(" | ")}`);
                  }, "")}>{busy === `x${a.id}` ? "Testing..." : "Test now"}</button>
                  <button className="btn-ghost !py-1 !px-2" onClick={() => setEditing(toDraft(a))}>Edit</button>
                  <button className="btn-ghost !py-1 !px-2" onClick={() => { if (confirm(`Delete "${a.name}"?`)) void act(`d${a.id}`, () => api(`/admin/automations/${a.id}`, { method: "DELETE" }), "Deleted."); }}>Delete</button>
                </span>
              </div>
              {a.description && <p className="muted">{a.description}</p>}
              <p className="text-xs muted">{(JSON.parse(a.actions) as Act[]).map((x) => d.actions[x.type]?.label || x.type).join(" -> ")}
                {a.conditions !== "{}" && <> | only when {a.conditions}</>} | ran {n(a.runs)} times, last {when(a.last_run_at)}</p>
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="Jobs, newest first">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-left muted"><th className="py-1 pr-3">#</th><th className="pr-3">Automation</th><th className="pr-3">Event</th><th className="pr-3">State</th><th className="pr-3">When (UTC)</th><th>What happened</th></tr></thead>
            <tbody>
              {d.jobs.map((j) => (
                <tr key={j.id} style={{ borderTop: "1px solid var(--line)" }} className="align-top">
                  <td className="py-1 pr-3">{j.id}</td><td className="pr-3">{j.label}</td><td className="pr-3"><code className="text-xs">{j.event}</code></td>
                  <td className="pr-3" style={j.status === "failed" ? ember : undefined}>{j.status}{j.attempts > 1 ? ` (${j.attempts} tries)` : ""}
                    {["failed", "cancelled"].includes(j.status) && <button className="underline ml-2 text-xs" onClick={() => act(`r${j.id}`, () => api(`/admin/jobs/${j.id}/retry`, { body: {} }), "Retried.")}>retry</button>}
                    {j.status === "queued" && <button className="underline ml-2 text-xs" onClick={() => act(`c${j.id}`, () => api(`/admin/jobs/${j.id}/cancel`, { body: {} }), "Cancelled.")}>cancel</button>}</td>
                  <td className="pr-3 whitespace-nowrap">{when(j.finished_at || j.run_at)}</td>
                  <td className="muted text-xs">{(JSON.parse(j.result || "[]") as { type: string; ok: boolean; note: string }[]).map((s, i) => <div key={i} style={s.ok ? undefined : ember}>{s.type}: {s.note}</div>)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!d.jobs.length && <p className="muted text-sm">No jobs yet.</p>}
        </div>
      </Panel>

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="Events, last 30 days">
          {!d.events.length && <p className="muted text-sm">None yet.</p>}
          {d.events.map((e) => <div key={e.type} className="flex justify-between text-sm"><code className="text-xs">{e.type}</code><span>{n(e.n)} <span className="muted text-xs">last {when(e.last)}</span></span></div>)}
        </Panel>
        <Panel title="Workers AI, last 30 days">
          {!d.ai.usage.length && <p className="muted text-sm">No calls yet.</p>}
          {d.ai.usage.map((u) => <div key={u.purpose} className="flex justify-between text-sm"><span>{u.purpose}</span><span>{n(u.calls)} calls, {n(u.calls - u.ok)} failed, {(u.ms / Math.max(1, u.calls) / 1000).toFixed(1)} s each</span></div>)}
          <p className="muted text-xs mt-2">Cloudflare bills Workers AI in neurons; see the Workers AI page of your Cloudflare dashboard for the day's count.</p>
        </Panel>
      </div>

      <Panel title="Audit log" kicker="Who changed what">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-left muted"><th className="py-1 pr-3">When (UTC)</th><th className="pr-3">Who</th><th className="pr-3">Did</th><th className="pr-3">To</th><th>Detail</th></tr></thead>
            <tbody>
              {d.audit.map((x) => (
                <tr key={x.id} style={{ borderTop: "1px solid var(--line)" }} className="align-top">
                  <td className="py-1 pr-3 whitespace-nowrap">{when(x.ts)}</td><td className="pr-3">{x.actor_kind}{x.actor_name ? `: ${x.actor_name}` : ""}</td>
                  <td className="pr-3"><code className="text-xs">{x.action}</code></td><td className="pr-3">{x.target}</td><td className="muted text-xs break-all">{x.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!d.audit.length && <p className="muted text-sm">Nothing yet.</p>}
        </div>
      </Panel>
    </div>
  );
}
