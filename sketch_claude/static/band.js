// Music and effects, synthesised in the browser: the theme, stings, rimshots, saws and meme hits.
export class Band {
  // ``gate`` decides, cue by cue, whether to sound it now and where to log it (the render's mix
  // replays the log offline). With no gate every cue sounds at once.
  constructor(out, gate = null) {
    this.ac = out.ac; this.out = this.ac.createGain(); this.out.gain.value = 0.55; this.out.connect(out.master);
    this.gate = gate;
    const beat = 60 / 116;
    this.length = { theme: (bars = 2) => (bars * 4 + 2) * beat, sting: () => 60 / 130 * 2.2, scratch: () => 0.5, boom: () => 1.2, airhorn: () => 1.1,
                    pad: (secs = 8) => secs, tension: (secs = 8) => secs, piano: (m = 0) => 6, heart: (secs = 6) => secs, chime: () => 1.6,
                    stomp: () => 0.6, rain: (secs = 10) => secs, snap: () => 0.4 };
    for (const fn of CUES) {
      const real = this[fn].bind(this);
      this[fn] = (...args) => {
        if (this.gate) { this.gate.log(fn, args); if (!this.gate.audible()) return this.length[fn]?.(...args); }
        const r = real(...args);
        return r ?? this.length[fn]?.(...args);
      };
    }
  }
  timeBase() { return this.at ?? this.ac.currentTime; }
  noise(dur) {
    const b = this.ac.createBuffer(1, Math.ceil(this.ac.sampleRate * dur), this.ac.sampleRate), d = b.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    const s = this.ac.createBufferSource(); s.buffer = b; return s;
  }
  env(node, t, a, peak, dec) {
    const g = this.ac.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(peak, t + a);
    g.gain.exponentialRampToValueAtTime(0.0001, t + a + dec); node.connect(g); g.connect(this.out); return g;
  }
  bass(f, t, dur) {
    const o = this.ac.createOscillator(); o.type = "sawtooth"; o.frequency.value = f;
    const lp = this.ac.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.setValueAtTime(1400, t); lp.frequency.exponentialRampToValueAtTime(180, t + dur);
    o.connect(lp); this.env(lp, t, 0.005, 0.5, dur); o.start(t); o.stop(t + dur + 0.05);
  }
  kick(t) { const o = this.ac.createOscillator(); o.frequency.setValueAtTime(120, t); o.frequency.exponentialRampToValueAtTime(40, t + 0.15); this.env(o, t, 0.002, 0.9, 0.2); o.start(t); o.stop(t + 0.3); }
  snare(t, peak = 0.35) { const n = this.noise(0.25), hp = this.ac.createBiquadFilter(); hp.type = "highpass"; hp.frequency.value = 1500; n.connect(hp); this.env(hp, t, 0.002, peak, 0.16); n.start(t); }
  hat(t) { const n = this.noise(0.06), hp = this.ac.createBiquadFilter(); hp.type = "highpass"; hp.frequency.value = 7000; n.connect(hp); this.env(hp, t, 0.001, 0.12, 0.04); n.start(t); }
  crash(t) { const n = this.noise(1.6), hp = this.ac.createBiquadFilter(); hp.type = "highpass"; hp.frequency.value = 4000; n.connect(hp); this.env(hp, t, 0.003, 0.3, 1.4); n.start(t); }
  brass(f, t, dur) {
    for (const det of [-6, 0, 7]) {
      const o = this.ac.createOscillator(); o.type = "square"; o.frequency.value = f; o.detune.value = det;
      const lp = this.ac.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 2200; o.connect(lp);
      this.env(lp, t, 0.03, 0.06, dur); o.start(t); o.stop(t + dur + 0.1);
    }
  }
  // the theme: a slap-bass riff with a horn stab, the sound of a sitcom coming back from the break
  theme(bars = 2) {
    const t0 = this.timeBase() + 0.05, beat = 60 / 116;
    const E1 = 41.2, riff = [[0, E1, 0.18], [0.5, E1, 0.12], [0.75, E1 * 2, 0.1], [1, E1 * 1.189, 0.2], [1.5, E1 * 1.335, 0.2], [2, E1 * 1.498, 0.3],
                             [2.75, E1 * 1.335, 0.12], [3, E1 * 1.189, 0.2], [3.5, E1 * 1.122, 0.2]];
    for (let b = 0; b < bars; b++) {
      const tb = t0 + b * 4 * beat;
      for (const [at, f, d] of riff) this.bass(f * 2, tb + at * beat, d);
      for (let i = 0; i < 8; i++) this.hat(tb + i * beat / 2);
      this.kick(tb); this.kick(tb + 2 * beat); this.snare(tb + beat); this.snare(tb + 3 * beat);
    }
    const end = t0 + bars * 4 * beat;
    this.brass(329.6, end, 0.25); this.brass(392, end + beat * 0.5, 0.25); this.brass(493.9, end + beat, 0.9);
    this.kick(end + beat); this.crash(end + beat);
    return (bars * 4 + 2) * beat;
  }
  sting() { const t = this.timeBase() + 0.02, beat = 60 / 130; this.bass(82.4, t, 0.15); this.bass(98, t + beat / 2, 0.15); this.bass(123.5, t + beat, 0.4); this.brass(493.9, t + beat, 0.5); this.crash(t + beat); return beat * 2.2; }
  rimshot() { const t = this.timeBase() + 0.02; this.snare(t, 0.4); this.snare(t + 0.18, 0.45); this.crash(t + 0.42); }
  saw(dur = 2.2) {
    const t = this.timeBase() + 0.02, o = this.ac.createOscillator(); o.type = "sawtooth";
    o.frequency.setValueAtTime(90, t); o.frequency.exponentialRampToValueAtTime(420, t + 0.6); o.frequency.setValueAtTime(420, t + dur - 0.4); o.frequency.exponentialRampToValueAtTime(120, t + dur);
    const bp = this.ac.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = 900; bp.Q.value = 2; o.connect(bp);
    this.env(bp, t, 0.08, 0.18, dur); o.start(t); o.stop(t + dur + 0.1);
  }
  clatter() { const t = this.timeBase() + 0.01; for (let i = 0; i < 6; i++) { const n = this.noise(0.08), bp = this.ac.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = 600 + Math.random() * 1400; bp.Q.value = 6; n.connect(bp); this.env(bp, t + i * 0.07 + Math.random() * 0.04, 0.002, 0.5, 0.09); n.start(t + i * 0.07); } }
  thud() { const t = this.timeBase() + 0.01; this.kick(t); const n = this.noise(0.3), lp = this.ac.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 300; n.connect(lp); this.env(lp, t, 0.003, 0.6, 0.25); n.start(t); }
  whoosh() { const t = this.timeBase() + 0.01, n = this.noise(0.8), bp = this.ac.createBiquadFilter(); bp.type = "bandpass"; bp.Q.value = 1.5; bp.frequency.setValueAtTime(300, t); bp.frequency.exponentialRampToValueAtTime(3000, t + 0.6); n.connect(bp); this.env(bp, t, 0.2, 0.25, 0.5); n.start(t); }
  // meme hits
  boom() {
    const t = this.timeBase() + 0.01, o = this.ac.createOscillator(); o.type = "sine";
    o.frequency.setValueAtTime(110, t); o.frequency.exponentialRampToValueAtTime(38, t + 0.9);
    const sh = this.ac.createWaveShaper(); const c = new Float32Array(256); for (let i = 0; i < 256; i++) { const x = i / 128 - 1; c[i] = Math.tanh(x * 3); } sh.curve = c;
    o.connect(sh); this.env(sh, t, 0.004, 0.9, 1.1); o.start(t); o.stop(t + 1.2);
    const n = this.noise(0.25), lp = this.ac.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 500; n.connect(lp); this.env(lp, t, 0.002, 0.5, 0.2); n.start(t);
  }
  scratch() {
    const t = this.timeBase() + 0.01;
    for (const [a, b, d] of [[0, 0.16, 1], [0.18, 0.34, -1]]) {
      const n = this.noise(0.2), bp = this.ac.createBiquadFilter(); bp.type = "bandpass"; bp.Q.value = 4;
      bp.frequency.setValueAtTime(d > 0 ? 400 : 2400, t + a); bp.frequency.exponentialRampToValueAtTime(d > 0 ? 2400 : 300, t + b);
      n.connect(bp); this.env(bp, t + a, 0.01, 0.7, b - a); n.start(t + a);
    }
  }
  airhorn() {
    const t = this.timeBase() + 0.01;
    for (const [s, d] of [[0, 0.18], [0.24, 0.18], [0.48, 0.55]]) for (const f of [415, 466, 554]) {
      const o = this.ac.createOscillator(); o.type = "sawtooth"; o.frequency.value = f;
      const lp = this.ac.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 2600; o.connect(lp);
      this.env(lp, t + s, 0.01, 0.07, d); o.start(t + s); o.stop(t + s + d + 0.05);
    }
  }

  // ---- the drama: beds that sit under a scene, so a quiet moment is never dead air
  chord(mood) {
    // root-position triads and sevenths, by mood, around A2..A4
    return { warm: [220, 277.2, 329.6, 415.3], sad: [220, 261.6, 329.6, 392], tense: [207.7, 246.9, 293.7, 349.2],
             inner: [196, 246.9, 293.7, 370], hope: [261.6, 329.6, 392, 493.9], night: [174.6, 220, 261.6, 329.6] }[mood] || [220, 277.2, 329.6];
  }
  pad(secs = 8, mood = "warm") {
    const t = this.timeBase() + 0.02, notes = this.chord(mood);
    for (const [i, f] of notes.entries()) for (const det of [-7, 7]) {
      const o = this.ac.createOscillator(); o.type = i % 2 ? "triangle" : "sawtooth"; o.frequency.value = f / (i === 0 ? 2 : 1); o.detune.value = det;
      const lp = this.ac.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = mood === "inner" ? 900 : 1300; lp.Q.value = 0.5;
      const g = this.ac.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(0.022, t + Math.min(2.5, secs / 3));
      g.gain.setValueAtTime(0.022, t + Math.max(0.1, secs - 2)); g.gain.linearRampToValueAtTime(0.0001, t + secs);
      o.connect(lp); lp.connect(g); g.connect(this.out); o.start(t); o.stop(t + secs + 0.1);
    }
  }
  tension(secs = 8) {
    // a low drone that pulses, rising a semitone across its length
    const t = this.timeBase() + 0.02, o = this.ac.createOscillator(); o.type = "sawtooth";
    o.frequency.setValueAtTime(55, t); o.frequency.linearRampToValueAtTime(58.3, t + secs);
    const lp = this.ac.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 320;
    const g = this.ac.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(0.09, t + 1.5); g.gain.linearRampToValueAtTime(0.0001, t + secs);
    const lfo = this.ac.createOscillator(); lfo.frequency.value = 1.6; const lg = this.ac.createGain(); lg.gain.value = 0.04; lfo.connect(lg); lg.connect(g.gain);
    o.connect(lp); lp.connect(g); g.connect(this.out); o.start(t); lfo.start(t); o.stop(t + secs + 0.1); lfo.stop(t + secs + 0.1);
  }
  piano(motif = 0) {
    // the family motif: four notes and a held fifth, a little different each time
    const t = this.timeBase() + 0.02, M = [[440, 392, 349.2, 329.6, 261.6], [329.6, 349.2, 392, 440, 523.3], [261.6, 329.6, 293.7, 246.9, 220]][motif % 3];
    M.forEach((f, i) => {
      const at = t + i * 0.55, o = this.ac.createOscillator(), o2 = this.ac.createOscillator(); o.type = "triangle"; o2.type = "sine"; o.frequency.value = f; o2.frequency.value = f * 2;
      const g = this.ac.createGain(); g.gain.setValueAtTime(0.0001, at); g.gain.exponentialRampToValueAtTime(0.12, at + 0.01); g.gain.exponentialRampToValueAtTime(0.0001, at + (i === M.length - 1 ? 3.2 : 1.4));
      o.connect(g); o2.connect(g); g.connect(this.out); o.start(at); o2.start(at); o.stop(at + 3.4); o2.stop(at + 3.4);
    });
  }
  heart(secs = 6) { const t = this.timeBase() + 0.02; for (let b = 0; b < secs / 0.85; b++) { this.kick(t + b * 0.85); this.kick(t + b * 0.85 + 0.2); } }
  chime() {
    const t = this.timeBase() + 0.02;
    [1318.5, 1568, 1975.5, 2637].forEach((f, i) => { const o = this.ac.createOscillator(); o.type = "sine"; o.frequency.value = f; this.env(o, t + i * 0.07, 0.005, 0.06, 1.3); o.start(t + i * 0.07); o.stop(t + 1.6); });
    const n = this.noise(1.2), bp = this.ac.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.setValueAtTime(800, t); bp.frequency.exponentialRampToValueAtTime(6000, t + 1); n.connect(bp); this.env(bp, t, 0.3, 0.12, 0.8); n.start(t);
  }
  stomp() { const t = this.timeBase() + 0.01; this.kick(t); this.kick(t + 0.01); const n = this.noise(0.2), lp = this.ac.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 260; n.connect(lp); this.env(lp, t, 0.002, 0.8, 0.18); n.start(t); }
  rain(secs = 10) {
    const t = this.timeBase() + 0.02, n = this.noise(secs), hp = this.ac.createBiquadFilter(); hp.type = "bandpass"; hp.frequency.value = 2500; hp.Q.value = 0.4;
    const g = this.ac.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(0.18, t + 2); g.gain.linearRampToValueAtTime(0.0001, t + secs);
    n.connect(hp); hp.connect(g); g.connect(this.out); n.start(t);
    const w = this.noise(secs), lp = this.ac.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 400;
    const wg = this.ac.createGain(); wg.gain.setValueAtTime(0.0001, t); wg.gain.linearRampToValueAtTime(0.22, t + 3); wg.gain.linearRampToValueAtTime(0.0001, t + secs); w.connect(lp); lp.connect(wg); wg.connect(this.out); w.start(t);
  }
  snap() { const t = this.timeBase() + 0.01, n = this.noise(0.3), bp = this.ac.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.setValueAtTime(4000, t); bp.frequency.exponentialRampToValueAtTime(300, t + 0.3); n.connect(bp); this.env(bp, t, 0.003, 0.5, 0.28); n.start(t); }
}

export const CUES = ["theme", "sting", "rimshot", "saw", "clatter", "thud", "whoosh", "boom", "scratch", "airhorn",
                     "pad", "tension", "piano", "heart", "chime", "stomp", "rain", "snap"];
