"""PDF layout theme for Sigma AI exports (PLAN §4.5: "one design system
across every tool" so a paper artifact and the app screen it came from read
as one product). Values here are derived from desktop/src/design/tokens.css
-- font sizes and spacing convert on one fixed factor, colors are the same
hex values -- so a token change and a PDF-theme change are the same edit in
spirit, never two hand-maintained copies of the same number.

Font choice: ReportLab's base-14 fonts (the Helvetica family) render
identically with zero font files installed or bundled -- the same
"pure Python, no system dependencies" property that got ReportLab chosen
over WeasyPrint in the first place (PLAN §4.5, §7). tokens.css's Inter is a
webfont; Helvetica is the nearest guaranteed-available sans-serif, so the
type *scale* below mirrors tokens.css exactly even though the *typeface*
has to differ.
"""

from __future__ import annotations

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm

# ---- Page (A4; swapping to letter is a one-line change if Shawn prefers) ----
PAGE_SIZE = A4
MARGIN_TOP = 20 * mm
MARGIN_BOTTOM = 22 * mm  # extra room for the two-line policy footer
MARGIN_LEFT = 18 * mm
MARGIN_RIGHT = 18 * mm

# ---- Type scale (tokens.css: 1rem = 16px; 1px = 0.75pt -> pt = rem * 12) ----
_REM_TO_PT = 12.0
TEXT_XS = 0.72 * _REM_TO_PT
TEXT_SM = 0.86 * _REM_TO_PT
TEXT_BASE = 1.00 * _REM_TO_PT
TEXT_MD = 1.15 * _REM_TO_PT
TEXT_LG = 1.44 * _REM_TO_PT
TEXT_XL = 1.80 * _REM_TO_PT
TEXT_2XL = 2.25 * _REM_TO_PT

LEADING_TIGHT = 1.2
LEADING_NORMAL = 1.5

FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_ITALIC = "Helvetica-Oblique"
FONT_MONO = "Courier"

# ---- Spacing scale (tokens.css --space-*, same rem->pt factor as type) ----
SPACE_1 = 0.25 * _REM_TO_PT
SPACE_2 = 0.50 * _REM_TO_PT
SPACE_3 = 0.75 * _REM_TO_PT
SPACE_4 = 1.00 * _REM_TO_PT
SPACE_5 = 1.50 * _REM_TO_PT
SPACE_6 = 2.00 * _REM_TO_PT

# ---- Palette (tokens.css :root -- light theme, the only theme M1 ships) ----
TEXT = HexColor("#1c2128")
TEXT_MUTED = HexColor("#5b6470")
TEXT_FAINT = HexColor("#88919c")
BORDER = HexColor("#dde1e6")

ACCENT = HexColor("#3556d6")
ACCENT_SOFT = HexColor("#eaeefc")
ACCENT_BORDER = HexColor("#b9c4f2")

PASS = HexColor("#1a7f37")
FLAG = HexColor("#9a6700")
FAIL = HexColor("#cf222e")

NEUTRAL_SOFT = HexColor("#eceef1")

# research §F: risk likelihood/impact reuse the same pass/flag/fail
# semantic scale as every status pill in the app -- low=pass, medium=flag,
# high=fail. One mapping, used by charter_pdf_tables.build_risks.
RISK_LEVEL_COLOR = {"low": PASS, "medium": FLAG, "high": FAIL}

# PLAN §1's policy sentence, verbatim: outputs are working documents, not
# certification evidence, not validation for regulated processes. Carried
# on every exported page's footer (M1 export brief).
FOOTER_POLICY_SENTENCE = (
    "Working document — not certification evidence and not validation for regulated processes."
)


def build_styles() -> dict[str, ParagraphStyle]:
    """One ParagraphStyle per role used across charter_pdf_sections.py and
    charter_pdf_tables.py -- named for the token/role they come from, not
    for their one current call site, so a new section reuses these instead
    of inventing a sibling style."""
    return {
        "title": ParagraphStyle("title", fontName=FONT_BOLD, fontSize=TEXT_XL, leading=TEXT_XL * LEADING_TIGHT, textColor=TEXT),
        "subtitle": ParagraphStyle("subtitle", fontName=FONT, fontSize=TEXT_LG, leading=TEXT_LG * LEADING_TIGHT, textColor=TEXT_MUTED),
        "meta": ParagraphStyle("meta", fontName=FONT, fontSize=TEXT_SM, leading=TEXT_SM * LEADING_NORMAL, textColor=TEXT_FAINT),
        "heading": ParagraphStyle("heading", fontName=FONT_BOLD, fontSize=TEXT_MD, leading=TEXT_MD * LEADING_TIGHT, textColor=TEXT, spaceBefore=SPACE_5, spaceAfter=SPACE_2),
        "label": ParagraphStyle("label", fontName=FONT_BOLD, fontSize=TEXT_XS, leading=TEXT_XS * LEADING_NORMAL, textColor=TEXT_MUTED),
        "body": ParagraphStyle("body", fontName=FONT, fontSize=TEXT_BASE, leading=TEXT_BASE * LEADING_NORMAL, textColor=TEXT),
        "body_muted": ParagraphStyle("body_muted", fontName=FONT_ITALIC, fontSize=TEXT_SM, leading=TEXT_SM * LEADING_NORMAL, textColor=TEXT_MUTED),
        "callout": ParagraphStyle("callout", fontName=FONT_BOLD, fontSize=TEXT_MD, leading=TEXT_MD * LEADING_NORMAL, textColor=ACCENT),
        "bullet": ParagraphStyle("bullet", fontName=FONT, fontSize=TEXT_SM, leading=TEXT_SM * LEADING_NORMAL, textColor=TEXT, leftIndent=SPACE_4, bulletIndent=SPACE_1),
        "table_header": ParagraphStyle("table_header", fontName=FONT_BOLD, fontSize=TEXT_XS, leading=TEXT_XS * LEADING_NORMAL, textColor=TEXT_MUTED),
        "table_cell": ParagraphStyle("table_cell", fontName=FONT, fontSize=TEXT_SM, leading=TEXT_SM * LEADING_NORMAL, textColor=TEXT),
        "footer_meta": ParagraphStyle("footer_meta", fontName=FONT_MONO, fontSize=TEXT_XS, leading=TEXT_XS * LEADING_NORMAL, textColor=TEXT_FAINT),
        "footer_policy": ParagraphStyle("footer_policy", fontName=FONT_ITALIC, fontSize=TEXT_XS, leading=TEXT_XS * LEADING_NORMAL, textColor=TEXT_FAINT),
    }
