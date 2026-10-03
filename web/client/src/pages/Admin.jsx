// The owner's page: who signed up, the links page, the media wall.

import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api.js';
import { useSession } from '../App.jsx';
import Icon from '../components/Icon.jsx';
import { price } from '../shop.js';

const ICONS = ['link', 'youtube', 'tiktok', 'instagram', 'facebook', 'x', 'kickstarter', 'book', 'email', 'website', 'patreon', 'discord', 'github', 'threads', 'pinterest'];

export default function Admin() {
  const { user, ready } = useSession();
  if (!ready) return <p className="muted">Loading…</p>;
  if (user?.role !== 'admin') {
    return (
      <section className="narrow">
        <h1>Admins only</h1>
        <p>
          Sign in with an email listed in <code>ADMIN_EMAILS</code> in the server's <code>.env</code> file.{' '}
          <Link to="/account">Sign in</Link>
        </p>
      </section>
    );
  }
  return (
    <>
      <Stats />
      <MediaAdmin />
      <LinksAdmin />
      <Subscribers />
    </>
  );
}

function Stats() {
  const [s, setS] = useState(null);
  useEffect(() => {
    api('/admin/stats').then(setS).catch(() => {});
  }, []);
  if (!s) return null;
  return (
    <section>
      <h1>Admin</h1>
      <ul className="stats">
        <li><b>{s.subscribers}</b> emails</li>
        <li><b>{s.consenting}</b> want updates</li>
        <li><b>{s.users}</b> accounts</li>
        <li><b>{s.listings}</b> network listings</li>
        <li><b>{s.downloads}</b> downloads</li>
      </ul>
      {s.downloadsByBook.length > 0 && (
        <p className="muted small">{s.downloadsByBook.map((b) => `${b.slug}: ${b.count}`).join(' · ')}</p>
      )}
      <h2>The funnel</h2>
      <table className="table">
        <thead>
          <tr><th>What people asked for</th><th>Book</th><th className="num">People</th></tr>
        </thead>
        <tbody>
          {s.signups.map((r) => (
            <tr key={`${r.kind}-${r.slug}`}>
              <td>{{ sample: 'Free sample', waitlist: 'Amazon launch list', purchase: 'Bought' }[r.kind] || r.kind}</td>
              <td>{r.slug}</td>
              <td className="num">{r.count}</td>
            </tr>
          ))}
          {s.sales.map((r) => (
            <tr key={`sale-${r.slug}-${r.currency}-${r.test}`} className={r.test ? 'dim' : ''}>
              <td>Sales{r.test ? ' (test checkout)' : ''}</td>
              <td>{r.slug}</td>
              <td className="num">{r.count} · {price(r.cents, r.currency)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="row">
        <a className="button" href="/api/admin/signups.csv?kind=waitlist">Download the Amazon launch list (CSV)</a>
      </p>
      <p className="muted small">
        The launch list is everyone who asked to hear when the paperback is on Amazon -- send them that one email. The
        general mailing list below holds only people who ticked the updates box.
      </p>
      <Orders />
    </section>
  );
}

function Orders() {
  const [orders, setOrders] = useState(null);
  useEffect(() => {
    api('/admin/orders').then((d) => setOrders(d.orders)).catch(() => setOrders([]));
  }, []);
  if (!orders?.length) return null;
  return (
    <>
      <h2>Orders</h2>
      <table className="table">
        <thead>
          <tr><th>When</th><th>Book</th><th>Email</th><th>Status</th><th className="num">Amount</th></tr>
        </thead>
        <tbody>
          {orders.map((o) => (
            <tr key={o.ref} className={o.test || o.status !== 'paid' ? 'dim' : ''}>
              <td>{new Date(o.createdAt).toLocaleString()}</td>
              <td>{o.book}</td>
              <td>{o.email}</td>
              <td>{o.status}{o.test ? ' (test)' : ''}</td>
              <td className="num">{price(o.amountCents, o.currency)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

function MediaAdmin() {
  const [items, setItems] = useState([]);
  const [url, setUrl] = useState('');
  const [title, setTitle] = useState('');
  const [featured, setFeatured] = useState(false);
  const [error, setError] = useState('');
  const load = useCallback(() => api('/media').then((d) => setItems(d.media)), []);
  useEffect(() => {
    load();
  }, [load]);

  async function add(e) {
    e.preventDefault();
    setError('');
    try {
      await api('/media', { method: 'POST', body: { url, title, featured } });
      setUrl('');
      setTitle('');
      setFeatured(false);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section>
      <h2>Media wall</h2>
      <p className="muted">
        Paste the address of one YouTube video or short, one TikTok, or one Instagram post or reel -- copied from the
        platform's Share button. Featured items go first.
      </p>
      <form className="panel form" onSubmit={add}>
        <label>Link<input required value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://www.tiktok.com/@shortcircuitr5/video/…" /></label>
        <label>Title <span className="muted">(optional)</span><input value={title} onChange={(e) => setTitle(e.target.value)} /></label>
        <label className="check"><input type="checkbox" checked={featured} onChange={(e) => setFeatured(e.target.checked)} /> Featured</label>
        {error && <p className="error">{error}</p>}
        <button className="button primary">Add to the wall</button>
      </form>
      <table className="table">
        <tbody>
          {items.map((m) => (
            <tr key={m.id}>
              <td><Icon name={m.platform} size={16} /> {m.title || m.url}</td>
              <td>
                <button className="link" onClick={() => api(`/media/${m.id}`, { method: 'PATCH', body: { featured: !m.featured } }).then(load)}>
                  {m.featured ? 'Unfeature' : 'Feature'}
                </button>
              </td>
              <td>
                <button className="link danger" onClick={() => window.confirm('Remove from the wall?') && api(`/media/${m.id}`, { method: 'DELETE' }).then(load)}>
                  Remove
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function LinksAdmin() {
  const [links, setLinks] = useState([]);
  const [form, setForm] = useState({ label: '', url: '', icon: 'link' });
  const [error, setError] = useState('');
  const load = useCallback(() => api('/links', { query: { all: '1' } }).then((d) => setLinks(d.links)), []);
  useEffect(() => {
    load();
  }, [load]);

  const patch = (id, body) => api(`/links/${id}`, { method: 'PATCH', body }).then(load).catch((e) => setError(e.message));

  async function move(index, delta) {
    const a = links[index];
    const b = links[index + delta];
    if (!a || !b) return;
    await patch(a.id, { sort: b.sort });
    await patch(b.id, { sort: a.sort === b.sort ? a.sort + delta : a.sort });
  }

  async function add(e) {
    e.preventDefault();
    setError('');
    try {
      await api('/links', { method: 'POST', body: form });
      setForm({ label: '', url: '', icon: 'link' });
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section>
      <h2>Links page</h2>
      <p className="muted">
        What appears on <Link to="/links">/links</Link> -- the page to put in your Instagram and TikTok bio.
      </p>
      <table className="table">
        <tbody>
          {links.map((l, i) => (
            <tr key={l.id} className={l.visible ? '' : 'dim'}>
              <td><Icon name={l.icon} size={16} /> {l.label}</td>
              <td className="small muted">{l.url}</td>
              <td className="nowrap">
                <button className="link" onClick={() => move(i, -1)} aria-label="Move up">↑</button>
                <button className="link" onClick={() => move(i, 1)} aria-label="Move down">↓</button>
                <button className="link" onClick={() => patch(l.id, { visible: !l.visible })}>{l.visible ? 'Hide' : 'Show'}</button>
                <button className="link danger" onClick={() => window.confirm(`Delete "${l.label}"?`) && api(`/links/${l.id}`, { method: 'DELETE' }).then(load)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <form className="panel form" onSubmit={add}>
        <div className="grid3">
          <label>Button text<input required maxLength={80} value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })} /></label>
          <label>Address<input required value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} placeholder="https://" /></label>
          <label>
            Icon
            <select value={form.icon} onChange={(e) => setForm({ ...form, icon: e.target.value })}>
              {ICONS.map((i) => <option key={i} value={i}>{i}</option>)}
            </select>
          </label>
        </div>
        {error && <p className="error">{error}</p>}
        <button className="button primary">Add link</button>
      </form>
    </section>
  );
}

function Subscribers() {
  const [rows, setRows] = useState([]);
  useEffect(() => {
    api('/admin/subscribers').then((d) => setRows(d.subscribers)).catch(() => {});
  }, []);
  return (
    <section>
      <h2>Emails</h2>
      <p className="muted">
        <a className="button" href="/api/admin/subscribers.csv">Download the mailing list (CSV)</a>{' '}
        Only people who ticked "send me updates" and have not unsubscribed are in the file.
      </p>
      <table className="table">
        <thead><tr><th>Email</th><th>Name</th><th>From</th><th>Updates?</th><th>When</th></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id}>
              <td>{r.email}</td>
              <td>{r.name}</td>
              <td>{r.source}</td>
              <td>{r.unsubscribedAt ? 'left' : r.marketingConsent ? 'yes' : 'no'}</td>
              <td className="nowrap">{new Date(r.createdAt).toLocaleDateString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
