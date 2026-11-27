"""Quirks found by running a real two-column IEEE-style paper through the checker.

Real Word papers number headings and reference lists with Word lists (the
number is not in the text), caption tables as "TABLE I" with no period, and use
8 pt text for references, captions and tables. Each test builds a small paper
with one of those quirks. Tests come in pairs: the quirk must not raise false
alarms, and a real problem next to it must still be reported.
"""
import collections

import pytest
from docx import Document
from docx.shared import Inches, Pt

import checker
from docx_helpers import number_paragraph, set_numbering
from rules import get_ruleset

IEEE = get_ruleset("ieee_conference")
SPRINGER = get_ruleset("springer_lncs")

BRACKET, ROMAN, ARABIC_DOT, ARABIC, ROMAN_FROM_3 = 1, 2, 3, 4, 5   # numbering instance ids used by Paper


def words(n):
    return " ".join(["word"] * n)


class Paper:
    def __init__(self):
        self.doc = Document()
        sec = self.doc.sections[0]
        sec.page_width, sec.page_height = Inches(8.5), Inches(11)
        sec.top_margin, sec.bottom_margin = Inches(0.75), Inches(1.0)
        sec.left_margin = sec.right_margin = Inches(0.625)
        normal = self.doc.styles["Normal"]
        normal.font.name, normal.font.size = "Times New Roman", Pt(10)
        set_numbering(
            self.doc,
            {0: {0: ("decimal", "[%1]", 1)}, 1: {0: ("upperRoman", "%1.", 1)},
             2: {0: ("decimal", "%1.", 1)}, 3: {0: ("decimal", "%1", 1)}},
            {BRACKET: (0, {}), ROMAN: (1, {}), ARABIC_DOT: (2, {}), ARABIC: (3, {}), ROMAN_FROM_3: (1, {0: 3})})
        self.doc.add_paragraph("A Study of Things")
        self.doc.add_paragraph("A. Author, B. Author")
        self.doc.add_paragraph("Abstract—" + words(160))
        self.doc.add_paragraph("Index Terms—alpha, beta")

    def _add(self, text, size=None, font=None, style=None):
        p = self.doc.add_paragraph(text, style=style)
        for run in p.runs:
            if size:
                run.font.size = Pt(size)
            if font:
                run.font.name = font
        return p

    def body(self, text=None, size=None, font=None):
        return self._add(text or f"Some prior work is discussed here {words(20)}.", size, font)

    def heading(self, text, number=None, style="Heading 2", size=None):
        p = self._add(text, size, style=style)
        if number:
            number_paragraph(p, number, 0)
        return p

    def references(self, n, numbering="auto", num_id=BRACKET, size=8, heading="References", heading_number=None):
        self.heading(heading, heading_number, style="Heading 1")
        for k in range(1, n + 1):
            if numbering == "typed":
                self._add(f"[{k}] A. Writer, Title {k}, 2020.", size, style="List Paragraph")
            else:
                p = self._add(f"A. Writer, Title {k}, 2020.", size, style="List Paragraph")
                if numbering == "auto":
                    number_paragraph(p, num_id, 0)

    def table_caption(self, first="TABLE I", title="Results of runs", size=8, same_line=False):
        if same_line:
            self._add(f"{first} {title}", size)
        else:
            self._add(first, size)
            self._add(title, size)

    def issues(self, tmp_path, rules=IEEE):
        path = tmp_path / "paper.docx"
        self.doc.save(path)
        return checker.check(str(path), rules)


@pytest.fixture
def paper():
    return Paper()


def rules_of(issues, rule):
    return [i for i in issues if i.rule == rule]


def counts(issues):
    return dict(collections.Counter(i.rule for i in issues))


# ---------------- references ----------------

def test_auto_numbered_references_match_citations(paper, tmp_path):
    paper.body("First [1], second [2], third [3]. " + words(15))
    paper.references(3)
    assert counts(paper.issues(tmp_path)) == {}


def test_citation_beyond_the_reference_list_is_reported_once(paper, tmp_path):
    paper.body("Cited [1] [2] [3] [4]. " + words(15))
    paper.references(3)
    found = rules_of(paper.issues(tmp_path), "Citation without reference")
    assert len(found) == 1 and "[4]" in found[0].detail


def test_uncited_auto_numbered_reference_is_a_warning(paper, tmp_path):
    paper.body("Cited [1] and [2]. " + words(15))
    paper.references(3)
    found = rules_of(paper.issues(tmp_path), "Reference never cited")
    assert [(i.severity, i.where) for i in found] == [("WARN", "reference [3]")]


def test_typed_reference_numbers_still_work(paper, tmp_path):
    paper.body("Cited [1] and [2]. " + words(15))
    paper.references(2, numbering="typed")
    assert counts(paper.issues(tmp_path)) == {}


@pytest.mark.parametrize("size", [8, 12, 20])
def test_reference_entries_are_never_checked_as_body_text(paper, tmp_path, size):
    paper.body("Cited [1] and [2]. " + words(15))
    paper.references(2, size=size)
    assert rules_of(paper.issues(tmp_path), "Body text style") == []


def test_unnumbered_reference_list_gives_one_warning_not_citation_errors(paper, tmp_path):
    paper.body("Cited [1] and [2]. " + words(15))
    paper.references(3, numbering="none")
    got = paper.issues(tmp_path)
    assert counts(got) == {"Reference numbering": 1}
    assert got[0].severity == "WARN" and "not numbered" in got[0].detail


def test_references_heading_with_its_own_list_number_is_still_the_heading(paper, tmp_path):
    paper.body("Cited [1]. " + words(15))
    paper.references(1, heading_number=ROMAN)
    assert counts(paper.issues(tmp_path)) == {}


def test_extra_unnumbered_paragraph_in_the_reference_list_is_ignored(paper, tmp_path):
    paper.body("Cited [1] and [2]. " + words(15))
    paper.references(2)
    paper.body("continuation of the last entry", size=12)
    assert counts(paper.issues(tmp_path)) == {}


def test_springer_dotted_auto_numbered_references(paper, tmp_path):
    paper.body("Cited [1] and [2]. " + words(15))
    paper.references(2, num_id=ARABIC_DOT)
    assert rules_of(paper.issues(tmp_path, SPRINGER), "Citation without reference") == []
    assert rules_of(paper.issues(tmp_path, SPRINGER), "Reference never cited") == []


def test_paragraphs_after_a_later_heading_are_body_again(paper, tmp_path):
    paper.body("Cited [1]. " + words(15))
    paper.references(1)
    paper.heading("Appendix", None, style="Heading 1")
    paper.body(size=12)
    found = rules_of(paper.issues(tmp_path), "Body text style")
    assert len(found) == 1 and "12.0" in found[0].detail


# ---------------- headings (IEEE: Roman numerals) ----------------

def test_roman_auto_numbered_headings_are_clean_even_when_large(paper, tmp_path):
    for name in ("Introduction", "Method", "Results"):
        paper.heading(name, ROMAN, size=16)
        paper.body()
    assert counts(paper.issues(tmp_path)) == {}


def test_heading_without_a_number_is_reported(paper, tmp_path):
    paper.heading("Introduction", ROMAN)
    paper.heading("Methodology", None)
    found = rules_of(paper.issues(tmp_path), "Heading numbering")
    assert len(found) == 1 and "Methodology" in found[0].where + found[0].detail and "no number" in found[0].detail


@pytest.mark.parametrize("name", ["Acknowledgment", "Acknowledgments", "ACKNOWLEDGMENT", "Acknowledgement", "References"])
def test_headings_that_are_never_numbered_are_not_reported(paper, tmp_path, name):
    paper.heading("Introduction", ROMAN)
    paper.heading(name, None, style="Heading 1")
    assert rules_of(paper.issues(tmp_path), "Heading numbering") == []


def test_unnumbered_level_three_headings_are_not_reported(paper, tmp_path):
    paper.heading("Introduction", ROMAN)
    paper.heading("Details", None, style="Heading 3")
    assert counts(paper.issues(tmp_path)) == {}


def test_arabic_numbers_in_a_roman_template_are_reported_once(paper, tmp_path):
    for name in ("Introduction", "Method", "Results"):
        paper.heading(name, ARABIC_DOT)
    found = rules_of(paper.issues(tmp_path), "Heading numbering")
    assert len(found) == 1 and "Roman" in found[0].detail


def test_out_of_order_roman_auto_numbers(paper, tmp_path):
    paper.heading("Introduction", ROMAN)
    paper.heading("Results", ROMAN_FROM_3)          # Word prints III. here
    found = rules_of(paper.issues(tmp_path), "Heading numbering")
    assert len(found) == 1 and "numbered III but section 2 was expected" in found[0].detail


def test_typed_roman_heading_out_of_order_still_reported(paper, tmp_path):
    paper.body("I. INTRODUCTION")
    paper.body("III. RESULTS")
    found = rules_of(paper.issues(tmp_path), "Heading numbering")
    assert len(found) == 1 and "section 2 was expected" in found[0].detail


def test_typed_mixed_case_roman_heading_is_a_heading_not_body(paper, tmp_path):
    paper.body("I. Introduction", size=16)
    paper.body("II. Method", size=16)
    assert rules_of(paper.issues(tmp_path), "Body text style") == []


def test_sentence_starting_with_an_initial_is_still_body(paper, tmp_path):
    paper.body("I. Smith and J. Jones showed that this works well in practice.", size=12)
    assert len(rules_of(paper.issues(tmp_path), "Body text style")) == 1


# ---------------- headings (Springer: numbers) ----------------

def test_springer_auto_numbered_headings_are_clean(paper, tmp_path):
    for name in ("Introduction", "Method"):
        paper.heading(name, ARABIC)
        paper.body()
    assert rules_of(paper.issues(tmp_path, SPRINGER), "Heading numbering") == []


def test_springer_dotted_auto_numbers_are_accepted(paper, tmp_path):
    paper.heading("Introduction", ARABIC_DOT)
    paper.heading("Method", ARABIC_DOT)
    assert rules_of(paper.issues(tmp_path, SPRINGER), "Heading numbering") == []


def test_springer_roman_numbers_are_reported_once(paper, tmp_path):
    paper.heading("Introduction", ROMAN)
    paper.heading("Method", ROMAN)
    found = rules_of(paper.issues(tmp_path, SPRINGER), "Heading numbering")
    assert len(found) == 1 and "Arabic" in found[0].detail


def test_springer_unnumbered_heading_is_reported(paper, tmp_path):
    paper.heading("Introduction", ARABIC)
    paper.heading("Method", None, style="Heading 1")
    found = rules_of(paper.issues(tmp_path, SPRINGER), "Heading numbering")
    assert len(found) == 1 and "Method" in found[0].detail


def test_springer_typed_number_with_a_dot_is_a_heading(paper, tmp_path):
    paper.body("1. Introduction", size=16)
    assert rules_of(paper.issues(tmp_path, SPRINGER), "Body text style") == []


# ---------------- table captions ----------------

def test_uppercase_table_caption_without_a_period(paper, tmp_path):
    paper.body("As shown in Table I the runs agree. " + words(15))
    paper.table_caption("TABLE I", "Results of runs")
    assert counts(paper.issues(tmp_path)) == {}


def test_table_caption_with_title_on_the_same_line(paper, tmp_path):
    paper.body("As shown in Table I the runs agree. " + words(15))
    paper.table_caption("TABLE I", "Results of runs", same_line=True)
    assert counts(paper.issues(tmp_path)) == {}


def test_table_with_no_mention_in_the_text_is_warned(paper, tmp_path):
    paper.table_caption("TABLE II", "Results of runs")
    found = rules_of(paper.issues(tmp_path), "Table not referenced")
    assert len(found) == 1 and found[0].where == "Table II"


def test_mention_without_a_caption_is_an_error(paper, tmp_path):
    paper.body("As shown in Table III the runs agree. " + words(15))
    found = rules_of(paper.issues(tmp_path), "Table referenced but missing")
    assert len(found) == 1 and "Table III" in found[0].detail


def test_prose_starting_with_table_is_not_a_caption(paper, tmp_path):
    paper.body("Table I shows the results of all runs in detail across datasets and seeds.")
    got = counts(paper.issues(tmp_path))
    assert got == {"Table referenced but missing": 1}


def test_mixed_case_caption_with_a_period_still_works(paper, tmp_path):
    paper.body("See Table I. " + words(15))
    paper.table_caption("Table I.", "Results of runs", same_line=True)
    assert counts(paper.issues(tmp_path)) == {}


def test_springer_uppercase_arabic_caption_without_a_period(paper, tmp_path):
    paper.body("See Table 1 for the numbers. " + words(15))
    paper.table_caption("TABLE 1", "Results of runs")
    assert rules_of(paper.issues(tmp_path, SPRINGER), "Table referenced but missing") == []
    assert rules_of(paper.issues(tmp_path, SPRINGER), "Table not referenced") == []


def test_caption_title_line_is_not_body_text(paper, tmp_path):
    paper.body("See Table I. " + words(15))
    paper.table_caption("TABLE I", "Results of runs", size=12)
    assert rules_of(paper.issues(tmp_path), "Body text style") == []


def test_caption_at_the_very_end_of_the_document_does_not_crash(paper, tmp_path):
    paper._add("TABLE I", 8)
    paper.issues(tmp_path)


def test_a_paragraph_after_a_complete_caption_is_still_body(paper, tmp_path):
    paper.table_caption("TABLE I", "Results of runs", same_line=True)
    paper.body(size=12)
    assert len(rules_of(paper.issues(tmp_path), "Body text style")) == 1


# ---------------- body text is still checked ----------------

def test_real_body_paragraph_with_wrong_size_is_flagged(paper, tmp_path):
    paper.body(size=12)
    found = rules_of(paper.issues(tmp_path), "Body text style")
    assert len(found) == 1 and "size 12.0" in found[0].detail


def test_real_body_paragraph_with_wrong_font_is_flagged(paper, tmp_path):
    paper.body(font="Arial")
    found = rules_of(paper.issues(tmp_path), "Body text style")
    assert len(found) == 1 and "font Arial" in found[0].detail


# ---------------- all quirks in one paper ----------------

def test_a_paper_with_every_quirk_and_two_real_problems(paper, tmp_path):
    paper.heading("Introduction", ROMAN, size=16)
    paper.body("Background [1], [2] and Table I. " + words(15))
    paper.heading("Method", ROMAN, size=16)
    paper.body("Details [3]. " + words(15), size=12)             # real problem 1: wrong size
    paper.table_caption("TABLE I", "Results of runs")
    paper.heading("Results", None, size=16)                      # real problem 2: heading with no number
    paper.body("More [2]. " + words(15))
    paper.heading("Acknowledgment", None, style="Heading 1")
    paper.body("Thanks. " + words(15))
    paper.references(3)
    got = paper.issues(tmp_path)
    assert counts(got) == {"Body text style": 1, "Heading numbering": 1}


# ---------------- gaps found by mutation testing ----------------

def _classified(paper):
    paras = paper.doc.paragraphs
    return list(zip([p.text[:14] for p in paras], checker.classify(paras, IEEE)))


@pytest.mark.parametrize("letter", ["C", "D", "L", "M"])
def test_letter_subheadings_that_look_like_big_roman_numerals_are_subheadings(letter):
    assert checker.heading_number(f"{letter}. Dataset details") == ("sub", None)


def test_letter_subheading_c_is_not_a_numbering_problem(paper, tmp_path):
    paper.heading("I. Method", style="Heading 1")
    paper.heading("A. First", style="Heading 2")
    paper.heading("B. Second", style="Heading 2")
    paper.heading("C. Third", style="Heading 2")
    paper.heading("D. Fourth", style="Heading 2")
    assert rules_of(paper.issues(tmp_path), "Heading numbering") == []


def test_unnumbered_reference_entries_that_start_like_a_roman_heading_stay_reference_text(paper):
    paper.heading("References", style="Normal")
    for text in ("I. Goodfellow, Y. Bengio, Deep Learning, MIT Press", "V. Vapnik, Statistical Learning Theory, Wiley"):
        paper.doc.add_paragraph(text)
    assert [lab for _t, lab in _classified(paper)][-2:] == ["reference_text", "reference_text"]


def test_references_heading_in_capitals_still_opens_the_reference_list(paper):
    paper.heading("REFERENCES", style="Normal")
    paper.doc.add_paragraph("A. Writer, Title, 2020")
    assert [lab for _t, lab in _classified(paper)][-2:] == ["heading", "reference_text"]


def test_long_paragraph_after_a_bare_table_label_is_body_text_not_a_caption(paper):
    paper.table_caption("TABLE I", title=words(40))
    assert [lab for _t, lab in _classified(paper)][-2:] == ["caption_table", "body"]


def test_short_line_after_a_bare_table_label_is_its_title(paper):
    paper.table_caption("TABLE I", title="Results of runs")
    assert [lab for _t, lab in _classified(paper)][-2:] == ["caption_table", "caption_text"]


def test_appendix_heading_needs_no_number(paper, tmp_path):
    paper.heading("I. Method", style="Heading 1")
    paper.heading("Appendix", style="Heading 1")
    assert rules_of(paper.issues(tmp_path), "Heading numbering") == []


def test_ordinary_unnumbered_heading_is_still_reported(paper, tmp_path):
    paper.heading("I. Method", style="Heading 1")
    paper.heading("Discussion", style="Heading 1")
    assert len(rules_of(paper.issues(tmp_path), "Heading numbering")) == 1
