// The paperback: DeepSeek's 3 Trees book, coming to Amazon. Until there is an Amazon link, the page
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
          <h1>{n ? `${n.trees} trees. One chainsaw. A ${n.diameterFt}-foot geodesic cabin.` : 'Trees, one chainsaw, and a geodesic cabin.'}</h1>
          <p className="lead">
            <b>{paperback ? fullTitle(paperback.title, paperback.subtitle) : book ? fullTitle(book.title, book.subtitle) : ''}</b>
            {book?.author ? `, by ${book.author}` : ''}. The whole method in print, start to finish -- felling, splitting,
            the jig, the panels, raising the shell -- then why it scales, and everything it grows into. Every length,
            angle and dollar in it is computed by the project's own open model.
          </p>
          {n && (
            <ul className="stats">
              <li><b>{n.days}</b> days, tree to shell</li>
              <li><b>{n.strutsPerTree}</b> struts from one tree</li>
              <li><b>{n.members}</b> members, <b>{n.panels}</b> panels</li>
              <li><b>{n.floorSqft}</b> sq ft of floor</li>
              <li><b>${n.sawUsd}</b> chainsaw</li>
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
            Every figure in it -- the {n ? `${n.members} members` : 'members'}, the cut lengths, the days and the
            dollars -- is produced by the project's open software when the book is built. Nothing is typed in, so
            nothing goes quietly stale.
          </p>
        </div>
        <div className="panel">
          <h3>Build it day by day</h3>
          <p className="muted">
            The build in the order it happens, from the saw on day zero to a closed shell, then why the same nine
            processes work at any size, and the variations the frame can become.
          </p>
        </div>
      </section>

      {paid && (
        <section className="closing">
          <h2>Want the long version now?</h2>
          <p className="lead">
            The complete edition, <b>{fullTitle(paid.title, paid.subtitle)}</b>, is the 40-hour frame plus every way to
            finish it, priced -- sold only on this site, {price(paid.priceCents, paid.currency)}.
          </p>
          <Link className="button primary big" to={`/${paid.page || 'buy'}`}>See the complete edition</Link>
        </section>
      )}
    </>
  );
}
