/** Typed functions for every sigma-engine endpoint the app calls. All
 * fetches go through `request()` here — nothing in src/app or src/tools
 * calls `fetch` directly (M1 brief). Endpoint paths/shapes are taken
 * verbatim from engine/sigma_engine/routes/*.py; nothing here is invented.
 */
import { resolveEngineBaseUrl } from "./runtime";
import { ApiError } from "./errors";
import type { PydanticErrorItem } from "./errors";
import type {
  ArtifactIndexEntry,
  BaselineResponse,
  Computed,
  ColumnType,
  DatasetDetail,
  DatasetMeta,
  DatasetPreview,
  DescriptiveStats,
  GateResult,
  HealthResponse,
  OverrideLogEntry,
  ParetoResult,
  PrescoreResult,
  ProjectMetadata,
  SampleSizeResponse,
  SmokeResponse,
} from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const base = resolveEngineBaseUrl();
  let res: Response;
  try {
    res = await fetch(`${base}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
  } catch (err) {
    throw new ApiError(
      `Could not reach the engine (${base}${path}): ${err instanceof Error ? err.message : String(err)}`,
      0,
    );
  }

  if (!res.ok) {
    let body: unknown = null;
    try {
      body = await res.json();
    } catch {
      /* non-JSON error body -- body stays null */
    }
    const detail = (body as { detail?: unknown } | null)?.detail;
    if (res.status === 422 && Array.isArray(detail)) {
      throw new ApiError("Validation failed", 422, { validation: detail as PydanticErrorItem[] });
    }
    const detailText = typeof detail === "string" ? detail : res.statusText;
    throw new ApiError(detailText || `HTTP ${res.status}`, res.status, { detail: detailText });
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

function postJson(body: unknown): RequestInit {
  return { method: "POST", body: JSON.stringify(body) };
}

// ---- /project (routes/projects.py) ----

export function createProject(input: { project_id: string; name: string; created_at: string }): Promise<ProjectMetadata> {
  return request<ProjectMetadata>("/project/create", postJson(input));
}

export function openProject(projectId: string): Promise<ProjectMetadata> {
  return request<ProjectMetadata>(`/project/${encodeURIComponent(projectId)}`);
}

export interface ProjectInfoResponse {
  project_id: string;
  name: string;
  /** Real, absolute on-disk folder path (routes/projects.py's /info,
   * backed by ProjectStore.resolved_project_path) -- the value
   * app/project/path.ts uses instead of the documented-default guess. */
  folder_path: string;
  artifact_count: number;
  artifact_index: Record<string, ArtifactIndexEntry>;
}

export function getProjectInfo(projectId: string): Promise<ProjectInfoResponse> {
  return request<ProjectInfoResponse>(`/project/${encodeURIComponent(projectId)}/info`);
}

// ---- /artifacts (routes/artifacts.py) ----

export interface ValidateArtifactResponse {
  valid: boolean;
  artifact: unknown;
}

export function validateArtifact(toolId: string, body: unknown): Promise<ValidateArtifactResponse> {
  return request<ValidateArtifactResponse>(`/artifacts/${toolId}/validate`, postJson(body));
}

export interface SaveArtifactResponse {
  artifact_id: string;
  tool_id: string;
  version: number;
}

export function saveArtifact(projectId: string, toolId: string, body: unknown): Promise<SaveArtifactResponse> {
  return request<SaveArtifactResponse>(`/project/${encodeURIComponent(projectId)}/artifacts/${toolId}`, postJson(body));
}

export function loadArtifact(projectId: string, artifactId: string, version?: number): Promise<Record<string, unknown>> {
  const qs = version != null ? `?version=${version}` : "";
  return request<Record<string, unknown>>(
    `/project/${encodeURIComponent(projectId)}/artifacts/${encodeURIComponent(artifactId)}${qs}`,
  );
}

export interface ListVersionsResponse {
  artifact_id: string;
  versions: number[];
}

export function listArtifactVersions(projectId: string, artifactId: string): Promise<ListVersionsResponse> {
  return request<ListVersionsResponse>(
    `/project/${encodeURIComponent(projectId)}/artifacts/${encodeURIComponent(artifactId)}/versions`,
  );
}

// ---- /prescore (routes/prescore.py) ----

export function runPrescore(toolId: string, body: unknown): Promise<PrescoreResult[]> {
  return request<PrescoreResult[]>(`/prescore/${toolId}`, postJson(body));
}

// ---- /gates (routes/gates.py) ----

export function checkGate(gateId: string, projectId: string): Promise<GateResult> {
  return request<GateResult>("/gates/check", postJson({ gate_id: gateId, project_id: projectId }));
}

export function overrideGate(input: {
  gate_id: string;
  project_id: string;
  reason: string;
  timestamp: string;
}): Promise<OverrideLogEntry> {
  return request<OverrideLogEntry>("/gates/override", postJson(input));
}

// ---- Export (routes/export.py) ----

/** GET .../artifacts/T-03/pdf as a Blob, for the charter's "Export PDF"
 * button (M1 brief) -- a separate path from request() above because the
 * response body is a binary PDF, not JSON. Error handling mirrors
 * request(): a non-JSON or non-string `detail` just falls back to the
 * HTTP status text. */
export async function downloadCharterPdf(projectId: string, version?: number): Promise<Blob> {
  const base = resolveEngineBaseUrl();
  const qs = version != null ? `?version=${version}` : "";
  const url = `${base}/project/${encodeURIComponent(projectId)}/artifacts/T-03/pdf${qs}`;

  let res: Response;
  try {
    res = await fetch(url);
  } catch (err) {
    throw new ApiError(`Could not reach the engine (${url}): ${err instanceof Error ? err.message : String(err)}`, 0);
  }

  if (!res.ok) {
    let detailText = res.statusText;
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detailText = body.detail;
    } catch {
      /* non-JSON error body -- fall back to statusText */
    }
    throw new ApiError(detailText || `HTTP ${res.status}`, res.status, { detail: detailText });
  }

  return res.blob();
}

// ---- Datasets (routes/datasets.py) — T-11 import half ----

export interface DatasetImportBody {
  source_filename: string;
  content_base64: string;
  column_types?: Record<string, ColumnType>;
}

/** Parse+infer+scan only — nothing persisted. Safe to call repeatedly as
 * the user tries different column-type overrides in the T-11 preview. */
export function previewDataset(projectId: string, body: DatasetImportBody): Promise<DatasetPreview> {
  return request<DatasetPreview>(`/project/${encodeURIComponent(projectId)}/datasets/preview`, postJson(body));
}

export function saveDataset(projectId: string, body: DatasetImportBody & { created_at: string }): Promise<DatasetMeta> {
  return request<DatasetMeta>(`/project/${encodeURIComponent(projectId)}/datasets`, postJson(body));
}

export function listDatasets(projectId: string): Promise<DatasetMeta[]> {
  return request<DatasetMeta[]>(`/project/${encodeURIComponent(projectId)}/datasets`);
}

export function getDataset(projectId: string, datasetId: string): Promise<DatasetDetail> {
  return request<DatasetDetail>(`/project/${encodeURIComponent(projectId)}/datasets/${encodeURIComponent(datasetId)}`);
}

// ---- Stats (routes/stats.py) — T-13 baseline, T-14 chart facts ----

export interface BaselineRequestBody {
  data?: number[];
  project_id?: string;
  dataset_id?: string;
  column?: string;
  usl?: number | null;
  lsl?: number | null;
  operational_definition_ok: boolean;
  enable_rule2?: boolean;
  enable_rule3?: boolean;
  apply_sigma_shift?: boolean;
}

/** The only way T-13 gets numbers onto the screen — every field in the
 * response is rendered as-is, nothing recomputed client-side (M2 brief). */
export function runBaseline(body: BaselineRequestBody): Promise<BaselineResponse> {
  return request<BaselineResponse>("/stats/baseline", postJson(body));
}

/** Engine-computed n/mean/sd/median/IQR for a raw column pulled from a
 * dataset — what T-14's chart headlines quote instead of re-deriving
 * anything by hand (rubric R-MEA-10). */
export function runDescriptive(data: number[]): Promise<Computed<DescriptiveStats>> {
  return request<Computed<DescriptiveStats>>("/stats/descriptive", postJson({ data }));
}

/** Sorted tally + cumulative share + the engine-made vital-few call
 * (T-14's Pareto chart never decides its own headline client-side). */
export function runPareto(categories: string[]): Promise<Computed<ParetoResult>> {
  return request<Computed<ParetoResult>>("/stats/pareto", postJson({ categories }));
}

// ---- Stats: sample-size guidance (routes/stats.py) — T-11 -----------------

export interface SampleSizeRequestBody {
  calculator?: "mean" | "proportion";
  planning_sd?: number;
  planning_p?: number;
  margin_of_error?: number;
  confidence_level?: number;
  is_convenience_sample?: boolean;
  single_shift_only?: boolean;
  single_operator_only?: boolean;
  short_collection_window?: boolean;
}

/** Always returns the I-MR rule of thumb + applicable bias warnings;
 * `calculator` in the body additionally runs the requested margin-of-
 * error formula (T-11's sample-size panel, PLAN §4.1). */
export function runSampleSize(body: SampleSizeRequestBody): Promise<SampleSizeResponse> {
  return request<SampleSizeResponse>("/stats/sample-size", postJson(body));
}

// ---- diagnostics (main.py) ----

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export function getSmoke(): Promise<SmokeResponse> {
  return request<SmokeResponse>("/smoke");
}
