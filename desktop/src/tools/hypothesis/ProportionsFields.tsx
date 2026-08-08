import { Button, Field, TextInput } from "../../design/components";
import { emptyProportionGroup } from "./hypothesisFormState";
import type { ProportionGroupValue } from "./hypothesisFormState";
import "./HypothesisForm.css";

export interface ProportionsFieldsProps {
  groups: ProportionGroupValue[];
  onGroupsChange: (groups: ProportionGroupValue[]) => void;
  targetText: string;
  onTargetChange: (v: string) => void;
}

/** One proportion vs. a target (pass rate vs. a spec), or two proportions
 * against each other -- successes/n per group, exactly matching
 * GroupInput's successes+n input path (hypothesis_common.group_successes_n),
 * no need to fabricate a fake per-unit 0/1 array. */
export function ProportionsFields({ groups, onGroupsChange, targetText, onTargetChange }: ProportionsFieldsProps) {
  function updateGroup(i: number, next: ProportionGroupValue) {
    onGroupsChange(groups.map((g, idx) => (idx === i ? next : g)));
  }

  return (
    <>
      {groups.map((g, i) => (
        <div className="sigma-hyp-row" key={i} data-testid={`hyp-proportion-group-${i}`}>
          <Field label="Label" htmlFor={`hyp-prop-${i}-label`}>
            <TextInput id={`hyp-prop-${i}-label`} data-testid={`hyp-prop-${i}-label`} value={g.label} onChange={(e) => updateGroup(i, { ...g, label: e.target.value })} />
          </Field>
          <Field label="Successes" required htmlFor={`hyp-prop-${i}-successes`} helper="How many units passed / had the outcome.">
            <TextInput id={`hyp-prop-${i}-successes`} data-testid={`hyp-prop-${i}-successes`} type="number" value={g.successesText} onChange={(e) => updateGroup(i, { ...g, successesText: e.target.value })} />
          </Field>
          <Field label="n (total units)" required htmlFor={`hyp-prop-${i}-n`}>
            <TextInput id={`hyp-prop-${i}-n`} data-testid={`hyp-prop-${i}-n`} type="number" value={g.nText} onChange={(e) => updateGroup(i, { ...g, nText: e.target.value })} />
          </Field>
          {groups.length > 1 && (
            <Button variant="ghost" size="sm" onClick={() => onGroupsChange(groups.filter((_, idx) => idx !== i))}>Remove</Button>
          )}
        </div>
      ))}

      {groups.length === 1 ? (
        <>
          <Field label="Target proportion (0-1)" required htmlFor="hyp-prop-target" helper="e.g. 0.05 for a 5% target rate.">
            <TextInput id="hyp-prop-target" data-testid="hyp-prop-target" type="number" step="0.01" min={0} max={1} value={targetText} onChange={(e) => onTargetChange(e.target.value)} />
          </Field>
          <Button variant="ghost" size="sm" data-testid="hyp-prop-add-group" onClick={() => onGroupsChange([...groups, emptyProportionGroup("Group B")])}>
            + Compare against a second group instead of a target
          </Button>
        </>
      ) : (
        <p className="sigma-hyp-hint">Comparing two groups directly -- no target needed.</p>
      )}
    </>
  );
}
