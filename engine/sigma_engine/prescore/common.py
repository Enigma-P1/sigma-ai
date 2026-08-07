"""Shared PrescoreResult type every tool's prescore module returns.

Three statuses, not two: "hard_flag" exists only for checks the rubric
itself grades on a three-tier scale (SIPOC's step-count range is the one
Define-phase example -- 4-7 pass, 8-9 flag, outside 4-9 hard_flag). Checks
with no such middle tier just use pass/flag.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Status = Literal["pass", "flag", "hard_flag"]


class PrescoreResult(BaseModel):
    check_id: str
    tool_id: str
    status: Status
    detail: str
