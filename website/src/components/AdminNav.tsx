// The owner's pages, one row of links, with the count of unread notices on Automations.

import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { api } from "../lib/api";

const PAGES: [string, string][] = [
  ["/admin/studio", "Studio"],
  ["/admin", "Backers and orders"],
  ["/admin/analytics", "Analytics"],
  ["/admin/list", "The list and email"],
  ["/admin/users", "Members"],
  ["/admin/ops", "Automations"],
  ["/admin/agents", "Agents and keys"],
];

export default function AdminNav() {
  const [unread, setUnread] = useState(0);
  useEffect(() => { api<{ unread: number }>("/admin/notices/unread").then((r) => setUnread(r.unread)).catch(() => undefined); }, []);
  const cls = ({ isActive }: { isActive: boolean }) => `btn-ghost !py-1.5 !px-3 ${isActive ? "accent font-semibold" : ""}`;
  return (
    <nav className="flex flex-wrap gap-2 text-sm" aria-label="Admin pages">
      {PAGES.map(([to, label]) => (
        <NavLink key={to} end to={to} className={cls}>
          {label}{to === "/admin/ops" && unread > 0 && <span className="ml-1.5 rounded-full px-1.5 text-xs font-semibold" style={{ background: "var(--accent)", color: "var(--bg)" }}>{unread}</span>}
        </NavLink>
      ))}
    </nav>
  );
}
