# Getting v0.2 over the line

Three reviewers judged release readiness on 2026-08-13: GPT (gpt-5.6-luna)
said **NOT-READY**, Grok (grok-4.6) said **READY-WITH-FIXES**, and a
same-day security pass found two holes. The disagreement between the two
external verdicts is smaller than it looks — they named almost the same
blockers and almost the same don't-block list. This document is the merge:
what was fixed the same day, what actually gates the release, in what
order, and what we will not let block a free point release.

Full verdicts: `docs/uat/ship-review-verdicts.md`. UAT evidence:
`docs/uat/`.

## Fixed the same day (already on main)

| Finding | Who raised it | Status |
|---|---|---|
| Any website could drive the engine while the app ran — CORS `*` + private-network allowance meant evil.com could read the project list and call DELETE. CSRF on loopback. | security pass | **Fixed** — Origin allowlist inside the CORS layer; evil.com 403, suffix tricks 403, app origin and no-Origin callers unaffected. Live-verified + 15 tests. |
| Dataset and image ids escaped the project folder (`datasets/../../…` reached `/tmp`) | security pass | **Fixed** — same `safe_segment` guard as project ids; confirmed live before and after. |
| The data-first front door was "a help-panel detour, not a door" — Create still landed on the T-01 quiz, T-11/T-14 still wore the gate banner | Grok #3 / over-claim list | **Fixed** — a plain line with navigation sits above the quiz; T-11/T-14 are ungated (verified 0/0/1 banners against T-03). The gate still stands on every artifact-writing tool, tollgate and pack. |
| Phase 2.2 (chart export) silently never shipped | Grok #2 | **Fixed** — labelled "Download this chart as a picture" on the Pareto, real filename, verified live. |
| "The downloaded PNG may still be the 20k–80k mess" | Grok #2 | **Checked, false** — driven end to end on Mike's file; the download is categorical and correct. The packet's confusing image was the uncaptioned *before* shot. |
| No stated threat model; plaintext advisor key unaddressed | GPT #3 | **Partly fixed** — `SECURITY.md` states the local threat model and the key's storage plainly. Keychain storage is v0.3 (below). |

## Second-pass review — 2026-08-13, after the same-day fixes

Both reviewers looked again at the fixed build (`docs/uat/ship-rereview-verdicts.md`).
Both still say **NOT-READY**, and both moved for the same reason: the
engineering moved, the release promise did not. Grok: *"Moved as
engineering, not as a public release."*

They converge on one surface. **The one-page summary is the
release-critical artifact, and as it stands it is a populated form rather
than something a supervisor would hand a manager.** Grok, on the filled
page: *"a user can now reach a one-pager that is worse than empty — it is
sendable-looking and wrong. Empty would have been embarrassing. This would
get someone dressed down."* GPT independently: *"not yet the polished,
decision-ready artifact a real supervisor would confidently use to brief
their boss."*

That is a consequence of our own front-door work — an ungated import path
now leads somewhere that concatenates whatever is on file. It is therefore
ours, and it is **Gate 0**: it precedes the installer, because there is no
point paying for a build of a page we already know does not hold up.

What they said is wrong with it, and what is being fixed:

| Finding | Fix |
|---|---|
| The Pareto is not on the page — *"a one-pager without the Pareto is a cover sheet"* | The chart goes on it, through the same fingerprinted capture the tool reports use |
| 487 errors / 10 rows / 3 tallies, three denominators presented as one story | Every count names what it counts and over what; where the page cannot reconcile two scopes it says so, rather than presenting a tidy lie |
| Tool residue in the body — *"3 tally mark(s) across 2 categories with at least one"*, artifact ids, hashes | Body reads like a supervisor wrote it; ids and hashes stay in the provenance footer, which both reviewers said is fine |
| One of four causes shown with no explanation | Labelled: verified cause shown, N others still unproven |
| No owner, no date, no ask | The charter carries both; the next step becomes actionable, still under "not a computed result" |
| Problem line truncates mid-sentence — *"the page already gave up on being complete"* | Clip at a sentence boundary or fit it |

Also confirmed by the second pass: the chart PNG fix is **letter and
spirit** done (*"C is categorical, labelled axes, cumulative line, real
part numbers"*), the security fixes are accepted on our live verification,
and the do-not-block list is unchanged. The door fix is letter-done and
spirit-half-done — landing is still the T-01 quiz — which stays a v0.3
item unless the fresh-eyes UAT says otherwise.

## What still gates the release, in order

### Gate 0 — The summary becomes a manager artifact
Both reviewers' remaining product blocker, above. Done when a driven run
produces a page that survives the question "would a supervisor put this on
a table in an ops meeting" — not "are the fields filled."

### Gate 1 — Installers built from this code, and a cold-start smoke on both OSes
Both reviewers' #1, and ours. v0.1.1's sidecar failed on installed Windows
after every local check was green; installers find their own bugs.
- Tag a release candidate; CI builds Windows + macOS installers.
  **This costs real money and Shawn triggers it** — nothing else in this
  plan spends anything.
- Cold-start smoke on each OS: install → launch → create project → import
  `ErrorLog_Sept.xlsx` → Pareto → download the chart → one-page summary →
  quit → relaunch → project still there. Twenty minutes per OS, by hand.
- Any failure loops back here. Nothing below proceeds on a red installer.

### Gate 2 — Fresh-eyes UAT on the release candidate
Both reviewers, correctly: the scorecard proved the controls exist, not
that a new user succeeds. And the counts in PLAN.md must never be quoted
as user success — they are "we built the buttons."
- Re-run `docs/uat/method/` with **new personas** (new scenarios, new
  data files — the old ones are burned; a driver who has seen the fixed
  build cannot un-know the paths).
- Pass bar, decided now so it can't drift later: both personas import
  their own file, fix at least one data problem, produce a chart they can
  read, and **leave with the one-page summary** — with no step recorded
  impossible in their first hour. Discoverability counts: finding import
  without the help panel is part of the test, and the new T-01 door is
  what's being tested.
- Fail → fix → re-run. The method is cheap; embarrassment is not.

### Gate 3 — Release evidence and honest release notes
GPT's credibility point: "a one-page summary exists" is weaker than
"users leave with a manager artifact," and we never showed a filled one.
- Attach to the release: a populated one-page summary PDF, an
  empty-project summary (showing the gaps named), the downloaded chart
  PNG, and the before/after Pareto pair — captioned this time.
- Release-notes language rules (from Grok's over-claim list, adopted):
  say what was built and what the fresh-eyes UAT showed, with its date.
  Do **not** say the UAT was "answered," do not quote 8-of-10 as user
  success, do not claim the 26-tool wall is solved. "Two supervisors'
  biggest blockers from the 2026-08-12 test now have working controls;
  a fresh test on this build showed X" — where X is whatever Gate 2
  actually showed.
- README refreshed to match the app as it is (first-screen wording,
  glossary, security section links).

### Gate 4 — Tag, publish, watch
- Version bump to 0.2.0, changelog from the commit log.
- Publish installers + notes.
- First-week watch: issues triaged daily; the UAT method rerun against
  anything a real user reports that smells like the old findings.

## Explicitly not blocking v0.2 (both reviewers agree)

Paste-rows-from-clipboard · fishbone high/medium/low priority (a real
design question, not a reflex) · undo (immutable dataset lineage covers
the data; deletion has a typed confirmation) · Letter/A4 choice ·
correlation/regression (EXIT-15 says so on screen) · the remaining DMAIC
banners on artifact-writing tools (that gate is the product's spine) ·
plaintext advisor key (disclosed in-app and in SECURITY.md) · the
localhost engine as a design (documented) · single-maintainer process.

## v0.3 seeds (from the reviews, not re-litigated here)

Advisor key into the OS credential store · paste target on import ·
chart downloads for the other four chart types · project-level undo or
trash · the A3/summary evidence surfaced in-app · Letter/A4.

## Who does what

| Step | Owner |
|---|---|
| Trigger the CI installer builds (spends money) | **Shawn** |
| Cold-start smoke on Windows/macOS | Shawn (hands on real machines) |
| Fresh-eyes UAT run + report | Claude, method in `docs/uat/method/` |
| Fixes from either gate | Claude |
| Release notes draft under the language rules | Claude, Shawn approves |
| Tag + publish | Shawn |
