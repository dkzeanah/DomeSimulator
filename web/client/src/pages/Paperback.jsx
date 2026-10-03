// The paperback: coming to Amazon. Until there is an Amazon link, the page
// gathers a launch list; with one, it is a Buy on Amazon button.

import { Link } from 'react-router-dom';
import Waitlist from '../components/Waitlist.jsx';
import { fullTitle, offered, price, useBooks, useFacts } from '../shop.js';

export default function Paperback() {
  const { books, error } = useBooks();
  const facts = useFacts();
  const book = offered(books, 'amazon');
  const paid = offered(books, 'paid');
  const paperback = facts?.books?.paperback;
  const n = paperback?.numbers;

  return (
    <>
      <section className="sales-hero">
        <div>
          <p className="eyebrow">{book?.amazonUrl ? 'On Amazon' : 'Coming to Amazon'} · paperback</p>
          <h1>From a standing tree to a dry, raised shell.</h1>
          <p className="lead">
            <b>{paperback ? fullTitle(paperback.title, paperback.subtitle) : book ? fullTitle(book.title, book.subtitle) : ''}</b>
            {paperback?.author ? `, by ${paperback.author}` : ''}. A timber cabin framed from trees you split yourself:
            what has to be right, the geometry from one number, the stick, the panel, the skin, the seam, the ground,
            and what all of it costs -- every length, angle and price computed from the geometry.
          </p>
          {n && (
            <ul className="stats">
              <li><b>{n.frameHours} h</b> of frame work</li>
              <li><b>{n.members}</b> members in two lengths</li>
              <li><b>{n.panels}</b> panels, one jig</li>
              <li><b>{n.diameterFt} ft</b> across, <b>{n.floorSqft}</b> sq ft</li>
            </ul>
          )}
        </div>
        <div className="hero-card">
          {error && <p className="error">{error}</p>}
          {book?.cover && <img className="book-cover" src={book.cover} alt={`Cover of ${fullTitle(book.title, book.subtitle)}`} width="720" height="931" />}
          {paperback && (
            <p className="small muted center">
              {paperback.parts.length} Parts · {paperback.chapters} chapters · {paperback.figures} figures
              {paperback.pages ? ` · ${paperback.pages} pages` : ''}
            </p>
          )}
          {!book?.amazonUrl && <h2>Be first to know</h2>}
          <Waitlist book={book} />
          <p className="small center">
            Or read the opening now: <Link to="/sample">the free sample</Link>
          </p>
        </div>
      </section>

      {paperback && (
        <section>
          <p className="eyebrow">What is in it</p>
          <h2>{paperback.parts.length} Parts, in the order you need them</h2>
          <ol className="parts-grid">
            {paperback.parts.map((part) => (
              <li key={part.number}>
                <span className="part-n">Part {part.number}</span>
                <b>{part.title}</b>
                <span className="muted small">{part.chapters.map((c) => c.title).join(' · ')}</span>
              </li>
            ))}
          </ol>
        </section>
      )}

      <section className="split">
        <div className="panel">
          <h3>A book that shows its working</h3>
          <p className="muted">
            Every figure in it -- the {n ? `${n.members} members` : 'members'}, the cut lengths, the hours, the
            {n ? ` $${n.frameUsd} frame` : ' frame'} and the {n ? `$${n.shellUsd}` : ''} it costs to build the whole
            dome -- is produced by the project's open software when the book is built. Nothing is typed in, so nothing
            goes quietly stale.
          </p>
        </div>
        <div className="panel">
          <h3>And says where the savings are not</h3>
          <p className="muted">
            Most of the saving is building it yourself -- the margin and the labour anyone keeps who builds their own
            house. The dome's own shape is a real saving and a small one
            {n?.unchangedPct ? `, and ${n.unchangedPct} percent of what a house costs does not care what shape it is at all` : ''}.
            The book prints those numbers too.
          </p>
        </div>
      </section>

      {paid && (
        <section className="closing">
          <h2>Want the long version now?</h2>
          <p className="lead">
            The digital edition, <b>{paid.subtitle}</b>, is the whole build day by day plus how it scales -- sold only
            on this site, {price(paid.priceCents, paid.currency)}.
          </p>
          <Link className="button primary big" to={`/${paid.page || 'buy'}`}>See the digital edition</Link>
        </section>
      )}
    </>
  );
}
