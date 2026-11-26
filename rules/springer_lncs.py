"""Springer LNCS rule set. Partly checked on 2026-11-27, so `verified: False`.

Confirmed from Springer's proceedings author guidelines: Word templates use Times; only the
first two heading levels are numbered ("1 Introduction", "2.1 ..."); table captions go above
the table and the guidelines' example numbers them with Arabic numerals ("Table 1."); figure
captions go below; citations are numbered in square brackets. Body size 10 pt comes from the
older LNCS instructions and a conference LNCS Word template (medium confidence). The
reference LIST is numbered "1. Author: Title ..." in the Word template, hence "dotted".

NOT confirmed (the guidelines point to the templates for them), so they are `None`, which
means "not checked": page size, margins, abstract word limit (sources conflict: at most 150
words in older LNCS instructions, 150-250 in one conference template).
Fill them in from the official Word template, or use the Custom option with the official
template .docx, which reads page size, margins and fonts from the file.

To mark this rule set verified: fill the None values, set `verified` to True and
`last_verified` to the date (YYYY-MM-DD).
"""

RULES = {
    "name": "Springer LNCS",
    "page_name": "A4",
    "page_width_in": None,
    "page_height_in": None,
    "margins_in": None,
    "margin_tolerance_in": 0.05,
    "body_font": "Times New Roman",
    "body_size_pt": 10,
    "abstract_words": None,
    "require_index_terms": True,
    "keywords_label": "Keywords",
    "heading_style": "numeric",
    "table_numbering": "arabic",
    "reference_style": "dotted",
    "flag_double_spaces": True,
    "require_figure_table_references": True,
    "verified": False,
    "source": "https://www.springer.com/de/authors-editors/conference-proceedings/conference-proceedings-guidelines",
    "last_verified": None,
}
