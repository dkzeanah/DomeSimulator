// `npm run migrate`: bring the configured database up to date and stop.

import { createDb, dialect, migrate } from './db.js';

const db = createDb();
await migrate(db);
console.log(`Migrated (${dialect(db)}).`);
await db.destroy();
