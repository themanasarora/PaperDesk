"""IEEE conference-style rule set used by checker.py.

IMPORTANT: these values come from general knowledge of the IEEE conference
template. Before charging anyone, compare each value with the official template
and the target conference's own author instructions, and edit this file.
Each rule can be tuned here without touching checker.py.
"""

RULES = {
    "name": "IEEE conference",
    # Page setup, in inches (US Letter: 8.5 x 11)
    "page_width_in": 8.5,
    "page_height_in": 11.0,
    "margins_in": {"top": 0.75, "bottom": 1.0, "left": 0.625, "right": 0.625},
    "margin_tolerance_in": 0.05,
    # Text
    "body_font": "Times New Roman",
    "body_size_pt": 10,
    # Abstract
    "abstract_words": (150, 250),
    "require_index_terms": True,
    # Section headings: "roman" = I., II., III. ...; "numeric" = 1, 1.1, 2 ...
    "heading_style": "roman",
    # References
    "reference_style": "numeric",  # [1], [2], ...
    # Extra checks
    "flag_double_spaces": True,
    # Not yet checked against the official template; see rules/__init__.py
    "verified": False,
    "source": "",
    "last_verified": None,
    "require_figure_table_references": True,
}
