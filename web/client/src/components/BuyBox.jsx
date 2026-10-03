// The Buy button: an email, then Stripe's own checkout page.
//
// The price shown is the catalogue's, and the server charges the catalogue's
// -- the browser never sends an amount. With no Stripe key set, a local
// server runs a test checkout and this box says so.

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api.js';
import { useSession } from '../App.jsx';
import { price } from '../shop.js';

export default function BuyBox({ book, compact = false }) {
  const { user } = useSession();
  const [mode, setMode] = useState(undefined);
  const [email, setEmail] = useState('');
  const [consent, setConsent] = useState(false);
  const [trap, setTrap] = useState('');
  const [state, setState] = useState({ busy: false, error: '' });

  useEffect(() => {
    api('/shop').then((d) => setMode(d.mode)).catch(() => setMode(null));
  }, []);
  useEffect(() => {
    if (user?.email) setEmail(user.email);
  }, [user]);

  if (!book) return null;
  const amount = price(book.priceCents, book.currency);

  if (mode === null || !book.available) {
    return (
      <div className="buybox">
        <p className="buy-price">{amount}</p>
        <p><b>On sale soon.</b> Read the free sample while the shop opens.</p>
        <Link className="button primary" to="/sample">Get the free sample</Link>
      </div>
    );
  }

  async function submit(event) {
    event.preventDefault();
    setState({ busy: true, error: '' });
    try {
      const { url } = await api('/checkout', {
        method: 'POST',
        body: { book: book.slug, email, marketingConsent: consent, website: trap || undefined },
      });
      window.location.assign(url);
    } catch (error) {
      setState({ busy: false, error: error.message });
    }
  }

  return (
    <form className="buybox" onSubmit={submit}>
      {!compact && <p className="buy-price">{amount}</p>}
      <label>
        Email for your receipt
        <input type="email" required autoComplete="email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} />
      </label>
      <input className="trap" tabIndex={-1} autoComplete="off" aria-hidden="true" value={trap} onChange={(e) => setTrap(e.target.value)} />
      <label className="check">
        <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
        Also send me build updates and the paperback's launch. Unsubscribe any time.
      </label>
      <button className="button primary big" disabled={state.busy || mode === undefined}>
        {state.busy ? 'Opening checkout…' : `Buy the digital edition · ${amount}`}
      </button>
      {state.error && <p className="error">{state.error}</p>}
      <p className="muted small">
        {mode === 'test'
          ? 'Test checkout: this server has no Stripe key yet, so no card is asked for and no money moves.'
          : 'Card details go to Stripe on its own secure page, never to this site. You come straight back to your download.'}
      </p>
    </form>
  );
}
