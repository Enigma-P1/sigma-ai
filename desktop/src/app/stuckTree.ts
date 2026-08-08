/** The "I'm stuck" offline decision tree (PLAN §4.2 item 3): 2-3 plain-
 * English questions routing to a tool, worked offline, no AI. Phase-aware
 * (Jordan usability fix): Define and Measure each carry their own tree;
 * a phase with no tree yet gets an honest fallback leaf rather than
 * silently reusing Define's. Completion-aware (same fix): StuckButton
 * runs a tree's leaf recommendation through nextNotDoneToolId below
 * before showing it, so this file's trees can name a natural starting
 * point without needing to know project state themselves. */

import type { Phase, ProjectMetadata } from "../api/types";
import { toolsForPhase } from "./tools";

export interface StuckLeaf {
  kind: "leaf";
  id: string;
  recommendation: string;
  explanation: string;
  toolId?: string;
}

export interface StuckQuestion {
  kind: "question";
  id: string;
  question: string;
  yes: StuckNode;
  no: StuckNode;
}

export type StuckNode = StuckQuestion | StuckLeaf;

export function isStuckLeaf(node: StuckNode): node is StuckLeaf {
  return node.kind === "leaf";
}

const recommendSipoc: StuckLeaf = {
  kind: "leaf",
  id: "leaf-sipoc",
  recommendation: "Map the process next — SIPOC (T-04)",
  explanation:
    "You have a charter and you know what the customer needs. Next, name the process boundaries: what comes in, " +
    "from whom, what goes out, to whom. Worth a COPQ pass (T-02) too, any time you need a dollar figure for leadership.",
  toolId: "T-04",
};

const questionKnowsCustomerNeed: StuckQuestion = {
  kind: "question",
  id: "q-customer-need",
  question: "Do you know exactly what your customer or stakeholder needs — in their own words, not just what's easy to measure?",
  yes: recommendSipoc,
  no: {
    kind: "leaf",
    id: "leaf-voc",
    recommendation: "Capture the customer's actual need — VoC → CTQ Tree (T-05)",
    explanation:
      "Easy-to-measure and customer-critical aren't the same thing. Gather real statements from the people the " +
      "process serves, turn them into needs, then into measurable CTQs, before you lock the metric.",
    toolId: "T-05",
  },
};

const questionHasCharter: StuckQuestion = {
  kind: "question",
  id: "q-has-charter",
  question: "Do you have a written charter for it yet — problem statement, goal, scope, and team?",
  yes: questionKnowsCustomerNeed,
  no: {
    kind: "leaf",
    id: "leaf-charter",
    recommendation: "Write the charter — Project Charter (T-03)",
    explanation:
      "A scoped problem still needs to be written down before anyone can act on it: what/where/when/how much, a " +
      "SMART goal, scope in/out, a named owner, and a timeline. This is the tool that makes it real.",
    toolId: "T-03",
  },
};

export const DEFINE_STUCK_TREE: StuckQuestion = {
  kind: "question",
  id: "q-has-scoped-problem",
  question: "Do you already have a specific, scoped problem you're working on?",
  yes: questionHasCharter,
  no: {
    kind: "leaf",
    id: "leaf-picker",
    recommendation: "Start with the Project Picker (T-01)",
    explanation:
      "Before anything else gets built, check whether this is actually a workable first project — narrow scope, " +
      "a measurable outcome, data you can get, an owner who cares, plausible impact. Takes minutes, saves weeks.",
    toolId: "T-01",
  },
};

// ---- Measure ----------------------------------------------------------

const questionMsaChecked: StuckQuestion = {
  kind: "question",
  id: "q-measure-msa-checked",
  question: "Has the measurement system itself been checked yet — test/retest repeatability or two-rater agreement (T-12)?",
  yes: {
    kind: "leaf",
    id: "leaf-measure-baseline",
    recommendation: "Run the baseline — Stability then Capability (T-13)",
    explanation:
      "Data collected, measurement system checked — now let the engine tell you whether the process is stable, " +
      "and only then whether it's capable. Never the other way around.",
    toolId: "T-13",
  },
  no: {
    kind: "leaf",
    id: "leaf-measure-msa",
    recommendation: "Check the measurement system — Measurement Check (T-12)",
    explanation:
      "Real data is in hand, but a baseline built on an unchecked gauge is a guess wearing a number's clothes. " +
      "Confirm the measurement first — the engine blocks capability language until this passes.",
    toolId: "T-12",
  },
};

const questionHasRealData: StuckQuestion = {
  kind: "question",
  id: "q-measure-has-data",
  question: "Have you collected real process data yet — a check sheet, time study, or an imported dataset?",
  yes: questionMsaChecked,
  no: {
    kind: "leaf",
    id: "leaf-measure-collect",
    recommendation: "Plan the collection — Data Collection Plan (T-11)",
    explanation:
      "Before tallying or timing anything, pin the operational definition (two people would measure it the same " +
      "way), the data type, and the sample size. That plan is what T-08/T-09's numbers mean anything against.",
    toolId: "T-11",
  },
};

export const MEASURE_STUCK_TREE: StuckQuestion = {
  kind: "question",
  id: "q-measure-has-baseline",
  question: "Do you already have a stable, engine-verified baseline number for this metric?",
  yes: {
    kind: "leaf",
    id: "leaf-measure-charts",
    recommendation: "Visualize it — Pareto / Histogram / Run Chart (T-14)",
    explanation:
      "Baseline in hand — now let the charts carry the read: where the vital few live (Pareto), how the data's " +
      "shaped (histogram), whether it drifts over time (run chart).",
    toolId: "T-14",
  },
  no: questionHasRealData,
};

/** Phase -> its stuck tree, only for phases with one written yet (Define,
 * Measure). Absent for every other phase -- an honest "not built here
 * yet" leaf, not a silent reuse of Define's questions. */
export const STUCK_TREE_BY_PHASE: Partial<Record<Phase, StuckQuestion>> = {
  Define: DEFINE_STUCK_TREE,
  Measure: MEASURE_STUCK_TREE,
};

export function stuckTreeNotBuiltLeaf(phase: Phase): StuckLeaf {
  return {
    kind: "leaf",
    id: "leaf-not-built",
    recommendation: `No stuck-tree for ${phase} yet`,
    explanation:
      "This phase's guided routing hasn't shipped yet. Use the DMAIC rail on the left to see what's available " +
      `in ${phase}, or open a tool directly.`,
  };
}

/** Completion-aware substitution (Jordan usability fix): never point at a
 * tool the project has already completed. `doneToolIds` is whatever the
 * caller considers "done" for this project (StuckButton passes
 * project.artifact_index's tool_ids, unioned with any locally-marked-done
 * tools like T-14's chart-visited state). Walks the phase's LIVE tools in
 * declared order starting from the leaf's own tool, wrapping once; null
 * means every live tool in the phase already reads done. */
export function nextNotDoneToolId(phase: Phase, leafToolId: string | undefined, doneToolIds: ReadonlySet<string>): string | null {
  const liveIds = toolsForPhase(phase).filter((t) => t.live).map((t) => t.id);
  if (liveIds.length === 0) return null;
  if (leafToolId && !doneToolIds.has(leafToolId)) return leafToolId;

  const startIndex = leafToolId ? Math.max(liveIds.indexOf(leafToolId), 0) : 0;
  for (let offset = 0; offset < liveIds.length; offset++) {
    const candidate = liveIds[(startIndex + offset) % liveIds.length];
    if (!doneToolIds.has(candidate)) return candidate;
  }
  return null; // every live tool in this phase is already done
}

/** project.artifact_index's tool_ids, as a plain set -- the "done" signal
 * every tool-status pill in the rail already uses (PhaseSection.toolStatus). */
export function doneToolIdsFromProject(project: ProjectMetadata): Set<string> {
  return new Set(Object.values(project.artifact_index).map((e) => e.tool_id));
}
