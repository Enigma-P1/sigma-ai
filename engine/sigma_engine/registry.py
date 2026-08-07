"""tool_id -> (artifact model, prescore function), so the FastAPI routes are
one generic CRUD set parameterized by tool_id rather than five near-copies.
"""

from __future__ import annotations

from typing import Callable

from .artifacts import ArtifactBase, CharterArtifact, CopqArtifact, PickerArtifact, SipocArtifact, VocCtqArtifact
from .prescore import (
    PrescoreResult,
    run_charter_prescore,
    run_copq_prescore,
    run_picker_prescore,
    run_sipoc_prescore,
    run_voc_ctq_prescore,
)

ARTIFACT_REGISTRY: dict[str, type[ArtifactBase]] = {
    "T-01": PickerArtifact,
    "T-02": CopqArtifact,
    "T-03": CharterArtifact,
    "T-04": SipocArtifact,
    "T-05": VocCtqArtifact,
}

PRESCORE_REGISTRY: dict[str, Callable[[ArtifactBase], list[PrescoreResult]]] = {
    "T-01": run_picker_prescore,
    "T-02": run_copq_prescore,
    "T-03": run_charter_prescore,
    "T-04": run_sipoc_prescore,
    "T-05": run_voc_ctq_prescore,
}
