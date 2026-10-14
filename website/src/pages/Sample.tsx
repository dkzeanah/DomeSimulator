import SampleForm from "../components/SampleForm";
import { useMeta } from "../lib/meta";
import { JoinQuest, Panel } from "../components/ui";
import { cabin, sample } from "../lib/facts";

export default function Sample() {
  useMeta("Free sample: The 40 Hour Cabin", `The first ${sample.pages} pages of The 40 Hour Cabin, free: how to build a geodesic dome cabin from split logs, exactly as printed.`, "/sample");
  return (
    <div className="mx-auto max-w-5xl px-4 py-10 grid gap-6 md:grid-cols-[1fr_1fr]">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">Free</p>
        <h1 className="text-4xl font-bold mt-1">The opening of {cabin.title}</h1>
        <p className="muted mt-3">
          {sample.pages} pages, exactly as printed in the {cabin.pages}-page complete edition: the front matter
          ({sample.front.join(", ")}) and {sample.chapters.length} of its {sample.ofChapters} chapters.
        </p>
        <ul className="mt-4 space-y-2">
          {sample.chapters.map((c) => (
            <li key={c.number} className="panel-2 p-3"><span className="muted num mr-2">Ch {c.number}</span>{c.title}</li>
          ))}
        </ul>
        <img src="/img/the-40-hour-cabin-cover.jpg" alt={`${cabin.title} cover`} className="mt-6 w-48 rounded-lg" />
      </div>
      <div className="grid gap-6 content-start">
        <Panel title="Send it to me">
          <SampleForm />
        </Panel>
        <JoinQuest />
      </div>
    </div>
  );
}
