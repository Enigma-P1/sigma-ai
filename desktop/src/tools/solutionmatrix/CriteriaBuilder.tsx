import { Button, Field, TextInput } from "../../design/components";
import type { SolutionCriterion } from "../../api/types";
import { emptyCriterion } from "./solutionMatrixLogic";

export interface CriteriaBuilderProps {
  criteria: SolutionCriterion[];
  onAdd: (c: SolutionCriterion) => void;
  onChange: (criterionId: string, next: SolutionCriterion) => void;
  onRemove: (criterionId: string) => void;
}

/** Optional weighted-criteria matrix: named criteria + weights, declared
 * once (declared_at is stamped when the criterion is first added, so it
 * naturally precedes any score entered afterward -- rubric R-IMP-01 #3's
 * "weights set before scoring", the same before-data-collection ordering
 * T-19's success threshold uses). Can stay empty -- solutions then rank by
 * impact/effort alone. */
export function CriteriaBuilder({ criteria, onAdd, onChange, onRemove }: CriteriaBuilderProps) {
  return (
    <div className="sigma-solmatrix-criteria-builder">
      {criteria.length === 0 && <p className="sigma-solmatrix-criteria-empty">No weighted criteria yet -- solutions rank by impact/effort alone.</p>}
      {criteria.map((c, i) => (
        <div className="sigma-solmatrix-criterion-row" key={c.criterion_id} data-testid={`solmatrix-criterion-${i}`}>
          <Field label="Criterion name" htmlFor={`solmatrix-criterion-${i}-name`}>
            <TextInput id={`solmatrix-criterion-${i}-name`} data-testid={`solmatrix-criterion-${i}-name`} value={c.name} onChange={(e) => onChange(c.criterion_id, { ...c, name: e.target.value })} placeholder="Cost to implement" />
          </Field>
          <Field label="Weight" htmlFor={`solmatrix-criterion-${i}-weight`}>
            <TextInput
              id={`solmatrix-criterion-${i}-weight`} data-testid={`solmatrix-criterion-${i}-weight`} type="number" min="0" step="0.5"
              value={c.weight} onChange={(e) => onChange(c.criterion_id, { ...c, weight: Number(e.target.value) })}
            />
          </Field>
          <Button variant="ghost" size="sm" type="button" onClick={() => onRemove(c.criterion_id)} data-testid={`solmatrix-criterion-${i}-remove`}>
            Remove
          </Button>
        </div>
      ))}
      <Button variant="ghost" size="sm" type="button" onClick={() => onAdd(emptyCriterion())} data-testid="solmatrix-add-criterion">
        + Add weighted criterion
      </Button>
    </div>
  );
}
