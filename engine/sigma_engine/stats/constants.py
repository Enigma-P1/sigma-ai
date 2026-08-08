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
