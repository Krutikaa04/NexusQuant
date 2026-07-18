"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BrandLockup } from "./Brand";
import { NAV } from "./nav";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside
      style={{
        width: "var(--sidebar-w)",
        borderRight: "1px solid var(--border)",
        background: "var(--bg-1)",
        display: "flex",
        flexDirection: "column",
        position: "sticky",
        top: 0,
        height: "100vh",
      }}
    >
      <div style={{ height: "var(--topbar-h)", display: "flex", alignItems: "center", padding: "0 18px", borderBottom: "1px solid var(--border)" }}>
        <Link href="/dashboard" aria-label="NexusQuant home">
          <BrandLockup />
        </Link>
      </div>

      <nav style={{ flex: 1, overflowY: "auto", padding: "14px 12px" }}>
        {NAV.map((section) => (
          <div key={section.title} style={{ marginBottom: 18 }}>
            <div
              className="dim"
              style={{ fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase", padding: "0 10px 8px", fontWeight: 600 }}
            >
              {section.title}
            </div>
            {section.items.map((item) => {
              const active = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="nav-item"
                  data-active={active}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 11,
                    padding: "9px 10px",
                    borderRadius: 9,
                    marginBottom: 2,
                    color: active ? "var(--text)" : "var(--text-muted)",
                    background: active ? "var(--accent-soft)" : "transparent",
                    fontWeight: active ? 600 : 500,
                    fontSize: 13.5,
                    position: "relative",
                  }}
                >
                  <span style={{ color: active ? "var(--accent)" : "var(--text-dim)", display: "flex" }}>
                    <Icon />
                  </span>
                  <span style={{ flex: 1 }}>{item.label}</span>
                  {item.status === "soon" && (
                    <span className="dim" style={{ fontSize: 9.5, letterSpacing: "0.06em", textTransform: "uppercase", border: "1px solid var(--border-strong)", borderRadius: 5, padding: "1px 5px" }}>
                      Soon
                    </span>
                  )}
                  {active && (
                    <span style={{ position: "absolute", left: -12, top: 8, bottom: 8, width: 3, borderRadius: 3, background: "var(--accent)" }} />
                  )}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      <div style={{ padding: 14, borderTop: "1px solid var(--border)" }}>
        <div className="panel" style={{ padding: 12, borderRadius: 12 }}>
          <div className="row between" style={{ marginBottom: 6 }}>
            <span className="card-title">Build</span>
            <span className="pill pill-up" style={{ padding: "1px 8px" }}><span className="dot" />v0.1</span>
          </div>
          <div className="dim" style={{ fontSize: 11.5, lineHeight: 1.5 }}>
            Markets + Strategy Core live.
          </div>
        </div>
      </div>

      <style>{`.nav-item:hover { background: var(--panel-2) !important; color: var(--text) !important; }`}</style>
    </aside>
  );
}
