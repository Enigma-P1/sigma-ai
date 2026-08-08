import type { HelperFrameContent } from "../helperFrameTypes";

/** T-16 process FMEA helper content. "What good looks like" restates
 * rubric R-ANA-03 (process FMEA -- anchor consistency, severity-sensitive
 * prioritization, actions with owners), one source of truth, no parallel
 * checklist (tier-a-done-means §2). */
export const fmeaHelperContent: HelperFrameContent = {
  toolId: "T-16",
  isPlaceholder: false,
  whatThisIs:
    "A worksheet that documents how your process fails: one row per specific failure of a specific step, " +
    "with its effect, its cause, and three 1-10 ratings -- Severity (how bad when it happens), Occurrence " +
    "(how often the cause shows up), Detection (how likely current controls catch it before it moves on). " +
    "The tool multiplies them into an RPN and sorts severity-first, because RPN alone has a known flaw: " +
    "equal RPNs are not equal risks. A 6x6x8 mix-up and an 8x2x3 burn hazard multiply to 288 and 48, and " +
    "the second one is still the row a responsible team addresses -- high severity is never ignorable, " +
    "whatever the arithmetic says.",
  whenToUse:
    "In Analyze, once the T-06 map names your steps -- the map is the row source, so failure modes stay " +
    "specific (\"marked cups taken out of order in the drink queue,\" not \"process fails\"). At the " +
    "Coffee Bar the FMEA walks all five mapped steps and surfaces two different priorities the fishbone " +
    "alone would not rank: the queue mix-up row carries the highest RPN (288), while the steam-wand burn " +
    "row tops the severity-first view at severity 8 with an RPN of only 48 -- and both get actions with " +
    "owners, for two different reasons the ratings make explicit.",
  whenNotTo:
    "Not a substitute for cause verification -- the FMEA ranks risks; the fishbone's evidence discipline " +
    "verifies causes. And the classic misuse is chasing the RPN league table while a severity-9/10 row " +
    "sits unaddressed: that is the exact failure the tool warns about, and this tool makes it loud -- a " +
    "severity-9/10 row whose effect reads safety/regulatory with no action recorded raises a blocking " +
    "flag that stops \"project may close\" at Wrap, however clean everything else is. Also skip the " +
    "ratings-by-gut-feel session: every number is an anchor lookup, not a vibe.",
  fieldGuidance: [
    {
      field: "Step",
      good: "Picked from the T-06 map so the row is tied to a mapped step (\"Cup waits in drink queue\"), with the free-text name matching what the floor calls it.",
      bad: "\"The whole morning process.\" (a mode at whole-process altitude can't be rated or fixed -- which step, failing how?)",
    },
    {
      field: "Failure mode",
      good: "A specific way that step fails: \"marked cups taken out of order during a nine-deep burst.\"",
      bad: "\"Delay\" or \"defect.\" (single-word modes are the whole-process problem in miniature -- the prescore flags them)",
    },
    {
      field: "Effect",
      good: "What the customer or process experiences when it happens: \"two customers' drinks swap at handoff; both remade, both waits double.\"",
      bad: "A restatement of the mode. (the effect is the consequence, not the failure said twice)",
    },
    {
      field: "Cause",
      good: "The mechanism behind the mode: \"cup marks smear near the steam wand; grab order is whatever is closest.\"",
      bad: "\"Operator error.\" (blames a person, names no mechanism, and suggests no countermeasure)",
    },
    {
      field: "Severity / Occurrence / Detection",
      good: "Each number chosen by reading the 1-10 anchor text (focus a rating to see it) and matching your row's reality to the anchor's wording -- with the reasoning noted when reality sits between two anchors (\"re-pulls run ~1 in 12 sampled orders, between the 1-in-20 and 1-in-8 anchors; rated 7\").",
      bad: "A column of straight 5s. (identical middle numbers are the signature of anchors never consulted -- the rubric's spot-check looks for exactly this)",
    },
    {
      field: "Action / Owner / Due",
      good: "For the top severity-first rows and the top RPN rows: a concrete action, a named owner, a date. \"Move cup marking to printed sticker labels -- Priya Shah -- Aug 21.\"",
      bad: "An action with no owner (the prescore flags it -- unowned actions are wishes), or a severity-9/10 row with the action left blank (the blocking flag, and rightly).",
    },
  ],
  whatGoodLooksLike: [
    "Failure modes are specific failures of specific mapped steps, each with its own effect and cause -- " +
      "\"process fails\" is not a mode.",
    "Ratings are anchor lookups: spot-check any row and the number matches its anchor's wording, with " +
      "between-anchor judgment calls argued in a note, not silent.",
    "Prioritization is severity-sensitive in substance: the action list reflects that equal RPNs are not " +
      "equal risks and that high severity is never ignorable -- the severity-8 burn row gets an action and " +
      "owner even though its RPN of 48 ranks near the bottom of the multiplication table.",
    "Top items -- by severity and by RPN -- carry concrete actions with named owners and dates; " +
      "lower-priority rows may honestly wait, and that choice is visible, not accidental.",
    "No severity-9/10 safety or regulatory row is left without an action -- the blocking flag stays empty " +
      "because the risk was addressed, not because the wording was softened to dodge the keyword screen.",
    "The anchors-consulted confirmation is true as recorded: it flips when the anchor text was actually " +
      "shown for the row's ratings, and only then -- it is an honesty self-report, not a formality.",
  ],
  commonMistakes: [
    "Working the RPN league table top-down while a high-severity row waits -- the exact misuse the " +
      "severity-first sort exists to prevent; RPN is a tiebreaker within severity, not the headline.",
    "Detection ratings all the same middle number -- the anchor scale runs from \"almost certain to catch " +
      "it\" (1) to \"no current control could\" (10), and real steps differ.",
    "Down-rating severity to make an uncomfortable row disappear from the top of the sort -- severity is " +
      "the anchor-matched worst credible effect, not a negotiation with the flag logic.",
    "Actions without owners, or owners without dates -- an unowned action is a wish, and the prescore " +
      "says so.",
    "Rating the step's chronic slowness as a failure mode -- the 8.4-minute average is the baseline's " +
      "common-cause story; FMEA rows are discrete failures (mix-ups, re-pulls, jams, burns) that ride on " +
      "top of it.",
  ],
  source:
    "Method source: industry-standard process-FMEA structure with 1-10 severity/occurrence/detection " +
    "anchor scales in this engine's own generic wording -- no AIAG or ASQ licensed text (traceability " +
    "matrix I.C.2, PLAN §6). RPN = S x O x D, computed by the engine, never hand-typed; sort is " +
    "severity-first then RPN, with the RPN limitation stated on the form; severity-9/10 safety/regulatory " +
    "rows without actions raise the R-WRAP-03 project-close blocker. Acceptance checklist: rubric R-ANA-03.",
};
