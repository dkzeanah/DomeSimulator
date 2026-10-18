// The seam as a climate system and the cell wall, in the browser. The constants, modes, layers and
// weathers come from the desktop modules (scripts/portal_spaces_export.py -> generated/cell-wall.json);
// this file is two_v_demo.seam_climate's dew_point(), decide(), plate_setpoint(), wood_is_safe()
// and cold_channel(), and two_v_demo.cell_wall's profile() and check_scenario(), line for line.
// scripts/test_portal_spaces.mjs checks them against the Python.

import data from "../generated/cell-wall.json";

export const CW = data;
const C: Record<string, number> = Object.fromEntries(CW.climate.constants.map((c) => [c.key, c.value]));
const WC: Record<string, number> = Object.fromEntries(CW.wall.constants.map((c) => [c.key, c.value]));
export const climateConstant = (k: string) => C[k];

/** Python's f"{x:.nf}": to n places, a tie on the float's exact value going to the even digit. */
export function pyFixed(x: number, n: number) {
  const k = 10 ** n, s = x * k, f = Math.floor(s);
  if (s - f === 0.5) { const even = f % 2 === 0 ? f : f + 1; return (even / k).toFixed(n); }
  return x.toFixed(n);
}

export const vapourPressureHpa = (t: number) => 6.112 * Math.exp((C.magnus_a * t) / (C.magnus_b_c + t));
export function dewPoint(t: number, rh: number) {
  const g = Math.log(Math.max(rh, 1e-6)) + (C.magnus_a * t) / (C.magnus_b_c + t);
  return (C.magnus_b_c * g) / (C.magnus_a - g);
}

export interface Sensors { t_in: number; rh_in: number; t_out: number; rh_out: number; t_seam: number; rh_seam: number; wood_mc: number; rain: boolean; harvest: boolean; cooling: boolean }
export interface Decision { mode: string; dp_in: number; dp_out: number; dp_seam: number; reasons: string[] }

/** The owner's three questions, in order, as code (seam_climate.decide). */
export function decide(s: Sensors): Decision {
  const dp_in = dewPoint(s.t_in, s.rh_in), dp_out = dewPoint(s.t_out, s.rh_out), dp_seam = dewPoint(s.t_seam, s.rh_seam);
  const m = C.dp_margin_k;
  const why: string[] = [];
  const done = (mode: string): Decision => ({ mode, dp_in, dp_out, dp_seam, reasons: why });
  const wetFrame = s.wood_mc >= C.mc_wet || s.rh_seam >= C.seam_rh_wet;
  if (s.rain) {
    why.push("raining: shut every exposed intake");
    if (wetFrame) { why.push("frame wet: dry it on its own loop, sealed from the rain"); return done("FRAME_LOOP"); }
    return done("CLOSED");
  }
  if (wetFrame) {
    why.push(`frame wet (seam dew point ${pyFixed(dp_seam, 1)} C)`);
    if (dp_out < dp_seam - m) { why.push("outside air is drier than the seam's: purge it straight back out"); return done("PURGE"); }
    why.push("no outside air dry enough: close the loop through the desiccant");
    return done("FRAME_LOOP");
  }
  const outsideDrier = dp_out < dp_in - m, outsideWetter = dp_out > dp_in + m;
  why.push(`dew point in ${pyFixed(dp_in, 1)} C, out ${pyFixed(dp_out, 1)} C: ` + (outsideDrier ? "outside is drier" : outsideWetter ? "outside is wetter" : "about the same"));
  if (s.rh_in > C.rh_high) {
    if (outsideDrier) {
      if (s.harvest && s.t_out <= dp_in - C.plate_below_dp_k) {
        why.push(`outside skin near ${pyFixed(s.t_out, 0)} C, under the indoor dew point: condense for free, then exhaust`);
        return done("CONDENSE");
      }
      why.push("inside too humid, outside drier: exhaust");
      return done("EXHAUST");
    }
    why.push("inside too humid and outside no help: dehumidify, hold pressure");
    return done("DRY_SUPPLY");
  }
  if (outsideDrier) { why.push("outside air can dry the dome: take it in"); return done("INTAKE"); }
  if (outsideWetter) { why.push("outside air is a moisture source: dry supply only" + (s.cooling ? ", with the cooling running" : "")); return done("DRY_SUPPLY"); }
  return done("IDLE");
}

export const plateSetpoint = (dp: number) => Math.max(C.frost_floor_c, dp - C.plate_below_dp_k);
export function woodIsSafe(tWood: number, dpAir: number, driedFirst: boolean) {
  const dp = driedFirst ? Math.min(dpAir, plateSetpoint(dpAir) + C.plate_approach_k) : dpAir;
  return tWood > dp + C.wood_margin_k;
}
export function coldChannel(tAir = C.indoor_t_c, rhAir = 0.55, belowDp = 17.5) {
  const dp = dewPoint(tAir, rhAir), owners = dp - belowDp, plate = plateSetpoint(dp), after = Math.min(dp, plate + C.plate_approach_k);
  return { t_air: tAir, rh_air: rhAir, dp, below: belowDp, owners_plate: owners, owners_frost: owners <= 0, plate, dp_after: after,
    wood_at_dp_safe_raw: woodIsSafe(dp, dp, false), wood_at_dp_safe_dried: woodIsSafe(dp, dp, true), wood_min_dried: after + C.wood_margin_k };
}

// ---------------------------------------------------------------- the cell wall

export type Layer = (typeof CW.wall.layers)[number];
export const LAYER: Record<string, Layer> = Object.fromEntries(CW.wall.layers.map((l) => [l.key, l]));
export const DEFAULT_STACK = CW.wall.layers.map((l) => l.key);

/** Steady-state winter temperature at the middle of every layer, room to weather (cell_wall.profile). */
export function profile(stack: string[] = DEFAULT_STACK, tOut: number = CW.wall.profileInputs.winter_out_c) {
  const P = CW.wall.profileInputs;
  const resist: [string, number][] = [["room film", P.film_in_rsi]];
  for (const k of stack) resist.push([k, k === "core" ? P.core_rsi : LAYER[k].rsi]);
  resist.push(["outside film", P.film_out_rsi]);
  const total = resist.reduce((s, [, r]) => s + r, 0);
  const q = (P.room_c - tOut) / total;
  let acc = 0;
  return resist.map(([layer, rsi]) => { const mid = acc + rsi / 2; acc += rsi; return { layer, temp_c: P.room_c - q * mid, rsi }; });
}

/** The router's interlocks: the rules a set of layer modes breaks (cell_wall.check_scenario). */
export function checkScenario(modes: Record<string, string>, tOut: number | null = null): string[] {
  const broken: string[] = [];
  for (const [key, mode] of Object.entries(modes)) {
    if (!LAYER[key]) broken.push(`no layer ${key}`);
    else if (!LAYER[key].modes.includes(mode)) broken.push(`${key} cannot be ${mode}`);
  }
  const on: Record<string, string> = Object.fromEntries(Object.entries(modes).filter(([, m]) => m !== "off"));
  if (on.fog === "fog" && (on.air_in === "supply" || on.air_in === "exhaust")) broken.push("fog with the air layer running pushes it out or dilutes it");
  if (on.fog === "fog" && on.filter) broken.push("fog must never reach the intake filter");
  if (on.water === "flood" && on.filter) broken.push("no outside air in during a wildfire: smoke");
  if (on.water === "flood" && on.vacuum) broken.push("a clamp beside a flooded layer pulls water through any leak");
  if (on.airbag === "inflate" && on.vacuum) broken.push("the clamp would fight the bladders");
  if (on.core && on.vacuum !== "clamp") broken.push("injected glue or foam needs the clamp on while it cures");
  if (tOut !== null && tOut <= 0 && ["capture", "flood", "circulate"].includes(on.water)) broken.push("the water layer freezes below 0 C outside");
  return broken;
}

export const wallConstant = (k: string) => WC[k];
