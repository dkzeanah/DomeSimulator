import { Link } from 'react-router-dom';
import BookGate from '../components/BookGate.jsx';
import { price, useBooks } from '../shop.js';

const ACTION = {
  paid: (b) => (
    <Link className="button primary" to={`/${b.page || 'buy'}`}>
      Buy the digital edition · {price(b.priceCents, b.currency)}
    </Link>
  ),
  amazon: (b) =>
    b.amazonUrl ? (
      <a className="button primary" href={b.amazonUrl} target="_blank" rel="noreferrer">Buy on Amazon</a>
    ) : (
      <Link className="button" to={`/${b.page || 'paperback'}`}>Coming to Amazon: join the launch list</Link>
    ),
};

export default function Books() {
  const { books, error } = useBooks();

  return (
    <section>
      <h1>The books</h1>
      <p className="lead">
        Start with the free sample. Then the whole thing two ways: the digital edition, sold here, or the paperback,
        coming to Amazon.
      </p>
      {error && <p className="error">{error}</p>}
      {!books && !error && <p className="muted">Loading…</p>}
      <div className="books">
        {books?.map((book) => (
          <article key={book.slug} className={`book ${book.featured ? 'featured' : ''}`}>
            <div className="book-head">
              {book.cover && <img className="book-cover" src={book.cover} alt={`Cover of ${book.title}`} width="720" height="931" loading="lazy" />}
              <span className={`badge ${book.offer === 'free' ? '' : 'quiet'}`}>
                {{ free: 'Free', paid: 'Digital', amazon: 'Paperback' }[book.offer]}
              </span>
              <h2>{book.title}</h2>
              {book.subtitle && <p className="subtitle">{book.subtitle}</p>}
              <p className="muted">{book.blurb}</p>
              {book.offer === 'free' && book.available && (
                <p className="small muted">
                  Edition {book.edition} · {book.sizeMb} MB · updated {new Date(book.updatedAt).toLocaleDateString()}
                </p>
              )}
            </div>
            {book.offer === 'free' ? (
              <BookGate book={book} cta="Send me the free sample" />
            ) : (
              <div className="gate">
                {ACTION[book.offer]?.(book)}
                {book.page && <Link to={`/${book.page}`} className="small">What is in it →</Link>}
              </div>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}
