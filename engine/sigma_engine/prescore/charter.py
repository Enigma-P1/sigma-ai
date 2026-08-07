"""T-03 prescore: solution-language heuristics + magnitude pattern (the two
checks named in the M1 brief), plus the buildable-now subset of R-DEF-03/04's
other "Pre-scored in code" lines that don't need an artifact this milestone
doesn't build yet (owner-placeholder, consequential-metric presence,
risk-block presence). Checks that need T-13/T-20/T-22 are out of scope here
-- see the build report for the exact list.
"""

from __future__ import annotations

import re

from ..artifacts.charter import CharterArtifact
from .common import PrescoreResult

# PLAN §4.1: "Rule-based checks (regex/keyword heuristics + checklist
# confirmations) flag solution-shaped statements." One reviewable list,
# used for both the problem statement (R-DEF-02) and the goal (R-DEF-03).
SOLUTION_LANGUAGE_KEYWORDS: tuple[str, ...] = (
    "train", "training", "hire", "hiring", "install", "installing",
    "implement", "implementing", "because", "due to",
)

_KEYWORD_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in SOLUTION_LANGUAGE_KEYWORDS) + r")\b",
    re.IGNORECASE,
)

# R-DEF-04 pre-score: "owner-name blocklist." Case-insensitive exact match
# against the trimmed name -- deliberately narrow (no substring matching)
# so a real person named e.g. "Teamsy" isn't caught by accident.
PLACEHOLDER_OWNER_NAMES = frozenset({"tbd", "team", "management", "n/a", "none", "unassigned"})


def _scan_solution_language(text: str) -> list[str]:
    return sorted({m.group(1).lower() for m in _KEYWORD_PATTERN.finditer(text)})


def _problem_statement_text(artifact: CharterArtifact) -> str:
    ps = artifact.problem_statement
    return " ".join([ps.what, ps.where, ps.when])


def run_charter_prescore(artifact: CharterArtifact) -> list[PrescoreResult]:
    results: list[PrescoreResult] = []

    hits = _scan_solution_language(_problem_statement_text(artifact))
    results.append(PrescoreResult(
        check_id="problem_statement_solution_language",
        tool_id="T-03",
        status="pass" if not hits else "flag",
        detail="clean" if not hits else f"solution/cause language found: {hits}",
    ))

    goal_hits = _scan_solution_language(artifact.goal.statement)
    results.append(PrescoreResult(
        check_id="goal_solution_language",
        tool_id="T-03",
        status="pass" if not goal_hits else "flag",
        detail="clean" if not goal_hits else f"solution/cause language found: {goal_hits}",
    ))

    mag = artifact.problem_statement.magnitude
    missing = [name for name, val in (("unit", mag.unit), ("period", mag.period)) if not val.strip()]
    results.append(PrescoreResult(
        check_id="magnitude_pattern",
        tool_id="T-03",
        status="pass" if not missing else "flag",
        detail="number+unit+period all present" if not missing else f"magnitude missing: {missing}",
    ))

    owner_name = artifact.process_owner.name.strip().lower()
    is_placeholder = owner_name in PLACEHOLDER_OWNER_NAMES
    results.append(PrescoreResult(
        check_id="owner_not_placeholder",
        tool_id="T-03",
        status="flag" if is_placeholder else "pass",
        detail=(
            f"owner name {artifact.process_owner.name!r} looks like a placeholder"
            if is_placeholder else "owner is named"
        ),
    ))

    results.append(PrescoreResult(
        check_id="consequential_metric_present",
        tool_id="T-03",
        status="pass" if artifact.goal.consequential_metrics else "flag",
        detail=(
            "at least one guardrail metric named" if artifact.goal.consequential_metrics
            else "no consequential/guardrail metric named"
        ),
    ))

    results.append(PrescoreResult(
        check_id="risk_block_present",
        tool_id="T-03",
        status="pass" if artifact.risks else "flag",
        detail=(
            f"{len(artifact.risks)} risk row(s)" if artifact.risks
            else "key-risks block is empty (matrix correction A-4)"
        ),
    ))

    return results
