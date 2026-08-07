"""Reference tests for stats/sigma_level.py.

DPMO<->sigma-level cross-checked against two independently published
tables, both fetched live 2026-08-07 (constants.py cites both):
  Wikipedia "Six Sigma", § Sigma levels: 1σ->691462, 2σ->308538,
  3σ->66807, 4σ->6210, 5σ->233, 6σ->3.4 DPMO (all with 1.5σ shift).
  MoreSteam.com "Six Sigma Conversion Table": independently states the
  same 3/4/5/6-sigma figures (66,800 / 6,210 / 233 / 3.4 DPMO).
dpmo_from_capability is cross-checked against NIST §6.1.6's own
"Translating capability into rejects" table (centered process,
Cp=1.00/1.33/1.66/2.00 -> ~2700/64/0.6/0.002 ppm two-sided) -- allowing a
generous relative tolerance since NIST's own Cp column is itself rounded
(e.g. 1.33 stands for 4/3).
"""

import pytest

from sigma_engine.stats.sigma_level import (
    dpmo_from_capability,
    dpmo_from_defects,
    dpu,
    fpy_from_dpu,
    observed_yield_in_spec,
    rty,
    sigma_level_from_dpmo,
)

# Wikipedia "Six Sigma" § Sigma levels AND MoreSteam.com "Six Sigma
# Conversion Table" (independent sources, identical figures) -- DPMO with
# the 1.5-sigma shift already applied, by starting (short-term) sigma level.
PUBLISHED_DPMO_BY_SIGMA_LEVEL = {1: 691_462, 2: 308_538, 3: 66_807, 4: 6_210, 5: 233, 6: 3.4}


@pytest.mark.parametrize("level,published_dpmo", PUBLISHED_DPMO_BY_SIGMA_LEVEL.items())
def test_sigma_level_from_dpmo_recovers_published_table_with_shift(level, published_dpmo):
    recovered, convention = sigma_level_from_dpmo(published_dpmo, apply_shift=True)
    assert recovered == pytest.approx(level, abs=0.01)
    assert convention == "with 1.5σ shift"


def test_sigma_level_convention_label_is_always_present_and_differs_without_shift():
    """'the number never travels without its label' -- and turning the
    shift off changes both the label and the number by exactly 1.5."""
    with_shift, conv_with = sigma_level_from_dpmo(66_807, apply_shift=True)
    without_shift, conv_without = sigma_level_from_dpmo(66_807, apply_shift=False)
    assert conv_with == "with 1.5σ shift"
    assert conv_without == "without shift"
    assert with_shift - without_shift == pytest.approx(1.5)


NIST_CENTERED_REJECTS_PPM = {1.00: 2700, 1.33: 64, 1.66: 0.6, 2.00: 0.002}


@pytest.mark.parametrize("cp_value,published_ppm", NIST_CENTERED_REJECTS_PPM.items())
def test_dpmo_from_capability_matches_nist_rejects_table(cp_value, published_ppm):
    """Centered process: Cpu = Cpl = Cp."""
    got = dpmo_from_capability(cp_value, cp_value)
    assert got == pytest.approx(published_ppm, rel=0.07)  # NIST's own Cp column is rounded


def test_dpmo_from_capability_one_sided_uses_only_the_supplied_index():
    two_sided = dpmo_from_capability(1.5, 1.5)
    one_sided = dpmo_from_capability(1.5, None)
    assert one_sided == pytest.approx(two_sided / 2)


def test_dpmo_from_defects_hand_computed():
    # 10 defects over 1000 units at 5 opportunities/unit -> 1e6*10/5000 = 2000
    assert dpmo_from_defects(10, 1000, 5) == pytest.approx(2000.0)


def test_dpu_fpy_rty_hand_computed():
    assert dpu(5, 100) == pytest.approx(0.05)
    import math
    assert fpy_from_dpu(0.05) == pytest.approx(math.exp(-0.05))
    # Two steps, FPY 0.95 and 0.90 -> RTY = 0.855
    assert rty([0.95, 0.90]) == pytest.approx(0.855)


def test_observed_yield_in_spec_hand_computed():
    data = [10, 20, 30, 40, 50]  # 3 of 5 within [15, 45]
    assert observed_yield_in_spec(data, lsl=15, usl=45) == pytest.approx(3 / 5)


def test_observed_yield_in_spec_one_sided():
    data = [10, 20, 30, 40, 50]  # 4 of 5 are >= 15
    assert observed_yield_in_spec(data, lsl=15, usl=None) == pytest.approx(4 / 5)


def test_rty_requires_at_least_one_fpy():
    with pytest.raises(ValueError):
        rty([])
