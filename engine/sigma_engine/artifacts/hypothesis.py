"""T-17 Hypothesis Testing artifact: THIN by design (build brief) -- stores
the question as stated, the routing decision object, the result (or exit),
and the declared-primary flag, with routing/result always server-
recomputed from the stored question, exactly MsaArtifact's "no hand-typed
totals anywhere" pattern (artifacts/msa.py) applied here to `routing`/
`result` instead of `result`/`verdict`: never something a client, or a
hand-edited on-disk JSON file, can set independently of the question.

This recompute-on-validate is what makes prescore/hypothesis.py's route-
tamper check meaningful (rubric R-ANA-04: "the artifact's route matches
what the rule tree produces from the recorded inputs") -- see that
module's docstring for why the prescore check still exists even though
this validator re-derives the same thing at construction time (the GET
.../artifacts/{id} load path returns the stored dict verbatim, without
re-running this validator -- same caveat MsaArtifact's own docstring
states).
"""

from __future__ import annotations

from typing import Literal

from pydantic import model_validator

from ..stats.hypothesis_common import HypothesisQuestion, HypothesisTestResult
from ..stats.hypothesis_runner import run_hypothesis
from ..stats.hypothesis_selector import RoutingDecision
from ..provenance import Computed
from .base import ArtifactBase


class HypothesisRunArtifact(ArtifactBase):
    tool_id: Literal["T-17"] = "T-17"

    question: HypothesisQuestion
    declared_primary: bool = True

    # Server-computed, never hand-typed -- unconditionally replaced below,
    # same contract as MsaArtifact.result / CopqArtifact.total.
    routing: RoutingDecision | None = None
    result: Computed[HypothesisTestResult] | None = None
    refused: bool = False

    @model_validator(mode="after")
    def _recompute(self) -> "HypothesisRunArtifact":
        run_result = run_hypothesis(self.question)
        self.routing = run_result.routing
        self.result = run_result.result
        self.refused = run_result.refused
        return self
