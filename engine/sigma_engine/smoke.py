"""The NIST-verified smoke calculation exposed by GET /smoke."""

from scipy import stats

from .nist_lew import CERTIFIED_MEAN, CERTIFIED_STDEV, DATA, DATASET_NAME

# Relative tolerance for "computed == certified", per the M1 brief.
RELATIVE_TOLERANCE = 1e-9


def compute_smoke_result() -> dict:
    """Compute mean/stdev over the NIST Lew dataset and compare to certified values."""
    n = len(DATA)
    # ddof=1 -> sample standard deviation (denominator n-1), matching the
    # StRD certified value's stated definition.
    described = stats.describe(DATA, ddof=1)
    mean = float(described.mean)
    stdev = float(described.variance**0.5)

    mean_match = abs(mean - CERTIFIED_MEAN) <= RELATIVE_TOLERANCE * abs(CERTIFIED_MEAN)
    stdev_match = abs(stdev - CERTIFIED_STDEV) <= RELATIVE_TOLERANCE * abs(CERTIFIED_STDEV)

    return {
        "dataset": DATASET_NAME,
        "n": n,
        "mean": mean,
        "stdev": stdev,
        "certified_mean": CERTIFIED_MEAN,
        "certified_stdev": CERTIFIED_STDEV,
        "match": bool(mean_match and stdev_match),
    }
