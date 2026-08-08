"""Schema accept/reject tests for T-11 DataCollectionPlanArtifact. Content
completeness (an empty operational-definition sentence, no rationale) is a
prescore flag -- see test_prescore_data_collection_plan.py -- never a
schema rejection here, matching charter.py's documented hard/soft split."""

import pytest
from pydantic import ValidationError

from factories import make_data_collection_plan
from sigma_engine.artifacts.data_collection_plan import DataCollectionPlanArtifact


def test_accepts_a_complete_plan():
    artifact = DataCollectionPlanArtifact.model_validate(make_data_collection_plan())
    assert artifact.data_type == "continuous"
    assert len(artifact.stratification_factors) == 2
    assert artifact.operational_definition.two_people_confirmed is True
    assert artifact.logistics.planned_n == 30


def test_accepts_a_minimal_blank_plan():
    """A plan-in-progress -- nothing but the shared envelope -- is still a
    valid, saveable artifact (PLAN §4.2: content quality is prescore's
    job, not the schema's)."""
    base = {
        "schema_version": 1, "artifact_id": "dcp-blank", "tool_id": "T-11",
        "created_at": "2026-08-07T00:00:00", "updated_at": "2026-08-07T00:00:00",
    }
    artifact = DataCollectionPlanArtifact.model_validate(base)
    assert artifact.data_type is None
    assert artifact.stratification_factors == []
    assert artifact.operational_definition.two_people_confirmed is False
    assert artifact.logistics.planned_n is None


def test_rejects_invalid_data_type():
    with pytest.raises(ValidationError):
        DataCollectionPlanArtifact.model_validate(make_data_collection_plan(data_type="attribute"))


def test_rejects_stratification_factor_with_empty_name():
    with pytest.raises(ValidationError):
        DataCollectionPlanArtifact.model_validate(
            make_data_collection_plan(stratification_factors=[{"name": "", "values_expected": []}])
        )


def test_rejects_duplicate_stratification_factor_names():
    factors = [{"name": "shift", "values_expected": ["AM"]}, {"name": "shift", "values_expected": ["PM"]}]
    with pytest.raises(ValidationError, match="stratification factor names must be unique"):
        DataCollectionPlanArtifact.model_validate(make_data_collection_plan(stratification_factors=factors))


def test_rejects_non_positive_planned_n():
    plan = make_data_collection_plan()
    plan["logistics"] = {**plan["logistics"], "planned_n": 0}
    with pytest.raises(ValidationError):
        DataCollectionPlanArtifact.model_validate(plan)


def test_stratification_factors_may_start_empty_with_a_stated_reason():
    plan = make_data_collection_plan(
        stratification_factors=[], no_stratification_reason="Single register, single shift -- nothing to split on."
    )
    artifact = DataCollectionPlanArtifact.model_validate(plan)
    assert artifact.stratification_factors == []
    assert artifact.no_stratification_reason != ""


def test_round_trip_via_model_dump():
    artifact = DataCollectionPlanArtifact.model_validate(make_data_collection_plan())
    round_tripped = DataCollectionPlanArtifact.model_validate(artifact.model_dump(mode="json"))
    assert round_tripped == artifact
