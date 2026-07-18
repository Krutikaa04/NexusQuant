"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { PageHeader, ErrorState, EmptyState } from "@/components/ui";
import { Modal, Field, inputStyle, FormError } from "@/components/Modal";
import { StatusBadge, Tag, LifecycleTimeline, AuditTrail } from "@/components/strategies/bits";
import { IconArrowRight } from "@/components/icons";
import { useApi } from "@/lib/useApi";
import { titleCase } from "@/lib/format";
import {
  StrategyApi,
  healthTone,
  STRATEGY_API,
  type StrategyAudit,
  type StrategyDetail,
} from "@/lib/strategies";

const TABS = ["Overview", "Configuration", "Instruments", "Versions", "Lifecycle", "Health", "Audit"] as const;
type Tab = (typeof TABS)[number];

export default function StrategyDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const router = useRouter();
  const { data, error, loading, refresh } = useApi<StrategyDetail>(`${STRATEGY_API}/${id}`, 6000);
  const audit = useApi<StrategyAudit[]>(`/api-strategies/${id}/audit`, 6000);

  const [tab, setTab] = useState<Tab>("Overview");
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [cloneOpen, setCloneOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  async function run(fn: () => Promise<unknown>) {
    setBusy(true);
    setActionError(null);
    try {
      await fn();
      refresh();
      audit.refresh();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Action failed.");
    } finally {
      setBusy(false);
    }
  }

  if (error && !data) {
    return (
      <>
        <PageHeader title="Strategy" />
        <ErrorState message={error} onRetry={refresh} />
      </>
    );
  }

  if (loading && !data) {
    return (
      <>
        <PageHeader title="Loading strategy…" />
        <div className="panel skeleton" style={{ height: 120, marginBottom: 16 }} />
        <div className="panel skeleton" style={{ height: 260 }} />
      </>
    );
  }

  if (!data) return null;

  return (
    <div>
      <div style={{ marginBottom: 14 }}>
        <Link href="/strategies" className="dim" style={{ fontSize: 12.5 }}>← All strategies</Link>
      </div>

      <PageHeader
        title={data.name}
        subtitle={data.description || "No description provided."}
        badge={<StatusBadge status={data.status} />}
        actions={
          <div className="row gap-8" style={{ flexWrap: "wrap" }}>
            <button className="btn" onClick={() => setCloneOpen(true)} disabled={busy}>Clone</button>
            {!data.is_terminal && (
              <button className="btn btn-ghost" onClick={() => setDeleteOpen(true)} disabled={busy} style={{ color: "var(--down)" }}>
                Delete
              </button>
            )}
          </div>
        }
      />

      {actionError && <div className="fade-in" style={{ marginBottom: 14 }}><FormError message={actionError} /></div>}

      {/* Lifecycle action bar */}
      {data.available_transitions.length > 0 && (
        <div className="panel panel-pad fade-up" style={{ marginBottom: 16 }}>
          <div className="row between" style={{ flexWrap: "wrap", gap: 10 }}>
            <div>
              <div className="card-title">Lifecycle actions</div>
              <div className="dim" style={{ fontSize: 12, marginTop: 3 }}>
                Only legal transitions from <b>{titleCase(data.status)}</b> are shown. Each is audited.
              </div>
            </div>
            <div className="row gap-8" style={{ flexWrap: "wrap" }}>
              {data.available_transitions.map((to) => (
                <button
                  key={to}
                  className={`btn ${to === "retired" ? "btn-ghost" : "btn-primary"}`}
                  style={to === "retired" ? { color: "var(--down)" } : undefined}
                  disabled={busy}
                  onClick={() => run(() => StrategyApi.transition(id, to))}
                >
                  {titleCase(to)} <IconArrowRight width={14} height={14} />
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="row" style={{ gap: 4, marginBottom: 16, borderBottom: "1px solid var(--border)", flexWrap: "wrap" }}>
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className="btn btn-ghost"
            data-active={tab === t}
            style={{
              borderRadius: 0, padding: "9px 14px", fontSize: 13,
              borderBottom: tab === t ? "2px solid var(--accent)" : "2px solid transparent",
              color: tab === t ? "var(--text)" : "var(--text-muted)",
              fontWeight: tab === t ? 600 : 500,
            }}
          >
            {t}
            {t === "Versions" && <span className="dim" style={{ marginLeft: 6, fontSize: 11 }}>{data.version_count}</span>}
          </button>
        ))}
      </div>

      {tab === "Overview" && <OverviewTab data={data} />}
      {tab === "Configuration" && <ConfigTab data={data} />}
      {tab === "Instruments" && <InstrumentsTab data={data} />}
      {tab === "Versions" && <VersionsTab data={data} onRollback={(v) => run(() => StrategyApi.rollback(id, v))} busy={busy} strategyId={id} />}
      {tab === "Lifecycle" && (
        <div className="panel panel-pad fade-up">
          <div className="card-title" style={{ marginBottom: 20 }}>Lifecycle timeline</div>
          <div style={{ overflowX: "auto", paddingBottom: 8 }}>
            <LifecycleTimeline status={data.status} />
          </div>
        </div>
      )}
      {tab === "Health" && <HealthTab data={data} />}
      {tab === "Audit" && (
        <div className="panel panel-pad fade-up">
          <div className="card-title" style={{ marginBottom: 16 }}>Audit log</div>
          <AuditTrail entries={audit.data ?? []} />
        </div>
      )}

      {/* Clone modal */}
      <CloneModal
        open={cloneOpen}
        defaultName={`${data.name} (copy)`}
        busy={busy}
        onClose={() => setCloneOpen(false)}
        onSubmit={async (name) => {
          setBusy(true);
          setActionError(null);
          try {
            const created = await StrategyApi.clone(id, name);
            setCloneOpen(false);
            router.push(`/strategies/${created.id}`);
          } catch (e) {
            setActionError(e instanceof Error ? e.message : "Clone failed.");
          } finally {
            setBusy(false);
          }
        }}
      />

      {/* Delete modal */}
      <Modal title="Delete strategy" open={deleteOpen} onClose={() => setDeleteOpen(false)}>
        <p className="muted" style={{ fontSize: 13.5, lineHeight: 1.6, marginBottom: 16 }}>
          This soft-deletes <b>{data.name}</b>. It will be hidden from all listings but its history is
          retained in the audit trail. This cannot be undone from the UI.
        </p>
        <div className="row" style={{ justifyContent: "flex-end", gap: 10 }}>
          <button className="btn" onClick={() => setDeleteOpen(false)} disabled={busy}>Cancel</button>
          <button
            className="btn btn-primary"
            style={{ background: "var(--down)", borderColor: "var(--down)" }}
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              try {
                await StrategyApi.remove(id);
                router.push("/strategies");
              } catch (e) {
                setActionError(e instanceof Error ? e.message : "Delete failed.");
                setBusy(false);
                setDeleteOpen(false);
              }
            }}
          >
            Delete
          </button>
        </div>
      </Modal>
    </div>
  );
}

// ---- tabs ---------------------------------------------------------------

function MetaRow({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="row between" style={{ padding: "10px 0", borderTop: "1px solid var(--border)" }}>
      <span className="muted" style={{ fontSize: 12.5 }}>{k}</span>
      <span style={{ fontSize: 12.5, fontWeight: 500 }}>{v}</span>
    </div>
  );
}

function OverviewTab({ data }: { data: StrategyDetail }) {
  return (
    <div className="grid fade-up" style={{ gridTemplateColumns: "minmax(0,1.4fr) minmax(0,1fr)", alignItems: "start" }}>
      <div className="panel">
        <div className="panel-pad card-title">Details</div>
        <div style={{ padding: "0 20px 12px" }}>
          <MetaRow k="Owner" v={data.owner} />
          <MetaRow k="Category" v={titleCase(data.category)} />
          <MetaRow k="Status" v={<StatusBadge status={data.status} />} />
          <MetaRow k="Current version" v={`v${data.version}`} />
          <MetaRow k="Versions" v={data.version_count} />
          <MetaRow k="Created" v={data.created_at ? new Date(data.created_at).toLocaleString("en-IN") : "—"} />
          <MetaRow k="Updated" v={data.updated_at ? new Date(data.updated_at).toLocaleString("en-IN") : "—"} />
          {data.tags.length > 0 && (
            <div style={{ paddingTop: 12 }}>
              <div className="row gap-8" style={{ flexWrap: "wrap" }}>{data.tags.map((t) => <Tag key={t}>{t}</Tag>)}</div>
            </div>
          )}
        </div>
      </div>
      <div className="panel panel-pad">
        <div className="card-title" style={{ marginBottom: 14 }}>Health summary</div>
        <HealthGrid data={data} compact />
      </div>
    </div>
  );
}

function KVBlock({ title, obj }: { title: string; obj: Record<string, unknown> | undefined }) {
  const entries = Object.entries(obj ?? {});
  return (
    <div className="panel panel-pad">
      <div className="card-title" style={{ marginBottom: 12 }}>{title}</div>
      {entries.length === 0 ? (
        <div className="dim" style={{ fontSize: 12.5 }}>Not configured.</div>
      ) : (
        <div>
          {entries.map(([k, v]) => (
            <div key={k} className="row between" style={{ padding: "8px 0", borderTop: "1px solid var(--border)" }}>
              <span className="muted mono" style={{ fontSize: 12 }}>{k}</span>
              <span className="mono" style={{ fontSize: 12 }}>{typeof v === "object" ? JSON.stringify(v) : String(v)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ConfigTab({ data }: { data: StrategyDetail }) {
  const c = data.configuration;
  return (
    <div className="grid fade-up" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))" }}>
      <KVBlock title="Entry parameters" obj={c.entry_params as Record<string, unknown>} />
      <KVBlock title="Exit parameters" obj={c.exit_params as Record<string, unknown>} />
      <KVBlock title="Risk parameters" obj={c.risk_params as Record<string, unknown>} />
      <KVBlock title="Position sizing" obj={c.position_sizing as Record<string, unknown>} />
      <KVBlock title="Trading session" obj={c.trading_session as Record<string, unknown>} />
    </div>
  );
}

function Chips({ items }: { items: string[] }) {
  if (!items || items.length === 0) return <span className="dim" style={{ fontSize: 12.5 }}>None</span>;
  return <div className="row gap-8" style={{ flexWrap: "wrap" }}>{items.map((i) => <Tag key={i}>{i}</Tag>)}</div>;
}

function InstrumentsTab({ data }: { data: StrategyDetail }) {
  const si = data.supported_instruments;
  return (
    <div className="panel panel-pad fade-up">
      <div style={{ marginBottom: 18 }}>
        <div className="card-title" style={{ marginBottom: 8 }}>Symbols</div>
        <Chips items={si.symbols} />
      </div>
      <div style={{ marginBottom: 18 }}>
        <div className="card-title" style={{ marginBottom: 8 }}>Exchanges</div>
        <Chips items={si.exchanges} />
      </div>
      <div>
        <div className="card-title" style={{ marginBottom: 8 }}>Timeframes</div>
        <Chips items={si.timeframes} />
      </div>
    </div>
  );
}

function VersionsTab({
  data, onRollback, busy, strategyId,
}: { data: StrategyDetail; onRollback: (v: number) => void; busy: boolean; strategyId: string }) {
  const [diff, setDiff] = useState<{ version: number; fields: string[] } | null>(null);

  async function loadDiff(v: number) {
    try {
      const res = await fetch(`/api-strategies/${strategyId}/compare?a=${v}&b=${data.version}`, { cache: "no-store" });
      const j = await res.json();
      setDiff({ version: v, fields: j.changed_fields ?? [] });
    } catch {
      setDiff({ version: v, fields: [] });
    }
  }

  if (data.versions.length === 0) return <EmptyState title="No versions" />;

  return (
    <div className="panel fade-up">
      <div style={{ overflowX: "auto" }}>
        <table className="table">
          <thead>
            <tr>
              <th className="num">Version</th>
              <th>Change summary</th>
              <th>Author</th>
              <th>Created</th>
              <th style={{ textAlign: "right" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {data.versions.map((v) => {
              const current = v.version === data.version;
              return (
                <tr key={v.id}>
                  <td className="num">
                    v{v.version} {current && <span className="pill pill-info" style={{ padding: "0 7px", marginLeft: 4 }}>current</span>}
                  </td>
                  <td><span style={{ fontSize: 12.5 }}>{v.change_summary || "—"}</span></td>
                  <td><span className="dim mono" style={{ fontSize: 11.5 }}>{v.created_by}</span></td>
                  <td><span className="dim mono" style={{ fontSize: 11.5 }}>{v.created_at ? new Date(v.created_at).toLocaleString("en-IN") : "—"}</span></td>
                  <td style={{ textAlign: "right" }}>
                    <div className="row gap-8" style={{ justifyContent: "flex-end" }}>
                      {!current && (
                        <button className="btn btn-ghost" style={{ padding: "4px 10px", fontSize: 12 }} onClick={() => loadDiff(v.version)}>
                          Diff
                        </button>
                      )}
                      {!current && data.is_editable && (
                        <button className="btn" style={{ padding: "4px 10px", fontSize: 12 }} disabled={busy} onClick={() => onRollback(v.version)}>
                          Rollback
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {diff && (
        <div className="panel-pad" style={{ borderTop: "1px solid var(--border)" }}>
          <div className="card-title" style={{ marginBottom: 8 }}>
            Changes: v{diff.version} → v{data.version}
          </div>
          {diff.fields.length === 0 ? (
            <div className="dim" style={{ fontSize: 12.5 }}>No differences.</div>
          ) : (
            <div className="row gap-8" style={{ flexWrap: "wrap" }}>{diff.fields.map((f) => <Tag key={f}>{f}</Tag>)}</div>
          )}
        </div>
      )}
    </div>
  );
}

function HealthGrid({ data, compact }: { data: StrategyDetail; compact?: boolean }) {
  const h = data.health;
  if (!h) return <div className="dim" style={{ fontSize: 12.5 }}>No health record.</div>;
  const rows: [string, React.ReactNode][] = [
    ["Health score", h.health_score != null ? `${(h.health_score * 100).toFixed(0)}%` : "—"],
    ["Enabled", h.enabled ? <span className="pill pill-up" style={{ padding: "0 8px" }}>Yes</span> : <span className="pill pill-down" style={{ padding: "0 8px" }}>No</span>],
    ["Trading allowed", h.trading_allowed ? <span className="pill pill-up" style={{ padding: "0 8px" }}>Yes</span> : <span className="pill" style={{ padding: "0 8px" }}>No</span>],
    ["Consecutive successes", h.consecutive_successes],
    ["Consecutive failures", h.consecutive_failures],
    ["Last evaluation", h.last_evaluation ? new Date(h.last_evaluation).toLocaleString("en-IN") : "—"],
    ["Last execution", h.last_execution ? new Date(h.last_execution).toLocaleString("en-IN") : "—"],
  ];
  return (
    <div>
      {rows.map(([k, v]) => (
        <div key={k} className="row between" style={{ padding: compact ? "8px 0" : "11px 0", borderTop: "1px solid var(--border)" }}>
          <span className="muted" style={{ fontSize: 12.5 }}>{k}</span>
          <span style={{ fontSize: 12.5, fontWeight: 500 }}>{v}</span>
        </div>
      ))}
    </div>
  );
}

function HealthTab({ data }: { data: StrategyDetail }) {
  const tone = healthTone(data.health?.health_score ?? null);
  return (
    <div className="grid fade-up" style={{ gridTemplateColumns: "minmax(0,1fr) minmax(0,1.3fr)", alignItems: "start" }}>
      <div className="panel panel-pad" style={{ textAlign: "center" }}>
        <div className="card-title" style={{ marginBottom: 16 }}>Health score</div>
        <div className="stat-value" style={{ fontSize: 44, color: tone === "up" ? "var(--up)" : tone === "down" ? "var(--down)" : "var(--text)" }}>
          {data.health?.health_score != null ? `${(data.health.health_score * 100).toFixed(0)}%` : "—"}
        </div>
        <div className="dim" style={{ fontSize: 12, marginTop: 8 }}>
          Populated by downstream validation & execution services.
        </div>
      </div>
      <div className="panel panel-pad">
        <div className="card-title" style={{ marginBottom: 12 }}>Operational health</div>
        <HealthGrid data={data} />
      </div>
    </div>
  );
}

function CloneModal({
  open, defaultName, busy, onClose, onSubmit,
}: { open: boolean; defaultName: string; busy: boolean; onClose: () => void; onSubmit: (name: string) => void }) {
  const [name, setName] = useState(defaultName);
  return (
    <Modal title="Clone strategy" open={open} onClose={onClose}>
      <Field label="New strategy name">
        <input style={inputStyle} value={name} onChange={(e) => setName(e.target.value)} autoFocus />
      </Field>
      <div className="muted" style={{ fontSize: 12.5, lineHeight: 1.6, marginBottom: 16 }}>
        Creates a new <b>Draft</b> strategy with a copy of the current configuration. History is not copied.
      </div>
      <div className="row" style={{ justifyContent: "flex-end", gap: 10 }}>
        <button className="btn" onClick={onClose} disabled={busy}>Cancel</button>
        <button className="btn btn-primary" disabled={busy || !name.trim()} onClick={() => onSubmit(name.trim())}>
          {busy ? "Cloning…" : "Clone"}
        </button>
      </div>
    </Modal>
  );
}
