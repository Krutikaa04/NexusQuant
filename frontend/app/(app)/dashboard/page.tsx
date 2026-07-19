"use client";

import { useApi } from "@/lib/useApi";
import type { Overview } from "@/lib/types";
import { changeClass, fmtNum, fmtPct, fmtTime, titleCase } from "@/lib/format";
import { PageHeader, StatCard, ErrorState, SkeletonRows } from "@/components/ui";
import { Sparkline } from "@/components/Sparkline";
import { WatchTable } from "@/components/market/WatchTable";
import { Movers } from "@/components/market/Movers";
import { Breadth } from "@/components/market/Breadth";

export default function DashboardPage() {
  const { data, error, loading, refresh } = useApi<Overview>("/api/overview", 2500);

  if (error && !data) return <><PageHeader title="Command Center" /><ErrorState message={error} onRetry={refresh} /></>;

  return (
    <div>
      <PageHeader
        title="Command Center"
        subtitle="Market intelligence across the tracked NSE universe."
        badge={
          data?.data_feed?.is_real_market_data ? (
            <span className="pill pill-up" title={data.data_feed.note}>
              <span className="live-dot" />Live · {data.data_feed.provider}
            </span>
          ) : (
            <span className="pill pill-warn" title={data?.data_feed?.note ?? "Simulated development feed, not live NSE quotes."}>
              <span className="live-dot" />Simulated feed
            </span>
          )
        }
        actions={
          <span className="pill mono" title="Last update">
            {data ? fmtTime(data.as_of) : "—"}
          </span>
        }
      />

      {/* Index strip */}
      <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))", marginBottom: 18 }}>
        {loading && !data
          ? Array.from({ length: 3 }).map((_, i) => <div key={i} className="panel skeleton" style={{ height: 96 }} />)
          : data?.indices.map((idx, i) => (
              <div key={idx.symbol} className="panel panel-pad fade-up" style={{ animationDelay: `${i * 60}ms` }}>
                <div className="row between">
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 15 }}>{idx.name}</div>
                    <div className="dim" style={{ fontSize: 11 }}>{idx.symbol}</div>
                  </div>
                  <Sparkline data={idx.spark} positive={idx.change_pct >= 0} width={80} height={30} />
                </div>
                <div className="row between" style={{ marginTop: 12, alignItems: "flex-end" }}>
                  <div className="mono" style={{ fontSize: 22, fontWeight: 700 }}>{fmtNum(idx.last)}</div>
                  <div className={`pill ${idx.change_pct >= 0 ? "pill-up" : "pill-down"}`}>
                    {fmtPct(idx.change_pct)}
                  </div>
                </div>
              </div>
            ))}
      </div>

      {/* Stat row */}
      <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))", marginBottom: 18 }}>
        <StatCard
          label="Session"
          value={data ? titleCase(data.session.phase) : "—"}
          sub={data ? `${data.session.exchange} · ${data.session.is_trading_day ? "Trading day" : "Closed"}` : ""}
          delay={0}
        />
        <StatCard
          label="Breadth (A/D)"
          value={data ? `${data.breadth.advances} / ${data.breadth.declines}` : "—"}
          sub={data ? `${data.breadth.total} constituents` : ""}
          tone={data && data.breadth.advances >= data.breadth.declines ? "up" : "down"}
          delay={60}
        />
        <StatCard
          label="Data Quality"
          value={data ? `${(data.quality.avg_score * 100).toFixed(1)}%` : "—"}
          sub={data ? `${data.quality.ready}/${data.quality.total} feeds ready` : ""}
          tone="up"
          delay={120}
        />
        <StatCard
          label="Top Mover"
          value={data?.gainers[0] ? data.gainers[0].symbol : "—"}
          sub={data?.gainers[0] ? <span className={changeClass(data.gainers[0].change_pct)}>{fmtPct(data.gainers[0].change_pct)}</span> : ""}
          delay={180}
        />
      </div>

      {/* Main grid */}
      <div className="grid" style={{ gridTemplateColumns: "minmax(0, 2.3fr) minmax(0, 1fr)", alignItems: "start" }}>
        <div className="panel fade-up">
          <div className="row between panel-pad" style={{ paddingBottom: 12 }}>
            <span className="card-title">Watchlist · NSE Equities</span>
            <span className="dim" style={{ fontSize: 11.5 }}>Click a row for full analysis</span>
          </div>
          {loading && !data ? <SkeletonRows rows={8} cols={6} /> : data && <WatchTable rows={data.equities} />}
        </div>

        <div className="grid" style={{ gridTemplateColumns: "1fr" }}>
          {data && <Breadth breadth={data.breadth} />}
          {data && <Movers title="Top Gainers" rows={data.gainers} tone="up" />}
          {data && <Movers title="Top Losers" rows={data.losers} tone="down" />}
        </div>
      </div>

      <div className="dim" style={{ marginTop: 20, fontSize: 11.5, textAlign: "center" }}>
        All figures derived live from the SPEC-004 ingestion pipeline · synthetic development feed
      </div>
    </div>
  );
}
