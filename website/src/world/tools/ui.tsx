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

/** A studio's sections: a row of tabs and the one that is open. */
export function Tabs<T extends string>({ tabs, value, onChange, colour }: { tabs: [T, string][]; value: T; onChange: (v: T) => void; colour: string }) {
  return (
    <div className="flex flex-wrap gap-1 border-b pb-1.5" role="tablist" style={{ borderColor: "var(--line)" }}>
      {tabs.map(([v, text]) => (
        <button key={v} role="tab" aria-selected={value === v} className={`px-2 py-1 text-xs rounded-t ${value === v ? "font-semibold" : "muted"}`}
          style={value === v ? { color: colour, boxShadow: `inset 0 -2px 0 ${colour}` } : undefined} onClick={() => onChange(v)}>{text}</button>
      ))}
    </div>
  );
}

export function Select({ label, value, options, onChange, disabled }: { label: string; value: string; options: (string | [string, string])[]; onChange: (v: string) => void; disabled?: boolean }) {
  return (
    <label className="grid gap-0.5 text-xs">
      <span className="muted">{label}</span>
      <select className="field !py-1 text-sm" value={value} disabled={disabled} onChange={(e) => onChange(e.target.value)}>
        {options.map((o) => { const [v, t] = typeof o === "string" ? [o, o] : o; return <option key={v} value={v}>{t}</option>; })}
      </select>
    </label>
  );
}

/** A count with minus and plus. */
export function Stepper({ label, value, min = 0, max = 99, onChange, note }: { label: string; value: number; min?: number; max?: number; onChange: (v: number) => void; note?: string }) {
  return (
    <div className="flex items-center justify-between gap-2 text-xs py-0.5">
      <span className="muted">{label}{note && <span className="opacity-70"> {note}</span>}</span>
      <span className="flex items-center gap-1">
        <button className="btn-ghost !py-0 !px-1.5" aria-label={`Fewer ${label}`} disabled={value <= min} onClick={() => onChange(Math.max(min, value - 1))}>&minus;</button>
        <span className="num w-6 text-center font-semibold">{value}</span>
        <button className="btn-ghost !py-0 !px-1.5" aria-label={`More ${label}`} disabled={value >= max} onClick={() => onChange(Math.min(max, value + 1))}>+</button>
      </span>
    </div>
  );
}

/** Save a text file to the visitor's computer. */
export function download(name: string, text: string, type = "application/json") {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement("a"); a.href = url; a.download = name; a.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 2000);
}

export const ftIn = (inches: number) => {
  const ft = Math.floor(inches / 12), rest = inches - ft * 12;
  return ft ? `${ft} ft ${rest.toFixed(1)} in` : `${rest.toFixed(1)} in`;
};
