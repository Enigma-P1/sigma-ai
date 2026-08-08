import { Button, MissingHint, Panel, VerdictBanner } from "../../design/components";
import { PrescoreStrip } from "../PrescoreStrip";
import { CriteriaBuilder } from "./CriteriaBuilder";
import { RankedFixListPanel } from "./RankedFixListPanel";
import { SolutionRow } from "./SolutionRow";
import { SOLUTION_MATRIX_CHECK_LABELS } from "./solutionMatrixChecks";
import { emptySolution, solutionMatrixMissingFields } from "./solutionMatrixLogic";
import { useSolutionMatrixForm } from "./useSolutionMatrixForm";
import type { ProjectMetadata } from "../../api/types";
import "./SolutionMatrixForm.css";

export interface SolutionMatrixFormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
}

/** T-18 Solution Selection Matrix: candidate solutions for the top-ranked
 * verified cause, an impact/effort quadrant rendered live from the ratings,
 * an optional weighted-criteria matrix, and the engine's ranked fix list --
 * the queue the Improve loop works through. Every mutation goes through
 * useSolutionMatrixForm; the quadrant/weighted-total/ranking render as
 * drafts (labeled) before the first save, then as the engine's own
 * computed values once a version has round-tripped (FmeaForm's precedent). */
export function SolutionMatrixForm({ projectId, project, onSaved }: SolutionMatrixFormProps) {
  const f = useSolutionMatrixForm(projectId, project, onSaved);
  const scoresById = new Map((f.serverArtifact?.scores?.value ?? []).map((s) => [s.solution_id, s]));

  return (
    <Panel title="Solution Selection Matrix" right={f.version != null && <span data-testid="solmatrix-version-badge">v{f.version} saved</span>}>
      <p>
        List candidate solutions for your top-ranked verified cause -- at least two, so this is a real comparison, not a
        rubber stamp. Every solution links to the cause(s) it addresses; an unlinked solution is flagged and never enters
        the ranked list. Impact and effort (1-5 each) render a live quadrant; an optional weighted-criteria matrix adds a
        second, more precise ranking on top.
      </p>

      <Panel title="Weighted criteria (optional)" collapsible defaultOpen={f.criteria.length > 0}>
        <CriteriaBuilder criteria={f.criteria} onAdd={f.addCriterion} onChange={f.updateCriterion} onRemove={f.removeCriterion} />
      </Panel>

      <Panel title="Solutions">
        {f.solutions.map((s, i) => (
          <SolutionRow
            key={s.solution_id} solution={s} index={i} criteria={f.criteria} verifiedCauses={f.verifiedCauses}
            serverScore={scoresById.get(s.solution_id)} onChange={(next) => f.updateSolution(s.solution_id, next)}
          />
        ))}
        <div className="sigma-solmatrix-row-actions">
          <Button variant="ghost" size="sm" type="button" onClick={() => f.addSolution(emptySolution())} data-testid="solmatrix-add-solution">
            + Add solution
          </Button>
          {f.solutions.length > 0 && (
            <Button variant="ghost" size="sm" type="button" onClick={() => f.removeSolution(f.solutions[f.solutions.length - 1].solution_id)} data-testid="solmatrix-remove-last-solution">
              Remove last
            </Button>
          )}
        </div>
      </Panel>

      {f.generalError && <VerdictBanner tone="fail" headline={f.generalError} />}

      <div className="sigma-solmatrix-save-row">
        <Button variant="primary" disabled={!f.canSave} onClick={() => void f.handleSave()} data-testid="solmatrix-save">
          {f.saving ? "Saving…" : f.version != null ? "Save new version" : "Save"}
        </Button>
        {!f.saving && <MissingHint fields={solutionMatrixMissingFields(f.solutions)} />}
      </div>

      <PrescoreStrip results={f.prescore} labels={SOLUTION_MATRIX_CHECK_LABELS} />

      <RankedFixListPanel rankedFixList={f.serverArtifact?.ranked_fix_list} saved={f.version != null} />
    </Panel>
  );
}
