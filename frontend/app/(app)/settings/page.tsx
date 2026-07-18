"use client";

import { PageHeader } from "@/components/ui";

const SECTIONS = [
  {
    title: "Profile",
    rows: [
      { k: "Name", v: "Portfolio Manager" },
      { k: "Role", v: "Head of Systematic Trading" },
      { k: "Workspace", v: "Trading Desk" },
    ],
  },
  {
    title: "Market Data",
    rows: [
      { k: "Primary exchange", v: "NSE" },
      { k: "Base currency", v: "INR" },
      { k: "Default candle interval", v: "1 minute" },
      { k: "Data feed", v: "Synthetic (development)" },
    ],
  },
  {
    title: "Preferences",
    rows: [
      { k: "Theme", v: "Institutional Dark" },
      { k: "Number format", v: "Indian (en-IN)" },
      { k: "Live refresh", v: "2.5s" },
    ],
  },
];

export default function SettingsPage() {
  return (
    <div>
      <PageHeader title="Settings" subtitle="Workspace, market-data, and interface preferences." />

      <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(300px,1fr))" }}>
        {SECTIONS.map((s, i) => (
          <div key={s.title} className="panel fade-up" style={{ animationDelay: `${i * 60}ms` }}>
            <div className="panel-pad card-title">{s.title}</div>
            <div style={{ padding: "0 20px 16px" }}>
              {s.rows.map((r) => (
                <div key={r.k} className="row between" style={{ padding: "11px 0", borderTop: "1px solid var(--border)" }}>
                  <span className="muted" style={{ fontSize: 13 }}>{r.k}</span>
                  <span style={{ fontSize: 13, fontWeight: 500 }}>{r.v}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="panel panel-pad fade-up" style={{ marginTop: 18 }}>
        <div className="card-title" style={{ marginBottom: 8 }}>About preferences</div>
        <div className="muted" style={{ fontSize: 13, lineHeight: 1.65, maxWidth: 620 }}>
          Settings are presentational in this build. Persistent, per-user configuration (RBAC-scoped)
          arrives with the Governance layer (SPEC-015). The dark institutional theme is the platform default.
        </div>
      </div>
    </div>
  );
}
