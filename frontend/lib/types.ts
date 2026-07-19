// Shared response shapes mirroring the backend contracts.

export interface InstrumentSnapshot {
  symbol: string;
  name: string;
  segment: string;
  sector: string;
  last: number | null;
  change_pct: number;
  day_high: number | null;
  day_low: number | null;
  spark: number[];
  readiness: string;
  quality_score: number | null;
  regimes: string[];
  candle_count: number;
}

export interface DataFeed {
  provider: string;
  kind: string;
  is_real_market_data: boolean;
  note: string;
}

export interface Overview {
  as_of: string;
  data_feed?: DataFeed;
  session: {
    exchange: string;
    phase: string;
    is_trading_day: boolean;
    is_holiday: boolean;
    open: string | null;
    close: string | null;
  };
  breadth: { advances: number; declines: number; unchanged: number; total: number };
  quality: { ready: number; total: number; avg_score: number };
  indices: InstrumentSnapshot[];
  equities: InstrumentSnapshot[];
  gainers: InstrumentSnapshot[];
  losers: InstrumentSnapshot[];
}

export interface Candle {
  symbol: string;
  interval_seconds: number;
  open_time: string;
  close_time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  tick_count: number;
}

export interface QualitySnapshot {
  symbol: string;
  score: number;
  confidence: string;
  readiness: string;
  metrics: Record<string, number>;
  as_of: string;
}

export interface ModuleInfo {
  key: string;
  name: string;
  spec: string;
  status: "live" | "coming_soon";
  summary: string;
}

export interface ServiceInfo {
  name: string;
  spec: string;
  status: string;
  summary: string;
}

export interface SystemInfo {
  modules: ModuleInfo[];
  services: ServiceInfo[];
}
