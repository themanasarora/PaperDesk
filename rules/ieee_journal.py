"""IEEE journal (Transactions) rule set: PLACEHOLDER.

Numeric values are copied from the conference rule set and have NOT been
checked against the official journal template. Before relying on this:
check every value, then fill in `source` (official URL), `last_verified`
(ISO date, e.g. "2026-12-01") and set `verified` to True.
"""

RULES = {
    "name": "IEEE journal",
    "page_name": "US Letter",
    "page_width_in": 8.5,
    "page_height_in": 11.0,
    "margins_in": {"top": 0.75, "bottom": 1.0, "left": 0.625, "right": 0.625},
    "margin_tolerance_in": 0.05,
    "body_font": "Times New Roman",
    "body_size_pt": 10,
    "abstract_words": (150, 250),
    "require_index_terms": True,
    "keywords_label": "Index Terms",
    "heading_style": "roman",
    "table_numbering": "roman",
    "reference_style": "numeric",
    "flag_double_spaces": True,
    "require_figure_table_references": True,
    "verified": False,
    "source": "",
    "last_verified": None,
}
