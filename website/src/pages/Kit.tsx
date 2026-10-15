// The promotional kit: cheat sheet, campaign outline, presentation, letters, outreach.
// Every figure is read from facts; the letters' bracketed fields are for the sender.

import { useEffect, useState } from "react";
import { useMeta } from "../lib/meta";
import { NavLink, Route, Routes } from "react-router-dom";
import { Panel } from "../components/ui";
import { usd } from "../lib/api";
import { book, cabin, facts, sample } from "../lib/facts";

const d = facts.dome, p = facts.price, x = cabin.numbers;
const SITE = "https://www.zeanahlab.com";

function CheatSheet() {
  const rows: [string, string, string][] = [
    ["The dome", `${d.acrossFt} ft across, ${d.tallFt} ft tall, ${d.floorSqft} sq ft of floor`, "seed_model.seed_geometry()"],
    ["The frame", `${d.members} wedge members, ${d.bays} panels, ${d.vertices} vertices`, "seed_model"],
    ["Frame work", `${x.frameHours} hours`, "the book's hour ledger"],
    ["Price of the stem cell", `${usd(p.stemCell)} (cost ${usd(p.costToBuild)}, ${Math.round(p.marginOnCost * 100)}% on cost)`, "kickstarter.cost_stack()"],
    ["Per square foot", usd(p.perSqft), "kickstarter.cost_stack()"],
    ["Wood one log keeps as wedges", `${facts.wood.wedgeVsMilled}x what it keeps as boards`, "seed_model.harvest()"],
    ["Trees, against a mitred dome", `${Math.round(facts.wood.treesVsMitred * 100)}%`, "seed_model.trees_against_mitred()"],
    ["Quilt insulation", `${facts.quilt.shirtsPerLayer} shirts a layer`, "kickstarter.quilt_economics()"],
    ["Campaign goal", usd(facts.goal.total), "kickstarter.goal_lines()"],
    ["Founder plaques", `${facts.plaques.slots}, one per panel`, "seed_model faces"],
    ["The book", `${cabin.pages} pages, ${cabin.chapters} chapters, ${cabin.figures} computed figures`, "wedge_book"],
  ];
  return (
    <Panel kicker="One page" title="Project cheat sheet">
      <table className="w-full text-sm">
        <tbody>
          {rows.map(([k, v, src]) => (
            <tr key={k} className="border-t align-top" style={{ borderColor: "var(--line)" }}>
              <td className="py-2 pr-3 font-semibold">{k}</td><td className="py-2 pr-3 num">{v}</td><td className="py-2 text-xs muted"><code>{src}</code></td>
            </tr>
          ))}
        </tbody>
      </table>
      <h3 className="text-2xl font-semibold mt-8">The rules the site is built on</h3>
      <ul className="text-sm mt-2 grid gap-1.5">
        <li><b>The two questions.</b> What does this hour produce? What does this hour make possible?</li>
        <li><b>Rate and gate.</b> Every pad, method and offer shows what it pays and what it takes to get in.</li>
        <li><b>The mirror rule.</b> The site shows real numbers moving. It never invents progress, and an empty list says so.</li>
        <li><b>Credentials that are also structure.</b> A founder's plaque is a panel of the building.</li>
      </ul>
      <button className="btn-ghost mt-6" onClick={() => window.print()}>Print this page</button>
    </Panel>
  );
}

function Outline() {
  return (
    <div className="grid gap-6">
      <Panel kicker="Campaign outline" title="What is being funded, and why">
        <ol className="grid gap-3">
          {facts.goal.lines.map((l, i) => (
            <li key={l.key} className="panel-2 p-4">
              <div className="flex justify-between gap-3"><b>{i + 1}. {l.what}</b><span className="num accent">{usd(l.usd)}</span></div>
              <p className="text-sm muted mt-1">{l.why}</p>
            </li>
          ))}
        </ol>
        <p className="text-sm mt-4 num">Total: <b>{usd(facts.goal.total)}</b></p>
      </Panel>
      <Panel kicker="Rewards" title="Tiers">
        <ul className="grid md:grid-cols-2 gap-3">
          {[...facts.tiers].sort((a, b) => a.pledge - b.pledge).map((t) => (
            <li key={t.key} className="panel-2 p-4"><b>{usd(t.pledge)} - {t.label}</b><p className="text-sm muted mt-1">{t.why}</p></li>
          ))}
        </ul>
        <p className="text-sm muted mt-4">
          The {book.title} itself -- {usd((book.priceCents || 0) / 100)} digital, and the hand-made triangular edition when it is printed --
          is the reward that funds the middle of the campaign. The founder plaques ({facts.plaques.slots}) are its top.
        </p>
      </Panel>
    </div>
  );
}

const SLIDES: { kicker: string; title: string; body: string; img?: string }[] = [
  { kicker: "Zeanah Lab", title: "A home you can read like an account", body: `A ${d.acrossFt}-foot dome split from logs, every number computed by open code.`, img: "dome-filled-dialled-pairs" },
  { kicker: "The problem", title: "Housing hides its numbers", body: "What a home costs, what it earns, who built it and whether it worked -- none of it is written down where anyone can check." },
  { kicker: "The object", title: `${d.members} wedges, ${d.bays} panels`, body: `${x.frameHours} hours of frame work. ${usd(p.stemCell)} for the stem cell, ${usd(p.perSqft)} a square foot.`, img: "dome-frame-open-triangles" },
  { kicker: "The wood", title: `${facts.wood.wedgeVsMilled}x the wood from every log`, body: `Split into wedges instead of sawn into boards -- and ${Math.round(facts.wood.treesVsMitred * 100)}% of the trees a mitred dome takes.` },
  { kicker: "Finished any way", title: "Every triangle closed, cut flush", body: "Pairs, rings, chevrons, louvers, covers: each one built from the infill tool's own solids.", img: "dome-filled-rings-flipflop" },
  { kicker: "The network", title: "Pads with their numbers on", body: "Each pad shows its rate, how often it is let, and what a season costs -- the same arithmetic for every pad." },
  { kicker: "The proof", title: `${cabin.pages} pages, ${cabin.figures} computed figures`, body: `The 40 Hour Cabin: the method, the tools and the costs. The first ${sample.pages} pages are free.` },
  { kicker: "The ask", title: `${usd(facts.goal.total)} to stand one dome for a year`, body: "One standing, instrumented dome, the hub designed until it ships, and the tools to make the next ones." },
  { kicker: "Founders", title: `${facts.plaques.slots} panels, ${facts.plaques.slots} names`, body: "A founder's plaque is a panel of the building -- permanent, public, and load-bearing.", img: "dome-filled-louvers" },
];

function Presentation() {
  const [i, setI] = useState(0);
  useEffect(() => {
    const k = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === " ") setI((v) => Math.min(SLIDES.length - 1, v + 1));
      if (e.key === "ArrowLeft") setI((v) => Math.max(0, v - 1));
    };
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, []);
  const s = SLIDES[i];
  return (
    <div className="panel overflow-hidden">
      <div className="grid md:grid-cols-2 min-h-[420px]">
        <div className="p-8 flex flex-col justify-center">
          <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">{s.kicker}</p>
          <h2 className="text-4xl font-bold mt-2">{s.title}</h2>
          <p className="mt-4 text-lg muted">{s.body}</p>
        </div>
        {s.img ? <img src={`/img/${s.img}.jpg`} alt="" className="w-full h-full object-cover" /> : <div className="bg-[var(--panel-2)] grid place-items-center"><div className="tri w-40 h-36 bg-[var(--accent)] opacity-80" /></div>}
      </div>
      <div className="flex items-center justify-between p-4 border-t" style={{ borderColor: "var(--line)" }}>
        <button className="btn-ghost" onClick={() => setI(Math.max(0, i - 1))} disabled={i === 0}>Back</button>
        <span className="muted text-sm num">{i + 1} / {SLIDES.length} - arrow keys work</span>
        <button className="btn" onClick={() => setI(Math.min(SLIDES.length - 1, i + 1))} disabled={i === SLIDES.length - 1}>Next</button>
      </div>
    </div>
  );
}

const LETTERS: { key: string; title: string; to: string; body: string }[] = [
  { key: "veterans", title: "To a veterans' organization", to: "[Organization], [Name]",
    body: `Dear [Name],\n\nI am building a small, owner-built home -- a ${d.acrossFt}-foot dome framed from split logs in about ${x.frameHours} hours of frame work -- and a network of people who build, host and maintain them. Every number in the method is computed by open code and published at ${SITE}.\n\nThe work is skilled, physical and teachable: felling and splitting, cutting to a cut list, raising a frame, fitting panels. Veterans are exactly the builders, maintainers and teachers this needs, and I would like to talk with you about whether any of your members want to learn it, teach it, or host a build.\n\nI can send the book's free opening (${sample.pages} pages) or come and show the method in person.\n\nWith respect,\n[Your name]\n${SITE}` },
  { key: "landowner", title: "To a landowner (pad host)", to: "[Name]",
    body: `Dear [Name],\n\nI am looking for land where a small dome could stand on a serviced pad -- water, power and drainage to one spot. The pad network at ${SITE}/network lists every pad with its own numbers: the nightly rate, how often it is let, and what a season costs to run, worked out the same way for every host.\n\nIf you have a corner that could take a ${d.acrossFt}-foot circle, I would be glad to walk it with you and work out together what it would cost and what it could earn.\n\nThank you,\n[Your name]` },
  { key: "press", title: "To a journalist", to: "[Publication], [Name]",
    body: `Dear [Name],\n\nA dome you can build from logs with one chainsaw, ${d.members} wedge members, ${x.frameHours} hours of frame work -- and a book (${cabin.pages} pages, ${cabin.figures} figures) in which every number is computed by code anyone can read.\n\nThe project publishes what is usually hidden: what the home costs (${usd(p.stemCell)} for the stem cell), what each piece takes, and -- when the first dome has stood a year -- what the sensors in its walls measured, whichever way it comes out.\n\nI would be happy to send the book, the films, or a still of any figure. ${SITE}\n\n[Your name]` },
  { key: "salvage", title: "To a business with reclaimable material", to: "[Business], [Name]",
    body: `Dear [Name],\n\nWe build small domes and log every load of reclaimed material we use -- what it was, how long it took to reclaim, and what it would have cost new. If you have material headed for disposal (clean timber, sheet goods, fabric for quilted insulation), we would collect it and record it publicly at ${SITE}/recyclers, credited to you if you wish.\n\nThank you,\n[Your name]` },
  { key: "permit", title: "To a building department", to: "[Jurisdiction] Building Department",
    body: `Hello,\n\nI am planning a ${d.floorSqft}-square-foot accessory structure: a ${d.acrossFt}-foot-diameter geodesic dome framed in split timber on a prepared pad. Before applying, I would like to ask what this jurisdiction requires for a structure of this size and use -- engineering, foundation, and any exemption thresholds -- so the application is complete the first time.\n\nI can provide the full member schedule and geometry, all generated by the project's open software.\n\nThank you,\n[Your name]\n[Address of the site]` },
];

function Letters() {
  const [copied, setCopied] = useState<string | null>(null);
  return (
    <div className="grid gap-4">
      {LETTERS.map((l) => (
        <Panel key={l.key} kicker={`To: ${l.to}`} title={l.title}>
          <pre className="whitespace-pre-wrap text-sm font-sans">{l.body}</pre>
          <button className="btn-ghost mt-3" onClick={async () => { await navigator.clipboard.writeText(l.body).catch(() => undefined); setCopied(l.key); }}>
            {copied === l.key ? "Copied" : "Copy the letter"}
          </button>
        </Panel>
      ))}
    </div>
  );
}

function Outreach() {
  const groups = [
    ["Veterans", "Builders, maintainers and teachers. The work is skilled, physical and credentialed by what you have built -- a frame you raised is its own proof. Learn it, teach it, or host a build.", "/kit/letters"],
    ["Women building a place of their own", "The stated first beneficiaries of the network: a home that is owned outright, small enough to finish, built where you choose, among neighbours who are on the map. Safety, ownership, independence, community.", "/network"],
    ["Recyclers", "Reclaimed timber, sheet goods and fabric go into real builds. Every load is logged: what it was, the hours, and what it would have cost new.", "/recyclers"],
    ["Landowners", "A serviced pad on a corner of your land. Its numbers -- rate, nights let, running cost -- are shown the same way as every other pad's.", "/network"],
  ];
  return (
    <div className="grid md:grid-cols-2 gap-4">
      {groups.map(([t, b, to]) => (
        <Panel key={t} title={t}><p className="text-sm muted">{b}</p><a className="btn-ghost mt-3" href={to}>Start here</a></Panel>
      ))}
    </div>
  );
}

export default function Kit() {
  useMeta("Press kit and letters", "The dome project on one page: cheat sheet, campaign outline, presentation, and letter templates for veterans organizations, landowners, press and recyclers.", "/kit");
  const tab = ({ isActive }: { isActive: boolean }) => (isActive ? "accent font-semibold" : "muted");
  return (
    <div className="mx-auto max-w-6xl px-4 py-10 grid gap-6">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">For press, partners and backers</p>
        <h1 className="text-4xl font-bold mt-1">The kit</h1>
        <nav className="flex flex-wrap gap-5 mt-4 text-sm">
          <NavLink end to="/kit" className={tab}>Cheat sheet</NavLink>
          <NavLink to="/kit/outline" className={tab}>Campaign outline</NavLink>
          <NavLink to="/kit/presentation" className={tab}>Presentation</NavLink>
          <NavLink to="/kit/letters" className={tab}>Letters</NavLink>
          <NavLink to="/kit/outreach" className={tab}>Outreach</NavLink>
        </nav>
      </div>
      <Routes>
        <Route index element={<CheatSheet />} />
        <Route path="outline" element={<Outline />} />
        <Route path="presentation" element={<Presentation />} />
        <Route path="letters" element={<Letters />} />
        <Route path="outreach" element={<Outreach />} />
      </Routes>
    </div>
  );
}
