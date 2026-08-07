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
  GateResult,
  HealthResponse,
  OverrideLogEntry,
  PrescoreResult,
  ProjectMetadata,
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

// ---- diagnostics (main.py) ----

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export function getSmoke(): Promise<SmokeResponse> {
  return request<SmokeResponse>("/smoke");
}
