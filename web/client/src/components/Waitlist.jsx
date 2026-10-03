// "Tell me when it is on Amazon."

import { useState } from 'react';
import { api } from '../api.js';

export default function Waitlist({ book }) {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [consent, setConsent] = useState(false);
  const [trap, setTrap] = useState('');
  const [state, setState] = useState({ busy: false, error: '', done: false });

  if (!book) return null;
  if (book.amazonUrl) {
    return (
      <a className="button primary big" href={book.amazonUrl} target="_blank" rel="noreferrer">
        Buy the paperback on Amazon
      </a>
    );
  }
  if (state.done) {
    return (
      <div className="gate done">
        <p className="ok"><b>You are on the list.</b> One email, the day the paperback is on Amazon.</p>
      </div>
    );
  }

  async function submit(event) {
    event.preventDefault();
    setState({ busy: true, error: '', done: false });
    try {
      await api('/waitlist', {
        method: 'POST',
        body: { book: book.slug, email, name: name || undefined, marketingConsent: consent, website: trap || undefined },
      });
      setState({ busy: false, error: '', done: true });
    } catch (error) {
      setState({ busy: false, error: error.message, done: false });
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
      <input className="trap" tabIndex={-1} autoComplete="off" aria-hidden="true" value={trap} onChange={(e) => setTrap(e.target.value)} />
      <label className="check">
        <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
        Also send me the occasional build update. Unsubscribe any time.
      </label>
      <button className="button primary" disabled={state.busy}>
        {state.busy ? 'One moment…' : 'Tell me when it is on Amazon'}
      </button>
      {state.error && <p className="error">{state.error}</p>}
      <p className="muted small">Your email is used for the launch email and, only if you tick the box, updates. Never sold or shared.</p>
    </form>
  );
}
