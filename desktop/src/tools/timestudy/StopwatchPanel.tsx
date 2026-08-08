import { Button, Field, TextInput } from "../../design/components";
import { formatStopwatch } from "./timeStudyLogic";
import type { ElementTime, WorkElement } from "../../api/types";

export interface StopwatchPanelProps {
  elements: WorkElement[];
  running: boolean;
  elapsedMs: number;
  currentCycleTimes: ElementTime[];
  currentNote: string;
  onSetNote: (note: string) => void;
  onStart: () => void;
  onSplit: (elementId: string) => void;
  onFinish: () => void;
  onCancel: () => void;
}

/** The phone-as-stopwatch capture path: Start, then one split button per
 * element, then Finish commits the cycle. Client timestamps are fine for
 * capture (M2 brief) -- every stat rendered elsewhere comes only from the
 * engine's response after save, never from anything computed here. */
export function StopwatchPanel({
  elements, running, elapsedMs, currentCycleTimes, currentNote, onSetNote, onStart, onSplit, onFinish, onCancel,
}: StopwatchPanelProps) {
  const splitById = Object.fromEntries(currentCycleTimes.map((t) => [t.element_id, t.seconds]));

  return (
    <div className="sigma-timestudy-stopwatch">
      <div className="sigma-timestudy-stopwatch__clock" data-testid="timestudy-stopwatch-clock">
        {formatStopwatch(elapsedMs)}
      </div>

      {!running ? (
        <Button variant="primary" type="button" onClick={onStart} data-testid="timestudy-stopwatch-start">
          Start cycle
        </Button>
      ) : (
        <>
          <div className="sigma-timestudy-stopwatch__splits">
            {elements.map((e) => (
              <button
                key={e.element_id} type="button" className="sigma-timestudy-stopwatch__split"
                data-testid={`timestudy-split-${e.element_id}`} onClick={() => onSplit(e.element_id)}
              >
                <span>{e.name}</span>
                <span data-testid={`timestudy-split-${e.element_id}-value`}>
                  {splitById[e.element_id] != null ? `${splitById[e.element_id].toFixed(1)}s` : "—"}
                </span>
              </button>
            ))}
          </div>
          <Field label="Observer note (optional)" htmlFor="timestudy-stopwatch-note">
            <TextInput id="timestudy-stopwatch-note" data-testid="timestudy-stopwatch-note" value={currentNote} onChange={(e) => onSetNote(e.target.value)} />
          </Field>
          <div className="sigma-timestudy-stopwatch__actions">
            <Button variant="primary" type="button" disabled={currentCycleTimes.length === 0} onClick={onFinish} data-testid="timestudy-stopwatch-finish">
              Finish cycle
            </Button>
            <Button variant="ghost" type="button" onClick={onCancel} data-testid="timestudy-stopwatch-cancel">
              Cancel
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
