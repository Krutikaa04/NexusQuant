"use client";

import { useState } from "react";
import Link from "next/link";
import { useApi } from "@/lib/useApi";
import { fmtTime, titleCase } from "@/lib/format";
import {
  LIFECYCLE,
  RESEARCH_API,
  type ProjectSummary,
  type ResearchDashboard,
} from "@/lib/research";
import { PageHeader, StatCard, ErrorState, EmptyState, SkeletonRows } from "@/components/ui";
import { Modal } from "@/components/Modal";
import { NewProjectForm } from "@/components/research/forms";
import { StatusPill } from "@/components/research/bits";
import { IconResearch } from "@/components/icons";

export default function ResearchPage() {
  const [createOpen, setCreateOpen] = useState(false);
  const dash = useApi<ResearchDashboard>(`${RESEARCH_API}/dashboard`, 6000);
  const projects = useApi<ProjectSummary[]>(`${RESEARCH_API}/projects`, 6000);

  if (dash.error && !dash.data) {
    return (
      <>
        <PageHeader title="Research OS" />
        <ErrorState message={dash.error} onRetry={dash.refresh} />
      </>
    );
  }

  const stats = dash.data?.stats;
  const inFlight = stats
    ? (stats.by_status.active ?? 0) + (stats.by_status.experimenting ?? 0)
    : 0;

  return (
    <div>
      <PageHeader
        title="Research OS"
        subtitle="The governed workspace — every strategy starts here and earns its way forward."
        badge={<span className="pill pill-info"><span className="dot" />SPEC-007 · Live</span>}
        actions={
          <button className="btn btn-primary" onClick={() => setCreateOpen(true)}>
            + New project
          </button>
        }
      />

      {/* Stats */}
      <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(200px,1fr))", marginBottom: 20 }}>
        <StatCard label="Projects" value={stats?.projects ?? "—"} sub={`${inFlight} in active research`} />
        <StatCard label="Hypotheses" value={stats?.hypotheses ?? "—"} sub="Across live projects" delay={50} />
        <StatCard
          label="Experiments"
          value={stats?.experiments ?? "—"}
          sub={stats ? `${stats.experiments_running} running · ${stats.experiments_completed} completed` : ""}
          tone={stats && stats.experiments_running > 0 ? "up" : "neutral"}
          delay={100}
        />
        <StatCard label="Reviews" value={stats?.reviews ?? "—"} sub="Immutable governance records" delay={150} />
      </div>

      {/* Pipeline distribution */}
      {stats && (
        <div className="panel panel-pad fade-up" style={{ marginBottom: 20 }}>
          <div className="card-title" style={{ marginBottom: 14 }}>Pipeline distribution</div>
          <div className="row" style={{ gap: 10, flexWrap: "wrap" }}>
            {LIFECYCLE.map((stage) => {
              const count = stats.by_status[stage] ?? 0;
              return (
                <div
                  key={stage}
                  className="row gap-8"
                  style={{
                    padding: "7px 12px", borderRadius: 8, fontSize: 12.5,
                    border: "1px solid var(--border)",
                    background: count > 0 ? "var(--accent-soft)" : "var(--bg-2)",
                    color: count > 0 ? "var(--text)" : "var(--text-dim)",
                  }}
                >
                  {titleCase(stage)}
                  <b className="mono" style={{ color: count > 0 ? "var(--accent)" : undefined }}>{count}</b>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="grid" style={{ gridTemplateColumns: "minmax(0,2.2fr) minmax(0,1fr)", alignItems: "start" }}>
        {/* Project cards */}
        <div>
          {projects.loading && !projects.data && (
            <div className="panel"><SkeletonRows rows={6} cols={4} /></div>
          )}
          {projects.data && projects.data.length === 0 && (
            <EmptyState
              title="No research projects yet"
              hint="Create your first project — every strategy begins as governed research."
            />
          )}
          <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(320px,1fr))" }}>
            {projects.data?.map((p, i) => (
              <Link key={p.id} href={`/research/${p.id}`} className="proj-card panel panel-pad fade-up" style={{ animationDelay: `${i * 50}ms`, display: "block" }}>
                <div className="row between" style={{ marginBottom: 10, alignItems: "flex-start", gap: 10 }}>
                  <div style={{ fontWeight: 700, fontSize: 15, lineHeight: 1.35 }}>{p.name}</div>
                  <StatusPill status={p.status} />
                </div>
                <div className="muted" style={{ fontSize: 12.5, lineHeight: 1.6, minHeight: 40, marginBottom: 12, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                  {p.description || "No description."}
                </div>
                <div className="row" style={{ gap: 6, flexWrap: "wrap", marginBottom: 14 }}>
                  {p.tags.map((t) => (
                    <span key={t} className="pill" style={{ padding: "0 8px", fontSize: 10.5 }}>{t}</span>
                  ))}
                </div>
                <div className="row between dim" style={{ fontSize: 11.5, borderTop: "1px solid var(--border)", paddingTop: 10 }}>
                  <span>{p.owner}</span>
                  <span className="mono">
                    {p.hypothesis_count}H · {p.experiment_count}E · {p.review_count}R
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Activity feed */}
        <div className="panel fade-up">
          <div className="panel-pad row between" style={{ paddingBottom: 10 }}>
            <span className="card-title">Recent activity</span>
            <span className="pill pill-up" style={{ padding: "0 8px" }}><span className="live-dot" style={{ width: 6, height: 6 }} />Audit-faithful</span>
          </div>
          <div style={{ maxHeight: 560, overflowY: "auto", padding: "0 8px 10px" }}>
            {dash.data?.activity.length === 0 && (
              <div className="dim" style={{ padding: 20, fontSize: 12.5, textAlign: "center" }}>No activity yet.</div>
            )}
            {dash.data?.activity.map((a, i) => (
              <Link key={`${a.at}-${i}`} href={`/research/${a.project_id}`} className="act-row" style={{ display: "flex", gap: 12, padding: "10px 12px", borderRadius: 8 }}>
                <div style={{
                  width: 30, height: 30, borderRadius: 9, flexShrink: 0,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  background: a.kind === "review" ? "rgba(245,166,35,0.12)" : "var(--accent-soft)",
                  color: a.kind === "review" ? "var(--warn)" : "var(--accent)",
                }}>
                  {a.kind === "review" ? "⚖" : <IconResearch width={14} height={14} />}
                </div>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontSize: 12.5, fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {a.project}
                  </div>
                  <div className="muted" style={{ fontSize: 12 }}>{titleCase(a.detail)}</div>
                  <div className="dim" style={{ fontSize: 10.5, marginTop: 2 }}>
                    {a.actor} · {fmtTime(a.at)}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      <Modal title="New research project" open={createOpen} onClose={() => setCreateOpen(false)}>
        <NewProjectForm
          onDone={() => {
            setCreateOpen(false);
            projects.refresh();
            dash.refresh();
          }}
        />
      </Modal>

      <style>{`
        .proj-card { transition: transform 0.18s ease, border-color 0.2s ease; }
        .proj-card:hover { transform: translateY(-3px); border-color: var(--accent); }
        .act-row:hover { background: var(--panel-2); }
      `}</style>
    </div>
  );
}
