import type { ColumnInfo, Derivation, QualityScanResult } from "../../api/types";
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

// --- docs/uat/PLAN.md 1.5's three additions, as structured findings rather
// than pre-rendered strings -- the preview-time scan block (DataImportForm)
// and the saved-dataset rows view (DatasetRowsView) both need the same
// three counts, but say different things about them: a preview has no
// dataset_id yet to fix anything against, while the rows view has the
// actual Recode / Delete rows / Edit cells controls right there to point
// at. One extraction, two renderings -- never two copies of "what did the
// scan find." ---

export interface RepeatedHeaderFinding {
  kind: "repeated_header_row";
  count: number;
}

export interface NearDuplicateFinding {
  kind: "near_duplicate";
  column: string;
  variants: string[];
}

export interface MixedDateFormatFinding {
  kind: "mixed_date_format";
  column: string;
  shapes: string[];
}

export type QualityActionFinding = RepeatedHeaderFinding | NearDuplicateFinding | MixedDateFormatFinding;

/** Flattens the three PLAN §1.5 fields into one list of findings, each
 * naming exactly one thing to look at (one near-duplicate group, not one
 * per column) so a caller can render "point at the fix" per item rather
 * than per column. All three source fields are optional on the wire
 * (engine default 0 / {} / {} -- older meta.json still loads), hence the
 * `?? ` fallbacks throughout this module. */
export function qualityActionFindings(q: QualityScanResult): QualityActionFinding[] {
  const findings: QualityActionFinding[] = [];
  const repeated = q.repeated_header_row_count ?? 0;
  if (repeated > 0) findings.push({ kind: "repeated_header_row", count: repeated });
  for (const [column, groups] of Object.entries(q.near_duplicate_values ?? {})) {
    for (const variants of groups) findings.push({ kind: "near_duplicate", column, variants });
  }
  for (const [column, shapes] of Object.entries(q.mixed_date_formats ?? {})) {
    findings.push({ kind: "mixed_date_format", column, shapes });
  }
  return findings;
}

/** The preview-time (nothing saved yet) wording for one finding — always
 * names the control that fixes it by the label that control carries on the
 * rows view, and says plainly that the control shows up after saving,
 * since there is no dataset_id yet at preview time to act against (research
 * README: "a finding a user cannot act on is just a scolding"). */
function describeQualityActionFinding(f: QualityActionFinding): string {
  switch (f.kind) {
    case "repeated_header_row":
      return (
        `${f.count} row${f.count === 1 ? "" : "s"} repeat the column header as data, not a real record -- ` +
        `save this dataset, then delete ${f.count === 1 ? "it" : "them"} with Delete rows on the rows view`
      );
    case "near_duplicate":
      return (
        `${f.column}: ${f.variants.map((v) => `"${v}"`).join(", ")} look like the same value, spelled differently -- ` +
        `save this dataset, then merge them into one with Recode on the rows view`
      );
    case "mixed_date_format":
      return (
        `${f.column}: ${f.shapes.length} different date formats (${f.shapes.join(", ")}) -- ` +
        `save this dataset, then fix the odd ones out with Edit a cell on the rows view`
      );
  }
}

/** The plain-English scan summary (M2 brief: "quality-scan results
 * rendered plainly"). Renders a real, specific headline whether the scan
 * is clean or dirty — never hidden when zero. Counts every PLAN §1.5
 * finding too (one near-duplicate group = one issue, one mixed-format
 * column = one issue, matching how duplicate_row_count/
 * repeated_header_row_count already count rows) -- a file with three
 * spellings of one name and nothing else wrong must not read "clean". */
export function summarizeQuality(q: QualityScanResult): QualitySummary {
  const missing = sumValues(q.missing_values);
  const nonNumeric = sumValues(q.non_numeric_in_numeric_columns);
  const actionIssues = qualityActionFindings(q).length;
  const totalIssues = missing + nonNumeric + q.duplicate_row_count + actionIssues;
  if (totalIssues === 0) {
    return {
      headline:
        `Quality scan clean: ${q.row_count} rows — no missing values, non-numeric values, duplicate rows, ` +
        `repeated header rows, mixed spellings, or mixed date formats`,
      tone: "pass",
      totalIssues,
    };
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
  for (const finding of qualityActionFindings(q)) {
    lines.push(describeQualityActionFinding(finding));
  }
  lines.push(`${q.row_count} total rows scanned`);
  return lines;
}

export interface ColumnTotal {
  column: string;
  total: number;
}

/** The rows view's header line (docs/uat/README.md's sharpest finding: "the
 * app never once showed either of them their own rows" -- no total was ever
 * shown, only five sample values per column). One entry per column
 * confirmed numeric (ColumnInfo.type -- the same caller-overridable
 * effective type build_columns() computes engine-side, not inferred_type),
 * summing that column's actual saved values. A blank cell or a stray
 * non-numeric cell (the quality scan's own non_numeric_in_numeric_columns
 * finding) is skipped rather than treated as zero -- it stays visible as a
 * quality finding above the rows table, it just doesn't quietly distort
 * the total here. */
export function numericColumnTotals(columns: ColumnInfo[], rows: Record<string, string>[]): ColumnTotal[] {
  return columns
    .filter((c) => c.type === "numeric")
    .map((c) => ({
      column: c.name,
      total: rows.reduce((sum, row) => {
        const raw = row[c.name];
        if (raw == null || raw.trim() === "") return sum;
        const n = Number(raw);
        return Number.isFinite(n) ? sum + n : sum;
      }, 0),
    }));
}

// --- Derivation controls (docs/uat/PLAN.md 1.2/1.3/1.4) -------------------

export interface ValueCount {
  value: string;
  count: number;
}

/** Distinct values in one column with counts, most-common first (ties
 * broken alphabetically) -- what Recode lists so a supervisor can see "JM
 * (3), J. Morales (1), J Morales (1)" and pick which spellings are really
 * the same person (Dave's UAT complaint, docs/uat/README.md, answered
 * directly). Blank cells are excluded: recoding a blank into a value is
 * Edit a cell's job, not Recode's -- RecodeDerivation only ever rewrites a
 * cell that already holds one of the mapped source values. */
export function distinctValueCounts(rows: Record<string, string>[], column: string): ValueCount[] {
  const counts = new Map<string, number>();
  for (const row of rows) {
    const v = row[column];
    if (v == null || v === "") continue;
    counts.set(v, (counts.get(v) ?? 0) + 1);
  }
  return [...counts.entries()]
    .map(([value, count]) => ({ value, count }))
    .sort((a, b) => b.count - a.count || a.value.localeCompare(b.value));
}

/** Mirrors datasets.py's _count_repeated_header_rows at row-INDEX
 * granularity -- the engine only ever returns a count
 * (QualityScanResult.repeated_header_row_count), never which rows, because
 * nothing server-side needs the indices once counted. The rows view has
 * the full row set already loaded, so re-deriving which ones match (to
 * preselect them for Delete rows -- the finding's own "point at the fix")
 * costs one more linear pass and copies the engine's exact-string-equality
 * rule byte for byte. Display convenience only: the engine's count stays
 * the fact of record, this just answers "which ones". */
export function repeatedHeaderRowIndices(columns: ColumnInfo[], rows: Record<string, string>[]): number[] {
  const names = columns.map((c) => c.name);
  const indices: number[] = [];
  rows.forEach((row, i) => {
    if (names.every((name) => row[name] === name)) indices.push(i);
  });
  return indices;
}

/** One human sentence fragment naming WHAT a derivation did, for the "new
 * dataset created" banner (DatasetRowsView) -- so the banner says more than
 * "something changed," which the CRITICAL rule in docs/uat/PLAN.md 1.2-1.4
 * treats as the whole point: a derivation must never read as a mystery
 * in-place edit. */
export function derivationSummary(d: Derivation): string {
  switch (d.kind) {
    case "edit_cells":
      return `${d.edits.length} cell edit${d.edits.length === 1 ? "" : "s"}`;
    case "add_row":
      return "one row added";
    case "delete_rows":
      return `${d.row_indices.length} row${d.row_indices.length === 1 ? "" : "s"} deleted`;
    case "recode":
      return `${Object.keys(d.mapping).length} value${Object.keys(d.mapping).length === 1 ? "" : "s"} recoded on ${d.column}`;
    case "derive_column":
      return `"${d.new_column_name}" derived from ${d.left_column} and ${d.right_column}`;
  }
}
