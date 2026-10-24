// The Wedge Builder: a buyer types their dome and their logs and gets a cut list solved for it.
// The address is private like a receipt (/cutlist/:ref?key=...), or the signed-in owner of the
// order. Requests are solved on the owner's machine (functions/_lib/cutlists.ts), so the page
// shows the queue and checks back by itself until the PDF is ready.

import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { ErrorLine, Panel } from "../components/ui";
import { api } from "../lib/api";

type Key = "diameter_ft" | "log_in" | "log_ft";
interface Option { key: string; label: string }
interface Form {
  limits: Record<Key, { min: number; max: number }>; orientations: Option[]; seamJoins: Option[]; patterns: Option[]; groundIn: Option[];
  defaults: Record<Key, number> & { orientation: string; seam_join: string; pattern: string; ground_in: string };
}
interface Job {
  ref: string; status: "queued" | "rendering" | "done" | "failed"; error: string | null; design: string | null; pdfUrl: string | null; createdAt: string; doneAt: string | null;
  params: Record<Key, number> & { orientation: string; seam_join: string; label: string };
  summary: { logs?: number; rounds?: number; families?: number; setups?: number; jigs?: number; pages?: number | null } | null;
}
interface State { order: { ref: string; product: string }; credits: number; used: number; queueLength: number; form: Form; jobs: Job[] }

const FIELDS: { key: Key; label: string; unit: string; help: string; step: string }[] = [
  { key: "diameter_ft", label: "Floor diameter", unit: "ft", step: "0.1", help: "Across the floor, from one corner of the ten-sided base to the opposite corner." },
  { key: "log_in", label: "Log diameter", unit: "in", step: "0.5", help: "Measure the small end of your thinnest log. Every wedge is cut as if the log were this size all the way along." },
  { key: "log_ft", label: "Usable log length", unit: "ft", step: "0.5", help: "The straight length of each log you can cut rounds from." },
];

const WORDS: Record<Job["status"], string> = { queued: "Waiting in line", rendering: "Being solved now", done: "Ready", failed: "Could not be made" };

export default function CutList() {
  const { ref } = useParams();
  const [q] = useSearchParams();
  const key = q.get("key") || "";
  const [s, setS] = useState<State | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sendError, setSendError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [f, setF] = useState<Record<string, string>>({});
  const [sent, setSent] = useState(0);   // a new request restarts the checking
  const path = `/orders/${ref}/cutlists?key=${encodeURIComponent(key)}`;

  useEffect(() => {
    let live = true;
    let timer: ReturnType<typeof setTimeout>;
    async function load() {
      try {
        const r = await api<State>(path);
        if (!live) return;
        setS(r);
        setF((old) => Object.keys(old).length ? old : Object.fromEntries(Object.entries(r.form.defaults).map(([k, v]) => [k, String(v)])));
        if (r.jobs.some((j) => j.status === "queued" || j.status === "rendering")) timer = setTimeout(load, 8000);
      } catch (e) { if (live) setError((e as Error).message); }
    }
    void load();
    return () => { live = false; clearTimeout(timer); };
  }, [path, sent]);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setSendError(null);
    try {
      await api(path, { body: { ...f, diameter_ft: Number(f.diameter_ft), log_in: Number(f.log_in), log_ft: Number(f.log_ft) } });
      setSent((n) => n + 1);
    } catch (err) { setSendError((err as Error).message); }
    setBusy(false);
  }

  if (error) return <div className="mx-auto max-w-xl px-4 py-10"><ErrorLine error={error} /></div>;
  if (!s) return <div className="mx-auto max-w-xl px-4 py-10 muted">Loading your cut lists...</div>;
  const left = s.credits - s.used;
  const waiting = s.jobs.some((j) => j.status === "queued" || j.status === "rendering");
  return (
    <div className="mx-auto max-w-2xl px-4 py-10 grid gap-6">
      <Panel kicker={`${s.order.product} -- ${left} of ${s.credits} cut list${s.credits === 1 ? "" : "s"} left`} title="Your dome's cut list">
        <p className="text-sm">
          Type your dome and your logs. The same solver that computed the book works out every cut for <i>your</i> numbers: the saw setups,
          the cut families, which round of which log each wedge comes from, the jigs and the seams. You get a printable PDF.
        </p>
        {left > 0 && !waiting ? (
          <form className="grid gap-4 mt-4" onSubmit={send}>
            {FIELDS.map((x) => (
              <label key={x.key} className="grid gap-1">
                <span className="text-sm font-semibold">{x.label} ({x.unit})</span>
                <input className="field" type="number" required step={x.step} min={s.form.limits[x.key].min} max={s.form.limits[x.key].max}
                  value={f[x.key] ?? ""} onChange={(e) => setF({ ...f, [x.key]: e.target.value })} />
                <span className="text-xs muted">{x.help} Between {s.form.limits[x.key].min} and {s.form.limits[x.key].max} {x.unit}.</span>
              </label>
            ))}
            <label className="grid gap-1">
              <span className="text-sm font-semibold">Build pattern</span>
              <select className="field" value={f.pattern} onChange={(e) => setF({ ...f, pattern: e.target.value })}>
                {s.form.patterns.map((o) => <option key={o.key} value={o.key}>{o.label}</option>)}
              </select>
              <span className="text-xs muted">
                Alternating panels point in and out, so the faces across a seam cancel and the key fills only the dome's own fold.
                The cut list then says which way every panel points, band by band from the ground.
              </span>
            </label>
            {f.pattern && f.pattern !== "uniform" && (
              <label className="grid gap-1">
                <span className="text-sm font-semibold">Which ground panels point in</span>
                <select className="field" value={f.ground_in} onChange={(e) => setF({ ...f, ground_in: e.target.value })}>
                  {s.form.groundIn.map((o) => <option key={o.key} value={o.key}>{o.label}</option>)}
                </select>
                <span className="text-xs muted">If you have already stood your ground panels, pick what you built. Otherwise leave it: the better choice puts every unavoidable matched seam where it costs least.</span>
              </label>
            )}
            {(!f.pattern || f.pattern === "uniform") && <>
            <label className="grid gap-1">
              <span className="text-sm font-semibold">Which way the wedge's point faces</span>
              <select className="field" value={f.orientation} onChange={(e) => setF({ ...f, orientation: e.target.value })}>
                {s.form.orientations.map((o) => <option key={o.key} value={o.key}>{o.label}</option>)}
              </select>
              <span className="text-xs muted">The book builds with the point to the dome's centre. If you have not chosen, leave it there.</span>
            </label>
            <label className="grid gap-1">
              <span className="text-sm font-semibold">How the seams are joined</span>
              <select className="field" value={f.seam_join} onChange={(e) => setF({ ...f, seam_join: e.target.value })}>
                {s.form.seamJoins.map((o) => <option key={o.key} value={o.key}>{o.label}</option>)}
              </select>
            </label>
            </>}
            <label className="grid gap-1">
              <span className="text-sm font-semibold">A name for it (optional)</span>
              <input className="field" maxLength={60} placeholder="e.g. the back meadow cabin" value={f.label ?? ""} onChange={(e) => setF({ ...f, label: e.target.value })} />
              <span className="text-xs muted">Printed on the cover.</span>
            </label>
            <button className="btn" disabled={busy}>{busy ? "Sending..." : "Solve my cut list"}</button>
            <ErrorLine error={sendError} />
            <p className="text-xs muted">
              This is a cutting and assembly plan, not an engineered design. It does not check snow, wind or your wood's strength, and it is not
              stamped for a permit. A request the solver cannot build (logs too short for the size, say) comes back with the reason and does not use up a cut list.
            </p>
          </form>
        ) : waiting ? (
          <p className="panel-2 p-3 text-sm mt-4">Your cut list is being solved{s.queueLength > 1 ? ` (${s.queueLength} in line)` : ""}. This page checks by itself, and we email you when it is ready.</p>
        ) : (
          <p className="panel-2 p-3 text-sm mt-4">This order's cut lists have all been made. Each one stays below to download again.</p>
        )}
      </Panel>

      {s.jobs.length > 0 && (
        <Panel kicker="Made for this order" title="Your cut lists">
          <ul className="grid gap-3">
            {s.jobs.map((j) => (
              <li key={j.ref} className="panel-2 p-3 grid gap-1 text-sm">
                <p><b>{j.params.label || `${j.params.diameter_ft} ft dome`}</b> -- {j.params.diameter_ft} ft floor, {j.params.log_in} in logs, {j.params.log_ft} ft long</p>
                <p className="muted">{WORDS[j.status]}{j.design ? ` -- design ${j.design}` : ""}
                  {j.summary?.logs ? ` -- ${j.summary.logs} logs, ${j.summary.families} cut families, ${j.summary.jigs} jigs` : ""}
                  {j.summary?.pages ? `, ${j.summary.pages} pages` : ""}</p>
                {j.status === "failed" && j.error && <p>{j.error}</p>}
                {j.pdfUrl && <a className="btn text-center" href={j.pdfUrl}>Download the cut list (PDF)</a>}
              </li>
            ))}
          </ul>
        </Panel>
      )}
      <p className="text-sm muted">Keep this page's address: it is private to your order. <Link className="underline" to={`/thanks/${ref}?key=${encodeURIComponent(key)}`}>Your receipt</Link>.</p>
    </div>
  );
}
