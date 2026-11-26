"""Build a rule set from a journal's own blank template (.docx).

Reads only what a Word file states reliably: page size, margins, and the body text
font and size. Everything else (abstract length, headings, keywords, figure/table rules)
is switched off, so a Custom check never invents requirements the template cannot show.
"""
import datetime
import os
from collections import Counter

from docx import Document

from checker import effective_font

MIN_BODY_WORDS = 15


def _page_name(w: float, h: float) -> str:
    if abs(w - 8.5) <= 0.02 and abs(h - 11.0) <= 0.02:
        return "US Letter"
    if abs(w - 8.27) <= 0.02 and abs(h - 11.69) <= 0.02:
        return "A4"
    return f"{w:.2f} x {h:.2f} in"


def _body_font(doc):
    """Most common (font, size) by character count over long paragraphs; else the Normal style."""
    counts = Counter()
    for p in doc.paragraphs:
        if len(p.text.split()) < MIN_BODY_WORDS:
            continue
        for run in p.runs:
            if run.text.strip():
                name, size = effective_font(doc, p, run)
                if name is not None and size is not None:
                    counts[(name, size)] += len(run.text)
    if counts:
        return counts.most_common(1)[0][0]
    normal = doc.styles["Normal"].font
    return normal.name, (normal.size.pt if normal.size else None)


def rules_from_template(path: str, name: str | None = None, today: datetime.date | None = None) -> dict:
    doc = Document(path)
    sec = doc.sections[0]
    w, h = sec.page_width.inches, sec.page_height.inches
    font, size = _body_font(doc)
    today = today or datetime.date.today()
    return {
        "name": name or f"Custom template ({os.path.basename(path)})",
        "page_name": _page_name(w, h),
        "page_width_in": round(w, 2),
        "page_height_in": round(h, 2),
        "margins_in": {"top": round(sec.top_margin.inches, 3), "bottom": round(sec.bottom_margin.inches, 3),
                       "left": round(sec.left_margin.inches, 3), "right": round(sec.right_margin.inches, 3)},
        "margin_tolerance_in": 0.05,
        "body_font": font,
        "body_size_pt": size,
        "abstract_words": None,
        "require_index_terms": False,
        "keywords_label": "Keywords",
        "heading_style": "none",
        "table_numbering": "roman",
        "reference_style": "bracket",
        "flag_double_spaces": False,
        "require_figure_table_references": False,
        "verified": True,
        "source": "uploaded template",
        "last_verified": today.isoformat(),
    }
