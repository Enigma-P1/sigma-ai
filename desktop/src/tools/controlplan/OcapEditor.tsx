import { Button, Field, Panel, TextInput } from "../../design/components";
import type { OcapEntry } from "../../api/types";

export interface OcapEditorProps {
  entries: OcapEntry[];
  onChange: (ocapId: string, patch: Partial<OcapEntry>) => void;
  onRemove: (ocapId: string) => void;
}

/** The out-of-control action path, per monitored item: trigger signal ->
 * exact action_steps -> escalation contact -> acting owner (rubric
 * R-CTL-04 #1's four concrete elements). */
export function OcapEditor({ entries, onChange, onRemove }: OcapEditorProps) {
  if (entries.length === 0) return null;
  return (
    <Panel title="Response Plan (OCAP)" subtitle="What happens the moment a signal fires">
      {entries.map((o) => (
        <div key={o.ocap_id} className="sigma-controlplan-ocap-row" data-testid={`controlplan-ocap-${o.ocap_id}`}>
          <Field label="Trigger signal" htmlFor={`ocap-${o.ocap_id}-trigger`}>
            <TextInput id={`ocap-${o.ocap_id}-trigger`} value={o.trigger_signal} onChange={(e) => onChange(o.ocap_id, { trigger_signal: e.target.value })} />
          </Field>
          <Field label="Action steps (first response, then containment)" htmlFor={`ocap-${o.ocap_id}-steps`}>
            <TextInput
              id={`ocap-${o.ocap_id}-steps`} value={o.action_steps.join(" | ")}
              onChange={(e) => onChange(o.ocap_id, { action_steps: e.target.value.split("|").map((s) => s.trim()).filter(Boolean) })}
              placeholder="First response | Containment step"
            />
          </Field>
          <Field label="Escalation trigger" htmlFor={`ocap-${o.ocap_id}-esc-trigger`}>
            <TextInput id={`ocap-${o.ocap_id}-esc-trigger`} value={o.escalation_trigger} onChange={(e) => onChange(o.ocap_id, { escalation_trigger: e.target.value })} />
          </Field>
          <Field label="Escalation contact" htmlFor={`ocap-${o.ocap_id}-esc-contact`}>
            <TextInput id={`ocap-${o.ocap_id}-esc-contact`} value={o.escalation_contact} onChange={(e) => onChange(o.ocap_id, { escalation_contact: e.target.value })} />
          </Field>
          <Field label="Acting owner" htmlFor={`ocap-${o.ocap_id}-owner`}>
            <TextInput id={`ocap-${o.ocap_id}-owner`} value={o.acting_owner} onChange={(e) => onChange(o.ocap_id, { acting_owner: e.target.value })} />
          </Field>
          <Button variant="danger" size="sm" onClick={() => onRemove(o.ocap_id)}>Remove OCAP entry</Button>
        </div>
      ))}
    </Panel>
  );
}
