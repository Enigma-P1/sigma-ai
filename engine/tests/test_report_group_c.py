"""Group C reports — the table-shaped ones (T-02, T-08, T-09, T-10, T-18, T-22, T-23).

These share one failure mode and it is not arithmetic. Every artifact
behind them carries unbounded free text, and a report table is a fixed
grid: ReportLab splits BETWEEN rows and never within one, so a cell taller
than the frame forces a page break and then overflows anyway. The worked
example's control plan carried a 400-character sampling rationale in its
"how often" field, which on its own turned one row into a full page of
eight-character-wide columns and pushed the table off page one entirely.

So the tests here are mostly about shape, not sums.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from sigma_engine.export import report_pdf, report_theme as rt
from sigma_engine.export.reports import control_plan as cp_report
from sigma_engine.export.reports import copq as copq_report
from sigma_engine.export.reports import five_s as five_s_report
from sigma_engine.export.reports import yield_calc as yield_report
from sigma_engine.routes.export import ARTIFACT_REPORTS

GROUP_C = ("T-02", "T-08", "T-09", "T-10", "T-18", "T-22", "T-23")


def test_every_group_c_tool_has_a_report_registered():
    for tool_id in GROUP_C:
        assert tool_id in ARTIFACT_REPORTS, tool_id


def test_every_group_c_report_exposes_the_five_zone_contract():
    """build_story is what the route calls; the other three are what make a
    report a report rather than a data dump. A module missing one of them
    fails at request time, on a route with no per-tool test."""
    for tool_id in GROUP_C:
        _, module, _ = ARTIFACT_REPORTS[tool_id]
        for name in ("TOOL_ID", "TOOL_TITLE", "build_story", "build_verdict", "build_meaning", "build_report_card"):
            assert hasattr(module, name), f"{tool_id} report is missing {name}"


# ------------------------------------------------------------------ clipping


def test_clip_cuts_on_a_word_boundary_and_marks_the_cut():
    text = "Register order-paid timestamp to name call, tenths of a minute, every fourth espresso order"
    out = rt.clip(text, 40)
    assert len(out) <= 40
    assert out.endswith("…")
    # No mid-word truncation: the last real word survives whole.
    assert out.rstrip("…").split()[-1] in text.split()


def test_clip_leaves_short_text_completely_alone():
    assert rt.clip("Daily at close of peak", 45) == "Daily at close of peak"
    assert not rt.clip("Daily at close of peak", 45).endswith("…")


def test_clip_collapses_whitespace_so_a_pasted_paragraph_cannot_blow_a_row():
    assert rt.clip("a\n\n  b\tc", 40) == "a b c"


def test_the_control_plan_keeps_the_rationale_but_not_in_the_grid():
    """The fix for the 400-character cell was NOT to delete the reason --
    it is the most useful sentence on the page for anyone deciding whether
    the frequency is keepable. It moved out of the table."""
    long_reason = "because " + "the sampling rationale runs on and on " * 12
    artifact = _control_plan(frequency_reason=long_reason)

    table_text = _table_text(cp_report.build_items_table(artifact, rt.report_styles(), 400.0))
    assert "sampling rationale" not in table_text

    story_text = _story_text(cp_report, artifact)
    assert "sampling rationale" in story_text
    assert "WHY THESE FREQUENCIES" in story_text


def test_the_control_plan_does_not_badge_a_ctq_that_already_says_so():
    artifact = _control_plan(characteristic="Order-to-handoff time (the primary CTQ)")
    table_text = _table_text(cp_report.build_items_table(artifact, rt.report_styles(), 400.0))
    assert table_text.count("primary CTQ") == 1


def test_an_essay_in_every_field_still_renders_a_short_document():
    """The regression that started this: one row per page, and the table
    pushed off page one entirely."""
    essay = "words that go on " * 60
    artifact = _control_plan(
        characteristic=essay, how_measured=essay, where=essay, frequency=essay, frequency_reason=essay
    )
    pdf = report_pdf.render(
        story_builder=lambda w: cp_report.build_story(
            artifact=artifact, project_name="P", version=1,
            provenance_rows=[("Artifact", "control-plan")], exported_at="x", content_width=w,
        ),
        title="t", project_id="p", engine_version="0.1.0",
    )
    assert pdf.startswith(b"%PDF-")
    assert pdf.count(b"/Type /Page\n") <= 3, "a table of clipped cells should not run to a document"


# ---------------------------------------------------------------- judgements


def test_copq_calls_a_total_containing_estimates_an_estimate():
    """A dollar figure is the most portable thing this app produces: it gets
    lifted into a slide and repeated by someone who never saw how it was
    built. The label rides on the headline for that reason."""
    artifact = _copq(estimate_amounts=[100.0], measured_amounts=[153.0])
    text, tone = copq_report.build_verdict(artifact)
    assert rt.LABELS["estimate"] in text
    assert tone == "flag"
    # The split is stated in money, not in row counts -- three estimated rows
    # worth $12 and one measured row worth $180,000 is not "75% estimated".
    assert "$100" in text


def test_copq_with_no_estimates_makes_no_estimate_claim():
    artifact = _copq(estimate_amounts=[], measured_amounts=[253.0])
    text, tone = copq_report.build_verdict(artifact)
    assert rt.LABELS["estimate"] not in text
    assert tone == "neutral"


def test_yield_report_names_the_convention_beside_the_sigma_level():
    """The same process reads ~1.5 sigma different on the other convention,
    and quoting the flattering one unlabelled is this number's classic
    abuse."""
    artifact = _yield_with_dpmo()
    card = " ".join(text for _, text in yield_report.build_report_card(artifact))
    assert "convention" in card
    story_text = _story_text(yield_report, artifact)
    assert "shift" in story_text.lower()


def test_five_s_does_not_fail_a_mid_scale_sustain_that_is_improving():
    """A flat pass/fail split called Sustain 3/5 a FAILURE on an area that
    had climbed 10 -> 15 -> 18 with Sustain itself rising 2 -> 3. A verdict
    that harsh on visible progress teaches people to ignore verdicts."""
    artifact = _five_s(sustain_history=[2, 3])
    tones = {text: tone for tone, text in five_s_report.build_report_card(artifact)}
    sustain_items = [(t, txt) for txt, t in tones.items() if "Sustain is" in txt]
    assert sustain_items, "the Sustain read must always print"
    tone, text = sustain_items[0]
    assert tone == "flag"
    assert "moved from 2 to 3" in text


def test_five_s_still_fails_a_genuinely_low_sustain():
    artifact = _five_s(sustain_history=[1, 1])
    tones = [(tone, text) for tone, text in five_s_report.build_report_card(artifact) if "Sustain is" in text]
    assert tones and tones[0][0] == "fail"


# ------------------------------------------------------------------ fixtures


def _flatten(flowables) -> str:
    out: list[str] = []
    for flowable in flowables:
        if hasattr(flowable, "getPlainText"):
            out.append(flowable.getPlainText())
        elif hasattr(flowable, "_cellvalues"):
            for row in flowable._cellvalues:
                for cell in row:
                    out.append(cell if isinstance(cell, str) else _flatten([cell]))
        elif hasattr(flowable, "_content"):
            out.append(_flatten(flowable._content))
    return " ".join(str(o) for o in out)


def _table_text(table) -> str:
    return _flatten([table])


def _story_text(module, artifact) -> str:
    return _flatten(
        module.build_story(
            artifact=artifact, project_name="P", version=1,
            provenance_rows=[("Artifact", "a")], exported_at="x", content_width=400.0,
        )
    )


def _control_plan(**overrides):
    from sigma_engine.artifacts.control_plan import ControlPlanArtifact

    item = {
        "item_id": "i1",
        "characteristic": overrides.get("characteristic", "Order-to-handoff time"),
        "how_measured": overrides.get("how_measured", "POS timestamp"),
        "where": overrides.get("where", "Front counter"),
        "frequency": overrides.get("frequency", "Daily at close"),
        "frequency_reason": overrides.get("frequency_reason", "peak volume lands in one window"),
        "is_primary_ctq": True,
        "owner_name": "Priya Shah",
        "owner_accepted": True,
    }
    return ControlPlanArtifact.model_validate(
        {
            "schema_version": 1, "artifact_id": "control-plan", "tool_id": "T-22",
            "created_at": "2026-08-10T00:00:00Z", "updated_at": "2026-08-10T00:00:00Z",
            "monitored_items": [item],
            "ocap_entries": [
                {"ocap_id": "o1", "monitored_item_id": "i1", "trigger_signal": "point beyond the band",
                 "action_steps": ["check the grinder"], "escalation_contact": "Marcus"}
            ],
            "as_of": "2026-08-10T00:00:00Z",
        }
    )


def _copq(*, estimate_amounts: list[float], measured_amounts: list[float]):
    from sigma_engine.artifacts.copq import CopqArtifact

    rows = [
        {"category": "scrap", "quantity": amount, "rate": 1.0, "period": "Q2 2026",
         "basis": "Q2 scrap log export, line 14", "is_estimate": False}
        for amount in measured_amounts
    ] + [
        {"category": "lost_business", "quantity": amount, "rate": 1.0, "period": "Q2 2026",
         "basis": "estimate from operator interview", "is_estimate": True}
        for amount in estimate_amounts
    ]
    return CopqArtifact.model_validate(
        {
            "schema_version": 1, "artifact_id": "copq", "tool_id": "T-02",
            "created_at": "2026-08-10T00:00:00Z", "updated_at": "2026-08-10T00:00:00Z",
            "rows": rows,
        }
    )


def _yield_with_dpmo():
    from sigma_engine.artifacts.yield_calc import YieldCalcArtifact

    return YieldCalcArtifact.model_validate(
        {
            "schema_version": 1, "artifact_id": "yieldcalc", "tool_id": "T-10",
            "created_at": "2026-08-10T00:00:00Z", "updated_at": "2026-08-10T00:00:00Z",
            "steps": [
                {"name": "print", "units_in": 1000, "first_pass_correct": 950},
                {"name": "trim", "units_in": 950, "first_pass_correct": 930},
            ],
            "steps_in_series": True,
            "dpmo_block": {
                "defects": 70, "units": 1000, "opportunities_per_unit": 2.0,
                "opportunity_justification": "two named first-presentation checks",
                "apply_sigma_shift": True,
            },
        }
    )


def _five_s(*, sustain_history: list[int]):
    from sigma_engine.artifacts.five_s import FiveSArtifact

    rounds = []
    for index, sustain in enumerate(sustain_history):
        rounds.append(
            {
                "round_id": f"r{index}",
                "date": f"2026-09-{10 + index * 7:02d}",
                "area": "Espresso station",
                "scores": [
                    {"category": "sort", "score": 4},
                    {"category": "set_in_order", "score": 4},
                    {"category": "shine", "score": 4},
                    {"category": "standardize", "score": 3},
                    {"category": "sustain", "score": sustain},
                ],
                "improvement_action": "fix the dial-in log",
                "improvement_action_owner": "Marcus Webb",
            }
        )
    return FiveSArtifact.model_validate(
        {
            "schema_version": 1, "artifact_id": "five-s", "tool_id": "T-23",
            "created_at": "2026-08-10T00:00:00Z", "updated_at": "2026-08-10T00:00:00Z",
            "rounds": rounds,
        }
    )
