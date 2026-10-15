# The zeanahlab.com database

Written by `scripts/model_db.py` from `migrations/` -- do not edit. `model.sqlite` beside this file is the same database, built fresh.

## account_meta

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| user_id | INTEGER |  |  | PK |
| key | TEXT |  |  | PK |
| value | TEXT |  |  |  |

0 row(s) in the model.

## agent_proposals

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| key_id | INTEGER | yes |  | -> api_keys.id |
| action | TEXT |  |  |  |
| payload | TEXT |  |  |  |
| reason | TEXT | yes |  |  |
| status | TEXT |  | 'pending' |  |
| result | TEXT | yes |  |  |
| created_at | TEXT |  |  |  |
| decided_at | TEXT | yes |  |  |
| decided_by | INTEGER | yes |  | -> users.id |

0 row(s) in the model.

## ai_runs

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| purpose | TEXT |  |  |  |
| model | TEXT |  |  |  |
| input_chars | INTEGER |  |  |  |
| output_chars | INTEGER |  | 0 |  |
| ms | INTEGER |  |  |  |
| ok | INTEGER |  |  |  |
| error | TEXT | yes |  |  |
| created_at | TEXT |  |  |  |

0 row(s) in the model.

## api_calls

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| key_id | INTEGER | yes |  | -> api_keys.id |
| ts | TEXT |  |  |  |
| method | TEXT |  |  |  |
| path | TEXT |  |  |  |
| status | INTEGER |  |  |  |
| note | TEXT | yes |  |  |

0 row(s) in the model.

## api_keys

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| name | TEXT |  |  |  |
| prefix | TEXT |  |  |  |
| key_hash | TEXT |  |  |  |
| scopes | TEXT |  |  |  |
| rate_per_min | INTEGER |  | 30 |  |
| created_by | INTEGER | yes |  | -> users.id |
| created_at | TEXT |  |  |  |
| expires_at | TEXT | yes |  |  |
| last_used_at | TEXT | yes |  |  |
| revoked_at | TEXT | yes |  |  |

0 row(s) in the model.

## assets

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| user_id | INTEGER |  |  | PK |
| name | TEXT |  |  | PK |
| description | TEXT |  | '' |  |
| value | REAL |  | 0 |  |

0 row(s) in the model.

## audit_log

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| ts | TEXT |  |  |  |
| actor_kind | TEXT |  |  |  |
| actor_id | INTEGER | yes |  |  |
| actor_name | TEXT | yes |  |  |
| action | TEXT |  |  |  |
| target | TEXT | yes |  |  |
| detail | TEXT | yes |  |  |

0 row(s) in the model.

## automations

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| name | TEXT |  |  |  |
| description | TEXT | yes |  |  |
| trigger | TEXT |  |  |  |
| conditions | TEXT |  | '{}' |  |
| actions | TEXT |  |  |  |
| delay_minutes | INTEGER |  | 0 |  |
| active | INTEGER |  | 0 |  |
| runs | INTEGER |  | 0 |  |
| last_run_at | TEXT | yes |  |  |
| created_by | TEXT | yes |  |  |
| created_at | TEXT |  |  |  |
| updated_at | TEXT |  |  |  |

7 row(s) in the model.

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

## campaigns

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| name | TEXT |  |  |  |
| identity | TEXT |  |  | -> identities.key |
| subject | TEXT |  |  |  |
| body | TEXT |  |  |  |
| segment | TEXT |  | '{}' |  |
| status | TEXT |  | 'draft' |  |
| queued_count | INTEGER |  | 0 |  |
| created_at | TEXT |  |  |  |
| queued_at | TEXT | yes |  |  |

0 row(s) in the model.

## conversions

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| ts | TEXT |  |  |  |
| visitor_id | TEXT | yes |  |  |
| kind | TEXT |  |  |  |
| ref | TEXT | yes |  |  |
| value_cents | INTEGER |  | 0 |  |

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

## email_events

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| outbox_id | INTEGER | yes |  | -> outbox.id |
| kind | TEXT |  |  |  |
| detail | TEXT | yes |  |  |
| created_at | TEXT |  |  |  |

0 row(s) in the model.

## enrollments

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| subscriber_id | INTEGER |  |  | PK |
| sequence | TEXT |  |  | PK |
| enrolled_at | TEXT |  |  |  |
| next_step | INTEGER |  | 0 |  |
| status | TEXT |  | 'active' |  |

0 row(s) in the model.

## events

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| kind | TEXT |  |  |  |
| label | TEXT |  |  |  |
| created_at | TEXT |  |  |  |

0 row(s) in the model.

## identities

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| key | TEXT | yes |  | PK |
| from_name | TEXT |  |  |  |
| from_email | TEXT |  |  |  |
| reply_to | TEXT | yes |  |  |
| archive_bcc | TEXT | yes |  |  |
| purpose | TEXT |  |  |  |

2 row(s) in the model.

## jobs

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| automation_id | INTEGER | yes |  | -> automations.id |
| event_id | INTEGER | yes |  | -> ops_events.id |
| label | TEXT |  |  |  |
| status | TEXT |  | 'queued' |  |
| attempts | INTEGER |  | 0 |  |
| run_at | TEXT |  |  |  |
| started_at | TEXT | yes |  |  |
| finished_at | TEXT | yes |  |  |
| result | TEXT | yes |  |  |
| error | TEXT | yes |  |  |
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

## login_attempts

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| email | TEXT |  |  |  |
| ip_hash | TEXT | yes |  |  |
| ok | INTEGER |  |  |  |
| ts | TEXT |  |  |  |

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

## notices

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| level | TEXT |  | 'info' |  |
| title | TEXT |  |  |  |
| body | TEXT | yes |  |  |
| link | TEXT | yes |  |  |
| created_at | TEXT |  |  |  |
| read_at | TEXT | yes |  |  |

0 row(s) in the model.

## ops_events

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| type | TEXT |  |  |  |
| data | TEXT |  |  |  |
| created_at | TEXT |  |  |  |

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
| visitor_id | TEXT | yes |  |  |

0 row(s) in the model.

## outbox

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| subscriber_id | INTEGER | yes |  | -> subscribers.id |
| to_email | TEXT |  |  |  |
| identity | TEXT |  |  | -> identities.key |
| kind | TEXT |  |  |  |
| campaign_id | INTEGER | yes |  | -> campaigns.id |
| sequence | TEXT | yes |  |  |
| step | INTEGER | yes |  |  |
| subject | TEXT |  |  |  |
| html | TEXT |  |  |  |
| text | TEXT |  |  |  |
| status | TEXT |  | 'queued' |  |
| attempts | INTEGER |  | 0 |  |
| lease_until | TEXT | yes |  |  |
| message_id | TEXT | yes |  |  |
| error | TEXT | yes |  |  |
| created_at | TEXT |  |  |  |
| sent_at | TEXT | yes |  |  |

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

## sequence_steps

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| sequence | TEXT |  |  | PK |
| step | INTEGER |  |  | PK |
| delay_hours | REAL |  |  |  |
| identity | TEXT |  |  | -> identities.key |
| subject | TEXT |  |  |  |
| body | TEXT |  |  |  |

2 row(s) in the model.

## sequences

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| key | TEXT | yes |  | PK |
| name | TEXT |  |  |  |
| trigger | TEXT |  |  |  |
| active | INTEGER |  | 0 |  |

1 row(s) in the model.

## sessions

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| token_hash | TEXT | yes |  | PK |
| user_id | INTEGER |  |  | -> users.id |
| created_at | TEXT |  |  |  |
| expires_at | TEXT |  |  |  |
| last_seen_at | TEXT | yes |  |  |
| user_agent | TEXT | yes |  |  |
| country | TEXT | yes |  |  |

0 row(s) in the model.

## settings

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| key | TEXT | yes |  | PK |
| value | TEXT |  |  |  |
| updated_at | TEXT |  |  |  |

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

## subscriber_tags

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| subscriber_id | INTEGER |  |  | PK |
| tag | TEXT |  |  | PK |
| created_at | TEXT |  |  |  |

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
| status | TEXT |  | 'unconfirmed' |  |
| confirmed_at | TEXT | yes |  |  |
| visitor_id | TEXT | yes |  |  |
| first_source | TEXT | yes |  |  |
| first_medium | TEXT | yes |  |  |
| first_campaign | TEXT | yes |  |  |
| first_referrer | TEXT | yes |  |  |
| first_landing | TEXT | yes |  |  |

0 row(s) in the model.

## suppressions

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| email | TEXT | yes |  | PK |
| reason | TEXT |  |  |  |
| created_at | TEXT |  |  |  |

0 row(s) in the model.

## user_tokens

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| token_hash | TEXT | yes |  | PK |
| user_id | INTEGER |  |  | -> users.id |
| purpose | TEXT |  |  |  |
| created_at | TEXT |  |  |  |
| expires_at | TEXT |  |  |  |
| used_at | TEXT | yes |  |  |

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
| status | TEXT |  | 'active' |  |
| suspended_reason | TEXT | yes |  |  |
| last_seen_at | TEXT | yes |  |  |
| email_verified_at | TEXT | yes |  |  |
| admin_note | TEXT | yes |  |  |

0 row(s) in the model.

## visits

| column | type | null | default | key |
| --- | --- | --- | --- | --- |
| id | INTEGER | yes |  | PK |
| ts | TEXT |  |  |  |
| visitor_id | TEXT | yes |  |  |
| session_id | TEXT | yes |  |  |
| path | TEXT |  |  |  |
| referrer_host | TEXT | yes |  |  |
| utm_source | TEXT | yes |  |  |
| utm_medium | TEXT | yes |  |  |
| utm_campaign | TEXT | yes |  |  |
| utm_content | TEXT | yes |  |  |
| country | TEXT | yes |  |  |
| device | TEXT | yes |  |  |

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
