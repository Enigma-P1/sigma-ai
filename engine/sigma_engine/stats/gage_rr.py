"""Full crossed Gage R&R by the ANOVA method (T-35).

WHAT THIS IS, versus what T-12 already does. T-12 is a narrow measurement
check: one operator, test/retest repeatability, honestly named. It cannot
see whether two people measuring the same part agree, and it says so. This
module answers the question T-12 routes out of -- how much of the variation
you are looking at is the parts, and how much is the measuring -- by
decomposing the variance across parts, operators, and their interaction.

It is the tool a manufacturing quality engineer names unprompted, and the
biggest single gap in the statistics engine until now.

METHOD: two-way ANOVA with interaction, the standard crossed study where
every operator measures every part. Sums of squares are the textbook
decomposition and the module asserts the identity SS_total = SS_part +
SS_operator + SS_interaction + SS_error rather than trusting it, because a
silent arithmetic slip here produces plausible-looking components that are
simply wrong.

VARIANCE COMPONENTS are recovered from expected mean squares:

    sigma2_repeatability = MS_error
    sigma2_interaction   = (MS_interaction - MS_error) / replicates
    sigma2_operator      = (MS_operator - MS_interaction) / (parts * replicates)
    sigma2_part          = (MS_part - MS_interaction) / (operators * replicates)

NEGATIVE COMPONENTS ARE CLAMPED TO ZERO and reported as clamped. A variance
cannot be negative; the estimator can be, when the true component is near
zero and noise pushes the mean-square difference the wrong way. Silently
clamping is standard and silently NOT reporting it is how a study that
barely resolved anything gets read as clean.

INTERACTION POOLING. When the operator-by-part interaction is not
significant the convention is to pool it into error and re-derive without
it, which gives a better repeatability estimate. The threshold is alpha =
0.25, deliberately loose, and the decision is reported rather than hidden --
the two models can give visibly different %GRR and a reader is entitled to
know which one produced the number.

THRESHOLDS AND WORDING. The 10% / 30% acceptance bands are industry
convention and are used here, but the verdict text is this engine's own.
AIAG's manual wording is copyrighted; the arithmetic is not. Same stance
already taken for the FMEA anchor scales.
"""

from __future__ import annotations

import math
from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field

Verdict = Literal["acceptable", "marginal", "unacceptable"]
Basis = Literal["study_variation", "tolerance"]

# Convention, frozen here so no caller invents its own bands.
GRR_ACCEPTABLE_MAX_PERCENT = 10.0
GRR_MARGINAL_MAX_PERCENT = 30.0
# Distinct categories: the measurement system must resolve at least this
# many non-overlapping groups of parts to be useful for anything but
# pass/fail sorting.
NDC_MINIMUM = 5
# 1.41 = sqrt(2), from the standard number-of-distinct-categories formula
# ndc = (sigma_part / sigma_grr) * sqrt(2).
NDC_MULTIPLIER = math.sqrt(2.0)
# Deliberately loose: pooling a real interaction into error understates
# reproducibility, so the test errs toward keeping the interaction term.
INTERACTION_POOLING_ALPHA = 0.25
# 6 sigma spans ~99.73% of a normal distribution; the study-variation and
# tolerance percentages are both computed on that span by convention.
STUDY_VARIATION_SIGMA_MULTIPLIER = 6.0


class Measurement(BaseModel):
    """One reading. Parts and operators are identified by label, not index,
    so a caller cannot silently transpose the study by reordering rows."""

    model_config = ConfigDict(frozen=True)

    part: str = Field(min_length=1)
    operator: str = Field(min_length=1)
    value: float


class AnovaRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: str
    df: int
    ss: float
    ms: float
    f_statistic: float | None = None
    p_value: float | None = None


class VarianceComponent(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    variance: float
    std_dev: float
    percent_study_variation: float
    percent_tolerance: float | None = None
    # True when the raw estimator came out negative and was clamped to zero.
    clamped_from_negative: bool = False


class GageRRResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    parts: int
    operators: int
    replicates: int
    anova: tuple[AnovaRow, ...]
    interaction_pooled: bool
    interaction_p_value: float | None
    components: tuple[VarianceComponent, ...]
    grr_percent_study_variation: float
    grr_percent_tolerance: float | None
    number_of_distinct_categories: int
    verdict: Verdict
    basis: Basis
    warnings: tuple[str, ...] = ()


class GageRRError(ValueError):
    """Raised when the design cannot support the decomposition at all."""


def _grid(measurements: Sequence[Measurement]) -> tuple[list[str], list[str], int, dict[tuple[str, str], list[float]]]:
    cells: dict[tuple[str, str], list[float]] = {}
    parts: list[str] = []
    operators: list[str] = []
    for m in measurements:
        if m.part not in parts:
            parts.append(m.part)
        if m.operator not in operators:
            operators.append(m.operator)
        cells.setdefault((m.part, m.operator), []).append(m.value)

    if len(parts) < 2:
        raise GageRRError("a Gage R&R needs at least 2 parts -- with one part there is no part-to-part variation to compare the gauge against")
    if len(operators) < 2:
        raise GageRRError("a crossed Gage R&R needs at least 2 operators; for a single operator use the T-12 measurement check, which is honest about having no reproducibility term")

    missing = [(p, o) for p in parts for o in operators if (p, o) not in cells]
    if missing:
        raise GageRRError(
            f"crossed study requires every operator to measure every part; missing {len(missing)} combination(s), "
            f"e.g. part {missing[0][0]!r} / operator {missing[0][1]!r}"
        )

    counts = {len(v) for v in cells.values()}
    if len(counts) != 1:
        raise GageRRError(
            "every part/operator cell must have the same number of repeat readings -- "
            f"found {sorted(counts)}. An unbalanced study needs a different estimator than this one."
        )
    replicates = counts.pop()
    if replicates < 2:
        raise GageRRError("each operator must measure each part at least twice -- with one reading per cell there is nothing to estimate repeatability from")
    return parts, operators, replicates, cells


def _f_p_value(f_stat: float, df_num: int, df_den: int) -> float | None:
    # F == 0 is a real, meaningful result -- the term explains nothing, and
    # p is 1.0, the strongest possible case for pooling it away. An earlier
    # guard of `f_stat <= 0` returned None there, which the pooling decision
    # read as "unknown" and so declined to pool: the exact opposite of what
    # a zero interaction calls for. Only genuinely undefined inputs return
    # None now.
    if f_stat < 0 or df_num <= 0 or df_den <= 0:
        return None
    if f_stat == 0:
        return 1.0
    try:
        from scipy import stats as scipy_stats
    except ImportError:  # pragma: no cover -- scipy is a hard dependency
        return None
    return float(scipy_stats.f.sf(f_stat, df_num, df_den))


def compute_gage_rr(
    measurements: Sequence[Measurement],
    *,
    tolerance: float | None = None,
    pool_interaction: bool | None = None,
) -> GageRRResult:
    """Run the crossed study.

    `pool_interaction=None` decides by the significance test (the usual
    behaviour). Pass True or False to force it -- a caller reproducing a
    published worked example needs to be able to match its model choice.
    """
    parts, operators, replicates, cells = _grid(measurements)
    n_p, n_o, n_r = len(parts), len(operators), replicates
    total_n = n_p * n_o * n_r

    all_values = [v for p in parts for o in operators for v in cells[(p, o)]]
    grand_mean = sum(all_values) / total_n

    part_means = {p: sum(v for o in operators for v in cells[(p, o)]) / (n_o * n_r) for p in parts}
    op_means = {o: sum(v for p in parts for v in cells[(p, o)]) / (n_p * n_r) for o in operators}
    cell_means = {key: sum(vals) / len(vals) for key, vals in cells.items()}

    ss_part = n_o * n_r * sum((part_means[p] - grand_mean) ** 2 for p in parts)
    ss_op = n_p * n_r * sum((op_means[o] - grand_mean) ** 2 for o in operators)
    ss_int = n_r * sum(
        (cell_means[(p, o)] - part_means[p] - op_means[o] + grand_mean) ** 2 for p in parts for o in operators
    )
    ss_error = sum((v - cell_means[(p, o)]) ** 2 for p in parts for o in operators for v in cells[(p, o)])
    ss_total = sum((v - grand_mean) ** 2 for v in all_values)

    # Assert the decomposition rather than trusting it: an arithmetic slip
    # here yields components that look entirely plausible and are wrong.
    reconstructed = ss_part + ss_op + ss_int + ss_error
    if not math.isclose(reconstructed, ss_total, rel_tol=1e-9, abs_tol=1e-9):
        raise GageRRError(
            f"ANOVA decomposition failed: SS_total={ss_total!r} but the parts sum to {reconstructed!r}"
        )

    df_part, df_op = n_p - 1, n_o - 1
    df_int = df_part * df_op
    df_error = n_p * n_o * (n_r - 1)

    ms_part = ss_part / df_part
    ms_op = ss_op / df_op
    ms_int = ss_int / df_int if df_int else 0.0
    ms_error = ss_error / df_error

    f_int = (ms_int / ms_error) if (ms_error > 0 and df_int) else None
    p_int = _f_p_value(f_int, df_int, df_error) if f_int is not None else None

    should_pool = pool_interaction
    if should_pool is None:
        should_pool = p_int is not None and p_int > INTERACTION_POOLING_ALPHA

    warnings: list[str] = []
    if should_pool:
        # Pooled model: interaction folded back into error.
        ms_error_used = (ss_int + ss_error) / (df_int + df_error)
        var_repeat = ms_error_used
        var_int = 0.0
        var_op_raw = (ms_op - ms_error_used) / (n_p * n_r)
        var_part_raw = (ms_part - ms_error_used) / (n_o * n_r)
    else:
        ms_error_used = ms_error
        var_repeat = ms_error
        var_int_raw = (ms_int - ms_error) / n_r
        var_int = max(var_int_raw, 0.0)
        if var_int_raw < 0:
            warnings.append("The operator-by-part interaction estimate came out negative and was set to zero.")
        var_op_raw = (ms_op - ms_int) / (n_p * n_r)
        var_part_raw = (ms_part - ms_int) / (n_o * n_r)

    var_op = max(var_op_raw, 0.0)
    var_part = max(var_part_raw, 0.0)
    if var_op_raw < 0:
        warnings.append(
            "The operator (reproducibility) estimate came out negative and was set to zero — the operators "
            "differ by less than the noise in this study, not by nothing."
        )
    if var_part_raw < 0:
        warnings.append(
            "The part-to-part estimate came out negative and was set to zero — these parts are too alike for "
            "this study to say anything about the gauge."
        )

    var_reproducibility = var_op + var_int
    var_grr = var_repeat + var_reproducibility
    var_total = var_grr + var_part

    if var_total <= 0:
        raise GageRRError("total variance is zero -- every reading in the study is identical, so there is nothing to decompose")

    sd_total = math.sqrt(var_total)

    def component(name: str, variance: float, clamped: bool = False) -> VarianceComponent:
        sd = math.sqrt(variance)
        return VarianceComponent(
            name=name,
            variance=variance,
            std_dev=sd,
            # Percentages are on STANDARD DEVIATIONS, not variances -- the
            # convention, and the reason the columns do not sum to 100.
            percent_study_variation=100.0 * sd / sd_total,
            percent_tolerance=(
                100.0 * STUDY_VARIATION_SIGMA_MULTIPLIER * sd / tolerance if tolerance and tolerance > 0 else None
            ),
            clamped_from_negative=clamped,
        )

    components = (
        component("repeatability", var_repeat),
        component("reproducibility", var_reproducibility, clamped=var_op_raw < 0),
        component("operator", var_op, clamped=var_op_raw < 0),
        component("operator_x_part", var_int),
        component("gage_rr", var_grr),
        component("part_to_part", var_part, clamped=var_part_raw < 0),
        component("total_variation", var_total),
    )

    grr_percent_sv = 100.0 * math.sqrt(var_grr) / sd_total
    grr_percent_tol = (
        100.0 * STUDY_VARIATION_SIGMA_MULTIPLIER * math.sqrt(var_grr) / tolerance
        if tolerance and tolerance > 0
        else None
    )

    ndc_raw = NDC_MULTIPLIER * math.sqrt(var_part) / math.sqrt(var_grr) if var_grr > 0 else 0.0
    ndc = int(ndc_raw)  # truncated, by convention, not rounded

    basis: Basis = "tolerance" if grr_percent_tol is not None else "study_variation"
    judged = grr_percent_tol if grr_percent_tol is not None else grr_percent_sv
    if judged <= GRR_ACCEPTABLE_MAX_PERCENT:
        verdict: Verdict = "acceptable"
    elif judged <= GRR_MARGINAL_MAX_PERCENT:
        verdict = "marginal"
    else:
        verdict = "unacceptable"

    if ndc < NDC_MINIMUM:
        warnings.append(
            f"Only {ndc} distinct categories — the gauge cannot reliably separate these parts into "
            f"more than {ndc} group(s). Below {NDC_MINIMUM} it is a sorting tool, not a measuring one."
        )
    if n_p < 10:
        warnings.append(f"{n_p} parts. Fewer than 10 makes the part-to-part estimate — and so every percentage — unstable.")
    if n_r < 2:  # pragma: no cover -- _grid already rejects this
        warnings.append("Fewer than 2 repeats per cell.")

    anova = [
        AnovaRow(source="part", df=df_part, ss=ss_part, ms=ms_part,
                 f_statistic=(ms_part / ms_int) if (ms_int > 0 and not should_pool) else (ms_part / ms_error_used if ms_error_used > 0 else None)),
        AnovaRow(source="operator", df=df_op, ss=ss_op, ms=ms_op,
                 f_statistic=(ms_op / ms_int) if (ms_int > 0 and not should_pool) else (ms_op / ms_error_used if ms_error_used > 0 else None)),
        AnovaRow(source="operator_x_part", df=df_int, ss=ss_int, ms=ms_int, f_statistic=f_int, p_value=p_int),
        AnovaRow(source="repeatability", df=df_error, ss=ss_error, ms=ms_error),
        AnovaRow(source="total", df=total_n - 1, ss=ss_total, ms=ss_total / (total_n - 1)),
    ]

    return GageRRResult(
        parts=n_p,
        operators=n_o,
        replicates=n_r,
        anova=tuple(anova),
        interaction_pooled=bool(should_pool),
        interaction_p_value=p_int,
        components=components,
        grr_percent_study_variation=grr_percent_sv,
        grr_percent_tolerance=grr_percent_tol,
        number_of_distinct_categories=ndc,
        verdict=verdict,
        basis=basis,
        warnings=tuple(warnings),
    )
