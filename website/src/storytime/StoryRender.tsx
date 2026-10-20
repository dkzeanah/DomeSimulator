// A bedtime story, rendered frame by frame for a film: /storytime-render, driven by
// `py -3.12 -m sketch_claude storytime <slug>` (sketch_claude/storytime_render.py) in a headless
// browser. The world is the player's own (engine.ts, scenes.ts) on a virtual clock -- every frame is
// exactly 1/fps of story time however slow the machine -- and the read-along words, the cover title
// and the page breaths are drawn into each frame the way the player draws them, the spoken word in
// gold. Frames go to the render server in order (the Episode Director's frame pipe); the narration
// and the lullaby are mixed in afterwards from the same manifest, so picture and sound share one clock.
//
//   ?w=1920&h=1080&fps=30            the frame
//   &from=0&to=99                    a run of pages (a rehearsal of a few)
//   &base=N                          the frame number page `from` starts at (a pass resumed after a browser hang)
//   &stills=1                        one still per page instead of the film (checked before a render)

import { useEffect, useRef, useState } from "react";
import { Storyworld } from "./engine";
import { makeScenes, reshoot } from "./scenes";
import type { Manifest, StoryPage } from "./Storytime";

const GAP = 1.4;
const GOLD = "#ffd36b";

/** The page's words laid out like the player's: whole words with their punctuation, centred lines,
 *  the verse's own line breaks kept. Each word knows which narration words fall inside it. */
function layout(g: CanvasRenderingContext2D, p: StoryPage, maxW: number) {
  const toks = [...p.text.matchAll(/\S+/g)].map((m) => ({ s: m.index!, e: m.index! + m[0].length, w: 0 }));
  const lines: typeof toks[] = [[]];
  let width = 0;
  const space = g.measureText(" ").width;
  for (const tok of toks) {
    tok.w = g.measureText(p.text.slice(tok.s, tok.e)).width;
    const prev = lines[lines.length - 1];
    const before = prev.length ? p.text.slice(prev[prev.length - 1].e, tok.s) : "";
    if (prev.length && (before.includes("\n") || width + space + tok.w > maxW)) { lines.push([]); width = 0; }
    const line = lines[lines.length - 1];
    width += (line.length ? space : 0) + tok.w;
    line.push(tok);
  }
  return { lines: lines.filter((l) => l.length), space };
}

function drawWords(g: CanvasRenderingContext2D, W: number, H: number, p: StoryPage, t: number) {
  if (!p.text.trim()) return;
  const unit = Math.min(W, H);
  const size = Math.round(unit * (W >= H ? 0.046 : 0.05));
  g.font = `${size}px Georgia, "Times New Roman", serif`;
  const { lines, space } = layout(g, p, W * (W >= H ? 0.82 : 0.88));
  const lh = size * 1.32, bottom = H - unit * 0.07, top = bottom - lines.length * lh;
  const grad = g.createLinearGradient(0, top - lh * 2.2, 0, H);
  grad.addColorStop(0, "rgba(4,6,14,0)"); grad.addColorStop(0.4, "rgba(4,6,14,0.6)"); grad.addColorStop(1, "rgba(4,6,14,0.88)");
  g.fillStyle = grad; g.fillRect(0, top - lh * 2.2, W, H - top + lh * 2.2);
  // where the narrator is: the character the latest spoken word starts at (none: all bright)
  const narrated = !!p.audio && p.words.length > 0;
  let at = -1;
  if (narrated) for (const w of p.words) { if (w[0] <= t + 0.05) at = w[2]; else break; }
  g.textBaseline = "alphabetic";
  g.shadowColor = "rgba(0,0,0,0.6)"; g.shadowBlur = size * 0.3; g.shadowOffsetY = size * 0.06;
  lines.forEach((line, i) => {
    const lw = line.reduce((n, x) => n + x.w, 0) + space * (line.length - 1);
    let x = (W - lw) / 2;
    const y = top + lh * (i + 0.8);
    for (const tok of line) {
      g.fillStyle = !narrated ? "#ffffff" : at >= tok.s && at < tok.e ? GOLD : tok.e <= at ? "#ffffff" : "rgba(255,255,255,0.72)";
      g.fillText(p.text.slice(tok.s, tok.e), x, y);
      x += tok.w + space;
    }
  });
  g.shadowColor = "transparent"; g.shadowBlur = 0; g.shadowOffsetY = 0;
}

function drawTitle(g: CanvasRenderingContext2D, W: number, H: number, m: Manifest, t: number) {
  const unit = Math.min(W, H), a = Math.min(1, t / 1.6);
  g.save(); g.globalAlpha = a; g.textAlign = "center"; g.fillStyle = "#fff";
  g.shadowColor = "rgba(0,0,0,0.55)"; g.shadowBlur = unit * 0.03;
  g.font = `600 ${Math.round(unit * 0.026)}px Georgia, serif`;
  g.fillText((m.series || "").toUpperCase().split("").join(String.fromCharCode(8202)), W / 2, H * 0.17 + (1 - a) * 8);
  let size = Math.round(unit * (W >= H ? 0.1 : 0.085));
  g.font = `bold ${size}px Georgia, serif`;
  while (g.measureText(m.title).width > W * 0.9 && size > 20) { size -= 4; g.font = `bold ${size}px Georgia, serif`; }
  g.fillText(m.title, W / 2, H * 0.17 + size * 1.25 + (1 - a) * 8);
  g.restore();
}

declare global { interface Window { __story?: { done: boolean; error?: string; frames: number } } }

export default function StoryRender() {
  const glRef = useRef<HTMLCanvasElement>(null);
  const outRef = useRef<HTMLCanvasElement>(null);
  const once = useRef(false);
  const [status, setStatus] = useState("starting");

  useEffect(() => {
    if (once.current) return;
    once.current = true;
    const q = new URLSearchParams(location.search);
    const W = Number(q.get("w") || 1920), H = Number(q.get("h") || 1080), fps = Number(q.get("fps") || 30);
    const stills = q.get("stills") === "1";
    const say = (s: string) => { console.log(`[render] ${s}`); setStatus(s); };
    window.__story = { done: false, frames: 0 };
    (async () => {
      const m: Manifest = await fetch("/render/manifest.json").then((r) => r.json());
      const from = Math.max(0, Number(q.get("from") || 0)), to = Math.min(m.pages.length - 1, Number(q.get("to") ?? m.pages.length - 1));
      const gl = glRef.current!, out = outRef.current!;
      gl.width = W; gl.height = H; out.width = W; out.height = H;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const w = new Storyworld(gl) as Storyworld & Record<string, any>;
      w.renderer.setPixelRatio(1);
      w.resize(W, H);
      w.sun.shadow.mapSize.set(2048, 2048);
      await w.loadDome();
      w.build();
      const scenes = makeScenes(w, m.figures as never) as Record<string, (d: number) => { dur: number }>;
      const g = out.getContext("2d")!;
      let n = Math.max(0, Number(q.get("base") || 0)), inflight: Promise<unknown>[] = [];
      const send = async (blob: Blob, k: number, name?: string) => {
        const url = name ? `/render/still?name=${encodeURIComponent(name)}` : `/render/frame?n=${k}`;
        for (let attempt = 0; ; attempt++) {
          const ac = new AbortController(), timer = setTimeout(() => ac.abort(), 30_000);
          try { const r = await fetch(url, { method: "POST", body: blob, signal: ac.signal }); clearTimeout(timer); if (r.ok) return; throw new Error(String(r.status)); }
          catch (e) { if (attempt > 4) throw e; await new Promise((res) => setTimeout(res, 500)); }
        }
      };
      const shoot = async (k: number, name?: string) => {
        // a frame that will not encode stops the render with a reason, never a silent hang
        const blob: Blob = await Promise.race([
          new Promise<Blob>((res, rej) => out.toBlob((b) => (b ? res(b) : rej(new Error("toBlob gave nothing"))), name ? "image/png" : "image/jpeg", 0.92)),
          new Promise<Blob>((_, rej) => setTimeout(() => rej(new Error(`frame ${k} did not encode in 20 s`)), 20_000)),
        ]);
        const p = send(blob, k, name);
        inflight.push(p);
        if (inflight.length >= 6) { await Promise.all(inflight); inflight = []; }
      };
      const timeline: { id: string; start: number; duration: number }[] = [];
      let at = 0;
      for (let i = from; i <= to; i++) {
        const p = m.pages[i], dur = p.duration + GAP;
        let shot = (scenes[p.scene] || scenes.stars)(dur);
        if (p.shot && p.shot !== "scene") shot = reshoot(w, shot, p.shot, dur) as typeof shot;
        w.play(shot, dur);
        const frames0 = Math.round(dur * fps);
        timeline.push({ id: p.id, start: at, duration: frames0 / fps });
        const frames = Math.round(dur * fps), still = Math.round(frames * 0.6);
        for (let f = 0; f < frames; f++) {
          w.step(1 / fps);
          if (stills && f !== still) continue;
          g.drawImage(gl, 0, 0);
          const t = f / fps;
          if (p.kind === "title") drawTitle(g, W, H, m, t); else drawWords(g, W, H, p, t);
          if (stills) { await shoot(0, `${String(i + 1).padStart(2, "0")}-${p.id}-${p.scene}.png`); break; }
          await shoot(n++);
          if (n % (fps * 5) === 0) say(`page ${i + 1}/${m.pages.length} (${p.id}) frame ${n}`);
        }
        at += Math.round(dur * fps) / fps;          // page starts on frame boundaries, as the soundtrack places them
      }
      await Promise.all(inflight);
      await fetch("/render/done", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ frames: n, fps, timeline }) });
      window.__story = { done: true, frames: n };
      say(`done: ${n} frames`);
      console.log("[render-done]");
    })().catch((e) => {
      window.__story = { done: true, error: String(e), frames: 0 };
      console.log(`[render] failed: ${e}`); console.log("[render-done]");
      fetch("/render/done", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ error: String(e) }) }).catch(() => {});
      setStatus(`failed: ${e}`);
    });
  }, []);

  return (
    <div style={{ background: "#05070f", color: "#fff", minHeight: "100vh", padding: 12, fontFamily: "system-ui" }}>
      <p>Storytime render: {status}</p>
      <canvas ref={glRef} style={{ width: 480, height: "auto", display: "block" }} />
      <canvas ref={outRef} style={{ width: 480, height: "auto", display: "block", marginTop: 8 }} />
    </div>
  );
}
