"""IEEE conference rule set. Partly checked on 2026-11-27, so still `verified: False`.

Confirmed from IEEE-hosted conference template instructions (ewh.ieee.org example paper;
current Word templates at the `source` page): US Letter; margins top 0.75 in, bottom 1 in,
sides 0.625 in; Times New Roman preferred (the template says "preferred", not required);
main text 10 pt; Roman-numeral section headings (optional in the template); tables
numbered with Roman numerals ("TABLE I"); figures labelled "Fig. 1"; numeric [1]
references; current template keyword line reads "Keywords".

NOT confirmed: the abstract word range. The conference template states no limit
(150-250 is the IEEE Transactions rule and a common conference convention), so check it
against your conference's own call for papers.

To mark this rule set verified: confirm the abstract range, set `verified` to True and
`last_verified` to the date (YYYY-MM-DD).
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
    "keywords_label": "Keywords",
    # Section headings: "roman" = I., II., III. ...; "numeric" = 1, 1.1, 2 ...
    "heading_style": "roman",
    # References
    "reference_style": "bracket",  # [1], [2], ...
    # Extra checks
    "flag_double_spaces": True,
    # Not yet checked against the official template; see rules/__init__.py
    "verified": False,
    "source": "https://www.ieee.org/conferences/publishing/templates.html",
    "last_verified": None,
    "require_figure_table_references": True,
}
