# Coffee Bar demo — the primary threaded example

This is the Define, Measure, and Analyze thread of the suite's primary
worked example
(PLAN §4.4): a
campus coffee bar where espresso orders averaged 8.4 minutes from register to
handoff during the weekday 7:00-10:00 peak — continuous data, headed for an
I-MR baseline, capability, and a t-test in later phases. The point of the demo
is continuity: the picker routes the problem to full DMAIC, the charter's
problem statement (8.4 minutes, Q2 2026) becomes CTQ C1 in the VoC tree, C1 is
the charter's primary metric (5.0-minute target, lower is better), the COPQ
worksheet prices the pain at $4,021 for Q2 ($16,084/yr on the charter, basis
stated), and the SIPOC fixes the register-to-handoff boundaries every later
tool must respect. That thread — charter problem → CTQ → metric → baseline →
test — is the method itself. The charter ships twice on purpose:
`charter-flawed.json` is the solution-shaped first draft that trips the
engine's real prescore flags, `charter.json` is the corrected version that
passes clean, and `charter-teaching-note.md` names each flaw and why the fix
matters.

`measure/` continues the same thread with the same numbers: the collection
plan turns C1 into an operational definition (register timestamp to name
call, tenths of a minute, two-people test confirmed), `wait-times.csv` is the
plan executed — 120 orders over 10 mornings, mean 8.408 against the charter's
8.4 — the check sheet's 40 delay tallies Pareto out to drink-queue backlog
plus grinder rework at exactly 80% (engine-verified vital few), the time
study's element medians (0.8 + 4.5 + 2.0 + 0.6 + 0.5 minutes — the sum of
a typical cycle's medians, not the mean total; the eight timed cycles
average 8.8) rebuild the 8.4-minute total and flag the July 28 rush cycle
as the honest outlier, the passing genuine repeat-timing measurement check
(camera-video test/retest, blind to the first pass — repeatability 8.94%,
acceptable, resolution 0.1 min on a 5.1-min span) licenses the capability
language, and the process map and calibrated spaghetti diagram put the
pain on the floor: the espresso
station is the named constraint and the 4.5-minute drink queue in front of
it is that constraint's consequence, not the constraint itself, and the
barista walks ~796 m per peak in the current layout. What the baseline
proves (`measure/baseline-run.md`, run through the live engine): the
process is **stable but not capable** — zero control-chart signals at
n=120, yet every sampled order blew past the customer's 5-minute line,
Cpk −1.14 — so the wait is what this process is built to produce, not a
bad day. That hands Analyze its exact question — which common causes (the
drink queue, the grinder rework) drive the 8.4 minutes — and the
before/after t-test its frozen baseline.

`analyze/` answers that question with evidence, not agreement. The fishbone
(all six branches, eleven causes, engine prescore clean) carries five
**verified** causes, each with its evidence pointer intact: the drink-queue
pileup ahead of the single espresso station (check sheet: 22 of 40 delay
tallies, 55% — the Pareto's biggest vital-few bar) and grinder rework
re-pulls (10 of 40, 25%), plus the 5-Why chain that digs the pileup three
levels down — serial station (the map's engine-named constraint readout as
dated observation), single brew group, and the Improve-ready root: **one
machine head, batch sizes locked to one drink at a time**. Staffing shape
stays honestly *investigating*, music tempo and cup placement stay
*candidates* wearing the no-evidence chip, and register hardware and
measurement clock skew are *ruled out* with their evidence kept on the
board (the register step medians 0.8 min; the T-12 check passed at 8.94%).
The FMEA adds what the fishbone can't rank — discrete failure risk on the
mapped steps: the highest RPN (288) is the drink-queue handoff mix-up,
while the severity-first view leads with a severity-8 steam-scald row at
RPN 48 — the stated RPN limitation on display — and both carry actions
with owners, so no safety row sits unaddressed and no blocking flag fires.
The hypothesis run (`analyze/hypothesis-run.json`, live through
`/stats/hypothesis/run`, declared-primary, Welch t) rules the daypart
question in as real but minor and out as a driver: late mornings run 0.45
min slower than early (p = 0.0165, d = −0.44, CI −0.81 to −0.08), while
even the early window averages 8.18 against the 5.0 promise — the causes
operate all morning, which is the espresso-capacity story again. The
hand-off to Improve is the ranked verified-cause list: (1) drink-queue
pileup / one-head batching root, 55% of tallied delays and 4.5 of the 8.4
minutes; (2) grinder rework, 25% of tallies and ~2 minutes per re-pull —
together the engine-verified 80% vital few, with daypart shuffling
explicitly not on the list. Improve and Control artifacts (and the
proposed-layout spaghetti overlay) arrive with their milestones.
