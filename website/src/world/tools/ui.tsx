// The small controls the tool panels share: a stepped dial, a row of choices, a check box, a
// figure row and a section heading, in the Dome Creator panel's look.

import type { ReactNode } from "react";

export function Dial({ label, values, value, onChange, show }: { label: string; values: number[]; value: number; onChange: (v: number) => void; show: (v: number) => string }) {
  const i = Math.max(0, values.findIndex((v) => Math.abs(v - value) < 1e-9));
  return (
    <label className="grid gap-0.5 text-xs">
      <span className="flex justify-between"><span className="muted">{label}</span><span className="num font-semibold">{show(values[i])}</span></span>
      <input type="range" min={0} max={values.length - 1} step={1} value={i} onChange={(e) => onChange(values[Number(e.target.value)])} />
    </label>
  );
}

export function Choice<T extends string>({ label, value, options, onChange, colour }: { label?: string; value: T; options: [T, string][]; onChange: (v: T) => void; colour: string }) {
  return (
    <div className="grid gap-0.5 text-xs">
      {label && <span className="muted">{label}</span>}
      <div className="flex flex-wrap gap-1" role="group" aria-label={label}>
        {options.map(([v, text]) => (
          <button key={v} className={`btn-ghost !py-1 !px-2 text-xs ${value === v ? "font-semibold" : "muted"}`} aria-pressed={value === v}
            style={value === v ? { borderColor: colour, color: colour } : undefined} onClick={() => onChange(v)}>{text}</button>
        ))}
      </div>
    </div>
  );
}

export function Check({ label, value, onChange }: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  return <label className="flex items-center gap-1.5 text-xs"><input type="checkbox" checked={value} onChange={(e) => onChange(e.target.checked)} />{label}</label>;
}

export function Row({ k, v }: { k: string; v: ReactNode }) {
  return <div className="flex justify-between gap-2 py-0.5 border-b text-xs" style={{ borderColor: "var(--line)" }}><span className="muted">{k}</span><span className="num font-semibold text-right">{v}</span></div>;
}

export function Head({ children }: { children: ReactNode }) {
  return <p className="text-xs font-semibold mt-1">{children}</p>;
}

export const ftIn = (inches: number) => {
  const ft = Math.floor(inches / 12), rest = inches - ft * 12;
  return ft ? `${ft} ft ${rest.toFixed(1)} in` : `${rest.toFixed(1)} in`;
};
