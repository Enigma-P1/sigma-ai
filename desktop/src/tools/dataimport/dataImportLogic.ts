import type { QualityScanResult } from "../../api/types";
import type { VerdictTone } from "../../design/components";

/** Chunked to avoid `String.fromCharCode(...bigArray)` blowing the call
 * stack on a larger file — 32KB is comfortably under any engine's
 * argument-count limit. */
function bytesToBase64(bytes: Uint8Array): string {
  let binary = "";
  const chunkSize = 0x8000;
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunkSize));
  }
  return btoa(binary);
}

export async function fileToBase64(file: File): Promise<string> {
  const buf = await file.arrayBuffer();
  return bytesToBase64(new Uint8Array(buf));
}

function sumValues(counts: Record<string, number>): number {
  return Object.values(counts).reduce((a, b) => a + b, 0);
}

export interface QualitySummary {
  headline: string;
  tone: VerdictTone;
  totalIssues: number;
}

/** The plain-English scan summary (M2 brief: "quality-scan results
 * rendered plainly"). Renders a real, specific headline whether the scan
 * is clean or dirty — never hidden when zero. */
export function summarizeQuality(q: QualityScanResult): QualitySummary {
  const missing = sumValues(q.missing_values);
  const nonNumeric = sumValues(q.non_numeric_in_numeric_columns);
  const totalIssues = missing + nonNumeric + q.duplicate_row_count;
  if (totalIssues === 0) {
    return { headline: `Quality scan clean: ${q.row_count} rows, no missing values, no non-numeric values, no duplicates`, tone: "pass", totalIssues };
  }
  return { headline: `Quality scan found ${totalIssues} issue${totalIssues === 1 ? "" : "s"} across ${q.row_count} rows`, tone: "flag", totalIssues };
}

/** One plain-language line per finding, always including the row count
 * so there is always at least one line to show. */
export function qualityFindingLines(q: QualityScanResult): string[] {
  const lines: string[] = [];
  for (const [col, n] of Object.entries(q.missing_values)) {
    if (n > 0) lines.push(`${col}: ${n} missing value${n === 1 ? "" : "s"}`);
  }
  for (const [col, n] of Object.entries(q.non_numeric_in_numeric_columns)) {
    if (n > 0) lines.push(`${col}: ${n} non-numeric value${n === 1 ? "" : "s"} in a column typed numeric`);
  }
  if (q.duplicate_row_count > 0) {
    lines.push(`${q.duplicate_row_count} duplicate row${q.duplicate_row_count === 1 ? "" : "s"}`);
  }
  lines.push(`${q.row_count} total rows scanned`);
  return lines;
}
