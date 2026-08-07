"""T-05 prescore: tree completeness -- every CTQ resolves to a parent need
and statement, and carries a measure (rubric R-DEF-07). Schema typing
already guarantees every field is non-empty; what it *cannot* verify is
that a need_id or statement_id string actually names a sibling that
exists -- dangling references are exactly why this is a prescore check
and not (only) a schema one.
"""

from __future__ import annotations

from ..artifacts.voc_ctq import VocCtqArtifact
from .common import PrescoreResult


def run_voc_ctq_prescore(artifact: VocCtqArtifact) -> list[PrescoreResult]:
    need_ids = {need.need_id for need in artifact.needs}
    statement_ids = {stmt.statement_id for stmt in artifact.statements}

    orphan_ctqs = [ctq.ctq_id for ctq in artifact.ctqs if ctq.need_id not in need_ids]
    orphan_needs = [
        need.need_id for need in artifact.needs
        if not set(need.statement_ids).issubset(statement_ids)
    ]
    # measure/direction are schema-required non-empty on every Ctq, so this
    # can't currently fail -- checked anyway so the result stays honest if
    # that ever changes, matching the picker-prescore precedent.
    unmeasured = [ctq.ctq_id for ctq in artifact.ctqs if not ctq.measure.strip()]

    problems = []
    if orphan_ctqs:
        problems.append(f"CTQs with no resolving need: {orphan_ctqs}")
    if orphan_needs:
        problems.append(f"needs with a dangling statement reference: {orphan_needs}")
    if unmeasured:
        problems.append(f"CTQs missing a measure: {unmeasured}")

    status = "pass" if not problems else "flag"
    detail = (
        "every CTQ resolves to a parent need and statement, with measure+direction present"
        if not problems else "; ".join(problems)
    )
    return [PrescoreResult(check_id="tree_completeness", tool_id="T-05", status=status, detail=detail)]
