import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { trackView } from "../lib/track";
import { isRealStaff, isStaff, setViewAs, useSession, type ViewMode } from "../lib/session";
import { Toast } from "./ui";
import { TOOL_GROUPS } from "../lib/toolsMenu";

const NAV = [
  ["/portal", "Portal"],
  ["/start", "Free Pages"],
  ["/book", "The Book"],
  ["/build", "The Build"],
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
  const { me, viewAs, setMe, notify } = useSession();
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
      {(isRealStaff(me) || viewAs) && <ViewAs mode={viewAs ? "guest" : me?.viewingAsUser ? "user" : "admin"} />}
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
            <ToolsMenu staff={isStaff(me)} />
            {me && isStaff(me) && <NavLink to="/admin/studio" className={({ isActive }) => (isActive || loc.pathname.startsWith("/admin") ? "accent" : "muted hover:text-[var(--ink)]")}>Admin</NavLink>}
            {me && <NavLink to="/mylinks" className={({ isActive }) => (isActive ? "accent" : "muted hover:text-[var(--ink)]")}>My Links</NavLink>}
            <NavLink to="/account" className="btn-ghost !py-1.5">{me ? me.displayName : "Sign in"}</NavLink>
            {me && <button type="button" className="muted hover:text-[var(--ink)] text-sm" onClick={signOut}>Sign out</button>}
          </nav>
          <button className="md:hidden btn-ghost !py-1.5" aria-expanded={open} onClick={() => setOpen(!open)}>Menu</button>
        </div>
        {open && (
          <nav className="md:hidden border-t px-4 py-3 grid gap-3" style={{ borderColor: "var(--line)" }}>
            {[...NAV, ...(me ? [["/mylinks", "My Links"] as const] : []), ...(me && isStaff(me) ? [["/admin/studio", "Admin"] as const] : []), ["/account", me ? me.displayName : "Sign in"] as const].map(([to, label]) => (
              <NavLink key={to} to={to} onClick={() => setOpen(false)}>{label}</NavLink>
            ))}
            <details className="grid gap-2">
              <summary className="cursor-pointer">Tools</summary>
              <div className="grid gap-2 pl-3 pt-2">
                <NavLink to="/tools" onClick={() => setOpen(false)}>All tools</NavLink>
                {TOOL_GROUPS.filter((g) => !g.staff || isStaff(me)).map((g) => (
                  <div key={g.title} className="grid gap-1.5">
                    <p className="text-[11px] uppercase tracking-[0.15em] muted">{g.title}</p>
                    {g.items.map((t) => t.external
                      ? <a key={t.key} href={t.to} target="_blank" rel="noopener">{t.label} &#8599;</a>
                      : <NavLink key={t.key} to={t.to} onClick={() => setOpen(false)}>{t.label}</NavLink>)}
                  </div>
                ))}
              </div>
            </details>
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
            <Link to="/software">Software</Link>
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

/** The owner's switch: the site as they see it, as a signed-in member with nothing bought sees it,
 *  or as a visitor who is not signed in. */
function ViewAs({ mode }: { mode: ViewMode }) {
  const btn = (m: ViewMode, label: string) => (
    <button type="button" onClick={() => m !== mode && setViewAs(m)} aria-pressed={m === mode}
      className="px-2.5 py-0.5 rounded-full"
      style={m === mode ? { background: "#fff", color: "#111" } : { color: "inherit", opacity: 0.85 }}>{label}</button>
  );
  const say = mode === "user" ? "Viewing the site as a regular member: admin pages and owner access are off."
    : mode === "guest" ? "Viewing the site signed out, as a visitor sees it."
    : "View the site as:";
  return (
    <div role="status" className="flex flex-wrap items-center justify-center gap-2 text-xs font-semibold py-1 px-4"
      style={{ background: mode === "user" ? "#1d4ed8" : mode === "guest" ? "#7c2d92" : "#26303d", color: "#fff" }}>
      <span>{say}</span>
      <span className="inline-flex rounded-full p-0.5" style={{ background: "rgba(255,255,255,.15)" }}>
        {btn("admin", "Admin")}{btn("user", "Regular member")}{btn("guest", "Signed out")}
      </span>
    </div>
  );
}

/** The Tools menu: every tool, grouped (src/lib/toolsMenu.ts); the label itself goes to /tools. */
function ToolsMenu({ staff }: { staff: boolean }) {
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  useEffect(() => setOpen(false), [loc.pathname]);
  const groups = TOOL_GROUPS.filter((g) => !g.staff || staff);
  const here = loc.pathname === "/tools" || groups.some((g) => g.items.some((t) => !t.external && loc.pathname.startsWith(t.to.split("#")[0]) && t.to !== "/"));
  return (
    <div className="relative" onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}>
      <button type="button" className={here ? "accent" : "muted hover:text-[var(--ink)]"} aria-expanded={open} aria-haspopup="menu"
        onClick={() => setOpen(!open)} onKeyDown={(e) => { if (e.key === "Escape") setOpen(false); }}>Tools &#9662;</button>
      {open && (
        <div role="menu" className="absolute right-0 top-full pt-2 z-50">
          <div className="panel p-3 grid gap-3 w-[min(560px,90vw)] sm:grid-cols-2 text-sm shadow-xl">
            {groups.map((g) => (
              <div key={g.title} className="grid gap-1 content-start">
                <p className="text-[11px] uppercase tracking-[0.15em] muted font-semibold">{g.title}</p>
                {g.items.map((t) => t.external ? (
                  <a key={t.key} role="menuitem" href={t.to} target="_blank" rel="noopener" className="rounded px-2 py-1 hover:bg-[var(--line)]">
                    <span className="font-semibold">{t.label} &#8599;</span><span className="block text-xs muted">{t.blurb}</span></a>
                ) : (
                  <Link key={t.key} role="menuitem" to={t.to} className="rounded px-2 py-1 hover:bg-[var(--line)]">
                    <span className="font-semibold">{t.label}</span><span className="block text-xs muted">{t.blurb}</span></Link>
                ))}
              </div>
            ))}
            <Link to="/tools" className="sm:col-span-2 text-center underline text-xs">All tools on one page</Link>
          </div>
        </div>
      )}
    </div>
  );
}
