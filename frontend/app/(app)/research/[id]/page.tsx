"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useApi } from "@/lib/useApi";
import { fmtTime, titleCase } from "@/lib/format";
import {
  RESEARCH_API,
  mutate,
  type ProjectDetail,
  type Transition,
} from "@/lib/research";
import { PageHeader, ErrorState, SkeletonRows, EmptyState } from "@/components/ui";
import { Modal } from "@/components/Modal";
import {
  DecisionPill,
  ExperimentPill,
  LifecycleRail,
  MetricChips,
  StatusPill,
} from "@/components/research/bits";
import {
  ExperimentForm,
  HypothesisForm,
  ReviewForm,
  TransitionForm,
} from "@/components/research/forms";

type ModalKind = null | "hypothesis" | "experiment" | "review" | "transition";

export default function ProjectPage() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;
  const [modal, setModal] = useState<ModalKind>(null);
  const [rowBusy, setRowBusy] = useState<string | null>(null);
  const [rowError, setRowError] = useState<string | null>(null);

  const detail = useApi<ProjectDetail>(`${RESEARCH_API}/projects/${projectId}`, 5000);
  const history = useApi<Transition[]>(`${RESEARCH_API}/projects/${projectId}/history`, 8000);

  const p = detail.data;

  const refreshAll = () => {
    detail.refresh();
    history.refresh();
  };

  const runExperimentAction = async (id: string, action: "start" | "complete") => {
    setRowBusy(id);
    setRowError(null);
    try {
      if (action === "start") {
        await mutate(`/experiments/${id}/start`, "POST");
      } else {
        await mutate(`/experiments/${id}/complete`, "POST", {
          status: "completed",
          metrics: {},
          notes: "Marked complete from the dashboard.",
        });
      }
      refreshAll();
    } catch (e) {
      setRowError(e instanceof Error ? e.message : "action failed");
    } finally {
      setRowBusy(null);
    }
  };

  if (detail.error && !p) {
    return (
      <>
        <PageHeader title="Research Project" />
        <ErrorState message={detail.error} onRetry={detail.refresh} />
      </>
    );
  }

  const frozen = p ? ["approved", "retired"].includes(p.status) : false;
  const nextStatus = p?.allowed_transitions[0];

  return (
    <div>
      <div className="dim fade-up" style={{ fontSize: 12, marginBottom: 10 }}>
        <Link href="/research" style={{ color: "var(--text-muted)" }}>Research OS</Link>
        <span style={{ margin: "0 8px" }}>/</span>
        <span>{p?.name ?? "…"}</span>
      </div>

      <PageHeader
        title={p?.name ?? "Loading…"}
        subtitle={p?.description ?? undefined}
        badge={p && <StatusPill status={p.status} />}
        actions={
          p && (
            <div className="row gap-8">
              {frozen && (
                <span className="pill pill-warn"><span className="dot" />Immutable — research locked</span>
              )}
              {nextStatus && (
                <button className="btn btn-primary" onClick={() => setModal("transition")}>
                  Advance → {titleCase(nextStatus)}
                </button>
              )}
            </div>
          )
        }
      />

      {/* Lifecycle rail */}
      <div className="panel panel-pad fade-up" style={{ marginBottom: 18 }}>
        <div className="row between" style={{ marginBottom: 16, flexWrap: "wrap", gap: 8 }}>
          <span className="card-title">Research lifecycle</span>
          {p && (
            <span className="dim" style={{ fontSize: 11.5 }}>
              Owner <b style={{ color: "var(--text-muted)" }}>{p.owner}</b> · created {p ? fmtTime(p.created_at) : ""}
              {p.tags.length > 0 && <> · {p.tags.join(" · ")}</>}
            </span>
          )}
        </div>
        {p ? <LifecycleRail status={p.status} /> : <div className="skeleton" style={{ height: 60 }} />}
      </div>

      <div className="grid" style={{ gridTemplateColumns: "minmax(0,2.2fr) minmax(0,1fr)", alignItems: "start" }}>
        {/* Left column */}
        <div className="grid" style={{ gridTemplateColumns: "1fr" }}>
          {/* Hypotheses */}
          <div className="panel fade-up">
            <div className="panel-pad row between" style={{ paddingBottom: 10 }}>
              <span className="card-title">Hypotheses</span>
              <button className="btn" disabled={frozen} onClick={() => setModal("hypothesis")} style={{ padding: "6px 12px", fontSize: 12.5 }}>
                + Hypothesis
              </button>
            </div>
            {!p && <SkeletonRows rows={2} cols={3} />}
            {p && p.hypotheses.length === 0 && (
              <div style={{ padding: "0 20px 20px" }}>
                <EmptyState title="No hypotheses yet" hint="A project needs at least one hypothesis before it can activate." />
              </div>
            )}
            {p?.hypotheses.map((h) => (
              <div key={h.id} style={{ padding: "14px 20px", borderTop: "1px solid var(--border)", opacity: h.archived ? 0.5 : 1 }}>
                <div className="row between" style={{ gap: 10, alignItems: "flex-start" }}>
                  <div style={{ fontSize: 13.5, fontWeight: 600, lineHeight: 1.5 }}>{h.statement}</div>
                  {h.archived && <span className="pill" style={{ padding: "0 8px" }}>Archived</span>}
                </div>
                <div className="muted" style={{ fontSize: 12.5, marginTop: 6 }}>
                  <span className="dim">Success:</span> {h.success_criteria}
                </div>
                {h.notes && <div className="dim" style={{ fontSize: 12, marginTop: 4 }}>{h.notes}</div>}
              </div>
            ))}
          </div>

          {/* Experiments */}
          <div className="panel fade-up">
            <div className="panel-pad row between" style={{ paddingBottom: 10 }}>
              <span className="card-title">Experiments</span>
              <button className="btn" disabled={frozen} onClick={() => setModal("experiment")} style={{ padding: "6px 12px", fontSize: 12.5 }}>
                + Experiment
              </button>
            </div>
            {rowError && (
              <div className="down" style={{ padding: "0 20px 10px", fontSize: 12.5 }} role="alert">{rowError}</div>
            )}
            {!p && <SkeletonRows rows={3} cols={5} />}
            {p && p.experiments.length === 0 && (
              <div style={{ padding: "0 20px 20px" }}>
                <EmptyState title="No experiments yet" hint="Experiments pin explicit dataset and feature versions for reproducibility." />
              </div>
            )}
            {p && p.experiments.length > 0 && (
              <div style={{ overflowX: "auto" }}>
                <table className="table">
                  <thead>
                    <tr>
                      <th>Experiment</th>
                      <th>Versions</th>
                      <th>Status</th>
                      <th>Metrics</th>
                      <th style={{ textAlign: "right" }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {p.experiments.map((e) => (
                      <tr key={e.id}>
                        <td>
                          <div style={{ fontWeight: 600 }}>{e.name}</div>
                          <div className="dim" style={{ fontSize: 11 }}>{fmtTime(e.created_at)}</div>
                        </td>
                        <td>
                          <div className="mono" style={{ fontSize: 11.5 }}>{e.dataset_version}</div>
                          <div className="mono dim" style={{ fontSize: 11.5 }}>{e.feature_version}</div>
                        </td>
                        <td><ExperimentPill status={e.status} /></td>
                        <td><MetricChips metrics={e.metrics} /></td>
                        <td style={{ textAlign: "right" }}>
                          {e.status === "pending" && (
                            <button className="btn" disabled={rowBusy === e.id} onClick={() => runExperimentAction(e.id, "start")} style={{ padding: "5px 11px", fontSize: 12 }}>
                              {rowBusy === e.id ? "…" : "Start"}
                            </button>
                          )}
                          {e.status === "running" && (
                            <button className="btn" disabled={rowBusy === e.id} onClick={() => runExperimentAction(e.id, "complete")} style={{ padding: "5px 11px", fontSize: 12 }}>
                              {rowBusy === e.id ? "…" : "Complete"}
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Right column */}
        <div className="grid" style={{ gridTemplateColumns: "1fr" }}>
          {/* Timeline */}
          <div className="panel fade-up">
            <div className="panel-pad card-title" style={{ paddingBottom: 8 }}>Timeline</div>
            <div style={{ padding: "0 20px 16px" }}>
              {!history.data && <SkeletonRows rows={3} cols={2} />}
              {history.data?.slice().reverse().map((t, i) => (
                <div key={i} style={{ display: "flex", gap: 12, position: "relative", paddingBottom: 16 }}>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                    <div style={{ width: 10, height: 10, borderRadius: "50%", background: i === 0 ? "var(--accent)" : "var(--border-strong)", marginTop: 4, flexShrink: 0 }} />
                    <div style={{ width: 2, flex: 1, background: "var(--border)", marginTop: 4 }} />
                  </div>
                  <div style={{ paddingBottom: 2 }}>
                    <div style={{ fontSize: 12.5, fontWeight: 600 }}>
                      {t.from_status ? `${titleCase(t.from_status)} → ${titleCase(t.to_status)}` : "Project created"}
                    </div>
                    <div className="dim" style={{ fontSize: 11 }}>{t.actor} · {fmtTime(t.at)}</div>
                    {t.note && <div className="muted" style={{ fontSize: 11.5, marginTop: 3 }}>{t.note}</div>}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Reviews */}
          <div className="panel fade-up">
            <div className="panel-pad row between" style={{ paddingBottom: 10 }}>
              <span className="card-title">Reviews</span>
              <button className="btn" disabled={p?.status === "retired"} onClick={() => setModal("review")} style={{ padding: "6px 12px", fontSize: 12.5 }}>
                + Review
              </button>
            </div>
            <div style={{ padding: "0 20px 16px" }}>
              {p && p.reviews.length === 0 && (
                <div className="dim" style={{ fontSize: 12.5, padding: "6px 0 10px" }}>
                  No reviews yet. Promotion to Approved requires an approving review at the Production Candidate stage.
                </div>
              )}
              {p?.reviews.map((r) => (
                <div key={r.id} style={{ padding: "12px 0", borderTop: "1px solid var(--border)" }}>
                  <div className="row between" style={{ marginBottom: 6 }}>
                    <span style={{ fontSize: 12.5, fontWeight: 600 }}>{r.reviewer}</span>
                    <DecisionPill decision={r.decision} />
                  </div>
                  <div className="muted" style={{ fontSize: 12.5, lineHeight: 1.55 }}>{r.comments}</div>
                  <div className="dim" style={{ fontSize: 10.5, marginTop: 5 }}>
                    at {titleCase(r.stage)} stage · {fmtTime(r.created_at)} · immutable
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Modals */}
      {p && (
        <>
          <Modal title="Add hypothesis" open={modal === "hypothesis"} onClose={() => setModal(null)}>
            <HypothesisForm projectId={p.id} onDone={() => { setModal(null); refreshAll(); }} />
          </Modal>
          <Modal title="Register experiment" open={modal === "experiment"} onClose={() => setModal(null)}>
            <ExperimentForm
              projectId={p.id}
              hypotheses={p.hypotheses.filter((h) => !h.archived)}
              onDone={() => { setModal(null); refreshAll(); }}
            />
          </Modal>
          <Modal title="Submit review" open={modal === "review"} onClose={() => setModal(null)}>
            <ReviewForm projectId={p.id} onDone={() => { setModal(null); refreshAll(); }} />
          </Modal>
          {nextStatus && (
            <Modal title={`Advance to ${titleCase(nextStatus)}`} open={modal === "transition"} onClose={() => setModal(null)}>
              <TransitionForm projectId={p.id} toStatus={nextStatus} onDone={() => { setModal(null); refreshAll(); }} />
            </Modal>
          )}
        </>
      )}
    </div>
  );
}
