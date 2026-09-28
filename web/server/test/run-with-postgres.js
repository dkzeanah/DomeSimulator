// `npm run test:pg`: start a throwaway Postgres, run every test against it,
// stop it. Proves the migrations and queries work on Postgres as well as
// SQLite without anyone installing a database.
//
// The server is started with pg_ctl rather than embedded-postgres's own
// start(): Postgres refuses to run from an administrator shell, and on Windows
// pg_ctl is what drops those rights before launching it.

import { execFileSync, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import EmbeddedPostgres from 'embedded-postgres';
import pgPkg from 'pg';

const here = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.resolve(here, '..', '..', '.pg-test');
const port = 54329;
const user = 'domenet';
const password = 'domenet';

const platform = { win32: 'windows', darwin: 'darwin', linux: 'linux' }[process.platform];
// The platform package that embedded-postgres installed exports its binaries' paths.
const { pg_ctl: pgCtl } = await import(`@embedded-postgres/${platform}-${process.arch}`);

fs.rmSync(dataDir, { recursive: true, force: true });
// initialise() runs initdb, which is happy under any user.
await new EmbeddedPostgres({ databaseDir: dataDir, user, password, port, persistent: false, onLog: () => {} }).initialise();

let status = 1;
try {
  execFileSync(pgCtl, ['-D', dataDir, '-o', `-p ${port}`, '-w', '-l', path.join(dataDir, 'log.txt'), 'start'], { stdio: 'ignore' });
  const admin = new pgPkg.Client({ host: 'localhost', port, user, password, database: 'postgres' });
  await admin.connect();
  await admin.query('CREATE DATABASE domenet_test');
  await admin.end();
  const result = spawnSync(process.execPath, ['--test', '--test-concurrency=1', 'test/*.test.js'], {
    cwd: path.resolve(here, '..'),
    stdio: 'inherit',
    env: { ...process.env, TEST_DATABASE_URL: `postgres://${user}:${password}@localhost:${port}/domenet_test` },
  });
  status = result.status ?? 1;
} catch (error) {
  console.error(error.message);
  const log = path.join(dataDir, 'log.txt');
  if (fs.existsSync(log)) console.error(fs.readFileSync(log, 'utf8').slice(-2000));
} finally {
  try {
    execFileSync(pgCtl, ['-D', dataDir, '-m', 'fast', '-w', 'stop'], { stdio: 'ignore' });
  } catch { /* already stopped */ }
  fs.rmSync(dataDir, { recursive: true, force: true });
}
process.exit(status);
