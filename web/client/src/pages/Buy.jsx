// The sales page for the complete edition, sold here: the 40-hour frame plus
// every way to style the dome, priced. (The Amazon paperback is a different
// book -- see Paperback.jsx.)

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
  const parts = digital?.parts || [];
  const styleAt = parts.findIndex((p) => p.title === 'Style It');
  const frameParts = styleAt > 0 ? parts.slice(0, styleAt) : [];
  const style = styleAt >= 0 ? parts[styleAt] : null;
  const tools = parts.find((p) => p.title === 'The Tools');
  const frameChapters = frameParts.reduce((sum, p) => sum + p.chapters.length, 0);

  return (
    <>
      {params.get('cancelled') && (
        <p className="callout">Checkout was cancelled and nothing was charged. The book is here whenever you want it.</p>
      )}
      <section className="sales-hero">
        <div>
          <p className="eyebrow">The complete edition · PDF · sold only here</p>
          <h1>The 40-hour frame, and every way to finish it -- priced.</h1>
          <p className="lead">
            <b>{book ? fullTitle(book.title, book.subtitle) : ''}</b> takes a geodesic cabin from standing trees to a
            dry, raised shell -- split-log members, one jig, every length and angle -- and then dresses that same frame
            every way the project's Dome Creator can: finishes rendered and priced, every material and panel swept,
            every item on the floor on one price list. Every figure is computed by the project's own open software.
          </p>
          {n && (
            <ul className="stats">
              <li><b>{n.frameHours} h</b> of frame work</li>
              <li><b>{n.members}</b> members, <b>{n.panels}</b> panels</li>
              <li><b>{n.styles}</b> finishes rendered, <b>${n.styleLowUsd}</b> to <b>${n.styleHighUsd}</b></li>
              <li><b>{n.combos}</b> frame-and-panel combinations priced</li>
              <li><b>{n.items}</b> fit-out items on one price list</li>
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
        <h2>The frame, the finish, and the tools behind them</h2>
        <div className="cards">
          {frameParts.length > 0 && (
            <div className="card">
              <h3>The 40-hour frame</h3>
              <p className="muted">{frameParts.length} Parts · {frameChapters} chapters</p>
              <p>
                What has to be right, the geometry from one number, the tree and the split, the panel and its jig,
                the skin, the seam, the floor and the ground, what it costs and what it is worth -- and the
                variations, from hubs to a dome hung in the trees.
              </p>
            </div>
          )}
          {style && (
            <div className="card">
              <h3>{style.title}</h3>
              <p className="muted">{style.chapters.length} chapters</p>
              <p>
                The same frame in the Dome Creator: dressed in twelve finishes and rendered, every frame material,
                panel, cladding and foundation swept, every skin on every frame priced, and every item you could put
                on the floor on one list.
              </p>
            </div>
          )}
          {tools && (
            <div className="card">
              <h3>{tools.title}</h3>
              <p className="muted">{tools.chapters.length} chapters</p>
              <p>
                The software that wrote the book and how to drive it: the solver, the 3-D worlds, the cutting
                calculator that numbers every piece and sets up every saw cut, and every part priced.
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
            No. They are two books from the same project. This complete edition is the frame and every way to finish
            it, priced, and it is sold only here. The paperback on Amazon is the trees-and-chainsaw build, day by day
            -- <Link to="/paperback">see it here</Link>. The free sample is cut from this complete edition.
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
            Yes -- <Link to="/sample">the free sample</Link> is the opening chapters of this complete edition, exactly as built.
          </p>
        </details>
      </section>

      {book && (
        <section className="closing">
          <h2>Frame it in forty hours. Finish it your way.</h2>
          <p className="lead">{amount}, once. Every future edition included.</p>
          <BuyBox book={book} compact />
        </section>
      )}
    </>
  );
}
