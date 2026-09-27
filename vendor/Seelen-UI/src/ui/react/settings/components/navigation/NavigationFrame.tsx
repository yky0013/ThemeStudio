// SPDX-License-Identifier: AGPL-3.0-or-later
// Presentation extracted from Seelen's Navigation in this directory.
// Resource/session fetching remains in the original native Navigation adapter.
import { useState } from "preact/hooks";
import type { ComponentChildren } from "preact";
import cs from "./index.module.css";

export interface NavigationItem { id: string; label: string; icon: ComponentChildren }
export function NavigationFrame({ title, items, active, onSelect, footer, collapseLabel }: {
  title: string; items: NavigationItem[]; active: string; onSelect: (id: string) => void; footer: ComponentChildren; collapseLabel: string;
}) {
  const [collapsed, setCollapsed] = useState(false);
  return <nav className={`${cs.navigation} ${collapsed ? cs.collapsed : ""}`} aria-label={title}>
    <button type="button" className={cs.header} onClick={() => setCollapsed(!collapsed)} aria-label={collapseLabel} aria-expanded={!collapsed}>
      <span aria-hidden="true" style={{ fontSize: 24, color: "var(--system-accent-color)" }}>◈</span><h1>{title}</h1><span className={cs.chevron}>‹</span>
    </button>
    <div className={cs.body}><div className={cs.group}>{items.map((item) => <a key={item.id} href={`#workbench-${item.id}`} title={collapsed ? item.label : undefined}
      className={`${cs.item} ${active === item.id ? cs.active : ""}`} aria-current={active === item.id ? "location" : undefined}
      onClick={(event) => { event.preventDefault(); onSelect(item.id); }}>
      <div className={cs.iconWrapper} style={{ width: 24, justifyContent: "center", fontSize: 18 }}>{item.icon}</div><span className={cs.label}>{item.label}</span>
    </a>)}</div></div><div className={cs.footer}>{collapsed ? "0.1" : footer}</div>
  </nav>;
}
