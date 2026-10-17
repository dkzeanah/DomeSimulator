// Where a buyer lands after paying. The page's address is their receipt and download.
// With `test`, it is also the local stand-in for Stripe's page (TEST_CHECKOUT=1 only).

import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { ErrorLine, Panel } from "../components/ui";
import { api, money } from "../lib/api";
import { useSession } from "../lib/session";

interface Order { ref: string; status: string; amountCents: number; currency: string; email: string; book: { title: string; subtitle: string; kind: string }; downloadUrl: string | null; codebaseUrl: string; bookingNote: string; test: boolean; shipsNote: string | null; honorNote: string | null; fulfillment: string | null; owned: boolean; emailDelivery: string | null }

export default function Thanks({ test = false }: { test?: boolean }) {
  const { ref } = useParams();
  const { me } = useSession();
  const [q] = useSearchParams();
  const key = q.get("key") || "";
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [claimError, setClaimError] = useState<string | null>(null);
  useEffect(() => {
    let live = true;
    let timer: ReturnType<typeof setTimeout>;
    async function load() {
      try {
        const r = await api<{ order: Order }>(`/orders/${ref}?key=${encodeURIComponent(key)}`);
        if (!live) return;
        setOrder(r.order);
        if (r.order.status === "pending") timer = setTimeout(load, 2500);
      } catch (e) { if (live) setError((e as Error).message); }
    }
    void load();
    return () => { live = false; clearTimeout(timer); };
  }, [ref, key, me?.id]);
  // Saved to the signed-in account by itself only when it was bought with that account's
  // address; anyone else viewing the link (the owner helping a buyer) is asked first.
  const claim = () => api<{ order: Order }>(`/orders/${ref}/claim?key=${encodeURIComponent(key)}`, { body: {} })
    .then((r) => setOrder(r.order)).catch((e) => setClaimError(e.message));
  const sameBuyer = Boolean(me && order && me.email.toLowerCase() === (order.email || "").toLowerCase());
  useEffect(() => {
    if (!me || !key || !order || order.status !== "paid" || order.owned || claimError || !sameBuyer) return;
    void claim();
  }, [me?.id, ref, key, order?.status, order?.owned, claimError, sameBuyer]); // eslint-disable-line react-hooks/exhaustive-deps
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
            {order.downloadUrl && <>
              <p>Your book is ready. Download the complete PDF now.</p>
              <a className="btn text-center" href={order.downloadUrl}>Download the book (PDF)</a>
              {order.emailDelivery === "sent" ? <p className="text-sm muted">A download link was emailed to {order.email}.</p>
                : ["queued", "sending"].includes(order.emailDelivery || "") ? <p className="text-sm muted">Your download email is queued for {order.email}. You can download here immediately.</p>
                : <p className="text-sm muted">Your download is available here even if the email does not arrive. Keep this private receipt link.</p>}
            </>}
            {order.codebaseUrl && <a className="btn-ghost text-center" href={order.codebaseUrl}>The codebase</a>}
            {order.bookingNote && <p>{order.bookingNote}</p>}
            {order.book.kind === "digital" && !order.downloadUrl && order.shipsNote && <p className="panel-2 p-3 text-sm">{order.shipsNote}</p>}
            {order.book.kind === "digital" && !order.downloadUrl && !order.shipsNote && <p className="panel-2 p-3 text-sm">Your payment is recorded, but the download is temporarily unavailable. Contact owner@zeanahlab.com with order reference {order.ref}.</p>}
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
      {me ? <p className="mt-4 text-sm"><Link className="underline" to="/account/books">My books</Link>{order.owned ? " — this purchase is saved to your account." : " — your receipt link still gives you access."}
          {!order.owned && !sameBuyer && key && order.status === "paid" && <> <button className="underline" onClick={() => void claim()}>Save it to my account</button> (it was bought with {order.email || "another address"}).</>}</p>
        : <p className="mt-4 text-sm"><Link className="underline" to={`/account?order=${encodeURIComponent(ref || "")}&key=${encodeURIComponent(key)}`}>Sign in or make an account</Link> to save this purchase in My books. An account is optional for downloading.</p>}
      <ErrorLine error={claimError} />
    </div>
  );
}
