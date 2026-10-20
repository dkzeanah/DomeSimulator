// @ts-nocheck
// Camera moves for the bedtime stories: the Episode Director's shot library (sketch_claude/static/cine.js),
// ported. Each shot is a function of t in [0, 1] giving the camera's position, target and lens.
const E = {
  linear: (t) => t,
  smooth: (t) => t * t * (3 - 2 * t),
  smoother: (t) => t * t * t * (t * (t * 6 - 15) + 10),
  outCubic: (t) => 1 - Math.pow(1 - t, 3),
  inOutSine: (t) => -(Math.cos(Math.PI * t) - 1) / 2,
};
export const EASE = E;

export function fovForLens(mm) { return 2 * Math.atan(24 / (2 * mm)) * 180 / Math.PI; }   // full-frame, vertical

// ------------------------------------------------------------ the shot library
// Every shot is a function of t in [0, 1] giving the camera's position, target and lens. They are
// built against a subject point and the camera where it is now, so any of them works from anywhere.

export function makeShots(T) {
  const V = (x, y, z) => new T.Vector3(x, y, z);
  const fromTo = (a, b, e = E.smoother) => (t) => a.clone().lerp(b, e(t));
  return {
    dollyIn({ from, subject, dist = 0.45, dur = 5, fov }) {
      const end = subject.clone().lerp(from, dist);
      const p = fromTo(from, end);
      return { dur, at: (t) => ({ pos: p(t), target: subject, fov }) };
    },
    dollyOut({ from, subject, factor = 1.9, dur = 5, fov }) {
      const end = subject.clone().add(from.clone().sub(subject).multiplyScalar(factor));
      const p = fromTo(from, end);
      return { dur, at: (t) => ({ pos: p(t), target: subject, fov }) };
    },
    orbit({ subject, radius = 8, height = 2.5, from = 0, sweep = 120, dur = 8, fov, lift = 0 }) {
      return { dur, at: (t) => {
        const a = (from + sweep * E.inOutSine(t)) * Math.PI / 180;
        return { pos: V(subject.x + Math.cos(a) * radius, subject.y + Math.sin(a) * radius, subject.z + height + lift * t), target: subject, fov };
      } };
    },
    slide({ from, subject, dist = 3, dur = 6, fov }) {
      // a slider: the camera tracks sideways, parallel to the subject, keeping the same aim
      const view = subject.clone().sub(from), side = V(view.y, -view.x, 0).normalize().multiplyScalar(dist);
      const p0 = from.clone().sub(side.clone().multiplyScalar(0.5)), p1 = from.clone().add(side.clone().multiplyScalar(0.5));
      return { dur, at: (t) => { const e = E.smooth(t), off = side.clone().multiplyScalar(e - 0.5); return { pos: p0.clone().lerp(p1, e), target: subject.clone().add(off.multiplyScalar(0.7)), fov }; } };
    },
    pan({ from, subject, sweep = 60, dur = 6, fov }) {
      const v = subject.clone().sub(from), r = Math.hypot(v.x, v.y), a0 = Math.atan2(v.y, v.x) - sweep / 2 * Math.PI / 180;
      return { dur, at: (t) => { const a = a0 + sweep * Math.PI / 180 * E.inOutSine(t); return { pos: from, target: V(from.x + Math.cos(a) * r, from.y + Math.sin(a) * r, subject.z), fov }; } };
    },
    crane({ from, subject, rise = 4, back = 2, dur = 7, fov }) {
      const d = from.clone().sub(subject); d.z = 0; d.normalize();
      const end = from.clone().addScaledVector(d, back); end.z += rise;
      const p = fromTo(from, end);
      return { dur, at: (t) => ({ pos: p(t), target: subject, fov }) };
    },
    pedestal({ from, subject, rise = 2, dur = 5, fov }) {
      const p = fromTo(from, from.clone().add(V(0, 0, rise))), q = fromTo(subject, subject.clone().add(V(0, 0, rise)));
      return { dur, at: (t) => ({ pos: p(t), target: q(t), fov }) };
    },
    dollyZoom({ from, subject, dur = 5, fovFrom = 30, fovTo = 70 }) {
      // the vertigo shot: the camera closes in while the lens widens, the subject stays the same size
      const d0 = from.distanceTo(subject), w = d0 * Math.tan(fovFrom * Math.PI / 360);
      return { dur, at: (t) => {
        const f = fovFrom + (fovTo - fovFrom) * E.smooth(t), d = w / Math.tan(f * Math.PI / 360);
        return { pos: subject.clone().add(from.clone().sub(subject).normalize().multiplyScalar(d)), target: subject, fov: f };
      } };
    },
    reveal({ subject, radius = 7, dur = 7, fov }) {
      // from low behind the deck, rising over it to the whole dome
      return { dur, at: (t) => {
        const e = E.smoother(t), a = (-120 + 40 * e) * Math.PI / 180;
        return { pos: V(subject.x + Math.cos(a) * radius * (1.3 - 0.3 * e), subject.y + Math.sin(a) * radius * (1.3 - 0.3 * e), 0.2 + 3.2 * e),
                 target: V(subject.x, subject.y, subject.z * (0.4 + 0.6 * e)), fov };
      } };
    },
    flyover({ subject, radius = 9, height = 6, dur = 10, fov }) {
      // a drone pass: in low from one side, up over the top, out the other side, banking
      return { dur, at: (t) => {
        const e = E.inOutSine(t), x = -radius + 2 * radius * e;
        return { pos: V(subject.x + x, subject.y - radius * 0.8, subject.z + 1.5 + height * Math.sin(Math.PI * e)),
                 target: V(subject.x + x * 0.25, subject.y, subject.z), fov, roll: Math.sin(Math.PI * 2 * e) * 0.06 };
      } };
    },
    spiral({ subject, radius = 7, height = 7, turns = 0.8, dur = 9, fov }) {
      return { dur, at: (t) => {
        const e = E.smoother(t), a = (turns * 360 * e - 90) * Math.PI / 180, r = radius * (1.2 - 0.5 * e);
        return { pos: V(subject.x + Math.cos(a) * r, subject.y + Math.sin(a) * r, subject.z + height * (1 - e) + 1.2), target: subject, fov };
      } };
    },
    hold({ from, subject, dur = 3, fov, drift = 0.15 }) {
      // a locked-off shot that breathes: a slow push so a static frame never looks frozen
      const end = from.clone().lerp(subject, drift);
      const p = fromTo(from, end, E.linear);
      return { dur, at: (t) => ({ pos: p(t), target: subject, fov }) };
    },
    keys({ keys, dur }) {
      // a camera path through keyframes (Catmull-Rom), each key {pos, target, fov}
      const P = new T.CatmullRomCurve3(keys.map((k) => k.pos), false, "centripetal");
      const Q = new T.CatmullRomCurve3(keys.map((k) => k.target), false, "centripetal");
      return { dur: dur || keys.length * 3, at: (t) => {
        const e = E.smoother(t), i = Math.min(keys.length - 2, Math.floor(e * (keys.length - 1))), f = e * (keys.length - 1) - i;
        const fov = keys[i].fov + ((keys[i + 1]?.fov ?? keys[i].fov) - keys[i].fov) * f;
        return { pos: P.getPoint(e), target: Q.getPoint(e), fov };
      } };
    },
  };
}
