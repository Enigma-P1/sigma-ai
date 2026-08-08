import { Button, Field, Panel, TextArea, VerdictBanner } from "../../design/components";
import type { A3Panel } from "../../api/types";
import { A3_PANEL_SEED_TOOL_HINT, A3_PANEL_TITLES } from "../../api/types";

export interface PanelEditorProps {
  panel: A3Panel;
  seeding: boolean;
  onNarrativeChange: (narrative: string) => void;
  onReseed: () => void;
}

/** One A3 panel: its seed source (or the honest "not seeded yet"), a
 * "re-seed from artifact" affordance, and the editable narrative text --
 * a guided narrative builder, not field concatenation (PLAN §4.1). */
export function PanelEditor({ panel, seeding, onNarrativeChange, onReseed }: PanelEditorProps) {
  return (
    <div className="sigma-a3-panel-editor" data-testid={`a3-panel-${panel.panel}`}>
      <Panel title={A3_PANEL_TITLES[panel.panel]} subtitle={`Seeds from ${A3_PANEL_SEED_TOOL_HINT[panel.panel]}`}>
        {panel.seeded_from ? (
          <VerdictBanner
            tone="pass" headline={`Seeded from ${panel.seeded_from.tool_id}/${panel.seeded_from.artifact_ref}`}
            detail={panel.seeded_from.fields.length ? `fields: ${panel.seeded_from.fields.join(", ")}` : undefined}
          />
        ) : (
          <VerdictBanner tone="flag" headline="Not seeded yet" detail="Re-seed from its source artifact, or write the narrative by hand." />
        )}

        <Button variant="ghost" size="sm" disabled={seeding} onClick={onReseed} data-testid={`a3-reseed-${panel.panel}`}>
          {seeding ? "Seeding…" : "Re-seed from artifact"}
        </Button>

        <Field label="Narrative" htmlFor={`a3-narrative-${panel.panel}`} helper="The story in your own words -- editable after seeding, never a field dump.">
          <TextArea
            id={`a3-narrative-${panel.panel}`} data-testid={`a3-narrative-${panel.panel}`} rows={5}
            value={panel.narrative} onChange={(e) => onNarrativeChange(e.target.value)}
          />
        </Field>
      </Panel>
    </div>
  );
}
