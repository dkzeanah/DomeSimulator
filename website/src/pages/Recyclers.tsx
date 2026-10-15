import { useEffect, useState } from "react";
import { useMeta } from "../lib/meta";
import { Link } from "react-router-dom";
import { ErrorLine, Panel } from "../components/ui";
import { api, money } from "../lib/api";
import { useSession } from "../lib/session";

interface Row { display_name: string; hours: number; cents: number; loads: number }
interface Mine { material: string; quantity: number; unit: string; hours: number; replacement_cents: number; created_at: string }

export default function Recyclers() {
  useMeta("Recyclers: salvage, counted", "Reclaimed timber, sheet goods and fabric for small dome builds, logged with the hours it took and what it would have cost new.", "/recyclers");
  const { me, notify } = useSession();
  const [board, setBoard] = useState<Row[]>([]);
  const [mine, setMine] = useState<Mine[]>([]);
  const [f, setF] = useState({ material: "", quantity: "", unit: "board ft", hours: "", replacementValue: "", note: "" });
  const [error, setError] = useState<string | null>(null);
  const load = () => api<{ board: Row[]; mine: Mine[] }>("/salvage").then((r) => { setBoard(r.board); setMine(r.mine); }).catch(() => undefined);
  useEffect(() => { void load(); }, []);
  async function save(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const r = await api<{ savedPerHourCents: number }>("/salvage", { body: { ...f, quantity: Number(f.quantity), hours: Number(f.hours), replacementValue: Number(f.replacementValue) } });
      notify("Salvage logged", `That hour saved ${money(r.savedPerHourCents)} of new material.`);
      setF({ ...f, material: "", quantity: "", hours: "", replacementValue: "", note: "" });
      void load();
    } catch (err) { setError((err as Error).message); }
  }
  return (
    <div className="mx-auto max-w-6xl px-4 py-10 grid gap-6">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] accent font-semibold">Recyclers</p>
        <h1 className="text-4xl font-bold mt-1">Salvage, counted as account work</h1>
        <p className="muted mt-2 max-w-3xl">Every load reclaimed is logged with the hours it took and what the same material costs new. Divide one by the other and an hour of salvage has a rate, like any other method.</p>
      </div>
      <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
        <Panel title="The board">
          {board.length ? (
            <table className="w-full text-sm num">
              <thead><tr className="muted text-left"><th>Recycler</th><th>Loads</th><th>Hours</th><th>Saved new</th><th>Per hour</th></tr></thead>
              <tbody>{board.map((r) => (
                <tr key={r.display_name} className="border-t" style={{ borderColor: "var(--line)" }}>
                  <td className="py-1.5">{r.display_name}</td><td>{r.loads}</td><td>{r.hours}</td><td>{money(r.cents)}</td><td className="accent">{money(Math.round(r.cents / r.hours))}</td>
                </tr>))}
              </tbody>
            </table>
          ) : <p className="muted">No salvage logged yet. The first load here will be a real one.</p>}
        </Panel>
        <Panel title="Log a load">
          {me ? (
            <form onSubmit={save} className="grid gap-2 text-sm">
              <input className="field" required placeholder="Material, e.g. reclaimed 2x6" value={f.material} onChange={(e) => setF({ ...f, material: e.target.value })} />
              <div className="grid grid-cols-2 gap-2">
                <input className="field" required type="number" step="any" min="0" placeholder="Quantity" value={f.quantity} onChange={(e) => setF({ ...f, quantity: e.target.value })} />
                <input className="field" required placeholder="Unit" value={f.unit} onChange={(e) => setF({ ...f, unit: e.target.value })} />
                <input className="field" required type="number" step="any" min="0.05" placeholder="Hours it took" value={f.hours} onChange={(e) => setF({ ...f, hours: e.target.value })} />
                <input className="field" required type="number" step="any" min="0" placeholder="Cost new ($)" value={f.replacementValue} onChange={(e) => setF({ ...f, replacementValue: e.target.value })} />
              </div>
              <input className="field" placeholder="Where it came from (optional)" value={f.note} onChange={(e) => setF({ ...f, note: e.target.value })} />
              <button className="btn">Log it</button>
              <ErrorLine error={error} />
            </form>
          ) : <p className="text-sm"><Link className="underline" to="/account">Make an account</Link> to log salvage.</p>}
          {mine.length > 0 && <ul className="text-sm mt-4 grid gap-1">{mine.map((m, i) => <li key={i} className="flex justify-between"><span>{m.quantity} {m.unit} {m.material}</span><span className="muted num">{money(m.replacement_cents)}</span></li>)}</ul>}
        </Panel>
      </div>
    </div>
  );
}
