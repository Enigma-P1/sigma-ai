import type { HelperFrameContent } from "../helperFrameTypes";

/** T-06 Process Map (swimlane) + Waste Walk helper content. "What good
 * looks like" is drawn from the rubric items that grade this tool --
 * R-MEA-01 (as-is map, anchor of the phase's map work) and R-MEA-02
 * (value analysis + waste walk) -- one source of truth, no parallel
 * checklist (tier-a-done-means §2). */
export const processMapHelperContent: HelperFrameContent = {
  toolId: "T-06",
  isPlaceholder: false,
  whatThisIs:
    "A swimlane map of the process as it actually runs: steps sit in lanes named for who does the work, " +
    "arrows show the flow including the rework loops, and every step is tagged value-add / non-value-add / " +
    "enabling and walked against the 8 wastes. The times, defect points, and strata you attach here are the " +
    "one data model every downstream Measure tool reuses -- and the engine names the bottleneck step from " +
    "your step times against the pace demand requires.",
  whenToUse:
    "First thing in Measure, right after the SIPOC fixes the boundaries. Build it by walking the process and " +
    "watching real work -- the Coffee Bar map came from standing at the counter through morning peaks, not " +
    "from memory. Update it whenever observed reality contradicts it.",
  whenNotTo:
    "Never map the procedure as written, or the improved process as hoped. The classic misuse is drawing the " +
    "intended process from memory in a back room: Analyze then hunts causes in a fiction, and every cause " +
    "found is a cause in a document, not in the process. If the map has no waits, no workarounds, and no " +
    "rework loops, it is probably that fiction.",
  fieldGuidance: [
    {
      field: "Lane name",
      good: "\"Cashier\" and \"Barista (espresso station)\" -- the roles that actually touch an order, so every handoff between them is visible.",
      bad: "One lane called \"Coffee bar.\" (one lane means no handoffs on the map -- and handoffs are where time dies)",
    },
    {
      field: "Lane owner",
      good: "Priya Shah, morning shift lead -- a person who runs that part of the work.",
      bad: "\"TBD\" or \"the team.\" (a lane nobody owns is a lane nobody will answer for)",
    },
    {
      field: "Step name",
      good: "\"Wait for milk steamer to free up\" -- a verb and an object, including the inconvenient steps the procedure never mentions.",
      bad: "\"Make drink.\" (one giant box hiding six real steps -- the waits and workarounds inside it are exactly what Measure needs to see)",
    },
    {
      field: "Type (value-add / non-value-add / enabling)",
      good: "\"Pull espresso shots\" = value-add (changes the drink, the customer pays for it). \"Order sits at pickup waiting for a name call\" = non-value-add.",
      bad: "Everything tagged value-add or enabling. (the value test was never really applied -- an honest map of a real process always finds NVA)",
    },
    {
      field: "Time (minutes)",
      good: "2.5 on \"Steam milk,\" from the time study -- observed, not recalled. Leave it blank if you haven't timed it yet; blank is honest.",
      bad: "Times recalled from memory in a meeting. (recalled times run optimistic, and the bottleneck readout inherits the error)",
    },
    {
      field: "Reason",
      good: "\"Customer pays for this and it transforms the drink -- passes the value test.\" One sentence applying the test: would the customer pay, does it change the thing, done right the first time?",
      bad: "\"It's important.\" (importance is not the test -- lots of NVA steps feel important to the people doing them)",
    },
    {
      field: "Defect point",
      good: "Yes on \"Assemble & hand off\" -- wrong-drink remakes are caught there, per the check sheet.",
      bad: "No on every step of a remake problem. (defects come from somewhere -- a defect problem mapped with zero defect points is suspect on its face)",
    },
    {
      field: "Stratification factors",
      good: "\"shift,\" \"register vs mobile order,\" \"drink type\" -- the suspected sources of difference, so this step's data can be split later.",
      bad: "None anywhere, when mornings plainly differ from afternoons. (what you don't capture as a factor you can never analyze)",
    },
    {
      field: "8-wastes walk",
      good: "Waiting checked on step 4 with the note \"barista waits ~2 min for the steamer, seen 9 of 15 mornings\" -- an observation tied to a place.",
      bad: "All 8 wastes checked with empty notes. (a recited list proves you know the acronym, not that you walked the process)",
    },
    {
      field: "Connectors (From / To)",
      good: "The full flow including the loop back: \"Check drink\" -> \"Remake\" -> \"Pull shots.\" Rework loops that exist in reality appear on the map.",
      bad: "A straight happy-path chain with no loops on a process that visibly remakes drinks.",
    },
    {
      field: "Available time (minutes)",
      good: "180 -- the 7:00-10:00 weekday peak the charter scopes, since that's when the pace matters.",
      bad: "1440 (the whole day). (averaging the empty afternoon into the peak hides the constraint the project exists to fix)",
    },
    {
      field: "Demand (units)",
      good: "95 espresso orders per peak, from the POS count -- what actually has to get through.",
      bad: "A hoped-for or rounded-up number. (the bottleneck verdict is only as honest as the demand it's judged against)",
    },
  ],
  whatGoodLooksLike: [
    "The map shows the as-is process -- walked or observed, not the procedure as written or the improved " +
      "state as hoped. The tell: it contains the inconvenient parts (workarounds, waits, informal handoffs).",
    "Start and end match the SIPOC boundaries, and the lanes (at least two) are the roles that actually " +
      "touch the work.",
    "Decision points and rework loops that exist in reality appear on the map -- a defect problem mapped " +
      "with zero rework loops is suspect on its face.",
    "Steps carry the data downstream tools reuse: times and/or defect points on the relevant steps, strata " +
      "named where a split will matter -- one project data model, many views.",
    "Every step is tagged value-add / non-value-add / enabling with the value test applied honestly: the " +
      "customer would pay for it, it changes the thing, it's done right the first time.",
    "Waste-walk entries are concrete observations tied to steps (\"waits ~2 min at step 4 for the " +
      "steamer\"), not a recited list of the 8 wastes.",
    "The tags roll up to a number Improve can attack -- NVA time or NVA step share -- and the demand block " +
      "is filled so the engine can name the bottleneck step against the required pace.",
  ],
  commonMistakes: [
    "Mapping the procedure as written (or as remembered in a conference room) instead of walking the real " +
      "process -- the one failure that voids everything built on the map.",
    "Happy path only: no waits, no workarounds, no rework loops.",
    "Altitude jumps -- three giant boxes, then twelve micro-steps. Keep one consistent level of detail.",
    "Tagging everything value-add or enabling because NVA feels like an accusation. It isn't; it's the " +
      "improvement inventory.",
    "Lanes drawn by department when the handoffs that matter happen between roles.",
  ],
  source:
    "Method source (traceability matrix III.A, I.B.1, I.B.2): standard LSS curriculum -- swimlane process " +
    "mapping, the value-add test, the 8 wastes. Bottleneck readout per matrix correction A-7: longest " +
    "effective step time vs required pace (available time / demand), computed by the engine, never on " +
    "screen. Acceptance checklist: rubric R-MEA-01, R-MEA-02.",
};
