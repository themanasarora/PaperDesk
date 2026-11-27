import random

import pytest
from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

from docx_helpers import number_paragraph, number_style, numbered_doc, set_numbering
from numbering import rendered_labels

DEC_BRACKET = {0: {0: ("decimal", "[%1]", 1)}}
ONE = {1: (0, {})}


def labels(specs, abstracts, nums):
    return rendered_labels(numbered_doc(specs, abstracts, nums))


def items(n, num_id=1, ilvl=0):
    return [(f"p{i}", num_id, ilvl) for i in range(n)]


# ---- number formats ----

def test_decimal_in_brackets_like_ieee_reference_lists():
    assert labels(items(3), DEC_BRACKET, ONE) == ["[1]", "[2]", "[3]"]


def test_decimal_with_dot_and_start_value():
    assert labels(items(2), {0: {0: ("decimal", "%1.", 5)}}, ONE) == ["5.", "6."]


def test_upper_roman_up_to_xiv():
    got = labels(items(14), {0: {0: ("upperRoman", "%1.", 1)}}, ONE)
    assert got[:4] == ["I.", "II.", "III.", "IV."] and got[8] == "IX." and got[13] == "XIV."


def test_lower_roman_in_parentheses():
    assert labels(items(3), {0: {0: ("lowerRoman", "(%1)", 1)}}, ONE) == ["(i)", "(ii)", "(iii)"]


def test_upper_letter_wraps_after_z():
    got = labels(items(28), {0: {0: ("upperLetter", "%1.", 1)}}, ONE)
    assert got[0] == "A." and got[25] == "Z." and got[26] == "AA." and got[27] == "BB."


def test_lower_letter():
    assert labels(items(2), {0: {0: ("lowerLetter", "%1)", 1)}}, ONE) == ["a)", "b)"]


def test_decimal_zero_pads_single_digits():
    got = labels(items(10), {0: {0: ("decimalZero", "%1", 1)}}, ONE)
    assert got[0] == "01" and got[8] == "09" and got[9] == "10"


def test_bullet_and_none_formats_have_no_label():
    assert labels(items(2), {0: {0: ("bullet", "•", 1)}}, ONE) == ["", ""]
    assert labels(items(2), {0: {0: ("none", "", 1)}}, ONE) == ["", ""]


def test_unknown_format_falls_back_to_decimal():
    assert labels(items(2), {0: {0: ("someFutureFormat", "%1.", 1)}}, ONE) == ["1.", "2."]


def test_literal_text_in_level_text_is_kept():
    assert labels(items(2), {0: {0: ("decimal", "Section %1:", 1)}}, ONE) == ["Section 1:", "Section 2:"]


# ---- counting rules ----

MULTI = {0: {0: ("decimal", "%1.", 1), 1: ("decimal", "%1.%2", 1), 2: ("decimal", "%1.%2.%3", 1)}}


def test_multilevel_numbering_resets_deeper_levels():
    specs = [("a", 1, 0), ("b", 1, 1), ("c", 1, 1), ("d", 1, 2), ("e", 1, 0), ("f", 1, 1)]
    assert labels(specs, MULTI, ONE) == ["1.", "1.1", "1.2", "1.2.1", "2.", "2.1"]


def test_unnumbered_paragraphs_do_not_count_or_reset():
    specs = [("a", 1, 0), ("plain", None, 0), ("b", 1, 0)]
    assert labels(specs, DEC_BRACKET, ONE) == ["[1]", "", "[2]"]


def test_separate_abstracts_count_independently_when_interleaved():
    abstracts = {0: {0: ("decimal", "%1.", 1)}, 1: {0: ("upperLetter", "%1.", 1)}}
    nums = {1: (0, {}), 2: (1, {})}
    specs = [("a", 1, 0), ("b", 2, 0), ("c", 1, 0), ("d", 2, 0)]
    assert labels(specs, abstracts, nums) == ["1.", "A.", "2.", "B."]


def test_two_numbering_instances_of_one_list_continue_the_count():
    nums = {1: (0, {}), 2: (0, {})}
    specs = [("a", 1, 0), ("b", 2, 0), ("c", 1, 0)]
    assert labels(specs, DEC_BRACKET, nums) == ["[1]", "[2]", "[3]"]


def test_start_override_restarts_the_count():
    nums = {1: (0, {}), 2: (0, {0: 1})}
    specs = [("a", 1, 0), ("b", 1, 0), ("c", 2, 0), ("d", 2, 0)]
    assert labels(specs, DEC_BRACKET, nums) == ["[1]", "[2]", "[1]", "[2]"]


def test_start_override_to_a_later_number():
    nums = {1: (0, {0: 7})}
    assert labels(items(2), DEC_BRACKET, nums) == ["[7]", "[8]"]


def test_numbering_in_a_table_cell_counts_but_is_not_returned():
    doc = numbered_doc([("a", 1, 0)], DEC_BRACKET, ONE)
    cell = doc.add_table(rows=1, cols=1).cell(0, 0)
    number_paragraph(cell.paragraphs[0], 1, 0)
    number_paragraph(doc.add_paragraph("c"), 1, 0)
    assert rendered_labels(doc) == ["[1]", "[3]"]


# ---- where the numbering comes from ----

def test_numbering_defined_on_the_paragraph_style():
    doc = Document()
    set_numbering(doc, DEC_BRACKET, ONE)
    style = doc.styles.add_style("Refs", 1)
    number_style(style, 1)
    for t in ("a", "b"):
        doc.add_paragraph(t, style="Refs")
    assert rendered_labels(doc) == ["[1]", "[2]"]


def test_numbering_inherited_through_style_inheritance():
    doc = Document()
    set_numbering(doc, DEC_BRACKET, ONE)
    base = doc.styles.add_style("RefBase", 1)
    number_style(base, 1)
    child = doc.styles.add_style("RefChild", 1)
    child.base_style = base
    doc.add_paragraph("a", style="RefChild")
    assert rendered_labels(doc) == ["[1]"]


def test_paragraph_numbering_overrides_the_style():
    abstracts = {0: {0: ("decimal", "%1.", 1)}, 1: {0: ("upperLetter", "%1.", 1)}}
    nums = {1: (0, {}), 2: (1, {})}
    doc = Document()
    set_numbering(doc, abstracts, nums)
    style = doc.styles.add_style("Refs", 1)
    number_style(style, 1)
    p = doc.add_paragraph("a", style="Refs")
    number_paragraph(p, 2, 0)
    assert rendered_labels(doc) == ["A."]


def test_num_id_zero_switches_numbering_off_even_if_the_style_has_it():
    doc = Document()
    set_numbering(doc, DEC_BRACKET, ONE)
    style = doc.styles.add_style("Refs", 1)
    number_style(style, 1)
    number_paragraph(doc.add_paragraph("a", style="Refs"), 0, 0)
    doc.add_paragraph("b", style="Refs")
    assert rendered_labels(doc) == ["", "[1]"]


def test_missing_ilvl_means_level_zero():
    doc = Document()
    set_numbering(doc, DEC_BRACKET, ONE)
    number_paragraph(doc.add_paragraph("a"), 1, None)
    assert rendered_labels(doc) == ["[1]"]


# ---- bad input never crashes ----

def test_unknown_num_id_gives_no_label():
    assert labels(items(2, num_id=99), DEC_BRACKET, ONE) == ["", ""]


def test_num_pointing_at_missing_abstract_gives_no_label():
    assert labels(items(2), DEC_BRACKET, {1: (42, {})}) == ["", ""]


def test_level_not_defined_gives_no_label():
    assert labels(items(2, ilvl=5), DEC_BRACKET, ONE) == ["", ""]


def test_level_text_naming_an_undefined_level_does_not_crash():
    got = labels(items(1), {0: {0: ("decimal", "%1.%3", 1)}}, ONE)
    assert len(got) == 1 and got[0].startswith("1.")


def test_document_without_any_lists():
    doc = Document()
    doc.add_paragraph("x")
    assert rendered_labels(doc) == [""]


def test_empty_document():
    assert rendered_labels(Document()) == []


def test_document_with_no_numbering_part_content():
    doc = Document()
    set_numbering(doc, {}, {})
    number_paragraph(doc.add_paragraph("a"), 1, 0)
    assert rendered_labels(doc) == [""]


def test_garbage_numbering_values_do_not_crash():
    doc = Document()
    root = doc.part.numbering_part.element
    for child in list(root):
        root.remove(child)
    root.append(parse_xml(
        f'<w:abstractNum {nsdecls("w")} w:abstractNumId="0"><w:lvl w:ilvl="0"><w:start w:val="abc"/>'
        f'<w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/></w:lvl></w:abstractNum>'))
    root.append(parse_xml(f'<w:num {nsdecls("w")} w:numId="1"><w:abstractNumId w:val="0"/></w:num>'))
    number_paragraph(doc.add_paragraph("a"), 1, 0)
    got = rendered_labels(doc)
    assert len(got) == 1


def test_random_numbering_setups_never_crash_and_keep_length():
    rng = random.Random(20261127)
    fmts = ["decimal", "upperRoman", "lowerRoman", "upperLetter", "lowerLetter", "bullet", "none", "weird"]
    texts = ["%1.", "[%1]", "%1.%2", "(%2)", "", "%9", "x%1y%1", "%"]
    for _ in range(200):
        abstracts = {a: {l: (rng.choice(fmts), rng.choice(texts), rng.randint(0, 30))
                         for l in range(rng.randint(1, 3))} for a in range(rng.randint(1, 3))}
        nums = {n: (rng.randint(0, 4), {rng.randint(0, 3): rng.randint(0, 9)} if rng.random() < 0.3 else {})
                for n in range(1, rng.randint(2, 5))}
        specs = [(f"p{i}", rng.choice([None, 0, 1, 2, 3, 9]), rng.choice([None, 0, 1, 2, 7]))
                 for i in range(rng.randint(0, 12))]
        got = labels(specs, abstracts, nums)
        assert len(got) == len(specs) and all(isinstance(x, str) for x in got)
