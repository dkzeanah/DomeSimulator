// The sales page for the digital edition, sold here.

import { Link, useSearchParams } from 'react-router-dom';
import BuyBox from '../components/BuyBox.jsx';
import { chapterCount, fullTitle, offered, price, useBooks, useFacts } from '../shop.js';

export default function Buy() {
  const { books, error } = useBooks();
  const facts = useFacts();
  const [params] = useSearchParams();
  const book = offered(books, 'paid');
  const digital = facts?.books?.digital;
  const n = digital?.numbers;
  const amount = book ? price(book.priceCents, book.currency) : '';
  const [build, scale, variations] = digital?.parts || [];

  return (
    <>
      {params.get('cancelled') && (
        <p className="callout">Checkout was cancelled and nothing was charged. The book is here whenever you want it.</p>
      )}
      <section className="sales-hero">
        <div>
          <p className="eyebrow">The digital edition · PDF · sold only here</p>
          <h1>{n ? `${n.trees} trees. One chainsaw. A ${n.diameterFt}-foot geodesic cabin.` : 'Trees, one chainsaw, and a geodesic cabin.'}</h1>
          <p className="lead">
            <b>{book ? fullTitle(book.title, book.subtitle) : ''}</b> is the whole method, start to finish -- felling,
            splitting, the jig, the panels, raising the shell -- and then everything it grows into. Every length,
            angle, hour and dollar in it is computed by the project's own open model, not guessed.
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
          {digital && (
            <p className="small muted center">
              {digital.chapters} chapters · {digital.figures} figures{digital.pages ? ` · ${digital.pages} pages` : ''}
            </p>
          )}
          <BuyBox book={book} />
        </div>
      </section>

      <section>
        <p className="eyebrow">What you get</p>
        <h2>Three books in one</h2>
        <div className="cards">
          {build && (
            <div className="card">
              <h3>{build.title}</h3>
              <p className="muted">{build.chapters.length} chapters</p>
              <p>
                The build, day by day: the saw on Day Zero, felling, bucking, ripping, the jig, the panels, raising the
                shell. Then closing it in, doors and windows, weather, finishing,
                heat and power -- and what the author would do differently.
              </p>
            </div>
          )}
          {scale && (
            <div className="card">
              <h3>{scale.title}</h3>
              <p className="muted">{scale.chapters.length} chapters</p>
              <p>
                Why the parts list does not grow with the house: the same nine processes at any size, what an hour at
                the log is worth, where the fuel goes, why a round house needs less skin, and the pad you keep when you
                move.
              </p>
            </div>
          )}
          {variations && (
            <div className="card">
              <h3>{variations.title}</h3>
              <p className="muted">{variations.chapters.length} chapters</p>
              <p>
                Everything else the frame can become: hats you stack for warmth, the floating dome, the boat-hull
                shell, hubs or no hubs, zomes, the seam that does four jobs, and the module catalogue.
              </p>
            </div>
          )}
        </div>
        <ul className="checklist two">
          <li><b>Two lengths, not forty.</b> Every member is one of two cut lengths; one jig on a flat board builds every panel.</li>
          <li><b>Numbers you can check.</b> Each figure is produced by code that is open on GitHub. Change an input and the book changes with it.</li>
          <li><b>Honest about the costs.</b> Where a number does not help the argument, the book prints it anyway.</li>
          <li><b>Every future edition.</b> Your download link always serves the newest version of the book.</li>
          <li><b>Reads anywhere.</b> One PDF: phone, tablet, laptop or printer. No account, no app, no DRM.</li>
        </ul>
      </section>

      {digital && (
        <section>
          <p className="eyebrow">Look inside</p>
          <h2>All {chapterCount(digital.parts)} chapters</h2>
          {digital.parts.map((part) => (
            <details key={part.number} className="toc-part">
              <summary>
                Part {part.number}: {part.title} <span className="muted">· {part.chapters.length} chapters</span>
              </summary>
              <ol>
                {part.chapters.map((c) => <li key={c.number} value={c.number}>{c.title}</li>)}
              </ol>
            </details>
          ))}
        </section>
      )}

      <section className="split">
        <div className="panel">
          <h3>It is for you if…</h3>
          <ul className="checklist">
            <li>you have trees, or can get logs, and want a building from them;</li>
            <li>you are comfortable with a chainsaw, or ready to learn it properly;</li>
            <li>you want to understand <i>why</i> each step works, not just follow it;</li>
            <li>you like plans you can check yourself.</li>
          </ul>
        </div>
        <div className="panel">
          <h3>It is not for you if…</h3>
          <ul className="checklist no">
            <li>you need a stamped, code-approved plan -- this is a method, not an engineered drawing set;</li>
            <li>you want a kit delivered to your door;</li>
            <li>you want a finished house in a weekend. The frame is fast; the rest of a house is still a house.</li>
          </ul>
        </div>
      </section>

      <section className="narrow-wide">
        <h2>Questions</h2>
        <details className="faq">
          <summary>Is this the same as the paperback?</summary>
          <p>
            No. They are two books from the same project. This digital edition is the long one: the full day-by-day
            build, why it scales, and the variations. The paperback, <i>The 40 Hour Cabin</i>, is a tighter print book
            coming to Amazon -- <Link to="/paperback">see it here</Link>. The free sample is from the paperback.
          </p>
        </details>
        <details className="faq">
          <summary>How do I get the book after paying?</summary>
          <p>
            Stripe takes the payment on its own page and sends you straight back to a page with your download. That
            page's link is your receipt: bookmark it and it downloads the newest edition any time. If you buy while
            signed in, the book is also kept in your account.
          </p>
        </details>
        <details className="faq">
          <summary>What format is it?</summary>
          <p>A PDF{digital?.pages ? ` of ${digital.pages} pages` : ''}, in colour. It opens on any phone, tablet or computer and prints on ordinary paper.</p>
        </details>
        <details className="faq">
          <summary>Are the numbers real?</summary>
          <p>
            Every figure is computed from the dome's solved geometry and the project's cost model, and the code is{' '}
            <a href="https://github.com/dkzeanah/DomeSimulator" target="_blank" rel="noreferrer">open on GitHub</a>.
            Prices are declared assumptions, labelled as such, so you can put in your own.
          </p>
        </details>
        <details className="faq">
          <summary>Can I read some of it first?</summary>
          <p>
            Yes -- <Link to="/sample">the free sample</Link> is the opening chapters of the paperback, exactly as printed.
          </p>
        </details>
      </section>

      {book && (
        <section className="closing">
          <h2>Start with the trees you have.</h2>
          <p className="lead">{amount}, once. Every future edition included.</p>
          <BuyBox book={book} compact />
        </section>
      )}
    </>
  );
}
