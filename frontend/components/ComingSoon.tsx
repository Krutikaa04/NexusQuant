import type { ReactNode } from "react";
import { IconArrowRight } from "./icons";
import { PageHeader } from "./ui";

interface Props {
  title: string;
  spec: string;
  tagline: string;
  description: string;
  capabilities: string[];
  icon: ReactNode;
}

/** A polished placeholder for modules not yet implemented — never a blank screen. */
export function ComingSoon({ title, spec, tagline, description, capabilities, icon }: Props) {
  return (
    <div>
      <PageHeader
        title={title}
        subtitle={tagline}
        badge={<span className="pill pill-warn"><span className="dot" />Coming soon</span>}
      />

      <div className="panel fade-up" style={{ overflow: "hidden" }}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "minmax(0,1.3fr) minmax(0,1fr)",
            gap: 0,
          }}
          className="cs-grid"
        >
          <div style={{ padding: "34px 34px 34px 34px" }}>
            <div className="row gap-12" style={{ marginBottom: 18 }}>
              <div
                style={{
                  width: 52, height: 52, borderRadius: 14,
                  background: "var(--accent-soft)", color: "var(--accent)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  border: "1px solid rgba(52,226,196,0.25)",
                }}
              >
                {icon}
              </div>
              <div>
                <div className="pill pill-info" style={{ marginBottom: 6 }}>{spec}</div>
                <div style={{ fontSize: 15, fontWeight: 600 }}>On the roadmap</div>
              </div>
            </div>

            <p className="muted" style={{ fontSize: 14, lineHeight: 1.7, maxWidth: 520 }}>
              {description}
            </p>

            <div style={{ marginTop: 26 }}>
              <div className="card-title" style={{ marginBottom: 14 }}>Planned capabilities</div>
              <div className="grid" style={{ gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                {capabilities.map((c) => (
                  <div key={c} className="row gap-8" style={{ fontSize: 13.5, color: "var(--text-muted)" }}>
                    <span style={{ color: "var(--accent)", display: "flex" }}><IconArrowRight width={15} height={15} /></span>
                    {c}
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div
            style={{
              borderLeft: "1px solid var(--border)",
              background: "radial-gradient(120% 100% at 100% 0%, rgba(76,141,255,0.10), transparent 60%), var(--bg-1)",
              padding: 34,
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
            }}
          >
            <div className="card-title" style={{ marginBottom: 14 }}>Dependency chain</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {[
                { n: "Event Fabric", done: true },
                { n: "Data Platform", done: true },
                { n: "Market Data", done: true },
                { n: "Strategy Core", done: true },
                { n: title, done: false },
              ].map((s, i) => (
                <div key={i} className="row gap-12">
                  <span
                    style={{
                      width: 22, height: 22, borderRadius: "50%", flexShrink: 0,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: 11, fontWeight: 700,
                      background: s.done ? "var(--accent-soft)" : "var(--panel-2)",
                      color: s.done ? "var(--accent)" : "var(--text-dim)",
                      border: `1px solid ${s.done ? "rgba(52,226,196,0.3)" : "var(--border-strong)"}`,
                    }}
                  >
                    {s.done ? "✓" : i + 1}
                  </span>
                  <span style={{ fontSize: 13.5, color: s.done ? "var(--text-muted)" : "var(--text)", fontWeight: s.done ? 500 : 600 }}>
                    {s.n}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <style>{`@media (max-width: 900px){ .cs-grid{ grid-template-columns: 1fr !important; } .cs-grid > div:last-child{ border-left: none !important; border-top: 1px solid var(--border); } }`}</style>
    </div>
  );
}
