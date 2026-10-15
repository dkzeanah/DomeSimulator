// The page tells its own server it was viewed: path, where the visitor came from (the first
// page of a visit only), and the campaign tags on the link that brought them. Nothing leaves
// for anyone else. The server sets the first-party ids, and skips them when the browser asks
// not to be tracked.

const UTM_KEY = "zl.utm";

function utm(): Record<string, string> {
  const q = new URLSearchParams(location.search);
  const fresh: Record<string, string> = {};
  for (const k of ["source", "medium", "campaign", "content"]) {
    const v = q.get(`utm_${k}`);
    if (v) fresh[k] = v.slice(0, 80);
  }
  try {
    if (Object.keys(fresh).length) sessionStorage.setItem(UTM_KEY, JSON.stringify(fresh));
    return Object.keys(fresh).length ? fresh : JSON.parse(sessionStorage.getItem(UTM_KEY) || "{}");
  } catch {
    return fresh;
  }
}

let first = true;

export function trackView(path: string) {
  const payload = JSON.stringify({ path, ref: first ? document.referrer : "", utm: utm() });
  first = false;
  // an ordinary same-site request, so the first-party cookie it sets is kept -- a beacon's
  // reply cookie is not reliably stored, which would split one visitor in two
  fetch("/api/a", { method: "POST", body: payload, headers: { "Content-Type": "application/json" }, keepalive: true, credentials: "same-origin" })
    .catch(() => undefined);
}
