# The zeanahlab.com database

Written by `scripts/model_db.py` from `migrations/` -- do not edit. `model.sqlite` beside this file is the same database, built fresh.

## account_meta

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| user_id | INTEGER |  |  | PK |
| key | TEXT |  |  | PK |
| value | TEXT |  |  |  |

0 row(s) in the model.

## assets

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| user_id | INTEGER |  |  | PK |
| name | TEXT |  |  | PK |
| description | TEXT |  | '' |  |
| value | REAL |  | 0 |  |

0 row(s) in the model.

## backers

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| user_id | INTEGER | yes |  | -> users.id |
| display_name | TEXT |  |  |  |
| tier | TEXT |  |  |  |
| pledge_cents | INTEGER |  |  |  |
| public | INTEGER |  | 1 |  |
| created_at | TEXT |  |  |  |

0 row(s) in the model.

## downloads

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| subscriber_id | INTEGER | yes |  | -> subscribers.id |
| user_id | INTEGER | yes |  | -> users.id |
| book_slug | TEXT |  |  |  |
| created_at | TEXT |  |  |  |

0 row(s) in the model.

## events

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| kind | TEXT |  |  |  |
| label | TEXT |  |  |  |
| created_at | TEXT |  |  |  |

0 row(s) in the model.

## listings

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| user_id | INTEGER |  |  | -> users.id |
| kind | TEXT |  |  |  |
| title | TEXT |  |  |  |
| body | TEXT | yes |  |  |
| city | TEXT | yes |  |  |
| region | TEXT | yes |  |  |
| country | TEXT | yes |  |  |
| postal_code | TEXT | yes |  |  |
| lat | REAL | yes |  |  |
| lng | REAL | yes |  |  |
| contact | TEXT | yes |  |  |
| nightly_rate_cents | INTEGER | yes |  |  |
| occupancy_pct | REAL | yes |  |  |
| season_cost_cents | INTEGER | yes |  |  |
| season_nights | INTEGER | yes |  |  |
| hookups | TEXT | yes |  |  |
| pad_status | TEXT | yes |  |  |
| visible | INTEGER |  | 1 |  |
| created_at | TEXT |  |  |  |
| updated_at | TEXT |  |  |  |

0 row(s) in the model.

## logs

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| user_id | INTEGER |  |  | -> users.id |
| ts | TEXT |  |  |  |
| method | TEXT |  |  |  |
| hours | REAL |  |  |  |
| cash | REAL |  | 0 |  |
| note | TEXT |  | '' |  |

0 row(s) in the model.

## method_xp

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| user_id | INTEGER |  |  | -> users.id |
| method | TEXT |  |  |  |
| skill | TEXT |  |  |  |
| xp_per_hour | REAL |  | 0 |  |

0 row(s) in the model.

## methods

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| user_id | INTEGER |  |  | PK |
| name | TEXT |  |  | PK |
| cash_per_hour | REAL |  | 0 |  |
| cost_per_hour | REAL |  | 0 |  |
| notes | TEXT |  | '' |  |

0 row(s) in the model.

## orders

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| ref | TEXT |  |  |  |
| key_hash | TEXT |  |  |  |
| book_slug | TEXT |  |  |  |
| amount_cents | INTEGER |  |  |  |
| currency | TEXT |  |  |  |
| email | TEXT | yes |  |  |
| user_id | INTEGER | yes |  | -> users.id |
| subscriber_id | INTEGER | yes |  | -> subscribers.id |
| status | TEXT |  | 'pending' |  |
| provider | TEXT |  |  |  |
| provider_session | TEXT | yes |  |  |
| marketing_consent | INTEGER |  | 0 |  |
| created_at | TEXT |  |  |  |
| paid_at | TEXT | yes |  |  |
| price_key | TEXT | yes |  |  |
| honor_note | TEXT | yes |  |  |
| ship_name | TEXT | yes |  |  |
| ship_address | TEXT | yes |  |  |
| fulfillment | TEXT | yes |  |  |

0 row(s) in the model.

## plaques

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| slot | INTEGER | yes |  | PK |
| backer_id | INTEGER | yes |  | -> backers.id |
| inscription | TEXT | yes |  |  |
| status | TEXT |  | 'claimed' |  |
| claimed_at | TEXT |  |  |  |

0 row(s) in the model.

## prices

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| product | TEXT |  |  | PK |
| key | TEXT |  |  | PK |
| label | TEXT |  |  |  |
| amount_cents | INTEGER |  |  |  |
| currency | TEXT |  | 'usd' |  |
| honor | INTEGER |  | 0 |  |
| honor_prompt | TEXT | yes |  |  |
| active | INTEGER |  | 1 |  |
| sort | INTEGER |  | 0 |  |

6 row(s) in the model.

## products

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| slug | TEXT | yes |  | PK |
| kind | TEXT |  |  |  |
| title | TEXT |  |  |  |
| subtitle | TEXT |  | '' |  |
| blurb | TEXT |  | '' |  |
| file_key | TEXT | yes |  |  |
| status | TEXT |  | 'live' |  |
| ships_note | TEXT | yes |  |  |
| ship_countries | TEXT | yes |  |  |
| external_url | TEXT | yes |  |  |
| sort | INTEGER |  | 0 |  |
| created_at | TEXT |  |  |  |
| updated_at | TEXT |  |  |  |

5 row(s) in the model.

## quest_requirements

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| user_id | INTEGER |  |  | -> users.id |
| quest | TEXT |  |  |  |
| kind | TEXT |  |  |  |
| target | TEXT |  |  |  |
| amount | REAL |  | 1 |  |

0 row(s) in the model.

## quests

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| user_id | INTEGER |  |  | PK |
| name | TEXT |  |  | PK |
| status | TEXT |  | 'not_started' |  |
| description | TEXT |  | '' |  |

0 row(s) in the model.

## salvage_logs

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| user_id | INTEGER |  |  | -> users.id |
| material | TEXT |  |  |  |
| quantity | REAL |  |  |  |
| unit | TEXT |  |  |  |
| hours | REAL |  |  |  |
| replacement_cents | INTEGER |  |  |  |
| note | TEXT | yes |  |  |
| created_at | TEXT |  |  |  |

0 row(s) in the model.

## sessions

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| token_hash | TEXT | yes |  | PK |
| user_id | INTEGER |  |  | -> users.id |
| created_at | TEXT |  |  |  |
| expires_at | TEXT |  |  |  |

0 row(s) in the model.

## signups

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| subscriber_id | INTEGER |  |  | -> subscribers.id |
| kind | TEXT |  |  |  |
| book_slug | TEXT |  |  |  |
| created_at | TEXT |  |  |  |

0 row(s) in the model.

## skills

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| user_id | INTEGER |  |  | PK |
| name | TEXT |  |  | PK |
| level | INTEGER |  | 1 |  |
| xp | REAL |  | 0 |  |

0 row(s) in the model.

## subscribers

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| email | TEXT |  |  |  |
| name | TEXT | yes |  |  |
| marketing_consent | INTEGER |  | 0 |  |
| source | TEXT | yes |  |  |
| created_at | TEXT |  |  |  |
| unsubscribed_at | TEXT | yes |  |  |

0 row(s) in the model.

## users

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| email | TEXT |  |  |  |
| password_hash | TEXT |  |  |  |
| display_name | TEXT |  |  |  |
| role | TEXT |  | 'member' |  |
| bio | TEXT | yes |  |  |
| city | TEXT | yes |  |  |
| region | TEXT | yes |  |  |
| country | TEXT | yes |  |  |
| public_profile | INTEGER |  | 0 |  |
| created_at | TEXT |  |  |  |
| updated_at | TEXT |  |  |  |

0 row(s) in the model.

## The catalogue as seeded

| product | kind | status | price | amount | honor |
| --- | --- | --- | --- | --- | --- |
| sample | digital | live | free | $0.00 |  |
| the-40-hour-cabin | digital | live | standard | $20.00 |  |
| triangular-book | physical | preorder | standard | $50.00 |  |
| triangular-book | physical | preorder | donation | $30.00 | yes |
| design-session | service | live | standard | $50.00 |  |
| 2-trees | amazon | waitlist | amazon | $12.99 |  |
