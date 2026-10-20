// The bedtime storytime player: the story's world full screen, one scene per page, and two ways to
// tell it. NARRATOR ON: the story is read aloud, the words light up as they are spoken, the pages
// turn by themselves. NARRATOR OFF ("I'll read it"): a grown-up reads aloud from the words on
// screen and turns the pages with the big arrows or a swipe; the world keeps moving. The switch is
// the biggest thing at the top of the screen, and the choice is offered at the start.
//
// Built for a tablet at bedtime: big buttons that hide themselves while the narrator reads, the
// screen kept awake, a soft lullaby, and one tap to start when the tablet will not let a page make
// sound on its own. A page with no recorded narration yet is read by the tablet's own voice.
// The Story Studio embeds the same player (embedded) to preview a draft as it is written.

import { useCallback, useEffect, useRef, useState } from "react";
import { Storyworld } from "./engine";
import { makeScenes, reshoot } from "./scenes";

export interface StoryPage { id: string; kind?: string; scene: string; shot?: string; text: string; key?: string; audio: string | null; words: [number, number, number, number][]; duration: number }
export interface Manifest { id: string; slug?: string; version?: number | null; title: string; series?: string; pages: StoryPage[]; figures: Record<string, number | string>; runtime: number }

const GAP = 1.4;            // seconds of quiet between pages, as the manifest's runtime counts them
const PREF = "storytime.narrator";

/** A soft lullaby pad: slow chords on a few sine voices, very quiet, under the narration. */
function lullaby() {
  const AC = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
  if (!AC) return null;
  const ac = new AC(), out = ac.createGain(), lp = ac.createBiquadFilter();
  lp.type = "lowpass"; lp.frequency.value = 900; out.gain.value = 0; lp.connect(out); out.connect(ac.destination);
  const chords = [[261.6, 329.6, 392.0], [220.0, 261.6, 329.6], [174.6, 220.0, 261.6], [196.0, 246.9, 293.7]];
  let k = 0, timer = 0;
  const play = () => {
    const t = ac.currentTime, ch = chords[k++ % chords.length];
    for (const f of [...ch, ch[0] / 2]) {
      const o = ac.createOscillator(), g = ac.createGain();
      o.type = "sine"; o.frequency.value = f; o.detune.value = (Math.random() - 0.5) * 6;
      g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(0.18, t + 2.5); g.gain.linearRampToValueAtTime(0, t + 8.5);
      o.connect(g); g.connect(lp); o.start(t); o.stop(t + 9);
    }
  };
  return {
    start() { ac.resume?.(); out.gain.cancelScheduledValues(ac.currentTime); out.gain.linearRampToValueAtTime(0.09, ac.currentTime + 3); if (!timer) { play(); timer = window.setInterval(play, 6000); } },
    stop(fade = 2) { out.gain.cancelScheduledValues(ac.currentTime); out.gain.linearRampToValueAtTime(0, ac.currentTime + fade); window.setTimeout(() => { window.clearInterval(timer); timer = 0; }, fade * 1000 + 100); },
    close() { window.clearInterval(timer); ac.close(); },
  };
}

/** The words of a page as spans [start, end]: the narration's own timings, or simply each word. */
function spansOf(p: StoryPage): [number, number][] {
  if (p.words.length) return p.words.map(([, , s, e]) => [s, e]);
  return [...p.text.matchAll(/\S+/g)].map((m) => [m.index!, m.index! + m[0].length]);
}

/** What the tablet's own voice reads: the same characters as the text, so its word positions match. */
const sayable = (t: string) => t.replace(/\s+--\s+/g, (m) => "," + " ".repeat(m.length - 1)).replace(/\n/g, " ");

function Icon({ d, size = 34 }: { d: string; size?: number }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d={d} /></svg>;
}
const PLAY = "M8 5v14l11-7z", PAUSE = "M6 5h4v14H6zm8 0h4v14h-4z", PREV = "M15.4 7.4 14 6l-6 6 6 6 1.4-1.4-4.6-4.6z", NEXT = "M8.6 16.6 10 18l6-6-6-6-1.4 1.4 4.6 4.6z";
const FULL = "M7 14H5v5h5v-2H7zm-2-4h2V7h3V5H5zm12 7h-3v2h5v-5h-2zM14 5v2h3v3h2V5z";
const SPEAKER = "M3 9v6h4l5 5V4L7 9H3zm13.5 3A4.5 4.5 0 0 0 14 8v8a4.5 4.5 0 0 0 2.5-4zM14 3.2v2.1a7 7 0 0 1 0 13.4v2.1a9 9 0 0 0 0-17.6z";
const BOOK = "M21 5c-1.1-.4-2.3-.5-3.5-.5-1.9 0-4 .4-5.5 1.5-1.5-1.1-3.6-1.5-5.5-1.5S2.5 4.9 1 6v14.6c1.5-1.1 3.6-1.5 5.5-1.5s4 .4 5.5 1.5c1.5-1.1 3.6-1.5 5.5-1.5 1.2 0 2.4.2 3.5.5V5zm0 13.5c-1.1-.4-2.3-.5-3.5-.5-1.7 0-4.2.7-5.5 1.5V8c1.3-.8 3.8-1.5 5.5-1.5 1.2 0 2.4.2 3.5.5v11.5z";

export interface StorytimeProps {
  src?: string;                         // a manifest URL, or
  manifest?: Manifest | null;           // the manifest itself (the Studio's preview)
  embedded?: boolean;                   // inside a page, not full screen
  jumpTo?: { page: number; at: number } | null;   // the Studio's "preview this page"
  onPage?: (i: number) => void;
  onGrownups?: () => void;
}

export default function Storytime({ src, manifest: given, embedded = false, jumpTo, onPage, onGrownups }: StorytimeProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const worldRef = useRef<(Storyworld & Record<string, any>) | null>(null);
  const scenesRef = useRef<Record<string, (dur: number) => unknown> | null>(null);
  const musicRef = useRef<ReturnType<typeof lullaby>>(null);
  const wakeRef = useRef<{ release: () => Promise<void> } | null>(null);
  const turnRef = useRef(0);
  const [fetched, setFetched] = useState<Manifest | null>(null);
  const manifest = given ?? fetched;
  const mRef = useRef<Manifest | null>(null); mRef.current = manifest;
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [narrator, setNarratorState] = useState(() => { try { return localStorage.getItem(PREF) !== "off"; } catch { return true; } });
  const narratorRef = useRef(narrator); narratorRef.current = narrator;
  const [playing, setPlaying] = useState(false);          // the narrator is reading
  const [started, setStarted] = useState(false);          // somebody has chosen how to tell it
  const [blocked, setBlocked] = useState(false);          // the tablet needs a tap before sound
  const [finished, setFinished] = useState(false);
  const [word, setWord] = useState(-1);
  const [chrome, setChrome] = useState(true);
  const playingRef = useRef(false);
  const pageRef = useRef(0);
  const hideTimer = useRef(0);
  const advance = useRef(0);
  const swipe = useRef<{ x: number; y: number } | null>(null);

  // the story's script, narration and figures
  useEffect(() => {
    if (given || !src) return;
    fetch(src).then((r) => { if (!r.ok) throw new Error(`The story did not load (${r.status}).`); return r.json(); })
      .then(setFetched).catch((e) => setError((e as Error).message));
  }, [src, given]);

  // the world, built once the first manifest is here (its figures letter the pictures), drawn every frame
  const haveManifest = !!manifest;
  useEffect(() => {
    if (!haveManifest || !canvasRef.current) return;
    const canvas = canvasRef.current;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const w = new Storyworld(canvas) as Storyworld & Record<string, any>;
    worldRef.current = w;
    let raf = 0, last = performance.now(), alive = true;
    const fit = () => { const r = canvas.getBoundingClientRect(); w.resize(Math.max(1, r.width), Math.max(1, r.height)); };
    const ro = new ResizeObserver(fit); ro.observe(canvas); fit();
    w.loadDome().then(() => {
      if (!alive) return;
      w.build();
      scenesRef.current = makeScenes(w, (mRef.current?.figures || {}) as never) as never;
      setReady(true);
      const loop = (now: number) => {
        const dt = Math.min(0.05, (now - last) / 1000); last = now;
        // the world holds still while the narrator is paused; a grown-up reading keeps it moving
        const moving = playingRef.current || !narratorRef.current || !w.shot;
        if (!document.hidden) w.step(moving ? dt : 0);
        raf = requestAnimationFrame(loop);
      };
      raf = requestAnimationFrame(loop);
    }).catch((e) => setError(`The picture did not load: ${(e as Error).message}`));
    return () => { alive = false; cancelAnimationFrame(raf); ro.disconnect(); w.renderer.dispose(); };
  }, [haveManifest]);

  const keepAwake = useCallback(async (on: boolean) => {
    try {
      if (on && !wakeRef.current && "wakeLock" in navigator) wakeRef.current = await (navigator as unknown as { wakeLock: { request: (t: string) => Promise<{ release: () => Promise<void> }> } }).wakeLock.request("screen");
      if (!on && wakeRef.current) { await wakeRef.current.release(); wakeRef.current = null; }
    } catch { /* not every tablet allows it */ }
  }, []);

  const hush = useCallback(() => {
    audioRef.current?.pause();
    try { window.speechSynthesis?.cancel(); } catch { /* none */ }
    window.clearTimeout(advance.current);
  }, []);

  const finish = useCallback(() => {
    playingRef.current = false; setPlaying(false); setFinished(true); musicRef.current?.stop(6); keepAwake(false);
  }, [keepAwake]);

  /** After a page is read: a breath, then the next page (or the end). */
  const readNext = useCallback((turn: number) => {
    window.clearTimeout(advance.current);
    advance.current = window.setTimeout(() => {
      const m = mRef.current;
      if (turn !== turnRef.current || !playingRef.current || !m) return;
      if (pageRef.current + 1 < m.pages.length) show(pageRef.current + 1, true);   // eslint-disable-line @typescript-eslint/no-use-before-define
      else finish();
    }, GAP * 1000);
  }, [finish]);   // eslint-disable-line react-hooks/exhaustive-deps

  /** Read the page aloud: its recorded narration, or the tablet's own voice. Resolves false if sound is blocked. */
  const read = useCallback((p: StoryPage, turn: number): Promise<boolean> => {
    const a = audioRef.current!;
    if (p.audio) {
      a.src = p.audio; a.currentTime = 0;
      return a.play().then(() => true, () => false);
    }
    const synth = window.speechSynthesis;
    if (!synth || !p.text.trim()) { readNext(turn); return Promise.resolve(true); }
    synth.cancel();
    const u = new SpeechSynthesisUtterance(sayable(p.text));
    u.rate = 0.9; u.pitch = 1.05;
    const voice = synth.getVoices().find((v) => /en[-_]US/i.test(v.lang) && /female|samantha|jenny|aria|zira/i.test(v.name)) || synth.getVoices().find((v) => /^en/i.test(v.lang));
    if (voice) u.voice = voice;
    const spans = spansOf(p);
    u.onboundary = (e) => { if (turn !== turnRef.current) return; const k = spans.findIndex(([s, en]) => e.charIndex >= s && e.charIndex < en + 1); if (k >= 0) setWord(k); };
    u.onend = () => { if (turn === turnRef.current) { setWord(spans.length); readNext(turn); } };
    synth.speak(u);
    return Promise.resolve(true);
  }, [readNext]);

  /** Open a page: stage its scene, start its camera move, and (with the narrator on) read it. */
  const show = useCallback((i: number, speak: boolean) => {
    const m = mRef.current, w = worldRef.current, scenes = scenesRef.current;
    if (!m || !w || !scenes || !m.pages.length) return;
    i = Math.max(0, Math.min(m.pages.length - 1, i));
    const p = m.pages[i];
    hush();
    pageRef.current = i; setPage(i); setWord(-1); setFinished(false); onPage?.(i);
    const dur = p.duration + GAP;
    let shot = (scenes[p.scene] || scenes.stars)(dur) as { dur: number };
    if (p.shot && p.shot !== "scene") shot = reshoot(w, shot, p.shot, dur);
    w.play(shot, shot.dur);
    const turn = ++turnRef.current;
    if (speak && narratorRef.current) {
      read(p, turn).then((ok) => {
        if (turn !== turnRef.current) return;
        playingRef.current = ok; setPlaying(ok); setBlocked(!ok);
        if (ok) setStarted(true);
      });
    } else { playingRef.current = false; setPlaying(false); }
  }, [hush, read, onPage]);

  // first page: read aloud straight away if the narrator is on and the tablet allows it
  useEffect(() => { if (ready) show(0, !embedded); }, [ready]);   // eslint-disable-line react-hooks/exhaustive-deps
  // the Studio's preview: jump to a page (and read it)
  useEffect(() => { if (ready && jumpTo) { setStarted(true); show(jumpTo.page, true); } }, [ready, jumpTo, show]);

  // narration's word timings, and the turn when it ends
  useEffect(() => {
    const a = audioRef.current; if (!a) return;
    const ended = () => readNext(turnRef.current);
    const tick = () => {
      const p = mRef.current?.pages[pageRef.current]; if (!p || !p.audio || !p.words.length) return;
      const now = a.currentTime;
      let k = -1; for (let j = 0; j < p.words.length; j++) if (p.words[j][0] <= now + 0.05) k = j; else break;
      setWord(k);
    };
    a.addEventListener("ended", ended); a.addEventListener("timeupdate", tick);
    const iv = window.setInterval(tick, 120);
    return () => { a.removeEventListener("ended", ended); a.removeEventListener("timeupdate", tick); window.clearInterval(iv); };
  }, [readNext]);

  // put the story down when the tablet is put down
  useEffect(() => {
    const vis = () => { if (document.hidden && playingRef.current) pause(); };
    document.addEventListener("visibilitychange", vis);
    return () => document.removeEventListener("visibilitychange", vis);
  });
  useEffect(() => () => { hush(); musicRef.current?.close(); keepAwake(false); }, [hush, keepAwake]);

  function poke() {
    setChrome(true);
    window.clearTimeout(hideTimer.current);
    hideTimer.current = window.setTimeout(() => { if (playingRef.current) setChrome(false); }, 4500);
  }
  function music() {
    if (!musicRef.current) musicRef.current = lullaby();
    musicRef.current?.start();
    keepAwake(true);
  }
  function bigScreen() {
    if (embedded) return;
    const el = document.documentElement as HTMLElement & { webkitRequestFullscreen?: () => Promise<void> };
    try { if (!document.fullscreenElement) (el.requestFullscreen?.() ?? el.webkitRequestFullscreen?.())?.catch?.(() => {}); } catch { /* fine */ }
  }
  function setNarrator(on: boolean) {
    setNarratorState(on); narratorRef.current = on;
    try { localStorage.setItem(PREF, on ? "on" : "off"); } catch { /* fine */ }
  }
  /** "Read it to me": the narrator reads from this page on. */
  function readToMe() {
    setNarrator(true); setStarted(true); music(); bigScreen();
    show(finished ? 0 : pageRef.current, true); poke();
  }
  /** "I'll read it": the narrator stops; the grown-up reads and turns the pages. */
  function illRead() {
    hush(); setNarrator(false); setStarted(true); setBlocked(false); music(); bigScreen();
    playingRef.current = false; setPlaying(false); setWord(-1);
    if (finished) show(0, false);
    setChrome(true);
  }
  function pause() {
    hush(); playingRef.current = false; setPlaying(false); setChrome(true);
    musicRef.current?.stop(1.5); keepAwake(false);
  }
  function go(d: number) {
    if (!mRef.current) return;
    const i = pageRef.current + d;
    if (i >= mRef.current.pages.length) { hush(); finish(); return; }
    music(); setStarted(true);
    show(i, narratorRef.current); poke();
  }
  function fullscreen() {
    const el = document.documentElement as HTMLElement & { webkitRequestFullscreen?: () => void };
    try { if (document.fullscreenElement) document.exitFullscreen(); else (el.requestFullscreen?.() ?? el.webkitRequestFullscreen?.()); } catch { /* fine */ }
  }

  const p = manifest?.pages[page];
  const text = p?.text ?? "";
  const showChrome = chrome || !playing;
  const spans = p ? spansOf(p) : [];
  const reading = narrator && (playing || word >= 0);
  const big = embedded ? "text-[0.95rem] sm:text-[1.1rem]" : "text-[1.25rem] sm:text-[1.6rem] lg:text-[1.85rem]";

  return (
    <div ref={rootRef}
         className={`${embedded ? "relative w-full aspect-video rounded-xl" : "fixed inset-0 z-[60]"} bg-[#05070f] text-white select-none overflow-hidden`}
         style={{ height: embedded ? undefined : "100dvh", touchAction: "manipulation", WebkitTapHighlightColor: "transparent" }}
         onPointerDown={(e) => { poke(); swipe.current = { x: e.clientX, y: e.clientY }; }}
         onPointerUp={(e) => {
           const s = swipe.current; swipe.current = null;
           if (!s || !started) return;
           const dx = e.clientX - s.x, dy = e.clientY - s.y;
           if (Math.abs(dx) > 70 && Math.abs(dx) > Math.abs(dy) * 1.5) go(dx < 0 ? 1 : -1);
         }}>
      <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" />
      <audio ref={audioRef} preload="auto" playsInline />

      {/* the cover's title, lettered over the dome */}
      {p?.kind === "title" && manifest && (
        <div className="absolute inset-x-0 top-[14%] text-center px-6 pointer-events-none story-fade">
          <p className="uppercase tracking-[0.3em] text-sm sm:text-base opacity-80">{manifest.series}</p>
          <h1 className={`mt-2 ${embedded ? "text-3xl" : "text-5xl sm:text-7xl"} font-bold`} style={{ fontFamily: "Georgia, serif", textShadow: "0 3px 18px rgba(0,0,0,0.55)" }}>{manifest.title}</h1>
        </div>
      )}

      {/* the words: lighting up as the narrator reads them, or all bright for a grown-up to read */}
      {p && p.kind !== "title" && text.trim() && (started || (narrator && !blocked && !embedded)) && (
        <div className={`absolute inset-x-0 bottom-0 px-4 sm:px-10 pt-20 pointer-events-none transition-[padding] duration-500 ${showChrome ? (embedded ? "pb-24" : "pb-40") : "pb-8"}`}
             style={{ background: "linear-gradient(to top, rgba(4,6,14,0.85), rgba(4,6,14,0.6) 60%, rgba(4,6,14,0))" }}>
          <p className={`mx-auto max-w-5xl text-center leading-snug ${big}`} style={{ fontFamily: "Georgia, 'Times New Roman', serif", textShadow: "0 2px 8px rgba(0,0,0,0.6)" }}>
            {(() => {
              const out: (string | React.ReactElement)[] = []; let at = 0;
              spans.forEach(([s, e], j) => {
                if (s < at) return;
                out.push(text.slice(at, s));
                const colour = !reading ? "#ffffff" : j === word ? "#ffd36b" : j < word ? "#ffffff" : "rgba(255,255,255,0.72)";
                out.push(<span key={j} style={{ color: colour, transition: "color .15s" }}>{text.slice(s, e)}</span>);
                at = e;
              });
              out.push(text.slice(at));
              return out.flatMap((n, i): (string | React.ReactElement)[] => typeof n === "string" ? n.split("\n").flatMap((t, k, A) => k < A.length - 1 ? [t, <br key={`b${i}-${k}`} />] : [t]) : [n]);
            })()}
          </p>
        </div>
      )}

      {/* controls: big, few, and out of the way while the narrator reads */}
      <div className={`absolute inset-x-0 bottom-0 pb-[max(1rem,env(safe-area-inset-bottom))] transition-opacity duration-500 ${showChrome ? "opacity-100" : "opacity-0 pointer-events-none"}`}>
        {manifest && (
          <div className="flex justify-center gap-1.5 mb-3 px-4 flex-wrap">
            {manifest.pages.map((q, i) => (
              <button key={q.id + i} aria-label={`Page ${i + 1}`} onClick={() => { setStarted(true); show(i, narratorRef.current); poke(); }}
                      className="h-3 rounded-full transition-all" style={{ width: i === page ? 28 : 12, background: i === page ? "#ffd36b" : q.audio ? "rgba(255,255,255,0.45)" : "rgba(255,255,255,0.22)" }} />
            ))}
          </div>
        )}
        <div className="flex items-center justify-center gap-5 sm:gap-8">
          <button aria-label="Previous page" onClick={() => go(-1)} className={`story-btn ${!narrator ? "story-btn-turn" : ""}`}><Icon d={PREV} size={narrator ? 34 : 48} /></button>
          {narrator && (
            <button aria-label={playing ? "Pause" : "Play"} onClick={() => (playing ? pause() : readToMe())} className="story-btn story-btn-big"><Icon d={playing ? PAUSE : PLAY} size={46} /></button>
          )}
          <button aria-label="Next page" onClick={() => go(1)} className={`story-btn ${!narrator ? "story-btn-turn" : ""}`}><Icon d={NEXT} size={narrator ? 34 : 48} /></button>
        </div>
      </div>
      <div className={`absolute top-0 inset-x-0 flex items-start justify-between gap-2 p-3 pt-[max(0.75rem,env(safe-area-inset-top))] transition-opacity duration-500 ${showChrome ? "opacity-100" : "opacity-0 pointer-events-none"}`}>
        {onGrownups && !embedded ? <button onClick={() => { pause(); onGrownups(); }} className="rounded-full bg-black/40 px-4 py-2.5 text-sm backdrop-blur">For grown-ups</button> : <span />}
        {/* the narrator switch: the one control everybody needs, so the biggest one up here */}
        <button role="switch" aria-checked={narrator} aria-label="Narrator" onClick={() => (narrator ? illRead() : readToMe())}
                className={`story-switch ${narrator ? "story-switch-on" : ""}`}>
          <Icon d={narrator ? SPEAKER : BOOK} size={embedded ? 20 : 26} />
          <span>{narrator ? "Narrator on" : "Narrator off -- I'm reading"}</span>
          <span className="story-knob" aria-hidden="true"><span /></span>
        </button>
        {!embedded ? <button aria-label="Full screen" onClick={fullscreen} className="story-btn !h-12 !w-12"><Icon d={FULL} size={26} /></button> : <span />}
      </div>

      {/* waiting, choosing, and the end */}
      {(!ready || error) && (
        <div className="absolute inset-0 grid place-items-center text-center px-6">
          <div>
            <div className="mx-auto mb-5 h-16 w-16 rounded-full bg-[#faf2d4] shadow-[0_0_60px_rgba(250,242,212,0.6)] story-pulse" />
            <p className="text-xl" style={{ fontFamily: "Georgia, serif" }}>{error ?? "Getting the story ready..."}</p>
          </div>
        </div>
      )}
      {ready && !started && (blocked || !narrator || embedded) && manifest && (
        <div className="absolute inset-0 grid place-items-center bg-[#05070f]/75 text-center px-6">
          <div>
            <p className={`${embedded ? "text-2xl" : "text-3xl sm:text-5xl"} font-bold`} style={{ fontFamily: "Georgia, serif" }}>{manifest.title}</p>
            <p className="mt-2 opacity-80">about {Math.max(1, Math.round(manifest.runtime / 60))} minutes</p>
            <div className={`mt-8 flex ${embedded ? "gap-3" : "gap-4 sm:gap-6"} justify-center flex-wrap`}>
              <button onClick={readToMe} className="story-choice story-choice-main"><Icon d={SPEAKER} size={embedded ? 30 : 44} /><span>Read it to me</span></button>
              <button onClick={illRead} className="story-choice"><Icon d={BOOK} size={embedded ? 30 : 44} /><span>I'll read it</span></button>
            </div>
          </div>
        </div>
      )}
      {finished && (
        <div className="absolute inset-0 grid place-items-center text-center px-6 story-dim">
          <div>
            <p className="text-4xl sm:text-5xl font-bold" style={{ fontFamily: "Georgia, serif" }}>Sweet dreams.</p>
            <div className="mt-8 flex gap-3 justify-center flex-wrap">
              <button onClick={readToMe} className="rounded-full bg-white/15 px-6 py-3 text-lg">Hear it again</button>
              <button onClick={() => { illRead(); show(0, false); }} className="rounded-full bg-white/10 px-6 py-3 text-lg">Read it again</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
