"use client";

import type { Overview } from "@/lib/types";

export function Breadth({ breadth }: { breadth: Overview["breadth"] }) {
  const { advances, declines, unchanged, total } = breadth;
  const t = total || 1;
  const aPct = (advances / t) * 100;
  const uPct = (unchanged / t) * 100;
  const dPct = (declines / t) * 100;

  return (
    <div className="panel panel-pad fade-up">
      <div className="card-title" style={{ marginBottom: 14 }}>Market Breadth</div>

      <div className="row between mono" style={{ fontSize: 13, marginBottom: 8 }}>
        <span className="up">▲ {advances}</span>
        <span className="dim">● {unchanged}</span>
        <span className="down">▼ {declines}</span>
      </div>

      <div style={{ display: "flex", height: 10, borderRadius: 6, overflow: "hidden", background: "var(--bg-2)" }}>
        <div style={{ width: `${aPct}%`, background: "var(--up)", transition: "width 0.5s ease" }} />
        <div style={{ width: `${uPct}%`, background: "var(--text-dim)", transition: "width 0.5s ease" }} />
        <div style={{ width: `${dPct}%`, background: "var(--down)", transition: "width 0.5s ease" }} />
      </div>

      <div className="row between" style={{ marginTop: 14 }}>
        <div>
          <div className="stat-value" style={{ fontSize: 22, color: "var(--up)" }}>{advances}</div>
          <div className="dim" style={{ fontSize: 11 }}>Advancing</div>
        </div>
        <div style={{ textAlign: "center" }}>
          <div className="stat-value" style={{ fontSize: 22 }}>{total}</div>
          <div className="dim" style={{ fontSize: 11 }}>Constituents</div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div className="stat-value" style={{ fontSize: 22, color: "var(--down)" }}>{declines}</div>
          <div className="dim" style={{ fontSize: 11 }}>Declining</div>
        </div>
      </div>
    </div>
  );
}
