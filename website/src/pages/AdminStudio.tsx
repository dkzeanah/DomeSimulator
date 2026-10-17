// The owner's studio: the first admin page. What the home page leads with, the rolling invite
// codes that set an account's access level, promo codes for friend prices, and giving any
// account a level by hand.

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import AdminNav from "../components/AdminNav";
import { ErrorLine, Panel } from "../components/ui";
import { api, money } from "../lib/api";
import { useCatalogue } from "../lib/catalogue";
import { isStaff, useSession } from "../lib/session";
import { FOCI, type Focus } from "../lib/site";

interface InviteCode { key: string; label: string; gives: string; code: string; shownUntil: string; worksUntil: string }
interface Promo { code: string; product: string; price_key: string; max_uses: number | null; uses: number; active: number; note: string | null; created_at: string }
interface Gated { product: string; key: string; label: string; amount_cents: number }

const when = (iso: string) => new Date(iso).toLocaleString(undefined, { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });

function FocusPanel({ onDone }: { onDone: (m: string) => void }) {
  const [focus, setFocus] = useState<Focus | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { api<{ focus: Focus }>("/site").then((r) => setFocus(r.focus)).catch(() => undefined); }, []);
  return (
    <Panel kicker="The home page" title="Lead with">
      <p className="text-sm muted mb-3">The home page's banner is built around one part of the site. The rest stays one click away in the strip under it.</p>
      <div className="grid grid-cols-2 gap-2 text-sm">
        {FOCI.map((f) => (
          <button key={f.key} className={`panel-2 p-3 text-left ${focus === f.key ? "ring-2 ring-[var(--accent)]" : ""}`} onClick={async () => {
            setError(null);
            try { await api("/admin/site", { method: "PATCH", body: { focus: f.key } }); setFocus(f.key); onDone(`The home page now leads with ${f.label.toLowerCase()}.`); } catch (e) { setError((e as Error).message); }
          }}>
            <span className="font-semibold">{f.label}</span>{focus === f.key && <span className="block text-xs accent">Leading now</span>}
          </button>
        ))}
      </div>
      <p className="text-sm mt-3"><Link className="underline" to="/">See the home page</Link></p>
      <ErrorLine error={error} />
    </Panel>
  );
}

function InvitePanel({ onDone }: { onDone: (m: string) => void }) {
  const [data, setData] = useState<{ periodHours: number; codes: InviteCode[]; joined: { level: string; n: number }[] } | null>(null);
  const [hours, setHours] = useState("");
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(() => api<NonNullable<typeof data>>("/admin/invites").then((r) => { setData(r); setHours(String(r.periodHours)); }).catch((e) => setError(e.message)), []);
  useEffect(() => { void load(); }, [load]);
  const act = async (fn: () => Promise<unknown>, m: string) => { setError(null); try { await fn(); await load(); onDone(m); } catch (e) { setError((e as Error).message); } };
  return (
    <Panel kicker="Only you see these" title="Invite codes">
      <p className="text-sm muted mb-4">
        Give one of these to someone making an account; they type it in the invite box when they sign up (or later, on their Profile tab).
        Each code rolls on its own every {data?.periodHours ?? "..."} hours and still works for one more period after, so a code you just gave out keeps working.
      </p>
      {!data ? <p className="muted text-sm">Loading...</p> : (
        <div className="grid gap-3">
          {data.codes.map((c) => (
            <div key={c.key} className="panel-2 p-4 grid gap-1">
              <div className="flex items-center justify-between gap-3 flex-wrap">
                <span className="font-semibold">{c.label}</span>
                <span className="font-mono text-2xl tracking-[0.2em] accent select-all">{c.code}</span>
              </div>
              <p className="text-xs muted">{c.gives}</p>
              <p className="text-xs muted">Shown until {when(c.shownUntil)}; works until {when(c.worksUntil)}.</p>
              <div className="flex gap-2 mt-1">
                <button className="btn-ghost !py-1 !px-2 text-xs" onClick={() => void navigator.clipboard?.writeText(c.code).then(() => onDone(`${c.label} code copied.`))}>Copy</button>
                <button className="btn-ghost !py-1 !px-2 text-xs" onClick={() => { if (confirm(`Roll the ${c.label.toLowerCase()} code now? The current one stops working at once.`)) void act(() => api(`/admin/invites/${c.key}/roll`, { body: {} }), `New ${c.label.toLowerCase()} code made.`); }}>Roll now</button>
              </div>
            </div>
          ))}
          <form className="flex gap-2 items-end text-sm" onSubmit={(e) => { e.preventDefault(); void act(() => api("/admin/invites", { method: "PATCH", body: { periodHours: Number(hours) } }), "Rolling period saved."); }}>
            <label className="grid gap-1 flex-1">Roll every (hours)<input className="field" type="number" min={1} max={2160} value={hours} onChange={(e) => setHours(e.target.value)} /></label>
            <button className="btn-ghost">Save</button>
          </form>
          <p className="text-xs muted">Accounts made with a code so far: {data.joined.length ? data.joined.map((j) => `${j.n} with a ${j.level} code`).join(", ") : "none yet"}.</p>
        </div>
      )}
      <ErrorLine error={error} />
    </Panel>
  );
}

function PromoPanel({ onDone }: { onDone: (m: string) => void }) {
  const { products } = useCatalogue();
  const [data, setData] = useState<{ promos: Promo[]; gated: Gated[] } | null>(null);
  const [f, setF] = useState({ target: "", code: "", maxUses: "", note: "" });
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(() => api<{ promos: Promo[]; gated: Gated[] }>("/admin/promos").then((r) => { setData(r); setF((x) => ({ ...x, target: x.target || (r.gated[0] ? `${r.gated[0].product}|${r.gated[0].key}` : "") })); }).catch((e) => setError(e.message)), []);
  useEffect(() => { void load(); }, [load]);
  const title = (slug: string) => products?.find((p) => p.slug === slug)?.title || slug;
  const priceOf = (product: string, key: string) => data?.gated.find((g) => g.product === product && g.key === key);
  const act = async (fn: () => Promise<unknown>, m: string) => { setError(null); try { await fn(); await load(); onDone(m); } catch (e) { setError((e as Error).message); } };
  return (
    <Panel kicker="For friends" title="Promo codes">
      <p className="text-sm muted mb-3">A promo code unlocks a book's friend price at checkout. Make one per person, or one to share; set a limit if you like. Only paid orders count as uses.</p>
      <form className="grid gap-2 text-sm" onSubmit={(e) => {
        e.preventDefault();
        const [product, priceKey] = f.target.split("|");
        void act(async () => {
          const r = await api<{ code: string }>("/admin/promos", { body: { product, priceKey, code: f.code, maxUses: f.maxUses ? Number(f.maxUses) : undefined, note: f.note } });
          setF({ ...f, code: "", maxUses: "", note: "" });
          return r;
        }, "Promo code made.");
      }}>
        <select className="field" value={f.target} onChange={(e) => setF({ ...f, target: e.target.value })}>
          {data?.gated.map((g) => <option key={`${g.product}|${g.key}`} value={`${g.product}|${g.key}`}>{title(g.product)}: {g.label}, {money(g.amount_cents)}</option>)}
        </select>
        <div className="grid grid-cols-2 gap-2">
          <input className="field font-mono uppercase" placeholder="Code (optional)" value={f.code} onChange={(e) => setF({ ...f, code: e.target.value })} />
          <input className="field" type="number" min={1} placeholder="Max uses (optional)" value={f.maxUses} onChange={(e) => setF({ ...f, maxUses: e.target.value })} />
        </div>
        <input className="field" placeholder="Who it is for (only you see this)" value={f.note} onChange={(e) => setF({ ...f, note: e.target.value })} />
        <button className="btn justify-self-start" disabled={!f.target}>Make the code</button>
      </form>
      <div className="mt-5 grid gap-2 text-sm">
        {data?.promos.length ? data.promos.map((p) => {
          const g = priceOf(p.product, p.price_key);
          return (
            <div key={p.code} className={`panel-2 p-3 flex items-center justify-between gap-3 flex-wrap ${p.active ? "" : "opacity-60"}`}>
              <div>
                <span className="font-mono font-semibold select-all">{p.code}</span>
                <span className="muted"> -- {title(p.product)}{g ? ` for ${money(g.amount_cents)}` : ""}</span>
                <span className="block text-xs muted">{p.uses}{p.max_uses != null ? ` of ${p.max_uses}` : ""} used{p.note ? ` -- ${p.note}` : ""}</span>
              </div>
              <button className="btn-ghost !py-1 !px-2 text-xs" onClick={() => void act(() => api(`/admin/promos/${encodeURIComponent(p.code)}`, { method: "PATCH", body: { active: !p.active } }), p.active ? "Code switched off." : "Code switched on.")}>{p.active ? "Switch off" : "Switch on"}</button>
            </div>
          );
        }) : <p className="muted">No promo codes yet.</p>}
      </div>
      <ErrorLine error={error} />
    </Panel>
  );
}

function LevelPanel({ owner, onDone }: { owner: boolean; onDone: (m: string) => void }) {
  const [q, setQ] = useState("");
  const [u, setU] = useState<{ id: number; email: string; username: string | null; display_name: string; role: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const levels = owner ? ["member", "friend", "manager"] : ["member", "friend"];
  return (
    <Panel kicker="By hand" title="Give an account a level">
      <p className="text-sm muted mb-3">The same levels the invite codes give, set directly. {owner ? "" : "Only the owner makes managers."}</p>
      <form className="flex gap-2 text-sm" onSubmit={async (e) => { e.preventDefault(); setError(null); setU(null); try { setU((await api<{ user: NonNullable<typeof u> }>(`/admin/find-user?q=${encodeURIComponent(q)}`)).user); } catch (err) { setError((err as Error).message); } }}>
        <input className="field" required placeholder="Their email or username" value={q} onChange={(e) => setQ(e.target.value)} />
        <button className="btn-ghost">Find</button>
      </form>
      {u && (
        <div className="panel-2 p-3 mt-3 text-sm grid gap-2">
          <p><b>{u.display_name}</b> {u.username && <span className="muted">@{u.username}</span>} <span className="muted">{u.email}</span></p>
          <p>Now: <span className="accent">{u.role === "admin" ? "owner" : u.role}</span></p>
          {u.role !== "admin" && (
            <div className="flex gap-2 flex-wrap">
              {levels.filter((l) => l !== u.role).map((l) => (
                <button key={l} className="btn-ghost !py-1 !px-2" onClick={async () => {
                  setError(null);
                  try { await api(`/admin/users/${u.id}/role`, { body: { role: l } }); setU({ ...u, role: l }); onDone(`${u.display_name} is now ${l === "member" ? "a member" : `a ${l}`}.`); } catch (err) { setError((err as Error).message); }
                }}>Make {l}</button>
              ))}
            </div>
          )}
        </div>
      )}
      <ErrorLine error={error} />
      <p className="text-xs muted mt-3">Everything else about an account is on <Link className="underline" to="/admin/users">Members</Link>.</p>
    </Panel>
  );
}

export default function AdminStudio() {
  const { me, notify } = useSession();
  if (!isStaff(me)) return <div className="mx-auto max-w-xl px-4 py-10 muted">Admins only.</div>;
  const owner = me!.role === "admin";
  const done = (m: string) => notify("Done", m);
  return (
    <div className="mx-auto max-w-6xl px-4 py-10 grid gap-6">
      <div>
        <h1 className="text-4xl font-bold">Studio</h1>
        <p className="muted mt-1">Signed in as {me!.displayName}{me!.username ? ` (@${me!.username})` : ""} -- {owner ? "the owner" : "a manager"}.</p>
      </div>
      <AdminNav />
      <div className="grid gap-6 lg:grid-cols-2">
        <FocusPanel onDone={done} />
        <LevelPanel owner={owner} onDone={done} />
        {owner ? <InvitePanel onDone={done} /> : <Panel title="Invite codes"><p className="text-sm muted">Only the owner sees the invite codes.</p></Panel>}
        <PromoPanel onDone={done} />
      </div>
      <p className="text-sm muted">Prices, product states (a pre-order going live), orders and backers are on <Link className="underline" to="/admin">Backers and orders</Link>.</p>
    </div>
  );
}
