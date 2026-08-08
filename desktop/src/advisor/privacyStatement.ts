/**
 * ADVISOR_PRIVACY_STATEMENT (M5 exit critic, Fix 2): the one honest
 * description of what the advisor sends, shared by both surfaces that show
 * it -- AdvisorSettingsScreen's "Privacy" panel and AdvisorPanel's
 * unconfigured-state banner.
 *
 * Before this fix each surface carried its own copy: AdvisorSettingsScreen's
 * was marked "verbatim (M5 brief) -- do not paraphrase," and AdvisorPanel's
 * was a second, divergent paraphrase. Both understated what actually gets
 * sent -- they named only "the current artifact and its computed results."
 * In fact (engine/sigma_engine/advisor/context.py's assemble_context and
 * engine/sigma_engine/advisor/modes.py's context selectors):
 *
 * - Every ask mode sends the current artifact in full, its computed
 *   results, and its pre-score findings.
 * - Every ask mode except tollgate/remedy (which narrow the set to their
 *   own phase/charter tools) sends short, code-generated summaries of
 *   EVERY other saved artifact in the project by default, so the advisor
 *   can reference one or ask to see it in full.
 * - "Check my claims" (the validator pass, same Advisor panel,
 *   engine/sigma_engine/advisor/validator.py's run_validator) additionally
 *   sends the same kind of summary for EVERY dataset imported into the
 *   project, unconditionally -- including up to 3 sample values per column
 *   (context.py's summarize_dataset).
 * - The API key this feature uses is stored in plain text in
 *   settings.json on this machine -- never encrypted.
 *
 * One constant, one honest paragraph, imported by both surfaces -- the
 * PLAN commitment this satisfies is that the screen states what is really
 * sent, not that any particular sentence stays frozen.
 */
export const ADVISOR_PRIVACY_STATEMENT =
  "The advisor (Layer 2) sends nothing until you actually use it. When you ask it something, the current " +
  "artifact goes in full, along with its computed results and pre-score findings; most modes also send short, " +
  "code-generated summaries of your project's other saved artifacts, so the advisor can reference them or ask " +
  'to see one in full. "Check my claims" additionally sends a summary of every dataset you\'ve imported into ' +
  "this project, including up to 3 sample values per column. Don't put customer names or other sensitive " +
  "identifiers in artifact text or imported datasets. Your API key is stored in plain text in settings.json on " +
  "this machine -- it is not encrypted.";
