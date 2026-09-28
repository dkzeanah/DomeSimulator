// The whole schema, in one migration because nothing has shipped yet.
// Later changes go in new files; never edit this one once it has run anywhere.

export async function up(knex) {
  // Everyone who has given us an email, account or not.
  await knex.schema.createTable('subscribers', (t) => {
    t.increments('id');
    t.string('email', 320).notNullable().unique();
    t.string('name', 120);
    t.boolean('marketing_consent').notNullable().defaultTo(false);
    t.string('source', 60); // which form: 'book', 'signup', ...
    t.timestamp('created_at').notNullable().defaultTo(knex.fn.now());
    t.timestamp('unsubscribed_at');
  });

  await knex.schema.createTable('users', (t) => {
    t.increments('id');
    t.string('email', 320).notNullable().unique();
    t.string('password_hash', 100).notNullable();
    t.string('display_name', 80).notNullable();
    t.string('role', 20).notNullable().defaultTo('member'); // member | admin
    t.text('bio');
    t.string('city', 100);
    t.string('region', 100);
    t.string('country', 100);
    t.string('website', 300);
    t.timestamp('created_at').notNullable().defaultTo(knex.fn.now());
    t.timestamp('updated_at').notNullable().defaultTo(knex.fn.now());
  });

  // A session cookie holds a random token; we keep only its hash, so a copy
  // of the database cannot be used to log in as anyone.
  await knex.schema.createTable('sessions', (t) => {
    t.string('token_hash', 64).primary();
    t.integer('user_id').notNullable().references('users.id').onDelete('CASCADE');
    t.timestamp('created_at').notNullable().defaultTo(knex.fn.now());
    t.timestamp('expires_at').notNullable();
    t.index(['user_id']);
  });

  await knex.schema.createTable('downloads', (t) => {
    t.increments('id');
    t.integer('subscriber_id').references('subscribers.id').onDelete('SET NULL');
    t.integer('user_id').references('users.id').onDelete('SET NULL');
    t.string('book_slug', 80).notNullable();
    t.string('file_name', 200);
    t.timestamp('created_at').notNullable().defaultTo(knex.fn.now());
    t.index(['book_slug']);
  });

  // The dome network: pads, domes, quilters, builders, people with trees.
  await knex.schema.createTable('listings', (t) => {
    t.increments('id');
    t.integer('user_id').notNullable().references('users.id').onDelete('CASCADE');
    t.string('kind', 30).notNullable();
    t.string('title', 120).notNullable();
    t.text('body');
    t.string('city', 100);
    t.string('region', 100);
    t.string('country', 100);
    t.string('postal_code', 20);
    t.double('lat');
    t.double('lng');
    t.string('contact', 300);
    t.boolean('visible').notNullable().defaultTo(true);
    t.timestamp('created_at').notNullable().defaultTo(knex.fn.now());
    t.timestamp('updated_at').notNullable().defaultTo(knex.fn.now());
    t.index(['kind']);
    t.index(['lat', 'lng']);
    t.index(['user_id']);
  });

  // The link-in-bio page.
  await knex.schema.createTable('links', (t) => {
    t.increments('id');
    t.string('label', 80).notNullable();
    t.string('url', 500).notNullable();
    t.string('icon', 30).notNullable().defaultTo('link');
    t.integer('sort').notNullable().defaultTo(0);
    t.boolean('visible').notNullable().defaultTo(true);
    t.timestamp('created_at').notNullable().defaultTo(knex.fn.now());
  });

  // Videos and posts from YouTube, TikTok and Instagram, pasted in by URL.
  await knex.schema.createTable('media_items', (t) => {
    t.increments('id');
    t.string('platform', 20).notNullable();
    t.string('url', 500).notNullable();
    t.string('embed_id', 120).notNullable();
    t.string('kind', 20).notNullable().defaultTo('video'); // video | short | post | reel
    t.string('title', 200);
    t.boolean('featured').notNullable().defaultTo(false);
    t.integer('sort').notNullable().defaultTo(0);
    t.timestamp('created_at').notNullable().defaultTo(knex.fn.now());
    t.unique(['platform', 'embed_id']);
  });
}

export async function down(knex) {
  for (const table of ['media_items', 'links', 'listings', 'downloads', 'sessions', 'users', 'subscribers']) {
    await knex.schema.dropTableIfExists(table);
  }
}
