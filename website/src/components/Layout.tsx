import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { trackView } from "../lib/track";
import { isStaff, useSession } from "../lib/session";
import { Toast } from "./ui";

const NAV = [
  ["/portal", "Portal"],
  ["/start", "Free Pages"],
  ["/book", "The Book"],
  ["/build", "The Build"],
  ["/calculator", "Calculator"],
  ["/network", "Pads"],
  ["/back", "Back It"],
  ["/kit", "Kit"],
  ["/episodes", "Episodes"],
  ["/media", "Media"],
] as const;

// The staging site runs the very build that "Promote to live" publishes, so it can only tell
// itself apart by its address: anything but the live domains (and this computer) says so.
const LIVE_HOSTS = ["www.zeanahlab.com", "zeanahlab.com", "localhost", "127.0.0.1"];
const STAGING = typeof window !== "undefined" && !LIVE_HOSTS.includes(window.location.hostname);

export default function Layout() {
  const { me, setMe, notify } = useSession();
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  const go = useNavigate();
  const signOut = async () => {
    setOpen(false);
    await api("/logout", { body: {} }).catch(() => undefined);
    setMe(null);
    notify("Signed out", "This device is signed out.");
    go("/");
  };
  // one page view per page shown, to the site's own counter
  useEffect(() => { trackView(loc.pathname); }, [loc.pathname]);
  return (
    <div className="min-h-screen flex flex-col">
      {STAGING && (
        <div role="status" className="text-center text-xs font-semibold py-1.5" style={{ background: "#b45309", color: "#fff" }}>
          STAGING -- a copy for checking changes. Orders here are test orders and no email is sent.
        </div>
      )}
      <header className="sticky top-0 z-40 border-b" style={{ borderColor: "var(--line)", background: "color-mix(in srgb, var(--bg) 88%, transparent)", backdropFilter: "blur(8px)" }}>
        <div className="mx-auto max-w-6xl px-4 h-14 flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-2 font-semibold" onClick={() => setOpen(false)}>
            <img src="/mark.svg" alt="" className="w-7 h-7" />
            <span className="display text-xl">Zeanah Lab</span>
          </Link>
          <nav className="hidden md:flex items-center gap-5 text-sm">
            {NAV.map(([to, label]) => (
              <NavLink key={to} to={to} className={({ isActive }) => (isActive ? "accent" : "muted hover:text-[var(--ink)]")}>{label}</NavLink>
            ))}
            {me && isStaff(me) && <NavLink to="/admin/studio" className={({ isActive }) => (isActive ? "accent" : "muted hover:text-[var(--ink)]")}>Studio</NavLink>}
            <NavLink to="/account" className="btn-ghost !py-1.5">{me ? me.displayName : "Sign in"}</NavLink>
            {me && <button type="button" className="muted hover:text-[var(--ink)] text-sm" onClick={signOut}>Sign out</button>}
          </nav>
          <button className="md:hidden btn-ghost !py-1.5" aria-expanded={open} onClick={() => setOpen(!open)}>Menu</button>
        </div>
        {open && (
          <nav className="md:hidden border-t px-4 py-3 grid gap-3" style={{ borderColor: "var(--line)" }}>
            {[...NAV, ...(me && isStaff(me) ? [["/admin/studio", "Studio"] as const] : []), ["/account", me ? me.displayName : "Sign in"] as const].map(([to, label]) => (
              <NavLink key={to} to={to} onClick={() => setOpen(false)}>{label}</NavLink>
            ))}
            {me && <button type="button" className="text-left" onClick={signOut}>Sign out</button>}
          </nav>
        )}
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
      {!loc.pathname.startsWith("/portal") && <footer className="border-t mt-16" style={{ borderColor: "var(--line)" }}>
        <div className="mx-auto max-w-6xl px-4 py-8 text-sm muted grid gap-2 sm:flex sm:justify-between">
          <p>Every number on this site is computed by the project's own open code, or counted from real records.</p>
          <p className="flex flex-wrap gap-x-4 gap-y-1">
            <Link to="/card">Contact</Link>
            <Link to="/kids">Kids' book</Link>
            <Link to="/domes">Dome classes</Link>
            <Link to="/recyclers">Recyclers</Link>
            <Link to="/privacy">Privacy</Link>
            <Link to="/kit">Press &amp; letters</Link>
            <a href="https://github.com/dkzeanah/DomeSimulator">The code</a>
          </p>
        </div>
      </footer>}
      <Toast />
    </div>
  );
}
