import { Button, Field, Panel, TextInput } from "../../design/components";
import type { ProcessMapLane } from "../../api/types";

export interface LanesPanelProps {
  lanes: ProcessMapLane[];
  onAdd: () => void;
  onUpdate: (laneId: string, patch: Partial<ProcessMapLane>) => void;
  onRemove: (laneId: string) => void;
}

/** Lane add/rename/set-owner controls -- plain HTML rows rather than
 * in-canvas text editing (ProcessMapCanvas renders lanes read-only; this
 * is where they're actually edited, same split the M2 brief draws between
 * the inspector panel/add-step buttons and canvas drag). Removing a lane
 * cascades to its steps/connectors in the hook (useProcessMapForm.removeLane). */
export function LanesPanel({ lanes, onAdd, onUpdate, onRemove }: LanesPanelProps) {
  return (
    <Panel title="Lanes" subtitle="Who owns each swimlane">
      <div className="sigma-processmap-lanes">
        {lanes.map((lane, i) => (
          <div className="sigma-processmap-lane-row" key={lane.lane_id}>
            <Field label="Lane name" htmlFor={`processmap-lane-${i}-name`}>
              <TextInput
                id={`processmap-lane-${i}-name`} data-testid={`processmap-lane-${i}-name`}
                value={lane.name} onChange={(e) => onUpdate(lane.lane_id, { name: e.target.value })}
              />
            </Field>
            <Field label="Owner" htmlFor={`processmap-lane-${i}-owner`}>
              <TextInput
                id={`processmap-lane-${i}-owner`} data-testid={`processmap-lane-${i}-owner`}
                value={lane.owner} onChange={(e) => onUpdate(lane.lane_id, { owner: e.target.value })}
                placeholder="Who runs this lane"
              />
            </Field>
            <Button variant="ghost" size="sm" type="button" onClick={() => onRemove(lane.lane_id)} data-testid={`processmap-lane-${i}-remove`}>
              Remove lane
            </Button>
          </div>
        ))}
      </div>
      <Button variant="ghost" size="sm" type="button" onClick={onAdd} data-testid="processmap-add-lane">
        + Add lane
      </Button>
    </Panel>
  );
}
