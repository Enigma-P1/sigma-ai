import { toFloatOrNull } from "../hypothesis/hypothesisParsing";
import { ARTIFACT_ID, SCHEMA_VERSION } from "./proofState";
import type { ProofState } from "./proofState";
import type { NextCauseRef, ProofArtifact, RankedEntry, VerifiedCauseEntry } from "../../api/types";

/** Assembles the T-20 save body. Every echoed field (pilot_ref, the
 * declared threshold, confounders, charter baseline/goal, next_cause_ref)
 * is copied in from an already-loaded artifact by useProofForm -- this
 * module stays pure (state in, JSON body out), matching every other
 * *Logic.ts body-builder in this app. */
export function buildProofBody(
  state: ProofState, resolvedBefore: number[], resolvedAfter: number[], nowIso: string, serverArtifact: ProofArtifact | null,
): Record<string, unknown> {
  const guardrails = state.guardrailMetricRef.trim()
    ? [{
      metric_ref: state.guardrailMetricRef.trim(), direction: state.guardrailDirection,
      before_value: Number(state.guardrailBeforeText) || 0, after_value: Number(state.guardrailAfterText) || 0,
    }]
    : [];

  return {
    schema_version: SCHEMA_VERSION, artifact_id: ARTIFACT_ID, tool_id: "T-20",
    created_at: serverArtifact?.created_at ?? nowIso, updated_at: nowIso,
    pilot_ref: state.pilotRef.trim(),
    metric_ref: state.metricRef.trim(),
    operational_definition_ref: state.operationalDefinitionRef.trim(),
    measurement_system_ref: state.measurementSystemRef.trim(),
    usl: toFloatOrNull(state.uslText), lsl: toFloatOrNull(state.lslText), operational_definition_ok: true,
    before: {
      values: resolvedBefore, dataset_id: state.before.mode === "dataset" ? state.before.datasetId || null : null,
      column: state.before.mode === "dataset" ? state.before.column || null : null,
    },
    after: {
      values: resolvedAfter, dataset_id: state.after.mode === "dataset" ? state.after.datasetId || null : null,
      column: state.after.mode === "dataset" ? state.after.column || null : null,
    },
    declared_threshold: {
      metric_ref: state.metricRef.trim(), direction: state.thresholdDirection,
      value: Number(state.thresholdValue) || 0, declared_at: nowIso,
    },
    confounders: state.confounders,
    declared_package: state.declaredPackage,
    guardrails,
    charter_ref: state.charterRef.trim(),
    charter_baseline_value: Number(state.charterBaselineText) || 0,
    charter_goal_value: Number(state.charterGoalText) || 0,
    charter_goal_direction: state.charterGoalDirection,
    next_cause_ref: state.nextCauseRef,
  };
}

/** Mirrors artifacts/proof.py's find_next_cause() (engine-authoritative;
 * this is the same live-draft-preview mirroring solutionMatrixLogic.ts's
 * quadrant computation already does elsewhere in this app) -- walks T-18's
 * ranked_fix_list (already rank-ordered) for the first linked cause that
 * is verified (T-15) and not yet piloted. */
export function findNextCauseClientSide(
  ranked: RankedEntry[], verifiedCauses: VerifiedCauseEntry[], pilotedCauseIds: string[],
): NextCauseRef | null {
  const verifiedTextById = new Map(verifiedCauses.map((c) => [c.cause_id, c.text]));
  const piloted = new Set(pilotedCauseIds);
  for (const sol of [...ranked].sort((a, b) => a.rank - b.rank)) {
    for (const cid of sol.linked_cause_ids) {
      const text = verifiedTextById.get(cid);
      if (text && !piloted.has(cid)) {
        return { cause_id: cid, cause_text: text, via_solution_id: sol.solution_id, via_solution_name: sol.name, rank: sol.rank };
      }
    }
  }
  return null;
}
