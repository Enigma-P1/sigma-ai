/** Every word this app puts in front of someone who never asked to learn it.
 *
 * WHY THIS EXISTS. Two supervisors used Sigma AI on their own data and both
 * hit the same wall: not the statistics, the vocabulary. One listed
 * nineteen terms he met with no explanation on the screen where they
 * appeared -- Green Belt, DMAIC, EXIT-01, provenance anchor, SHA-256 --
 * and said a supervisor "should not have to open a training essay to
 * understand why a button is disabled". The other closed with "if it asks
 * me what a sigma is, I'm going back to the Excel".
 *
 * The definitions here are written for them, not for a Black Belt: what it
 * is, why you would care, in the words someone running a warehouse floor
 * would use. Where a term is genuinely a piece of jargon the user does not
 * need, the definition says so rather than pretending it matters.
 *
 * `where` names the screen it is first met on, so the entry can say "you
 * saw this on..." rather than making someone hunt.
 */

export interface GlossaryEntry {
  term: string;
  short: string;
  where?: string;
}

export const GLOSSARY: GlossaryEntry[] = [
  // --- The words on the very first screen -------------------------------
  {
    term: "DMAIC",
    where: "the first screen, and the phase list down the left",
    short:
      "Define, Measure, Analyze, Improve, Control — five stages, in order. Work out what the problem is, "
      + "measure how bad it is now, find what's causing it, change something, then make the change stick. "
      + "The tool list on the left is grouped by those five stages. You don't have to learn it; working "
      + "top to bottom is the method.",
  },
  {
    term: "Green Belt",
    where: "the first screen",
    short:
      "A level of Six Sigma training, roughly \"can run an improvement project\". It describes how deep this "
      + "app goes, not something you need to have. Nothing here asks whether you're certified.",
  },
  {
    term: "Six Sigma",
    short:
      "A way of improving processes by measuring them instead of guessing. The name comes from a statistical "
      + "target for how rarely a process should produce a defect. You can use every tool here without caring "
      + "where the name came from.",
  },
  {
    term: "PDCA quick path",
    where: "T-01 Project Picker",
    short:
      "Plan-Do-Check-Act — a shorter loop for a problem too small to be worth the full five stages. If the fix "
      + "is obvious and cheap, take this route and skip the ceremony.",
  },
  {
    term: "EXIT-01, EXIT-10, EXIT-15 (and other EXIT codes)",
    where: "T-01, and various tools",
    short:
      "An honest dead end the app is allowed to reach — \"this isn't a good project\", \"this version doesn't "
      + "compute that\". The number is just a label so the same situation is named the same way everywhere. "
      + "Reaching one is a real answer, not a failure.",
  },

  // --- The tools, by the acronyms they carry ----------------------------
  {
    term: "SIPOC",
    where: "T-04",
    short:
      "Suppliers, Inputs, Process, Outputs, Customers. One page saying where a process starts and stops and "
      + "who it touches — so an argument about the fix doesn't turn out to be an argument about scope.",
  },
  {
    term: "VoC → CTQ",
    where: "T-05",
    short:
      "Voice of the Customer to Critical To Quality. Turn what a customer actually complains about (\"my order "
      + "is always wrong\") into something you can measure (\"wrong-item rate per 1,000 order lines\").",
  },
  {
    term: "COPQ",
    where: "T-02",
    short:
      "Cost of Poor Quality — what the problem costs you in money: rework, scrap, credits, overtime, the "
      + "driver you sent back across town. The number you use when you need a manager to care.",
  },
  {
    term: "MSA",
    where: "T-12",
    short:
      "Measurement System Analysis. Before trusting a number, check the way you collect it: would two people "
      + "recording the same thing write the same value? If not, every chart built on it is measuring the "
      + "clipboard, not the process.",
  },
  {
    term: "Gage R&R",
    where: "T-35",
    short:
      "Repeatability and Reproducibility. Repeatability is one person measuring the same item twice and getting "
      + "the same answer; reproducibility is two people getting the same answer. It tells you how much of the "
      + "variation you're seeing is the process and how much is the measuring.",
  },
  {
    term: "A3",
    where: "T-25",
    short:
      "A one-page summary of the whole project — named after the European paper size it's meant to fit on. "
      + "Problem, cause, fix, proof, and what keeps it fixed, on one sheet you can hand to someone.",
  },
  {
    term: "Tollgate",
    short:
      "A checkpoint between stages: a short list of \"is this actually done?\" questions before moving on. "
      + "The point is to catch a stage that was skipped rather than finished.",
  },
  {
    term: "6M",
    where: "T-15 Fishbone",
    short:
      "The six headings a fishbone diagram sorts causes under: People, Method, Machine, Material, Measurement, "
      + "Environment. They exist to stop everyone blaming the same thing — usually People.",
  },
  {
    term: "RPN",
    where: "T-16 FMEA",
    short:
      "Risk Priority Number — severity × how often it happens × how likely you are to catch it, each rated 1–10. "
      + "A rough ranking of which failure to worry about first. Useful for sorting; not a real measurement.",
  },

  // --- Words on the charts and the numbers ------------------------------
  {
    term: "Vital few",
    where: "the Pareto chart, T-14",
    short:
      "The handful of categories that carry most of the problem — the two aisles behind 80% of the errors. "
      + "The chart highlights them. If it takes most of your categories to reach 80%, there is no vital few, "
      + "and the chart says that instead.",
  },
  {
    term: "Cumulative share",
    where: "the Pareto chart, T-14",
    short:
      "The rising line across a Pareto: how much of the total you've accounted for once you include everything "
      + "to the left of where you're looking. Where it crosses 80% is the usual \"stop here\" mark.",
  },
  {
    term: "USL and LSL",
    short:
      "Upper and Lower Specification Limit — the fastest and slowest, biggest and smallest you'll accept. "
      + "Your rule, not a statistic: \"orders must be picked within 5 minutes\" is a USL of 5.",
  },
  {
    term: "sd (standard deviation)",
    short:
      "How spread out the numbers are. A small sd means most values sit close to the average; a large one means "
      + "they're all over the place. Two processes can share an average and behave completely differently.",
  },
  {
    term: "Cpk and Ppk",
    where: "T-13 baseline",
    short:
      "How comfortably a process fits inside the limits you set. Above about 1.33 is usually called capable; "
      + "below 1 means you're producing out-of-spec work as a matter of routine. Only meaningful once the "
      + "process is stable — which is why the app checks stability first and refuses to skip it.",
  },
  {
    term: "Sigma level",
    short:
      "Another way of saying how often the process produces a defect, on a scale where higher is better. "
      + "Six Sigma is the famous target. It's a translation of the defect rate, not extra information.",
  },
  {
    term: "DPMO",
    short:
      "Defects Per Million Opportunities. Lets you compare a process making 40 things a day with one making "
      + "40,000, by asking how often it goes wrong per chance to go wrong rather than per day.",
  },
  {
    term: "FPY and RTY",
    where: "T-10",
    short:
      "First Pass Yield and Rolled Throughput Yield. FPY is how much gets through one step right the first "
      + "time; RTY multiplies those together across every step. RTY is usually the number that shocks people, "
      + "because five steps at 95% each is 77% overall.",
  },
  {
    term: "Stratification factor",
    where: "T-11",
    short:
      "Something you record alongside each measurement so you can split the data by it later — shift, machine, "
      + "person, day of week. If you don't capture it while collecting, you can't ask the question afterwards.",
  },
  {
    term: "Guardrail metric",
    short:
      "Something you watch to make sure your fix didn't break something else. Speeding up picking is no good if "
      + "the error rate doubles — the error rate is the guardrail.",
  },
  {
    term: "Operational definition",
    short:
      "Writing down exactly what counts, so two people measure the same thing the same way. \"Late\" means "
      + "nothing until you say whether the clock starts when the order is placed or when it's picked.",
  },

  // --- The plumbing, and whether you need to care -----------------------
  {
    term: "Provenance anchor / SHA-256",
    where: "after saving an imported file",
    short:
      "A fingerprint of the exact file you imported. Later, when a chart says 1.26%, the app records which "
      + "fingerprint that number came from — so months on you can still prove which spreadsheet produced which "
      + "claim. You never need to read the long string; it's there so the answer to \"where did this come "
      + "from?\" is never a shrug.",
  },
  {
    term: "Artifact",
    short:
      "Anything you've saved in a tool — a charter, a fishbone, a control plan. The app keeps every version "
      + "rather than overwriting, so you can see what a tool said before you changed it.",
  },
  {
    term: "Draft",
    short:
      "Typing the app has kept for you but that you haven't saved as a finished piece of work. It survives "
      + "closing the app. It doesn't count towards a tool being done — that still needs a real save.",
  },
];

