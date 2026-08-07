"""Reference tests for stats/capability.py against NIST/SEMATECH §6.1.6's
own worked example: https://www.itl.nist.gov/div898/handbook/pmc/section1/pmc16.htm
"USL=20, LSL=8, xbar=16, s=2" -> Cp=1.0, Cpu=0.6667, Cpl=1.3333,
Cpk=min(Cpu,Cpl)=0.6667. Reproduced here to NIST's own 4-decimal
precision. The same arithmetic validates both the Cp/Cpk formula path
(sigma_within) and the Pp/Ppk formula path (sigma_overall) since NIST's
example uses a single generic "s" -- the two indices are the identical
formula fed a different sigma, per capability.py's docstring.
"""

import pytest

from sigma_engine.stats.capability import compute_capability, cp, cpk, cpl, cpu

NIST_USL, NIST_LSL, NIST_MEAN, NIST_S = 20.0, 8.0, 16.0, 2.0
NIST_TOLERANCE = 1e-3  # NIST's own worked numbers are printed to 4 decimals


def test_cp_matches_nist_worked_example():
    assert cp(NIST_USL, NIST_LSL, NIST_S) == pytest.approx(1.0)


def test_cpu_and_cpl_match_nist_worked_example():
    assert cpu(NIST_USL, NIST_MEAN, NIST_S) == pytest.approx(0.6667, abs=NIST_TOLERANCE)
    assert cpl(NIST_MEAN, NIST_LSL, NIST_S) == pytest.approx(1.3333, abs=NIST_TOLERANCE)


def test_cpk_is_the_min_of_cpu_and_cpl_matching_nist():
    assert cpk(NIST_USL, NIST_LSL, NIST_MEAN, NIST_S) == pytest.approx(0.6667, abs=NIST_TOLERANCE)
    assert cpk(NIST_USL, NIST_LSL, NIST_MEAN, NIST_S) == min(
        cpu(NIST_USL, NIST_MEAN, NIST_S), cpl(NIST_MEAN, NIST_LSL, NIST_S)
    )


def test_compute_capability_stable_reports_both_cp_cpk_and_pp_ppk():
    result = compute_capability(
        mean=NIST_MEAN, sigma_within=NIST_S, sigma_overall=NIST_S, usl=NIST_USL, lsl=NIST_LSL, n=60, stable=True
    ).value
    assert result.cp_index == pytest.approx(1.0)
    assert result.cpk_index == pytest.approx(0.6667, abs=NIST_TOLERANCE)
    assert result.pp_index == pytest.approx(1.0)
    assert result.ppk_index == pytest.approx(0.6667, abs=NIST_TOLERANCE)
    assert result.performance_not_capability is False


def test_compute_capability_unstable_reports_ppk_only_never_cpk():
    """matrix EXIT-04: not stable -> Pp/Ppk only, Cp/Cpk absent entirely."""
    result = compute_capability(
        mean=NIST_MEAN, sigma_within=NIST_S, sigma_overall=NIST_S, usl=NIST_USL, lsl=NIST_LSL, n=60, stable=False
    ).value
    assert result.cp_index is None
    assert result.cpk_index is None
    assert result.pp_index == pytest.approx(1.0)
    assert result.ppk_index == pytest.approx(0.6667, abs=NIST_TOLERANCE)
    assert result.performance_not_capability is True


def test_one_sided_upper_spec_only_reports_cpu_as_cpk_and_no_cp():
    """matrix III.F.1: Cp/Pp not reported without both limits."""
    result = compute_capability(
        mean=NIST_MEAN, sigma_within=NIST_S, sigma_overall=NIST_S, usl=NIST_USL, lsl=None, n=60, stable=True
    ).value
    assert result.one_sided is True
    assert result.cp_index is None
    assert result.pp_index is None
    assert result.cpk_index == pytest.approx(cpu(NIST_USL, NIST_MEAN, NIST_S))
    assert result.ppk_index == pytest.approx(cpu(NIST_USL, NIST_MEAN, NIST_S))


def test_one_sided_lower_spec_only_reports_cpl_as_cpk():
    result = compute_capability(
        mean=NIST_MEAN, sigma_within=NIST_S, sigma_overall=NIST_S, usl=None, lsl=NIST_LSL, n=60, stable=True
    ).value
    assert result.one_sided is True
    assert result.cpk_index == pytest.approx(cpl(NIST_MEAN, NIST_LSL, NIST_S))


def test_compute_capability_requires_at_least_one_spec_limit():
    with pytest.raises(ValueError):
        compute_capability(mean=16, sigma_within=2, sigma_overall=2, usl=None, lsl=None, n=60, stable=True)


def test_compute_capability_warns_below_nist_sample_size_floors():
    result = compute_capability(
        mean=NIST_MEAN, sigma_within=NIST_S, sigma_overall=NIST_S, usl=NIST_USL, lsl=NIST_LSL, n=30, stable=True
    )
    assert any("50" in w for w in result.provenance.warnings)
