"use client";

import Link from "next/link";
import type { InstrumentSnapshot } from "@/lib/types";
import { changeClass, fmtNum, fmtPct } from "@/lib/format";

export function Movers({ title, rows, tone }: { title: string; rows: InstrumentSnapshot[]; tone: "up" | "down" }) {
  return (
    <div className="panel panel-pad fade-up">
      <div className="row between" style={{ marginBottom: 14 }}>
        <span className="card-title">{title}</span>
        <span className={`pill ${tone === "up" ? "pill-up" : "pill-down"}`} style={{ padding: "1px 8px" }}>
          {tone === "up" ? "Gainers" : "Losers"}
        </span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {rows.length === 0 && <div className="dim" style={{ fontSize: 12.5 }}>No movers yet.</div>}
        {rows.map((r) => (
          <Link
            key={r.symbol}
            href={`/market?symbol=${r.symbol}`}
            className="mover-row row between"
            style={{ padding: "9px 8px", borderRadius: 8 }}
          >
            <div>
              <div style={{ fontWeight: 600, fontSize: 13.5 }}>{r.symbol}</div>
              <div className="dim" style={{ fontSize: 11 }}>{r.sector}</div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div className="mono" style={{ fontSize: 13 }}>{fmtNum(r.last)}</div>
              <div className={`mono ${changeClass(r.change_pct)}`} style={{ fontSize: 12, fontWeight: 600 }}>
                {fmtPct(r.change_pct)}
              </div>
            </div>
          </Link>
        ))}
      </div>
      <style>{`.mover-row:hover{background:var(--panel-2);}`}</style>
    </div>
  );
}
