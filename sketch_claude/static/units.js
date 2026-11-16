// Units: every number Dome Sketch shows goes through here, in the viewer's choice of
// metres, feet and inches, or inches. The model is always in metres; text from the solver
// carries unit tokens -- {m:1.234}, {m2:..}, {L:..}, {kg:..}, {kPa:..}, {MPa:..}, {deg:..} --
// that tokens() formats, so switching units re-labels everything without re-solving.

const IN = 0.0254, FT = 0.3048;
const KEY = "dome-sketch-units";
export const MODES = [["m", "m"], ["ftin", "ft-in"], ["in", "in"]];

let mode = "ftin";
try { mode = localStorage.getItem(KEY) || mode; } catch { /* private window: the default */ }
if (!MODES.some(([k]) => k === mode)) mode = "ftin";
const listeners = [];

export function get() { return mode; }
export function set(m) {
  if (!MODES.some(([k]) => k === m) || m === mode) return;
  mode = m;
  try { localStorage.setItem(KEY, m); } catch { /* not remembered */ }
  for (const f of listeners) f(m);
}
export function onChange(f) { listeners.push(f); }

function gcd(a, b) { return b ? gcd(b, a % b) : a; }
function frac16(x) {
  // whole inches and the nearest sixteenth: [whole, "1/8"]
  let s = Math.round(Math.abs(x) * 16), whole = Math.floor(s / 16), f = s % 16;
  if (!f) return [whole, ""];
  const g = gcd(f, 16);
  return [whole, `${f / g}/${16 / g}`];
}

export function ftin(m) {
  const neg = m < 0, inches = Math.abs(m) / IN;
  let [whole, f] = frac16(inches);
  const ft = Math.floor(whole / 12), inch = whole % 12;
  // 7' 0-1/8", 5' 10-1/8", 3/4", 0"
  const ins = f ? (inch || ft ? `${inch}-${f}` : f) : `${inch}`;
  return (neg ? "-" : "") + (ft ? `${ft}' ` : "") + `${ins}"`;
}

export function inches(m) {
  const neg = m < 0, [whole, f] = frac16(Math.abs(m) / IN);
  return `${neg ? "-" : ""}${whole.toLocaleString()}${f ? ` ${f}` : ""} in`;
}

export function mm(m) { return `${Math.round(m * 1000).toLocaleString()} mm`; }

/** A length, in the viewer's units. */
export function len(m) {
  if (m === null || m === undefined || !isFinite(m)) return "";
  if (mode === "m") return Math.abs(m) < 2 ? mm(m) : `${m.toFixed(3)} m`;
  if (mode === "in") return inches(m);
  return ftin(m);
}
export function area(m2) {
  return mode === "m" ? `${m2.toFixed(m2 < 10 ? 3 : 1)} m²` : `${(m2 * 10.7639).toFixed(m2 < 1 ? 2 : 1)} ft²`;
}
export function vol(L) {
  return mode === "m" ? `${Math.round(L).toLocaleString()} L` : `${Math.round(L / 3.78541).toLocaleString()} gal`;
}
export function mass(kg) {
  return mode === "m" ? `${Math.round(kg).toLocaleString()} kg` : `${Math.round(kg * 2.20462).toLocaleString()} lb`;
}
export function kpa(k) { return mode === "m" ? `${k.toFixed(1)} kPa` : `${(k * 0.145038).toFixed(2)} psi`; }
export function mpa(v) { return mode === "m" ? `${v.toFixed(1)} MPa` : `${(v * 0.145038).toFixed(2)} ksi`; }
export function deg(a, n = 1) { return `${(+a).toFixed(n)}°`; }

const TOKEN = /\{(m|m2|L|kg|kPa|MPa|deg):(-?[0-9.]+(?:e[-+]?[0-9]+)?)\}/gi;
const FMT = { m: len, m2: area, L: vol, kg: mass, kPa: kpa, MPa: mpa, deg: (v) => deg(v) };
/** Solver text with its unit tokens formatted. */
export function tokens(text) {
  return String(text ?? "").replace(TOKEN, (_, k, v) => (FMT[k] || FMT[k.toLowerCase()] || String)(parseFloat(v)));
}

// Form inputs: lengths are typed in metres, feet or inches. In feet-and-inches, a field for a
// small size (a log, a plate, a flue: max under 1.5 m) takes inches, the way a builder says it.
const small = (f) => !!f && f.max !== undefined && f.max <= 1.5;
export function inputUnit(f) { return mode === "m" ? "m" : mode === "in" || small(f) ? "in" : "ft"; }
export function toInput(m, f) {
  const u = inputUnit(f);
  if (u === "m") return +(+m).toFixed(4);
  if (u === "in") return +(m / IN).toFixed(3);
  return +(m / FT).toFixed(3);
}
export function fromInput(v, f) {
  const x = parseFloat(v), u = inputUnit(f);
  if (!isFinite(x)) return NaN;
  return u === "m" ? x : u === "in" ? x * IN : x * FT;
}
export function inputStep(f) {
  const u = inputUnit(f);
  if (u === "m") return (f && f.step) || 0.01;
  return u === "in" ? 0.0625 : 0.05;
}

/** Info keys say their unit by their ending (_m, _m2, _deg, _kg, _l). */
export function infoValue(k, v) {
  if (typeof v === "number") {
    if (k.endsWith("_m")) return len(v);
    if (k.endsWith("_m2")) return area(v);
    if (k.endsWith("_deg")) return deg(v);
    if (k.endsWith("_kg")) return mass(v);
    if (k.endsWith("_l")) return vol(v);
    return Number.isInteger(v) ? v.toLocaleString() : v.toFixed(3);
  }
  return tokens(String(v));
}
export function infoLabel(k) {
  const s = k.replace(/_(m|m2|deg|kg|l)$/, "").replace(/_/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
}
