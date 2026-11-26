import checker
from rules import get_ruleset, with_defaults

A4 = (8.27, 11.69)
NUMERIC = with_defaults({**get_ruleset("ieee_conference"), "heading_style": "numeric",
                         "keywords_label": "Keywords", "table_numbering": "arabic"})
A4_RULES = with_defaults({**get_ruleset("ieee_conference"), "page_name": "A4",
                          "page_width_in": 8.27, "page_height_in": 11.69})
FRONT = ["Title", "Author", "Abstract— short", "Keywords: a, b"]


def rules_hit(issues):
    return {i.rule for i in issues}


def test_ieee_baseline_unchanged():
    flawed = checker.check("samples/test_paper_flawed.docx")
    clean = checker.check("samples/test_paper_clean.docx")
    assert (sum(i.severity == "ERROR" for i in flawed), sum(i.severity == "WARN" for i in flawed)) == (9, 3)
    assert (sum(i.severity == "ERROR" for i in clean), sum(i.severity == "WARN" for i in clean)) == (0, 0)


def test_a4_document_fails_letter_ruleset(build_docx):
    issues = checker.check(build_docx(FRONT, page=A4))
    page = [i for i in issues if i.rule == "Page size"]
    assert page and "US Letter" in page[0].detail


def test_a4_document_passes_a4_ruleset(build_docx):
    assert "Page size" not in rules_hit(checker.check(build_docx(FRONT, page=A4), A4_RULES))


def test_keywords_label_in_message(build_docx):
    rules = with_defaults({**get_ruleset("ieee_conference"), "keywords_label": "Keywords"})
    issues = checker.check(build_docx(["Title", "Author", "Abstract— short"]), rules)
    msg = [i for i in issues if i.rule == "Index terms"]
    assert msg and "Keywords" in msg[0].detail


def test_numeric_headings_with_subsections_pass(build_docx):
    paras = FRONT + ["1 Introduction", "text", "1.1 Background", "text", "1.2 Scope", "text",
                     "2 Methods", "text", "References"]
    assert "Heading numbering" not in rules_hit(checker.check(build_docx(paras), NUMERIC))


def test_numeric_headings_out_of_order_flagged(build_docx):
    paras = FRONT + ["1 Introduction", "text", "3 Results", "text"]
    issues = checker.check(build_docx(paras), NUMERIC)
    msg = [i for i in issues if i.rule == "Heading numbering"]
    assert msg and "section 2 was expected" in msg[0].detail


def test_number_led_body_text_is_not_a_heading(build_docx):
    from docx import Document
    path = build_docx(["Title", "Author", "Abstract— x",
                       "2 samples were excluded from the study",
                       "2 Samples were excluded from the study."])
    labels = checker.classify(Document(path).paragraphs, NUMERIC)
    assert labels[3:] == ["body", "body"]


def test_arabic_table_captions(build_docx):
    paras = FRONT + ["See Table 1 for results.", "Table 1. Results"]
    hit = rules_hit(checker.check(build_docx(paras), NUMERIC))
    assert "Table not referenced" not in hit and "Table referenced but missing" not in hit


def test_arabic_table_without_reference_is_flagged(build_docx):
    hit = rules_hit(checker.check(build_docx(FRONT + ["Table 1. Results"]), NUMERIC))
    assert "Table not referenced" in hit


def test_arabic_table_reference_without_caption_is_flagged(build_docx):
    hit = rules_hit(checker.check(build_docx(FRONT + ["See Table 2 for results."]), NUMERIC))
    assert "Table referenced but missing" in hit


SPRINGER = get_ruleset("springer_lncs")


def test_springer_dotted_references_give_no_false_citation_errors(build_docx):
    paras = FRONT + ["1 Introduction", "See [1] and [2].", "References",
                     "1. Smith, J.: Paper. LNCS (2020).", "2. Doe, K.: Other. LNCS (2021)."]
    assert "Citation without reference" not in rules_hit(checker.check(build_docx(paras, page=A4), SPRINGER))


def test_springer_reference_without_final_period_is_not_a_heading(build_docx):
    paras = FRONT + ["1 Introduction", "See [1].", "2 Methods", "text", "References",
                     "1 Smith, J.: A paper. LNCS 1234 (2020)"]
    assert "Heading numbering" not in rules_hit(checker.check(build_docx(paras, page=A4), SPRINGER))
