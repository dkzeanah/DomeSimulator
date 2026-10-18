// The Masterclass Theatre's control panel: every lesson the masterclass renderer can play
// (two_v_demo.lesson_registry, exported to /portal/masterclass.json), chapter by chapter. A chapter
// plays on the theatre's screen for its own length: its title and promise, its narration line by
// line, and the equations its film's code computes, revealed step by step. The browser can read
// the narration aloud. The films themselves are rendered on the desktop; this is their script.

import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import type { ToolProps } from "./tools";
import { Head } from "./tools/ui";

interface Chapter { slug: string; number: string; title: string; promise: string; narration: string[]; equations: string[]; duration: number; mood: string }
interface Lesson { key: string; brand: string; title: string; style: string; minutes: number; chapters: Chapter[] }

let catalogue: Promise<{ lessons: Lesson[]; default: string }> | null = null;
const load = () => (catalogue ??= fetch("/portal/masterclass.json").then((r) => { if (!r.ok) throw new Error(String(r.status)); return r.json(); }));

function wrap(ctx: CanvasRenderingContext2D, text: string, x: number, y: number, width: number, line: number, max = 99) {
  const words = text.split(/\s+/);
  let row = "", n = 0;
  for (const w of words) {
    const test = row ? `${row} ${w}` : w;
    if (ctx.measureText(test).width > width && row) { ctx.fillText(row, x, y + n * line); row = w; if (++n >= max) return n; }
    else row = test;
  }
  if (row) { ctx.fillText(row, x, y + n * line); n++; }
  return n;
}

function paint(canvas: HTMLCanvasElement, lesson: Lesson, ch: Chapter, t: number, colour: string) {
  const ctx = canvas.getContext("2d")!;
  const W = canvas.width, H = canvas.height;
  ctx.fillStyle = "#0d1426"; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = colour; ctx.font = "600 26px system-ui, sans-serif"; ctx.fillText(`${lesson.brand.toUpperCase()}  ·  ${ch.number}`, 48, 64);
  ctx.fillStyle = "#f4efe6"; ctx.font = "700 54px system-ui, sans-serif"; const rows = wrap(ctx, ch.title, 48, 132, W - 96, 60, 2);
  ctx.fillStyle = "#c9cfe0"; ctx.font = "italic 30px system-ui, sans-serif"; wrap(ctx, ch.promise, 48, 132 + rows * 60 + 20, W - 96, 38, 2);
  const f = Math.min(1, t / Math.max(1, ch.duration));
  const lines = ch.narration.length;
  const now = Math.min(lines - 1, Math.floor(f * lines));
  const eqs = ch.equations.length ? Math.max(1, Math.ceil(f * ch.equations.length)) : 0;
  const top = 340;
  if (eqs) {
    ctx.fillStyle = "rgba(255,255,255,.06)"; ctx.fillRect(W * 0.56, top - 40, W * 0.44 - 48, H - top - 40);
    ctx.fillStyle = "#e8b45a"; ctx.font = "500 26px ui-monospace, monospace";
    let y = top;
    ch.equations.slice(0, eqs).forEach((e, i) => { ctx.fillStyle = i === eqs - 1 ? "#ffd27a" : "#c8b48a"; y += wrap(ctx, e, W * 0.56 + 20, y, W * 0.44 - 88, 32, 3) * 32 + 10; });
  }
  if (lines) {
    ctx.fillStyle = "#f4efe6"; ctx.font = "34px system-ui, sans-serif";
    wrap(ctx, ch.narration[now] || "", 48, top, eqs ? W * 0.5 - 48 : W - 96, 44, 7);
  }
  ctx.fillStyle = "rgba(255,255,255,.18)"; ctx.fillRect(48, H - 34, W - 96, 8);
  ctx.fillStyle = colour; ctx.fillRect(48, H - 34, (W - 96) * f, 8);
}

export default function MasterclassPanel({ world, colour }: ToolProps) {
  const [lessons, setLessons] = useState<Lesson[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [key, setKey] = useState<string>("");
  const [ci, setCi] = useState(0);
  const [t, setT] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [voice, setVoice] = useState(false);
  const canvas = useRef<HTMLCanvasElement | null>(null);
  const texture = useRef<THREE.CanvasTexture | null>(null);
  const spoken = useRef("");

  useEffect(() => { load().then((c) => { setLessons(c.lessons); setKey((k) => k || c.default || c.lessons[0].key); }).catch((e) => setError((e as Error).message)); }, []);
  const lesson = useMemo(() => lessons?.find((l) => l.key === key) ?? null, [lessons, key]);
  const ch = lesson?.chapters[ci] ?? null;
  useEffect(() => { setCi(0); setT(0); setPlaying(false); }, [key]);
  useEffect(() => { setT(0); }, [ci]);

  // the screen: one canvas texture, repainted as the chapter plays
  useEffect(() => {
    if (!lesson) return;
    const c = document.createElement("canvas"); c.width = 1280; c.height = 720;
    canvas.current = c;
    const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
    texture.current = tex;
    const g = new THREE.Group();
    const screen = new THREE.Mesh(new THREE.PlaneGeometry(16, 9), new THREE.MeshBasicMaterial({ map: tex }));
    screen.position.set(0, 6.5, -2);
    screen.userData.part = { id: "masterclass:screen", name: "the screen", examine: `${lesson.title}: ${lesson.chapters.length} chapters, about ${Math.round(lesson.minutes)} minutes.` };
    const frame = new THREE.Mesh(new THREE.PlaneGeometry(16.6, 9.6), new THREE.MeshStandardMaterial({ color: colour, emissive: colour, emissiveIntensity: 0.5 }));
    frame.position.set(0, 6.5, -2.05);
    const legs = new THREE.MeshLambertMaterial({ color: "#3a3226" });
    for (const x of [-7.5, 7.5]) { const l = new THREE.Mesh(new THREE.BoxGeometry(0.4, 2.2, 0.4), legs); l.position.set(x, 1.1, -2.1); g.add(l); }
    g.add(frame, screen);
    const put = () => world.current?.setModel(g);
    put();
    const timer = window.setTimeout(put, 50);
    return () => window.clearTimeout(timer);
  }, [lesson, world, colour]);
  useEffect(() => {
    if (!lesson || !ch || !canvas.current || !texture.current) return;
    paint(canvas.current, lesson, ch, t, colour);
    texture.current.needsUpdate = true;
  }, [lesson, ch, t, colour]);

  // the clock
  useEffect(() => {
    if (!playing || !ch) return;
    const start = performance.now() - t * 1000;
    const timer = window.setInterval(() => {
      const now = (performance.now() - start) / 1000;
      if (now >= ch.duration) {
        if (lesson && ci < lesson.chapters.length - 1) setCi((i) => i + 1); else setPlaying(false);
        setT(0);
      } else setT(now);
    }, 250);
    return () => window.clearInterval(timer);
  }, [playing, ch]); // eslint-disable-line react-hooks/exhaustive-deps

  // reading aloud, one narration line at a time
  const line = ch && ch.narration.length ? ch.narration[Math.min(ch.narration.length - 1, Math.floor((t / Math.max(1, ch.duration)) * ch.narration.length))] : "";
  useEffect(() => {
    if (!voice || !playing || !line || spoken.current === line || typeof speechSynthesis === "undefined") return;
    spoken.current = line;
    speechSynthesis.cancel();
    speechSynthesis.speak(new SpeechSynthesisUtterance(line));
  }, [voice, playing, line]);
  useEffect(() => { if (!playing || !voice) { if (typeof speechSynthesis !== "undefined") speechSynthesis.cancel(); spoken.current = ""; } }, [playing, voice]);
  useEffect(() => () => { if (typeof speechSynthesis !== "undefined") speechSynthesis.cancel(); }, []);

  if (error) return <p className="text-xs" style={{ color: "#ff8a7a" }}>Could not load the lessons: {error}</p>;
  if (!lessons || !lesson || !ch) return <p className="text-xs muted">Loading every lesson...</p>;
  return (
    <div className="grid gap-3">
      <div>
        <p className="text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: colour }}>The masterclass</p>
        <p className="text-xs muted mt-0.5">{lessons.length} lessons, every chapter with its narration and its working.</p>
      </div>
      <label className="grid gap-0.5 text-xs">
        <span className="muted">Lesson</span>
        <select className="field !py-1 text-sm" value={key} onChange={(e) => setKey(e.target.value)}>
          {lessons.map((l) => <option key={l.key} value={l.key}>{l.title} ({Math.max(1, Math.round(l.minutes))} min)</option>)}
        </select>
      </label>
      <div className="flex items-center gap-2">
        <button className="btn-ghost !py-1 !px-2 text-sm" disabled={ci === 0} onClick={() => setCi((i) => i - 1)} aria-label="Previous chapter">&larr;</button>
        <button className="btn-ghost !py-1 !px-3 text-sm font-semibold" style={{ borderColor: colour, color: colour }} onClick={() => setPlaying((p) => !p)}>{playing ? "Pause" : "Play"}</button>
        <button className="btn-ghost !py-1 !px-2 text-sm" disabled={ci === lesson.chapters.length - 1} onClick={() => setCi((i) => i + 1)} aria-label="Next chapter">&rarr;</button>
        <label className="flex items-center gap-1 text-xs ml-auto"><input type="checkbox" checked={voice} onChange={(e) => setVoice(e.target.checked)} />Read aloud</label>
      </div>
      <input type="range" min={0} max={Math.max(1, Math.round(ch.duration))} step={1} value={Math.round(t)} onChange={(e) => setT(Number(e.target.value))} aria-label="Scrub the chapter" />
      <p className="text-[11px] muted num">{Math.floor(t)} of {Math.round(ch.duration)} s, chapter {ci + 1} of {lesson.chapters.length}</p>
      <div>
        <Head>{ch.number} {ch.title}</Head>
        <p className="text-xs italic">{ch.promise}</p>
        {ch.equations.length > 0 && (
          <div className="mt-1 text-[11px] num panel-2 p-2">{ch.equations.map((e, i) => <div key={i}>{e}</div>)}</div>
        )}
      </div>
      <div>
        <Head>Chapters</Head>
        <ol className="text-xs space-y-0.5">
          {lesson.chapters.map((c, i) => (
            <li key={c.slug}><button className="text-left hover:underline" style={i === ci ? { color: colour, fontWeight: 600 } : undefined} onClick={() => setCi(i)}>{c.number} {c.title}</button></li>
          ))}
        </ol>
      </div>
      <details className="text-xs"><summary className="cursor-pointer font-semibold">The chapter&rsquo;s narration</summary>
        <div className="mt-1 space-y-1">{ch.narration.map((n, i) => <p key={i} style={n === line ? { color: colour } : undefined}>{n}</p>)}</div>
      </details>
      <p className="text-[11px] muted leading-snug">
        The script and the working of every film in <code>two_v_demo/lesson_*.py</code>, as the renderer plays them. The films themselves, with their pictures, are on the Media page.
      </p>
    </div>
  );
}
