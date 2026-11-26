"""Springer LNCS rule set: PLACEHOLDER.

Structure (A4, numeric headings, Arabic table numbers, "Keywords") is set for
the Springer family. Margins, font size and abstract range are copied from the
IEEE conference set and are NOT checked against the official LNCS template.
Before relying on this: check every value, then fill in `source` (official
URL), `last_verified` (ISO date) and set `verified` to True.
"""

RULES = {
    "name": "Springer LNCS",
    "page_name": "A4",
    "page_width_in": 8.27,
    "page_height_in": 11.69,
    "margins_in": {"top": 0.75, "bottom": 1.0, "left": 0.625, "right": 0.625},
    "margin_tolerance_in": 0.05,
    "body_font": "Times New Roman",
    "body_size_pt": 10,
    "abstract_words": (150, 250),
    "require_index_terms": True,
    "keywords_label": "Keywords",
    "heading_style": "numeric",
    "table_numbering": "arabic",
    "reference_style": "dotted",
    "flag_double_spaces": True,
    "require_figure_table_references": True,
    "verified": False,
    "source": "",
    "last_verified": None,
}
