import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { NavLink, Route, Routes, useLocation } from 'react-router-dom';
import { api } from './api.js';
import Account from './pages/Account.jsx';
import Admin from './pages/Admin.jsx';
import Books from './pages/Books.jsx';
import Dome from './pages/Dome.jsx';
import Home from './pages/Home.jsx';
import Links from './pages/Links.jsx';
import Network from './pages/Network.jsx';
import Watch from './pages/Watch.jsx';

const Session = createContext({ user: null, site: null, refresh: () => {} });
export const useSession = () => useContext(Session);

export default function App() {
  const [user, setUser] = useState(null);
  const [site, setSite] = useState(null);
  const [ready, setReady] = useState(false);
  const location = useLocation();

  const refresh = useCallback(async () => {
    const { user } = await api('/auth/me').catch(() => ({ user: null }));
    setUser(user);
    setReady(true);
  }, []);

  useEffect(() => {
    refresh();
    api('/site').then(setSite).catch(() => setSite({ name: 'Dome Network' }));
  }, [refresh]);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [location.pathname]);

  // The links page is meant to be opened from a social bio, so it stands alone.
  const bare = location.pathname === '/links';

  return (
    <Session.Provider value={{ user, setUser, site, refresh, ready }}>
      {!bare && <Header />}
      <main className={bare ? 'bare' : 'page'}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/book" element={<Books />} />
          <Route path="/dome" element={<Dome />} />
          <Route path="/network" element={<Network />} />
          <Route path="/watch" element={<Watch />} />
          <Route path="/links" element={<Links />} />
          <Route path="/account" element={<Account />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      {!bare && <Footer />}
    </Session.Provider>
  );
}

function Header() {
  const { user, site } = useSession();
  const [open, setOpen] = useState(false);
  const location = useLocation();
  useEffect(() => {
    setOpen(false);
  }, [location.pathname]);
  return (
    <header className="topbar">
      <NavLink to="/" className="brand">
        <img src="/mark.svg" alt="" width="32" height="32" />
        <span>{site?.name || 'Dome Network'}</span>
      </NavLink>
      <button className="menu-toggle" aria-expanded={open} aria-label="Menu" onClick={() => setOpen(!open)}>
        <span />
        <span />
        <span />
      </button>
      <nav className={open ? 'open' : ''}>
        <NavLink to="/book">Free book</NavLink>
        <NavLink to="/dome">The dome</NavLink>
        <NavLink to="/network">Network</NavLink>
        <NavLink to="/watch">Watch</NavLink>
        <NavLink to="/links">Links</NavLink>
        {user?.role === 'admin' && <NavLink to="/admin">Admin</NavLink>}
        <NavLink to="/account" className="nav-account">
          {user ? user.displayName : 'Sign in'}
        </NavLink>
      </nav>
    </header>
  );
}

function Footer() {
  const { site } = useSession();
  return (
    <footer className="footer">
      <p>
        {site?.name || 'Dome Network'} · Every figure on this site is computed by the project's own model, not typed in.
      </p>
      <p>
        <a href="https://github.com/dkzeanah/DomeSimulator" target="_blank" rel="noreferrer">
          The code is open
        </a>{' '}
        · <NavLink to="/links">All links</NavLink>
      </p>
    </footer>
  );
}

function NotFound() {
  return (
    <section className="narrow">
      <h1>Nothing here</h1>
      <p>
        That page does not exist. Try the <NavLink to="/">front page</NavLink>.
      </p>
    </section>
  );
}
