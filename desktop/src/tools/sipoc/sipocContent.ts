import type { HelperFrameContent } from "../helperFrameTypes";

/** Real helper content for T-04 (PLAN §4.1's SIPOC row + rubric R-DEF-06). */
export const sipocHelperContent: HelperFrameContent = {
  toolId: "T-04",
  isPlaceholder: false,
  whatThisIs:
    "A five-column map of the process at a high level: Suppliers, Inputs, Process (steps), Outputs, Customers. " +
    "It sets the boundaries everything downstream -- baselining, root-cause work, the control plan -- has to agree with.",
  whenToUse: "Right after the charter, before any detailed process mapping (T-06) or data collection.",
  whenNotTo:
    "Don't drop to task-level detail here -- \"open the valve, check the gauge, close the valve\" belongs in the " +
    "detailed process map (T-06), not SIPOC. SIPOC stays at the altitude a stranger could follow in one read.",
  fieldGuidance: [
    {
      field: "Process steps",
      good: "4-7 high-level steps: receive order, prep, brew, package, hand off.",
      bad: "19 steps down to \"press the button\" -- that's the detailed map's job, not SIPOC's.",
    },
    {
      field: "Supplier / input pairing",
      good: "Resin vendor -> raw resin pellets (paired, one row).",
      bad: "A free-floating supplier list with no matching input -- nobody can tell who supplies what.",
    },
    {
      field: "Output / customer pairing",
      good: "Molded part -> Assembly line (the team that actually receives it).",
      bad: "Customer listed as only the next internal step when a real end customer plainly exists downstream.",
    },
    {
      field: "Scope start / end",
      good: "Start: \"order received.\" End: \"order handed off\" -- matching the charter's scope in/out.",
      bad: "Boundaries that quietly cover a different process than the one the charter scoped.",
    },
  ],
  whatGoodLooksLike: [
    "All five columns are populated, with the process column at 4-7 high-level steps.",
    "Every supplier is paired to its input, every output to the customer who actually receives it.",
    "The CTQ-bearing output appears here, so the VoC/CTQ tree (T-05) has something real to hang from.",
    "The process column's start and end boundaries match the charter's scope in/out.",
  ],
  commonMistakes: [
    "Process steps written at task level instead of high-level (that's T-06's job).",
    "Suppliers or customers listed as a loose list, not paired to a specific input or output.",
    "Customers named as only the next internal handoff when a real end customer exists.",
    "SIPOC boundaries that contradict the charter's stated scope -- the team ends up mapping a different process.",
  ],
};
