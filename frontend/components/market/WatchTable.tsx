"use client";

import { useRouter } from "next/navigation";
import type { InstrumentSnapshot } from "@/lib/types";
import { changeClass, fmtPct, regimeTone, titleCase } from "@/lib/format";
import { Sparkline } from "@/components/Sparkline";
import { PriceCell } from "./PriceCell";

export function WatchTable({ rows }: { rows: InstrumentSnapshot[] }) {
  const router = useRouter();

  return (
    <div style={{ overflowX: "auto" }}>
      <table className="table">
        <thead>
          <tr>
            <th>Instrument</th>
            <th>Trend</th>
            <th className="num">Last</th>
            <th className="num">Change</th>
            <th className="num">Day Range</th>
            <th>Regime</th>
            <th>Quality</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr
              key={r.symbol}
              style={{ cursor: "pointer" }}
              onClick={() => router.push(`/market?symbol=${r.symbol}`)}
              tabIndex={0}
              onKeyDown={(e) => e.key === "Enter" && router.push(`/market?symbol=${r.symbol}`)}
            >
              <td>
                <div style={{ fontWeight: 600 }}>{r.symbol}</div>
                <div className="dim" style={{ fontSize: 11.5 }}>{r.name}</div>
              </td>
              <td><Sparkline data={r.spark} positive={r.change_pct >= 0} /></td>
              <td className="num"><PriceCell value={r.last} /></td>
              <td className={`num ${changeClass(r.change_pct)}`} style={{ fontWeight: 600 }}>
                {fmtPct(r.change_pct)}
              </td>
              <td className="num dim" style={{ fontSize: 12 }}>
                {r.day_low?.toFixed(1)} – {r.day_high?.toFixed(1)}
              </td>
              <td>
                <div className="row gap-8" style={{ flexWrap: "wrap" }}>
                  {r.regimes.length ? (
                    r.regimes.map((rg) => (
                      <span key={rg} className={`pill ${regimeTone(rg)}`} style={{ padding: "1px 8px" }}>
                        {titleCase(rg)}
                      </span>
                    ))
                  ) : (
                    <span className="dim" style={{ fontSize: 12 }}>—</span>
                  )}
                </div>
              </td>
              <td>
                <span className={`pill ${r.readiness === "ready" ? "pill-up" : r.readiness === "degraded" ? "pill-warn" : "pill"}`} style={{ padding: "1px 8px" }}>
                  <span className="dot" />{titleCase(r.readiness)}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
