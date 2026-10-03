// The two ways to read the whole thing, as cards, and the nudge shown once
// somebody has the free sample in hand.

import { Link } from 'react-router-dom';
import { offered, price } from '../shop.js';

export function Upsell({ books, facts }) {
  const paid = offered(books, 'paid');
  const digital = facts?.books?.digital;
  if (!paid) return null;
  return (
    <div className="upsell">
      <p className="eyebrow">Next</p>
      <p>
        <b>The sample is a few chapters. The digital edition is all of it</b>
        {digital ? ` -- ${digital.chapters} chapters, ${digital.figures} figures, the whole build day by day` : ''}, for{' '}
        {price(paid.priceCents, paid.currency)}.
      </p>
      <Link className="button primary" to={`/${paid.page || 'buy'}`}>See what is in it</Link>
    </div>
  );
}

export function TwoWays({ books, facts }) {
  const paid = offered(books, 'paid');
  const print = offered(books, 'amazon');
  const digital = facts?.books?.digital;
  const paperback = facts?.books?.paperback;
  if (!paid && !print) return null;
  return (
    <section>
      <p className="eyebrow">Read all of it</p>
      <h2>Two books, one method</h2>
      <div className="offers">
        {paid && (
          <Link to={`/${paid.page || 'buy'}`} className="offer-card">
            {paid.cover && <img src={paid.cover} alt="" width="720" height="931" loading="lazy" />}
            <div>
              <span className="badge">Available now</span>
              <h3>{paid.subtitle || paid.title}</h3>
              <p className="muted">The digital edition{digital ? `: ${digital.chapters} chapters, ${digital.pages || '–'} pages` : ''}. Sold only here.</p>
              <p className="offer-price">{price(paid.priceCents, paid.currency)}</p>
            </div>
          </Link>
        )}
        {print && (
          <Link to={`/${print.page || 'paperback'}`} className="offer-card">
            {print.cover && <img src={print.cover} alt="" width="720" height="931" loading="lazy" />}
            <div>
              <span className="badge quiet">{print.amazonUrl ? 'On Amazon' : 'Coming to Amazon'}</span>
              <h3>{print.subtitle || print.title}</h3>
              <p className="muted">The paperback{paperback ? `: ${paperback.chapters} chapters, ${paperback.figures} figures` : ''}.</p>
              <p className="offer-price small">{print.amazonUrl ? 'Buy on Amazon' : 'Join the launch list'}</p>
            </div>
          </Link>
        )}
      </div>
    </section>
  );
}
