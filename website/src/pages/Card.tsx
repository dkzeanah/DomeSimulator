// The digital business card: every channel on one page, and a contact file a phone can save.
// The links are web/site.config.json's, through scripts/export_facts.py.

import { Link } from "react-router-dom";
import { facts } from "../lib/facts";
import { useMeta } from "../lib/meta";

const OWNER = "Donovan Zeanah";

const ICON: Record<string, string> = {
  youtube: "M10 15.5v-7l6 3.5-6 3.5Z M2 12c0-3.3.3-5 1-5.8C4 5.2 6 5 12 5s8 .2 9 1.2c.7.8 1 2.5 1 5.8s-.3 5-1 5.8c-1 1-3 1.2-9 1.2s-8-.2-9-1.2C2.3 17 2 15.3 2 12Z",
  tiktok: "M14 3v11.5a3.5 3.5 0 1 1-3.5-3.5M14 3c.5 2.6 2.4 4.4 5 4.6",
  instagram: "M7 3h10a4 4 0 0 1 4 4v10a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V7a4 4 0 0 1 4-4Z M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Z M17.5 6.5h.01",
  facebook: "M14 8h2.5V4.5H14A3.5 3.5 0 0 0 10.5 8v2.5H8V14h2.5v7H14v-7h2.5l.5-3.5h-3V8.5c0-.3.2-.5.5-.5Z",
  github: "M9 19c-4.3 1.4-4.3-2.5-6-3m12 5v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12.3 12.3 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21",
  mail: "M3 6h18v12H3z M3 6l9 7 9-7",
};

function Glyph({ name }: { name: string }) {
  return (
    <svg viewBox="0 0 24 24" className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d={ICON[name] || ICON.mail} />
    </svg>
  );
}

function saveContact() {
  const site = facts.site;
  const lines = [
    "BEGIN:VCARD", "VERSION:3.0", `FN:${OWNER}`, `N:Zeanah;Donovan;;;`, `ORG:${site.name}`,
    `EMAIL;TYPE=INTERNET:${site.email}`, `URL:${site.url}`,
    ...site.links.map((l) => `X-SOCIALPROFILE;TYPE=${l.icon}:${l.url}`),
    "END:VCARD",
  ];
  const url = URL.createObjectURL(new Blob([lines.join("\r\n")], { type: "text/vcard" }));
  const a = document.createElement("a");
  a.href = url; a.download = "donovan-zeanah.vcf"; a.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function Card() {
  const site = facts.site;
  useMeta(`${OWNER} -- every channel`, `${OWNER}, ${site.name}: YouTube, TikTok, Instagram, Facebook, email and the book.`, "/card");
  return (
    <div className="mx-auto max-w-md px-4 py-10">
      <div className="panel p-6 text-center">
        <img src="/mark.svg" alt="" className="w-20 h-20 mx-auto" />
        <h1 className="text-3xl font-bold mt-3">{OWNER}</h1>
        <p className="muted mt-1">{site.name}</p>
        <p className="text-sm mt-2">{site.tagline}</p>
        <div className="grid gap-2.5 mt-6 text-left">
          {site.links.map((l) => (
            <a key={l.url} href={l.url} target="_blank" rel="noopener" className="btn-ghost flex items-center gap-3 hover:border-[var(--accent)]">
              <Glyph name={l.icon} /><span className="flex-1">{l.label}</span><span aria-hidden className="muted">&rsaquo;</span>
            </a>
          ))}
          <a href={`mailto:${site.email}`} className="btn-ghost flex items-center gap-3 hover:border-[var(--accent)]">
            <Glyph name="mail" /><span className="flex-1">{site.email}</span><span aria-hidden className="muted">&rsaquo;</span>
          </a>
          <Link to="/book" className="btn text-center mt-2">The book: {facts.bookFacts.digital.title}</Link>
          <Link to="/kids" className="btn-ghost text-center">The kids' book: {facts.kidsBook.title}</Link>
          <button type="button" className="text-sm underline underline-offset-4 mt-2" onClick={saveContact}>Save my contact to your phone</button>
        </div>
      </div>
    </div>
  );
}
