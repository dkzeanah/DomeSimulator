// Admin -> Projects: the owner's board. Projects across the top, a quick-add line, the four
// columns (to do, doing, blocked, done), and each card opens to edit in place. Below, the
// projects themselves: rename, pause, finish, recolour.

import { useMemo, useState } from "react";
import AdminNav from "../components/AdminNav";
import { ErrorLine, Panel } from "../components/ui";
import { api } from "../lib/api";
import { COLOUR, STATUS_LABEL, dueLabel, href, today, urgency, useBoard, type Board, type Project, type Task } from "../lib/projects";
import { isStaff, useSession } from "../lib/session";

function Chip({ p }: { p: Project | undefined }) {
  if (!p) return null;
  return (
    <span className="inline-flex items-center gap-1.5 text-xs muted">
      <span aria-hidden className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: COLOUR[p.colour] || COLOUR.gold }} />{p.name}
    </span>
  );
}

function Due({ t }: { t: Task }) {
  const u = urgency(t);
  if (!t.dueDate) return null;
  const colour = u === "overdue" ? "var(--color-ember)" : u === "today" ? "var(--accent)" : "var(--muted)";
  return <span className="text-xs" style={{ color: colour, fontWeight: u === "overdue" || u === "today" ? 600 : 400 }}>{dueLabel(t)}</span>;
}

export function LinkLine({ link }: { link: string | null }) {
  if (!link) return null;
  const url = href(link);
  return url
    ? <a className="text-xs underline underline-offset-2 break-all" href={url} target={url.startsWith("/") ? undefined : "_blank"} rel="noopener">{link}</a>
    : <code className="text-xs muted break-all select-all">{link}</code>;
}

function Card({ t, board, act }: { t: Task; board: Board; act: (fn: () => Promise<unknown>) => Promise<void> }) {
  const [open, setOpen] = useState(false);
  const [f, setF] = useState({ title: t.title, notes: t.notes, dueDate: t.dueDate || "", link: t.link || "", assigneeId: t.assigneeId ? String(t.assigneeId) : "", projectId: String(t.projectId) });
  const p = board.projects.find((x) => x.id === t.projectId);
  const i = board.statuses.indexOf(t.status);
  const move = (s: string) => act(() => api(`/admin/tasks/${t.id}`, { method: "PATCH", body: { status: s } }));
  return (
    <li className="panel-2 p-3 grid gap-1.5 text-sm">
      <Chip p={p} />
      <button className="text-left font-semibold leading-snug" aria-expanded={open} onClick={() => setOpen(!open)}>
        <span className={t.status === "done" ? "line-through muted" : ""}>{t.title}</span>
      </button>
      <div className="flex flex-wrap gap-x-3 gap-y-1 items-center">
        <Due t={t} />
        {t.assigneeName && <span className="text-xs muted">{t.assigneeName}</span>}
        {t.notes && !open && <span className="text-xs muted" title={t.notes}>notes</span>}
      </div>
      {!open && <LinkLine link={t.link} />}
      <div className="flex gap-1.5">
        {i > 0 && <button className="btn-ghost !py-0.5 !px-2 text-xs" onClick={() => move(board.statuses[i - 1])} aria-label={`Move to ${STATUS_LABEL[board.statuses[i - 1]]}`}>&larr; {STATUS_LABEL[board.statuses[i - 1]]}</button>}
        {i < board.statuses.length - 1 && <button className="btn-ghost !py-0.5 !px-2 text-xs" onClick={() => move(board.statuses[i + 1])} aria-label={`Move to ${STATUS_LABEL[board.statuses[i + 1]]}`}>{STATUS_LABEL[board.statuses[i + 1]]} &rarr;</button>}
      </div>
      {open && (
        <form className="grid gap-2 mt-2" onSubmit={(e) => {
          e.preventDefault();
          void act(() => api(`/admin/tasks/${t.id}`, { method: "PATCH", body: { ...f, projectId: Number(f.projectId), assigneeId: f.assigneeId ? Number(f.assigneeId) : null } })).then(() => setOpen(false));
        }}>
          <input className="field" required maxLength={200} value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} />
          <textarea className="field" rows={3} placeholder="Notes" value={f.notes} onChange={(e) => setF({ ...f, notes: e.target.value })} />
          <div className="grid grid-cols-2 gap-2">
            <label className="grid gap-0.5 text-xs muted">Due<input className="field" type="date" value={f.dueDate} onChange={(e) => setF({ ...f, dueDate: e.target.value })} /></label>
            <label className="grid gap-0.5 text-xs muted">Who
              <select className="field" value={f.assigneeId} onChange={(e) => setF({ ...f, assigneeId: e.target.value })}>
                <option value="">Nobody yet</option>{board.staff.map((s) => <option key={s.id} value={s.id}>{s.display_name}</option>)}
              </select></label>
          </div>
          <label className="grid gap-0.5 text-xs muted">Project
            <select className="field" value={f.projectId} onChange={(e) => setF({ ...f, projectId: e.target.value })}>
              {board.projects.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}
            </select></label>
          <input className="field" placeholder="Link: /book, deliverables/0573-..., or https://..." value={f.link} onChange={(e) => setF({ ...f, link: e.target.value })} />
          <div className="flex gap-2 flex-wrap">
            <button className="btn !py-1.5">Save</button>
            <button type="button" className="btn-ghost !py-1.5" onClick={() => setOpen(false)}>Close</button>
            <button type="button" className="btn-ghost !py-1.5 ml-auto" style={{ color: "var(--color-ember)" }} onClick={() => { if (confirm(`Delete "${t.title}"?`)) void act(() => api(`/admin/tasks/${t.id}`, { method: "DELETE" })); }}>Delete</button>
          </div>
        </form>
      )}
    </li>
  );
}

function ProjectRow({ p, count, owner, act }: { p: Project; count: number; owner: boolean; act: (fn: () => Promise<unknown>) => Promise<void> }) {
  const [name, setName] = useState(p.name);
  const save = (body: Record<string, unknown>) => act(() => api(`/admin/projects/${p.id}`, { method: "PATCH", body }));
  return (
    <li className="panel-2 p-3 grid gap-2 sm:grid-cols-[1fr_auto_auto_auto] items-center text-sm">
      <form className="flex gap-2 items-center" onSubmit={(e) => { e.preventDefault(); if (name.trim() && name !== p.name) void save({ name }); }}>
        <span aria-hidden className="inline-block w-3 h-3 rounded-full shrink-0" style={{ background: COLOUR[p.colour] }} />
        <input className="field !py-1" value={name} onChange={(e) => setName(e.target.value)} onBlur={() => { if (name.trim() && name !== p.name) void save({ name }); }} aria-label="Project name" />
      </form>
      <span className="muted text-xs">{count} open</span>
      <div className="flex gap-2">
        <select className="field !py-1 !w-auto" value={p.status} onChange={(e) => void save({ status: e.target.value })} aria-label="Project status">
          <option value="active">Active</option><option value="paused">Paused</option><option value="done">Done</option>
        </select>
        <select className="field !py-1 !w-auto" value={p.colour} onChange={(e) => void save({ colour: e.target.value })} aria-label="Colour">
          {Object.keys(COLOUR).map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>
      {owner
        ? <button className="btn-ghost !py-1 !px-2 text-xs" style={{ color: "var(--color-ember)" }} onClick={() => { if (confirm(`Delete "${p.name}" and its ${count} open task(s)? This cannot be undone.`)) void act(() => api(`/admin/projects/${p.id}`, { method: "DELETE" })); }}>Delete</button>
        : <span />}
    </li>
  );
}

export default function AdminProjects() {
  const { me } = useSession();
  const { board, error, load, setError } = useBoard();
  const [only, setOnly] = useState<number | null>(null);
  const [showAll, setShowAll] = useState(false);
  const [doneAll, setDoneAll] = useState(false);
  const [quick, setQuick] = useState({ title: "", projectId: "", dueDate: "" });
  const [newProject, setNewProject] = useState("");
  const act = async (fn: () => Promise<unknown>) => { setError(null); try { await fn(); await load(); } catch (e) { setError((e as Error).message); } };
  const shownProjects = useMemo(() => board?.projects.filter((p) => showAll || p.status === "active") ?? [], [board, showAll]);
  if (!isStaff(me)) return <div className="mx-auto max-w-xl px-4 py-10 muted">Admins only.</div>;
  const visible = new Set(shownProjects.map((p) => p.id));
  const tasks = (board?.tasks ?? []).filter((t) => visible.has(t.projectId) && (only == null || t.projectId === only));
  const openCount = (id: number) => (board?.tasks ?? []).filter((t) => t.projectId === id && t.status !== "done").length;
  const projectFor = quick.projectId || (only != null ? String(only) : shownProjects[0] ? String(shownProjects[0].id) : "");
  return (
    <div className="mx-auto max-w-7xl px-4 py-10 grid gap-6">
      <div>
        <h1 className="text-4xl font-bold">Projects</h1>
        <p className="muted mt-1">Everything in the works, on one board. Open a card to edit it; the arrows move it along.</p>
      </div>
      <AdminNav />
      <ErrorLine error={error} />
      {!board ? <p className="muted">Loading...</p> : !board.projects.length ? (
        <Panel title="Start with a project">
          <p className="text-sm muted mb-3">A project is anything with several steps: a book, a film, the build, the campaign. Make one, then add its tasks.</p>
          <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); void act(() => api("/admin/projects", { body: { name: newProject } })).then(() => setNewProject("")); }}>
            <input className="field" required maxLength={80} placeholder="e.g. The kids' book" value={newProject} onChange={(e) => setNewProject(e.target.value)} />
            <button className="btn whitespace-nowrap">Make the project</button>
          </form>
        </Panel>
      ) : (
        <>
          <div className="flex flex-wrap gap-2 items-center text-sm">
            <button className={`btn-ghost !py-1 !px-3 ${only == null ? "accent font-semibold" : ""}`} onClick={() => setOnly(null)}>All projects</button>
            {shownProjects.map((p) => (
              <button key={p.id} className={`btn-ghost !py-1 !px-3 ${only === p.id ? "accent font-semibold" : ""}`} onClick={() => setOnly(p.id)}>
                <Chip p={p} />
              </button>
            ))}
            <label className="flex gap-1.5 items-center muted text-xs ml-auto"><input type="checkbox" checked={showAll} onChange={(e) => setShowAll(e.target.checked)} />Show paused and finished projects</label>
          </div>

          <form className="panel p-3 grid gap-2 sm:grid-cols-[1fr_220px_160px_auto] items-center text-sm" onSubmit={(e) => {
            e.preventDefault();
            void act(() => api("/admin/tasks", { body: { title: quick.title, projectId: Number(projectFor), dueDate: quick.dueDate || null } })).then(() => setQuick({ ...quick, title: "", dueDate: "" }));
          }}>
            <input className="field" required maxLength={200} placeholder="Add a task..." value={quick.title} onChange={(e) => setQuick({ ...quick, title: e.target.value })} aria-label="New task" />
            <select className="field" value={projectFor} onChange={(e) => setQuick({ ...quick, projectId: e.target.value })} aria-label="Project">
              {shownProjects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
            <input className="field" type="date" min={today(-365)} value={quick.dueDate} onChange={(e) => setQuick({ ...quick, dueDate: e.target.value })} aria-label="Due date (optional)" />
            <button className="btn" disabled={!projectFor}>Add</button>
          </form>

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4 items-start">
            {board.statuses.map((s) => {
              let col = tasks.filter((t) => t.status === s);
              if (s === "done") col = [...col].sort((a, b) => (b.doneAt || "").localeCompare(a.doneAt || ""));
              else col = [...col].sort((a, b) => (a.dueDate || "9999").localeCompare(b.dueDate || "9999") || a.sort - b.sort);
              const shown = s === "done" && !doneAll ? col.slice(0, 8) : col;
              return (
                <section key={s} className="panel p-3" aria-label={STATUS_LABEL[s]}>
                  <h2 className="text-lg font-semibold mb-2 flex justify-between">{STATUS_LABEL[s]}<span className="muted text-sm font-normal">{col.length}</span></h2>
                  {col.length ? <ul className="grid gap-2">{shown.map((t) => <Card key={`${t.id}-${t.updatedAt}`} t={t} board={board} act={act} />)}</ul>
                    : <p className="text-xs muted">{s === "blocked" ? "Nothing stuck." : "Nothing here."}</p>}
                  {s === "done" && col.length > shown.length && <button className="text-xs underline mt-2" onClick={() => setDoneAll(true)}>Show all {col.length}</button>}
                  {s === "done" && <p className="text-xs muted mt-2">Finished in the last 90 days.</p>}
                </section>
              );
            })}
          </div>

          <Panel kicker="The projects" title="Rename, pause, finish">
            <ul className="grid gap-2">
              {board.projects.map((p) => <ProjectRow key={`${p.id}-${p.updatedAt}`} p={p} count={openCount(p.id)} owner={me!.role === "admin"} act={act} />)}
            </ul>
            <form className="flex gap-2 mt-3 text-sm" onSubmit={(e) => { e.preventDefault(); void act(() => api("/admin/projects", { body: { name: newProject } })).then(() => setNewProject("")); }}>
              <input className="field" required maxLength={80} placeholder="A new project" value={newProject} onChange={(e) => setNewProject(e.target.value)} />
              <button className="btn-ghost whitespace-nowrap">Add project</button>
            </form>
            {me!.role !== "admin" && <p className="text-xs muted mt-2">Only the owner deletes a project.</p>}
          </Panel>
        </>
      )}
    </div>
  );
}
