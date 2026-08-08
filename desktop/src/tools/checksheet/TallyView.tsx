import { Panel } from "../../design/components";
import { StrataToggles } from "./StrataToggles";
import type { CheckSheetCategory, StrataFieldDef } from "../../api/types";

export interface TallyViewProps {
  categories: CheckSheetCategory[];
  strataFields: StrataFieldDef[];
  strataOptions: Record<string, string[]>;
  activeStrata: Record<string, string>;
  onSetActiveStratum: (key: string, value: string) => void;
  onAddStrataOption: (key: string, value: string) => void;
  tallyCounts: Record<string, number>;
  onTap: (categoryId: string) => void;
}

/** The field-capture screen: big tap targets, one per category (rubric
 * T-08 row: "tap to count as failures happen, works on a phone at the
 * line"). Each tap stamps an entry now with whatever strata toggles are
 * currently active -- no per-tap form to fill in. */
export function TallyView({
  categories, strataFields, strataOptions, activeStrata, onSetActiveStratum, onAddStrataOption, tallyCounts, onTap,
}: TallyViewProps) {
  return (
    <Panel title="Tally" subtitle="Set the strata toggles, then tap a category to log one entry, stamped now">
      {strataFields.length > 0 && (
        <div className="sigma-checksheet-tally__strata" data-testid="checksheet-active-strata">
          {strataFields.map((f, i) => (
            <StrataToggles
              key={f.key} field={f} index={i} options={strataOptions[f.key] ?? []} active={activeStrata[f.key] ?? ""}
              onSetActive={(v) => onSetActiveStratum(f.key, v)} onAddOption={(v) => onAddStrataOption(f.key, v)}
            />
          ))}
        </div>
      )}

      <div className="sigma-checksheet-tally__grid">
        {categories.map((c, i) => (
          // Index-based testid, same reasoning as StrataToggles' -- c.category_id
          // is an opaque generated id a test script can't predict, but the
          // categories array's order is otherwise stable (only add/remove reorders it).
          <button
            key={c.category_id} type="button" className="sigma-checksheet-tally__button"
            data-testid={`checksheet-tap-${i}`} onClick={() => onTap(c.category_id)}
          >
            <span className="sigma-checksheet-tally__label">{c.label}</span>
            <span className="sigma-checksheet-tally__count" data-testid={`checksheet-count-${i}`}>
              {tallyCounts[c.category_id] ?? 0}
            </span>
          </button>
        ))}
      </div>
    </Panel>
  );
}
