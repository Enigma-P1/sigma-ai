import type { StepType } from "../../api/types";

/** Konva draws to a <canvas>, not the DOM, so CSS custom properties in
 * design/tokens.css can't be read at draw time the way a stylesheet would.
 * These mirror tokens.css's --color-va/nva/enabling (themselves aliased
 * onto --color-pass/fail/accent) by hand -- tokens.css is light-theme-only
 * for M1 (its own header comment), so there is exactly one palette to stay
 * in sync with today. If a dark theme lands later, this is the file that
 * needs a real bridge (e.g. reading getComputedStyle on mount). */
export const STEP_FILL: Record<StepType, string> = {
  value_add: "#e7f6ec",
  non_value_add: "#fdecec",
  enabling: "#eaeefc",
};
export const STEP_STROKE: Record<StepType, string> = {
  value_add: "#1a7f37",
  non_value_add: "#cf222e",
  enabling: "#3556d6",
};

export const CANVAS_SELECTED_STROKE = "#2c47ba";
export const CANVAS_LANE_FILL = ["#ffffff", "#f6f7f8"]; // alternating bands
export const CANVAS_LANE_BORDER = "#dde1e6";
export const CANVAS_TEXT = "#1c2128";
export const CANVAS_TEXT_MUTED = "#5b6470";
export const CANVAS_CONNECTOR = "#88919c";
