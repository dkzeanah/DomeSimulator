// Back from checkout: the order, and the download once it is paid.
//
// This page's own address is the buyer's receipt and their way back to the
// book, so it says so plainly and offers to copy it.

import { useEffect, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { api } from '../api.js';
import { fullTitle, price } from '../shop.js';

export default function Thanks() {
  const { ref } = useParams();
  const [params] = useSearchParams();
  const key = params.get('key') || '';
  const [order, setOrder] = useState(null);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let tries = 0;
    let timer;
    let alive = true;
    async function load() {
      try {
        const { order } = await api(`/orders/${encodeURIComponent(ref)}`, { query: { key } });
        if (!alive) return;
        setOrder(order);
        // Stripe's confirmation can trail the buyer by a few seconds.
        if (order.status === 'pending' && tries++ < 30) timer = setTimeout(load, 2000);
      } catch (err) {
        if (alive) setError(err.message);
      }
    }
    load();
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, [ref, key]);

  async function copy() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }

  if (error) {
    return (
      <section className="narrow">
        <h1>We could not find that order</h1>
        <p className="error">{error}</p>
        <p>If you paid and this link is not working, get in touch through the <Link to="/links">links page</Link> with the email you used.</p>
      </section>
    );
  }
  if (!order) return <p className="muted">Loading your order…</p>;

  const paid = order.status === 'paid';
  return (
    <section className="narrow thanks">
      {order.book.cover && <img className="book-cover small-cover" src={order.book.cover} alt="" width="720" height="931" />}
      <p className="eyebrow">{paid ? 'Paid' : 'Confirming payment'}{order.test ? ' · test order' : ''}</p>
      <h1>{paid ? 'Thank you. The book is yours.' : 'Almost there…'}</h1>
      <p className="lead">
        <b>{fullTitle(order.book.title, order.book.subtitle)}</b>
        {' · '}
        {price(order.amountCents, order.currency)}
      </p>
      {paid ? (
        <>
          <a className="button primary big" href={order.downloadUrl}>Download the PDF</a>
          <div className="panel receipt">
            <h3>Keep this page</h3>
            <p className="muted">
              Its address is your receipt and your download link. Bookmark it, and it will always give you the newest
              edition of the book{order.email ? ` (bought with ${order.email})` : ''}.
            </p>
            {key && (
              <button type="button" className="button" onClick={copy}>
                {copied ? 'Copied' : 'Copy this page\'s link'}
              </button>
            )}
          </div>
          <p className="muted small">
            Want it in an account too? <Link to="/account?mode=signup">Make one</Link>, and buy while signed in next
            time. The <Link to="/paperback">paperback</Link> is coming to Amazon.
          </p>
        </>
      ) : (
        <p className="muted">
          Waiting for the payment to be confirmed. This usually takes a few seconds; the page will update by itself.
          {order.test ? ' (A test order is paid from the test checkout page.)' : ''}
        </p>
      )}
    </section>
  );
}
