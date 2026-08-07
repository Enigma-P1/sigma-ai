import { Field, Panel, SelectInput, TextInput } from "../../design/components";
import type { FieldFlag } from "../../design/components";
import { DynamicList } from "./DynamicList";
import type { RiskLevel, RiskRow } from "../../api/types";

export interface RisksSectionProps {
  value: RiskRow[];
  onChange: (v: RiskRow[]) => void;
  flag?: FieldFlag;
}

const emptyRisk = (): RiskRow => ({ risk: "", likelihood: "medium", impact: "medium", mitigation: "", owner: "" });
const LEVELS: RiskLevel[] = ["low", "medium", "high"];

/** Key risks & mitigations (matrix §5a correction A-4). Can start empty --
 * the schema allows it, prescore flags it (charterChecks.ts). */
export function RisksSection({ value, onChange, flag }: RisksSectionProps) {
  return (
    <Panel title="Key risks & mitigations" subtitle="What could derail this, and who owns watching for it?">
      <Field label="Risks" flag={flag}>
        <DynamicList
          items={value}
          onChange={onChange}
          makeEmpty={emptyRisk}
          addLabel="+ Add risk"
          renderRow={(risk, i, update) => (
            <>
              <TextInput
                data-testid={`charter-risk-${i}-risk`}
                value={risk.risk}
                onChange={(e) => update({ ...risk, risk: e.target.value })}
                placeholder="Key operator on leave during pilot"
              />
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-2)" }}>
                <SelectInput
                  data-testid={`charter-risk-${i}-likelihood`}
                  value={risk.likelihood}
                  onChange={(e) => update({ ...risk, likelihood: e.target.value as RiskLevel })}
                >
                  {LEVELS.map((l) => (
                    <option key={l} value={l}>
                      Likelihood: {l}
                    </option>
                  ))}
                </SelectInput>
                <SelectInput
                  data-testid={`charter-risk-${i}-impact`}
                  value={risk.impact}
                  onChange={(e) => update({ ...risk, impact: e.target.value as RiskLevel })}
                >
                  {LEVELS.map((l) => (
                    <option key={l} value={l}>
                      Impact: {l}
                    </option>
                  ))}
                </SelectInput>
              </div>
              <TextInput
                data-testid={`charter-risk-${i}-mitigation`}
                value={risk.mitigation}
                onChange={(e) => update({ ...risk, mitigation: e.target.value })}
                placeholder="Mitigation"
              />
              <TextInput
                data-testid={`charter-risk-${i}-owner`}
                value={risk.owner}
                onChange={(e) => update({ ...risk, owner: e.target.value })}
                placeholder="Owner"
              />
            </>
          )}
        />
      </Field>
    </Panel>
  );
}
