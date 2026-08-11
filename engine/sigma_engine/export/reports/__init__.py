"""One module per tool report.

Deliberately hand-laid, unlike export/project_pdf.py's generic walker: the
walker's job is completeness (print every field, never silently drop one),
and a report's job is the opposite -- decide what matters and give it the
page. Those are different enough that sharing code between them would make
both worse.
"""
