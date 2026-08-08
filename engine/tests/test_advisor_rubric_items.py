"""rubric_items.py: the tool_id -> rubric item IDs table and the item-text
transcription cross-check each other (every id one table cites resolves in
the other), and render_rubric_items_block degrades honestly for a tool
with no mapping instead of crashing.

M5 exit critic, Fix 7: none of the above ever checks RUBRIC_ITEM_TEXT
against the actual locked doc it claims to transcribe
(docs/green-belt-rubric.md) -- only internal self-consistency. The exit
critic did that comparison BY HAND and found 0 mismatches; the tests below
encode that same method (re-extract every item's title/Grades/Pass-means
from the doc on disk, strip markdown emphasis on BOTH sides since the doc
uses inline **bold**/*italic* that the plain-text transcription doesn't
carry, and diff) so a future edit to the locked doc that isn't matched by a
re-transcription in rubric_items.py fails CI instead of silently drifting.
Repo-root resolution follows test_prompt_pack.py's own PROMPTS_DIR pattern
(Path(__file__).resolve().parents[2]) -- reading docs/, never writing it,
matching this task's own "do not touch docs/" rule.
"""

from __future__ import annotations

import re
from pathlib import Path

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


# ================================================================
# Fix 7 (M5 exit critic): RUBRIC_ITEM_TEXT vs. docs/green-belt-rubric.md
# itself, not just its own internal consistency (module docstring above).
# ================================================================

DOC_PATH = Path(__file__).resolve().parents[2] / "docs" / "green-belt-rubric.md"

# Doc shape (confirmed by inspection of docs/green-belt-rubric.md): each
# item is a "#### R-XXX-NN — Title" heading; its body carries a
# "**Grades:** ..." line and a "**Pass means:**" label followed by a
# numbered list, terminated by the next "**Some Label:**" bold-label line
# (e.g. "**Needs work when:**", "**Fail / invalidates when:**").
_ITEM_HEADING_RE = re.compile(r"^#### (R-[A-Z]+-\d+) — (.+)$", re.MULTILINE)
_GRADES_LINE_RE = re.compile(r"^\*\*Grades:\*\* (.+)$", re.MULTILINE)
_PASS_MEANS_START_RE = re.compile(r"^\*\*Pass means:\*\*$", re.MULTILINE)
_NEXT_BOLD_LABEL_RE = re.compile(r"^\*\*[A-Za-z][^*]*:\*\*", re.MULTILINE)
_PASS_MEANS_ITEM_RE = re.compile(r"^\d+\. (.+)$", re.MULTILINE)
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")


def _strip_markdown_emphasis(text: str) -> str:
    """Some Grades lines and Pass-means items in the doc use inline
    **bold**/*italic* markdown that RUBRIC_ITEM_TEXT's plain-text
    transcription doesn't carry (by design -- it transcribes the words, not
    the doc's own emphasis markup). Applied to BOTH the doc-extracted text
    and the RUBRIC_ITEM_TEXT side before comparing, so a diff never fires
    on emphasis alone -- confirmed empirically while designing this test:
    without stripping both sides, comparing the doc's raw text against
    RUBRIC_ITEM_TEXT produces mismatches purely from markdown, not content;
    with both sides stripped, the diff is 0, matching the exit critic's own
    by-hand count."""
    text = _BOLD_RE.sub(r"\1", text)
    text = _ITALIC_RE.sub(r"\1", text)
    return text


def _extract_rubric_items_from_doc(doc_text: str) -> dict[str, tuple[str, str, tuple[str, ...]]]:
    """item_id -> (title, grades_line, pass_means_items), each already
    markdown-emphasis-stripped, walking every "#### R-XXX-NN — Title"
    section from the heading to the next heading (or EOF)."""
    headings = list(_ITEM_HEADING_RE.finditer(doc_text))
    sections: dict[str, tuple[str, str, tuple[str, ...]]] = {}
    for i, heading_match in enumerate(headings):
        item_id = heading_match.group(1)
        title = _strip_markdown_emphasis(heading_match.group(2).strip())
        start = heading_match.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(doc_text)
        body = doc_text[start:end]

        grades_match = _GRADES_LINE_RE.search(body)
        grades = _strip_markdown_emphasis(grades_match.group(1).strip()) if grades_match else ""

        pass_means_start = _PASS_MEANS_START_RE.search(body)
        pass_means: tuple[str, ...] = ()
        if pass_means_start:
            rest = body[pass_means_start.end():]
            next_label = _NEXT_BOLD_LABEL_RE.search(rest)
            pass_means_block = rest[: next_label.start()] if next_label else rest
            pass_means = tuple(
                _strip_markdown_emphasis(m.strip()) for m in _PASS_MEANS_ITEM_RE.findall(pass_means_block)
            )

        sections[item_id] = (title, grades, pass_means)
    return sections


def test_doc_extraction_finds_all_39_items():
    # A sanity check on the extraction regexes themselves, independent of
    # RUBRIC_ITEM_TEXT -- if this ever drops below 39, the doc's own
    # heading shape changed and the regexes need updating, not the diff
    # test below (which would otherwise just report 39 "missing" items).
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    extracted = _extract_rubric_items_from_doc(doc_text)
    assert len(extracted) == 39, f"expected 39 doc sections, found {len(extracted)}: {sorted(extracted)}"


def test_rubric_item_text_matches_the_locked_doc_on_disk():
    """The load-bearing binding this fix adds: RUBRIC_ITEM_TEXT's title,
    Grades line, and Pass-means items for every one of the 39 rubric items
    must match docs/green-belt-rubric.md exactly (modulo markdown emphasis
    -- see _strip_markdown_emphasis). A future edit to the locked doc that
    isn't matched by a re-transcription here fails this test until it is."""
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    doc_items = _extract_rubric_items_from_doc(doc_text)

    mismatches: list[str] = []
    for item_id, item in RUBRIC_ITEM_TEXT.items():
        if item_id not in doc_items:
            mismatches.append(f"{item_id}: in RUBRIC_ITEM_TEXT but no matching '#### {item_id} — ...' heading in the doc")
            continue
        doc_title, doc_grades, doc_pass_means = doc_items[item_id]
        py_title = _strip_markdown_emphasis(item.title)
        py_grades = _strip_markdown_emphasis(item.grades)
        py_pass_means = tuple(_strip_markdown_emphasis(p) for p in item.pass_means)

        if doc_title != py_title:
            mismatches.append(f"{item_id} title: doc={doc_title!r} py={py_title!r}")
        if doc_grades != py_grades:
            mismatches.append(f"{item_id} grades: doc={doc_grades!r} py={py_grades!r}")
        if doc_pass_means != py_pass_means:
            mismatches.append(
                f"{item_id} pass_means: doc has {len(doc_pass_means)} item(s), py has {len(py_pass_means)}: "
                f"doc={doc_pass_means!r} py={py_pass_means!r}"
            )

    for item_id in doc_items:
        if item_id not in RUBRIC_ITEM_TEXT:
            mismatches.append(f"{item_id}: has a doc heading but no RUBRIC_ITEM_TEXT entry")

    assert mismatches == [], "RUBRIC_ITEM_TEXT has drifted from docs/green-belt-rubric.md:\n" + "\n".join(mismatches)
