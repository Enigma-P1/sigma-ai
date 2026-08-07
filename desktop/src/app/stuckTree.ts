/** The "I'm stuck" offline decision tree (PLAN §4.2 item 3): 2-3 plain-
 * English questions routing to a tool, worked offline, no AI. M1 scope is
 * the Define phase only, hardcoded honestly rather than faked for every
 * phase (per the build brief). */

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

export function isStuckLeaf(node: StuckNode): node is StuckLeaf {
  return node.kind === "leaf";
}
