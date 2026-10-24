// The Portal's Dome Creator against the desktop Dome Creator: 240 designs, each built by
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
    ["solar_watts", "solarWatts"], ["bolt_count", "boltCount"], ["trees_required", "treesRequired"],
    ["layer_weight", "layerWeight"], ["layer_cost", "layerCost"], ["wall_area", "wallArea"], ["wall_weight", "wallWeight"],
    ["wall_cost", "wallCost"], ["wire_len", "wireLen"], ["wire_cost", "wireCost"], ["pex_len", "pexLen"], ["drain_len", "drainLen"],
    ["plumbing_cost", "plumbingCost"], ["prop_count", "propCount"], ["prop_weight", "propWeight"], ["prop_cost", "propCost"],
    ["prop_watts", "propWatts"], ["trunk_stock_count", "trunkStockCount"], ["assigned_sections", "assignedSections"],
    ["hardware_screws", "hardwareScrews"], ["wedge_splits", "wedgeSplits"], ["wedge_log_diameter", "wedgeLogDiameter"]];
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
    assert.equal(d.walls.length, c.answers.wall_count, `case ${i} wall count`);
    assert.equal(d.wedgePanelRows.length, c.wedgePanels.length, `case ${i} wedge panels`);
    for (const [j, [name, ft, logFt]] of c.wedgePanels.entries()) {
      const row = d.wedgePanelRows[j];
      assert.equal(row.name, name, `case ${i} wedge panel ${j}`);
      for (const [want, got] of [[ft, row.wedgeFt], [logFt, row.logFt]]) assert.ok(Math.abs(got - want) <= Math.max(1e-6, want * 1e-6), `case ${i} ${name}: ${want} vs ${got}`);
    }
    checks += 3;
  }
  console.log(`PASS ${checks} checks over ${cases.length} designs; largest relative difference ${worst.toExponential(2)}`);
} finally {
  await rm(temp, { recursive: true, force: true });
}
