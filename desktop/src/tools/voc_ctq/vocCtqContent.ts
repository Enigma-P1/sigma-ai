import type { HelperFrameContent } from "../helperFrameTypes";

/** Real helper content for T-05 (PLAN §4.1's VoC row + rubric R-DEF-07). */
export const vocCtqHelperContent: HelperFrameContent = {
  toolId: "T-05",
  isPlaceholder: false,
  whatThisIs:
    "A structured tree from what customers actually said, to what they need, to measurable requirements (CTQs). " +
    "The check running through every CTQ: is this what the customer critically needs, or just what's easy to measure?",
  whenToUse: "Alongside or right after SIPOC, before locking the charter's primary metric.",
  whenNotTo:
    "Don't write CTQs straight from what the process already tracks and skip the customer statements entirely -- " +
    "that's optimizing an invented voice, the exact failure mode this tool's check question exists to catch.",
  fieldGuidance: [
    {
      field: "Customer statement",
      good: "\"Parts sometimes arrive cracked.\" (close to verbatim, source noted: complaint log)",
      bad: "\"Improve packaging quality.\" (already pre-digested into a solution, no verbatim to audit)",
    },
    {
      field: "Need",
      good: "Parts must arrive intact -- traced to the cracked-parts statement above.",
      bad: "A need with no statement behind it -- there's nothing to trace it back to.",
    },
    {
      field: "CTQ measure",
      good: "Crack rate at receiving, lower is better, target <1%.",
      bad: "A measure the process already tracks that doesn't actually trace to a real need.",
    },
    {
      field: "Critical-vs-easy check",
      good: "Customer-critical: cracked parts are returned and re-ordered; not chosen for ease of measurement.",
      bad: "\"It's easy to pull from the system.\" (that's the failure mode this question exists to catch)",
    },
  ],
  whatGoodLooksLike: [
    "At least one real customer identified by role, internal or external -- \"everyone\" is nobody.",
    "Statements captured close to verbatim, each with a named source.",
    "The tree walks statement -> need -> CTQ with no dangling links, and every CTQ carries a measure and a direction.",
    "The critical-vs-easy check is answered honestly, in the student's own words, for every CTQ.",
    "The primary CTQ matches the charter's primary metric, or the mismatch is explained.",
  ],
  commonMistakes: [
    "Statements arrive pre-digested into needs, with no verbatim left to audit.",
    "A CTQ that's measurable but whose link to the need is a stretch.",
    "One customer voice standing in for two audiences that plainly differ (internal vs. external).",
    "A CTQ appearing with no customer statement behind it, treated downstream as \"the\" customer requirement.",
  ],
};
