// The local stand-in for Stripe's checkout page. The server only offers it
// when it has no Stripe key and is not in production; it pays test orders
// only, and no card is asked for.

import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { api } from '../api.js';
import { fullTitle, price } from '../shop.js';

export default function TestCheckout() {
  const { ref } = useParams();
  const [params] = useSearchParams();
  const key = params.get('key') || '';
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api(`/orders/${encodeURIComponent(ref)}`, { query: { key } })
      .then((d) => setOrder(d.order))
      .catch((e) => setError(e.message));
  }, [ref, key]);

  async function pay() {
    setBusy(true);
    try {
      await api(`/orders/${encodeURIComponent(ref)}/test-pay`, { method: 'POST', body: { key } });
      navigate(`/thanks/${ref}?key=${encodeURIComponent(key)}`);
    } catch (e) {
      setError(e.message);
      setBusy(false);
    }
  }

  return (
    <section className="narrow">
      <p className="eyebrow">Test checkout</p>
      <h1>This is not a real payment</h1>
      <p className="callout">
        The server has no Stripe key yet, so this page stands in for Stripe's. No card is asked for and no money moves.
        With <code>STRIPE_SECRET_KEY</code> set, buyers go to Stripe instead and this page stops working.
      </p>
      {error && <p className="error">{error}</p>}
      {order && (
        <div className="panel form">
          <p>
            <b>{fullTitle(order.book.title, order.book.subtitle)}</b>
            <br />
            {price(order.amountCents, order.currency)} · {order.email}
          </p>
          {order.status === 'paid' ? (
            <Link className="button primary" to={`/thanks/${ref}?key=${encodeURIComponent(key)}`}>Already paid: go to the download</Link>
          ) : (
            <button className="button primary" onClick={pay} disabled={busy}>
              {busy ? 'Paying…' : `Pay ${price(order.amountCents, order.currency)} (test)`}
            </button>
          )}
        </div>
      )}
    </section>
  );
}
