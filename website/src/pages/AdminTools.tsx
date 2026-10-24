// Admin -> Tools and releases: staging against live (and the button that promotes staging), the
// build-pack queue, and the studio tools that run on the owner's computer.

import { useEffect, useState } from "react";
import AdminNav from "../components/AdminNav";
import { ErrorLine, Panel } from "../components/ui";
import { api } from "../lib/api";
import { isStaff, useSession } from "../lib/session";

interface Run { id: number; branch: string; event: string; status: string; conclusion: string | null; sha: string; title: string; at: string; url: string }
interface Deploys { staging: Run | null; lastPromotion: Run | null; runs: Run[]; stagingUrl: string }
interface Job { ref: string; tool: string; status: string; params: string; attempts: number; error: string | null; size: number | null; downloads: number; created_at: string; done_at: string | null; email: string }

const when = (s: string) => new Date(s).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });

export default function AdminTools() {
  const { me } = useSession();
  const [d, setD] = useState<Deploys | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [ghError, setGhError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [confirm, setConfirm] = useState("");
  const [runId, setRunId] = useState("");
  const load = () => {
    api<Deploys>("/admin/deploys").then((r) => { setD(r); setGhError(null); }).catch((e) => setGhError(e.message));
    api<{ jobs: Job[] }>("/admin/tool-jobs").then((r) => setJobs(r.jobs)).catch(() => undefined);
  };
  useEffect(() => { if (me?.role === "admin") load(); }, [me]);
  if (!isStaff(me)) return <div className="mx-auto max-w-xl px-4 py-10 muted">Admins only.</div>;
  const promote = async () => {
    setError(null); setMsg(null);
    try { const r = await api<{ message: string }>("/admin/deploys/promote", { body: { confirm, stagingRun: runId || undefined } }); setMsg(r.message); setConfirm(""); setTimeout(load, 8000); }
    catch (e) { setError((e as Error).message); }
  };
  return (
    <div className="mx-auto max-w-6xl px-4 py-10 grid gap-6">
      <AdminNav />
      <h1 className="text-3xl font-bold">Tools and releases</h1>
      <ErrorLine error={error} />
      {msg && <p className="panel-2 p-3 text-sm">{msg}</p>}

      <Panel kicker="Staging, then live" title="What is on staging, and promoting it">
        {!d ? <p className="muted text-sm">{ghError || "Reading GitHub..."}</p> : (
          <div className="grid gap-3 text-sm">
            <p>Staging: {d.staging ? <><b>{d.staging.sha}</b> {d.staging.title} ({when(d.staging.at)}) -- <a className="underline" href={d.stagingUrl} target="_blank" rel="noopener">open staging</a></> : "no successful staging build yet"}</p>
            <p>Last promotion: {d.lastPromotion ? <>{d.lastPromotion.conclusion || d.lastPromotion.status} ({when(d.lastPromotion.at)}) <a className="underline" href={d.lastPromotion.url} target="_blank" rel="noopener">details</a></> : "none yet"}</p>
            <div className="flex flex-wrap gap-2 items-end">
              <label className="grid gap-1"><span className="text-xs muted">Staging run (blank = the newest)</span>
                <input className="field !w-48" value={runId} onChange={(e) => setRunId(e.target.value.replace(/\D/g, ""))} placeholder="newest" /></label>
              <label className="grid gap-1"><span className="text-xs muted">Type LIVE to confirm</span>
                <input className="field !w-32" value={confirm} onChange={(e) => setConfirm(e.target.value)} /></label>
              <button className="btn" disabled={confirm !== "LIVE"} onClick={() => void promote()}>Promote staging to live</button>
            </div>
            <p className="text-xs muted">Publishes the build you looked at on staging, applies its database changes to the live database, and moves main.
              Undo: Cloudflare, Pages, Deployments, Rollback (pages and code, not the data). Refreshing staging's data is
              <code> py -3.12 website/scripts/staging.py refresh</code> on your computer.</p>
            <details><summary className="cursor-pointer text-sm">Recent runs</summary>
              <ul className="mt-2 grid gap-1">{d.runs.map((r) => <li key={r.id}><a className="underline" href={r.url} target="_blank" rel="noopener">{r.id}</a> {r.branch} / {r.event}: {r.conclusion || r.status} -- {r.sha} {r.title}</li>)}</ul>
            </details>
          </div>
        )}
      </Panel>

      <Panel kicker="Queue" title="Build packs and cut lists">
        <p className="text-sm muted mb-2">Drawn on your computer: <code>py -3.12 website/scripts/render_packs.py --site https://www.zeanahlab.com --watch</code> (key scope packs:render) and
          <code> render_cutlists.py</code> (cutlists:render).</p>
        {jobs.length === 0 ? <p className="text-sm muted">Nothing asked for yet.</p> : (
          <table className="w-full text-sm"><thead><tr className="text-left muted"><th>When</th><th>Who</th><th>Design</th><th>Status</th><th>Size</th></tr></thead>
            <tbody>{jobs.map((j) => { const s = JSON.parse(j.params); return (
              <tr key={j.ref} className="border-t" style={{ borderColor: "var(--line)" }}><td className="py-1">{when(j.created_at)}</td><td>{j.email}</td>
                <td>{s.frequency}V {s.cut} {(+s.diameter_m).toFixed(2)} m</td><td>{j.status}{j.error ? `: ${j.error}` : ""}</td><td>{j.size ? `${(j.size / 1e6).toFixed(1)} MB` : ""}</td></tr>); })}</tbody></table>
        )}
      </Panel>

      <Panel kicker="On your computer" title="The studio">
        <p className="text-sm mb-3">Start it with <code>py -3.12 -m sketch_claude serve</code>, then open:</p>
        <div className="flex flex-wrap gap-2">
          {[["Episode Director: the visual episode editor", "/director"], ["Season room", "/season"], ["Modeller (every setting)", "/"], ["Lesson Studio", "/lesson?lesson=2v"]].map(([label, path]) => (
            <a key={path} className="btn-ghost" href={`http://127.0.0.1:8767${path}`} target="_blank" rel="noopener">{label}</a>
          ))}
        </div>
        <p className="text-xs muted mt-2">Rendering without the window: <code>py -3.12 -m sketch_claude episode --episode s01e03</code>, <code>py -3.12 -m film make 2v --engine web</code>. The guide for doing it with an LLM: docs/llm-episode-guide.md.</p>
      </Panel>
    </div>
  );
}
