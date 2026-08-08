from factories import make_data_collection_plan
from sigma_engine.artifacts.data_collection_plan import DataCollectionPlanArtifact
from sigma_engine.prescore.data_collection_plan import run_data_collection_plan_prescore


def test_complete_plan_passes_every_check():
    artifact = DataCollectionPlanArtifact.model_validate(make_data_collection_plan())
    results = run_data_collection_plan_prescore(artifact)
    assert len(results) == 6
    assert all(r.status == "pass" for r in results), results


def test_blank_plan_flags_every_check():
    base = {
        "schema_version": 1, "artifact_id": "dcp-blank", "tool_id": "T-11",
        "created_at": "2026-08-07T00:00:00", "updated_at": "2026-08-07T00:00:00",
    }
    artifact = DataCollectionPlanArtifact.model_validate(base)
    results = run_data_collection_plan_prescore(artifact)
    by_id = {r.check_id: r for r in results}
    assert by_id["operational_definition_complete"].status == "flag"
    assert by_id["two_people_confirmed"].status == "flag"
    assert by_id["data_type_declared"].status == "flag"
    assert by_id["stratification_or_reason"].status == "flag"
    assert by_id["logistics_complete"].status == "flag"
    assert by_id["planned_n_with_rationale"].status == "flag"


def test_one_missing_operational_definition_field_flags_and_names_it():
    plan = make_data_collection_plan()
    plan["operational_definition"] = {**plan["operational_definition"], "stops_when": ""}
    artifact = DataCollectionPlanArtifact.model_validate(plan)
    by_id = {r.check_id: r for r in run_data_collection_plan_prescore(artifact)}
    assert by_id["operational_definition_complete"].status == "flag"
    assert "stops_when" in by_id["operational_definition_complete"].detail


def test_two_people_unconfirmed_flags_even_with_full_definition_text():
    plan = make_data_collection_plan()
    plan["operational_definition"] = {**plan["operational_definition"], "two_people_confirmed": False}
    artifact = DataCollectionPlanArtifact.model_validate(plan)
    by_id = {r.check_id: r for r in run_data_collection_plan_prescore(artifact)}
    assert by_id["operational_definition_complete"].status == "pass"  # text fields are all still there
    assert by_id["two_people_confirmed"].status == "flag"


def test_no_stratification_reason_alone_satisfies_the_check():
    plan = make_data_collection_plan(
        stratification_factors=[], no_stratification_reason="Single uniform stream -- nothing to stratify by."
    )
    artifact = DataCollectionPlanArtifact.model_validate(plan)
    by_id = {r.check_id: r for r in run_data_collection_plan_prescore(artifact)}
    assert by_id["stratification_or_reason"].status == "pass"
    assert "Single uniform stream" in by_id["stratification_or_reason"].detail


def test_no_factors_and_no_reason_flags():
    plan = make_data_collection_plan(stratification_factors=[], no_stratification_reason="")
    artifact = DataCollectionPlanArtifact.model_validate(plan)
    by_id = {r.check_id: r for r in run_data_collection_plan_prescore(artifact)}
    assert by_id["stratification_or_reason"].status == "flag"


def test_planned_n_without_rationale_flags():
    plan = make_data_collection_plan()
    plan["logistics"] = {**plan["logistics"], "sample_size_rationale": ""}
    artifact = DataCollectionPlanArtifact.model_validate(plan)
    by_id = {r.check_id: r for r in run_data_collection_plan_prescore(artifact)}
    assert by_id["planned_n_with_rationale"].status == "flag"


def test_rationale_without_planned_n_flags():
    plan = make_data_collection_plan()
    plan["logistics"] = {**plan["logistics"], "planned_n": None}
    artifact = DataCollectionPlanArtifact.model_validate(plan)
    by_id = {r.check_id: r for r in run_data_collection_plan_prescore(artifact)}
    assert by_id["planned_n_with_rationale"].status == "flag"
