"""Descriptive statistics: mean, sample sd, median, IQR, min/max, n.

Formula source: NIST/SEMATECH e-Handbook of Statistical Methods,
§1.3.5.1 "Measures of Location" (mean, median) and §1.3.5.6 "Measures of
Scale" (sample standard deviation denom. n-1; interquartile range =
75th percentile minus 25th percentile):
  https://www.itl.nist.gov/div898/handbook/eda/section3/eda351.htm
  https://www.itl.nist.gov/div898/handbook/eda/section3/eda356.htm
NIST states IQR as "75th percentile minus 25th percentile" without
mandating an interpolation scheme; percentiles here use numpy's default
'linear' method (Hyndman & Fan type 7), the most common convention.

Reference-tested (tests/test_stats_descriptive.py) against three NIST
StRD Univariate Summary Statistics datasets: Lew (embedded pre-M2 in
nist_lew.py), and Lottery + Mavro (fetched live for M2, see
nist_lottery.py / nist_mavro.py) -- StRD certifies mean and sample sd
only, to 1e-9; median/IQR/min/max have no StRD certified value and are
instead checked against a small hand-computed fixture with the
arithmetic shown in the test.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from pydantic import BaseModel, ConfigDict

from ..provenance import Computed, compute


def n(data: Sequence[float]) -> int:
    return len(data)


def mean(data: Sequence[float]) -> float:
    if len(data) == 0:
        raise ValueError("mean requires at least 1 observation")
    return float(np.mean(data))


def weighted_mean(data: Sequence[float], weights: Sequence[float] | None) -> float:
    """Plain mean when weights is None (byte-identical to mean() -- the
    unweighted/continuous path this engine has always run); otherwise the
    weighted mean sum(v_i*w_i)/sum(w_i). This is the correct way to pool a
    set of values that were each already an average over a different-sized
    group -- e.g. daily defective proportions with a different order count
    each day (weights = subgroup sizes) -- instead of averaging the
    per-group averages themselves, which silently treats a light day and a
    heavy day as equally informative. Same pooling arithmetic as
    stats/p_chart.py's p_bar(sum(defectives)/sum(n)), generalized here from
    Subgroup counts to a plain (value, weight) pair (artifacts/proof.py's
    before/after DataRef -- rubric R-IMP-03 #1 same-yardstick, R-IMP-04
    anchor)."""
    if weights is None:
        return mean(data)
    if len(data) != len(weights):
        raise ValueError(f"weighted_mean: data ({len(data)}) and weights ({len(weights)}) must be the same length")
    total_weight = float(sum(weights))
    if total_weight <= 0:
        raise ValueError("weighted_mean requires a positive total weight")
    return sum(v * w for v, w in zip(data, weights)) / total_weight


def sample_sd(data: Sequence[float]) -> float:
    """Sample standard deviation, denominator n-1 (NIST §1.3.5.6)."""
    if len(data) < 2:
        raise ValueError("sample_sd requires at least 2 observations (denom. n-1)")
    return float(np.std(data, ddof=1))


def median(data: Sequence[float]) -> float:
    if len(data) == 0:
        raise ValueError("median requires at least 1 observation")
    return float(np.median(data))


def quartiles(data: Sequence[float]) -> tuple[float, float]:
    """(Q1, Q3) via linear-interpolation percentiles (numpy default)."""
    if len(data) == 0:
        raise ValueError("quartiles requires at least 1 observation")
    q1, q3 = np.percentile(data, [25, 75], method="linear")
    return float(q1), float(q3)


def iqr(data: Sequence[float]) -> float:
    q1, q3 = quartiles(data)
    return q3 - q1


class DescriptiveStats(BaseModel):
    model_config = ConfigDict(frozen=True)

    n: int
    mean: float
    sd: float
    median: float
    q1: float
    q3: float
    iqr: float
    min: float
    max: float


def compute_descriptive_stats(data: Sequence[float]) -> Computed[DescriptiveStats]:
    """The one supported way to produce a provenance-stamped
    DescriptiveStats. Requires n>=2 (sample_sd's denom. n-1)."""
    q1, q3 = quartiles(data)
    result = DescriptiveStats(
        n=len(data),
        mean=mean(data),
        sd=sample_sd(data),
        median=median(data),
        q1=q1,
        q3=q3,
        iqr=q3 - q1,
        min=float(np.min(data)),
        max=float(np.max(data)),
    )
    return compute(
        result,
        method="descriptive: mean, sample sd (n-1), median, IQR (linear-interpolation "
        "percentiles) per NIST/SEMATECH §1.3.5.1/§1.3.5.6",
        input_data=list(data),
        assumptions_checked=["n >= 2"],
    )
