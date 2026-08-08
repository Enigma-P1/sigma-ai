import type { HelperFrameContent } from "../helperFrameTypes";

/** T-22 Control Plan + OCAP + Scheduled Check-ins helper content. "What
 * good looks like" restates the rubric items that grade this tool --
 * R-CTL-03 (control plan core, anchor) and R-CTL-04 (response plan,
 * training, check-ins) -- one source of truth, no parallel checklist
 * (tier-a-done-means §2). */
export const controlPlanHelperContent: HelperFrameContent = {
  toolId: "T-22",
  isPlaceholder: false,
  whatThisIs:
    "The document that keeps the fix alive after the project ends: what's monitored, how it's measured, " +
    "where, how often, and BY WHOM -- a named person who has accepted the role. An unowned control plan is " +
    "theater, and the tool flags it as exactly that. Around the plan table sit the three things that make " +
    "it run: the OCAP (out-of-control action path -- what happens the moment a signal fires), the training " +
    "and handoff block (a fix nobody's trained on dies with the project), and scheduled check-ins the app " +
    "chases -- \"week 3: is the fix holding? enter this week's numbers\" -- scored against the frozen " +
    "control limits.",
  whenToUse:
    "As Improve closes, so what Control monitors is the implemented state. At the Coffee Bar: handoff " +
    "minutes (the primary CTQ) checked daily during the 7:00-10:00 peak, plus the changed method itself -- " +
    "the fix is monitored, not just the outcome -- with Priya Shah, the morning shift lead who owns the " +
    "process on the charter, as the named owner who accepted. The check-ins exist because Control is where " +
    "real projects go to die: control-phase tools are about 6% of real-world tool usage in the research " +
    "this product is built on. Spreadsheets fail here because nobody chases the next step; this schedules " +
    "the chase.",
  whenNotTo:
    "The classic misuse is the plan written to close the project instead of to run the process: owner " +
    "\"the team,\" frequency left at a default, check-ins scheduled and never answered. Each of those is a " +
    "named failure here -- \"the team\" is on the owner blocklist, an unreasoned frequency is the Needs-" +
    "work line, and a due check-in sitting unanswered is the abandonment this tool exists to catch. Don't " +
    "fill it in for a pilot-only change either: the plan monitors what was actually implemented.",
  fieldGuidance: [
    {
      field: "Characteristic / How measured / Where",
      good: "handoff_minutes, measured register-timestamp-to-name-call in tenths of a minute (the baseline's own operational definition, linked), at the register POS.",
      bad: "\"Speed, observed, at the bar.\" (nothing here could be checked by two people the same way -- the link to the operational definition is the point)",
    },
    {
      field: "Frequency + Reason",
      good: "Daily during peak, because ~48 orders flow per peak and a drift would show within a day -- the frequency has a reason tied to drift speed or volume.",
      bad: "\"Weekly\" left standing because it was the default. (a default with no rationale is the Needs-work line -- and a monthly check on a daily process misses three weeks of drift)",
    },
    {
      field: "Owner + Accepted",
      good: "Priya Shah -- a named person on the charter team who has actually accepted the role, box checked because it happened.",
      bad: "\"TBD,\" \"the team,\" or a bare role. (the blocklist catches these; an unowned plan is theater, and a named owner who never accepted is theater with a cast list)",
    },
    {
      field: "CTQ / Improve fix checkboxes",
      good: "Both covered: the primary CTQ row and a row for what Improve changed -- the paired-shot method being followed is monitored, not just the minutes.",
      bad: "Outcome-only monitoring. (when the number drifts you won't know whether the method lapsed or the method stopped working -- watch the fix too)",
    },
    {
      field: "OCAP entries",
      good: "Four concrete elements per monitored item: first response (re-check the next three orders), containment (call the backup barista in), escalation trigger and recipient (two signals in a week -> Dana Ellis), acting owner.",
      bad: "\"Investigate and fix.\" (not an action path -- the person on shift at 7:40 with a fired signal needs steps, not a sentiment)",
    },
    {
      field: "Training & Handoff rows",
      good: "Who gets trained, on the T-24 SOP by artifact id, by whom, by when, verified how -- sign-off or an observed demonstration, not \"told about it.\"",
      bad: "Training listed with no verification method. (a fix nobody is verifiably trained on dies with the project -- the row exists to outlive you)",
    },
    {
      field: "Check-ins (as-of date, entered numbers)",
      good: "Every check-in due by the as-of date answered with numbers against the frozen limits -- the next due date is computed from the cadence, never hand-typed.",
      bad: "A schedule accepted at close-out and never answered. (due-and-unanswered is the 6% statistic happening to you in real time)",
    },
  ],
  whatGoodLooksLike: [
    "Every monitored item names the characteristic, how it's measured (linked to its operational " +
      "definition), where, how often, and who -- a named person who has accepted the role, real enough to " +
      "appear on the charter team or a handoff note.",
    "The monitoring frequency has a reason -- tied to how fast the process could drift or how much volume " +
      "flows -- not a default left standing.",
    "The plan covers what Improve changed PLUS the primary CTQ (and the guardrail metric) -- the fix is " +
      "monitored, not just the outcome.",
    "Every monitored item has an OCAP with the four concrete elements: actionable first response, " +
      "containment step, escalation trigger and recipient, acting owner.",
    "The training block is complete -- who, on what (the T-24 SOP, which exists and is referenced), by " +
      "whom, by when, verified how -- and the SOP link resolves.",
    "The scheduled check-ins are accepted, and every check-in due within the window is answered with " +
      "numbers against the limits.",
  ],
  commonMistakes: [
    "No named owner -- an unowned control plan is no control plan, and the project's sustainment claim is " +
      "void. This is the tool's theater flag, and the rubric agrees with it.",
    "A stale owner: the named person left the role and nobody logged a re-handoff -- an unowned plan " +
      "wearing a name. Multi-shift processes need a primary owner per operating unit, not one global name.",
    "Frequency defaulted with no rationale, or the guardrail metric missing from the plan.",
    "An OCAP that says \"investigate and fix\" -- the primary CTQ with no followable response path means a " +
      "signal would fire into silence, which voids \"the improvement is protected.\"",
    "Training rows without a verification method -- listed is not trained, and told is not verified.",
    "Check-ins scheduled to look complete, then left unanswered as they come due -- the exact abandonment " +
      "pattern the Control phase is famous for.",
  ],
  source:
    "Method source: standard control-plan practice per traceability matrix VI.B.1 (named owner, cadence, " +
    "OCAP) and VI.B.3 (training & handoff block -- matrix correction A-5: a fix nobody is trained on dies " +
    "with the project); golden G-ctrlplan-01. Scheduled check-ins are PLAN §4.1's answer to Control being " +
    "the field's most-abandoned phase (~6% of real tool usage in the plan's research); next_due is " +
    "computed by artifacts/control_plan.py from the cadence, never hand-typed. Acceptance checklist: " +
    "rubric R-CTL-03 (anchor), R-CTL-04.",
};
