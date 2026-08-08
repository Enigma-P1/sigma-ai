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
from .msa import (
    AttributeAgreementResult,
    AttributeRating,
    Exit02Payload,
    Exit03Payload,
    ItemRepeats,
    MsaResult,
    PooledRepeatabilityResult,
    RepeatabilityResult,
    ResolutionCheckResult,
    check_resolution,
    cohens_kappa,
    compute_repeatability,
    pooled_within_item_sd,
    run_attribute_msa,
    run_continuous_msa,
)
from .normality import NormalityResult, assess_normality
from .sample_size import (
    MeanSampleSizeResult,
    ProportionSampleSizeResult,
    RuleOfThumbResult,
    imr_baseline_rule_of_thumb,
    sample_size_for_mean,
    sample_size_for_proportion,
    sampling_bias_warnings,
)
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
    "AttributeAgreementResult",
    "AttributeRating",
    "Exit02Payload",
    "Exit03Payload",
    "ItemRepeats",
    "MsaResult",
    "PooledRepeatabilityResult",
    "RepeatabilityResult",
    "ResolutionCheckResult",
    "check_resolution",
    "cohens_kappa",
    "compute_repeatability",
    "pooled_within_item_sd",
    "run_attribute_msa",
    "run_continuous_msa",
    "NormalityResult",
    "assess_normality",
    "MeanSampleSizeResult",
    "ProportionSampleSizeResult",
    "RuleOfThumbResult",
    "imr_baseline_rule_of_thumb",
    "sample_size_for_mean",
    "sample_size_for_proportion",
    "sampling_bias_warnings",
    "SigmaLevelResult",
    "compute_sigma_level",
]
