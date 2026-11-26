"""IEEE journal (Transactions) rule set. Partly checked on 2026-11-27, so `verified: False`.

Confirmed from the IEEE Transactions author instructions: abstract must be 150-250 words;
keyword line is "Index Terms"; Roman-numeral section headings; tables numbered with Roman
numerals; figures labelled "Fig."; numeric [1] references.

NOT confirmed (the instructions say to use the official Word template and do not state
them), so they are `None`, which means "not checked": page size, margins, body font and size.
Fill them in from the official template, or use the Custom option with the official
template .docx, which reads them from the file.

To mark this rule set verified: fill the None values, set `verified` to True and
`last_verified` to the date (YYYY-MM-DD).
"""

RULES = {
    "name": "IEEE journal",
    "page_name": "US Letter",
    "page_width_in": None,
    "page_height_in": None,
    "margins_in": None,
    "margin_tolerance_in": 0.05,
    "body_font": None,
    "body_size_pt": None,
    "abstract_words": (150, 250),
    "require_index_terms": True,
    "keywords_label": "Index Terms",
    "heading_style": "roman",
    "table_numbering": "roman",
    "reference_style": "bracket",
    "flag_double_spaces": True,
    "require_figure_table_references": True,
    "verified": False,
    "source": "https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/authoring-tools-and-templates",
    "last_verified": None,
}
