"""rubric_items.py: the tool_id -> rubric item IDs table and the item-text
transcription cross-check each other (every id one table cites resolves in
the other), and render_rubric_items_block degrades honestly for a tool
with no mapping instead of crashing."""

from __future__ import annotations

from sigma_engine.advisor.rubric_items import RUBRIC_ITEM_TEXT, TOOL_RUBRIC_ITEMS, render_rubric_items_block
from sigma_engine.registry import ARTIFACT_REGISTRY


def test_every_tool_rubric_item_id_resolves_in_rubric_item_text():
    for tool_id, item_ids in TOOL_RUBRIC_ITEMS.items():
        for item_id in item_ids:
            assert item_id in RUBRIC_ITEM_TEXT, f"{tool_id} cites {item_id!r}, which has no RUBRIC_ITEM_TEXT entry"


def test_every_rubric_item_text_entry_is_cited_by_at_least_one_tool():
    cited = {item_id for ids in TOOL_RUBRIC_ITEMS.values() for item_id in ids}
    uncited = set(RUBRIC_ITEM_TEXT) - cited
    assert uncited == set(), f"rubric items transcribed but never cited by any tool: {uncited}"


def test_all_39_locked_rubric_items_are_present():
    # docs/green-belt-rubric.md §1's own count: "the 39 proposed by the
    # traceability matrix... R-DEF-01..08, R-MEA-01..11, R-ANA-01..06,
    # R-IMP-01..05, R-CTL-01..06, R-WRAP-01..03."
    assert len(RUBRIC_ITEM_TEXT) == 39
    prefixes = {"R-DEF": 8, "R-MEA": 11, "R-ANA": 6, "R-IMP": 5, "R-CTL": 6, "R-WRAP": 3}
    for prefix, count in prefixes.items():
        matching = [i for i in RUBRIC_ITEM_TEXT if i.startswith(prefix + "-")]
        assert len(matching) == count, f"{prefix}: expected {count}, got {len(matching)} ({matching})"


def test_rubric_item_text_carries_title_grades_and_nonempty_pass_means():
    for item_id, item in RUBRIC_ITEM_TEXT.items():
        assert item.item_id == item_id
        assert item.title.strip()
        assert item.grades.strip()
        assert len(item.pass_means) >= 1
        assert all(p.strip() for p in item.pass_means)


def test_every_artifact_registry_tool_id_that_has_helper_content_is_in_tool_rubric_items():
    # Every real tool_id (T-01..T-25 minus T-13/T-14, which have no saved
    # artifact -- rubric_items.py's own comment) should have a rubric
    # mapping; a gap here would silently starve "review" mode for that tool.
    for tool_id in ARTIFACT_REGISTRY:
        assert tool_id in TOOL_RUBRIC_ITEMS, f"{tool_id} is a real artifact tool but has no TOOL_RUBRIC_ITEMS entry"
        assert len(TOOL_RUBRIC_ITEMS[tool_id]) >= 1


def test_render_rubric_items_block_includes_id_and_pass_means_text():
    block = render_rubric_items_block("T-02")
    assert "R-DEF-05" in block
    assert "COPQ is built from named cost buckets" in block


def test_render_rubric_items_block_lists_every_mapped_item_for_a_multi_item_tool():
    block = render_rubric_items_block("T-03")
    for item_id in TOOL_RUBRIC_ITEMS["T-03"]:
        assert item_id in block


def test_render_rubric_items_block_degrades_honestly_for_an_unmapped_tool():
    block = render_rubric_items_block("T-99")
    assert "No rubric items are mapped" in block
    assert "T-99" in block
