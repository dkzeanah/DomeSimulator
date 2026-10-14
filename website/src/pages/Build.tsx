import { LivePanel, useStats } from "../components/Live";
import { useMeta } from "../lib/meta";
import { Fraction, Panel, Stat } from "../components/ui";
import { usd } from "../lib/api";
import { facts } from "../lib/facts";

export default function Build() {
  useMeta("The stem-cell dome, inspected", `The ${facts.dome.acrossFt}-foot stem-cell dome: ${facts.dome.members} wedge members, ${facts.dome.bays} panels, its fit-outs and panel options, and what every dollar of the build goal is for.`, "/build");
  const stats = useStats();
  const d = facts.dome;
  const pledged = stats ? stats.pledgedCents / 100 : 0;
  // Goal lines are funded in the order the model lists them: a line is "funded" only
  // when recorded backing covers it and every line before it.
  let running = 0;
  const lines = facts.goal.lines.map((l) => {
    const start = running;
    running += l.usd;
    return { ...l, funded: Math.max(0, Math.min(l.usd, pledged - start)) };
  });
  return (
    <div className="mx-auto max-w-6xl px-4 py-10 grid gap-6">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">Inspect the dome</p>
        <h1 className="text-4xl sm:text-5xl font-bold mt-1">The stem cell, as an account</h1>
        <p className="muted mt-2 max-w-3xl">
          In a game you can inspect a player and read what they have done. This is the dome inspected the same way: its stats,
          its gear slots, and what every dollar of the goal is for. Nothing here is typed by hand; it is read from the cost model.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat value={`${d.acrossFt} ft`} label="across" />
        <Stat value={`${d.floorSqft} sq ft`} label="floor" />
        <Stat value={d.bays} label="panels (bays)" />
        <Stat value={d.members} label="wedge members" />
        <Stat value={usd(facts.price.stemCell)} label="stem-cell price" note={`cost to build ${usd(facts.price.costToBuild)}`} />
        <Stat value={`${Math.round(facts.price.marginOnCost * 100)}%`} label="margin on cost" note={`${usd(facts.price.profit)} a dome`} />
        <Stat value={usd(facts.price.perSqft)} label="per square foot" />
        <Stat value={`${facts.wood.wedgeVsMilled}x`} label="wood one log keeps as wedges, vs boards"
          note={`${Math.round(facts.wood.treesVsMitred * 100)}% of the trees a mitred dome takes`} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel kicker="Gear slots" title="Fit-outs">
          <ul className="grid gap-2">
            {facts.fitouts.map((f) => (
              <li key={f.key} className="panel-2 p-3">
                <p className="font-semibold">{f.label} <span className="muted text-xs font-normal">({f.shape})</span></p>
                <p className="text-sm muted mt-1">{f.blurb}</p>
              </li>
            ))}
          </ul>
        </Panel>
        <Panel kicker="Gear slots" title="Panel options">
          <ul className="grid gap-2">
            {facts.panels.map((p) => (
              <li key={p.key} className="panel-2 p-3 flex justify-between gap-3">
                <span><span className="font-semibold">{p.label}</span><span className="block text-xs muted">{p.note}</span></span>
                <span className="num font-semibold accent whitespace-nowrap">{usd(p.usd)}</span>
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      <Panel kicker="Where the money goes" title={`The goal: ${usd(facts.goal.total)}`}>
        <div className="grid gap-4">
          {lines.map((l) => (
            <div key={l.key} className="panel-2 p-4">
              <Fraction have={Math.round(l.funded)} need={Math.round(l.usd)} unit="$" label={l.what} />
              <p className="text-sm muted mt-2">{l.why}</p>
            </div>
          ))}
        </div>
      </Panel>

      <Panel kicker="Counted, not claimed" title="The build, live">
        <LivePanel stats={stats} />
      </Panel>
    </div>
  );
}
