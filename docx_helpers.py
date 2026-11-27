"""Test helpers: build .docx files that use Word's automatic numbering.

Not used by the app. Real papers number headings and reference lists with
Word lists, so the numbers are not in the paragraph text; these helpers let
tests recreate that.
"""
from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls


def set_numbering(doc, abstracts, nums):
    """abstracts: {abstract_id: {ilvl: (numFmt, lvlText, start)}};
    nums: {num_id: (abstract_id, {ilvl: startOverride})}."""
    root = doc.part.numbering_part.element
    for child in list(root):
        root.remove(child)
    for aid, levels in abstracts.items():
        lvls = "".join(
            f'<w:lvl w:ilvl="{lvl}"><w:start w:val="{start}"/><w:numFmt w:val="{fmt}"/>'
            f'<w:lvlText w:val="{text}"/></w:lvl>'
            for lvl, (fmt, text, start) in levels.items())
        root.append(parse_xml(f'<w:abstractNum {nsdecls("w")} w:abstractNumId="{aid}">{lvls}</w:abstractNum>'))
    for nid, (aid, overrides) in nums.items():
        ov = "".join(
            f'<w:lvlOverride w:ilvl="{lvl}"><w:startOverride w:val="{start}"/></w:lvlOverride>'
            for lvl, start in overrides.items())
        root.append(parse_xml(
            f'<w:num {nsdecls("w")} w:numId="{nid}"><w:abstractNumId w:val="{aid}"/>{ov}</w:num>'))


def _num_pr(num_id, ilvl):
    ilvl_xml = "" if ilvl is None else f'<w:ilvl w:val="{ilvl}"/>'
    return parse_xml(f'<w:numPr {nsdecls("w")}>{ilvl_xml}<w:numId w:val="{num_id}"/></w:numPr>')


def number_paragraph(paragraph, num_id, ilvl=0):
    paragraph._p.get_or_add_pPr().append(_num_pr(num_id, ilvl))
    return paragraph


def number_style(style, num_id, ilvl=None):
    style.element.get_or_add_pPr().append(_num_pr(num_id, ilvl))
    return style


def numbered_doc(specs, abstracts, nums):
    """specs: list of (text, num_id or None, ilvl). Returns the Document."""
    doc = Document()
    set_numbering(doc, abstracts, nums)
    for text, num_id, ilvl in specs:
        p = doc.add_paragraph(text)
        if num_id is not None:
            number_paragraph(p, num_id, ilvl)
    return doc
