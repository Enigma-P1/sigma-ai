import type { CheckSheetArtifact, CheckSheetCategory, CheckSheetEntry, StrataFieldDef } from "../../api/types";

let counter = 0;
/** Same counter-based id scheme as processMapLogic.ts's genId -- unique
 * for a session, not persisted identity. */
export function genId(prefix: string): string {
  counter += 1;
  return `${prefix}-${Date.now().toString(36)}-${counter}`;
}

export function emptyCategory(index: number): CheckSheetCategory {
  return { category_id: genId("cat"), label: `Category ${index + 1}` };
}

export function emptyStrataField(index: number): StrataFieldDef {
  return { key: genId("field"), label: `Field ${index + 1}` };
}

/** The exact fields the Save button's disabled state depends on, named in
 * plain English -- canSaveCheckSheet below and the rendered "Missing: ..."
 * hint both read from this one list (Jordan usability fix). */
export function checkSheetMissingFields(categories: CheckSheetCategory[]): string[] {
  if (categories.length === 0) return ["at least one category"];
  if (!categories.every((c) => c.label.trim() !== "")) return ["every category's label"];
  return [];
}

export function canSaveCheckSheet(categories: CheckSheetCategory[]): boolean {
  return checkSheetMissingFields(categories).length === 0;
}

/** Client-side display tally only -- a plain count of already-loaded,
 * LIVE entries' `count` (a soft-deleted one is excluded, same as the
 * engine's own check_sheet_export_rows), the same "not a computed result"
 * distinction processMapLogic's wasteTally draws (no provenance, nothing
 * the engine needs to stamp). Summing `count` rather than entries keeps
 * this correct for a transcribed entry too (one entry, several marks).
 * The graded Pareto counts always come from /stats/pareto after
 * to_dataset, never from this. */
export function tallyCounts(entries: CheckSheetEntry[]): Record<string, number> {
  const out: Record<string, number> = {};
  for (const e of entries) {
    if (e.deleted) continue;
    out[e.category_id] = (out[e.category_id] ?? 0) + (e.count ?? 1);
  }
  return out;
}

export function makeTallyEntry(categoryId: string, strata: Record<string, string>): CheckSheetEntry {
  const activeOnly = Object.fromEntries(Object.entries(strata).filter(([, v]) => v.trim() !== ""));
  return {
    entry_id: genId("entry"), category_id: categoryId, timestamp: new Date().toISOString(),
    strata: activeOnly, note: "", entry_mode: "tap", count: 1,
  };
}

/** "Transcribe a paper tally" mode (Jordan usability fix): reading counts
 * off an existing paper tally sheet after the fact, honestly -- one entry
 * per category with count > 0, all sharing the caller-supplied as-of
 * timestamp and source note (which sheet, whose handwriting). Stored with
 * entry_mode="transcribed" so the cross-artifact burst-entry check
 * (engine/sigma_engine/prescore/cross_checks.py) never mistakes this
 * batch for a suspicious real-time burst. */
export function makeTranscribedEntries(counts: Record<string, number>, asOf: string, sourceNote: string): CheckSheetEntry[] {
  return Object.entries(counts)
    .filter(([, count]) => count > 0)
    .map(([categoryId, count]) => ({
      entry_id: genId("entry"), category_id: categoryId, timestamp: asOf,
      strata: {}, note: sourceNote, entry_mode: "transcribed" as const, count,
    }));
}

/** Soft delete (rubric R-MEA-04, generalized to T-08): the entry stays in
 * the array, struck through in EntriesTable, excluded from tallyCounts
 * above and from the engine's exported dataset -- never a hard
 * .filter() removal. */
export function markEntryDeleted(entries: CheckSheetEntry[], entryId: string, reason: string, at: string): CheckSheetEntry[] {
  return entries.map((e) => (e.entry_id === entryId ? { ...e, deleted: { reason, at } } : e));
}

export function buildCheckSheetBody(input: {
  artifactId: string;
  schemaVersion: number;
  categories: CheckSheetCategory[];
  strataFields: StrataFieldDef[];
  entries: CheckSheetEntry[];
}): Record<string, unknown> {
  const now = new Date().toISOString();
  return {
    schema_version: input.schemaVersion,
    artifact_id: input.artifactId,
    tool_id: "T-08",
    created_at: now,
    updated_at: now,
    categories: input.categories,
    strata_fields: input.strataFields,
    entries: input.entries,
  };
}

export function checkSheetStateFromArtifact(artifact: CheckSheetArtifact): {
  categories: CheckSheetCategory[];
  strataFields: StrataFieldDef[];
  entries: CheckSheetEntry[];
} {
  return { categories: artifact.categories, strataFields: artifact.strata_fields, entries: artifact.entries };
}

/** Removing a category cascades to its entries -- an entry referencing a
 * removed category_id would fail the engine's referential-integrity check
 * on save (same reasoning as useProcessMapForm.removeLane's doomedSteps). */
export function removeCategoryCascade(categories: CheckSheetCategory[], entries: CheckSheetEntry[], categoryId: string) {
  return {
    categories: categories.filter((c) => c.category_id !== categoryId),
    entries: entries.filter((e) => e.category_id !== categoryId),
  };
}

/** Removing a strata field strips that key from every entry rather than
 * leaving an "undeclared strata key" the engine would reject on save. */
export function removeStrataFieldCascade(strataFields: StrataFieldDef[], entries: CheckSheetEntry[], key: string) {
  return {
    strataFields: strataFields.filter((f) => f.key !== key),
    entries: entries.map((e) => {
      if (!(key in e.strata)) return e;
      const next = { ...e.strata };
      delete next[key];
      return { ...e, strata: next };
    }),
  };
}

/** Every value a strata field could be toggled to: values already used on
 * some entry, plus any added-but-not-yet-tapped manual options. */
export function deriveStrataOptions(
  strataFields: StrataFieldDef[], entries: CheckSheetEntry[], manualOptions: Record<string, string[]>,
): Record<string, string[]> {
  const out: Record<string, string[]> = {};
  for (const f of strataFields) {
    const fromEntries = entries.map((e) => e.strata[f.key]).filter((v): v is string => Boolean(v));
    out[f.key] = Array.from(new Set([...(manualOptions[f.key] ?? []), ...fromEntries]));
  }
  return out;
}
