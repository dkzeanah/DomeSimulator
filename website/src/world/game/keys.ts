// The live shortcut list. Anything that adds keys -- the world, the game interface, a tool's
// panel -- registers them here while it is on screen, and the Keys tab shows exactly what
// works right now.

import { useEffect, useState } from "react";

export interface Key { keys: string; does: string }
const scopes = new Map<string, Key[]>();
const subs = new Set<() => void>();

export function registerKeys(scope: string, list: Key[]) {
  scopes.set(scope, list);
  subs.forEach((f) => f());
  return () => { if (scopes.get(scope) === list) { scopes.delete(scope); subs.forEach((f) => f()); } };
}

export function useKeyList(): [string, Key[]][] {
  const [, bump] = useState(0);
  useEffect(() => { const f = () => bump((n) => n + 1); subs.add(f); return () => { subs.delete(f); }; }, []);
  return [...scopes.entries()];
}

/** True when a key press belongs to a text box, not to the world. */
export const typing = (e: KeyboardEvent) => Boolean((e.target as HTMLElement)?.closest?.("input, textarea, select, [contenteditable]"));
