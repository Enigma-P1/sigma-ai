# Second opinion — 2026-08-13

**Intent:** Release-readiness review. Read the dossier at the top of the material — it defines the question (READY / READY-WITH-FIXES / NOT-READY for a public free v0.2), the evidence rules, and the four things wanted from you. The screenshots attached are the CURRENT build after the fixes; the appendices describe the state BEFORE the fixes, so judge direction of travel from the difference. Be adversarial: your value here is finding the hole we are too close to see, including anything we appear to have over-claimed.
**Mode:** answer · **Material:** 133833 chars

---

## openai · `gpt-5.6-luna`
*tokens: 51979 in / 2065 out*

**Verdict: NOT-READY.**

### Ship-blockers, ranked

1. **No installer build from the release candidate — day-one blocker.**  
   The current code has not been exercised as a Windows/macOS installer, despite the previous v0.1.1 sidecar launch failure. The packaged-origin probes do not prove installed-app startup, sidecar discovery, permissions, upgrades, project paths, or export/download behavior. Shipping now risks an app that passes CI and screenshots but does not launch for users.

2. **No independent fresh-eyes UAT on the fixed build — day-one usability blocker.**  
   The scripted scorecard proves controls exist and can be driven by a knowledgeable harness. It does not prove an untrained supervisor can find the front door, interpret the new data workflow, complete edits/recode/derived columns, filter charts, recover drafts, or produce the summary. The original evidence showed severe discoverability failures; those cannot be considered closed by replaying the same blocked steps.

3. **Security boundary is not acceptable without an explicit threat decision — scale/security blocker.**  
   The advisor key is stored plaintext, and the sidecar is an unauthenticated HTTP service on localhost. A local process can potentially call the engine while the app is running, and anyone with filesystem access can retrieve the advisor key. The localhost binding limits remote exposure, but it is not authentication or authorization. At minimum, use the OS credential store for keys and authenticate/authorize sidecar requests, or clearly document and accept the local-machine threat model before release.

4. **The manager-output claim is not yet evidenced — day-one credibility risk.**  
   “A one-page summary exists” is not equivalent to “the user leaves with a useful manager artifact.” The supplied current screenshots show import, rows, filtering, draft restoration, glossary, and deletion, but not the summary contents or its export. The summary reportedly names its gaps; that may be honest, but it may still be an empty form with a title. Verify it end-to-end from a real user flow and inspect the resulting PDF.

5. **Release-level data correctness needs a current-build acceptance test — potential day-one embarrassment.**  
   The old UAT demonstrated silent or misleading failure modes: dropped blank-category rows, repeated headers treated as data, duplicate people counted separately, malformed date axes, and unusable exported charts. The new screenshots show substantial improvement, including visible rows, totals, recoding, warnings, and categorical Pareto labels. However, the evidence does not show the complete current-build Mike scenario, nor does it prove the resulting charts and exports preserve labels and exclusions correctly.

### What I would explicitly **not** block on

- Paste-to-table, provided CSV/XLSX import and typed row entry are reliable.
- Fishbone high/medium/low priority, provided the distinction from evidence status is documented.
- Undo, because immutable dataset versions and lineage substantially reduce provenance risk; provide clear deletion warnings.
- Letter/A4 selection for v0.2.
- Correlation/regression, if the deferral is prominent and the scatter plot does not imply computed correlation.
- Optional LLM advisor functionality, since the app works without it—though its key storage still needs fixing.
- Full integration of every DMAIC tool into the A3, if the one-page summary is genuinely useful and accurately labels missing information.

### Apparent over-claims or misreads

- **“Eight of ten blocked items now work” overstates the evidence.** It means scripted replays found controls, not that users completed the workflows successfully. One Dave step remains impossible and one partial; no fresh-eyes run exists.
- **“The chart remembers its selections” is not demonstrated by the supplied material.** The screenshots show a selected subset and row count, but not persistence through navigation or restart. The old UAT explicitly showed chart selections being lost.
- **“Quality scan catches a repeated header row” is only partially evidenced.** The current screenshots visibly show duplicate-name and mixed-date findings, but not the repeated-header finding in the current build or the complete Mike file.
- **“One-page summary exists” is weaker than the dossier’s implied manager-readiness.** Existence alone does not establish useful seeded content, correct figures, or a printable export.
- **“23 tools export designed PDF reports” does not establish that the project export captures the actual analysis.** The previous UAT showed charts omitted from project/phase exports and “Chart not captured.” No current-build export evidence closes that gap.
- **The test gates establish regression confidence, not release confidence.** Passing pytest, golden replay, TypeScript, bundle, and packaged-origin probes does not cover installers, discoverability, hostile local processes, or real-user success.

The direction of travel is clearly good, and the fixes appear meaningful. I would move this to **READY-WITH-FIXES** after installer tests, independent UAT, security remediation or explicit risk acceptance, and an inspected end-to-end summary/export run.

---

## xai · `grok-4.6`
*tokens: 49936 in / 901 out*

**READY-WITH-FIXES**

Direction of travel is real: rows, totals ($671.15), recode, derive, drafts, filter-with-count, categorical on-screen Pareto, glossary, delete-confirm, and a data-first stuck-tree all exist in the current screenshots. That is not enough to ship *as-is*.

### Ship-blockers (ranked)

1. **No installer build from this code.** Day-one. v0.1.1 already failed on sidecar launch. A public “desktop v0.2” that nobody can double-click — or that dies on first open — is the release. Do not tag/publish until Windows and macOS installers are built and a cold-start smoke (launch, create project, import, one chart) passes on both.

2. **Chart image export may still be the 20k–80k Plotly PNG.** Day-one. Screenshot 8 is a correct categorical Pareto; screenshot 9 is the exact broken export Mike would email. Dossier claims “part numbers no longer plot as 20k–80k.” If 9 is current, that claim is false and the one artifact a supervisor shares is still wrong. Confirm the download, not just the on-screen chart. (Phase 2.2, the chart-screen report, is also missing from the landed list — 2.1/2.3/2.4/2.5 shipped; 2.2 quietly didn’t.)

3. **Do not ship the UAT-fix narrative you wrote.** Day-one reputation. The scorecard proves prior blocked *controls* exist. It does not prove a new supervisor succeeds. Every in-app screenshot still lands on T-01, still shows “Needs earlier steps (can override),” still hides import under T-11 “Data Collection Plan.” Release notes that say supervisors can now run a project will be falsified by anyone replaying Dave/Mike without clicking “I’m stuck.”

I cannot tell from this packet whether the one-page summary is actually a manager artifact or a gaps-named empty sheet — there is no screenshot of it filled. If the scorecard only checked “page exists,” treat that as unverified, not done.

### Do not block on

Paste-from-clipboard; fishbone high/medium/low (rightly deferred); undo; Letter/A4; EXIT-15 corr/regression; plaintext advisor key (already disclosed); 127.0.0.1 engine *as a design* (disclose it); remaining DMAIC banners; Aisle still inferred numeric; no fresh-eyes UAT *if you do not claim one*; single-maintainer process. Those are v0.3, not reasons to sit on a free point release.

### UAT misread / over-claim

- **“Front door” is over-claimed.** Decision 1 was keep the gate *and* let import+chart not pass through it. What shipped is a help-panel detour. Create still opens the five-question T-01 quiz. Mike’s #4 ask (strip the banners/gate from the tools he uses) was not done and is written up as if the spine exists.
- **“Something to show a manager: exists”** equates page-existence with the thing neither tester left with. Not shown. A3 seeding is claimed in a commit list, not evidenced.
- **Scorecard ≠ re-UAT.** You stated this, then used the counts as the readiness argument anyway. 4→1 / 2→0 is “we built the buttons,” not “a supervisor would now leave with a page.”
- **Pareto-axis claim vs screenshot 9.** Reconcile before you write it in the changelog.
- **Phase 1 exit was rewritten after the fact.** Own plan: Dave 7 (paste) was supposed to go impossible→done. It didn’t; it was reclassified partial. Honest in the “what did not move” note, not in the headline “eight of ten now work” if paste was one of the ten.
- Dave/Mike’s actual verdicts were about *trust and a path*, not missing widgets. You built the widgets. The 26-tool wall is intact. Do not tell the public you answered the UAT.

