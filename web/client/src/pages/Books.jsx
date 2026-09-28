import { useEffect, useState } from 'react';
import { api } from '../api.js';
import BookGate from '../components/BookGate.jsx';

export default function Books() {
  const [books, setBooks] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => {
    api('/books').then((d) => setBooks(d.books)).catch((e) => setError(e.message));
  }, []);

  return (
    <section>
      <h1>The books</h1>
      <p className="lead">
        Free as PDFs. Enter your email and the download starts -- no account needed. If you make an account, you can
        download any edition any time.
      </p>
      {error && <p className="error">{error}</p>}
      {!books && !error && <p className="muted">Loading…</p>}
      <div className="books">
        {books?.map((book) => (
          <article key={book.slug} className={`book ${book.featured ? 'featured' : ''}`}>
            <div className="book-head">
              {book.cover && <img className="book-cover" src={book.cover} alt={`Cover of ${book.title}`} width="720" height="931" loading="lazy" />}
              {book.featured && <span className="badge">Newest</span>}
              <h2>{book.title}</h2>
              {book.subtitle && <p className="subtitle">{book.subtitle}</p>}
              <p className="muted">{book.blurb}</p>
              {book.available && (
                <p className="small muted">
                  Edition {book.edition} · {book.sizeMb} MB · updated {new Date(book.updatedAt).toLocaleDateString()}
                </p>
              )}
            </div>
            <BookGate book={book} />
          </article>
        ))}
      </div>
    </section>
  );
}
