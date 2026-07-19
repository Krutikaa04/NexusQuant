"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { PageHeader, StatCard, ErrorState, SkeletonRows, EmptyState } from "@/components/ui";
import { Modal } from "@/components/Modal";
import { CreateStrategyForm } from "@/components/strategies/forms";
import { StatusBadge, Tag } from "@/components/strategies/bits";
import { IconStrategy } from "@/components/icons";
import { useApi } from "@/lib/useApi";
import { fmtTime, titleCase } from "@/lib/format";
import { readiness, type DashboardSummary, type StrategySummary } from "@/lib/strategies";

export default function StrategiesPage() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const summary = useApi<DashboardSummary>("/api-strategies/summary", 5000);
  const list = useApi<StrategySummary[]>("/api-strategies", 5000);

  const refresh = () => {
    summary.refresh();
    list.refresh();
  };

  if (list.error && !list.data) {
    return (
      <>
        <PageHeader title="Strategy Studio" />
        <ErrorState message={list.error} onRetry={refresh} />
      </>
    );
  }

  const s = summary.data;
  const rows = list.data ?? [];

  return (
    <div>
      <PageHeader
        title="Strategy Studio"
        subtitle="The core workspace — create, configure, version and manage the lifecycle of every strategy."
        badge={<span className="pill pill-info"><span className="dot" />Strategy Core</span>}
        actions={
          <button className="btn btn-primary" onClick={() => setOpen(true)}>
            <IconStrategy width={16} height={16} /> New strategy
          </button>
        }
      />

      {/* Stat row */}
      <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", marginBottom: 18 }}>
        <StatCard label="Total strategies" value={s ? s.total : "—"} delay={0} />
        <StatCard label="Active" value={s ? s.active : "—"} sub="Not archived" tone={s && s.active > 0 ? "up" : "neutral"} delay={60} />
        <StatCard label="Draft" value={s ? s.draft : "—"} delay={120} />
        <StatCard label="Execution-ready" value={s ? s.ready : "—"} tone={s && s.ready > 0 ? "up" : "neutral"} delay={180} />
        <StatCard label="Archived" value={s ? s.archived : "—"} tone="neutral" delay={240} />
      </div>

      {/* Table */}
      <div className="panel fade-up">
        <div className="row between panel-pad" style={{ paddingBottom: 12 }}>
          <span className="card-title">All strategies</span>
          <span className="dim" style={{ fontSize: 11.5 }}>
            {list.data ? `${rows.length} total · click a row to manage` : ""}
          </span>
        </div>

        {list.loading && !list.data ? (
          <SkeletonRows rows={6} cols={6} />
        ) : rows.length === 0 ? (
          <EmptyState title="No strategies yet" hint="Create your first strategy to begin." />
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Strategy</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th>Readiness</th>
                  <th className="num">Version</th>
                  <th>Last modified</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr
                    key={r.id}
                    onClick={() => router.push(`/strategies/${r.id}`)}
                    style={{ cursor: "pointer" }}
                  >
                    <td>
                      <div style={{ fontWeight: 600, fontSize: 13.5 }}>{r.name}</div>
                      <div className="dim" style={{ fontSize: 11.5, display: "flex", gap: 6, marginTop: 3, flexWrap: "wrap" }}>
                        {r.tags.slice(0, 3).map((t) => <Tag key={t}>{t}</Tag>)}
                      </div>
                    </td>
                    <td><span className="muted" style={{ fontSize: 12.5 }}>{titleCase(r.category)}</span></td>
                    <td><StatusBadge status={r.status} /></td>
                    <td>
                      {(() => {
                        const rd = readiness(r.status);
                        return <span className={`pill ${rd.tone}`} style={{ padding: "1px 9px" }}>{rd.label}</span>;
                      })()}
                    </td>
                    <td className="num">v{r.version}</td>
                    <td><span className="dim mono" style={{ fontSize: 11.5 }}>{r.updated_at ? fmtTime(r.updated_at) : "—"}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Modal title="New strategy" open={open} onClose={() => setOpen(false)} width={680}>
        <CreateStrategyForm
          onCreated={(created) => {
            setOpen(false);
            refresh();
            router.push(`/strategies/${created.id}`);
          }}
        />
      </Modal>
    </div>
  );
}
