// Who is signed in, and the visitor's own quest -- "Join the build" -- whose steps tick
// only when the visitor really does them (in this browser, or on their account).

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "./api";

export interface Me { id: number; email: string; displayName: string; role: string; bio: string; city: string; region: string; country: string; publicProfile: boolean }

export const JOIN_STEPS = [
  { key: "read", label: "Read what the book proves", unlock: "the free sample" },
  { key: "sample", label: "Get the free sample", unlock: "an account of your own" },
  { key: "account", label: "Make an account", unlock: "the pad network and your life account" },
  { key: "network", label: "Put yourself on the network", unlock: "your place on the map" },
] as const;
export type StepKey = (typeof JOIN_STEPS)[number]["key"];

interface Session {
  me: Me | null;
  refresh: () => Promise<void>;
  setMe: (m: Me | null) => void;
  steps: Record<StepKey, boolean>;
  mark: (k: StepKey) => void;
  toast: { title: string; body: string } | null;
  notify: (title: string, body: string) => void;
}

const Ctx = createContext<Session | null>(null);
const STORE = "zl.join.v1";

function load(): Record<StepKey, boolean> {
  try {
    return { read: false, sample: false, account: false, network: false, ...JSON.parse(localStorage.getItem(STORE) || "{}") };
  } catch {
    return { read: false, sample: false, account: false, network: false };
  }
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [steps, setSteps] = useState(load);
  const [toast, setToast] = useState<Session["toast"]>(null);

  const notify = useCallback((title: string, body: string) => {
    setToast({ title, body });
    window.setTimeout(() => setToast(null), 5200);
  }, []);

  const mark = useCallback((k: StepKey) => {
    setSteps((s) => {
      if (s[k]) return s;
      const next = { ...s, [k]: true };
      try { localStorage.setItem(STORE, JSON.stringify(next)); } catch { /* private mode: the tick lasts the visit */ }
      const step = JOIN_STEPS.find((x) => x.key === k)!;
      const done = Object.values(next).filter(Boolean).length;
      notify(`Quest progress ${done}/${JOIN_STEPS.length}`, `You can now: ${step.unlock}.`);
      return next;
    });
  }, [notify]);

  const refresh = useCallback(async () => {
    const r = await api<{ user: Me | null }>("/me").catch(() => ({ user: null }));
    setMe(r.user);
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  // An account that already did a step ticks it, on any device.
  useEffect(() => {
    if (!me) return;
    if (!steps.account) mark("account");
    api<{ checks: Record<string, boolean> }>("/me/standing").then(({ checks }) => {
      if (checks.readTheSample) mark("sample");
      if (checks.onTheNetwork) mark("network");
    }).catch(() => undefined);
  }, [me]); // eslint-disable-line react-hooks/exhaustive-deps

  return <Ctx.Provider value={{ me, refresh, setMe, steps, mark, toast, notify }}>{children}</Ctx.Provider>;
}

export function useSession() {
  const s = useContext(Ctx);
  if (!s) throw new Error("useSession outside SessionProvider");
  return s;
}
