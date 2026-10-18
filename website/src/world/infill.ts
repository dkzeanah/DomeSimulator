// The Panel Creator's data: the Triangle Infill tool's 41 ways to fill a dome's triangles, each
// panel type's pieces as the tool meshes and cuts them, each piece's numbers and saw recipe, and
// the forty seats the panels take on the dome -- all written by scripts/portal_spaces_export.py
// from infill/ and two_v_demo.infill_dome. The browser draws and reads; it solves nothing.

import data from "../generated/panel-creator.json";

export const P = data;
export type Way = (typeof P.ways)[number];

export interface Recipe { number: number; name: string; summary: string; dims: string[][]; steps: { kind: string; title: string; text: string }[] }
export interface PieceRow { n: number; name: string; group: string; pose: string; long: number; short: number; cuts: string; note: string; v: [number, number] }
export interface KindTable { kind: number; pieces: PieceRow[]; recipes: Recipe[]; prep?: Recipe | null; metrics: Record<string, number | string>; steps: string[]; fitting: string[] }
export interface WayTable { key: string; title: string; kinds: KindTable[] }
export interface RowsMesh { pos: Int16Array; col: Uint8Array; scale: number; palette: number[][] }

const cache = new Map<string, Promise<unknown>>();
function once<T>(key: string, make: () => Promise<T>): Promise<T> {
  let p = cache.get(key) as Promise<T> | undefined;
  if (!p) { p = make(); p.catch(() => cache.delete(key)); cache.set(key, p); }
  return p;
}

export function loadRows(head: { file: string; vertices: number; scale: number; palette: number[][] }): Promise<RowsMesh> {
  return once(head.file, async () => {
    const r = await fetch(head.file);
    if (!r.ok) throw new Error(`${head.file}: ${r.status}`);
    const buf = await r.arrayBuffer();
    const V = head.vertices;
    return { pos: new Int16Array(buf, 0, V * 3), col: new Uint8Array(buf, V * 6, V), scale: head.scale, palette: head.palette };
  });
}

export const loadTable = (w: Way) => once(w.table, async () => {
  const r = await fetch(w.table);
  if (!r.ok) throw new Error(`${w.table}: ${r.status}`);
  return (await r.json()) as WayTable;
});

export const wayByKey = (key: string) => P.ways.find((w) => w.key === key) ?? P.ways[0];
