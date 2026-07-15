"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useApi } from "@/lib/useApi";
import type { Candle, Overview, QualitySnapshot } from "@/lib/types";
import {
  changeClass,
  fmtNum,
  fmtPct,
  readinessTone,
  regimeTone,
  titleCase,
} from "@/lib/format";
import { PageHeader, ErrorState } from "@/components/ui";
import { CandleChart } from "@/components/CandleChart";

const INTERVALS = [
  { label: "1m", v: 60 },
  { label: "5m", v: 300 },
  { label: "15m", v: 900 },
];

interface RegimeResp {
  symbol: string;
  regimes: string[];
  indicators: Record<string, number>;
  as_of?: string;
}

function MarketInner() {
  const params = useSearchParams();
  const router = useRouter();
  const [interval, setInterval] = useState(60);

  const { data: overview } = useApi<Overview>("/api/overview", 4000);
  const universe = overview ? [...overview.indices, ...overview.equities] : [];
  const symbol = params.get("symbol") || "RELIANCE";
  const snap = universe.find((u) => u.symbol === symbol);

  const { data: candles, error } = useApi<Candle[]>(
    `/market/candles?symbol=${symbol}&interval_seconds=${interval}&limit=120`,
    3000
  );
  const { data: quality } = useApi<QualitySnapshot>(`/market/quality?symbol=${symbol}`, 3000);
  const { data: regime } = useApi<RegimeResp>(`/market/regime?symbol=${symbol}`, 5000);

  const setSymbol = (s: string) => router.push(`/market?symbol=${s}`);

  return (
    <div>
      <PageHeader
        title="Market Intelligence"
        subtitle="Immutable time series · data-quality scoring · regime classification (SPEC-004)"
        badge={<span className="pill pill-info"><span className="dot" />SPEC-004 · Live</span>}
      />

      {/* Symbol selector */}
      <div className="row" style={{ gap: 8, flexWrap: "wrap", marginBottom: 18 }}>
        {universe.map((u) => (
          <button
            key={u.symbol}
            onClick={() => setSymbol(u.symbol)}
            className="btn"
            style={{
              padding: "7px 13px",
              fontSize: 12.5,
              borderColor: u.symbol === symbol ? "var(--accent)" : "var(--border-strong)",
              background: u.symbol === symbol ? "var(--accent-soft)" : "var(--panel-2)",
              color: u.symbol === symbol ? "var(--text)" : "var(--text-muted)",
            }}
          >
            {u.symbol}
            <span className={`mono ${changeClass(u.change_pct)}`} style={{ fontSize: 11 }}>{fmtPct(u.change_pct, 1)}</span>
          </button>
        ))}
      </div>

      <div className="grid" style={{ gridTemplateColumns: "minmax(0, 2.4fr) minmax(0, 1fr)", alignItems: "start" }}>
        {/* Chart */}
        <div className="panel fade-up">
          <div className="row between panel-pad" style={{ paddingBottom: 10, flexWrap: "wrap", gap: 10 }}>
            <div>
              <div className="row gap-12" style={{ alignItems: "baseline" }}>
                <span style={{ fontSize: 19, fontWeight: 700 }}>{symbol}</span>
                {snap && <span className="muted" style={{ fontSize: 13 }}>{snap.name}</span>}
              </div>
              {snap && (
                <div className="row gap-12" style={{ marginTop: 4 }}>
                  <span className="mono" style={{ fontSize: 20, fontWeight: 700 }}>{fmtNum(snap.last)}</span>
                  <span className={`pill ${snap.change_pct >= 0 ? "pill-up" : "pill-down"}`}>{fmtPct(snap.change_pct)}</span>
                </div>
              )}
            </div>
            <div className="row gap-8">
              {INTERVALS.map((iv) => (
                <button
                  key={iv.v}
                  className="btn"
                  onClick={() => setInterval(iv.v)}
                  style={{
                    padding: "6px 12px",
                    fontSize: 12.5,
                    borderColor: interval === iv.v ? "var(--accent)" : "var(--border-strong)",
                    color: interval === iv.v ? "var(--accent)" : "var(--text-muted)",
                  }}
                >
                  {iv.label}
                </button>
              ))}
            </div>
          </div>
          <div style={{ padding: "4px 14px 18px" }}>
            {error && !candles ? (
              <ErrorState message={error} />
            ) : (
              <CandleChart candles={candles ?? []} />
            )}
          </div>
        </div>

        {/* Right rail */}
        <div className="grid" style={{ gridTemplateColumns: "1fr" }}>
          {/* Instrument */}
          <div className="panel panel-pad fade-up">
            <div className="card-title" style={{ marginBottom: 12 }}>Instrument</div>
            <InfoRow k="Symbol" v={symbol} mono />
            <InfoRow k="Name" v={snap?.name ?? "—"} />
            <InfoRow k="Segment" v={snap?.segment ?? "—"} />
            <InfoRow k="Sector" v={snap?.sector ?? "—"} />
            <InfoRow k="Candles" v={String(candles?.length ?? 0)} mono />
          </div>

          {/* Regime */}
          <div className="panel panel-pad fade-up">
            <div className="card-title" style={{ marginBottom: 12 }}>Market Regime</div>
            {regime && regime.regimes.length ? (
              <>
                <div className="row gap-8" style={{ flexWrap: "wrap", marginBottom: 14 }}>
                  {regime.regimes.map((r) => (
                    <span key={r} className={`pill ${regimeTone(r)}`}>{titleCase(r)}</span>
                  ))}
                </div>
                {Object.entries(regime.indicators).map(([k, v]) => (
                  <InfoRow key={k} k={titleCase(k)} v={fmtNum(v, 4)} mono />
                ))}
              </>
            ) : (
              <div className="dim" style={{ fontSize: 12.5 }}>Classifying — needs more candle history.</div>
            )}
          </div>

          {/* Data quality */}
          <div className="panel panel-pad fade-up">
            <div className="row between" style={{ marginBottom: 12 }}>
              <span className="card-title">Data Quality</span>
              {quality && (
                <span className={`pill ${readinessTone(quality.readiness)}`} style={{ padding: "1px 8px" }}>
                  <span className="dot" />{titleCase(quality.readiness)}
                </span>
              )}
            </div>
            {quality ? (
              <>
                <div className="row between" style={{ marginBottom: 12 }}>
                  <div className="stat-value" style={{ fontSize: 28, color: "var(--up)" }}>
                    {(quality.score * 100).toFixed(1)}%
                  </div>
                  <span className="pill pill-info">{titleCase(quality.confidence)} confidence</span>
                </div>
                {Object.entries(quality.metrics).map(([k, v]) => (
                  <InfoRow key={k} k={titleCase(k)} v={fmtNum(v, k.includes("ms") ? 1 : 4)} mono />
                ))}
              </>
            ) : (
              <div className="dim" style={{ fontSize: 12.5 }}>Awaiting quality snapshot…</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function InfoRow({ k, v, mono }: { k: string; v: string; mono?: boolean }) {
  return (
    <div className="row between" style={{ padding: "6px 0", borderBottom: "1px solid rgba(30,40,54,0.5)" }}>
      <span className="dim" style={{ fontSize: 12.5 }}>{k}</span>
      <span className={mono ? "mono" : ""} style={{ fontSize: 12.5, fontWeight: 500 }}>{v}</span>
    </div>
  );
}

export default function MarketPage() {
  return (
    <Suspense fallback={<PageHeader title="Market Intelligence" subtitle="Loading…" />}>
      <MarketInner />
    </Suspense>
  );
}
