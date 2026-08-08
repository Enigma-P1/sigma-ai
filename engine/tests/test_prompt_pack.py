"""The portable prompt pack's consistency tests (M5 unit 4, PLAN §5.2).

The pack lives at the repo root (prompts/) as plain markdown a user copies
into any chatbot; the engine ships the same 31 texts as constants in
advisor/prompt_pack.py (generated together with the files) so the packaged
app needs no filesystem access to prompts/. These tests pin all of it to
the locked sources -- rubric_items.py's TOOL_RUBRIC_ITEMS/RUBRIC_ITEM_TEXT
and a3.py's TOLLGATE_QUESTIONS -- so any drift (an edited file, a stale
regenerated module, a rubric change not propagated) fails CI instead of
shipping a pack that quietly disagrees with the app.

Repo-root access follows factories.py's own DEMO_CHARTER_PATH pattern:
Path(__file__).resolve().parents[2] -- these tests read the working repo,
which is exactly the point (the pack is a repo artifact, not test data).
"""

from __future__ import annotations

from pathlib import Path

from sigma_engine.advisor import prompt_pack
from sigma_engine.advisor.rubric_items import RUBRIC_ITEM_TEXT, TOOL_RUBRIC_ITEMS
from sigma_engine.artifacts.a3 import TOLLGATE_PHASES, TOLLGATE_QUESTIONS

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"
TOOLS_DIR = PROMPTS_DIR / "tools"
TOLLGATES_DIR = PROMPTS_DIR / "tollgates"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---- Inventory: exactly 25 + 6 + README ----


def test_pack_inventory_is_exactly_25_tools_6_tollgates_and_a_readme():
    assert (PROMPTS_DIR / "README.md").is_file()
    tool_files = sorted(p.name for p in TOOLS_DIR.glob("*.md"))
    tollgate_files = sorted(p.name for p in TOLLGATES_DIR.glob("*.md"))
    assert len(tool_files) == 25, tool_files
    assert len(tollgate_files) == 6, tollgate_files
    # No strays anywhere in the pack -- the three lists above are the pack.
    all_md = sorted(p.relative_to(PROMPTS_DIR).as_posix() for p in PROMPTS_DIR.rglob("*"))
    expected = sorted(
        ["README.md", "tools", "tollgates"]
        + [f"tools/{name}" for name in tool_files]
        + [f"tollgates/{name}" for name in tollgate_files]
    )
    assert all_md == expected, all_md


def test_tool_filenames_carry_every_tool_id_once():
    names = {p.name for p in TOOLS_DIR.glob("*.md")}
    for tool_id in TOOL_RUBRIC_ITEMS:  # T-01..T-25, the locked inventory
        matching = [n for n in names if n.startswith(f"{tool_id}-")]
        assert len(matching) == 1, f"{tool_id}: expected exactly one file, got {matching}"


def test_tollgate_filenames_are_the_six_phases_lowercased():
    names = sorted(p.name for p in TOLLGATES_DIR.glob("*.md"))
    assert names == sorted(f"{phase.lower()}.md" for phase in TOLLGATE_PHASES)


# ---- The fixed footer: byte-identical tail of every file in the pack ----


def test_every_pack_file_ends_with_the_fixed_footer_byte_identical():
    footer_tail = prompt_pack.FIXED_FOOTER + "\n"
    files = [PROMPTS_DIR / "README.md", *TOOLS_DIR.glob("*.md"), *TOLLGATES_DIR.glob("*.md")]
    assert len(files) == 32
    for path in files:
        assert _read(path).endswith(footer_tail), f"{path.name} does not end with the fixed footer"


def test_the_footer_states_the_weaker_guarantees_and_the_authority_rule():
    footer = prompt_pack.FIXED_FOOTER
    for required in (
        "no schema\nenforcement, no grounding check, and no injection defense",
        "numbers that come back from a chatbot are not authoritative",
        "the app's computed results are the record",
    ):
        assert required in footer, f"footer is missing: {required!r}"


# ---- Tool prompts pinned to rubric_items.py (the locked rubric source) ----


def test_every_tool_file_contains_its_mapped_rubric_item_ids_and_pass_bars():
    for tool_id, item_ids in TOOL_RUBRIC_ITEMS.items():
        path = next(TOOLS_DIR.glob(f"{tool_id}-*.md"))
        content = _read(path)
        for item_id in item_ids:
            item = RUBRIC_ITEM_TEXT[item_id]
            assert item_id in content, f"{path.name} is missing rubric item id {item_id}"
            assert item.title in content, f"{path.name} is missing {item_id}'s title"
            for pass_text in item.pass_means:
                assert pass_text in content, f"{path.name} is missing a {item_id} pass bar verbatim"


# ---- Tollgate prompts pinned to a3.py's TOLLGATE_QUESTIONS ----


def test_every_tollgate_file_contains_its_phase_questions_verbatim():
    for phase in TOLLGATE_PHASES:
        content = _read(TOLLGATES_DIR / f"{phase.lower()}.md")
        for question in TOLLGATE_QUESTIONS[phase]:
            assert question.question_id in content, f"{phase}: missing {question.question_id}"
            assert question.text in content, f"{phase}: missing question text verbatim: {question.text!r}"
        assert "go-with-actions" in content or "Go with actions" in content
        assert "No go" in content


# ---- The generated engine module matches the files byte-for-byte ----


def test_prompt_pack_module_matches_the_files_byte_for_byte():
    assert set(prompt_pack.TOOL_PROMPT_FILES) == set(TOOL_RUBRIC_ITEMS)
    for tool_id, (filename, content) in prompt_pack.TOOL_PROMPT_FILES.items():
        assert content == _read(TOOLS_DIR / filename), f"prompt_pack.py stale for {tool_id} ({filename})"

    assert set(prompt_pack.TOLLGATE_PROMPT_FILES) == set(TOLLGATE_PHASES)
    for phase, (filename, content) in prompt_pack.TOLLGATE_PROMPT_FILES.items():
        assert content == _read(TOLLGATES_DIR / filename), f"prompt_pack.py stale for {phase} ({filename})"


def test_prompt_text_accessors_return_the_text_or_none():
    assert prompt_pack.tool_prompt_text("T-01") == prompt_pack.TOOL_PROMPT_FILES["T-01"][1]
    assert prompt_pack.tool_prompt_text("T-99") is None
    assert prompt_pack.tollgate_prompt_text("Improve") == prompt_pack.TOLLGATE_PROMPT_FILES["Improve"][1]
    assert prompt_pack.tollgate_prompt_text("NotAPhase") is None
