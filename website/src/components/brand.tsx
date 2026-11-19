// The brand's building blocks: a section on one of the two grounds -- yin, the dark one, is the
// code (a drafting grid on charcoal); yang, the light one, is the timber (growth rings on the
// split face of a log) -- its heading, and the small pieces the pages share. Pages alternate
// grounds so a scroll reads as timber and code taking turns.

import type { ReactNode } from "react";
import { Link } from "react-router-dom";

type Ground = "yin" | "yang" | "plain";

export function Band({ ground = "plain", texture, className = "", id, children }: {
  ground?: Ground; texture?: "grid" | "rings"; className?: string; id?: string; children: ReactNode;
}) {
  return (
    <section id={id} className={`relative ${ground === "plain" ? "" : ground} ${className}`}>
      {texture && <div aria-hidden className={`absolute inset-0 pointer-events-none ${texture === "grid" ? "grid-lines" : "rings"}`} />}
      <div className="relative mx-auto max-w-6xl px-4 py-16 sm:py-20">{children}</div>
    </section>
  );
}

export function Head({ eyebrow, title, lede, center = false }: { eyebrow?: string; title: ReactNode; lede?: ReactNode; center?: boolean }) {
  return (
    <div className={`max-w-3xl ${center ? "mx-auto text-center" : ""}`}>
      {eyebrow && <p className="eyebrow">{eyebrow}</p>}
      <h2 className="text-3xl sm:text-[2.6rem] leading-[1.1] font-semibold mt-3">{title}</h2>
      {lede && <p className="muted text-lg mt-4 leading-relaxed">{lede}</p>}
    </div>
  );
}

/** A page's own opening: eyebrow, a big title and the line that says what the page is for. */
export function PageHero({ eyebrow, title, lede, children, image }: {
  eyebrow: string; title: ReactNode; lede: ReactNode; children?: ReactNode; image?: string;
}) {
  return (
    <section className="yin relative overflow-hidden border-b" style={{ borderColor: "var(--line)" }}>
      {image && <img src={image} alt="" aria-hidden className="absolute inset-0 w-full h-full object-cover opacity-25" />}
      <div aria-hidden className="absolute inset-0 grid-lines" />
      <div aria-hidden className="absolute inset-0" style={{ background: "linear-gradient(180deg, rgba(14,18,16,0.2), rgba(14,18,16,0.85))" }} />
      <div className="relative mx-auto max-w-6xl px-4 pt-20 pb-16 sm:pt-28 sm:pb-20">
        <p className="eyebrow">{eyebrow}</p>
        <h1 className="text-4xl sm:text-6xl leading-[1.04] mt-4 max-w-4xl">{title}</h1>
        <p className="mt-5 text-lg sm:text-xl max-w-3xl muted leading-relaxed">{lede}</p>
        {children && <div className="mt-8 flex flex-wrap gap-3">{children}</div>}
      </div>
    </section>
  );
}

/** A row of figures in the drawing-label type. Every value is passed in from facts, never typed. */
export function Figures({ items }: { items: [ReactNode, string][] }) {
  return (
    <dl className="grid grid-cols-2 sm:grid-cols-4 border-y" style={{ borderColor: "var(--line)" }}>
      {items.map(([value, label], i) => (
        <div key={label} className={`py-5 px-4 ${i ? "sm:border-l" : ""} ${i % 2 ? "border-l sm:border-l" : ""}`} style={{ borderColor: "var(--line)" }}>
          <dt className="mono text-[11px] uppercase tracking-[0.14em] muted">{label}</dt>
          <dd className="display num text-3xl sm:text-4xl font-semibold mt-1">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

/** One idea, one card: a mark, a title and a sentence or two. */
export function Pillar({ mark, title, children, to, cta }: { mark: string; title: string; children: ReactNode; to?: string; cta?: string }) {
  return (
    <div className="panel lift p-6 flex flex-col">
      <span className="mono text-xs accent">{mark}</span>
      <h3 className="text-xl font-semibold mt-3">{title}</h3>
      <div className="muted text-[0.95rem] mt-2 leading-relaxed flex-1">{children}</div>
      {to && <Link to={to} className="link-arrow text-sm mt-4">{cta || "More"}</Link>}
    </div>
  );
}

/** The two halves the brand is made of, side by side. */
export function Halves({ left, right }: { left: ReactNode; right: ReactNode }) {
  return (
    <div className="grid md:grid-cols-2 rounded-xl overflow-hidden border" style={{ borderColor: "var(--line)" }}>
      <div className="yin p-8 sm:p-10 relative"><div aria-hidden className="absolute inset-0 grid-lines" /><div className="relative">{left}</div></div>
      <div className="yang p-8 sm:p-10 relative"><div aria-hidden className="absolute inset-0 rings" /><div className="relative">{right}</div></div>
    </div>
  );
}
