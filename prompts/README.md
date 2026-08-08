# The Sigma AI portable prompt pack

Copy-paste expert prompts for using the Sigma AI method through **any** chatbot --
Claude, ChatGPT, Gemini, whatever you have. No API key, no setup, no account with
anyone in particular. This is the portable form of the app's Layer 2 advisor.

Thirty-one prompts:

- `tools/` -- one expert review prompt per Tier-A tool, `T-01-picker.md` through
  `T-25-a3.md`. Each one puts the chatbot in the role of a Black Belt mentor and hands
  it the exact rubric items the app itself grades that tool against.
- `tollgates/` -- one Champion review prompt per phase exit: `define.md`, `measure.md`,
  `analyze.md`, `improve.md`, `control.md`, `wrap.md`. Each one carries that phase's
  standard tollgate questions and the go / go-with-actions / no-go output frame.

## How to use one

1. Open the prompt file for your tool or gate and paste the **whole file** into the
   chatbot as your first message.
2. The prompt instructs the chatbot to demand your actual work before answering. Paste
   your artifact -- the app's exported JSON, or your fields typed out -- and the
   computed results the app shows for it.
3. Easiest path if you have the app: every tool screen's Advisor panel has an **Export
   for chatbot** button that produces one paste-ready block -- the prompt, your
   artifact's JSON, and the app's computed results, already labeled. One copy, one
   paste, done.
4. Discuss, revise your work, re-export, repeat.

Without the app, the prompts still work: paste whatever records you actually have and
say plainly what you don't. Every prompt instructs the chatbot to review only what is
in front of it and to ask for what's missing rather than assume it.

## What this pack is not (read this once, honestly)

These prompts are the same method as the in-app advisor -- same rubric text, same
tollgate questions, same demand-the-evidence discipline -- with **weaker guarantees**.
Inside the app, artifacts are schema-validated, every statistic is computed by code
with provenance attached, grounding checks flag claims that don't trace to data, and
user text is delimited so it can't be mistaken for instructions. A chatbot chat has
none of that: no schema enforcement, no grounding checks, no injection defense. The
prompts *instruct* the chatbot to behave -- demand data, never invent numbers, never
recompute the app's math -- but an instruction is not an enforcement. Expect the
occasional confident wrong answer, and weigh everything you get accordingly.

## The rule of the pack

If you take one sentence from this page, take this one:

> **Numbers that come back from a chatbot are not authoritative -- the app's computed
> results are the record.**

Use the chat to think, critique, and plan. When any number in a reply disagrees with a
number the app computed, the app's number wins -- copy it back over the chat's version,
never the other way around. A project that keeps two sets of numbers ends up trusting
neither.

---

**What this prompt is, honestly.** This is the portable form of Sigma AI's in-app
advisor: the same method, with weaker guarantees. Outside the app there is no schema
enforcement, no grounding check, and no injection defense -- nothing verifies that the
answer above stayed inside these instructions. And the one rule that prevents a
split-brain project: **numbers that come back from a chatbot are not authoritative --
the app's computed results are the record.** If a number in this chat disagrees with a
number the app computed, the app's number wins.
