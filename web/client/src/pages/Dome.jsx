// The stem cell, in the model's own numbers: size, price, what we keep, the
// fit-outs, the panels, the reward tiers and the goal. Nothing on this page is
// typed in -- it all comes from /api/facts, exported from seed_model.

import { useEffect, useState } from 'react';
import { api, money } from '../api.js';

export default function Dome() {
  const [facts, setFacts] = useState(null);
  useEffect(() => {
    api('/facts').then((d) => setFacts(d.facts)).catch(() => setFacts(false));
  }, []);
  if (facts === null) return <p className="muted">Loading…</p>;
  if (!facts) return <p className="error">The dome's figures are not available right now.</p>;
  const { dome, price, wood, goal, tiers, fitouts, panels, quilt } = facts;
  const maxLine = Math.max(...goal.lines.map((l) => l.usd));

  return (
    <>
      <section>
        <p className="eyebrow">The stem cell</p>
        <h1>What it is, and what it costs</h1>
        <p className="lead">
          A 2V geodesic hemisphere: {dome.bays} flat triangular bays on a {dome.baseSides}-sided base, framed by{' '}
          {dome.members} solid timber wedges split from a log -- point in, flat face out. {dome.acrossFt} ft across,{' '}
          {dome.tallFt} ft tall, {Math.round(dome.floorSqft)} sq ft of floor.
        </p>
        <div className="price-stack">
          <div><span>What it costs us to build</span><b>{money(price.costToBuild)}</b></div>
          <div><span>What we keep ({Math.round(price.marginOnCost * 100)}% on cost, named as profit)</span><b>{money(price.profit)}</b></div>
          <div className="total"><span>What you pay for the stem cell</span><b>{money(price.stemCell)}</b></div>
          <div><span>Per square foot of floor</span><b>${price.perSqft.toFixed(2)}</b></div>
        </div>
      </section>

      <section>
        <h2>Why wedges -- and the part that argues back</h2>
        <p>
          Split into wedges, one log keeps <b>{wood.wedgeVsMilled}×</b> the wood it would as sawn boards. But every bay
          has its own three wedges, so the frame uses more pieces than a dome that shares its struts. Put together, it
          takes <b>{Math.round(wood.treesVsMitred * 100)}%</b> of the trees a mitred dome would. It wins by the
          difference, not by a headline.
        </p>
        <p className="muted">One quilted insulating layer is about {quilt.shirtsPerLayer} t-shirts of recycled fabric.</p>
      </section>

      <section>
        <h2>One frame, every building</h2>
        <div className="cards">
          {fitouts.map((f) => (
            <article key={f.key} className="card">
              <h3>{f.label}</h3>
              <p>{f.blurb}</p>
            </article>
          ))}
        </div>
      </section>

      <section>
        <h2>The panels</h2>
        <p className="muted">Each bay takes one. Lift a panel out and the opening is back -- the function of the building is a set of panels.</p>
        <table className="table">
          <thead><tr><th>Panel</th><th>What it is</th><th className="num">Price</th></tr></thead>
          <tbody>
            {panels.map((p) => (
              <tr key={p.key}><td>{p.label}</td><td>{p.note}</td><td className="num">{p.usd ? money(p.usd) : 'included'}</td></tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h2>Kickstarter reward tiers</h2>
        <div className="cards">
          {tiers.map((t) => (
            <article key={t.key} className="card tier">
              <p className="tier-price">{money(t.pledge)}</p>
              <h3>{t.label}</h3>
              <p>{t.why}.</p>
            </article>
          ))}
        </div>
      </section>

      <section>
        <h2>Where the {money(goal.total)} goes</h2>
        <p className="muted">The goal is the sum of this list -- not a round number somebody liked.</p>
        <div className="bars">
          {goal.lines.map((l) => (
            <div key={l.key} className="bar-row">
              <div className="bar-label">
                <b>{l.what}</b>
                <span className="muted small">{l.why}</span>
              </div>
              <div className="bar-track"><div className="bar" style={{ width: `${(l.usd / maxLine) * 100}%` }} /></div>
              <div className="bar-value">{money(l.usd)}</div>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
