import { StatusPill } from "../../design/components";
import { panelCompleteness } from "./a3Logic";
import type { A3Panel } from "../../api/types";
import { A3_PANEL_ORDER, A3_PANEL_TITLES } from "../../api/types";

export interface CompletenessRailProps {
  panels: A3Panel[];
  activePanel: string | null;
  onSelect: (panel: string) => void;
}

/** The panel-by-panel completeness rail: one pill per panel, seeded/
 * narrated vs empty -- the story's own table of contents. */
export function CompletenessRail({ panels, activePanel, onSelect }: CompletenessRailProps) {
  const complete = panelCompleteness(panels);
  return (
    <nav className="sigma-a3-rail" data-testid="a3-completeness-rail" aria-label="A3 panels">
      {A3_PANEL_ORDER.map((kind) => (
        <button
          key={kind} type="button" className={`sigma-a3-rail__item ${activePanel === kind ? "sigma-a3-rail__item--active" : ""}`}
          onClick={() => onSelect(kind)} data-testid={`a3-rail-${kind}`}
        >
          <StatusPill tone={complete[kind] ? "pass" : "flag"} label={A3_PANEL_TITLES[kind]} />
        </button>
      ))}
    </nav>
  );
}
