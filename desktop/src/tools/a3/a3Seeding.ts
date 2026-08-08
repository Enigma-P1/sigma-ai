import { loadArtifact } from "../../api/client";
import type {
  CharterArtifact, ControlPlanArtifact, FishboneArtifact, FmeaArtifact, FmeaCloseCheckInput,
  ProjectMetadata, ProofArtifact, SolutionMatrixArtifact,
} from "../../api/types";

export interface NarrativeDraft {
  narrative: string;
  fields: string[];
}

const FALLBACK = (toolId: string, artifactId: string): NarrativeDraft => ({
  narrative: `Seeded from ${toolId}/${artifactId} -- replace this with the narrative in your own words.`,
  fields: [],
});

/** Draft a starting narrative for a panel from its source artifact
 * (PLAN §4.1: "each panel pre-seeded from its source artifact and
 * editable"). Deterministic string composition only -- no AI, no
 * numbers invented, every sentence traces to a loaded field. Tool
 * shapes not covered below fall back to an honest placeholder that still
 * carries seeded_from provenance. */
export async function draftNarrativeFor(projectId: string, toolId: string, artifactId: string): Promise<NarrativeDraft> {
  try {
    const data = await loadArtifact(projectId, artifactId);
    if (toolId === "T-03") {
      const c = data as unknown as CharterArtifact;
      const p = c.problem_statement;
      return {
        narrative: `${p.what} at ${p.where}, ${p.when}: ${p.magnitude.number}${p.magnitude.unit} (${p.magnitude.period}). `
          + `Business impact: ${c.business_impact.amount} ${c.business_impact.unit} (${c.business_impact.basis}). Goal: ${c.goal.statement}`,
        fields: ["problem_statement", "business_impact", "goal"],
      };
    }
    if (toolId === "T-15") {
      const fb = data as unknown as FishboneArtifact;
      const causes = fb.verified_causes?.value.causes ?? [];
      return {
        narrative: causes.length ? `Verified cause(s): ${causes.map((c) => c.text).join("; ")}.` : "No verified causes recorded yet.",
        fields: ["verified_causes"],
      };
    }
    if (toolId === "T-18") {
      const sm = data as unknown as SolutionMatrixArtifact;
      const ranked = sm.ranked_fix_list?.value.ranked ?? [];
      return {
        narrative: ranked.length ? `Top-ranked countermeasure: ${ranked[0].name} (quadrant: ${ranked[0].quadrant}).` : "No ranked fixes yet.",
        fields: ["ranked_fix_list"],
      };
    }
    if (toolId === "T-20") {
      const proof = data as unknown as ProofArtifact;
      return { narrative: proof.verdict?.value.headline ?? "No proof result yet.", fields: ["verdict"] };
    }
    if (toolId === "T-22") {
      const cp = data as unknown as ControlPlanArtifact;
      const health = cp.plan_health?.value;
      return {
        narrative: health?.is_theater
          ? `Control plan flags ${health.ownerless_item_ids.length} ownerless item(s) -- fix before this reads as sustained.`
          : "Every monitored item has a named, accepted owner; the fix is being watched.",
        fields: ["plan_health"],
      };
    }
    return FALLBACK(toolId, artifactId);
  } catch {
    return FALLBACK(toolId, artifactId);
  }
}

/** Resolve the project's latest T-16 FMEA into the closure panel's
 * FmeaCloseCheckInput (a3.py module docstring: caller-resolved snapshot
 * of the FMEA's own computed blocking_flags). Null when no FMEA is saved
 * yet -- the closure panel then shows nothing to check, not an error. */
export async function resolveFmeaCheck(projectId: string, project: ProjectMetadata): Promise<FmeaCloseCheckInput | null> {
  const fmeaArtifactId = Object.keys(project.artifact_index).find((id) => project.artifact_index[id]?.tool_id === "T-16");
  if (!fmeaArtifactId) return null;
  try {
    const data = (await loadArtifact(projectId, fmeaArtifactId)) as unknown as FmeaArtifact;
    return { fmea_artifact_id: fmeaArtifactId, blocking_flags: data.blocking_flags?.value ?? [] };
  } catch {
    return null;
  }
}
