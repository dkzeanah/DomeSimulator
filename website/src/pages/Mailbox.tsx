// The two links every email can carry: confirm (double opt-in) and unsubscribe (one click).
// Each page acts on arrival -- the link is the request -- and says plainly what happened.

import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ErrorLine, Panel } from "../components/ui";
import { api } from "../lib/api";
import { useSession, type Me } from "../lib/session";
import { useMeta } from "../lib/meta";

export function Confirm() {
  useMeta("Confirm your updates", "Confirm build updates from Zeanah Lab.", "/confirm");
  const [q] = useSearchParams();
  const [state, setState] = useState<"working" | "done" | "error">("working");
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api("/confirm", { body: { t: q.get("t") || "" } }).then(() => setState("done")).catch((e) => { setError(e.message); setState("error"); });
  }, [q]);
  return (
    <div className="mx-auto max-w-xl px-4 py-14">
      <Panel title={state === "done" ? "You are confirmed" : state === "error" ? "That link did not work" : "Confirming..."}>
        {state === "done" && <p className="muted">Build updates will come from donovan@zeanahlab.com. Every one has a one-click unsubscribe at the bottom.</p>}
        <ErrorLine error={error} />
        <Link className="btn mt-4" to="/">Back to the build</Link>
      </Panel>
    </div>
  );
}

export function Unsubscribe() {
  useMeta("Unsubscribe", "Stop email from Zeanah Lab.", "/unsubscribe");
  const [q] = useSearchParams();
  const t = q.get("t");
  const [done, setDone] = useState(false);
  const [mail, setMail] = useState("");
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (t) api("/unsubscribe", { body: { t } }).then(() => setDone(true)).catch((e) => setError(e.message));
  }, [t]);
  return (
    <div className="mx-auto max-w-xl px-4 py-14">
      <Panel title={done ? "You are unsubscribed" : "Unsubscribe"}>
        {done ? (
          <p className="muted">No more updates will be sent to you, and the address is kept off every future list. Receipts for anything you buy still arrive.</p>
        ) : t ? <p className="muted">One moment...</p> : (
          <form className="grid gap-2" onSubmit={async (e) => { e.preventDefault(); try { await api("/unsubscribe", { body: { email: mail } }); setDone(true); } catch (err) { setError((err as Error).message); } }}>
            <input className="field" type="email" required placeholder="The address to take off the list" value={mail} onChange={(e) => setMail(e.target.value)} />
            <button className="btn">Unsubscribe</button>
          </form>
        )}
        <ErrorLine error={error} />
      </Panel>
    </div>
  );
}

export function Privacy() {
  useMeta("Privacy", "What zeanahlab.com counts and keeps, and what it never does.", "/privacy");
  return (
    <div className="mx-auto max-w-3xl px-4 py-12 grid gap-6">
      <h1 className="text-4xl font-bold">What this site keeps</h1>
      <Panel title="Counting visits">
        <p className="muted">
          Each page view is counted on this site's own server: the page, the site that linked here, the campaign tags on that link, your
          country, and whether you are on a phone, tablet or computer. A random number in a cookie from this site alone ties your visits
          together, so a book sale can be traced to what brought it. No other company's script runs here, nothing follows you to other
          sites, and nothing is sold. If your browser sends Global Privacy Control or Do Not Track, your views are counted without that number.
        </p>
      </Panel>
      <Panel title="Email">
        <p className="muted">
          Your address is used only for what you asked for: the sample, receipts, and -- only if you ticked the box and then confirmed by
          email -- build updates. Every update has a one-click unsubscribe, and an address that unsubscribes is never mailed again.
          Mail is sent by this project's own mail server from owner@zeanahlab.com and donovan@zeanahlab.com.
        </p>
      </Panel>
      <Panel title="Payments and accounts">
        <p className="muted">
          Cards are taken on Stripe's own page; card numbers never reach this site. Account passwords are stored only as a salted hash.
          To delete your account and everything tied to it, use the Profile page, or email donovan@zeanahlab.com.
        </p>
      </Panel>
    </div>
  );
}

export function Reset() {
  useMeta("Choose a new password", "Reset your Zeanah Lab password.", "/reset");
  const [q] = useSearchParams();
  const { setMe } = useSession();
  const [pw, setPw] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  return (
    <div className="mx-auto max-w-xl px-4 py-14">
      <Panel title={done ? "Password changed" : "Choose a new password"}>
        {done ? <><p className="muted">You are signed in. Every other device was signed out.</p><Link className="btn mt-4" to="/account">Your account</Link></> : (
          <form className="grid gap-2" onSubmit={async (e) => {
            e.preventDefault(); setError(null);
            try { const r = await api<{ user: Me }>("/password/reset", { body: { t: q.get("t") || "", password: pw } }); setMe(r.user); setDone(true); } catch (err) { setError((err as Error).message); }
          }}>
            <input className="field" type="password" required minLength={10} autoComplete="new-password" placeholder="New password (10 characters or more)" value={pw} onChange={(e) => setPw(e.target.value)} />
            <button className="btn justify-self-start">Save it</button>
            <ErrorLine error={error} />
          </form>
        )}
      </Panel>
    </div>
  );
}

export function Verify() {
  useMeta("Confirm your email", "Confirm your Zeanah Lab account's email.", "/verify");
  const [q] = useSearchParams();
  const { refresh } = useSession();
  const [state, setState] = useState<"working" | "done" | "error">("working");
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api("/verify", { body: { t: q.get("t") || "" } }).then(() => { setState("done"); void refresh(); }).catch((e) => { setError(e.message); setState("error"); });
  }, [q, refresh]);
  return (
    <div className="mx-auto max-w-xl px-4 py-14">
      <Panel title={state === "done" ? "Email confirmed" : state === "error" ? "That link did not work" : "Confirming..."}>
        <ErrorLine error={error} />
        <Link className="btn mt-4" to="/account">Your account</Link>
      </Panel>
    </div>
  );
}
