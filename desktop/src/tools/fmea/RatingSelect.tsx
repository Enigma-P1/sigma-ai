import { SelectInput } from "../../design/components";
import type { FmeaAnchors } from "../../api/types";

export interface RatingSelectProps {
  dimension: "severity" | "occurrence" | "detection";
  value: number;
  anchors: FmeaAnchors;
  testId: string;
  onChange: (value: number) => void;
  onFocusAnchor: (dimension: "severity" | "occurrence" | "detection", value: number) => void;
}

const POINTS = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1];

/** One S/O/D rating select. Focusing (or changing) it surfaces that
 * point's anchor text via onFocusAnchor -- FmeaWorksheet renders the
 * actual text in one shared anchor-helper strip (the "anchors-consulted
 * mechanic" the build brief calls for) and marks the row's
 * anchors_consulted true. */
export function RatingSelect({ dimension, value, anchors, testId, onChange, onFocusAnchor }: RatingSelectProps) {
  return (
    <SelectInput
      data-testid={testId}
      value={value}
      onFocus={() => onFocusAnchor(dimension, value)}
      onChange={(e) => {
        const next = Number(e.target.value);
        onChange(next);
        onFocusAnchor(dimension, next);
      }}
    >
      {POINTS.map((p) => (
        <option key={p} value={p} title={anchors[dimension][String(p)]}>
          {p}
        </option>
      ))}
    </SelectInput>
  );
}
