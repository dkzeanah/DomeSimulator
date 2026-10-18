// The Portal's seam controller and cell wall against two_v_demo.seam_climate and
// two_v_demo.cell_wall: the controller's mode, dew points and reasons on 311 sets of sensors
// (the owner's weathers among them), the wall's temperature profile on 22 stacks, the router's
// interlocks on 208 sets of modes, and the cold channel.
//
//   npm run test:spaces              (asks the Python for fresh cases, then compares)
//   node scripts/test_portal_spaces.mjs <file>
import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { build } from "esbuild";

const site = resolve(import.meta.dirname, "..");
const temp = await mkdtemp(join(tmpdir(), "spaces-"));
let file = process.argv[2];
if (!file) {
  file = join(temp, "fixtures.json");
  const { execFileSync } = await import("node:child_process");
  execFileSync("py", ["-3.12", join(site, "scripts", "portal_spaces_export.py"), "--fixtures", file], { stdio: "inherit" });
}
const cases = JSON.parse(await readFile(file, "utf8"));
const out = join(temp, "climate.mjs");
let checks = 0;
const near = (got, want, what) => { assert.ok(Math.abs(got - want) <= Math.max(1e-9, Math.abs(want) * 1e-9), `${what}: Python ${want}, Portal ${got}`); checks++; };
try {
  await build({ entryPoints: [join(site, "src/world/climate.ts")], bundle: true, platform: "node", format: "esm", outfile: out, logLevel: "silent" });
  const m = await import(pathToFileURL(out).href);
  for (const [i, c] of cases.decide.entries()) {
    const d = m.decide(c.sensors);
    assert.equal(d.mode, c.mode, `decide ${i} mode (${JSON.stringify(c.sensors)})`); checks++;
    near(d.dp_in, c.dp[0], `decide ${i} dp_in`); near(d.dp_out, c.dp[1], `decide ${i} dp_out`); near(d.dp_seam, c.dp[2], `decide ${i} dp_seam`);
    assert.deepEqual(d.reasons, c.reasons, `decide ${i} reasons`); checks++;
  }
  for (const [i, c] of cases.profiles.entries()) {
    const rows = m.profile(c.stack ?? undefined, c.t_out ?? undefined);
    assert.equal(rows.length, c.rows.length, `profile ${i} rows`);
    rows.forEach((r, j) => { assert.equal(r.layer, c.rows[j].layer); near(r.temp_c, c.rows[j].temp_c, `profile ${i} ${r.layer}`); near(r.rsi, c.rows[j].rsi, `profile ${i} ${r.layer} rsi`); });
  }
  for (const [i, c] of cases.checks.entries()) {
    assert.deepEqual(m.checkScenario(c.modes, c.t_out), c.broken, `interlocks ${i} (${JSON.stringify(c.modes)})`); checks++;
  }
  for (const c of cases.cold) {
    const got = m.coldChannel(c.t, c.rh);
    for (const [k, want] of Object.entries(c.cold)) {
      if (typeof want === "number") near(got[k], want, `cold ${k}`); else { assert.equal(got[k], want, `cold ${k}`); checks++; }
    }
  }
  console.log(`PASS ${checks} checks: ${cases.decide.length} controller cases, ${cases.profiles.length} wall profiles, ${cases.checks.length} interlock sets, ${cases.cold.length} cold channels`);
} finally {
  await rm(temp, { recursive: true, force: true });
}
