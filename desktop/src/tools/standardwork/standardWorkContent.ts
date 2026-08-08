import type { HelperFrameContent } from "../helperFrameTypes";

/** T-24 Standard Work / SOP helper content. "What good looks like"
 * restates the rubric item that grades this tool -- R-CTL-06 (standard
 * work / SOP) -- one source of truth, no parallel checklist
 * (tier-a-done-means §2). */
export const standardWorkHelperContent: HelperFrameContent = {
  toolId: "T-24",
  isPlaceholder: false,
  whatThisIs:
    "The improved method written down so it survives the author. Each step is an action plus its standard " +
    "-- what right looks like, observably -- and the steps that changed from the old method are " +
    "highlighted, because that's where training starts and where backsliding starts. Version, owner, and " +
    "date make it a controlled document instead of a note; the SOP is the training artifact -- the exact " +
    "document the control plan's training rows point at. One method, one source.",
  whenToUse:
    "Once the proven change is implemented and Control needs a method to train and hold. At the Coffee " +
    "Bar: seed the steps from the process map's improved state, then write the standard for each -- the " +
    "paired-shot sequencing marked as changed-from-prior, with a standard someone could check against the " +
    "3.75-minute order pace the peak demands (48 orders in 180 minutes). Priya Shah owns v1, effective " +
    "dated. The test while writing: could a qualified-but-new barista run the morning from this page, " +
    "without the author in the building?",
  whenNotTo:
    "The classic misuse is documenting the OLD process with a patch note bolted on -- the SOP must be the " +
    "improved method as one clean sequence, or the method being trained is not the method that was proven. " +
    "Equally common: policy prose. \"Ensure quality\" and \"manage the queue\" are values, not steps; " +
    "nothing in them can be followed, checked, or trained. And an SOP that contradicts the implemented " +
    "change voids the sustainment story outright -- that is the invalidating line.",
  fieldGuidance: [
    {
      field: "Title / Version / Owner / Effective date",
      good: "\"Morning espresso service -- v1, Priya Shah, effective 2026-10-15.\" Version and owner are what let anyone tell current from stale, and let v2 supersede v1 cleanly.",
      bad: "An undated, unowned page. (nobody can tell whether it's the method or a museum piece)",
    },
    {
      field: "Supersedes",
      good: "Names the prior instruction it replaces -- the laminated card from 2024 -- so two methods never circulate as peers.",
      bad: "Left blank while the old card stays taped to the machine. (two sources means no standard)",
    },
    {
      field: "Seed steps from the process map",
      good: "Seeded from the map's improved state, then each step's standard filled in by hand -- the map gives the skeleton, you give the checkable detail.",
      bad: "Seeded and left. (map steps are names, not instructions -- a step without its standard is half a step)",
    },
    {
      field: "Step: Action",
      good: "\"Pull both shots for back-to-back milk drinks before steaming\" -- an action a qualified-but-new person could take, in the order the work happens.",
      bad: "\"Ensure espresso quality.\" (policy, not action -- the prescore flags steps that read as values instead of verbs)",
    },
    {
      field: "Step: Standard (what right looks like)",
      good: "Observable and checkable: \"second drink's shots pulled within 30 seconds of the first; queue ahead of the station no deeper than three cups.\"",
      bad: "\"Done properly.\" (a standard nobody could check is a preference, not a standard)",
    },
    {
      field: "Changed from the prior method",
      good: "Checked on exactly the steps the Improve change altered -- the highlighted steps are the training conversation and the backslide watchlist.",
      bad: "Nothing marked. (a trainer can't find what changed, so they train the old habit with new paper)",
    },
  ],
  whatGoodLooksLike: [
    "The improved method is written as steps a qualified-but-new person could follow -- each step an " +
      "action with its standard -- and the points that changed from the old method are highlighted.",
    "Version, owner, and date are set; if an older instruction existed, the SOP names what it supersedes.",
    "The SOP matches the process map's improved state and is the document the control plan's training " +
      "block points at -- one method, one source.",
    "It survives the author: the working test is whether someone could do the job from it with the author " +
      "gone.",
  ],
  commonMistakes: [
    "Writing the old process with a patch note -- the improved method must stand as one clean sequence.",
    "Steps written as policy (\"ensure,\" \"manage,\" \"be mindful of\") instead of actions -- nothing " +
      "followable, checkable, or trainable.",
    "Changed steps not marked -- training and auditing both lose their map of what's new.",
    "An SOP that contradicts the implemented change -- the method being trained is not the method that " +
      "was proven, and the sustainment story is void.",
    "Skipping version/owner/date because \"everyone knows\" -- the document is being written precisely " +
      "for the day that stops being true.",
  ],
  source:
    "Method source: standard work / SOP practice per traceability matrix V.C.1 (T-24 as the improved " +
    "method written down; III.A work instructions on the improved state); version/owner fields embody " +
    "VI.B.2 document control; this SOP is the training artifact VI.B.3's block (T-22) references. Golden " +
    "G-stdwork-01. Step schema (action + standard + changed-from-prior) checked by prescore/" +
    "standard_work.py. Acceptance checklist: rubric R-CTL-06.",
};
