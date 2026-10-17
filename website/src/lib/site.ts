// What the home page leads with: one module of the site, chosen on the admin studio page and
// kept in the database (/api/site), so switching it needs no redeploy.

import { useEffect, useState } from "react";
import { api } from "./api";

export const FOCI = [
  { key: "book", label: "The book", to: "/book" },
  { key: "kids", label: "The kids' book", to: "/kids" },
  { key: "domes", label: "Dome classes", to: "/domes" },
  { key: "network", label: "The pad network", to: "/network" },
] as const;
export type Focus = (typeof FOCI)[number]["key"];

export function useFocus() {
  const [focus, setFocus] = useState<Focus | null>(null);
  useEffect(() => { api<{ focus: Focus }>("/site").then((r) => setFocus(r.focus)).catch(() => setFocus("book")); }, []);
  return focus;
}
