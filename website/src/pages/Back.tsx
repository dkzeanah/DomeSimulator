import { useEffect, useState } from "react";
import { useMeta } from "../lib/meta";
import { ErrorLine, Fraction, Panel } from "../components/ui";
import { useStats } from "../components/Live";
import { api, money, usd } from "../lib/api";
import { facts } from "../lib/facts";

interface Plaque { slot: number; inscription: string | null; status: string; display_name: string | null }
interface Backer { display_name: string; tier: string; pledge_cents: number }

function LaunchList({ source, label }: { source: string; label: string }) {
  const [email, setEmail] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  async function join(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api("/subscribe", { body: { email, source, marketingConsent: true } });
      setDone(true);
    } catch (err) { setError((err as Error).message); }
  }
  return done ? <p className="accent">You will hear the day the campaign opens.</p> : (
    <form onSubmit={join} className="flex flex-col sm:flex-row gap-2">
      <input className="field" type="email" required placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} />
      <button className="btn whitespace-nowrap">{label}</button>
      <ErrorLine error={error} />
    </form>
  );
}

/** The forty panels, as a wall of triangles: gold where a founder's name is. */
function PlaqueWall({ plaques }: { plaques: Plaque[] }) {
  const bySlot = new Map(plaques.map((p) => [p.slot, p]));
  return (
    <div className="grid grid-cols-8 sm:grid-cols-10 gap-1.5">
      {Array.from({ length: facts.plaques.slots }, (_, i) => {
        const p = bySlot.get(i + 1);
        return (
          <div key={i} title={p ? `Panel ${i + 1}: ${p.inscription || p.display_name || "founder"} (${p.status})` : `Panel ${i + 1}: open`}
            className={`tri aspect-[1.15] flex items-end justify-center pb-1 text-[10px] num ${p ? "bg-[var(--accent)] text-[var(--accent-ink)]" : "bg-[var(--panel-2)] muted"}`}
            style={{ transform: i % 2 ? "rotate(180deg)" : undefined }}>
            <span style={{ transform: i % 2 ? "rotate(180deg)" : undefined }}>{i + 1}</span>
          </div>
        );
      })}
    </div>
  );
}

export default function Back() {
  useMeta("Back the build: founder plaques", `Back the first standing, instrumented geodesic dome: campaign tiers priced by the cost model, and ${facts.plaques.slots} founder plaques, one per panel.`, "/back");
  const stats = useStats();
  const [plaques, setPlaques] = useState<Plaque[]>([]);
  const [backers, setBackers] = useState<Backer[]>([]);
  useEffect(() => {
    api<{ plaques: Plaque[] }>("/plaques").then((r) => setPlaques(r.plaques)).catch(() => undefined);
    api<{ backers: Backer[] }>("/backers").then((r) => setBackers(r.backers)).catch(() => undefined);
  }, []);
  const ks = facts.site.kickstarterUrl;
  const tiers = [...facts.tiers].sort((a, b) => a.pledge - b.pledge);
  return (
    <div className="mx-auto max-w-6xl px-4 py-10 grid gap-6">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">Back the build</p>
        <h1 className="text-4xl sm:text-5xl font-bold mt-1">Put your name on something permanent</h1>
        <p className="muted mt-2 max-w-3xl">
          The campaign funds one standing dome, measured for a year, and the tools to make the next ones. Every tier below is priced by the
          project's own cost model, and every backer recorded here is a real one.
        </p>
      </div>

      <Panel kicker={ks ? "The campaign is open" : "The campaign opens soon"} title={`Goal ${usd(facts.goal.total)}`}>
        {stats && <Fraction have={Math.round(stats.pledgedCents / 100)} need={facts.goal.total} unit="$" label="Recorded backing" />}
        <div className="mt-4">
          {ks ? <a className="btn" href={ks}>Back it on Kickstarter</a> : <LaunchList source="backer" label="Tell me the day it opens" />}
        </div>
      </Panel>

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
        {tiers.map((t) => (
          <article key={t.key} className="panel p-5 flex flex-col">
            <p className="num text-2xl font-semibold accent">{usd(t.pledge)}</p>
            <h3 className="text-xl font-semibold mt-1">{t.label}</h3>
            <p className="text-sm muted mt-2 flex-1">{t.why}</p>
          </article>
        ))}
      </div>

      <Panel kicker="Founders" title={`The plaque wall: ${plaques.length} of ${facts.plaques.slots} panels claimed`}>
        <p className="muted text-sm mb-4">
          One plaque per panel of the first dome -- {facts.plaques.slots} in all, the count read from the dome's own geometry. A founder's plaque is a
          triangle cut to fit its panel and mounted in the building; it is listed here the day it is claimed, and marked again when it is cut and when it is mounted.
        </p>
        <PlaqueWall plaques={plaques} />
        {!ks && <div className="mt-5"><LaunchList source="founder" label="Hold me a panel's place in line" /></div>}
      </Panel>

      <Panel kicker="Public record" title="Backers">
        {backers.length ? (
          <ul className="grid sm:grid-cols-2 gap-2 text-sm">
            {backers.map((b, i) => (
              <li key={i} className="panel-2 p-3 flex justify-between gap-3">
                <span>{b.display_name}</span>
                <span className="muted">{facts.tiers.find((t) => t.key === b.tier)?.label || b.tier} - {money(b.pledge_cents)}</span>
              </li>
            ))}
          </ul>
        ) : <p className="muted text-sm">No backers recorded yet. The first name here will be a real one.</p>}
      </Panel>
    </div>
  );
}
