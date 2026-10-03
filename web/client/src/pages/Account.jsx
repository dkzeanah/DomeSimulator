import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '../api.js';
import { useSession } from '../App.jsx';
import { fullTitle, price } from '../shop.js';

export default function Account() {
  const { user, ready } = useSession();
  if (!ready) return <p className="muted">Loading…</p>;
  return user ? <Profile /> : <SignIn />;
}

function SignIn() {
  const { setUser } = useSession();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [mode, setMode] = useState(params.get('mode') === 'signup' ? 'signup' : 'login');
  const [email, setEmail] = useState(params.get('email') || '');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      const { user } =
        mode === 'signup'
          ? await api('/auth/signup', { method: 'POST', body: { email, password, displayName, marketingConsent: consent } })
          : await api('/auth/login', { method: 'POST', body: { email, password } });
      setUser(user);
      navigate(mode === 'signup' ? '/network' : '/');
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="narrow">
      <div className="tabs">
        <button className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>Sign in</button>
        <button className={mode === 'signup' ? 'active' : ''} onClick={() => setMode('signup')}>Make an account</button>
      </div>
      <form className="panel form" onSubmit={submit}>
        {mode === 'signup' && (
          <p className="muted">
            An account keeps the free sample one click away, holds any book you buy while signed in, and puts you on the dome network. It is free.
          </p>
        )}
        <label>
          Email
          <input type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        {mode === 'signup' && (
          <label>
            Your name, as others will see it
            <input required maxLength={80} autoComplete="name" value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
          </label>
        )}
        <label>
          Password {mode === 'signup' && <span className="muted">at least 10 characters -- a short sentence works well</span>}
          <input
            type="password"
            required
            minLength={mode === 'signup' ? 10 : 1}
            autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        {mode === 'signup' && (
          <label className="check">
            <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
            Send me the occasional build update and the Kickstarter launch.
          </label>
        )}
        {error && <p className="error">{error}</p>}
        <button className="button primary" disabled={busy}>
          {busy ? 'One moment…' : mode === 'signup' ? 'Make my account' : 'Sign in'}
        </button>
      </form>
    </section>
  );
}

function Profile() {
  const { user, setUser } = useSession();
  const navigate = useNavigate();
  const [form, setForm] = useState({ displayName: user.displayName, bio: user.bio, city: user.city, region: user.region, country: user.country, website: user.website });
  const [pw, setPw] = useState({ currentPassword: '', newPassword: '' });
  const [note, setNote] = useState('');
  const [error, setError] = useState('');
  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  async function save(e) {
    e.preventDefault();
    setNote('');
    setError('');
    try {
      const { user } = await api('/auth/me', { method: 'PATCH', body: form });
      setUser(user);
      setNote('Saved.');
    } catch (err) {
      setError(err.message);
    }
  }

  async function changePassword(e) {
    e.preventDefault();
    setNote('');
    setError('');
    try {
      await api('/auth/me', { method: 'PATCH', body: pw });
      setPw({ currentPassword: '', newPassword: '' });
      setNote('Password changed. Other devices have been signed out.');
    } catch (err) {
      setError(err.message);
    }
  }

  async function signOut() {
    await api('/auth/logout', { method: 'POST', body: {} });
    setUser(null);
    navigate('/');
  }

  async function deleteAccount() {
    const password = window.prompt('This deletes your account and your network listings for good. Type your password to confirm.');
    if (!password) return;
    try {
      await api('/auth/me', { method: 'DELETE', body: { password } });
      setUser(null);
      navigate('/');
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="narrow">
      <h1>Your account</h1>
      <p className="muted">
        Signed in as {user.email}. <Link to="/network">Your network listings</Link> · <Link to="/book">Books</Link>
      </p>
      {note && <p className="ok">{note}</p>}
      {error && <p className="error">{error}</p>}
      <Library />
      <form className="panel form" onSubmit={save}>
        <h2>Profile</h2>
        <label>Name others see<input required maxLength={80} value={form.displayName} onChange={set('displayName')} /></label>
        <label>About you<textarea rows={3} maxLength={2000} value={form.bio} onChange={set('bio')} /></label>
        <div className="grid3">
          <label>Town or city<input value={form.city} onChange={set('city')} /></label>
          <label>State / region<input value={form.region} onChange={set('region')} /></label>
          <label>Country<input value={form.country} onChange={set('country')} /></label>
        </div>
        <label>Website<input value={form.website} onChange={set('website')} placeholder="https://" /></label>
        <button className="button primary">Save profile</button>
      </form>
      <form className="panel form" onSubmit={changePassword}>
        <h2>Password</h2>
        <label>Current password<input type="password" autoComplete="current-password" required value={pw.currentPassword} onChange={(e) => setPw({ ...pw, currentPassword: e.target.value })} /></label>
        <label>New password<input type="password" autoComplete="new-password" required minLength={10} value={pw.newPassword} onChange={(e) => setPw({ ...pw, newPassword: e.target.value })} /></label>
        <button className="button">Change password</button>
      </form>
      <div className="row">
        <button className="button ghost" onClick={signOut}>Sign out</button>
        <button className="link danger" onClick={deleteAccount}>Delete my account</button>
      </div>
    </section>
  );
}

/** Books bought while signed in. A purchase made signed out lives on its receipt link. */
function Library() {
  const [orders, setOrders] = useState(null);
  useEffect(() => {
    api('/orders/mine').then((d) => setOrders(d.orders)).catch(() => setOrders([]));
  }, []);
  if (!orders) return null;
  return (
    <div className="panel form">
      <h2>Your books</h2>
      {orders.length === 0 ? (
        <p className="muted">
          Nothing bought on this account yet. <Link to="/buy">The digital edition</Link> ·{' '}
          <Link to="/sample">the free sample</Link>
        </p>
      ) : (
        orders.map((o) => (
          <div key={o.ref} className="row library-row">
            <span>
              <b>{fullTitle(o.book.title, o.book.subtitle)}</b>
              <span className="muted small"> · {price(o.amountCents, o.currency)} · {new Date(o.paidAt).toLocaleDateString()}</span>
            </span>
            <a className="button primary" href={o.downloadUrl}>Download</a>
          </div>
        ))
      )}
    </div>
  );
}
