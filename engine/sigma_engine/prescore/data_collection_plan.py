"""T-11 Data Collection Plan prescore: rubric R-MEA-05's rule-checkable
lines, one check per bullet -- all operational-definition fields non-empty;
the two-people box confirmed; data type declared; >=1 stratification
factor OR an explicit "none apply" reason; logistics fields non-empty;
planned-n present with its rationale. Everything here is a flag, never a
schema rejection (PLAN §4.2 hard/soft split, same stance as
prescore/charter.py) -- a plan mid-draft is still a valid, saveable plan."""

from __future__ import annotations

from ..artifacts.data_collection_plan import DataCollectionPlanArtifact
from .common import PrescoreResult


def run_data_collection_plan_prescore(artifact: DataCollectionPlanArtifact) -> list[PrescoreResult]:
    results: list[PrescoreResult] = []
    od = artifact.operational_definition

    od_fields = {
        "what_measured": od.what_measured, "how_instrument": od.how_instrument,
        "precision_unit": od.precision_unit, "starts_when": od.starts_when, "stops_when": od.stops_when,
    }
    missing_od = [name for name, val in od_fields.items() if not val.strip()]
    results.append(PrescoreResult(
        check_id="operational_definition_complete", tool_id="T-11",
        status="pass" if not missing_od else "flag",
        detail="what/how/precision/starts/stops are all stated" if not missing_od
        else f"operational definition missing: {missing_od}",
    ))

    results.append(PrescoreResult(
        check_id="two_people_confirmed", tool_id="T-11",
        status="pass" if od.two_people_confirmed else "flag",
        detail="confirmed: two people measuring this would record the same value" if od.two_people_confirmed
        else "not yet confirmed -- the two-people test hasn't been checked off",
    ))

    results.append(PrescoreResult(
        check_id="data_type_declared", tool_id="T-11",
        status="pass" if artifact.data_type is not None else "flag",
        detail=f"declared: {artifact.data_type}" if artifact.data_type is not None
        else "no data type declared -- every downstream chart/test route reads this field",
    ))

    has_factors = bool(artifact.stratification_factors)
    has_reason = bool(artifact.no_stratification_reason.strip())
    results.append(PrescoreResult(
        check_id="stratification_or_reason", tool_id="T-11",
        status="pass" if has_factors or has_reason else "flag",
        detail=(
            f"{len(artifact.stratification_factors)} stratification factor(s) declared" if has_factors
            else "no factors apply -- reason: " + artifact.no_stratification_reason if has_reason
            else "no stratification factors, and no 'none apply' reason given"
        ),
    ))

    lg = artifact.logistics
    lg_fields = {"who_collects": lg.who_collects, "where_collected": lg.where_collected, "when_how_often": lg.when_how_often}
    missing_lg = [name for name, val in lg_fields.items() if not val.strip()]
    results.append(PrescoreResult(
        check_id="logistics_complete", tool_id="T-11",
        status="pass" if not missing_lg else "flag",
        detail="who/where/when-how-often are all stated" if not missing_lg
        else f"collection logistics missing: {missing_lg}",
    ))

    has_n = lg.planned_n is not None
    has_rationale = bool(lg.sample_size_rationale.strip())
    results.append(PrescoreResult(
        check_id="planned_n_with_rationale", tool_id="T-11",
        status="pass" if has_n and has_rationale else "flag",
        detail=f"planned n={lg.planned_n}, rationale stated" if has_n and has_rationale
        else "planned n and/or its rationale is missing -- consult the sample-size guidance panel",
    ))

    return results
