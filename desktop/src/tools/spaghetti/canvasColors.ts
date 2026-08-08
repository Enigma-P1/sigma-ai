/** Operator color palette, indexed by Operator.color_index -- distinct
 * hues so a handful of overlapping traced routes stay tellable apart.
 * Konva draws to a <canvas>, not the DOM, so these can't be CSS custom
 * properties (same constraint documented in processmap/canvasColors.ts). */
export const OPERATOR_PALETTE = [
  "#3556d6", "#cf222e", "#1a7f37", "#9a6700", "#6e40c9", "#0969da", "#bf3989", "#57606a",
];

export function colorForOperator(colorIndex: number): string {
  const n = OPERATOR_PALETTE.length;
  return OPERATOR_PALETTE[((colorIndex % n) + n) % n];
}

export const CALIBRATION_LINE_COLOR = "#cf222e";
export const CALIBRATION_POINT_FILL = "#ffffff";
export const CALIBRATION_TEXT = "#1c2128";
export const TRACE_DRAFT_COLOR = "#1c2128";
export const TRACE_DRAFT_POINT_FILL = "#ffffff";
export const PLAYBACK_DOT_FILL = "#cf222e";
export const CANVAS_TEXT_MUTED = "#5b6470";
export const CANVAS_BG = "#eceef1";
