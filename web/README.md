# The dome network website

One small website that does five jobs:

| page | what it does |
|---|---|
| **/** and **/book** | Gives away the PDF books. A visitor types an email, gets a download link that works for a day, and is asked (not forced) whether they want updates. |
| **/account** | Lets people make an account: email, name, password. Account holders can download any book any time and list themselves on the network. |
| **/network** | The dome network: pad hosts, dome owners, quilters, builders and people with trees. Search by keyword, by type, or "near me". |
| **/links** | A link-in-bio page (like Linktree) for your Instagram and TikTok profiles. |
| **/watch** | Your YouTube, TikTok and Instagram posts on one page. |
| **/dome** | The stem cell's size, price, fit-outs, panels, reward tiers and goal -- all read from the Python model. |
| **/admin** | Only for you: the email list (and a CSV to download), the links page editor, and the media wall editor. |

It is a React front end and an Express server. Locally it keeps its data in a
**SQLite** file; on a real host it uses **Postgres**. Same code, same
features: the only difference is one setting (`DATABASE_URL`).

## Run it on this computer

You need Node.js 20 or newer (this machine has it). In a terminal, from the
`web` folder:

```bash
npm install
```

```bash
copy .env.example .env
```

Open `.env` in any text editor and put your own email after `ADMIN_EMAILS=`.
That is the email that gets the Admin page. Then:

```bash
npm run build
```

```bash
npm start
```

Open http://localhost:8787 and make an account with that email. The
**Admin** link appears in the menu.

To work on the site with live reloading instead, run `npm run dev` and open
http://localhost:5173.

## Everyday jobs

**Put a new edition of a book up.** Nothing to do here. The site always
serves the highest `-vN` version of each book in `deliverables/book/` -- publish
`the-40-hour-cabin-v2.pdf` and it is the one people get.

**Offer a different book, or change a title.** Edit `books.config.json`.

**Change the links page.** Admin page → *Links page*. (`site.config.json`
only fills it the very first time the site starts.)

**Put a video or post on the Watch page.** On YouTube, TikTok or Instagram,
press *Share* → *Copy link*, then paste it on the Admin page under *Media
wall*. Tick *Featured* to put it first.

**Show your newest YouTube uploads automatically.** Put your channel id
(starts with `UC`, found at youtube.com → your profile → *Settings* →
*Advanced settings*) after `YOUTUBE_CHANNEL_ID=` in `.env`. No API key needed.

**Get the mailing list.** Admin page → *Download the mailing list (CSV)*.
It contains only people who ticked "send me updates" and have not
unsubscribed. Import it into your mailing tool (Mailchimp, Buttondown,
ConvertKit...).

**Update the dome's figures after the model changes.** From the repository
root, run `py -3.12 web/export_facts.py`. Every figure on the site comes from
there; none is typed into the website code.

## Put it on the internet

Any host that runs Node and offers Postgres works. On **Render**, for
example:

1. Create a **PostgreSQL** database. Copy its *Internal Database URL*.
2. Create a **Web Service** from the GitHub repository with:
   * Root directory: `web`
   * Build command: `npm install && npm run build`
   * Start command: `npm start`
3. Add environment variables: `NODE_ENV=production`,
   `DATABASE_URL=` (the URL from step 1), `DATABASE_SSL=true`,
   `SESSION_SECRET=` (a long random string -- `.env.example` shows how to make
   one), `ADMIN_EMAILS=` (you), `PUBLIC_URL=` (the site's address).
4. The PDFs: the books in `deliverables/book/` are committed to git, so the
   host already has them and nothing needs setting. To serve books from
   somewhere else (a disk attached to the service, say), set `BOOKS_DIR`.

The server creates its own tables on first start (and on every start, it
brings them up to date). Point your own domain (e.g. zeanahlab.com) at the
service in the host's settings.

## Privacy and safety, built in

* Passwords are stored only as bcrypt hashes. Sessions are server-side and
  end when you sign out; changing a password signs out every other device.
* Download links are signed and expire after a day.
* Network listings show a location rounded to about a kilometre, never an
  exact spot, and contact details only to signed-in members.
* The Watch page loads nothing from YouTube, TikTok or Instagram until a
  visitor presses play.
* People can delete their own account; their listings go with it.
* Sign-in and the email form are rate-limited, and the email form has a
  hidden field that catches bots.

## Tests

```bash
npm test
```

runs the API tests against SQLite.

```bash
npm run test:pg
```

runs the same tests against a real, throwaway Postgres (downloaded by npm; no
install needed).
