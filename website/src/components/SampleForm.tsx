// The lead magnet: the opening of the book for an email. On success the visitor's quest
// moves, the download link appears at once, and -- if mail is set up -- a copy is emailed.

import { useState } from "react";
import { api } from "../lib/api";
import { sample } from "../lib/facts";
import { useSession } from "../lib/session";
import { ErrorLine, Honeypot } from "./ui";

export default function SampleForm({ onDone }: { onDone?: () => void }) {
  const { mark, me } = useSession();
  const [email, setEmail] = useState(me?.email || "");
  const [consent, setConsent] = useState(false);
  const [trap, setTrap] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<{ downloadUrl: string; expiresInHours: number; emailed: boolean } | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const r = await api<{ downloadUrl: string; expiresInHours: number; emailed: boolean }>("/leads", { body: { email, book: "sample", marketingConsent: consent, website: trap } });
      setDone(r);
      mark("sample");
      onDone?.();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return (
      <div className="grid gap-3">
        <a className="btn text-center" href={done.downloadUrl}>Download the sample ({sample.pages} pages)</a>
        <p className="text-sm muted">The link works for {done.expiresInHours} hours.{done.emailed ? " A copy is on its way to your inbox." : ""}</p>
      </div>
    );
  }

  return (
    <form onSubmit={submit} className="grid gap-3 relative">
      <label className="grid gap-1 text-sm">
        Email
        <input className="field" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" autoComplete="email" />
      </label>
      <label className="flex gap-2 items-start text-sm">
        <input type="checkbox" className="mt-1" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
        <span className="muted">Also send me build updates. (Optional. The sample comes either way, and one click unsubscribes.)</span>
      </label>
      <Honeypot value={trap} onChange={setTrap} />
      <button className="btn" disabled={busy}>{busy ? "One moment..." : `Get the free sample (${sample.pages} pages)`}</button>
      <ErrorLine error={error} />
    </form>
  );
}
