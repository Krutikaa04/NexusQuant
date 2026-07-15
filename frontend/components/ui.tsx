import type { ReactNode } from "react";

export function PageHeader({ title, subtitle, actions, badge }: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  badge?: ReactNode;
}) {
  return (
    <div className="row between fade-up" style={{ marginBottom: 22, flexWrap: "wrap", gap: 12 }}>
      <div>
        <div className="row gap-12" style={{ alignItems: "center" }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em" }}>{title}</h1>
          {badge}
        </div>
        {subtitle && <div className="muted" style={{ marginTop: 4, fontSize: 13.5 }}>{subtitle}</div>}
      </div>
      {actions && <div className="row gap-8">{actions}</div>}
    </div>
  );
}

export function StatCard({ label, value, sub, tone, delay = 0 }: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  tone?: "up" | "down" | "neutral";
  delay?: number;
}) {
  return (
    <div className="panel panel-pad fade-up" style={{ animationDelay: `${delay}ms` }}>
      <div className="card-title">{label}</div>
      <div className="stat-value" style={{ marginTop: 10, color: tone === "up" ? "var(--up)" : tone === "down" ? "var(--down)" : "var(--text)" }}>
        {value}
      </div>
      {sub && <div className="muted" style={{ marginTop: 6, fontSize: 12.5 }}>{sub}</div>}
    </div>
  );
}

export function SkeletonRows({ rows = 6, cols = 5 }: { rows?: number; cols?: number }) {
  return (
    <div style={{ padding: 14 }}>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="row" style={{ gap: 14, padding: "10px 0" }}>
          {Array.from({ length: cols }).map((_, c) => (
            <div key={c} className="skeleton" style={{ height: 16, flex: c === 0 ? 2 : 1, borderRadius: 5 }} />
          ))}
        </div>
      ))}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="panel panel-pad" style={{ textAlign: "center", padding: 40 }}>
      <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 6 }}>Unable to reach the backend</div>
      <div className="muted" style={{ fontSize: 13, marginBottom: 4 }}>
        Make sure the API is running on <span className="mono">:8004</span>.
      </div>
      <div className="dim mono" style={{ fontSize: 12, marginBottom: 16 }}>{message}</div>
      {onRetry && <button className="btn" onClick={onRetry}>Retry</button>}
    </div>
  );
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="panel panel-pad" style={{ textAlign: "center", padding: 40, color: "var(--text-dim)" }}>
      <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text-muted)" }}>{title}</div>
      {hint && <div style={{ fontSize: 12.5, marginTop: 6 }}>{hint}</div>}
    </div>
  );
}
