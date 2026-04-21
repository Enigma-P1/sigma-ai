# Sigma AI

AI-guided Six Sigma / Lean application that ingests operational data *and* Voice-of-Customer survey results, and walks a team through a full DMAIC cycle with evidence-grounded artifacts at every gate.

## Status

**Spark.** Research done. Scope not defined. Parked pending answers to five open questions (see [`docs/planning/open-questions.md`](docs/planning/open-questions.md)).

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
