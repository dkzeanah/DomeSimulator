// The owner's projects and tasks (/api/admin/projects), shared by the board and the Studio's
// "this week" panel.

import { useCallback, useEffect, useState } from "react";
import { api } from "./api";

export interface Project { id: number; name: string; description: string; status: string; colour: string; sort: number; updatedAt: string }
export interface Task {
  id: number; projectId: number; title: string; status: string; dueDate: string | null; notes: string; link: string | null;
  assigneeId: number | null; assigneeName: string | null; sort: number; createdAt: string; updatedAt: string; doneAt: string | null;
}
export interface Board { projects: Project[]; tasks: Task[]; staff: { id: number; display_name: string }[]; statuses: string[]; colours: string[] }

export const STATUS_LABEL: Record<string, string> = { todo: "To do", doing: "Doing", blocked: "Blocked", done: "Done" };
export const COLOUR: Record<string, string> = {
  gold: "var(--color-gold)", ember: "var(--color-ember)", sky: "var(--color-sky)", leaf: "var(--color-leaf)", stone: "#9aa4b2",
};

/** Today in the viewer's own calendar, YYYY-MM-DD. */
export function today(offsetDays = 0) {
  const d = new Date(Date.now() + offsetDays * 86_400_000);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

/** "overdue", "today", "soon" (within a week) or null, for a task not yet done. */
export function urgency(t: Task): "overdue" | "today" | "soon" | null {
  if (t.status === "done" || !t.dueDate) return null;
  if (t.dueDate < today()) return "overdue";
  if (t.dueDate === today()) return "today";
  return t.dueDate <= today(7) ? "soon" : null;
}

export function dueLabel(t: Task) {
  if (!t.dueDate) return "";
  const u = urgency(t);
  const d = new Date(`${t.dueDate}T12:00:00`).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
  return u === "overdue" ? `overdue, ${d}` : u === "today" ? "due today" : `due ${d}`;
}

/** A link a task points at, as an address the browser can open -- or null for a deliverable's
 *  folder, which lives on the owner's computer (PDFs and films are not in git) and is shown as text. */
export function href(link: string) {
  return link.startsWith("deliverables/") ? null : link;
}

export function useBoard() {
  const [board, setBoard] = useState<Board | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(() => api<Board>("/admin/projects").then((b) => { setBoard(b); setError(null); }).catch((e) => setError(e.message)), []);
  useEffect(() => { void load(); }, [load]);
  return { board, error, load, setError };
}
