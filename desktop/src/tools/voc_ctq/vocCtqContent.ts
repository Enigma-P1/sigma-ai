import type { HelperFrameContent } from "../helperFrameTypes";

/** T-05 VoC -> CTQ Tree helper content. "What good looks like" is drawn from
 * rubric R-DEF-07 -- one source of truth, no parallel checklist
 * (tier-a-done-means §2). The namesake critical-vs-easy check is a required
 * field on every CTQ (artifacts/voc_ctq.py). */
export const vocCtqHelperContent: HelperFrameContent = {
  toolId: "T-05",
  isPlaceholder: false,
  whatThisIs:
    "A structured tree from what customers actually said, to the needs behind those statements, to CTQs -- " +
    "critical-to-quality requirements measurable enough to run a project on. One check runs through every " +
    "CTQ: is this what the customer critically needs, or just what the process finds easy to measure?",
  whenToUse:
    "Alongside or right after SIPOC, before the charter's primary metric is locked -- the primary CTQ and " +
    "the charter metric should end up being the same measure.",
  whenNotTo:
    "Don't build the tree backward from metrics the process already tracks and skip the customer statements. " +
    "That is the classic misuse -- optimizing an invented voice. A CTQ with no customer statement behind it, " +
    "treated downstream as \"the customer requirement,\" fails outright (R-DEF-07).",
  fieldGuidance: [
    {
      field: "Customers",
      good: "\"External - student buying coffee before class\" -- a role, internal or external, specific enough to interview.",
      bad: "\"Everyone.\" (everyone is nobody -- and two audiences that plainly differ get flattened into one voice)",
    },
    {
      field: "Statement text",
      good: "\"I skip coffee before my 8am -- the line takes forever.\" (close to verbatim, in the customer's own words)",
      bad: "\"Customers want faster service.\" (pre-digested into a need -- there's no verbatim left to audit)",
    },
    {
      field: "Statement source",
      good: "Interview, complaint log, survey, or direct observation -- plus the detail: \"Q2 comment cards.\"",
      bad: "No source noted. (an unsourced quote can't be told apart from something the team made up)",
    },
    {
      field: "Needs",
      good: "\"Get the drink fast enough to make class\" -- one plain-English need, linked to the statements that voice it.",
      bad: "A need linked to no statement. (the tree's chain of custody breaks at its first link)",
    },
    {
      field: "CTQ measure",
      good: "\"Average order-to-handoff time, weekday 7:00-10:00 peak, in minutes\" -- two people would measure it the same way.",
      bad: "\"Customer satisfaction.\" (not measurable as stated -- measured how, on whom, by whom?)",
    },
    {
      field: "Direction and target",
      good: "Lower is better, target 5.0 minutes -- a direction always, a target where the customer's tolerance is known.",
      bad: "No direction. (a measure that could \"improve\" in either direction proves nothing)",
    },
    {
      field: "Critical to the customer, or just easy to measure?",
      good: "\"Customer-critical: three of the five statements are about the wait itself\" -- answered per CTQ, in your own words.",
      bad: "\"It's easy to pull from the system.\" (that is the exact failure this question exists to catch)",
    },
    {
      field: "Primary CTQ",
      good: "The one CTQ the project will baseline and improve -- the same measure the charter carries.",
      bad: "A primary chosen because its data is convenient, while the customers' actual pain sits unmeasured.",
    },
    {
      field: "Charter metric link",
      good: "\"C1 is the charter metric: same measure, same direction, target 5.0 min\" -- or an honest note explaining the mismatch.",
      bad: "Filled as a formality while the two measures quietly differ. (the project then proves something it never promised)",
    },
  ],
  whatGoodLooksLike: [
    "At least one real customer is identified by role, internal or external -- \"everyone\" is nobody.",
    "Customer statements are captured close to verbatim, each with its source noted (interview, complaint " +
      "log, survey, direct observation).",
    "The tree walks statement -> need -> measurable CTQ with no dangling links, and every CTQ carries a " +
      "measure and a direction or target.",
    "The critical-vs-easy check is answered for every CTQ, honestly and in your own words -- not copied " +
      "boilerplate.",
    "The primary CTQ is the charter's primary metric, or the mismatch is explained on the artifact.",
  ],
  commonMistakes: [
    "Statements arriving pre-digested into needs, with no verbatims left to audit.",
    "A CTQ that is measurable but whose link to the stated need is a stretch.",
    "One customer voice standing in for two that plainly differ (the student racing to class vs. the " +
      "regular who wants the drink made right).",
    "CTQs written from what the process already tracks, with customer statements back-filled to justify them.",
    "A CTQ with no direction or target, so \"improvement\" has no defined meaning.",
  ],
  source:
    "Method source (traceability matrix II.B.1-II.B.3): standard LSS curriculum -- customer identification, " +
    "customer data collection, and the CTQ tree. Layer-2 theme extraction is an assist only; manual capture " +
    "always works (PLAN §4.1). Acceptance checklist: rubric R-DEF-07.",
};
