import { useCallback, useEffect, useState } from "react";
import { Link, NavLink, Route, Routes } from "react-router-dom";
import { ErrorLine, Fraction, Honeypot, JoinQuest, Panel } from "../components/ui";
import { api, usd } from "../lib/api";
import { useSession, type Me } from "../lib/session";

// ---------------------------------------------------------------- sign in / up

function Auth() {
  const { setMe, notify } = useSession();
  const [mode, setMode] = useState<"in" | "up">("up");
  const [f, setF] = useState({ email: "", password: "", displayName: "", marketingConsent: false });
  const [trap, setTrap] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const r = await api<{ user: Me }>(mode === "up" ? "/signup" : "/login", { body: { ...f, website: trap } });
      setMe(r.user);
      notify(mode === "up" ? "Account made" : "Signed in", mode === "up" ? "You can now: list yourself on the network and keep your own life account." : `Welcome back, ${r.user.displayName}.`);
    } catch (err) { setError((err as Error).message); } finally { setBusy(false); }
  }
  return (
    <div className="mx-auto max-w-5xl px-4 py-10 grid gap-6 md:grid-cols-2">
      <Panel title={mode === "up" ? "Make an account" : "Sign in"}>
        <form onSubmit={submit} className="grid gap-3 text-sm relative">
          {mode === "up" && <label className="grid gap-1">Name shown to others<input className="field" required maxLength={80} value={f.displayName} onChange={(e) => setF({ ...f, displayName: e.target.value })} /></label>}
          <label className="grid gap-1">Email<input className="field" type="email" required autoComplete="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></label>
          <label className="grid gap-1">Password{mode === "up" && <span className="muted text-xs">At least 10 characters.</span>}
            <input className="field" type="password" required minLength={mode === "up" ? 10 : 1} autoComplete={mode === "up" ? "new-password" : "current-password"} value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} /></label>
          {mode === "up" && <label className="flex gap-2 items-start"><input type="checkbox" className="mt-1" checked={f.marketingConsent} onChange={(e) => setF({ ...f, marketingConsent: e.target.checked })} /><span className="muted">Send me build updates (optional).</span></label>}
          <Honeypot value={trap} onChange={setTrap} />
          <button className="btn" disabled={busy}>{busy ? "One moment..." : mode === "up" ? "Make my account" : "Sign in"}</button>
          <ErrorLine error={error} />
          <button type="button" className="text-sm underline underline-offset-4 justify-self-start" onClick={() => setMode(mode === "up" ? "in" : "up")}>
            {mode === "up" ? "I already have an account" : "I need an account"}
          </button>
        </form>
        {mode === "in" && <Forgot email={f.email} />}
      </Panel>
      <div className="grid gap-6 content-start">
        <Panel kicker="What an account is for" title="Own your numbers">
          <ul className="text-sm space-y-2 muted">
            <li>- Your standing with the build, as quests that tick when you really do them.</li>
            <li>- Your own life account: skills with levels, goals with requirements, your hours priced -- the program from <i>Snowball</i>, kept for you.</li>
            <li>- A place on the pad network, and contact details other members can see.</li>
          </ul>
        </Panel>
        <JoinQuest />
      </div>
    </div>
  );
}

function Forgot({ email }: { email: string }) {
  const [open, setOpen] = useState(false);
  const [mail, setMail] = useState(email);
  const [trap, setTrap] = useState("");
  const [note, setNote] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  if (!open) return <button type="button" className="text-sm underline underline-offset-4 mt-3" onClick={() => { setMail(email); setOpen(true); }}>I forgot my password</button>;
  return (
    <form className="grid gap-2 text-sm mt-4 relative" onSubmit={async (e) => {
      e.preventDefault(); setError(null);
      try { setNote((await api<{ note: string }>("/password/forgot", { body: { email: mail, website: trap } })).note); } catch (err) { setError((err as Error).message); }
    }}>
      <label className="grid gap-1">Your account's email<input className="field" type="email" required value={mail} onChange={(e) => setMail(e.target.value)} /></label>
      <Honeypot value={trap} onChange={setTrap} />
      <button className="btn-ghost justify-self-start">Send me a reset link</button>
      {note && <p className="accent">{note}</p>}
      <ErrorLine error={error} />
    </form>
  );
}

// ---------------------------------------------------------------- standing

const STANDING: [string, string, string][] = [
  ["onTheList", "On the list", "/sample"],
  ["readTheSample", "Read the sample", "/sample"],
  ["ownsTheBook", "Own the book", "/book"],
  ["onTheNetwork", "On the network", "/network"],
  ["salvaged", "Logged salvage", "/recyclers"],
  ["backer", "Backer", "/back"],
  ["founder", "Founder plaque", "/back"],
];

function Standing() {
  const [checks, setChecks] = useState<Record<string, boolean> | null>(null);
  useEffect(() => { api<{ checks: Record<string, boolean> }>("/me/standing").then((r) => setChecks(r.checks)).catch(() => setChecks({})); }, []);
  if (!checks) return <p className="muted">Loading...</p>;
  const done = STANDING.filter(([k]) => checks[k]).length;
  return (
    <Panel kicker="Your standing with the build" title={`${done} of ${STANDING.length}`}>
      <Fraction have={done} need={STANDING.length} label="Account progress" />
      <ul className="grid sm:grid-cols-2 gap-2 mt-4 text-sm">
        {STANDING.map(([k, label, to]) => (
          <li key={k} className="panel-2 p-3 flex items-center gap-2">
            <span aria-hidden className={`inline-block w-3.5 h-3 tri ${checks[k] ? "bg-[var(--accent)]" : "bg-[var(--line)]"}`} />
            {checks[k] ? label : <Link className="underline underline-offset-4" to={to}>{label}</Link>}
          </li>
        ))}
      </ul>
      <p className="text-xs muted mt-3">Each line is read from the records: a download, a paid order, a listing, a recorded backing. Nothing ticks on its own.</p>
    </Panel>
  );
}

// ---------------------------------------------------------------- the life account

interface Review {
  fhv: { last30: number | null; prior30: number | null; trend: string | null };
  capital: number;
  skills: { name: string; level: number; xp: number }[];
  quests: { name: string; status: string; description: string; met: number; total: number; unmet: string[] }[];
  assets: { name: string; value: number; description: string }[];
  logs: { ts: string; method: string; hours: number; cash: number; note: string }[];
  stages: { name: string; goal: string; quest: string; complete: boolean; current: boolean; missing: string[] }[];
}
interface Score { weight: number; methods: { name: string; cash: number; cost: number; xpTotal: number; unlocks: number; tv: number; xp: { skill: string; xp_per_hour: number }[] }[] }
interface PathRow { name: string; met: number; total: number; unlocks: number }

function MiniForm({ fields, submit, label }: { fields: [string, string, string?][]; submit: (v: Record<string, string>) => Promise<void>; label: string }) {
  const [v, setV] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  return (
    <form className="grid gap-2 text-sm" onSubmit={async (e) => {
      e.preventDefault();
      setError(null);
      try { await submit(v); setV({}); } catch (err) { setError((err as Error).message); }
    }}>
      {fields.map(([k, ph, type]) => type === "area"
        ? <textarea key={k} className="field" rows={3} placeholder={ph} value={v[k] || ""} onChange={(e) => setV({ ...v, [k]: e.target.value })} />
        : <input key={k} className="field" type={type || "text"} step="any" placeholder={ph} value={v[k] || ""} onChange={(e) => setV({ ...v, [k]: e.target.value })} />)}
      <button className="btn-ghost">{label}</button>
      <ErrorLine error={error} />
    </form>
  );
}

const lines = (s?: string) => (s || "").split(/\n|,/).map((x) => x.trim()).filter(Boolean);

function Life() {
  const { notify } = useSession();
  const [data, setData] = useState<{ review: Review; score: Score; path: PathRow[] } | null>(null);
  const load = useCallback(() => api("/life").then(setData).catch(() => undefined), []);
  useEffect(() => { void load(); }, [load]);
  const after = (title?: string, msg?: string) => { if (title) notify(title, msg || ""); return load(); };
  if (!data) return <p className="muted">Loading...</p>;
  const { review: r, score, path } = data;
  return (
    <div className="grid gap-6">
      <Panel kicker="The one metric" title="Future Hour Value">
        <div className="grid sm:grid-cols-3 gap-3">
          <div className="panel-2 p-4"><div className="num text-2xl accent">{r.fhv.last30 != null ? `${usd(r.fhv.last30)}/hr` : "no logs yet"}</div><div className="text-sm">last 30 days</div></div>
          <div className="panel-2 p-4"><div className="num text-2xl">{r.fhv.prior30 != null ? `${usd(r.fhv.prior30)}/hr` : "no logs yet"}</div><div className="text-sm">the 30 before</div></div>
          <div className="panel-2 p-4"><div className="text-lg">{r.fhv.trend || "two months of logs give a trend"}</div><div className="text-sm muted">trend</div></div>
        </div>
        <p className="text-xs muted mt-3">Average dollars per logged hour. A mirror, not a judge: it shows what you recorded, and grades nothing.</p>
      </Panel>

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel kicker="Skills tab" title="Skills">
          <ul className="grid gap-3">
            {r.skills.map((s) => (
              <li key={s.name}>
                <Fraction have={Math.round(s.xp * 10) / 10} need={100} label={`${s.name} - level ${s.level}`} />
                <button className="text-xs underline mt-1" onClick={async () => { const res = await api<{ message: string }>(`/life/skills/${encodeURIComponent(s.name)}/level`, { body: { level: s.level + 1 } }); await after("Level up", res.message); }}>
                  Declare level {s.level + 1}
                </button>
              </li>
            ))}
            {!r.skills.length && <li className="muted text-sm">No skills yet. The account is level 1 in everything.</li>}
          </ul>
          <p className="text-xs muted mt-3">The bar is your own scale: 100 xp a level, by default. You declare a level when you cross a threshold you could defend.</p>
          <div className="mt-4"><MiniForm label="Add a skill" fields={[["name", "Skill, e.g. welding"], ["level", "Level (1-99)", "number"]]}
            submit={async (v) => { await api("/life/skills", { body: { name: v.name, level: Number(v.level || 1) } }); await after(); }} /></div>
        </Panel>

        <Panel kicker="Quest journal" title="Quests">
          <ul className="grid gap-3">
            {r.quests.map((q) => (
              <li key={q.name} className="panel-2 p-3">
                {/* a quest with no requirements is all-or-nothing: 1/1 when done, 0/1 before */}
                <Fraction have={q.total ? q.met : q.status === "complete" ? 1 : 0} need={Math.max(q.total, 1)} label={`${q.name} (${q.status.replace("_", " ")})`} />
                {q.unmet.length > 0 && <ul className="text-xs muted mt-2">{q.unmet.map((u) => <li key={u}>missing: {u}</li>)}</ul>}
                {q.status !== "complete" && (
                  <button className="text-xs underline mt-2" onClick={async () => {
                    const res = await api<{ completed: boolean; unmet: string[]; unlocked: string[] }>(`/life/quests/${encodeURIComponent(q.name)}/complete`, { body: {} });
                    await after(res.completed ? `Quest complete: ${q.name}` : "Not yet", res.completed ? (res.unlocked.length ? `You can now start: ${res.unlocked.join(", ")}` : "Recorded.") : `Still missing: ${res.unmet.join("; ")}`);
                  }}>Complete</button>
                )}
              </li>
            ))}
            {!r.quests.length && <li className="muted text-sm">No quests yet. A goal with its requirements written down is the first skip.</li>}
          </ul>
          <div className="mt-4"><MiniForm label="Add a quest" fields={[["name", "Goal, e.g. freelance fabricator"], ["description", "What done looks like"],
            ["requires", "Requirements, one per line: skill:welding:3, quest:first client, capital:tools:2000, asset:workshop", "area"]]}
            submit={async (v) => { await api("/life/quests", { body: { name: v.name, description: v.description, requires: lines(v.requires) } }); await after(); }} /></div>
        </Panel>
      </div>

      <Panel kicker="The money-making guide for your life" title="Methods, scored">
        <p className="text-xs muted mb-3">TV = Cash + XP x ${score.weight} - Cost, with the unmet requirements each method trains toward counted as Unlocks.</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm num">
            <thead><tr className="muted text-left"><th className="py-1">Method</th><th>Cash/hr</th><th>Cost/hr</th><th>XP/hr</th><th>Unlocks</th><th>TV</th></tr></thead>
            <tbody>
              {score.methods.map((m) => (
                <tr key={m.name} className="border-t" style={{ borderColor: "var(--line)" }}>
                  <td className="py-1.5">{m.name}<span className="block text-xs muted">{m.xp.map((x) => `${x.skill} ${x.xp_per_hour}/hr`).join(", ")}</span></td>
                  <td>{usd(m.cash)}</td><td>{usd(m.cost)}</td><td>{m.xpTotal.toFixed(2)}</td><td>{m.unlocks}</td><td className="font-semibold accent">{m.tv.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!score.methods.length && <p className="muted text-sm">No methods rated yet. Rate your job, your side project, your study.</p>}
        </div>
        <div className="grid md:grid-cols-2 gap-6 mt-5">
          <MiniForm label="Rate a method" fields={[["name", "Method, e.g. day job"], ["cash", "Cash per hour ($)", "number"], ["cost", "Cost per hour ($)", "number"],
            ["xp", "XP streams, one per line: cad:0.2", "area"]]}
            submit={async (v) => { await api("/life/methods", { body: { name: v.name, cash: Number(v.cash || 0), cost: Number(v.cost || 0), xp: lines(v.xp) } }); await after(); }} />
          <MiniForm label="Log hours" fields={[["method", "Method"], ["hours", "Hours", "number"], ["note", "Note (optional)"]]}
            submit={async (v) => {
              const res = await api<{ cash: number; gained: { skill: string; xp: number }[]; forgone: { method: string; cash: number } | null }>("/life/logs", { body: { method: v.method, hours: Number(v.hours), note: v.note } });
              await after(`Logged ${v.hours}h of ${v.method}`, [`${usd(res.cash)} cash`, ...res.gained.map((g) => `${g.skill} +${g.xp}`), res.forgone ? `forgone: ${usd(res.forgone.cash)} from ${res.forgone.method}` : ""].filter(Boolean).join(" - "));
            }} />
        </div>
      </Panel>

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel kicker="Critical path" title="Do these first">
          <ul className="text-sm grid gap-1.5">
            {path.map((p) => <li key={p.name} className="flex justify-between gap-3"><span>{p.name}</span><span className="muted num">{p.met}/{p.total} - unlocks {p.unlocks}</span></li>)}
            {!path.length && <li className="muted">No open quests.</li>}
          </ul>
          <p className="text-xs muted mt-3">Load-bearing quests first (the most others wait on them), then the nearest to done.</p>
        </Panel>
        <Panel kicker="The ladder" title="The ten stages">
          <ol className="text-sm grid gap-1.5">
            {r.stages.map((s) => (
              <li key={s.name} className={`flex justify-between gap-3 ${s.current ? "accent font-semibold" : s.complete ? "" : "muted"}`}>
                <span>{s.name} - {s.goal}</span><span>{s.complete ? "complete" : s.current ? "current" : ""}</span>
              </li>
            ))}
          </ol>
          <p className="text-xs muted mt-3">A stage completes when you complete a quest with its name (e.g. "{r.stages.find((s) => s.current)?.quest || "reliable employment"}"), requirements and all.</p>
        </Panel>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel kicker="Bank" title={`Working capital ${usd(r.capital)}`}>
          <MiniForm label="Set working capital" fields={[["amount", "Dollars set aside", "number"]]}
            submit={async (v) => { await api("/life/capital", { body: { amount: Number(v.amount) } }); await after(); }} />
          <ul className="text-sm mt-4 grid gap-1">{r.assets.map((a) => <li key={a.name} className="flex justify-between"><span>{a.name}</span><span className="num">{usd(a.value)}</span></li>)}</ul>
          <div className="mt-3"><MiniForm label="Record an asset" fields={[["name", "Asset, e.g. workshop"], ["value", "Value ($)", "number"]]}
            submit={async (v) => { await api("/life/assets", { body: { name: v.name, value: Number(v.value || 0) } }); await after(); }} /></div>
        </Panel>
        <Panel kicker="Ledger" title="Recent hours">
          <ul className="text-sm grid gap-1">
            {r.logs.map((l, i) => <li key={i} className="flex justify-between gap-3"><span>{l.method} <span className="muted">{l.hours}h</span></span><span className="num muted">{usd(l.cash)} - {new Date(l.ts).toLocaleDateString()}</span></li>)}
            {!r.logs.length && <li className="muted">No hours logged yet.</li>}
          </ul>
        </Panel>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- security and your data

interface Sess { id: string; created_at: string; last_seen_at: string | null; user_agent: string | null; country: string | null; current: boolean }

function Security() {
  const { me, setMe, refresh } = useSession();
  const [sessions, setSessions] = useState<Sess[]>([]);
  const [pw, setPw] = useState({ currentPassword: "", newPassword: "" });
  const [del, setDel] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(() => api<{ sessions: Sess[] }>("/me/sessions").then((r) => setSessions(r.sessions)).catch((e) => setError(e.message)), []);
  useEffect(() => { void load(); }, [load]);
  const act = async (fn: () => Promise<unknown>, done: string) => { setError(null); setMsg(null); try { await fn(); setMsg(done); await load(); } catch (e) { setError((e as Error).message); } };
  const when = (s: string | null) => (s ? new Date(s).toLocaleString() : "--");
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {msg && <p className="accent lg:col-span-2">{msg}</p>}
      <div className="lg:col-span-2"><ErrorLine error={error} /></div>
      <Panel title="Where you are signed in">
        <div className="grid gap-2 text-sm">
          {sessions.map((s) => (
            <div key={s.id} className="panel-2 p-3 flex flex-wrap gap-2 justify-between items-center">
              <span><b>{s.user_agent || "A device"}</b>{s.country ? `, ${s.country}` : ""} {s.current && <span className="accent">(this one)</span>}<br /><span className="muted text-xs">signed in {when(s.created_at)}; last used {when(s.last_seen_at)}</span></span>
              {!s.current && <button className="btn-ghost !py-1" onClick={() => act(() => api(`/me/sessions/${s.id}`, { method: "DELETE" }), "That device is signed out.")}>Sign it out</button>}
            </div>
          ))}
          {sessions.length > 1 && <button className="btn-ghost justify-self-start" onClick={() => act(() => api("/me/sessions/others", { body: {} }), "Every other device is signed out.")}>Sign out everywhere else</button>}
        </div>
      </Panel>
      <Panel title="Password and email">
        <form className="grid gap-2 text-sm" onSubmit={(e) => { e.preventDefault(); void act(async () => { const r = await api<{ user: Me }>("/me", { method: "PATCH", body: pw }); setMe(r.user); setPw({ currentPassword: "", newPassword: "" }); }, "Password changed. Your other devices are signed out."); }}>
          <input className="field" type="password" required autoComplete="current-password" placeholder="Current password" value={pw.currentPassword} onChange={(e) => setPw({ ...pw, currentPassword: e.target.value })} />
          <input className="field" type="password" required minLength={10} autoComplete="new-password" placeholder="New password (10 characters or more)" value={pw.newPassword} onChange={(e) => setPw({ ...pw, newPassword: e.target.value })} />
          <button className="btn justify-self-start">Change password</button>
        </form>
        <p className="text-sm mt-5">{me!.email}: {me!.emailVerified ? <span className="accent">confirmed</span> : <>not confirmed yet. <button className="underline" onClick={() => act(() => api("/me/verify", { body: {} }), "A confirmation link is on its way.")}>Send me a link</button></>}</p>
      </Panel>
      <Panel title="Your data">
        <p className="text-sm muted mb-3">Everything this site keeps about you -- account, list entry, mail sent to you, orders, listings, life account, devices -- in one file.</p>
        <a className="btn-ghost" href="/api/me/export" download>Download my data</a>
      </Panel>
      <Panel title="Delete my account">
        <form className="grid gap-2 text-sm" onSubmit={(e) => { e.preventDefault(); if (!confirm("Delete your account for good?")) return; void act(async () => { await api("/me", { method: "DELETE", body: { password: del } }); setMe(null); await refresh(); }, "Your account is deleted."); }}>
          <p className="muted">Removes your account, listings and life account, and stops all updates. Receipts for past orders are kept, as the law requires, without your account.</p>
          <input className="field" type="password" required placeholder="Your password, to confirm" value={del} onChange={(e) => setDel(e.target.value)} />
          <button className="btn-ghost justify-self-start" style={{ color: "var(--color-ember)" }}>Delete my account</button>
        </form>
      </Panel>
    </div>
  );
}

// ---------------------------------------------------------------- profile

function Profile() {
  const { me, setMe, refresh } = useSession();
  const [f, setF] = useState({ displayName: me!.displayName, bio: me!.bio, city: me!.city, region: me!.region, country: me!.country, publicProfile: me!.publicProfile });
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  async function save(e: React.FormEvent) {
    e.preventDefault();
    try { const r = await api<{ user: Me }>("/me", { method: "PATCH", body: f }); setMe(r.user); setMsg("Saved."); setError(null); } catch (err) { setError((err as Error).message); }
  }
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Panel title="Profile">
        <form onSubmit={save} className="grid gap-2 text-sm">
          <input className="field" value={f.displayName} onChange={(e) => setF({ ...f, displayName: e.target.value })} placeholder="Name" />
          <textarea className="field" rows={3} value={f.bio} onChange={(e) => setF({ ...f, bio: e.target.value })} placeholder="About you" />
          <div className="grid grid-cols-3 gap-2">
            <input className="field" value={f.city} onChange={(e) => setF({ ...f, city: e.target.value })} placeholder="City" />
            <input className="field" value={f.region} onChange={(e) => setF({ ...f, region: e.target.value })} placeholder="Region" />
            <input className="field" value={f.country} onChange={(e) => setF({ ...f, country: e.target.value })} placeholder="Country" />
          </div>
          <button className="btn">Save</button>
          {msg && <p className="accent">{msg}</p>}
          <ErrorLine error={error} />
        </form>
      </Panel>
      <Panel title="Sign out">
        <button className="btn-ghost" onClick={async () => { await api("/logout", { body: {} }); setMe(null); await refresh(); }}>Sign out of this device</button>
        {me!.role === "admin" && <p className="mt-4"><Link className="underline" to="/admin">Admin</Link></p>}
      </Panel>
    </div>
  );
}

export default function Account() {
  const { me } = useSession();
  if (!me) return <Auth />;
  const tab = ({ isActive }: { isActive: boolean }) => (isActive ? "accent font-semibold" : "muted");
  return (
    <div className="mx-auto max-w-6xl px-4 py-10 grid gap-6">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">Your account</p>
        <h1 className="text-4xl font-bold mt-1">{me.displayName}</h1>
        <nav className="flex gap-5 mt-4 text-sm">
          <NavLink end to="/account" className={tab}>Standing</NavLink>
          <NavLink to="/account/life" className={tab}>Life account</NavLink>
          <NavLink to="/account/profile" className={tab}>Profile</NavLink>
          <NavLink to="/account/security" className={tab}>Security and data</NavLink>
        </nav>
      </div>
      <Routes>
        <Route index element={<div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]"><Standing /><JoinQuest /></div>} />
        <Route path="life" element={<Life />} />
        <Route path="profile" element={<Profile />} />
        <Route path="security" element={<Security />} />
      </Routes>
    </div>
  );
}
