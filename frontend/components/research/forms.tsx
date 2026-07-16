"use client";

import { useState } from "react";
import { Field, FormError, FormSuccess, inputStyle } from "@/components/Modal";
import { mutate } from "@/lib/research";
import { titleCase } from "@/lib/format";

interface FormProps {
  onDone: () => void;
}

function useSubmit(action: () => Promise<void>, onDone: () => void, successMsg: string) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      await action();
      setSuccess(successMsg);
      setTimeout(onDone, 650); // brief success feedback, then close/refresh
    } catch (e) {
      setError(e instanceof Error ? e.message : "request failed");
    } finally {
      setBusy(false);
    }
  };
  return { busy, error, success, submit };
}

export function NewProjectForm({ onDone }: FormProps) {
  const [name, setName] = useState("");
  const [owner, setOwner] = useState("");
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState("");

  const { busy, error, success, submit } = useSubmit(
    () =>
      mutate("/projects", "POST", {
        name,
        owner,
        description: description || null,
        tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
        metadata: {},
      }).then(() => undefined),
    onDone,
    "Project created."
  );

  return (
    <form onSubmit={(e) => { e.preventDefault(); submit(); }}>
      <FormError message={error} />
      <FormSuccess message={success} />
      <Field label="Project name" hint="Unique across the workspace, min 3 characters.">
        <input style={inputStyle} value={name} onChange={(e) => setName(e.target.value)} placeholder="Cross-Sectional Momentum — NIFTY100" required minLength={3} />
      </Field>
      <Field label="Owner">
        <input style={inputStyle} value={owner} onChange={(e) => setOwner(e.target.value)} placeholder="asha" required />
      </Field>
      <Field label="Description">
        <textarea style={{ ...inputStyle, minHeight: 80, resize: "vertical" }} value={description} onChange={(e) => setDescription(e.target.value)} placeholder="What is this research about?" />
      </Field>
      <Field label="Tags" hint="Comma-separated, e.g. momentum, nifty100">
        <input style={inputStyle} value={tags} onChange={(e) => setTags(e.target.value)} placeholder="momentum, cross-sectional" />
      </Field>
      <button className="btn btn-primary" type="submit" disabled={busy} style={{ width: "100%", justifyContent: "center", marginTop: 4 }}>
        {busy ? "Creating…" : "Create project"}
      </button>
    </form>
  );
}

export function HypothesisForm({ projectId, onDone }: FormProps & { projectId: string }) {
  const [statement, setStatement] = useState("");
  const [criteria, setCriteria] = useState("");
  const [notes, setNotes] = useState("");

  const { busy, error, success, submit } = useSubmit(
    () =>
      mutate("/hypotheses", "POST", {
        project_id: projectId,
        statement,
        success_criteria: criteria,
        notes: notes || null,
      }).then(() => undefined),
    onDone,
    "Hypothesis recorded."
  );

  return (
    <form onSubmit={(e) => { e.preventDefault(); submit(); }}>
      <FormError message={error} />
      <FormSuccess message={success} />
      <Field label="Statement" hint="The falsifiable research question (min 8 characters).">
        <textarea style={{ ...inputStyle, minHeight: 70, resize: "vertical" }} value={statement} onChange={(e) => setStatement(e.target.value)} required minLength={8} placeholder="12-1 momentum ranks predict next-month cross-sectional returns" />
      </Field>
      <Field label="Success criteria" hint="How this hypothesis will be judged.">
        <textarea style={{ ...inputStyle, minHeight: 56, resize: "vertical" }} value={criteria} onChange={(e) => setCriteria(e.target.value)} required minLength={3} placeholder="Rank IC > 0.05 with t-stat > 2.5 over 5y walk-forward" />
      </Field>
      <Field label="Notes (optional)">
        <textarea style={{ ...inputStyle, minHeight: 48, resize: "vertical" }} value={notes} onChange={(e) => setNotes(e.target.value)} />
      </Field>
      <button className="btn btn-primary" type="submit" disabled={busy} style={{ width: "100%", justifyContent: "center" }}>
        {busy ? "Saving…" : "Add hypothesis"}
      </button>
    </form>
  );
}

export function ExperimentForm({ projectId, hypotheses, onDone }: FormProps & {
  projectId: string;
  hypotheses: { id: string; statement: string }[];
}) {
  const [name, setName] = useState("");
  const [dataset, setDataset] = useState("");
  const [feature, setFeature] = useState("");
  const [hypothesisId, setHypothesisId] = useState("");
  const [notes, setNotes] = useState("");

  const { busy, error, success, submit } = useSubmit(
    () =>
      mutate("/experiments", "POST", {
        project_id: projectId,
        name,
        dataset_version: dataset,
        feature_version: feature,
        hypothesis_id: hypothesisId || null,
        notes: notes || null,
      }).then(() => undefined),
    onDone,
    "Experiment registered."
  );

  return (
    <form onSubmit={(e) => { e.preventDefault(); submit(); }}>
      <FormError message={error} />
      <FormSuccess message={success} />
      <Field label="Experiment name">
        <input style={inputStyle} value={name} onChange={(e) => setName(e.target.value)} required minLength={3} placeholder="baseline-12-1-deciles" />
      </Field>
      <div className="grid" style={{ gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <Field label="Dataset version" hint="Explicit, pinned (SPEC-007 §8).">
          <input style={inputStyle} value={dataset} onChange={(e) => setDataset(e.target.value)} required placeholder="nifty100_daily@v3" />
        </Field>
        <Field label="Feature version">
          <input style={inputStyle} value={feature} onChange={(e) => setFeature(e.target.value)} required placeholder="mom_12_1@v1" />
        </Field>
      </div>
      <Field label="Hypothesis (optional)">
        <select style={inputStyle} value={hypothesisId} onChange={(e) => setHypothesisId(e.target.value)}>
          <option value="">— unlinked —</option>
          {hypotheses.map((h) => (
            <option key={h.id} value={h.id}>{h.statement.slice(0, 80)}</option>
          ))}
        </select>
      </Field>
      <Field label="Notes (optional)">
        <textarea style={{ ...inputStyle, minHeight: 48, resize: "vertical" }} value={notes} onChange={(e) => setNotes(e.target.value)} />
      </Field>
      <button className="btn btn-primary" type="submit" disabled={busy} style={{ width: "100%", justifyContent: "center" }}>
        {busy ? "Registering…" : "Register experiment"}
      </button>
    </form>
  );
}

export function ReviewForm({ projectId, onDone }: FormProps & { projectId: string }) {
  const [reviewer, setReviewer] = useState("");
  const [decision, setDecision] = useState("approve");
  const [comments, setComments] = useState("");

  const { busy, error, success, submit } = useSubmit(
    () =>
      mutate("/reviews", "POST", {
        project_id: projectId,
        reviewer,
        decision,
        comments,
      }).then(() => undefined),
    onDone,
    "Review recorded — reviews are immutable once submitted."
  );

  return (
    <form onSubmit={(e) => { e.preventDefault(); submit(); }}>
      <FormError message={error} />
      <FormSuccess message={success} />
      <Field label="Reviewer">
        <input style={inputStyle} value={reviewer} onChange={(e) => setReviewer(e.target.value)} required placeholder="vikram" />
      </Field>
      <Field label="Decision">
        <select style={inputStyle} value={decision} onChange={(e) => setDecision(e.target.value)}>
          {["approve", "reject", "needs_changes"].map((d) => (
            <option key={d} value={d}>{titleCase(d)}</option>
          ))}
        </select>
      </Field>
      <Field label="Comments" hint="Required — the rationale becomes part of the immutable record.">
        <textarea style={{ ...inputStyle, minHeight: 80, resize: "vertical" }} value={comments} onChange={(e) => setComments(e.target.value)} required minLength={3} />
      </Field>
      <button className="btn btn-primary" type="submit" disabled={busy} style={{ width: "100%", justifyContent: "center" }}>
        {busy ? "Recording…" : "Submit review"}
      </button>
    </form>
  );
}

export function TransitionForm({ projectId, toStatus, onDone }: FormProps & {
  projectId: string;
  toStatus: string;
}) {
  const [actor, setActor] = useState("");
  const [note, setNote] = useState("");

  const { busy, error, success, submit } = useSubmit(
    () =>
      mutate(`/projects/${projectId}/transition`, "POST", {
        to_status: toStatus,
        actor,
        note: note || null,
      }).then(() => undefined),
    onDone,
    `Advanced to ${titleCase(toStatus)}.`
  );

  return (
    <form onSubmit={(e) => { e.preventDefault(); submit(); }}>
      <FormError message={error} />
      <FormSuccess message={success} />
      <Field label="Actor" hint="Recorded in the immutable status history.">
        <input style={inputStyle} value={actor} onChange={(e) => setActor(e.target.value)} required placeholder="asha" />
      </Field>
      <Field label="Note (optional)">
        <textarea style={{ ...inputStyle, minHeight: 56, resize: "vertical" }} value={note} onChange={(e) => setNote(e.target.value)} />
      </Field>
      <button className="btn btn-primary" type="submit" disabled={busy} style={{ width: "100%", justifyContent: "center" }}>
        {busy ? "Advancing…" : `Advance to ${titleCase(toStatus)}`}
      </button>
    </form>
  );
}
