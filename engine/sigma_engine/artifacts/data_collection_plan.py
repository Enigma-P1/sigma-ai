"""T-11 Data Collection Plan artifact -- the PLAN half of T-11 (the import
half lives in datasets.py/routes/datasets.py, the sample-size half in
stats/sample_size.py; both already exist and are unaffected by this file).
This is PLAN §4.1's T-11 row: "operational definition builder ('two people
would measure it the same way' check), data type identification,
stratification factors ... sample-size guidance." Rubric R-MEA-05 grades
it; prescore/data_collection_plan.py runs its rule-checkable lines.

Content-quality fields (an operational-definition sentence, a stated
rationale) are prescore flags, not schema rejections -- the same PLAN §4.2
hard/soft split charter.py documents: the schema only hard-requires what
would be structurally meaningless otherwise (a stratification factor with
no name, a negative planned sample size). No computed fields live here --
unlike TimeStudyArtifact/SpaghettiArtifact, a Data Collection Plan is a
plan a person writes down, not a result the engine derives."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .base import ArtifactBase

# The field every downstream chart/test route reads (rubric R-MEA-05 #2):
# continuous (a measured amount) vs the two attribute flavors -- defective
# (pass/fail per unit) vs count (defects per unit/area, matrix EXIT-11's
# "defectives != defects" distinction) -- never a bare two-way
# continuous/attribute split, so a count-type project can't be silently
# routed down the p-chart/proportion path the matrix bars it from by name.
DataCollectionDataType = Literal["continuous", "attribute_defective", "attribute_count"]


class OperationalDefinition(BaseModel):
    """Rubric R-MEA-05 #1's "two people" test, as fields: what is
    measured, how (instrument/method), precision or unit, the exact
    starting and stopping moments, and the confirmation itself -- the plan
    T-13's own operational_definition_ok checkbox is confirming against."""

    what_measured: str = ""
    how_instrument: str = ""
    precision_unit: str = ""
    starts_when: str = ""
    stops_when: str = ""
    two_people_confirmed: bool = False


class StratificationFactor(BaseModel):
    """One suspected source of difference (shift, machine, operator, day
    ...), captured so it can be recorded as a column later (rubric
    R-MEA-05 #3) -- name is structurally required (an unnamed factor means
    nothing), values_expected is optional guidance, not enforced against
    collected data here (that cross-check is a judgment call, per the
    rubric's own "Pre-scored in code" vs "Judgment-only" split)."""

    name: str = Field(min_length=1)
    values_expected: list[str] = Field(default_factory=list)


class CollectionLogistics(BaseModel):
    """Rubric R-MEA-05 #4/#5: who collects, where, when/how often, and the
    planned n with its sample-size rationale (the calculator/rule-of-thumb
    output from stats/sample_size.py, restated here as the plan's own
    committed number+reason, not re-derived)."""

    who_collects: str = ""
    where_collected: str = ""
    when_how_often: str = ""
    planned_n: int | None = Field(default=None, gt=0)
    sample_size_rationale: str = ""


class DataCollectionPlanArtifact(ArtifactBase):
    tool_id: Literal["T-11"] = "T-11"

    # Optional link to the charter's metric (rubric R-DEF-03 #2: "the
    # primary metric ... points at the Data Collection Plan's definition")
    # -- a plain string, not a resolved cross-artifact reference; the
    # engine doesn't validate it points at a real charter field.
    metric_name: str = ""
    charter_metric_id: str | None = None

    operational_definition: OperationalDefinition = Field(default_factory=OperationalDefinition)
    data_type: DataCollectionDataType | None = None

    stratification_factors: list[StratificationFactor] = Field(default_factory=list)
    # The rubric's explicit escape hatch (R-MEA-05 pre-score: "≥1
    # stratification factor OR an explicit 'none apply' reason") -- a
    # project with genuinely one uniform stream can say so instead of
    # inventing factors to satisfy a checklist.
    no_stratification_reason: str = ""

    logistics: CollectionLogistics = Field(default_factory=CollectionLogistics)
    bias_note: str = ""

    @model_validator(mode="after")
    def _unique_stratification_factor_names(self) -> "DataCollectionPlanArtifact":
        names = [f.name for f in self.stratification_factors]
        if len(names) != len(set(names)):
            raise ValueError("stratification factor names must be unique")
        return self
