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
# Group D — the form-shaped four. T-03 Charter keeps its own hand-laid PDF.
GROUP_D = ("T-01", "T-11", "T-19", "T-24")
GROUP_CD = GROUP_C + GROUP_D


def test_every_group_c_and_d_tool_has_a_report_registered():
    for tool_id in GROUP_CD:
        assert tool_id in ARTIFACT_REPORTS, tool_id


def test_every_group_c_report_exposes_the_five_zone_contract():
    """build_story is what the route calls; the other three are what make a
    report a report rather than a data dump. A module missing one of them
    fails at request time, on a route with no per-tool test."""
    for tool_id in GROUP_CD:
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


# ------------------------------------------------------------------- group D


def test_pilot_plan_does_not_punish_a_correctly_declared_package():
    """The tool has a first-class concept for bundling changes on purpose --
    declared_package, with a rationale and a server-stamped attribution
    note -- and the schema REFUSES more than one change without it
    (EXIT-10). So a multi-change plan that reaches a report is by
    construction the honest path being used correctly, and an earlier
    version of this report flagged it as a mistake."""
    from sigma_engine.export.reports import pilot_plan as pilot_report

    bundled = _pilot(change_count=2, declared_package=True)
    text, tone = pilot_report.build_verdict(bundled)
    assert tone == "pass"
    assert "declared package" in text.lower()


def test_more_than_one_change_without_a_package_never_reaches_a_report():
    """Pinned because the report's wording depends on it: the "undeclared
    multi-change" case is unreachable, so the page does not need -- and must
    not have -- a scolding branch for it."""
    with pytest.raises(Exception) as caught:
        _pilot(change_count=2, declared_package=False)
    assert "EXIT-10" in str(caught.value)


def test_pilot_plan_prints_the_falsification_line_beside_the_success_line():
    """Printing only the success half is what makes a pilot unfalsifiable in
    practice: with no result that would have counted as failure, any outcome
    can be narrated as a win."""
    from sigma_engine.export.reports import pilot_plan as pilot_report

    text = _story_text(pilot_report, _pilot(change_count=1, declared_package=False))
    assert "FAILURE MEANS" in text.upper()
    assert "SUCCESS MEANS" in text.upper()


def test_collection_plan_names_which_part_of_the_definition_is_missing():
    """A prose definition reads as complete and hides the gap. Naming the
    missing part is the whole value of splitting it into fields."""
    from sigma_engine.export.reports import data_collection_plan as dcp_report

    artifact = _collection_plan(stops_when="")
    text, tone = dcp_report.build_verdict(artifact)
    assert tone == "fail"
    assert "clock stops when" in text.lower()


def test_collection_plan_treats_unstratified_with_no_reason_as_a_failure():
    """Not recoverable later: data collected without a factor can never be
    split by it afterwards."""
    from sigma_engine.export.reports import data_collection_plan as dcp_report

    card = dcp_report.build_report_card(_collection_plan(strata=[], no_strata_reason=""))
    assert any(tone == "fail" and "stratification" in text.lower() for tone, text in card)

    card = dcp_report.build_report_card(_collection_plan(strata=[], no_strata_reason="single barista, single till"))
    assert not any(tone == "fail" and "stratification" in text.lower() for tone, text in card)


def test_standard_work_catches_a_standard_that_just_restates_the_action():
    """SOPs fail most often by merging "what you do" with "what right looks
    like" -- and a step whose standard echoes its action is that failure
    made machine-visible."""
    from sigma_engine.export.reports import standard_work as sop_report

    card = sop_report.build_report_card(_sop(standard_echoes_action=True))
    assert any(tone == "fail" and "identical to the action" in text for tone, text in card)


def test_standard_work_escapes_a_step_containing_markup_characters():
    """A spec like "<0.5 mm" is entirely plausible in an SOP step, and
    building the cell's markup before escaping breaks the Paragraph parse
    rather than printing."""
    from sigma_engine.export.reports import standard_work as sop_report

    artifact = _sop(action="Trim to <0.5 mm & deburr", note="see drawing <A-12>")
    pdf = report_pdf.render(
        story_builder=lambda w: sop_report.build_story(
            artifact=artifact, project_name="P", version=1,
            provenance_rows=[("Artifact", "sop")], exported_at="x", content_width=w,
        ),
        title="t", project_id="p", engine_version="0.1.0",
    )
    assert pdf.startswith(b"%PDF-")


def test_picker_names_the_failed_criterion_rather_than_just_refusing():
    """"Not viable as scoped" invites a rescope that changes nothing. The
    sponsor needs to know which of the five failed, in their own words."""
    from sigma_engine.export.reports import picker as picker_report

    artifact = _picker(failing="measurable_outcome", detail="we want it to feel faster")
    text, tone = picker_report.build_verdict(artifact)
    assert tone == "fail"
    assert "measurable" in text.lower()
    card = " ".join(t for _, t in picker_report.build_report_card(artifact))
    assert "we want it to feel faster" in card


def _pilot(*, change_count: int, declared_package: bool):
    from sigma_engine.artifacts.pilot_plan import PilotPlanArtifact

    # The schema pins the_one_change.statement to changes[0].text -- the one
    # declared change cannot read two ways in the same artifact.
    first = "change the grinder routine"
    changes = [{"change_id": "chg-1", "text": first}] + [
        {"change_id": f"chg-{i}", "text": f"additional change number {i}"} for i in range(2, change_count + 1)
    ]
    body = {
        "schema_version": 1, "artifact_id": "pilot-plan", "tool_id": "T-19",
        "created_at": "2026-08-10T00:00:00Z", "updated_at": "2026-08-10T00:00:00Z",
        "the_one_change": {"statement": first, "linked_cause_ids": ["c1"]},
        "changes": changes,
        "comparison_design": {"kind": "before_period", "description": "same peak window, prior 10 mornings"},
        "inclusion": {"who_or_what": "weekday peak espresso orders", "how_selected": "every order in the 7-10 window",
                      "honesty_note": "one site only, chosen because the owner agreed"},
        "success_threshold": {"metric_ref": "handoff_minutes", "direction": "lower_is_better", "value": 5.5,
                              "declared_at": "2026-09-03T15:00:00Z"},
        "analysis_plan": {"expected_route": "two-sample t-test", "rationale": "continuous data, two independent windows"},
        "falsification_line": "if the pilot-window mean is not below 5.5 minutes, the change did not work",
        "confounder_checklist": {
            "staffing": {"changed": True, "note": "one barista off sick in week two"},
            "season": {"changed": False},
            "demand": {"changed": False},
            "measurement": {"changed": False},
            "other": {"changed": False},
        },
    }
    if declared_package:
        body["declared_package"] = {
            "components": [c["text"] for c in changes],
            "rationale": "the two only work together",
        }
    return PilotPlanArtifact.model_validate(body)


def _collection_plan(*, stops_when: str = "cup reaches the handoff counter", strata=None, no_strata_reason: str = ""):
    from sigma_engine.artifacts.data_collection_plan import DataCollectionPlanArtifact

    return DataCollectionPlanArtifact.model_validate(
        {
            "schema_version": 1, "artifact_id": "collection-plan", "tool_id": "T-11",
            "created_at": "2026-08-10T00:00:00Z", "updated_at": "2026-08-10T00:00:00Z",
            "metric_name": "order-to-handoff time",
            "operational_definition": {
                "what_measured": "minutes from order paid to cup handed over",
                "how_instrument": "POS timestamp",
                "precision_unit": "tenths of a minute",
                "starts_when": "order is paid",
                "stops_when": stops_when,
                "two_people_confirmed": True,
            },
            "data_type": "continuous",
            "stratification_factors": [{"name": s} for s in (strata if strata is not None else ["shift"])],
            "no_stratification_reason": no_strata_reason,
            "logistics": {"who_collects": "Marcus", "where_collected": "front counter",
                          "when_how_often": "every 4th order at peak", "planned_n": 120,
                          "sample_size_rationale": "rule of thumb for an I-MR baseline"},
        }
    )


def _sop(*, standard_echoes_action: bool = False, action: str = "Dial in the grinder", note: str = ""):
    from sigma_engine.artifacts.standard_work import StandardWorkArtifact

    standard = action if standard_echoes_action else "shot pulls 25-29 s at 36 g out"
    return StandardWorkArtifact.model_validate(
        {
            "schema_version": 1, "artifact_id": "sop", "tool_id": "T-24",
            "created_at": "2026-08-10T00:00:00Z", "updated_at": "2026-08-10T00:00:00Z",
            "title": "Espresso dial-in", "version": 1, "owner": "Marcus Webb",
            "effective_date": "2026-09-22",
            "steps": [{"step_id": "s1", "order": 1, "action": action, "standard": standard, "note": note}],
        }
    )


def _picker(*, failing: str, detail: str):
    from sigma_engine.artifacts.picker import PickerArtifact

    fields = ("scope_narrow", "measurable_outcome", "data_obtainable",
              "process_owner_engaged", "business_impact_plausible")
    body = {
        "schema_version": 1, "artifact_id": "picker", "tool_id": "T-01",
        "created_at": "2026-08-10T00:00:00Z", "updated_at": "2026-08-10T00:00:00Z",
        "route": "EXIT-01",
    }
    for field in fields:
        if field == failing:
            body[field] = {"answer": False, "detail": detail}
        else:
            body[field] = {"answer": True, "detail": "fine"}
    return PickerArtifact.model_validate(body)


def test_pilot_plan_actually_reports_the_confounders_that_were_ticked():
    """The checklist holds ConfounderAnswer objects, not bare booleans. An
    earlier version dumped to JSON and tested `value is True` -- never true
    for a dict -- so this line silently never printed on a page whose whole
    argument is that naming confounders in advance is what separates a
    limitation from an excuse."""
    from sigma_engine.export.reports import pilot_plan as pilot_report

    card = pilot_report.build_report_card(_pilot(change_count=1, declared_package=False))
    acknowledged = [text for tone, text in card if "confounder(s) acknowledged" in text]
    assert acknowledged, "a ticked confounder must reach the report card"
    assert "staffing" in acknowledged[0]
    assert "off sick" in acknowledged[0]


# ------------------------------------------------------------------- group B

GROUP_B = ("T-04", "T-05", "T-06", "T-07", "T-15")


def test_every_group_b_tool_has_a_report_with_the_five_zone_contract():
    for tool_id in GROUP_B:
        assert tool_id in ARTIFACT_REPORTS, tool_id
        _, module, _ = ARTIFACT_REPORTS[tool_id]
        for name in ("TOOL_ID", "TOOL_TITLE", "build_story", "build_verdict", "build_meaning", "build_report_card"):
            assert hasattr(module, name), f"{tool_id} report is missing {name}"


def test_the_canvas_reports_ask_for_a_chart_and_the_others_do_not():
    """T-06, T-07 and T-15 are drawings -- the picture IS the deliverable,
    so their route entry must request a capture. A report whose wants_chart
    is False silently prints without its diagram and still passes as a
    valid PDF, which is the failure that looks like success."""
    for tool_id in ("T-06", "T-07", "T-15"):
        _, _, wants_chart = ARTIFACT_REPORTS[tool_id]
        assert wants_chart is True, f"{tool_id} is a diagram report and must request its capture"
    for tool_id in ("T-04", "T-05"):
        _, _, wants_chart = ARTIFACT_REPORTS[tool_id]
        assert wants_chart is False, f"{tool_id} has no canvas to capture"


def test_a_canvas_report_says_the_picture_is_missing_rather_than_omitting_it():
    """The reader has to be able to tell "no diagram was captured" from
    "this process has no diagram"."""
    from sigma_engine.export.reports import process_map as pm_report

    text = _flatten(
        pm_report.build_story(
            artifact=_process_map(), project_name="P", version=1,
            chart_png=None, chart_unavailable_reason="Chart not captured — open this tool's screen.",
            provenance_rows=[("Artifact", "process-map")], exported_at="x", content_width=400.0,
        )
    )
    assert "not captured" in text


def test_process_map_prints_waste_names_not_python_reprs():
    """A duck-typed getattr(w, "kind", w) fell through to str(w) on the
    model and printed "waste id='waiting' note='...'" onto a page a
    supervisor reads. The field is waste_id and it is a Literal."""
    from sigma_engine.export.reports import process_map as pm_report

    table_text = _table_text(pm_report.build_steps_table(_process_map(), rt.report_styles(), 400.0))
    assert "Waiting" in table_text
    assert "waste_id" not in table_text
    assert "note=" not in table_text


def test_a_verified_cause_cannot_be_saved_without_evidence():
    """Pinned because the report's wording depends on it: the guard lives in
    the schema, which is the strongest place for it, so the page reports the
    known-versus-suspected split rather than lecturing about a state the
    tool refuses to create."""
    with pytest.raises(Exception) as caught:
        _fishbone(verified_with_evidence=False)
    assert "evidence is required" in str(caught.value)


def test_fishbone_leads_with_how_much_is_known_versus_suspected():
    from sigma_engine.export.reports import fishbone as fb_report

    text, tone = fb_report.build_verdict(_fishbone(verified_with_evidence=True))
    assert tone == "pass"
    assert "verified with evidence" in text


def test_fishbone_resolves_evidence_to_words_rather_than_ids():
    """"ds-4a2f" beside a verified cause is a promise that evidence exists,
    not evidence."""
    from sigma_engine.export.reports import fishbone as fb_report

    text = _flatten(
        fb_report.build_story(
            artifact=_fishbone(verified_with_evidence=True), project_name="P", version=1,
            provenance_rows=[("Artifact", "fishbone")], exported_at="x", content_width=400.0,
        )
    )
    assert "dataset" in text
    assert "ds-4a2f" in text  # the ref still prints -- resolved means labelled, not hidden


def _process_map():
    from sigma_engine.artifacts.process_map import ProcessMapArtifact

    return ProcessMapArtifact.model_validate(
        {
            "schema_version": 1, "artifact_id": "process-map", "tool_id": "T-06",
            "created_at": "2026-08-10T00:00:00Z", "updated_at": "2026-08-10T00:00:00Z",
            "lanes": [{"lane_id": "l1", "name": "Front counter"}],
            "steps": [
                {"step_id": "s1", "lane_id": "l1", "name": "Take the order", "order": 1,
                 "step_type": "enabling", "time_minutes": 0.8},
                {"step_id": "s2", "lane_id": "l1", "name": "Cup waits", "order": 2,
                 "step_type": "non_value_add", "time_minutes": 4.5,
                 "wastes": [{"waste_id": "waiting", "note": "cups sit in the queue"}]},
                {"step_id": "s3", "lane_id": "l1", "name": "Make the drink", "order": 3,
                 "step_type": "value_add", "time_minutes": 2.0},
            ],
        }
    )


def _fishbone(*, verified_with_evidence: bool):
    from sigma_engine.artifacts.fishbone import FishboneArtifact

    cause = {
        "cause_id": "c1", "branch": "machine", "text": "grinder drifts mid-peak", "status": "verified",
    }
    if verified_with_evidence:
        cause["evidence"] = {"kind": "dataset", "ref": "ds-4a2f"}
    return FishboneArtifact.model_validate(
        {
            "schema_version": 1, "artifact_id": "fishbone", "tool_id": "T-15",
            "created_at": "2026-08-10T00:00:00Z", "updated_at": "2026-08-10T00:00:00Z",
            "effect": {"text": "orders take too long at peak"},
            "causes": [cause, {"cause_id": "c2", "branch": "method", "text": "no dial-in routine", "status": "candidate"}],
        }
    )
