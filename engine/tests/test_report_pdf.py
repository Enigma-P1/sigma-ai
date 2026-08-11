"""Per-tool report layer: the shared frame, the chart gate, and the two
Phase-1 reports (T-13 Capability, T-16 FMEA).

Asserts against built flowables rather than parsed PDF bytes, matching
test_charter_pdf.py and test_project_pdf.py: no pypdf dependency, and a
failure names the wrong content instead of showing a binary diff.
"""

from __future__ import annotations

import json
import re
import subprocess

import pytest
from fastapi.testclient import TestClient

from sigma_engine.artifacts.fmea import FmeaArtifact
from sigma_engine.export import report_pdf, report_theme
from sigma_engine.export.reports import capability as cap
from sigma_engine.export.reports import fmea as fmea_report
from sigma_engine.main import app
from sigma_engine.stats.baseline import run_baseline


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


# A stable, deliberately-terrible process: predictable and nowhere near the
# 5.0 spec. Mirrors the Coffee Bar shape that makes the teaching point.
STABLE_BAD = [8.0 + (i % 7) * 0.1 for i in range(60)]
CAPABLE = [4.0 + (i % 5) * 0.02 for i in range(60)]


# ---------------------------------------------------------------- chart gate


def test_chart_absent_is_reported_not_silently_dropped():
    png, reason = report_pdf.check_chart(None, None, "abc")
    assert png is None
    assert "not captured" in reason


def test_chart_with_matching_hash_is_used():
    png, reason = report_pdf.check_chart(b"PNGDATA", "abc", "abc")
    assert png == b"PNGDATA"
    assert reason is None


def test_chart_with_mismatched_hash_is_refused_with_a_reason():
    """The whole point of the gate: a picture drawn from different data must
    never appear under a footer claiming the engine produced the page."""
    png, reason = report_pdf.check_chart(b"PNGDATA", "stale-hash", "fresh-hash")
    assert png is None
    assert "different data" in reason


def test_chart_is_taken_on_trust_when_there_is_nothing_to_check_against():
    png, reason = report_pdf.check_chart(b"PNGDATA", None, None)
    assert png == b"PNGDATA"
    assert reason is None


def test_fingerprint_is_stable_and_order_sensitive():
    assert report_pdf.data_fingerprint([1, 2, 3]) == report_pdf.data_fingerprint([1, 2, 3])
    assert report_pdf.data_fingerprint([1, 2, 3]) != report_pdf.data_fingerprint([3, 2, 1])


def test_fingerprint_matches_javascript_byte_for_byte():
    """Cross-language pin.

    The client hashes JSON.stringify(values); the engine hashes json.dumps.
    Those agree on everything EXCEPT whole floats -- Python writes 5.0 where
    JavaScript writes 5 -- so the engine normalises. Without this test the
    mismatch is invisible until a dataset happens to contain a round number,
    at which point every chart silently vanishes from every report and the
    pages still look complete.
    """
    values = [5, 4.8, 8.408333333333333, 0, -1.5, 120, 3.0]
    script = (
        "const c=require('crypto');"
        f"const v={json.dumps([5, 4.8, 8.408333333333333, 0, -1.5, 120, 3.0])};"
        "process.stdout.write(c.createHash('sha256').update(JSON.stringify(v)).digest('hex'));"
    )
    try:
        js_hash = subprocess.run(
            ["node", "-e", script], capture_output=True, text=True, timeout=30, check=True
        ).stdout.strip()
    except (FileNotFoundError, subprocess.SubprocessError) as exc:  # pragma: no cover
        pytest.skip(f"node unavailable for the cross-language check: {exc}")
    assert report_pdf.data_fingerprint(values) == js_hash


# -------------------------------------------------------------- capability


def _baseline(data, **kw):
    return run_baseline(data, operational_definition_ok=True, **kw)


def test_stable_but_incapable_states_both_findings_separately():
    """The product's best teaching moment, and the one most easily lost by
    collapsing stability and capability into a single verdict."""
    result = _baseline(STABLE_BAD, usl=5.0)
    text, tone = cap.build_verdict(result)
    assert tone == "fail"
    assert "stable" in text.lower()
    assert "cannot meet the specification" in text
    meaning = cap.build_meaning(result)
    assert "predictable" in meaning
    assert "not tighter" in meaning or "not move a stable process" in meaning


def test_capable_process_reads_as_a_pass():
    result = _baseline(CAPABLE, usl=5.0, lsl=3.0)
    _, tone = cap.build_verdict(result)
    assert tone == "pass"


def test_no_spec_limits_does_not_invent_a_capability_claim():
    """With no spec limits the engine's own gate refuses the baseline before
    capability is even reached, and the report prints that gate message
    verbatim rather than inventing a softer one. Asserting the real message
    matters: an earlier version of this test asserted wording from a branch
    the gate makes unreachable, so it would have passed while saying nothing
    about what a user sees."""
    result = _baseline(STABLE_BAD)
    text, tone = cap.build_verdict(result)
    assert tone == "neutral"
    assert "spec limit" in text
    assert result.gate_ok is False


def test_report_card_reports_normality_from_the_real_field():
    """Regression. NormalityResult carries `advisory` and `p_band`, not a
    boolean `normal`; the first cut read `.normal` through getattr with a
    None default, so the normality line silently disappeared from every
    report while the page still looked finished."""
    result = _baseline(STABLE_BAD, usl=5.0)
    card = " ".join(text for _, text in cap.build_report_card(result))
    assert "Distribution shape" in card
    assert "p p" not in card  # the p_band already reads "p >= 0.15"


def test_report_card_carries_sample_size_and_stability():
    card = cap.build_report_card(_baseline(STABLE_BAD, usl=5.0))
    joined = " ".join(t for _, t in card)
    assert "Sample size: 60" in joined
    assert "Stability" in joined


def test_capability_story_renders_without_a_chart():
    result = _baseline(STABLE_BAD, usl=5.0)
    story = cap.build_story(
        result=result,
        project_name="P",
        chart_png=None,
        chart_unavailable_reason="Chart not captured — test",
        provenance_rows=[("Dataset", "d1")],
        exported_at="2026-08-10 00:00 UTC",
        content_width=480.0,
    )
    text = _flatten(story)
    assert "Process Capability" in text
    assert "Chart not captured" in text
    assert "PROVENANCE" in text
    assert "2026-08-10 00:00 UTC" in text


# --------------------------------------------------------------------- FMEA


def _fmea(rows: list[dict]) -> FmeaArtifact:
    return FmeaArtifact.model_validate(
        {
            "artifact_id": "fmea",
            "tool_id": "T-16",
            "schema_version": 1,
            "created_at": "2026-08-01T00:00:00",
            "updated_at": "2026-08-01T00:00:00",
            "rows": rows,
        }
    )


ROW_LOW = {
    "row_id": "r1",
    "step_name": "Call name",
    "failure_mode": "Name called once",
    "effect": "Drink cools",
    "cause": "Single spoken call",
    "severity": 4,
    "occurrence": 5,
    "detection": 4,
}
ROW_HIGH_SEV = {
    "row_id": "r2",
    "step_name": "Prepare drink",
    "failure_mode": "Steam wand contacts hand",
    "effect": "Barista scalds a hand",
    "cause": "Wand parks in the work path",
    "severity": 9,
    "occurrence": 2,
    "detection": 3,
}


def test_high_severity_is_not_buried_under_a_bigger_rpn():
    """RPN 40 with severity 9 must outrank RPN 80 with severity 4: equal
    RPNs are not equal risks, and severity-first ordering is the guard."""
    artifact = _fmea([ROW_LOW, ROW_HIGH_SEV])
    order = [row.row_id for row in fmea_report._ordered_rows(artifact)]
    assert order[0] == "r2"


def test_verdict_flags_severity_nine_and_up():
    _, tone = fmea_report.build_verdict(_fmea([ROW_HIGH_SEV]))
    assert tone in ("flag", "fail")


def test_report_card_flags_uncalibrated_ratings():
    card = " ".join(t for _, t in fmea_report.build_report_card(_fmea([ROW_LOW])))
    assert "anchor" in card.lower()


def test_report_card_flags_a_high_severity_row_with_no_action():
    card = " ".join(t for _, t in fmea_report.build_report_card(_fmea([ROW_HIGH_SEV])))
    assert "no action" in card.lower()


def test_report_card_always_says_rpn_is_not_a_safety_threshold():
    card = " ".join(t for _, t in fmea_report.build_report_card(_fmea([ROW_LOW])))
    assert "no RPN below which" in card


def test_fmea_table_gives_the_text_columns_most_of_the_width():
    """The on-screen FMEA clips every text cell because the row is sized
    around the narrow S/O/D selects. On paper there is no hover to recover
    the tail, so the priority is inverted here -- and pinned, because it is
    the whole reason this report exists."""
    text_share = sum(frac for key, _, frac in fmea_report.COLUMNS if key in {"step_name", "failure_mode", "effect", "cause"})
    rating_share = sum(frac for key, _, frac in fmea_report.COLUMNS if key in {"severity", "occurrence", "detection"})
    assert text_share > 0.6
    assert rating_share < 0.15
    assert abs(sum(frac for _, _, frac in fmea_report.COLUMNS) - 1.0) < 0.02


def test_fmea_story_contains_every_row_in_full():
    """No truncation: the complete cell text has to survive onto the page."""
    artifact = _fmea([ROW_LOW, ROW_HIGH_SEV])
    story = fmea_report.build_story(
        artifact=artifact,
        project_name="P",
        version=1,
        provenance_rows=[("Artifact", "fmea · v1")],
        exported_at="2026-08-10 00:00 UTC",
        content_width=760.0,
    )
    text = _flatten(story)
    assert "Steam wand contacts hand" in text
    assert "Wand parks in the work path" in text
    assert "Single spoken call" in text


def test_fmea_renders_a_real_landscape_pdf():
    pdf = report_pdf.render(
        story_builder=lambda w: fmea_report.build_story(
            artifact=_fmea([ROW_LOW, ROW_HIGH_SEV]),
            project_name="P",
            version=1,
            provenance_rows=[],
            exported_at="2026-08-10 00:00 UTC",
            content_width=w,
        ),
        title="t",
        project_id="p",
        engine_version="0.1.0",
        page_size=fmea_report.PAGE_SIZE,
    )
    assert pdf.startswith(b"%PDF-")
    assert fmea_report.PAGE_SIZE[0] > fmea_report.PAGE_SIZE[1]  # landscape


# ------------------------------------------------------------------- routes


def test_fmea_report_route_404s_without_a_saved_fmea(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path))
    client = TestClient(app)
    client.post(
        "/project/create", json={"project_id": "p1", "name": "P", "created_at": "2026-08-09T00:00:00"}
    )
    response = client.post("/project/p1/report/T-16/pdf", json={})
    assert response.status_code == 404


def test_capability_report_route_422s_without_a_dataset(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path))
    client = TestClient(app)
    client.post(
        "/project/create", json={"project_id": "p2", "name": "P", "created_at": "2026-08-09T00:00:00"}
    )
    response = client.post("/project/p2/report/T-13/pdf", json={})
    assert response.status_code == 422
    assert "dataset_id" in response.json()["detail"]


# -------------------------------------------------------------------- frame


def test_report_card_never_renders_silently_empty():
    """An empty report card and a report card that failed to run look
    identical on paper, and the reader cannot tell which they are holding."""
    styles = report_theme.report_styles()
    text = _flatten(report_theme.report_card([], styles, 480.0))
    assert "No checks flagged" in text


def test_recommendation_is_labelled_as_not_computed():
    styles = report_theme.report_styles()
    text = _flatten(report_theme.recommendation_block("Standardise the new method.", styles, 480.0))
    assert "not a computed result" in text


def test_shared_labels_exist_for_the_honesty_vocabulary():
    for key in ("estimate", "pilot_only", "unstable", "msa_unqualified"):
        assert report_theme.LABELS[key]


def test_utc_stamp_shape():
    assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC$", report_theme.utc_stamp())


def test_one_sided_spec_says_not_applicable_not_not_claimable():
    """Two different absences were printing the same words. Cp needs BOTH
    spec limits and is undefined against a one-sided spec -- arithmetic, not
    a judgement. "Not claimable" is the phrase for a capability WITHHELD
    because the process is unstable, and telling a one-sided-spec user their
    process failed a test it never took is exactly the false signal this
    product exists to avoid."""
    assert "needs both spec limits" in cap._index_pair(None, -1.09, stable=True)
    assert "not claimable" in cap._index_pair(None, None, stable=False)


def test_chart_is_capped_so_the_report_stays_one_page():
    """Rendered at full width the real I-MR chart pushed the provenance zone
    onto page two, which is the zone that answers 'where did this number come
    from'. The cap keeps the aspect ratio and shrinks the width with it."""
    import struct
    import zlib

    def _png(width: int, height: int) -> bytes:
        raw = b"".join(b"\x00" + b"\x00\x00\x00" * width for _ in range(height))
        def chunk(tag: bytes, data: bytes) -> bytes:
            return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))
        return (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b"")
        )

    styles = report_theme.report_styles()
    flowables = report_theme.chart(_png(1000, 1000), content_width=480.0, styles=styles)
    image = flowables[0]
    assert image.drawHeight <= report_theme.MAX_CHART_HEIGHT + 1
    # square source stays square after the cap
    assert abs(image.drawWidth - image.drawHeight) < 1


# ------------------------------------------------------- Group A (phase 2)
#
# Built from the real worked example rather than hand-shaped fixtures. Two
# bugs in phase 1 (NormalityResult.advisory, DescriptiveStats.sd) existed
# only because a report was written against a remembered schema; fixtures
# would have agreed with the mistake.

import pathlib

from sigma_engine.artifacts.control_chart import ControlChartArtifact
from sigma_engine.artifacts.hypothesis import HypothesisRunArtifact
from sigma_engine.artifacts.msa import MsaArtifact
from sigma_engine.artifacts.proof import ProofArtifact
from sigma_engine.export.reports import control_chart as chart_report
from sigma_engine.export.reports import hypothesis as hyp_report
from sigma_engine.export.reports import msa as msa_report
from sigma_engine.export.reports import proof as proof_report
from sigma_engine.project_store import ProjectStore

EXAMPLE_ZIP = pathlib.Path(__file__).resolve().parents[2] / "examples" / "coffee-bar-example-project.zip"


@pytest.fixture(scope="module")
def example_store(tmp_path_factory):
    """The shipped worked example, unzipped. Using the artifact we actually
    distribute means these tests fail if the example and the reports drift
    apart -- which is how the blank-forms bug survived review."""
    import zipfile

    if not EXAMPLE_ZIP.is_file():
        pytest.skip("worked-example zip not present")
    root = tmp_path_factory.mktemp("example-projects")
    with zipfile.ZipFile(EXAMPLE_ZIP) as zf:
        zf.extractall(root)
    return ProjectStore(root)


def _artifact(store, artifact_id, model):
    return model.model_validate(store.load_artifact("coffee-bar-example", artifact_id, None))


def test_msa_report_states_what_it_did_not_measure_even_when_passing(example_store):
    """A page headed 'measurement study' that stays silent about
    reproducibility is how a marginal gauge gets waved through."""
    artifact = _artifact(example_store, "msa", MsaArtifact)
    _, tone = msa_report.build_verdict(artifact)
    assert tone == "pass"
    card = " ".join(t for _, t in msa_report.build_report_card(artifact))
    assert "reproducibility" in card.lower()
    assert "NOT assessed" in card or "not assessed" in card.lower()
    assert "Gage R&R" in card


def test_msa_names_the_denominator_the_percentage_is_against(example_store):
    """8.94% of tolerance and 8.94% of study variation are different claims."""
    artifact = _artifact(example_store, "msa", MsaArtifact)
    card = " ".join(t for _, t in msa_report.build_report_card(artifact))
    assert "study variation" in card or "tolerance" in card


def test_proof_prints_confounders_that_argue_against_its_own_result(example_store):
    artifact = _artifact(example_store, "proof", ProofArtifact)
    card = [t for _, t in proof_report.build_report_card(artifact)]
    joined = " ".join(card)
    assert "season" in joined.lower()
    assert "demand" in joined.lower()
    # Confounders lead: they are the reason to distrust everything above.
    assert "season" in card[0].lower() or "demand" in card[0].lower()


def test_proof_names_which_target_the_narrow_margin_refers_to(example_store):
    """The pilot declared 5.5; the charter's goal is 5.0. An unqualified
    'narrow margin' beside a verdict quoting the other threshold reads as a
    contradiction rather than a caution."""
    artifact = _artifact(example_store, "proof", ProofArtifact)
    card = " ".join(t for _, t in proof_report.build_report_card(artifact))
    assert "CHARTER goal" in card


def test_proof_never_claims_causation(example_store):
    artifact = _artifact(example_store, "proof", ProofArtifact)
    card = " ".join(t for _, t in proof_report.build_report_card(artifact))
    assert "not, by itself, proof of cause" in card


def test_hypothesis_renders_the_engines_plain_language_not_a_paraphrase(example_store):
    artifact = _artifact(example_store, "hypothesis", HypothesisRunArtifact)
    verdict, _ = hyp_report.build_verdict(artifact)
    assert verdict == artifact.result.value.plain_language.comparison_summary


def test_hypothesis_diagnostic_names_the_test_and_the_p_value(example_store):
    artifact = _artifact(example_store, "hypothesis", HypothesisRunArtifact)
    rows = dict(hyp_report.build_diagnostic_rows(artifact))
    assert "Test selected" in rows
    assert "p-value" in rows


def test_control_chart_report_flags_unacknowledged_signals(example_store):
    artifact = _artifact(example_store, "control-chart", ControlChartArtifact)
    card = " ".join(t for _, t in chart_report.build_report_card(artifact))
    assert "frozen" in card.lower()
    assert "Rules 1 and 4" in card


def test_control_chart_says_when_limits_are_not_frozen(example_store):
    artifact = _artifact(example_store, "control-chart", ControlChartArtifact)
    unfrozen = artifact.model_copy(update={"frozen_at": None})
    text, tone = chart_report.build_verdict(unfrozen)
    assert tone == "flag"
    assert "not frozen" in text.lower()


@pytest.mark.parametrize(
    "artifact_id,model,module,wants_chart",
    [
        ("msa", MsaArtifact, msa_report, False),
        ("proof", ProofArtifact, proof_report, True),
        ("hypothesis", HypothesisRunArtifact, hyp_report, True),
        ("control-chart", ControlChartArtifact, chart_report, True),
    ],
)
def test_every_group_a_report_renders_a_real_pdf(example_store, artifact_id, model, module, wants_chart):
    artifact = _artifact(example_store, artifact_id, model)
    extra = {"chart_png": None, "chart_unavailable_reason": "not captured in this test"} if wants_chart else {}
    pdf = report_pdf.render(
        story_builder=lambda w: module.build_story(
            artifact=artifact,
            project_name="Coffee Bar",
            version=1,
            provenance_rows=[("Artifact", artifact_id)],
            exported_at="2026-08-10 00:00 UTC",
            content_width=w,
            **extra,
        ),
        title=module.TOOL_TITLE,
        project_id="coffee-bar-example",
        engine_version="0.1.0",
        page_size=getattr(module, "PAGE_SIZE", None),
    )
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 2000
