"""Minimal targeted parser for the held-out scenario specs' YAML
frontmatter (evals/scenarios/{s1-helpdesk,s2-library}/spec.md) -- read-only
input. Deliberately NOT a general YAML parser (no PyYAML in engine/.venv,
and the harness must run with only what that venv already has): this
reads exactly the three fields the coverage checker needs
(`scenario_id`, `in_scope_tools`, `na_tools`'s keys) out of the specific,
narrow subset of YAML these two files actually use -- a flow-style list
(`[T-01, T-02, ...]`, possibly wrapped across lines) and a block mapping
of `T-nn: "reason"` rows.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_FRONTMATTER = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
_SCENARIO_ID = re.compile(r'^scenario_id:\s*(\S+)\s*$', re.MULTILINE)
_TOOL_ID = re.compile(r"\bT-\d+\b")
_NA_ROW = re.compile(r'^\s{2}(T-\d+):\s*"(.*)"\s*$')


@dataclass(frozen=True)
class ScenarioSpec:
    scenario_id: str
    in_scope_tools: tuple[str, ...]
    na_tools: dict[str, str]


def _frontmatter_text(spec_path: Path) -> str:
    text = spec_path.read_text(encoding="utf-8")
    m = _FRONTMATTER.match(text)
    if not m:
        raise ValueError(f"{spec_path}: no YAML frontmatter block found (expected a leading '---' ... '---')")
    return m.group(1)


def _flow_list_after(key: str, fm: str) -> tuple[str, ...]:
    """`key: [A, B,\n        C, D]` -- flow lists may wrap across lines in
    these specs; grab from `key:` up to the matching `]` and pull every
    T-nn token out of that span, in order, deduped."""
    start = re.search(rf"^{re.escape(key)}:\s*\[", fm, re.MULTILINE)
    if not start:
        raise ValueError(f"frontmatter key {key!r} not found (or not a flow list) in this spec")
    close = fm.index("]", start.end())
    span = fm[start.end():close]
    seen: list[str] = []
    for tid in _TOOL_ID.findall(span):
        if tid not in seen:
            seen.append(tid)
    return tuple(seen)


def _na_tools_block(fm: str) -> dict[str, str]:
    """`na_tools:` followed by 2-space-indented `T-nn: "reason"` rows,
    ending at the next top-level (unindented) key."""
    m = re.search(r"^na_tools:\s*$", fm, re.MULTILINE)
    if not m:
        raise ValueError("frontmatter key 'na_tools' not found")
    out: dict[str, str] = {}
    for line in fm[m.end():].splitlines():
        if line.strip() == "":
            continue
        if not line.startswith("  "):
            break  # dedented back to the next top-level key
        row = _NA_ROW.match(line)
        if row:
            out[row.group(1)] = row.group(2)
    return out


def parse_scenario_spec(spec_path: Path) -> ScenarioSpec:
    fm = _frontmatter_text(spec_path)
    sid = _SCENARIO_ID.search(fm)
    if not sid:
        raise ValueError(f"{spec_path}: 'scenario_id' not found in frontmatter")
    return ScenarioSpec(
        scenario_id=sid.group(1),
        in_scope_tools=_flow_list_after("in_scope_tools", fm),
        na_tools=_na_tools_block(fm),
    )
