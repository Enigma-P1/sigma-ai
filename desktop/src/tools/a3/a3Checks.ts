import type { TollgatePhase, TollgateQuestion } from "../../api/types";

/** Mirrors engine/sigma_engine/artifacts/a3.py's TOLLGATE_QUESTIONS by
 * hand (fmeaLogic.ts's CLIENT_ANCHORS convention) -- this engine's own
 * original wording, available for display before the first save. Once a
 * version is saved, the server-echoed `tollgates[].questions` is what
 * renders (A3Form.tsx), kept identical here on purpose. */
export const CLIENT_TOLLGATE_QUESTIONS: Record<TollgatePhase, TollgateQuestion[]> = {
  Define: [
    { question_id: "define-1", text: "Is the problem stated in measurable terms, with no cause and no fix implied?" },
    { question_id: "define-2", text: "Does the charter name a process owner who has actually agreed to the scope?" },
    { question_id: "define-3", text: "Is the business impact stated in dollars or hours, and does it hold up against an independent number?" },
  ],
  Measure: [
    { question_id: "measure-1", text: "Is the baseline built on a process the data shows is stable, not just assumed to be?" },
    { question_id: "measure-2", text: "Has the measurement system itself been checked, and did it pass?" },
    { question_id: "measure-3", text: "Is the operational definition tight enough that two different people would measure the same thing the same way?" },
  ],
  Analyze: [
    { question_id: "analyze-1", text: "Does every candidate cause carry actual evidence, not just an opinion in the room?" },
    { question_id: "analyze-2", text: "Are the verified causes the ones the data points to, not just the easiest ones to fix?" },
    { question_id: "analyze-3", text: "Has every severity-9/10 failure mode been given an action, not just logged and left?" },
  ],
  Improve: [
    { question_id: "improve-1", text: "Was exactly one change piloted at a time, with a success threshold set before the data came in?" },
    { question_id: "improve-2", text: "Does the before/after proof account honestly for anything else that changed during the pilot?" },
    { question_id: "improve-3", text: "How much of the original gap does this fix close, and what is the plan for what's left?" },
  ],
  Control: [
    { question_id: "control-1", text: "Does every monitored item have a real, named owner who has accepted the role?" },
    { question_id: "control-2", text: "Is there an out-of-control response path a person could actually follow, today, without asking what it means?" },
    { question_id: "control-3", text: "Is someone trained on the new method, by name, with a way to verify they can actually do it?" },
  ],
  Wrap: [
    { question_id: "wrap-1", text: "Does the realized benefit trace to the measured improvement, not to the original COPQ hope?" },
    { question_id: "wrap-2", text: "Are the lessons learned substantive, including at least one thing that didn't work?" },
    { question_id: "wrap-3", text: "Is every open item handed off to a named owner, not left to fall through?" },
  ],
};

export const A3_CHECK_LABELS: Record<string, string> = {
  panels_seeded_or_narrated: "Every panel is seeded or narrated",
  realized_benefits_present: "Realized benefits name the COPQ re-run + window",
  tollgates_answered: "Every phase's tollgate is answered",
  lessons_substantive: "Lessons include something that went wrong",
  open_items_have_owners: "Open items have owners",
  close_blocked_surfaced: "No unaddressed severity-9/10 FMEA row",
};
