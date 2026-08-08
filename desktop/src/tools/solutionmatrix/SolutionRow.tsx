import { Field, SelectInput, StatusPill, TextArea, TextInput } from "../../design/components";
import type { Solution, SolutionCriterion, SolutionScore, VerifiedCauseEntry } from "../../api/types";
import { draftQuadrant, draftWeightedTotal, genId, QUADRANT_LABELS } from "./solutionMatrixLogic";

export interface SolutionRowProps {
  solution: Solution;
  index: number;
  criteria: SolutionCriterion[];
  verifiedCauses: VerifiedCauseEntry[];
  /** The engine's own computed view for this solution, once a version has
   * round-tripped -- authoritative over the client draft when present
   * (FmeaWorksheet's serverAmount precedent). */
  serverScore: SolutionScore | undefined;
  onChange: (next: Solution) => void;
}

const RATING_OPTIONS = [1, 2, 3, 4, 5];

/** One solution's editable row: name/description, the verified-causes
 * picker (checkboxes over T-15's summary, plus a manual fallback), the
 * impact/effort selects rendering the quadrant live, and an optional
 * per-criterion score grid once the matrix has criteria declared. */
export function SolutionRow({ solution, index, criteria, verifiedCauses, serverScore, onChange }: SolutionRowProps) {
  const quadrant = serverScore?.quadrant ?? draftQuadrant(solution.impact, solution.effort);
  const isDraftQuadrant = !serverScore;
  const weightedTotal = serverScore ? serverScore.weighted_total : draftWeightedTotal(solution, criteria);

  function toggleCause(causeId: string, checked: boolean) {
    const next = checked ? [...solution.linked_cause_ids, causeId] : solution.linked_cause_ids.filter((c) => c !== causeId);
    onChange({ ...solution, linked_cause_ids: next });
  }

  function setScore(criterionId: string, score: number) {
    const existing = solution.criterion_scores.filter((sc) => sc.criterion_id !== criterionId);
    onChange({ ...solution, criterion_scores: [...existing, { criterion_id: criterionId, score, scored_at: new Date().toISOString() }] });
  }

  function scoreFor(criterionId: string): number | "" {
    return solution.criterion_scores.find((sc) => sc.criterion_id === criterionId)?.score ?? "";
  }

  return (
    <div className="sigma-solmatrix-row" data-testid={`solmatrix-row-${index}`}>
      <Field label="Solution name" htmlFor={`solmatrix-${index}-name`}>
        <TextInput id={`solmatrix-${index}-name`} data-testid={`solmatrix-${index}-name`} value={solution.name} onChange={(e) => onChange({ ...solution, name: e.target.value })} placeholder="Add a fixture alignment checklist" />
      </Field>
      <Field label="Description" htmlFor={`solmatrix-${index}-description`}>
        <TextArea id={`solmatrix-${index}-description`} data-testid={`solmatrix-${index}-description`} value={solution.description} onChange={(e) => onChange({ ...solution, description: e.target.value })} rows={2} />
      </Field>

      <Field label="Linked verified cause(s)" helper={verifiedCauses.length === 0 ? "No verified causes on file yet -- link by id below, or verify a cause on T-15 first." : undefined}>
        {verifiedCauses.length > 0 && (
          <div className="sigma-solmatrix-causes" role="group" aria-label={`Linked causes for ${solution.name || "this solution"}`}>
            {verifiedCauses.map((c) => (
              <label key={c.cause_id} className="sigma-solmatrix-cause-option">
                <input
                  type="checkbox"
                  data-testid={`solmatrix-${index}-cause-${c.cause_id}`}
                  checked={solution.linked_cause_ids.includes(c.cause_id)}
                  onChange={(e) => toggleCause(c.cause_id, e.target.checked)}
                />
                {c.text}
              </label>
            ))}
          </div>
        )}
        <ManualCauseLink index={index} linkedCauseIds={solution.linked_cause_ids} onLink={(id) => toggleCause(id, true)} onUnlink={(id) => toggleCause(id, false)} />
      </Field>

      <div className="sigma-solmatrix-ratings">
        <Field label="Impact (1-5)" htmlFor={`solmatrix-${index}-impact`}>
          <SelectInput id={`solmatrix-${index}-impact`} data-testid={`solmatrix-${index}-impact`} value={solution.impact} onChange={(e) => onChange({ ...solution, impact: Number(e.target.value) })}>
            {RATING_OPTIONS.map((n) => <option key={n} value={n}>{n}</option>)}
          </SelectInput>
        </Field>
        <Field label="Effort (1-5)" htmlFor={`solmatrix-${index}-effort`}>
          <SelectInput id={`solmatrix-${index}-effort`} data-testid={`solmatrix-${index}-effort`} value={solution.effort} onChange={(e) => onChange({ ...solution, effort: Number(e.target.value) })}>
            {RATING_OPTIONS.map((n) => <option key={n} value={n}>{n}</option>)}
          </SelectInput>
        </Field>
        <div className="sigma-solmatrix-quadrant" data-testid={`solmatrix-${index}-quadrant`}>
          <StatusPill tone="accent" label={`${QUADRANT_LABELS[quadrant]}${isDraftQuadrant ? " (draft)" : ""}`} dot={false} />
          {weightedTotal != null && <span className="sigma-solmatrix-weighted" data-testid={`solmatrix-${index}-weighted-total`}>weighted: {weightedTotal}{isDraftQuadrant ? " (draft)" : ""}</span>}
        </div>
      </div>

      {criteria.length > 0 && (
        <Field label="Criteria scores (1-5 each -- score all or leave all blank)">
          <div className="sigma-solmatrix-criteria-scores">
            {criteria.map((c) => (
              <label key={c.criterion_id} className="sigma-solmatrix-criterion-score">
                {c.name || c.criterion_id}
                <SelectInput data-testid={`solmatrix-${index}-score-${c.criterion_id}`} value={scoreFor(c.criterion_id)} onChange={(e) => setScore(c.criterion_id, Number(e.target.value))}>
                  <option value="">--</option>
                  {RATING_OPTIONS.map((n) => <option key={n} value={n}>{n}</option>)}
                </SelectInput>
              </label>
            ))}
          </div>
        </Field>
      )}
    </div>
  );
}

function ManualCauseLink({ index, linkedCauseIds, onLink, onUnlink }: { index: number; linkedCauseIds: string[]; onLink: (id: string) => void; onUnlink: (id: string) => void }) {
  return (
    <div className="sigma-solmatrix-manual-cause">
      <TextInput
        data-testid={`solmatrix-${index}-manual-cause-input`}
        placeholder="Or type a cause id and press Enter"
        onKeyDown={(e) => {
          const value = (e.target as HTMLInputElement).value.trim();
          if (e.key === "Enter" && value) {
            onLink(value);
            (e.target as HTMLInputElement).value = "";
            e.preventDefault();
          }
        }}
      />
      {linkedCauseIds.length > 0 && (
        <ul className="sigma-solmatrix-linked-ids" data-testid={`solmatrix-${index}-linked-ids`}>
          {linkedCauseIds.map((id) => (
            <li key={id || genId("linked")}>
              {id}{" "}
              <button type="button" onClick={() => onUnlink(id)} aria-label={`Unlink ${id}`}>
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
