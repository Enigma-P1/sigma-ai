"""T-15 Fishbone (6M) + 5 Whys: an effect statement (optionally linked to
the charter's baselined problem), six branch categories named plainly --
People/Method/Machine/Material/Measurement/Environment, the same 6Ms an
Ishikawa diagram uses in English rather than jargon -- and causes carrying
the evidence-discipline status vocabulary rubric R-ANA-02 grades on:
candidate (proposed, no evidence yet) -> investigating (evidence being
gathered) -> verified (evidence ties the cause to the gap) -> ruled_out (a
candidate the evidence argues against, kept on the board rather than
deleted -- see prescore/fishbone.py). A 5-Why chain is just causes linked
by parent_cause_id -- no separate schema, so a sub-cause and a why-chain
step are the same thing.

Evidence discipline is schema-enforced, not a prescore flag (rubric
R-ANA-02's own invalidator: "an unverified cause treated as verified"): a
cause whose status is "verified" must carry a non-empty Evidence -- there
is no field-level way to fake it once the schema is the gate. This mirrors
the build brief's own framing ("verified-without-evidence rejected at
schema level"), the same soft/hard split PLAN §4.2 draws everywhere else
in this engine (a wrong number/logic is a hard rejection; thin content is
a prescore flag).

verified_causes is server-computed and always present (never hand-typed --
the same "never something a client can set independently" contract as
every Computed[...] field here: process_map.py's longest_step/
constraint_step, copq.py's total): the R-ANA-06 ranked-list feed Improve
consumes, listing every verified cause with its evidence pointer intact.
Ranking itself (by likely impact) is a human/advisor judgment call the
rubric keeps outside code (R-ANA-06's "Judgment-only: plausibility of the
impact ranking") -- this field supplies the honest, unranked verified set
the ranking is drawn from, in causes-list order.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from ..provenance import Computed, compute
from .base import ArtifactBase

BranchId = Literal["people", "method", "machine", "material", "measurement", "environment"]
BRANCH_IDS: tuple[BranchId, ...] = ("people", "method", "machine", "material", "measurement", "environment")

CauseStatus = Literal["candidate", "investigating", "verified", "ruled_out"]

EvidenceKind = Literal["dataset", "hypothesis_run", "check_sheet", "observation_note"]


class Evidence(BaseModel):
    """What supports a cause (PLAN §4.1: "what data supports this?"). `ref`
    is an artifact id for the three artifact-backed kinds, or the note text
    itself for `observation_note` -- unchecked cross-reference, same
    contract as DataCollectionPlanArtifact.charter_metric_id (no project-
    store I/O at the schema layer)."""

    kind: EvidenceKind
    ref: str = Field(min_length=1)

    @field_validator("ref")
    @classmethod
    def _ref_non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("evidence.ref must not be blank")
        return v


class EffectStatement(BaseModel):
    """The diagram's effect -- should be the baselined problem, not a
    convenient symptom of it (rubric R-ANA-01 #1). `charter_ref` is an
    optional, unchecked T-03 artifact id -- same soft-link contract as
    charter_metric_id elsewhere in this engine."""

    text: str = Field(min_length=1)
    charter_ref: str | None = None


class CausePosition(BaseModel):
    """One cause's canvas position -- opaque display data (process_map.py's
    StepPosition pattern, kept local rather than shared: every canvas
    artifact in this engine owns its own position type)."""

    x: float
    y: float


class Cause(BaseModel):
    cause_id: str = Field(min_length=1)
    branch: BranchId
    text: str = Field(min_length=1)
    # Nullable: a top-level cause on a branch has no parent; a sub-cause /
    # 5-Why chain step points at the cause it answers "why" for.
    parent_cause_id: str | None = None
    status: CauseStatus = "candidate"
    evidence: Evidence | None = None
    why_chain_position: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _evidence_required_when_verified(self) -> "Cause":
        # The rubric's own invalidator line, enforced where nothing can
        # route around it: "team consensus is not evidence" (R-ANA-02) --
        # a verified cause with no Evidence object simply cannot be built.
        if self.status == "verified" and self.evidence is None:
            raise ValueError(f"cause {self.cause_id!r}: evidence is required (non-empty) when status='verified'")
        return self


class VerifiedCauseEntry(BaseModel):
    """One verified cause as it feeds Improve (R-ANA-06) -- evidence is
    non-optional here (unlike Cause.evidence) because the schema already
    guarantees every status='verified' cause carries one."""

    cause_id: str
    branch: BranchId
    text: str
    evidence: Evidence
    parent_cause_id: str | None
    why_chain_position: int | None


class VerifiedCausesSummary(BaseModel):
    count: int
    causes: list[VerifiedCauseEntry]


def compute_verified_causes(causes: list[Cause]) -> Computed[VerifiedCausesSummary]:
    """The only supported way to produce FishboneArtifact.verified_causes --
    never hand-assemble one (CopqArtifact.compute_copq_total's contract)."""
    verified = [c for c in causes if c.status == "verified"]
    entries: list[VerifiedCauseEntry] = []
    for c in verified:
        assert c.evidence is not None  # guaranteed by Cause._evidence_required_when_verified
        entries.append(VerifiedCauseEntry(
            cause_id=c.cause_id, branch=c.branch, text=c.text, evidence=c.evidence,
            parent_cause_id=c.parent_cause_id, why_chain_position=c.why_chain_position,
        ))
    summary = VerifiedCausesSummary(count=len(entries), causes=entries)
    return compute(
        summary,
        method=(
            "verified_causes = every cause with status == 'verified', in causes-list order, each carrying its "
            "evidence pointer (rubric R-ANA-02/R-ANA-06 feed) -- an empty list is an honest zero, not 'nothing to "
            "compute yet': a fishbone with no verified causes is a valid, common in-progress state."
        ),
        input_data=[c.model_dump(mode="json") for c in causes],
        assumptions_checked=["schema guarantees every status='verified' cause already carries non-empty evidence"],
    )


class FishboneArtifact(ArtifactBase):
    tool_id: Literal["T-15"] = "T-15"

    effect: EffectStatement
    causes: list[Cause] = Field(default_factory=list)
    # Keyed by cause_id; opaque to the engine (process_map.py's layout
    # pattern) -- round-trips on save/load, never read by any computation.
    layout: dict[str, CausePosition] = Field(default_factory=dict)

    # Server-computed, never hand-typed -- unconditionally replaced below,
    # same contract as every other Computed[...] field in this engine.
    # Always non-None after validation; Optional only so a POST body can
    # omit it (Computed[...] isn't trivially default-constructible) --
    # unlike longest_step/constraint_step this is never legitimately
    # absent: an empty list is itself the honest zero-verified-causes state.
    verified_causes: Computed[VerifiedCausesSummary] | None = None

    @model_validator(mode="after")
    def _referential_integrity(self) -> "FishboneArtifact":
        ids = [c.cause_id for c in self.causes]
        if len(ids) != len(set(ids)):
            raise ValueError("cause_id values must be unique")
        id_set = set(ids)
        for c in self.causes:
            if c.parent_cause_id is None:
                continue
            if c.parent_cause_id == c.cause_id:
                raise ValueError(f"cause {c.cause_id!r} cannot be its own parent")
            if c.parent_cause_id not in id_set:
                raise ValueError(f"cause {c.cause_id!r} references unknown parent_cause_id {c.parent_cause_id!r}")
        self._check_no_cycles()
        return self

    def _check_no_cycles(self) -> None:
        parent_of = {c.cause_id: c.parent_cause_id for c in self.causes}
        for start in parent_of:
            seen: set[str] = set()
            current: str | None = start
            while current is not None:
                if current in seen:
                    raise ValueError(f"cause {start!r} sits in a parent_cause_id cycle")
                seen.add(current)
                current = parent_of.get(current)

    @model_validator(mode="after")
    def _recompute_verified_causes(self) -> "FishboneArtifact":
        self.verified_causes = compute_verified_causes(self.causes)
        return self
