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

## 7. Email: your own list, your own mail server

No email company is involved. The site keeps the list, the campaigns, the follow-up
sequences and every message in its own database, in a queue. Your own mail program, on a
rented server with a static address, collects the queue every minute with `MAILER_TOKEN`
(setup makes it and keeps a copy in `website/private/mailer-token.txt`), signs each
message with zeanahlab.com's own key, delivers it, and reports back. Until that server
runs, messages wait in the queue -- nothing is lost.

- **owner@zeanahlab.com** sends the site's automatic mail; **donovan@zeanahlab.com** sends
  your updates; both copy every message to your Gmail.
- Updates go only to people who ticked the box *and* clicked the confirmation link. Every
  update has a one-click unsubscribe; an address that leaves is never mailed again.
- The law (CAN-SPAM) requires a postal address in marketing email. `npm run setup` asks for
  it (`MAIL_POSTAL_ADDRESS`); a P.O. box is fine. Until it is set, updates are held back;
  sample links and receipts still go.
- **Admin -> The list and email**: subscribers and where each came from, tags, campaigns
  (write, send a test to yourself, queue to a segment), and the sequences (read them, edit
  them, switch them on). **Admin -> Analytics**: visitors, the funnel, sources and what each
  earned, the list's growth, and how each address's mail is read -- all counted by the site.
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
  Token**) with *Cloudflare Pages: Edit* and *D1: Edit*.
- `CLOUDFLARE_ACCOUNT_ID` -- shown on the right of the Cloudflare dashboard home.

From then on, every change to `website/` merged into `main` is built, the database updated
and the site published (`.github/workflows/website.yml`). A pull request only builds, so a
broken page never goes live.

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
