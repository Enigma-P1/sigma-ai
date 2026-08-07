"""Shared envelope every Sigma AI artifact model inherits (M1 brief).

Every artifact carries schema_version, artifact_id, tool_id, created_at/
updated_at, and an optional free-text notes field. Timestamps are supplied
by the caller as ISO8601 strings and only checked for parseability here --
never generated with now() inside a validator -- so constructing an artifact
is a pure function of its inputs and tests stay deterministic (no wall
clock anywhere in the schema layer).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


def validate_iso8601(value: str) -> str:
    """Raise if `value` doesn't parse as an ISO8601 date or datetime."""
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"not a valid ISO8601 timestamp: {value!r}") from exc
    return value


class ArtifactBase(BaseModel):
    """Common fields for every artifact. `extra="forbid"` so a typo'd field
    name fails loudly at construction instead of silently vanishing."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int
    artifact_id: str
    tool_id: str
    created_at: str
    updated_at: str
    notes: str | None = None

    @field_validator("artifact_id")
    @classmethod
    def _artifact_id_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("artifact_id must not be empty")
        return v

    @field_validator("created_at", "updated_at")
    @classmethod
    def _timestamps_are_iso8601(cls, v: str) -> str:
        return validate_iso8601(v)
