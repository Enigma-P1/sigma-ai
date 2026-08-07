"""Tests for stats/baseline.py: the T-13 enforced order, and the frozen
EXIT-04 / EXIT-05 trigger behaviors (docs/traceability-matrix.md §4a).

Fixture datasets below were constructed and verified by direct
computation (see this milestone's build notes) to isolate exactly one
signal type each -- e.g. RULE1_DATASET trips rule 1 and nothing else at
the imr.py layer, confirmed by inspecting compute_imr_chart's own
signals list before being reused here at the orchestrator level.
"""

import numpy as np
import pytest

from sigma_engine.stats.baseline import run_baseline

# n=20 (clears the EXIT-04 companion floor), one obvious outlier (index 19),
# otherwise alternating so no accidental rule-4 run -- rule 1 signal alone.
RULE1_DATASET = [
    50, 49, 51, 48, 52, 49, 51, 50, 49, 51,
    48, 52, 49, 51, 50, 49, 51, 48, 52, 90,
]

# n=20, low-noise except 8 consecutive points (indices 8-15) nudged above
# the mean -- rule 4 signal alone, no point ever beyond 3 sigma.
RULE4_DATASET = [
    50, 49, 51, 48, 52, 49, 51, 50,
    50.5, 50.6, 50.4, 50.7, 50.5, 50.6, 50.4, 50.5,
    49, 51, 48, 52,
]

# Generous spec limits that don't themselves interfere with either fixture.
USL, LSL = 100.0, 0.0


def test_exit04_fires_on_a_rule1_dataset():
    result = run_baseline(RULE1_DATASET, usl=USL, lsl=LSL, operational_definition_ok=True)
    assert result.gate_ok is True
    assert result.stable is False
    assert "EXIT-04" in result.exits
    assert any(s.rule_id == "rule1" for s in result.stability.value.signals)


def test_exit04_fires_on_a_rule4_dataset():
    result = run_baseline(RULE4_DATASET, usl=USL, lsl=LSL, operational_definition_ok=True)
    assert result.gate_ok is True
    assert result.stable is False
    assert "EXIT-04" in result.exits
    assert any(s.rule_id == "rule4" for s in result.stability.value.signals)


@pytest.mark.parametrize("dataset", [RULE1_DATASET, RULE4_DATASET])
def test_unstable_baseline_has_no_cp_cpk_anywhere_only_ppk(dataset):
    """Baseline order enforcement: not stable -> Cp/Cpk absent, Pp/Ppk
    (performance, not capability) present."""
    result = run_baseline(dataset, usl=USL, lsl=LSL, operational_definition_ok=True)
    assert result.capability.value.cp_index is None
    assert result.capability.value.cpk_index is None
    assert result.capability.value.performance_not_capability is True
    assert result.capability.value.ppk_index is not None


def test_no_capability_without_spec_limits():
    """Order enforcement: specs + operational definition come first."""
    result = run_baseline(RULE1_DATASET, operational_definition_ok=True)
    assert result.gate_ok is False
    assert result.capability is None
    assert result.stability is None
    assert result.descriptive is None
    assert "spec limit" in result.gate_message


def test_no_computation_without_operational_definition_confirmed():
    result = run_baseline(RULE1_DATASET, usl=USL, lsl=LSL, operational_definition_ok=False)
    assert result.gate_ok is False
    assert result.capability is None
    assert "operational definition" in result.gate_message


def test_gate_fails_gracefully_below_two_observations():
    result = run_baseline([5.0], usl=USL, lsl=LSL, operational_definition_ok=True)
    assert result.gate_ok is False
    assert result.n == 1


# --- Sigma-level shift label: always present, on every code path ----------

# Spec limits scaled to each dataset -- USL/LSL=100/0 for RULE1_DATASET (its
# outlier spans a wide range) would make RULE4_DATASET's tightly-clustered
# data ~15 sigma from either limit, where norm.sf(3*cpk) itself underflows
# to exactly 0.0 in float64 (see sigma_level.py's dpmo_from_capability
# docstring) -- a real numerical floor, not a bug, but not a realistic
# Green Belt spec width either, so the sigma-level tests use limits scaled
# to each dataset's actual spread instead of exercising that floor here.
RULE4_USL, RULE4_LSL = 56.0, 44.0


@pytest.mark.parametrize("dataset,usl,lsl", [(RULE1_DATASET, USL, LSL), (RULE4_DATASET, RULE4_USL, RULE4_LSL)])
def test_sigma_level_convention_label_always_travels_with_the_number(dataset, usl, lsl):
    result = run_baseline(dataset, usl=usl, lsl=lsl, operational_definition_ok=True)
    assert result.sigma is not None
    assert result.sigma.value.convention in ("with 1.5σ shift", "without shift")


def test_sigma_level_shift_default_is_applied_and_toggleable():
    with_shift = run_baseline(RULE4_DATASET, usl=RULE4_USL, lsl=RULE4_LSL, operational_definition_ok=True)
    without_shift = run_baseline(
        RULE4_DATASET, usl=RULE4_USL, lsl=RULE4_LSL, operational_definition_ok=True, apply_sigma_shift=False
    )
    assert with_shift.sigma.value.convention == "with 1.5σ shift"  # default
    assert without_shift.sigma.value.convention == "without shift"
    assert with_shift.sigma.value.sigma_level - without_shift.sigma.value.sigma_level == pytest.approx(1.5)


# --- WECO rules 2/3: opt-in, off by default, and never trigger EXIT-04 ----
# (matrix §4a EXIT-04 is frozen to rule 1 / rule 4 signals only; zone rules
# are diagnostic-only even when explicitly enabled -- see imr.py's
# has_default_rule_signal docstring for why).

RULE2_ONLY_DATA = [
    50, 50.2, 49.8, 50.2, 49.8, 50.2, 49.8, 50.2, 49.8, 50.2,
    49.8, 50.2, 49.8, 50.2, 49.8, 50.2, 49.8,
    51.0, 50.2, 51.0,
]


def test_rule2_off_by_default_at_baseline_level():
    result = run_baseline(RULE2_ONLY_DATA, usl=60, lsl=40, operational_definition_ok=True)
    assert result.stability.value.rule2_enabled is False
    assert not any(s.rule_id == "rule2" for s in result.stability.value.signals)


def test_rule2_enabled_signals_but_still_does_not_trigger_exit04():
    result = run_baseline(
        RULE2_ONLY_DATA, usl=60, lsl=40, operational_definition_ok=True, enable_rule2=True
    )
    assert any(s.rule_id == "rule2" for s in result.stability.value.signals)
    assert result.stable is True  # rule 2 alone never flips stability
    assert "EXIT-04" not in result.exits


# --- EXIT-05: branches at exactly n=100 (matrix §4a, frozen) ---------------

def _skewed_sample(n: int) -> list[float]:
    # Fixed seed: deterministic and reproducible: same 100 draws every run,
    # sliced down to n. Exponential is clearly non-normal (concern fires).
    rng = np.random.default_rng(2026)
    return list(rng.exponential(scale=3.0, size=100))[:n]


def test_exit05_percentile_capability_only_from_n_100():
    data = _skewed_sample(100)
    result = run_baseline(data, usl=max(data) + 1, lsl=-1.0, operational_definition_ok=True)
    assert result.normality.value.advisory == "concern"
    assert "EXIT-05" in result.exits
    assert result.percentile_capability is not None
    assert result.observed_yield is None
    assert result.percentile_capability.value.n == 100


def test_exit05_observed_yield_fallback_below_n_100():
    data = _skewed_sample(99)
    full_data_for_specs = _skewed_sample(100)  # same generation, same spec limits both sides of the boundary
    result = run_baseline(
        data, usl=max(full_data_for_specs) + 1, lsl=-1.0, operational_definition_ok=True
    )
    assert result.normality.value.advisory == "concern"
    assert "EXIT-05" in result.exits
    assert result.percentile_capability is None
    assert result.observed_yield is not None
    assert result.observed_yield.value.n == 99


def test_baseline_result_round_trips_through_json():
    from sigma_engine.stats.baseline import BaselineResult

    result = run_baseline(RULE4_DATASET, usl=USL, lsl=LSL, operational_definition_ok=True)
    dumped = result.model_dump(mode="json")
    reloaded = BaselineResult.model_validate(dumped)
    assert reloaded == result
