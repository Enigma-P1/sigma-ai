# Research Summary — Six Sigma / Lean Software Landscape (2024-2026)

Condensed from two parallel research passes run 2026-04-21: commercial landscape + methodology/academic frontier. Full project context lives in the Personal-AI vault at `context/projects/sigma-ai.md`.

## Market structure

Three disconnected camps, no bridge between them:

| Camp | Examples | Has | Lacks |
|---|---|---|---|
| Stats depth | Minitab, JMP, SigmaXL, QI Macros | Real statistics | Guidance, survey side, affordable pricing |
| Workflow / culture | KaiNexus, Rever, Planview | Governance, idea capture | Stats engine |
| VoC text | Qualtrics, Medallia | Survey analytics | DMAIC output |
| AI-native DMAIC (new) | DMAIC.app, Pearl dmAIc, Praxie, Visual Paradigm (free) | Guided DMAIC | Thin stats, near-zero survey ingestion |

## Pricing gap

Free (Visual Paradigm, ChatGPT prompts) → $300-$1,300 perpetual (QI Macros, SigmaXL) → $1,320-$8,820 / user / year (Minitab, JMP) → custom enterprise (KaiNexus, Qualtrics, Medallia). **A 5-50 person team that wants guided DMAIC + real stats + survey ingestion has no product in 2026.**

## Methodology frontier — what's automated, what isn't

- **Measure & Control are solved** — process mining (Celonis), always-on SPC are commodities.
- **Define, Analyze, Improve are not** — LLMs fail here. Documented failure modes: sycophancy, premature convergence, spurious causal claims, confabulation. LLM-as-statistician hallucinates test choice.
- Every working 2025-2026 academic framework for LLM-powered FMEA / RCA uses **RAG + ontology grounding + human-in-the-loop**. Pure LLM approaches don't clear the reliability bar.

## Adoption barriers (not mostly statistical)

Per SixSigma.us, Invensis, Tandfonline 2025 digitalization study, and WSJ-cited data: >60% of LSS projects fail. Top causes: **middle-manager resistance**, **wrong project selection** (pet project, boil the ocean), **fear-of-failure culture**, training cost. Statistical complexity is a barrier but ranks below all of these.

**Implication:** a differentiated tool must make project selection evidence-driven before kickoff, not just make stats easier.

## Whitespace

1. Fusing raw operational data + open-ended survey text in one pipeline — nobody does this
2. Automated VoC → CTQ tree with confidence scoring — Qualica has a manual editor, Jeda.ai does Kano for PMs, no tool fuses survey text into DMAIC
3. Evidence-grounded fishbone / 5-why — cross-reference AI-generated causes against actual data, rank by statistical support
4. SPC + VoC temporal correlation — "process shifted 0.7σ in week 14; complaint theme spiked the same week"
5. Deterministic stats-tool selector + LLM explainer — rule-based assumption check + LLM as explainer, not statistician

## Positioning thesis (to stress-test)

> Stop starting improvement projects from gut feel. Start from what your data and your customers actually said.

Wedge: VoC + ops data fused into evidence-backed CTQs and charters. Stats engine underneath, LLM coach on top. Priced for mid-market.

## What NOT to build (per research)

- Don't out-Minitab Minitab
- Don't build LLM-as-statistician
- Don't build another free AI charter generator (Visual Paradigm commoditized that in 2025)
- Don't target certified Black Belts (they have Minitab, won't switch)
