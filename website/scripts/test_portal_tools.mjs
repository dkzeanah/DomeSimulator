// The Portal's 3D Zome against the desktop wedge zome: 60 zomes, each solved by
// wedge_zome.geometry and by src/world/zome.ts, every figure of fabrication.facts compared.
//
//   npm run test:tools               (asks the tool for fresh cases, then compares)
//   node scripts/test_portal_tools.mjs <file>   (cases already written by portal_tools_export.py --fixtures)
import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { build } from "esbuild";

const site = resolve(import.meta.dirname, "..");
const temp = await mkdtemp(join(tmpdir(), "zome-"));
let file = process.argv[2];
if (!file) {
  file = join(temp, "fixtures.json");
  const { execFileSync } = await import("node:child_process");
  execFileSync("py", ["-3.12", join(site, "scripts", "portal_tools_export.py"), "--fixtures", file], { stdio: "inherit" });
}
const cases = JSON.parse(await readFile(file, "utf8"));
const out = join(temp, "zome.mjs");
let checks = 0, worst = 0;
const near = (got, want, what) => {
  const tol = Math.max(1e-6, Math.abs(want) * 1e-6);
  worst = Math.max(worst, Math.abs(got - want) / Math.max(1, Math.abs(want)));
  assert.ok(Math.abs(got - want) <= tol, `${what}: tool ${want}, Portal ${got}`);
  checks++;
};
const same = (got, want, what) => {
  if (typeof want === "number") return near(got, want, what);
  if (Array.isArray(want)) { assert.equal(got.length, want.length, `${what} length`); return want.forEach((w, i) => same(got[i], w, `${what}[${i}]`)); }
  if (want && typeof want === "object") return Object.keys(want).forEach((k) => same(got[k], want[k], `${what}.${k}`));
  assert.equal(got, want, what);
  checks++;
};
try {
  await build({ entryPoints: [join(site, "src/world/zome.ts")], bundle: true, platform: "node", format: "esm", outfile: out, logLevel: "silent" });
  const { facts } = await import(pathToFileURL(out).href);
  for (const [i, c] of cases.entries()) {
    const f = facts(c.config);
    const label = `case ${i} ${JSON.stringify(c.config)}`;
    for (const [k, want] of Object.entries(c.answers)) {
      if (k === "types") same(f.types.map(({ members, ...t }) => t), want, `${label} types`);
      else same(f[k], want, `${label} ${k}`);
    }
  }
  console.log(`PASS ${checks} checks over ${cases.length} zomes; largest relative difference ${worst.toExponential(2)}`);
} finally {
  await rm(temp, { recursive: true, force: true });
}
