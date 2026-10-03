// The lead magnet: the free sample, for an email.

import BookGate from '../components/BookGate.jsx';
import { TwoWays, Upsell } from '../components/Offers.jsx';
import { offered, useBooks, useFacts } from '../shop.js';

export default function Sample() {
  const { books, error } = useBooks();
  const facts = useFacts();
  const book = offered(books, 'free');
  const sample = facts?.books?.sample;
  const paperback = facts?.books?.paperback;
  const n = paperback?.numbers;

  return (
    <>
      <section className="sales-hero">
        <div>
          <p className="eyebrow">Free sample · PDF{sample?.pages ? ` · ${sample.pages} pages` : ''}</p>
          <h1>Read the part most dome guides skip.</h1>
          <p className="lead">
            Most dome books open with angles. This one opens with what actually has to be right -- and what you are
            allowed to get wrong. The frame forgives. Water does not. And the whole method rests on one cut: stop
            squaring the log, start splitting it.
          </p>
          {n && (
            <ul className="stats">
              <li><b>{n.members}</b> split-log members</li>
              <li><b>{n.panels}</b> flat-built panels</li>
              <li><b>{n.floorSqft}</b> sq ft of floor</li>
              <li><b>{n.frameHours} h</b> of frame work</li>
            </ul>
          )}
        </div>
        <div className="hero-card">
          {error && <p className="error">{error}</p>}
          {book ? (
            <>
              {book.cover && <img className="book-cover" src={book.cover} alt={`Cover of ${book.subtitle || book.title}`} width="720" height="931" />}
              <h2>{book.title}</h2>
              {book.subtitle && <p className="subtitle">{book.subtitle}</p>}
              <BookGate book={book} cta="Send me the free sample" after={<Upsell books={books} facts={facts} />} />
            </>
          ) : (
            !error && <p className="muted">Loading…</p>
          )}
        </div>
      </section>

      {sample && (
        <section className="split">
          <div>
            <h2>What is in the sample</h2>
            <p>
              Pages cut straight from the paperback -- its own page numbers, figures and tables -- so what you read is
              exactly what the book prints. {sample.chapters.length} of its {sample.ofChapters} chapters:
            </p>
            <ol className="checklist">
              {sample.front.map((title) => (
                <li key={title}><b>{title}</b> -- the promise, and how the hours are counted</li>
              ))}
              {sample.chapters.map((c) => (
                <li key={c.number}><span className="muted">Chapter {c.number}</span> <b>{c.title}</b></li>
              ))}
            </ol>
          </div>
          <div className="panel">
            <h3>Why the sample starts here</h3>
            <p className="muted">
              A dome is a frame, a skin and a floor. People spend all their care on the frame -- the one part that
              forgives mistakes -- and lose the house to the skin. These chapters put the care where it belongs before
              you cut anything.
            </p>
            <p className="muted">
              Then the cut itself. A round log is already symmetric, so split it and every wedge comes out alike --
              no mill, no planer, and not half the tree thrown away as the price of a rectangle.
            </p>
          </div>
        </section>
      )}

      <TwoWays books={books} facts={facts} />
    </>
  );
}
