import { useEffect, useState } from "react";
import { loadArtifact } from "../../api/client";
import type { ControlChartArtifact, FrozenLimitsRef, ProjectMetadata } from "../../api/types";

export const CONTROL_CHART_ARTIFACT_ID = "control-chart"; // T-21's fixed single-instance id (controlChartState.ts)

/** T-21's frozen baseline -> T-22's FrozenLimitsRef (module docstring of
 * control_plan.py: the caller-resolved snapshot, copied once, never
 * recomputed by this artifact). Null whenever T-21 hasn't frozen yet. */
function frozenLimitsFromControlChart(cc: ControlChartArtifact): FrozenLimitsRef | null {
  if (cc.imr_baseline) {
    const b = cc.imr_baseline.value;
    return { control_chart_artifact_id: CONTROL_CHART_ARTIFACT_ID, chart_type: "imr", center: b.i_cl, ucl: b.i_ucl, lcl: b.i_lcl, p_bar: null, frozen_at: cc.frozen_at ?? "" };
  }
  if (cc.p_baseline) {
    return { control_chart_artifact_id: CONTROL_CHART_ARTIFACT_ID, chart_type: "p", center: null, ucl: null, lcl: null, p_bar: cc.p_baseline.value.p_bar, frozen_at: cc.frozen_at ?? "" };
  }
  return null;
}

/** Best-effort loads the project's saved T-21 control chart and resolves
 * its frozen band -- split out of useControlPlanForm.ts (file-size split,
 * not a behavior change). Null whenever no chart is frozen yet -- the
 * check-in panel explains what's missing. */
export function useFrozenLimits(projectId: string, project: ProjectMetadata): FrozenLimitsRef | null {
  const [frozenLimits, setFrozenLimits] = useState<FrozenLimitsRef | null>(null);

  useEffect(() => {
    if (!project.artifact_index[CONTROL_CHART_ARTIFACT_ID]) return;
    let cancelled = false;
    loadArtifact(projectId, CONTROL_CHART_ARTIFACT_ID)
      .then((data) => {
        if (!cancelled) setFrozenLimits(frozenLimitsFromControlChart(data as unknown as ControlChartArtifact));
      })
      .catch(() => {
        /* no control chart yet -- the check-in panel explains what's missing */
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, project.artifact_index]);

  return frozenLimits;
}
