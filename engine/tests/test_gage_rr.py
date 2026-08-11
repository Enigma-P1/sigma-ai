"""Full crossed Gage R&R (T-35).

The headline test is `test_hand_computed_two_by_two_by_two`: every value in
it was derived by hand from the ANOVA definitions before the module was
run, so it checks the arithmetic against an independent derivation rather
than against itself. The rest cover the decisions that make a Gage R&R
mislead when they go wrong -- negative components, interaction pooling,
percentages taken on the wrong scale, and designs that cannot support the
estimate at all.
"""

from __future__ import annotations

import math

import pytest

from sigma_engine.stats.gage_rr import (
    GRR_ACCEPTABLE_MAX_PERCENT,
    GageRRError,
    Measurement,
    compute_gage_rr,
)


def _ms(rows: list[tuple[str, str, float]]) -> list[Measurement]:
    return [Measurement(part=p, operator=o, value=v) for p, o, v in rows]


# Hand-derived fixture. 2 parts x 2 operators x 2 replicates:
#
#   grand mean 4.5; part means 2.5 / 6.5; operator means 4 / 5;
#   cell means 2, 3, 6, 7 -- chosen so the interaction is exactly zero.
#
#   SS_part  = 2*2 * ((2.5-4.5)^2 + (6.5-4.5)^2)          = 32
#   SS_op    = 2*2 * ((4-4.5)^2   + (5-4.5)^2)            =  2
#   SS_int   = 0 (every cell residual is exactly 0)
#   SS_error = 2+2+2+2                                     =  8
#   SS_total                                               = 42  (= 32+2+0+8)
HAND = _ms(
    [
        ("p1", "A", 1.0), ("p1", "A", 3.0),
        ("p1", "B", 2.0), ("p1", "B", 4.0),
        ("p2", "A", 5.0), ("p2", "A", 7.0),
        ("p2", "B", 6.0), ("p2", "B", 8.0),
    ]
)


def _component(result, name):
    return next(c for c in result.components if c.name == name)


def test_hand_computed_two_by_two_by_two():
    result = compute_gage_rr(HAND)
    ss = {row.source: row.ss for row in result.anova}
    assert ss["part"] == pytest.approx(32.0)
    assert ss["operator"] == pytest.approx(2.0)
    assert ss["operator_x_part"] == pytest.approx(0.0, abs=1e-12)
    assert ss["repeatability"] == pytest.approx(8.0)
    assert ss["total"] == pytest.approx(42.0)

    # Interaction is exactly zero, so F=0, p=1, and the model pools it.
    assert result.interaction_pooled is True
    # Pooled MS_error = (0 + 8) / (1 + 4) = 1.6
    assert _component(result, "repeatability").variance == pytest.approx(1.6)
    # (MS_op - MS_error) / (parts * reps) = (2 - 1.6) / 4 = 0.1
    assert _component(result, "operator").variance == pytest.approx(0.1)
    # (MS_part - MS_error) / (operators * reps) = (32 - 1.6) / 4 = 7.6
    assert _component(result, "part_to_part").variance == pytest.approx(7.6)
    # GRR = 1.6 + 0.1 = 1.7 ; total = 9.3
    assert _component(result, "gage_rr").variance == pytest.approx(1.7)
    assert _component(result, "total_variation").variance == pytest.approx(9.3)
    # 100 * sqrt(1.7) / sqrt(9.3)
    assert result.grr_percent_study_variation == pytest.approx(100 * math.sqrt(1.7 / 9.3))
    # ndc = sqrt(2) * sqrt(7.6) / sqrt(1.7) = 2.99..., truncated
    assert result.number_of_distinct_categories == 2


def test_sum_of_squares_identity_holds_on_random_data():
    """The module raises if the decomposition does not reconstruct, so this
    also proves that guard is reachable rather than decorative."""
    import random

    random.seed(11)
    rows = [
        (f"p{p}", op, 10.0 + p * 1.7 + random.gauss(0, 0.5))
        for p in range(6)
        for op in ("A", "B", "C")
        for _ in range(3)
    ]
    result = compute_gage_rr(_ms(rows))
    ss = {row.source: row.ss for row in result.anova}
    assert ss["part"] + ss["operator"] + ss["operator_x_part"] + ss["repeatability"] == pytest.approx(ss["total"])


def test_percentages_are_taken_on_standard_deviations_not_variances():
    """The convention, and the reason the %study-variation column does not
    sum to 100. Computing it on variances instead would make a bad gauge
    look far better than it is."""
    result = compute_gage_rr(HAND)
    grr = _component(result, "gage_rr")
    total = _component(result, "total_variation")
    assert grr.percent_study_variation == pytest.approx(100 * grr.std_dev / total.std_dev)
    assert grr.percent_study_variation != pytest.approx(100 * grr.variance / total.variance)


def test_a_gauge_swamped_by_noise_is_unacceptable():
    import random

    random.seed(3)
    # Parts nearly identical, measurement noise large: the study is looking
    # at the gauge, not the parts.
    rows = [
        (f"p{p}", op, 10.0 + p * 0.01 + random.gauss(0, 2.0))
        for p in range(10)
        for op in ("A", "B", "C")
        for _ in range(3)
    ]
    result = compute_gage_rr(_ms(rows))
    assert result.verdict == "unacceptable"
    assert result.number_of_distinct_categories < 5
    assert any("distinct categories" in w for w in result.warnings)


def test_a_precise_gauge_on_well_spread_parts_is_acceptable():
    import random

    random.seed(5)
    rows = [
        (f"p{p}", op, 10.0 + p * 2.0 + random.gauss(0, 0.05))
        for p in range(10)
        for op in ("A", "B", "C")
        for _ in range(3)
    ]
    result = compute_gage_rr(_ms(rows))
    assert result.verdict == "acceptable"
    assert result.grr_percent_study_variation < GRR_ACCEPTABLE_MAX_PERCENT


def test_negative_variance_components_are_clamped_and_reported():
    """A variance cannot be negative; the ESTIMATOR can be, when the true
    component sits near zero. Clamping silently is standard. Not reporting
    it is how a study that barely resolved anything reads as clean."""
    # Operators identical by construction, so the operator component's raw
    # estimate lands at or below zero.
    rows = []
    for p in range(4):
        for op in ("A", "B"):
            rows += [(f"p{p}", op, 5.0 + p), (f"p{p}", op, 5.0 + p + 0.4)]
    result = compute_gage_rr(_ms(rows), pool_interaction=False)
    operator = _component(result, "operator")
    assert operator.variance >= 0.0
    if operator.clamped_from_negative:
        assert any("negative" in w for w in result.warnings)


def test_interaction_pooling_is_reported_not_hidden():
    """The pooled and unpooled models can give visibly different %GRR, so a
    reader is entitled to know which produced the number."""
    pooled = compute_gage_rr(HAND, pool_interaction=True)
    unpooled = compute_gage_rr(HAND, pool_interaction=False)
    assert pooled.interaction_pooled is True
    assert unpooled.interaction_pooled is False
    assert pooled.grr_percent_study_variation != pytest.approx(unpooled.grr_percent_study_variation)


def test_tolerance_percentage_uses_a_six_sigma_span():
    result = compute_gage_rr(HAND, tolerance=12.0)
    grr_sd = _component(result, "gage_rr").std_dev
    assert result.grr_percent_tolerance == pytest.approx(100 * 6 * grr_sd / 12.0)
    assert result.basis == "tolerance"


def test_verdict_prefers_tolerance_when_one_is_given():
    """Percent of tolerance answers 'can this gauge police the spec', which
    is the question a spec'd part is actually asking."""
    result = compute_gage_rr(HAND, tolerance=1000.0)
    assert result.basis == "tolerance"
    assert result.verdict == "acceptable"  # huge tolerance, tiny GRR against it


def test_single_operator_is_refused_and_points_at_the_honest_alternative():
    rows = [("p1", "A", 1.0), ("p1", "A", 2.0), ("p2", "A", 5.0), ("p2", "A", 6.0)]
    with pytest.raises(GageRRError, match="T-12"):
        compute_gage_rr(_ms(rows))


def test_single_part_is_refused():
    rows = [("p1", "A", 1.0), ("p1", "A", 2.0), ("p1", "B", 1.0), ("p1", "B", 2.0)]
    with pytest.raises(GageRRError, match="at least 2 parts"):
        compute_gage_rr(_ms(rows))


def test_missing_cell_is_refused_by_name():
    rows = [r for r in [("p1", "A", 1.0), ("p1", "A", 2.0), ("p1", "B", 1.0), ("p1", "B", 2.0),
                        ("p2", "A", 5.0), ("p2", "A", 6.0)]]
    with pytest.raises(GageRRError, match="every operator to measure every part"):
        compute_gage_rr(_ms(rows))


def test_unbalanced_replicates_are_refused():
    rows = [("p1", "A", 1.0), ("p1", "A", 2.0), ("p1", "B", 1.0), ("p1", "B", 2.0),
            ("p2", "A", 5.0), ("p2", "A", 6.0), ("p2", "A", 6.5),
            ("p2", "B", 5.0), ("p2", "B", 6.0)]
    with pytest.raises(GageRRError, match="same number of repeat readings"):
        compute_gage_rr(_ms(rows))


def test_one_reading_per_cell_is_refused():
    rows = [("p1", "A", 1.0), ("p1", "B", 2.0), ("p2", "A", 5.0), ("p2", "B", 6.0)]
    with pytest.raises(GageRRError, match="at least twice"):
        compute_gage_rr(_ms(rows))


def test_identical_readings_everywhere_are_refused_rather_than_dividing_by_zero():
    rows = [(f"p{p}", op, 4.0) for p in range(3) for op in ("A", "B") for _ in range(2)]
    with pytest.raises(GageRRError, match="nothing to decompose"):
        compute_gage_rr(_ms(rows))


def test_few_parts_are_flagged():
    rows = [(f"p{p}", op, 1.0 + p + (0.1 if op == "B" else 0.0)) for p in range(3) for op in ("A", "B") for _ in range(2)]
    rows = [(p, o, v + (0.01 * i)) for i, (p, o, v) in enumerate(rows)]
    result = compute_gage_rr(_ms(rows))
    assert any("Fewer than 10" in w for w in result.warnings)


def test_anova_table_carries_every_source_with_its_df():
    result = compute_gage_rr(HAND)
    sources = [row.source for row in result.anova]
    assert sources == ["part", "operator", "operator_x_part", "repeatability", "total"]
    dfs = {row.source: row.df for row in result.anova}
    assert dfs["part"] == 1 and dfs["operator"] == 1 and dfs["operator_x_part"] == 1
    assert dfs["repeatability"] == 4 and dfs["total"] == 7


# ------------------------------------------------- artifact, prescore, report

from sigma_engine.artifacts.gage_rr import GageRRArtifact  # noqa: E402
from sigma_engine.export.reports import gage_rr as grr_report  # noqa: E402
from sigma_engine.prescore.gage_rr import run_gage_rr_prescore  # noqa: E402
from sigma_engine.registry import ARTIFACT_REGISTRY, PRESCORE_REGISTRY  # noqa: E402


def _artifact(rows, **kw) -> GageRRArtifact:
    return GageRRArtifact.model_validate(
        {
            "artifact_id": "gage-rr",
            "tool_id": "T-35",
            "schema_version": 1,
            "created_at": "2026-08-10T00:00:00",
            "updated_at": "2026-08-10T00:00:00",
            "readings": [{"part": p, "operator": o, "value": v} for p, o, v in rows],
            **kw,
        }
    )


HAND_ROWS = [
    ("p1", "A", 1.0), ("p1", "A", 3.0), ("p1", "B", 2.0), ("p1", "B", 4.0),
    ("p2", "A", 5.0), ("p2", "A", 7.0), ("p2", "B", 6.0), ("p2", "B", 8.0),
]


def test_t35_is_registered_everywhere_it_has_to_be():
    """A tool missing from either registry fails at a different layer each
    time -- artifacts save but never prescore, or prescore but never
    export."""
    assert "T-35" in ARTIFACT_REGISTRY
    assert "T-35" in PRESCORE_REGISTRY


def test_artifact_recomputes_and_matches_the_hand_derived_result():
    artifact = _artifact(HAND_ROWS)
    assert artifact.result is not None
    assert artifact.result.grr_percent_study_variation == pytest.approx(100 * math.sqrt(1.7 / 9.3))


def test_a_client_supplied_result_does_not_survive_validation():
    """CopqArtifact.total's contract: server-computed, unconditionally
    replaced, so nobody can post a flattering %GRR."""
    artifact = _artifact(HAND_ROWS)
    tampered = GageRRArtifact.model_validate(
        {**artifact.model_dump(mode="json"), "result": {**artifact.result.model_dump(mode="json"), "grr_percent_study_variation": 1.0}}
    )
    assert tampered.result.grr_percent_study_variation != pytest.approx(1.0)


def test_a_half_entered_study_still_saves_and_says_why_it_cannot_compute():
    """A study is built up over a shift. Refusing to save a partial one
    would make the tool unusable for the way the work actually happens."""
    artifact = _artifact([("p1", "A", 1.0), ("p1", "A", 2.0)])
    assert artifact.result is None
    assert artifact.design_error
    assert "2 parts" in artifact.design_error


def test_prescore_hard_flags_an_unusable_gauge():
    import random

    random.seed(9)
    rows = [
        (f"p{p}", op, 10.0 + p * 0.01 + random.gauss(0, 2.0))
        for p in range(10)
        for op in ("A", "B", "C")
        for _ in range(3)
    ]
    flags = run_gage_rr_prescore(_artifact(rows))
    statuses = {f.check_id: f.status for f in flags}
    assert statuses["grr_verdict"] == "hard_flag"
    assert statuses["grr_ndc"] == "hard_flag"


def test_prescore_catches_a_hand_edited_result(tmp_path):
    """Mirrors prescore/copq.py's safety net: the stored result is recomputed
    from the stored readings, because the load path returns the file as-is."""
    artifact = _artifact(HAND_ROWS)
    edited = artifact.model_copy(
        update={"result": artifact.result.model_copy(update={"grr_percent_study_variation": 1.0})}
    )
    flags = {f.check_id: f for f in run_gage_rr_prescore(edited)}
    assert flags["grr_result_matches_readings"].status == "hard_flag"
    assert "edited outside the app" in flags["grr_result_matches_readings"].detail


def test_report_names_the_basis_beside_the_number():
    """%GRR of study variation and of tolerance answer different questions,
    and a gauge can pass one and fail the other."""
    without = grr_report.build_verdict(_artifact(HAND_ROWS))[0]
    with_tol = grr_report.build_verdict(_artifact(HAND_ROWS, tolerance=100.0))[0]
    assert "of study variation" in without
    assert "of tolerance" in with_tol


def test_report_card_warns_that_the_study_can_only_judge_the_parts_it_was_given():
    """The commonest way a Gage R&R flatters a gauge, and invisible in the
    arithmetic: narrow parts understate part-to-part and so overstate %GRR."""
    card = " ".join(t for _, t in grr_report.build_report_card(_artifact(HAND_ROWS)))
    assert "span the real range of production" in card


def test_report_card_explains_why_the_percentages_do_not_sum_to_100():
    card = " ".join(t for _, t in grr_report.build_report_card(_artifact(HAND_ROWS)))
    assert "standard deviations, not variances" in card


def test_report_renders_a_real_pdf_including_the_anova_table():
    from sigma_engine.export import report_pdf as rp

    artifact = _artifact(HAND_ROWS, tolerance=20.0)
    pdf = rp.render(
        story_builder=lambda w: grr_report.build_story(
            artifact=artifact,
            project_name="P",
            version=1,
            provenance_rows=[("Artifact", "gage-rr")],
            exported_at="2026-08-10 00:00 UTC",
            content_width=w,
        ),
        title="t",
        project_id="p",
        engine_version="0.1.0",
    )
    assert pdf.startswith(b"%PDF-")


def test_report_on_an_uncomputable_study_states_the_reason_rather_than_crashing():
    artifact = _artifact([("p1", "A", 1.0), ("p1", "A", 2.0)])
    text, tone = grr_report.build_verdict(artifact)
    assert tone == "neutral"
    assert "cannot be computed" in text


def test_prescore_check_ids_are_unique():
    """check_id is the identity of a check everywhere downstream -- it keys
    the results strip's pills and their test ids. Emitting one id per
    warning produced collisions the moment a study raised two, which is the
    common case (few parts AND few categories)."""
    import random

    random.seed(9)
    rows = [
        (f"p{p}", op, 10.0 + p * 0.01 + random.gauss(0, 2.0))
        for p in range(4)  # under 10 parts -> a parts warning as well as the ndc one
        for op in ("A", "B", "C")
        for _ in range(3)
    ]
    artifact = _artifact(rows)
    assert len(artifact.result.warnings) >= 2, "this fixture is meant to raise more than one warning"
    ids = [f.check_id for f in run_gage_rr_prescore(artifact)]
    assert len(ids) == len(set(ids))
    assert "grr_warnings" in ids


def test_report_card_states_one_clamp_once():
    """reproducibility and gage_rr are SUMS that inherit the clamp flag from
    `operator`. Iterating every component printed one event two or three
    times in near-identical words, reading as several separate problems."""
    # Operators identical, parts far apart: the operator variance estimator
    # goes negative and is floored, which is the clamp under test.
    rows = [
        (f"p{p}", op, p * 10.0 + trial * 0.1)
        for p in range(1, 4)
        for op in ("A", "B", "C")
        for trial in range(3)
    ]
    artifact = _artifact(rows)
    clamped = [c.name for c in artifact.result.components if c.clamped_from_negative]
    assert "operator" in clamped and "reproducibility" in clamped, "fixture must clamp a sum and its cause"
    card = [text for _, text in grr_report.build_report_card(artifact)]
    assert sum(1 for text in card if "floored at zero" in text) == 1


def test_the_chart_series_matches_the_order_the_client_draws():
    """The engine hashes this series and refuses any chart image whose
    fingerprint disagrees. If the two sides order the bars differently the
    hashes never match, the picture is silently dropped from every report,
    and nothing else fails -- so the orders are pinned against each other
    here, by reading the client's own constant."""
    import pathlib
    import re as _re

    from sigma_engine.routes.export import GRR_CHART_COMPONENT_ORDER, _grr_chart_series

    logic = pathlib.Path(__file__).resolve().parents[2] / "desktop" / "src" / "tools" / "gagerr" / "gageRrLogic.ts"
    source = logic.read_text()
    match = _re.search(r"CHART_COMPONENT_ORDER = \[([^\]]+)\]", source)
    assert match, "client CHART_COMPONENT_ORDER not found -- did gageRrLogic.ts move?"
    client_order = tuple(_re.findall(r'"([^"]+)"', match.group(1)))
    assert client_order == GRR_CHART_COMPONENT_ORDER

    # And the series the engine hashes is exactly those four, then the same
    # four again as %tolerance when the study has a tolerance.
    artifact = _artifact(HAND_ROWS)
    assert len(_grr_chart_series(artifact)) == len(GRR_CHART_COMPONENT_ORDER)
    with_tolerance = _artifact(HAND_ROWS, tolerance=20.0)
    assert len(_grr_chart_series(with_tolerance)) == 2 * len(GRR_CHART_COMPONENT_ORDER)


def test_a_study_that_cannot_be_computed_has_no_chart_to_verify():
    """None means "nothing to compare against" and check_chart then takes
    the image on trust. A half-entered study has no components at all, so
    it must return None rather than raising on the missing result."""
    from sigma_engine.routes.export import _grr_chart_series

    assert _grr_chart_series(_artifact([("p1", "A", 1.0), ("p1", "A", 2.0)])) is None


def test_every_tested_anova_row_carries_a_p_value():
    """An F with an empty p column beside it is not a test a reader can
    use. part and operator both had F statistics and neither had a p --
    the denominator's degrees of freedom were never carried to compute one."""
    result = compute_gage_rr(
        [
            Measurement(part=f"p{p}", operator=op, value=p * 2.0 + (0.3 if op == "B" else 0.0) + trial * 0.1)
            for p in range(1, 6)
            for op in ("A", "B")
            for trial in range(3)
        ]
    )
    rows = {row.source: row for row in result.anova}
    for source in ("part", "operator", "operator_x_part"):
        assert rows[source].f_statistic is not None, source
        assert rows[source].p_value is not None, source
        assert 0.0 <= rows[source].p_value <= 1.0
    # repeatability and total are not tests -- nothing to test them against.
    assert rows["repeatability"].p_value is None
    assert rows["total"].p_value is None


def test_the_f_denominator_follows_the_pooling_decision():
    """Parts and operators are random effects: unpooled, their error term
    is the INTERACTION mean square, not the residual. Pooling changes the
    denominator, and so must change F -- if it did not, one of the two
    models would be using the wrong error term."""
    rows = [
        Measurement(part=f"p{p}", operator=op, value=p * 2.0 + (0.4 if op == "B" else 0.0) + trial * 0.1)
        for p in range(1, 6)
        for op in ("A", "B")
        for trial in range(3)
    ]
    pooled = {r.source: r for r in compute_gage_rr(rows, pool_interaction=True).anova}
    kept = {r.source: r for r in compute_gage_rr(rows, pool_interaction=False).anova}
    assert pooled["part"].f_statistic != kept["part"].f_statistic
    # Same SS and MS either way -- only the test around them moves.
    assert pooled["part"].ms == pytest.approx(kept["part"].ms)
