import type { ReactNode } from "react";
import { titleCase } from "@/lib/format";
import { LIFECYCLE, statusTone, type StrategyAudit } from "@/lib/strategies";

/** Lifecycle status badge with a semantic tone. */
export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`pill ${statusTone(status)}`}>
      <span className="dot" />
      {titleCase(status)}
    </span>
  );
}

export function Tag({ children }: { children: ReactNode }) {
  return (
    <span
      style={{
        fontSize: 11, padding: "2px 8px", borderRadius: 6,
        border: "1px solid var(--border-strong)", color: "var(--text-muted)",
        background: "var(--bg-2)",
      }}
    >
      {children}
    </span>
  );
}

/** Horizontal lifecycle timeline. Highlights states up to and including the current one. */
export function LifecycleTimeline({ status }: { status: string }) {
  const retired = status === "retired";
  const currentIdx = LIFECYCLE.indexOf(status);
  return (
    <div className="row" style={{ flexWrap: "wrap", gap: 0, alignItems: "stretch" }}>
      {LIFECYCLE.map((s, i) => {
        const done = i < currentIdx || (retired && s === "retired");
        const active = s === status;
        const reached = i <= currentIdx;
        return (
          <div key={s} className="row" style={{ alignItems: "center" }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", minWidth: 78 }}>
              <span
                style={{
                  width: 26, height: 26, borderRadius: "50%",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 11, fontWeight: 700,
                  background: active ? "var(--accent)" : reached ? "var(--accent-soft)" : "var(--panel-2)",
                  color: active ? "#04121a" : reached ? "var(--accent)" : "var(--text-dim)",
                  border: `1px solid ${reached ? "rgba(52,226,196,0.35)" : "var(--border-strong)"}`,
                }}
              >
                {done ? "✓" : i + 1}
              </span>
              <span
                style={{
                  fontSize: 10.5, marginTop: 6, textAlign: "center", lineHeight: 1.2,
                  color: active ? "var(--text)" : "var(--text-dim)",
                  fontWeight: active ? 600 : 500,
                }}
              >
                {titleCase(s)}
              </span>
            </div>
            {i < LIFECYCLE.length - 1 && (
              <span
                style={{
                  width: 22, height: 2, marginTop: -18,
                  background: i < currentIdx ? "var(--accent)" : "var(--border-strong)",
                }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

const ACTION_TONE: Record<string, string> = {
  created: "var(--accent)",
  cloned: "var(--accent)",
  updated: "var(--accent-2)",
  transition: "var(--warn)",
  rollback: "var(--accent-2)",
  deleted: "var(--down)",
};

/** Vertical audit log timeline. */
export function AuditTrail({ entries }: { entries: StrategyAudit[] }) {
  if (entries.length === 0) {
    return <div className="dim" style={{ fontSize: 13, padding: "8px 2px" }}>No audit entries yet.</div>;
  }
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
      {entries.map((e, i) => (
        <div key={e.id} className="row" style={{ gap: 12, alignItems: "stretch" }}>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
            <span style={{ width: 10, height: 10, borderRadius: "50%", background: ACTION_TONE[e.action] ?? "var(--text-dim)", marginTop: 5 }} />
            {i < entries.length - 1 && <span style={{ flex: 1, width: 2, background: "var(--border)" }} />}
          </div>
          <div style={{ paddingBottom: 16 }}>
            <div className="row gap-8" style={{ alignItems: "center" }}>
              <span style={{ fontSize: 13, fontWeight: 600 }}>{titleCase(e.action)}</span>
              {e.from_status && e.to_status && e.action === "transition" && (
                <span className="dim mono" style={{ fontSize: 11.5 }}>
                  {titleCase(e.from_status)} → {titleCase(e.to_status)}
                </span>
              )}
              {e.version != null && <span className="dim" style={{ fontSize: 11 }}>v{e.version}</span>}
            </div>
            {e.detail && <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>{e.detail}</div>}
            <div className="dim mono" style={{ fontSize: 10.5, marginTop: 3 }}>
              {e.actor}{e.created_at ? ` · ${new Date(e.created_at).toLocaleString("en-IN")}` : ""}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
