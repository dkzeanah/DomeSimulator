// The 3D Wedge Method's data: the raw-wedge simulator's (geodesic_raw_wedge_dome_dihedral.py)
// own solved dome for each wedge orientation, its jig walk-through, and its cut and seam tables
// over a grid of long edges and trunks -- all written by scripts/portal_tools_export.py. The
// browser solves nothing here; it draws and reads what the simulator solved.

import data from "../generated/wedge-method.json";

export const W = data;
export type Orientation = string;
export type Summary = (typeof W.grid)[keyof typeof W.grid];
export type MeshHead = typeof W.meshes.point_dome_in;
export type JigHead = typeof W.jig;

export const summary = (o: Orientation, longEdge: number, trunk: number): Summary =>
  (W.grid as Record<string, Summary>)[`${o}|${longEdge}|${trunk}`];

export interface MeshBuffers { pos: Int16Array; col: Uint8Array; idx: Uint16Array }

const loaded = new Map<string, Promise<MeshBuffers>>();

/** One of the simulator's mesh files: int16 positions, a colour index per vertex, uint16 triangles. */
export function loadMesh(head: { file: string; vertices: number; indices: number }): Promise<MeshBuffers> {
  let p = loaded.get(head.file);
  if (!p) {
    p = fetch(head.file).then((r) => { if (!r.ok) throw new Error(`${head.file}: ${r.status}`); return r.arrayBuffer(); }).then((buf) => {
      const V = head.vertices;
      const off = V * 6 + V + (V % 2);
      return { pos: new Int16Array(buf, 0, V * 3), col: new Uint8Array(buf, V * 6, V), idx: new Uint16Array(buf, off, head.indices) };
    });
    p.catch(() => loaded.delete(head.file));
    loaded.set(head.file, p);
  }
  return p;
}
