import { useState } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";
import { useSession } from "../lib/session";
import { Toast } from "./ui";

const NAV = [
  ["/start", "Free Pages"],
  ["/book", "The Book"],
  ["/build", "The Build"],
  ["/network", "Pads"],
  ["/back", "Back It"],
  ["/kit", "Kit"],
] as const;

export default function Layout() {
  const { me } = useSession();
  const [open, setOpen] = useState(false);
  return (
    <div className="min-h-screen flex flex-col">
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
            <NavLink to="/account" className="btn-ghost !py-1.5">{me ? me.displayName : "Sign in"}</NavLink>
          </nav>
          <button className="md:hidden btn-ghost !py-1.5" aria-expanded={open} onClick={() => setOpen(!open)}>Menu</button>
        </div>
        {open && (
          <nav className="md:hidden border-t px-4 py-3 grid gap-3" style={{ borderColor: "var(--line)" }}>
            {[...NAV, ["/account", me ? me.displayName : "Sign in"] as const].map(([to, label]) => (
              <NavLink key={to} to={to} onClick={() => setOpen(false)}>{label}</NavLink>
            ))}
          </nav>
        )}
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
      <footer className="border-t mt-16" style={{ borderColor: "var(--line)" }}>
        <div className="mx-auto max-w-6xl px-4 py-8 text-sm muted grid gap-2 sm:flex sm:justify-between">
          <p>Every number on this site is computed by the project's own open code, or counted from real records.</p>
          <p className="flex gap-4">
            <Link to="/recyclers">Recyclers</Link>
            <Link to="/kit">Press &amp; letters</Link>
            <a href="https://github.com/dkzeanah/DomeSimulator">The code</a>
          </p>
        </div>
      </footer>
      <Toast />
    </div>
  );
}
