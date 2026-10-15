// Members: find any account; see its devices, orders, listings, list status and history;
// suspend or restore it, sign it out everywhere, make a password-reset link, or delete it.
// Every act is written to the audit log.

import { useCallback, useEffect, useState } from "react";
import AdminNav from "../components/AdminNav";
import { ErrorLine, Panel } from "../components/ui";
import { api, money, n } from "../lib/api";
import { isStaff, useSession } from "../lib/session";

interface Row { id: number; email: string; display_name: string; role: string; status: string; created_at: string; last_seen_at: string | null; email_verified_at: string | null; orders: number; spent_cents: number; listings: number; sessions: number; list_status: string | null; city: string | null; country: string | null }
interface Detail {
  user: { id: number; email: string; displayName: string; role: string; status: string; suspendedReason: string | null; adminNote: string | null; lastSeenAt: string | null; emailVerifiedAt: string | null; isAdmin: boolean; createdAt: string; city: string; region: string; country: string; publicProfile: boolean };
  list: { status: string; marketing_consent: number; first_source: string | null; first_campaign: string | null; tags: string[] } | null;
  sessions: { id: string; created_at: string; last_seen_at: string | null; user_agent: string | null; country: string | null }[];
  orders: { ref: string; product: string; amount_cents: number; status: string; fulfillment: string | null; created_at: string }[];
  listings: { id: number; kind: string; title: string; visible: number }[];
  logins: { ok: number; ts: string }[];
  audit: { ts: string; actor_kind: string; actor_name: string | null; action: string; detail: string | null }[];
}

const when = (s: string | null) => (s ? s.slice(0, 16).replace("T", " ") : "--");

function Member({ id, onChanged, owner }: { id: number; onChanged: () => void; owner: boolean }) {
  const [d, setD] = useState<Detail | null>(null);
  const [note, setNote] = useState("");
  const [reason, setReason] = useState("");
  const [link, setLink] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(() => api<Detail>(`/admin/users/${id}`).then((r) => { setD(r); setNote(r.user.adminNote || ""); }).catch((e) => setError(e.message)), [id]);
  useEffect(() => { void load(); }, [load]);
  if (!d) return <p className="muted text-sm">{error || "Loading..."}</p>;
  const u = d.user;
  const hands = owner || u.role === "member";   // a manager acts on members only
  const act = async (fn: () => Promise<unknown>, done: string) => { setError(null); setMsg(null); try { await fn(); setMsg(done); await load(); onChanged(); } catch (e) { setError((e as Error).message); } };
  return (
    <div className="grid gap-4 text-sm">
      <div>
        <h3 className="text-2xl font-semibold">{u.displayName} {u.isAdmin ? <span className="accent text-sm">owner</span> : u.role === "manager" && <span className="accent text-sm">manager</span>}</h3>
        <p className="muted">{u.email} -- joined {when(u.createdAt)}, last seen {when(u.lastSeenAt)} -- email {u.emailVerifiedAt ? "confirmed" : "not confirmed"}</p>
        <p className="muted">{[u.city, u.region, u.country].filter(Boolean).join(", ") || "no place given"}; profile {u.publicProfile ? "public" : "private"}</p>
        {u.status === "suspended" && <p style={{ color: "var(--color-ember)" }}>Suspended{u.suspendedReason ? `: ${u.suspendedReason}` : ""}</p>}
      </div>
      {msg && <p className="accent">{msg}</p>}
      <ErrorLine error={error} />
      {owner && !u.isAdmin && (
        <div className="panel-2 p-3 flex flex-wrap gap-3 items-center">
          {u.role === "manager"
            ? <><span>Manager: can open every admin page and do the day's work, but cannot make managers, make agent keys, delete accounts, or change another manager's account.</span>
                <button className="btn-ghost !py-1.5" onClick={() => act(() => api(`/admin/users/${id}/role`, { body: { role: "member" } }), "Now a member.")}>Make a member again</button></>
            : <><span className="muted">Give this person the admin pages, short of making managers, agent keys and deleting accounts.</span>
                <button className="btn-ghost !py-1.5" onClick={() => { if (confirm(`Make ${u.email} a manager?`)) void act(() => api(`/admin/users/${id}/role`, { body: { role: "manager" } }), "Now a manager."); }}>Make a manager</button></>}
        </div>
      )}
      {!hands && <p className="muted">Only the owner can change a manager's account.</p>}
      {hands && <div className="flex flex-wrap gap-2">
        {u.status === "suspended"
          ? <button className="btn-ghost !py-1.5" onClick={() => act(() => api(`/admin/users/${id}`, { method: "PATCH", body: { status: "active" } }), "Restored.")}>Restore the account</button>
          : !u.isAdmin && <span className="flex gap-2"><input className="field !w-56" placeholder="Reason (they will see it)" value={reason} onChange={(e) => setReason(e.target.value)} />
            <button className="btn-ghost !py-1.5" onClick={() => { if (confirm(`Suspend ${u.email}? They are signed out at once and cannot sign in.`)) void act(() => api(`/admin/users/${id}`, { method: "PATCH", body: { status: "suspended", reason } }), "Suspended and signed out."); }}>Suspend</button></span>}
        <button className="btn-ghost !py-1.5" onClick={() => act(() => api(`/admin/users/${id}/signout`, { body: {} }), "Signed out everywhere.")}>Sign out everywhere</button>
        <button className="btn-ghost !py-1.5" onClick={() => act(async () => setLink((await api<{ link: string }>(`/admin/users/${id}/reset-link`, { body: {} })).link), "Reset link made (and queued by email).")}>Make a reset link</button>
        <button className="btn-ghost !py-1.5" onClick={() => act(() => api(`/admin/users/${id}`, { method: "PATCH", body: { emailVerified: !u.emailVerifiedAt } }), "Changed.")}>{u.emailVerifiedAt ? "Mark email unconfirmed" : "Mark email confirmed"}</button>
      </div>}
      {link && <div className="panel-2 p-3"><b>Reset link</b> (works once, 24 hours; send it only to {u.email}):<br /><code className="break-all select-all text-xs">{link}</code></div>}
      <label className="grid gap-1">Your note (never shown to them)
        <textarea className="field" rows={2} value={note} onChange={(e) => setNote(e.target.value)} />
        <button className="btn-ghost !py-1 justify-self-start" onClick={() => act(() => api(`/admin/users/${id}`, { method: "PATCH", body: { adminNote: note } }), "Note saved.")}>Save note</button>
      </label>
      <div className="grid gap-4 md:grid-cols-2">
        <div><b>Signed in on</b>{d.sessions.map((s) => <p key={s.id} className="muted">{s.user_agent || "a device"}{s.country ? `, ${s.country}` : ""} -- last {when(s.last_seen_at || s.created_at)}</p>)}{!d.sessions.length && <p className="muted">nowhere</p>}</div>
        <div><b>The list</b>{d.list ? <p className="muted">{d.list.status}, updates {d.list.marketing_consent ? "yes" : "no"}; came from {d.list.first_source || "?"}{d.list.first_campaign ? ` / ${d.list.first_campaign}` : ""}; tags: {d.list.tags.join(", ") || "none"}</p> : <p className="muted">not on it</p>}</div>
        <div><b>Orders</b>{d.orders.map((o) => <p key={o.ref} className="muted">{o.ref} {o.product} {money(o.amount_cents)} {o.status}{o.fulfillment ? ` / ${o.fulfillment}` : ""} -- {when(o.created_at)}</p>)}{!d.orders.length && <p className="muted">none</p>}</div>
        <div><b>Network listings</b>{d.listings.map((l) => <p key={l.id} className="muted">#{l.id} {l.kind}: {l.title}{l.visible ? "" : " (hidden)"}</p>)}{!d.listings.length && <p className="muted">none</p>}</div>
        <div><b>Recent sign-ins</b>{d.logins.slice(0, 8).map((l, i) => <p key={i} className="muted">{when(l.ts)} {l.ok ? "ok" : "wrong password"}</p>)}{!d.logins.length && <p className="muted">none recorded</p>}</div>
        <div><b>History</b>{d.audit.map((a, i) => <p key={i} className="muted">{when(a.ts)} {a.action} by {a.actor_name || a.actor_kind}</p>)}{!d.audit.length && <p className="muted">nothing</p>}</div>
      </div>
      {owner && !u.isAdmin && (
        <details className="panel-2 p-3">
          <summary className="cursor-pointer" style={{ color: "var(--color-ember)" }}>Delete this account</summary>
          <form className="grid gap-2 mt-2" onSubmit={(e) => { e.preventDefault(); const c = (e.currentTarget.elements.namedItem("confirm") as HTMLInputElement).value; void act(() => api(`/admin/users/${id}`, { method: "DELETE", body: { confirm: c } }), "Deleted."); }}>
            <p className="muted">Removes the account, its listings and life account. Orders stay (for the books), without the link to the account. Their list entry is kept but stops getting updates.</p>
            <input name="confirm" className="field" placeholder={`Type ${u.email} to confirm`} />
            <button className="btn-ghost !py-1 justify-self-start">Delete for good</button>
          </form>
        </details>
      )}
    </div>
  );
}

export default function AdminUsers() {
  const { me } = useSession();
  const [rows, setRows] = useState<Row[] | null>(null);
  const [meta, setMeta] = useState<{ counts: { status: string; n: number }[]; active7: number }>({ counts: [], active7: 0 });
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [open, setOpen] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(() => api<{ users: Row[]; counts: { status: string; n: number }[]; active7: number }>(`/admin/users?q=${encodeURIComponent(q)}&status=${status}`)
    .then((r) => { setRows(r.users); setMeta(r); }).catch((e) => setError(e.message)), [q, status]);
  useEffect(() => { if (isStaff(me)) { const t = setTimeout(() => void load(), 250); return () => clearTimeout(t); } }, [me, load]);
  if (!isStaff(me)) return <div className="mx-auto max-w-xl px-4 py-10 muted">Admins only.</div>;
  const total = meta.counts.reduce((s, c) => s + c.n, 0);
  return (
    <div className="mx-auto max-w-6xl px-4 py-10 grid gap-6">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">Accounts</p>
        <h1 className="text-4xl font-bold">Members</h1>
      </div>
      <AdminNav />
      <ErrorLine error={error} />
      <Panel title={`${n(total)} accounts, ${n(meta.active7)} seen this week`}>
        <div className="flex flex-wrap gap-2 mb-4 text-sm">
          <input className="field !w-64" placeholder="Search name or email" value={q} onChange={(e) => setQ(e.target.value)} />
          <select className="field !w-auto" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">everyone</option>
            {meta.counts.map((c) => <option key={c.status} value={c.status}>{c.status} ({c.n})</option>)}
          </select>
        </div>
        <div className="grid gap-2">
          {rows?.map((r) => (
            <div key={r.id} className="panel-2 p-3 text-sm">
              <button className="w-full text-left flex flex-wrap gap-x-4 gap-y-1 items-baseline" onClick={() => setOpen(open === r.id ? null : r.id)} aria-expanded={open === r.id}>
                <b>{r.display_name}</b><span className="muted">{r.email}</span>
                {r.role === "admin" && <span className="accent text-xs">owner</span>}{r.role === "manager" && <span className="accent text-xs">manager</span>}
                {r.status === "suspended" && <span className="text-xs" style={{ color: "var(--color-ember)" }}>suspended</span>}
                <span className="muted text-xs ml-auto">{r.orders ? `${r.orders} orders, ${money(r.spent_cents)}; ` : ""}{r.listings ? `${r.listings} listings; ` : ""}{r.sessions} devices; seen {when(r.last_seen_at)}</span>
              </button>
              {open === r.id && <div className="mt-4 pt-4" style={{ borderTop: "1px solid var(--line)" }}><Member id={r.id} owner={me?.role === "admin"} onChanged={() => void load()} /></div>}
            </div>
          ))}
          {rows && !rows.length && <p className="muted text-sm">No accounts match.</p>}
          {!rows && <p className="muted text-sm">Loading...</p>}
        </div>
      </Panel>
    </div>
  );
}
