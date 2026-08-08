/** Text-box parsing shared by every T-17 array/number field. Pure string
 * -> number(s) parsing only -- no statistics computed here (hard rule:
 * every statistic rendered comes from the engine response). */

/** Splits on commas, whitespace, and newlines so "1, 2, 3", "1 2 3", and
 * one-value-per-line all work the same way; drops anything that isn't a
 * finite number rather than silently coercing it to 0. */
export function parseNumberList(text: string): number[] {
  return text
    .split(/[\s,]+/)
    .map((t) => t.trim())
    .filter((t) => t !== "")
    .map(Number)
    .filter((n) => Number.isFinite(n));
}

/** Count of tokens that failed to parse -- used to warn the user their
 * paste had junk in it, separately from how many good values remain. */
export function countUnparsedTokens(text: string): number {
  const tokens = text.split(/[\s,]+/).map((t) => t.trim()).filter((t) => t !== "");
  return tokens.filter((t) => !Number.isFinite(Number(t))).length;
}

export function toInt(text: string, fallback: number): number {
  const n = Number(text);
  return Number.isFinite(n) ? Math.trunc(n) : fallback;
}

export function toFloatOrNull(text: string): number | null {
  if (text.trim() === "") return null;
  const n = Number(text);
  return Number.isFinite(n) ? n : null;
}
