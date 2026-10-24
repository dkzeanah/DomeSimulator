// The paid tools, three ways in: Dome Sketch's own page (/sketch), the trial of every tool
// (/software), and each account's own links (/mylinks), which show only what that account may open
// (the owner sees everything). Access comes from /api/me/tools (functions/_lib/tools.ts).

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Buy from "../components/Buy";
import { ErrorLine, Panel } from "../components/ui";
import { api } from "../lib/api";
import { useCatalogue } from "../lib/catalogue";
import { useMeta } from "../lib/meta";
import { useSession } from "../lib/session";
import grid from "../generated/sketch-grid.json";

interface Tool { key: string; title: string; blurb: string; href: string; access: boolean; why: string; credits?: number; used?: number; local?: boolean; buy?: string }
interface Pack { ref: string; status: string; spec: Record<string, any>; error: string | null; size: number | null; createdAt: string; doneAt: string | null; pdfUrl: string | null }

const G = grid as unknown as { designs: Record<string, unknown>; diameters: number[]; cuts: unknown[]; windows: number[]; trial: string[] };

function useTools() {
  const { me } = useSession();
  const [tools, setTools] = useState<Tool[] | null>(null);
  const [admin, setAdmin] = useState(false);
  useEffect(() => { api<{ tools: Tool[]; admin: boolean }>("/me/tools").then((r) => { setTools(r.tools); setAdmin(r.admin); }).catch(() => setTools([])); }, [me?.id]);
  return { tools, admin, me };
}

function Packs() {
  const [packs, setPacks] = useState<Pack[] | null>(null);
  useEffect(() => {
    let live = true, timer: ReturnType<typeof setTimeout>;
    const load = () => api<{ packs: Pack[] }>("/sketch/packs").then((r) => {
      if (!live) return;
      setPacks(r.packs);
      if (r.packs.some((p) => p.status === "queued" || p.status === "rendering")) timer = setTimeout(load, 15000);
    }).catch(() => setPacks([]));
    load();
    return () => { live = false; clearTimeout(timer); };
  }, []);
  if (!packs?.length) return <p className="text-sm muted">No build packs yet. In Dome Sketch, press <b>Make my build pack</b>.</p>;
  return (
    <ul className="grid gap-2">
      {packs.map((p) => (
        <li key={p.ref} className="panel-2 p-3 text-sm flex flex-wrap gap-3 items-center justify-between">
          <span><b>{p.spec.frequency}V {p.spec.cut}, {(+p.spec.diameter_m).toFixed(2)} m</b> -- {p.spec.door ? "door" : "no door"}, {p.spec.windows} windows, {p.spec.skin} skin</span>
          {p.pdfUrl ? <a className="btn" href={p.pdfUrl}>Download the pack (PDF)</a>
            : <span className="muted">{p.status === "failed" ? p.error : "Being drawn on the workshop computer; this page checks by itself."}</span>}
        </li>
      ))}
    </ul>
  );
}

export function SketchPage() {
  useMeta("Dome Sketch", "Design a framed-panel geodesic dome in 3-D and get the build pack: plans, cut list, materials, tools, price estimate and every assembly step.", "/sketch");
  const { tools, me } = useTools();
  const { get } = useCatalogue();
  const t = tools?.find((x) => x.key === "domesketch");
  const product = get("dome-sketch");
  return (
    <div className="mx-auto max-w-5xl px-4 py-10 grid gap-6">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">Dome Sketch</p>
        <h1 className="text-4xl sm:text-5xl font-bold mt-1">Design your dome. Then build it.</h1>
        <p className="mt-2 muted max-w-3xl">
          Shape a framed-panel geodesic dome in your browser: {G.cuts.length} geodesic choices, {G.diameters.length} sizes
          from {G.diameters[0]} to {G.diameters[G.diameters.length - 1]} m, door, windows, skylight, skin. Walk round it, cut a section through it,
          explode it, step through the build. Then make its build pack: the plans, cut list, materials, tools, a price estimate and every
          assembly step, for your design exactly.
        </p>
      </div>
      {!tools ? <p className="muted">Checking your access...</p> : t?.access ? (
        <Panel kicker={`Yours (${t.why})`} title="Open Dome Sketch">
          <a className="btn" href="/sketch-app/">Open Dome Sketch</a>
          {t.credits !== undefined && <p className="text-sm muted mt-2">{Math.max(0, t.credits - (t.used || 0))} of {t.credits} build packs left.</p>}
          <h3 className="font-semibold mt-4 mb-2">Your build packs</h3>
          <Packs />
        </Panel>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          <Panel kicker="Free" title="Try it">
            <p className="text-sm mb-3">Two designs open in full: turn them, section them, explode them, read their cut lists.</p>
            <a className="btn-ghost" href="/sketch-app/">Open the trial</a>
          </Panel>
          <Panel kicker="$10 one time, or free with the book" title="Every design and the build pack">
            {product ? (me ? <Buy product={product} cta="Get Dome Sketch" /> : <p className="text-sm"><Link className="underline" to="/account">Sign in or make an account</Link> first: Dome Sketch belongs to your account.</p>) : <p className="muted text-sm">Loading...</p>}
            <p className="text-xs muted mt-2">Already bought the book? <Link className="underline" to="/account/books">Save it to your account</Link> and Dome Sketch opens.</p>
          </Panel>
        </div>
      )}
    </div>
  );
}

const TRIAL: { key: string; title: string; trial: string[]; full: string[]; try?: [string, string]; note?: string }[] = [
  { key: "dome-sketch", title: "Dome Sketch", try: ["/sketch-app/", "Open the trial"],
    trial: ["Two complete designs: the 16 ft reference and a 4 m 2V", "Every view, style, section, explode and build step", "Each design's cut list and measurements"],
    full: ["Every geodesic, size, door, window and skylight choice", "Skin, furnishings and porch on any design", "Build packs: the full plan set as a PDF, for your design exactly"] },
  { key: "wedge-builder", title: "Wedge Builder", try: ["/calculator", "Try the wedge calculator"],
    trial: ["The wedge calculator: what each split keeps of a log, at your kerf", "Every film on Episodes"],
    full: ["A cut list for your own wedge dome and logs: saw setups, cut families, log plan, jigs, seams", "Alternating in/out builds, band by band"] },
  { key: "studio", title: "Episode Director and the Season room", note: "The owner's production tools for the films (not sold).",
    trial: ["The finished episodes, on Episodes"], full: [] },
];

export function SoftwarePage() {
  useMeta("Software", "Try the dome tools: Dome Sketch, the Wedge Builder and the calculator. What the trial does and what the full tools add.", "/software");
  const { get } = useCatalogue();
  return (
    <div className="mx-auto max-w-5xl px-4 py-10 grid gap-6">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">Software</p>
        <h1 className="text-4xl sm:text-5xl font-bold mt-1">Try the tools</h1>
        <p className="mt-2 muted max-w-3xl">Every tool here runs on the project's own solvers: the numbers you see are the ones the book and the films use.</p>
      </div>
      {TRIAL.map((t) => {
        const p = get(t.key);
        return (
          <section key={t.key} id={t.key} className="panel p-5 grid gap-4 scroll-mt-20">
            <h2 className="text-2xl font-semibold">{t.title}</h2>
            {t.note && <p className="text-sm muted">{t.note}</p>}
            <div className="grid gap-4 sm:grid-cols-2">
              <div><h3 className="font-semibold mb-1">Free trial</h3><ul className="text-sm grid gap-1">{t.trial.map((x) => <li key={x}>- {x}</li>)}</ul>
                {t.try && <a className="btn-ghost mt-3 inline-block" href={t.try[0]}>{t.try[1]}</a>}</div>
              {t.full.length > 0 && <div><h3 className="font-semibold mb-1">The full tool</h3><ul className="text-sm grid gap-1">{t.full.map((x) => <li key={x}>- {x}</li>)}</ul>
                {p && p.status === "live" && <div className="mt-3"><Buy product={p} cta={`Get ${t.title}`} /></div>}
                {t.key === "dome-sketch" && <p className="text-xs muted mt-2">Free with The 40 Hour Cabin.</p>}</div>}
            </div>
          </section>
        );
      })}
    </div>
  );
}

export function MyLinksPage() {
  useMeta("My Links", "The tools your account can open.", "/mylinks");
  const { tools, admin, me } = useTools();
  const [error] = useState<string | null>(null);
  if (!me) return <div className="mx-auto max-w-xl px-4 py-10"><p><Link className="underline" to="/account">Sign in</Link> to see your links.</p></div>;
  const open = tools?.filter((t) => t.access) || [], locked = tools?.filter((t) => !t.access) || [];
  return (
    <div className="mx-auto max-w-5xl px-4 py-10 grid gap-6">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">My Links</p>
        <h1 className="text-4xl font-bold mt-1">{admin ? "Everything (you are the owner)" : "Your tools"}</h1>
      </div>
      <ErrorLine error={error} />
      <div className="grid sm:grid-cols-2 gap-4">
        {open.map((t) => (
          <Panel key={t.key} kicker={t.local ? "On your computer: py -3.12 -m sketch_claude serve" : t.why} title={t.title}>
            <p className="text-sm mb-3">{t.blurb}</p>
            {t.href.startsWith("/") && !t.href.startsWith("/sketch-app") ? <Link className="btn" to={t.href}>Open</Link> : <a className="btn" href={t.href} target={t.local ? "_blank" : undefined} rel="noopener">Open</a>}
            {t.key === "domesketch" && t.credits !== undefined && <p className="text-xs muted mt-2">{Math.max(0, t.credits - (t.used || 0))} of {t.credits} build packs left.</p>}
          </Panel>
        ))}
      </div>
      {open.some((t) => t.key === "domesketch") && <Panel kicker="Dome Sketch" title="Your build packs"><Packs /></Panel>}
      {locked.length > 0 && (
        <section className="grid gap-3">
          <h2 className="text-2xl font-semibold">More tools</h2>
          {locked.map((t) => (
            <div key={t.key} className="panel-2 p-3 text-sm flex flex-wrap justify-between gap-2">
              <span><b>{t.title}</b>: {t.blurb} <span className="muted">({t.why})</span></span>
              <Link className="btn-ghost" to={`/software#${t.buy || t.key}`}>See it</Link>
            </div>
          ))}
        </section>
      )}
    </div>
  );
}
