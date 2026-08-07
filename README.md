# Sigma AI

AI-guided Six Sigma / Lean application that ingests operational data *and* Voice-of-Customer survey results, and walks a team through a full DMAIC cycle with evidence-grounded artifacts at every gate.

## Status

**Building — milestone 0 (of 7) underway.** The v1 build plan is approved after a three-round external review loop (see [`PLAN.md`](PLAN.md)). Milestone 0's governing documents are landing: the [BoK traceability matrix](docs/traceability-matrix.md) (coverage proven against the pinned ASQ 2022 + IASSC Green Belt bodies of knowledge), the [Green Belt grading rubric](docs/green-belt-rubric.md) (locked 2026-08-07 after a three-round external-model Belt review — per owner ruling no human certified Belt reviews this project, and no claim here implies otherwise), and the frozen [Tier-A definition of done](docs/tier-a-done-means.md). No app code before these existed, by design. This README predates the plan below this line and gets its full rewrite at the final milestone.

## The positioning thesis (to stress-test)

> Stop starting improvement projects from gut feel. Start from what your data and your customers actually said.

A mid-market DMAIC platform whose wedge is **VoC + ops data fused into evidence-backed CTQs and project charters**, with a deterministic stats engine underneath and an LLM coach on top.

## Why this could work

Three disconnected camps exist in the Six Sigma / Lean software market and nothing bridges them:

| Camp | Examples | What they have | What they lack |
|---|---|---|---|
| Stats depth | Minitab, JMP, SigmaXL | Deep statistics | No guidance, no survey side, expensive |
| Workflow/culture | KaiNexus, Rever, Planview | Governance, idea capture | No stats |
| VoC text | Qualtrics, Medallia | Survey analytics | No DMAIC output |
| AI-native DMAIC (new) | DMAIC.app, Praxie, Pearl dmAIc, Visual Paradigm | Guided DMAIC | Thin stats, near-zero survey ingestion |

The clearest whitespace is the **VoC-to-CTQ-to-DMAIC bridge with evidence grounding**. See [`docs/planning/whitespace.md`](docs/planning/whitespace.md).

## What the research says NOT to build

- Don't out-Minitab Minitab.
- Don't build "LLM-as-statistician" — documented failure modes: sycophancy, premature convergence, spurious causal claims.
- Don't build another free AI charter generator — Visual Paradigm commoditized that to $0 in 2025.
- Don't target certified Black Belts — they have Minitab and won't switch.

See [`docs/planning/anti-patterns.md`](docs/planning/anti-patterns.md).

## Repo layout

```
docs/
  research/
    landscape.md            # Commercial landscape — 2024-2026 tools, pricing, gaps
    methodology-frontier.md # Academic + practitioner state of AI-enabled DMAIC
  planning/
    whitespace.md           # Where the opening is
    anti-patterns.md        # What not to build
    open-questions.md       # 5 questions blocking v1 scope
```

## Origin

Surfaced as a spark on 2026-04-21 during a session in the personal-ai vault. Full landscape research captured same day. Awaiting revisit.
