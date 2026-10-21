// /mykids: a private bedtime story, opened only by its link (/mykids?k=...). The link is made in the
// Story Studio (Admin -> Stories -> Private link) and can be replaced there at any time, which retires
// the old one. Nothing about the story is in the site's code: its words and narration come from the
// server, and only when the key in the link is the story's current one. A tablet remembers the link,
// so the story opens again from the home screen; search engines are asked to stay away.

import { useEffect, useState } from "react";
import { api } from "../lib/api";
import Storytime, { type Manifest } from "../storytime/Storytime";

const REMEMBER = "storytime.mykids";

export default function MyKids() {
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [aside, setAside] = useState(false);

  useEffect(() => {
    document.title = "Goodnight";
    const meta = document.createElement("meta"); meta.name = "robots"; meta.content = "noindex, nofollow"; document.head.appendChild(meta);
    const q = new URLSearchParams(location.search);
    let key = q.get("k") || "";
    try { if (key) localStorage.setItem(REMEMBER, key); else key = localStorage.getItem(REMEMBER) || ""; } catch { /* private mode */ }
    if (!key) { setError("This page opens with its own link. Ask for it."); return; }
    api<Manifest>(`/stories/by-link/${encodeURIComponent(key)}`).then(setManifest).catch((e) => {
      try { localStorage.removeItem(REMEMBER); } catch { /* fine */ }
      setError((e as Error).message);
    });
    const prev = document.body.style.overflow; document.body.style.overflow = "hidden";
    return () => { meta.remove(); document.body.style.overflow = prev; };
  }, []);

  if (error) {
    return <div className="fixed inset-0 z-[60] grid place-items-center bg-[#05070f] px-6 text-center text-xl text-white" style={{ fontFamily: "Georgia, serif" }}>{error}</div>;
  }
  if (!manifest) {
    return <div className="fixed inset-0 z-[60] grid place-items-center bg-[#05070f] text-white text-xl" style={{ fontFamily: "Georgia, serif" }}>Getting the story ready...</div>;
  }
  return (
    <>
      {!aside && <Storytime manifest={manifest} onGrownups={() => setAside(true)} />}
      {aside && (
        <div className="fixed inset-0 z-[60] grid place-items-center bg-[#05070f] px-6 text-center text-white">
          <div className="max-w-md grid gap-4">
            <p className="text-2xl" style={{ fontFamily: "Georgia, serif" }}>{manifest.title}</p>
            <p className="opacity-80">This story is private. Only people with its link can open it, and the link can be changed at any time.</p>
            <button className="mx-auto rounded-full bg-[#ffd36b] px-6 py-3 text-lg font-semibold text-[#2a1d0a]" onClick={() => setAside(false)}>Back to the story</button>
          </div>
        </div>
      )}
    </>
  );
}
