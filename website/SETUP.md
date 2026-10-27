# zeanahlab.com — how to put it online

This folder is the whole website: the pages people see (`src/`), the small server that
stores emails, accounts, orders and the pad network (`functions/`), and the database layout
(`migrations/`). It runs on Cloudflare, which already holds the zeanahlab.com domain. The
free tier covers it; the only paid piece is Stripe's per-sale fee.

You type each command below into a terminal opened in this `website` folder. Nothing here
needs programming. Do the steps once, in order; after that, publishing is automatic.

## The short way: one command

```bash
npm run setup
```

It does every step below for you and asks only what it must: your browser opens once to
sign in to Cloudflare (click **Allow**); it stops to let you switch R2 on if it is off; it
asks for the optional email and payment keys (leave blank to skip); and it asks before it
publishes. Run it again any time -- finished steps are skipped. *Wrangler*, which you will
see named, is just Cloudflare's own command-line tool; the script drives it for you.

Done (2026-10-14): the database, the book store (both PDFs uploaded), the site project and its
two required secrets, the first publish, and the address: www.zeanahlab.com and zeanahlab.com
now point at the site (they were `A 47.231.197.101`, which no longer answered; the mail
records were left alone). Still open: the postal address for marketing email and the mail server (`npm run setup` asks for
them) and the two GitHub secrets for automatic publishing (step 9).

The steps below are what the script does, by hand.

## What lives where

| Thing | Where | Why |
|---|---|---|
| The pages and pictures | Cloudflare Pages | fast everywhere, free |
| Emails, accounts, orders, pads, backers, plaques | Cloudflare D1 (a database) | free tier, backed up by Cloudflare |
| The book PDFs | Cloudflare R2 (file storage) | the full book is 74 MB, too big for Pages; the sample has to stay behind the email form |
| Email: the list, campaigns, the queue | D1, on this site | your own mail program on a rented server delivers it |
| Taking card payments | Stripe | the card never touches this site |
| The numbers on every page | `src/generated/facts.json` | written by `npm run facts` from the project's own models -- never typed |

## 1. Try it on this computer first

```bash
npm install
```

```bash
copy .dev.vars.example .dev.vars
```

Open `.dev.vars` in any text editor. Put a long random line after `SESSION_SECRET=` (the
file says how to make one) and your email after `ADMIN_EMAILS=`. Then:

```bash
npm run db:local
```

```bash
npm run books:local
```

```bash
npm run preview
```

Open http://127.0.0.1:8788. Make an account with the email you put in `ADMIN_EMAILS` and the
Admin page appears under your name. The shop runs in test mode here: "Pay (test)" charges
nothing.

## 2. Sign wrangler in to your Cloudflare account

```bash
npx wrangler login
```

A browser window asks you to allow it. That is the only sign-in this needs.

## 3. Make the database

```bash
npx wrangler d1 create zeanahlab
```

It prints a `database_id`. Open `wrangler.toml` and replace the line of zeros after
`database_id =` with it. Then build the tables:

```bash
npm run db:remote
```

## 4. Make the book store and put the books in it

R2 must be switched on once in the Cloudflare dashboard (**R2 Object Storage**). Cloudflare
asks for a card even on the free tier; nothing is charged under 10 GB.

```bash
npx wrangler r2 bucket create zeanahlab-books
```

```bash
npm run books:remote
```

This uploads the newest edition of the sample and the complete book from the library.
Run it again whenever a new edition is published.

## 5. Make the site, give it its secrets, and publish it

```bash
npx wrangler pages project create zeanahlab --production-branch main
```

Each of these asks you to paste a value (it is stored encrypted at Cloudflare, never in
this folder):

```bash
npx wrangler pages secret put SESSION_SECRET --project-name zeanahlab
```

```bash
npx wrangler pages secret put ADMIN_EMAILS --project-name zeanahlab
```

Then publish:

```bash
npm run build
```

```bash
npx wrangler pages deploy dist --project-name zeanahlab --branch main
```

It prints an address ending in `.pages.dev`. The site is live there.

## 6. Put it on www.zeanahlab.com

In the Cloudflare dashboard: **Workers & Pages → zeanahlab → Custom domains → Set up a
domain**, type `www.zeanahlab.com`, and confirm. Cloudflare adds the DNS record itself
because it already runs the domain. Do the same for `zeanahlab.com` (or add a redirect
rule from the bare domain to `www`).

## 7. Email: your own list, sent by Cloudflare

The site keeps the list, the campaigns, the follow-up sequences and every message in its
own database, in a queue. Once a minute the **zeanahlab-ops** Worker (step 10) collects the
queue with `MAILER_TOKEN` (copy in `website/private/mailer-token.txt`) and sends each message
through **Cloudflare Email Sending** from zeanahlab.com -- part of Workers Paid: 3,000 emails
a month included, then $0.35 per 1,000 (Cloudflare's price list). No rented server. Until
sending is switched on, messages wait in the queue -- nothing is lost.

Switch it on once: Cloudflare dashboard -> **Compute -> Email Service -> Email Sending ->
Onboard Domain** -> zeanahlab.com -> Done. It adds its own records under `cf-bounce` and a
DMARC record. Add `dkzeanah@gmail.com` as a verified destination address (Email Routing ->
Destination addresses) so the archive copy of each message is free and uncounted.

- **owner@zeanahlab.com** sends the site's automatic mail; **donovan@zeanahlab.com** sends
  your updates; both copy every message to your Gmail.
- Updates go only to people who ticked the box *and* clicked the confirmation link. Every
  update has a one-click unsubscribe; an address that leaves is never mailed again.
- The law (CAN-SPAM) requires a postal address in marketing email. `npm run setup` asks for
  it (`MAIL_POSTAL_ADDRESS`); a P.O. box is fine. Until it is set, updates are held back;
  sample links, receipts and password resets still go.
- **Admin -> The list and email**: subscribers and where each came from, tags, campaigns
  (write, send a test to yourself, queue to a segment), and the sequences. **Admin ->
  Analytics**: visitors, the funnel, sources and what each earned, the list's growth.
- Tag every link you post so Analytics can credit it:
  `https://www.zeanahlab.com/start?utm_source=instagram&utm_campaign=closing-the-triangle`

## 8. Taking payments

1. In Stripe: **Developers → API keys**, copy the secret key.
2. **Developers → Webhooks → Add endpoint**: `https://www.zeanahlab.com/api/stripe/webhook`,
   event `checkout.session.completed`. Copy its signing secret.

```bash
npx wrangler pages secret put STRIPE_SECRET_KEY --project-name zeanahlab
```

```bash
npx wrangler pages secret put STRIPE_WEBHOOK_SECRET --project-name zeanahlab
```

Until the Stripe key is set, the shop says "opens soon" instead of taking money. Never set
`TEST_CHECKOUT` on the live site.

## 9. Publish automatically from GitHub

In GitHub: **Settings → Secrets and variables → Actions**, add

- `CLOUDFLARE_API_TOKEN` -- make one in Cloudflare (**My Profile → API Tokens → Create
  Token** → *Custom token*) with Account: *Cloudflare Pages: Edit*, *D1: Edit*, *Workers
  Scripts: Edit*, *Workers R2 Storage: Edit*. Paste it with
  `gh secret set CLOUDFLARE_API_TOKEN --repo dkzeanah/DomeSimulator`.
- `CLOUDFLARE_ACCOUNT_ID` -- shown on the right of the Cloudflare dashboard home.

From then on, a change to `website/` pushed to the `staging` branch is built and published
to the staging site, and nothing reaches zeanahlab.com until you press **Promote to live**
(see "Staging, then live" below). A pull request or a push to `main` only builds.

## 10. The clock, automations, members and agents (Workers Paid)

Pages cannot run on a schedule, so a small Worker, **zeanahlab-ops** (`ops/`), does it:
once a minute it asks the site to run what is due and delivers the mail queue.

```bash
npx wrangler deploy -c ops/wrangler.toml
```

Its two secrets are the site's: `OPS_TOKEN` (copy in `website/private/ops-token.txt`) and
`MAILER_TOKEN`. Cloudflare will not attach the once-a-minute schedule until the account has
a workers.dev subdomain: open **Workers & Pages** in the dashboard once and it is made.

- **Admin -> Automations**: when THIS happens (a sale, a confirmation, a new listing, an
  agent's proposal, Monday morning), do THESE (a notice, an email to you, a tag, a sequence,
  a signed webhook, the numbers report, a Workers AI listing check or update draft). Every
  run is in the job log; a failed run retries three times, then tells you. The notices are
  your inbox on the site. *Ask about your numbers* answers only from counted figures and
  shows them beside the answer.
- **Admin -> Members**: find any account; see its devices, orders, listings and history;
  suspend or restore it, sign it out everywhere, make a password-reset link, delete it.
  Members have *Account -> Security and data*: devices, password, email confirmation, a
  download of everything the site holds about them, and deleting the account. Eight wrong
  passwords for one address in fifteen minutes and the door waits.
- **Admin -> Agents and keys**: give an LLM or script its own key with only the scopes you
  tick, an expiry and a per-minute limit. It starts at `GET /api/agent/tools` (with
  `Authorization: Bearer <key>`), which lists what it may do as tools. Sending mail, changing
  a price or hiding a listing is never done by an agent: it becomes a proposal you approve.
  Every call is logged; every change by anyone is in the audit log.
- Workers AI runs on Cloudflare's own GPUs; each call is logged (Automations -> Workers AI).
  Testing it on this computer (`npm run preview`) also needs the workers.dev subdomain.
- Health check (secrets by kind, never by value; Stripe and AI answer or not):
  `curl -H "Authorization: Bearer <OPS_TOKEN>" https://www.zeanahlab.com/api/ops/health`

## Everyday jobs

- **A new edition of the book:** `npm run books:remote`. The site serves whatever is in the
  store.
- **The model's numbers changed** (price, tiers, goal): `npm run facts`, then commit
  `src/generated/facts.json`. Every page agrees with the model again.
- **A real backer:** Admin page → *Record a backer* (from the campaign's own records -- the
  site never takes a pledge itself). A founder: *Claim a founder plaque*.
- **The list:** Admin page → *Download CSV*.
- **Change the database:** add a new numbered file in `migrations/`; never edit one that has
  already run.

## The studio (Admin -> Studio, `/admin/studio`)

After `migrations/0008_studio.sql` is applied (`npm run db:remote`) and the site deployed:

- **Signing in:** the owner is whoever `ADMIN_EMAILS` (a secret) names. That account can also
  sign in with the username `OWNER_USERNAME` (`wrangler.toml`, `shortcircuiter`), which nobody
  else can take. Any member may pick a username at sign-up or on their Profile tab.
  *Sign out* is in the header.
- **Lead with:** which part of the site the home page's banner is about (the book, the kids'
  book, dome classes, the pad network). No redeploy.
- **Invite codes** (owner only): one live code per level -- *friend* (friend prices on every
  book) and *manager* (the admin pages). Each rolls on its own every 72 hours (changeable) and
  still works for one period after; *Roll now* kills a code at once. People type it in the
  invite box when they make an account, or later on their Profile tab.
- **Give an account a level:** the same levels by hand, by email or username.
- **Projects** (`/admin/projects`, after `migrations/0009_projects.sql`): your projects and
  their tasks on one board -- to do, doing, blocked, done -- with due dates, notes, who has
  it, and a link (a page here, a `deliverables/...` folder, or any https:// address). The
  Studio's *This week* shows what is overdue, due in seven days, in progress or blocked.
  Managers edit; only you delete a project. A task added or finished is an event
  (`task.created`, `task.done`) automations can act on.
- **Promo codes:** each unlocks one book's friend price ($5 for the $20 book, $1 for the $5
  kids' book). None exist until you make them here; the repository is public, so none are
  seeded.
- **The kids' book** is a pre-order until its PDF is in the book store. Build it with
  `py -3.12 -m kids_book` (from the project folder), send it with `npm run books:remote`
  (it goes up as `my-own-home-my-own-dome.pdf`), then set it *live* on *Backers and
  orders*. Buyers' order pages show the download from then on.
- **Dome classes** (`/domes`): every figure comes from `npm run facts`, which also writes
  `src/generated/dome-classes.json` (one class per whole inch of longest strut, solved by
  `seed_model`).

## The Wedge Builder (cut lists for a buyer's own dome)

A buyer types their dome's size and their logs and gets a PDF cut list: the saw setups, the
cut families, which round of which log each wedge comes from, the jigs and the seams. The
website only takes the request and hands over the PDF. **Your computer does the solving**,
with the project's `wedge_builder` package, so a request waits until you run the render
script below.

**Once:**

1. Put the tables online: `npm run db:remote` (adds `migrations/0015_cutlists.sql`).
2. Make an agent key with only the **cutlists:render** box ticked (Admin -> Agents and keys).
   Copy it; it is shown once.
3. The Wedge Builder starts **hidden** at a placeholder $79. Set its price and put it *live*
   on *Backers and orders* when you are ready. It then shows on the book page's shelf.

**Who gets cut lists:** the rows in the `tool_grants` table. As seeded, one Wedge Builder
order makes 25 cut lists and the complete edition of the book makes 1. Change a row to change
the offer. A cut list the solver refuses (logs too short for the size, say) shows the buyer
the reason and does not use up their credit.

**Rendering the queue** (from the project folder, with the key from step 2):

```bash
set ZL_AGENT_KEY=zl_...
py -3.12 website/scripts/render_cutlists.py --site https://www.zeanahlab.com --watch
```

`--watch` keeps looking every minute until you close the window. Leave it out to render
what is waiting and stop. Each buyer is emailed when theirs is ready, and you keep a copy of
every PDF in `website/private/cutlists/` (never committed). A new request also fires the
`cutlist.requested` event, so an automation can notify you. The whole queue is at
`/api/admin/cutlists`.

To try a cut list yourself without the website: `py -3.12 -m wedge_builder --diameter-ft 19.4
--log-in 10 --log-ft 16`. Before changing the solver, run `py -3.12 -m wedge_builder.selftest`.

## Staging, then live

There are two copies of the site. **Staging** (https://dev.zeanahlab.com, only you can open
it) is where a change is looked at. **Live** (www.zeanahlab.com) changes only when you say so.

| | Staging | Live |
|---|---|---|
| Published by | a push to the `staging` branch | the **Promote to live** button |
| Database | `zeanahlab-staging`: a copy of live, refreshed when you ask | `zeanahlab` |
| Book files | `zeanahlab-books-staging` | `zeanahlab-books` |
| Payments | test mode, no card is charged | Stripe |
| Email | never sent (no mail token) | sent |
| A banner saying "STAGING" | yes | no |

**The routine:**

1. Push your change to `staging`. Two minutes later it is on the staging site.
2. To look at it with today's real data first, refresh staging's copy:
   `py -3.12 scripts/staging.py refresh`. This also rehearses any new database change on
   real data, exactly as going live will apply it.
3. Happy with it? In GitHub: **Actions -> website -> Run workflow -> Run workflow** (leave the
   box blank). It publishes *the same build you looked at* to zeanahlab.com, applies its
   database changes to the live database, and moves `main` to it.
4. Changed your mind after? Cloudflare -> Workers & Pages -> zeanahlab -> **Deployments** ->
   the previous production deployment -> **Rollback**. That is instant, but it puts back the
   pages and the code, **not the database**. So database changes only ever ADD (a table, a
   column, a row) and never rename or remove, and the previous site keeps working.

To promote an older staging build, type its run number (from the Actions list) in the box.

Promoting moves `main` to the promoted commit when it can. If `main` has commits staging
does not (merging a pull request on GitHub adds one), the site still goes live and the run
warns. Then merge `main` into `staging` once, and the next promotion moves it again. A
brand-new `staging` branch pushed at the same commit as `main` starts no run, because
nothing in `website/` changed. Push a real change to start the first one.

**Once, to set staging up:**

1. `py -3.12 scripts/staging.py setup` makes the staging database and file store, writes the
   database's id into `wrangler.toml` (commit that), copies the books, and prints the two
   **Preview** secrets to paste into Cloudflare (Settings -> Variables and Secrets ->
   Preview): `SESSION_SECRET` and `ADMIN_EMAILS`. Nothing else goes under Preview.
2. `py -3.12 scripts/staging.py refresh` gives it its first copy of live data.
3. Make the `staging` branch and push it. The first push publishes the staging site.
4. Custom domain: Workers & Pages -> zeanahlab -> Custom domains -> **Set up a domain** ->
   `dev.zeanahlab.com`. Then in DNS, change that record to a CNAME pointing at
   `staging.zeanahlab.pages.dev`, so it shows staging and not live.
5. Lock it: Zero Trust -> Access -> Applications -> **Add** a self-hosted app for
   `dev.zeanahlab.com` that allows only your email. Also under zeanahlab -> Settings ->
   General, switch on **Access policy** for preview deployments, so the `*.pages.dev`
   addresses are locked too.

`py -3.12 scripts/staging.py refresh --local` rehearses the same refresh between this
computer's two local databases.
