"""M2 stats-core: deterministic statistics the tools and honesty exits
stand on (descriptive, I-MR, capability, normality advisory, sigma level/
DPMO, and the T-13 baseline orchestrator). Every computed result is a
provenance-stamped Computed value (provenance.py) -- see docs/
traceability-matrix.md §4a for the frozen thresholds enforced throughout.
"""

from .baseline import BaselineResult, ObservedYieldResult, PercentileCapabilityResult, run_baseline
from .capability import CapabilityResult, compute_capability
from .descriptive import DescriptiveStats, compute_descriptive_stats
from .hypothesis_categorical import chi_square_independence, cochran_preflight, one_proportion_exact, two_proportion_z
from .hypothesis_common import GroupInput, HypothesisQuestion, HypothesisTestResult
from .hypothesis_nonparametric import mann_whitney_u, wilcoxon_signed_rank
from .hypothesis_parametric import one_sample_t, one_way_anova, paired_t, welch_two_sample_t
from .hypothesis_runner import HypothesisRunResult, run_hypothesis
from .hypothesis_selector import RoutingDecision, route_hypothesis
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
    "chi_square_independence",
    "cochran_preflight",
    "one_proportion_exact",
    "two_proportion_z",
    "GroupInput",
    "HypothesisQuestion",
    "HypothesisTestResult",
    "mann_whitney_u",
    "wilcoxon_signed_rank",
    "one_sample_t",
    "one_way_anova",
    "paired_t",
    "welch_two_sample_t",
    "HypothesisRunResult",
    "run_hypothesis",
    "RoutingDecision",
    "route_hypothesis",
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
