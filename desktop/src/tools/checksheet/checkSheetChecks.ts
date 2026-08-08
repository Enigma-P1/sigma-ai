/** check_id -> plain-English label for T-08's prescore strip
 * (prescore/check_sheet.py has 4 possible checks). */
export const CHECK_SHEET_CHECK_LABELS: Record<string, string> = {
  strata_declared: "Stratification fields declared",
  entries_present: "Entries tallied",
  entries_carry_full_strata: "Every entry carries its declared strata",
  category_coverage: "Every category has been tallied",
};
