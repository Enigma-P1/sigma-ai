import type { ImrSignal, NormalityResult } from "../../api/types";

export function parseSpecLimit(text: string): number | null {
  if (text.trim() === "") return null;
  const n = Number(text);
  return Number.isFinite(n) ? n : null;
}

/** Every signal covering a given point index, for a hover tooltip naming
 * the rule (M2 brief: "signals colored with rule name on hover"). */
export function signalsAtIndex(signals: ImrSignal[], index: number): ImrSignal[] {
  return signals.filter((s) => index >= s.start_index && index <= s.end_index);
}

export function pointColor(signals: ImrSignal[], index: number, accent: string, fail: string): string {
  return signalsAtIndex(signals, index).length > 0 ? fail : accent;
}

export function pointHoverText(signals: ImrSignal[], index: number, value: number): string {
  const here = signalsAtIndex(signals, index);
  if (here.length === 0) return `point ${index}: ${value}`;
  return [`point ${index}: ${value}`, ...here.map((s) => `${s.rule_id}: ${s.description}`)].join("<br>");
}

// Cp/Cpk render this exact string wherever the engine returned null for
// instability (EXIT-04) -- never a blank cell (M2 brief).
export const EXIT04_CELL_TEXT = "not available — not stable (EXIT-04)";
export const PP_ONE_SIDED_CELL_TEXT = "not available (needs both spec limits)";

export function exitExplanation(exitId: string): string {
  switch (exitId) {
    case "EXIT-04":
      return "EXIT-04: the I-MR chart signaled instability (or too few points to freeze limits) — this is a performance read, not a capability claim.";
    case "EXIT-05":
      return "EXIT-05: the normality check found a concern — a percentile-method (n≥100) or observed-yield (n<100) supplement is shown alongside the normal-theory numbers.";
    default:
      return exitId;
  }
}

export function normalityText(n: NormalityResult): string {
  switch (n.advisory) {
    case "too_few_to_judge":
      return `Too few points to judge normality (n=${n.n} < 15) — advisory only, never a gate.`;
    case "concern":
      return `A concern was flagged (Anderson-Darling, ${n.p_band}) — see the EXIT-05 supplement below.`;
    case "no_concern":
      return `No concern (Anderson-Darling, ${n.p_band}).`;
  }
}

export function fmt(n: number, digits = 3): string {
  return n.toFixed(digits);
}

/** sigma_level is null on the wire whenever the underlying z-score is
 * non-finite (pydantic's default float-to-JSON rule for inf/-inf/nan) --
 * an extremely capable process against very wide spec limits, not an
 * error. Render that honestly instead of crashing .toFixed() on null. */
export function sigmaLevelText(sigmaLevel: number | null, digits = 2): string {
  return sigmaLevel == null ? "not finite at this scale (process is far more capable than these spec limits require)" : fmt(sigmaLevel, digits);
}
