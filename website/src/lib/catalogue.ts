// What is for sale, at what price, read from the database (/api/catalogue) -- so a price
// change on the admin page shows everywhere at once, with no redeploy.

import { useEffect, useState } from "react";
import { api } from "./api";

export interface PriceOption { key: string; label: string; amountCents: number; currency: string; honor: boolean; honorPrompt: string | null; gated?: boolean }
export interface Product {
  slug: string; kind: "digital" | "physical" | "service" | "amazon" | "tool"; title: string; subtitle: string; blurb: string; status: string;
  shipsNote: string | null; shipCountries: string[]; externalUrl: string | null; prices: PriceOption[];
}

export function useCatalogue() {
  const [products, setProducts] = useState<Product[] | null>(null);
  useEffect(() => { api<{ products: Product[] }>("/catalogue").then((r) => setProducts(r.products)).catch(() => setProducts([])); }, []);
  return { products, get: (slug: string) => products?.find((p) => p.slug === slug) };
}
