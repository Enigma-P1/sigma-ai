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

TOP CATEGORIES HAS TWO POSSIBLE SOURCES, NEVER A GUESSED ONE. A check
sheet (T-08) is the tool this section was built for, but the app now also
lets a supervisor import a file and chart it with no project setup at
all (docs/RELEASE-v0.2.md's data-first front door) -- and that Pareto is
computed on the fly and saved nowhere, so a project that has one but no
check sheet used to print "No categorized tally saved yet" over work the
user had just watched the app do. The fix is not this module inventing a
second tally: routes/export.py's POST body carries the user's OWN T-14
selection (dataset id + category column, read back from
chartSetViewStore.ts), and this module's dataset_categories_headline()
states stats/pareto.py's compute_pareto() vital-few finding for that
exact column -- the same fields the on-screen chart's own headline reads,
quoted again here, which is reuse, not a second opinion. Guessing a
column this route was never told would be exactly that second opinion,
so an absent or invalid selection prints the honest gap instead of a
guess (see _categories_section's own comment for which source wins when
both a check sheet and a valid selection exist -- and for why a captured
chart image REPLACES the category table there rather than sitting beside
it).

QUOTE, NEVER RE-DERIVE (pack_pdf.py's own rule, restated here because this
page touches more saved artifacts than any other single page in the
suite). Every number below is read straight off a saved artifact's own
field, off a Computed[...] block that artifact already carries --
verified_causes, ranked_fix_list, and so on -- or, for the check-sheet
tally, off check_sheet.py's own report tally()/total_count(), the exact
functions T-08's own report renders from, instead of re-sorting the
entries a second way. The dataset-Pareto path above is the same
discipline applied to a number that has no saved artifact to quote:
compute_pareto() is engine code, not this module's, so calling it again
is still quoting the engine, not re-deriving. Nothing on this page ever
forms a second opinion about a number another report -- or the chart
this project's own screen already drew -- already owns.

THE NEXT ACTION IS ADVICE, MARKED AS ADVICE. Every other line on this
page is a fact pulled off a saved artifact. That one line is routing
logic over those facts -- pilot the top-ranked fix if one is ranked,
else rank fixes for a verified cause, else verify a candidate, else find
causes, else write the charter, with an imported-but-uncharted dataset
getting its own rung so it is acknowledged rather than talked over -- and
report_theme.recommendation_block is what keeps a reader from mistaking
routing advice for one more computed result (report_theme.py's own
"verdict and recommendation are different things"). The one piece of
charter data this line is allowed to add is WHO and BY WHEN: the
charter's own process_owner and goal.target_date, because a suggestion
with no owner and no date is not a next step a supervisor can hand to
anyone -- still never a number this function invents, only two fields
already sitting on the artifact it is already reading.

ONE PAGE, BY MEASURED BUDGET, NOT BY HOPE. export/reports/a3.py's
PANEL_BUDGETS shows how this codebase enforces a page limit: a per-section
character/row cap, sized by rendering the real thing and measuring what
fits, with rt.clip() doing the cutting and a pointer to the fuller report
wherever a section truncates. The budgets below (categories shown,
verified causes listed, the charter narrative's clip lengths) came from
the same exercise, not a guess -- see the constants' own comments. The
problem and the goal are two separate budgets, not one shared between
them, because a single combined clip can cut the ENTIRE second sentence
rather than trim it -- found rendering a real charter, where the whole
"Goal: ..." sentence disappeared behind one ellipsis, with nothing on the
page to show it had ever been there. Each sentence gets its own room and
its own, word-boundary clip, so the worst case is a shortened sentence,
never a silently absent one.
"""

from __future__ import annotations

from typing import Any, NamedTuple

from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table

from ...artifacts.charter import CharterArtifact
from ...artifacts.check_sheet import CheckSheetArtifact
from ...artifacts.fishbone import FishboneArtifact
from ...artifacts.solution_matrix import SolutionMatrixArtifact
from ...datasets import DatasetMeta
from ...stats.pareto import ParetoResult
from .. import pdf_theme, report_theme as rt
from ..charter_pdf_common import base_table_style, esc, fmt_date, fmt_number
from . import check_sheet as check_sheet_report_mod

TOOL_TITLE = "Project Summary"


class DatasetParetoSource(NamedTuple):
    """The user's own T-14 selection, resolved: which column of which
    imported file, and the engine's compute_pareto tally over it -- routes/
    export.py's _resolve_dataset_pareto builds this (dataset id + column
    from the request body, both re-checked against the project's own saved
    datasets), and it is the one input to this module that is NOT read
    straight off a saved artifact, because a raw import's Pareto has none
    (module docstring's "TOP CATEGORIES HAS TWO POSSIBLE SOURCES"). None
    everywhere downstream means "no valid selection was sent" -- an absent
    body, an unknown dataset id, an unknown column, or a column with
    nothing left to tally once blanks are dropped -- and every one of
    those falls through to the check sheet or the honest gap, never a 500
    (task rule: an unknown dataset id or column degrades, it does not
    break the page)."""

    source_filename: str
    column: str
    pareto: ParetoResult


# Two independent clips, not one shared budget -- see the module
# docstring's last paragraph for why a single combined budget is the wrong
# shape. Split close to even because neither sentence is reliably the
# shorter one project to project.
#
# These were 90/70, and at 90/70 the rich-project worst case printed
# "...across every one of the eighteen..." and stopped. A re-reviewer put
# it better than the measurement did: the page had already given up on
# being complete, and a reader who sees one sentence cut mid-clause stops
# trusting the ones that were not. The clip is a last resort against an
# essay pasted into a charter field, not the normal case, and at 90 it was
# firing on ordinary sentences.
#
# What paid for the raise was not a new budget, it was two sections that
# were spending more than they were worth: PROVENANCE as a titled
# five-row table (_provenance_footer, ~110pt) and a headline that spelled
# out category names the chart underneath was about to label
# (DATASET_PARETO_HEADLINE_NAMES_CHARS, ~54pt). Re-measured against the
# same worst case afterwards: 200/170 fits with the chart at
# SUMMARY_CHART_MAX_HEIGHT, and so does 260/220 -- about two lines of
# slack held back deliberately, because a summary that reprints a
# 260-character problem statement verbatim has become the charter it is
# supposed to summarise.
PROBLEM_CHAR_BUDGET = 200
GOAL_CHAR_BUDGET = 170

# The dataset-Pareto chart's own height cap, distinct from report_theme's
# report-wide MAX_CHART_HEIGHT: that budget assumes the chart IS zone 2 of
# the page, true for a per-tool report and false here, where TOP
# CATEGORIES shares one page with four other zones. It can still afford to
# be generous -- the chart REPLACES the category table when it is shown
# (_categories_section), never sits beside it, so this is the only extra
# cost TOP CATEGORIES pays over the no-chart case, not an addition on top
# of the table's own height. Rendered and measured against the same
# rich-project worst case as PROBLEM_CHAR_BUDGET above; a manager reading
# bar labels across a desk is the reason this stays close to a per-tool
# report's own MAX_CHART_HEIGHT rather than shrinking to a thumbnail.
#
# 160 rather than the 220 the worst case would actually allow, because the
# last 60pt of chart cost more than they were worth: report_theme.chart()
# preserves the image's aspect ratio, so height buys width at 1.79:1, and
# at 220 the picture is ~390pt wide but PROBLEM_CHAR_BUDGET has to fall
# back to 90 and clip both charter sentences mid-word. At 160 the chart is
# ~286pt -- about four inches printed, which is a normal figure in a
# report someone reads at a desk -- and the sentences above it are whole.
# A bigger picture of the problem is not worth a truncated statement OF
# the problem.
SUMMARY_CHART_MAX_HEIGHT = 160.0

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


def _n(count: int, singular: str, plural: str | None = None) -> str:
    """"612 rows", "1 row" -- never "612 row(s)".

    The parenthesised plural is how a program hedges when it does not know
    the count at the time the sentence is written. This page knows the
    count. Everywhere else in the app "row(s)" is a fair shorthand between
    the tool and the analyst driving it, but a re-reviewer reading this
    page as a manager's handout named the same tic in three places and
    called it what it is: tool residue, the thing a supervisor deletes
    before sending the page upward. Cheap to remove, and the whole point of
    this artifact is that nothing needs deleting before it is sent."""
    return f"{count:,} {singular if count == 1 else (plural or singular + 's')}"


def _provenance_footer(rows: list[tuple[str, str]], styles: dict, exported_at: str) -> list[Any]:
    """Provenance as a footnote, not as a fifth section.

    report_theme.provenance() renders a labelled two-column table, which is
    right for a per-tool report: there the reader came to check one number
    and the label column is how they find its row. This page is not that.
    It is the sheet a supervisor hands upward, and measured on the
    rich-project worst case that table cost 150pt -- 22% of the page, more
    than PROBLEM, GOAL & BASELINE and DATA IMPORTED combined -- because
    every long value wrapped to a second line inside a 357pt value column.
    Both re-reviewers named the same thing from the reader's side, without
    seeing the measurement: artifact ids, a SHA-256 and an engine version,
    set as a titled block, read as findings rather than as reference
    matter, and a manager translating this page upward deletes all of it.

    So the same facts run as one muted sentence in table-cell type. Nothing
    is dropped -- the dataset fingerprint and the artifact versions are the
    whole reason this page can be trusted, and a reader checking a number
    still finds every one of them -- but they sit where a footnote sits and
    cost ~40pt instead of ~150pt. The shared helper is deliberately left
    alone; it is correct for the thirty-odd reports that use it, and this
    is the one page whose reader is not the analyst."""
    style = ParagraphStyle(
        "summary_provenance_footer",
        parent=styles["table_cell"],
        textColor=pdf_theme.TEXT_FAINT,
        spaceBefore=pdf_theme.SPACE_3,
    )
    parts = [f"{label}: {value}" for label, value in rows if value]
    parts.append(f"Exported {exported_at}")
    return [Paragraph(esc(" · ".join(parts)), style)]


def _line(text: str, styles: dict, *, muted: bool = False) -> Any:
    """One section's body line. `muted` is this page's ONLY tone signal --
    it never uses pass/flag/fail color, because a missing artifact is not
    a failed check, it is an honest fact about what has been done so far
    (report_theme.chart()'s own placeholder makes the identical choice for
    a missing picture)."""
    return Paragraph(esc(text), styles["body_muted"] if muted else styles["body"])


# --------------------------------------------------------------------- T-03


def _value_unit(value: str, unit: str) -> str:
    """Join a number to its unit the way a person writes it: "1.26%" and
    "$6,800" take no space, but "487 picking errors" does. The rule is
    whether the unit opens with a symbol or a word -- found rendering the
    populated summary, where "487picking errors" ran together in the one
    artifact a manager actually reads. A charter's unit is free text, so a
    fixed choice (always-space or never-space) is wrong half the time."""
    unit = unit.strip()
    if not unit:
        return value
    sep = "" if not unit[0].isalnum() else " "
    return f"{value}{sep}{unit}"


def problem_text(charter: CharterArtifact) -> str:
    """The problem sentence alone -- what/where/when/magnitude, the same
    field composition the desktop's own A3 background-panel seed uses
    (desktop/src/tools/a3/a3Seeding.ts's draftNarrativeFor for T-03).
    Split from goal_text below so the two can be clipped independently --
    see PROBLEM_CHAR_BUDGET's own comment for why."""
    p = charter.problem_statement
    magnitude = _value_unit(fmt_number(p.magnitude.number), p.magnitude.unit)
    if p.magnitude.period:
        magnitude += f" ({p.magnitude.period})"
    return f"{p.what} at {p.where}, {p.when}: {magnitude}."


def goal_text(charter: CharterArtifact) -> str:
    """The goal sentence alone, in the charter's own words. Kept as its own
    function (not inlined at the one call site) so it reads the same as
    problem_text above -- one function per sentence this page quotes."""
    return f"Goal: {charter.goal.statement}"


def baseline_text(charter: CharterArtifact) -> str | None:
    """None means "charter exists but recorded no baseline" -- goal.
    baseline_value is optional on the schema (a SMART goal can be typed
    before a baseline is measured), which is exactly the "if there is one"
    the task brief asks this section to honor."""
    g = charter.goal
    if g.baseline_value is None:
        return None
    return (
        f"{_value_unit(fmt_number(g.baseline_value), g.unit)} → "
        f"{_value_unit(fmt_number(g.target_value), g.unit)} by {fmt_date(g.target_date)}"
    )


def _problem_goal_baseline_section(charter: CharterArtifact | None, styles: dict) -> list[Any]:
    """PROBLEM & GOAL and BASELINE share one zone label. Both are the
    charter's -- problem_statement narrative, goal.statement on its own
    line under it, then goal's own baseline_value/target_value pair under
    that -- and one desk-facing page reads a problem, its goal and its
    baseline as one fact, not three; the task's bullets all still print,
    in full whenever they fit, they just no longer pay for a second or
    third zone label's spacing. Problem and goal are two separate lines
    (not one concatenated line) so each gets its own clip budget --
    PROBLEM_CHAR_BUDGET's own comment has the full reasoning for why a
    shared budget is the wrong shape here."""
    out = [_label("PROBLEM, GOAL & BASELINE", styles)]
    if charter is None:
        out.append(_line("No charter saved yet.", styles, muted=True))
        return out
    out.append(_line(rt.clip(problem_text(charter), PROBLEM_CHAR_BUDGET), styles))
    out.append(_line(rt.clip(goal_text(charter), GOAL_CHAR_BUDGET), styles))
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
    text = f"{_n(latest.row_count, 'row')} imported from {latest.source_filename}"
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
    intro = (
        f"{total:,} {'mark' if total == 1 else 'marks'} tallied on the check sheet, across "
        f"{len(nonzero)} categor{'y' if len(nonzero) == 1 else 'ies'} in use."
    )
    if len(nonzero) > len(shown):
        intro += f" Top {len(shown)} shown here; the full ranking is in the Check Sheet report."
    return intro, [(label, count, count / total) for label, count in shown]


# How many vital-few category names dataset_categories_headline() spells
# out before it starts counting instead -- MUST match the on-screen
# chart's own HEADLINE_NAME_LIMIT (charts/Pareto.tsx). The headline below
# quotes the same engine-computed vital_few/flat/cumulative_share fields
# that chart headline reads, so a mismatched limit would make the two
# headlines disagree about how many names to spell out for the identical
# finding -- the last thing a page built on "quote, never re-derive"
# should do to the ONE line that names the finding.
DATASET_PARETO_HEADLINE_NAME_LIMIT = 5

# ...and how many characters those names may spend between them before the
# headline drops the clause and names nothing.
#
# The count limit above is the wrong unit on its own, because it assumes
# categories are named like categories. "Aisle 3, Aisle 7, Aisle 12" is
# five words and the best half of the sentence. Five imported part-number
# descriptions are 300 characters, and on the rich-project worst case they
# turned this ONE line into five -- 90pt, more than PROBLEM, GOAL &
# BASELINE and DATA IMPORTED together, for a clause naming what the reader
# is about to see named again.
#
# Because that is the fact that makes the clause optional: whichever branch
# _categories_section takes, the categories are identified directly below
# it -- by the chart's own x-axis labels, or by the table's first column.
# The names are never lost by being left out of the sentence, so the
# sentence keeps them only while they are free. Sized to hold the good case
# (short labels, comfortably inside two lines at this page's ~510pt column)
# and to drop the pathological one whole rather than truncate it mid-label,
# which would read as damage.
DATASET_PARETO_HEADLINE_NAMES_CHARS = 100


def dataset_categories_headline(source: DatasetParetoSource) -> str:
    """The one line that names the finding -- "5 of 12 carry 68% of 78
    rows" -- built from compute_pareto's own vital_few/flat/cumulative_
    share fields (stats/pareto.py), the exact fields the on-screen chart's
    own headline reads (charts/Pareto.tsx's headlineFor). Quoting those
    fields again here, in print voice, is reuse, not a second opinion
    (module docstring) -- the number on this page can never disagree with
    the number the chart the user was just looking at already showed,
    because it is the same number."""
    pareto = source.pareto
    if pareto.flat:
        return (
            f"Grouped by '{source.column}': no single one stands out -- {len(pareto.categories)} values, "
            f"fairly even across {pareto.total:,} rows."
        )
    vital = [c for c in pareto.categories if c.vital_few]
    share = vital[-1].cumulative_share if vital else 0.0
    finding = (
        f"Grouped by '{source.column}': {len(vital)} of {len(pareto.categories)} carry "
        f"{share * 100:.1f}% of {pareto.total:,} rows"
    )
    named = vital[:DATASET_PARETO_HEADLINE_NAME_LIMIT]
    names = ", ".join(c.category for c in named)
    if len(vital) > len(named):
        names += f" and {len(vital) - len(named)} more"
    if len(names) > DATASET_PARETO_HEADLINE_NAMES_CHARS:
        return f"{finding}."
    return f"{finding} -- {names}."


def dataset_categories_rows(source: DatasetParetoSource) -> list[tuple[str, int, float]]:
    """Up to TOP_CATEGORIES_SHOWN (label, count, share) rows off the
    engine's own compute_pareto result -- the table shown in place of the
    headline-only chart view when there is no chart image to show instead
    (_categories_section's own comment has the full when/why). Shares
    _categories_table with the check-sheet path below -- same three
    columns, same cap -- so the two sources read as one design."""
    return [(c.category, c.count, c.share) for c in source.pareto.categories[:TOP_CATEGORIES_SHOWN]]


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


def _categories_section(
    check_sheet: CheckSheetArtifact | None,
    dataset_pareto: DatasetParetoSource | None,
    styles: dict,
    content_width: float,
    *,
    chart_png: bytes | None = None,
) -> list[Any]:
    """The check sheet wins whenever one has been saved at all, even an
    empty one -- and a valid dataset+column selection is only ever the
    fallback for when it hasn't. A T-08 check sheet is a tool a user
    deliberately set up (named categories, its own report, its own
    strata); a T-14 selection is this project's best AVAILABLE number
    while that deliberate step hasn't happened yet, not a replacement for
    it once it has -- two categorizations of the same underlying problem
    can legitimately disagree (a check sheet's categories may be coarser,
    or dated after a recode fixed a spelling split), and silently letting
    the newer, less-deliberate one override a tool the user actually ran
    would itself be a second opinion, the exact thing this page's own
    docstring forbids. Only the dataset-Pareto branch ever carries a
    chart -- T-08's own report has never had one (ARTIFACT_REPORTS'
    wants_chart=False), so there is nothing to show or to miss there.

    THE CHART REPLACES THE TABLE, it never sits beside it. A table of
    counts and a bar chart of the identical counts is the same finding
    twice, and on a one-page sheet the two compete for the space that
    made the page worth handing to anyone -- confirmed the hard way, by
    rendering a rich project with both and watching it spill to a second
    sheet. When a chart image is available this section shows it and
    nothing else; when it is not (no capture, or the fingerprint was
    refused), the table is still the best available rendering, and there
    is no half-height placeholder paid for in between -- a table already
    on the page needs no apology for the picture it does not have."""
    out = [_label("TOP CATEGORIES", styles)]
    if check_sheet is not None:
        intro, rows = categories_rows(check_sheet)
        out.append(_line(intro, styles, muted=not rows))
        if rows:
            out.append(_categories_table(rows, styles, content_width))
        return out
    if dataset_pareto is not None:
        out.append(_line(dataset_categories_headline(dataset_pareto), styles))
        if chart_png:
            out += rt.chart(chart_png, content_width=content_width, styles=styles, max_height=SUMMARY_CHART_MAX_HEIGHT)
            return out
        rows = dataset_categories_rows(dataset_pareto)
        out.append(_categories_table(rows, styles, content_width))
        if len(dataset_pareto.pareto.categories) > len(rows):
            out.append(_line(f"Top {len(rows)} shown here; open T-14 for the full ranking.", styles, muted=True))
        return out
    out.append(_line("No categorized tally saved yet.", styles, muted=True))
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
    intro = f"{_n(total, 'cause')} on the fishbone; {verified_count} verified."
    if verified is None or verified_count == 0:
        return intro, []
    shown = list(verified.causes)[:VERIFIED_CAUSES_SHOWN]
    lines = [rt.clip(c.text, _CAUSE_TEXT_CLIP) for c in shown]
    # "1 verified" of "4 cause(s)" leaves a reader to do the subtraction
    # themselves to learn the other three are candidates, not confirmed --
    # said plainly instead, once there IS a gap between what is shown and
    # what is on the board (an all-verified fishbone has nothing to
    # reconcile, so it stays silent). Kept to one short clause: this page
    # is already at its measured one-page budget everywhere else, and the
    # clarification only needs to name the count, not narrate it.
    unproven_count = total - verified_count
    if unproven_count > 0:
        intro += f" Shown below; {unproven_count} more still unproven."
    if verified_count > len(shown):
        lines.append(f"+{_n(verified_count - len(shown), 'more verified cause')} -- see the Fishbone report.")
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


def _owner_ask(charter: CharterArtifact | None) -> str:
    """WHO, and BY WHEN -- a suggestion with neither is not a next step. The
    charter's own process_owner (schema-required, non-empty --
    artifacts/charter.py) and goal.target_date are already on file the
    moment a charter is saved, so appending them costs this function
    nothing it has to invent; empty string with no charter to draw them
    from, so every cascade rung below composes with this the same way."""
    if charter is None:
        return ""
    return f" Owner: {charter.process_owner.name}, by {fmt_date(charter.goal.target_date)}."


def next_action_text(
    charter: CharterArtifact | None,
    fishbone: FishboneArtifact | None,
    solution_matrix: SolutionMatrixArtifact | None,
    datasets: list[DatasetMeta] | None = None,
    categories_available: bool = False,
) -> str:
    """Routing advice over what is already on file, cascading from the
    most decision-ready saved artifact down to "start at the charter" --
    never a number this function invents, only a choice of which already-
    computed fact to point at next (module docstring's "advice, marked as
    advice"), plus the charter's own owner and date appended wherever a
    charter exists to draw them from (_owner_ask above).

    `datasets`/`categories_available` exist so this line stops being blind
    to data: the data-first front door (docs/RELEASE-v0.2.md) lets a
    supervisor import a file and chart it before any charter exists, and a
    cascade that only ever looked at charter/fishbone/solution_matrix told
    that supervisor "No charter saved yet -- start there" while a ranked
    Pareto sat one screen away, unacknowledged. `categories_available`
    also refines the charter-only rung below: "bring in data" is stale
    advice once TOP CATEGORIES already has a ranking to show for it."""
    owner_ask = _owner_ask(charter)
    if solution_matrix is not None and solution_matrix.ranked_fix_list is not None:
        ranked = solution_matrix.ranked_fix_list.value.ranked
        if ranked:
            top = ranked[0]
            return (
                f'Top-ranked countermeasure on file: "{top.name}" ({top.quadrant.replace("_", " ")}). Pilot it '
                "and bring the before/after numbers back." + owner_ask
            )
    if fishbone is not None:
        verified = fishbone.verified_causes.value if fishbone.verified_causes else None
        verified_count = verified.count if verified else 0
        if verified_count >= 1:
            return (
                f"{_n(verified_count, 'verified cause')} on the fishbone -- rank countermeasures for them in the "
                "Solution Matrix (T-18) next." + owner_ask
            )
        if fishbone.causes:
            return "Causes are on the board but none are verified yet -- attach evidence to a candidate cause." + owner_ask
        return "The fishbone is open with no causes on it yet -- add candidate causes on the branches that fit." + owner_ask
    if charter is not None:
        if categories_available:
            return (
                "Data is in and ranked above -- open the Fishbone (T-15) and find causes for what it shows."
                + owner_ask
            )
        return "The charter is on file -- bring in data and find out where the gap actually concentrates." + owner_ask
    if datasets:
        latest = datasets[-1]
        if categories_available:
            return (
                f"{_n(latest.row_count, 'row')} imported from {latest.source_filename}, already grouped and ranked "
                "above -- write the charter next: state the problem and the goal in measurable, dated terms, so "
                "this ranking has something to be measured against."
            )
        return (
            f"{_n(latest.row_count, 'row')} imported from {latest.source_filename} -- group it into a Pareto (T-14) "
            "to see where it concentrates, then write the charter: state the problem and the goal in measurable, "
            "dated terms."
        )
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
    dataset_pareto: DatasetParetoSource | None = None,
    chart_png: bytes | None = None,
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
    story.append(
        rt.keep(
            _categories_section(
                check_sheet,
                dataset_pareto,
                styles,
                content_width,
                chart_png=chart_png,
            )
        )
    )
    story.append(rt.keep(_fishbone_section(fishbone, styles)))

    # TOP CATEGORIES has a ranking to point at (for next_action_text's own
    # "stop being blind to data" rung) when either source actually printed
    # rows -- a check sheet on file with nothing tallied, or no valid T-14
    # selection at all, both still mean "nothing ranked yet" here even
    # though the section itself is present.
    categories_available = (
        check_sheet is not None and check_sheet_report_mod.total_count(check_sheet) > 0
    ) or dataset_pareto is not None
    story += rt.recommendation_block(
        next_action_text(charter, fishbone, solution_matrix, datasets, categories_available), styles, content_width
    )

    story += _provenance_footer(provenance_rows, styles, exported_at)
    return story
