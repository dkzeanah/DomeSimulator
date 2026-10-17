// Dome classes. A 2V wedge dome is fixed by one number -- its longest strut -- and every figure
// here is worked out from it by the project's own solver (scripts/export_facts.py writes
// src/generated/dome-classes.json; nothing is typed). Members whose domes share a longest strut
// are one class: the same panels fit, so they can trade them and help each other.

import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import raw from "../generated/dome-classes.json";
import { ErrorLine, Panel, Stat } from "../components/ui";
import { api, n, usd } from "../lib/api";
import { facts } from "../lib/facts";
import { useMeta } from "../lib/meta";
import { useSession, type MyDome } from "../lib/session";

export type DomeClass = (typeof raw.classes)[number];
const CLASSES = raw.classes;
const FIRST = CLASSES[0].longIn, LAST = CLASSES[CLASSES.length - 1].longIn;
const byLong = (l: number) => CLASSES.find((c) => c.longIn === Math.round(l)) ?? null;
/** The book's own dome: the class the stem cell's diameter belongs to. */
const BOOK = CLASSES.find((c) => c.diameterFt === facts.dome.acrossFt) ?? CLASSES[0];

/** The class a strut names: the longest to the nearest inch, or a shortest within half an inch. */
export function classOf(longest: number | null, shortest: number | null): DomeClass | null {
  if (longest != null && Number.isFinite(longest)) return byLong(longest);
  if (shortest != null && Number.isFinite(shortest)) {
    const best = CLASSES.reduce((a, c) => (Math.abs(c.shortIn - shortest) < Math.abs(a.shortIn - shortest) ? c : a));
    return Math.abs(best.shortIn - shortest) <= 0.5 ? best : null;
  }
  return null;
}

const ftIn = (inches: number) => {
  const ft = Math.floor(inches / 12), rest = Math.round((inches - ft * 12) * 10) / 10;
  return rest ? `${ft} ft ${rest} in` : `${ft} ft`;
};
const pct = (part: number, whole: number) => `${Math.round((part / whole) * 100)}%`;

function Row({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-3 border-b py-1.5 text-sm" style={{ borderColor: "var(--line)" }}>
      <dt className="muted">{k}</dt><dd className="num font-semibold text-right">{v}</dd>
    </div>
  );
}

/** Everything one number gives you. */
export function ClassSheet({ c }: { c: DomeClass }) {
  const cost = c.cost;
  return (
    <div className="grid gap-6">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Stat value={`${c.diameterFt} ft`} label="across" />
        <Stat value={`${c.heightFt} ft`} label="tall at the top" />
        <Stat value={`${n(c.floorSqft)} sq ft`} label="floor inside the base ring" />
        <Stat value={`${n(c.frameLb)} lb`} label="frame weight, green pine" />
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <h3 className="text-xl font-semibold mb-2">Panels it takes</h3>
          <dl>
            {c.panels.map((p) => (
              <Row key={p.name} k={`${p.count} triangles, sides ${p.sidesIn.join(" x ")} in`} v={`${p.areaSqft} sq ft each`} />
            ))}
            {c.panels.map((p) => <Row key={`w${p.name}`} k={`Narrowest width of a ${p.sidesIn.join("/")} panel`} v={`${p.minWidthIn} in`} />)}
            <Row k="Area to close, all panels" v={`${n(c.panelSqft)} sq ft`} />
            <Row k="The sphere those panels stand in for" v={`${n(c.sphereSqft)} sq ft`} />
          </dl>
          <p className="text-xs muted mt-2">The narrowest width is what decides whether a panel can be cut whole from a sheet: it fits if the sheet is at least that wide.</p>
        </div>
        <div>
          <h3 className="text-xl font-semibold mb-2">Frame</h3>
          <dl>
            {c.members.map((m) => <Row key={m.type} k={`${m.count} wedge members, type ${m.type}`} v={`${m.stockIn} in of stock each`} />)}
            <Row k="Nodes (where struts meet)" v={c.nodes} />
            <Row k="Seams between panels" v={`${c.seams}, ${n(c.seamFt)} ft in all`} />
            <Row k="Wood in the frame" v={`${c.woodCuft} cu ft`} />
            <Row k="Base ring" v={`${c.baseRingFt} ft around`} />
          </dl>
          <h3 className="text-xl font-semibold mt-6 mb-2">What the frame is made of, by cost</h3>
          <dl>
            <Row k="Wood (wedges, priced as shelf timber)" v={`${pct(cost.wood, cost.frame)} -- ${usd(cost.wood)}`} />
            <Row k="Joining hardware" v={`${pct(cost.hardware, cost.frame)} -- ${usd(cost.hardware)}`} />
            <Row k="Seam hose" v={`${pct(cost.seams, cost.frame)} -- ${usd(cost.seams)}`} />
            <Row k="The frame" v={usd(cost.frame)} />
          </dl>
          <p className="text-xs muted mt-2">{raw.notes.hardware} {raw.notes.cost} {raw.notes.frameLb}</p>
        </div>
      </div>
    </div>
  );
}

function useCounts() {
  const [counts, setCounts] = useState<Record<number, { n: number; built: number }>>({});
  useEffect(() => {
    api<{ classes: { longIn: number; n: number; built: number }[] }>("/domes")
      .then((r) => setCounts(Object.fromEntries(r.classes.map((c) => [c.longIn, { n: c.n, built: c.built }]))))
      .catch(() => undefined);
  }, []);
  return counts;
}

/** The one-number box: type a strut, get its class. */
function StrutBox({ onClass, initial }: { onClass: (c: DomeClass) => void; initial?: number }) {
  const [which, setWhich] = useState<"long" | "short">("long");
  const [v, setV] = useState(initial ? String(initial) : "");
  const [error, setError] = useState<string | null>(null);
  return (
    <form className="grid gap-3 text-sm" onSubmit={(e) => {
      e.preventDefault();
      const x = Number(v);
      const c = which === "long" ? classOf(x, null) : classOf(null, x);
      if (!c) { setError(which === "long" ? `Classes run from ${FIRST} to ${LAST} inches of longest strut.` : "No class has a shortest strut within half an inch of that."); return; }
      setError(null); onClass(c);
    }}>
      <div className="flex gap-4">
        <label className="flex gap-2"><input type="radio" checked={which === "long"} onChange={() => setWhich("long")} />My longest strut</label>
        <label className="flex gap-2"><input type="radio" checked={which === "short"} onChange={() => setWhich("short")} />My shortest strut</label>
      </div>
      <div className="flex gap-2">
        <input className="field" type="number" step="any" min={1} required placeholder="Inches, e.g. 72" value={v} onChange={(e) => setV(e.target.value)} />
        <button className="btn whitespace-nowrap">Show my class</button>
      </div>
      <p className="text-xs muted">In inches: 6 ft is 72 in. A 2V dome's shortest strut is always the same fraction of its longest, so either one names it.</p>
      <ErrorLine error={error} />
    </form>
  );
}

export default function Domes() {
  useMeta("Dome classes", "One number -- the longest strut -- and the whole dome follows: size, weight, panels, frame. Members with the same strut are one class and share panels.", "/domes");
  const go = useNavigate();
  const counts = useCounts();
  const popular = Object.entries(counts).sort((a, b) => b[1].n - a[1].n).slice(0, 12);
  return (
    <div className="mx-auto max-w-6xl px-4 py-10 grid gap-6">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">A home you can account for</p>
        <h1 className="text-4xl sm:text-5xl font-bold mt-1">One number names your whole dome</h1>
        <p className="mt-3 max-w-3xl">
          Measure the longest strut. From it the project's solver works out the rest: how wide and tall, how heavy the frame is,
          what share of it is wood and what share is hardware, the size of every panel, and what it takes to close it.
          Members whose domes share that number are a <b>dome class</b>: their panels fit each other's, so they can trade, lend and advise.
        </p>
      </div>
      <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <Panel kicker="Find your class" title="Enter one strut">
          <StrutBox onClass={(c) => go(`/domes/${c.longIn}`)} />
        </Panel>
        <Panel kicker="Counted from accounts" title="Classes with members">
          {popular.length ? (
            <ul className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-sm">
              {popular.map(([l, c]) => (
                <li key={l}><Link className="panel-2 p-3 block" to={`/domes/${l}`}><span className="num font-semibold accent">{l} in</span><span className="block text-xs muted">{c.n} member{c.n === 1 ? "" : "s"}, {c.built} built</span></Link></li>
              ))}
            </ul>
          ) : <p className="text-sm muted">No one has added a dome yet. Add yours on <Link className="underline" to="/account/dome">your account</Link> and you start the first class.</p>}
        </Panel>
      </div>
      <Panel kicker={`The book's dome: the ${BOOK.longIn}-inch class`} title="What one number gives you">
        <ClassSheet c={BOOK} />
      </Panel>
    </div>
  );
}

export function DomeClassPage() {
  const { longIn } = useParams();
  const { me } = useSession();
  const c = byLong(Number(longIn));
  const [data, setData] = useState<{ count: number; sameClass: boolean; members: { displayName: string; username: string; city: string; region: string; country: string; status: string; note: string; contact: string | null; you: boolean }[] } | null>(null);
  useMeta(c ? `Dome class ${c.longIn} in` : "Dome class", c ? `A ${c.diameterFt}-foot 2V wedge dome from a ${c.longIn}-inch longest strut: every figure computed, and the members who share its panels.` : "", `/domes/${longIn}`);
  useEffect(() => { if (c) api(`/domes/${c.longIn}`).then(setData).catch(() => setData(null)); }, [longIn, me?.dome?.longIn]); // eslint-disable-line react-hooks/exhaustive-deps
  if (!c) return <div className="mx-auto max-w-xl px-4 py-10"><p>No class for that strut. <Link className="underline" to="/domes">Find yours</Link>.</p></div>;
  const prev = byLong(c.longIn - 1), next = byLong(c.longIn + 1);
  return (
    <div className="mx-auto max-w-6xl px-4 py-10 grid gap-6">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">Dome class -- 2V wedge dome</p>
        <h1 className="text-4xl sm:text-5xl font-bold mt-1">{c.longIn}-inch longest strut <span className="muted text-2xl">({ftIn(c.longIn)})</span></h1>
        <p className="mt-2 muted">Shortest strut {c.shortIn} in. {raw.method}.</p>
        <p className="mt-2 text-sm flex gap-4">
          {prev && <Link className="underline" to={`/domes/${prev.longIn}`}>{prev.longIn} in</Link>}
          <Link className="underline" to="/domes">All classes</Link>
          {next && <Link className="underline" to={`/domes/${next.longIn}`}>{next.longIn} in</Link>}
        </p>
      </div>
      <Panel><ClassSheet c={c} /></Panel>
      <Panel kicker="Members who share these panels" title={data ? `${data.count} in this class` : "Members"}>
        {!data ? <p className="muted text-sm">Loading...</p> : (
          <>
            {data.members.length ? (
              <ul className="grid sm:grid-cols-2 gap-3 text-sm">
                {data.members.map((m, i) => (
                  <li key={i} className="panel-2 p-3">
                    <p className="font-semibold">{m.displayName}{m.username && <span className="muted font-normal"> @{m.username}</span>}{m.you && <span className="accent text-xs"> (you)</span>}</p>
                    <p className="muted">{[m.city, m.region, m.country].filter(Boolean).join(", ") || "Location not given"} -- {m.status}</p>
                    {m.note && <p className="mt-1">{m.note}</p>}
                    {m.contact && <p className="mt-1">Contact: {m.contact}</p>}
                  </li>
                ))}
              </ul>
            ) : <p className="text-sm muted">{data.count ? "Everyone in this class keeps their profile private." : "Nobody has joined this class yet."}</p>}
            <p className="text-xs muted mt-3">
              Only members with a public profile are named. {data.sameClass ? "You are in this class, so you see the contact each one lists on the network." : "Members of this class see each other's network contact."}
            </p>
            {!me && <p className="text-sm mt-3"><Link className="underline" to="/account">Make an account</Link> and add your dome to join a class.</p>}
            {me && !me.dome && <p className="text-sm mt-3"><Link className="underline" to="/account/dome">Add your dome</Link> to join a class.</p>}
          </>
        )}
      </Panel>
    </div>
  );
}

/** The account tab: attach your number, see your sheet, join your class. */
export function MyDomePanel() {
  const { me, refresh, notify } = useSession();
  const [c, setC] = useState<DomeClass | null>(me?.dome ? byLong(me.dome.longIn) : null);
  const [status, setStatus] = useState(me?.dome?.status || "planning");
  const [note, setNote] = useState(me?.dome?.note || "");
  const [error, setError] = useState<string | null>(null);
  const save = async () => {
    if (!c) return;
    setError(null);
    try {
      await api<{ dome: MyDome }>("/me/dome", { method: "PATCH", body: { longIn: c.longIn, status, note } });
      await refresh();
      notify("Dome saved", `You are in the ${c.longIn}-inch class.`);
    } catch (e) { setError((e as Error).message); }
  };
  return (
    <div className="grid gap-6">
      <div className="grid gap-6 lg:grid-cols-2">
        <Panel kicker="One number" title={me?.dome ? `Your dome: the ${me.dome.longIn}-inch class` : "Add your dome"}>
          <StrutBox initial={me?.dome?.longIn} onClass={setC} />
        </Panel>
        {c && (
          <Panel kicker={`${c.longIn}-inch class`} title="Save it to your account">
            <div className="grid gap-3 text-sm">
              <label className="grid gap-1">Where it stands
                <select className="field" value={status} onChange={(e) => setStatus(e.target.value)}>
                  <option value="planning">Planning it</option><option value="building">Building it</option><option value="built">Built</option>
                </select>
              </label>
              <label className="grid gap-1">A line for your class (optional)
                <input className="field" maxLength={300} placeholder="e.g. Spare BAB panels, happy to trade" value={note} onChange={(e) => setNote(e.target.value)} />
              </label>
              <div className="flex gap-2 flex-wrap">
                <button className="btn" onClick={save}>{me?.dome ? "Save changes" : "Join this class"}</button>
                <Link className="btn-ghost" to={`/domes/${c.longIn}`}>See the class</Link>
                {me?.dome && <button className="btn-ghost" onClick={async () => { await api("/me/dome", { method: "PATCH", body: { clear: true } }); setC(null); await refresh(); }}>Remove my dome</button>}
              </div>
              <p className="text-xs muted">Your class page names you only if your profile is public (Profile tab). The count includes everyone.</p>
              <ErrorLine error={error} />
            </div>
          </Panel>
        )}
      </div>
      {c && <Panel><ClassSheet c={c} /></Panel>}
    </div>
  );
}
