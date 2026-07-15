"use client";

import { useApi } from "@/lib/useApi";
import type { SystemInfo } from "@/lib/types";
import { PageHeader, StatCard, ErrorState } from "@/components/ui";
import { titleCase } from "@/lib/format";

export default function SystemPage() {
  const { data, error, refresh } = useApi<SystemInfo>("/api/system", 0);
  const { data: health } = useApi<{ status: string; live_feed: boolean }>("/api/health", 5000);

  if (error && !data) return <><PageHeader title="System" /><ErrorState message={error} onRetry={refresh} /></>;

  const implemented = data?.services.length ?? 0;
  const liveModules = data?.modules.filter((m) => m.status === "live").length ?? 0;

  return (
    <div>
      <PageHeader
        title="System"
        subtitle="Platform service status and the implementation roadmap."
        badge={<span className="pill pill-up"><span className="live-dot" />{health?.status === "ok" ? "Operational" : "…"}</span>}
      />

      <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(210px,1fr))", marginBottom: 20 }}>
        <StatCard label="Backend" value={health?.status === "ok" ? "Operational" : "—"} sub="FastAPI · :8004" tone="up" />
        <StatCard label="Live Feed" value={health?.live_feed ? "Streaming" : "Idle"} sub="Synthetic dev feed" tone={health?.live_feed ? "up" : "neutral"} delay={60} />
        <StatCard label="Services Implemented" value={`${implemented} / 12`} sub="Bounded contexts" delay={120} />
        <StatCard label="Modules Live" value={`${liveModules}`} sub="User-facing surfaces" delay={180} />
      </div>

      <div className="grid" style={{ gridTemplateColumns: "minmax(0,1fr) minmax(0,1fr)", alignItems: "start" }}>
        <div className="panel fade-up">
          <div className="panel-pad card-title">Implemented Services</div>
          <div style={{ padding: "0 6px 8px" }}>
            {data?.services.map((s) => (
              <div key={s.spec} className="row between" style={{ padding: "12px 14px", borderTop: "1px solid var(--border)" }}>
                <div>
                  <div className="row gap-8">
                    <span style={{ fontWeight: 600 }}>{s.name}</span>
                    <span className="pill pill-info" style={{ padding: "0 7px" }}>{s.spec}</span>
                  </div>
                  <div className="dim" style={{ fontSize: 12, marginTop: 3, maxWidth: 360 }}>{s.summary}</div>
                </div>
                <span className="pill pill-up" style={{ padding: "1px 8px" }}><span className="dot" />{titleCase(s.status)}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="panel fade-up">
          <div className="panel-pad card-title">Module Roadmap</div>
          <div style={{ padding: "0 6px 8px" }}>
            {data?.modules.map((m) => (
              <div key={m.spec} className="row between" style={{ padding: "12px 14px", borderTop: "1px solid var(--border)" }}>
                <div>
                  <div className="row gap-8">
                    <span style={{ fontWeight: 600 }}>{m.name}</span>
                    <span className="pill" style={{ padding: "0 7px" }}>{m.spec}</span>
                  </div>
                  <div className="dim" style={{ fontSize: 12, marginTop: 3, maxWidth: 360 }}>{m.summary}</div>
                </div>
                <span className={`pill ${m.status === "live" ? "pill-up" : "pill-warn"}`} style={{ padding: "1px 8px" }}>
                  <span className="dot" />{m.status === "live" ? "Live" : "Planned"}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
