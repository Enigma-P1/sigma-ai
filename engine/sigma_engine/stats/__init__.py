"""M2 stats-core: deterministic statistics the tools and honesty exits
stand on (descriptive, I-MR, capability, normality advisory, sigma level/
DPMO, and the T-13 baseline orchestrator). Every computed result is a
provenance-stamped Computed value (provenance.py) -- see docs/
traceability-matrix.md §4a for the frozen thresholds enforced throughout.
"""

from .baseline import BaselineResult, ObservedYieldResult, PercentileCapabilityResult, run_baseline
from .capability import CapabilityResult, compute_capability
from .descriptive import DescriptiveStats, compute_descriptive_stats
from .imr import ImrChartResult, Signal, compute_imr_chart
from .normality import NormalityResult, assess_normality
from .sigma_level import SigmaLevelResult, compute_sigma_level

__all__ = [
    "BaselineResult",
    "ObservedYieldResult",
    "PercentileCapabilityResult",
    "run_baseline",
    "CapabilityResult",
    "compute_capability",
    "DescriptiveStats",
    "compute_descriptive_stats",
    "ImrChartResult",
    "Signal",
    "compute_imr_chart",
    "NormalityResult",
    "assess_normality",
    "SigmaLevelResult",
    "compute_sigma_level",
]
