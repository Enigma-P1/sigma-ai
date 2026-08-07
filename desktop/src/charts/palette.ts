/** Chart palette — literal color values mirrored from design/tokens.css.
 * Plotly draws into its own SVG layer and can't resolve CSS custom
 * properties there, so this file keeps its own copies. Kept in lockstep
 * by hand, the same convention api/types.ts already uses for the
 * engine's Pydantic models — a tokens.css palette edit needs a matching
 * edit here.
 */

export const CHART_COLORS = {
  text: "#1c2128",
  textMuted: "#5b6470",
  textFaint: "#88919c",
  surface: "#ffffff",
  grid: "#dde1e6",
  border: "#c3c9d1",

  accent: "#3556d6",
  accentSoft: "#eaeefc",

  pass: "#1a7f37",
  passSoft: "#e7f6ec",
  flag: "#9a6700",
  flagSoft: "#fef3d6",
  fail: "#cf222e",
  failSoft: "#fdecec",
  exit: "#6e40c9",

  neutral: "#88919c",
  neutralSoft: "#eceef1",
} as const;

/** Muted-plus-accent qualitative series palette (research §F: "signals
 * colored, noise muted") — used when a chart shows several non-signal
 * series (e.g. BoxChart's groups) and no single one of them is itself
 * "the signal." Signal-bearing marks (I-MR rule violations, Pareto's
 * vital few) use CHART_COLORS.accent/fail directly, not this list. */
export const CHART_SERIES_PALETTE = [
  "#3556d6", // accent
  "#5b6470", // muted slate
  "#1a7f37", // pass green
  "#9a6700", // flag amber
  "#6e40c9", // exit violet
  "#0f6d8c", // muted teal -- a 5th qualitative hue, kept low-chroma to match the muted-plus-accent brief
] as const;

export const CHART_FONT_FAMILY =
  'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Avenir, Helvetica, Arial, sans-serif';
