// Types + mutation helpers for the Research OS module (SPEC-007).
// API calls go through the /api-research proxy prefix (distinct from the /research pages).

export const RESEARCH_API = "/api-research";

export interface ProjectSummary {
  id: string;
  name: string;
  owner: string;
  description: string | null;
  status: string;
  tags: string[];
  hypothesis_count: number;
  experiment_count: number;
  review_count: number;
  allowed_transitions: string[];
  created_at: string;
  updated_at: string;
}

export interface Hypothesis {
  id: string;
  project_id: string;
  statement: string;
  success_criteria: string;
  notes: string | null;
  archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface Experiment {
  id: string;
  project_id: string;
  hypothesis_id: string | null;
  name: string;
  dataset_version: string;
  feature_version: string;
  status: string;
  metrics: Record<string, number>;
  notes: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface Review {
  id: string;
  project_id: string;
  reviewer: string;
  decision: string;
  comments: string;
  stage: string;
  created_at: string;
}

export interface ProjectDetail extends ProjectSummary {
  metadata: Record<string, unknown>;
  hypotheses: Hypothesis[];
  experiments: Experiment[];
  reviews: Review[];
}

export interface Transition {
  from_status: string | null;
  to_status: string;
  actor: string;
  note: string | null;
  at: string;
}

export interface ResearchDashboard {
  stats: {
    projects: number;
    by_status: Record<string, number>;
    hypotheses: number;
    experiments: number;
    experiments_running: number;
    experiments_completed: number;
    reviews: number;
  };
  activity: {
    kind: string;
    at: string;
    project_id: string;
    project: string;
    actor: string;
    detail: string;
    note: string | null;
  }[];
}

export const LIFECYCLE: string[] = [
  "draft",
  "active",
  "experimenting",
  "validated",
  "paper_trading",
  "production_candidate",
  "approved",
  "retired",
];

export const STATUS_TONE: Record<string, string> = {
  draft: "pill",
  active: "pill-info",
  experimenting: "pill-info",
  validated: "pill-up",
  paper_trading: "pill-warn",
  production_candidate: "pill-warn",
  approved: "pill-up",
  retired: "pill-down",
};

export const EXPERIMENT_TONE: Record<string, string> = {
  pending: "pill",
  running: "pill-info",
  completed: "pill-up",
  failed: "pill-down",
  cancelled: "pill-warn",
};

export const DECISION_TONE: Record<string, string> = {
  approve: "pill-up",
  reject: "pill-down",
  needs_changes: "pill-warn",
};

/** POST/PATCH JSON with typed error extraction (FastAPI `detail`). */
export async function mutate<T>(
  path: string,
  method: "POST" | "PATCH",
  body?: unknown
): Promise<T> {
  const res = await fetch(`${RESEARCH_API}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const json = await res.json().catch(() => null);
  if (!res.ok) {
    const detail =
      json && typeof json.detail === "string"
        ? json.detail
        : json?.detail?.[0]?.msg
          ? `${json.detail[0].loc?.slice(-1)[0]}: ${json.detail[0].msg}`
          : `${res.status} ${res.statusText}`;
    throw new Error(detail);
  }
  return json as T;
}
