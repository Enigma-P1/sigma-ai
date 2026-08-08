import { Field, Panel, TextArea } from "../../design/components";

export interface FalsificationSectionProps {
  value: string;
  onChange: (v: string) => void;
}

/** Step 4: "what would prove this DIDN'T work" (rubric R-IMP-02 #4) -- the
 * one line the whole pilot can be judged against. The helper text carries
 * the teeth: prescore/pilot_plan.py flags a line under 25 characters or a
 * bare negation like the rubric's own bad example. */
export function FalsificationSection({ value, onChange }: FalsificationSectionProps) {
  return (
    <Panel title="4. Falsification line" subtitle="What would prove this didn't work?">
      <Field
        label="If this fix doesn't actually work, what specifically would show it?" htmlFor="pilot-falsification" required
        helper={
          <>
            Name a metric, a threshold, and a window: &ldquo;if scrap rate stays above 4.5% for two full weeks after
            rollout, this did not fix it.&rdquo; Too thin and the tool flags it: &ldquo;if it doesn&rsquo;t
            work&rdquo; says nothing a reviewer could check.
          </>
        }
      >
        <TextArea id="pilot-falsification" data-testid="pilot-falsification" rows={3} value={value} onChange={(e) => onChange(e.target.value)} />
      </Field>
    </Panel>
  );
}
