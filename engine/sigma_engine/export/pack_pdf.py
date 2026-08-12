"""Phase packs — one phase's reports, bound with a cover and an index.

WHY A PACK AND NOT A ZIP OF PDFS. Managers review work a phase at a time,
and a review runs on one document that can be printed, annotated and
handed on. Seven separate downloads is seven chances to open the wrong
one, and it loses the thing a pack is actually for: seeing at a glance
which tools in a phase were done, which were skipped, and what each one
concluded — before reading any of them.

WHAT MAKES THIS DIFFERENT FROM THE PROJECT EXPORT. `project_pdf.py` is
the receipts: every field of every artifact, generically walked, 125 pages
of it, for when somebody needs to know exactly what was saved. A pack is
the opposite — the designed per-tool reports, in phase order, nothing
else. Same source data, different job, and neither one substitutes.

THE INDEX CARRIES THE VERDICTS. Each entry prints its report's own verdict
line and tone dot, so the first page answers "how did this phase go"
without turning one. That is the page a manager actually reads, and it is
built by calling each report's `build_verdict` — never by re-deriving a
judgement here, which would be a second opinion competing with the page
it indexes.

MISSING TOOLS ARE LISTED, NOT OMITTED. A Measure pack with no measurement
check is the most important fact about that phase, and a pack that simply
did not mention T-12 would read as complete.
"""

from __future__ import annotations

from typing import Any, Callable

from reportlab.platypus import PageBreak, Paragraph, Table, TableStyle

from . import pdf_theme as theme
from . import report_pdf, report_theme as rt
from .charter_pdf_common import esc, kv_table
from .project_pdf import TOOL_TITLES

# A pack is per phase, and Intake is one tool -- packing it alone would be
# a cover page in front of a single report. It is folded into Define,
# which is where a reviewer looks for "was this the right project".
PACK_PHASES = ("Define", "Measure", "Analyze", "Improve", "Control", "Wrap")
PHASE_FOLD_IN: dict[str, tuple[str, ...]] = {"Define": ("Intake",)}

PHASE_SUBTITLES = {
    "Define": "Is this the right problem, and is it worth solving?",
    "Measure": "Can we trust the numbers, and what do they say now?",
    "Analyze": "What is actually causing it, and how do we know?",
    "Improve": "What did we change, and did it work?",
    "Control": "What keeps it from coming back?",
    "Wrap": "What happened, and what did it teach us?",
}


def phases_for(phase: str) -> tuple[str, ...]:
    """The phase, plus any phase folded into it."""
    return (*PHASE_FOLD_IN.get(phase, ()), phase)


def tools_in_phase(phase: str) -> list[str]:
    wanted = set(phases_for(phase))
    return sorted(tool_id for tool_id, (tool_phase, _) in TOOL_TITLES.items() if tool_phase in wanted)


def build_pack(
    *,
    phase: str,
    project_name: str,
    project_id: str,
    engine_version: str,
    entries: list[tuple[str, Callable[[float], list[Any]], tuple[str, rt.Tone]]],
    missing: list[str],
    exported_at: str,
) -> bytes:
    """`entries` is (tool_id, story_builder, (verdict_text, tone)) in the
    order they should appear. The caller owns loading artifacts and binding
    each report module's `build_story` -- this module owns the binding, the
    cover and the index, and nothing about any individual tool.
    """
    if phase not in PACK_PHASES:
        raise ValueError(f"no pack defined for phase {phase!r}")

    def story(content_width: float) -> list[Any]:
        styles = rt.report_styles()
        out: list[Any] = []
        out += _cover(
            phase=phase,
            project_name=project_name,
            styles=styles,
            content_width=content_width,
            exported_at=exported_at,
            done=[tool_id for tool_id, _, _ in entries],
            missing=missing,
        )
        out += _index(entries=entries, missing=missing, styles=styles, content_width=content_width)

        for tool_id, story_builder, _ in entries:
            out.append(PageBreak())
            out += story_builder(content_width)
        return out

    return report_pdf.render(
        story_builder=story,
        title=f"{project_name} — {phase} pack",
        project_id=project_id,
        engine_version=engine_version,
    )


def _cover(
    *,
    phase: str,
    project_name: str,
    styles: dict,
    content_width: float,
    exported_at: str,
    done: list[str],
    missing: list[str],
) -> list[Any]:
    out: list[Any] = [
        Paragraph(esc(f"{phase} pack"), styles["report_title"]),
        Paragraph(esc(project_name), styles["subtitle"]),
    ]
    subtitle = PHASE_SUBTITLES.get(phase)
    if subtitle:
        out.append(Paragraph(esc(subtitle), styles["meaning"]))
    out.append(
        kv_table(
            [
                ("Reports enclosed", f"{len(done)} of {len(done) + len(missing)} tools in this phase"),
                ("Exported", exported_at),
            ],
            styles,
            content_width,
            label_frac=0.28,
        )
    )
    return out


def _index(
    *,
    entries: list[tuple[str, Callable[[float], list[Any]], tuple[str, rt.Tone]]],
    missing: list[str],
    styles: dict,
    content_width: float,
) -> list[Any]:
    """The page a manager reads. Every enclosed report's own verdict, plus
    every tool in the phase that produced nothing."""
    items: list[tuple[rt.Tone, str]] = []
    for tool_id, _, (verdict_text, tone) in entries:
        _, title = TOOL_TITLES[tool_id]
        items.append((tone, f"{tool_id} {title} — {verdict_text}"))
    for tool_id in missing:
        _, title = TOOL_TITLES[tool_id]
        # "flag", not "fail": a tool can be legitimately skipped, and the
        # pack is not the place that decides. Naming it is the job.
        items.append(("flag", f"{tool_id} {title} — not done in this project."))

    # Rendered here rather than through report_theme.report_card, which is
    # the right shape but carries its own heading -- "what would change this
    # answer" is a caveat list about one verdict, and this is an index of
    # several. Same tone dots, same reading, correct heading.
    rows = []
    styling: list[tuple] = []
    for index, (tone, text) in enumerate(items):
        rows.append([Paragraph("\u25a0", styles["card_item"]), Paragraph(esc(text), styles["card_item"])])
        styling.append(("TEXTCOLOR", (0, index), (0, index), theme_colour(tone)))
    table = Table(rows, colWidths=[theme.SPACE_5, content_width - theme.SPACE_5])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), theme.SPACE_2),
                ("TOPPADDING", (0, 0), (-1, -1), theme.SPACE_1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), theme.SPACE_1),
                *styling,
            ]
        )
    )
    return [Paragraph("WHAT THIS PHASE CONCLUDED", styles["zone_label"]), table]


def theme_colour(tone: rt.Tone) -> Any:
    """The tone palette, read from the shared theme so a colour change in
    one place moves the packs too."""
    return {
        "pass": theme.PASS,
        "flag": theme.FLAG,
        "fail": theme.FAIL,
        "neutral": theme.TEXT_MUTED,
    }[tone]
