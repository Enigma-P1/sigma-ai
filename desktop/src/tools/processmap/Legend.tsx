import { STEP_TYPE_LABELS } from "./processMapLogic";
import { STEP_TYPES } from "../../api/types";
import "./Legend.css";

const SWATCH_CLASS: Record<string, string> = {
  value_add: "sigma-processmap-legend__swatch--va",
  non_value_add: "sigma-processmap-legend__swatch--nva",
  enabling: "sigma-processmap-legend__swatch--enabling",
};

/** Small VA/NVA/enabling legend for the canvas colors (design tokens --
 * see design/tokens.css's --color-va/nva/enabling). */
export function Legend() {
  return (
    <div className="sigma-processmap-legend" data-testid="processmap-legend">
      {STEP_TYPES.map((t) => (
        <span className="sigma-processmap-legend__item" key={t}>
          <span className={`sigma-processmap-legend__swatch ${SWATCH_CLASS[t]}`} aria-hidden="true" />
          {STEP_TYPE_LABELS[t]}
        </span>
      ))}
    </div>
  );
}
