-- Prevent duplicate transactional receipts from repeated payment callbacks.
ALTER TABLE outbox ADD COLUMN dedupe_key TEXT;
CREATE UNIQUE INDEX outbox_dedupe ON outbox(dedupe_key) WHERE dedupe_key IS NOT NULL;
CREATE INDEX orders_owner_paid ON orders(user_id, status);
CREATE INDEX orders_email_paid ON orders(email, status);
