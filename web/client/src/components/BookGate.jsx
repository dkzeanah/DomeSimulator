// The email form in front of a book. On success it shows the download button
// and offers to turn the email into an account.

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api.js';
import { useSession } from '../App.jsx';

export default function BookGate({ book, after = null, cta = 'Get the free PDF' }) {
  const { user } = useSession();
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [consent, setConsent] = useState(true);
  const [trap, setTrap] = useState('');
  const [state, setState] = useState({ busy: false, error: '', url: '' });

  if (!book.available) {
    return <p className="muted">This book is being printed. Check back soon.</p>;
  }

  if (user) {
    return (
      <div className="gate done">
        <a className="button primary" href={`/api/books/${book.slug}/download`}>
          Download the PDF{book.sizeMb ? ` (${book.sizeMb} MB)` : ''}
        </a>
        <p className="muted">You are signed in, so there is nothing to fill in.</p>
        {after}
      </div>
    );
  }

  if (state.url) {
    return (
      <div className="gate done">
        <a className="button primary" href={state.url}>
          Download the PDF{book.sizeMb ? ` (${book.sizeMb} MB)` : ''}
        </a>
        <p className="muted">
          The link works for a day. Want to keep every edition and join the dome network?{' '}
          <Link to={`/account?email=${encodeURIComponent(email)}&mode=signup`}>Make an account</Link> with the same email.
        </p>
        {after}
      </div>
    );
  }

  async function submit(event) {
    event.preventDefault();
    setState({ busy: true, error: '', url: '' });
    try {
      const { downloadUrl } = await api('/leads', {
        method: 'POST',
        body: { email, name: name || undefined, book: book.slug, marketingConsent: consent, website: trap || undefined },
      });
      setState({ busy: false, error: '', url: downloadUrl });
    } catch (error) {
      setState({ busy: false, error: error.message, url: '' });
    }
  }

  return (
    <form className="gate" onSubmit={submit}>
      <label>
        Your email
        <input type="email" required autoComplete="email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} />
      </label>
      <label>
        First name <span className="muted">(optional)</span>
        <input autoComplete="given-name" value={name} onChange={(e) => setName(e.target.value)} />
      </label>
      {/* Hidden from people; bots fill it in and are refused. */}
      <input className="trap" tabIndex={-1} autoComplete="off" aria-hidden="true" value={trap} onChange={(e) => setTrap(e.target.value)} />
      <label className="check">
        <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
        Send me the occasional build update, and the paperback and Kickstarter launches. Unsubscribe any time.
      </label>
      <button className="button primary" disabled={state.busy}>
        {state.busy ? 'One moment…' : cta}
      </button>
      {state.error && <p className="error">{state.error}</p>}
      <p className="muted small">
        We store your email to send you the book and, only if you tick the box, updates. Nothing is sold or shared.
      </p>
    </form>
  );
}
