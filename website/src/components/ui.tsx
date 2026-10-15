// The panels the site is built from. Each one has a visible state; together they snap
// into pages the way panels snap into a dome.

import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { JOIN_STEPS, useSession } from "../lib/session";

export function Panel({ title, kicker, children, className = "" }: { title?: ReactNode; kicker?: string; children: ReactNode; className?: string }) {
  return (
    <section className={`panel p-5 sm:p-6 ${className}`}>
      {kicker && <p className="text-xs font-semibold uppercase tracking-[0.18em] accent mb-1">{kicker}</p>}
      {title && <h2 className="text-2xl sm:text-3xl font-semibold mb-3">{title}</h2>}
      {children}
    </section>
  );
}

/** A real fraction, rendered: where you are over where you need to be. */
export function Fraction({ have, need, label, unit = "" }: { have: number; need: number; label: string; unit?: string }) {
  const pct = need > 0 ? Math.min(100, (have / need) * 100) : 0;
  const [w, setW] = useState(0);
  useEffect(() => { const t = window.setTimeout(() => setW(pct), 60); return () => window.clearTimeout(t); }, [pct]);
  return (
    <div>
      <div className="flex items-baseline justify-between gap-3 text-sm mb-1.5">
        <span>{label}</span>
        <span className="num font-semibold">{unit}{have.toLocaleString()} <span className="muted">/ {unit}{need.toLocaleString()}</span></span>
      </div>
      <div className="xp-track" role="progressbar" aria-valuenow={have} aria-valuemax={need} aria-label={label}>
        <div className="xp-fill" style={{ width: `${w}%` }} />
      </div>
    </div>
  );
}

export function Stat({ value, label, note }: { value: ReactNode; label: string; note?: string }) {
  return (
    <div className="panel-2 p-4">
      <div className="num text-3xl font-semibold accent">{value}</div>
      <div className="text-sm mt-1">{label}</div>
      {note && <div className="text-xs muted mt-1">{note}</div>}
    </div>
  );
}

/** "You can now ..." -- the unlock message real life never sends. */
export function Toast() {
  const { toast } = useSession();
  if (!toast) return null;
  return (
    <div role="status" className="toast fixed bottom-4 left-4 right-4 sm:left-auto sm:w-96 z-50 panel p-4 shadow-2xl" style={{ borderColor: "var(--accent)" }}>
      <p className="text-xs uppercase tracking-[0.18em] accent font-semibold">{toast.title}</p>
      <p className="mt-1">{toast.body}</p>
    </div>
  );
}

/** The visitor's own quest, everywhere it helps. */
export function JoinQuest({ compact = false }: { compact?: boolean }) {
  const { steps } = useSession();
  const done = JOIN_STEPS.filter((s) => steps[s.key]).length;
  const next = JOIN_STEPS.find((s) => !steps[s.key]);
  const href: Record<string, string> = { read: "/book", sample: "/sample", account: "/account", network: "/network" };
  return (
    <div className={compact ? "" : "panel p-5"}>
      <Fraction have={done} need={JOIN_STEPS.length} label="Quest: join the build" />
      <ol className="mt-3 space-y-1.5 text-sm">
        {JOIN_STEPS.map((s) => (
          <li key={s.key} className="flex items-center gap-2">
            <span aria-hidden className={`inline-block w-3 h-3 tri ${steps[s.key] ? "bg-[var(--accent)]" : "bg-[var(--line)]"}`} />
            {steps[s.key] ? <span className="muted line-through">{s.label}</span> : <Link className="underline underline-offset-4" to={href[s.key]}>{s.label}</Link>}
          </li>
        ))}
      </ol>
      {next ? <p className="text-xs muted mt-3">Next unlocks: {next.unlock}.</p> : <p className="text-xs accent mt-3">Quest complete. You are part of the build.</p>}
    </div>
  );
}

export function ErrorLine({ error }: { error: string | null }) {
  return error ? <p role="alert" className="text-sm mt-2" style={{ color: "var(--color-ember)" }}>{error}</p> : null;
}

/** A field bots fill and people never see. */
export function Honeypot({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <label aria-hidden className="absolute -left-[9999px] w-px h-px overflow-hidden">
      Website <input tabIndex={-1} autoComplete="off" value={value} onChange={(e) => onChange(e.target.value)} />
    </label>
  );
}
