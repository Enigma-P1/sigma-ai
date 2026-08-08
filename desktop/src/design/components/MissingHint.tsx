import "./MissingHint.css";

export interface MissingHintProps {
  /** Plain-English labels for whatever's missing, sourced from the exact
   * same validation that disabled the Save/Run button next to this hint
   * (Jordan usability fix: a disabled button with no reason read as
   * broken, not "not ready yet"). Renders nothing when empty -- a button
   * disabled only because a save is in flight has nothing to list. */
  fields: string[];
}

/** "Missing: field, field" -- the one shared hint every disabled-Save
 * button in the app renders next to it. */
export function MissingHint({ fields }: MissingHintProps) {
  if (fields.length === 0) return null;
  return (
    <p className="sigma-missing-hint" data-testid="missing-hint">
      Missing: {fields.join(", ")}
    </p>
  );
}
