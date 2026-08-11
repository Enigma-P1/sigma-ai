"""Every named statistical constant the stats-core modules use, in one
place, each cited at its definition (Hard rule: "no magic numbers in
formulas"). All URLs fetched live 2026-08-07 unless noted; raw fetched
HTML is not committed, only the transcribed numbers below, each
cross-checked against a worked example in the corresponding test module.
"""

from __future__ import annotations

# --- I-MR control chart constants (imr.py, capability.py) -----------------
# NIST/SEMATECH e-Handbook of Statistical Methods, Shewhart control chart
# constants table (subgroup size n=2 row), given in two places that agree:
# §6.3.2.1 "Shewhart X-bar and R and S Control Charts" (the A2/D3/D4 table)
#   https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc321.htm
# §6.3.2.2 "Individuals Control Charts" (d2=1.128 stated directly, used in
#   the worked flow-rate example reference-tested in test_stats_imr.py)
#   https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc322.htm
# A moving range of 2 consecutive individuals is treated as a subgroup of
# size 2, so the same n=2 table row supplies d2 (bias-correction factor,
# individuals-chart limits) and D3/D4 (moving-range-chart limits).
D2_CONSTANT_N2 = 1.128
D3_CONSTANT_N2 = 0.0
D4_CONSTANT_N2 = 3.267

# 3-sigma is the historical, near-universal industry default (NIST
# §6.3.2: "k=3 has become an accepted standard in industry").
CONTROL_CHART_SIGMA_MULTIPLIER = 3.0

# --- Western Electric (WECO) rules (imr.py) --------------------------------
# NIST/SEMATECH §6.3.2 "What are Variables Control Charts?", section "What
# are the WECO rules for signaling Out of Control?":
#   https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc32.htm
# Rule numbering below matches docs/traceability-matrix.md §VI.A.1/§4a:
# rule 1 + rule 4 are the frozen default; rules 2-3 are opt-in (running all
# four drops in-control ARL from ~371 to ~91.75 per NIST's own citation of
# Champ and Woodall 1987 -- a ~4x false-alarm increase).
WE_RULE1_SIGMA = 3.0          # rule 1: any point beyond +/-3 sigma
WE_RULE2_ZONE_SIGMA = 2.0     # rule 2: 2 of last 3 points beyond +/-2 sigma (same side)
WE_RULE2_COUNT, WE_RULE2_WINDOW = 2, 3
WE_RULE3_ZONE_SIGMA = 1.0     # rule 3: 4 of last 5 points beyond +/-1 sigma (same side)
WE_RULE3_COUNT, WE_RULE3_WINDOW = 4, 5
WE_RULE4_RUN_LENGTH = 8       # rule 4: 8 consecutive points on one side of center

# --- Supplementary run tests (rules 5-8) -------------------------------------
# Western Electric defines FOUR rules; these four are the standard
# supplementary tests, published by Lloyd Nelson (Journal of Quality
# Technology, 1984) and carried by every SPC package since. Nelson numbers
# his set 1-8 in a different order from WECO's, so the ids here continue THIS
# module's sequence rather than claiming Nelson's numbering -- see imr.py's
# docstring. All four are opt-in for the same reason rules 2 and 3 are: each
# additional test shortens the in-control ARL and multiplies false alarms.
WE_RULE5_TREND_LENGTH = 6      # rule 5: 6 points steadily increasing or decreasing
WE_RULE6_HUG_LENGTH = 15       # rule 6: 15 points within 1 sigma of center (either side)
WE_RULE6_ZONE_SIGMA = 1.0
WE_RULE7_ALTERNATING_LENGTH = 14  # rule 7: 14 points alternating up and down
WE_RULE8_MIXTURE_LENGTH = 8    # rule 8: 8 points on both sides, none within 1 sigma
WE_RULE8_ZONE_SIGMA = 1.0

# Companion floor for trusting/freezing limits (docs/traceability-matrix.md
# §4a, EXIT-04 row): a window used to set or freeze control limits needs at
# least this many points AND no default-rule signal within it. Below this,
# the chart runs diagnostically only -- no stability or capability claim.
EXIT04_MIN_POINTS_TO_FREEZE_LIMITS = 20

# --- Process capability (capability.py) ------------------------------------
# NIST/SEMATECH §6.1.6 "What is Process Capability?":
#   https://www.itl.nist.gov/div898/handbook/pmc/section1/pmc16.htm
# Quoted directly: "Most capability indices estimates are valid only if the
# sample size used is 'large enough'. Large enough is generally thought to
# be about 50 independent data values" and "we need n >= 100 for capability
# studies" (in the confidence-limits discussion). These are advisory floors
# (attached as provenance warnings), not hard gates -- PLAN §4.2 draws hard
# gates only at "no capability without spec limits" and "no capability
# claim without a stability check."
CAPABILITY_ADVISORY_MIN_N = 50
CAPABILITY_STUDY_RECOMMENDED_MIN_N = 100

# Cp/Cpk/Pp/Ppk's "3 sigma" / "6 sigma" are the same three-sigma industry
# convention as CONTROL_CHART_SIGMA_MULTIPLIER above (NIST §6.1.6: process
# "width" is "6 process standard deviation units"; Cpu/Cpl are the
# one-sided half of that, 3 sigma) -- reused rather than a second literal
# "3"/"6" in capability.py, so the two conventions can't silently drift.
CAPABILITY_ONE_SIDED_SIGMA_MULTIPLIER = CONTROL_CHART_SIGMA_MULTIPLIER  # 3.0
CAPABILITY_TWO_SIDED_SIGMA_MULTIPLIER = 2 * CONTROL_CHART_SIGMA_MULTIPLIER  # 6.0

# --- Normality advisory (normality.py) -------------------------------------
# Anderson-Darling test: NIST/SEMATECH §1.3.5.14 "Anderson-Darling Test"
#   https://www.itl.nist.gov/div898/handbook/eda/section3/eda35e.htm
# Concern threshold p<0.05 is frozen in docs/traceability-matrix.md §4a,
# EXIT-05 row ("Anderson-Darling p < 0.05, n-aware framing"). The n<15
# too-few-to-judge floor is this M2 brief's own frozen threshold for T-13's
# per-sample advisory -- deliberately distinct from EXIT-14's n<20 floor
# (matrix §4a), which gates a *different* decision (T-17's 3+ group
# nonparametric-route selection, not T-13's single-sample AD advisory).
NORMALITY_CONCERN_ALPHA = 0.05
MIN_N_FOR_NORMALITY_JUDGMENT = 15
# Below this, scipy's variance estimate degenerates (ddof=1); guard so we
# never hand scipy a sample it can't compute on rather than silently NaN.
MIN_N_FOR_ANDERSON_DARLING_STATISTIC = 3

# --- Sigma level / DPMO shift convention (sigma_level.py) ------------------
# The 1.5-sigma shift is industry convention (Motorola/Mikel Harry), not a
# NIST quantity. Cross-checked against two independently published tables,
# both fetched live 2026-08-07 (see test_stats_sigma_level.py):
#   Wikipedia "Six Sigma", section "Sigma levels" (states the formula
#   DPMO = 1,000,000 x (1 - Phi(level - 1.5)) explicitly):
#     https://en.wikipedia.org/wiki/Six_Sigma
#   MoreSteam.com "Six Sigma Conversion Table":
#     https://www.moresteam.com/toolbox/six-sigma-conversion-table
# Frozen default in docs/traceability-matrix.md §4a / III.F.4: shift
# applied by default, and the number never travels without its label.
SIGMA_SHIFT_DEFAULT = 1.5
CONVENTION_WITH_SHIFT = "with 1.5σ shift"
CONVENTION_WITHOUT_SHIFT = "without shift"

# --- Pareto vital-few line (pareto.py) -------------------------------------
# Standard Pareto / Six Sigma "80/20" cumulative-share convention (not a
# NIST quantity) -- PLAN §4.1 T-14 row: "vital-few bars highlighted to the
# 80% line."
PARETO_VITAL_FEW_CUMULATIVE_SHARE = 0.8

# --- EXIT-05 non-normal capability path (baseline.py) ----------------------
# Frozen exactly in docs/traceability-matrix.md §4a, EXIT-05 row: empirical
# percentiles at the +/-3-sigma-equivalent normal coverage points, used
# only at n >= 100; below 100 no percentile indices are reported.
EXIT05_MIN_N_FOR_PERCENTILE_CAPABILITY = 100
PERCENTILE_UPPER = 99.865
PERCENTILE_LOWER = 0.135
PERCENTILE_MEDIAN = 50.0

# --- T-12 Measurement Check / MSA (msa.py) ----------------------------------
# Every number below is frozen in docs/traceability-matrix.md §4a, EXIT-02
# rows (continuous + attribute) -- not this milestone's to choose.

# Resolution pre-check (continuous, run before any repeatability math):
# gauge increment must be <= 1/10 of the span it must resolve, AND the
# readings must show >=5 distinct values -- either failure is automatic
# fail ("the gauge can't see the process").
MSA_RESOLUTION_MAX_INCREMENT_FRACTION_OF_SPAN = 0.10
MSA_RESOLUTION_MIN_DISTINCT_VALUES = 5

# Sample guidance (matrix §4a: "≥10 items spanning the observed range,
# near-limit items when specs exist"; ">=2 repeat readings per item") --
# advisory/prescore-flagged (PLAN §4.2 soft/hard split), not a hard gate:
# a study can run smaller, it just says so honestly.
MSA_MIN_ITEMS_GUIDANCE = 10
MSA_MIN_REPEATS_PER_ITEM = 2

# Repeatability% (a.k.a. "%EV," renamed "repeatability%" at Belt-panel
# round 2 -- matrix III.E): %EV = 6*s_repeat / denominator * 100.
MSA_REPEATABILITY_EV_SIGMA_MULTIPLIER = 6.0
# Bands are exclusive-exhaustive (matrix §4a, round-3 lock fix): <=10
# acceptable; >10 and <=30 marginal; >30 fail. Golden-pinned at exactly
# 10.0 (acceptable) and exactly 30.0 (marginal).
MSA_REPEATABILITY_ACCEPTABLE_MAX_PERCENT = 10.0
MSA_REPEATABILITY_MARGINAL_MAX_PERCENT = 30.0

# Two-rater Cohen's kappa bands (matrix §4a, round-3 lock fix, also
# exclusive-exhaustive): >=0.75 acceptable; >=0.40 and <0.75 marginal;
# <0.40 fail. Golden-pinned at exactly kappa=0.75 (acceptable).
MSA_KAPPA_ACCEPTABLE_MIN = 0.75
MSA_KAPPA_MARGINAL_MIN = 0.40

# Belt-panel note, printed on every continuous verdict (matrix §4a / rubric
# R-MEA-07 Pass #1): the 10%/30% bands are borrowed from full-gauge-study
# convention, so passing them on repeatability alone is the lenient side.
MSA_REPEATABILITY_ONLY_CAVEAT = (
    "Repeatability-only: a full multi-operator gauge study was not done here. "
    "The 10% / 30% bands above are borrowed from full-gauge-study convention, "
    "so passing them on repeatability alone is the lenient side -- a full "
    "study could only read worse, not better."
)

# --- T-11 sample-size guidance (sample_size.py) -----------------------------
# I-MR baseline rule of thumb: convention, not a derived law (task brief) --
# loosely anchored above this engine's own EXIT-04 floor for freezing
# control limits (matrix §4a: >=20 points, imported from baseline's
# constants below by the module, not re-declared) with headroom for a few
# points to be excludable as special causes and still clear that floor.
IMR_BASELINE_MIN_N_CONVENTION = 25
IMR_BASELINE_RECOMMENDED_N_CONVENTION = 30

# Margin-of-error calculators (means, proportions): NIST/SEMATECH §7.2.1
# (CI for a mean) and §7.2.4/§7.2.4.2 (CI for a proportion), each solved
# for n. Default confidence level when the caller doesn't state one.
#   https://www.itl.nist.gov/div898/handbook/prc/section2/prc221.htm
#   https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm
SAMPLE_SIZE_DEFAULT_CONFIDENCE_LEVEL = 0.95

# --- T-09 Guided Time Study / Work Sampling (artifacts/time_study.py) ------
# Outlier fence: NIST/SEMATECH e-Handbook §7.1.6 "What are outliers in the
# data?" -- "A point beyond an inner fence on either side is considered a
# mild outlier," inner fences = Q1 - 1.5*IQR / Q3 + 1.5*IQR (same 1.5xIQR
# convention as Tukey (1977), Exploratory Data Analysis, the origin of the
# boxplot whisker rule):
#   https://www.itl.nist.gov/div898/handbook/prc/section1/prc16.htm
# Verified live 2026-08-08. Outliers found this way are flagged, never
# dropped from the descriptive stats (rubric R-MEA-04: "never silently
# deleted") -- see artifacts/time_study.py's compute_element_stats.
TIME_STUDY_IQR_FENCE_MULTIPLIER = 1.5

# Cycle-count guidance floor -- advisory (prescore flag), never a hard
# block (PLAN §4.2's soft/hard split; a study can run smaller, it just
# names the shortfall, matching rubric R-MEA-04's own worked example: "6
# cycles; tool recommends 10 -- treat spread as rough").
TIME_STUDY_MIN_CYCLES_GUIDANCE = 10

# --- T-17 Hypothesis Testing selector (hypothesis_*.py) ---------------------
# Every frozen number below is docs/traceability-matrix.md §4a's Named-exit
# registry (EXIT-06..15) -- nothing in hypothesis_*.py chooses its own
# thresholds, same discipline as the MSA_* block above.
#
# DOC CONFLICT FLAGGED (see this milestone's final report): this build
# brief's own prose paraphrased EXIT-06 as "Welch/1-sample t n>=5 per
# sample; paired t >=6 pairs" and EXIT-09 as "|r1| ... AND >=0.5". Both are
# the PRE-Belt-panel-round-2 numbers. §4a states plainly that both were
# revised -- "(both raised from 5/6 at Belt-panel round 2 -- n=5 invites
# garbage-as-proof)" for EXIT-06, "(lowered from 0.5 at Belt-panel round 2:
# moderate dependence already distorts I-MR limits and test error rates)"
# for EXIT-09 -- and the matrix is marked LOCKED, dated the same day as
# this brief. Per this brief's own "Read first (binding)" instruction, the
# matrix is the frozen, most-recently-corrected source, so the CURRENT
# §4a values ship below (n>=8, pairs>=8, |r1|>=0.3) -- not the brief's
# paraphrase of the pre-correction numbers.

# EXIT-06: refuse-to-compute floors, per route (§4a EXIT-06 row) -- gates
# only, explicitly NOT a powered-study guarantee (§4a's own parenthetical:
# power/adequacy are R-MEA-05's sample-size guidance and R-ANA-05's
# effect-size/CI discipline, not this floor).
HYP_MIN_N_WELCH_T = 8               # Welch two-sample t, per sample
HYP_MIN_N_ONE_SAMPLE_T = 8          # one-sample t vs target
HYP_MIN_PAIRS_PAIRED_T = 8          # paired t, pairs
HYP_MIN_GROUPS_ANOVA = 3
HYP_MIN_N_PER_GROUP_ANOVA = 4
HYP_PROPORTION_MIN_N_PHAT = 5.0     # n*phat >= 5 AND n*(1-phat) >= 5, per sample
HYP_MIN_N_PER_GROUP_MANN_WHITNEY = 4
HYP_MIN_NONZERO_DIFFS_WILCOXON = 6  # both the paired route and the one-sample-vs-target route

# EXIT-07: chi-square sparse-cell rule (Cochran's rule).
CHI_SQUARE_COCHRAN_MIN_EXPECTED = 5.0
CHI_SQUARE_COCHRAN_MIN_CELL_FRACTION = 0.80   # >=80% of cells must clear the floor above
CHI_SQUARE_COCHRAN_ABSOLUTE_FLOOR = 1.0        # AND no cell below this, at all

# EXIT-09: lag-1 autocorrelation, both significant AND material (§4a).
# NIST/SEMATECH §1.3.3.1 "Autocorrelation Plot" gives both the r_h formula
# and the +/-2/sqrt(N) large-lag confidence band this significance test
# reuses: https://www.itl.nist.gov/div898/handbook/eda/section3/eda331.htm
HYP_AUTOCORR_SIGNIFICANCE_NUMERATOR = 2.0      # |r1| > this / sqrt(n)
HYP_AUTOCORR_MATERIAL_MIN_ABS_R1 = 0.3          # AND |r1| >= this (lowered from 0.5, Belt-panel round 2)

# EXIT-12: multiplicity -- one pre-declared primary comparison.
HYP_MAX_PRIMARY_COMPARISONS = 1

# EXIT-13 / EXIT-14 / significance level, frozen throughout (§4a preamble:
# "Default significance level throughout: alpha = 0.05, two-sided").
HYP_ALPHA_TWO_SIDED = 0.05
HYP_CI_CONFIDENCE_LEVEL = 1.0 - HYP_ALPHA_TWO_SIDED  # 0.95 -- ties every CI in this module to the same alpha
HYP_SWITCH_MAX_GROUP_N = 15                     # per-group n < this considers the rank-route switch (PLAN §4.1)
HYP_EXIT14_MAX_GROUP_N_FOR_NORMALITY_CONCERN = 20  # matrix §4a EXIT-14 row; deliberately != HYP_SWITCH_MAX_GROUP_N
# and deliberately != normality.py's own MIN_N_FOR_NORMALITY_JUDGMENT (15)
# -- see hypothesis_common.py's advisory_normality_concern() docstring for
# why T-17 runs its own AD-based check instead of reusing assess_normality.

# --- Effect-size interpretation bands (hypothesis_common.py) ---------------
# Magnitude-in-words only -- never a gate, never a computed threshold.
# Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences
# (2nd ed.). Lawrence Erlbaum -- conventional small/medium/large benchmarks
# for d, eta-squared, and r (Cohen's own guidance: "there is a certain risk
# in offering conventional operational definitions for these terms," used
# here only to put an approximate word on a number, never to gate output).
COHEN_D_SMALL, COHEN_D_MEDIUM, COHEN_D_LARGE = 0.2, 0.5, 0.8
COHEN_ETA2_SMALL, COHEN_ETA2_MEDIUM, COHEN_ETA2_LARGE = 0.01, 0.06, 0.14
COHEN_R_SMALL, COHEN_R_MEDIUM, COHEN_R_LARGE = 0.1, 0.3, 0.5
# Cramer's V generic bands (1-df-style rule of thumb, distinct table from
# Cohen's r above): Rea, L.M., & Parker, R.A. (1992). Designing and
# Conducting Survey Research. Jossey-Bass.
CRAMERS_V_WEAK, CRAMERS_V_MODERATE, CRAMERS_V_STRONG = 0.1, 0.3, 0.5
