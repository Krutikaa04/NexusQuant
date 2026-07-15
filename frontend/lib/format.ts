export function fmtNum(v: number | null | undefined, dp = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return v.toLocaleString("en-IN", { minimumFractionDigits: dp, maximumFractionDigits: dp });
}

export function fmtPct(v: number | null | undefined, dp = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  const sign = v > 0 ? "+" : "";
  return `${sign}${v.toFixed(dp)}%`;
}

export function fmtInt(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  return v.toLocaleString("en-IN");
}

export function changeClass(v: number | null | undefined): string {
  if (v === null || v === undefined || v === 0) return "";
  return v > 0 ? "up" : "down";
}

export function titleCase(s: string): string {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function fmtTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString("en-IN", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return iso;
  }
}

const REGIME_TONE: Record<string, string> = {
  bull: "pill-up",
  bear: "pill-down",
  sideways: "pill",
  high_volatility: "pill-warn",
  low_volatility: "pill-info",
  expiry_week: "pill-warn",
};

export function regimeTone(regime: string): string {
  return REGIME_TONE[regime] ?? "pill";
}

const READINESS_TONE: Record<string, string> = {
  ready: "pill-up",
  degraded: "pill-warn",
  blocked: "pill-down",
  unknown: "pill",
};

export function readinessTone(readiness: string): string {
  return READINESS_TONE[readiness] ?? "pill";
}
