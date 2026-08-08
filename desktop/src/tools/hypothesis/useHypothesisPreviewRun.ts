import { useState } from "react";
import { routeHypothesis, runHypothesis } from "../../api/client";
import { ApiError } from "../../api/errors";
import { buildHypothesisRequest } from "./hypothesisRequestBuilder";
import { missingFieldsForPreview } from "./hypothesisValidation";
import type { HypothesisFormState } from "./hypothesisFormState";
import type { DatasetDetail, DatasetProvenance, HypRoutingDecision, HypothesisRunResult } from "../../api/types";

/** T-17's two-step engine wiring (build brief): Preview calls /route
 * (routing only, safe to call speculatively); Run calls /run (routes +
 * computes in one call, refusing honestly when an exit fires -- and
 * costing nothing extra past a raised exit, so it's offered even then:
 * recognizing an exit is a pass, rubric R-ANA-04 #3, not a dead end). */
export function useHypothesisPreviewRun(state: HypothesisFormState, projectId: string, getDatasetDetailCached: (id: string) => Promise<DatasetDetail>) {
  const [previewing, setPreviewing] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [routing, setRouting] = useState<HypRoutingDecision | null>(null);
  const [derivedNotes, setDerivedNotes] = useState<string[]>([]);
  const [routeProvenance, setRouteProvenance] = useState<DatasetProvenance[] | undefined>(undefined);

  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [runResult, setRunResult] = useState<HypothesisRunResult | null>(null);

  /** Called by the outer form hook whenever a question/data field changes
   * -- never show a stale tree or result for edited inputs. */
  function reset() {
    setRouting(null);
    setRunResult(null);
  }

  const missingForPreview = missingFieldsForPreview(state);
  const canPreview = missingForPreview.length === 0 && !previewing;

  async function handlePreview() {
    if (!canPreview) return;
    setPreviewing(true);
    setPreviewError(null);
    try {
      const { body, notes } = await buildHypothesisRequest(state, projectId, getDatasetDetailCached);
      const resp = await routeHypothesis(body);
      setRouting(resp);
      setDerivedNotes(notes);
      setRouteProvenance(resp.dataset_provenance);
    } catch (err) {
      setPreviewError(err instanceof ApiError ? err.message : "Could not preview the decision tree.");
      setRouting(null);
    } finally {
      setPreviewing(false);
    }
  }

  const canRun = routing != null && !running;

  async function handleRun() {
    if (!canRun) return;
    setRunning(true);
    setRunError(null);
    try {
      const { body, notes } = await buildHypothesisRequest(state, projectId, getDatasetDetailCached);
      const resp = await runHypothesis(body);
      setRunResult(resp);
      setRouting(resp.routing);
      setDerivedNotes(notes);
    } catch (err) {
      setRunError(err instanceof ApiError ? err.message : "Could not run the test.");
    } finally {
      setRunning(false);
    }
  }

  return {
    previewing, previewError, routing, setRouting, derivedNotes, routeProvenance, missingForPreview, canPreview, handlePreview,
    running, runError, runResult, canRun, handleRun, reset,
  };
}
