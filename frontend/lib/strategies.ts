// Types + client helpers for the Strategy Core API (proxied at /api-strategies).

export const STRATEGY_API = "/api-strategies";

export interface StrategyHealth {
  health_score: number | null;
  last_evaluation: string | null;
  last_execution: string | null;
  consecutive_failures: number;
  consecutive_successes: number;
  enabled: boolean;
  trading_allowed: boolean;
  updated_at: string | null;
}

export interface StrategyConfig {
  symbols: string[];
  exchanges: string[];
  timeframes: string[];
  entry_params: Record<string, unknown>;
  exit_params: Record<string, unknown>;
  risk_params: Record<string, unknown>;
  position_sizing: Record<string, unknown>;
  trading_session: Record<string, unknown>;
}

export interface StrategySummary {
  id: string;
  name: string;
  description: string;
  category: string;
  owner: string;
  status: string;
  tags: string[];
  version: number;
  execution_ready: boolean;
  created_at: string | null;
  updated_at: string | null;
  health: StrategyHealth | null;
}

export interface StrategyVersion {
  id: string;
  version: number;
  name: string;
  description: string;
  category: string;
  tags: string[];
  config: Record<string, unknown>;
  change_summary: string;
  created_by: string;
  created_at: string | null;
}

export interface StrategyAudit {
  id: number;
  action: string;
  from_status: string | null;
  to_status: string | null;
  version: number | null;
  detail: string;
  actor: string;
  created_at: string | null;
}

export interface StrategyDetail extends StrategySummary {
  configuration: Partial<StrategyConfig>;
  supported_instruments: { symbols: string[]; exchanges: string[]; timeframes: string[] };
  available_transitions: string[];
  is_terminal: boolean;
  is_editable: boolean;
  execution_ready: boolean;
  version_count: number;
  versions: StrategyVersion[];
}

export interface DashboardSummary {
  total: number;
  by_status: Record<string, number>;
  active: number;
  ready: number;
  draft: number;
  paused: number;
  archived: number;
  health: { avg_score: number | null; scored: number; trading_allowed: number; enabled: number };
  recent: StrategySummary[];
}

// Lifecycle ordering (for the timeline) and presentation tones.
export const LIFECYCLE: string[] = [
  "draft", "configured", "validated", "ready", "paused", "archived",
];

const STATUS_TONE: Record<string, string> = {
  draft: "pill",
  configured: "pill-info",
  validated: "pill-info",
  ready: "pill-up",
  paused: "pill-warn",
  archived: "pill-down",
};

export function statusTone(status: string): string {
  return STATUS_TONE[status] ?? "pill";
}

/** Execution-readiness label + tone derived from lifecycle status. */
export function readiness(status: string): { label: string; tone: string } {
  switch (status) {
    case "ready":
      return { label: "Ready", tone: "pill-up" };
    case "paused":
      return { label: "Paused", tone: "pill-warn" };
    case "archived":
      return { label: "Archived", tone: "pill-down" };
    default:
      return { label: "Not ready", tone: "pill" };
  }
}

export function healthTone(score: number | null | undefined): "up" | "down" | "neutral" {
  if (score === null || score === undefined) return "neutral";
  if (score >= 0.75) return "up";
  if (score >= 0.5) return "neutral";
  return "down";
}

async function send<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${STRATEGY_API}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const j = await res.json();
      if (j?.detail) detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export interface CreateStrategyInput {
  name: string;
  description?: string;
  category?: string;
  owner?: string;
  tags?: string[];
  config?: Partial<StrategyConfig>;
}

export const StrategyApi = {
  create: (body: CreateStrategyInput) => send<StrategyDetail>("POST", "", body),
  update: (id: string, body: Record<string, unknown>) =>
    send<StrategyDetail>("PATCH", `/${id}`, body),
  transition: (id: string, to_status: string, reason = "") =>
    send<StrategyDetail>("POST", `/${id}/transition`, { to_status, reason }),
  archive: (id: string) => send<StrategyDetail>("POST", `/${id}/archive`),
  rollback: (id: string, version: number) =>
    send<StrategyDetail>("POST", `/${id}/rollback`, { version }),
  clone: (id: string, name: string) =>
    send<StrategyDetail>("POST", `/${id}/clone`, { name }),
  remove: (id: string) => send<void>("DELETE", `/${id}`),
};
