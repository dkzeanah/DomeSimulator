// "The build, live": the public numbers, counted from the database. When nothing has
// happened yet the panel says zero -- the mirror rule.

import { useEffect, useState } from "react";
import { api, money, n } from "../lib/api";
import { facts } from "../lib/facts";
import { Fraction, Stat } from "./ui";

export interface Stats {
  subscribers: number; members: number; sampleDownloads: number; booksSold: number; pads: number; padsHosting: number;
  listings: number; backers: number; pledgedCents: number; goalUsd: number; plaquesClaimed: number; plaqueSlots: number;
  salvageHours: number; salvageCents: number; feed: { kind: string; label: string; created_at: string }[];
}

export function useStats(tick = 0) {
  const [s, setS] = useState<Stats | null>(null);
  useEffect(() => { api<Stats>("/stats").then(setS).catch(() => setS(null)); }, [tick]);
  return s;
}

const ago = (iso: string) => {
  const m = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m} min ago`;
  if (m < 1440) return `${Math.round(m / 60)} h ago`;
  return `${Math.round(m / 1440)} d ago`;
};

export function LivePanel({ stats }: { stats: Stats | null }) {
  if (!stats) return <p className="muted text-sm">The live numbers could not be read just now.</p>;
  return (
    <div className="grid gap-5">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Stat value={n(stats.subscribers)} label="on the list" />
        <Stat value={n(stats.members)} label="accounts" />
        <Stat value={n(stats.pads)} label="pads on the network" note={`${n(stats.padsHosting)} hosting now`} />
        <Stat value={n(stats.backers)} label="backers" />
      </div>
      <Fraction have={Math.round(stats.pledgedCents / 100)} need={stats.goalUsd} unit="$" label="Recorded backing toward the build goal" />
      <Fraction have={stats.plaquesClaimed} need={stats.plaqueSlots} label="Founder plaques claimed (one per panel)" />
      <div>
        <p className="text-xs uppercase tracking-[0.18em] muted mb-2">Latest</p>
        {stats.feed.length ? (
          <ul className="text-sm space-y-1">
            {stats.feed.slice(0, 6).map((e, i) => (
              <li key={i} className="flex justify-between gap-3"><span>{e.label}</span><span className="muted whitespace-nowrap">{ago(e.created_at)}</span></li>
            ))}
          </ul>
        ) : <p className="text-sm muted">Nothing yet. The first entry here will be a real one.</p>}
      </div>
      <p className="text-xs muted">Goal {money(facts.goal.total * 100)} from <code>kickstarter.goal_lines()</code>; {facts.plaques.slots} plaque slots from the stem cell's own panels.</p>
    </div>
  );
}
