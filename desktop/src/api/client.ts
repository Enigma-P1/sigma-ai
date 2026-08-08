/** Typed functions for every sigma-engine endpoint the app calls. All
 * fetches go through `request()` here — nothing in src/app or src/tools
 * calls `fetch` directly (M1 brief). Endpoint paths/shapes are taken
 * verbatim from engine/sigma_engine/routes/*.py; nothing here is invented.
 */
import { resolveEngineBaseUrl } from "./runtime";
import { ApiError } from "./errors";
import type { PydanticErrorItem } from "./errors";
import type {
  AdvisorAskRequest,
  AdvisorAskResponse,
  AdvisorExportResponse,
  AdvisorSettingsResponse,
  AdvisorSettingsUpdateRequest,
  AdvisorStatusResponse,
  AdvisorValidateRequest,
  ArtifactIndexEntry,
  BaselineResponse,
  Computed,
  ColumnType,
  DatasetDetail,
  DatasetMeta,
  DatasetPreview,
  DescriptiveStats,
  FloorPlanDetail,
  FloorPlanImageMeta,
  GateResult,
  HealthResponse,
  HypothesisQuestion,
  HypothesisRouteResponse,
  HypothesisRunResult,
  OverrideLogEntry,
  ParetoResult,
  PrescoreResult,
  ProjectMetadata,
  SampleSizeResponse,
  SmokeResponse,
  TollgatePhase,
  ValidatorReport,
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

function putJson(body: unknown): RequestInit {
  return { method: "PUT", body: JSON.stringify(body) };
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

/** `projectId` (optional) turns on the engine's project-aware prescore
 * checks for tools that have one -- today that is T-21's
 * measurement_check_on_file only (routes/prescore.py). Omitted, the call
 * stays artifact-only exactly as before. */
export function runPrescore(toolId: string, body: unknown, projectId?: string): Promise<PrescoreResult[]> {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  return request<PrescoreResult[]>(`/prescore/${toolId}${query}`, postJson(body));
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

// ---- Stats: Hypothesis Testing (routes/hypothesis.py) — T-17 -------------

export interface HypDatasetColumnRef {
  dataset_id: string;
  column: string;
}

/** `question` is used as-is unless a *_column ref below overrides one of
 * its array slots with a loaded dataset column -- `project_id` is required
 * whenever any ref is given (routes/hypothesis.py's _resolve_question). */
export interface HypothesisRequestBody {
  question: HypothesisQuestion;
  project_id?: string;
  group_columns?: Record<number, HypDatasetColumnRef>;
  paired_before_column?: HypDatasetColumnRef;
  paired_after_column?: HypDatasetColumnRef;
  sample_column?: HypDatasetColumnRef;
}

/** Routing only -- the printed decision tree, safe to call speculatively
 * (never computes a test statistic). */
export function routeHypothesis(body: HypothesisRequestBody): Promise<HypothesisRouteResponse> {
  return request<HypothesisRouteResponse>("/stats/hypothesis/route", postJson(body));
}

/** Route + compute in one call. Refuses with the named EXIT when one
 * fires (`refused: true`, `result: null`) -- every number T-17 renders
 * comes from this response, nothing computed client-side. */
export function runHypothesis(body: HypothesisRequestBody): Promise<HypothesisRunResult> {
  return request<HypothesisRunResult>("/stats/hypothesis/run", postJson(body));
}

// ---- Floor-plan images (routes/floorplans.py) — T-07 upload ----

export interface FloorPlanUploadBody {
  source_filename: string;
  content_base64: string;
  created_at: string;
}

/** Upload IS save here -- no preview/confirm step like datasets have
 * (there's no column-type equivalent for an image). */
export function uploadFloorPlan(projectId: string, body: FloorPlanUploadBody): Promise<FloorPlanImageMeta> {
  return request<FloorPlanImageMeta>(`/project/${encodeURIComponent(projectId)}/floorplans`, postJson(body));
}

/** Fetches the image back (meta + base64 bytes) so a reloaded project can
 * rebuild the canvas background without the original File still in
 * memory (T-11's dataset GET is the same "re-fetch on reload" shape). */
export function getFloorPlan(projectId: string, imageId: string): Promise<FloorPlanDetail> {
  return request<FloorPlanDetail>(`/project/${encodeURIComponent(projectId)}/floorplans/${encodeURIComponent(imageId)}`);
}

// ---- Check sheet (routes/check_sheet.py) — T-08 to_dataset action ----

export interface ToDatasetRequestBody {
  created_at: string;
}

/** Materializes a saved CheckSheetArtifact's entries as a stored project
 * dataset (rubric R-MEA-06 #3: zero re-entry) -- the artifact must already
 * be saved; this operates on the persisted version, not a client draft. */
export function checkSheetToDataset(projectId: string, artifactId: string, body: ToDatasetRequestBody): Promise<DatasetMeta> {
  return request<DatasetMeta>(
    `/project/${encodeURIComponent(projectId)}/check-sheet/${encodeURIComponent(artifactId)}/to-dataset`,
    postJson(body),
  );
}

// ---- Time study (routes/time_study.py) — T-09 to_dataset action ----

export interface TimeStudyToDatasetRequestBody {
  element_id: string;
  created_at: string;
}

/** Materializes one work element's recorded cycle times as a stored
 * project dataset, feeding T-13 baseline with no re-typed copy. */
export function timeStudyToDataset(projectId: string, artifactId: string, body: TimeStudyToDatasetRequestBody): Promise<DatasetMeta> {
  return request<DatasetMeta>(
    `/project/${encodeURIComponent(projectId)}/time-study/${encodeURIComponent(artifactId)}/to-dataset`,
    postJson(body),
  );
}

// ---- Advisor (routes/advisor.py) — Layer 2, strictly optional ----

/** Assembles project context, calls the configured model, and returns the
 * answer + how the call was budgeted. A 409 (ApiError.status === 409)
 * means the advisor isn't configured or is turned off — always render
 * that as the plain-language unconfigured state, never as a generic
 * failure (M5 brief: Layer 2 is optional end to end). */
export function askAdvisor(body: AdvisorAskRequest): Promise<AdvisorAskResponse> {
  return request<AdvisorAskResponse>("/advisor/ask", postJson(body));
}

/** api_key_masked is last-4-only (or null) — never the real key. */
export function getAdvisorSettings(): Promise<AdvisorSettingsResponse> {
  return request<AdvisorSettingsResponse>("/advisor/settings");
}

/** Full-replace PUT: base_url/enabled are always taken as given.
 * api_key is the one write-only field — omit it (or send "") to leave the
 * stored key unchanged, since the GET response never hands the real key
 * back for a form to round-trip. */
export function putAdvisorSettings(body: AdvisorSettingsUpdateRequest): Promise<AdvisorSettingsResponse> {
  return request<AdvisorSettingsResponse>("/advisor/settings", putJson(body));
}

/** Cheap "is the advisor usable right now" check — no project context, no
 * API call to Anthropic. Safe to call on every tool screen mount. The
 * route takes no request body, unlike every other POST in this file. */
export function getAdvisorStatus(): Promise<AdvisorStatusResponse> {
  return request<AdvisorStatusResponse>("/advisor/status", { method: "POST" });
}

/** The validator pass (PLAN §5.3.6, anti-hallucination layer 6): a second,
 * cheaper-model call that reads `body` against the project's own data and
 * flags free-text claims it can't trace. Same 409-when-unconfigured
 * contract as askAdvisor. Never blocks a save — this never saves anything
 * itself; it's a separate, opt-in check the caller runs before its own
 * save call. */
export function validateAdvisor(body: AdvisorValidateRequest): Promise<ValidatorReport> {
  return request<ValidatorReport>("/advisor/validate", postJson(body));
}

/** The paste-ready chatbot export (M5 unit 4, PLAN §5.2): the tool's
 * portable prompt + the artifact's JSON + the engine-computed facts as one
 * copyable block. Works with NO key configured — no model call happens
 * anywhere behind this. Pass `{ mode: "tollgate", phase }` for the phase
 * variant (tool prompt swapped for the Champion prompt, artifact JSON
 * swapped for the phase's artifact summaries). */
export function getAdvisorExport(
  projectId: string,
  toolId: string,
  opts: { artifactId?: string; mode?: "tool" | "tollgate"; phase?: TollgatePhase } = {},
): Promise<AdvisorExportResponse> {
  const params = new URLSearchParams();
  if (opts.artifactId) params.set("artifact_id", opts.artifactId);
  if (opts.mode) params.set("mode", opts.mode);
  if (opts.phase) params.set("phase", opts.phase);
  const query = params.toString();
  return request<AdvisorExportResponse>(
    `/advisor/export/${encodeURIComponent(projectId)}/${encodeURIComponent(toolId)}${query ? `?${query}` : ""}`,
  );
}

// ---- diagnostics (main.py) ----

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export function getSmoke(): Promise<SmokeResponse> {
  return request<SmokeResponse>("/smoke");
}
