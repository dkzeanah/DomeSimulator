// The shop: paid orders, and a record of every form an email came in through.
//
// subscribers keeps one row per address; signups keeps *each* time somebody
// asked for something (the free sample, the Amazon waitlist, a purchase), so
// the admin page can say which offer is pulling people in.

export async function up(knex) {
  await knex.schema.createTable('orders', (t) => {
    t.increments('id');
    // What the buyer's link carries. `ref` is public; the key that unlocks the
    // download is kept only as a hash, like a session token.
    t.string('ref', 32).notNullable().unique();
    t.string('key_hash', 64).notNullable();
    t.string('book_slug', 80).notNullable();
    t.integer('amount_cents').notNullable();
    t.string('currency', 3).notNullable();
    t.string('email', 320);
    t.integer('user_id').references('users.id').onDelete('SET NULL');
    t.integer('subscriber_id').references('subscribers.id').onDelete('SET NULL');
    t.string('status', 20).notNullable().defaultTo('pending'); // pending | paid | refunded
    t.string('provider', 20).notNullable(); // stripe | test
    t.string('provider_session', 255);
    t.boolean('marketing_consent').notNullable().defaultTo(false);
    t.timestamp('created_at').notNullable().defaultTo(knex.fn.now());
    t.timestamp('paid_at');
    t.index(['book_slug']);
    t.index(['status']);
    t.index(['user_id']);
  });

  await knex.schema.createTable('signups', (t) => {
    t.increments('id');
    t.integer('subscriber_id').notNullable().references('subscribers.id').onDelete('CASCADE');
    t.string('kind', 20).notNullable(); // sample | waitlist | purchase
    t.string('book_slug', 80).notNullable();
    t.timestamp('created_at').notNullable().defaultTo(knex.fn.now());
    t.index(['kind', 'book_slug']);
  });
}

export async function down(knex) {
  await knex.schema.dropTableIfExists('signups');
  await knex.schema.dropTableIfExists('orders');
}
