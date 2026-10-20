// One clock for everything that moves. Live, it is the wall clock. During an offline render it
// is virtual: time advances one frame at a time, waits resolve on frame boundaries, and so every
// frame of an episode is the same however slow the machine or hidden the window.

export const clock = {
  offline: false,
  t: 0,                      // virtual milliseconds
  timers: [],                // [{at, resolve}]
  now() { return this.offline ? this.t : performance.now(); },
  wait(s) {
    if (!this.offline) return new Promise((r) => setTimeout(r, s * 1000));
    return new Promise((resolve) => this.timers.push({ at: this.t + s * 1000, resolve }));
  },
  // advance virtual time and wake whatever was waiting, then let their promise chains run
  async advance(ms, yields = 4) {
    this.t += ms;
    for (;;) {
      const due = this.timers.filter((w) => w.at <= this.t + 1e-6).sort((a, b) => a.at - b.at);
      if (!due.length) break;
      this.timers = this.timers.filter((w) => !due.includes(w));
      for (const w of due) w.resolve();
      await yieldMany(yields);
    }
    await yieldMany(yields);
  },
};

// microtask-and-message yields that background tabs do not throttle (setTimeout is throttled)
const mc = new MessageChannel();
const q = [];
mc.port1.onmessage = () => q.shift()?.();
export function yieldTask() { return new Promise((r) => { q.push(r); mc.port2.postMessage(0); }); }
async function yieldMany(n = 4) { for (let i = 0; i < n; i++) { await Promise.resolve(); await yieldTask(); } }
