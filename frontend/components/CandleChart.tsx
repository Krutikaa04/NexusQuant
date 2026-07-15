"use client";

import { useState } from "react";
import type { Candle } from "@/lib/types";
import { fmtNum, fmtTime } from "@/lib/format";

interface Props {
  candles: Candle[];
  height?: number;
}

/** Institutional candlestick + volume chart, drawn as pure SVG with a crosshair tooltip. */
export function CandleChart({ candles, height = 340 }: Props) {
  const [hover, setHover] = useState<number | null>(null);

  if (!candles || candles.length === 0) {
    return (
      <div className="row" style={{ height, justifyContent: "center", color: "var(--text-dim)" }}>
        No candle data yet — the pipeline is warming up.
      </div>
    );
  }

  const W = 960;
  const H = height;
  const padL = 8;
  const padR = 62;
  const padT = 14;
  const volH = 56;
  const priceH = H - padT - volH - 26;

  const plotW = W - padL - padR;
  const n = candles.length;
  const bw = Math.max(2, (plotW / n) * 0.64);
  const step = plotW / n;

  const highs = candles.map((c) => c.high);
  const lows = candles.map((c) => c.low);
  const hi = Math.max(...highs);
  const lo = Math.min(...lows);
  const span = hi - lo || 1;
  const pad = span * 0.08;
  const top = hi + pad;
  const bot = lo - pad;
  const yPrice = (v: number) => padT + ((top - v) / (top - bot)) * priceH;

  const maxVol = Math.max(...candles.map((c) => c.volume), 1);
  const volTop = padT + priceH + 18;
  const yVol = (v: number) => volTop + (1 - v / maxVol) * volH;

  const gridN = 4;
  const gridLines = Array.from({ length: gridN + 1 }, (_, i) => bot + (span + 2 * pad) * (i / gridN));

  const hc = hover !== null ? candles[hover] : candles[n - 1];

  return (
    <div style={{ position: "relative", width: "100%", overflowX: "auto" }}>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        width="100%"
        height={H}
        style={{ display: "block" }}
        onMouseLeave={() => setHover(null)}
      >
        {/* grid + price axis */}
        {gridLines.map((g, i) => (
          <g key={i}>
            <line x1={padL} x2={W - padR} y1={yPrice(g)} y2={yPrice(g)} stroke="var(--border)" strokeWidth="1" />
            <text x={W - padR + 6} y={yPrice(g) + 3.5} fontSize="10.5" fill="var(--text-dim)" className="mono">
              {fmtNum(g, 0)}
            </text>
          </g>
        ))}

        {/* candles */}
        {candles.map((c, i) => {
          const x = padL + i * step + (step - bw) / 2;
          const cx = x + bw / 2;
          const up = c.close >= c.open;
          const col = up ? "var(--up)" : "var(--down)";
          const yO = yPrice(c.open);
          const yC = yPrice(c.close);
          const bodyY = Math.min(yO, yC);
          const bodyH = Math.max(1.2, Math.abs(yC - yO));
          return (
            <g key={i} opacity={hover === null || hover === i ? 1 : 0.55}>
              <line x1={cx} x2={cx} y1={yPrice(c.high)} y2={yPrice(c.low)} stroke={col} strokeWidth="1.1" />
              <rect x={x} y={bodyY} width={bw} height={bodyH} fill={col} rx="0.6" />
              <rect
                x={padL + i * step}
                y={padT}
                width={step}
                height={H - padT - 8}
                fill="transparent"
                onMouseEnter={() => setHover(i)}
              />
            </g>
          );
        })}

        {/* volume */}
        {candles.map((c, i) => {
          const x = padL + i * step + (step - bw) / 2;
          const up = c.close >= c.open;
          const y = yVol(c.volume);
          return (
            <rect
              key={`v${i}`}
              x={x}
              y={y}
              width={bw}
              height={volTop + volH - y}
              fill={up ? "var(--up)" : "var(--down)"}
              opacity={hover === null || hover === i ? 0.4 : 0.22}
            />
          );
        })}

        {/* crosshair */}
        {hover !== null && (
          <line
            x1={padL + hover * step + step / 2}
            x2={padL + hover * step + step / 2}
            y1={padT}
            y2={volTop + volH}
            stroke="var(--accent)"
            strokeWidth="1"
            strokeDasharray="3 3"
            opacity="0.7"
          />
        )}
      </svg>

      {/* OHLC readout */}
      <div
        className="row gap-16 mono"
        style={{ position: "absolute", top: 8, left: 10, fontSize: 12, pointerEvents: "none", flexWrap: "wrap" }}
      >
        <span className="dim">{fmtTime(hc.open_time)}</span>
        <span>O <b>{fmtNum(hc.open)}</b></span>
        <span>H <b>{fmtNum(hc.high)}</b></span>
        <span>L <b>{fmtNum(hc.low)}</b></span>
        <span className={hc.close >= hc.open ? "up" : "down"}>C <b>{fmtNum(hc.close)}</b></span>
        <span className="dim">Vol {fmtNum(hc.volume, 0)}</span>
      </div>
    </div>
  );
}
