import type { HelperFrameContent } from "../helperFrameTypes";

/** T-04 SIPOC helper content. "What good looks like" is drawn from rubric
 * R-DEF-06 -- one source of truth, no parallel checklist (tier-a-done-means
 * §2). Step-count bands (4-7 pass, 8-9 tolerated, outside 4-9 hard-flag)
 * match prescore/sipoc.py. */
export const sipocHelperContent: HelperFrameContent = {
  toolId: "T-04",
  isPlaceholder: false,
  whatThisIs:
    "A one-page map of the process at high altitude: Suppliers, Inputs, Process (a handful of steps), " +
    "Outputs, Customers. It fixes the boundaries -- where the process starts and ends -- that every " +
    "downstream artifact has to agree with.",
  whenToUse:
    "Right after the charter, before detailed process mapping (T-06) or any data collection. Build it with " +
    "people who run the process -- ten minutes at the counter beats an hour at a desk.",
  whenNotTo:
    "Not for task-level detail -- \"open the valve, check the gauge\" belongs in the swimlane process map, " +
    "not here. The classic misuse is mapping a different process than the one the charter scoped (or the " +
    "process as you wish it worked); every downstream artifact then inherits the mismatch.",
  fieldGuidance: [
    {
      field: "Supplier -> Input pairs",
      good: "\"Bean roastery -> roasted espresso beans\" -- each supplier paired to the input it provides, one row per pair.",
      bad: "A loose list of suppliers with no matching inputs. (free-floating lists don't show who feeds what)",
    },
    {
      field: "Process steps",
      good: "4-7 steps a stranger could follow in one read: take order, queue cup, prepare drink, finish, hand off.",
      bad: "Nineteen steps down to \"press the button.\" (that altitude is the detailed map's job; 8-9 is tolerated, outside 4-9 is hard-flagged)",
    },
    {
      field: "Output -> Customer pairs",
      good: "\"Finished drink, handed off -> the ordering customer\" -- whoever actually receives it, including the output the CTQ hangs on.",
      bad: "Customer listed as only the next internal step when a real end customer plainly exists downstream.",
    },
    {
      field: "Scope start",
      good: "\"Customer places order at the register\" -- the same boundary the charter's scope-in names.",
      bad: "A start that quietly reaches upstream of the chartered scope (into purchasing, into the supplier).",
    },
    {
      field: "Scope end",
      good: "\"Drink handed to the customer\" -- exactly where the charter says the project stops.",
      bad: "An end past the chartered boundary. (the team ends up mapping -- and fixing -- a different process)",
    },
  ],
  whatGoodLooksLike: [
    "All five columns are populated, and the process column is 4-7 high-level steps (8-9 is tolerated with " +
      "a flag; outside 4-9 is hard-flagged).",
    "The process column's start and end boundaries match the charter scope -- a SIPOC that contradicts the " +
      "charter fails outright, because every downstream artifact inherits the mismatch.",
    "Outputs are paired to the customers who actually receive them, and inputs to their suppliers -- not " +
      "free-floating lists.",
    "The CTQ-bearing output appears -- the thing the customer cares about is on the map, so the CTQ tree " +
      "(T-05) has something to hang from.",
  ],
  commonMistakes: [
    "Process steps written at task level (\"press the button\") -- that detail belongs in the T-06 map.",
    "Suppliers or customers entered as loose lists rather than paired to a specific input or output.",
    "Only the next internal step listed as the customer when a real end customer exists.",
    "Boundaries that drift from the charter's stated scope, so the team maps a different process than the " +
      "one chartered.",
    "Drawing it alone at a desk instead of walking it with the people who run the process.",
  ],
  source:
    "Method source (traceability matrix II.A.2, II.A.4): standard LSS curriculum -- the SIPOC model, process " +
    "elements and boundaries. Step-count range (4-7, tolerated to 9) declared in rubric R-DEF-06. Acceptance " +
    "checklist: rubric R-DEF-06.",
};
