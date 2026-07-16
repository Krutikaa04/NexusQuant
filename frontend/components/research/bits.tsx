"use client";

import { titleCase } from "@/lib/format";
import { DECISION_TONE, EXPERIMENT_TONE, LIFECYCLE, STATUS_TONE } from "@/lib/research";

export function StatusPill({ status }: { status: string }) {
  return (
    <span className={`pill ${STATUS_TONE[status] ?? "pill"}`} style={{ padding: "2px 9px" }}>
      <span className="dot" />
      {titleCase(status)}
    </span>
  );
}

export function ExperimentPill({ status }: { status: string }) {
  return (
    <span className={`pill ${EXPERIMENT_TONE[status] ?? "pill"}`} style={{ padding: "1px 8px" }}>
      {status === "running" && <span className="live-dot" style={{ width: 6, height: 6 }} />}
      {titleCase(status)}
    </span>
  );
}

export function DecisionPill({ decision }: { decision: string }) {
  return (
    <span className={`pill ${DECISION_TONE[decision] ?? "pill"}`} style={{ padding: "1px 8px" }}>
      {titleCase(decision)}
    </span>
  );
}

/** Horizontal lifecycle rail — the SPEC-007 state machine as a visual stepper. */
export function LifecycleRail({ status }: { status: string }) {
  const currentIdx = LIFECYCLE.indexOf(status);
  return (
    <div style={{ overflowX: "auto", paddingBottom: 4 }}>
      <div className="row" style={{ gap: 0, minWidth: 700 }}>
        {LIFECYCLE.map((stage, i) => {
          const done = i < currentIdx;
          const current = i === currentIdx;
          return (
            <div key={stage} className="row" style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", flex: 1 }}>
                <div
                  style={{
                    width: 26, height: 26, borderRadius: "50%",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 11, fontWeight: 700, zIndex: 1,
                    background: current
                      ? "linear-gradient(135deg,var(--accent),var(--accent-2))"
                      : done ? "var(--accent-soft)" : "var(--panel-2)",
                    color: current ? "#04121a" : done ? "var(--accent)" : "var(--text-dim)",
                    border: `1.5px solid ${current || done ? "rgba(52,226,196,0.5)" : "var(--border-strong)"}`,
                    boxShadow: current ? "0 0 0 4px rgba(52,226,196,0.15)" : "none",
                    transition: "all 0.3s ease",
                  }}
                >
                  {done ? "✓" : i + 1}
                </div>
                <div
                  className={current ? "" : "dim"}
                  style={{
                    fontSize: 10.5, marginTop: 6, textAlign: "center",
                    fontWeight: current ? 700 : 500,
                    color: current ? "var(--accent)" : undefined,
                    whiteSpace: "nowrap", padding: "0 4px",
                  }}
                >
                  {titleCase(stage)}
                </div>
              </div>
              {i < LIFECYCLE.length - 1 && (
                <div
                  style={{
                    height: 2, flex: 0.6, marginTop: -18,
                    background: i < currentIdx ? "var(--accent)" : "var(--border-strong)",
                    opacity: i < currentIdx ? 0.6 : 1,
                  }}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function MetricChips({ metrics }: { metrics: Record<string, number> }) {
  const entries = Object.entries(metrics);
  if (entries.length === 0) return <span className="dim" style={{ fontSize: 12 }}>—</span>;
  return (
    <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
      {entries.slice(0, 4).map(([k, v]) => (
        <span key={k} className="pill mono" style={{ padding: "1px 8px", fontSize: 11 }}>
          {k} <b style={{ color: "var(--text)" }}>{typeof v === "number" ? v : String(v)}</b>
        </span>
      ))}
    </div>
  );
}
