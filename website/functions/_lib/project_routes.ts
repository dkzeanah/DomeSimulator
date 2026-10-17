// The owner's projects and tasks: Admin -> Projects (the board) and the Studio's "this week".
// Owner and managers add and change them; only the owner deletes a whole project. Every change
// is in the audit log, and a task being added or finished is an event automations can use.

import { requireAdmin, requireOwner } from "./auth";
import { Ctx, HttpError, body, json, nowIso, text } from "./http";
import { audit, emit } from "./ops";
import api from "./routes";

export const PROJECT_STATUSES = ["active", "paused", "done"] as const;
export const TASK_STATUSES = ["todo", "doing", "blocked", "done"] as const;
export const COLOURS = ["gold", "ember", "sky", "leaf", "stone"] as const;

interface ProjectRow { id: number; name: string; description: string; status: string; colour: string; sort: number; created_at: string; updated_at: string }
interface TaskRow {
  id: number; project_id: number; title: string; status: string; due_date: string | null; notes: string; link: string | null;
  assignee_id: number | null; sort: number; created_by: number | null; created_at: string; updated_at: string; done_at: string | null;
}

const DAY = /^\d{4}-\d{2}-\d{2}$/;

function oneOf<T extends readonly string[]>(v: unknown, allowed: T, field: string): T[number] {
  const s = String(v ?? "");
  if (!(allowed as readonly string[]).includes(s)) throw new HttpError(400, `${field} is one of ${allowed.join(", ")}.`);
  return s as T[number];
}

function dueDate(v: unknown): string | null {
  if (v === null || v === undefined || v === "") return null;
  const s = String(v);
  if (!DAY.test(s) || Number.isNaN(Date.parse(`${s}T00:00:00Z`))) throw new HttpError(400, "dueDate is a day, YYYY-MM-DD.");
  return s;
}

function link(b: Record<string, unknown>): string | null {
  const s = text(b, "link", { max: 500 });
  if (!s) return null;
  if (!/^(https?:\/\/|\/|deliverables\/)/.test(s)) throw new HttpError(400, "link is a page on this site (/book), a deliverable (deliverables/...), or an https:// address.");
  return s;
}

const toProject = (p: ProjectRow) => ({ id: p.id, name: p.name, description: p.description, status: p.status, colour: p.colour, sort: p.sort, updatedAt: p.updated_at });
const toTask = (t: TaskRow & { assignee_name?: string | null }) => ({
  id: t.id, projectId: t.project_id, title: t.title, status: t.status, dueDate: t.due_date, notes: t.notes, link: t.link,
  assigneeId: t.assignee_id, assigneeName: t.assignee_name ?? null, sort: t.sort, createdAt: t.created_at, updatedAt: t.updated_at, doneAt: t.done_at,
});

async function taskOf(ctx: Ctx, id: number) {
  const t = await ctx.env.DB.prepare("SELECT * FROM tasks WHERE id = ?").bind(id).first<TaskRow>();
  if (!t) throw new HttpError(404, "No such task.");
  return t;
}

async function staffId(ctx: Ctx, v: unknown): Promise<number | null> {
  if (v === null || v === undefined || v === "") return null;
  const id = Number(v);
  const u = await ctx.env.DB.prepare("SELECT id FROM users WHERE id = ? AND role IN ('admin', 'manager')").bind(id).first();
  if (!u) throw new HttpError(400, "A task is given to the owner or a manager.");
  return id;
}

/** Everything the board needs at once: projects, their tasks, and who can be given one. */
api.get("/admin/projects", async (ctx) => {
  requireAdmin(ctx);
  const db = ctx.env.DB;
  const projects = (await db.prepare("SELECT * FROM projects ORDER BY status = 'done', sort, id").all<ProjectRow>()).results;
  // finished tasks older than ninety days stay in the database but leave the board
  const tasks = (await db.prepare(
    "SELECT tasks.*, users.display_name assignee_name FROM tasks LEFT JOIN users ON users.id = tasks.assignee_id "
    + "WHERE tasks.status != 'done' OR tasks.done_at >= ? ORDER BY tasks.sort, tasks.id",
  ).bind(nowIso(-90 * 86_400_000)).all<TaskRow & { assignee_name: string | null }>()).results;
  const staff = (await db.prepare("SELECT id, display_name FROM users WHERE role IN ('admin', 'manager') AND status = 'active' ORDER BY role = 'admin' DESC, display_name").all()).results;
  return json({ projects: projects.map(toProject), tasks: tasks.map(toTask), staff, statuses: TASK_STATUSES, colours: COLOURS });
});

api.post("/admin/projects", async (ctx) => {
  requireAdmin(ctx);
  const b = await body(ctx);
  const name = text(b, "name", { min: 1, max: 80, required: true })!;
  const colour = b.colour ? oneOf(b.colour, COLOURS, "colour") : "gold";
  const sort = (await ctx.env.DB.prepare("SELECT COALESCE(MAX(sort), 0) + 1 n FROM projects").first<{ n: number }>())!.n;
  const r = await ctx.env.DB.prepare("INSERT INTO projects(name, description, colour, sort, created_at, updated_at) VALUES(?, ?, ?, ?, ?, ?) RETURNING *")
    .bind(name, text(b, "description", { max: 1000 }) || "", colour, sort, nowIso(), nowIso()).first<ProjectRow>();
  await audit(ctx, "project.create", `project:${r!.id}`, { name });
  return json({ project: toProject(r!) }, 201);
});

api.patch("/admin/projects/:id", async (ctx) => {
  requireAdmin(ctx);
  const b = await body(ctx);
  const sets: string[] = [], vals: unknown[] = [];
  if ("name" in b) { sets.push("name = ?"); vals.push(text(b, "name", { min: 1, max: 80, required: true })); }
  if ("description" in b) { sets.push("description = ?"); vals.push(text(b, "description", { max: 1000 }) || ""); }
  if ("status" in b) { sets.push("status = ?"); vals.push(oneOf(b.status, PROJECT_STATUSES, "status")); }
  if ("colour" in b) { sets.push("colour = ?"); vals.push(oneOf(b.colour, COLOURS, "colour")); }
  if ("sort" in b) { sets.push("sort = ?"); vals.push(Math.round(Number(b.sort) || 0)); }
  if (!sets.length) throw new HttpError(400, "Nothing to change.");
  sets.push("updated_at = ?"); vals.push(nowIso());
  const r = await ctx.env.DB.prepare(`UPDATE projects SET ${sets.join(", ")} WHERE id = ? RETURNING *`).bind(...vals, Number(ctx.params.id)).first<ProjectRow>();
  if (!r) throw new HttpError(404, "No such project.");
  await audit(ctx, "project.edit", `project:${r.id}`, b);
  return json({ project: toProject(r) });
});

/** The owner alone deletes a project, and its tasks go with it. */
api.delete("/admin/projects/:id", async (ctx) => {
  requireOwner(ctx);
  const id = Number(ctx.params.id);
  const p = await ctx.env.DB.prepare("SELECT name, (SELECT COUNT(*) FROM tasks WHERE project_id = projects.id) n FROM projects WHERE id = ?").bind(id).first<{ name: string; n: number }>();
  if (!p) throw new HttpError(404, "No such project.");
  await ctx.env.DB.prepare("DELETE FROM tasks WHERE project_id = ?").bind(id).run();
  await ctx.env.DB.prepare("DELETE FROM projects WHERE id = ?").bind(id).run();
  await audit(ctx, "project.delete", `project:${id}`, { name: p.name, tasks: p.n });
  return json({ ok: true });
});

api.post("/admin/tasks", async (ctx) => {
  const u = requireAdmin(ctx);
  const b = await body(ctx);
  const projectId = Number(b.projectId);
  const p = await ctx.env.DB.prepare("SELECT id, name FROM projects WHERE id = ?").bind(projectId).first<{ id: number; name: string }>();
  if (!p) throw new HttpError(400, "projectId names no project.");
  const title = text(b, "title", { min: 1, max: 200, required: true })!;
  const status = b.status ? oneOf(b.status, TASK_STATUSES, "status") : "todo";
  const sort = (await ctx.env.DB.prepare("SELECT COALESCE(MAX(sort), 0) + 1 n FROM tasks WHERE project_id = ?").bind(projectId).first<{ n: number }>())!.n;
  const r = await ctx.env.DB.prepare(
    "INSERT INTO tasks(project_id, title, status, due_date, notes, link, assignee_id, sort, created_by, created_at, updated_at, done_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING *",
  ).bind(projectId, title, status, dueDate(b.dueDate), text(b, "notes", { max: 4000 }) || "", link(b), await staffId(ctx, b.assigneeId), sort, u.id,
    nowIso(), nowIso(), status === "done" ? nowIso() : null).first<TaskRow>();
  await audit(ctx, "task.create", `task:${r!.id}`, { project: p.name, title });
  await emit(ctx, "task.created", { taskId: r!.id, project: p.name, title, due: r!.due_date ?? "" });
  return json({ task: toTask(r!) }, 201);
});

api.patch("/admin/tasks/:id", async (ctx) => {
  requireAdmin(ctx);
  const t = await taskOf(ctx, Number(ctx.params.id));
  const b = await body(ctx);
  const sets: string[] = [], vals: unknown[] = [];
  if ("title" in b) { sets.push("title = ?"); vals.push(text(b, "title", { min: 1, max: 200, required: true })); }
  if ("notes" in b) { sets.push("notes = ?"); vals.push(text(b, "notes", { max: 4000 }) || ""); }
  if ("link" in b) { sets.push("link = ?"); vals.push(link(b)); }
  if ("dueDate" in b) { sets.push("due_date = ?"); vals.push(dueDate(b.dueDate)); }
  if ("assigneeId" in b) { sets.push("assignee_id = ?"); vals.push(await staffId(ctx, b.assigneeId)); }
  if ("sort" in b) { sets.push("sort = ?"); vals.push(Math.round(Number(b.sort) || 0)); }
  if ("projectId" in b) {
    const p = await ctx.env.DB.prepare("SELECT id FROM projects WHERE id = ?").bind(Number(b.projectId)).first();
    if (!p) throw new HttpError(400, "projectId names no project.");
    sets.push("project_id = ?"); vals.push(Number(b.projectId));
  }
  let finished = false;
  if ("status" in b) {
    const s = oneOf(b.status, TASK_STATUSES, "status");
    sets.push("status = ?"); vals.push(s);
    sets.push("done_at = ?"); vals.push(s === "done" ? (t.done_at || nowIso()) : null);
    finished = s === "done" && t.status !== "done";
  }
  if (!sets.length) throw new HttpError(400, "Nothing to change.");
  sets.push("updated_at = ?"); vals.push(nowIso());
  const r = await ctx.env.DB.prepare(`UPDATE tasks SET ${sets.join(", ")} WHERE id = ? RETURNING *`).bind(...vals, t.id).first<TaskRow>();
  await audit(ctx, "task.edit", `task:${t.id}`, b);
  if (finished) {
    const p = await ctx.env.DB.prepare("SELECT name FROM projects WHERE id = ?").bind(r!.project_id).first<{ name: string }>();
    await emit(ctx, "task.done", { taskId: t.id, project: p?.name ?? "", title: r!.title });
  }
  return json({ task: toTask(r!) });
});

api.delete("/admin/tasks/:id", async (ctx) => {
  requireAdmin(ctx);
  const t = await taskOf(ctx, Number(ctx.params.id));
  await ctx.env.DB.prepare("DELETE FROM tasks WHERE id = ?").bind(t.id).run();
  await audit(ctx, "task.delete", `task:${t.id}`, { title: t.title });
  return json({ ok: true });
});
