-- My Own Home, My Own Dome is free (owner, 2026-10-20): /kids reads it aloud as a bedtime story,
-- and the whole verse is on the page. What can still be ordered is a printed picture book, and that
-- is pending: no price and no shipping yet, so it is a waitlist, and the digital prices are retired.

UPDATE products
   SET kind = 'physical',
       subtitle = 'A rhyming picture book -- free to read, printed edition pending',
       blurb = 'One log, one saw, and one stubborn kid: the dome build told in rhyme. Free to read and watch as a bedtime story; the printed book is on its way.',
       file_key = NULL,
       status = 'waitlist',
       ships_note = 'The printed picture book is pending. It cannot be ordered yet; leave your email and you will hear the day it can.',
       updated_at = '2026-10-20T00:00:00Z'
 WHERE slug = 'my-own-home-my-own-dome';

UPDATE prices SET active = 0 WHERE product = 'my-own-home-my-own-dome';
