// Admin -> Stories: the Story Studio, where the bedtime stories are written, staged, narrated and
// published -- one iteration at a time.
//
//   Write    every page: its words, where it is set (a scene of the storytime world) and how the
//            camera moves (the Episode Director's shot library), with the story playing beside it.
//   Save     each save is a new version; nothing is overwritten. Any version can be read again,
//            previewed and published, so going back is one click.
//   Narrate  a page's narration is kept by its words, so unchanged pages stay narrated across
//            versions. New words are narrated by the script (Edge TTS, with word timings) or
//            recorded right here in the owner's own voice. Pages without narration yet are read by
//            the tablet's own voice, and the narrator switch lets a grown-up read any of it.
//   Publish /kids reads the published version; saving and publishing land in the audit log and
//            as events (story.version, story.published) automations can act on.

import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import AdminNav from "../components/AdminNav";
import { ErrorLine, Panel } from "../components/ui";
import { api } from "../lib/api";
import { isStaff, useSession } from "../lib/session";
import Storytime, { type Manifest } from "../storytime/Storytime";
import { SCENES, SHOTS } from "../storytime/scenes";

interface Voice { name: string; rate?: string; pitch?: string }
interface Page { id: string; kind?: string; scene: string; shot?: string; text: string }
interface Doc { title: string; series?: string; voice: Voice; figures?: Record<string, unknown>; pages: Page[] }
interface StoryItem { slug: string; title: string; series: string; status: string; liveVersion: number | null; latest: number; versions: number; updatedAt: string }
interface Detail {
  story: { slug: string; title: string; series: string; status: string; liveVersion: number | null };
  versions: { n: number; note: string; author: string; createdAt: string }[];
  version: { n: number; note: string; doc: Doc };
  manifest: Manifest & { narrated: number };
}

const VOICES: { name: string; label: string; rate: string }[] = [
  { name: "en-US-JennyNeural", label: "Jenny (the storyteller), gentle", rate: "-12%" },
  { name: "en-US-AriaNeural", label: "Aria, bright", rate: "-10%" },
  { name: "en-US-AnaNeural", label: "Ana, a child's voice", rate: "-8%" },
  { name: "en-US-GuyNeural", label: "Guy, warm", rate: "-10%" },
  { name: "mine", label: "My own voice (record each page here)", rate: "+0%" },
];
const KINDS = ["intro", "title", "page", "outro"];
const SITE = typeof window !== "undefined" ? window.location.origin : "https://zeanahlab.com";
const day = (iso: string) => new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });

/** A recording's word timings, estimated: each word gets time in proportion to its length. */
function estimateWords(text: string, duration: number): [number, number, number, number][] {
  const toks = [...text.matchAll(/\S+/g)];
  const total = toks.reduce((n, m) => n + m[0].length + 1, 0) || 1;
  const t0 = 0.3, span = Math.max(0.5, duration - 0.7);
  let at = 0;
  return toks.map((m) => {
    const a = t0 + span * at / total; at += m[0].length + 1;
    return [Math.round(a * 1000) / 1000, Math.round((t0 + span * at / total) * 1000) / 1000, m.index!, m.index! + m[0].length];
  });
}

function blobToBase64(b: Blob): Promise<string> {
  return new Promise((res, rej) => { const r = new FileReader(); r.onload = () => res(String(r.result).split(",")[1]); r.onerror = rej; r.readAsDataURL(b); });
}

/** Record one page in the owner's own voice. */
function Recorder({ slug, page, pageKey, voice, onDone, onError }: { slug: string; page: Page; pageKey?: string; voice: string; onDone: () => void; onError: (e: string) => void }) {
  const [state, setState] = useState<"idle" | "recording" | "saving">("idle");
  const rec = useRef<MediaRecorder | null>(null);
  const t0 = useRef(0);
  async function start() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
      const type = ["audio/webm;codecs=opus", "audio/mp4", "audio/ogg"].find((t) => MediaRecorder.isTypeSupported?.(t)) || "";
      const r = new MediaRecorder(stream, type ? { mimeType: type } : undefined);
      const chunks: Blob[] = [];
      r.ondataavailable = (e) => e.data.size && chunks.push(e.data);
      r.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setState("saving");
        try {
          const blob = new Blob(chunks, { type: r.mimeType || "audio/webm" });
          const duration = (performance.now() - t0.current) / 1000;
          await api(`/admin/stories/${slug}/narration`, { body: { key: pageKey, audio: await blobToBase64(blob), contentType: blob.type.split(";")[0], duration: Math.round(duration * 100) / 100, words: estimateWords(page.text, duration), voice } });
          onDone();
        } catch (e) { onError((e as Error).message); }
        setState("idle");
      };
      rec.current = r; t0.current = performance.now(); r.start(); setState("recording");
    } catch (e) { onError(`The microphone is not available: ${(e as Error).message}`); }
  }
  if (!pageKey || !page.text.trim()) return null;
  return state === "recording"
    ? <button type="button" className="btn !py-1 !px-3 text-xs" style={{ background: "var(--color-ember)" }} onClick={() => rec.current?.stop()}>Stop and keep</button>
    : <button type="button" className="btn-ghost !py-1 !px-3 text-xs" disabled={state === "saving"} onClick={start}>{state === "saving" ? "Saving..." : "Record it myself"}</button>;
}

export default function AdminStories() {
  const { me } = useSession();
  const [list, setList] = useState<StoryItem[]>([]);
  const [slug, setSlug] = useState<string | null>(null);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [doc, setDoc] = useState<Doc | null>(null);
  const [dirty, setDirty] = useState(false);
  const [note, setNote] = useState("");
  const [preview, setPreview] = useState<Manifest | null>(null);
  const [jump, setJump] = useState<{ page: number; at: number } | null>(null);
  const [current, setCurrent] = useState(0);
  const [fresh, setFresh] = useState({ slug: "", title: "", from: "" });
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadList = () => api<{ stories: StoryItem[] }>("/admin/stories").then((r) => { setList(r.stories); if (!slug && r.stories[0]) setSlug(r.stories[0].slug); }).catch((e) => setError(e.message));
  const load = (s: string, v?: number) => api<Detail>(`/admin/stories/${s}${v ? `?v=${v}` : ""}`).then((r) => {
    setDetail(r); setDoc(r.version.doc); setPreview(r.manifest); setDirty(false); setNote("");
  }).catch((e) => setError(e.message));
  useEffect(() => { if (isStaff(me)) loadList(); }, [me]);   // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (slug) load(slug); }, [slug]);

  // the preview follows the draft, a moment after the typing stops
  useEffect(() => {
    if (!dirty || !doc || !slug) return;
    const t = window.setTimeout(() => api<Manifest>(`/admin/stories/${slug}/preview`, { body: { doc } }).then(setPreview).catch((e) => setError(e.message)), 900);
    return () => window.clearTimeout(t);
  }, [doc, dirty, slug]);

  const groups = useMemo(() => [...new Set(SCENES.map((s) => s.group))], []);
  if (!isStaff(me)) return <div className="mx-auto max-w-xl px-4 py-10 muted">Admins only.</div>;

  const act = async (fn: () => Promise<unknown>, done: string) => { setError(null); setMsg(null); try { await fn(); setMsg(done); } catch (e) { setError((e as Error).message); } };
  const edit = (fn: (d: Doc) => Doc) => { setDoc((d) => (d ? fn(structuredClone(d)) : d)); setDirty(true); };
  const editPage = (i: number, patch: Partial<Page>) => edit((d) => { d.pages[i] = { ...d.pages[i], ...patch }; if (patch.shot === "scene") delete d.pages[i].shot; return d; });
  const move = (i: number, by: number) => edit((d) => { const j = i + by; if (j < 0 || j >= d.pages.length) return d; [d.pages[i], d.pages[j]] = [d.pages[j], d.pages[i]]; return d; });
  const newId = (d: Doc) => { let k = d.pages.length + 1; while (d.pages.some((p) => p.id === `p${k}`)) k++; return `p${k}`; };
  const addPage = (at: number) => edit((d) => { d.pages.splice(at, 0, { id: newId(d), kind: "page", scene: d.pages[at - 1]?.scene || "town", text: "" }); return d; });
  const dupPage = (i: number) => edit((d) => { d.pages.splice(i + 1, 0, { ...d.pages[i], id: newId(d) }); return d; });
  const dropPage = (i: number) => edit((d) => { d.pages.splice(i, 1); return d; });

  const story = detail?.story;
  const live = story?.liveVersion;
  const shown = detail?.version.n;
  const narrated = preview ? preview.pages.filter((p) => p.audio).length : 0;
  const needs = preview ? preview.pages.filter((p) => !p.audio && p.text.trim()).length : 0;
  const mine = doc?.voice.name === "mine";

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 grid gap-6">
      <h1 className="text-4xl font-bold">Stories</h1>
      <AdminNav />
      <p className="muted max-w-3xl">
        The bedtime stories at <Link className="underline" to="/kids">/kids</Link>. Write a page, see it played beside you, save it as a new version
        (nothing is ever overwritten), narrate what changed, and publish. The children's page reads the published version.
      </p>
      {msg && <p className="accent">{msg}</p>}
      <ErrorLine error={error} />

      <div className="grid gap-6 lg:grid-cols-[17rem_1fr]">
        {/* ---------------------------------------------------------------- the stories */}
        <div className="grid gap-4 content-start">
          <Panel title="The stories">
            <ul className="grid gap-1.5">
              {list.map((s) => (
                <li key={s.slug}>
                  <button className={`w-full text-left panel-2 px-3 py-2 ${s.slug === slug ? "ring-2 ring-[var(--accent)]" : ""}`} onClick={() => setSlug(s.slug)}>
                    <span className="font-semibold block leading-snug">{s.title}</span>
                    <span className="text-xs muted">{s.status === "live" ? `live: v${s.liveVersion}` : s.status} -- {s.versions} version{s.versions === 1 ? "" : "s"}</span>
                  </button>
                </li>
              ))}
              {!list.length && <li className="muted text-sm">No stories yet.</li>}
            </ul>
          </Panel>
          <Panel title="A new story">
            <form className="grid gap-2 text-sm" onSubmit={(e) => {
              e.preventDefault();
              void act(async () => {
                const r = await api<{ slug: string }>("/admin/stories", { body: { slug: fresh.slug, title: fresh.title, from: fresh.from || undefined } });
                setFresh({ slug: "", title: "", from: "" }); await loadList(); setSlug(r.slug);
              }, "Story started as version 1.");
            }}>
              <input className="field" required placeholder="Title" value={fresh.title} onChange={(e) => setFresh({ ...fresh, title: e.target.value, slug: fresh.slug || "" })} />
              <input className="field" required pattern="[a-z0-9][a-z0-9-]{1,58}[a-z0-9]" placeholder="address, e.g. the-lighthouse" value={fresh.slug}
                     onChange={(e) => setFresh({ ...fresh, slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "-") })} />
              <select className="field" value={fresh.from} onChange={(e) => setFresh({ ...fresh, from: e.target.value })}>
                <option value="">Start from the series' hello and goodnight</option>
                {list.map((s) => <option key={s.slug} value={s.slug}>Copy the intro and goodnight of "{s.title}"</option>)}
              </select>
              <p className="text-xs muted">It is set at /kids/{fresh.slug || "address"} once published.</p>
              <button className="btn">Start it</button>
            </form>
          </Panel>
          {detail && (
            <Panel title="Versions">
              <ul className="grid gap-1.5 text-sm max-h-[28rem] overflow-auto">
                {detail.versions.map((v) => (
                  <li key={v.n}>
                    <button className={`w-full text-left panel-2 px-3 py-2 ${v.n === shown ? "ring-2 ring-[var(--accent)]" : ""}`}
                            onClick={() => { if (!dirty || confirm("Leave your unsaved changes?")) void load(detail.story.slug, v.n); }}>
                      <span className="font-semibold">v{v.n}</span>{v.n === live && <span className="ml-2 text-xs accent font-semibold">LIVE</span>}
                      <span className="block text-xs muted">{v.note || "no note"} -- {day(v.createdAt)}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </Panel>
          )}
        </div>

        {/* ---------------------------------------------------------------- the open story */}
        {doc && story && preview && (
          <div className="grid gap-5 content-start min-w-0">
            <div className="grid gap-5 xl:grid-cols-[1fr_1fr] items-start">
              <div className="grid gap-3 xl:sticky xl:top-20">
                <Storytime manifest={preview} embedded jumpTo={jump} onPage={setCurrent} />
                <p className="text-xs muted">
                  The children's player, playing this draft. Gold dots have narration; pale dots are read by the tablet's own voice until they are narrated.
                </p>
              </div>
              <div className="grid gap-4">
                <Panel kicker={`Showing v${shown}${dirty ? " + unsaved changes" : ""}`} title={doc.title}>
                  <div className="grid gap-2 text-sm">
                    <label className="grid gap-0.5 text-xs muted">Title<input className="field" value={doc.title} onChange={(e) => edit((d) => ({ ...d, title: e.target.value }))} /></label>
                    <label className="grid gap-0.5 text-xs muted">Series<input className="field" value={doc.series || ""} onChange={(e) => edit((d) => ({ ...d, series: e.target.value }))} /></label>
                    <label className="grid gap-0.5 text-xs muted">Narrator
                      <select className="field" value={doc.voice.name} onChange={(e) => { const v = VOICES.find((x) => x.name === e.target.value)!; edit((d) => ({ ...d, voice: { name: v.name, rate: v.rate, pitch: "+0Hz" } })); }}>
                        {VOICES.map((v) => <option key={v.name} value={v.name}>{v.label}</option>)}
                        {!VOICES.some((v) => v.name === doc.voice.name) && <option value={doc.voice.name}>{doc.voice.name}</option>}
                      </select></label>
                    <div className="flex flex-wrap gap-2 items-end mt-1">
                      <input className="field flex-1 min-w-[12rem]" placeholder="What changed in this version" value={note} onChange={(e) => setNote(e.target.value)} />
                      <button className="btn" disabled={!dirty} onClick={() => act(async () => {
                        const r = await api<{ n: number }>(`/admin/stories/${story.slug}/versions`, { body: { doc, note } });
                        await load(story.slug, r.n); await loadList();
                      }, "Saved as a new version.")}>Save as v{(detail.versions[0]?.n || 0) + 1}</button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button className="btn-ghost" disabled={dirty || shown === live} onClick={() => act(async () => {
                        await api(`/admin/stories/${story.slug}/publish`, { body: { n: shown } }); await load(story.slug, shown); await loadList();
                      }, `v${shown} is live at /kids${story.slug === "my-own-home" ? "" : `/${story.slug}`}.`)}>{shown === live ? `v${shown} is live` : `Publish v${shown}`}</button>
                      {story.status === "live" && <button className="btn-ghost" onClick={() => act(async () => { await api(`/admin/stories/${story.slug}`, { method: "PATCH", body: { status: "hidden" } }); await loadList(); await load(story.slug, shown); }, "Hidden from /kids.")}>Hide from /kids</button>}
                      {story.status === "hidden" && live && <button className="btn-ghost" onClick={() => act(async () => { await api(`/admin/stories/${story.slug}`, { method: "PATCH", body: { status: "live" } }); await loadList(); await load(story.slug, shown); }, "Back on /kids.")}>Show on /kids again</button>}
                      <a className="btn-ghost" href={story.slug === "my-own-home" ? "/kids" : `/kids/${story.slug}`} target="_blank" rel="noopener">Open /kids</a>
                    </div>
                  </div>
                </Panel>
                <Panel kicker="Narration" title={`${narrated} of ${preview.pages.length} pages narrated`}>
                  {needs === 0 ? <p className="text-sm muted">Every page with words has narration.</p> : mine ? (
                    <p className="text-sm muted">{needs} page{needs === 1 ? "" : "s"} to record. Press "Record it myself" on each, read it the way you would at bedtime, and stop.</p>
                  ) : (
                    <div className="grid gap-2 text-sm">
                      <p className="muted">{needs} page{needs === 1 ? "" : "s"} have new words. Save the version, then narrate it from the project with an agent key that has the <code>stories:write</code> scope (<Link className="underline" to="/admin/agents">Agents and keys</Link>):</p>
                      <code className="panel-2 p-2 text-xs break-all select-all">py -3.12 website/scripts/export_storytime.py {story.slug} --site {SITE}{dirty ? "" : ` --version ${shown}`}</code>
                      <p className="text-xs muted">Or record any page yourself below. Until then the tablet's own voice reads them, and a grown-up can always switch the narrator off and read.</p>
                    </div>
                  )}
                </Panel>
              </div>
            </div>

            {/* ---------------------------------------------------------------- the pages */}
            <Panel title="Pages">
              <ol className="grid gap-3">
                {doc.pages.map((p, i) => {
                  const mp = preview.pages[i];
                  const has = !!mp?.audio && mp.key && mp.text === p.text;
                  return (
                    <li key={i} className={`panel-2 p-3 grid gap-2 ${i === current ? "ring-2 ring-[var(--accent)]" : ""}`}>
                      <div className="flex flex-wrap items-center gap-2 text-xs">
                        <span className="font-semibold text-sm">{i + 1}.</span>
                        <input className="field !w-28 !py-1 text-xs" value={p.id} onChange={(e) => editPage(i, { id: e.target.value.replace(/[^A-Za-z0-9_-]/g, "") })} aria-label="Page name" />
                        <select className="field !w-auto !py-1 text-xs" value={p.kind || "page"} onChange={(e) => editPage(i, { kind: e.target.value })} aria-label="Kind">
                          {KINDS.map((k) => <option key={k}>{k}</option>)}
                        </select>
                        <span className={`rounded-full px-2 py-0.5 ${has ? "accent" : "muted"}`} style={{ border: "1px solid var(--line)" }}>{has ? "narrated" : p.text.trim() ? "needs narration" : "no words"}</span>
                        <span className="ml-auto flex gap-1">
                          <button type="button" className="btn-ghost !py-1 !px-2" onClick={() => setJump({ page: i, at: Date.now() })}>Play</button>
                          <button type="button" className="btn-ghost !py-1 !px-2" onClick={() => move(i, -1)} aria-label="Move up">&uarr;</button>
                          <button type="button" className="btn-ghost !py-1 !px-2" onClick={() => move(i, 1)} aria-label="Move down">&darr;</button>
                          <button type="button" className="btn-ghost !py-1 !px-2" onClick={() => dupPage(i)}>Copy</button>
                          <button type="button" className="btn-ghost !py-1 !px-2" style={{ color: "var(--color-ember)" }} onClick={() => { if (confirm(`Take page ${i + 1} out of this draft?`)) dropPage(i); }}>Remove</button>
                        </span>
                      </div>
                      <div className="grid gap-2 sm:grid-cols-2">
                        <label className="grid gap-0.5 text-xs muted">Where it is set
                          <select className="field !py-1.5 text-sm" value={p.scene} onChange={(e) => editPage(i, { scene: e.target.value })}>
                            {groups.map((g) => <optgroup key={g} label={g}>{SCENES.filter((s) => s.group === g).map((s) => <option key={s.name} value={s.name}>{s.label}</option>)}</optgroup>)}
                          </select></label>
                        <label className="grid gap-0.5 text-xs muted">Camera
                          <select className="field !py-1.5 text-sm" value={p.shot || "scene"} onChange={(e) => editPage(i, { shot: e.target.value })}>
                            {SHOTS.map((s) => <option key={s.name} value={s.name}>{s.label}</option>)}
                          </select></label>
                      </div>
                      <textarea className="field text-base leading-snug" rows={Math.min(8, Math.max(2, p.text.split("\n").length + 1))} value={p.text}
                                style={{ fontFamily: "Georgia, serif" }} placeholder={p.kind === "title" ? "The title, as it is read out" : "What is read on this page"}
                                onChange={(e) => editPage(i, { text: e.target.value })} />
                      <div className="flex flex-wrap items-center gap-2">
                        {has && mp.audio && <audio controls preload="none" src={mp.audio} className="h-8 max-w-full" />}
                        {!dirty && <Recorder slug={story.slug} page={p} pageKey={mp?.key} voice={mine ? "mine" : doc.voice.name}
                                             onDone={() => { setMsg(`Page ${i + 1} recorded.`); void load(story.slug, shown); }} onError={setError} />}
                        {dirty && p.text.trim() && !has && <span className="text-xs muted">Save to record this page.</span>}
                      </div>
                      <button type="button" className="text-xs muted justify-self-start underline" onClick={() => addPage(i + 1)}>+ a page after this one</button>
                    </li>
                  );
                })}
              </ol>
            </Panel>
          </div>
        )}
      </div>
    </div>
  );
}
