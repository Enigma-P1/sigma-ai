"""Parser for docs/traceability-matrix.md -- read-only input.

Two things are pulled out of the real document, on demand, never
hand-copied into this package as a second source of truth:

1. §1's authoritative tool inventory table -> the Tier-A tool id set
   (must be exactly the 25 PLAN §9 refers to as "one authoritative
   count, no drift between milestones, rubric, and goldens").
2. Every golden id (`G-xxx-nn`) cited anywhere in the document, for the
   golden-id reconciliation report.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_TIER_A_ROW = re.compile(r"^\|\s*(T-\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(A|B|v1\.1|v2)\s*\|\s*$")
_GOLDEN_ID = re.compile(r"\bG-[a-z0-9]+-\d{2}\b")


@dataclass(frozen=True)
class ToolRow:
    tool_id: str
    name: str
    phase: str
    tier: str


def parse_tool_inventory(matrix_path: Path) -> list[ToolRow]:
    """§1's "Authoritative tool inventory" table, every row (all tiers) --
    matched purely by row shape (`| T-nn | name | phase | tier |`), which
    only that one table in the whole document uses; every other table
    keys its rows on BoK item codes (I.A.1, 3.4.1, ...) or attribute
    names, never a bare T-nn in the first cell."""
    rows: list[ToolRow] = []
    seen: set[str] = set()
    for line in matrix_path.read_text(encoding="utf-8").splitlines():
        m = _TIER_A_ROW.match(line)
        if not m:
            continue
        tool_id = m.group(1)
        if tool_id in seen:
            continue  # defensive: a tool id should appear once in §1
        seen.add(tool_id)
        rows.append(ToolRow(tool_id=tool_id, name=m.group(2), phase=m.group(3), tier=m.group(4)))
    return rows


def parse_tier_a_ids(matrix_path: Path) -> set[str]:
    return {r.tool_id for r in parse_tool_inventory(matrix_path) if r.tier == "A"}


def extract_golden_ids(matrix_path: Path) -> set[str]:
    text = matrix_path.read_text(encoding="utf-8")
    return set(_GOLDEN_ID.findall(text))


def assert_tier_a_count(matrix_path: Path, expected: int = 25) -> set[str]:
    """Loud, specific failure if §1's Tier-A row count ever drifts from the
    number PLAN §9 / the matrix's own §6 summary claims -- a parser bug or
    a real matrix edit both need a human to look, not a silent pass."""
    ids = parse_tier_a_ids(matrix_path)
    if len(ids) != expected:
        raise AssertionError(
            f"matrix parser found {len(ids)} Tier-A tool(s) in {matrix_path} (expected {expected}): "
            f"{sorted(ids)} -- either the matrix's §1 table changed (update the harness/tests deliberately) "
            "or the parser regex no longer matches its row shape (a real drift, not a passable one)"
        )
    return ids
