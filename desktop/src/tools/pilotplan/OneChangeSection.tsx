import { Button, Field, Panel, TextArea, TextInput, VerdictBanner } from "../../design/components";
import type { PilotChange } from "../../api/types";

export interface OneChangeSectionProps {
  statement: string;
  linkedSolutionId: string | null;
  extraChanges: PilotChange[];
  exitError: string | null;
  /** True whenever a declared package (DeclaredPackageSection) is active --
   * `changes` is then derived from the package's own components list
   * (pilotPlanLogic.ts's changesFromState), so the "+ add another change"
   * EXIT-10 demo affordance is hidden here rather than offering two ways
   * to grow the same list. */
  packageActive: boolean;
  onStatementChange: (v: string) => void;
  onAddExtraChange: () => void;
  onUpdateExtraChange: (index: number, next: PilotChange) => void;
  onRemoveExtraChange: (index: number) => void;
}

/** Step 1 of the guided flow: ONE change, stated in one sentence (rubric
 * R-IMP-02 #1) -- the study's whole reason for existing. The "+ describe
 * another change" affordance is deliberate: it lets a student try to
 * bundle a second change and see the engine refuse it by name (EXIT-10,
 * artifacts/pilot_plan.py) rather than silently accept a fix nobody could
 * later attribute -- remove the extra entry and the plan saves clean. */
export function OneChangeSection({
  statement, linkedSolutionId, extraChanges, exitError, packageActive,
  onStatementChange, onAddExtraChange, onUpdateExtraChange, onRemoveExtraChange,
}: OneChangeSectionProps) {
  return (
    <Panel title="1. The one change" subtitle="One sentence. Not a bundle of fixes.">
      <Field
        label={packageActive ? "Describe the package as a whole" : "What are you changing?"} htmlFor="pilot-statement" required
        helper={
          packageActive
            ? "The package's own summary sentence -- the components themselves are listed below, in the declared-package section."
            : linkedSolutionId ? `Pre-filled from the top-ranked fix list entry (${linkedSolutionId}) -- edit freely.` : "Pick the top item from T-18's ranked fix list, or describe your own change."
        }
      >
        <TextArea id="pilot-statement" data-testid="pilot-statement" rows={2} value={statement} onChange={(e) => onStatementChange(e.target.value)} placeholder="Add a fixture alignment checklist before each shift" />
      </Field>

      {!packageActive && (
        extraChanges.length === 0 ? (
          <Button variant="ghost" size="sm" type="button" onClick={onAddExtraChange} data-testid="pilot-add-another-change">
            + Describe another change (to see why the tool says no)
          </Button>
        ) : (
          <div className="sigma-pilot-extra-changes">
            {extraChanges.map((c, i) => (
              <div className="sigma-pilot-extra-change-row" key={c.change_id}>
                <TextInput
                  data-testid={`pilot-extra-change-${i}`} value={c.text}
                  onChange={(e) => onUpdateExtraChange(i, { ...c, text: e.target.value })}
                  placeholder="A second, different change"
                />
                <Button variant="ghost" size="sm" type="button" onClick={() => onRemoveExtraChange(i)} data-testid={`pilot-remove-extra-change-${i}`}>
                  Remove -- keep to one change
                </Button>
              </div>
            ))}
          </div>
        )
      )}

      {exitError && (
        <div data-testid="pilot-exit10-banner">
          <VerdictBanner tone="exit" headline="EXIT-10: more than one change in this pilot" detail={exitError} />
        </div>
      )}
    </Panel>
  );
}
