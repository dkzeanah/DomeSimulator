-- The owner's sending identities (2026-10-14) and a first follow-up sequence, switched OFF
-- until the owner has read it. Edit rows after this -- never this file.
--
-- owner@    the site's automatic mail: confirmations, sample links, receipts, pre-order news
-- donovan@  the owner's own voice: newsletters, the follow-up sequence, outreach
-- Both copy every message to the owner's Gmail (archive_bcc), so nothing lives in one place.
--
-- Body tokens are filled in when a message is queued: {{name}} and the book's own figures
-- ({{book_pages}}, {{book_figures}}, {{frame_hours}}, {{sample_pages}}, {{dome_ft}},
-- {{book_price}}) from facts.json and the catalogue, and {{site}}. The unsubscribe line and
-- postal address are added to every marketing message by the code, not by the copy.

INSERT INTO identities (key, from_name, from_email, reply_to, archive_bcc, purpose) VALUES
 ('owner', 'Zeanah Lab', 'owner@zeanahlab.com', 'donovan@zeanahlab.com', 'dkzeanah@gmail.com',
  'Automatic mail from the site: confirmations, sample links, receipts, pre-order updates.'),
 ('donovan', 'Donovan Zeanah', 'donovan@zeanahlab.com', 'donovan@zeanahlab.com', 'dkzeanah@gmail.com',
  'The owner''s own voice: newsletters, the follow-up sequence, outreach and replies.');

INSERT INTO sequences (key, name, trigger, active) VALUES
 ('sample-followup', 'After the free sample', 'sample', 0);

INSERT INTO sequence_steps (sequence, step, delay_hours, identity, subject, body) VALUES
 ('sample-followup', 0, 48, 'donovan', 'What comes after the first {{sample_pages}} pages',
  'Hi {{name}},

You have the opening of The 40 Hour Cabin. The rest of the book is {{book_pages}} pages and {{book_figures}} figures -- every one drawn and priced by code you can read -- taking a {{dome_ft}}-foot dome from standing tree to raised shell in {{frame_hours}} hours of frame work.

If the sample answered a question for you, reply and tell me which one. I read every reply.

Donovan'),
 ('sample-followup', 1, 168, 'donovan', 'The whole book, and the one printed by hand',
  'Hi {{name}},

The complete edition is {{book_price}} as a download, with every future edition included. There is also a triangular edition, printed and bound by hand to fund the first standing dome.

Both are here: {{site}}/book

Donovan');
