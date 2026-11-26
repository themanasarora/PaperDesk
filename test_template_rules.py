import datetime

from docx import Document
from docx.shared import Inches, Pt

import checker
from template_rules import rules_from_template

TODAY = datetime.date(2026, 11, 27)
LONG = "This body paragraph has well over fifteen words so that it counts as real body text in the template."


def make_template(tmp_path, page=(8.27, 11.69), margins=(0.75, 1.0, 0.6, 0.6), font="Times New Roman", size=10):
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(page[0]), Inches(page[1])
    sec.top_margin, sec.bottom_margin = Inches(margins[0]), Inches(margins[1])
    sec.left_margin, sec.right_margin = Inches(margins[2]), Inches(margins[3])
    doc.add_paragraph("Short title")
    for _ in range(3):
        run = doc.add_paragraph().add_run(LONG)
        run.font.name, run.font.size = font, Pt(size)
    path = tmp_path / "template.docx"
    doc.save(path)
    return str(path)


def test_reads_page_margins_and_body_font(tmp_path):
    r = rules_from_template(make_template(tmp_path), name="Mine", today=TODAY)
    assert r["page_name"] == "A4"
    assert (r["page_width_in"], r["page_height_in"]) == (8.27, 11.69)
    assert r["margins_in"] == {"top": 0.75, "bottom": 1.0, "left": 0.6, "right": 0.6}
    assert (r["body_font"], r["body_size_pt"]) == ("Times New Roman", 10)


def test_names_us_letter(tmp_path):
    r = rules_from_template(make_template(tmp_path, page=(8.5, 11.0)), today=TODAY)
    assert r["page_name"] == "US Letter"


def test_unknown_page_size_is_described_by_its_dimensions(tmp_path):
    r = rules_from_template(make_template(tmp_path, page=(6.0, 9.0)), today=TODAY)
    assert r["page_name"] == "6.00 x 9.00 in"


def test_body_font_is_the_most_common_not_the_title(tmp_path):
    r = rules_from_template(make_template(tmp_path, font="Georgia", size=11), today=TODAY)
    assert (r["body_font"], r["body_size_pt"]) == ("Georgia", 11)


def test_custom_rules_only_check_page_margins_and_font(tmp_path):
    r = rules_from_template(make_template(tmp_path), name="Mine", today=TODAY)
    assert r["name"] == "Mine"
    assert r["abstract_words"] is None and r["heading_style"] == "none"
    assert r["require_index_terms"] is False and r["require_figure_table_references"] is False
    assert r["verified"] is True and r["last_verified"] == "2026-11-27"


def test_paper_matching_its_own_template_passes_layout_checks(tmp_path):
    path = make_template(tmp_path)
    issues = checker.check(path, rules_from_template(path, today=TODAY))
    assert not {i.rule for i in issues} & {"Page size", "Margin", "Body text style"}


def test_template_without_body_paragraphs_falls_back_to_normal_style(tmp_path):
    doc = Document()
    doc.add_paragraph("short")
    path = tmp_path / "t.docx"
    doc.save(path)
    normal = Document(str(path)).styles["Normal"].font
    r = rules_from_template(str(path), today=TODAY)
    assert r["body_font"] == normal.name
    assert r["body_size_pt"] == (normal.size.pt if normal.size else None)
