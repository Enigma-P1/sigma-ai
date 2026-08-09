"""T-20 prescore: rubric R-IMP-03/04's rule-checkable lines.

  - threshold_as_declared: verdict.threshold_verdict is one of the two
    Literal values and matches a fresh recompute against the artifact's
    own declared_threshold + after data (route-tamper-check shape,
    prescore/hypothesis.py's precedent) -- never a reworded free-text verdict.
  - confounder_echo_present: the confounder checklist is present and, when
    any factor changed, verdict.weakened is true and the headline carries
    the weakened sentence (R-IMP-03 #3's "any reported confound tempers
    the claim").
  - guardrail_section_present_or_explicitly_none: guardrails is either
    non-empty or explicitly an empty list (R-IMP-03 #5) -- flags a
    project with a charter consequential metric named but zero guardrails
    entered here as a likely omission (advisory; this module alone can't
    see the charter to know for certain, so it stays "flag" not "hard_flag").
  - gap_arithmetic_consistency: recompute original_gap/recovered/remaining
    from the artifact's own stored inputs and compare -- a wrong number
    at the loop's decision point is a named invalidator (R-IMP-04).
  - metric_identity_single_copy: the schema-enforced-by-shape "same
    metric/definition/measurement system" guarantee (proof.py's module
    docstring), re-affirmed here the same way route_tamper_check
    re-affirms what HypothesisRunArtifact's own validator already ensures.
  - capability_language_requires_stability (M6 fidelity-panel fix): when
    this artifact's own computed stability read says a window is NOT
    stable, capability-index vocabulary in its free-text fields is a
    schema-visible contradiction -- the engine gated Cpk/Ppk on stability
    (stats/baseline.py, rubric R-MEA-08/R-MEA-09), so no free-text claim
    of it can be backed by these numbers. The solution-language-keyword
    idiom (prescore/charter.py): a small reviewable vocabulary, matched
    case-insensitively on word boundaries, over the enumerated free-text
    fields this schema actually has (`notes` + the five confounder
    notes). Fires ONLY when a computed stable field is False; never on a
    stable (or not-computed) artifact. T-25/A3 gets no analogous check:
    the A3 schema carries no computed stability state of its own (its
    computed fields are realized benefits, the gap verdict, and the close
    check), so there is nothing schema-visible there to contradict.
"""

from __future__ import annotations

import re

from ..artifacts.proof import CONFOUNDER_FIELDS, ProofArtifact, compute_gap
from ..stats.descriptive import weighted_mean
from .common import PrescoreResult

# Capability-index vocabulary (module docstring's last check). Deliberately
# small and reviewable, like SOLUTION_LANGUAGE_KEYWORDS -- word-boundary
# matching means "capable" never fires inside "escapable".
CAPABILITY_LANGUAGE_KEYWORDS: tuple[str, ...] = (
    "cpk", "ppk", "process capability", "sigma level", "capable",
)

_CAPABILITY_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in CAPABILITY_LANGUAGE_KEYWORDS) + r")\b",
    re.IGNORECASE,
)


def run_proof_prescore(artifact: ProofArtifact) -> list[PrescoreResult]:
    return [
        _threshold_as_declared(artifact),
        _confounder_echo_present(artifact),
        _guardrail_section_present_or_explicitly_none(artifact),
        _gap_arithmetic_consistency(artifact),
        _metric_identity_single_copy(artifact),
        _capability_language_requires_stability(artifact),
    ]


def _threshold_as_declared(artifact: ProofArtifact) -> PrescoreResult:
    """Was vacuous (critic finding 6): `v in ("met", "not_met")` is always
    true -- threshold_verdict's own type (Literal["met", "not_met"]) already
    guarantees that, so the check never actually looked at anything. Now
    recomputes the after value the same weight-aware way ProofArtifact.
    _recompute does and compares the expected met/not_met read against the
    STORED verdict -- the matches-recomputed idiom (prescore/yield_calc.py)
    applied here, so a hand-edited threshold_verdict (met stored while the
    data says not_met, or vice versa) hard_flags instead of sailing through
    on a check that could never fail."""
    if artifact.verdict is None:
        return PrescoreResult(check_id="threshold_as_declared", tool_id="T-20", status="flag", detail="no verdict computed")
    recomputed_after = weighted_mean(artifact.after.values, artifact.after.weights)
    expected_met = (
        recomputed_after <= artifact.declared_threshold.value if artifact.declared_threshold.direction == "lower_is_better"
        else recomputed_after >= artifact.declared_threshold.value
    )
    expected_verdict = "met" if expected_met else "not_met"
    stored = artifact.verdict.value.threshold_verdict
    matches = stored == expected_verdict
    return PrescoreResult(
        check_id="threshold_as_declared", tool_id="T-20", status="pass" if matches else "hard_flag",
        detail=(
            f"threshold_verdict={stored!r} matches a fresh recompute ({recomputed_after:g} vs declared "
            f"{artifact.declared_threshold.value:g}, {artifact.declared_threshold.direction})" if matches else
            f"stored threshold_verdict={stored!r} does not match a fresh recompute (after={recomputed_after:g} vs "
            f"declared {artifact.declared_threshold.value:g}, {artifact.declared_threshold.direction} -> expected "
            f"{expected_verdict!r}) -- the file may have been hand-edited"
        ),
    )


def _confounder_echo_present(artifact: ProofArtifact) -> PrescoreResult:
    changed = [name for name in CONFOUNDER_FIELDS if getattr(artifact.confounders, name).changed]
    if artifact.verdict is None:
        return PrescoreResult(check_id="confounder_echo_present", tool_id="T-20", status="flag", detail="no verdict computed")
    weakened_matches = artifact.verdict.value.weakened == bool(changed)
    # Two honest phrasings, gated on threshold_met (Fix 1): "weakens this
    # proof" (an improvement claim, tempered) when the threshold was met,
    # "muddies attribution" (no improvement claim to temper -- a failure
    # reading, weakened further) when it wasn't. Either counts as the
    # confounder having actually printed.
    sentence_present = (
        not changed
        or "weakens this proof" in artifact.verdict.value.headline
        or "muddies attribution" in artifact.verdict.value.headline
    )
    ok = weakened_matches and sentence_present
    return PrescoreResult(
        check_id="confounder_echo_present", tool_id="T-20", status="pass" if ok else "hard_flag",
        detail=(
            f"{len(changed)} confounder(s) changed ({changed}); verdict.weakened={artifact.verdict.value.weakened}, "
            f"weakened sentence in headline={sentence_present}"
        ),
    )


def _guardrail_section_present_or_explicitly_none(artifact: ProofArtifact) -> PrescoreResult:
    ok = artifact.guardrail_report is not None  # always true once _recompute has run -- schema guarantee
    n = len(artifact.guardrails)
    return PrescoreResult(
        check_id="guardrail_section_present_or_explicitly_none", tool_id="T-20", status="pass" if (ok and n > 0) else "flag" if ok else "hard_flag",
        detail=(
            f"{n} guardrail(s) reported alongside the primary metric" if n > 0
            else "guardrails is explicitly empty -- confirm the charter really named no consequential metric, "
            "rather than one being silently dropped (R-DEF-03 #3 / R-IMP-03 #5)"
        ),
    )


def _gap_arithmetic_consistency(artifact: ProofArtifact) -> PrescoreResult:
    if artifact.gap is None:
        return PrescoreResult(check_id="gap_arithmetic_consistency", tool_id="T-20", status="flag", detail="no gap computed")
    recomputed = compute_gap(
        charter_baseline_value=artifact.charter_baseline_value, charter_goal_value=artifact.charter_goal_value,
        after_value=artifact.gap.value.after_value, direction=artifact.charter_goal_direction,
        next_cause_ref=artifact.next_cause_ref,
    ).value
    stored = artifact.gap.value
    matches = (
        recomputed.original_gap == stored.original_gap and recomputed.recovered == stored.recovered
        and recomputed.remaining == stored.remaining and recomputed.goal_met == stored.goal_met
    )
    return PrescoreResult(
        check_id="gap_arithmetic_consistency", tool_id="T-20", status="pass" if matches else "hard_flag",
        detail=(
            f"original_gap={stored.original_gap:g}, recovered={stored.recovered:g}, remaining={stored.remaining:g}, "
            f"goal_met={stored.goal_met} -- recomputed and matches" if matches
            else f"stored gap fields don't match a fresh recompute from the artifact's own inputs -- the file may "
            f"have been hand-edited (stored remaining={stored.remaining:g}, recomputed={recomputed.remaining:g})"
        ),
    )


def _proof_free_text_fields(artifact: ProofArtifact) -> list[tuple[str, str]]:
    """The free-text fields this schema actually has, enumerated (module
    docstring): the artifact-level `notes` plus each confounder answer's
    `note`. Refs (metric_ref etc.) are identity labels, not narrative, and
    `next_cause_ref.cause_text` is echoed from the fishbone, not authored
    here -- both deliberately excluded."""
    fields = [("notes", artifact.notes or "")]
    for name in CONFOUNDER_FIELDS:
        fields.append((f"confounders.{name}.note", getattr(artifact.confounders, name).note))
    return fields


def _capability_language_requires_stability(artifact: ProofArtifact) -> PrescoreResult:
    unstable_sides = [
        side for side, baseline in (("before", artifact.before_baseline), ("after", artifact.after_baseline))
        if baseline is not None and baseline.stable is False
    ]
    if not unstable_sides:
        return PrescoreResult(
            check_id="capability_language_requires_stability", tool_id="T-20", status="pass",
            detail=(
                "no computed stability field on this artifact reads unstable -- free-text capability language "
                "(if any) is not contradicted by the artifact's own computed state"
            ),
        )
    hits = [
        (field_name, sorted({m.group(1).lower() for m in _CAPABILITY_PATTERN.finditer(text)}))
        for field_name, text in _proof_free_text_fields(artifact)
        if _CAPABILITY_PATTERN.search(text)
    ]
    sides = " and ".join(unstable_sides)
    if not hits:
        return PrescoreResult(
            check_id="capability_language_requires_stability", tool_id="T-20", status="pass",
            detail=(
                f"the {sides} baseline reads not-stable, and no free-text field carries capability-index "
                "vocabulary -- nothing claimed past what the numbers back"
            ),
        )
    named = "; ".join(f"{field_name}: {terms}" for field_name, terms in hits)
    return PrescoreResult(
        check_id="capability_language_requires_stability", tool_id="T-20", status="flag",
        detail=(
            f"stability failed here (the {sides} baseline reads not-stable, so the engine gated its "
            f"capability indices) -- capability language in free text can't be backed by these numbers "
            f"(rubric R-MEA-08/R-MEA-09): {named}"
        ),
    )


def _metric_identity_single_copy(artifact: ProofArtifact) -> PrescoreResult:
    # Schema-enforced by shape (proof.py's module docstring: one field
    # each, not a before/after pair) -- always true; stated here so the
    # rubric's own R-IMP-03 #1 criterion has a visible, named check.
    ok = bool(artifact.metric_ref.strip() and artifact.operational_definition_ref.strip() and artifact.measurement_system_ref.strip())
    return PrescoreResult(
        check_id="metric_identity_single_copy", tool_id="T-20", status="pass" if ok else "hard_flag",
        detail=(
            f"metric_ref={artifact.metric_ref!r}, operational_definition_ref={artifact.operational_definition_ref!r}, "
            f"measurement_system_ref={artifact.measurement_system_ref!r} -- one copy each, shared by before and "
            "after by construction (a changed yardstick cannot happen)"
        ),
    )
