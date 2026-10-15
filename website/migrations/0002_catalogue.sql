-- The catalogue lives in the database: what is offered, at which prices, in which states.
-- Evergreen: a new product, a price change, a sale ending or a book going to print is a row
-- edit (admin page or SQL), not a code change and not a redeploy. Orders record the price
-- they were sold at, so changing a price never rewrites history.

CREATE TABLE products (
  slug TEXT PRIMARY KEY,
  kind TEXT NOT NULL,                  -- digital | physical | service | amazon
  title TEXT NOT NULL,
  subtitle TEXT NOT NULL DEFAULT '',
  blurb TEXT NOT NULL DEFAULT '',
  file_key TEXT,                       -- R2 object for a digital product
  status TEXT NOT NULL DEFAULT 'live', -- live | preorder | waitlist | hidden
  ships_note TEXT,                     -- physical: what a buyer is promised about shipping
  ship_countries TEXT,                 -- physical: comma list Stripe may ship to, e.g. US
  external_url TEXT,                   -- amazon: the listing, once it exists
  sort INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

-- One product, several ways to pay for it. `honor` marks a price that rests on the buyer's
-- word (e.g. the reduced price for a non-monetary donation): the buyer must describe what
-- they are giving, and that description is kept on the order.
CREATE TABLE prices (
  product TEXT NOT NULL REFERENCES products(slug) ON DELETE CASCADE,
  key TEXT NOT NULL,
  label TEXT NOT NULL,
  amount_cents INTEGER NOT NULL,       -- 0 = free (given for an email)
  currency TEXT NOT NULL DEFAULT 'usd',
  honor INTEGER NOT NULL DEFAULT 0,
  honor_prompt TEXT,                   -- what the buyer is asked to describe
  active INTEGER NOT NULL DEFAULT 1,
  sort INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (product, key)
);

-- What each order bought, at which price, and -- for a physical product -- where it goes.
ALTER TABLE orders ADD COLUMN price_key TEXT;
ALTER TABLE orders ADD COLUMN honor_note TEXT;
ALTER TABLE orders ADD COLUMN ship_name TEXT;
ALTER TABLE orders ADD COLUMN ship_address TEXT;     -- JSON from Stripe's shipping details
ALTER TABLE orders ADD COLUMN fulfillment TEXT;      -- NULL (nothing to send) | waiting | printed | shipped
