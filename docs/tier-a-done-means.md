---
type: knowledge
status: frozen-at-m0
tags: [m0, definition-of-done, tier-a]
date: 2026-08-07
---

# Tier A "done means" — the frozen checklist

Frozen at milestone 0 per PLAN §8, so "full polish" can't quietly thin under
schedule pressure. A Tier-A tool counts as **done** only when every item below
checks. This list changes only by a logged decision (vault `decisions/` entry +
a dated note here) — never silently, never per-tool.

Milestone timing: items 1–7 are checked at the milestone that builds the tool
(M1–M4). Item 8 is checked for every Tier-A tool when Layer 2 lands (M5). The
§9 golden-scenario walkthrough re-checks 1–7 for all tools at M6.

## 1. Instruction layer

- [ ] The five-part helper frame (PLAN §4.3) is present and always visible:
  **what this is** (two sentences, plain English) · **when to use it / when
  not to** (including the classic misuse) · **per-field guidance** with one
  good and one bad example per field · **what good looks like** (the
  acceptance checklist) · **common mistakes** (the 3–5 an instructor sees).
- [ ] Every jargon term is defined at first use; no term appears only as jargon.
- [ ] The help panel cites the tool's method source (PLAN §6).

## 2. Rubric wiring

- [ ] Every rubric item the traceability matrix assigns to this tool exists in
  `docs/green-belt-rubric.md` with pass / needs-work criteria.
- [ ] The tool's "what good looks like" panel is drawn from those same rubric
  items — one source of truth, no parallel checklist.
- [ ] The deterministic pre-score checks (the rule-based subset of the rubric)
  run in code and are unit-tested.

## 3. Goldens and stats fidelity

- [ ] At least one golden exists: the tool's output on the demo scenario is
  frozen (matrix `G-…` ID) and diffed in CI on every change.
- [ ] Every computed statistic has a deterministic unit test against a
  NIST/SEMATECH reference value or a published worked example (PLAN §9).
  These tests are the final authority on the math.
- [ ] Formula implementations name their source (e.g. NIST section, published
  constants table) in a code comment at the definition site.

## 4. Decision trees (routed tools only)

- [ ] If the matrix marks the tool as routed (test selector, chart selector,
  stability→capability path, project picker), the decision tree is rendered
  in-app as a visible flowchart.
- [ ] The rendered tree and the code path are generated from, or tested
  against, the same rule table — they cannot drift apart.
- [ ] Every unsupported case the matrix's exit registry assigns to this tool
  is detected and produces its named exit, never a computed-anyway answer.

## 5. Export and provenance

- [ ] The artifact saves as schema-valid JSON (Pydantic model is the source of
  truth) and round-trips: save → load → identical artifact.
- [ ] PDF export renders the artifact completely, and the artifact appears
  correctly in the A3 roll-up.
- [ ] Every computed result is a provenance object (PLAN §4.5): input-data
  hash, method identifier, software version, assumptions checked, warnings.
  Exports carry them. Schema forbids the LLM creating or mutating any
  quantitative field.
- [ ] Artifacts version on edit; prior versions remain loadable.

## 6. Demo threading

- [ ] "Show me the example" works: the Coffee Bar demo project has this tool
  filled in at the right point in its flow (PLAN §4.4).
- [ ] If the tool's attribute-data path differs, the Print Shop demo covers it.
- [ ] If the matrix assigns this tool a flawed-example teaching moment, the
  flawed version + its correction + the why are present.

## 7. Gates

- [ ] Hard math guards specified in PLAN §4.1/§4.2 for this tool are enforced
  in the state machine (e.g. no capability without spec limits; no capability
  claim without passed stability + measurement checks) and unit-tested.
- [ ] Soft sequence gates warn, list what's missing, and accept a required,
  logged override reason. Overrides appear in the project record.
- [ ] A failed upstream check (e.g. failed measurement system) degrades this
  tool's language downstream exactly as the plan specifies — verified by test.

## 8. Advisor hooks (checked at M5, not at the tool's build milestone)

- [ ] "Review my artifact" grades against this tool's rubric items and returns
  structured pass / needs-work per criterion.
- [ ] The tool's artifact JSON + computed stats + pre-score assemble into the
  advisor context within the PLAN §5.1 token budget.
- [ ] The prompt pack contains this tool's portable prompt, with rubric
  embedded and the numbers-are-not-authoritative banner.

## What "done" is NOT

"It renders" is not done. "The happy path works" is not done. A tool with
helper text but no golden, a chart with no verdict headline, a selector whose
tree exists only in code, an export with no provenance — each is the exact
thinning this checklist exists to block. If an item genuinely cannot apply to
a tool, the matrix says so explicitly per tool; silence is not an exemption.
