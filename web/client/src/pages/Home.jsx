import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, money } from '../api.js';
import BookGate from '../components/BookGate.jsx';
import MediaCard from '../components/MediaCard.jsx';

export default function Home() {
  const [facts, setFacts] = useState(null);
  const [book, setBook] = useState(null);
  const [media, setMedia] = useState([]);

  useEffect(() => {
    api('/facts').then((d) => setFacts(d.facts)).catch(() => {});
    api('/books').then((d) => setBook(d.books.find((b) => b.featured) || d.books[0] || null)).catch(() => {});
    api('/media').then((d) => setMedia(d.media.slice(0, 3))).catch(() => {});
  }, []);

  const dome = facts?.dome;
  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">The stem-cell dome</p>
          <h1>One frame, split from a log. Any building you need.</h1>
          <p className="lead">
            A 2V geodesic dome built from triangular wedges, point in and flat face out. The frame never changes;
            the panels decide whether it is a guest house, a workshop or a garage.
          </p>
          {dome && (
            <ul className="stats">
              <li><b>{dome.acrossFt} ft</b> across</li>
              <li><b>{Math.round(dome.floorSqft)} sq ft</b> of floor</li>
              <li><b>{dome.bays}</b> bays</li>
              <li><b>{dome.members}</b> wedges</li>
              {facts.price && <li><b>{money(facts.price.stemCell)}</b> the stem cell</li>}
            </ul>
          )}
        </div>
        <div className="hero-card">
          {book ? (
            <>
              <p className="eyebrow">Free book</p>
              {book.cover && <img className="book-cover" src={book.cover} alt={`Cover of ${book.title}: ${book.subtitle}`} width="720" height="931" />}
              <h2>{book.title}</h2>
              {book.subtitle && <p className="subtitle">{book.subtitle}</p>}
              <p className="muted">{book.blurb}</p>
              <BookGate book={book} />
            </>
          ) : (
            <p className="muted">Loading the book…</p>
          )}
        </div>
      </section>

      <section className="tiles">
        <Link to="/dome" className="tile">
          <h3>How the dome works</h3>
          <p>The price, what we keep, every fit-out and every reward tier -- straight from the model.</p>
        </Link>
        <Link to="/network" className="tile">
          <h3>Find the dome network</h3>
          <p>Pad hosts, dome owners, quilters, builders and people with trees, near you.</p>
        </Link>
        <Link to="/watch" className="tile">
          <h3>Watch the films</h3>
          <p>YouTube, TikTok and Instagram in one place.</p>
        </Link>
      </section>

      {media.length > 0 && (
        <section>
          <h2>Latest</h2>
          <div className="media-grid">
            {media.map((item) => <MediaCard key={item.id} item={item} />)}
          </div>
        </section>
      )}
    </>
  );
}
