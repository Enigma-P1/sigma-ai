# Re-running the supervisor UAT

Everything needed to run the 2026-08-12 test again, against the same two
plans, so the counts in `../PLAN.md` can be compared honestly after each phase
of work.

## What is here

| File | Role |
|---|---|
| `phase1-persona-system.txt` | Holds a model as an uncertified ops supervisor. Used to generate a persona. |
| `phase1-prompt.txt` | Asks for: who you are, the problem you actually have, the data you realistically have, what would make you keep or close the software, and a numbered 10–20 step plan — all **before seeing a screen**. |
| `dave-plan.md`, `mike-plan.md` | The two personas and plans that phase 1 produced, verbatim. Re-run against these to compare with the baseline. |
| `DRIVER-RULES.md` | The rules the driver works under. The important ones: do exactly what the persona said; never use codebase knowledge to find a feature; record facts, not verdicts; an impossible step is a result, not a blocker. |
| `harness.mjs` | Serves the production bundle at the packaged origin, injects the Tauri globals, records video, captions screenshots, writes the transcript. |
| `phase3-persona-system.txt`, `phase3-prompt.txt` | Puts the model back in persona and asks for the write-up from its own screenshots. |
| `phase3.sh` | Builds the material, spreads the screenshots across the whole run, and calls the second-opinion tool. |
| `data/` | The two files the testers "had on their desktop". `ErrorLog_Sept.xlsx` is deliberately awful — two date formats in one column, 8 missing order numbers, 4 blank right-part cells, 5 trailing-space part numbers, one blank row, and the header line pasted a second time at row 46. Do not clean it. |

## Running it

Build the bundle, then start one engine per tester on its own **empty**
projects root — an example project in the store changes the first-run
experience, which is part of what is being measured.

```bash
cd desktop && npm run build

mkdir -p /tmp/uat-roots/{dave,mike}
cd engine
SIGMA_PROJECTS_ROOT=/tmp/uat-roots/dave .venv/bin/python -m sigma_engine.main --port 8801 &
SIGMA_PROJECTS_ROOT=/tmp/uat-roots/mike .venv/bin/python -m sigma_engine.main --port 8802 &
```

Then drive each plan in chunks of a few steps per script:

```js
import { openApp, openProject } from "<path>/harness.mjs";
const app = await openApp({ enginePort: 8801, out: "/tmp/uat/dave", chunk: "01-first-open" });
await app.shot("cold-start", "the very first screen");
app.say(await app.text());        // dump every word, then read it as the user would
app.note("step 1", "what they expected", "what actually happened");
await app.close();                // flushes the video
```

App state lives in the engine, so a later chunk reopens the project and
carries on. `openApp` takes `{enginePort, out, chunk, sitePort, viewport}`.

Finally, hand each model its own run back:

```bash
./phase3.sh /tmp/uat/dave openai <vision-model> dave-report.md 26
./phase3.sh /tmp/uat/mike xai   <vision-model> mike-report.md 26
```

## Two things that will bite

**The engine port is hard-coded in the client.** `resolveEngineBaseUrl()`
returns `127.0.0.1:8756` in the packaged branch, so two testers cannot share
it. The harness patches `window.fetch` to rewrite 8756 to the port the run was
given — still absolute, still cross-origin, still preflighted, only the port
differs. That is the single deviation from the shipped app.

**Pick the models explicitly in phase 3.** The second-opinion tool's auto-pick
excludes vision models, so a run with `--image` and no `--openai-model` /
`--xai-model` will not see the screenshots. Give phase 3 a large
`--max-tokens`: the first attempt at Dave's report came back empty because
reasoning consumed the whole budget before any prose was written.
