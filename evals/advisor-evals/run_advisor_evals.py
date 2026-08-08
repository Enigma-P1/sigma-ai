#!/usr/bin/env python3
"""M6 advisor-evals runner (PLAN §9's "Advisor evals" paragraph, verbatim):

    "a frozen set of artifact-review and tollgate calls with known-defective
    artifacts -- crude defects (solution-shaped problem statement, fishbone
    with zero evidence) and subtle Green-Belt-fail patterns (capability
    claimed on an unstable process, before/after 'proof' with a reported
    confound, control plan with no owner) -- the advisor must catch them.
    Run per release like the vault's goldens, with model/version pinned per
    run so results are comparable."

This is deliberately NOT the golden-scenario harness (evals/harness/): that
harness diffs deterministic engine math against frozen numbers. The advisor
is not deterministic -- it is a live model call -- so there is nothing to
diff byte-for-byte. What this runner instead proves, in two layers:

  1. DETERMINISTIC LAYER (always available, no API key needed): every
     fixture's own artifact body validates against its schema (POST
     /artifacts/{tool}/validate) and is run through the engine's rule-based
     pre-score (POST /prescore/{tool}). That result is frozen into each
     fixture's *.expect.json under "deterministic_layer" -- code guarantees,
     recorded honestly, including what code does NOT catch.
  2. ADVISOR LAYER (needs a configured Anthropic key): the actual review /
     tollgate / validate call to the live engine, graded against each
     fixture's declared "must_catch" criteria via a small per-fixture
     matcher (see grade_response below).

No Anthropic API key exists in the environment this runner was built in --
see the README for the honest status line this ships with. --live is
therefore expected to refuse cleanly (POST /advisor/status says
unconfigured) until a release environment configures one; --mock proves the
runner's own grading mechanics work end to end using canned responses,
without needing a key or even a reachable engine.

Usage (engine/.venv/bin/python -- the one interpreter this repo pins with
httpx + anthropic installed, same convention as evals/harness/run_goldens.py):

    engine/.venv/bin/python evals/advisor-evals/run_advisor_evals.py --mock
    engine/.venv/bin/python evals/advisor-evals/run_advisor_evals.py --live [--engine-url URL]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = SCRIPT_DIR / "fixtures"
MOCK_RESPONSES_DIR = FIXTURES_DIR / "mock-responses"
RUNS_DIR = SCRIPT_DIR / "runs"

DEFAULT_ENGINE_URL = "http://127.0.0.1:8000"


# ================================================================
# Fixture loading
# ================================================================


@dataclass(frozen=True)
class Fixture:
    fixture_id: str
    body: dict[str, Any]
    expect: dict[str, Any]


def load_fixtures() -> list[Fixture]:
    """Every *.expect.json in fixtures/ paired with its sibling *.json body
    (same basename). Sorted by fixture_id so output order is stable and
    diffable run to run."""
    fixtures: list[Fixture] = []
    for expect_path in sorted(FIXTURES_DIR.glob("*.expect.json")):
        fixture_id = expect_path.name[: -len(".expect.json")]
        body_path = FIXTURES_DIR / f"{fixture_id}.json"
        if not body_path.exists():
            raise FileNotFoundError(f"fixture {fixture_id!r} has an expectation file but no body at {body_path}")
        expect = json.loads(expect_path.read_text(encoding="utf-8"))
        body = json.loads(body_path.read_text(encoding="utf-8"))
        if expect.get("fixture_id") != fixture_id:
            raise ValueError(f"{expect_path} declares fixture_id={expect.get('fixture_id')!r}, filename says {fixture_id!r}")
        fixtures.append(Fixture(fixture_id=fixture_id, body=body, expect=expect))
    if not fixtures:
        raise FileNotFoundError(f"no fixtures found under {FIXTURES_DIR}")
    return fixtures


def load_mock_response(fixture_id: str, outcome: str) -> dict[str, Any]:
    path = MOCK_RESPONSES_DIR / f"{fixture_id}.{outcome}.json"
    return json.loads(path.read_text(encoding="utf-8"))


# ================================================================
# Grading -- one small, declarative matcher per fixture (the "grading"
# block in each *.expect.json), plus a lenient text fallback used whenever
# the response never parsed into structured output. Every function here is
# defensive on purpose (garbage in -> a failed grade with a reason, never
# an exception) -- this is exercised directly by engine/tests/
# test_advisor_evals_fixtures.py's "grader never crashes on garbage" case.
# ================================================================


@dataclass(frozen=True)
class GradeResult:
    passed: bool
    reason: str


def _as_dict(x: Any) -> dict[str, Any]:
    return x if isinstance(x, dict) else {}


def _as_list(x: Any) -> list[Any]:
    return x if isinstance(x, list) else []


def _check_criterion_verdict(check: dict[str, Any], structured: dict[str, Any]) -> tuple[bool, str]:
    criterion_id = check.get("criterion_id")
    expect_verdict = check.get("expect_verdict")
    criteria = _as_list(structured.get("criteria"))
    match = next((c for c in criteria if _as_dict(c).get("criterion_id") == criterion_id), None)
    if match is None:
        return False, f"criterion {criterion_id!r} not present in response.criteria"
    got = _as_dict(match).get("verdict")
    if got != expect_verdict:
        return False, f"criterion {criterion_id!r} verdict={got!r}, expected {expect_verdict!r}"
    return True, f"criterion {criterion_id!r} verdict={got!r} as expected"


def _check_recommendation_is_not(check: dict[str, Any], structured: dict[str, Any]) -> tuple[bool, str]:
    disallowed = set(check.get("values", []))
    got = structured.get("recommendation")
    if got is None:
        return False, "no 'recommendation' field in structured response"
    if got in disallowed:
        return False, f"recommendation={got!r} is in the disallowed set {sorted(disallowed)}"
    return True, f"recommendation={got!r}, not in disallowed set {sorted(disallowed)}"


def _check_actions_or_reasons_mention_any(check: dict[str, Any], structured: dict[str, Any]) -> tuple[bool, str]:
    keywords = [str(k).lower() for k in check.get("keywords", [])]
    parts: list[str] = [str(r) for r in _as_list(structured.get("reasons"))]
    for action in _as_list(structured.get("actions")):
        parts.append(str(_as_dict(action).get("action", "")))
    haystack = " ".join(parts).lower()
    hits = [k for k in keywords if k in haystack]
    if not hits:
        return False, f"none of {keywords} appear in reasons/actions text"
    return True, f"matched keyword(s) {hits} in reasons/actions"


def _check_flag_present(check: dict[str, Any], response: dict[str, Any]) -> tuple[bool, str]:
    substr = str(check.get("field_path_contains", "")).lower()
    allowed_severities = set(check.get("severity_in", []))
    for flag in _as_list(response.get("flags")):
        flag = _as_dict(flag)
        field_path = str(flag.get("field_path", "")).lower()
        severity = flag.get("severity")
        if substr in field_path and (not allowed_severities or severity in allowed_severities):
            return True, f"flag on field_path={flag.get('field_path')!r} severity={severity!r} matched"
    return False, f"no flag with field_path containing {substr!r} and severity in {sorted(allowed_severities)}"


_CHECK_HANDLERS = {
    "criterion_verdict": _check_criterion_verdict,
    "recommendation_is_not": _check_recommendation_is_not,
    "actions_or_reasons_mention_any": _check_actions_or_reasons_mention_any,
    "flag_present": _check_flag_present,
}


def _grade_structured(expect: dict[str, Any], payload: dict[str, Any]) -> GradeResult:
    checks = expect.get("grading", {}).get("checks", [])
    if not checks:
        return GradeResult(False, "expectation file declares no grading checks -- nothing to grade against")
    reasons: list[str] = []
    for check in checks:
        handler = _CHECK_HANDLERS.get(check.get("type"))
        if handler is None:
            return GradeResult(False, f"unknown grading check type {check.get('type')!r}")
        ok, reason = handler(check, payload)
        reasons.append(reason)
        if not ok:
            return GradeResult(False, "; ".join(reasons))
    return GradeResult(True, "; ".join(reasons))


def _grade_text_fallback(expect: dict[str, Any], text: Any) -> GradeResult:
    keywords = [str(k).lower() for k in expect.get("grading", {}).get("text_fallback_keywords", [])]
    text_l = str(text or "").lower()
    hits = [k for k in keywords if k in text_l]
    if hits:
        return GradeResult(True, f"lenient text-match fallback: found {hits} in the raw answer text")
    return GradeResult(False, "lenient text-match fallback: none of the declared keywords appear in the raw answer text")


def grade_response(expect: dict[str, Any], response: Any) -> GradeResult:
    """The one per-fixture matcher every mode routes through. `response`
    shape:
      - mode="review"/"tollgate": an AdvisorAskResponse-shaped dict (the
        exact JSON body POST /advisor/ask returns): {"structured": {...}
        or None, "answer": "...", "unstructured_fallback": bool, ...}.
      - mode="validate": a ValidatorReport-shaped dict (the exact JSON body
        POST /advisor/validate returns): {"flags": [...],
        "checked_field_count": int, "unstructured_fallback": bool,
        "raw_answer": "...", ...}.
    The canned mock-responses/*.json files are written in these same two
    shapes precisely so --live and --mock can share this one function with
    no translation step. Falls back to a lenient keyword search over the
    raw answer text whenever structured output never parsed (matches this
    engine's own honest "unstructured_fallback" contract -- routes/
    advisor.py's AdvisorAskResponse docstring). Never raises: any exception
    here is a bug in the response's shape, not grounds to crash a whole
    eval run over one fixture -- reported as a failed grade instead."""
    try:
        response = _as_dict(response)
        mode = expect.get("mode")
        unstructured = bool(response.get("unstructured_fallback"))
        if mode == "validate":
            if unstructured:
                return _grade_text_fallback(expect, response.get("raw_answer", ""))
            return _grade_structured(expect, response)
        else:
            structured = response.get("structured")
            if unstructured or structured is None:
                return _grade_text_fallback(expect, response.get("answer", ""))
            return _grade_structured(expect, _as_dict(structured))
    except Exception as exc:  # noqa: BLE001 -- deliberately broad, see docstring
        return GradeResult(False, f"grader error on a malformed response: {exc!r}")


# ================================================================
# Version/model pins (PLAN §9: "model/version pinned per run so results
# are comparable"). Local pins need no network call -- this script always
# runs under engine/.venv/bin/python (the README says so), the one
# interpreter that has both `sigma_engine` (editable-installed) and
# `anthropic` importable, so both version numbers are available with no
# HTTP round trip. The engine_version / advisor_model pair is upgraded to
# the LIVE engine's own values in --live mode (see resolve_pins below) --
# the running engine is the actual authority on what it is; a --mock run
# has no running engine to ask and pins the local package version instead,
# labeled honestly.
# ================================================================


def local_pins() -> dict[str, str]:
    import anthropic

    import sigma_engine
    from sigma_engine.advisor.client import resolve_model

    return {
        "engine_version": sigma_engine.__version__,
        "anthropic_sdk_version": anthropic.__version__,
        "advisor_model": resolve_model(),
        "engine_version_source": "local sigma_engine package (engine/.venv), not a live /health call",
    }


def live_pins(client: httpx.Client, status_body: dict[str, Any]) -> dict[str, str]:
    import anthropic

    health = client.get("/health")
    health.raise_for_status()
    engine_version = health.json().get("engine_version", "unknown")
    return {
        "engine_version": engine_version,
        "anthropic_sdk_version": anthropic.__version__,
        "advisor_model": status_body.get("model", "unknown"),
        "engine_version_source": "live GET /health",
    }


# ================================================================
# --mock: no network, no engine required. Loads the two canned responses
# per fixture (one that WOULD pass, one that WOULD fail) and runs each
# through the exact same grade_response() --live uses, then asserts the
# grader classified both correctly -- this is the runner's own proof that
# its mechanics work end to end (PLAN §9 unit constraint #3), independent
# of whether a key is ever configured.
# ================================================================


def run_mock(fixtures: list[Fixture]) -> tuple[int, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    all_self_checks_ok = True

    for fx in fixtures:
        for outcome in ("pass", "fail"):
            canned = load_mock_response(fx.fixture_id, outcome)
            grade = grade_response(fx.expect, canned)
            expected_pass = outcome == "pass"
            self_check_ok = grade.passed == expected_pass
            all_self_checks_ok = all_self_checks_ok and self_check_ok
            rows.append({
                "fixture_id": fx.fixture_id,
                "tool_id": fx.expect.get("tool_id"),
                "mode": fx.expect.get("mode"),
                "canned_response": outcome,
                "expected_grade": "pass" if expected_pass else "fail",
                "actual_grade": "pass" if grade.passed else "fail",
                "self_check": self_check_ok,
                "reason": grade.reason,
            })

    print(f"[run_advisor_evals] mode=mock  {len(fixtures)} fixture(s), {len(rows)} canned response(s) graded")
    print()
    header = f"{'fixture_id':<34} {'canned':<6} {'expected':<9} {'actual':<7} {'ok':<4} reason"
    print(header)
    print("-" * len(header))
    for r in rows:
        ok_mark = "OK" if r["self_check"] else "FAIL"
        print(f"{r['fixture_id']:<34} {r['canned_response']:<6} {r['expected_grade']:<9} {r['actual_grade']:<7} {ok_mark:<4} {r['reason']}")
    print()

    if all_self_checks_ok:
        print(f"[run_advisor_evals] mock self-check PASSED: the grader correctly distinguished pass/fail canned responses on all {len(rows)} case(s).")
    else:
        n_bad = sum(1 for r in rows if not r["self_check"])
        print(f"[run_advisor_evals] mock self-check FAILED: {n_bad} canned response(s) graded opposite of what they should have -- the grader logic itself is broken.")

    output = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "mode": "mock",
        "pins": local_pins(),
        "engine_url": None,
        "rows": rows,
        "summary": {
            "total_canned_responses": len(rows),
            "self_checks_passed": sum(1 for r in rows if r["self_check"]),
            "self_checks_failed": sum(1 for r in rows if not r["self_check"]),
            "grader_mechanics_ok": all_self_checks_ok,
        },
    }
    return (0 if all_self_checks_ok else 1), output


# ================================================================
# --live: real HTTP against a running engine. Refuses up front (before any
# per-fixture call) if the advisor isn't configured -- PLAN §9 unit
# constraint: "refuses with a clear message if /advisor/status says
# unconfigured," never a wall of per-fixture 409s.
# ================================================================


def _ensure_project(client: httpx.Client, project_id: str) -> None:
    resp = client.post("/project/create", json={
        "project_id": project_id, "name": f"Advisor eval: {project_id}",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    if resp.status_code not in (200, 409):  # 409 = already exists from a prior run, fine to reuse
        resp.raise_for_status()


def _save_prerequisite_artifacts(client: httpx.Client, project_id: str, fx: Fixture) -> None:
    for tool_id in fx.expect.get("live_setup", {}).get("save_before_call", []):
        resp = client.post(f"/project/{project_id}/artifacts/{tool_id}", json=fx.body)
        resp.raise_for_status()


def _call_advisor(client: httpx.Client, project_id: str, fx: Fixture) -> tuple[bool, Any]:
    """Returns (ok, payload_or_error_detail). ok=False means a non-2xx from
    the engine itself (e.g. 502 AdvisorCallFailed) -- reported as a failed
    grade with the engine's own error detail, not a crash."""
    ask = fx.expect.get("live_setup", {}).get("advisor_ask", {})
    mode = ask.get("mode")
    if mode == "validate":
        resp = client.post("/advisor/validate", json={
            "project_id": project_id, "tool_id": ask["tool_id"], "body": fx.body,
        })
    elif mode == "tollgate":
        resp = client.post("/advisor/ask", json={
            "project_id": project_id, "mode": "tollgate", "phase": ask["phase"],
        })
    else:  # "review" (and any future prose/structured mode driven by artifact_id)
        resp = client.post("/advisor/ask", json={
            "project_id": project_id, "mode": mode, "artifact_id": ask["artifact_id"],
        })
    if resp.status_code != 200:
        detail = resp.json().get("detail", resp.text) if resp.content else resp.text
        return False, f"HTTP {resp.status_code}: {detail}"
    return True, resp.json()


def run_live(fixtures: list[Fixture], engine_url: str) -> tuple[int, dict[str, Any]]:
    try:
        client = httpx.Client(base_url=engine_url, timeout=60.0)
        status_resp = client.get("/health")
        status_resp.raise_for_status()
    except httpx.HTTPError as exc:
        print(f"[run_advisor_evals] could not reach the engine at {engine_url}: {exc}", file=sys.stderr)
        print("[run_advisor_evals] start it with: cd engine && .venv/bin/python -m uvicorn sigma_engine.main:app --port 8000", file=sys.stderr)
        return 1, {"error": "engine_unreachable", "engine_url": engine_url, "detail": str(exc)}

    status = client.post("/advisor/status").json()
    if not status.get("configured"):
        print(
            "[run_advisor_evals] REFUSING to run live evals: the advisor is not configured on this engine "
            f"(model={status.get('model')!r}, configured=False). Live advisor evals need a configured Anthropic "
            "API key -- set one via PUT /advisor/settings or the ANTHROPIC_API_KEY environment variable on the "
            "engine process, then re-run with --live. No advisor calls were made.",
            file=sys.stderr,
        )
        return 1, {"error": "advisor_unconfigured", "engine_url": engine_url, "status": status}

    pins = live_pins(client, status)
    rows: list[dict[str, Any]] = []

    for fx in fixtures:
        project_id = fx.expect.get("live_setup", {}).get("project_id", f"advisor-eval-{fx.fixture_id}")
        try:
            _ensure_project(client, project_id)
            _save_prerequisite_artifacts(client, project_id, fx)
            ok, payload = _call_advisor(client, project_id, fx)
        except httpx.HTTPError as exc:
            rows.append({
                "fixture_id": fx.fixture_id, "tool_id": fx.expect.get("tool_id"), "mode": fx.expect.get("mode"),
                "grade": "fail", "reason": f"setup/call error: {exc}", "project_id": project_id,
            })
            continue

        if not ok:
            rows.append({
                "fixture_id": fx.fixture_id, "tool_id": fx.expect.get("tool_id"), "mode": fx.expect.get("mode"),
                "grade": "fail", "reason": payload, "project_id": project_id,
            })
            continue

        grade = grade_response(fx.expect, payload)
        rows.append({
            "fixture_id": fx.fixture_id, "tool_id": fx.expect.get("tool_id"), "mode": fx.expect.get("mode"),
            "grade": "pass" if grade.passed else "fail", "reason": grade.reason, "project_id": project_id,
            "raw_response": payload,
        })

    print(f"[run_advisor_evals] mode=live  engine={engine_url}  pins={pins}")
    print()
    header = f"{'fixture_id':<34} {'mode':<10} {'grade':<6} reason"
    print(header)
    print("-" * len(header))
    for r in rows:
        print(f"{r['fixture_id']:<34} {r['mode']:<10} {r['grade']:<6} {r['reason']}")
    print()
    n_pass = sum(1 for r in rows if r["grade"] == "pass")
    print(f"[run_advisor_evals] SUMMARY: {n_pass}/{len(rows)} fixture(s) caught by the advisor.")

    output = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "mode": "live",
        "pins": pins,
        "engine_url": engine_url,
        "rows": rows,
        "summary": {"total": len(rows), "passed": n_pass, "failed": len(rows) - n_pass},
    }
    # Mechanical success (every fixture ran and produced a graded result) is
    # exit 0 regardless of individual pass/fail -- an advisor MISSING a
    # defect is exactly the eval signal this suite exists to surface and
    # review, not a runner crash (see README's "what a live exit code
    # means"). Only a run that never produced any rows counts as a failure.
    return (0 if rows else 1), output


# ================================================================
# Output + CLI
# ================================================================


def write_run_output(output: dict[str, Any]) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = RUNS_DIR / f"{date}-{output['mode']}.json"
    path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--live", action="store_true", help="call the live engine's advisor routes (needs a configured Anthropic key)")
    group.add_argument("--mock", action="store_true", help="grade canned responses only -- no network, no engine, no key needed")
    ap.add_argument("--engine-url", default=DEFAULT_ENGINE_URL, help=f"live mode only (default: {DEFAULT_ENGINE_URL})")
    args = ap.parse_args()

    fixtures = load_fixtures()

    if args.mock:
        code, output = run_mock(fixtures)
    else:
        code, output = run_live(fixtures, args.engine_url)

    if "error" not in output:
        path = write_run_output(output)
        print(f"[run_advisor_evals] wrote {path}")
    else:
        print(f"[run_advisor_evals] refused before any run output was produced (see message above).")

    return code


if __name__ == "__main__":
    raise SystemExit(main())
