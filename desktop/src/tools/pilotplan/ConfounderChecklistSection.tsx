import { Field, Panel, TextInput, YesNoToggle } from "../../design/components";
import type { PilotConfounderAnswer, PilotConfounderChecklist } from "../../api/types";

export interface ConfounderChecklistSectionProps {
  value: PilotConfounderChecklist;
  onChange: (next: PilotConfounderChecklist) => void;
}

const ROWS: { key: keyof PilotConfounderChecklist; label: string; placeholder: string }[] = [
  { key: "staffing", label: "Staffing changed?", placeholder: "No staffing changes planned during the window." },
  { key: "season", label: "Season/demand pattern changed?", placeholder: "No seasonal shift expected." },
  { key: "demand", label: "Demand/volume changed?", placeholder: "Order volume steady." },
  { key: "measurement", label: "Measurement changed?", placeholder: "Same log, same operational definition." },
  { key: "other", label: "Anything else changed?", placeholder: "None identified." },
];

/** Step 5: the plain-English confounder checklist (rubric R-IMP-02 #5) --
 * answered up front here, re-answered at T-20's proof against what
 * actually happened. All five required at the schema level; the notes
 * are what prescore's checklist_completeness actually grades. */
export function ConfounderChecklistSection({ value, onChange }: ConfounderChecklistSectionProps) {
  function updateRow(key: keyof PilotConfounderChecklist, patch: Partial<PilotConfounderAnswer>) {
    onChange({ ...value, [key]: { ...value[key], ...patch } });
  }

  return (
    <Panel title="5. Confounder checklist" subtitle="Anything else that could explain a change in the numbers?">
      {ROWS.map(({ key, label, placeholder }) => (
        <Field key={key} label={label} htmlFor={`pilot-confounder-${key}-note`}>
          <div className="sigma-pilot-confounder-row">
            <YesNoToggle name={`pilot-confounder-${key}`} value={value[key].changed} onChange={(v) => updateRow(key, { changed: v })} />
            <TextInput
              id={`pilot-confounder-${key}-note`} data-testid={`pilot-confounder-${key}-note`}
              value={value[key].note} onChange={(e) => updateRow(key, { note: e.target.value })} placeholder={placeholder}
            />
          </div>
        </Field>
      ))}
    </Panel>
  );
}
