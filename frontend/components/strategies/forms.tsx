"use client";

import { useState } from "react";
import { Field, FormError, inputStyle } from "@/components/Modal";
import { StrategyApi, type CreateStrategyInput, type StrategyDetail } from "@/lib/strategies";

function parseList(v: string): string[] {
  return v.split(",").map((s) => s.trim()).filter(Boolean);
}

function parseJson(v: string): Record<string, unknown> {
  const t = v.trim();
  if (!t) return {};
  return JSON.parse(t) as Record<string, unknown>;
}

/** Create-strategy form. On success, calls onCreated with the new strategy. */
export function CreateStrategyForm({ onCreated }: { onCreated: (s: StrategyDetail) => void }) {
  const [name, setName] = useState("");
  const [category, setCategory] = useState("");
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState("");
  const [symbols, setSymbols] = useState("");
  const [exchanges, setExchanges] = useState("NSE");
  const [timeframes, setTimeframes] = useState("1m");
  const [entry, setEntry] = useState("");
  const [exit, setExit] = useState("");
  const [risk, setRisk] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!name.trim()) {
      setError("Name is required.");
      return;
    }
    let payload: CreateStrategyInput;
    try {
      payload = {
        name: name.trim(),
        description: description.trim(),
        category: category.trim() || undefined,
        tags: parseList(tags),
        config: {
          symbols: parseList(symbols),
          exchanges: parseList(exchanges),
          timeframes: parseList(timeframes),
          entry_params: parseJson(entry),
          exit_params: parseJson(exit),
          risk_params: parseJson(risk),
        },
      };
    } catch {
      setError("Entry / exit / risk parameters must be valid JSON (e.g. {\"rsi_below\": 30}).");
      return;
    }
    setBusy(true);
    try {
      const created = await StrategyApi.create(payload);
      onCreated(created);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create strategy.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit}>
      <FormError message={error} />
      <div className="grid" style={{ gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <Field label="Name">
          <input style={inputStyle} value={name} onChange={(e) => setName(e.target.value)} placeholder="NIFTY Mean Reversion" autoFocus />
        </Field>
        <Field label="Category">
          <input style={inputStyle} value={category} onChange={(e) => setCategory(e.target.value)} placeholder="mean_reversion" />
        </Field>
      </div>
      <Field label="Description">
        <input style={inputStyle} value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Short thesis for this strategy" />
      </Field>
      <Field label="Tags" hint="Comma-separated">
        <input style={inputStyle} value={tags} onChange={(e) => setTags(e.target.value)} placeholder="intraday, rsi" />
      </Field>

      <div className="card-title" style={{ margin: "6px 0 12px" }}>Configuration</div>
      <div className="grid" style={{ gridTemplateColumns: "1fr 1fr 1fr", gap: 14 }}>
        <Field label="Symbols" hint="Comma-separated">
          <input style={inputStyle} value={symbols} onChange={(e) => setSymbols(e.target.value)} placeholder="RELIANCE, TCS" />
        </Field>
        <Field label="Exchanges">
          <input style={inputStyle} value={exchanges} onChange={(e) => setExchanges(e.target.value)} />
        </Field>
        <Field label="Timeframes">
          <input style={inputStyle} value={timeframes} onChange={(e) => setTimeframes(e.target.value)} />
        </Field>
      </div>
      <div className="grid" style={{ gridTemplateColumns: "1fr 1fr 1fr", gap: 14 }}>
        <Field label="Entry params" hint="JSON">
          <input style={inputStyle} value={entry} onChange={(e) => setEntry(e.target.value)} placeholder='{"rsi_below": 30}' />
        </Field>
        <Field label="Exit params" hint="JSON">
          <input style={inputStyle} value={exit} onChange={(e) => setExit(e.target.value)} placeholder='{"rsi_above": 70}' />
        </Field>
        <Field label="Risk params" hint="JSON">
          <input style={inputStyle} value={risk} onChange={(e) => setRisk(e.target.value)} placeholder='{"max_loss_pct": 2}' />
        </Field>
      </div>

      <div className="row" style={{ justifyContent: "flex-end", gap: 10, marginTop: 8 }}>
        <button type="submit" className="btn btn-primary" disabled={busy}>
          {busy ? "Creating…" : "Create strategy"}
        </button>
      </div>
    </form>
  );
}
