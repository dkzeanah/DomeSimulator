// Start the server: migrate, seed the links on first run, listen.

import { createApp } from './app.js';
import { config } from './config.js';
import { createDb, dialect, migrate } from './db.js';
import { seedLinks } from './routes/content.js';

const db = createDb();
await migrate(db);
const seeded = await seedLinks(db);

const app = createApp(db);
app.listen(config.port, () => {
  console.log(`Dome network API on http://localhost:${config.port} (${dialect(db)})`);
  if (seeded) console.log(`Seeded ${seeded} links from site.config.json`);
  if (!config.adminEmails.length) console.log('No ADMIN_EMAILS set: nobody can edit links or media yet (see .env.example).');
});
