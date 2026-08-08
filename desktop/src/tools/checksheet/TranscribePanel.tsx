import { useState } from "react";
import { Button, Field, Panel, TextArea, TextInput } from "../../design/components";
import type { CheckSheetCategory } from "../../api/types";

export interface TranscribePanelProps {
  categories: CheckSheetCategory[];
  onLog: (counts: Record<string, number>, asOf: string, sourceNote: string) => void;
}

/** "Transcribe a paper tally" mode (Jordan usability fix): the honest path
 * for reading counts off an existing paper tally sheet after the fact --
 * a count per category, one as-of timestamp, one required source note
 * (which sheet, whose handwriting), logged as entry_mode="transcribed" so
 * the cross-artifact burst-entry check never mistakes this batch for a
 * suspicious real-time burst (engine/sigma_engine/prescore/cross_checks.py). */
export function TranscribePanel({ categories, onLog }: TranscribePanelProps) {
  const [counts, setCounts] = useState<Record<string, string>>({});
  const [asOf, setAsOf] = useState("");
  const [sourceNote, setSourceNote] = useState("");

  const parsedCounts = Object.fromEntries(
    categories.map((c) => [c.category_id, Math.max(0, Math.floor(Number(counts[c.category_id] ?? "0")) || 0)]),
  );
  const totalCount = Object.values(parsedCounts).reduce((a, b) => a + b, 0);
  const canLog = totalCount > 0 && asOf.trim() !== "" && sourceNote.trim() !== "";

  function log() {
    if (!canLog) return;
    onLog(parsedCounts, asOf, sourceNote.trim());
    setCounts({});
  }

  return (
    <Panel title="Transcribe a paper tally" subtitle="Reading counts off an existing paper sheet after the fact -- honestly, not tapped live">
      <div className="sigma-checksheet-transcribe__counts" data-testid="checksheet-transcribe-counts">
        {categories.map((c, i) => (
          <Field key={c.category_id} label={c.label} htmlFor={`checksheet-transcribe-count-${i}`}>
            <TextInput
              id={`checksheet-transcribe-count-${i}`} data-testid={`checksheet-transcribe-count-${i}`}
              type="number" min={0} value={counts[c.category_id] ?? ""}
              onChange={(e) => setCounts((prev) => ({ ...prev, [c.category_id]: e.target.value }))}
            />
          </Field>
        ))}
      </div>

      <Field label="As of" required htmlFor="checksheet-transcribe-asof" helper="When was this paper sheet's period -- not right now.">
        <TextInput
          id="checksheet-transcribe-asof" data-testid="checksheet-transcribe-asof" type="datetime-local"
          value={asOf} onChange={(e) => setAsOf(e.target.value)}
        />
      </Field>
      <Field label="Source note" required htmlFor="checksheet-transcribe-note" helper="Which sheet, whose handwriting -- required, this is what makes a transcription honest.">
        <TextArea
          id="checksheet-transcribe-note" data-testid="checksheet-transcribe-note" rows={2}
          value={sourceNote} onChange={(e) => setSourceNote(e.target.value)}
          placeholder="e.g. clipboard sheet dated 7/20, transcribed by Priya 7/22"
        />
      </Field>

      <Button variant="primary" disabled={!canLog} onClick={log} data-testid="checksheet-transcribe-log">
        Log {totalCount > 0 ? `${totalCount} transcribed ` : ""}{totalCount === 1 ? "count" : "counts"}
      </Button>
    </Panel>
  );
}
