// Where a buyer lands after paying. The page's address is their receipt and download.
// With `test`, it is also the local stand-in for Stripe's page (TEST_CHECKOUT=1 only).

import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { ErrorLine, Panel } from "../components/ui";
import { api, money } from "../lib/api";

interface Order { ref: string; status: string; amountCents: number; currency: string; email: string; book: { title: string; subtitle: string; kind: string }; downloadUrl: string | null; codebaseUrl: string; bookingNote: string; test: boolean; shipsNote: string | null; honorNote: string | null; fulfillment: string | null }

export default function Thanks({ test = false }: { test?: boolean }) {
  const { ref } = useParams();
  const [q] = useSearchParams();
  const key = q.get("key") || "";
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api<{ order: Order }>(`/orders/${ref}?key=${encodeURIComponent(key)}`).then((r) => setOrder(r.order)).catch((e) => setError(e.message));
  }, [ref, key]);
  if (error) return <div className="mx-auto max-w-xl px-4 py-10"><ErrorLine error={error} /></div>;
  if (!order) return <div className="mx-auto max-w-xl px-4 py-10 muted">Loading your order...</div>;
  if (test && order.status !== "paid") {
    return (
      <div className="mx-auto max-w-xl px-4 py-10">
        <Panel kicker="Test checkout - no card" title={`${order.book.title}: ${money(order.amountCents, order.currency)}`}>
          <button className="btn" onClick={async () => { const r = await api<{ order: Order }>(`/orders/${ref}/test-pay?key=${encodeURIComponent(key)}`, { body: {} }); setOrder(r.order); }}>Pay (test)</button>
        </Panel>
      </div>
    );
  }
  return (
    <div className="mx-auto max-w-xl px-4 py-10">
      <Panel kicker={order.status === "paid" ? "Paid - thank you" : "Waiting for the payment to confirm"} title={order.book.title}>
        {order.status === "paid" ? (
          <div className="grid gap-3">
            {order.downloadUrl && <a className="btn text-center" href={order.downloadUrl}>Download the book</a>}
            {order.codebaseUrl && <a className="btn-ghost text-center" href={order.codebaseUrl}>The codebase</a>}
            {order.bookingNote && <p>{order.bookingNote}</p>}
            {order.book.kind === "digital" && !order.downloadUrl && order.shipsNote && <p className="panel-2 p-3 text-sm">{order.shipsNote}</p>}
            {order.book.kind === "physical" && (
              <div className="panel-2 p-3 text-sm grid gap-1">
                <p><b>{order.book.subtitle || order.book.title}</b> -- {order.fulfillment === "shipped" ? "shipped" : order.fulfillment === "printed" ? "printed, shipping soon" : "waiting to be printed"}.</p>
                {order.shipsNote && <p className="muted">{order.shipsNote}</p>}
                {order.honorNote && <p className="muted">Your donation, as you described it: "{order.honorNote}"</p>}
              </div>
            )}
            <p className="text-sm muted">Keep this page's address: it is your receipt and your download link, on any device. {order.email && `Receipt for ${order.email}.`}</p>
          </div>
        ) : <p className="muted">Refresh in a moment. If your card was charged and this does not change, reply to the receipt email.</p>}
      </Panel>
      <p className="mt-4 text-sm"><Link className="underline" to="/account">Make an account</Link> to keep your books in one place.</p>
    </div>
  );
}
