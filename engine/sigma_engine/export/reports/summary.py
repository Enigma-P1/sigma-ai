"""One-page Project Summary — the artifact both UAT testers came for and
neither got (docs/uat/README.md; docs/uat/PLAN.md Phase 2 item 2.4). Dave:
"I need one page I can put on a desk and talk through in ten minutes."
Mike had nothing to show his manager but a single Pareto.

Six things, printed from whatever the project actually has: the problem
and goal (T-03), the baseline number if the charter recorded one, how
much data came in and from where, the top categories from any saved
tally, the fishbone's causes and how many are verified, and the next
action. Not gated on DMAIC order, not gated on any tool being "done" --
this page renders for a project that has only a charter exactly as
readily as one that has all four.

NAME THE GAPS, NEVER DROP A SECTION. A project with no charter prints "No
charter saved yet" where the problem statement goes -- the section
heading still prints, the honest absence sits under it. Both testers'
sharpest complaint was software that looks complete while hiding what is
missing; a summary that quietly omitted its own gaps would be that exact
failure, wearing a nicer font.

QUOTE, NEVER RE-DERIVE (pack_pdf.py's own rule, restated here because this
page touches more saved artifacts than any other single page in the
suite). Every number below is read straight off a saved artifact's own
field, or off a Computed[...] block that artifact already carries --
verified_causes, ranked_fix_list, and so on. The one exception is the
check-sheet tally, which the CheckSheetArtifact itself does not store
(artifacts/check_sheet.py: "no computed statistics live here"); for that
one section this module calls check_sheet.py's own report tally()/
total_count(), the exact functions T-08's own report renders from,
instead of re-sorting the entries a second way. Nothing on this page ever
forms a second opinion about a number another report already owns.

THE NEXT ACTION IS ADVICE, MARKED AS ADVICE. Every other line on this
page is a fact pulled off a saved artifact. That one line is routing
logic over those facts -- pilot the top-ranked fix if one is ranked,
else rank fixes for a verified cause, else verify a candidate, else find
causes, else write the charter -- and report_theme.recommendation_block
is what keeps a reader from mistaking routing advice for one more
computed result (report_theme.py's own "verdict and recommendation are
different things").

ONE PAGE, BY MEASURED BUDGET, NOT BY HOPE. export/reports/a3.py's
PANEL_BUDGETS shows how this codebase enforces a page limit: a per-section
character/row cap, sized by rendering the real thing and measuring what
fits, with rt.clip() doing the cutting and a pointer to the fuller report
wherever a section truncates. The budgets below (categories shown,
verified causes listed, the charter narrative's clip length) came from
the same exercise, not a guess -- see the constants' own comments.
"""

from __future__ import annotations

from typing import Any

from reportlab.platypus import Paragraph, Table

from ...artifacts.charter import CharterArtifact
from ...artifacts.check_sheet import CheckSheetArtifact
from ...artifacts.fishbone import FishboneArtifact
from ...artifacts.solution_matrix import SolutionMatrixArtifact
from ...datasets import DatasetMeta
from .. import report_theme as rt
from ..charter_pdf_common import base_table_style, esc, fmt_date, fmt_number
from . import check_sheet as check_sheet_report_mod

TOOL_TITLE = "Project Summary"

# Charter narrative clip. Measured, not guessed: a short charter (the demo
# Coffee Bar's) never comes near this budget, so tuning it against one
# understates the real worst case -- a charter written with a genuinely
# long problem/goal sentence, at TEXT_BASE in this page's ~493pt column,
# tips the page onto a second sheet somewhere around 180 characters once
# every other section (categories, causes, provenance) is also carrying
# real content. 160 leaves a real margin below that measured tipping
# point, and it is still a full sentence-and-a-half quoted verbatim, not
# a headline fragment.
PROBLEM_GOAL_CHAR_BUDGET = 160

# How many check-sheet categories print by row before the rest are
# named-but-not-listed. Four is the Pareto "vital few" shape at its most
# common size (stats/pareto.py's own 80% convention rarely needs more to
# tell the story) -- five was tried first and was one row too many once
# every other section was also at its own cap (test_project_summary.py's
# rich-project measurement: five pushed the page onto a second sheet).
TOP_CATEGORIES_SHOWN = 4

# How many verified-cause texts print before the rest are counted rather
# than quoted. A fishbone with a dozen verified causes is real and this
# page must not pretend otherwise, but listing all twelve is a fishbone
# report, not a one-page summary. Three, at the clip width below, is sized
# to hold one line each -- the same rendered-and-measured check that set
# TOP_CATEGORIES_SHOWN.
VERIFIED_CAUSES_SHOWN = 3

# Each verified cause's own text, individually -- short enough that a
# typical cause sentence stays on one line at this page's column width
# (~493pt) rather than wrapping to two; a longer cause is cut, with a
# pointer to the Fishbone report where the whole sentence lives.
_CAUSE_TEXT_CLIP = 90


def _label(text: str, styles: dict) -> Any:
    return Paragraph(text, styles["zone_label"])


def _line(text: str, styles: dict, *, muted: bool = False) -> Any:
    """One section's body line. `muted` is this page's ONLY tone signal --
    it never uses pass/flag/fail color, because a missing artifact is not
    a failed check, it is an honest fact about what has been done so far
    (report_theme.chart()'s own placeholder makes the identical choice for
    a missing picture)."""
    return Paragraph(esc(text), styles["body_muted"] if muted else styles["body"])


# --------------------------------------------------------------------- T-03


def problem_and_goal_text(charter: CharterArtifact) -> str:
    """Same field composition the desktop's own A3 background-panel seed
    uses (desktop/src/tools/a3/a3Seeding.ts's draftNarrativeFor for T-03) --
    one more place that quotes the charter the same way rather than
    inventing a second phrasing of it."""
    p = charter.problem_statement
    magnitude = f"{fmt_number(p.magnitude.number)}{p.magnitude.unit}"
    if p.magnitude.period:
        magnitude += f" ({p.magnitude.period})"
    return f"{p.what} at {p.where}, {p.when}: {magnitude}. Goal: {charter.goal.statement}"


def baseline_text(charter: CharterArtifact) -> str | None:
    """None means "charter exists but recorded no baseline" -- goal.
    baseline_value is optional on the schema (a SMART goal can be typed
    before a baseline is measured), which is exactly the "if there is one"
    the task brief asks this section to honor."""
    g = charter.goal
    if g.baseline_value is None:
        return None
    return f"{fmt_number(g.baseline_value)}{g.unit} → {fmt_number(g.target_value)}{g.unit} by {fmt_date(g.target_date)}"


def _problem_goal_baseline_section(charter: CharterArtifact | None, styles: dict) -> list[Any]:
    """PROBLEM & GOAL and BASELINE share one zone label. Both are the
    charter's -- problem_statement/goal.statement narrative, then goal's
    own baseline_value/target_value pair right under it -- and one desk-
    facing page reads a goal and its baseline as one fact, not two; the
    task's two bullets both still print, in full, they just no longer pay
    for a second zone label's spacing (the rendered-and-measured page
    budget: see PROBLEM_GOAL_CHAR_BUDGET's own comment)."""
    out = [_label("PROBLEM, GOAL & BASELINE", styles)]
    if charter is None:
        out.append(_line("No charter saved yet.", styles, muted=True))
        return out
    problem_goal = rt.clip(problem_and_goal_text(charter), PROBLEM_GOAL_CHAR_BUDGET)
    out.append(_line(problem_goal, styles))
    baseline = baseline_text(charter)
    if baseline is None:
        out.append(_line("No baseline number recorded on the charter yet.", styles, muted=True))
    else:
        out.append(_line(f"Baseline → target: {baseline}", styles))
    return out


# --------------------------------------------------------------- dataset(s)


def dataset_text(datasets: list[DatasetMeta]) -> str | None:
    """None means no dataset has ever been saved to this project. Picks the
    most recently created dataset -- list_datasets is already sorted
    oldest-first (datasets.py), so the last entry is the newest, which for
    a derivation chain (recode/derive_column/edit) is also the current tip
    of whatever cleanup has happened since the raw upload."""
    if not datasets:
        return None
    latest = datasets[-1]
    text = f"{latest.row_count:,} row(s) imported from {latest.source_filename}"
    if len(datasets) > 1:
        text += f" (most recent of {len(datasets)} datasets saved in this project)"
    return text


def _dataset_section(datasets: list[DatasetMeta], styles: dict) -> list[Any]:
    out = [_label("DATA IMPORTED", styles)]
    text = dataset_text(datasets)
    if text is None:
        out.append(_line("No dataset imported yet.", styles, muted=True))
    else:
        out.append(_line(text, styles))
    return out


# ------------------------------------------------------------- T-08 / Pareto


def categories_rows(check_sheet: CheckSheetArtifact) -> tuple[str, list[tuple[str, int, float]]]:
    """(intro line, up to TOP_CATEGORIES_SHOWN (label, count, share) rows),
    off check_sheet.py's own tally()/total_count() -- reused, not
    recomputed (module docstring). Zero-count categories (tally() prints
    every declared category, even untallied ones, on T-08's own report)
    are dropped here first: a Pareto ranking has nothing to say about a
    category nobody hit yet, and keeping them out of the count is what
    keeps "N categories, top 5 shown" honest rather than off-by-however-
    many-are-empty."""
    total = check_sheet_report_mod.total_count(check_sheet)
    if total == 0:
        return "Check sheet on file, but nothing has been tallied yet.", []
    nonzero = [(label, count) for label, count in check_sheet_report_mod.tally(check_sheet) if count > 0]
    shown = nonzero[:TOP_CATEGORIES_SHOWN]
    intro = f"{total:,} tally mark(s) across {len(nonzero)} categor{'y' if len(nonzero) == 1 else 'ies'} with at least one."
    if len(nonzero) > len(shown):
        intro += f" Top {len(shown)} shown here; the full ranking is in the Check Sheet report."
    return intro, [(label, count, count / total) for label, count in shown]


def _categories_table(rows: list[tuple[str, int, float]], styles: dict, content_width: float) -> Any:
    header = [Paragraph(esc(h), styles["table_header"]) for h in ("Category", "Count", "Share")]
    body = [
        [
            Paragraph(esc(rt.clip(label, 60)), styles["table_cell"]),
            Paragraph(f"{count:,}", styles["table_cell_num"]),
            Paragraph(f"{share * 100:.1f}%", styles["table_cell_num"]),
        ]
        for label, count, share in rows
    ]
    fracs = (0.6, 0.2, 0.2)
    table = Table([header, *body], colWidths=[content_width * f for f in fracs], repeatRows=1, hAlign="LEFT")
    table.setStyle(base_table_style())
    return table


def _categories_section(check_sheet: CheckSheetArtifact | None, styles: dict, content_width: float) -> list[Any]:
    out = [_label("TOP CATEGORIES", styles)]
    if check_sheet is None:
        out.append(_line("No categorized tally saved yet.", styles, muted=True))
        return out
    intro, rows = categories_rows(check_sheet)
    out.append(_line(intro, styles, muted=not rows))
    if rows:
        out.append(_categories_table(rows, styles, content_width))
    return out


# --------------------------------------------------------------------- T-15


def fishbone_lines(fishbone: FishboneArtifact) -> tuple[str, list[str]]:
    """(intro line, up to VERIFIED_CAUSES_SHOWN clipped verified-cause
    texts) off FishboneArtifact.verified_causes -- a Computed[...] field
    the artifact already carries (fishbone.py's compute_verified_causes),
    never recomputed here."""
    total = len(fishbone.causes)
    if total == 0:
        return "The fishbone is open with no causes on it yet.", []
    verified = fishbone.verified_causes.value if fishbone.verified_causes else None
    verified_count = verified.count if verified else 0
    intro = f"{total} cause(s) on the fishbone; {verified_count} verified."
    if verified is None or verified_count == 0:
        return intro, []
    shown = list(verified.causes)[:VERIFIED_CAUSES_SHOWN]
    lines = [rt.clip(c.text, _CAUSE_TEXT_CLIP) for c in shown]
    if verified_count > len(shown):
        lines.append(f"+{verified_count - len(shown)} more verified cause(s) -- see the Fishbone report.")
    return intro, lines


def _fishbone_section(fishbone: FishboneArtifact | None, styles: dict) -> list[Any]:
    out = [_label("FISHBONE CAUSES", styles)]
    if fishbone is None:
        out.append(_line("No fishbone saved yet.", styles, muted=True))
        return out
    intro, lines = fishbone_lines(fishbone)
    out.append(_line(intro, styles, muted=not fishbone.causes))
    for line in lines:
        out.append(Paragraph(f"• {esc(line)}", styles["card_item"]))
    return out


# ------------------------------------------------------------- next action


def next_action_text(
    charter: CharterArtifact | None, fishbone: FishboneArtifact | None, solution_matrix: SolutionMatrixArtifact | None
) -> str:
    """Routing advice over what is already on file, cascading from the
    most decision-ready saved artifact down to "start at the charter" --
    never a number this function invents, only a choice of which already-
    computed fact to point at next (module docstring's "advice, marked as
    advice")."""
    if solution_matrix is not None and solution_matrix.ranked_fix_list is not None:
        ranked = solution_matrix.ranked_fix_list.value.ranked
        if ranked:
            top = ranked[0]
            return (
                f'Top-ranked countermeasure on file: "{top.name}" ({top.quadrant.replace("_", " ")}). Pilot it '
                "and bring the before/after numbers back."
            )
    if fishbone is not None:
        verified = fishbone.verified_causes.value if fishbone.verified_causes else None
        verified_count = verified.count if verified else 0
        if verified_count >= 1:
            return (
                f"{verified_count} verified cause(s) on the fishbone -- rank countermeasures for them in the "
                "Solution Matrix (T-18) next."
            )
        if fishbone.causes:
            return "Causes are on the board but none are verified yet -- attach evidence to a candidate cause."
        return "The fishbone is open with no causes on it yet -- add candidate causes on the branches that fit."
    if charter is not None:
        return "The charter is on file -- bring in data and find out where the gap actually concentrates."
    return "No charter saved yet -- start there: state the problem and the goal in measurable, dated terms."


# ----------------------------------------------------------------- the page


def build_story(
    *,
    project_name: str,
    charter: CharterArtifact | None,
    fishbone: FishboneArtifact | None,
    solution_matrix: SolutionMatrixArtifact | None,
    check_sheet: CheckSheetArtifact | None,
    datasets: list[DatasetMeta],
    provenance_rows: list[tuple[str, str]],
    exported_at: str,
    content_width: float,
) -> list[Any]:
    styles = rt.report_styles()

    story: list[Any] = []
    story += rt.header(
        project_name=project_name,
        tool_id="Summary",
        tool_title=TOOL_TITLE,
        version=None,  # not one saved artifact's version -- this rolls several up live, on every request
        styles=styles,
        content_width=content_width,
    )

    story.append(rt.keep(_problem_goal_baseline_section(charter, styles)))
    story.append(rt.keep(_dataset_section(datasets, styles)))
    story.append(rt.keep(_categories_section(check_sheet, styles, content_width)))
    story.append(rt.keep(_fishbone_section(fishbone, styles)))

    story += rt.recommendation_block(next_action_text(charter, fishbone, solution_matrix), styles, content_width)

    story.append(rt.keep(rt.provenance(provenance_rows, styles, content_width, exported_at=exported_at)))
    return story
