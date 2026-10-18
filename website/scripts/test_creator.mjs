// The Portal's Dome Creator against the desktop Dome Creator: 160 designs, each built by
// dome_model.DomeModel and by src/world/creator.ts, every figure compared.
//
//   npm run test:creator          (asks the Creator for fresh cases, then compares)
//   node scripts/test_creator.mjs <file>   (cases already written by creator_export.py --fixtures)
import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { build } from "esbuild";

const site = resolve(import.meta.dirname, "..");
const temp = await mkdtemp(join(tmpdir(), "creator-"));
let file = process.argv[2];
if (!file) {
  // no cases given: the desktop Creator makes them now, from the tables as they stand
  file = join(temp, "fixtures.json");
  const { execFileSync } = await import("node:child_process");
  execFileSync("py", ["-3.12", join(site, "scripts", "creator_export.py"), "--fixtures", file], { stdio: "inherit" });
}
const cases = JSON.parse(await readFile(file, "utf8"));
const out = join(temp, "creator.mjs");
try {
  await build({ entryPoints: [join(site, "src/world/creator.ts")], bundle: true, platform: "node", format: "esm", outfile: out, logLevel: "silent" });
  const { design } = await import(pathToFileURL(out).href);
  const pairs = [["height", "height"], ["floor_area", "floorArea"], ["surface_area", "surfaceArea"], ["strut_count", "strutCount"],
    ["strut_total_len", "strutTotalLen"], ["hub_count", "hubCount"], ["panel_count", "panelCount"], ["frame_weight", "frameWeight"],
    ["frame_cost", "frameCost"], ["hub_weight", "hubWeight"], ["hub_cost", "hubCost"], ["panel_weight", "panelWeight"],
    ["panel_cost", "panelCost"], ["foundation_area", "foundationArea"], ["foundation_weight", "foundationWeight"],
    ["foundation_cost", "foundationCost"], ["structure_weight", "structureWeight"], ["total_cost", "totalCost"],
    ["solar_watts", "solarWatts"], ["bolt_count", "boltCount"], ["trees_required", "treesRequired"]];
  let checks = 0, worst = 0;
  for (const [i, c] of cases.entries()) {
    const d = design(c.config);
    for (const [py, ts] of pairs) {
      const want = c.answers[py], got = d[ts];
      const tol = Math.max(1e-6, Math.abs(want) * 1e-6);
      worst = Math.max(worst, Math.abs(got - want) / Math.max(1, Math.abs(want)));
      assert.ok(Math.abs(got - want) <= tol, `case ${i} ${py}: Creator ${want}, Portal ${got} (${JSON.stringify(c.config)})`);
      checks++;
    }
    assert.deepEqual(d.strutClasses.map((s) => [s.name, s.length, s.count]), c.strutClasses, `case ${i} strut classes`);
    checks++;
    // the fit-out the Portal leaves out really is zero for these designs
    for (const k of ["wall_cost", "wire_cost", "plumbing_cost", "prop_cost"]) assert.equal(c.answers[k], 0, `case ${i} ${k}`);
  }
  console.log(`PASS ${checks} checks over ${cases.length} designs; largest relative difference ${worst.toExponential(2)}`);
} finally {
  await rm(temp, { recursive: true, force: true });
}
