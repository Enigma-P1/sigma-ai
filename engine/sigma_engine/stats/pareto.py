"""Pareto: category tally -> sorted-descending bars + cumulative share +
the vital-few line (PLAN §4.1 T-14 row: "vital-few bars highlighted to the
80% line"). The frozen 80% cumulative-share convention is the standard
Pareto/Six-Sigma "vital few" cutoff, not a NIST quantity (see
constants.py). `flat` names the honest opposite case (PLAN §4.5 /
research §F: "flat-bars honest headline") -- no small subset actually
dominates, so the chart says that instead of forcing a vital-few claim
onto a roughly-even distribution.
"""

from __future__ import annotations

from collections import Counter
from typing import Sequence

from pydantic import BaseModel, ConfigDict

from ..provenance import Computed, compute
from .constants import PARETO_VITAL_FEW_CUMULATIVE_SHARE


class ParetoCategory(BaseModel):
    model_config = ConfigDict(frozen=True)

    category: str
    count: int
    share: float
    cumulative_share: float
    vital_few: bool


class ParetoResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    total: int
    categories: tuple[ParetoCategory, ...]  # sorted count-descending
    vital_few_count: int
    # True when it takes (most of) the distinct categories themselves to
    # reach 80% -- no small subset actually dominates (module docstring).
    flat: bool


def compute_pareto(raw_categories: Sequence[str]) -> Computed[ParetoResult]:
    """The one supported way to produce a provenance-stamped ParetoResult.
    Counting, sorting, cumulative-share, and the vital-few/flat calls are
    all made here -- server-side, engine-verified -- so T-14's chart
    headline never has to guess at them client-side."""
    if len(raw_categories) == 0:
        raise ValueError("compute_pareto requires at least one category value")
    tally = Counter(raw_categories)
    total = sum(tally.values())
    ordered = sorted(tally.items(), key=lambda kv: (-kv[1], kv[0]))  # count desc, name asc as a tiebreak

    categories: list[ParetoCategory] = []
    cumulative = 0
    vital_few_count = 0
    crossed = False
    for name, count in ordered:
        cumulative += count
        cumulative_share = cumulative / total
        is_vital = not crossed
        if is_vital:
            vital_few_count += 1
        if cumulative_share >= PARETO_VITAL_FEW_CUMULATIVE_SHARE:
            crossed = True
        categories.append(ParetoCategory(
            category=name, count=count, share=count / total,
            cumulative_share=cumulative_share, vital_few=is_vital,
        ))

    result = ParetoResult(
        total=total, categories=tuple(categories), vital_few_count=vital_few_count,
        flat=(vital_few_count / len(ordered)) >= PARETO_VITAL_FEW_CUMULATIVE_SHARE,
    )
    return compute(
        result,
        method="Pareto: tally per category, sorted count-descending, cumulative share; vital few = the categories "
        f"up to and including the one that crosses {PARETO_VITAL_FEW_CUMULATIVE_SHARE:.0%} cumulative share "
        f"(PLAN §4.1 T-14 row); flat = it takes >= {PARETO_VITAL_FEW_CUMULATIVE_SHARE:.0%} of the distinct "
        "categories themselves to get there, i.e. no small subset dominates",
        input_data={"categories": list(raw_categories)},
    )
