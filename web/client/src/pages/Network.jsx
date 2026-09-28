// The dome network: search it, and list yourself on it.

import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api.js';
import { useSession } from '../App.jsx';
import Icon from '../components/Icon.jsx';

const RADII = [25, 50, 100, 250, 500, 1000];

function useKinds() {
  const [kinds, setKinds] = useState([]);
  useEffect(() => {
    api('/network/kinds').then((d) => setKinds(d.kinds)).catch(() => {});
  }, []);
  return kinds;
}

function locate() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) return reject(new Error('This browser cannot share a location.'));
    navigator.geolocation.getCurrentPosition(
      (p) => resolve({ lat: Number(p.coords.latitude.toFixed(5)), lng: Number(p.coords.longitude.toFixed(5)) }),
      () => reject(new Error('Location was not shared. You can still search by town or keyword.')),
      { timeout: 10000 },
    );
  });
}

export default function Network() {
  const { user } = useSession();
  const kinds = useKinds();
  const kindLabel = Object.fromEntries(kinds.map((k) => [k.key, k.label]));
  const [q, setQ] = useState('');
  const [kind, setKind] = useState('');
  const [near, setNear] = useState(null);
  const [radiusKm, setRadiusKm] = useState(250);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');

  const search = useCallback(async () => {
    setError('');
    try {
      const d = await api('/network', { query: { q, kind, radiusKm: near ? radiusKm : '', lat: near?.lat, lng: near?.lng } });
      setResults(d);
    } catch (e) {
      setError(e.message);
    }
  }, [q, kind, near, radiusKm]);

  useEffect(() => {
    search();
    // Search again whenever a filter other than the text box changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kind, near, radiusKm]);

  async function useMyLocation() {
    try {
      setNear(await locate());
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <>
      <section>
        <h1>The dome network</h1>
        <p className="lead">
          A dome needs somewhere to stand, somebody to quilt for it, and somebody to build it. Find them here -- or list
          yourself so they can find you.
        </p>
        <div className="kind-chips">
          <button className={!kind ? 'chip active' : 'chip'} onClick={() => setKind('')}>Everyone</button>
          {kinds.map((k) => (
            <button key={k.key} className={kind === k.key ? 'chip active' : 'chip'} onClick={() => setKind(k.key)} title={k.blurb}>
              {k.label}
            </button>
          ))}
        </div>
        <form
          className="search"
          onSubmit={(e) => {
            e.preventDefault();
            search();
          }}
        >
          <input placeholder="Search by town, state, keyword…" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search" />
          <button className="button">Search</button>
        </form>
        <div className="near">
          {near ? (
            <>
              <span><Icon name="pin" size={16} /> Near you, within</span>
              <select value={radiusKm} onChange={(e) => setRadiusKm(Number(e.target.value))} aria-label="Distance">
                {RADII.map((r) => <option key={r} value={r}>{r} km ({Math.round(r * 0.621)} mi)</option>)}
              </select>
              <button className="link" onClick={() => setNear(null)}>anywhere instead</button>
            </>
          ) : (
            <button className="link" onClick={useMyLocation}><Icon name="pin" size={16} /> Show what is near me</button>
          )}
        </div>
        {error && <p className="error">{error}</p>}
      </section>

      <section>
        {results === null ? (
          <p className="muted">Loading…</p>
        ) : results.results.length === 0 ? (
          <p className="muted">Nobody matches yet. {user ? 'Be the first -- add a listing below.' : <><Link to="/account">Sign in</Link> and be the first.</>}</p>
        ) : (
          <>
            <p className="muted small">{results.total} found</p>
            <div className="cards">
              {results.results.map((l) => <ListingCard key={l.id} listing={l} kindLabel={kindLabel} />)}
            </div>
          </>
        )}
        {results && !user && results.results.some((l) => l.contactHidden) && (
          <p className="muted small"><Link to="/account">Sign in</Link> to see how to contact people.</p>
        )}
      </section>

      {user ? <MyListings kinds={kinds} kindLabel={kindLabel} onChange={search} /> : (
        <section className="callout">
          <h2>List yourself</h2>
          <p><Link to="/account?mode=signup">Make a free account</Link> to add a pad, a dome, a quilting service, a build crew or a stand of trees.</p>
        </section>
      )}
    </>
  );
}

function ListingCard({ listing, kindLabel, children }) {
  const place = [listing.city, listing.region, listing.country].filter(Boolean).join(', ');
  return (
    <article className={`card listing ${listing.kind}`}>
      <p className="eyebrow">{kindLabel[listing.kind] || listing.kind}{listing.visible ? '' : ' · hidden'}</p>
      <h3>{listing.title}</h3>
      {place && <p className="muted small"><Icon name="pin" size={14} /> {place}{listing.distanceKm !== undefined ? ` · ${listing.distanceKm} km away` : ''}</p>}
      {listing.body && <p>{listing.body}</p>}
      {listing.contact && <p className="small"><b>Contact:</b> {listing.contact}</p>}
      <p className="muted small">by {listing.owner.displayName}</p>
      {children}
    </article>
  );
}

const EMPTY = { kind: '', title: '', body: '', city: '', region: '', country: '', postalCode: '', contact: '', lat: null, lng: null, visible: true };

function MyListings({ kinds, kindLabel, onChange }) {
  const [mine, setMine] = useState([]);
  const [form, setForm] = useState(null);
  const [error, setError] = useState('');

  const load = useCallback(() => api('/network/mine').then((d) => setMine(d.results)).catch(() => {}), []);
  useEffect(() => {
    load();
  }, [load]);

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.type === 'checkbox' ? e.target.checked : e.target.value });

  async function save(e) {
    e.preventDefault();
    setError('');
    const body = { ...form };
    delete body.id;
    try {
      if (form.id) await api(`/network/${form.id}`, { method: 'PATCH', body });
      else await api('/network', { method: 'POST', body });
      setForm(null);
      load();
      onChange();
    } catch (err) {
      setError(err.message);
    }
  }

  async function remove(listing) {
    if (!window.confirm(`Delete "${listing.title}"? This cannot be undone.`)) return;
    await api(`/network/${listing.id}`, { method: 'DELETE' }).catch((err) => setError(err.message));
    load();
    onChange();
  }

  async function pinHere() {
    try {
      const { lat, lng } = await locate();
      setForm({ ...form, lat, lng });
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section>
      <h2>Your listings</h2>
      {mine.length === 0 && !form && <p className="muted">You are not on the map yet.</p>}
      <div className="cards">
        {mine.map((l) => (
          <ListingCard key={l.id} listing={l} kindLabel={kindLabel}>
            <div className="row">
              <button className="link" onClick={() => setForm({ ...EMPTY, ...l })}>Edit</button>
              <button className="link danger" onClick={() => remove(l)}>Delete</button>
            </div>
          </ListingCard>
        ))}
      </div>
      {!form && <button className="button" onClick={() => setForm({ ...EMPTY, kind: kinds[0]?.key || '' })}>Add a listing</button>}
      {form && (
        <form className="panel form" onSubmit={save}>
          <h3>{form.id ? 'Edit listing' : 'New listing'}</h3>
          <label>
            What are you?
            <select value={form.kind} onChange={set('kind')} required>
              {kinds.map((k) => <option key={k.key} value={k.key}>{k.label} -- {k.blurb}</option>)}
            </select>
          </label>
          <label>
            Headline <span className="muted">e.g. "Serviced pad on two acres" or "Quilting layers to order"</span>
            <input value={form.title} onChange={set('title')} required minLength={3} maxLength={120} />
          </label>
          <label>
            Details <span className="muted">what you have, what you need, when</span>
            <textarea rows={4} value={form.body || ''} onChange={set('body')} maxLength={4000} />
          </label>
          <div className="grid3">
            <label>Town or city<input value={form.city || ''} onChange={set('city')} /></label>
            <label>State / region<input value={form.region || ''} onChange={set('region')} /></label>
            <label>Country<input value={form.country || ''} onChange={set('country')} /></label>
          </div>
          <label>
            Postal code <span className="muted">(only you see this)</span>
            <input value={form.postalCode || ''} onChange={set('postalCode')} />
          </label>
          <div className="pin-row">
            <button type="button" className="button ghost" onClick={pinHere}><Icon name="pin" size={16} /> Put me on the map here</button>
            <span className="muted small">
              {form.lat !== null && form.lat !== undefined
                ? 'Location set. Others see it rounded to about a kilometre, never your exact spot.'
                : 'Optional. Without it you still show up in keyword searches, just not in "near me".'}
            </span>
            {form.lat !== null && form.lat !== undefined && (
              <button type="button" className="link" onClick={() => setForm({ ...form, lat: null, lng: null })}>remove</button>
            )}
          </div>
          <label>
            How to reach you <span className="muted">shown only to signed-in members</span>
            <input value={form.contact || ''} onChange={set('contact')} placeholder="email, phone or a link" maxLength={300} />
          </label>
          <label className="check">
            <input type="checkbox" checked={form.visible} onChange={set('visible')} /> Show this listing in search
          </label>
          {error && <p className="error">{error}</p>}
          <div className="row">
            <button className="button primary">Save</button>
            <button type="button" className="button ghost" onClick={() => setForm(null)}>Cancel</button>
          </div>
        </form>
      )}
    </section>
  );
}
