import type { CauseStatus } from "../../api/types";

/** Konva draws to a <canvas>, not the DOM, so CSS custom properties can't
 * be read at draw time -- these mirror design/tokens.css by hand
 * (processmap/canvasColors.ts's documented convention). Status color
 * coding per the build brief: candidate = muted, investigating = accent,
 * verified = pass-green, ruled_out = struck (drawn with a strikethrough
 * line in FishboneCanvas, colored faint here). */
export const CAUSE_FILL: Record<CauseStatus, string> = {
  candidate: "#eceef1",
  investigating: "#eaeefc",
  verified: "#e7f6ec",
  ruled_out: "#f0f1f3",
};
export const CAUSE_STROKE: Record<CauseStatus, string> = {
  candidate: "#88919c",
  investigating: "#3556d6",
  verified: "#1a7f37",
  ruled_out: "#c3c9d1",
};
export const CAUSE_TEXT: Record<CauseStatus, string> = {
  candidate: "#1c2128",
  investigating: "#1c2128",
  verified: "#1c2128",
  ruled_out: "#88919c",
};

export const CANVAS_SELECTED_STROKE = "#2c47ba";
export const CANVAS_TEXT = "#1c2128";
export const CANVAS_TEXT_MUTED = "#5b6470";
export const CANVAS_SPINE = "#5b6470";
export const CANVAS_BRANCH = "#88919c";
export const CANVAS_LINK = "#c3c9d1";
export const CANVAS_HEAD_FILL = "#eaeefc";
export const CANVAS_HEAD_STROKE = "#3556d6";
