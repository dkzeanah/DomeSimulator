// The bedtime storytime player: the story's world full screen, its narration read aloud with the
// words lighting up as they are spoken, one scene per page, turning by itself. Built for a tablet at
// bedtime: big buttons that hide themselves, the screen kept awake while it plays, a soft lullaby
// under the voice, and one tap to start when the tablet will not let a page make sound on its own.

import { useCallback, useEffect, useRef, useState } from "react";
import { Storyworld } from "./engine";
import { makeScenes } from "./scenes";

export interface StoryPage { id: string; kind?: string; scene: string; text: string; audio: string; words: [number, number, number, number][]; duration: number }
export interface Manifest { id: string; title: string; series?: string; pages: StoryPage[]; figures: Record<string, number | string>; runtime: number }

const GAP = 1.4;            // seconds of quiet between pages, as the manifest's runtime counts them

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

function Icon({ d, size = 34 }: { d: string; size?: number }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d={d} /></svg>;
}
const PLAY = "M8 5v14l11-7z", PAUSE = "M6 5h4v14H6zm8 0h4v14h-4z", PREV = "M6 6h2v12H6zm3.5 6 8.5 6V6z", NEXT = "M16 6h2v12h-2zM6 18l8.5-6L6 6z";
const FULL = "M7 14H5v5h5v-2H7zm-2-4h2V7h3V5H5zm12 7h-3v2h5v-5h-2zM14 5v2h3v3h2V5z", CC = "M19 4H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zm-8 7H9.5v-.5h-2v3h2V13H11v1a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1v-4a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1zm7 0h-1.5v-.5h-2v3h2V13H18v1a1 1 0 0 1-1 1h-3a1 1 0 0 1-1-1v-4a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1z";

export default function Storytime({ src, onGrownups }: { src: string; onGrownups: () => void }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const worldRef = useRef<(Storyworld & Record<string, any>) | null>(null);
  const scenesRef = useRef<Record<string, (dur: number) => unknown> | null>(null);
  const musicRef = useRef<ReturnType<typeof lullaby>>(null);
  const wakeRef = useRef<{ release: () => Promise<void> } | null>(null);
  const turnRef = useRef(0);
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [needTap, setNeedTap] = useState(false);
  const [finished, setFinished] = useState(false);
  const [word, setWord] = useState(-1);
  const [captions, setCaptions] = useState(true);
  const [chrome, setChrome] = useState(true);
  const playingRef = useRef(false);
  const pageRef = useRef(0);
  const hideTimer = useRef(0);

  // the story's script, narration and figures
  useEffect(() => {
    fetch(src).then((r) => { if (!r.ok) throw new Error(`The story did not load (${r.status}).`); return r.json(); })
      .then(setManifest).catch((e) => setError((e as Error).message));
  }, [src]);

  // the world, built once, drawn every frame
  useEffect(() => {
    if (!manifest || !canvasRef.current) return;
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
      scenesRef.current = makeScenes(w, manifest.figures as never) as never;
      setReady(true);
      const loop = (now: number) => {
        const dt = Math.min(0.05, (now - last) / 1000); last = now;
        if (!document.hidden) w.step(playingRef.current || !w.shot ? dt : 0);
        raf = requestAnimationFrame(loop);
      };
      raf = requestAnimationFrame(loop);
    }).catch((e) => setError(`The picture did not load: ${(e as Error).message}`));
    return () => { alive = false; cancelAnimationFrame(raf); ro.disconnect(); w.renderer.dispose(); };
  }, [manifest]);

  const keepAwake = useCallback(async (on: boolean) => {
    try {
      if (on && !wakeRef.current && "wakeLock" in navigator) wakeRef.current = await (navigator as unknown as { wakeLock: { request: (t: string) => Promise<{ release: () => Promise<void> }> } }).wakeLock.request("screen");
      if (!on && wakeRef.current) { await wakeRef.current.release(); wakeRef.current = null; }
    } catch { /* not every tablet allows it */ }
  }, []);

  /** Open a page: stage its scene, start its camera move, and (if playing) read it. */
  const show = useCallback((i: number, autoplay: boolean) => {
    const m = manifest, w = worldRef.current, scenes = scenesRef.current, a = audioRef.current;
    if (!m || !w || !scenes || !a) return;
    const p = m.pages[i];
    pageRef.current = i; setPage(i); setWord(-1); setFinished(false);
    const shot = (scenes[p.scene] || scenes.stars)(p.duration + GAP) as { dur: number };
    w.play(shot, shot.dur);
    const turn = ++turnRef.current;
    a.src = p.audio; a.currentTime = 0;
    if (autoplay) {
      a.play().then(() => { if (turn === turnRef.current) { playingRef.current = true; setPlaying(true); setNeedTap(false); } })
        .catch(() => { if (turn === turnRef.current) { playingRef.current = false; setPlaying(false); setNeedTap(true); } });
    }
  }, [manifest]);

  // first page, read aloud straight away if the tablet allows it
  useEffect(() => { if (ready) show(0, true); }, [ready, show]);

  // the next page when this one has been read, after a breath
  useEffect(() => {
    const a = audioRef.current; if (!a) return;
    let t = 0;
    const ended = () => {
      const turn = turnRef.current;
      t = window.setTimeout(() => {
        if (turn !== turnRef.current || !playingRef.current || !manifest) return;
        if (pageRef.current + 1 < manifest.pages.length) show(pageRef.current + 1, true);
        else { playingRef.current = false; setPlaying(false); setFinished(true); musicRef.current?.stop(6); keepAwake(false); }
      }, GAP * 1000);
    };
    const tick = () => {
      const p = manifest?.pages[pageRef.current]; if (!p) return;
      const now = a.currentTime;
      let k = -1; for (let j = 0; j < p.words.length; j++) if (p.words[j][0] <= now + 0.05) k = j; else break;
      setWord(k);
    };
    a.addEventListener("ended", ended); a.addEventListener("timeupdate", tick);
    const iv = window.setInterval(tick, 120);
    return () => { a.removeEventListener("ended", ended); a.removeEventListener("timeupdate", tick); window.clearInterval(iv); window.clearTimeout(t); };
  }, [manifest, show, keepAwake]);

  // put the story down when the tablet is put down
  useEffect(() => {
    const vis = () => { if (document.hidden && playingRef.current) pause(); };
    document.addEventListener("visibilitychange", vis);
    return () => document.removeEventListener("visibilitychange", vis);
  });
  useEffect(() => () => { musicRef.current?.close(); keepAwake(false); }, [keepAwake]);

  function poke() {
    setChrome(true);
    window.clearTimeout(hideTimer.current);
    hideTimer.current = window.setTimeout(() => { if (playingRef.current) setChrome(false); }, 4500);
  }
  function start() {
    if (!musicRef.current) musicRef.current = lullaby();
    musicRef.current?.start();
    keepAwake(true);
    const el = document.documentElement as HTMLElement & { webkitRequestFullscreen?: () => void };
    try { if (!document.fullscreenElement) (el.requestFullscreen?.() ?? el.webkitRequestFullscreen?.())?.catch?.(() => {}); } catch { /* fine */ }
    if (finished) { show(0, true); return; }
    const a = audioRef.current; if (!a) return;
    a.play().then(() => { playingRef.current = true; setPlaying(true); setNeedTap(false); poke(); }).catch(() => setNeedTap(true));
  }
  function pause() {
    audioRef.current?.pause(); playingRef.current = false; setPlaying(false); setChrome(true);
    musicRef.current?.stop(1.5); keepAwake(false);
  }
  function go(d: number) {
    if (!manifest) return;
    const i = Math.max(0, Math.min(manifest.pages.length - 1, pageRef.current + d));
    if (!musicRef.current) musicRef.current = lullaby();
    musicRef.current?.start(); keepAwake(true);
    show(i, true); poke();
  }
  function fullscreen() {
    const el = document.documentElement as HTMLElement & { webkitRequestFullscreen?: () => void };
    try { if (document.fullscreenElement) document.exitFullscreen(); else (el.requestFullscreen?.() ?? el.webkitRequestFullscreen?.()); } catch { /* fine */ }
  }

  const p = manifest?.pages[page];
  const text = p?.text ?? "";

  return (
    <div className="fixed inset-0 z-[60] bg-[#05070f] text-white select-none overflow-hidden"
         style={{ height: "100dvh", touchAction: "manipulation", WebkitTapHighlightColor: "transparent" }}
         onPointerDown={poke}>
      <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" />
      <audio ref={audioRef} preload="auto" playsInline />

      {/* the cover's title, lettered over the dome */}
      {p?.kind === "title" && manifest && (
        <div className="absolute inset-x-0 top-[12%] text-center px-6 pointer-events-none story-fade">
          <p className="uppercase tracking-[0.3em] text-sm sm:text-base opacity-80">{manifest.series}</p>
          <h1 className="mt-2 text-5xl sm:text-7xl font-bold" style={{ fontFamily: "Georgia, serif", textShadow: "0 3px 18px rgba(0,0,0,0.55)" }}>{manifest.title}</h1>
        </div>
      )}

      {/* the words, lighting up as they are read */}
      {captions && p && p.kind !== "title" && (
        <div className={`absolute inset-x-0 bottom-0 px-4 sm:px-10 pt-20 pointer-events-none transition-[padding] duration-500 ${chrome || !playing ? "pb-40" : "pb-8"}`}
             style={{ background: "linear-gradient(to top, rgba(4,6,14,0.82), rgba(4,6,14,0.55) 60%, rgba(4,6,14,0))" }}>
          <p className="mx-auto max-w-5xl text-center leading-snug text-[1.2rem] sm:text-[1.55rem] lg:text-[1.8rem]" style={{ fontFamily: "Georgia, 'Times New Roman', serif", textShadow: "0 2px 8px rgba(0,0,0,0.6)" }}>
            {(() => {
              // the text, with the word being spoken picked out in gold
              const out: (string | React.ReactElement)[] = []; let at = 0;
              const spans = p.words.map(([, , s, e], j) => ({ s, e, j }));
              for (const { s, e, j } of spans) {
                if (s < at) continue;
                out.push(text.slice(at, s));
                out.push(<span key={j} style={{ color: j === word ? "#ffd36b" : j < word ? "#ffffff" : "rgba(255,255,255,0.78)", transition: "color .15s" }}>{text.slice(s, e)}</span>);
                at = e;
              }
              out.push(text.slice(at));
              return out.flatMap((n, i) => typeof n === "string" ? n.split("\n").flatMap((t, k, A) => k < A.length - 1 ? [t, <br key={`b${i}-${k}`} />] : [t]) : [n]);
            })()}
          </p>
        </div>
      )}

      {/* controls: big, few, and out of the way while the story plays */}
      <div className={`absolute inset-x-0 bottom-0 pb-[max(1rem,env(safe-area-inset-bottom))] transition-opacity duration-500 ${chrome || !playing ? "opacity-100" : "opacity-0 pointer-events-none"}`}>
        {manifest && (
          <div className="flex justify-center gap-1.5 mb-3 px-4 flex-wrap">
            {manifest.pages.map((q, i) => (
              <button key={q.id} aria-label={`Page ${i + 1}`} onClick={() => { show(i, true); poke(); }}
                      className="h-3 rounded-full transition-all" style={{ width: i === page ? 28 : 12, background: i === page ? "#ffd36b" : "rgba(255,255,255,0.4)" }} />
            ))}
          </div>
        )}
        <div className="flex items-center justify-center gap-5 sm:gap-8">
          <button aria-label="Previous page" onClick={() => go(-1)} className="story-btn"><Icon d={PREV} /></button>
          <button aria-label={playing ? "Pause" : "Play"} onClick={() => (playing ? pause() : start())} className="story-btn story-btn-big"><Icon d={playing ? PAUSE : PLAY} size={46} /></button>
          <button aria-label="Next page" onClick={() => go(1)} className="story-btn"><Icon d={NEXT} /></button>
        </div>
      </div>
      <div className={`absolute top-0 inset-x-0 flex justify-between p-3 pt-[max(0.75rem,env(safe-area-inset-top))] transition-opacity duration-500 ${chrome || !playing ? "opacity-100" : "opacity-0 pointer-events-none"}`}>
        <button onClick={() => { pause(); onGrownups(); }} className="rounded-full bg-black/40 px-4 py-2.5 text-sm backdrop-blur">For grown-ups</button>
        <div className="flex gap-2">
          <button aria-label="Words on or off" onClick={() => setCaptions((c) => !c)} className={`story-btn !h-12 !w-12 ${captions ? "" : "opacity-50"}`}><Icon d={CC} size={26} /></button>
          <button aria-label="Full screen" onClick={fullscreen} className="story-btn !h-12 !w-12"><Icon d={FULL} size={26} /></button>
        </div>
      </div>

      {/* waiting, starting, and the end */}
      {(!ready || error) && (
        <div className="absolute inset-0 grid place-items-center text-center px-6">
          <div>
            <div className="mx-auto mb-5 h-16 w-16 rounded-full bg-[#faf2d4] shadow-[0_0_60px_rgba(250,242,212,0.6)] story-pulse" />
            <p className="text-xl" style={{ fontFamily: "Georgia, serif" }}>{error ?? "Getting the story ready..."}</p>
          </div>
        </div>
      )}
      {ready && needTap && !playing && (
        <button onClick={start} className="absolute inset-0 grid place-items-center bg-black/35 text-center px-6">
          <div>
            <div className="mx-auto mb-6 grid h-32 w-32 place-items-center rounded-full bg-[#ffd36b] text-[#2a1d0a] shadow-[0_0_80px_rgba(255,211,107,0.55)] story-pulse"><Icon d={PLAY} size={64} /></div>
            <p className="text-3xl sm:text-4xl font-bold" style={{ fontFamily: "Georgia, serif" }}>Tap to start the story</p>
            {manifest && <p className="mt-2 opacity-80">{manifest.title} -- about {Math.round(manifest.runtime / 60)} minutes</p>}
          </div>
        </button>
      )}
      {finished && (
        <div className="absolute inset-0 grid place-items-center text-center px-6 story-dim">
          <div>
            <p className="text-4xl sm:text-5xl font-bold" style={{ fontFamily: "Georgia, serif" }}>Sweet dreams.</p>
            <button onClick={start} className="mt-8 rounded-full bg-white/15 px-6 py-3 text-lg">Hear it again</button>
          </div>
        </div>
      )}
    </div>
  );
}
